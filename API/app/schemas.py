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

    outlet: str = Field(..., description="Kode outlet, salah satu dari kategori outlet model.", examples=["SHOP001"])
    horizon_days: int = Field(7, ge=1, le=14, description="Jumlah hari yang diprediksi, mulai hari setelah data historis terakhir.")


class SalesForecastPoint(BaseModel):
    date: dt.date
    predicted_net_sales: float = Field(..., description="Prediksi total NetSales outlet pada hari tersebut (IDR).")


class SalesHistoryPoint(BaseModel):
    date: dt.date
    net_sales: float


class SalesForecastSummary(BaseModel):
    total_predicted_net_sales: float
    average_daily_net_sales: float
    last_7_days_actual_net_sales: float
    change_vs_last_7_days_pct: float = Field(
        ...,
        description="Perubahan rata-rata harian prediksi terhadap rata-rata 7 hari aktual terakhir (persen).",
    )


class SalesForecastResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    outlet: str
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
DEMAND_FORECAST_EXAMPLE = {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 7}


class DemandForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": DEMAND_FORECAST_EXAMPLE})

    outlet: str = Field(..., description="Kode outlet.", examples=["SHOP001"])
    product: str = Field(..., description="Nama produk persis seperti pada kategori produk model.", examples=["Friendly Coffee (Ice)"])
    horizon_days: int = Field(7, ge=1, le=14, description="Jumlah hari yang diprediksi.")


class DemandForecastPoint(BaseModel):
    date: dt.date
    predicted_qty: float = Field(..., description="Prediksi jumlah unit terjual.")
    predicted_revenue: float = Field(..., description="Perkiraan pendapatan (qty x rata-rata harga unit historis, proxy).")


class DemandForecastSummary(BaseModel):
    total_predicted_qty: float
    average_daily_qty: float
    suggested_reorder_qty: float = Field(..., description="Pembulatan ke atas dari total prediksi permintaan pada horizon.")
    unit_price_used: float = Field(..., description="Rata-rata pendapatan per unit historis untuk outlet x produk ini.")
    last_7_days_actual_qty: float


class DemandForecastResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    outlet: str
    product: str
    currency: str = "IDR"
    horizon_days: int
    history_end: dt.date
    predictions: list[DemandForecastPoint]
    summary: DemandForecastSummary
    recent_history: list[dict]


class DemandActualPoint(BaseModel):
    date: dt.date
    outlet: str
    product: str
    qty: float = Field(..., ge=0)


class DemandEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actuals: list[DemandActualPoint] = Field(..., min_length=1, max_length=5000)


class DemandEvaluationResponse(BaseModel):
    note: str = Field(..., description="Catatan cara metrik dihitung dan keterbatasannya.")
    request_id: str
    model_id: str
    model_version: str
    evaluated_at: dt.datetime
    rows_evaluated: int
    rows_skipped: int
    skipped_reason: str | None = None
    metrics: dict[str, float]
    baseline_metrics: dict[str, float] = Field(..., description="Pembanding naif: nilai qty 7 hari sebelumnya.")
    sample: list[dict]


# Transaction segmentation
SEGMENTATION_EXAMPLE = {
    "transactions": [
        {"total_item": 1, "total_amount": 23000, "hour": 8, "day_of_week": 3, "use_loyalty_card": False},
        {"total_item": 2, "total_amount": 54000, "hour": 19, "day_of_week": 6, "use_loyalty_card": True},
    ]
}


class TransactionFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_item: int = Field(..., ge=1, le=50, description="Jumlah item pada struk (TotalItem).")
    total_amount: float = Field(..., ge=0, le=10_000_000, description="Nilai transaksi (TotalAmount).")
    hour: int = Field(..., ge=0, le=23, description="Jam transaksi.")
    day_of_week: int = Field(..., ge=0, le=6, description="Hari dalam minggu, 0 = Senin.")
    use_loyalty_card: bool = Field(False, description="Apakah transaksi memakai kartu loyalitas.")


class SegmentationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": SEGMENTATION_EXAMPLE})

    transactions: list[TransactionFeatures] = Field(..., min_length=1, max_length=500, description="Daftar transaksi yang akan dikelompokkan.")


class ClusterAssignment(BaseModel):
    index: int
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
    n_transactions: int
    assignments: list[ClusterAssignment]
    cluster_distribution: dict[str, int] = Field(..., description="Jumlah transaksi per label klaster pada request ini.")
    clusters_reference: list[dict] = Field(..., description="Profil seluruh klaster model (dari artefak clusters.json).")


class LabelledTransaction(TransactionFeatures):
    cluster: int | None = Field(None, description="Label klaster aktual, bila tersedia (dipakai untuk membandingkan hasil prediksi).")


class SegmentationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transactions: list[LabelledTransaction] = Field(..., min_length=2, max_length=5000, description="Transaksi berlabel klaster untuk menghitung Silhouette dan Davies-Bouldin.")


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
        description="Rasio transaksi yang labelnya sesuai prediksi model (hanya bila label aktual dikirim).",
    )


# Peak-hour prediction
PEAK_HOUR_EXAMPLE = {"outlet": "SHOP001"}


class PeakHourRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": PEAK_HOUR_EXAMPLE})

    outlet: str = Field(..., description="Kode outlet.", examples=["SHOP001"])
    date: dt.date | None = Field(None, description="Tanggal yang diprediksi. Default: hari pertama setelah data historis model.")


