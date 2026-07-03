"""Structured scheduling endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_tenant, get_scheduling_service
from app.core.context import TenantContext
from app.schemas.scheduling import Appointment, BookingRequest, Slot, SlotSearchRequest
from app.services.scheduling_service import SchedulingService

router = APIRouter()


@router.post("/slots/search", response_model=list[Slot])
async def search_slots(
    payload: SlotSearchRequest,
    tenant: TenantContext = Depends(get_current_tenant),
    service: SchedulingService = Depends(get_scheduling_service),
) -> list[Slot]:
    return await service.find_slots(payload)


@router.post("/appointments", response_model=Appointment)
async def book_appointment(
    payload: BookingRequest,
    tenant: TenantContext = Depends(get_current_tenant),
    service: SchedulingService = Depends(get_scheduling_service),
) -> Appointment:
    return await service.book(payload)


@router.post("/appointments/{appointment_id}/cancel", response_model=Appointment)
async def cancel_appointment(
    appointment_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    service: SchedulingService = Depends(get_scheduling_service),
) -> Appointment:
    return await service.cancel(appointment_id)
