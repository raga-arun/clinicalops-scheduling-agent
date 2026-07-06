"""Client for the internal Patient/Schedule module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class Patient(BaseInternalClient):
    async def find_patient(self, *, query: str) -> list[dict[str, Any]]:
        data = await self.get("/api/v1/schedule/patients", params={"q": query})
        return data or []

    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        return await self.get(f"/api/v1/schedule/patients/{patient_id}")
