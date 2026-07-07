# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Uses `uv` (Python 3.14). All commands run through `uv run`.

```bash
uv sync                                    # install deps (incl. dev group)
cp .env.example .env                       # configure internal API base URLs
uv run uvicorn app.main:app --reload       # dev server on :8000 (Swagger at /docs)
uv run pytest                              # run all tests
uv run pytest tests/test_health.py::test_health   # run a single test
uv run ruff check .                        # lint (import sorting only; see [tool.ruff.lint] select=["I"])
uv run ruff check --fix .                  # auto-fix imports
```

`asyncio_mode = "auto"` — async tests need no `@pytest.mark.asyncio` decorator.

## The one hard boundary

This service **never talks to FHIR or a database directly.** All data access goes
through internal microservices over HTTP, reached via clients in [app/clients/](app/clients/).
Only internal-API base URLs are ever configured — never FHIR/DB connection strings.
If a task seems to require a DB driver or FHIR client here, it belongs in a different
microservice.

## Architecture

Request flow: **API Gateway (`clinicalops-patient-gateway`) → this service (chatbot orchestrator)
→ internal APIs → FHIR/DB.** The gateway authenticates the caller (patient JWT) and forwards a
fixed set of context headers (`HeaderConstants` in the gateway's `common-lib`):
`Authorization`, `X-Tenant-ID`, `X-User-ID`, `X-Roles`, `X-Permissions`, and for correlation
**`X-Trace-ID`** (this platform uses trace id, **not** `X-Request-ID`).

Four cross-cutting mechanisms carry most of the design and span multiple files:

### 1. Multi-tenancy via contextvars (never threaded through call args)
- [TenantMiddleware](app/middleware/tenant.py) reads `X-Tenant-ID` and stores a
  `TenantContext` in a contextvar ([app/core/context.py](app/core/context.py)).
  `/health`, `/docs`, `/openapi.json`, `/redoc` are exempt; otherwise `REQUIRE_TENANT`
  makes a missing header a 400.
- [RequestContextMiddleware](app/middleware/request_context.py) reads/echoes the trace id
  (`X-Trace-ID`, generating one if absent) into a contextvar for cross-service correlation.
- [BaseInternalClient](app/clients/internal/base.py) reads both contextvars (`X-Tenant-ID`,
  `X-Trace-ID`) and re-attaches them as headers on every outbound call. **Services and agent
  tools never see tenant data** — they focus on task logic; tenancy is applied entirely in the client layer.

### 2. Client lifecycle: build once, borrow per request
- [ClientRegistry](app/clients/registry.py) composes the client groups
  (`internal`, `vault`, `redis`), each a [ManagedClient](app/clients/lifecycle.py)
  with `startup()`/`shutdown()`. Built once in the [app lifespan](app/main.py) and
  published via the [ClientProvider](app/clients/provider.py) singleton.
- [InternalAPIClients](app/clients/internal/client.py) owns pooled `httpx.AsyncClient`
  instances (one per internal service). Services reach everything through
  [BaseService](app/services/base.py) → `ClientProvider.get()`; they never construct clients.

### 3. Response envelope applied natively at the route layer
- Use [create_router()](app/api/route.py) from `app.api.route`, **not** `fastapi.APIRouter`.
  Its `EnvelopeRoute` wraps each endpoint's return value into a `SuccessResponse[T]`
  envelope and rewrites the declared `response_model` accordingly, so FastAPI still
  generates a correct OpenAPI schema — no separate patching step.
- Return a bare DTO for the default envelope; return a `SuccessResponse` subclass
  (e.g. `ChatEnvelope` with root-level `ui_directives`) to control message/status or add siblings of `data`.
- Errors are normalized to the matching `ErrorResponse` shape by handlers in
  [app/core/exceptions.py](app/core/exceptions.py) (app errors, validation, HTTP, uncaught).
  Envelope builders live in [app/core/envelope.py](app/core/envelope.py). Raise `AppError`
  subclasses (`MissingTenantError`, `InternalAPIError`) rather than returning error responses.

### 4. Agent layer (ADK skeleton — not yet wired)
[app/agents/](app/agents/) is intentionally unimplemented: `google-adk` is **not yet a
dependency** and its imports are deferred (`TYPE_CHECKING` / build-time) so modules stay
import-safe. When implementing ADK:
- [AgentProvider](app/agents/provider.py) mirrors `ClientProvider` — build the `Runner`
  once at startup (see the `# TODO` in [app/main.py](app/main.py) lifespan), borrow per request.
- [tools.py](app/agents/tools.py) tools are thin wrappers over
  [SchedulingService](app/services/scheduling_service.py); their docstrings are the tool
  descriptions the LLM reads.
- [ChatService](app/services/chat_service.py) borrows the shared runner and translates its
  events into a `ChatResponse`.

## Code style

- Do not add unnecessary comments.
- All imports go at the top of the file, never inline.
- Every environment variable used must be defined in [app/core/config.py](app/core/config.py).

## Layering

`api/v1/routes/` (thin, envelope routers) → `services/` (orchestration, no tenant handling)
→ `clients/internal/*` (HTTP + tenant/trace-id propagation). Config is layered pydantic
settings with env prefixes: `INTERNAL_`, `VAULT_`, `REDIS_` ([app/core/config.py](app/core/config.py)),
accessed via the `lru_cache`d `get_settings()`.

## Adding capabilities

- **New internal dependency:** add a client in [app/clients/internal/](app/clients/internal/),
  wire its pool in [client.py](app/clients/internal/client.py), add its base URL to
  `InternalAPISettings` in [config.py](app/core/config.py) and to `.env.example`.
- **New endpoint:** create the router with `create_router()`, include it in
  [app/api/v1/router.py](app/api/v1/router.py).

---

# Behavioral guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
