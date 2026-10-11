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

MODEL_ID = "stock_prediction"
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
        if not isinstance(self.estimator, dict) or not {"regressor", "classifier"} <= set(self.estimator):
            raise InvalidInputError("artefak stock_prediction harus berisi komponen regressor dan classifier", status_code=500, code="artifact_error")
        if HISTORY_FILE not in self.extra or STATS_FILE not in self.extra:
            raise InvalidInputError(
                "artefak stock_prediction tidak lengkap (butuh history.json dan product_stats.json)",
                status_code=500,
                code="artifact_error",
            )
        self.history = HistoryIndex(self.extra[HISTORY_FILE])
        self.product_stats: dict[str, dict[str, float]] = self.extra[STATS_FILE]
        categories = self.metadata.get("categories", {})
        self.outlets: list[str] = list(categories.get("outlet", []))
        self.products: list[str] = list(categories.get("product", []))
        self.feature_columns: list[str] = list(self.metadata.get("features", []))
        self.risk_threshold = float(self.metadata.get("risk_threshold", DEFAULT_RISK_THRESHOLD))
        if not (self.outlets and self.products and self.feature_columns):
            raise InvalidInputError("metadata stock_prediction tidak lengkap", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        outlet, product = self._validate(payload["outlet"], payload["product"])
        horizon = int(payload["horizon_days"])
        available = float(payload.get("available_stock") or 0.0)
        stats = self._stats(outlet, product)
        unit_price = float(stats.get("avg_price", 0.0))
        key = f"{outlet}|{product}|qty"

        history = self.history.fork()
        points: list[dict[str, Any]] = []
        cumulative = 0.0
        risk_probability = 0.0
        for step in range(horizon):
            day = next_day(history)
            frame = self._feature_row(history, outlet, product, day, key)
            requirement = max(0.0, float(self.estimator["regressor"].predict(frame)[0]))
            daily_qty = requirement / REQUIREMENT_WINDOW
            if step == 0:
                # the classifier was trained on the 7-day requirement of the first predicted day
                risk_probability = float(self.estimator["classifier"].predict_proba(frame)[0][1])
            cumulative += daily_qty
            history.append(day, {key: daily_qty})
            points.append({"date": day, "predicted_qty": round(daily_qty, 3), "cumulative_required_qty": round(cumulative, 3)})

        required = float(sum(point["predicted_qty"] for point in points))
        return {
            "outlet": outlet,
            "product": product,
            "horizon_days": horizon,
            "history_end": self.history.last_date,
            "predictions": points,
            "summary": {
                "required_stock": round(required, 3),
                "suggested_reorder_qty": float(math.ceil(max(0.0, required - available))),
                "estimated_available_stock": round(available, 3),
                "stockout_risk": bool(risk_probability >= self.risk_threshold),
                "stockout_probability": round(risk_probability, 4),
                "risk_threshold": self.risk_threshold,
                "historical_p75_daily_qty": round(float(stats.get("p75_qty", 0.0)), 3),
                "historical_p95_daily_qty": round(float(stats.get("p95_qty", 0.0)), 3),
                "unit_price_used": round(unit_price, 2),
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
        from sklearn.metrics import f1_score, precision_score, recall_score

        actual: list[float] = []
        predicted: list[float] = []
        baseline: list[float] = []
        probabilities: list[float] = []
        actual_risk: list[int] = []
        risk_support_available = True
        skipped = 0

        for item in payload["actuals"]:
            day, outlet, product = item["date"], item["outlet"], item["product"]
            if outlet not in self.outlets or product not in self.products:
                skipped += 1
                continue
            if day <= self.history.first_date + dt.timedelta(days=FIRST_USABLE_OFFSET_DAYS) or day > self.history.last_date:
                skipped += 1
                continue
            # risk_p75_required_stock is the train-period p75 of the 7-day requirement for this series
            threshold = float(self._stats(outlet, product).get("risk_p75_required_stock", 0.0))
            risk_support_available = risk_support_available and threshold > 0
            key = f"{outlet}|{product}|qty"
            frame = self._feature_row(self.history, outlet, product, day, key)
            value = float(item["required_stock"])
            actual.append(value)
            predicted.append(max(0.0, float(self.estimator["regressor"].predict(frame)[0])))
            baseline.append(self.history.lag(key, day, 7) * REQUIREMENT_WINDOW)
            probabilities.append(float(self.estimator["classifier"].predict_proba(frame)[0][1]))
            actual_risk.append(int(value > threshold) if threshold > 0 else 0)

        if not actual:
            raise InvalidInputError(
                "tidak ada baris yang bisa dievaluasi: outlet/produk harus dikenal dan tanggal dalam rentang historis model",
                details={"rows": len(payload["actuals"])},
            )

        a, p, b = (np.array(values) for values in (actual, predicted, baseline))
        metrics: dict[str, float | dict] = regression_metrics(a, p)
        if risk_support_available and len(set(actual_risk)) > 1:
            flags = [int(probability >= self.risk_threshold) for probability in probabilities]
            metrics["classification"] = {
                "precision": round(float(precision_score(actual_risk, flags, zero_division=0)), 4),
                "recall": round(float(recall_score(actual_risk, flags, zero_division=0)), 4),
                "f1": round(float(f1_score(actual_risk, flags, zero_division=0)), 4),
                "support": int(sum(actual_risk)),
                "risk_threshold": self.risk_threshold,
                "label_source": "kebutuhan stok aktual > p75 kebutuhan 7 hari data latih per series",
            }
        else:
            metrics["classification"] = {
                "available": 0.0,
                "reason": "label risiko tidak dapat dibentuk: ambang p75 series tidak tersedia atau hanya satu kelas pada data yang dikirim",
            }

        return {
            "rows_evaluated": len(actual),
            "rows_skipped": skipped,
            "skipped_reason": "outlet/produk tidak dikenal atau tanggal di luar rentang fitur model" if skipped else None,
            "metrics": metrics,
            "baseline_metrics": mae_rmse(a, b),
            "sample": [
                {"actual": round(x, 3), "predicted": round(y, 3), "stockout_probability": round(z, 4)}
                for x, y, z in list(zip(actual, predicted, probabilities))[:10]
            ],
        }
