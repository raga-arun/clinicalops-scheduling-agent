# Phase 2 — Doctor–Clinic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the four read-only doctor/clinic config endpoints — `/doctors`, `/clinics`,
`/doctor-clinic-mapping`, `/visit-type-mapping` — as `doctor_clinic` route → `DoctorClinicService`
→ `DoctorClinic` internal client against the ClinicalOps `/api/v1/common/*` module.

**Architecture:** Thin envelope routes call a service that owns logic (the "exactly one of
doctor_id/clinic_id" rule) and delegates to one internal client. The base internal client is
upgraded to unwrap the ClinicalOps `{status, data}` envelope so all domain clients receive the
payload. Responses are passed through as `dict`/`list[dict]` (no invented DTOs — upstream field
names not yet confirmed).

**Tech Stack:** FastAPI, httpx, pydantic, uv (Python 3.14).

## Global Constraints

- Never talk to FHIR/DB directly — only the internal ClinicalOps API (single `INTERNAL_API_URL`).
- Routes use `create_router()`; include with no extra prefix (paths are top-level under `/api/v1`).
- Services own logic; tools/routes stay thin; tenancy stays in the client layer.
- All imports at top of file. No unnecessary comments. No secret values in configs.
- No test files this pass — verify via import, `ruff`, app boot, and `curl` (a 502 from the
  unreachable fake internal host or a 400 from validation both prove the wiring + error envelope).
- Commit messages: plain conventional-commit, **no AI attribution / Co-Authored-By trailer**.

## Reference (spec)

`docs/superpowers/specs/2026-07-06-scheduling-agent-migration-design.md` §2 (rows 4–7), §3.

---

### Task 1: Unwrap the ClinicalOps envelope in the base internal client

**Files:**
- Modify: `app/clients/internal/base.py:60-62`

**Interfaces:**
- Produces: `BaseInternalClient.request(...)` returns the **payload** — `body["data"]` when the
  response body is a ClinicalOps envelope (`dict` containing both `"status"` and `"data"`),
  otherwise the raw body. `None` for empty responses (unchanged).

- [ ] **Step 1: Unwrap `data` after parsing the response**

Replace the tail of `request` in `app/clients/internal/base.py` (the `if not response.content` block):

```python
        if not response.content:
            return None
        body = response.json()
        if isinstance(body, dict) and "status" in body and "data" in body:
            return body["data"]
        return body
```

- [ ] **Step 2: Verify import + boot**

Run: `uv run python -c "import app.main" && uv run ruff check .`
Expected: no error; `All checks passed!`.

- [ ] **Step 3: Commit**

```bash
git add app/clients/internal/base.py
git commit -m "feat(clients): unwrap ClinicalOps {status,data} envelope in base client"
```

---

### Task 2: `DoctorClinic` internal client + group wiring

**Files:**
- Create: `app/clients/internal/doctor_clinic.py`
- Modify: `app/clients/internal/group.py`

**Interfaces:**
- Consumes: `BaseInternalClient` (payload-unwrapping from Task 1).
- Produces: `InternalAPIClients.doctor_clinic: DoctorClinic` with
  `list_doctors() -> list[dict]`, `list_clinics() -> list[dict]`,
  `clinics_for_doctor(doctor_id: str) -> list[dict]`,
  `doctors_for_clinic(clinic_id: str) -> list[dict]`,
  `visit_types(*, doctor_id: str | None, clinic_id: str | None) -> list[dict]`.

- [ ] **Step 1: Create `app/clients/internal/doctor_clinic.py`**

```python
"""Client for the internal Common module (doctors, clinics, visit types)."""

from typing import Any

from app.clients.internal.base import BaseInternalClient

_LIST_PARAMS = {"page": 0, "size": 200}


class DoctorClinic(BaseInternalClient):
    @staticmethod
    def _items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, dict) and "content" in payload:
            return payload["content"] or []
        return payload or []

    async def list_doctors(self) -> list[dict[str, Any]]:
        return self._items(await self.get("/api/v1/common/doctors", params=dict(_LIST_PARAMS)))

    async def list_clinics(self) -> list[dict[str, Any]]:
        return self._items(await self.get("/api/v1/common/clinics", params=dict(_LIST_PARAMS)))

    async def clinics_for_doctor(self, doctor_id: str) -> list[dict[str, Any]]:
        return self._items(
            await self.get(f"/api/v1/common/doctors/{doctor_id}/clinics", params=dict(_LIST_PARAMS))
        )

    async def doctors_for_clinic(self, clinic_id: str) -> list[dict[str, Any]]:
        return self._items(
            await self.get(f"/api/v1/common/clinics/{clinic_id}/doctors", params=dict(_LIST_PARAMS))
        )

    async def visit_types(
        self, *, doctor_id: str | None, clinic_id: str | None
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = dict(_LIST_PARAMS)
        if doctor_id:
            params["doctorId"] = doctor_id
        if clinic_id:
            params["clinicId"] = clinic_id
        return self._items(await self.get("/api/v1/common/visit-types", params=params))
```

- [ ] **Step 2: Wire `doctor_clinic` into the group**

In `app/clients/internal/group.py`, add the import, the attribute declaration, and the startup
construction.

Import (with the others):
```python
from app.clients.internal.doctor_clinic import DoctorClinic
```
Attribute (in `__init__`, after `self.patient: Patient`):
```python
        self.doctor_clinic: DoctorClinic
```
Construction (in `startup`, after the `self.patient = ...` line):
```python
        self.doctor_clinic = DoctorClinic(self._client, service_name="common")
```

- [ ] **Step 3: Verify import + boot**

Run: `uv run python -c "import app.main" && uv run ruff check .`
Expected: no error; `All checks passed!`.

- [ ] **Step 4: Commit**

```bash
git add app/clients/internal/doctor_clinic.py app/clients/internal/group.py
git commit -m "feat(clients): add DoctorClinic internal client for common module"
```

---

### Task 3: `BadRequestError` + `DoctorClinicService`

**Files:**
- Modify: `app/core/exceptions.py` (add `BadRequestError` after `MissingTenantError`)
- Create: `app/services/doctor_clinic_service.py`

**Interfaces:**
- Consumes: `InternalAPIClients.doctor_clinic` (Task 2), `BaseService`.
- Produces: `BadRequestError(AppError)` (400, `BAD_REQUEST`); `DoctorClinicService` with
  `list_doctors() -> list[dict]`, `list_clinics() -> list[dict]`,
  `doctor_clinic_mapping(*, doctor_id, clinic_id) -> dict`,
  `visit_type_mapping(*, doctor_id, clinic_id) -> list[dict]`.

- [ ] **Step 1: Add `BadRequestError` to `app/core/exceptions.py`**

After the `MissingTenantError` class:

```python
class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
```

- [ ] **Step 2: Create `app/services/doctor_clinic_service.py`**

```python
"""Doctor/clinic config orchestration over the internal Common API."""

from typing import Any

from app.core.exceptions import BadRequestError
from app.core.logging import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)


class DoctorClinicService(BaseService):
    async def list_doctors(self) -> list[dict[str, Any]]:
        logger.info("Listing doctors")
        return await self._clients.internal.doctor_clinic.list_doctors()

    async def list_clinics(self) -> list[dict[str, Any]]:
        logger.info("Listing clinics")
        return await self._clients.internal.doctor_clinic.list_clinics()

    async def doctor_clinic_mapping(
        self, *, doctor_id: str | None, clinic_id: str | None
    ) -> dict[str, Any]:
        if bool(doctor_id) == bool(clinic_id):
            raise BadRequestError("Provide exactly one of 'doctor_id' or 'clinic_id'")
        client = self._clients.internal.doctor_clinic
        if doctor_id:
            logger.info("Mapping clinics for doctor %s", doctor_id)
            return {"doctor_id": doctor_id, "clinics": await client.clinics_for_doctor(doctor_id)}
        logger.info("Mapping doctors for clinic %s", clinic_id)
        return {"clinic_id": clinic_id, "doctors": await client.doctors_for_clinic(clinic_id)}

    async def visit_type_mapping(
        self, *, doctor_id: str | None, clinic_id: str | None
    ) -> list[dict[str, Any]]:
        logger.info("Listing visit types (doctor=%s, clinic=%s)", doctor_id, clinic_id)
        return await self._clients.internal.doctor_clinic.visit_types(
            doctor_id=doctor_id, clinic_id=clinic_id
        )
```

- [ ] **Step 3: Verify import + boot**

Run: `uv run python -c "import app.services.doctor_clinic_service" && uv run ruff check .`
Expected: no error; `All checks passed!`.

- [ ] **Step 4: Commit**

```bash
git add app/core/exceptions.py app/services/doctor_clinic_service.py
git commit -m "feat(doctor-clinic): service + BadRequestError for mapping validation"
```

---

### Task 4: `doctor_clinic` routes + router wiring

**Files:**
- Create: `app/api/v1/routes/doctor_clinic.py`
- Modify: `app/api/v1/router.py`

**Interfaces:**
- Consumes: `DoctorClinicService` (Task 3).
- Produces: routes `GET /api/v1/doctors`, `GET /api/v1/clinics`,
  `GET /api/v1/doctor-clinic-mapping`, `GET /api/v1/visit-type-mapping`.

- [ ] **Step 1: Create `app/api/v1/routes/doctor_clinic.py`**

```python
"""Doctor/clinic config endpoints: doctors, clinics, and their mappings."""

from typing import Any

from app.api.route import create_router
from app.services.doctor_clinic_service import DoctorClinicService

router = create_router()


@router.get("/doctors", response_model=list[dict[str, Any]])
async def list_doctors() -> list[dict[str, Any]]:
    return await DoctorClinicService().list_doctors()


@router.get("/clinics", response_model=list[dict[str, Any]])
async def list_clinics() -> list[dict[str, Any]]:
    return await DoctorClinicService().list_clinics()


@router.get("/doctor-clinic-mapping", response_model=dict[str, Any])
async def doctor_clinic_mapping(
    doctor_id: str | None = None, clinic_id: str | None = None
) -> dict[str, Any]:
    return await DoctorClinicService().doctor_clinic_mapping(
        doctor_id=doctor_id, clinic_id=clinic_id
    )


@router.get("/visit-type-mapping", response_model=list[dict[str, Any]])
async def visit_type_mapping(
    doctor_id: str | None = None, clinic_id: str | None = None
) -> list[dict[str, Any]]:
    return await DoctorClinicService().visit_type_mapping(
        doctor_id=doctor_id, clinic_id=clinic_id
    )
```

- [ ] **Step 2: Include the router in `app/api/v1/router.py`**

Add `doctor_clinic` to the import and include it with no extra prefix:

```python
from app.api.v1.routes import chat, doctor_clinic, health, scheduling

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(doctor_clinic.router, tags=["doctor-clinic"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["scheduling"])
```

- [ ] **Step 3: Verify boot + routes registered**

Run: `uv run python -c "import app.main" && uv run ruff check .`
Expected: no error; `All checks passed!`.

- [ ] **Step 4: Verify endpoints behave (validation 400 + wiring 502)**

```bash
uv run uvicorn app.main:app --port 8099 > /tmp/uvi2.log 2>&1 &
UVIPID=$!
for i in $(seq 1 20); do curl -s -o /dev/null -H "X-Tenant-ID: t1" http://127.0.0.1:8099/api/v1/health && break; sleep 0.5; done
echo "--- mapping with neither param (expect 400 BAD_REQUEST envelope) ---"
curl -s -H "X-Tenant-ID: t1" "http://127.0.0.1:8099/api/v1/doctor-clinic-mapping"
echo ""
echo "--- doctors (expect 502 INTERNAL_API_ERROR: fake host unreachable) ---"
curl -s -H "X-Tenant-ID: t1" "http://127.0.0.1:8099/api/v1/doctors"
echo ""
kill $UVIPID 2>/dev/null
```
Expected: first call returns an `error` envelope with `"errorCode":"BAD_REQUEST"` and status 400;
second returns an `error` envelope with `"errorCode":"INTERNAL_API_ERROR"` and status 502. Both
prove routing + service + client + error handling without a live backend.

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/routes/doctor_clinic.py app/api/v1/router.py
git commit -m "feat(doctor-clinic): doctors, clinics, doctor-clinic and visit-type mapping endpoints"
```

---

## Self-Review

- **Spec coverage (§2 rows 4–7):** `/doctors` (Task 4), `/clinics` (Task 4),
  `/doctor-clinic-mapping` (Task 3 logic + Task 4 route), `/visit-type-mapping` (Task 3 + 4). All
  routed through `DoctorClinicService` → `DoctorClinic` client on `/api/v1/common/*`.
- **Envelope handling:** Task 1 centralizes `data` unwrapping; pagination `content` normalized in the
  client. Existing `Scheduling`/`Patient` payload assumptions now hold.
- **No placeholders:** every step has concrete code + commands + expected output.
- **Type consistency:** `doctor_clinic` attribute and method names match across client (Task 2),
  service (Task 3), and routes (Task 4). `BadRequestError` defined (Task 3) before use.
- **Open items (unchanged from spec §14):** exact `/api/v1/common/*` paths, pagination shape, and
  visit-types query params confirmed against the live ClinicalOps API; response DTOs can be
  tightened once upstream fields are known.
