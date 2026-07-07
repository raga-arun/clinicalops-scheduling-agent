# Phase 9: Phone Verification (OTP) Routes Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Expose the three legacy phone-verification (OTP) routes the existing chatbot frontend calls, delegating to an external verification provider via a dedicated client.

**Architecture:** 3 routes → `VerificationService` → external `Verification` client → external verification/OTP service (owns Twilio Verify + OTP state + any token). Mirrors the Places external-client pattern. The routes use a **plain `APIRouter`** (not `create_router`) so responses are returned raw — the frontend reads the provider's `status`/`message`/`verification` shape at the root, not the ClinicalOps envelope.

**Tech Stack:** FastAPI, httpx external client, pydantic-settings.

## Global Constraints

- Work ONLY in `clinicalops-scheduling-agent`.
- NO changes to the frontend; match its request/response contract exactly (snake_case, non-enveloped).
- External-client pattern (user decision 2026-07-06): own base URL (`VERIFICATION_*`), tenant+trace headers only, no envelope unwrap. Twilio/OTP state stays OUT of this orchestrator.
- No internal OTP contract exists; the external path is provisional and 502s until the provider ships.
- Only the three phone routes are needed (frontend uses all three); email verification is out of scope.
- Services return `dict` pass-through; request DTOs OK.
- Commit messages: plain conventional-commit, NO AI/Claude attribution, NO `Co-Authored-By`.

## Frontend contract (from `frontend/.../services/api.ts`)

- `POST /api/v1/verification/phone/start` — body `{session_id, channel, force_resend}` → `{status, message}` (resend OTP).
- `POST /api/v1/verification/phone/confirm` — body `{session_id, code}` → `{status, message, verification:{status, sid, channel, to, e164_phone?, verified_at?, accessToken?}}`.
- `POST /api/v1/verification/phone/update` — body `{session_id, new_phone_number}` → `{status, message, new_phone_number?}`.
- Errors: non-2xx with a root `message` (our exception envelope already satisfies this).

---

### Task 1: Config + env
`VerificationSettings(env_prefix="VERIFICATION_")` (`base_url`, `timeout_seconds`); add to `Settings`; add `VERIFICATION_BASE_URL`/`VERIFICATION_TIMEOUT_SECONDS` to `.env.example`.

### Task 2: External Verification client
`app/clients/external/verification.py` — `Verification(ManagedClient)` mirroring `Places`,
with `start/confirm/update` POSTing to `/verification/phone/*`; register in `registry.py`.

### Task 3: Schemas + service
`app/schemas/verification.py` (`PhoneVerificationStart`, `PhoneVerificationConfirm`, `PhoneUpdate`);
`app/services/verification_service.py` (`VerificationService` pass-through).

### Task 4: Routes (plain APIRouter) + wire router
`app/api/v1/routes/verification.py` — 3 POST routes returning raw dicts; include in `router.py`.

### Task 5: Verify + commit
`uv run python -c "import app.main"`, `uv run ruff check .`, uvicorn boot + curl:
missing body → 422/400; valid call → 502 (external unreachable) with root `message`;
confirm response NOT enveloped. Commit.
