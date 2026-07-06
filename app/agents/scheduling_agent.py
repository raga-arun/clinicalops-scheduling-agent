"""Definition of the scheduling ``LlmAgent``.

Skeleton: wires an ADK ``LlmAgent`` with instructions, a model, and the
scheduling tools. Requires ``google-adk`` (not yet a dependency).

ADK imports are deferred to build time so this module stays import-safe until
the dependency and implementation land.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids runtime ADK import
    from google.adk.agents import LlmAgent

# Model id for the agent's LLM. Source from config/Vault when implemented.
SCHEDULING_AGENT_MODEL = "gemini-2.0-flash"

SCHEDULING_AGENT_INSTRUCTION = (
    "You are a clinical scheduling assistant. Help users find, book, and cancel "
    "appointments using the provided tools. Ask for missing details before acting."
)


def build_scheduling_agent() -> "LlmAgent":
    """Construct the scheduling agent with its tools and model."""
    # TODO:
    #   from google.adk.agents import LlmAgent
    #   from app.agents.tools import book_appointment, cancel_appointment, find_slots
    #   return LlmAgent(
    #       name="scheduling_agent",
    #       model=SCHEDULING_AGENT_MODEL,
    #       instruction=SCHEDULING_AGENT_INSTRUCTION,
    #       tools=[find_slots, book_appointment, cancel_appointment],
    #   )
    raise NotImplementedError
