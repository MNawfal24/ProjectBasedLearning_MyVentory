"""Artefact contract for the five model modules.

Each model owns an artefact directory (``<model_id>[/<version>]/``) with
``model.pkl`` and ``metadata.json``. A broken artefact raises ``ArtifactError``
so the registry can mark that model unavailable instead of failing startup.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pickle

from app.errors import ArtifactError


class ArtifactModel:
    model_id: str = ""
    task: str = ""
    description: str = ""
    quality_metrics: tuple[str, ...] = ()

    def __init__(self, artifact_dir: pathlib.Path) -> None:
        self.artifact_dir = pathlib.Path(artifact_dir)
        self.version: str = self.artifact_dir.name
        self.metadata: dict[str, Any] = {}
        self.extra: dict[str, Any] = {}
        self.estimator: Any = None

    def load(self) -> "ArtifactModel":
        """Load metadata, side JSON files and the estimator; called once per process."""
        metadata_path = self.artifact_dir / "metadata.json"
        model_path = self.artifact_dir / "model.pkl"
        missing = [path.name for path in (metadata_path, model_path) if not path.exists()]
        if missing:
            raise ArtifactError(
                f"artefak tidak lengkap: {', '.join(missing)} tidak ditemukan",
                details={"artifact_dir": str(self.artifact_dir), "missing": missing},
            )
        try:
            self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ArtifactError(f"metadata.json tidak valid: {exc}", details={"artifact_dir": str(self.artifact_dir)}) from exc
        self.version = str(self.metadata.get("model_version", self.metadata.get("saved_model", {}).get("model_version", "1.0.0")))
        # side files (history.json, product_stats.json, clusters.json, ...) become self.extra[<stem>]
        for path in sorted(self.artifact_dir.glob("*.json")):
            if path.name != "metadata.json":
                self.extra[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        try:
            self.estimator = pickle.load(model_path.open("rb"))
        except Exception as exc:  # noqa: BLE001 - surfaced as a structured 503 for this model only
            raise ArtifactError(
                f"gagal memuat model.pkl: {exc}",
                details={"artifact_dir": str(self.artifact_dir)},
            ) from exc
        if not self.metadata.get("features") and isinstance(self.estimator, dict):
            self.metadata["features"] = self.estimator.get("feature_names", [])
        self._after_load()
        return self

    def _after_load(self) -> None:
        """Hook for subclasses that wire up side artefacts and validate metadata."""

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(f"evaluasi tidak didukung untuk model {self.model_id}")

    def info(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_version": self.version,
            "task": self.task,
            "description": self.description,
            "algorithm": self.metadata.get("algorithm"),
            "trained_at": self.metadata.get("trained_at"),
            "features": self.metadata.get("features", self.metadata.get("saved_model", {}).get("feature_names", [])),
            "quality_metrics": list(self.quality_metrics),
            "metrics": self.metadata.get("metrics", {}),
            "notes": self.metadata.get("notes"),
            "artifact_dir": str(self.artifact_dir),
            "artifacts": sorted(path.name for path in self.artifact_dir.iterdir() if path.is_file()),
        }
