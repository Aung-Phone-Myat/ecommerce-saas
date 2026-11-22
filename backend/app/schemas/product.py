from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProductPrice = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class ProductCreate(BaseModel):
    """Request body for creating a product."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    price: ProductPrice
    stock_quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    """Partial product update. Only fields present in the body are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    price: ProductPrice | None = None
    stock_quantity: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ProductUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        return self


class ProductRead(BaseModel):
    """Public product representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
