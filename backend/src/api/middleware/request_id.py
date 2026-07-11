"""Middleware: Request ID injection for correlation across services."""

import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into every request for tracing."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and inject request ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/app in chain

        Returns:
            HTTP response with X-Request-ID header

        """
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Bind to structlog context for all logs in this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
