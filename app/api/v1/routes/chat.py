"""Chatbot endpoint."""

from fastapi import Depends

from app.api.deps import get_chat_service, get_current_tenant
from app.api.route import create_router
from app.core.context import TenantContext
from app.schemas.chat import ChatEnvelope, ChatRequest, UiDirectives
from app.services.chat_service import ChatService

router = create_router()


@router.post("", response_model=ChatEnvelope)
async def chat(
    payload: ChatRequest,
    tenant: TenantContext = Depends(get_current_tenant),
    service: ChatService = Depends(get_chat_service),
) -> ChatEnvelope:
    result = await service.handle(payload)
    # ui_directives is a root-level sibling of `data`; services can populate it
    # to drive the client UI. Defaults to all-false here.
    return ChatEnvelope(data=result, ui_directives=UiDirectives())
