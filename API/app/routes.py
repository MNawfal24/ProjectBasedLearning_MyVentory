"""All API endpoints: system status, predictions, evaluation and metrics.

Each model keeps its own request/response contract (``app/schemas.py``); a route
only wires validation, the registry lookup, the shared response envelope and the
metrics record. Endpoints are grouped by Swagger tag rather than by module,
because the five prediction routes are deliberately uniform.
"""

from __future__ import annotations

import datetime as dt
import time
from typing import Any, Callable

from fastapi import APIRouter, Depends, Request, Response

from app.config import settings
from app.errors import ApiError, InvalidInputError, UnknownModelError, request_id_of
from app.metrics import metrics_store
from app.model_registry import registry
from app.models.base import ArtifactModel
from app.schemas import (
    DemandEvaluationRequest,
    DemandEvaluationResponse,
    DemandForecastRequest,
    DemandForecastResponse,
    PeakHourEvaluationRequest,
    PeakHourEvaluationResponse,
    PeakHourRequest,
    PeakHourResponse,
    SalesEvaluationRequest,
    SalesEvaluationResponse,
    SalesForecastRequest,
    SalesForecastResponse,
    SegmentationEvaluationRequest,
    SegmentationEvaluationResponse,
    SegmentationRequest,
    SegmentationResponse,
    StockEvaluationRequest,
    StockEvaluationResponse,
    StockPredictionRequest,
    StockPredictionResponse,
)

router = APIRouter()

IN_MEMORY_NOTE = (
    "Metrik teknis disimpan in-memory di proses API dan bersifat sementara: "
    "data hilang ketika proses dihentikan atau di-restart. Tidak ada isi request, header, "
    "atau data pengguna yang disimpan - hanya jumlah request, status code, latency, jumlah inference, dan versi model."
)

# The served artefact is refit on the full history, so a date inside that history
# is in-sample. Out-of-sample figures live in metadata (GET /models/{model_id}).
EVALUATION_NOTE = (
    "Metrik dihitung dari data yang dikirim pada request memakai model yang sedang dilayani. "
    "Artefak yang dilayani dilatih ulang pada seluruh data historis, sehingga tanggal di dalam rentang "
    "historis bersifat in-sample; angka out-of-sample (holdout 28 hari terakhir) tersedia di metadata "
    "artefak melalui GET /api/v1/models/{model_id}."
)

EVALUATION_CONTRACTS: dict[str, type] = {
    "sales_forecast": SalesEvaluationRequest,
    "demand_forecast": DemandEvaluationRequest,
    "segmentation": SegmentationEvaluationRequest,
    "peak_hour": PeakHourEvaluationRequest,
    "stock_prediction": StockEvaluationRequest,
}


def _run(model_id: str, endpoint: str, request: Request, call: Callable[[ArtifactModel], dict], is_inference: bool) -> dict:
    """Run one model call, record its metrics and add the shared response envelope."""
    started = time.perf_counter()
    model = registry.get(model_id)
    version: str | None = None
    status_code = 500
    try:
        result = call(model)
        version = model.version
        status_code = 200
    except ApiError as exc:
        status_code = exc.status_code
        raise
    finally:
        metrics_store.record_model_call(
            model_id=model_id,
            endpoint=endpoint,
            latency_ms=(time.perf_counter() - started) * 1000,
            status_code=status_code,
            is_inference=is_inference and status_code == 200,
            model_version=version,
        )

    envelope = {
        "request_id": request_id_of(request),
        "model_id": model.model_id,
        "model_version": model.version,
        "task": model.task,
    }
    if endpoint == "evaluate":
        envelope["evaluated_at"] = dt.datetime.now(dt.timezone.utc)
        note = EVALUATION_NOTE
        if isinstance(result.get("metric_note"), str):
            note = f"{note} {result['metric_note']}"
        envelope["note"] = note
    else:
        envelope["generated_at"] = dt.datetime.now(dt.timezone.utc)
    return {**envelope, **result}


def require_evaluate_model(model_id: str) -> str:
    """Reject an unknown model id before the polymorphic evaluation body is validated."""
    if model_id not in EVALUATION_CONTRACTS:
        raise UnknownModelError(f"model '{model_id}' tidak dikenal", details={"known_models": sorted(EVALUATION_CONTRACTS)})
    return model_id


@router.get(
    "/health",
    tags=["system"],
    summary="Health check API",
    description=(
        "Memeriksa bahwa proses API hidup. Endpoint ini tidak bergantung pada artefak model, "
        "sehingga tetap 200 walaupun semua model belum tersedia."
    ),
)
def health(request: Request) -> dict:
    return {
        "request_id": request_id_of(request),
        "status": "ok",
        "service": settings.api_title,
        "api_version": settings.api_version,
        "timestamp": dt.datetime.now(dt.timezone.utc),
    }


