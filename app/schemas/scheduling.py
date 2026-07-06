"""Scheduling request/response schemas."""

from app.schemas.base import Model


class BookingRequest(Model):
    slot_id: str
    patient_id: str
    reason: str | None = None


class Appointment(Model):
    appointment_id: str
    slot_id: str
    patient_id: str
    status: str
