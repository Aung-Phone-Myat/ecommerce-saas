from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

PASSWORD = "correct-horse-battery-staple"


async def make_user(client: AsyncClient, username: str, email: str) -> dict[str, str]:
    """Register and log in a user, returning a bearer-token header."""
    registered = await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": PASSWORD},
    )
    assert registered.status_code == 201

    login = await client.post(
        "/api/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_customer(client: AsyncClient, headers: dict[str, str]) -> dict[str, Any]:
    response = await client.post(
        "/api/customers",
        headers=headers,
        json={"name": "Acme Corp", "email": "billing@acme.example.com"},
    )
    assert response.status_code == 201
    return response.json()


async def create_product(client: AsyncClient, headers: dict[str, str]) -> dict[str, Any]:
    response = await client.post(
        "/api/products",
        headers=headers,
        json={"name": "Laptop", "price": "10.00", "stock_quantity": 5},
    )
    assert response.status_code == 201
    return response.json()


async def submit_order(
    client: AsyncClient,
    headers: dict[str, str],
    customer_id: int,
    product_id: int,
) -> dict[str, Any]:
    response = await client.post(
        "/api/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_delete_customer_used_in_order_keeps_order_readable(client: AsyncClient) -> None:
    headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers)
    order = await submit_order(client, headers, customer["id"], product["id"])

    deleted = await client.delete(f"/api/customers/{customer['id']}", headers=headers)
    assert deleted.status_code == 204

    fetched = await client.get(f"/api/orders/{order['id']}", headers=headers)
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["customer_id"] is None
    assert body["customer"]["id"] is None
    assert body["customer"]["name"] == "Acme Corp"
    assert body["items"][0]["product"]["name"] == "Laptop"


async def test_delete_product_used_in_order_keeps_order_readable(client: AsyncClient) -> None:
    headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers)
    order = await submit_order(client, headers, customer["id"], product["id"])

    deleted = await client.delete(f"/api/products/{product['id']}", headers=headers)
    assert deleted.status_code == 204

    fetched = await client.get(f"/api/orders/{order['id']}", headers=headers)
    assert fetched.status_code == 200
    item = fetched.json()["items"][0]
    assert item["product_id"] is None
    assert item["product"]["id"] is None
    assert item["product"]["name"] == "Laptop"
    assert item["product"]["price"] == "10.00"


async def test_delete_both_parents_keeps_list_status_and_analytics_working(
    client: AsyncClient,
) -> None:
    headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers)
    order = await submit_order(client, headers, customer["id"], product["id"])

    assert (await client.delete(f"/api/customers/{customer['id']}", headers=headers)).status_code == 204
    assert (await client.delete(f"/api/products/{product['id']}", headers=headers)).status_code == 204

    listed = await client.get("/api/orders", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    changed = await client.put(
        f"/api/orders/{order['id']}/status",
        headers=headers,
        json={"status": "completed"},
    )
    assert changed.status_code == 200

    summary = await client.get("/api/analytics/summary", headers=headers)
    assert summary.status_code == 200
    analytics = summary.json()
    assert analytics["total_orders"] == 1
    assert Decimal(str(analytics["total_revenue"])) == Decimal("10.00")
