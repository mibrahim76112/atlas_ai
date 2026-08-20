"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials submitted at login."""

    email: EmailStr
    password: str = Field(..., max_length=128)


class RefreshRequest(BaseModel):
    """A refresh token being exchanged or revoked."""

    refresh_token: str


class TokenPair(BaseModel):
    """Issued credentials."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type, not a secret
    expires_in: int
