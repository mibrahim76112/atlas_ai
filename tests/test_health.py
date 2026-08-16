"""Tests for the health endpoint."""

import uuid

import pytest
from fastapi.testclient import TestClient

from atlas.core.config import get_settings
from atlas.main import create_app


@pytest.fixture
def client() -> TestClient:
    """A test client backed by a freshly built application."""
    return TestClient(create_app())


def test_health_returns_ok(client: TestClient) -> None:
    """The liveness probe reports the application's identity and status."""
    settings = get_settings()

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == settings.app_name
    assert body["environment"] == settings.environment
    assert body["version"] == "0.1.0"


def test_health_echoes_incoming_request_id(client: TestClient) -> None:
    """An inbound correlation ID is preserved, not replaced."""
    response = client.get("/health", headers={"X-Request-ID": "test-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-123"


def test_health_generates_request_id_when_absent(client: TestClient) -> None:
    """A correlation ID is minted when the caller doesn't supply one."""
    response = client.get("/health")

    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    uuid.UUID(request_id)  # raises ValueError if it isn't a valid UUID
