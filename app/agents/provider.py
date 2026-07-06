"""App-scoped access to the shared ADK agent ``Runner``.

The ``LlmAgent``, its model client, and the ``Runner`` are heavy and are built
once at application startup, then borrowed per request — mirroring
``ClientProvider`` for infrastructure clients. Services must never construct a
runner per request.

ADK imports are deferred to build time so this module stays import-safe until
the dependency and implementation land.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids runtime ADK import
    from google.adk.runners import Runner


class AgentProvider:
    """Holds the process-wide ADK ``Runner`` created at application startup."""

    _runner: "Runner | None" = None

    @classmethod
    def build(cls) -> None:
        """Construct the agent and Runner once, during app startup."""
        # TODO:
        #   from google.adk.runners import Runner
        #   from google.adk.sessions import InMemorySessionService  # or Redis-backed
        #   from app.agents.scheduling_agent import build_scheduling_agent
        #   cls._runner = Runner(
        #       agent=build_scheduling_agent(),
        #       app_name="clinicalops-scheduling-agent",
        #       session_service=InMemorySessionService(),
        #   )
        raise NotImplementedError

    @classmethod
    def get(cls) -> "Runner":
        if cls._runner is None:
            raise RuntimeError(
                "Agent runner is not initialized; build it during app startup."
            )
        return cls._runner

    @classmethod
    def reset(cls) -> None:
        cls._runner = None
