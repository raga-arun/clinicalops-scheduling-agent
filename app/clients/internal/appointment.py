"""Client for the internal Appointments (schedule) module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

APPOINTMENTS = "/api/v1/schedule/appointments"


class Appointments(BaseInternalClient):
    async def book(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post(APPOINTMENTS, json=payload)

    async def cancel(self, appointment_id: str) -> dict[str, Any]:
        return await self.post(f"{APPOINTMENTS}/{appointment_id}/cancel")

    async def get_by_id(self, appointment_id: str) -> dict[str, Any]:
        return await self.get(f"{APPOINTMENTS}/{appointment_id}")

    async def update_reason(self, appointment_id: str, reason: str) -> dict[str, Any]:
        return await self.put(f"{APPOINTMENTS}/{appointment_id}", json={"reason": reason})
