"""Application entrypoint."""

from fastapi import FastAPI

from atlas.api.errors import register_exception_handlers
from atlas.api.routes import auth, health
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
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
