from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient, Response

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


async def create_customer(client: AsyncClient, headers: dict[str, str], name: str = "Acme Corp") -> dict[str, Any]:
    response = await client.post("/api/customers", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()


async def create_product(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str,
    price: str = "10.00",
    stock_quantity: int = 5,
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
    items: list[dict[str, int]],
) -> Response:
    return await client.post(
        "/api/orders",
        headers=headers,
        json={"customer_id": customer_id, "items": items},
    )


def as_decimal(value: object) -> Decimal:
    """Accept either string or numeric JSON representations of Decimal."""
    return Decimal(str(value))


async def stock_of(client: AsyncClient, headers: dict[str, str], product_id: int) -> int:
    response = await client.get(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    return response.json()["stock_quantity"]


async def test_orders_require_bearer_token(client: AsyncClient) -> None:
    response = await client.get("/api/orders")

    assert response.status_code == 401


async def test_create_order_calculates_total_and_deducts_stock(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    laptop = await create_product(client, headers, name="Laptop", price="10.00", stock_quantity=5)
    mouse = await create_product(client, headers, name="Mouse", price="2.50", stock_quantity=3)

    response = await submit_order(
        client,
        headers,
        customer["id"],
        [
            {"product_id": laptop["id"], "quantity": 2},
            {"product_id": mouse["id"], "quantity": 1},
        ],
    )

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "pending"
    assert order["customer_id"] == customer["id"]
    assert order["customer"]["name"] == "Acme Corp"
    assert order["owner_id"] == 1
    assert as_decimal(order["total_amount"]) == Decimal("22.50")
    assert len(order["items"]) == 2

    item_by_product = {item["product_id"]: item for item in order["items"]}
    laptop_item = item_by_product[laptop["id"]]
    assert laptop_item["quantity"] == 2
    assert as_decimal(laptop_item["price_at_time_of_purchase"]) == Decimal("10.00")
    assert as_decimal(laptop_item["line_total"]) == Decimal("20.00")
    assert laptop_item["product"]["name"] == "Laptop"

    assert await stock_of(client, headers, laptop["id"]) == 3
    assert await stock_of(client, headers, mouse["id"]) == 2

    fetched = await client.get(f"/api/orders/{order['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["total_amount"] == order["total_amount"]

    listed = await client.get("/api/orders", headers=headers)
    assert [item["id"] for item in listed.json()] == [order["id"]]


async def test_create_order_aggregates_duplicate_product_lines(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers, name="Notebook", price="3.00", stock_quantity=5)

    response = await submit_order(
        client,
        headers,
        customer["id"],
        [
            {"product_id": product["id"], "quantity": 1},
            {"product_id": product["id"], "quantity": 2},
        ],
    )

    assert response.status_code == 201
    order = response.json()
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 3
    assert as_decimal(order["total_amount"]) == Decimal("9.00")
    assert await stock_of(client, headers, product["id"]) == 2


async def test_create_order_rejects_foreign_customer_without_side_effects(
    client: AsyncClient,
) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    _, headers_b = await make_user(client, "bob", "bob@example.com")
    customer_b = await create_customer(client, headers_b, name="Bob's customer")
    product_a = await create_product(client, headers_a, name="Alice's product", stock_quantity=5)

    response = await submit_order(
        client,
        headers_a,
        customer_b["id"],
        [{"product_id": product_a["id"], "quantity": 1}],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"
    assert await stock_of(client, headers_a, product_a["id"]) == 5
    listed = await client.get("/api/orders", headers=headers_a)
    assert listed.json() == []


async def test_create_order_rejects_foreign_product_without_deducting_own_stock(
    client: AsyncClient,
) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    _, headers_b = await make_user(client, "bob", "bob@example.com")
    customer_a = await create_customer(client, headers_a)
    product_a = await create_product(client, headers_a, name="Alice's product", stock_quantity=5)
    product_b = await create_product(client, headers_b, name="Bob's product", stock_quantity=5)

    response = await submit_order(
        client,
        headers_a,
        customer_a["id"],
        [
            {"product_id": product_a["id"], "quantity": 1},
            {"product_id": product_b["id"], "quantity": 1},
        ],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
    assert await stock_of(client, headers_a, product_a["id"]) == 5
    listed = await client.get("/api/orders", headers=headers_a)
    assert listed.json() == []


async def test_create_order_rejects_insufficient_stock_without_partial_deduction(
    client: AsyncClient,
) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    low_stock = await create_product(client, headers, name="Low", stock_quantity=2)
    plenty_stock = await create_product(client, headers, name="Plenty", stock_quantity=5)

    response = await submit_order(
        client,
        headers,
        customer["id"],
        [
            {"product_id": low_stock["id"], "quantity": 3},
            {"product_id": plenty_stock["id"], "quantity": 1},
        ],
    )

    assert response.status_code == 409
    assert response.json()["detail"] == f"Insufficient stock for product {low_stock['id']}"
    assert await stock_of(client, headers, low_stock["id"]) == 2
    assert await stock_of(client, headers, plenty_stock["id"]) == 5
    listed = await client.get("/api/orders", headers=headers)
    assert listed.json() == []


async def test_order_keeps_price_at_time_of_purchase(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers, name="Desk", price="10.00", stock_quantity=5)

    created = await submit_order(
        client,
        headers,
        customer["id"],
        [{"product_id": product["id"], "quantity": 1}],
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    changed = await client.put(
        f"/api/products/{product['id']}",
        headers=headers,
        json={"price": "15.00"},
    )
    assert changed.status_code == 200

    fetched = await client.get(f"/api/orders/{order_id}", headers=headers)
    assert fetched.status_code == 200
    order = fetched.json()
    assert as_decimal(order["total_amount"]) == Decimal("10.00")
    assert as_decimal(order["items"][0]["price_at_time_of_purchase"]) == Decimal("10.00")
    assert as_decimal(order["items"][0]["product"]["price"]) == Decimal("15.00")


async def test_update_order_status(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers, name="Chair", stock_quantity=2)
    created = await submit_order(
        client,
        headers,
        customer["id"],
        [{"product_id": product["id"], "quantity": 1}],
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    response = await client.put(
        f"/api/orders/{order_id}/status",
        headers=headers,
        json={"status": "completed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    fetched = await client.get(f"/api/orders/{order_id}", headers=headers)
    assert fetched.json()["status"] == "completed"


async def test_user_cannot_access_another_users_order(client: AsyncClient) -> None:
    _, headers_a = await make_user(client, "alice", "alice@example.com")
    _, headers_b = await make_user(client, "bob", "bob@example.com")
    customer_a = await create_customer(client, headers_a)
    product_a = await create_product(client, headers_a, name="Alice's product", stock_quantity=5)
    created = await submit_order(
        client,
        headers_a,
        customer_a["id"],
        [{"product_id": product_a["id"], "quantity": 1}],
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    fetched = await client.get(f"/api/orders/{order_id}", headers=headers_b)
    assert fetched.status_code == 404
    assert fetched.json()["detail"] == "Order not found"

    changed = await client.put(
        f"/api/orders/{order_id}/status",
        headers=headers_b,
        json={"status": "completed"},
    )
    assert changed.status_code == 404
    assert changed.json()["detail"] == "Order not found"

    listed = await client.get("/api/orders", headers=headers_b)
    assert listed.json() == []

    owner_view = await client.get(f"/api/orders/{order_id}", headers=headers_a)
    assert owner_view.json()["status"] == "pending"


async def test_status_update_rejects_invalid_status(client: AsyncClient) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)
    product = await create_product(client, headers, name="Lamp", stock_quantity=1)
    created = await submit_order(
        client,
        headers,
        customer["id"],
        [{"product_id": product["id"], "quantity": 1}],
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    response = await client.put(
        f"/api/orders/{order_id}/status",
        headers=headers,
        json={"status": "unknown"},
    )

    assert response.status_code == 422
    fetched = await client.get(f"/api/orders/{order_id}", headers=headers)
    assert fetched.json()["status"] == "pending"


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"product_id": 1, "quantity": 0}],
        [{"product_id": 0, "quantity": 1}],
    ],
)
async def test_create_order_rejects_invalid_items(
    client: AsyncClient,
    items: list[dict[str, int]],
) -> None:
    _, headers = await make_user(client, "alice", "alice@example.com")
    customer = await create_customer(client, headers)

    response = await submit_order(client, headers, customer["id"], items)

    assert response.status_code == 422
