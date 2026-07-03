"""Client for the internal Scheduling API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class SchedulingClient(BaseInternalClient):
    async def search_slots(
        self, *, practitioner_id: str | None, start: str, end: str
    ) -> list[dict[str, Any]]:
        params = {"start": start, "end": end}
        if practitioner_id:
            params["practitioner"] = practitioner_id
        data = await self.get("/slots", params=params)
        return data or []

    async def create_appointment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post("/appointments", json=payload)

    async def cancel_appointment(self, appointment_id: str) -> dict[str, Any]:
        return await self.post(f"/appointments/{appointment_id}/cancel")

    async def get_appointment(self, appointment_id: str) -> dict[str, Any]:
        return await self.get(f"/appointments/{appointment_id}")
