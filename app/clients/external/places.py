"""External places service client (address autocomplete + details).

Proxies a separate service that owns Google Places and its API key. This client
forwards tenant + trace headers for correlation only — no X-Agent-Type, no
ClinicalOps envelope unwrapping.
"""

from typing import Any

import httpx

from app.clients.lifecycle import ManagedClient
from app.core.config import Settings, get_settings
from app.core.context import get_tenant, get_trace_id
from app.core.exceptions import InternalAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Places(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings.places
        self._client: httpx.AsyncClient | None = None

    async def startup(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self._settings.base_url, timeout=self._settings.timeout_seconds
        )

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _headers(self) -> dict[str, str]:
        settings = get_settings()
        headers: dict[str, str] = {}
        tenant = get_tenant()
        if tenant:
            headers[settings.tenant_header] = tenant.tenant_id
        trace_id = get_trace_id()
        if trace_id:
            headers[settings.trace_id_header] = trace_id
        return headers

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        assert self._client is not None
        try:
            response = await self._client.get(path, params=params, headers=self._headers())
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("Places service returned %s for %s", exc.response.status_code, path)
            raise InternalAPIError(
                f"places responded with {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Places service call failed: %s", exc)
            raise InternalAPIError("places is unreachable") from exc
        return response.json() if response.content else None

    async def autocomplete(
        self, *, input_text: str, session_id: str | None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"input": input_text}
        if session_id:
            params["sessionId"] = session_id
        return await self._get("/places/autocomplete", params) or []

    async def get_place(self, place_id: str, *, session_id: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if session_id:
            params["sessionId"] = session_id
        return await self._get(f"/places/{place_id}", params) or {}
