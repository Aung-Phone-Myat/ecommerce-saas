from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserRegister(BaseModel):
    """Request body for user registration."""

    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Store and compare emails case-insensitively."""
        return value.lower()


class UserLogin(BaseModel):
    """Login credentials. Provide exactly one of email or username."""

    email: EmailStr | None = None
    username: str | None = None
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.lower() if value else value

    @model_validator(mode="after")
    def require_identifier(self) -> "UserLogin":
        if (self.email is None) == (self.username is None):
            raise ValueError("Provide exactly one of email or username")
        return self


class TokenRead(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserRead(BaseModel):
    """Public user representation. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
