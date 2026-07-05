"""Route class and router factory that apply the success envelope natively.

Instead of rewriting response bytes in middleware, ``EnvelopeRoute`` wraps the
endpoint's *return value* before FastAPI serializes it and rewrites the declared
``response_model`` to the enveloped form. That keeps a single source of truth:
FastAPI generates the OpenAPI schema (success envelope included) itself, so no
separate schema-patching step is needed.

Endpoints stay clean::

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(...)          # -> {"data": {...}, "status": ...}

To control the message/status code, or to add root-level siblings of ``data``
(e.g. ``ui_directives``), return a ``SuccessResponse`` subclass yourself and it
is passed through untouched::

    @router.post("", response_model=ChatEnvelope)
    async def chat(...) -> ChatEnvelope:
        return ChatEnvelope(data=..., ui_directives=UiDirectives(...))
"""

import functools
import inspect
from typing import Any, Callable

from fastapi import APIRouter
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool

from app.schemas.common import ErrorResponse, SuccessResponse

# Standard error responses documented on every enveloped operation. The
# exception handlers emit these envelopes at runtime; this just documents them.
_ERROR_DESCRIPTIONS = {
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    422: "Validation Error",
    500: "Internal Server Error",
    502: "Bad Gateway",
}

DEFAULT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    code: {"model": ErrorResponse, "description": description}
    for code, description in _ERROR_DESCRIPTIONS.items()
}


def _is_envelope(model: Any) -> bool:
    return isinstance(model, type) and issubclass(model, SuccessResponse)


def _to_envelope(result: Any, *, default_status: int) -> SuccessResponse:
    """Wrap a bare endpoint payload; pass through an already-built envelope."""
    if isinstance(result, SuccessResponse):
        return result
    return SuccessResponse(status_code=default_status, data=result)


def _wrap_endpoint(endpoint: Callable[..., Any], *, default_status: int) -> Callable[..., Any]:
    """Return an async endpoint that envelopes the wrapped endpoint's result.

    ``functools.wraps`` keeps ``__wrapped__`` pointing at the original, so
    ``inspect.signature`` (and therefore FastAPI's dependency resolution) still
    sees the real parameters — path/query/body params and ``Depends`` are
    untouched.
    """
    endpoint_is_async = inspect.iscoroutinefunction(endpoint)

    @functools.wraps(endpoint)
    async def wrapper(**values: Any) -> Any:
        if endpoint_is_async:
            result = await endpoint(**values)
        else:
            result = await run_in_threadpool(endpoint, **values)
        return _to_envelope(result, default_status=default_status)

    return wrapper


class EnvelopeRoute(APIRoute):
    def __init__(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
        response_model = kwargs.get("response_model")
        if response_model is not None and not _is_envelope(response_model):
            kwargs["response_model"] = SuccessResponse[response_model]

        default_status = kwargs.get("status_code") or 200
        wrapped = _wrap_endpoint(endpoint, default_status=default_status)
        super().__init__(path, wrapped, **kwargs)


def create_router(**kwargs: Any) -> APIRouter:
    """APIRouter that envelopes responses and documents the standard errors."""
    responses = {**DEFAULT_ERROR_RESPONSES, **kwargs.pop("responses", {})}
    return APIRouter(route_class=EnvelopeRoute, responses=responses, **kwargs)
