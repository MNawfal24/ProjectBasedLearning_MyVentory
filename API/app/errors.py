"""Structured error types, rendered as a JSON body by the handlers in main.py."""

from __future__ import annotations

from typing import Any

from fastapi import Request


def request_id_of(request: Request) -> str:
    """Request id stamped by the middleware; shared by response and error bodies."""
    return getattr(request.state, "request_id", "-")


class ApiError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details or {}


class UnknownModelError(ApiError):
    status_code = 404
    code = "unknown_model"


class InvalidInputError(ApiError):
    """Syntactically valid request that the model cannot use, e.g. an unknown outlet."""

    status_code = 422
    code = "invalid_input"


class ModelNotReadyError(ApiError):
    """The requested model has no usable artefact loaded in this process."""

    status_code = 503
    code = "model_not_ready"


class ArtifactError(ApiError):
    status_code = 500
    code = "artifact_error"


class EvaluationNotSupportedError(ApiError):
    status_code = 422
    code = "evaluation_not_supported"
