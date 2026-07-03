"""Internal microservice client group backed by pooled httpx clients."""

import httpx

from app.clients.internal.availability_client import AvailabilityClient
from app.clients.internal.patient_client import PatientClient
from app.clients.internal.scheduling_client import SchedulingClient
from app.clients.lifecycle import ManagedClient
from app.core.config import Settings


class InternalAPIClients(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._pools: list[httpx.AsyncClient] = []
        self.scheduling: SchedulingClient
        self.patient: PatientClient
        self.availability: AvailabilityClient

    def _make_pool(self, base_url: str) -> httpx.AsyncClient:
        internal = self._settings.internal
        client = httpx.AsyncClient(
            base_url=base_url,
            timeout=internal.timeout_seconds,
            limits=httpx.Limits(
                max_connections=internal.max_connections,
                max_keepalive_connections=internal.max_keepalive_connections,
            ),
        )
        self._pools.append(client)
        return client

    async def startup(self) -> None:
        internal = self._settings.internal
        self.scheduling = SchedulingClient(
            self._make_pool(internal.scheduling_base_url), service_name="scheduling-api"
        )
        self.patient = PatientClient(
            self._make_pool(internal.patient_base_url), service_name="patient-api"
        )
        self.availability = AvailabilityClient(
            self._make_pool(internal.availability_base_url), service_name="availability-api"
        )

    async def shutdown(self) -> None:
        for pool in self._pools:
            await pool.aclose()
        self._pools.clear()
