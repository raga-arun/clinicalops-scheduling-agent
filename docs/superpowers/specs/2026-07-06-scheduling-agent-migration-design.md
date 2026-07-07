# Scheduling Agent Migration — Design

**Date:** 2026-07-06
**Target repo:** `clinicalops-scheduling-agent` (multi-tenant FastAPI chatbot orchestrator)
**Source (reference only):** `scheduling-agent-chacko-allergy/medical_scheduling_agent` (single-tenant, ~20k LOC)
**Philosophy reference (do not copy patterns):** `clinicalops-scheduling-voice-agent`

## 1. Goal

Migrate the working single-tenant scheduling agent into the new multi-tenant repo, preserving the
**conversational flow** while replacing the architecture. The old service does everything itself
(FHIR, Azure blob/OpenAI, healow/ECW, SMS/email, Google Places). The new service is a **thin
orchestrator**: it holds the agent + flow logic and delegates all data/persistence to internal
ClinicalOps APIs over HTTP.

Highest priority: **standardization and maintainability** — small single-purpose files, clean
layering, consistent request/response envelopes, proper logging. The old code's structure is not a
model to follow.

## 2. Scope

### In — the 17 endpoints migrated in this effort

| Endpoint | Route file | Service | Backing internal/external call |
|---|---|---|---|
| `POST /api/v1/appointments/start-session` | `chat.py` | `SessionService` | internal session API — **not ready → stub** (see §6 schema) |
| `GET  /api/v1/appointments/session/{session_id}` | `chat.py` | `SessionService` | internal session API — **not ready → stub** |
| `POST /api/v1/appointments/message` | `chat.py` | `ChatService` | ADK runner (Gemini) → tools → services |
| `GET  /api/v1/doctors` | `doctor_clinic.py` | `DoctorClinicService` | `GET /api/v1/common/doctors` |
| `GET  /api/v1/clinics` | `doctor_clinic.py` | `DoctorClinicService` | `GET /api/v1/common/clinics` |
| `GET  /api/v1/doctor-clinic-mapping` | `doctor_clinic.py` | `DoctorClinicService` | internal common API |
| `GET  /api/v1/visit-type-mapping` | `doctor_clinic.py` | `DoctorClinicService` | internal common API |
| `GET  /api/v1/address/places/autocomplete` | `address.py` | `AddressService` | **external places service (via client)** |
| `GET  /api/v1/address/places/get` | `address.py` | `AddressService` | **external places service (via client)** |
| `GET  /api/v1/appointments/schedule` | `slots.py` | `SlotsService` | `GET /api/v1/common/slots*` |
| `GET  /api/v1/appointments/slots` | `slots.py` | `SlotsService` | internal slots API |
| `GET  /api/v1/appointments/month-slots` | `slots.py` | `SlotsService` | internal slots API |
| `GET  /api/v1/appointments/nearest-dates-slots` | `slots.py` | `SlotsService` | internal slots API |
| `POST /api/v1/appointments/patient/lookup` | `patient.py` | `PatientService` | `POST /api/v1/schedule/patients/lookup` |
| `POST /api/v1/appointments/appointment` | `appointments.py` | `AppointmentService` | `POST /api/v1/schedule/appointments` |
| `POST /api/v1/appointments/cancel` | `appointments.py` | `AppointmentService` | internal appointment cancel |
| `POST /api/v1/appointments/insurance-upload` | `insurance.py` | `InsuranceService` | internal insurance API — **not ready → stub** |
| `POST /api/v1/webhooks/twilio-reminder-response` | `webhooks.py` | `WebhookService` | internal session + appointment cancel |

Exact internal endpoint paths are confirmed at implementation time against the ClinicalOps API; the
reference voice agent uses `/api/v1/common/*` (doctors, clinics, slots) and `/api/v1/schedule/*`
(patients, appointments).

### Out — explicitly not migrated in this effort

Phone verification (`/verification/phone/*`),
`multi-doctor-clinic-mapping`, `month-slots-multi-doctor-clinic`, `*-with-all`, all `admin-*`
reschedule/cancel, `reset-cancellation`, insurance capture / `get-insurance`, patient create /
`profile-lookup`, ECW-direct search routes, `message/public/message`.

### Dropped entirely (deleted concepts, not ported)

Azure (blob, OpenAI, S3 fallback), healow/ECW clients, in-service notifications (SMS/email — the
**internal scheduling API sends these itself** on book/cancel), the monoliths
(`agent_original.py`, `main.py`, `agent_wrapper.py`, `admin_utils.py`), and the
`RedisEnhancedSessionManager` / `collected_data` state model.

