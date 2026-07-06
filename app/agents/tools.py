"""ADK tools exposing scheduling capabilities to the agent.

Each tool is a thin wrapper over ``SchedulingService``. Tenancy is applied
inside the client layer (headers/key prefixes), so tools never receive or
handle tenant data — they focus purely on the task.

The function docstrings double as the tool descriptions the LLM reads, so keep
them clear and action-oriented when implemented.

Skeleton only: signatures and intent are defined; bodies are unimplemented.
"""

from __future__ import annotations

from typing import Any

# Tools call the service layer, which reaches shared clients via ClientProvider:
#   from app.services.scheduling_service import SchedulingService


async def find_slots(
    start: str,
    end: str,
    practitioner_id: str | None = None,
) -> list[dict[str, Any]]:
    """Find available appointment slots in a time range for an optional practitioner."""
    # TODO: return await SchedulingService().find_slots(
    #     SlotSearchRequest(start=start, end=end, practitioner_id=practitioner_id)
    # )
    raise NotImplementedError


async def book_appointment(
    slot_id: str,
    patient_id: str,
) -> dict[str, Any]:
    """Book an appointment for a patient into a specific slot."""
    # TODO: return await SchedulingService().book(BookingRequest(...))
    raise NotImplementedError


async def cancel_appointment(appointment_id: str) -> dict[str, Any]:
    """Cancel an existing appointment by its id."""
    # TODO: return await SchedulingService().cancel(appointment_id)
    raise NotImplementedError
