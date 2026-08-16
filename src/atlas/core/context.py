"""Request-scoped context, available anywhere without threading it through calls."""

from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
