# Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the client/config foundation so the app talks to a **single** internal
ClinicalOps API base URL with tenant/trace/agent-type headers, renamed domain clients, and no
Azure/per-host remnants — while the app still boots cleanly.

**Architecture:** Collapse the scaffold's three per-host internal base URLs into one
`INTERNAL_API_URL`. Domain client classes (`Patient`, `Scheduling`) share one pooled
`httpx.AsyncClient`. `BaseInternalClient` adds an `X-Agent-Type` header so the internal API can tell
this chat agent apart from the voice agent. `availability` client is deleted.

**Tech Stack:** FastAPI, httpx, pydantic-settings, uv (Python 3.14).

## Global Constraints

- This service **never** talks to FHIR or a DB directly — only internal-API base URLs are configured.
- Every env var used is defined in `app/core/config.py` and listed in `.env.example` (no secret values).
- All imports at top of file. No inline imports. No unnecessary comments.
- Routes use `create_router()` (envelope-aware), not `fastapi.APIRouter`.
- No test files this pass (per instruction). Verify via import, `ruff`, and app boot instead.
- `google-adk` is **not** added in this phase (deferred to the Agent phase).

## Reference (spec)

`docs/superpowers/specs/2026-07-06-scheduling-agent-migration-design.md` §4, §10.

---

## Setup (once, before Task 1)

- [ ] **Create the migration branch**

```bash
cd /Users/auriga/Projects/raga/clinicalops/clinicalops-scheduling-agent
git checkout -b feat/scheduling-agent-migration
git add docs/superpowers/specs/2026-07-06-scheduling-agent-migration-design.md docs/superpowers/plans/2026-07-06-phase1-foundation.md
git commit -m "docs: scheduling-agent migration spec + phase 1 plan"
```

---

### Task 1: Collapse internal config to one API URL + agent type

**Files:**
- Modify: `app/core/config.py`

**Interfaces:**
- Produces: `Settings.internal.api_url: str`, `Settings.internal.timeout_seconds: float`,
  `Settings.internal.max_connections: int`, `Settings.internal.max_keepalive_connections: int`,
  `Settings.agent_type: str`.

- [ ] **Step 1: Replace `InternalAPISettings` and add `agent_type`**

In `app/core/config.py`, replace the `InternalAPISettings` class body:

```python
class InternalAPISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INTERNAL_", extra="ignore")

    api_url: str = "http://clinicalops-api.internal"

    timeout_seconds: float = 15.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
```

Then add `agent_type` to the top-level `Settings` class, next to `service_name`:

```python
    service_name: str = "clinicalops-scheduling-agent"
    service_version: str = "0.1.0"
    agent_type: str = "scheduling-chat-agent"
```

`agent_type` reads env `AGENT_TYPE` (no prefix on top-level `Settings`).

- [ ] **Step 2: Verify config imports and resolves**

Run: `uv run python -c "from app.core.config import get_settings; s=get_settings(); print(s.internal.api_url, s.agent_type)"`
Expected: prints `http://clinicalops-api.internal scheduling-chat-agent` with no error.

- [ ] **Step 3: Commit**

```bash
git add app/core/config.py
git commit -m "feat(config): single INTERNAL_API_URL + AGENT_TYPE, drop per-host URLs"
```

---

### Task 2: Propagate `X-Agent-Type` in the base internal client

**Files:**
- Modify: `app/clients/internal/base.py:20-29`

**Interfaces:**
- Consumes: `Settings.agent_type` (Task 1).
- Produces: every internal call now carries `X-Agent-Type: <settings.agent_type>` in addition to
  tenant + trace headers.

- [ ] **Step 1: Add the agent-type header in `_context_headers`**

Replace the `_context_headers` method in `app/clients/internal/base.py`:

```python
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
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "import app.clients.internal.base"`
Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add app/clients/internal/base.py
git commit -m "feat(clients): send X-Agent-Type on internal calls"
```

---

### Task 3: One pooled internal client; rename domain clients; drop availability

**Files:**
- Create: `app/clients/internal/scheduling.py` (renamed from `scheduling_client.py`)
- Create: `app/clients/internal/patient.py` (renamed from `patient_client.py`)
- Delete: `app/clients/internal/scheduling_client.py`, `app/clients/internal/patient_client.py`,
  `app/clients/internal/availability_client.py`
- Modify: `app/clients/internal/group.py`

**Interfaces:**
- Consumes: `Settings.internal.api_url` (Task 1).
- Produces: `InternalAPIClients.scheduling: Scheduling`, `InternalAPIClients.patient: Patient`,
  both bound to one shared `httpx.AsyncClient` whose `base_url` is `internal.api_url`.
  `Scheduling.search_slots(*, practitioner_id, start, end) -> list[dict]`,
  `Scheduling.create_appointment(payload) -> dict`,
  `Scheduling.cancel_appointment(appointment_id) -> dict`,
  `Scheduling.get_appointment(appointment_id) -> dict`,
  `Patient.find_patient(*, query) -> list[dict]`, `Patient.get_patient(patient_id) -> dict`.

- [ ] **Step 1: Create `app/clients/internal/scheduling.py`**

Class renamed `Scheduling`; paths now carry the ClinicalOps prefix (single base URL):

```python
"""Client for the internal Scheduling module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class Scheduling(BaseInternalClient):
    async def search_slots(
        self, *, practitioner_id: str | None, start: str, end: str
    ) -> list[dict[str, Any]]:
        params = {"start": start, "end": end}
        if practitioner_id:
            params["practitioner"] = practitioner_id
        data = await self.get("/api/v1/common/slots", params=params)
        return data or []

    async def create_appointment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post("/api/v1/schedule/appointments", json=payload)

    async def cancel_appointment(self, appointment_id: str) -> dict[str, Any]:
        return await self.post(f"/api/v1/schedule/appointments/{appointment_id}/cancel")

    async def get_appointment(self, appointment_id: str) -> dict[str, Any]:
        return await self.get(f"/api/v1/schedule/appointments/{appointment_id}")
```

- [ ] **Step 2: Create `app/clients/internal/patient.py`**

```python
"""Client for the internal Patient/Schedule module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


