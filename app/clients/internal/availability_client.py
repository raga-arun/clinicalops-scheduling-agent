"""Client for the internal Availability API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class AvailabilityClient(BaseInternalClient):
    async def search(
        self, *, specialty: str | None, start: str, end: str
    ) -> list[dict[str, Any]]:
        params = {"start": start, "end": end}
        if specialty:
            params["specialty"] = specialty
        data = await self.get("/availability", params=params)
        return data or []
