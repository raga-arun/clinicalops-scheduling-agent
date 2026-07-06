"""Scheduling orchestration over the internal APIs."""

from app.schemas.scheduling import Appointment, BookingRequest
from app.services.base import BaseService


class SchedulingService(BaseService):
    async def book(self, req: BookingRequest) -> Appointment:
        raw = await self._clients.internal.scheduling.create_appointment(req.model_dump())
        return Appointment(**raw)

    async def cancel(self, appointment_id: str) -> Appointment:
        raw = await self._clients.internal.scheduling.cancel_appointment(appointment_id)
        return Appointment(**raw)
