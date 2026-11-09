"""Test configuration: a temp artefacts root so tests never touch ML/artifacts."""

from __future__ import annotations

import json
import pathlib
import shutil
import sys

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "API"))

from app.config import settings  # noqa: E402
from app.metrics import metrics_store  # noqa: E402
from app.main import create_app  # noqa: E402
from app.model_registry import registry  # noqa: E402

REAL_ARTIFACTS = REPO_ROOT / "ML" / "artifacts"


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Client backed by the real artefact directory (models are trained in-repo)."""
    settings.artifacts_root = REAL_ARTIFACTS
    registry.artifacts_root = REAL_ARTIFACTS
    metrics_store.reset()
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def empty_artifacts(tmp_path, monkeypatch) -> pathlib.Path:
    """Point the registry at an empty directory to exercise the 'model unavailable' path."""
    root = tmp_path / "artifacts"
    root.mkdir()
    monkeypatch.setattr(settings, "artifacts_root", root)
    monkeypatch.setattr(registry, "artifacts_root", root)
    registry.load_all()
    metrics_store.reset()
    yield root
    monkeypatch.undo()
    registry.load_all()


@pytest.fixture
def broken_artifact(tmp_path, monkeypatch) -> pathlib.Path:
    """Copy every real artefact, then corrupt one model.joblib to test load-failure isolation."""
    root = tmp_path / "artifacts"
    root.mkdir()
    if not (REAL_ARTIFACTS / "sales_forecast").is_dir():
        pytest.skip("artefak sales_forecast tidak tersedia")
    for source in REAL_ARTIFACTS.iterdir():
        if source.is_dir():
            shutil.copytree(source, root / source.name)
    version_dir = next(path for path in (root / "sales_forecast").iterdir() if path.is_dir())
    (version_dir / "model.joblib").write_bytes(b"not-a-pickle")
    monkeypatch.setattr(settings, "artifacts_root", root)
    monkeypatch.setattr(registry, "artifacts_root", root)
    registry.load_all()
    metrics_store.reset()
    yield root
    monkeypatch.undo()
    registry.load_all()


def artifact_dir(model_id: str) -> pathlib.Path:
    base = REAL_ARTIFACTS / model_id
    versions = sorted(path for path in base.iterdir() if path.is_dir())
    return versions[-1]


def read_metadata(model_id: str) -> dict:
    return json.loads((artifact_dir(model_id) / "metadata.json").read_text(encoding="utf-8"))
