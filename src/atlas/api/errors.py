"""Translate application errors into HTTP responses."""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from atlas.core.exceptions import (
    AppError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

_STATUS_BY_TYPE: list[tuple[type[AppError], int]] = [
    (AuthenticationError, 401),
    (PermissionDeniedError, 403),
    (NotFoundError, 404),
    (ConflictError, 409),
]


def _status_for(exc: AppError) -> int:
    for exc_type, status_code in _STATUS_BY_TYPE:
        if isinstance(exc, exc_type):
            return status_code
    return 500


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render an AppError as a consistent JSON error body."""
    if not isinstance(exc, AppError):
        raise exc

    status_code = _status_for(exc)

    if status_code >= 500:
        logger.exception("unhandled application error")

    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every application exception handler to the app."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render Pydantic validation failures in the same envelope as AppError."""
    if not isinstance(exc, RequestValidationError):
        raise exc

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "The request body is invalid.",
                "details": jsonable_encoder(exc.errors()),
            }
        },
    )
