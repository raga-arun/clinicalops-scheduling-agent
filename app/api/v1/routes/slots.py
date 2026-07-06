"""Slot availability endpoints: live slots, month overview, nearest dates."""

from typing import Any

from app.api.route import create_router
from app.services.slots_service import SlotsService

router = create_router()


@router.get("/appointments/slots", response_model=list[dict[str, Any]])
async def live_slots(
    doctor_id: str,
    clinic_id: str,
    date: str,
    slot_type: str = "NP",
    slots_count: int = 20,
) -> list[dict[str, Any]]:
    return await SlotsService().live_slots(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        date=date,
        slot_type=slot_type,
        slots_count=slots_count,
    )


@router.get("/appointments/month-slots", response_model=dict[str, Any])
async def month_slots(
    doctor_id: str,
    clinic_id: str,
    start_date: str,
    slot_type: str = "NP",
) -> dict[str, Any]:
    return await SlotsService().month_slots(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        start_date=start_date,
        slot_type=slot_type,
    )


@router.get("/appointments/nearest-dates-slots", response_model=list[dict[str, Any]])
async def nearest_dates_slots(
    doctor_id: str,
    clinic_id: str,
    slot_type: str = "NP",
    count: int = 3,
) -> list[dict[str, Any]]:
    return await SlotsService().nearest_dates_slots(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        slot_type=slot_type,
        count=count,
    )
