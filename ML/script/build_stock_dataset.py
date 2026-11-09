"""Build the stock-out risk dataset from Stock.csv and the transaction export.

Every feature and label comes from a recorded value: the ledger state in
Stock.csv and the outlet traffic in Transactions.csv. Nothing is reconstructed
or assumed, so no lead time, outstanding order or adaptive reorder point is
invented here.

  * stock state (ClosingStock, MinimumStock, gap, cover days) is read as is;
  * demand features are lagged StockOut, which is what the ledger recorded;
  * outlet traffic (receipts, units, sales) comes from Transactions.csv, lagged
    so it is known before the day being predicted;
  * ``demand_true``, ``is_censored`` and ``lost_units`` expose how much demand
    the ledger could not serve, so the censoring can be measured instead of
    guessed.

Labels are forward-looking: they answer "will this outlet x item run out
within H days". Every feature uses data up to and including day t; every label
uses days t+1..t+H.

Outputs:
  * ML/data/stock_forecast_dataset.csv
  * ML/data/stock_forecast_dataset_meta.json
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd

DATA_DIR = pathlib.Path(__file__).resolve().parents[1] / "data"
STOCK_PATH = DATA_DIR / "Stock.csv"
TRANSACTIONS_PATH = DATA_DIR / "Transactions.csv"
MASTER_PATH = DATA_DIR / "ItemMaster.csv"
OUT_PATH = DATA_DIR / "stock_forecast_dataset.csv"
META_PATH = DATA_DIR / "stock_forecast_dataset_meta.json"

SPLIT_DATE = pd.Timestamp("2025-08-31")
MAX_DAYS_TO_EMPTY = 14
HORIZONS = (2, 3, 7)

STOCK_STATE = [
    "ClosingStock",
    "MinimumStock",
    "gap_to_min",
    "cover_days",
]
DEMAND = ["avg7", "avg28", "std7", "std28", "lag1", "lag7", "lag14", "lag28", "series_mean"]
TRAFFIC = [
    "receipts_lag1",
    "receipts_roll7",
    "items_lag1",
    "items_roll7",
    "sales_lag1",
    "sales_roll7",
    "cash_share_lag1",
]
CALENDAR = ["dow", "is_weekend", "day", "month"]
CATEGORICAL = ["Outlet", "ItemID"]
FEATURES = STOCK_STATE + DEMAND + TRAFFIC + CALENDAR
LABELS = [f"Y_empty_{h}" for h in HORIZONS] + ["Y_belowmin_3"]


def load_stock() -> pd.DataFrame:
    stock = pd.read_csv(STOCK_PATH, parse_dates=["Date"])
    stock = stock.sort_values(["Outlet", "ItemID", "Date"]).reset_index(drop=True)
    assert (stock.OpeningStock + stock.StockIn - stock.StockOut == stock.ClosingStock).all()
    return stock


def load_true_demand(master: pd.DataFrame) -> pd.DataFrame:
    """Daily units actually sold per outlet x item, before the ledger censored them."""
    transactions = pd.read_csv(TRANSACTIONS_PATH, parse_dates=["Date"])
    lines = transactions[["Outlet", "Date", "Items"]].copy()
    lines["ProductName"] = lines.Items.str.split(",")
    lines = lines.explode("ProductName")
    lines["ProductName"] = lines.ProductName.str.strip()
    lines = lines.merge(master, on="ProductName", how="inner")
    assert len(lines) == len(lines.dropna(subset=["ItemID"])), "unknown product name in transactions"
    return lines.groupby(["Outlet", "ItemID", "Date"]).size().to_frame("demand_true").reset_index()


def load_traffic() -> pd.DataFrame:
    """Outlet-day footfall, lagged so the value is known before the predicted day."""
    transactions = pd.read_csv(TRANSACTIONS_PATH, parse_dates=["Date"])
    traffic = (
        transactions.groupby(["Outlet", "Date"])
        .agg(
            receipts=("ReceiptNumber", "nunique"),
            items=("TotalItem", "sum"),
            sales=("NetSales", "sum"),
            cash=("PaymentMethod", lambda x: (x == "Cash").sum()),
        )
        .reset_index()
        .sort_values(["Outlet", "Date"])
    )
    traffic["cash_share"] = traffic.cash / traffic.receipts
    by_outlet = traffic.groupby("Outlet", sort=False)
    for column in ("receipts", "items", "sales", "cash_share"):
        traffic[f"{column}_lag1"] = by_outlet[column].shift(1)
        traffic[f"{column}_roll7"] = by_outlet[column].transform(lambda s: s.shift(1).rolling(7).mean())
    return traffic



def add_features(frame: pd.DataFrame, traffic: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    by_series = frame.groupby(["Outlet", "ItemID"], sort=False)

    for window in (7, 28):
        frame[f"avg{window}"] = by_series.StockOut.transform(lambda s: s.shift(1).rolling(window).mean())
        frame[f"std{window}"] = by_series.StockOut.transform(lambda s: s.shift(1).rolling(window).std())
    for lag in (1, 7, 14, 28):
        frame[f"lag{lag}"] = by_series.StockOut.shift(lag)
    assert frame.lag1.fillna(-1).equals(by_series.StockOut.shift(1).fillna(-1)), "lag1 is not yesterday's StockOut"

    train = frame.Date <= SPLIT_DATE
    frame["series_mean"] = frame.loc[train].groupby(["Outlet", "ItemID"]).StockOut.transform("mean")
    frame["series_mean"] = frame.groupby(["Outlet", "ItemID"]).series_mean.transform("first")
    frame["series_mean"] = frame.series_mean.fillna(frame.groupby(["Outlet", "ItemID"]).StockOut.transform("mean"))

    frame["gap_to_min"] = frame.ClosingStock - frame.MinimumStock
    frame["cover_days"] = np.where(frame.avg7 > 0, frame.ClosingStock / frame.avg7.replace(0, np.nan), 99.0)
    frame["cover_days"] = frame.cover_days.clip(upper=99)

    frame["dow"] = frame.Date.dt.dayofweek
    frame["is_weekend"] = (frame.dow >= 5).astype(int)
    frame["day"] = frame.Date.dt.day
    frame["month"] = frame.Date.dt.month

    frame = frame.merge(
        traffic[["Outlet", "Date", "receipts_lag1", "receipts_roll7", "items_lag1", "items_roll7", "sales_lag1", "sales_roll7", "cash_share_lag1"]],
        on=["Outlet", "Date"],
        how="left",
    )
    return frame


def add_labels(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    empty = (frame.ClosingStock == 0).astype(int)
    below_min = (frame.ClosingStock < frame.MinimumStock).astype(int)
    keys = [frame.Outlet, frame.ItemID]

    def forward_any(series: pd.Series, horizon: int) -> pd.Series:
        # shift(-horizon) then rolling gives days t+1..t+horizon, excluding today
        return series.groupby(keys, sort=False).transform(
            lambda s: s.shift(-horizon).rolling(horizon, min_periods=horizon).max()
        )

    for horizon in HORIZONS:
        frame[f"Y_empty_{horizon}"] = forward_any(empty, horizon)
    frame["Y_belowmin_3"] = forward_any(below_min, 3)

    days_to_empty = np.full(len(frame), np.nan)
    for _, group in frame.groupby(["Outlet", "ItemID"], sort=False):
        positions = group.index.to_numpy()
        closing = group.ClosingStock.to_numpy()
        for row in range(len(closing)):
            for step in range(1, MAX_DAYS_TO_EMPTY + 1):
                if row + step < len(closing) and closing[row + step] == 0:
                    days_to_empty[positions[row]] = step
                    break
    frame["days_to_empty"] = days_to_empty
    return frame


def add_censoring(frame: pd.DataFrame, demand: pd.DataFrame) -> pd.DataFrame:
    frame = frame.merge(demand, on=["Outlet", "ItemID", "Date"], how="left")
    frame["demand_true"] = frame.demand_true.fillna(0)
    frame["is_censored"] = (frame.demand_true > frame.StockOut).astype(int)
    frame["lost_units"] = (frame.demand_true - frame.StockOut).clip(lower=0)
    return frame


def check(frame: pd.DataFrame, stock: pd.DataFrame) -> None:
    missing = frame[FEATURES].isna().sum()
    assert int(missing.sum()) == 0, f"NaN in features: {missing[missing > 0].to_dict()}"
    assert bool(frame.days_to_empty.dropna().between(1, MAX_DAYS_TO_EMPTY).all()), "days_to_empty out of range"

    for label in LABELS:
        assert bool(frame[label].isin([0, 1]).all()), f"{label} is not binary"
        assert int(frame[label].isna().sum()) == 0, f"{label} has NaN"

    # a longer window must contain the shorter one
    assert bool((frame.Y_empty_7 >= frame.Y_empty_3).all()), "7-day label must cover the 3-day label"
    assert bool((frame.Y_empty_3 >= frame.Y_empty_2).all()), "3-day label must cover the 2-day label"

    assert frame.Date.max() < stock.Date.max(), "the tail must be dropped for the forward windows"
    assert set(frame.split.unique()) == {"train", "test"}

    print(
        f"rows={len(frame):,} series={frame.groupby(['Outlet', 'ItemID']).ngroups} "
        f"dates={frame.Date.nunique()} train={(frame.split == 'train').sum():,} test={(frame.split == 'test').sum():,}"
    )
    print(f"censored rows={frame.is_censored.mean():.2%} lost units={int(frame.lost_units.sum()):,} "
          f"fill rate={frame.StockOut.sum() / frame.demand_true.sum():.2%}")
    print("label base rate (train / test):")
    for label in LABELS:
        train = frame.loc[frame.split == "train", label].mean()
        test = frame.loc[frame.split == "test", label].mean()
        print(f"  {label:<14} {train:.3f} / {test:.3f}")
    print("days_to_empty quantiles:", frame.days_to_empty.quantile([0.25, 0.5, 0.75]).round(1).to_dict())


def main() -> None:
    master = pd.read_csv(MASTER_PATH)
    stock = load_stock()

    frame = add_features(stock, load_traffic())
    frame = add_labels(frame)
    frame = add_censoring(frame, load_true_demand(master))

    frame = frame.dropna(subset=FEATURES + [f"Y_empty_{max(HORIZONS)}"]).reset_index(drop=True)
    frame["split"] = np.where(frame.Date <= SPLIT_DATE, "train", "test")

    columns = (
        ["Date", "Outlet", "ItemID", "split"]
        + ["OpeningStock", "StockIn", "StockOut", "ClosingStock", "MinimumStock"]
        + STOCK_STATE
        + DEMAND
        + TRAFFIC
        + CALENDAR
        + LABELS
        + ["days_to_empty", "demand_true", "is_censored", "lost_units"]
    )
    frame = frame.loc[:, columns]
    check(frame, stock)

    frame["Date"] = frame.Date.dt.strftime("%Y-%m-%d")
    frame.to_csv(OUT_PATH, index=False)

    meta = {
        "version": "1.0.0",
        "source": ["Stock.csv", "Transactions.csv", "ItemMaster.csv"],
        "grain": "Outlet x ItemID x Date",
        "split": {"train_end": SPLIT_DATE.strftime("%Y-%m-%d"), "test_start": "2025-09-01", "rule": "Date <= train_end"},
        "features": FEATURES,
        "feature_groups": {
            "stock_state": STOCK_STATE,
            "demand": DEMAND,
            "traffic": TRAFFIC,
            "calendar": CALENDAR,
            "categorical": CATEGORICAL,
        },
        "labels": {
            "Y_empty_2": "ClosingStock reaches 0 within 2 days",
            "Y_empty_3": "ClosingStock reaches 0 within 3 days",
            "Y_empty_7": "ClosingStock reaches 0 within 7 days",
            "Y_belowmin_3": "ClosingStock drops below the constant MinimumStock within 3 days",
            "days_to_empty": f"first day with ClosingStock == 0, capped at {MAX_DAYS_TO_EMPTY}, NaN when none",
        },
        "diagnostics_not_features": ["demand_true", "is_censored", "lost_units", "days_to_empty"],
        "notes": (
            "Features use data up to and including day t; labels use days t+1..t+H. "
            "series_mean is the mean StockOut of the series over the TRAIN split only, so it is leak free for test rows. "
            "No lead time, outstanding order or adaptive reorder point is derived here: the dataset only uses the "
            "Stock.csv columns, so every feature is a recorded value. "
            "Demand features use the recorded StockOut, which is what an inventory system can observe. demand_true is the "
            "uncensored demand from Transactions.csv and is kept for diagnostics only: recorded sales understate real "
            "demand for the items whose ledger could not serve every sale. "
            "The last 7 days of every series are dropped because Y_empty_7 needs a complete forward window."
        ),
    }
    META_PATH.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(DATA_DIR.parents[1])} ({len(frame):,} rows) and {META_PATH.name}")


if __name__ == "__main__":
    main()
