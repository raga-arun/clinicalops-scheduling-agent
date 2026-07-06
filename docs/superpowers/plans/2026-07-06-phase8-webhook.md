# Phase 8: Twilio Reminder Webhook Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Re-target the original Azure-backed `twilio-reminder-response` webhook to the new architecture: cancel the appointment on a "no" reply, drop all Azure/session-blob persistence.

**Architecture:** Route → `WebhookService` → `AppointmentService` (cancel). The reminder is per-appointment, so the payload carries `appointment_id` (the old flow located it via the Azure session blob, which no longer exists). Tenancy flows through the existing middleware/contextvar; Twilio Studio must send `X-Tenant-ID`.

**Tech Stack:** FastAPI, existing envelope router + services.

## Global Constraints

- Work ONLY in `clinicalops-scheduling-agent`.
- Drop Azure blob persistence and the `reminder_tracking` session store (no durable session backend exists; sessions deferred to ADK).
- Preserve the original yes/no + `request_for_cancellation` branch semantics, minus persistence.
- Services return `dict` pass-through; request DTO OK.
- Cancel via the existing `AppointmentService.cancel`; no new internal client.
- Commit messages: plain conventional-commit, NO AI/Claude attribution, NO `Co-Authored-By`.

## Behavior

- `user_response == "yes"` → acknowledge, no action.
- `user_response == "no"`, `request_for_cancellation == false` → cancel `appointment_id`.
- `user_response == "no"`, `request_for_cancellation == true` → acknowledge only
  (cancellation already being handled elsewhere; mirrors the original's flag branch).

---

### Task 1: Webhook request schema

**Files:**
- Create: `app/schemas/webhook.py`

`TwilioReminderResponse(Model)`: `appointment_id: str`, `reminder_type: str`,
`user_response: Literal["yes", "no"]`, `request_for_cancellation: bool = False`,
`patient_id: str | None = None`, `session_id: str | None = None` (last two for correlation/logging).

### Task 2: Webhook service

**Files:**
- Create: `app/services/webhook_service.py`

`WebhookService(BaseService).handle_reminder_response(req) -> dict` implementing the
branch behavior above, logging the response, calling `AppointmentService().cancel`
on the cancel path, returning `{appointmentId, reminderType, userResponse, action}`.

### Task 3: Webhook route + wire router

**Files:**
- Create: `app/api/v1/routes/webhook.py`
- Modify: `app/api/v1/router.py`

`POST /webhooks/twilio-reminder-response` (TwilioReminderResponse) →
`WebhookService().handle_reminder_response`. Include router, tag `webhook`.

### Task 4: Verify + commit

`uv run python -c "import app.main"`, `uv run ruff check .`, uvicorn boot + curl
(400 missing body; "yes" → acknowledged 200-envelope; "no" → 502 cancel reaching fake host). Commit.
