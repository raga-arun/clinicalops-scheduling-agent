"""Appointment endpoints: book and cancel."""

from typing import Any

from app.api.route import create_router
from app.schemas.scheduling import BookingRequest
from app.services.appointment_service import AppointmentService

router = create_router()


@router.post("/appointments", response_model=dict[str, Any])
async def book_appointment(payload: BookingRequest) -> dict[str, Any]:
    return await AppointmentService().book(payload)


@router.post("/appointments/{appointment_id}/cancel", response_model=dict[str, Any])
async def cancel_appointment(appointment_id: str) -> dict[str, Any]:
    return await AppointmentService().cancel(appointment_id)
