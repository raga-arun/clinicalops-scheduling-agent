"""Scheduling request/response schemas."""

from app.schemas.base import Model


class SlotSearchRequest(Model):
    practitioner_id: str | None = None
    specialty: str | None = None
    start: str
    end: str


class Slot(Model):
    slot_id: str
    practitioner_id: str
    start: str
    end: str
    status: str


class BookingRequest(Model):
    slot_id: str
    patient_id: str
    reason: str | None = None


class Appointment(Model):
    appointment_id: str
    slot_id: str
    patient_id: str
    status: str