## 3. Architecture & layering

```
route (thin, envelope)  →  service (all logic)  →  client (HTTP: internal or external)
                                                 →  agent tools call services, never clients
```

- Routes use `create_router()` (envelope-aware) and only parse/validate input and call a service.
- **Services own the logic.** Tools are thin wrappers that call services. Services call clients.
- Tenancy/trace are applied **only in the client layer** (contextvars → headers). Services, tools,
  and routes never see or thread tenant data.

### Directory layout (single-purpose files)

```
app/
  api/v1/routes/
    health.py            # exists
    chat.py              # start-session, session/{id}, message
    doctor_clinic.py     # doctors, clinics, doctor-clinic-mapping, visit-type-mapping
    address.py           # places/autocomplete, places/get
    slots.py             # schedule, slots, month-slots, nearest-dates-slots
    appointments.py      # appointment (book), cancel
    patient.py           # patient/lookup
    insurance.py         # insurance-upload
    webhooks.py          # twilio-reminder-response
  services/
    chat_service.py          # drives the ADK runner → ChatResponse + ui_directives
    session_service.py       # scheduling_agent_sessions CRUD via internal API (stub until ready)
    doctor_clinic_service.py
    address_service.py       # external places service
    slots_service.py
    appointment_service.py   # book + cancel
    patient_service.py       # lookup
    insurance_service.py     # upload (stub until ready)
    webhook_service.py       # reminder-response handling
    nlu/extraction.py        # Gemini structured extraction (replaces Azure OpenAI + insurance_nlp)
    base.py                  # exists (ClientProvider access)
  agents/
    scheduling_agent.py      # LlmAgent construction (wire existing skeleton)
    prompts.py               # instruction / prompt text
    provider.py              # Runner provider (exists)
    tools/
      greeting.py, patient.py, insurance.py, calendar.py, selections.py, rating.py
  clients/
    internal/
      base.py                # exists — tenant/trace/agent-type header propagation
      group.py               # one pooled httpx client, shared base URL
      patient.py             # class Patient
      scheduling.py          # class Scheduling  (slots)
      appointments.py        # class Appointments (book/cancel)
      doctor_clinic.py       # class DoctorClinic (doctors/clinics/mapping)
      insurance.py           # class Insurance (stub)
      session.py             # class Session (scheduling_agent_sessions, stub)
    external/
      places.py              # class Places — external places service client (no API key held here)
    redis/ , vault/          # exist
  core/
    config.py                # single INTERNAL_API_URL; drop per-host URLs & Azure/ECW
    formatting.py, validators.py  # slim reusable helpers ported from old formatting/validators
    (context, envelope, exceptions, logging — exist)
  schemas/
    chat.py, doctor_clinic.py, address.py, slots.py, appointment.py, patient.py, insurance.py, session.py
```

Client class names drop the `Client` suffix and are grouped by internal-API module, not per
endpoint (`Patient`, `Scheduling`, `Appointments`, `DoctorClinic`, `Insurance`, `Session`).

## 4. Internal API client design

- **Single base URL** `INTERNAL_API_URL` (matches the reference and real ClinicalOps API). Collapse
  the scaffold's `scheduling_base_url` / `patient_base_url` / `availability_base_url`. Delete
  `availability_client` (slots live under `/api/v1/common/slots`).
- All domain client classes share **one pooled `httpx.AsyncClient`** and carry their own path
  prefix (`/api/v1/common`, `/api/v1/schedule`).
- `BaseInternalClient` keeps the repo's contextvar propagation and adds an `X-Agent-Type` header
  (from config) so the internal API can distinguish this chat agent from the voice agent.
- **Not-ready endpoints** (session, insurance): the client method + service method are fully defined
  with the expected request/response shape, but the HTTP call is stubbed behind a clear
  `# TODO(internal-api-not-ready)` marker returning a typed placeholder, so wiring is a one-line
  change when the API lands.

## 5. State model (the key change)

No local `collected_data` blob, no session snapshot in Redis, no per-step Redis writes.

- **Session state lives in the internal `scheduling_agent_sessions` table** (§6). As the agent
  collects each field it **persists it to that row via `SessionService`** → internal session API.
- `current_step` on the row is the flow position (replaces `collected_data.current_tool`).
- **Booking** = a single `POST /schedule/appointments`; nothing about the appointment is kept
  locally afterward.