class Patient(BaseInternalClient):
    async def find_patient(self, *, query: str) -> list[dict[str, Any]]:
        data = await self.get("/api/v1/schedule/patients", params={"q": query})
        return data or []

    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        return await self.get(f"/api/v1/schedule/patients/{patient_id}")
```

- [ ] **Step 3: Delete the old client files**

```bash
git rm app/clients/internal/scheduling_client.py app/clients/internal/patient_client.py app/clients/internal/availability_client.py
```

- [ ] **Step 4: Rewrite `app/clients/internal/group.py`**

```python
"""Internal ClinicalOps API client group backed by one pooled httpx client."""

import httpx

from app.clients.internal.patient import Patient
from app.clients.internal.scheduling import Scheduling
from app.clients.lifecycle import ManagedClient
from app.core.config import Settings


class InternalAPIClients(ManagedClient):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: httpx.AsyncClient | None = None
        self.scheduling: Scheduling
        self.patient: Patient

    async def startup(self) -> None:
        internal = self._settings.internal
        self._client = httpx.AsyncClient(
            base_url=internal.api_url,
            timeout=internal.timeout_seconds,
            limits=httpx.Limits(
                max_connections=internal.max_connections,
                max_keepalive_connections=internal.max_keepalive_connections,
            ),
        )
        self.scheduling = Scheduling(self._client, service_name="scheduling")
        self.patient = Patient(self._client, service_name="patient")

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
```

- [ ] **Step 5: Verify imports and app boot**

Run: `uv run python -c "import app.main"`
Expected: no error (no lingering import of `availability_client`).

Run: `uv run ruff check .`
Expected: no errors (imports sorted).

- [ ] **Step 6: Verify the server starts and health responds**

Run (in one shell):
```bash
uv run uvicorn app.main:app --port 8099 &
sleep 3
curl -s -H "X-Tenant-ID: t1" http://127.0.0.1:8099/api/v1/health
kill %1
```
Expected: a JSON success envelope from `/health` (200), server log shows startup with no traceback.

- [ ] **Step 7: Commit**

```bash
git add app/clients/internal/
git commit -m "refactor(clients): single pooled internal client, rename Scheduling/Patient, drop availability"
```

---

### Task 4: Update `.env.example`

**Files:**
- Modify: `.env.example:10-14`

**Interfaces:**
- Consumes: env names from Tasks 1–3 (`INTERNAL_API_URL`, `INTERNAL_TIMEOUT_SECONDS`, `AGENT_TYPE`).

- [ ] **Step 1: Replace the internal-URL block and add agent type**

Replace lines 10–14 of `.env.example`:

```bash
# --- Service ---
ENVIRONMENT=local
LOG_LEVEL=INFO
AGENT_TYPE=scheduling-chat-agent
```

...and the internal block:

```bash
# --- Internal ClinicalOps API (single base URL; NOT FHIR, NOT DB) ---
INTERNAL_API_URL=http://clinicalops-api.internal
INTERNAL_TIMEOUT_SECONDS=15
```

(Leave the Vault and Redis blocks unchanged.)

- [ ] **Step 2: Verify no stale keys remain**

Run: `grep -nE "INTERNAL_(SCHEDULING|PATIENT|AVAILABILITY)_BASE_URL" .env.example || echo OK`
Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs(env): single INTERNAL_API_URL + AGENT_TYPE"
```

---

## Self-Review

- **Spec coverage (§4, §10):** single `INTERNAL_API_URL` (Task 1, 4), pooled client + renamed
  domain clients + availability deleted (Task 3), `X-Agent-Type` header (Task 2), env updated
  (Task 4). Gemini/`PLACES_API_URL`/`google-adk` intentionally deferred to their phases.
- **Non-breaking:** existing `SchedulingService`/demo routes call `internal.scheduling.search_slots`
  / `internal.patient` — attribute names and method signatures preserved, so app boots.
- **No placeholders:** every step has concrete code/commands and expected output.
- **Type consistency:** `Scheduling`/`Patient` method names match `group.py` construction and
  `SchedulingService` usage.
