"""Client for the internal Common module (doctors, clinics, visit types)."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

_LIST_PARAMS = {"page": 0, "size": 200}


class DoctorClinic(BaseInternalClient):
    @staticmethod
    def _items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, dict) and "content" in payload:
            return payload["content"] or []
        return payload or []

    async def list_doctors(self) -> list[dict[str, Any]]:
        return self._items(await self.get("/api/v1/common/doctors", params=dict(_LIST_PARAMS)))

    async def list_clinics(self) -> list[dict[str, Any]]:
        return self._items(await self.get("/api/v1/common/clinics", params=dict(_LIST_PARAMS)))

    async def clinics_for_doctor(self, doctor_id: str) -> list[dict[str, Any]]:
        return self._items(
            await self.get(f"/api/v1/common/doctors/{doctor_id}/clinics", params=dict(_LIST_PARAMS))
        )

    async def doctors_for_clinic(self, clinic_id: str) -> list[dict[str, Any]]:
        return self._items(
            await self.get(f"/api/v1/common/clinics/{clinic_id}/doctors", params=dict(_LIST_PARAMS))
        )

    async def visit_types(
        self, *, doctor_id: str | None, clinic_id: str | None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = dict(_LIST_PARAMS)
        if doctor_id:
            params["doctorId"] = doctor_id
        if clinic_id:
            params["clinicId"] = clinic_id
        return self._items(await self.get("/api/v1/common/visit-types", params=params))
