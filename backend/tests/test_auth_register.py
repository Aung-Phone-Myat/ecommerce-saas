import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User

pytestmark = pytest.mark.anyio


async def test_register_user_success(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "correct-horse-battery-staple",
    }

    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == payload["username"]
    assert body["email"] == payload["email"]
    assert body["id"] > 0
    assert "created_at" in body
    assert "updated_at" in body
    assert "password" not in body
    assert "hashed_password" not in body

    user = await db_session.scalar(select(User).where(User.email == payload["email"]))
    assert user is not None
    assert user.hashed_password != payload["password"]
    assert verify_password(payload["password"], user.hashed_password)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "alice",
            "email": "not-an-email",
            "password": "correct-horse-battery-staple",
        },
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "short",
        },
        {
            "username": "a",
            "email": "alice@example.com",
            "password": "correct-horse-battery-staple",
        },
        {
            "username": "alice space",
            "email": "alice@example.com",
            "password": "correct-horse-battery-staple",
        },
    ],
)
async def test_register_rejects_invalid_input(
    client: AsyncClient, payload: dict[str, str]
) -> None:
    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == 422


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "correct-horse-battery-staple",
    }

    first_response = await client.post("/api/auth/register", json=payload)
    assert first_response.status_code == 201

    duplicate_payload = {**payload, "email": "ALICE@EXAMPLE.COM"}
    duplicate_response = await client.post("/api/auth/register", json=duplicate_payload)

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "Email is already registered"}
