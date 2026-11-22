from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

PASSWORD = "correct-horse-battery-staple"


async def make_user(client: AsyncClient, username: str, email: str) -> tuple[int, dict[str, str]]:
    """Register a user and return its id plus a bearer-token header."""
    registered = await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": PASSWORD},
    )
    assert registered.status_code == 201
    user_id: int = registered.json()["id"]

    login = await client.post(
        "/api/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


async def create_customer(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str = "Acme Corp",
    email: str | None = "billing@acme.example.com",
    phone: str | None = "+1-555-0100",
    address: str | None = "1 Main Street, Springfield",
) -> dict[str, Any]:
    response = await client.post(
        "/api/customers",
        headers=headers,
        json={"name": name, "email": email, "phone": phone, "address": address},
    )
    assert response.status_code == 201
    return response.json()


async def test_customers_require_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/customers")

    assert response.status_code == 401


async def test_create_customer_sets_owner_to_current_user(client: AsyncClient) -> None:
    user_id, headers = await make_user(client, "alice", "alice@example.com")

    customer = await create_customer(client, headers)

    assert customer["name"] == "Acme Corp"
    assert customer["email"] == "billing@acme.example.com"
    assert customer["phone"] == "+1-555-0100"
    assert customer["address"] == "1 Main Street, Springfield"
    assert customer["owner_id"] == user_id


async def test_create_customer_allows_optional_fields_to_be_omitted(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")

    response = await client.post("/api/customers", headers=headers, json={"name": "Walk-in"})

    assert response.status_code == 201
    customer = response.json()
    assert customer["name"] == "Walk-in"
    assert customer["email"] is None
    assert customer["phone"] is None
    assert customer["address"] is None


async def test_list_customers_only_returns_current_users_customers(client: AsyncClient) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    await create_customer(client, headers_a, name="Alice's customer")

    _, headers_b = await make_user(client, "bob", "bob@example.com")
    await create_customer(client, headers_b, name="Bob's customer")

    response = await client.get("/api/customers", headers=headers_a)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Alice's customer"]


async def test_get_owned_customer(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)

    response = await client.get(f"/api/customers/{customer['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == customer["id"]


@pytest.mark.parametrize("method", ["get", "put", "delete"])
async def test_user_cannot_access_another_users_customer(
    client: AsyncClient,
    method: str,
) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    _, headers_b = await make_user(client, "bob", "bob@example.com")
    customer_b = await create_customer(client, headers_b, name="Bob's customer")
    customer_id = customer_b["id"]

    if method == "get":
        response = await client.get(f"/api/customers/{customer_id}", headers=headers_a)
    elif method == "put":
        response = await client.put(
            f"/api/customers/{customer_id}",
            headers=headers_a,
            json={"name": "Hacked"},
        )
    else:
        response = await client.delete(f"/api/customers/{customer_id}", headers=headers_a)

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"

    still_owned = await client.get(f"/api/customers/{customer_id}", headers=headers_b)
    assert still_owned.status_code == 200
    assert still_owned.json()["name"] == "Bob's customer"


async def test_update_customer_partially_and_clear_optional_fields(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)

    response = await client.put(
        f"/api/customers/{customer['id']}",
        headers=headers,
        json={"name": "Acme Industries", "phone": "+1-555-0200"},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Acme Industries"
    assert updated["phone"] == "+1-555-0200"
    assert updated["email"] == "billing@acme.example.com"
    assert updated["address"] == "1 Main Street, Springfield"

    cleared = await client.put(
        f"/api/customers/{customer['id']}",
        headers=headers,
        json={"email": None, "address": None},
    )

    assert cleared.status_code == 200
    assert cleared.json()["email"] is None
    assert cleared.json()["address"] is None


async def test_delete_customer(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)

    deleted = await client.delete(f"/api/customers/{customer['id']}", headers=headers)

    assert deleted.status_code == 204
    assert deleted.content == b""

    fetched = await client.get(f"/api/customers/{customer['id']}", headers=headers)
    assert fetched.status_code == 404

    listed = await client.get("/api/customers", headers=headers)
    assert listed.json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "x" * 256},
        {"name": "Acme", "email": "x" * 256},
        {"name": "Acme", "phone": "x" * 51},
    ],
)
async def test_create_customer_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict[str, object],
) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")

    response = await client.post("/api/customers", headers=headers, json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": None},
    ],
)
async def test_update_rejects_empty_or_invalid_payload(
    client: AsyncClient,
    payload: dict[str, object],
) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)

    response = await client.put(
        f"/api/customers/{customer['id']}",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422
