"""Standard success and error response envelopes."""

from typing import Any

from app.schemas.base import Model


class HealthResponse(Model):
    status: str = "ok"
    service: str
    version: str


class SuccessResponse[T](Model):
    """
        Envelope for all 2xx responses.
    """

    status: str = "success"
    status_code: int = 200
    message: str = "Request successful"
    data: T | None = None


class FieldError(Model):
    field: str | None = None
    rejected_value: Any | None = None
    message: str


class ErrorResponse(Model):
    status: str = "error"
    status_code: int
    message: str
    error_code: str
    path: str
    errors: list[FieldError] | None = None
