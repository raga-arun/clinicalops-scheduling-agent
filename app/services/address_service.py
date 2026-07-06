"""Address autocomplete/details orchestration over the external places service."""

from typing import Any

from app.core.logging import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class AddressService(BaseService):
    async def autocomplete(
        self, *, input_text: str, session_id: str | None
    ) -> list[dict[str, Any]]:
        logger.info("Address autocomplete (session=%s)", session_id)
        return await self._clients.places.autocomplete(
            input_text=input_text, session_id=session_id
        )

    async def get_place(self, place_id: str, *, session_id: str | None) -> dict[str, Any]:
        logger.info("Address details lookup for place %s", place_id)
        return await self._clients.places.get_place(place_id, session_id=session_id)
