"""Doctor/clinic config orchestration over the internal Common API."""

from typing import Any

from app.core.exceptions import BadRequestError
from app.core.logging import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class DoctorClinicService(BaseService):
    async def list_doctors(self) -> list[dict[str, Any]]:
        logger.info("Listing doctors")
        return await self._clients.internal.doctor_clinic.list_doctors()

    async def list_clinics(self) -> list[dict[str, Any]]:
        logger.info("Listing clinics")
        return await self._clients.internal.doctor_clinic.list_clinics()

    async def doctor_clinic_mapping(
        self, *, doctor_id: str | None, clinic_id: str | None
    ) -> dict[str, Any]:
        if bool(doctor_id) == bool(clinic_id):
            raise BadRequestError("Provide exactly one of 'doctor_id' or 'clinic_id'")
        client = self._clients.internal.doctor_clinic
        if doctor_id:
            logger.info("Mapping clinics for doctor %s", doctor_id)
            return {"doctor_id": doctor_id, "clinics": await client.clinics_for_doctor(doctor_id)}
        logger.info("Mapping doctors for clinic %s", clinic_id)
        return {"clinic_id": clinic_id, "doctors": await client.doctors_for_clinic(clinic_id)}

    async def visit_type_mapping(
        self, *, doctor_id: str | None, clinic_id: str | None
    ) -> list[dict[str, Any]]:
        logger.info("Listing visit types (doctor=%s, clinic=%s)", doctor_id, clinic_id)
        return await self._clients.internal.doctor_clinic.visit_types(
            doctor_id=doctor_id, clinic_id=clinic_id
        )
