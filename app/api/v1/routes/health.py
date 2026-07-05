"""Liveness and readiness endpoints."""

from app.api.route import create_router
from app.core.config import get_settings
from app.schemas.common import HealthResponse

router = create_router()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(service=settings.service_name, version=settings.service_version)
