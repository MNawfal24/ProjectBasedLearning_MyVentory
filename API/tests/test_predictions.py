"""Request validation, response contract and error handling for the three endpoints."""

from __future__ import annotations

import pytest

SALES = "/api/v1/sales-forecast"
DEMAND = "/api/v1/demand-forecast"
SEGMENTATION = "/api/v1/segmentation"

VALID_SALES = {"outlet": "SHOP001", "horizon_days": 3}
VALID_DEMAND = {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 3}
VALID_SEGMENTATION = {"products": ["Chocolate (Gedhe)"]}


def require_ready(client, model_id: str) -> None:
    if model_id not in client.get("/api/v1/ready").json()["ready_models"]:
        pytest.skip(f"model {model_id} tidak tersedia pada artefak")


# Shared response envelope: same identity fields on every prediction endpoint.
@pytest.mark.parametrize(
    ("path", "payload", "model_id"),
    [
        (SALES, VALID_SALES, "sales_forecast"),
        (DEMAND, VALID_DEMAND, "demand_forecast"),
        (SEGMENTATION, VALID_SEGMENTATION, "product_segmentation"),
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
        (DEMAND, {}),
        (DEMAND, {"outlet": "SHOP001"}),
        (DEMAND, {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": -1}),
        (SEGMENTATION, {}),
        (SEGMENTATION, {"products": []}),
        (SEGMENTATION, {"products": "Chocolate (Gedhe)"}),
        (SEGMENTATION, {"products": ["Chocolate (Gedhe)"], "unknown_field": 1}),
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
        (SEGMENTATION, {"products": ["Produk Tidak Ada"]}, "product_segmentation"),
    ],
)
def test_semantically_invalid_input_returns_422_invalid_input(client, path, payload, model_id):
    require_ready(client, model_id)
    response = client.post(path, json=payload)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "invalid_input"


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
