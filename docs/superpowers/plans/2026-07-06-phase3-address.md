# Phase 3 — Address (external places service) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `/api/v1/address/places/autocomplete` and `/api/v1/address/places/get` as an
`address` route → `AddressService` → `Places` external client that proxies a separate places
service. This agent holds **no Google key** and does no Google-specific formatting.

**Architecture:** `Places` is a `ManagedClient` with its own pooled `httpx.AsyncClient` (base URL
`PLACES_API_URL`), registered next to internal/vault/redis. It forwards tenant + trace headers for
correlation but does not send `X-Agent-Type` and does not unwrap the ClinicalOps envelope. The
service and routes are thin pass-throughs.

**Tech Stack:** FastAPI, httpx, pydantic-settings, uv (Python 3.14).

## Global Constraints

- No Google Maps key in this service — the external places service owns Google.
- Routes use `create_router()`; included with no extra prefix (paths carry `/address/...`).
- Services own logic; routes stay thin; correlation headers live in the client.
- All imports at top of file. No unnecessary comments. No secret values in configs.
- No test files this pass — verify via import, `ruff`, app boot, and `curl` (a 502 from the
  unreachable fake places host or a 422 from missing query params both prove the wiring).
- Commit messages: plain conventional-commit, **no AI attribution / Co-Authored-By trailer**.

## Reference (spec)

`docs/superpowers/specs/2026-07-06-scheduling-agent-migration-design.md` §2 (address rows), §8, §10.

---

### Task 1: `PLACES_API_URL` config + `.env.example`

**Files:**
- Modify: `app/core/config.py`
- Modify: `.env.example`

**Interfaces:**
- Produces: `Settings.places.base_url: str`, `Settings.places.timeout_seconds: float`.

- [ ] **Step 1: Add `PlacesSettings` and wire it into `Settings`**

In `app/core/config.py`, add after `RedisSettings`:

```python
class PlacesSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PLACES_", extra="ignore")

    base_url: str = "http://places-api.internal"
    timeout_seconds: float = 10.0
```

Then add the field to `Settings` (after `redis: RedisSettings = ...`):

```python
    places: PlacesSettings = Field(default_factory=PlacesSettings)
```

- [ ] **Step 2: Add the block to `.env.example`** (after the Redis block)

```bash
# --- External places service (owns Google Places + key; NOT this service) ---
PLACES_API_URL=http://places-api.internal
PLACES_TIMEOUT_SECONDS=10
```

- [ ] **Step 3: Verify**

Run: `uv run python -c "from app.core.config import get_settings; print(get_settings().places.base_url)"`
Expected: prints `http://places-api.internal`.

- [ ] **Step 4: Commit**

```bash
git add app/core/config.py .env.example
git commit -m "feat(config): add PLACES_API_URL for external places service"
```

---

### Task 2: `Places` external client + registry wiring

**Files:**
- Create: `app/clients/external/__init__.py` (empty)
- Create: `app/clients/external/places.py`
- Modify: `app/clients/registry.py`

**Interfaces:**
- Consumes: `Settings.places` (Task 1), `ManagedClient`, `get_tenant`/`get_trace_id`, `get_settings`,
  `InternalAPIError`.
- Produces: `ClientRegistry.places: Places` with
  `autocomplete(*, input_text: str, session_id: str | None) -> list[dict]` and
  `get_place(place_id: str, *, session_id: str | None) -> dict`.

- [ ] **Step 1: Create `app/clients/external/__init__.py`** (empty file)

- [ ] **Step 2: Create `app/clients/external/places.py`**

```python
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
```

- [ ] **Step 3: Register `places` in `app/clients/registry.py`**

Add the import:
```python
from app.clients.external.places import Places
```
In `__init__`, add the attribute and include it in `_managed`:
```python
        self.internal = InternalAPIClients(settings)
        self.vault = VaultClient(settings)
        self.redis = RedisClient(settings)
        self.places = Places(settings)
        self._managed: list[ManagedClient] = [self.internal, self.vault, self.redis, self.places]
```

- [ ] **Step 4: Verify import + boot**

