"""Client for the internal Scheduling slots (Common module) of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "content" in payload:
        return payload["content"] or []
    return payload or []


class Scheduling(BaseInternalClient):
    async def slot_counts(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        start_date: str,
        end_date: str,
        slot_type: str = "NP",
    ) -> list[dict[str, Any]]:
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "slotType": slot_type,
            "status": "FREE",
            "doctorId": doctor_id,
            "clinicId": clinic_id,
        }
        return _as_list(await self.get("/api/v1/common/slots/count", params=params))

    async def live_slots(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        date: str,
        slot_type: str = "NP",
        slots_count: int = 20,
    ) -> list[dict[str, Any]]:
        params = {
            "slotType": slot_type,
            "doctorId": doctor_id,
            "clinicId": clinic_id,
            "date": date,
            "page": 0,
            "size": slots_count,
            "sort": "date,ASC",
        }
        return _as_list(await self.get("/api/v1/common/slots/live-slots", params=params))
