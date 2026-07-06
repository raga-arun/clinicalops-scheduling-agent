"""Base async HTTP client for internal microservices."""

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.context import get_tenant, get_trace_id
from app.core.exceptions import InternalAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseInternalClient:
    def __init__(self, client: httpx.AsyncClient, *, service_name: str):
        self._client = client
        self._service_name = service_name

    def _context_headers(self) -> dict[str, str]:
        settings = get_settings()
        headers: dict[str, str] = {"X-Agent-Type": settings.agent_type}
        tenant = get_tenant()
        if tenant:
            headers[settings.tenant_header] = tenant.tenant_id
        trace_id = get_trace_id()
        if trace_id:
            headers[settings.trace_id_header] = trace_id
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        headers = self._context_headers()
        try:
            response = await self._client.request(
                method, path, params=params, json=json, headers=headers
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Internal API %s returned %s for %s %s",
                self._service_name,
                exc.response.status_code,
                method,
                path,
            )
            raise InternalAPIError(
                f"{self._service_name} responded with {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Internal API %s call failed: %s", self._service_name, exc)
            raise InternalAPIError(f"{self._service_name} is unreachable") from exc

        if not response.content:
            return None
        return response.json()

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Any:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, **kwargs)
