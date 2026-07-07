# Phase 5 — Patient + Appointments Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the patient lookup/get-or-create and appointment book/cancel capabilities onto the internal `/api/v1/schedule/*` API, and retire the remaining scaffold `scheduling.py` route + `SchedulingService` + `BookingRequest`/`Appointment` schemas.

**Architecture:** Frontend-facing REST endpoints (`patient.py`, `appointment.py` routers) → services (`PatientService`, `AppointmentService`) → internal clients (`Patient`, `Appointments`). Services return `dict`/`list[dict]` pass-through; request bodies are validated pydantic models with snake_case fields; internal clients own the snake→camel payload mapping and the `/api/v1/schedule/*` paths.

**Tech Stack:** FastAPI, httpx async pooled client, pydantic-settings, `uv` (Python 3.14).

## Global Constraints

- Work ONLY in `clinicalops-scheduling-agent`.
- Internal contract = **voice-agent contract** (`clinicalops-scheduling-voice-agent`), confirmed by the user over the in-progress `clinicalops-internal-api` branch.
- This service NEVER talks to FHIR/DB directly — all access via the internal API over HTTP.
- Tenant/trace propagation lives ONLY in the client layer; services/routes never see tenant data.
- Use `create_router()` (not `fastapi.APIRouter`); routers are thin and delegate to services.
- Services return `dict`/`list[dict]` pass-through — no invented response DTOs (upstream field names unconfirmed). Request bodies MAY be pydantic models (input field names are ours).
- No per-step Redis writes, no `collected_data` blob.
- Add logging via `get_logger(__name__)`.
- Do NOT write tests this pass.
- No new env vars needed (reuses `INTERNAL_API_URL`).
- **Commit messages:** plain conventional-commit, NO AI/Claude attribution, NO `Co-Authored-By` trailer.
- Verify each task: `uv run python -c "import app.main"`, `uv run ruff check .`, and (final) uvicorn boot + curl.

### Authoritative internal contract (from voice agent)

Patient (`/api/v1/schedule/patients`):
- Search: `GET` params `{phone, dob, name?, page=0, size=20}` → paginated `data.content`; take first.
- Create: `POST` body `{name, dateOfBirth, gender?, email?, phone}` → `data`.
- Get by id: `GET /{id}` → `data`.
- Appointments: `GET /{id}/appointments` params `{size=20, sort=appointmentDatetime}` → `data.content`; fields of interest: `appointmentDatetime, id, isFutureAppointment, reason, slotId, status`. Active = `isFutureAppointment is True and status == "SCHEDULED"`.

Appointments (`/api/v1/schedule/appointments`):
- Book: `POST` body `{slotId, patientId, doctorId, clinicId, slotType, reason, notificationModes:["EMAIL"], sendInsuranceRequest:true}` → `data` (has `id`).
- Update reason: `PUT /{id}` body `{reason}` → `data`.
- Cancel: `POST /{id}/cancel` → `data`.

Note: `BaseInternalClient` already unwraps the `{status, data}` envelope, so client methods receive `data` directly (paginated payloads arrive as `{content, ...}`).

---

### Task 1: Patient internal client

**Files:**
- Modify: `app/clients/internal/patient.py`

**Interfaces:**
- Produces: `Patient.search(*, phone, date_of_birth, name=None) -> dict | None`, `Patient.create(*, name, date_of_birth, phone, gender=None, email=None) -> dict`, `Patient.get(patient_id) -> dict`, `Patient.appointments(patient_id, *, size=20, sort="appointmentDatetime") -> list[dict]`.

- [ ] **Step 1: Replace the file contents**

```python
"""Client for the internal Patient (schedule) module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

PATIENTS = "/api/v1/schedule/patients"


def _content(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "content" in payload:
        return payload["content"] or []
    return payload or []


class Patient(BaseInternalClient):
    async def search(
        self, *, phone: str, date_of_birth: str, name: str | None = None
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {"phone": phone, "dob": date_of_birth, "page": 0, "size": 20}
        if name is not None:
            params["name"] = name
        content = _content(await self.get(PATIENTS, params=params))
        return content[0] if content else None

    async def create(
        self,
        *,
        name: str,
        date_of_birth: str,
        phone: str,
        gender: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "dateOfBirth": date_of_birth, "phone": phone}
        if gender is not None:
            payload["gender"] = gender
        if email is not None:
            payload["email"] = email
        return await self.post(PATIENTS, json=payload)

    async def get(self, patient_id: str) -> dict[str, Any]:
        return await super().get(f"{PATIENTS}/{patient_id}")

    async def appointments(
        self, patient_id: str, *, size: int = 20, sort: str = "appointmentDatetime"
    ) -> list[dict[str, Any]]:
        params = {"size": size, "sort": sort}
        return _content(await super().get(f"{PATIENTS}/{patient_id}/appointments", params=params))
```

