from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.customer import Customer
from app.models.product import Product

ORDER_STATUSES = ("pending", "paid", "shipped", "completed", "cancelled")
STATUS_CHECK = "status IN ('pending', 'paid', 'shipped', 'completed', 'cancelled')"


class Order(Base):
    """An order placed by a customer in a user's store."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(STATUS_CHECK, name="ck_orders_status"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_non_negative"),
        Index("ix_orders_owner_id", "owner_id"),
        Index("ix_orders_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer: Mapped[Customer] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    """A product line within an order, with the price captured at purchase time."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint(
            "price_at_time_of_purchase >= 0",
            name="ck_order_items_price_non_negative",
        ),
        UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_at_time_of_purchase: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    @property
    def line_total(self) -> Decimal:
        """Return this line's captured-price total."""
        return self.price_at_time_of_purchase * self.quantity
