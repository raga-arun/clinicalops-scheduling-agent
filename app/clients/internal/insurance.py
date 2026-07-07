"""Client for the internal patient-insurance (schedule) module of the ClinicalOps API.

Provisional: the internal insurance-upload endpoint is not yet available, so this
path will 502 until the backend ships. Contract mirrors the schedule module.
"""

from typing import Any

from app.clients.internal.base import BaseInternalClient

PATIENTS = "/api/v1/schedule/patients"


class Insurance(BaseInternalClient):
    async def submit(self, patient_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post(f"{PATIENTS}/{patient_id}/insurance", json=payload)
