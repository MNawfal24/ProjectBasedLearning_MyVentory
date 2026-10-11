"""Technical metric consistency tests (in-memory, per process)."""

from __future__ import annotations

import pytest

from app.metrics import metrics_store

SALES = "/api/v1/sales-forecast"


@pytest.fixture(autouse=True)
def clean_metrics(client):
    metrics_store.reset()
    yield
    metrics_store.reset()


def test_summary_counts_requests_and_separates_models(client):
    if "sales_forecast" not in client.get("/api/v1/ready").json()["ready_models"]:
        pytest.skip("model sales_forecast tidak tersedia")
    for _ in range(3):
        assert client.post(SALES, json={"outlet": "SHOP001", "horizon_days": 2}).status_code == 200
    client.get("/api/v1/health")

    summary = client.get("/api/v1/metrics/").json()["summary"]
    assert summary["requests"] >= 4
    assert summary["success"] >= 4
    assert summary["failure"] == 0
    assert summary["error_rate"] == 0.0
    assert summary["inferences"] == 3
    assert summary["latency_ms"]["avg"] > 0
    assert summary["latency_ms"]["p50"] <= summary["latency_ms"]["p95"]
    assert "1.0.0" in summary["model_versions"]

    by_model = {row["model_id"]: row for row in client.get("/api/v1/metrics/").json()["by_model"]}
    assert by_model["sales_forecast"]["inferences"] == 3
    assert by_model["sales_forecast"]["model_versions"] == {"1.0.0": 3}


def test_failures_are_counted_with_their_status_code(client):
    if "sales_forecast" not in client.get("/api/v1/ready").json()["ready_models"]:
        pytest.skip("model sales_forecast tidak tersedia")
    client.post(SALES, json={"outlet": "SHOP999", "horizon_days": 2})  # 422
    client.post(SALES, json={"outlet": "SHOP001", "horizon_days": 99})  # 422 validation

    by_model = {row["model_id"]: row for row in client.get("/api/v1/metrics/models").json()["by_model"]}
    sales = by_model["sales_forecast"]
    assert sales["technical"]["failure"] == 1
    assert sales["technical"]["status_codes"]["422"] == 1
    assert sales["technical"]["inferences"] == 0


def test_endpoint_view_covers_non_model_routes(client):
    client.get("/api/v1/health")
    client.get("/api/v1/models")
    if "sales_forecast" in client.get("/api/v1/ready").json()["ready_models"]:
        client.post(SALES, json={"outlet": "SHOP001", "horizon_days": 2})
    endpoints = {row["endpoint"] for row in client.get("/api/v1/metrics/").json()["by_endpoint"]}
    assert "/api/v1/health" in endpoints
    assert "/api/v1/models" in endpoints
    if "sales_forecast" in client.get("/api/v1/ready").json()["ready_models"]:
        assert SALES in endpoints


def test_model_metrics_are_attributed_per_model_and_endpoint(client):
    ready = client.get("/api/v1/ready").json()["ready_models"]
    if "peak_hour" not in ready:
        pytest.skip("model peak_hour tidak tersedia")
    client.post("/api/v1/peak-hour", json={"outlet": "SHOP001"})
    payload = client.get("/api/v1/metrics/models/peak_hour").json()
    assert payload["model_id"] == "peak_hour"
    assert payload["model_version"]
    assert payload["technical"]["inferences"] == 1
    assert [row["endpoint"] for row in payload["endpoints"]] == ["predict"]


def test_quality_metrics_are_reported_separately_from_technical_metrics(client):
    body = client.get("/api/v1/metrics/models").json()
    sales = next(row for row in body["by_model"] if row["model_id"] == "sales_forecast")
    if sales["status"] != "ready":
        pytest.skip("model sales_forecast tidak tersedia")
    assert {"mae", "rmse", "wape"} <= set(sales["quality"])
    assert "latency_ms" in sales["technical"]
    assert "latency_ms" not in sales["quality"]


def test_reset_clears_counters(client):
    client.get("/api/v1/health")
    assert client.get("/api/v1/metrics/").json()["summary"]["requests"] > 0
    assert client.post("/api/v1/metrics/reset").status_code == 200
    summary = client.get("/api/v1/metrics/").json()["summary"]
    assert summary["requests"] == 1  # only the summary request itself after the reset
    assert summary["inferences"] == 0
