"""FastAPI application factory and app instance."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.clients.provider import ClientProvider
from app.clients.registry import ClientRegistry
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.tenant import TenantMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    registry = ClientRegistry(settings)
    await registry.startup()
    ClientProvider.set(registry)
    try:
        yield
    finally:
        await registry.shutdown()
        ClientProvider.reset()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
