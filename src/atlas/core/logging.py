"""Structured JSON logging."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from atlas.core.context import request_id_ctx


class JSONFormatter(logging.Formatter):
    """Render each log record as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Install the JSON formatter on the root logger."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
