"""Request validation, response contract and error handling for the five endpoints."""

from __future__ import annotations

import pytest

SALES = "/api/v1/sales-forecast"
DEMAND = "/api/v1/demand-forecast"
SEGMENTATION = "/api/v1/segmentation"
PEAK = "/api/v1/peak-hour"
STOCK = "/api/v1/stock-prediction"

VALID_SALES = {"outlet": "SHOP001", "horizon_days": 3}
VALID_DEMAND = {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 3}
VALID_SEGMENTATION = {"transactions": [{"total_item": 1, "total_amount": 23000, "hour": 8, "day_of_week": 3, "use_loyalty_card": False}]}
VALID_PEAK = {"outlet": "SHOP001"}
VALID_STOCK = {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 7, "available_stock": 5}


def require_ready(client, model_id: str) -> None:
    if model_id not in client.get("/api/v1/ready").json()["ready_models"]:
        pytest.skip(f"model {model_id} tidak tersedia pada artefak")


# Shared response envelope: same identity fields on every prediction endpoint.
@pytest.mark.parametrize(
    ("path", "payload", "model_id"),
    [
        (SALES, VALID_SALES, "sales_forecast"),
        (DEMAND, VALID_DEMAND, "demand_forecast"),
        (SEGMENTATION, VALID_SEGMENTATION, "segmentation"),
        (PEAK, VALID_PEAK, "peak_hour"),
        (STOCK, VALID_STOCK, "stock_prediction"),
    ],
)
def test_response_envelope_is_consistent(client, path, payload, model_id):
    require_ready(client, model_id)
    response = client.post(path, json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["model_id"] == model_id
    assert body["model_version"]
    assert body["task"]
    assert body["request_id"] == response.headers["X-Request-Id"]
    assert body["generated_at"]


# Bodies that must be rejected before any model runs.
@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (SALES, {}),
        (SALES, {"outlet": "SHOP001", "horizon_days": 0}),
        (SALES, {"outlet": "SHOP001", "horizon_days": 99}),
        (SALES, {"outlet": "SHOP001", "horizon_days": "tujuh"}),
        (SALES, {"outlet": "SHOP001", "horizon_days": 7, "unknown_field": 1}),
        (DEMAND, {"outlet": "SHOP001"}),
        (DEMAND, {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": -1}),
        (SEGMENTATION, {"transactions": []}),
        (SEGMENTATION, {"transactions": [{"total_item": 1}]}),
        (SEGMENTATION, {"transactions": [{"total_item": 1, "total_amount": 23000, "hour": 25, "day_of_week": 3}]}),
        (SEGMENTATION, {"transactions": [{"total_item": 1, "total_amount": 23000, "hour": 8, "day_of_week": 9}]}),
        (PEAK, {}),
        (PEAK, {"outlet": "SHOP001", "date": "bukan-tanggal"}),
        (STOCK, {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "available_stock": -5}),
    ],
)
def test_invalid_request_is_rejected_with_422_and_structured_body(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]["errors"]
    assert body["request_id"] == response.headers["X-Request-Id"]


@pytest.mark.parametrize(
    ("path", "payload", "model_id"),
    [
        (SALES, {"outlet": "SHOP999", "horizon_days": 2}, "sales_forecast"),
        (DEMAND, {"outlet": "SHOP001", "product": "Produk Tidak Ada", "horizon_days": 2}, "demand_forecast"),
        (STOCK, {"outlet": "SHOP999", "product": "Friendly Coffee (Ice)", "horizon_days": 2}, "stock_prediction"),
        (PEAK, {"outlet": "SHOP999"}, "peak_hour"),
    ],
)
def test_semantically_invalid_input_returns_422_invalid_input(client, path, payload, model_id):
    require_ready(client, model_id)
    response = client.post(path, json=payload)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "invalid_input"


def test_peak_hour_date_outside_supported_range_is_rejected(client):
    require_ready(client, "peak_hour")
    response = client.post(PEAK, json={"outlet": "SHOP001", "date": "2020-01-01"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert "allowed_range" in response.json()["error"]["details"]


def test_unknown_evaluate_model_returns_404(client):
    response = client.post("/api/v1/models/nope/evaluate", json={"actuals": []})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_model"


def test_evaluate_with_wrong_body_contract_returns_422(client):
    require_ready(client, "sales_forecast")
    response = client.post("/api/v1/models/sales_forecast/evaluate", json={"actuals": [{"date": "2025-09-01", "outlet": "SHOP001", "qty": 3}]})
    assert response.status_code == 422
    assert response.json()["error"]["code"] in ("invalid_input", "validation_error")


def test_evaluate_without_usable_rows_reports_422_not_fake_metrics(client):
    require_ready(client, "sales_forecast")
    response = client.post(
        "/api/v1/models/sales_forecast/evaluate",
        json={"actuals": [{"date": "2020-01-01", "outlet": "SHOP001", "net_sales": 1000}]},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_input"
    assert "metrics" not in body


def test_unknown_route_returns_structured_404(client):
    response = client.get("/api/v1/tidak-ada")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
