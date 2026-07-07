"""App-scoped access to the shared ADK agent ``Runner``.

The ``LlmAgent``, its model client, and the ``Runner`` are heavy and are built
once at application startup, then borrowed per request — mirroring
``ClientProvider`` for infrastructure clients. Services must never construct a
runner per request.

Sessions use ADK's in-memory ``InMemorySessionService``: process-local and not
durable across workers/restarts. A durable session backend is deferred.
"""

from __future__ import annotations

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from app.agents.scheduling_agent import build_scheduling_agent

APP_NAME = "clinicalops-scheduling-agent"


class AgentProvider:
    """Holds the process-wide ADK ``Runner`` created at application startup."""

    _runner: Runner | None = None

    @classmethod
    def build(cls) -> None:
        """Construct the agent and Runner once, during app startup."""
        cls._runner = Runner(
            app_name=APP_NAME,
            agent=build_scheduling_agent(),
            session_service=InMemorySessionService(),
        )

    @classmethod
    def get(cls) -> Runner:
        if cls._runner is None:
            raise RuntimeError(
                "Agent runner is not initialized; build it during app startup."
            )
        return cls._runner

    @classmethod
    def reset(cls) -> None:
        cls._runner = None
