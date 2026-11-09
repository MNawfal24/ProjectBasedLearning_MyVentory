"""FastAPI application: middleware, exception handlers and app assembly.

One application serving the five model modules. Startup never fails because of a
missing or broken model artefact: ``/api/v1/ready`` reports what loaded.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import routes
from app.config import settings
from app.errors import ApiError, request_id_of
from app.metrics import metrics_store
from app.model_registry import registry

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("myventory.api")

REQUEST_ID_HEADER = "X-Request-Id"


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.load_all()
    logger.info("API siap: %d/%d model dimuat", len(registry.loaded_ids()), len(registry.statuses()))
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=(
            "REST API Smart Inventory yang menyediakan lima layanan prediksi machine learning: "
            "sales forecasting, demand forecasting, transaction segmentation, peak-hour prediction, dan "
            "stock prediction.\n\n"
            "Setiap model dimuat dari artefaknya sendiri di ``ML/artifacts/<model_id>/<versi>`` dan "
            "dapat gagal dimuat tanpa menghentikan aplikasi - periksa ``GET /api/v1/ready``.\n\n"
            "Metrik teknis API disimpan in-memory (hilang saat proses restart) dan dipisahkan dari "
            "metrik kualitas model yang berasal dari data uji saat pelatihan."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001 - converted to a 500 response by the handler below
            metrics_store.record_request(
                endpoint=_endpoint_label(request),
                latency_ms=(time.perf_counter() - started) * 1000,
                status_code=500,
            )
            raise
        response.headers[REQUEST_ID_HEADER] = request_id
        metrics_store.record_request(
            endpoint=_endpoint_label(request),
            latency_ms=(time.perf_counter() - started) * 1000,
            status_code=response.status_code,
        )
        return response

    register_exception_handlers(app)
    app.include_router(routes.router, prefix=settings.api_prefix)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "service": settings.api_title,
            "api_version": settings.api_version,
            "docs": "/docs",
            "api_prefix": settings.api_prefix,
            "ready": f"{settings.api_prefix}/ready",
        }

    return app


def _endpoint_label(request: Request) -> str:
    """Route template for the metric label, falling back to the raw path."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or request.url.path


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_body(request, exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = {
            "errors": [
                {
                    "field": ".".join(str(part) for part in error["loc"][1:]) or "body",
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ]
        }
        return JSONResponse(status_code=422, content=_error_body(request, "validation_error", "Input request tidak valid", details))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_body(request, "http_error", str(exc.detail), {}))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error pada %s", request.url.path)
        return JSONResponse(status_code=500, content=_error_body(request, "internal_error", "Terjadi kesalahan internal", {}))


def _error_body(request: Request, code: str, message: str, details: dict) -> dict:
    return {
        "request_id": request_id_of(request),
        "error": {"code": code, "message": message, "details": details},
    }


app = create_app()