Run: `uv run python -c "import app.main" && uv run ruff check .`
Expected: no error; `All checks passed!`.

- [ ] **Step 5: Commit**

```bash
git add app/clients/external/ app/clients/registry.py
git commit -m "feat(clients): add Places external client and register it"
```

---

### Task 3: `AddressService`

**Files:**
- Create: `app/services/address_service.py`

**Interfaces:**
- Consumes: `ClientRegistry.places` (Task 2), `BaseService`.
- Produces: `AddressService` with
  `autocomplete(*, input_text: str, session_id: str | None) -> list[dict]` and
  `get_place(place_id: str, *, session_id: str | None) -> dict`.

- [ ] **Step 1: Create `app/services/address_service.py`**

```python
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
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "import app.services.address_service" && uv run ruff check .`
Expected: no error; `All checks passed!`.

- [ ] **Step 3: Commit**

```bash
git add app/services/address_service.py
git commit -m "feat(address): service proxying the external places service"
```

---

### Task 4: `address` routes + router wiring

**Files:**
- Create: `app/api/v1/routes/address.py`
- Modify: `app/api/v1/router.py`

**Interfaces:**
- Consumes: `AddressService` (Task 3).
- Produces: `GET /api/v1/address/places/autocomplete`, `GET /api/v1/address/places/get`.

- [ ] **Step 1: Create `app/api/v1/routes/address.py`**

```python
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
```

- [ ] **Step 2: Include the router in `app/api/v1/router.py`**

Add `address` to the import and include it (after `doctor_clinic`):
```python
from app.api.v1.routes import address, chat, doctor_clinic, health, scheduling
```
```python
api_router.include_router(doctor_clinic.router, tags=["doctor-clinic"])
api_router.include_router(address.router, tags=["address"])
```

- [ ] **Step 3: Verify boot + behavior (422 validation + 502 wiring)**

```bash
uv run python -c "import app.main" && uv run ruff check .
uv run uvicorn app.main:app --port 8099 > /tmp/uvi3.log 2>&1 &
UVIPID=$!
for i in $(seq 1 20); do curl -s -o /dev/null -H "X-Tenant-ID: t1" http://127.0.0.1:8099/api/v1/health && break; sleep 0.5; done
echo "--- autocomplete missing 'input' (expect 422 validation) ---"
curl -s -w "\n[HTTP %{http_code}]\n" -H "X-Tenant-ID: t1" "http://127.0.0.1:8099/api/v1/address/places/autocomplete"
echo "--- autocomplete (expect 502: fake places host) ---"
curl -s -w "\n[HTTP %{http_code}]\n" -H "X-Tenant-ID: t1" "http://127.0.0.1:8099/api/v1/address/places/autocomplete?input=123%20Main"
echo "--- get place (expect 502) ---"
curl -s -w "\n[HTTP %{http_code}]\n" -H "X-Tenant-ID: t1" "http://127.0.0.1:8099/api/v1/address/places/get?place_id=abc"
kill $UVIPID 2>/dev/null
```
Expected: first returns a validation `error` envelope (422); the other two return
`"errorCode":"INTERNAL_API_ERROR"` (502) — proving route → service → external client → error path.

- [ ] **Step 4: Commit**

```bash
git add app/api/v1/routes/address.py app/api/v1/router.py
git commit -m "feat(address): autocomplete and place-details endpoints"
```

---

## Self-Review

- **Spec coverage (§2 address rows, §8):** both endpoints routed through `AddressService` →
  `Places` external client on `PLACES_API_URL`; no Google key held (§10 satisfied — Task 1 omits it).
- **Pattern fit:** `Places` is a `ManagedClient` registered like internal/vault/redis; forwards
  tenant+trace only.
- **No placeholders:** every step has concrete code + commands + expected output.
- **Type consistency:** `places` attribute + method names (`autocomplete`, `get_place`) match across
  client (Task 2), service (Task 3), routes (Task 4).
- **Open items:** external places service paths (`/places/autocomplete`, `/places/{id}`), query
  param names (`input`, `sessionId`), and response shapes confirmed against that service later.
