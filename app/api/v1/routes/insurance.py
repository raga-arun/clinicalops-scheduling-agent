"""Insurance endpoint: submit a patient's insurance details."""

from typing import Any

from app.api.route import create_router
from app.schemas.insurance import InsuranceUpload
from app.services.insurance_service import InsuranceService

router = create_router()


@router.post("/patients/{patient_id}/insurance", response_model=dict[str, Any])
async def submit_insurance(patient_id: str, payload: InsuranceUpload) -> dict[str, Any]:
    return await InsuranceService().submit(patient_id, payload)
