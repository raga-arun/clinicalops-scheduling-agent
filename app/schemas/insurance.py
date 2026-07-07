"""Insurance request schemas."""

from app.schemas.base import Model


class InsuranceUpload(Model):
    insurance_provider: str
    insurance_member_id: str | None = None
