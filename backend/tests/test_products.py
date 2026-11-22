from decimal import Decimal
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


async def create_product(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str = "Laptop",
    description: str | None = "A fast laptop",
    price: str = "999.99",
    stock_quantity: int = 5,
) -> dict[str, Any]:
    response = await client.post(
        "/api/products",
        headers=headers,
        json={
            "name": name,
            "description": description,
            "price": price,
            "stock_quantity": stock_quantity,
        },
    )
    assert response.status_code == 201
    return response.json()


def as_decimal(value: object) -> Decimal:
    """Accept either string or numeric JSON representations of Decimal."""
    return Decimal(str(value))


async def test_products_require_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/products")

    assert response.status_code == 401


async def test_create_product_sets_owner_to_current_user(client: AsyncClient) -> None:
    user_id, headers = await make_user(client, "alice", "alice@example.com")

    product = await create_product(client, headers)

    assert product["name"] == "Laptop"
    assert product["description"] == "A fast laptop"
    assert as_decimal(product["price"]) == Decimal("999.99")
    assert product["stock_quantity"] == 5
    assert product["owner_id"] == user_id


async def test_list_products_only_returns_current_users_products(client: AsyncClient) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    await create_product(client, headers_a, name="Alice's product")

    _, headers_b = await make_user(client, "bob", "bob@example.com")
    await create_product(client, headers_b, name="Bob's product")

    response = await client.get("/api/products", headers=headers_a)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Alice's product"]


async def test_get_owned_product(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    product = await create_product(client, headers)

    response = await client.get(f"/api/products/{product['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == product["id"]


@pytest.mark.parametrize("method", ["get", "put", "delete"])
async def test_user_cannot_access_another_users_product(
    client: AsyncClient,
    method: str,
) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    _, headers_b = await make_user(client, "bob", "bob@example.com")
    product_b = await create_product(client, headers_b, name="Bob's product")
    product_id = product_b["id"]

    if method == "get":
        response = await client.get(f"/api/products/{product_id}", headers=headers_a)
    elif method == "put":
        response = await client.put(
            f"/api/products/{product_id}",
            headers=headers_a,
            json={"name": "Hacked"},
        )
    else:
        response = await client.delete(f"/api/products/{product_id}", headers=headers_a)

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"

    still_owned = await client.get(f"/api/products/{product_id}", headers=headers_b)
    assert still_owned.status_code == 200
    assert still_owned.json()["name"] == "Bob's product"


async def test_update_product_partially_and_clear_description(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    product = await create_product(client, headers)

    response = await client.put(
        f"/api/products/{product['id']}",
        headers=headers,
        json={"name": "Gaming Laptop", "price": "1299.50", "stock_quantity": 0},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Gaming Laptop"
    assert as_decimal(updated["price"]) == Decimal("1299.50")
    assert updated["stock_quantity"] == 0
    assert updated["description"] == "A fast laptop"

    cleared = await client.put(
        f"/api/products/{product['id']}",
        headers=headers,
        json={"description": None},
    )

    assert cleared.status_code == 200
    assert cleared.json()["description"] is None


async def test_delete_product(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    product = await create_product(client, headers)

    deleted = await client.delete(f"/api/products/{product['id']}", headers=headers)

    assert deleted.status_code == 204
    assert deleted.content == b""

    fetched = await client.get(f"/api/products/{product['id']}", headers=headers)
    assert fetched.status_code == 404

    listed = await client.get("/api/products", headers=headers)
    assert listed.json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "price": "1.00"},
        {"name": "Laptop", "price": "-1.00"},
        {"name": "Laptop", "price": "1.00", "stock_quantity": -1},
        {"name": "Laptop", "price": "1.234"},
    ],
)
async def test_create_product_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict[str, object],
) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")

    response = await client.post("/api/products", headers=headers, json=payload)

    assert response.status_code == 422


async def test_update_requires_at_least_one_field(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    product = await create_product(client, headers)

    response = await client.put(
        f"/api/products/{product['id']}",
        headers=headers,
        json={},
    )

    assert response.status_code == 422
