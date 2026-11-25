"""Product segmentation: KMeans over seven product-level sales features."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import davies_bouldin_score, silhouette_score

from app.errors import ArtifactError, EvaluationNotSupportedError, InvalidInputError
from app.models.base import ArtifactModel

MODEL_ID = "product_segmentation"
TASK = "clustering"
DESCRIPTION = "Segmentasi produk menjadi Best Seller, Regular Seller, Seasonal Product, atau Slow Moving."
QUALITY_METRICS = ("silhouette", "davies_bouldin", "label_agreement")


class SegmentationModel(ArtifactModel):
    model_id = MODEL_ID
    task = TASK
    description = DESCRIPTION
    quality_metrics = QUALITY_METRICS

    def _after_load(self) -> None:
        bundle = self.estimator
        required = {"scaler", "model", "feature_names", "label_map"}
        if not isinstance(bundle, dict) or not required.issubset(bundle):
            raise ArtifactError("artefak product_segmentation bukan bundle segmentasi produk")
        self.scaler = bundle["scaler"]
        self.kmeans = bundle["model"]
        self.feature_columns = list(bundle["feature_names"])
        self.label_map = {int(cluster): str(label) for cluster, label in bundle["label_map"].items()}

        csv_path = self.artifact_dir / "product_segments.csv"
        if not csv_path.exists():
            raise ArtifactError("product_segments.csv tidak ditemukan", details={"artifact_dir": str(self.artifact_dir)})
        frame = pd.read_csv(csv_path)
        missing = [column for column in ["product", "cluster", "revenue", *self.feature_columns] if column not in frame.columns]
        if missing:
            raise ArtifactError("product_segments.csv tidak lengkap", details={"missing": missing})
        self.products: list[dict[str, Any]] = json.loads(frame.to_json(orient="records"))
        self._by_name = {str(row["product"]): row for row in self.products}

        profile_path = self.artifact_dir / "segment_profile.csv"
        if profile_path.exists():
            self.clusters_reference: list[dict[str, Any]] = json.loads(pd.read_csv(profile_path).to_json(orient="records"))
        else:
            self.clusters_reference = [
                {
                    "cluster": cluster,
                    "segment": self.label_map.get(cluster, f"Cluster {cluster}"),
                    "centroid": {column: float(value) for column, value in zip(self.feature_columns, row)},
                }
                for cluster, row in enumerate(np.asarray(self.kmeans.cluster_centers_))
            ]

    def _rows(self, names: list[str]) -> list[dict[str, Any]]:
        missing = [name for name in names if name not in self._by_name]
        if missing:
            raise InvalidInputError(
                "sebagian produk tidak ada pada artefak segmentasi",
                details={"missing_products": missing[:20], "n_missing": len(missing)},
            )
        return [self._by_name[name] for name in names]

    def _matrix(self, rows: list[dict[str, Any]]) -> np.ndarray:
        return np.asarray([[float(row[column]) for column in self.feature_columns] for row in rows], dtype=float)

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        names = [str(name) for name in payload.get("products") or []]
        rows = self._rows(names)
        scaled = self.scaler.transform(self._matrix(rows))
        labels = np.asarray(self.kmeans.predict(scaled), dtype=int)
        distances = np.asarray(self.kmeans.transform(scaled), dtype=float)

        assignments: list[dict[str, Any]] = []
        for row, cluster, row_distances in zip(rows, labels, distances):
            cluster = int(cluster)
            assignments.append(
                {
                    "product": str(row["product"]),
                    "cluster": cluster,
                    "label": self.label_map.get(cluster, f"Cluster {cluster}"),
                    "distance_to_centroid": round(float(row_distances[cluster]), 4),
                    "profile": {
                        **{column: float(row[column]) for column in self.feature_columns},
                        "revenue": float(row["revenue"]),
                    },
                }
            )

        top_products: dict[str, list[dict[str, Any]]] = {}
        for label in dict.fromkeys(self.label_map.values()):
            members = [row for row in rows if self.label_map.get(int(row["cluster"])) == label]
            members.sort(key=lambda row: float(row["revenue"]), reverse=True)
            top_products[label] = members[:5]

        distribution = Counter(assignment["label"] for assignment in assignments)
        return {
            "model_id": self.model_id,
            "model_version": self.version,
            "n_products": len(assignments),
            "assignments": assignments,
            "cluster_distribution": dict(distribution),
            "clusters_reference": self.clusters_reference,
            "top_products": top_products,
        }

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        names = [str(name) for name in payload.get("products") or []]
        rows = self._rows(names)
        scaled = self.scaler.transform(self._matrix(rows))
        predicted = np.asarray(self.kmeans.predict(scaled), dtype=int)
        actual = np.asarray([int(row["cluster"]) for row in rows], dtype=int)

        if len(set(predicted)) < 2 or len(set(actual)) < 2:
            raise EvaluationNotSupportedError(
                "metrik klaster membutuhkan minimal dua klaster berbeda pada produk yang dikirim",
                details={"n_predicted_labels": len(set(predicted)), "n_actual_labels": len(set(actual))},
            )

        metrics = {
            "silhouette": round(float(silhouette_score(scaled, predicted)), 4),
            "davies_bouldin": round(float(davies_bouldin_score(scaled, predicted)), 4),
            "label_agreement": round(float(np.mean(predicted == actual)), 4),
        }
        return {
            "rows_evaluated": len(rows),
            "n_labels": len(set(predicted)),
            "metrics": metrics,
            "label_agreement": metrics["label_agreement"],
            "metric_note": (
                "Silhouette dan Davies-Bouldin dihitung pada ruang fitur yang sudah diskalakan; "
                "label_agreement membandingkan klaster prediksi dengan segmentasi tersimpan di product_segments.csv."
            ),
        }
