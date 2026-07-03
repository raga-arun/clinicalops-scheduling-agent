"""Scheduling request/response schemas."""

from pydantic import BaseModel


class SlotSearchRequest(BaseModel):
    practitioner_id: str | None = None
    specialty: str | None = None
    start: str
    end: str


class Slot(BaseModel):
    slot_id: str
    practitioner_id: str
    start: str
    end: str
    status: str


class BookingRequest(BaseModel):
    slot_id: str
    patient_id: str
    reason: str | None = None


class Appointment(BaseModel):
    appointment_id: str
    slot_id: str
    patient_id: str
    status: str
