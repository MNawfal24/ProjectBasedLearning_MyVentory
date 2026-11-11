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
        if not isinstance(self.estimator, dict) or "model" not in self.estimator:
            raise InvalidInputError("artefak sales_forecast tidak memuat bundle notebook", status_code=500, code="artifact_error")
        self.bundle = self.estimator
        self.feature_columns = list(self.bundle["feature_names"])
        self.history_values = [float(value) for value in self.bundle["history"]]
        self.last_date = dt.date.fromisoformat(str(self.bundle["last_date"])[:10])
        self.history_dates = [self.last_date - dt.timedelta(days=len(self.history_values) - index - 1) for index in range(len(self.history_values))]

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        horizon = int(payload["horizon_days"])
        history = list(self.history_values)

        predictions: list[dict[str, Any]] = []
        for _ in range(horizon):
            day = self.last_date + dt.timedelta(days=len(predictions) + 1)
            row = self._feature_row(history, day)
            value = max(0.0, float(self.bundle["model"].predict(row)[0]))
            history.append(value)
            predictions.append({"date": day, "predicted_net_sales": round(value, 2)})

        values = [point["predicted_net_sales"] for point in predictions]
        recent = list(zip(self.history_dates[-7:], self.history_values[-7:]))
        recent_total = float(sum(value for _, value in recent))
        recent_avg = recent_total / len(recent) if recent else 0.0
        predicted_avg = float(np.mean(values)) if values else 0.0
        change = ((predicted_avg - recent_avg) / recent_avg * 100) if recent_avg else 0.0

        return {
            "outlet": None,
            "currency": "IDR",
            "horizon_days": horizon,
            "history_end": self.last_date,
            "predictions": predictions,
            "summary": {
                "total_predicted_net_sales": round(float(sum(values)), 2),
                "average_daily_net_sales": round(predicted_avg, 2),
                "last_7_days_actual_net_sales": round(recent_total, 2),
                "change_vs_last_7_days_pct": round(change, 2),
            },
            "recent_history": [{"date": day, "net_sales": round(value, 2)} for day, value in recent],
        }

    def _feature_row(self, history: list[float], day: dt.date) -> pd.DataFrame:
        values = {f"lag{lag}": history[-lag] for lag in self.bundle["lags"]}
        values.update({"roll_mean_7": float(np.mean(history[-7:])), "roll_mean_14": float(np.mean(history[-14:])), "roll_mean_28": float(np.mean(history[-28:])), "roll_std_7": float(np.std(history[-7:]))})
        values.update({"dow": day.weekday(), "is_weekend": int(day.weekday() >= 5), "day": day.day, "month": day.month, "day_of_year": day.timetuple().tm_yday})
        return pd.DataFrame([[values[column] for column in self.feature_columns]], columns=self.feature_columns)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload["actuals"]
        evaluated: list[tuple[float, float, float]] = []
        skipped = 0
        for item in rows:
            day = item["date"]
            if day <= self.history_dates[FIRST_USABLE_OFFSET_DAYS] or day > self.last_date:
                skipped += 1
                continue
            index = self.history_dates.index(day)
            prediction = max(0.0, float(self.bundle["model"].predict(self._feature_row(self.history_values[:index], day))[0]))
            evaluated.append((float(item["net_sales"]), prediction, self.history_values[index - 7]))

        if not evaluated:
            raise InvalidInputError(
                "tidak ada baris yang bisa dievaluasi: tanggal harus berada di dalam rentang data historis model",
                details={"rows": len(rows), "history_range": [self.history_dates[0].isoformat(), self.last_date.isoformat()]},
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
