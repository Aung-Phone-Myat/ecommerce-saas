from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


class InvalidTokenError(Exception):
    """Raised when an access token is missing, malformed, expired, or wrong type."""


def hash_password(password: str) -> str:
    """Hash a plaintext password with the recommended algorithm (Argon2)."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored hash."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create a short-lived bearer token for the given subject (user id)."""
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str:
    """Validate a token and return its subject, or raise InvalidTokenError."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError from exc

    subject = payload.get("sub")
    if payload.get("type") != "access" or not isinstance(subject, str) or not subject:
        raise InvalidTokenError
    return subject