Note: `get(self, patient_id)` shadows `BaseInternalClient.get`; the by-id and appointments calls use `super().get(...)` for the raw HTTP GET. The `search`/`create` methods call `self.get`/`self.post` on a full path, which resolve to the base HTTP verbs (there is no arg collision there since they pass a path string).

Correction to avoid the name clash entirely — do NOT override `get`. Use distinct method names:

```python
"""Client for the internal Patient (schedule) module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

PATIENTS = "/api/v1/schedule/patients"


def _content(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "content" in payload:
        return payload["content"] or []
    return payload or []


class Patient(BaseInternalClient):
    async def search(
        self, *, phone: str, date_of_birth: str, name: str | None = None
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {"phone": phone, "dob": date_of_birth, "page": 0, "size": 20}
        if name is not None:
            params["name"] = name
        content = _content(await self.get(PATIENTS, params=params))
        return content[0] if content else None

    async def create(
        self,
        *,
        name: str,
        date_of_birth: str,
        phone: str,
        gender: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "dateOfBirth": date_of_birth, "phone": phone}
        if gender is not None:
            payload["gender"] = gender
        if email is not None:
            payload["email"] = email
        return await self.post(PATIENTS, json=payload)

    async def get_by_id(self, patient_id: str) -> dict[str, Any]:
        return await self.get(f"{PATIENTS}/{patient_id}")

    async def appointments(
        self, patient_id: str, *, size: int = 20, sort: str = "appointmentDatetime"
    ) -> list[dict[str, Any]]:
        params = {"size": size, "sort": sort}
        return _content(await self.get(f"{PATIENTS}/{patient_id}/appointments", params=params))
```

- [ ] **Step 2: Verify import + lint**

Run: `uv run python -c "import app.main" && uv run ruff check app/clients/internal/patient.py`
Expected: no output / "All checks passed!"

---

### Task 2: Appointments internal client

**Files:**
- Create: `app/clients/internal/appointment.py`
- Modify: `app/clients/internal/scheduling.py` (remove appointment methods; leave slots-only)
- Modify: `app/clients/internal/group.py` (register `appointment`)

**Interfaces:**
- Produces: `Appointments.book(payload: dict) -> dict`, `Appointments.cancel(appointment_id) -> dict`, `Appointments.get(appointment_id) -> dict`, `Appointments.update_reason(appointment_id, reason) -> dict`.
- Consumes: `InternalAPIClients` from Task's group wiring.

- [ ] **Step 1: Create `app/clients/internal/appointment.py`**

```python
"""Client for the internal Appointments (schedule) module of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

APPOINTMENTS = "/api/v1/schedule/appointments"


class Appointments(BaseInternalClient):
    async def book(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post(APPOINTMENTS, json=payload)

    async def cancel(self, appointment_id: str) -> dict[str, Any]:
        return await self.post(f"{APPOINTMENTS}/{appointment_id}/cancel")

    async def get_by_id(self, appointment_id: str) -> dict[str, Any]:
        return await self.get(f"{APPOINTMENTS}/{appointment_id}")

    async def update_reason(self, appointment_id: str, reason: str) -> dict[str, Any]:
        return await self.put(f"{APPOINTMENTS}/{appointment_id}", json={"reason": reason})
```

- [ ] **Step 2: Strip appointment methods from `scheduling.py`**

Remove `create_appointment`, `cancel_appointment`, `get_appointment` from `Scheduling`. The class keeps only `slot_counts` and `live_slots` (plus `_as_list`). Final file:

```python
"""Client for the internal Scheduling slots (Common module) of the ClinicalOps API."""

from typing import Any

from app.clients.internal.base import BaseInternalClient


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "content" in payload:
        return payload["content"] or []
    return payload or []


class Scheduling(BaseInternalClient):
    async def slot_counts(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        start_date: str,
        end_date: str,
        slot_type: str = "NP",
    ) -> list[dict[str, Any]]:
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "slotType": slot_type,
            "status": "FREE",
            "doctorId": doctor_id,
            "clinicId": clinic_id,
        }
        return _as_list(await self.get("/api/v1/common/slots/count", params=params))

    async def live_slots(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        date: str,
        slot_type: str = "NP",
        slots_count: int = 20,
    ) -> list[dict[str, Any]]:
        params = {
            "slotType": slot_type,
            "doctorId": doctor_id,
            "clinicId": clinic_id,
            "date": date,
            "page": 0,
            "size": slots_count,
            "sort": "date,ASC",
        }
        return _as_list(await self.get("/api/v1/common/slots/live-slots", params=params))
```

- [ ] **Step 3: Register `appointment` in `group.py`**

Add the import `from app.clients.internal.appointment import Appointments`, declare `self.appointment: Appointments` in `__init__`, and in `startup()` add `self.appointment = Appointments(self._client, service_name="scheduling")`.

