"""Client for the internal Patient (schedule) module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

PATIENTS = "/api/v1/schedule/patients"


def _content(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "content" in payload:
        return payload["content"] or []
    return payload or []


class Patient(BaseInternalClient):
    async def search(
        self, *, phone: str, date_of_birth: str, name: str | None = None
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {"phone": phone, "dob": date_of_birth, "page": 0, "size": 20}
        if name is not None:
            params["name"] = name
        content = _content(await self.get(PATIENTS, params=params))
        return content[0] if content else None

    async def create(
        self,
        *,
        name: str,
        date_of_birth: str,
        phone: str,
        gender: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "dateOfBirth": date_of_birth, "phone": phone}
        if gender is not None:
            payload["gender"] = gender
        if email is not None:
            payload["email"] = email
        return await self.post(PATIENTS, json=payload)

    async def get_by_id(self, patient_id: str) -> dict[str, Any]:
        return await self.get(f"{PATIENTS}/{patient_id}")

    async def appointments(
        self, patient_id: str, *, size: int = 20, sort: str = "appointmentDatetime"
    ) -> list[dict[str, Any]]:
        params = {"size": size, "sort": sort}
        return _content(await self.get(f"{PATIENTS}/{patient_id}/appointments", params=params))
