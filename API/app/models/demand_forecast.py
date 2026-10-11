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
        if HISTORY_FILE not in self.extra or STATS_FILE not in self.extra:
            raise InvalidInputError(
                "artefak demand_forecast tidak lengkap (butuh history.json dan product_stats.json)",
                status_code=500,
                code="artifact_error",
            )
        self.history = HistoryIndex(self.extra[HISTORY_FILE])
        self.product_stats: dict[str, dict[str, float]] = self.extra[STATS_FILE]
        categories = self.metadata.get("categories", {})
        self.outlets: list[str] = list(categories.get("outlet", []))
        self.products: list[str] = list(categories.get("product", []))
        self.feature_columns: list[str] = list(self.metadata.get("features", []))
        if not (self.outlets and self.products and self.feature_columns):
            raise InvalidInputError("metadata demand_forecast tidak lengkap", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        outlet, product = self._validate(payload["outlet"], payload["product"])
        horizon = int(payload["horizon_days"])
        history = self.history.fork()
        key = f"{outlet}|{product}|qty"
        unit_price = float(self._stats(outlet, product).get("avg_price", 0.0))

        predictions: list[dict[str, Any]] = []
        for _ in range(horizon):
            day = next_day(history)
            qty = max(0.0, float(self.estimator.predict(self._feature_row(history, outlet, product, day, key))[0]))
            history.append(day, {key: qty})
            predictions.append({"date": day, "predicted_qty": round(qty, 3), "predicted_revenue": round(qty * unit_price, 2)})

        total = float(sum(point["predicted_qty"] for point in predictions))
        recent = [self.history.value(key, self.history.last_date - dt.timedelta(days=offset)) for offset in range(6, -1, -1)]
        return {
            "outlet": outlet,
            "product": product,
            "currency": "IDR",
            "horizon_days": horizon,
            "history_end": self.history.last_date,
            "predictions": predictions,
            "summary": {
                "total_predicted_qty": round(total, 3),
                "average_daily_qty": round(total / horizon, 3),
                "suggested_reorder_qty": float(math.ceil(total)),
                "unit_price_used": round(unit_price, 2),
                "last_7_days_actual_qty": round(float(sum(recent)), 3),
            },
            "recent_history": [
                {"date": self.history.last_date - dt.timedelta(days=offset), "qty": round(value, 3)}
                for offset, value in zip(range(6, -1, -1), recent)
            ],
        }

    def _validate(self, outlet: str, product: str) -> tuple[str, str]:
        if outlet not in self.outlets:
            raise InvalidInputError(f"outlet '{outlet}' tidak dikenal model", details={"allowed": self.outlets})
        if product not in self.products:
            raise InvalidInputError(
                f"produk '{product}' tidak dikenal model",
                details={"hint": "gunakan salah satu nama dari GET /api/v1/models/demand_forecast", "total_products": len(self.products)},
            )
        return outlet, product

    def _stats(self, outlet: str, product: str) -> dict[str, float]:
        return self.product_stats.get(f"{outlet}|{product}", {})

    def _feature_row(self, history: HistoryIndex, outlet: str, product: str, day: dt.date, key: str) -> pd.DataFrame:
        values: dict[str, float] = {}
        values.update(calendar_features(day))
        values.update(lag_features(history, key, day, LAGS, ROLLS))
        values["product_avg"] = float(self._stats(outlet, product).get("avg_qty", 0.0))
        values.update(one_hot("outlet", outlet, self.outlets))
        return pd.DataFrame(ordered_row(values, self.feature_columns), columns=self.feature_columns)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        actual: list[float] = []
        predicted: list[float] = []
        baseline: list[float] = []
        skipped = 0
        for item in payload["actuals"]:
            day, outlet, product = item["date"], item["outlet"], item["product"]
            if outlet not in self.outlets or product not in self.products:
                skipped += 1
                continue
            if day <= self.history.first_date + dt.timedelta(days=FIRST_USABLE_OFFSET_DAYS) or day > self.history.last_date:
                skipped += 1
                continue
            key = f"{outlet}|{product}|qty"
            frame = self._feature_row(self.history, outlet, product, day, key)
            actual.append(float(item["qty"]))
            predicted.append(max(0.0, float(self.estimator.predict(frame)[0])))
            baseline.append(self.history.lag(key, day, 7))

        if not actual:
            raise InvalidInputError(
                "tidak ada baris yang bisa dievaluasi: outlet/produk harus dikenal dan tanggal berada di rentang historis model",
                details={"rows": len(payload["actuals"])},
            )

        a, p, b = (np.array(values) for values in (actual, predicted, baseline))
        return {
            "rows_evaluated": len(actual),
            "rows_skipped": skipped,
            "skipped_reason": "outlet/produk tidak dikenal atau tanggal di luar rentang fitur model" if skipped else None,
            "metrics": regression_metrics(a, p),
            "baseline_metrics": regression_metrics(a, b),
            "sample": [
                {"actual": round(x, 3), "predicted": round(y, 3), "baseline_lag7": round(z, 3)}
                for x, y, z in zip(actual, predicted, baseline)
            ][:10],
        }
