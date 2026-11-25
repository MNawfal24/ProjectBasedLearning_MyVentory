"""Demand forecasting per product: SARIMA, ETS or Gradient Boosting per SKU."""

from __future__ import annotations

import datetime as dt
import math
import re
from typing import Any

import numpy as np
import pandas as pd

from app.errors import ArtifactError, EvaluationNotSupportedError, InvalidInputError
from app.models.base import ArtifactModel

MODEL_ID = "demand_forecast"
ARTIFACT_FOLDER = "demand_forecast_product"
TASK = "regression"
DESCRIPTION = "Prediksi jumlah unit terjual harian untuk satu produk."
QUALITY_METRICS = ("mae", "rmse", "wape")

# SARIMA/ETS/GBR models are stored per product; the notebook exports them under
# the historical folder name ``demand_forecast_product``.
FEATURE_PATTERNS = (
    (re.compile(r"lag_?(\d+)"), "lag"),
    (re.compile(r"roll_?mean_?(\d+)"), "roll_mean"),
    (re.compile(r"roll_?std_?(\d+)"), "roll_std"),
)


class DemandForecastModel(ArtifactModel):
    model_id = MODEL_ID
    artifact_folder = ARTIFACT_FOLDER
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        bundle = self.estimator
        if not isinstance(bundle, dict) or not bundle:
            raise ArtifactError("artefak demand_forecast harus berupa dict per produk")
        sample = next(iter(bundle.values()))
        if not isinstance(sample, dict) or "last_date" not in sample:
            raise ArtifactError("entri produk tidak memuat last_date")
        self.bundles: dict[str, dict[str, Any]] = {str(name): value for name, value in bundle.items()}
        self.products = list(self.bundles)
        self._last_dates = {name: pd.Timestamp(value["last_date"]).date() for name, value in self.bundles.items()}
        self.last_date = max(self._last_dates.values())

    @staticmethod
    def _history(bundle: dict[str, Any]) -> list[float]:
        raw = bundle.get("history")
        if raw is None and "model" in bundle:
            model = getattr(bundle["model"], "model", None)
            raw = getattr(model, "endog", None)
        if raw is None:
            return []
        return [float(value) for value in np.asarray(raw, dtype=float).reshape(-1)]

    def _gb_feature_frame(self, bundle: dict[str, Any], values: list[float], day: dt.date) -> pd.DataFrame:
        features: dict[str, float] = {f"lag_{lag}": values[-lag] for lag in bundle["lags"]}
        features["roll_mean_7"] = float(np.mean(values[-7:]))
        features["roll_mean_14"] = float(np.mean(values[-14:]))
        features["roll_mean_28"] = float(np.mean(values[-28:]))
        features["roll_std_7"] = float(np.std(values[-7:], ddof=1))
        features["dow"] = day.weekday()
        features["is_weekend"] = int(day.weekday() >= 5)
        features["day"] = day.day
        features["month"] = day.month
        features["day_of_year"] = day.timetuple().tm_yday

        row: list[float] = []
        for name in bundle["feature_names"]:
            if name in features:
                row.append(features[name])
                continue
            for pattern, kind in FEATURE_PATTERNS:
                match = pattern.fullmatch(name)
                if match:
                    window = int(match.group(1))
                    if kind == "lag":
                        row.append(values[-window])
                    elif kind == "roll_mean":
                        row.append(float(np.mean(values[-window:])))
                    else:
                        row.append(float(np.std(values[-window:], ddof=1)))
                    break
            else:
                raise ArtifactError("fitur Gradient Boosting tidak dikenali", details={"feature": name})
        return pd.DataFrame([row], columns=bundle["feature_names"])

    def _forecast(self, bundle: dict[str, Any], horizon: int) -> list[float]:
        if "params" in bundle:
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            result = SARIMAX(
                bundle["history"],
                order=tuple(bundle["order"]),
                seasonal_order=tuple(bundle["seasonal_order"]),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).smooth(bundle["params"])
            values = np.asarray(result.forecast(horizon), dtype=float)
        elif "lags" in bundle:
            values = []
            known = self._history(bundle)
            for step in range(horizon):
                day = pd.Timestamp(bundle["last_date"]).date() + dt.timedelta(days=step + 1)
                prediction = float(np.asarray(bundle["model"].predict(self._gb_feature_frame(bundle, known, day))).reshape(-1)[0])
                prediction = max(0.0, prediction)
                known.append(prediction)
                values.append(prediction)
            values = np.asarray(values, dtype=float)
        else:
            values = np.asarray(bundle["model"].forecast(horizon), dtype=float)
        return [max(0.0, float(value)) for value in np.asarray(values, dtype=float).reshape(-1)]

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        product = str(payload["product"])
        if product not in self.bundles:
            raise InvalidInputError(
                f"produk '{product}' tidak ada dalam artefak demand_forecast",
                details={"product": product, "n_products": len(self.products)},
            )
        horizon = int(payload.get("horizon_days") or 7)
        bundle = self.bundles[product]
        last_date = self._last_dates[product]
        values = self._forecast(bundle, horizon)

        predictions = [
            {
                "date": last_date + dt.timedelta(days=step + 1),
                "predicted_qty": round(float(value), 3),
                "predicted_revenue": 0.0,
            }
            for step, value in enumerate(values)
        ]

        history = self._history(bundle)
        count = len(history)
        recent_history: list[dict[str, Any]] = []
        if count:
            start = last_date - dt.timedelta(days=count - 1)
            for offset in range(max(0, count - 7), count):
                recent_history.append(
                    {"date": start + dt.timedelta(days=offset), "qty": round(history[offset], 3)}
                )

        total = float(sum(item["predicted_qty"] for item in predictions))
        average = total / horizon
        last_7 = float(sum(item["qty"] for item in recent_history))
        return {
            "model_id": self.model_id,
            "model_version": self.version,
            "outlet": payload.get("outlet"),
            "product": product,
            "horizon_days": horizon,
            "history_end": last_date,
            "predictions": predictions,
            "summary": {
                "total_predicted_qty": round(total, 3),
                "average_daily_qty": round(average, 3),
                "suggested_reorder_qty": math.ceil(average * 7),
                "last_7_days_actual_qty": round(last_7, 3),
                "unit_price_used": 0.0,
            },
            "recent_history": recent_history,
            "note": "predicted_revenue memakai harga 0 karena artefak tidak menyimpan harga per produk",
        }

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise EvaluationNotSupportedError(
            "evaluasi demand_forecast belum tersedia: model per produk disimpan sebagai model terlatih, bukan data uji",
            details={"products": len(self.products)},
        )
