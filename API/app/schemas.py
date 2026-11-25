"""Request and response contracts for all endpoints.

Each model gets its own request/response classes because result shapes differ.
The shared envelope (``request_id``, ``model_id``, ``model_version``, ``task``,
``generated_at``) is added by the routes, so those fields are repeated per
response model rather than inherited from a base class.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

# Sales forecasting
SALES_FORECAST_EXAMPLE = {"outlet": "SHOP001", "horizon_days": 7}


class SalesForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": SALES_FORECAST_EXAMPLE})

    outlet: str | None = Field(..., description="Kode outlet. Null berarti agregat seluruh outlet pada artefak.")
    horizon_days: int = Field(7, ge=1, le=14, description="Jumlah hari yang diprediksi, mulai hari setelah data historis terakhir.")


class SalesForecastPoint(BaseModel):
    date: dt.date
    predicted_net_sales: float = Field(..., description="Prediksi total NetSales pada hari tersebut (IDR).")


class SalesHistoryPoint(BaseModel):
    date: dt.date
    net_sales: float


class SalesForecastSummary(BaseModel):
    total_predicted_net_sales: float
    average_daily_net_sales: float
    last_7_days_actual_net_sales: float
    change_vs_last_7_days_pct: float | None = Field(
        None,
        description="Perubahan total prediksi terhadap total 7 hari aktual terakhir (persen).",
    )


class SalesForecastResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    outlet: str | None
    currency: str = "IDR"
    horizon_days: int
    history_end: dt.date = Field(..., description="Tanggal terakhir yang tersedia di data historis model.")
    predictions: list[SalesForecastPoint]
    summary: SalesForecastSummary
    recent_history: list[SalesHistoryPoint] = Field(..., description="7 hari aktual terakhir dari data historis model.")


class SalesActualPoint(BaseModel):
    date: dt.date
    outlet: str
    net_sales: float = Field(..., ge=0)


class SalesEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actuals: list[SalesActualPoint] = Field(..., min_length=1, max_length=5000, description="Data aktual berlabel untuk dihitung metriknya.")


class SalesEvaluationResponse(BaseModel):
    note: str = Field(..., description="Catatan cara metrik dihitung dan keterbatasannya.")
    request_id: str
    model_id: str
    model_version: str
    evaluated_at: dt.datetime
    rows_evaluated: int
    rows_skipped: int = Field(..., description="Baris yang dilewati karena tanggalnya di luar rentang fitur model.")
    skipped_reason: str | None = None
    metrics: dict[str, float]
    baseline_metrics: dict[str, float] = Field(
        ...,
        description="Metrik pembanding naif: nilai aktual 7 hari sebelumnya (sama hari, minggu lalu).",
    )
    sample: list[dict]


# Demand forecasting
DEMAND_FORECAST_EXAMPLE = {"product": "Friendly Coffee (Ice)", "horizon_days": 7}


class DemandForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": DEMAND_FORECAST_EXAMPLE})

    outlet: str | None = Field(None, description="Opsional; artefak demand memprediksi total item per produk secara global.")
    product: str = Field(..., description="Nama produk persis seperti pada artefak demand_forecast_product.", examples=["Friendly Coffee (Ice)"])
    horizon_days: int = Field(7, ge=1, le=14, description="Jumlah hari yang diprediksi.")


class DemandForecastPoint(BaseModel):
    date: dt.date
    predicted_qty: float = Field(..., description="Prediksi jumlah unit terjual.")
    predicted_revenue: float = Field(..., description="Perkiraan pendapatan (0 bila artefak tidak menyimpan harga).")


class DemandForecastSummary(BaseModel):
    total_predicted_qty: float
    average_daily_qty: float
    suggested_reorder_qty: float = Field(..., description="Pembulatan ke atas kebutuhan 7 hari dari rata-rata prediksi.")
    unit_price_used: float
    last_7_days_actual_qty: float


class DemandForecastResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    outlet: str | None
    product: str
    currency: str = "IDR"
    horizon_days: int
    history_end: dt.date
    predictions: list[DemandForecastPoint]
    summary: DemandForecastSummary
    recent_history: list[dict]
    note: str | None = None


class DemandActualPoint(BaseModel):
    date: dt.date
    outlet: str
    product: str
    qty: float = Field(..., ge=0)


class DemandEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actuals: list[DemandActualPoint] = Field(..., min_length=1, max_length=5000)


class DemandEvaluationResponse(BaseModel):
    note: str
    request_id: str
    model_id: str
    model_version: str
    evaluated_at: dt.datetime
    rows_evaluated: int
    rows_skipped: int
    skipped_reason: str | None = None
    metrics: dict[str, float]
    baseline_metrics: dict[str, float]
    sample: list[dict]


# Product segmentation
SEGMENTATION_EXAMPLE = {"products": ["Chocolate (Gedhe)", "Friendly Coffee (Ice)"]}


class SegmentationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": SEGMENTATION_EXAMPLE})

    products: list[str] = Field(..., min_length=1, max_length=500, description="Nama produk yang akan disegmentasikan.")


class ClusterAssignment(BaseModel):
    product: str
    cluster: int
    label: str
    distance_to_centroid: float
    profile: dict[str, float]


class SegmentationResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    n_products: int
    assignments: list[ClusterAssignment]
    cluster_distribution: dict[str, int] = Field(..., description="Jumlah produk per label klaster pada request ini.")
    clusters_reference: list[dict] = Field(..., description="Profil seluruh klaster model.")
    top_products: dict[str, list[dict]] = Field(default_factory=dict, description="Lima produk teratas berdasarkan revenue pada setiap segmen.")


class SegmentationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products: list[str] = Field(..., min_length=2, max_length=5000, description="Produk untuk menghitung Silhouette dan Davies-Bouldin.")


class SegmentationEvaluationResponse(BaseModel):
    note: str = Field(..., description="Catatan cara metrik dihitung dan keterbatasannya.")
    request_id: str
    model_id: str
    model_version: str
    evaluated_at: dt.datetime
    rows_evaluated: int
    n_labels: int
    metrics: dict[str, float]
    label_agreement: float | None = Field(
        None,
        description="Rasio produk yang labelnya sesuai dengan segmentasi tersimpan (bila tersedia).",
    )
