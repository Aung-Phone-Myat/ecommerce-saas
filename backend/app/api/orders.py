from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate
from app.services import order as order_service
from app.services.order import (
    InsufficientStockError,
    OrderCustomerNotFoundError,
    OrderNotFoundError,
    OrderProductNotFoundError,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def not_found_error(detail: str) -> HTTPException:
    """Return a consistent 404 for missing or foreign-owned resources."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    """Place an order for the current user's customer and products."""
    try:
        order = await order_service.create_order(db, current_user.id, payload)
    except OrderCustomerNotFoundError:
        raise not_found_error("Customer not found") from None
    except OrderProductNotFoundError:
        raise not_found_error("Product not found") from None
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient stock for product {exc.product_id}",
        ) from None
    return OrderRead.model_validate(order)


@router.get("", response_model=list[OrderRead])
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[OrderRead]:
    """List all orders belonging to the authenticated user."""
    orders = await order_service.list_orders(db, current_user.id)
    return [OrderRead.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    """Return one order if it belongs to the authenticated user."""
    try:
        order = await order_service.get_owned_order(db, current_user.id, order_id)
    except OrderNotFoundError:
        raise not_found_error("Order not found") from None
    return OrderRead.model_validate(order)


@router.put("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> OrderRead:
    """Update the status of an order owned by the authenticated user."""
    try:
        order = await order_service.update_order_status(
            db, current_user.id, order_id, payload.status
        )
    except OrderNotFoundError:
        raise not_found_error("Order not found") from None
    return OrderRead.model_validate(order)
