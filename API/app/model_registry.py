"""Model registry: loading the five models and reporting their readiness.

Every model loads independently from ``<artifacts_root>/<model_id>/<version>``.
A missing or broken artefact marks only that model ``unavailable`` (with the
reason) instead of preventing the application from starting.
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any

from app.config import settings
from app.errors import ApiError, ModelNotReadyError, UnknownModelError
from app.models.base import ArtifactModel
from app.models.demand_forecast import DemandForecastModel
from app.models.peak_hour import PeakHourModel
from app.models.sales_forecast import SalesForecastModel
from app.models.segmentation import SegmentationModel
from app.models.stock_prediction import StockPredictionModel

logger = logging.getLogger(__name__)

# The five models this API is contracted to serve, in documentation order.
MODEL_CLASSES: dict[str, type[ArtifactModel]] = {
    SalesForecastModel.model_id: SalesForecastModel,
    DemandForecastModel.model_id: DemandForecastModel,
    SegmentationModel.model_id: SegmentationModel,
    PeakHourModel.model_id: PeakHourModel,
    StockPredictionModel.model_id: StockPredictionModel,
}


class ModelRegistry:
    def __init__(self, artifacts_root: pathlib.Path | None = None) -> None:
        self.artifacts_root = pathlib.Path(artifacts_root or settings.artifacts_root)
        self._loaded: dict[str, ArtifactModel] = {}
        self._failures: dict[str, dict[str, Any]] = {}

    def load_all(self) -> None:
        """(Re)load every known model; a single broken artefact never raises."""
        self._loaded.clear()
        self._failures.clear()
        for model_id, model_class in MODEL_CLASSES.items():
            directory = self._latest_dir(model_id)
            if directory is None:
                self._failures[model_id] = {
                    "reason": "artefak belum tersedia",
                    "detail": f"tidak ada direktori model di {self.artifacts_root / model_id}",
                }
                logger.warning("model %s tidak tersedia: artefak tidak ditemukan", model_id)
                continue
            try:
                model = model_class(directory).load()
            except ApiError as exc:
                self._failures[model_id] = {"reason": exc.message, "detail": exc.details or {}}
                logger.error("model %s gagal dimuat: %s", model_id, exc.message)
            except Exception as exc:  # noqa: BLE001 - a broken artefact must not stop the app
                self._failures[model_id] = {"reason": "gagal memuat artefak", "detail": {"error": repr(exc)}}
                logger.exception("model %s gagal dimuat", model_id)
            else:
                self._loaded[model_id] = model
                logger.info("model %s v%s dimuat dari %s", model_id, model.version, directory)

    def _latest_dir(self, model_id: str) -> pathlib.Path | None:
        """Highest version directory that actually carries a model.joblib."""
        base = self.artifacts_root / model_id
        if not base.is_dir():
            return None
        candidates = [path for path in base.iterdir() if path.is_dir() and (path / "model.joblib").exists()]
        if not candidates:
            return None

        def sort_key(path: pathlib.Path) -> tuple:
            numeric = tuple(int(part) if part.isdigit() else 0 for part in path.name.split("."))
            return (numeric, path.name)

        return max(candidates, key=sort_key)

    def get(self, model_id: str) -> ArtifactModel:
        if model_id not in MODEL_CLASSES:
            raise UnknownModelError(f"model '{model_id}' tidak dikenal", details={"known_models": sorted(MODEL_CLASSES)})
        model = self._loaded.get(model_id)
        if model is None:
            raise ModelNotReadyError(
                f"model '{model_id}' belum siap menerima request",
                details=self._failures.get(model_id, {"reason": "artefak belum tersedia"}),
            )
        return model

    def status(self, model_id: str) -> dict[str, Any]:
        model = self._loaded.get(model_id)
        if model is not None:
            return {
                "model_id": model_id,
                "status": "ready",
                "model_version": model.version,
                "task": model.task,
                "description": model.description,
                "quality_metrics": list(model.quality_metrics),
            }
        model_class = MODEL_CLASSES.get(model_id)
        return {
            "model_id": model_id,
            "status": "unavailable",
            "model_version": None,
            "task": model_class.task if model_class else None,
            "description": model_class.description if model_class else None,
            "quality_metrics": [],
            "reason": self._failures.get(model_id, {}).get("reason", "artefak belum tersedia"),
        }

    def statuses(self) -> list[dict[str, Any]]:
        return [self.status(model_id) for model_id in MODEL_CLASSES]

    def loaded_ids(self) -> list[str]:
        return sorted(self._loaded)

    def loaded(self, model_id: str) -> ArtifactModel | None:
        """The loaded instance, or ``None`` when the model is not ready."""
        return self._loaded.get(model_id)

    def versions(self) -> dict[str, str]:
        return {model_id: model.version for model_id, model in self._loaded.items()}


registry = ModelRegistry()
