"""Builders for the standard error response envelope.

Shared by the exception handlers and the tenant middleware so every error on the
wire has the same shape. Success envelopes are handled by
``app.api.route.EnvelopeRoute``.
"""

from http import HTTPStatus
from typing import Any

from app.schemas.common import ErrorResponse, FieldError


def error_code_from_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).name
    except ValueError:
        return "ERROR"


def error_payload(
    *,
    status_code: int,
    message: str,
    error_code: str,
    path: str,
    errors: list[FieldError] | None = None,
) -> dict[str, Any]:
    return ErrorResponse(
        status_code=status_code,
        message=message,
        error_code=error_code,
        path=path,
        errors=errors,
    ).model_dump(by_alias=True, exclude_none=True)
