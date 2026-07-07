"""Patient-insurance orchestration over the internal schedule API."""

from typing import Any

from app.core.logging import get_logger
from app.schemas.insurance import InsuranceUpload
from app.services.base import BaseService

logger = get_logger(__name__)


class InsuranceService(BaseService):
    async def submit(self, patient_id: str, req: InsuranceUpload) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "insuranceProvider": req.insurance_provider,
            "insuranceMemberId": req.insurance_member_id,
        }
        logger.info(
            "Submitting insurance patient=%s provider=%s",
            patient_id,
            req.insurance_provider,
        )
        return await self._clients.internal.insurance.submit(patient_id, payload)
