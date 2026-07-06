# Phase 6: Insurance (provisional stub) Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add the patient-insurance persistence surface (provisional) so the Phase 7 agent has a place to send chat-extracted insurance details.

**Architecture:** Thin route → `InsuranceService` → `Insurance` internal client, targeting a provisional `/api/v1/schedule/patients/{id}/insurance` path on the shared internal pooled client. Sessions are intentionally **not** built here — ADK owns session state in Phase 7 (user decision 2026-07-06).

**Tech Stack:** FastAPI, httpx async pooled client, pydantic-settings.

## Global Constraints

- Work ONLY in `clinicalops-scheduling-agent`.
- Authoritative contract = voice-agent repo; where it has none (sessions/insurance), paths are **provisional** and clearly marked; they 502 until the backend ships.
- No `collected_data` blob, no per-step Redis writes.
- Services return `dict`/`list[dict]` pass-through (request DTOs OK; no invented response DTOs).
- Layering: routes → services → clients. Tenancy applied only in the client layer.
- Commit messages: plain conventional-commit, NO AI/Claude attribution, NO `Co-Authored-By` trailer.
- Insurance domain fields mirror the original agent: `insurance_provider`, `insurance_member_id`.

---

### Task 1: Insurance internal client

**Files:**
- Create: `app/clients/internal/insurance.py`
- Modify: `app/clients/internal/group.py`

`Insurance(BaseInternalClient)` with `submit(patient_id, payload) -> dict`
POSTing to `/api/v1/schedule/patients/{patient_id}/insurance`. Register in the
group as `self.insurance = Insurance(self._client, service_name="scheduling")`.

### Task 2: Insurance request schema

**Files:**
- Create: `app/schemas/insurance.py`

`InsuranceUpload(Model)` with `insurance_provider: str`, `insurance_member_id: str | None = None`.

### Task 3: Insurance service

**Files:**
- Create: `app/services/insurance_service.py`

`InsuranceService(BaseService).submit(patient_id, req)` builds
`{insuranceProvider, insuranceMemberId}`, logs, and calls the client.

### Task 4: Insurance route + wire router

**Files:**
- Create: `app/api/v1/routes/insurance.py`
- Modify: `app/api/v1/router.py`

`POST /patients/{patient_id}/insurance` (InsuranceUpload) → `InsuranceService().submit`.
Include the router (no prefix), tag `insurance`.

### Task 5: Verify + commit

Run `uv run python -c "import app.main"`, `uv run ruff check .`, uvicorn boot + curl
(400 for missing body, 502 `INTERNAL_API_ERROR` for a valid call). Commit.
