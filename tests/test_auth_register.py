"""Tests for user registration."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.models.user import User

URL = "/api/v1/auth/register"
PASSWORD = "correct-horse-battery"


async def test_register_returns_created_user(client: AsyncClient) -> None:
    response = await client.post(URL, json={"email": "new@example.com", "password": PASSWORD})

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["is_active"] is True
    assert "id" in body and "created_at" in body


async def test_register_never_leaks_credentials(client: AsyncClient) -> None:
    response = await client.post(URL, json={"email": "leak@example.com", "password": PASSWORD})

    body = response.json()
    assert "password" not in body
    assert "password_hash" not in body
    assert PASSWORD not in response.text


async def test_register_stores_an_argon2_hash(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(URL, json={"email": "hash@example.com", "password": PASSWORD})

    result = await db_session.execute(select(User).where(User.email == "hash@example.com"))
    user = result.scalar_one()

    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$argon2id$")


async def test_register_normalises_email_case(client: AsyncClient) -> None:
    response = await client.post(URL, json={"email": "Mixed@Example.COM", "password": PASSWORD})

    assert response.status_code == 201
    assert response.json()["email"] == "mixed@example.com"


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    await client.post(URL, json={"email": "taken@example.com", "password": PASSWORD})

    response = await client.post(URL, json={"email": "taken@example.com", "password": PASSWORD})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_registered"


async def test_duplicate_detection_is_case_insensitive(client: AsyncClient) -> None:
    await client.post(URL, json={"email": "user@example.com", "password": PASSWORD})

    response = await client.post(URL, json={"email": "USER@EXAMPLE.COM", "password": PASSWORD})

    assert response.status_code == 409


@pytest.mark.parametrize("password", ["short", "", "x" * 129])
async def test_register_rejects_bad_passwords(client: AsyncClient, password: str) -> None:
    response = await client.post(URL, json={"email": "bad@example.com", "password": password})

    assert response.status_code == 422


@pytest.mark.parametrize("email", ["not-an-email", "@example.com", "a@", ""])
async def test_register_rejects_bad_emails(client: AsyncClient, email: str) -> None:
    response = await client.post(URL, json={"email": email, "password": PASSWORD})

    assert response.status_code == 422
