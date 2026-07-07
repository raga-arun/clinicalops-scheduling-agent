"""Chatbot endpoint."""

from app.api.route import create_router
from app.schemas.chat import ChatEnvelope, ChatHistory, ChatRequest
from app.services.chat_service import ChatService

router = create_router()


@router.post("", response_model=ChatEnvelope)
async def chat(payload: ChatRequest) -> ChatEnvelope:
    result = await ChatService().handle(payload)
    # ui_directives is a root-level sibling of `data`, driving the client UI.
    return ChatEnvelope(data=result.response, ui_directives=result.ui_directives)


@router.get("/{session_id}", response_model=ChatHistory)
async def chat_history(session_id: str) -> ChatHistory:
    return await ChatService().history(session_id)