class HourlyPrediction(BaseModel):
    hour: int
    predicted_tx_count: float = Field(..., description="Prediksi jumlah struk pada jam tersebut.")
    is_peak: bool = Field(..., description="True bila jam ini diklasifikasikan sebagai jam sibuk.")
    peak_probability: float = Field(..., description="Probabilitas kelas jam sibuk dari classifier.")


class PeakHourSummary(BaseModel):
    busiest_hour: int
    busiest_hour_predicted_tx_count: float
    peak_hours: list[int] = Field(..., description="Jam yang diklasifikasikan sibuk pada tanggal ini.")
    predicted_total_tx: float
    average_tx_per_hour: float
    reference_peak_hours: list[int] = Field(..., description="Jam sibuk outlet menurut profil rata-rata data latih.")


class PeakHourResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    outlet: str
    date: dt.date
    history_end: dt.date
    hours_covered: list[int] = Field(..., description="Jam yang dicakup model (jam operasional pada data latih).")
    predictions: list[HourlyPrediction]
    summary: PeakHourSummary


class PeakHourActualPoint(BaseModel):
    date: dt.date
    outlet: str
    hour: int = Field(..., ge=0, le=23)
    tx_count: float = Field(..., ge=0)


class PeakHourEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actuals: list[PeakHourActualPoint] = Field(..., min_length=2, max_length=5000)
    peak_label: str = Field(
        "actual",
        pattern="^(actual|reference)$",
        description=(
            "'actual': label sibuk dihitung dari p75 volume aktual pada data yang dikirim (menilai ketepatan angka). "
            "'reference': label sibuk memakai jam sibuk outlet dari profil data latih (menilai klasifikasi jam sibuk). "
            "Catatan: label 'reference' adalah fungsi deterministik dari jam dan outlet, sehingga skor mendekati sempurna "
            "pada mode ini memang diharapkan - bukan bukti kualitas model. Gunakan mode 'actual' bila ingin menguji "
            "kemampuan model menandai jam yang benar-benar ramai pada data baru."
        ),
    )


class PeakHourEvaluationResponse(BaseModel):
    note: str = Field(..., description="Catatan cara metrik dihitung dan keterbatasannya.")
    request_id: str
    model_id: str
    model_version: str
    evaluated_at: dt.datetime
    rows_evaluated: int
    rows_skipped: int
    skipped_reason: str | None = None
    peak_label: str
    metrics: dict[str, float | dict]
    baseline_metrics: dict[str, float] = Field(..., description="Pembanding naif: volume jam yang sama 7 hari sebelumnya.")
    sample: list[dict]


# Stock prediction
STOCK_PREDICTION_EXAMPLE = {"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 7}


class StockPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": STOCK_PREDICTION_EXAMPLE})

    outlet: str = Field(..., description="Kode outlet.")
    product: str = Field(..., description="Nama produk persis seperti pada kategori produk model.")
    horizon_days: int = Field(7, ge=1, le=14, description="Panjang horizon kebutuhan stok yang diprediksi.")
    available_stock: float = Field(
        0.0,
        ge=0,
        le=1_000_000,
        description="Perkiraan stok yang tersedia saat ini (opsional). Dipakai untuk menghitung saran jumlah pemesanan ulang.",
    )


class StockPredictionPoint(BaseModel):
    date: dt.date
    predicted_qty: float = Field(..., description="Prediksi permintaan pada hari tersebut (bagian dari akumulasi kebutuhan).")
    cumulative_required_qty: float = Field(..., description="Akumulasi kebutuhan stok dari awal horizon sampai hari ini.")


class StockPredictionSummary(BaseModel):
    required_stock: float = Field(..., description="Total kebutuhan stok pada horizon (unit).")
    suggested_reorder_qty: float = Field(..., description="Pembulatan ke atas kebutuhan stok dikurangi perkiraan stok tersedia.")
    estimated_available_stock: float = Field(..., description="Perkiraan stok tersedia dari input request, atau 0 bila tidak dikirim.")
    stockout_risk: bool
    stockout_probability: float = Field(
        ...,
        description=(
            "Probabilitas label risiko untuk kebutuhan stok 7 hari (window yang dilatih classifier), "
            "bukan untuk horizon yang diminta pada request."
        ),
    )
    risk_threshold: float = Field(..., description="Ambang probabilitas yang dikalibrasi saat pelatihan.")
    historical_p75_daily_qty: float
    historical_p95_daily_qty: float
    unit_price_used: float


class StockPredictionResponse(BaseModel):
    request_id: str
    model_id: str
    model_version: str
    task: str
    generated_at: dt.datetime
    outlet: str
    product: str
    horizon_days: int
    history_end: dt.date
    predictions: list[StockPredictionPoint]
    summary: StockPredictionSummary
    proxy_label: str = Field(..., description="Penjelasan label risiko stock-out yang dipakai model (bukan data stok nyata).")


class StockActualPoint(BaseModel):
    date: dt.date
    outlet: str
    product: str
    required_stock: float = Field(..., ge=0, description="Kebutuhan stok aktual (mis. jumlah unit terjual pada 7 hari setelah tanggal tersebut).")


class StockEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actuals: list[StockActualPoint] = Field(..., min_length=2, max_length=5000)


class StockEvaluationResponse(BaseModel):
    note: str = Field(..., description="Catatan cara metrik dihitung dan keterbatasannya.")
    request_id: str
    model_id: str
    model_version: str
    evaluated_at: dt.datetime
    rows_evaluated: int
    rows_skipped: int
    skipped_reason: str | None = None
    metrics: dict[str, float | dict]
    baseline_metrics: dict[str, float]
    sample: list[dict]
