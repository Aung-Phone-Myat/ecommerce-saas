from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatus

ORDER_LOAD_OPTIONS = (
    selectinload(Order.customer),
    selectinload(Order.items).selectinload(OrderItem.product),
)


class OrderCustomerNotFoundError(Exception):
    """Raised when the order's customer is missing or owned by another user."""


class OrderProductNotFoundError(Exception):
    """Raised when an ordered product is missing or owned by another user."""


class InsufficientStockError(Exception):
    """Raised when a requested product quantity exceeds available stock."""

    def __init__(self, product_id: int) -> None:
        self.product_id = product_id
        super().__init__(f"Insufficient stock for product {product_id}")


class OrderNotFoundError(Exception):
    """Raised when an order does not exist for the current owner."""


def _owned_order_query(owner_id: int, order_id: int):
    """Build an owner-scoped order query with nested data eagerly loaded."""
    return (
        select(Order)
        .options(*ORDER_LOAD_OPTIONS)
        .where(Order.id == order_id, Order.owner_id == owner_id)
    )


async def create_order(db: AsyncSession, owner_id: int, payload: OrderCreate) -> Order:
    """Create an owner-scoped order, validate stock, and deduct it atomically."""
    try:
        customer_id = await db.scalar(
            select(Customer.id).where(
                Customer.id == payload.customer_id,
                Customer.owner_id == owner_id,
            )
        )
        if customer_id is None:
            raise OrderCustomerNotFoundError

        # Combine duplicate product lines so each product is deducted once.
        quantities: dict[int, int] = {}
        for item in payload.items:
            quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

        product_ids = list(quantities)
        result = await db.execute(
            select(Product)
            .where(Product.id.in_(product_ids), Product.owner_id == owner_id)
            .order_by(Product.id)
            .with_for_update()
        )
        products = list(result.scalars().all())
        if len(products) != len(product_ids):
            raise OrderProductNotFoundError

        products_by_id = {product.id: product for product in products}
        order_items: list[OrderItem] = []
        total_amount = Decimal(0)

        # Validate every line before mutating any stock.
        for product_id, quantity in quantities.items():
            product = products_by_id[product_id]
            if product.stock_quantity < quantity:
                raise InsufficientStockError(product_id)
            total_amount += product.price * quantity
            order_items.append(
                OrderItem(
                    product_id=product_id,
                    quantity=quantity,
                    price_at_time_of_purchase=product.price,
                )
            )

        for product_id, quantity in quantities.items():
            products_by_id[product_id].stock_quantity -= quantity

        order = Order(
            owner_id=owner_id,
            customer_id=customer_id,
            status="pending",
            total_amount=total_amount,
            items=order_items,
        )
        db.add(order)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return await get_owned_order(db, owner_id, order.id)


async def list_orders(db: AsyncSession, owner_id: int) -> list[Order]:
    """Return all orders owned by the given user, newest first."""
    result = await db.execute(
        select(Order)
        .options(*ORDER_LOAD_OPTIONS)
        .where(Order.owner_id == owner_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return list(result.scalars().all())


async def get_owned_order(db: AsyncSession, owner_id: int, order_id: int) -> Order:
    """Return an order with nested details only if it belongs to the given user."""
    order = await db.scalar(_owned_order_query(owner_id, order_id))
    if order is None:
        raise OrderNotFoundError
    return order


async def update_order_status(
    db: AsyncSession,
    owner_id: int,
    order_id: int,
    status: OrderStatus,
) -> Order:
    """Update the status of an order owned by the given user."""
    order = await get_owned_order(db, owner_id, order_id)
    order.status = status

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return await get_owned_order(db, owner_id, order_id)
