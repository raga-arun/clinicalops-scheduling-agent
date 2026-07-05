"""Chatbot orchestration: NLU plus internal scheduling calls."""

import uuid

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.base import BaseService
from app.services.nlu.intents import Intent
from app.services.nlu.llm import NLUEngine
from app.services.scheduling_service import SchedulingService


class ChatService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._nlu = NLUEngine()
        self._scheduling = SchedulingService()

    async def handle(self, req: ChatRequest) -> ChatResponse:
        session_id = req.session_id or uuid.uuid4().hex
        result = await self._nlu.detect(req.message, history=req.history)

        if result.intent == Intent.FIND_SLOTS:
            reply = "Let me look for available slots."
        elif result.intent == Intent.BOOK_APPOINTMENT:
            reply = "I can book that once I have the details."
        elif result.intent == Intent.CANCEL_APPOINTMENT:
            reply = "I can help you cancel an appointment."
        else:
            reply = "I can help you find, book, or cancel appointments."

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            intent=result.intent.value,
            data=result.entities,
        )
