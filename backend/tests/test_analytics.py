from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient, Response

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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def create_customer(client: AsyncClient, headers: dict[str, str], name: str) -> dict[str, Any]:
    response = await client.post("/api/customers", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()


async def create_product(
    client: AsyncClient,
    headers: dict[str, str],
    name: str,
    price: str = "5.00",
    stock_quantity: int = 10,
) -> dict[str, Any]:
    response = await client.post(
        "/api/products",
        headers=headers,
        json={
            "name": name,
            "description": None,
            "price": price,
            "stock_quantity": stock_quantity,
        },
    )
    assert response.status_code == 201
    return response.json()


async def submit_order(
    client: AsyncClient,
    headers: dict[str, str],
    customer_id: int,
    product_id: int,
) -> Response:
    response = await client.post(
        "/api/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 1}],
        },
    )
    assert response.status_code == 201
    return response


async def set_status(
    client: AsyncClient, headers: dict[str, str], order_id: int, status_value: str
) -> None:
    response = await client.put(
        f"/api/orders/{order_id}/status",
        headers=headers,
        json={"status": status_value},
    )
    assert response.status_code == 200


async def test_analytics_summary_requires_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/analytics/summary")

    assert response.status_code == 401


async def test_analytics_summary_is_zero_for_new_user(client: AsyncClient) -> None:
    headers = await make_user(client, "alice", "alice@example.com")

    response = await client.get("/api/analytics/summary", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "total_products": 0,
        "total_customers": 0,
        "total_orders": 0,
        "total_revenue": "0.00",
        "pending_orders": 0,
    }


async def test_analytics_summary_counts_and_completed_revenue(client: AsyncClient) -> None:
    headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers, "Acme Corp")
    product = await create_product(client, headers, "Widget", price="5.00", stock_quantity=10)

    orders = [
        await submit_order(client, headers, customer["id"], product["id"]) for _ in range(4)
    ]
    await set_status(client, headers, orders[0].json()["id"], "completed")
    await set_status(client, headers, orders[1].json()["id"], "completed")
    await set_status(client, headers, orders[2].json()["id"], "paid")
    await set_status(client, headers, orders[3].json()["id"], "cancelled")

    response = await client.get("/api/analytics/summary", headers=headers)

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_products"] == 1
    assert summary["total_customers"] == 1
    assert summary["total_orders"] == 4
    assert Decimal(str(summary["total_revenue"])) == Decimal("10.00")
    assert summary["pending_orders"] == 0


async def test_analytics_summary_counts_pending_orders(client: AsyncClient) -> None:
    headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers, "Acme Corp")
    product = await create_product(client, headers, "Widget", price="2.50", stock_quantity=10)

    orders = [
        await submit_order(client, headers, customer["id"], product["id"]) for _ in range(3)
    ]
    await set_status(client, headers, orders[0].json()["id"], "shipped")
    await set_status(client, headers, orders[1].json()["id"], "completed")

    response = await client.get("/api/analytics/summary", headers=headers)

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_orders"] == 3
    assert summary["pending_orders"] == 1
    assert Decimal(str(summary["total_revenue"])) == Decimal("2.50")


async def test_analytics_summary_is_owner_scoped(client: AsyncClient) -> None:
    alice = await make_user(client, "alice", "alice@example.com")
    bob = await make_user(client, "bob", "bob@example.com")

    alice_customer = await create_customer(client, alice, "Alice's customer")
    alice_product = await create_product(client, alice, "Alice's product", price="4.00")
    bob_customer = await create_customer(client, bob, "Bob's customer")
    bob_product = await create_product(client, bob, "Bob's product", price="100.00")

    alice_order = await submit_order(client, alice, alice_customer["id"], alice_product["id"])
    bob_order = await submit_order(client, bob, bob_customer["id"], bob_product["id"])
    await set_status(client, alice, alice_order.json()["id"], "completed")
    await set_status(client, bob, bob_order.json()["id"], "completed")
    await create_product(client, bob, "Bob's other product", stock_quantity=1)

    response = await client.get("/api/analytics/summary", headers=alice)

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_products"] == 1
    assert summary["total_customers"] == 1
    assert summary["total_orders"] == 1
    assert Decimal(str(summary["total_revenue"])) == Decimal("4.00")
    assert summary["pending_orders"] == 0
