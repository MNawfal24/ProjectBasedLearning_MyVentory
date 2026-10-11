"""Evaluation endpoint tests driven by the real dataset in ML/data/Transactions.csv.

These exercise the labelled-evaluation path end to end: actuals are taken from
the dataset itself, so the reported metrics are computed from real observations.
"""

from __future__ import annotations

import datetime as dt
import pathlib

import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_PATH = REPO_ROOT / "ML" / "data" / "Transactions.csv"


@pytest.fixture(scope="module")
def transactions() -> pd.DataFrame:
    if not DATA_PATH.exists():
        pytest.skip("dataset Transactions.csv tidak tersedia")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["Date"]).dt.date
    return df


def require_ready(client, model_id: str) -> None:
    if model_id not in client.get("/api/v1/ready").json()["ready_models"]:
        pytest.skip(f"model {model_id} tidak tersedia pada artefak")


def test_sales_forecast_evaluation_on_real_actuals(client, transactions):
    require_ready(client, "sales_forecast")
    daily = transactions.groupby(["Outlet", "date"])["NetSales"].sum().reset_index()
    last_day = daily["date"].max()
    window = [last_day - dt.timedelta(days=offset) for offset in range(6, -1, -1)]
    actuals = [
        {"date": row.date.isoformat(), "outlet": row.Outlet, "net_sales": round(float(row.NetSales), 2)}
        for row in daily[daily["date"].isin(window)].itertuples()
    ]
    response = client.post("/api/v1/models/sales_forecast/evaluate", json={"actuals": actuals})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["model_id"] == "sales_forecast"
    assert body["rows_evaluated"] == len(actuals)
    assert body["rows_skipped"] == 0
    for key in ("mae", "rmse", "wape"):
        assert body["metrics"][key] >= 0
        assert body["baseline_metrics"][key] >= 0
    assert body["metrics"]["wape"] < 1.0, "model harus mengalahkan prediksi nol pada data uji"
    assert len(body["sample"]) == min(10, len(actuals))
    assert "in-sample" in body["note"]


def test_demand_forecast_evaluation_on_real_actuals(client, transactions):
    require_ready(client, "demand_forecast")
    lines = transactions[["Outlet", "date", "Items"]].copy()
    lines["product"] = lines["Items"].str.split(",")
    lines = lines.explode("product")
    lines["product"] = lines["product"].str.strip()
    top = lines["product"].value_counts().head(3).index.tolist()
    daily = lines.groupby(["Outlet", "product", "date"]).size().reset_index(name="qty")
    last_day = daily["date"].max()
    window = [last_day - dt.timedelta(days=offset) for offset in range(3, -1, -1)]
    subset = daily[daily["date"].isin(window) & daily["product"].isin(top)]
    actuals = [
        {"date": row.date.isoformat(), "outlet": row.Outlet, "product": row.product, "qty": float(row.qty)}
        for row in subset.itertuples()
    ]
    assert actuals, "tidak ada baris aktual untuk diuji"
    response = client.post("/api/v1/models/demand_forecast/evaluate", json={"actuals": actuals})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_evaluated"] == len(actuals)
    assert body["metrics"]["mae"] >= 0
    assert body["baseline_metrics"]["mae"] >= 0


