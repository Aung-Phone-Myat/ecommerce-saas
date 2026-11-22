from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserRead

pytestmark = pytest.mark.anyio

REGISTER_PAYLOAD = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "correct-horse-battery-staple",
}


async def register_user(client: AsyncClient) -> dict[str, Any]:
    response = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    return response.json()


async def login(client: AsyncClient, payload: dict[str, str]) -> Any:
    return await client.post("/api/auth/login", json=payload)


async def test_login_with_email_returns_token_and_current_user(client: AsyncClient) -> None:
    await register_user(client)

    response = await login(
        client,
        {"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    me = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["email"] == REGISTER_PAYLOAD["email"]
    assert me_body["username"] == REGISTER_PAYLOAD["username"]
    assert "hashed_password" not in me_body
    UserRead.model_validate(me_body)


async def test_login_with_username(client: AsyncClient) -> None:
    await register_user(client)

    response = await login(
        client,
        {"username": REGISTER_PAYLOAD["username"], "password": REGISTER_PAYLOAD["password"]},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


@pytest.mark.parametrize(
    "payload",
    [
        {"email": REGISTER_PAYLOAD["email"], "password": "wrong-password"},
        {"email": "nobody@example.com", "password": REGISTER_PAYLOAD["password"]},
        {"username": REGISTER_PAYLOAD["username"], "password": "wrong-password"},
    ],
)
async def test_login_rejects_bad_credentials(client: AsyncClient, payload: dict[str, str]) -> None:
    await register_user(client)

    response = await login(client, payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email/username or password"


@pytest.mark.parametrize(
    "payload",
    [
        {"password": REGISTER_PAYLOAD["password"]},
        {"email": REGISTER_PAYLOAD["email"]},
        {
            "email": REGISTER_PAYLOAD["email"],
            "username": REGISTER_PAYLOAD["username"],
            "password": REGISTER_PAYLOAD["password"],
        },
    ],
)
async def test_login_rejects_invalid_payload(client: AsyncClient, payload: dict[str, str]) -> None:
    response = await login(client, payload)

    assert response.status_code == 422


async def test_current_user_requires_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/users/me")

    assert response.status_code == 401


async def test_current_user_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


async def test_current_user_rejects_token_for_deleted_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await register_user(client)
    token_response = await login(
        client,
        {"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = token_response.json()["access_token"]

    user = await db_session.scalar(select(User))
    assert user is not None
    await db_session.delete(user)
    await db_session.commit()

    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
