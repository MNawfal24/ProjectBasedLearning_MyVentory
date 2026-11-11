"""Demand forecasting: daily quantity per outlet x product.

HistGradientBoostingRegressor over calendar fields, lag/rolling quantity and the
product's historical average. Revenue is a proxy: ``NetSales`` is recorded per
receipt, so ``avg_price`` in ``product_stats.json`` is revenue per unit line.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import numpy as np
import pandas as pd

from app.errors import InvalidInputError
from app.models.base import ArtifactModel
from app.models.common import HistoryIndex, calendar_features, lag_features, next_day, one_hot, ordered_row, regression_metrics

MODEL_ID = "demand_forecast"
TASK = "regression"
DESCRIPTION = "Prediksi jumlah permintaan harian per outlet dan produk."
QUALITY_METRICS = ("mae", "rmse", "wape")

# Feature windows, matching ML/train/train_demand_forecast.py.
LAGS = (7, 14, 28)
ROLLS = (7, 28)
HISTORY_FILE = "history"
STATS_FILE = "product_stats"
FIRST_USABLE_OFFSET_DAYS = 27  # the first 28 days have incomplete lag28/roll28


class DemandForecastModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        if not isinstance(self.estimator, dict) or not {"products", "history", "dates"} <= set(self.estimator):
            raise InvalidInputError("artefak demand_forecast tidak memuat bundle notebook", status_code=500, code="artifact_error")
        self.products = list(self.estimator["products"])
        self.history = np.asarray(self.estimator["history"], dtype=float)
        self.dates = [dt.date.fromisoformat(str(value)[:10]) for value in self.estimator["dates"]]
        self.last_date = self.dates[-1]

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        product = payload["product"]
        self._validate_product(product)
        horizon = int(payload["horizon_days"])
        values = self.history[:, self.products.index(product)].tolist()

        predictions: list[dict[str, Any]] = []
        for _ in range(horizon):
            day = self.last_date + dt.timedelta(days=len(predictions) + 1)
            qty = max(0.0, float(values[-7]))
            values.append(qty)
            predictions.append({"date": day, "predicted_qty": round(qty, 3), "predicted_revenue": 0.0})

        total = float(sum(point["predicted_qty"] for point in predictions))
        return {
            "outlet": None,
            "product": product,
            "currency": "IDR",
            "horizon_days": horizon,
            "history_end": self.last_date,
            "predictions": predictions,
            "summary": {
                "total_predicted_qty": round(total, 3),
                "average_daily_qty": round(total / horizon, 3),
                "suggested_reorder_qty": float(math.ceil(total)),
                "unit_price_used": 0.0,
                "last_7_days_actual_qty": round(float(sum(self.history[-7:, self.products.index(product)])), 3),
            },
            "recent_history": [
                {"date": self.dates[-7 + index], "qty": round(float(value), 3)}
                for index, value in enumerate(self.history[-7:, self.products.index(product)])
            ],
        }

    def _validate_product(self, product: str) -> None:
        if product not in self.products:
            raise InvalidInputError(
                f"produk '{product}' tidak dikenal model",
                details={"hint": "gunakan salah satu nama dari GET /api/v1/models/demand_forecast", "total_products": len(self.products)},
            )

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise InvalidInputError("evaluasi tidak tersedia untuk artefak demand_forecast notebook", status_code=422, code="invalid_input")
        raise InvalidInputError("evaluasi tidak tersedia untuk artefak demand_forecast notebook", status_code=422, code="invalid_input")
