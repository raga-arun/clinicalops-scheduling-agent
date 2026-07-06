"""Doctor/clinic config endpoints: doctors, clinics, and their mappings."""

from typing import Any

from app.api.route import create_router
from app.services.doctor_clinic_service import DoctorClinicService

router = create_router()


@router.get("/doctors", response_model=list[dict[str, Any]])
async def list_doctors() -> list[dict[str, Any]]:
    return await DoctorClinicService().list_doctors()


@router.get("/clinics", response_model=list[dict[str, Any]])
async def list_clinics() -> list[dict[str, Any]]:
    return await DoctorClinicService().list_clinics()


@router.get("/doctor-clinic-mapping", response_model=dict[str, Any])
async def doctor_clinic_mapping(
    doctor_id: str | None = None, clinic_id: str | None = None
) -> dict[str, Any]:
    return await DoctorClinicService().doctor_clinic_mapping(
        doctor_id=doctor_id, clinic_id=clinic_id
    )


@router.get("/visit-type-mapping", response_model=list[dict[str, Any]])
async def visit_type_mapping(
    doctor_id: str | None = None, clinic_id: str | None = None
) -> list[dict[str, Any]]:
    return await DoctorClinicService().visit_type_mapping(
        doctor_id=doctor_id, clinic_id=clinic_id
    )
