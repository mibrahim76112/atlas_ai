"""JWT creation and validation."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt

from atlas.core.config import Settings
from atlas.core.exceptions import AuthenticationError

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class IssuedToken:
    """A freshly minted token plus the metadata needed to revoke it."""

    token: str
    jti: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenClaims:
    """Validated claims from an incoming token."""

    subject: str
    token_type: TokenType
    jti: str
    expires_at: datetime


def _create(
    subject: str,
    token_type: TokenType,
    lifetime: timedelta,
    settings: Settings,
) -> IssuedToken:
    now = datetime.now(UTC)
    expires_at = now + lifetime
    jti = str(uuid.uuid4())

    token = jwt.encode(
        {
            "sub": subject,
            "type": token_type,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return IssuedToken(token=token, jti=jti, expires_at=expires_at)


def create_access_token(subject: str, settings: Settings) -> IssuedToken:
    return _create(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        settings,
    )


def create_refresh_token(subject: str, settings: Settings) -> IssuedToken:
    return _create(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
        settings,
    )


def decode_token(token: str, expected_type: TokenType, settings: Settings) -> TokenClaims:
    """Validate a token's signature, expiry, and type."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat", "jti", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc

    if payload["type"] != expected_type:
        raise AuthenticationError("Invalid or expired token.")

    return TokenClaims(
        subject=str(payload["sub"]),
        token_type=expected_type,
        jti=str(payload["jti"]),
        expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=UTC),
    )
