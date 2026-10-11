"""Behaviour when model artefacts are missing or broken."""

from __future__ import annotations

from app.model_registry import MODEL_CLASSES, registry

EXPECTED_MODELS = set(MODEL_CLASSES)


def test_missing_artifacts_keep_the_app_alive(client, empty_artifacts):
    assert client.get("/api/v1/health").status_code == 200

    ready = client.get("/api/v1/ready")
    assert ready.status_code == 503
    body = ready.json()
    assert body["status"] == "not_ready"
    assert body["ready_models"] == []
    assert set(body["unavailable_models"]) == EXPECTED_MODELS
    for item in body["models"]:
        assert item["status"] == "unavailable"
        assert item["reason"]


def test_missing_artifacts_return_503_not_ready_with_reason(client, empty_artifacts):
    response = client.post("/api/v1/sales-forecast", json={"outlet": "SHOP001", "horizon_days": 2})
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "model_not_ready"
    assert body["error"]["details"]["reason"]
    assert body["request_id"] == response.headers["X-Request-Id"]


def test_model_list_reports_unavailable_without_quality_metrics(client, empty_artifacts):
    body = client.get("/api/v1/models").json()
    assert body["ready_models"] == 0
    for entry in body["models"]:
        assert entry["status"] == "unavailable"
        assert entry["quality"] is None
        assert entry["reason"]


def test_model_info_of_unavailable_model_returns_503(client, empty_artifacts):
    response = client.get("/api/v1/models/stock_prediction")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_not_ready"


def test_corrupt_artifact_is_isolated_to_that_model(client, broken_artifact):
    body = client.get("/api/v1/ready").json()
    statuses = {item["model_id"]: item for item in body["models"]}
    assert statuses["sales_forecast"]["status"] == "unavailable"
    assert "model.joblib" in statuses["sales_forecast"]["reason"]
    # the other models are untouched by the broken artefact
    assert registry.loaded("demand_forecast") is not None

    response = client.post("/api/v1/sales-forecast", json={"outlet": "SHOP001", "horizon_days": 2})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_not_ready"


def test_registry_marks_artifacts_without_metadata_as_unavailable(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    version = root / "segmentation" / "1.0.0"
    version.mkdir(parents=True)
    (version / "model.joblib").write_bytes(b"irrelevant")
    monkeypatch.setattr(registry, "artifacts_root", root)
    registry.load_all()
    try:
        assert registry.loaded("segmentation") is None
        assert "metadata.json" in registry.status("segmentation")["reason"]
    finally:
        monkeypatch.undo()
        registry.load_all()
