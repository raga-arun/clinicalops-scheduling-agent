"""External phone-verification (OTP) service client.

Proxies a separate service that owns Twilio Verify, the OTP send/confirm state,
and any patient token issued on success. This client forwards tenant + trace
headers for correlation only — no X-Agent-Type, and no ClinicalOps envelope
unwrapping: the raw provider payload (``status``/``message``/``verification``)
is passed straight back so the legacy chatbot UI keeps working unchanged.
"""

from typing import Any

import httpx

from app.clients.lifecycle import ManagedClient
from app.core.config import Settings, get_settings
from app.core.context import get_tenant, get_trace_id
from app.core.exceptions import InternalAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)

PHONE = "/verification/phone"


class Verification(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings.verification
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

    async def _post(self, path: str, json: dict[str, Any]) -> Any:
        assert self._client is not None
        try:
            response = await self._client.post(path, json=json, headers=self._headers())
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Verification service returned %s for %s", exc.response.status_code, path
            )
            raise InternalAPIError(
                f"verification responded with {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Verification service call failed: %s", exc)
            raise InternalAPIError("verification is unreachable") from exc
        return response.json() if response.content else {}

    async def start(
        self, *, session_id: str, channel: str, force_resend: bool
    ) -> dict[str, Any]:
        return await self._post(
            f"{PHONE}/start",
            {"sessionId": session_id, "channel": channel, "forceResend": force_resend},
        )

    async def confirm(self, *, session_id: str, code: str) -> dict[str, Any]:
        return await self._post(f"{PHONE}/confirm", {"sessionId": session_id, "code": code})

    async def update(self, *, session_id: str, new_phone_number: str) -> dict[str, Any]:
        return await self._post(
            f"{PHONE}/update",
            {"sessionId": session_id, "newPhoneNumber": new_phone_number},
        )
