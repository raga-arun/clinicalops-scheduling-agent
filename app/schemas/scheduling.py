"""Appointment request schemas."""

from app.schemas.base import Model


class BookingRequest(Model):
    slot_id: str
    patient_id: str
    doctor_id: str
    clinic_id: str
    slot_type: str = "NP"
    reason: str | None = None
