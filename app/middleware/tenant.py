"""Tenant extraction middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.context import TenantContext, set_tenant
from app.core.envelope import error_payload

_TENANT_EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        path = request.url.path

        if any(path.endswith(p) or path == p for p in _TENANT_EXEMPT_PREFIXES):
            return await call_next(request)

        tenant_id = request.headers.get(settings.tenant_header)

        if not tenant_id and settings.require_tenant:
            return JSONResponse(
                status_code=400,
                content=error_payload(
                    status_code=400,
                    message=f"Missing required header: {settings.tenant_header}",
                    error_code="MISSING_TENANT",
                    path=path,
                ),
            )

        if tenant_id:
            set_tenant(TenantContext(tenant_id=tenant_id))

        return await call_next(request)
