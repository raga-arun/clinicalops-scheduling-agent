"""Patient endpoints: lookup, get-or-create, appointment history."""

from typing import Any

from app.api.route import create_router
from app.schemas.patient import PatientLookup, PatientUpsert
from app.services.patient_service import PatientService

router = create_router()


@router.post("/patients/lookup", response_model=dict[str, Any] | None)
async def lookup_patient(payload: PatientLookup) -> dict[str, Any] | None:
    return await PatientService().lookup(payload)


@router.post("/patients", response_model=dict[str, Any])
async def upsert_patient(payload: PatientUpsert) -> dict[str, Any]:
    return await PatientService().get_or_create(payload)


@router.get("/patients/{patient_id}/appointments", response_model=list[dict[str, Any]])
async def patient_appointments(patient_id: str, active: bool = False) -> list[dict[str, Any]]:
    return await PatientService().appointments(patient_id, active=active)
