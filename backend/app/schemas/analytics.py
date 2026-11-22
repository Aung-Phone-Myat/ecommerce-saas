from decimal import Decimal

from pydantic import BaseModel, Field


class AnalyticsSummary(BaseModel):
    """Owner-scoped dashboard metrics."""

    total_products: int = Field(ge=0)
    total_customers: int = Field(ge=0)
    total_orders: int = Field(ge=0)
    total_revenue: Decimal = Field(ge=0)
    pending_orders: int = Field(ge=0)
