"""Appointment orchestration over the internal schedule API."""

from typing import Any

from app.core.logging import get_logger
from app.schemas.scheduling import BookingRequest
from app.services.base import BaseService

logger = get_logger(__name__)


class AppointmentService(BaseService):
    async def book(self, req: BookingRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "slotId": req.slot_id,
            "patientId": req.patient_id,
            "doctorId": req.doctor_id,
            "clinicId": req.clinic_id,
            "slotType": req.slot_type,
            "reason": req.reason,
            "notificationModes": ["EMAIL"],
            "sendInsuranceRequest": True,
        }
        logger.info(
            "Booking appointment slot=%s patient=%s doctor=%s clinic=%s",
            req.slot_id,
            req.patient_id,
            req.doctor_id,
            req.clinic_id,
        )
        return await self._clients.internal.appointment.book(payload)

    async def cancel(self, appointment_id: str) -> dict[str, Any]:
        logger.info("Cancelling appointment %s", appointment_id)
        return await self._clients.internal.appointment.cancel(appointment_id)
