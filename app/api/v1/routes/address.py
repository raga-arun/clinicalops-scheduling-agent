"""Address endpoints backed by the external places service."""

from typing import Any

from fastapi import Query

from app.api.route import create_router
from app.services.address_service import AddressService

router = create_router()


@router.get("/address/places/autocomplete", response_model=list[dict[str, Any]])
async def autocomplete(
    input_text: str = Query(alias="input"),
    session_id: str | None = None,
) -> list[dict[str, Any]]:
    return await AddressService().autocomplete(input_text=input_text, session_id=session_id)


@router.get("/address/places/get", response_model=dict[str, Any])
async def get_place(
    place_id: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    return await AddressService().get_place(place_id, session_id=session_id)
