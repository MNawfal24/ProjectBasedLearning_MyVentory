"""Inference tests against the real artefacts produced by ML/train.

These are not mock tests: every case here exercises the estimator loaded from
``ML/artifacts``. Cases for unavailable models live in
``test_model_availability.py`` and are explicitly mock-based.
"""

from __future__ import annotations

import datetime as dt

import pytest

HOURS = list(range(7, 23))


def require_ready(client, model_id: str) -> None:
    if model_id not in client.get("/api/v1/ready").json()["ready_models"]:
        pytest.skip(f"model {model_id} tidak tersedia pada artefak")


def test_sales_forecast_is_deterministic_and_ordered(client):
    require_ready(client, "sales_forecast")
    payload = {"outlet": "SHOP001", "horizon_days": 5}
    first = client.post("/api/v1/sales-forecast", json=payload).json()
    second = client.post("/api/v1/sales-forecast", json=payload).json()

    assert [point["predicted_net_sales"] for point in first["predictions"]] == [
        point["predicted_net_sales"] for point in second["predictions"]
    ]
    dates = [dt.date.fromisoformat(point["date"]) for point in first["predictions"]]
    assert dates[0] == dt.date.fromisoformat(first["history_end"]) + dt.timedelta(days=1)
    assert dates == sorted(dates)
    assert len(dates) == 5
    assert all(point["predicted_net_sales"] > 0 for point in first["predictions"])
    assert len(first["recent_history"]) == 7
    assert first["summary"]["total_predicted_net_sales"] == pytest.approx(
        sum(point["predicted_net_sales"] for point in first["predictions"]), rel=1e-6
    )


def test_sales_forecast_magnitude_is_plausible_against_recent_actuals(client):
    require_ready(client, "sales_forecast")
    body = client.post("/api/v1/sales-forecast", json={"outlet": "SHOP001", "horizon_days": 7}).json()
    recent_avg = body["summary"]["last_7_days_actual_net_sales"] / 7
    predicted_avg = body["summary"]["average_daily_net_sales"]
    # the holdout WAPE of this model is ~0.14; a 4x band catches a broken feature path
    assert 0.25 * recent_avg < predicted_avg < 4 * recent_avg


def test_demand_forecast_returns_qty_revenue_and_reorder(client):
    require_ready(client, "demand_forecast")
    body = client.post(
        "/api/v1/demand-forecast",
        json={"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 4},
    ).json()
    assert len(body["predictions"]) == 4
    assert all(point["predicted_qty"] >= 0 for point in body["predictions"])
    assert body["summary"]["suggested_reorder_qty"] == pytest.approx(
        __import__("math").ceil(body["summary"]["total_predicted_qty"]), abs=1
    )
    assert body["summary"]["unit_price_used"] > 0


def test_segmentation_assigns_clusters_with_labels(client):
    require_ready(client, "segmentation")
    body = client.post(
        "/api/v1/segmentation",
        json={
            "transactions": [
                {"total_item": 1, "total_amount": 20000, "hour": 8, "day_of_week": 0, "use_loyalty_card": False},
                {"total_item": 2, "total_amount": 55000, "hour": 20, "day_of_week": 5, "use_loyalty_card": True},
            ]
        },
    ).json()
    assert body["n_transactions"] == 2
    assert [item["index"] for item in body["assignments"]] == [0, 1]
    for item in body["assignments"]:
        assert isinstance(item["cluster"], int)
        assert item["label"]
        assert item["distance_to_centroid"] >= 0
    assert sum(body["cluster_distribution"].values()) == 2
    assert body["clusters_reference"]


def test_segmentation_ignores_batch_order(client):
    require_ready(client, "segmentation")
    low = {"total_item": 1, "total_amount": 20000, "hour": 8, "day_of_week": 0, "use_loyalty_card": False}
    high = {"total_item": 2, "total_amount": 55000, "hour": 20, "day_of_week": 5, "use_loyalty_card": True}
    forward = client.post("/api/v1/segmentation", json={"transactions": [low, high]}).json()["assignments"]
    backward = client.post("/api/v1/segmentation", json={"transactions": [high, low]}).json()["assignments"]
    assert forward[0]["cluster"] == backward[1]["cluster"]
    assert forward[1]["cluster"] == backward[0]["cluster"]


def test_peak_hour_covers_all_business_hours(client):
    require_ready(client, "peak_hour")
    body = client.post("/api/v1/peak-hour", json={"outlet": "SHOP002"}).json()
    assert body["hours_covered"] == HOURS
    assert [point["hour"] for point in body["predictions"]] == HOURS
    assert body["date"] == (dt.date.fromisoformat(body["history_end"]) + dt.timedelta(days=1)).isoformat()
    assert all(point["predicted_tx_count"] >= 0 for point in body["predictions"])
    assert all(0.0 <= point["peak_probability"] <= 1.0 for point in body["predictions"])
    assert body["summary"]["peak_hours"], "model harus menandai minimal satu jam sibuk"
    assert body["summary"]["busiest_hour"] in HOURS
    assert body["summary"]["reference_peak_hours"]
    assert body["summary"]["predicted_total_tx"] == pytest.approx(
        sum(point["predicted_tx_count"] for point in body["predictions"]), rel=1e-6
    )


def test_peak_hour_is_stable_for_the_same_outlet_and_date(client):
    require_ready(client, "peak_hour")
    payload = {"outlet": "SHOP003"}
    first = client.post("/api/v1/peak-hour", json=payload).json()
    second = client.post("/api/v1/peak-hour", json=payload).json()
    assert first["summary"] == second["summary"]


def test_stock_prediction_reports_requirement_and_proxy_risk(client):
    require_ready(client, "stock_prediction")
    body = client.post(
        "/api/v1/stock-prediction",
        json={"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 7, "available_stock": 3},
    ).json()
    assert len(body["predictions"]) == 7
    cumulative = [point["cumulative_required_qty"] for point in body["predictions"]]
    assert cumulative == sorted(cumulative)
    summary = body["summary"]
    assert summary["required_stock"] == pytest.approx(cumulative[-1], rel=1e-3)
    assert summary["suggested_reorder_qty"] == pytest.approx(max(0.0, summary["required_stock"] - 3), abs=1)
    assert 0.0 <= summary["stockout_probability"] <= 1.0
    assert summary["risk_threshold"] > 0
    assert isinstance(summary["stockout_risk"], bool)
    assert "PROXY" in body["proxy_label"]


def test_stock_reorder_uses_available_stock(client):
    require_ready(client, "stock_prediction")
    base = {"outlet": "SHOP002", "product": "Lemons", "horizon_days": 7}
    none_available = client.post("/api/v1/stock-prediction", json={**base, "available_stock": 0}).json()["summary"]
    plenty_available = client.post("/api/v1/stock-prediction", json={**base, "available_stock": 1000}).json()["summary"]
    assert plenty_available["suggested_reorder_qty"] == 0
    assert none_available["suggested_reorder_qty"] >= 0
    assert none_available["required_stock"] == pytest.approx(plenty_available["required_stock"], rel=1e-3)
