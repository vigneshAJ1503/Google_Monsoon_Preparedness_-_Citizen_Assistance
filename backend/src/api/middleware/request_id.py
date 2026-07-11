"""
Middleware: Request ID injection for correlation across services.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into every request for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Bind to structlog context for all logs in this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
