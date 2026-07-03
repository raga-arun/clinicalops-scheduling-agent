"""Client for the internal Patient API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class PatientClient(BaseInternalClient):
    async def find_patient(self, *, query: str) -> list[dict[str, Any]]:
        data = await self.get("/patients", params={"q": query})
        return data or []

    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        return await self.get(f"/patients/{patient_id}")
