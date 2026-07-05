"""Custom exceptions and exception handlers producing the error envelope.

Normalizes every error path — application errors, request validation, FastAPI /
Starlette HTTP errors (404, 405, explicit HTTPException), and uncaught
exceptions — into the standard ``ErrorResponse`` shape.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.envelope import error_code_from_status, error_payload
from app.core.logging import get_logger
from app.schemas.common import FieldError

logger = get_logger(__name__)

_VALIDATION_LOC_SKIP = {"body", "query", "path", "header", "cookie"}


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, *, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code


class MissingTenantError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "MISSING_TENANT"


class InternalAPIError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "INTERNAL_API_ERROR"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                status_code=exc.status_code,
                message=exc.message,
                error_code=exc.error_code,
                path=request.url.path,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            FieldError(
                field=_field_from_loc(err.get("loc", ())),
                rejected_value=err.get("input"),
                message=err.get("msg", ""),
            )
            for err in exc.errors()
        ]
        message = errors[0].message if errors else "Validation failed"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_payload(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=message,
                error_code="BAD_REQUEST",
                path=request.url.path,
                errors=errors,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                status_code=exc.status_code,
                message=message,
                error_code=error_code_from_status(exc.status_code),
                path=request.url.path,
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            status_code=code,
            content=error_payload(
                status_code=code,
                message="Internal server error",
                error_code=error_code_from_status(code),
                path=request.url.path,
            ),
        )


def _field_from_loc(loc: tuple) -> str | None:
    parts = [str(item) for item in loc if item not in _VALIDATION_LOC_SKIP]
    return ".".join(parts) if parts else None
