from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal["pending", "paid", "shipped", "completed", "cancelled"]


class OrderItemCreate(BaseModel):
    """A requested product line when creating an order."""

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    """Request body for creating an order."""

    customer_id: int = Field(gt=0)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    """Request body for changing an order's status."""

    status: OrderStatus


class CustomerSummary(BaseModel):
    """Customer details embedded in an order response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    phone: str | None
    address: str | None


class ProductSummary(BaseModel):
    """Product details embedded in an order item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int


class OrderItemRead(BaseModel):
    """An order line with the price captured at purchase time."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product: ProductSummary
    quantity: int
    price_at_time_of_purchase: Decimal
    line_total: Decimal


class OrderRead(BaseModel):
    """Full order representation, including customer and product details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer: CustomerSummary
    owner_id: int
    status: OrderStatus
    total_amount: Decimal
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime
