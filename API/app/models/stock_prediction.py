"""Stock prediction: required stock over a horizon plus a stock-out risk flag.

The artefact holds a regressor for ``required_stock_7d`` (units needed over the
next seven days for one outlet x product) and a classifier for a **proxy**
stock-out risk label. The source dataset has no stock level, stock-out flag or
reorder point, so the risk label describes demand pace, not recorded stock-outs.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import numpy as np
import pandas as pd

from app.errors import InvalidInputError
from app.models.base import ArtifactModel
from app.models.common import (
    HistoryIndex,
    calendar_features,
    lag_features,
    mae_rmse,
    next_day,
    one_hot,
    ordered_row,
    regression_metrics,
)

MODEL_ID = "stock_depletion"
TASK = "regression+classification"
DESCRIPTION = "Prediksi kebutuhan stok per outlet dan produk serta risiko kekurangan stok (label proxy)."
QUALITY_METRICS = ("mae", "rmse", "wape", "precision", "recall", "f1")

# Feature windows, matching ML/train/train_stock_prediction.py.
LAGS = (7, 14, 28)
ROLLS = (7, 28)
REQUIREMENT_WINDOW = 7  # the regressor target is a 7-day requirement
FIRST_USABLE_OFFSET_DAYS = 27  # the first 28 days have incomplete lag28/roll28
DEFAULT_RISK_THRESHOLD = 0.5
HISTORY_FILE = "history"
STATS_FILE = "product_stats"

PROXY_LABEL_NOTE = (
    "Label risiko stock-out adalah PROXY: bernilai 1 bila kebutuhan stok 7 hari ke depan melebihi persentil 75 "
    "kebutuhan 7 hari series tersebut pada data latih (yaitu 'produk ini bergerak lebih cepat dari kebiasaannya'). "
    "Dataset sumber tidak memuat level stok, flag stock-out, atau reorder point, sehingga label ini bukan kejadian "
    "stock-out yang tercatat."
)


class StockPredictionModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        if not isinstance(self.estimator, dict) or not {"models", "state", "horizon_days"} <= set(self.estimator):
            raise InvalidInputError("artefak stock_depletion tidak memuat bundle notebook", status_code=500, code="artifact_error")
        self.bundle = self.estimator
        self.state = self.bundle["state"]
        self.outlets = sorted(self.state.Outlet.unique().tolist())
        self.products = sorted(self.state.ItemID.unique().tolist())
        self.product_names = {}
        if "ProductName" in self.state.columns:
            self.product_names = dict(zip(self.state.ItemID, self.state.ProductName))
        self.risk_threshold = DEFAULT_RISK_THRESHOLD
        if not self.outlets or not self.products:
            raise InvalidInputError("metadata stock_prediction tidak lengkap", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        outlet = payload.get("outlet") or self.outlets[0]
        product = payload["product"]
        if product not in self.products:
            matches = [item_id for item_id, name in self.product_names.items() if name == product]
            if len(matches) == 1:
                product = matches[0]
        self._validate(outlet, product)
        horizon = min(int(payload["horizon_days"]), int(self.bundle["horizon_days"]))
        available = float(payload.get("available_stock") or 0.0)
        row = self.state[(self.state.Outlet == outlet) & (self.state.ItemID == product)].iloc[0]
        model = self.bundle["models"][f"{outlet}|{product}"]
        forecast = np.clip(np.asarray(model.forecast(int(self.bundle["horizon_days"])), dtype=float), 0, None)
        points: list[dict[str, Any]] = []
        cumulative = 0.0
        for step in range(horizon):
            day = dt.date.fromisoformat(str(self.metadata.get("period", {}).get("end", self.bundle["last_date"]))[:10]) + dt.timedelta(days=step + 1)
            daily_qty = float(forecast[step])
            cumulative += daily_qty
            points.append({"date": day, "predicted_qty": round(daily_qty, 3), "cumulative_required_qty": round(cumulative, 3)})

        required = float(sum(point["predicted_qty"] for point in points))
        return {
            "outlet": outlet,
            "product": payload["product"],
            "horizon_days": horizon,
            "history_end": dt.date.fromisoformat(str(self.metadata.get("period", {}).get("end", self.bundle["last_date"]))[:10]),
            "predictions": points,
            "summary": {
                "required_stock": round(required, 3),
                "suggested_reorder_qty": float(math.ceil(max(0.0, required - available))),
                "estimated_available_stock": round(available, 3),
                "stockout_risk": bool(row.days_to_min <= 3),
                "stockout_probability": 1.0 if row.days_to_min <= 3 else 0.0,
                "risk_threshold": self.risk_threshold,
                "historical_p75_daily_qty": 0.0,
                "historical_p95_daily_qty": 0.0,
                "unit_price_used": 0.0,
            },
            "proxy_label": PROXY_LABEL_NOTE,
        }

    def _validate(self, outlet: str, product: str) -> tuple[str, str]:
        if outlet not in self.outlets:
            raise InvalidInputError(f"outlet '{outlet}' tidak dikenal model", details={"allowed": self.outlets})
        if product not in self.products:
            raise InvalidInputError(
                f"produk '{product}' tidak dikenal model",
                details={"hint": "gunakan salah satu nama dari GET /api/v1/models/stock_prediction", "total_products": len(self.products)},
            )
        return outlet, product

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise InvalidInputError("evaluasi tidak tersedia untuk artefak stock_depletion notebook", status_code=422, code="invalid_input")
        raise InvalidInputError("evaluasi tidak tersedia untuk artefak stock_depletion notebook", status_code=422, code="invalid_input")
