"""Transaction segmentation: StandardScaler + KMeans over receipt features.

The artefact bundles ``clusters.json`` with a profile per cluster, so a response
can carry a readable label next to the raw cluster index.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.errors import EvaluationNotSupportedError, InvalidInputError
from app.models.base import ArtifactModel

MODEL_ID = "segmentation"
TASK = "clustering"
DESCRIPTION = "Segmentasi transaksi berdasarkan karakteristik keranjang, waktu, dan loyalitas."
QUALITY_METRICS = ("silhouette", "davies_bouldin")

CLUSTERS_FILE = "clusters"

# Training feature column -> API request field.
FEATURE_SOURCES = {
    "total_item": "total_item",
    "total_amount": "total_amount",
    "hour": "hour",
    "dow": "day_of_week",
    "is_weekend": "is_weekend",
    "use_loyalty_card": "use_loyalty_card",
}


class SegmentationModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        if not isinstance(self.estimator, dict) or not {"scaler", "kmeans"} <= set(self.estimator):
            raise InvalidInputError("artefak segmentation harus berisi komponen scaler dan kmeans", status_code=500, code="artifact_error")
        self.feature_columns: list[str] = list(self.metadata.get("features", []))
        self.clusters: list[dict] = list(self.extra.get(CLUSTERS_FILE, []))
        self._by_index = {int(entry["cluster"]): entry for entry in self.clusters}
        if not self.feature_columns:
            raise InvalidInputError("metadata segmentation tidak memuat daftar fitur", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload["transactions"]
        scaled = self.estimator["scaler"].transform(self._matrix(rows))
        labels = self.estimator["kmeans"].predict(scaled)
        centroids = self.estimator["kmeans"].cluster_centers_

        assignments = []
        for position, label in enumerate(labels):
            index = int(label)
            profile = self._by_index.get(index, {})
            assignments.append(
                {
                    "index": position,
                    "cluster": index,
                    "label": profile.get("label", f"cluster_{index}"),
                    "distance_to_centroid": round(float(np.linalg.norm(scaled[position] - centroids[index])), 4),
                    "profile": {key: round(float(value), 4) for key, value in (profile.get("profile") or {}).items()},
                }
            )

        distribution: dict[str, int] = {}
        for assignment in assignments:
            distribution[assignment["label"]] = distribution.get(assignment["label"], 0) + 1

        return {
            "n_transactions": len(assignments),
            "assignments": assignments,
            "cluster_distribution": distribution,
            "clusters_reference": self.clusters,
        }

    def _matrix(self, rows: list[dict[str, Any]]) -> np.ndarray:
        """Project request transactions onto the training feature order."""
        matrix = []
        for row in rows:
            day_of_week = int(row["day_of_week"])
            derived = {
                "total_item": float(row["total_item"]),
                "total_amount": float(row["total_amount"]),
                "hour": float(row["hour"]),
                "day_of_week": float(day_of_week),
                "is_weekend": float(day_of_week >= 5),
                "use_loyalty_card": float(int(bool(row.get("use_loyalty_card", False)))),
            }
            values = {column: derived[source] for column, source in FEATURE_SOURCES.items()}
            missing = [column for column in self.feature_columns if column not in values]
            if missing:
                raise InvalidInputError(f"fitur model tidak dapat dibentuk dari request: {missing}", details={"features": self.feature_columns})
            matrix.append([values[column] for column in self.feature_columns])
        return np.array(matrix, dtype=float)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        from sklearn.metrics import davies_bouldin_score, silhouette_score

        rows = payload["transactions"]
        scaled = self.estimator["scaler"].transform(self._matrix(rows))
        predicted = self.estimator["kmeans"].predict(scaled)
        labels = [row.get("cluster") for row in rows]
        has_labels = all(label is not None for label in labels)
        reference = np.array(labels, dtype=int) if has_labels else predicted

        unique = np.unique(reference)
        if len(unique) < 2:
            raise EvaluationNotSupportedError(
                "Silhouette dan Davies-Bouldin hanya valid bila terdapat minimal dua klaster berbeda pada data yang dikirim",
                details={"rows": len(rows), "n_labels": int(len(unique))},
            )

        return {
            "rows_evaluated": len(rows),
            "n_labels": int(len(unique)),
            "metrics": {
                "silhouette": round(float(silhouette_score(scaled, reference)), 4),
                "davies_bouldin": round(float(davies_bouldin_score(scaled, reference)), 4),
            },
            "label_agreement": round(float(np.mean(predicted == reference)), 4) if has_labels else None,
            "metric_note": (
                "Metrik dihitung pada data yang dikirim pada request ini, memakai label aktual bila tersedia "
                "atau label prediksi model bila tidak."
            ),
        }