def test_peak_hour_evaluation_on_real_actuals(client, transactions):
    require_ready(client, "peak_hour")
    hourly = transactions.groupby(["Outlet", "date", "Time"]).size().reset_index(name="tx_count")
    hourly["hour"] = hourly["Time"].str.slice(0, 2).astype(int)
    grouped = hourly.groupby(["Outlet", "date", "hour"]).agg(tx_count=("tx_count", "sum")).reset_index()
    last_day = grouped["date"].max()
    window = [last_day - dt.timedelta(days=offset) for offset in range(2, -1, -1)]
    subset = grouped[grouped["date"].isin(window)]
    actuals = [
        {"date": row.date.isoformat(), "outlet": row.Outlet, "hour": int(row.hour), "tx_count": float(row.tx_count)}
        for row in subset.itertuples()
    ]
    response = client.post("/api/v1/models/peak_hour/evaluate", json={"actuals": actuals, "peak_label": "reference"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_evaluated"] == len(actuals)
    assert body["peak_label"] == "reference"
    assert body["metrics"]["mae"] >= 0
    classification = body["metrics"]["classification"]
    assert {"precision", "recall", "f1", "support"} <= set(classification)
    assert classification["support"] > 0


def test_stock_evaluation_on_real_actuals(client, transactions):
    require_ready(client, "stock_prediction")
    lines = transactions[["Outlet", "date", "Items"]].copy()
    lines["product"] = lines["Items"].str.split(",")
    lines = lines.explode("product")
    lines["product"] = lines["product"].str.strip()
    top = lines["product"].value_counts().head(3).index.tolist()
    daily = lines.groupby(["Outlet", "product", "date"]).size().reset_index(name="qty")
    pivot = daily.pivot_table(index=["Outlet", "product", "date"], values="qty", aggfunc="sum").reset_index()
    last_day = pivot["date"].max()
    rows = []
    for row in pivot.itertuples():
        window_end = row.date + dt.timedelta(days=6)
        if window_end > last_day:
            continue
        rows.append((row.Outlet, row.product, row.date, window_end))
    frame = pivot.set_index(["Outlet", "product", "date"])["qty"]
    actuals = []
    for outlet, product, day, window_end in rows:
        if product not in top:
            continue
        total = 0.0
        for offset in range(7):
            key = (outlet, product, day + dt.timedelta(days=offset))
            if key in frame.index:
                total += float(frame.loc[key])
        actuals.append({"date": day.isoformat(), "outlet": outlet, "product": product, "required_stock": total})
    actuals = actuals[-60:]
    assert actuals, "tidak ada baris aktual untuk diuji"
    response = client.post("/api/v1/models/stock_prediction/evaluate", json={"actuals": actuals})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_evaluated"] == len(actuals)
    assert body["metrics"]["mae"] >= 0
    assert body["metrics"]["rmse"] >= 0
    assert "classification" in body["metrics"]


def test_stock_evaluation_baseline_uses_the_evaluated_rows_own_date(client, transactions):
    """A skipped row must not shift the naive lag-7 baseline onto a different date."""
    require_ready(client, "stock_prediction")
    series = (
        transactions[transactions["Outlet"] == "SHOP001"]
        .groupby(["date", "Items"])
        .size()
        .reset_index(name="qty")
    )
    series = series[series["Items"] == "Friendly Coffee (Ice)"].set_index("date")["qty"]
    last_day = series.index.max()
    lag7_value = float(series.get(last_day - dt.timedelta(days=7), 0.0))

    response = client.post(
        "/api/v1/models/stock_prediction/evaluate",
        json={
            "actuals": [
                # skipped: before the first usable date
                {"date": "2025-01-05", "outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "required_stock": 99.0},
                {"date": last_day.isoformat(), "outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "required_stock": 12.0},
            ]
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_evaluated"] == 1
    assert body["rows_skipped"] == 1
    # baseline for the single evaluated row is its own lag-7 daily qty scaled to the 7-day window
    assert body["baseline_metrics"]["mae"] == pytest.approx(abs(12.0 - lag7_value * 7), abs=0.01)


def test_peak_hour_evaluation_with_actual_labels_differs_from_reference(client, transactions):
    """'actual' derives busy labels from the submitted volumes, so scores must not be perfect."""
    require_ready(client, "peak_hour")
    hourly = transactions.groupby(["Outlet", "date", "Time"]).size().reset_index(name="tx_count")
    hourly["hour"] = hourly["Time"].str.slice(0, 2).astype(int)
    grouped = hourly.groupby(["Outlet", "date", "hour"]).agg(tx_count=("tx_count", "sum")).reset_index()
    last_day = grouped["date"].max()
    window = [last_day - dt.timedelta(days=offset) for offset in range(6, -1, -1)]
    subset = grouped[grouped["date"].isin(window)]
    actuals = [
        {"date": row.date.isoformat(), "outlet": row.Outlet, "hour": int(row.hour), "tx_count": float(row.tx_count)}
        for row in subset.itertuples()
    ]
    response = client.post("/api/v1/models/peak_hour/evaluate", json={"actuals": actuals, "peak_label": "actual"})
    assert response.status_code == 200, response.text
    classification = response.json()["metrics"]["classification"]
    assert classification["label_source"] == "p75 volume aktual pada data request"
    assert 0.0 <= classification["f1"] <= 1.0
    assert classification["support"] > 0


def test_stock_evaluation_reports_unavailable_classification_when_labels_missing(client, transactions):
    """A series without a stored risk threshold must report why classification is absent."""
    require_ready(client, "stock_prediction")
    lines = transactions[["Outlet", "date", "Items"]].copy()
    lines["product"] = lines["Items"].str.split(",")
    lines = lines.explode("product")
    lines["product"] = lines["product"].str.strip()
    top = lines["product"].value_counts().head(2).index.tolist()
    daily = lines.groupby(["Outlet", "product", "date"]).size().reset_index(name="qty")
    last_day = daily["date"].max()
    subset = daily[daily["date"].isin([last_day - dt.timedelta(days=offset) for offset in range(6, -1, -1)]) & daily["product"].isin(top)]
    actuals = [
        {"date": row.date.isoformat(), "outlet": row.Outlet, "product": row.product, "required_stock": float(row.qty)}
        for row in subset.itertuples()
    ]
    response = client.post("/api/v1/models/stock_prediction/evaluate", json={"actuals": actuals})
    assert response.status_code == 200, response.text
    metrics = response.json()["metrics"]
    assert "mae" in metrics and "wape" in metrics
    classification = metrics["classification"]
    if "available" in classification:
        assert classification["reason"]
    else:
        assert {"precision", "recall", "f1", "support"} <= set(classification)


def test_segmentation_evaluation_rejects_a_single_label(client, transactions):
    """Silhouette needs at least two clusters; a degenerate request must not invent a score."""
    require_ready(client, "segmentation")
    row = transactions.iloc[0]
    payload = {
        "transactions": [
            {
                "total_item": int(row.TotalItem),
                "total_amount": float(row.TotalAmount),
                "hour": int(str(row.Time)[:2]),
                "day_of_week": dt.date.fromisoformat(str(row.Date)).weekday(),
                "use_loyalty_card": bool(row.UseLoyaltyCard),
                "cluster": 0,
            }
            for _ in range(3)
        ]
    }
    response = client.post("/api/v1/models/segmentation/evaluate", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "evaluation_not_supported"
    assert "metrics" not in body


def test_segmentation_evaluation_on_real_transactions(client, transactions):
    require_ready(client, "segmentation")
    sample = transactions.head(200)
    payload = {
        "transactions": [
            {
                "total_item": int(row.TotalItem),
                "total_amount": float(row.TotalAmount),
                "hour": int(str(row.Time)[:2]),
                "day_of_week": dt.date.fromisoformat(str(row.Date)).weekday(),
                "use_loyalty_card": bool(row.UseLoyaltyCard),
            }
            for row in sample.itertuples()
        ]
    }
    response = client.post("/api/v1/models/segmentation/evaluate", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_evaluated"] == len(payload["transactions"])
    assert -1.0 <= body["metrics"]["silhouette"] <= 1.0
    assert body["metrics"]["davies_bouldin"] >= 0
    assert body["n_labels"] >= 2
