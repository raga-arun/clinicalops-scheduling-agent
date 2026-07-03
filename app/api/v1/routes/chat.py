"""Chatbot endpoint."""

from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service, get_current_tenant
from app.core.context import TenantContext
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    tenant: TenantContext = Depends(get_current_tenant),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.handle(payload)
