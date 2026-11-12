"""Transaction segmentation: StandardScaler + KMeans over receipt features.

The artefact bundles ``clusters.json`` with a profile per cluster, so a response
can carry a readable label next to the raw cluster index.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.errors import EvaluationNotSupportedError, InvalidInputError
from app.models.base import ArtifactModel

MODEL_ID = "product_segmentation"
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
        if not isinstance(self.estimator, dict) or not {"scaler", "model", "feature_names", "label_map"} <= set(self.estimator):
            raise InvalidInputError("artefak product_segmentation tidak memuat bundle notebook", status_code=500, code="artifact_error")
        self.feature_columns = list(self.estimator["feature_names"])
        self._by_index = {int(key): value for key, value in self.estimator["label_map"].items()}
        self.clusters = []
        segments_path = self.artifact_dir / "product_segments.csv"
        if segments_path.exists():
            import pandas as pd
            self.products = pd.read_csv(segments_path).to_dict(orient="records")
        else:
            self.products = []
        if not self.feature_columns:
            raise InvalidInputError("metadata segmentation tidak memuat daftar fitur", status_code=500, code="artifact_error")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload["transactions"] or [{"product": product} for product in payload.get("products", [])]
        if not rows:
            raise InvalidInputError("kirim products atau transactions", details={"field": "products"})
        scaled = self.estimator["scaler"].transform(self._matrix(rows))
        labels = self.estimator["model"].predict(scaled)
        centroids = self.estimator["model"].cluster_centers_

        assignments = []
        for position, label in enumerate(labels):
            index = int(label)
            profile = self._by_index.get(index, f"cluster_{index}")
            assignment = {
                    "index": position,
                    "cluster": index,
                    "label": profile,
                    "distance_to_centroid": round(float(np.linalg.norm(scaled[position] - centroids[index])), 4),
                    "profile": {},
                }
            if rows[position].get("product"):
                assignment["product"] = rows[position]["product"]
            assignments.append(assignment)

        distribution: dict[str, int] = {}
        for assignment in assignments:
            distribution[assignment["label"]] = distribution.get(assignment["label"], 0) + 1

        product_rows = {row.get("product"): row for row in self.products}
        top_products: dict[str, list[dict[str, Any]]] = {}
        for label in distribution:
            products = [item.get("product") for item in assignments if item["label"] == label and item.get("product")]
            ranked = sorted(
                (product_rows[product] for product in products if product in product_rows),
                key=lambda row: float(row.get("revenue", 0)),
                reverse=True,
            )
            top_products[label] = [
                {
                    "product": row["product"],
                    "revenue": float(row.get("revenue", 0)),
                    "quantity": float(row.get("quantity", 0)),
                }
                for row in ranked[:5]
            ]

        return {
            "n_transactions": len(assignments),
            "assignments": assignments,
            "cluster_distribution": distribution,
            "top_products": top_products,
            "clusters_reference": self.clusters,
        }

    def _matrix(self, rows: list[dict[str, Any]]) -> np.ndarray:
        """Project request transactions onto the training feature order."""
        matrix = []
        for row in rows:
            product = row.get("product")
            if product:
                match = next((item for item in self.products if item.get("product") == product), None)
                if match is None:
                    raise InvalidInputError(f"produk '{product}' tidak dikenal model", details={"total_products": len(self.products)})
                matrix.append([float(match[column]) for column in self.feature_columns])
                continue
            if any(row.get(field) is None for field in ("total_item", "total_amount", "hour", "day_of_week")):
                raise InvalidInputError("transactions membutuhkan total_item, total_amount, hour, dan day_of_week")
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
        predicted = self.estimator["model"].predict(scaled)
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
