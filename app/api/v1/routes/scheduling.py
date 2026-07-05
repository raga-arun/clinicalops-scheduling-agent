"""Structured scheduling endpoints."""

from app.api.route import create_router
from app.schemas.scheduling import Appointment, BookingRequest, Slot, SlotSearchRequest
from app.services.scheduling_service import SchedulingService

router = create_router()


@router.post("/slots/search", response_model=list[Slot])
async def search_slots(payload: SlotSearchRequest) -> list[Slot]:
    return await SchedulingService().find_slots(payload)


@router.post("/appointments", response_model=Appointment)
async def book_appointment(payload: BookingRequest) -> Appointment:
    return await SchedulingService().book(payload)


@router.post("/appointments/{appointment_id}/cancel", response_model=Appointment)
async def cancel_appointment(appointment_id: str) -> Appointment:
    return await SchedulingService().cancel(appointment_id)
