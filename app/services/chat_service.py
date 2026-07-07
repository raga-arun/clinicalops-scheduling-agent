"""Chatbot orchestration: drives the ADK scheduling agent.

``handle`` borrows the shared ADK ``Runner`` (built once at startup), runs one
conversation turn, and translates the event stream into a reply plus the UI
directives derived from which tools the agent used. Tenancy is applied inside
the client layer, so this service never touches tenant data.
"""

import uuid
from dataclasses import dataclass

from google.genai import types

from app.agents.provider import APP_NAME, AgentProvider
from app.core.exceptions import BadRequestError
from app.core.logging import get_logger
from app.schemas.chat import ChatHistory, ChatMessage, ChatRequest, ChatResponse, UiDirectives

logger = get_logger(__name__)

USER_ID = "patient"
SELECTION_TOOLS = {"list_doctors", "list_clinics", "list_doctor_clinics"}
CALENDAR_TOOLS = {"find_available_dates", "find_slots"}
_ROLE_MAP = {"user": "user", "model": "assistant"}


@dataclass
class ChatResult:
    response: ChatResponse
    ui_directives: UiDirectives


def _ui_directives(tool_names: set[str]) -> UiDirectives:
    return UiDirectives(
        show_selections=bool(tool_names & SELECTION_TOOLS),
        show_calendly=bool(tool_names & CALENDAR_TOOLS),
    )


class ChatService:
    def __init__(self) -> None:
        self._runner = AgentProvider.get()

    async def _ensure_session(self, session_id: str) -> None:
        service = self._runner.session_service
        existing = await service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        if existing is None:
            await service.create_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=session_id
            )

    async def handle(self, req: ChatRequest) -> ChatResult:
        session_id = req.session_id or uuid.uuid4().hex
        await self._ensure_session(session_id)

        content = types.Content(role="user", parts=[types.Part(text=req.message)])
        reply = ""
        tool_names: set[str] = set()

        logger.info("Chat turn session=%s", session_id)
        async for event in self._runner.run_async(
            user_id=USER_ID, session_id=session_id, new_message=content
        ):
            for call in event.get_function_calls():
                tool_names.add(call.name)
            if event.is_final_response() and event.content and event.content.parts:
                reply = "".join(
                    part.text for part in event.content.parts if part.text
                ).strip()

        return ChatResult(
            response=ChatResponse(session_id=session_id, reply=reply),
            ui_directives=_ui_directives(tool_names),
        )

    async def history(self, session_id: str) -> ChatHistory:
        session = await self._runner.session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        if session is None:
            raise BadRequestError(f"Unknown session: {session_id}")

        messages: list[ChatMessage] = []
        for event in session.events:
            role = _ROLE_MAP.get(getattr(event.content, "role", ""), None)
            if role is None or not event.content or not event.content.parts:
                continue
            text = "".join(part.text for part in event.content.parts if part.text).strip()
            if text:
                messages.append(ChatMessage(role=role, content=text))
        return ChatHistory(session_id=session_id, messages=messages)
