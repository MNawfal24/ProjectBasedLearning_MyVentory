"""Sales forecasting: one global daily NetSales model covering all outlets."""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
import pandas as pd

from app.errors import ArtifactError, InvalidInputError
from app.models.base import ArtifactModel
from app.models.common import regression_metrics

MODEL_ID = "sales_forecast"
TASK = "regression"
DESCRIPTION = "Prediksi total penjualan harian (NetSales) per outlet atau agregat semua outlet."
QUALITY_METRICS = ("mae", "rmse", "wape")

LAGS = (1, 7, 14, 28)
ROLLS = (7, 14, 28)
# lag_28/roll_std_28 need 28 previous days.
FIRST_USABLE_POSITION = 28


class SalesForecastModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        bundle = self.estimator
        if not isinstance(bundle, dict) or "obj" not in bundle or "history" not in bundle:
            raise ArtifactError("artefak sales_forecast bukan bundle model global")
        encoding = bundle.get("encoding")
        if encoding not in (None, "code"):
            raise ArtifactError("encoding outlet tidak didukung", details={"encoding": encoding})

        frame = bundle["history"]
        required = {"date", "outlet_id", "net_sales"}
        if not hasattr(frame, "columns") or not required.issubset(frame.columns):
            raise ArtifactError("history artefak harus berkolom date, outlet_id, net_sales")

        frame = frame[["date", "outlet_id", "net_sales"]].copy()
        frame["date"] = pd.to_datetime(frame["date"]).dt.date
        frame["outlet_id"] = frame["outlet_id"].astype(str)

        self.model = bundle["obj"]
        self.feature_columns = list(bundle.get("features") or [])
        if not self.feature_columns:
            raise ArtifactError("metadata artefak tidak memuat daftar fitur")

        self.outlets = [str(outlet) for outlet in bundle.get("outlets") or sorted(frame["outlet_id"].unique())]
        self.outlet_codes = {outlet: index for index, outlet in enumerate(self.outlets)}

        dates: list[dt.date] | None = None
        series: dict[str, list[float]] = {}
        for outlet in self.outlets:
            rows = frame[frame["outlet_id"] == outlet].sort_values("date")
            outlet_dates = list(rows["date"])
            if dates is None:
                dates = outlet_dates
            elif outlet_dates != dates:
                raise ArtifactError("tanggal history antar outlet tidak seragam", details={"outlet": outlet})
            series[outlet] = [float(value) for value in rows["net_sales"]]

        if not dates or len(dates) <= FIRST_USABLE_POSITION:
            raise ArtifactError("history terlalu pendek untuk membentuk lag 28 hari")
        self.dates = dates
        self.series = series
        self.last_date = dates[-1]

    def _feature_frame(self, outlet: str, values: list[float], day: dt.date) -> pd.DataFrame:
        features: dict[str, float] = {}
        for lag in LAGS:
            features[f"lag_{lag}"] = values[-lag]
        for window in ROLLS:
            recent = values[-window:]
            features[f"roll_mean_{window}"] = float(np.mean(recent))
            features[f"roll_std_{window}"] = float(np.std(recent, ddof=1))
        features.update(
            {
                "dow": day.weekday(),
                "is_weekend": int(day.weekday() >= 5),
                "day": day.day,
                "month": day.month,
                "day_of_year": day.timetuple().tm_yday,
                "week_of_year": day.isocalendar()[1],
                "outlet_id": self.outlet_codes[outlet],
            }
        )
        return pd.DataFrame([[features[column] for column in self.feature_columns]], columns=self.feature_columns)

    def _predict_one(self, outlet: str, values: list[float], day: dt.date) -> float:
        prediction = float(np.asarray(self.model.predict(self._feature_frame(outlet, values, day))).reshape(-1)[0])
        return max(0.0, prediction)

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        outlet = payload.get("outlet")
        if outlet is not None and outlet not in self.outlet_codes:
            raise InvalidInputError(
                f"outlet '{outlet}' tidak dikenal",
                details={"outlet": outlet, "known_outlets": self.outlets},
            )
        horizon = int(payload.get("horizon_days") or 7)
        scope = self.outlets if outlet is None else [outlet]
        histories = {name: list(self.series[name]) for name in scope}

        predictions: list[dict[str, Any]] = []
        for step in range(horizon):
            day = self.last_date + dt.timedelta(days=step + 1)
            total = 0.0
            for name in scope:
                value = self._predict_one(name, histories[name], day)
                histories[name].append(value)
                total += value
            predictions.append({"date": day, "predicted_net_sales": round(total, 2)})

        tail = self.dates[-7:]
        start = len(self.dates) - len(tail)
        recent_history = [
            {
                "date": day,
                "net_sales": round(float(sum(self.series[name][start + offset] for name in scope)), 2),
            }
            for offset, day in enumerate(tail)
        ]
        last_7 = float(sum(item["net_sales"] for item in recent_history))
        total_predicted = float(sum(item["predicted_net_sales"] for item in predictions))
        change_pct = None if last_7 == 0 else round((total_predicted - last_7) / last_7 * 100, 2)

        return {
            "model_id": self.model_id,
            "model_version": self.version,
            "outlet": outlet,
            "horizon_days": horizon,
            "history_end": self.last_date,
            "predictions": predictions,
            "summary": {
                "total_predicted_net_sales": round(total_predicted, 2),
                "average_daily_net_sales": round(total_predicted / horizon, 2),
                "last_7_days_actual_net_sales": round(last_7, 2),
                "change_vs_last_7_days_pct": change_pct,
            },
            "recent_history": recent_history,
        }

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        actuals: list[float] = []
        predictions: list[float] = []
        baselines: list[float] = []
        sample: list[dict[str, Any]] = []
        skipped = 0
        for item in payload["actuals"]:
            outlet = str(item["outlet"])
            day = item["date"]
            if outlet not in self.outlet_codes:
                skipped += 1
                continue
            try:
                position = self.dates.index(day)
            except ValueError:
                skipped += 1
                continue
            if position < FIRST_USABLE_POSITION:
                skipped += 1
                continue
            values = self.series[outlet][:position]
            prediction = self._predict_one(outlet, values, day)
            actual = float(item["net_sales"])
            baseline = float(values[position - 7])
            actuals.append(actual)
            predictions.append(prediction)
            baselines.append(baseline)
            if len(sample) < 10:
                sample.append(
                    {
                        "date": day,
                        "outlet": outlet,
                        "actual": round(actual, 2),
                        "predicted": round(prediction, 2),
                        "baseline": round(baseline, 2),
                    }
                )

        if not actuals:
            raise InvalidInputError(
                "tidak ada baris yang bisa dievaluasi",
                details={
                    "reason": "tanggal harus berada dalam history dan setelah 28 hari pertama",
                    "history_start": self.dates[0].isoformat(),
                    "history_end": self.last_date.isoformat(),
                },
            )

        actual = np.asarray(actuals, dtype=float)
        predicted = np.asarray(predictions, dtype=float)
        baseline = np.asarray(baselines, dtype=float)
        return {
            "rows_evaluated": len(actuals),
            "rows_skipped": skipped,
            "skipped_reason": None if skipped == 0 else "outlet tidak dikenal atau tanggal di luar rentang fitur",
            "metrics": regression_metrics(actual, predicted),
            "baseline_metrics": regression_metrics(actual, baseline),
            "sample": sample,
            "metric_note": "baseline_metrics memakai nilai aktual 7 hari sebelumnya (naive-7).",
        }
