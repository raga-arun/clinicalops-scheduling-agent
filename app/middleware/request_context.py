"""Request-id middleware for cross-service correlation."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.context import set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        request_id = request.headers.get(settings.request_id_header) or uuid.uuid4().hex
        set_request_id(request_id)

        response = await call_next(request)
        response.headers[settings.request_id_header] = request_id
        return response
