"""Application entrypoint."""

from fastapi import FastAPI

from atlas.api.routes import health
from atlas.core.config import get_settings
from atlas.core.logging import configure_logging
from atlas.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )

    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)

    return app


app = create_app()
