"""ADK tools exposing scheduling capabilities to the agent.

Each tool is a thin wrapper over a service. Tenancy is applied inside the client
layer (headers/key prefixes), so tools never receive or handle tenant data — they
focus purely on the task. The function docstrings double as the tool descriptions
the LLM reads, so keep them clear and action-oriented.
"""

from __future__ import annotations

from typing import Any

from app.schemas.insurance import InsuranceUpload
from app.schemas.patient import PatientLookup, PatientUpsert
from app.schemas.scheduling import BookingRequest
from app.services.appointment_service import AppointmentService
from app.services.doctor_clinic_service import DoctorClinicService
from app.services.insurance_service import InsuranceService
from app.services.patient_service import PatientService
from app.services.slots_service import SlotsService


async def list_doctors() -> list[dict[str, Any]]:
    """List the doctors available for scheduling at this practice."""
    return await DoctorClinicService().list_doctors()


async def list_clinics() -> list[dict[str, Any]]:
    """List the clinic locations available for scheduling at this practice."""
    return await DoctorClinicService().list_clinics()


async def list_doctor_clinics(
    doctor_id: str | None = None,
    clinic_id: str | None = None,
) -> dict[str, Any]:
    """Given exactly one of a doctor or a clinic, list the clinics that doctor
    works at, or the doctors who work at that clinic."""
    return await DoctorClinicService().doctor_clinic_mapping(
        doctor_id=doctor_id, clinic_id=clinic_id
    )


async def find_available_dates(
    doctor_id: str,
    clinic_id: str,
    slot_type: str = "NP",
) -> list[dict[str, Any]]:
    """Find the nearest upcoming dates that have open appointment slots for a
    doctor at a clinic. Use this to offer the patient a few date options."""
    return await SlotsService().nearest_dates_slots(
        doctor_id=doctor_id, clinic_id=clinic_id, slot_type=slot_type
    )


async def find_slots(
    doctor_id: str,
    clinic_id: str,
    date: str,
    slot_type: str = "NP",
) -> list[dict[str, Any]]:
    """List the open appointment time slots for a doctor at a clinic on a specific
    date (YYYY-MM-DD). Each slot includes the id needed to book it."""
    return await SlotsService().live_slots(
        doctor_id=doctor_id, clinic_id=clinic_id, date=date, slot_type=slot_type
    )


async def lookup_patient(
    phone: str,
    date_of_birth: str,
    name: str | None = None,
) -> dict[str, Any] | None:
    """Look up an existing patient by phone and date of birth (YYYY-MM-DD).
    Returns the patient record, or null if no match is found."""
    return await PatientService().lookup(
        PatientLookup(phone=phone, date_of_birth=date_of_birth, name=name)
    )


async def register_patient(
    name: str,
    date_of_birth: str,
    phone: str,
    gender: str | None = None,
    email: str | None = None,
) -> dict[str, Any]:
    """Register a new patient (or return the existing match) using their name,
    date of birth (YYYY-MM-DD), and phone. Returns the patient record with its id."""
    return await PatientService().get_or_create(
        PatientUpsert(
            name=name,
            date_of_birth=date_of_birth,
            phone=phone,
            gender=gender,
            email=email,
        )
    )


async def book_appointment(
    slot_id: str,
    patient_id: str,
    doctor_id: str,
    clinic_id: str,
    slot_type: str = "NP",
    reason: str | None = None,
) -> dict[str, Any]:
    """Book an appointment for a patient into a specific open slot. Requires the
    slot id, patient id, doctor id, and clinic id; include the reason for visit."""
    return await AppointmentService().book(
        BookingRequest(
            slot_id=slot_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            slot_type=slot_type,
            reason=reason,
        )
    )


async def cancel_appointment(appointment_id: str) -> dict[str, Any]:
    """Cancel an existing appointment by its id."""
    return await AppointmentService().cancel(appointment_id)


async def submit_insurance(
    patient_id: str,
    insurance_provider: str,
    insurance_member_id: str | None = None,
) -> dict[str, Any]:
    """Save a patient's insurance details (provider and optional member id)."""
    return await InsuranceService().submit(
        patient_id,
        InsuranceUpload(
            insurance_provider=insurance_provider,
            insurance_member_id=insurance_member_id,
        ),
    )


SCHEDULING_TOOLS = [
    list_doctors,
    list_clinics,
    list_doctor_clinics,
    find_available_dates,
    find_slots,
    lookup_patient,
    register_patient,
    book_appointment,
    cancel_appointment,
    submit_insurance,
]
