"""Chatbot orchestration: drives the ADK scheduling agent.

Skeleton: ``handle`` borrows the shared ADK ``Runner`` (built once at startup)
and translates its events into a ``ChatResponse``. The agent decides which
scheduling tool to call; tenancy is applied inside the client layer, so this
service never touches tenant data.
"""

import uuid

from app.agents.provider import AgentProvider
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.base import BaseService


class ChatService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        # Borrow the shared runner; never build one per request.
        self._runner = AgentProvider.get()

    async def handle(self, req: ChatRequest) -> ChatResponse:
        session_id = req.session_id or uuid.uuid4().hex
        # TODO: drive the agent and collect the final reply + structured data:
        #   events = self._runner.run_async(
        #       user_id=..., session_id=session_id, new_message=req.message
        #   )
        #   async for event in events:
        #       ... accumulate the final response ...
        raise NotImplementedError
