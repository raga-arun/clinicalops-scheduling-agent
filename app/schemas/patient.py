"""Patient request schemas."""

from app.schemas.base import Model


class PatientLookup(Model):
    phone: str
    date_of_birth: str
    name: str | None = None


class PatientUpsert(Model):
    name: str
    date_of_birth: str
    phone: str
    gender: str | None = None
    email: str | None = None
