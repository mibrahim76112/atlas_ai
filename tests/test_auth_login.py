"""Tests for login, token rotation, and protected routes."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from atlas.core.config import get_settings

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"

EMAIL = "login@example.com"
PASSWORD = "correct-horse-battery"


async def _register_and_login(client: AsyncClient) -> dict[str, str]:
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})
    response = await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})
    return response.json()


async def test_login_returns_token_pair(client: AsyncClient) -> None:
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    response = await client.post(LOGIN, json={"email": EMAIL, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == get_settings().access_token_expire_minutes * 60


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    response = await client.post(LOGIN, json={"email": EMAIL, "password": "wrong-password-x"})

    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    response = await client.post(LOGIN, json={"email": "nobody@example.com", "password": PASSWORD})

    assert response.status_code == 401


async def test_login_error_does_not_reveal_which_field_was_wrong(client: AsyncClient) -> None:
    await client.post(REGISTER, json={"email": EMAIL, "password": PASSWORD})

    unknown = await client.post(LOGIN, json={"email": "nobody@example.com", "password": PASSWORD})
    bad_password = await client.post(LOGIN, json={"email": EMAIL, "password": "wrong-password-x"})

    assert unknown.json() == bad_password.json()


async def test_me_returns_current_user(client: AsyncClient) -> None:
    tokens = await _register_and_login(client)

    response = await client.get(ME, headers={"Authorization": f"Bearer {tokens['access_token']}"})

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


async def test_me_requires_a_token(client: AsyncClient) -> None:
    response = await client.get(ME)

    assert response.status_code == 401


@pytest.mark.parametrize("header", ["Bearer not-a-jwt", "Bearer ", "Basic abc123"])
async def test_me_rejects_malformed_credentials(client: AsyncClient, header: str) -> None:
    response = await client.get(ME, headers={"Authorization": header})

    assert response.status_code == 401


async def test_refresh_token_is_not_accepted_as_access_token(client: AsyncClient) -> None:
    tokens = await _register_and_login(client)

    response = await client.get(ME, headers={"Authorization": f"Bearer {tokens['refresh_token']}"})

    assert response.status_code == 401


async def test_token_signed_with_wrong_secret_is_rejected(client: AsyncClient) -> None:
    forged = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000000",
            "type": "access",
            "jti": "forged",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        "wrong-secret-" + "x" * 40,
        algorithm="HS256",
    )

    response = await client.get(ME, headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


async def test_expired_token_is_rejected(client: AsyncClient) -> None:
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000000",
            "type": "access",
            "jti": "expired",
            "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(ME, headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401


async def test_refresh_issues_a_new_pair(client: AsyncClient) -> None:
    tokens = await _register_and_login(client)

    response = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["refresh_token"] != tokens["refresh_token"]


async def test_refresh_token_cannot_be_reused(client: AsyncClient) -> None:
    tokens = await _register_and_login(client)

    first = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    second = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})

    assert first.status_code == 200
    assert second.status_code == 401


async def test_logout_revokes_the_refresh_token(client: AsyncClient) -> None:
    tokens = await _register_and_login(client)

    logout = await client.post(LOGOUT, json={"refresh_token": tokens["refresh_token"]})
    reuse = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})

    assert logout.status_code == 204
    assert reuse.status_code == 401