- **Redis only when genuinely needed** — ADK conversation continuity across turns, and transient
  values (e.g. an OTP if introduced later). Not a write on every step.

## 6. Session schema (internal `scheduling_agent_sessions`)

```sql
id UUID PK, created_at, created_by, updated_at, updated_by, version, is_deleted,
patient_id UUID, name, date_of_birth DATE, phone_e164, email, source,
provider_id UUID, clinic_id UUID, visit_type_id UUID,
preferred_contact_method, status DEFAULT 'active', current_step
```

`SessionService`/`Session` client mirror this shape. `start-session` creates a row (stub);
`session/{id}` reads it (stub); tools update fields as collected.

## 7. Agent design (flow preserved)

- **ADK + Gemini** for both conversation and structured extraction (Azure OpenAI dropped).
- **Flow unchanged:** greeting → patient detection → insurance → reason-for-visit → slot/calendar
  selection → confirmation → rating. Same tool set, re-expressed thin.
- `scheduling_agent.py` builds the `LlmAgent`; instruction text in `prompts.py` to keep the agent
  file small. Tools split by group under `agents/tools/`.
- **Message turn:** `POST /chat/message` → `ChatService` borrows the shared `Runner` (built once at
  startup via `AgentProvider`), runs one turn natively async (no `asyncio.run`/`process_user_turn`),
  returns final text + `ui_directives` in the existing `ChatEnvelope`.
- `ui_directives` (`show_calendar`, `show_rating`, `need_selections`) remain the frontend contract,
  derived from the agent's explicit turn output / current session step — not from a local blob.
- **Not rigid:** flow order comes from the prompt + tool set, not hardcoded branching, so per-tenant
  flow configuration can be added later without restructuring.

## 8. Address / places (external service)

`AddressService` → `clients/external/places.py` calls a **separate external places service** over
HTTP for autocomplete + details. This agent holds **no Google Maps API key** — Google Places
credentials and calls live in that external service. Base URL via config (`PLACES_API_URL`).

## 9. Twilio reminder webhook

Re-target the old Azure-blob + `admin_cancel` logic to internal APIs:
- Record the reminder reply; on `user_response == "no"` (without `request_for_cancellation`), cancel
  the appointment via the internal appointment-cancel endpoint.
- Reminder-tracking fields are **not** in `scheduling_agent_sessions`, so reminder-history
  persistence is deferred/stubbed; the cancel-on-"no" behavior is preserved.

## 10. Config / env

- Add `INTERNAL_API_URL`, `INTERNAL_API_TIMEOUT`, `AGENT_TYPE`, `PLACES_API_URL`,
  Gemini/ADK model + key settings to `app/core/config.py`; remove per-host internal URLs and all
  Azure/ECW settings. **No `GOOGLE_MAPS_API_KEY`** — the external places service owns it.
- Every env var used is defined in `config.py` and listed in `.env.example` (no secret values).
- Add `google-adk` to `pyproject.toml`.

## 11. Logging

Structured logging via the repo's `core/logging.py` at each layer boundary (route entry, service
action, outbound client call + status, agent turn start/end + tool invocations). No `print`.

## 12. Testing

**Deferred this pass** per instruction — build structure + logging, not tests. Internal session/
insurance APIs aren't ready, so tests come in the next step.

## 13. Phasing (each phase = its own implementation plan)

1. **Foundation** — config (single URL, drop Azure), `google-adk` dep, `base`/`group` client
   rework, `.env.example`, header propagation (`X-Agent-Type`).
2. **Doctor–clinic** — `doctor_clinic` route/service/client (read-only first slice).
3. **Address** — external places client + `address` route/service.
4. **Slots** — `slots` route/service + slot client methods.
5. **Patient + appointments** — lookup, book, cancel.
6. **Session + insurance (stubs)** — `SessionService`/`Session`, `InsuranceService`/`Insurance`
   against the known shapes.
7. **Agent** — tools split, agent + prompts + runner wiring, chat flow (`start-session`,
   `message`, `session/{id}`), `ui_directives`, `nlu/extraction`.
8. **Webhook** — reminder-response re-targeting.

## 14. Open items / assumptions

- Exact internal endpoint paths for slots/patient-lookup/cancel confirmed at implementation against
  the live ClinicalOps API (reference paths in §2).
- `X-Agent-Type` value for this agent to be confirmed.
- Address/places is served by a separate external places service reached via `PLACES_API_URL`
  (this agent holds no Google key). Confirm that base URL / whether it shares the internal gateway.
