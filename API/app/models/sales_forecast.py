"""Sales forecasting: daily net sales per outlet.

HistGradientBoostingRegressor over calendar fields plus lag/rolling sales of the
same outlet. Multi-day horizons are recursive: each predicted day is appended to
a forked history so the next day's lags include it, mirroring training.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
import pandas as pd

from app.errors import InvalidInputError
from app.models.base import ArtifactModel
from app.models.common import HistoryIndex, calendar_features, lag_features, next_day, one_hot, ordered_row, regression_metrics

MODEL_ID = "sales_forecast"
TASK = "regression"
DESCRIPTION = "Prediksi total penjualan harian (NetSales) per outlet."
QUALITY_METRICS = ("mae", "rmse", "wape")

# Feature windows, matching ML/train/train_sales_forecast.py.
LAGS = (1, 7, 14, 28)
ROLLS = (7, 28)
HISTORY_FILE = "history"
FIRST_USABLE_OFFSET_DAYS = 27  # the first 28 days have incomplete lag28/roll28


class SalesForecastModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        history = self.extra.get(HISTORY_FILE)
        if history is None:
            raise InvalidInputError("artefak sales_forecast tidak memuat history.json", status_code=500, code="artifact_error")
        self.history = HistoryIndex(history)
        self.outlets: list[str] = list(self.metadata.get("categories", {}).get("outlet", []))
        self.feature_columns: list[str] = list(self.metadata.get("features", []))
        if not self.outlets or not self.feature_columns:
            raise InvalidInputError("metadata sales_forecast tidak lengkap", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        outlet = payload["outlet"]
        if outlet not in self.outlets:
            raise InvalidInputError(f"outlet '{outlet}' tidak dikenal model", details={"outlet": outlet, "allowed": self.outlets})
        horizon = int(payload["horizon_days"])
        history = self.history.fork()
        key = f"{outlet}|net_sales"

        predictions: list[dict[str, Any]] = []
        for _ in range(horizon):
            day = next_day(history)
            value = max(0.0, float(self.estimator.predict(self._feature_row(history, outlet, day, key))[0]))
            history.append(day, {key: value})
            predictions.append({"date": day, "predicted_net_sales": round(value, 2)})

        values = [point["predicted_net_sales"] for point in predictions]
        recent = self._recent(key, days=7)
        recent_total = float(sum(value for _, value in recent))
        recent_avg = recent_total / len(recent) if recent else 0.0
        predicted_avg = float(np.mean(values)) if values else 0.0
        change = ((predicted_avg - recent_avg) / recent_avg * 100) if recent_avg else 0.0

        return {
            "outlet": outlet,
            "currency": "IDR",
            "horizon_days": horizon,
            "history_end": self.history.last_date,
            "predictions": predictions,
            "summary": {
                "total_predicted_net_sales": round(float(sum(values)), 2),
                "average_daily_net_sales": round(predicted_avg, 2),
                "last_7_days_actual_net_sales": round(recent_total, 2),
                "change_vs_last_7_days_pct": round(change, 2),
            },
            "recent_history": [{"date": day, "net_sales": round(value, 2)} for day, value in recent],
        }

    def _feature_row(self, history: HistoryIndex, outlet: str, day: dt.date, key: str) -> pd.DataFrame:
        values: dict[str, float] = {}
        values.update(calendar_features(day))
        values.update(lag_features(history, key, day, LAGS, ROLLS))
        values.update(one_hot("outlet", outlet, self.outlets))
        return pd.DataFrame(ordered_row(values, self.feature_columns), columns=self.feature_columns)

    def _recent(self, key: str, days: int) -> list[tuple[dt.date, float]]:
        """Last ``days`` observed values, taken from the artefact history (not the forecast)."""
        return [
            (self.history.last_date - dt.timedelta(days=offset - 1), self.history.value(key, self.history.last_date - dt.timedelta(days=offset - 1)))
            for offset in range(days, 0, -1)
        ]

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload["actuals"]
        evaluated: list[tuple[float, float, float]] = []
        skipped = 0
        for item in rows:
            day, outlet = item["date"], item["outlet"]
            if outlet not in self.outlets or day <= self.history.first_date + dt.timedelta(days=FIRST_USABLE_OFFSET_DAYS) or day > self.history.last_date:
                skipped += 1
                continue
            key = f"{outlet}|net_sales"
            prediction = max(0.0, float(self.estimator.predict(self._feature_row(self.history, outlet, day, key))[0]))
            evaluated.append((float(item["net_sales"]), prediction, self.history.lag(key, day, 7)))

        if not evaluated:
            raise InvalidInputError(
                "tidak ada baris yang bisa dievaluasi: tanggal harus berada di dalam rentang data historis model",
                details={"rows": len(rows), "history_range": [self.history.first_date.isoformat(), self.history.last_date.isoformat()]},
            )

        actual = np.array([row[0] for row in evaluated])
        predicted = np.array([row[1] for row in evaluated])
        baseline = np.array([row[2] for row in evaluated])
        return {
            "rows_evaluated": len(evaluated),
            "rows_skipped": skipped,
            "skipped_reason": "outlet tidak dikenal atau tanggal di luar rentang fitur model" if skipped else None,
            "metrics": regression_metrics(actual, predicted),
            "baseline_metrics": regression_metrics(actual, baseline),
            "sample": [
                {"actual": round(a, 2), "predicted": round(p, 2), "baseline_lag7": round(b, 2)}
                for a, p, b in evaluated[:10]
            ],
        }
