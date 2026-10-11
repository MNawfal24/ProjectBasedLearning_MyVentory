"""In-memory technical metrics: request counts, errors and latency percentiles.

Two views stay separate so nothing is double counted: ``record_request`` counts
every HTTP request by endpoint (traffic and latency, including rejected ones),
while ``record_model_call`` counts model attributions and inference counts.
Per process only, lost on restart, and no request body, header or user content is
stored - just counters, status codes, latencies and model versions.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from app.config import settings


@dataclass
class _Bucket:
    requests: int = 0
    success: int = 0
    failure: int = 0
    inferences: int = 0
    latency_total_ms: float = 0.0
    latencies: Deque[float] = field(default_factory=deque)
    status_codes: dict[str, int] = field(default_factory=dict)
    model_versions: dict[str, int] = field(default_factory=dict)

    def record(self, *, latency_ms: float, status_code: int, success: bool, is_inference: bool, model_version: str | None) -> None:
        self.requests += 1
        self.success += int(success)
        self.failure += int(not success)
        self.inferences += int(is_inference)
        self.latency_total_ms += latency_ms
        self.latencies.append(latency_ms)
        key = str(status_code)
        self.status_codes[key] = self.status_codes.get(key, 0) + 1
        if model_version:
            self.model_versions[model_version] = self.model_versions.get(model_version, 0) + 1

    def snapshot(self) -> dict:
        latencies = sorted(self.latencies)
        return {
            "requests": self.requests,
            "success": self.success,
            "failure": self.failure,
            "error_rate": round(self.failure / self.requests, 4) if self.requests else 0.0,
            "inferences": self.inferences,
            "latency_ms": {
                "avg": round(self.latency_total_ms / self.requests, 3) if self.requests else 0.0,
                "p50": _percentile(latencies, 50),
                "p95": _percentile(latencies, 95),
            },
            "status_codes": dict(sorted(self.status_codes.items())),
            "model_versions": dict(sorted(self.model_versions.items())),
            "latency_samples_kept": len(latencies),
        }


def _percentile(sorted_values: list[float], percentile: float) -> float:
    """Linear interpolation between the two closest ranks."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return round(sorted_values[0], 3)
    rank = (percentile / 100) * (len(sorted_values) - 1)
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    weight = rank - low
    return round(sorted_values[low] * (1 - weight) + sorted_values[high] * weight, 3)


class MetricsStore:
    def __init__(self, latency_sample_size: int = 2000) -> None:
        self._sample_size = latency_sample_size
        self._lock = threading.Lock()
        self._overall = _Bucket()
        self._by_endpoint: dict[str, _Bucket] = {}
        self._by_model: dict[str, _Bucket] = {}
        self._by_model_endpoint: dict[tuple[str, str], _Bucket] = {}

    def _bucket(self, store: dict, key) -> _Bucket:
        bucket = store.get(key)
        if bucket is None:
            bucket = _Bucket(latencies=deque(maxlen=self._sample_size))
            store[key] = bucket
        return bucket

    def record_request(self, *, endpoint: str, latency_ms: float, status_code: int) -> None:
        kwargs = {
            "latency_ms": latency_ms,
            "status_code": status_code,
            "success": status_code < 400,
            "is_inference": False,
            "model_version": None,
        }
        with self._lock:
            self._overall.record(**kwargs)
            self._bucket(self._by_endpoint, endpoint).record(**kwargs)

    def record_model_call(
        self,
        *,
        model_id: str,
        endpoint: str,
        latency_ms: float,
        status_code: int,
        is_inference: bool,
        model_version: str | None,
    ) -> None:
        kwargs = {
            "latency_ms": latency_ms,
            "status_code": status_code,
            "success": status_code < 400,
            "is_inference": is_inference,
            "model_version": model_version,
        }
        with self._lock:
            self._bucket(self._by_model, model_id).record(**kwargs)
            self._bucket(self._by_model_endpoint, (model_id, endpoint)).record(**kwargs)

    def summary(self) -> dict:
        """Overall traffic, with inference counts and versions summed over the models."""
        with self._lock:
            summary = self._overall.snapshot()
            models = [bucket.snapshot() for bucket in self._by_model.values()]
        summary["inferences"] = sum(item["inferences"] for item in models)
        versions: dict[str, int] = {}
        for item in models:
            for version, count in item["model_versions"].items():
                versions[version] = versions.get(version, 0) + count
        summary["model_versions"] = dict(sorted(versions.items()))
        return summary

    def by_endpoint(self) -> list[dict]:
        with self._lock:
            return [{"endpoint": key, **bucket.snapshot()} for key, bucket in sorted(self._by_endpoint.items())]

    def by_model(self) -> list[dict]:
        with self._lock:
            return [{"model_id": key, **bucket.snapshot()} for key, bucket in sorted(self._by_model.items())]

    def by_model_endpoint(self) -> list[dict]:
        with self._lock:
            return [
                {"model_id": model_id, "endpoint": endpoint, **bucket.snapshot()}
                for (model_id, endpoint), bucket in sorted(self._by_model_endpoint.items())
            ]

    def reset(self) -> None:
        with self._lock:
            self._overall = _Bucket()
            self._by_endpoint.clear()
            self._by_model.clear()
            self._by_model_endpoint.clear()


metrics_store = MetricsStore(latency_sample_size=settings.latency_sample_size)
