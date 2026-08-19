"""User request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr = Field(
        ...,
        description="Email address, used as the login identifier.",
    )
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Plaintext password. Stored only as an argon2id hash.",
    )


class UserRead(BaseModel):
    """Public view of a user. Never contains the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
