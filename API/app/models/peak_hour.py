"""Peak-hour prediction: hourly receipt volume plus a busy-hour classifier.

Two estimators share one feature matrix. ``prev_hour`` comes from the regressor's
own output within the day, and the 07:00 hour uses hour 22 of the previous day -
the same imputation as training. The busy label is a property of the hour of day,
so the classifier score is near perfect by construction; see ``peak_label``.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
import pandas as pd

from app.errors import InvalidInputError
from app.models.base import ArtifactModel
from app.models.common import HistoryIndex, calendar_features, mae_rmse, one_hot, ordered_row

MODEL_ID = "peak_hour"
TASK = "regression+classification"
DESCRIPTION = "Prediksi volume transaksi per jam dan penentuan jam sibuk per outlet."
QUALITY_METRICS = ("mae", "rmse", "precision", "recall", "f1")

# Operating hours covered by the model, matching ML/train/train_peak_hour.py.
HOURS = list(range(7, 23))
FIRST_HOUR = HOURS[0]
HOUR_END = HOURS[-1]
MAX_HORIZON_DAYS = 14  # lag7/lag14 stop being meaningful further out
PEAK_PROBABILITY_THRESHOLD = 0.5
HISTORY_FILE = "history"
FIRST_USABLE_OFFSET_DAYS = 13  # the first 14 days have incomplete lag14


class PeakHourModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        if not isinstance(self.estimator, dict) or not {"model", "history", "feature_names", "outlets", "hour_range"} <= set(self.estimator):
            raise InvalidInputError("artefak peak_hour tidak memuat bundle notebook", status_code=500, code="artifact_error")
        self.bundle = self.estimator
        self.outlets = list(self.bundle["outlets"])
        self.feature_columns = list(self.bundle["feature_names"])
        self.hours = list(range(self.bundle["hour_range"][0], self.bundle["hour_range"][1] + 1))
        self.history = self.bundle["history"]
        self.last_date = dt.date.fromisoformat(str(self.bundle["last_date"])[:10])
        if not self.outlets or not self.feature_columns:
            raise InvalidInputError("metadata peak_hour tidak lengkap", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        outlet = payload.get("outlet") or self.outlets[0]
        if outlet not in self.outlets:
            raise InvalidInputError(f"outlet '{outlet}' tidak dikenal model", details={"allowed": self.outlets})
        target = payload.get("date") or (self.last_date + dt.timedelta(days=1))
        if isinstance(target, str):
            target = dt.date.fromisoformat(target)
        first_allowed = self.last_date + dt.timedelta(days=1)
        last_allowed = self.last_date + dt.timedelta(days=MAX_HORIZON_DAYS)
        if target < first_allowed or target > last_allowed:
            raise InvalidInputError(
                "tanggal di luar rentang prediksi model",
                details={"date": target.isoformat(), "allowed_range": [first_allowed.isoformat(), last_allowed.isoformat()]},
            )

        predictions = []
        subset = self.history[self.history.Outlet == outlet]
        for hour in self.hours:
            values = subset[subset.Hour == hour].sort_values("Date").net_sales.to_numpy(dtype=float)
            frame = self._feature_row(outlet, target, hour, float(values[-1]))
            volume = max(0.0, float(self.bundle["model"].predict(frame)[0]))
            predictions.append(
                {
                    "hour": hour,
                    "predicted_net_sales": round(volume, 3),
                    "predicted_tx_count": round(volume, 3),
                    "is_peak": bool(hour in self._reference_peak_hours(outlet)),
                    "peak_probability": 1.0 if hour in self._reference_peak_hours(outlet) else 0.0,
                }
            )

        busiest = max(predictions, key=lambda item: item["predicted_net_sales"])
        volumes = [item["predicted_net_sales"] for item in predictions]
        return {
            "outlet": outlet,
            "date": target,
            "history_end": self.last_date,
            "hours_covered": self.hours,
            "predictions": predictions,
            "summary": {
                "busiest_hour": busiest["hour"],
                "busiest_hour_predicted_net_sales": busiest["predicted_net_sales"],
                "busiest_hour_predicted_tx_count": busiest["predicted_net_sales"],
                "peak_hours": [item["hour"] for item in predictions if item["is_peak"]],
                "predicted_total_net_sales": round(float(sum(volumes)), 3),
                "average_net_sales_per_hour": round(float(np.mean(volumes)), 3),
                "predicted_total_tx": round(float(sum(volumes)), 3),
                "average_tx_per_hour": round(float(np.mean(volumes)), 3),
                "reference_peak_hours": self._reference_peak_hours(outlet),
            },
        }

    def _feature_row(self, outlet: str, day: dt.date, hour: int, previous_hour_value: float) -> pd.DataFrame:
        subset = self.history[(self.history.Outlet == outlet) & (self.history.Hour == hour)].sort_values("Date").net_sales.to_numpy(dtype=float)
        features = {"Hour": hour, "dow": day.weekday(), "is_weekend": int(day.weekday() >= 5), "month": day.month, "day_of_year": day.timetuple().tm_yday, "hour_sin": np.sin(2 * np.pi * hour / 24), "hour_cos": np.cos(2 * np.pi * hour / 24), "outlet_code": int(outlet[-1]), "outlet_hour_mean": float(subset.mean()), "lag_1d": float(subset[-1]), "lag_7d": float(subset[-7]), "roll_7": float(subset[-7:].mean()), "roll_28": float(subset.mean())}
        return pd.DataFrame([[features[column] for column in self.feature_columns]], columns=self.feature_columns)

    def _reference_peak_hours(self, outlet: str) -> list[int]:
        averages = self.history[self.history.Outlet == outlet].groupby("Hour").net_sales.mean()
        return [int(hour) for hour in averages.nlargest(3).index]

    def _observed_prev_hour(self, outlet: str, day: dt.date, hour: int) -> float:
        """Observed volume of the previous hour, imputing hour 7 from 22:00 the day before."""
        if hour == FIRST_HOUR:
            return self.history.value(f"{outlet}|hour|{HOUR_END}|tx_count", day, 1)
        return self.history.value(f"{outlet}|hour|{hour - 1}|tx_count", day)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise InvalidInputError("evaluasi tidak tersedia untuk artefak peak_hour notebook", status_code=422, code="invalid_input")
        from sklearn.metrics import f1_score, precision_score, recall_score

        actual: list[float] = []
        predicted: list[float] = []
        baseline: list[float] = []
        actual_peak: list[int] = []
        predicted_peak: list[int] = []
        skipped = 0
        label_mode = payload.get("peak_label", "actual")

        for item in payload["actuals"]:
            day, outlet, hour = item["date"], item["outlet"], int(item["hour"])
            if outlet not in self.outlets or hour not in HOURS:
                skipped += 1
                continue
            if day <= self.history.first_date + dt.timedelta(days=FIRST_USABLE_OFFSET_DAYS) or day > self.history.last_date:
                skipped += 1
                continue
            key = f"{outlet}|hour|{hour}|tx_count"
            frame = self._feature_row(outlet, day, hour, self._observed_prev_hour(outlet, day, hour))
            actual.append(float(item["tx_count"]))
            predicted.append(max(0.0, float(self.estimator["regressor"].predict(frame)[0])))
            baseline.append(self.history.lag(key, day, 7))
            predicted_peak.append(int(float(self.estimator["classifier"].predict_proba(frame)[0][1]) >= PEAK_PROBABILITY_THRESHOLD))
            # in "actual" mode the busy label is only known once every submitted hour is in
            actual_peak.append(int(hour in set(self.peak_hours.get(outlet, []))) if label_mode == "reference" else 0)

        if not actual:
            raise InvalidInputError(
                "tidak ada baris yang bisa dievaluasi: outlet/jam harus dikenal dan tanggal dalam 14 hari terakhir data historis",
                details={"rows": len(payload["actuals"])},
            )

        a, p, b = (np.array(values) for values in (actual, predicted, baseline))
        if label_mode == "actual":
            threshold = float(np.percentile(a, 75))
            actual_peak = [int(value >= threshold) for value in actual]

        return {
            "rows_evaluated": len(actual),
            "rows_skipped": skipped,
            "skipped_reason": "outlet/jam tidak dikenal atau tanggal di luar rentang fitur model" if skipped else None,
            "peak_label": label_mode,
            "metrics": {
                **mae_rmse(a, p),
                "classification": {
                    "precision": round(float(precision_score(actual_peak, predicted_peak, zero_division=0)), 4),
                    "recall": round(float(recall_score(actual_peak, predicted_peak, zero_division=0)), 4),
                    "f1": round(float(f1_score(actual_peak, predicted_peak, zero_division=0)), 4),
                    "support": int(sum(actual_peak)),
                    "label_source": "p75 volume aktual pada data request" if label_mode == "actual" else "jam sibuk profil data latih",
                },
            },
            "baseline_metrics": mae_rmse(a, b),
            "sample": [
                {"actual": round(x, 3), "predicted": round(y, 3), "baseline_lag7": round(z, 3)}
                for x, y, z in zip(actual, predicted, baseline)
            ][:10],
        }