@router.get(
    "/ready",
    tags=["system"],
    summary="Readiness check model",
    description=(
        "Melaporkan model mana yang sudah dimuat dan siap menerima request. "
        "Status HTTP 200 bila minimal satu model siap, 503 bila tidak ada model yang siap."
    ),
)
def ready(request: Request, response: Response) -> dict:
    statuses = registry.statuses()
    ready_models = [item["model_id"] for item in statuses if item["status"] == "ready"]
    if not ready_models:
        response.status_code = 503
    return {
        "request_id": request_id_of(request),
        "status": "ready" if ready_models else "not_ready",
        "ready_models": ready_models,
        "unavailable_models": [item["model_id"] for item in statuses if item["status"] != "ready"],
        "models": statuses,
        "artifacts_root": str(registry.artifacts_root),
    }


@router.get(
    "/models",
    tags=["system"],
    summary="Daftar model dan statusnya",
    description="Menampilkan kelima model yang dikontrakkan API beserta status kesiapan, versi, dan metrik kualitas hasil pelatihan.",
)
def list_models(request: Request) -> dict:
    models = []
    for status in registry.statuses():
        model = registry.loaded(status["model_id"])
        models.append(
            {
                **status,
                "quality": model.metadata.get("metrics", {}) if model else None,
                "trained_at": model.metadata.get("trained_at") if model else None,
            }
        )
    return {
        "request_id": request_id_of(request),
        "total_models": len(models),
        "ready_models": len(registry.loaded_ids()),
        "models": models,
    }


@router.get(
    "/models/{model_id}",
    tags=["system"],
    summary="Informasi dan versi satu model",
    description="Menampilkan identitas, versi, daftar fitur, catatan pelatihan, metrik kualitas, dan daftar berkas artefak satu model.",
)
def model_info(model_id: str, request: Request) -> dict:
    return {"request_id": request_id_of(request), "status": "ready", **registry.get(model_id).info()}


@router.post(
    "/sales-forecast",
    tags=["predictions"],
    response_model=SalesForecastResponse,
    summary="Sales forecasting",
    description=(
        "Memprediksi total penjualan harian (NetSales) satu outlet untuk beberapa hari ke depan. "
        "Model HistGradientBoostingRegressor dilatih pada fitur kalender dan lag/rolling penjualan; "
        "prediksi bersifat rekursif, hasil hari sebelumnya dipakai sebagai input hari berikutnya."
    ),
)
def predict_sales_forecast(payload: SalesForecastRequest, request: Request) -> dict:
    return _run("sales_forecast", "predict", request, lambda model: model.predict(payload.model_dump()), is_inference=True)


@router.post(
    "/demand-forecast",
    tags=["predictions"],
    response_model=DemandForecastResponse,
    summary="Demand forecasting",
    description=(
        "Memprediksi jumlah permintaan harian (unit) satu outlet x produk, beserta perkiraan pendapatan "
        "dan saran jumlah pemesanan ulang pada horizon yang diminta."
    ),
)
def predict_demand_forecast(payload: DemandForecastRequest, request: Request) -> dict:
    return _run("demand_forecast", "predict", request, lambda model: model.predict(payload.model_dump()), is_inference=True)


@router.post(
    "/segmentation",
    tags=["predictions"],
    response_model=SegmentationResponse,
    summary="Transaction segmentation",
    description=(
        "Mengelompokkan transaksi ke klaster hasil KMeans (StandardScaler + KMeans) berdasarkan jumlah item, "
        "nilai transaksi, jam, hari, dan penggunaan kartu loyalitas. Setiap hasil menyertakan label klaster "
        "dan jarak ke centroid."
    ),
)
def predict_segmentation(payload: SegmentationRequest, request: Request) -> dict:
    return _run("segmentation", "predict", request, lambda model: model.predict(payload.model_dump()), is_inference=True)


@router.post(
    "/peak-hour",
    tags=["predictions"],
    response_model=PeakHourResponse,
    summary="Peak-hour prediction",
    description=(
        "Memprediksi volume struk untuk setiap jam operasional satu outlet pada satu tanggal, "
        "menentukan jam tersibuk, dan menandai jam sibuk menurut classifier."
    ),
)
def predict_peak_hour(payload: PeakHourRequest, request: Request) -> dict:
    return _run("peak_hour", "predict", request, lambda model: model.predict(payload.model_dump()), is_inference=True)


@router.post(
    "/stock-prediction",
    tags=["predictions"],
    response_model=StockPredictionResponse,
    summary="Stock prediction",
    description=(
        "Memprediksi kebutuhan stok satu outlet x produk pada horizon tertentu, saran jumlah pemesanan ulang "
        "(dikurangi stok tersedia bila dikirim), dan risiko kekurangan stok. Label risiko adalah proxy berbasis "
        "kecepatan penjualan, bukan data stok nyata - lihat field proxy_label pada response."
    ),
)
def predict_stock_prediction(payload: StockPredictionRequest, request: Request) -> dict:
    return _run("stock_prediction", "predict", request, lambda model: model.predict(payload.model_dump()), is_inference=True)


