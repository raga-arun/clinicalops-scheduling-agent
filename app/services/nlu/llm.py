"""NLU engine for intent detection and entity extraction."""

from dataclasses import dataclass, field
from typing import Any

from app.schemas.chat import ChatMessage
from app.services.nlu.intents import Intent


@dataclass
class NLUResult:
    intent: Intent
    entities: dict[str, Any] = field(default_factory=dict)


class NLUEngine:
    async def detect(
        self, message: str, *, history: list[ChatMessage] | None = None
    ) -> NLUResult:
        return NLUResult(intent=Intent.UNKNOWN, entities={})
