"""Health, readiness and model inventory tests."""

from __future__ import annotations

from app.model_registry import MODEL_CLASSES

EXPECTED_MODELS = {"sales_forecast", "demand_forecast", "segmentation", "peak_hour", "stock_prediction"}


def test_model_ids_match_contract():
    assert set(MODEL_CLASSES) == EXPECTED_MODELS


def test_health_is_ok_and_carries_request_id(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["request_id"] == response.headers["X-Request-Id"]
    assert body["api_version"]


def test_health_echoes_incoming_request_id(client):
    response = client.get("/api/v1/health", headers={"X-Request-Id": "trace-123"})
    assert response.headers["X-Request-Id"] == "trace-123"
    assert response.json()["request_id"] == "trace-123"


def test_ready_lists_all_five_models_with_status(client):
    response = client.get("/api/v1/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert {item["model_id"] for item in body["models"]} == EXPECTED_MODELS
    for item in body["models"]:
        assert item["status"] in ("ready", "unavailable")
        if item["status"] == "ready":
            assert item["model_version"]
            assert item["quality_metrics"]
        else:
            assert item["reason"]


def test_ready_reports_loaded_models_and_status_code_matches(client):
    body = client.get("/api/v1/ready").json()
    ready = [item["model_id"] for item in body["models"] if item["status"] == "ready"]
    assert body["ready_models"] == ready
    expected_status = 200 if ready else 503
    assert client.get("/api/v1/ready").status_code == expected_status


def test_models_endpoint_lists_status_and_quality(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    body = response.json()
    assert body["total_models"] == 5
    assert body["ready_models"] == len([m for m in body["models"] if m["status"] == "ready"])
    for entry in body["models"]:
        assert {"model_id", "status", "task", "quality", "trained_at"} <= set(entry)


def test_model_info_returns_identity_features_and_metrics(client):
    response = client.get("/api/v1/models/sales_forecast")
    assert response.status_code == 200
    body = response.json()
    assert body["model_id"] == "sales_forecast"
    assert body["model_version"]
    assert body["features"]
    assert body["algorithm"]
    assert "model.joblib" in body["artifacts"]
    assert body["metrics"]


def test_unknown_model_info_returns_404_structured_error(client):
    response = client.get("/api/v1/models/does_not_exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "unknown_model"
    assert body["request_id"] == response.headers["X-Request-Id"]
    assert "sales_forecast" in body["error"]["details"]["known_models"]


def test_openapi_documents_every_prediction_endpoint(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    for path in (
        "/api/v1/sales-forecast",
        "/api/v1/demand-forecast",
        "/api/v1/segmentation",
        "/api/v1/peak-hour",
        "/api/v1/stock-prediction",
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/models",
        "/api/v1/models/{model_id}",
        "/api/v1/models/{model_id}/evaluate",
        "/api/v1/metrics/",
        "/api/v1/metrics/models",
    ):
        assert path in paths, path
    assert "/api/v1/models/{model_id}/evaluate" in paths
