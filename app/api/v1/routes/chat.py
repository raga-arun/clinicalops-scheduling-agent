"""Chatbot endpoint."""

from app.api.route import create_router
from app.schemas.chat import ChatEnvelope, ChatRequest, UiDirectives
from app.services.chat_service import ChatService

router = create_router()


@router.post("", response_model=ChatEnvelope)
async def chat(payload: ChatRequest) -> ChatEnvelope:
    result = await ChatService().handle(payload)
    # ui_directives is a root-level sibling of `data`; services can populate it
    # to drive the client UI. Defaults to all-false here.
    return ChatEnvelope(data=result, ui_directives=UiDirectives())