@router.post(
    "/models/{model_id}/evaluate",
    tags=["predictions"],
    response_model=SalesEvaluationResponse
    | DemandEvaluationResponse
    | SegmentationEvaluationResponse
    | PeakHourEvaluationResponse
    | StockEvaluationResponse,
    summary="Evaluasi model dengan data aktual berlabel",
    description=(
        "Menghitung metrik kualitas model dari data aktual berlabel yang dikirim pada request. "
        "Bentuk body mengikuti model yang dipilih: sales_forecast dan demand_forecast memakai pasangan "
        "tanggal/outlet/(produk) + nilai aktual; segmentation memakai transaksi (label klaster opsional); "
        "peak_hour memakai volume per jam; stock_prediction memakai kebutuhan stok aktual. "
        "Metrik hanya dihitung bila datanya valid - tidak ada nilai evaluasi fiktif."
    ),
)
def evaluate_model(
    payload: SalesEvaluationRequest
    | DemandEvaluationRequest
    | SegmentationEvaluationRequest
    | PeakHourEvaluationRequest
    | StockEvaluationRequest,
    request: Request,
    model_id: str = Depends(require_evaluate_model),
) -> dict:
    request_class = EVALUATION_CONTRACTS[model_id]
    if not isinstance(payload, request_class):
        raise InvalidInputError(
            f"body request tidak sesuai kontrak evaluasi model '{model_id}'",
            details={"expected": request_class.__name__, "received": type(payload).__name__},
        )
    return _run(model_id, "evaluate", request, lambda model: model.evaluate(payload.model_dump()), is_inference=False)


@router.get(
    "/metrics/",
    tags=["metrics"],
    summary="Ringkasan metrik teknis API",
    description="Jumlah request, request sukses/gagal, error rate, latency rata-rata/p50/p95, dan jumlah inference per model.",
)
def metrics_summary(request: Request) -> dict:
    return {
        "request_id": request_id_of(request),
        "generated_at": dt.datetime.now(dt.timezone.utc),
        "scope": "summary",
        "note": IN_MEMORY_NOTE,
        "summary": metrics_store.summary(),
        "by_model": metrics_store.by_model(),
        "by_endpoint": metrics_store.by_endpoint(),
        "model_versions_in_use": registry.versions(),
    }


@router.get(
    "/metrics/models",
    tags=["metrics"],
    summary="Metrik teknis per model",
    description="Metrik teknis dipisah per model (dan per endpoint), dilengkapi metrik kualitas hasil pelatihan bila tersedia.",
)
def metrics_by_model(request: Request) -> dict:
    rows = []
    for status in registry.statuses():
        model = registry.loaded(status["model_id"])
        rows.append(
            {
                "model_id": status["model_id"],
                "status": status["status"],
                "model_version": model.version if model else None,
                "technical": _technical(status["model_id"]),
                "quality": model.metadata.get("metrics") if model else None,
            }
        )
    return {
        "request_id": request_id_of(request),
        "generated_at": dt.datetime.now(dt.timezone.utc),
        "scope": "per_model",
        "note": IN_MEMORY_NOTE,
        "quality_note": (
            "Metrik kualitas berasal dari data uji (holdout) saat pelatihan, bukan dari trafik API. "
            "Model yang belum tersedia tidak memiliki metrik kualitas."
        ),
        "by_model": rows,
        "by_model_endpoint": metrics_store.by_model_endpoint(),
    }


@router.get(
    "/metrics/models/{model_id}",
    tags=["metrics"],
    summary="Metrik teknis satu model",
    description="Metrik teknis satu model, termasuk rincian per endpoint, jumlah inference, dan versi model yang dipakai.",
)
def metrics_for_model(model_id: str, request: Request) -> dict:
    model = registry.get(model_id)
    return {
        "request_id": request_id_of(request),
        "generated_at": dt.datetime.now(dt.timezone.utc),
        "model_id": model_id,
        "note": IN_MEMORY_NOTE,
        "technical": _technical(model_id),
        "endpoints": [row for row in metrics_store.by_model_endpoint() if row["model_id"] == model_id],
        "model_version": model.version,
    }


@router.post(
    "/metrics/reset",
    tags=["metrics"],
    summary="Reset metrik teknis",
    description="Mengosongkan penghitung metrik in-memory. Berguna untuk pengujian dan pengukuran ulang.",
)
def reset_metrics(request: Request) -> dict:
    metrics_store.reset()
    return {"request_id": request_id_of(request), "status": "reset", "note": IN_MEMORY_NOTE}


def _technical(model_id: str) -> dict[str, Any]:
    for row in metrics_store.by_model():
        if row["model_id"] == model_id:
            return row
    return {
        "model_id": model_id,
        "requests": 0,
        "success": 0,
        "failure": 0,
        "error_rate": 0.0,
        "inferences": 0,
        "latency_ms": {"avg": 0.0, "p50": 0.0, "p95": 0.0},
        "status_codes": {},
        "model_versions": {},
        "latency_samples_kept": 0,
    }
