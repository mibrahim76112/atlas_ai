"""ASGI middleware."""

import logging
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from atlas.core.context import request_id_ctx

REQUEST_ID_HEADER = b"x-request-id"

logger = logging.getLogger(__name__)


class RequestContextMiddleware:
    """Attach a correlation ID to every request and log its completion."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(REQUEST_ID_HEADER)
        request_id = incoming.decode() if incoming else str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER, request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "request completed",
                extra={
                    "extra_fields": {
                        "method": scope["method"],
                        "path": scope["path"],
                        "status_code": status_code,
                        "duration_ms": round(duration_ms, 2),
                    }
                },
            )
            request_id_ctx.reset(token)
