"""Shared inference helpers: the history store, feature builders and metrics.

These exist because multi-day forecasts rebuild lag features at request time.
They must stay in sync with the training scripts in ``ML/train``: the column order
in ``metadata.json -> features`` is what the estimator expects, and every value
mirrors the training-time construction.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Sequence

import numpy as np


class HistoryIndex:
    """Daily series from ``history.json``: ``{"dates": [...], "series": {"<key>": [...]}}``."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.dates: list[dt.date] = [dt.date.fromisoformat(d) for d in payload["dates"]]
        if not self.dates:
            raise ValueError("history.json tidak memiliki tanggal")
        self.series: dict[str, list[float]] = {key: [float(v) for v in values] for key, values in payload["series"].items()}
        self._position = {day: index for index, day in enumerate(self.dates)}

    @property
    def first_date(self) -> dt.date:
        return self.dates[0]

    @property
    def last_date(self) -> dt.date:
        return self.dates[-1]

    def fork(self) -> "HistoryIndex":
        """Copy, so one request can append predicted days without mutating shared state."""
        clone = HistoryIndex.__new__(HistoryIndex)
        clone.dates = list(self.dates)
        clone.series = {key: list(values) for key, values in self.series.items()}
        clone._position = dict(self._position)
        return clone

    def value(self, key: str, day: dt.date, days_back: int = 0) -> float:
        """Value at ``day - days_back``; days outside the stored range count as 0."""
        target = day - dt.timedelta(days=days_back)
        position = self._position.get(target)
        if position is None:
            return 0.0
        series = self.series.get(key, [])
        return series[position] if position < len(series) else 0.0

    def lag(self, key: str, day: dt.date, steps: int) -> float:
        return self.value(key, day, steps)

    def rolling_mean(self, key: str, day: dt.date, window: int) -> float:
        """Mean over the ``window`` days strictly before ``day``, matching training."""
        values = [self.value(key, day, step) for step in range(1, window + 1)]
        return sum(values) / len(values)

    def append(self, day: dt.date, values: dict[str, float]) -> None:
        """Append a predicted day; keys absent from ``values`` carry the last value forward."""
        if day != self.last_date + dt.timedelta(days=1):
            raise ValueError(f"hari {day} tidak berurutan setelah {self.last_date}")
        self.dates.append(day)
        self._position[day] = len(self.dates) - 1
        for key, series in self.series.items():
            series.append(float(values[key]) if key in values else (series[-1] if series else 0.0))
        for key, value in values.items():
            if key not in self.series:
                self.series[key] = [0.0] * (len(self.dates) - 1) + [float(value)]


def next_day(history: HistoryIndex) -> dt.date:
    return history.last_date + dt.timedelta(days=1)


def calendar_features(day: dt.date) -> dict[str, float]:
    return {
        "dow": day.weekday(),
        "day": day.day,
        "month": day.month,
        "is_weekend": int(day.weekday() >= 5),
    }


def lag_features(history: HistoryIndex, key: str, day: dt.date, lags: Sequence[int], rolls: Sequence[int]) -> dict[str, float]:
    values: dict[str, float] = {}
    for lag in lags:
        values[f"lag{lag}"] = history.lag(key, day, lag)
    for window in rolls:
        values[f"roll{window}"] = history.rolling_mean(key, day, window)
    return values


def one_hot(prefix: str, value: str, categories: Sequence[str]) -> dict[str, float]:
    return {f"{prefix}_{candidate}": int(candidate == value) for candidate in categories}


def ordered_row(values: dict[str, float], columns: Sequence[str]) -> list[list[float]]:
    """Project a feature dict onto the model's column order."""
    missing = [column for column in columns if column not in values]
    if missing:
        raise KeyError(f"fitur hilang: {missing}")
    return [[values[column] for column in columns]]


def mae_rmse(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": round(float(np.mean(np.abs(actual - predicted))), 4),
        "rmse": round(float(np.sqrt(np.mean((actual - predicted) ** 2))), 4),
    }


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """MAE/RMSE plus WAPE; WAPE is NaN when the actuals sum to zero."""
    total = float(np.abs(actual).sum())
    wape = round(float(np.abs(actual - predicted).sum() / total), 4) if total else float("nan")
    return {**mae_rmse(actual, predicted), "wape": wape}
