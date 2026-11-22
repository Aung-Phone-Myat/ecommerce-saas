from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.schemas.analytics import AnalyticsSummary


async def get_analytics_summary(db: AsyncSession, owner_id: int) -> AnalyticsSummary:
    """Aggregate dashboard metrics for a single owner."""
    total_products = await db.scalar(
        select(func.count(Product.id)).where(Product.owner_id == owner_id)
    )
    total_customers = await db.scalar(
        select(func.count(Customer.id)).where(Customer.owner_id == owner_id)
    )
    order_stats = await db.execute(
        select(
            func.count(Order.id),
            func.count(Order.id).filter(Order.status == "pending"),
            func.sum(Order.total_amount).filter(Order.status == "completed"),
        ).where(Order.owner_id == owner_id)
    )
    total_orders, pending_orders, completed_revenue = order_stats.one()

    return AnalyticsSummary(
        total_products=total_products or 0,
        total_customers=total_customers or 0,
        total_orders=total_orders or 0,
        total_revenue=(
            Decimal(str(completed_revenue)) if completed_revenue is not None else Decimal("0.00")
        ),
        pending_orders=pending_orders or 0,
    )
