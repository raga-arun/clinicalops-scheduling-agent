"""Chatbot request/response schemas."""

from typing import Any, Literal

from pydantic import Field

from app.schemas.base import Model


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
