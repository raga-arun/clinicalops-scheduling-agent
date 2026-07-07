# clinicalops-scheduling-agent

Multi-tenant **FastAPI chatbot microservice for FHIR scheduling**.

This service orchestrates conversational scheduling (find slots, book, cancel,
reschedule). It **never talks to FHIR or a database directly** — all data access
and real bookings happen behind **internal microservices**, which this service
reaches over HTTP through the clients in [app/clients/](app/clients/).

## Architecture

```
API Gateway ──(X-Tenant-ID header)──▶  this service  ──▶  Internal APIs ──▶ FHIR / DB
                                       (chatbot orchestrator)   (scheduling, patient, availability)
```

- **Multi-tenancy** — the gateway authenticates the caller and forwards the
  tenant in `X-Tenant-ID`. [TenantMiddleware](app/middleware/tenant.py) reads it
  into a contextvar; every internal-API call propagates it automatically.
- **No direct FHIR / DB access** — only internal-API base URLs are configured
  (see [app/core/config.py](app/core/config.py)).
- **Internal API clients** — [BaseInternalClient](app/clients/base.py) forwards
  tenant + trace id and normalizes errors; one client per internal service.

## Layout

```
app/
  main.py                 # app factory, middleware wiring, lifespan (client pool)
  core/                   # config, context (tenant/trace-id), logging, exceptions
  middleware/             # tenant extraction, trace-id correlation
  api/
    deps.py               # DI: clients, services, tenant guard
    v1/router.py          # v1 aggregate router
    v1/routes/            # health, chat, scheduling endpoints
  clients/                # client groups behind one ManagedClient lifecycle
    registry.py           #   ClientRegistry: startup/shutdown all groups
    internal/             #   internal microservice HTTP clients (scheduling, patient, availability)
    vault/                #   Vault secrets client
    redis/                #   Redis cache / session client
  services/               # orchestration (chat, scheduling) + nlu/ (intent/LLM)
  schemas/                # pydantic request/response DTOs
tests/                    # pytest + FastAPI TestClient
```

## Getting started

```bash
uv sync                       # install deps
cp .env.example .env          # configure internal API base URLs
uv run uvicorn app.main:app --reload   # dev server on :8000  (Swagger at /docs)
uv run pytest                 # run tests
```

## Extending

- Add a new internal dependency: create a client in `app/clients/`, register it
  in [registry.py](app/clients/registry.py), add its base URL to
  [config.py](app/core/config.py).
- Add conversational capability: extend [Intent](app/services/nlu/intents.py),
  wire a real LLM in [llm.py](app/services/nlu/llm.py), branch in
  [chat_service.py](app/services/chat_service.py).
