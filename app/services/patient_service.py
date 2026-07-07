"""Patient orchestration over the internal schedule API."""

from typing import Any

from app.core.logging import get_logger
from app.schemas.patient import PatientLookup, PatientUpsert
from app.services.base import BaseService

logger = get_logger(__name__)

_ACTIVE_STATUS = "SCHEDULED"


class PatientService(BaseService):
    async def lookup(self, req: PatientLookup) -> dict[str, Any] | None:
        logger.info("Patient lookup by phone+dob")
        return await self._clients.internal.patient.search(
            phone=req.phone, date_of_birth=req.date_of_birth, name=req.name
        )

    async def get_or_create(self, req: PatientUpsert) -> dict[str, Any]:
        existing = await self._clients.internal.patient.search(
            phone=req.phone, date_of_birth=req.date_of_birth
        )
        if existing:
            logger.info("Found existing patient %s", existing.get("id"))
            return existing
        logger.info("Creating new patient")
        return await self._clients.internal.patient.create(
            name=req.name,
            date_of_birth=req.date_of_birth,
            phone=req.phone,
            gender=req.gender,
            email=req.email,
        )

    async def appointments(self, patient_id: str, *, active: bool = False) -> list[dict[str, Any]]:
        logger.info("Fetching appointments for patient %s active=%s", patient_id, active)
        items = await self._clients.internal.patient.appointments(patient_id)
        if active:
            return [
                a
                for a in items
                if a.get("isFutureAppointment") is True and a.get("status") == _ACTIVE_STATUS
            ]
        return items
