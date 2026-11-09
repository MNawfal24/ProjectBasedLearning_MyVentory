"""Generate a synthetic daily stock ledger (Stock.csv) from the real transaction export.

The export carries no stock counts, so the ledger is simulated with a daily (s, S)
replenishment policy driven by the *actual* units sold per outlet x product:

  * MinimumStock = max(1, ceil(mean daily demand * 3)) - the same 3-day cover rule
    the web seeder uses for min_quantity;
  * reorder point s = MinimumStock and order-up-to
    S = s + ceil(mean * (L+1) + 1.96 * std * sqrt(L+1)), lead time L per outlet;
  * one order is outstanding at a time and arrives as StockIn after L days;
  * StockOut = min(real demand, OpeningStock + StockIn), so stock-outs lose sales
    and ClosingStock never goes negative.

Outputs (and nothing else):
  * ML/data/Stock.csv      - Date, Outlet, ItemID, OpeningStock, StockIn,
                             StockOut, ClosingStock, MinimumStock
  * ML/data/ItemMaster.csv - ItemID -> product name (P001.. in the same
                             alphabetical order as the web seeder's SKU)
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "Transactions.csv"
OUT_PATH = DATA_PATH.parent / "Stock.csv"
MASTER_PATH = DATA_PATH.parent / "ItemMaster.csv"

COVER_DAYS = 3
WARMUP_DAYS = 14
Z = 1.96
LEAD_DAYS = {"SHOP001": 3, "SHOP002": 2, "SHOP003": 2}
COLUMNS = [
    "Date",
    "Outlet",
    "ItemID",
    "OpeningStock",
    "StockIn",
    "StockOut",
    "ClosingStock",
    "MinimumStock",
]


def item_master(products) -> dict[str, str]:
    """ItemID -> product name, P001.. in sorted order (matches the web seeder)."""
    return {f"P{i:03d}": name for i, name in enumerate(sorted(products), start=1)}


def load_transactions(path: pathlib.Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["Date"])
    df["product_list"] = df["Items"].str.split(",").apply(lambda xs: [x.strip() for x in xs])
    return df


def product_demand(df: pd.DataFrame) -> pd.DataFrame:
    """Daily units sold per outlet x product, zero filled for days without a sale."""
    lines = df[["Outlet", "date", "product_list", "NetSales"]].explode("product_list")
    lines = lines.rename(columns={"product_list": "product"})
    lines["revenue"] = lines["NetSales"] / lines.groupby(level=0)["product"].transform("size")
    out = (
        lines.groupby(["Outlet", "product", "date"])
        .agg(qty=("product", "size"), revenue=("revenue", "sum"))
        .reset_index()
    )
    dates = pd.date_range(out["date"].min(), out["date"].max(), freq="D")
    index = pd.MultiIndex.from_product(
        [sorted(out["Outlet"].unique()), sorted(out["product"].unique()), dates],
        names=["Outlet", "product", "date"],
    )
    out = out.set_index(["Outlet", "product", "date"]).reindex(index)
    out["qty"] = out["qty"].fillna(0)
    out["revenue"] = out["revenue"].fillna(0.0)
    return out.reset_index()


def simulate(panel: pd.DataFrame, item_ids: dict[str, str]) -> pd.DataFrame:
    """Daily ledger per outlet x item. ``item_ids`` maps ItemID -> product name."""
    id_of = {name: pid for pid, name in item_ids.items()}
    rows = []
    for key, series in panel.groupby(["Outlet", "product"], sort=True):
        outlet, product = str(key[0]), str(key[1])
        series = series.sort_values("date")
        warm = series["qty"].head(WARMUP_DAYS)
        mean = float(warm.mean())
        std = float(warm.std(ddof=0))
        lead = LEAD_DAYS[outlet]

        minimum = max(1, math.ceil(mean * COVER_DAYS))
        target = minimum + math.ceil(mean * (lead + 1) + Z * std * math.sqrt(lead + 1))

        on_hand = target
        pending: dict[int, int] = {}
        for i, (date, demand) in enumerate(zip(series["date"], series["qty"].astype(int))):
            stock_in = pending.pop(i, 0)
            available = on_hand + stock_in
            stock_out = min(int(demand), available)
            closing = available - stock_out
            rows.append(
                (date, outlet, id_of[product], on_hand, stock_in, stock_out, closing, minimum)
            )
            on_hand = closing
            position = on_hand + sum(pending.values())
            if position <= minimum and not pending:
                pending[i + lead] = max(0, target - position)
    return pd.DataFrame(rows, columns=COLUMNS)


def check(stock: pd.DataFrame, panel: pd.DataFrame, item_ids: dict[str, str]) -> None:
    expected = panel["date"].nunique() * panel["Outlet"].nunique() * panel["product"].nunique()
    assert len(stock) == expected, f"row count {len(stock)} != {expected}"
    assert (stock["OpeningStock"] + stock["StockIn"] - stock["StockOut"] == stock["ClosingStock"]).all()
    assert (stock["ClosingStock"] >= 0).all()
    assert (stock["StockIn"] >= 0).all() and (stock["StockOut"] >= 0).all()
    assert (stock["MinimumStock"] >= 1).all()

    keys = ["Date", "Outlet", "ItemID"]
    assert not stock.duplicated(keys).any()
    days = stock.groupby(["Outlet", "ItemID"]).size()
    assert days.nunique() == 1 and days.iloc[0] == panel["date"].nunique()

    id_of = {name: pid for pid, name in item_ids.items()}
    demand = panel.rename(columns={"date": "Date", "qty": "Demand"}).copy()
    demand["ItemID"] = demand["product"].map(id_of)
    merged = stock.merge(demand[["Date", "Outlet", "ItemID", "Demand"]], on=keys, how="left")
    assert len(merged) == len(stock)
    assert bool(merged["Demand"].notna().all())
    stockout = (merged["StockOut"] < merged["Demand"]).to_numpy()
    assert bool((merged.loc[~stockout, "StockOut"] == merged.loc[~stockout, "Demand"]).all())

    print(
        f"rows={len(stock)} dates={stock['Date'].nunique()} outlets={stock['Outlet'].nunique()} "
        f"items={stock['ItemID'].nunique()} stockout_rows={int(stockout.sum())} "
        f"({stockout.mean():.2%}) fill_rate={1 - (merged['Demand'] - merged['StockOut']).sum() / merged['Demand'].sum():.2%} "
        f"replenishments={int((stock['StockIn'] > 0).sum())}"
    )
    summary = stock.groupby("Outlet").agg(
        avg_closing=("ClosingStock", "mean"),
        min_closing=("ClosingStock", "min"),
        avg_stock_out=("StockOut", "mean"),
    )
    print(summary.round(2).to_string())


def main() -> None:
    df = load_transactions()
    panel = product_demand(df)
    item_ids = item_master(panel["product"].unique())

    stock = simulate(panel, item_ids)
    check(stock, panel, item_ids)

    stock["Date"] = stock["Date"].dt.strftime("%Y-%m-%d")
    stock.to_csv(OUT_PATH, index=False)
    pd.DataFrame({"ItemID": list(item_ids), "ProductName": list(item_ids.values())}).to_csv(
        MASTER_PATH, index=False
    )
    print(f"wrote {OUT_PATH.relative_to(DATA_PATH.parents[1])} and {MASTER_PATH.relative_to(DATA_PATH.parents[1])}")


if __name__ == "__main__":
    main()
