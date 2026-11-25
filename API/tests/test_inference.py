"""Inference tests against the real artefacts in API/artifacts.

These are not mock tests: every case here exercises the estimator loaded from
``API/artifacts``. Cases for unavailable models live in
``test_availability.py``.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest


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


def test_sales_forecast_supports_all_outlets_aggregate(client):
    require_ready(client, "sales_forecast")
    aggregate = client.post("/api/v1/sales-forecast", json={"outlet": None, "horizon_days": 3})
    assert aggregate.status_code == 200, aggregate.text
    body = aggregate.json()
    assert body["outlet"] is None
    per_outlet = sum(
        client.post("/api/v1/sales-forecast", json={"outlet": outlet, "horizon_days": 3}).json()["summary"]["total_predicted_net_sales"]
        for outlet in ("SHOP001", "SHOP002", "SHOP003")
    )
    assert body["summary"]["total_predicted_net_sales"] == pytest.approx(per_outlet, rel=1e-6)


def test_sales_forecast_magnitude_is_plausible_against_recent_actuals(client):
    require_ready(client, "sales_forecast")
    body = client.post("/api/v1/sales-forecast", json={"outlet": "SHOP001", "horizon_days": 7}).json()
    recent_avg = body["summary"]["last_7_days_actual_net_sales"] / 7
    predicted_avg = body["summary"]["average_daily_net_sales"]
    # the holdout WAPE of this model is ~0.05; a 4x band catches a broken feature path
    assert 0.25 * recent_avg < predicted_avg < 4 * recent_avg


def test_demand_forecast_returns_qty_and_reorder(client):
    require_ready(client, "demand_forecast")
    body = client.post(
        "/api/v1/demand-forecast",
        json={"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 4},
    ).json()
    assert len(body["predictions"]) == 4
    assert all(point["predicted_qty"] >= 0 for point in body["predictions"])
    expected_reorder = math.ceil(body["summary"]["total_predicted_qty"] / body["horizon_days"] * 7)
    assert body["summary"]["suggested_reorder_qty"] == pytest.approx(expected_reorder, abs=1)
    assert body["summary"]["unit_price_used"] == 0.0


def test_segmentation_assigns_labels_and_top_products(client):
    require_ready(client, "product_segmentation")
    body = client.post(
        "/api/v1/segmentation",
        json={"products": ["Chocolate (Gedhe)", "Friendly Coffee (Ice)"]},
    ).json()
    assert body["n_products"] == 2
    assert [item["product"] for item in body["assignments"]] == ["Chocolate (Gedhe)", "Friendly Coffee (Ice)"]
    for item in body["assignments"]:
        assert isinstance(item["cluster"], int)
        assert item["label"]
        assert item["distance_to_centroid"] >= 0
        assert item["profile"]
    assert sum(body["cluster_distribution"].values()) == 2
    assert body["clusters_reference"]
    assert set(body["top_products"]) == {"Best Seller", "Regular Seller", "Seasonal Product", "Slow Moving"}
    for products in body["top_products"].values():
        assert len(products) <= 5


def test_segmentation_ignores_batch_order(client):
    require_ready(client, "product_segmentation")
    low = "Chocolate (Gedhe)"
    high = "Friendly Coffee (Ice)"
    forward = client.post("/api/v1/segmentation", json={"products": [low, high]}).json()["assignments"]
    backward = client.post("/api/v1/segmentation", json={"products": [high, low]}).json()["assignments"]
    assert forward[0]["cluster"] == backward[1]["cluster"]
    assert forward[1]["cluster"] == backward[0]["cluster"]
