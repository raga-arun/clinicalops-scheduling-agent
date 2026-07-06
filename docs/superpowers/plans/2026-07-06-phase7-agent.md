# Phase 7: ADK Scheduling Agent Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Wire a working Google ADK `LlmAgent` (Gemini) that orchestrates the Phase 1-6 services as capability tools, driven per-turn through a shared `Runner`, and surfaced via the existing `POST /api/v1/chat` endpoint with `ui_directives`.

**Architecture:** One `LlmAgent` + ~10 thin capability tools wrapping the services (no `collected_data` blob, no step-machine). A shared `Runner` + `InMemorySessionService` built once at startup (`AgentProvider`), borrowed per request. `ChatService` drives one turn, collects the final reply and the tool calls made, and maps those to `ui_directives`. Tenancy stays entirely in the client layer — tools never see tenant data.

**Tech Stack:** google-adk (Gemini), FastAPI, ADK `InMemorySessionService`.

## Global Constraints

- Work ONLY in `clinicalops-scheduling-agent`.
- Capability-tools + LLM orchestration (user decision 2026-07-06); NOT the original step-machine.
- Non-rigid flow; NO `collected_data` blob; NO per-step Redis writes.
- Drop: Azure session save/load, SMS/email notifications, post-booking rating (user decision 2026-07-06), admin/Healow/ECW.
- Sessions via ADK `InMemorySessionService` (per-process stub; durable backend deferred).
- Services return `dict`/`list[dict]`; tools return the same, JSON-serializable for the LLM.
- Every env var defined in `app/core/config.py`; add to `.env.example` with NO secret values.
- ADK/Gemini credentials (`GOOGLE_API_KEY`) sourced from env (Vault in prod); model id from config.
- Commit messages: plain conventional-commit, NO AI/Claude attribution, NO `Co-Authored-By`.
- Preserve the original's persona + security/non-disclosure guardrails in the instruction (trimmed, tool-name lists removed since tools are generic).

---

### Task 1: Dependency + agent config

**Files:**
- Modify: `pyproject.toml` (add `google-adk`)
- Modify: `app/core/config.py` (add `AgentSettings`, env prefix `AGENT_`)
- Modify: `.env.example`

`AgentSettings`: `name: str = "Ava"`, `model: str = "gemini-2.0-flash"`, `max_output_tokens: int = 600`.
`.env.example` adds `AGENT_NAME`, `AGENT_MODEL`, `GOOGLE_API_KEY=`, `GOOGLE_GENAI_USE_VERTEXAI=false`.

### Task 2: Capability tools

**Files:**
- Rewrite: `app/agents/tools.py`

~10 async tools wrapping services (docstrings = tool descriptions):
`list_doctors`, `list_clinics`, `list_doctor_clinics(doctor_id, clinic_id)`,
`find_available_dates(doctor_id, clinic_id, slot_type)`,
`find_slots(doctor_id, clinic_id, date, slot_type)`,
`lookup_patient(phone, date_of_birth, name)`,
`register_patient(name, date_of_birth, phone, gender, email)`,
`book_appointment(slot_id, patient_id, doctor_id, clinic_id, slot_type, reason)`,
`cancel_appointment(appointment_id)`,
`submit_insurance(patient_id, insurance_provider, insurance_member_id)`.
Export `SCHEDULING_TOOLS: list` of the raw functions (ADK wraps callables).

### Task 3: Agent definition + trimmed instruction

**Files:**
- Rewrite: `app/agents/scheduling_agent.py`

`build_scheduling_agent() -> LlmAgent` reading name/model/max_output_tokens from config,
instruction = trimmed persona + security guardrails + non-rigid flow guide, `tools=SCHEDULING_TOOLS`.

### Task 4: Provider + lifespan wiring

**Files:**
- Rewrite: `app/agents/provider.py` (build Runner + InMemorySessionService; expose runner + session_service + a `create_session` helper)
- Modify: `app/main.py` (call `AgentProvider.build()` / `AgentProvider.reset()` in lifespan)

### Task 5: ChatService drives a turn + ui_directives

**Files:**
- Rewrite: `app/services/chat_service.py`
- Modify: `app/schemas/chat.py` (add `ChatResult` carrying `ChatResponse` + `UiDirectives`)
- Modify: `app/api/v1/routes/chat.py` (unpack result → envelope; add `GET /chat/{session_id}` history)

`handle(req) -> ChatResult`: ensure ADK session, run one turn, collect final text + tool names,
map tools→directives (`list_*`→show_selections, `find_*`→show_calendly), return response + directives.

### Task 6: Verify + commit

`uv run python -c "import app.main"`, `uv run ruff check .`, uvicorn boot; `POST /chat`
returns 502/agent-error path without real Gemini creds (or a reply if creds present). Commit.