- [ ] **Step 4: Verify import + lint**

Run: `uv run python -c "import app.main" && uv run ruff check app/clients/internal/`
Expected: no output / "All checks passed!"

---

### Task 3: Request schemas

**Files:**
- Create: `app/schemas/patient.py`
- Modify: `app/schemas/scheduling.py` (replace with the fuller `BookingRequest`; drop `Appointment`)

**Interfaces:**
- Produces: `PatientLookup{phone, date_of_birth, name?}`, `PatientUpsert{name, date_of_birth, phone, gender?, email?}`, `BookingRequest{slot_id, patient_id, doctor_id, clinic_id, slot_type, reason?}`.

- [ ] **Step 1: Create `app/schemas/patient.py`**

```python
"""Patient request schemas."""

from app.schemas.base import Model


class PatientLookup(Model):
    phone: str
    date_of_birth: str
    name: str | None = None


class PatientUpsert(Model):
    name: str
    date_of_birth: str
    phone: str
    gender: str | None = None
    email: str | None = None
```

- [ ] **Step 2: Replace `app/schemas/scheduling.py`**

```python
"""Appointment request schemas."""

from app.schemas.base import Model


class BookingRequest(Model):
    slot_id: str
    patient_id: str
    doctor_id: str
    clinic_id: str
    slot_type: str = "NP"
    reason: str | None = None
```

- [ ] **Step 3: Verify lint** (import verified after services wire in)

Run: `uv run ruff check app/schemas/`
Expected: "All checks passed!"

---

### Task 4: PatientService + AppointmentService

**Files:**
- Create: `app/services/patient_service.py`
- Create: `app/services/appointment_service.py`
- Delete: `app/services/scheduling_service.py`

**Interfaces:**
- Consumes: `Patient` (Task 1), `Appointments` (Task 2), `PatientUpsert`/`PatientLookup`/`BookingRequest` (Task 3).
- Produces: `PatientService.lookup`, `PatientService.get_or_create`, `PatientService.appointments`; `AppointmentService.book`, `AppointmentService.cancel`.

- [ ] **Step 1: Create `app/services/patient_service.py`**

```python
"""Patient orchestration over the internal schedule API."""

from typing import Any

from app.core.logging import get_logger
from app.schemas.patient import PatientLookup, PatientUpsert
from app.services.base import BaseService

logger = get_logger(__name__)

_ACTIVE_STATUS = "SCHEDULED"


class PatientService(BaseService):
    async def lookup(self, req: PatientLookup) -> dict[str, Any] | None:
        logger.info("Patient lookup by phone+dob")
        return await self._clients.internal.patient.search(
            phone=req.phone, date_of_birth=req.date_of_birth, name=req.name
        )

    async def get_or_create(self, req: PatientUpsert) -> dict[str, Any]:
        existing = await self._clients.internal.patient.search(
            phone=req.phone, date_of_birth=req.date_of_birth
        )
        if existing:
            logger.info("Found existing patient %s", existing.get("id"))
            return existing
        logger.info("Creating new patient")
        return await self._clients.internal.patient.create(
            name=req.name,
            date_of_birth=req.date_of_birth,
            phone=req.phone,
            gender=req.gender,
            email=req.email,
        )

    async def appointments(self, patient_id: str, *, active: bool = False) -> list[dict[str, Any]]:
        logger.info("Fetching appointments for patient %s active=%s", patient_id, active)
        items = await self._clients.internal.patient.appointments(patient_id)
        if active:
            return [
                a
                for a in items
                if a.get("isFutureAppointment") is True and a.get("status") == _ACTIVE_STATUS
            ]
        return items
```

- [ ] **Step 2: Create `app/services/appointment_service.py`**

```python
"""Appointment orchestration over the internal schedule API."""

from typing import Any

from app.core.logging import get_logger
from app.schemas.scheduling import BookingRequest
from app.services.base import BaseService

logger = get_logger(__name__)


class AppointmentService(BaseService):
    async def book(self, req: BookingRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "slotId": req.slot_id,
            "patientId": req.patient_id,
            "doctorId": req.doctor_id,
            "clinicId": req.clinic_id,
            "slotType": req.slot_type,
            "reason": req.reason,
            "notificationModes": ["EMAIL"],
            "sendInsuranceRequest": True,
        }
        logger.info(
            "Booking appointment slot=%s patient=%s doctor=%s clinic=%s",
            req.slot_id,
            req.patient_id,
            req.doctor_id,
            req.clinic_id,
        )
        return await self._clients.internal.appointment.book(payload)

    async def cancel(self, appointment_id: str) -> dict[str, Any]:
        logger.info("Cancelling appointment %s", appointment_id)
        return await self._clients.internal.appointment.cancel(appointment_id)
```

