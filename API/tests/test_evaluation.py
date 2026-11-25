"""Evaluation endpoint tests driven by the real dataset and stored segmentation."""

from __future__ import annotations

import datetime as dt
import pathlib

import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_PATH = REPO_ROOT / "ML" / "data" / "Transactions.csv"
SEGMENTS_PATH = REPO_ROOT / "API" / "artifacts" / "product_segmentation" / "1.0.0" / "product_segments.csv"


@pytest.fixture(scope="module")
def transactions() -> pd.DataFrame:
    if not DATA_PATH.exists():
        pytest.skip("dataset Transactions.csv tidak tersedia")
    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["Date"]).dt.date
    return df


@pytest.fixture(scope="module")
def segment_products() -> list[str]:
    if not SEGMENTS_PATH.exists():
        pytest.skip("product_segments.csv tidak tersedia")
    return pd.read_csv(SEGMENTS_PATH)["product"].head(30).tolist()


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


def test_demand_forecast_evaluation_is_explicitly_unsupported(client):
    require_ready(client, "demand_forecast")
    response = client.post(
        "/api/v1/models/demand_forecast/evaluate",
        json={"actuals": [{"date": "2025-09-30", "outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "qty": 10}]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "evaluation_not_supported"


def test_segmentation_evaluation_rejects_a_single_label(client, segment_products):
    """Silhouette needs at least two clusters; a degenerate request must not invent a score."""
    require_ready(client, "product_segmentation")
    payload = {"products": [segment_products[0]] * 3}
    response = client.post("/api/v1/models/product_segmentation/evaluate", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "evaluation_not_supported"
    assert "metrics" not in body


def test_segmentation_evaluation_on_stored_products(client, segment_products):
    require_ready(client, "product_segmentation")
    response = client.post("/api/v1/models/product_segmentation/evaluate", json={"products": segment_products})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_evaluated"] == len(segment_products)
    assert -1.0 <= body["metrics"]["silhouette"] <= 1.0
    assert body["metrics"]["davies_bouldin"] >= 0
    assert 0.0 <= body["metrics"]["label_agreement"] <= 1.0
    assert body["n_labels"] >= 2
