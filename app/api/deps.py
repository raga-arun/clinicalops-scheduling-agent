"""FastAPI dependencies for clients, services, and tenant resolution."""

from fastapi import Depends, Request

from app.clients.registry import ClientRegistry
from app.core.context import TenantContext, get_tenant
from app.core.exceptions import MissingTenantError
from app.services.chat_service import ChatService
from app.services.scheduling_service import SchedulingService


def get_clients(request: Request) -> ClientRegistry:
    return request.app.state.clients


def get_current_tenant() -> TenantContext:
    tenant = get_tenant()
    if tenant is None:
        raise MissingTenantError("Tenant context is not available.")
    return tenant


def get_chat_service(clients: ClientRegistry = Depends(get_clients)) -> ChatService:
    return ChatService(clients)


def get_scheduling_service(
    clients: ClientRegistry = Depends(get_clients),
) -> SchedulingService:
    return SchedulingService(clients)
