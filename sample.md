# Standard Response Formats

Conventions used by the ClinicalOps Scheduling Agent API. All responses are
JSON. The `X-Request-ID` header is echoed on every response for tracing.

## Simple response

A single resource is returned as a bare JSON object matching its schema. No
outer envelope.

```json
{
  "appointment_id": "appt_9f2c1a",
  "slot_id": "slot_4471",
  "patient_id": "pat_00817",
  "status": "booked"
}
```

Health check (`GET /api/v1/health`):

```json
{
  "status": "ok",
  "service": "clinicalops-scheduling-agent",
  "version": "0.1.0"
}
```

## Error response

Every error uses a single envelope with a stable machine-readable `code` and a
human-readable `message`. The HTTP status carries the class of error.

```json
{
  "error": {
    "code": "missing_tenant",
    "message": "Missing required header: X-Tenant-ID"
  }
}
```

| Code                 | HTTP | Meaning                                          |
| -------------------- | ---- | ------------------------------------------------ |
| `missing_tenant`     | 400  | Tenant header not supplied by the gateway        |
| `internal_api_error` | 502  | A downstream internal microservice call failed   |
| `internal_error`     | 500  | Unhandled server error                           |

## Pagination response

List endpoints return items under `data` alongside a `pagination` block.

```json
{
  "data": [
    {
      "slot_id": "slot_4471",
      "practitioner_id": "prac_221",
      "start": "2026-07-10T09:00:00Z",
      "end": "2026-07-10T09:30:00Z",
      "status": "free"
    },
    {
      "slot_id": "slot_4472",
      "practitioner_id": "prac_221",
      "start": "2026-07-10T09:30:00Z",
      "end": "2026-07-10T10:00:00Z",
      "status": "free"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 57,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```
