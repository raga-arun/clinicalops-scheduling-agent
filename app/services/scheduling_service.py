"""Scheduling orchestration over the internal APIs."""

from app.clients.registry import ClientRegistry
from app.schemas.scheduling import Appointment, BookingRequest, Slot, SlotSearchRequest


class SchedulingService:
    def __init__(self, clients: ClientRegistry):
        self._clients = clients

    async def find_slots(self, req: SlotSearchRequest) -> list[Slot]:
        raw = await self._clients.internal.scheduling.search_slots(
            practitioner_id=req.practitioner_id, start=req.start, end=req.end
        )
        return [Slot(**item) for item in raw]

    async def book(self, req: BookingRequest) -> Appointment:
        raw = await self._clients.internal.scheduling.create_appointment(req.model_dump())
        return Appointment(**raw)

    async def cancel(self, appointment_id: str) -> Appointment:
        raw = await self._clients.internal.scheduling.cancel_appointment(appointment_id)
        return Appointment(**raw)
