# Phase 4 — Slots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans.

**Goal:** Migrate the three frontend-facing slot endpoints (`slots`, `month-slots`,
`nearest-dates-slots`) onto the unified internal slots API, dropping the redundant
Healow-era `schedule` endpoint.

**Architecture:** `slots.py` route (thin, envelope) → `SlotsService` (orchestration,
free-slot filtering, nearest-date selection) → `Scheduling` internal client
(`/api/v1/common/slots/count`, `/api/v1/common/slots/live-slots`). No Azure, no Healow,
no caching, no month-batching — the internal `/count` endpoint returns a whole range in
one call.

**Tech Stack:** FastAPI, httpx (pooled), pydantic-settings, `uv`/Python 3.14.

## Global Constraints

- This service never touches FHIR/DB directly — only the internal API over HTTP.
- Services return `dict`/`list[dict]` pass-through (upstream field names unconfirmed); no invented DTOs.
- Tenancy/trace headers applied only in the client layer; never threaded through services.
- Commit messages: plain conventional-commit, NO AI/Claude attribution, NO `Co-Authored-By`.
- Verification only (no tests this pass): `uv run python -c "import app.main"`, `uv run ruff check .`, uvicorn boot + curl.

**Authoritative internal contract** (from the voice agent's `CalendarService`):
- `GET /api/v1/common/slots/count` — params `startDate, endDate, slotType, status=FREE, doctorId, clinicId` → `[{date, count}]`.
- `GET /api/v1/common/slots/live-slots` — params `slotType, doctorId, clinicId, date, page, size, sort` → paginated (`content`) slots with a `status` field.

---

### Task 1: Scheduling client slot methods

**Files:**
- Modify: `app/clients/internal/scheduling.py`

Replace the placeholder `search_slots` (wrong practitioner/start/end contract) with two
real methods matching the internal contract; leave the appointment methods untouched
(Phase 5). Add a module-level `_as_list` normalizer mirroring `DoctorClinic._items`.

- [ ] **Step 1:** Add `_as_list(payload)` returning `payload["content"]` when payload is a
  dict with `content`, else `payload or []`.
- [ ] **Step 2:** Replace `search_slots` with:
  - `slot_counts(*, doctor_id, clinic_id, start_date, end_date, slot_type="NP") -> list[dict]`
    → GET `/api/v1/common/slots/count`, params `{startDate, endDate, slotType, status: "FREE", doctorId, clinicId}`.
  - `live_slots(*, doctor_id, clinic_id, date, slot_type="NP", slots_count=20) -> list[dict]`
    → GET `/api/v1/common/slots/live-slots`, params `{slotType, doctorId, clinicId, date, page: 0, size: slots_count, sort: "date,ASC"}`.
- [ ] **Step 3:** Verify import: `uv run python -c "import app.clients.internal.scheduling"`.

### Task 2: Retire superseded scaffold slot-search

**Files:**
- Modify: `app/services/scheduling_service.py` (remove `find_slots`)
- Modify: `app/api/v1/routes/scheduling.py` (remove `/slots/search` route)
- Modify: `app/schemas/scheduling.py` (remove `SlotSearchRequest`, `Slot`)

The scaffold `POST /scheduling/slots/search` used invented DTOs and the removed
`search_slots`; it is superseded by this phase. Keep `book`/`cancel`, `BookingRequest`,
`Appointment` for Phase 5.

- [ ] **Step 1:** Delete `find_slots` from `SchedulingService`; drop the now-unused
  `Slot, SlotSearchRequest` names from its import.
- [ ] **Step 2:** Delete the `search_slots` route and its `Slot, SlotSearchRequest` import
  from `scheduling.py`.
- [ ] **Step 3:** Delete `SlotSearchRequest` and `Slot` classes from `scheduling.py` schema.
- [ ] **Step 4:** Verify import: `uv run python -c "import app.main"`.

### Task 3: SlotsService

**Files:**
- Create: `app/services/slots_service.py`

**Interfaces (Produces):**
- `live_slots(*, doctor_id, clinic_id, date, slot_type="NP", slots_count=20) -> list[dict]`
  — free slots for a date (filters `status == "free"`).
- `month_slots(*, doctor_id, clinic_id, start_date, slot_type="NP") -> dict`
  — `{month, data: [{date, slot_count, weekday}], total_slots}` over `start_date`'s calendar month.
- `nearest_dates_slots(*, doctor_id, clinic_id, slot_type="NP", count=3) -> list[dict]`
  — nearest `count` dates (within `LOOKAHEAD_DAYS=60`) that have availability, each
  `{date, weekday, slot_count, slots}`.

- [ ] **Step 1:** Write module with `LOOKAHEAD_DAYS = 60` and helpers `_weekday(d)` and
  `_month_bounds(start_date)` (via `calendar.monthrange`), then the three methods.
  `live_slots` filters `str(s.get("status","")).lower() == "free"`. `nearest_dates_slots`
  fetches counts for `[today, today+LOOKAHEAD_DAYS]`, keeps `count>0`, sorts by date,
  takes `count`, then fetches `live_slots` per date sequentially.
- [ ] **Step 2:** Verify import: `uv run python -c "import app.services.slots_service"`.

### Task 4: Slots routes + wiring

**Files:**
- Create: `app/api/v1/routes/slots.py`
- Modify: `app/api/v1/router.py` (include `slots.router`, no prefix)

Public paths under `api_prefix=/api/v1`: `/appointments/slots`, `/appointments/month-slots`,
`/appointments/nearest-dates-slots`. Snake_case query params for consistency with `doctor_clinic`.

- [ ] **Step 1:** Create `slots.py` with three GET routes delegating to `SlotsService`,
  `response_model` `list[dict[str, Any]]` / `dict[str, Any]`.
- [ ] **Step 2:** Add `slots` to the `router.py` import and `include_router(slots.router, tags=["slots"])`.
- [ ] **Step 3:** Verify: `uv run python -c "import app.main"` and `uv run ruff check .`.
- [ ] **Step 4:** Boot + curl: missing required param → 400 validation; valid call → 502
  `INTERNAL_API_ERROR` (client reached the fake host).
- [ ] **Step 5:** Commit `feat(slots): live, month, and nearest-date slot endpoints`.
