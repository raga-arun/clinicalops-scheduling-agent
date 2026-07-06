"""Client for the internal Scheduling module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class Scheduling(BaseInternalClient):
    async def search_slots(
        self, *, practitioner_id: str | None, start: str, end: str
    ) -> list[dict[str, Any]]:
        params = {"start": start, "end": end}
        if practitioner_id:
            params["practitioner"] = practitioner_id
        data = await self.get("/api/v1/common/slots", params=params)
        return data or []

    async def create_appointment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post("/api/v1/schedule/appointments", json=payload)

    async def cancel_appointment(self, appointment_id: str) -> dict[str, Any]:
        return await self.post(f"/api/v1/schedule/appointments/{appointment_id}/cancel")

    async def get_appointment(self, appointment_id: str) -> dict[str, Any]:
        return await self.get(f"/api/v1/schedule/appointments/{appointment_id}")