- [ ] **Step 3: Delete `app/services/scheduling_service.py`**

Run: `rm app/services/scheduling_service.py`

- [ ] **Step 4: Verify import + lint**

Run: `uv run python -c "import app.main" && uv run ruff check app/services/`
Expected: no output / "All checks passed!" (note: `app.main` still imports the scaffold `scheduling` route until Task 5 — expect an ImportError here referencing `scheduling_service`; that is resolved in Task 5. If it errors only on the deleted module, proceed to Task 5 then re-verify.)

---

### Task 5: Routes + router wiring, retire scaffold scheduling route

**Files:**
- Create: `app/api/v1/routes/patient.py`
- Create: `app/api/v1/routes/appointment.py`
- Delete: `app/api/v1/routes/scheduling.py`
- Modify: `app/api/v1/router.py`

**Interfaces:**
- Consumes: `PatientService`, `AppointmentService` (Task 4), `PatientLookup`/`PatientUpsert`/`BookingRequest` (Task 3).

- [ ] **Step 1: Create `app/api/v1/routes/patient.py`**

```python
"""Patient endpoints: lookup, get-or-create, appointment history."""

from typing import Any

from app.api.route import create_router
from app.schemas.patient import PatientLookup, PatientUpsert
from app.services.patient_service import PatientService

router = create_router()


@router.post("/patients/lookup", response_model=dict[str, Any] | None)
async def lookup_patient(payload: PatientLookup) -> dict[str, Any] | None:
    return await PatientService().lookup(payload)


@router.post("/patients", response_model=dict[str, Any])
async def upsert_patient(payload: PatientUpsert) -> dict[str, Any]:
    return await PatientService().get_or_create(payload)


@router.get("/patients/{patient_id}/appointments", response_model=list[dict[str, Any]])
async def patient_appointments(
    patient_id: str, active: bool = False
) -> list[dict[str, Any]]:
    return await PatientService().appointments(patient_id, active=active)
```

- [ ] **Step 2: Create `app/api/v1/routes/appointment.py`**

```python
"""Appointment endpoints: book and cancel."""

from typing import Any

from app.api.route import create_router
from app.schemas.scheduling import BookingRequest
from app.services.appointment_service import AppointmentService

router = create_router()


@router.post("/appointments", response_model=dict[str, Any])
async def book_appointment(payload: BookingRequest) -> dict[str, Any]:
    return await AppointmentService().book(payload)


@router.post("/appointments/{appointment_id}/cancel", response_model=dict[str, Any])
async def cancel_appointment(appointment_id: str) -> dict[str, Any]:
    return await AppointmentService().cancel(appointment_id)
```

- [ ] **Step 3: Delete `app/api/v1/routes/scheduling.py`**

Run: `rm app/api/v1/routes/scheduling.py`

- [ ] **Step 4: Update `app/api/v1/router.py`**

Replace the `scheduling` import with `appointment, patient`; remove the `scheduling` include; add patient + appointment includes (no prefix, mounted at `/api/v1`):

```python
"""Aggregate v1 router."""

from fastapi import APIRouter

from app.api.v1.routes import (
    address,
    appointment,
    chat,
    doctor_clinic,
    health,
    patient,
    slots,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(doctor_clinic.router, tags=["doctor-clinic"])
api_router.include_router(address.router, tags=["address"])
api_router.include_router(slots.router, tags=["slots"])
api_router.include_router(patient.router, tags=["patient"])
api_router.include_router(appointment.router, tags=["appointment"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
```

- [ ] **Step 5: Verify import + lint**

Run: `uv run python -c "import app.main" && uv run ruff check .`
Expected: no output / "All checks passed!"

- [ ] **Step 6: Boot + curl smoke test**

Start uvicorn on a fresh port pointed at a fake internal host, then:
- `POST /api/v1/patients/lookup` with missing body → 400 with per-field validation errors.
- `POST /api/v1/patients/lookup` with valid body + `-H "X-Tenant-ID: t1"` → 502 `INTERNAL_API_ERROR`.
- `POST /api/v1/appointments` with valid body → 502 `INTERNAL_API_ERROR`.
- `POST /api/v1/appointments/abc/cancel` → 502 `INTERNAL_API_ERROR`.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(patient): lookup, get-or-create, and appointment book/cancel endpoints"
```

---

## Self-Review

- Spec coverage: patient lookup ✅ (Task 5 `/patients/lookup`), get-or-create ✅, book ✅, cancel ✅, scaffold retired ✅ (scheduling route/service/Appointment schema deleted).
- Type consistency: `Patient.get_by_id`/`appointments`/`search`/`create`, `Appointments.book`/`cancel`, `PatientService.lookup`/`get_or_create`/`appointments`, `AppointmentService.book`/`cancel` — names consistent across tasks.
- No placeholders: all code is concrete.
