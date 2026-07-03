"""Custom exceptions and FastAPI exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class MissingTenantError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "missing_tenant"


class InternalAPIError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "internal_api_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
