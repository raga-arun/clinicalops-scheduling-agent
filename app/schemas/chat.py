"""Chatbot request/response schemas."""

from typing import Any, Literal

from pydantic import Field

from app.schemas.base import Model
from app.schemas.common import SuccessResponse


class ChatMessage(Model):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(Model):
    session_id: str | None = None
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(Model):
    session_id: str
    reply: str
    intent: str | None = None
    data: dict[str, Any] | None = None


class ChatHistory(Model):
    session_id: str
    messages: list[ChatMessage] = Field(default_factory=list)


class UiDirectives(Model):
    show_selections: bool = False
    show_calendly: bool = False
    show_rating: bool = False
    show_reason_for_visit: bool = False
    show_insurance_upload: bool = False


class ChatEnvelope(SuccessResponse[ChatResponse]):
    """Chat success envelope with a root-level ``ui_directives`` sibling of ``data``."""

    ui_directives: UiDirectives = Field(default_factory=UiDirectives)
