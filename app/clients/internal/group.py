"""Internal ClinicalOps API client group backed by one pooled httpx client."""

import httpx

from app.clients.internal.doctor_clinic import DoctorClinic
from app.clients.internal.patient import Patient
from app.clients.internal.scheduling import Scheduling
from app.clients.lifecycle import ManagedClient
from app.core.config import Settings


class InternalAPIClients(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: httpx.AsyncClient | None = None
        self.scheduling: Scheduling
        self.patient: Patient
        self.doctor_clinic: DoctorClinic

    async def startup(self) -> None:
        internal = self._settings.internal
        self._client = httpx.AsyncClient(
            base_url=internal.api_url,
            timeout=internal.timeout_seconds,
            limits=httpx.Limits(
                max_connections=internal.max_connections,
                max_keepalive_connections=internal.max_keepalive_connections,
            ),
        )
        self.scheduling = Scheduling(self._client, service_name="scheduling")
        self.patient = Patient(self._client, service_name="patient")
        self.doctor_clinic = DoctorClinic(self._client, service_name="common")

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
