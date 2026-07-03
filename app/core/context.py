"""Request-scoped tenant and request-id context via contextvars."""

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str


_tenant_ctx: ContextVar[TenantContext | None] = ContextVar("tenant_ctx", default=None)
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)


def set_tenant(ctx: TenantContext) -> None:
    _tenant_ctx.set(ctx)


def get_tenant() -> TenantContext | None:
    return _tenant_ctx.get()


def require_tenant() -> TenantContext:
    ctx = _tenant_ctx.get()
    if ctx is None:
        raise LookupError("Tenant context is not set for this request.")
    return ctx


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()
