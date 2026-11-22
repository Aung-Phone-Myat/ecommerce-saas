from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CustomerCreate(BaseModel):
    """Request body for creating a customer."""

    name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=2000)


class CustomerUpdate(BaseModel):
    """Partial customer update. Only fields present in the body are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_update(self) -> "CustomerUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Name cannot be null")
        return self


class CustomerRead(BaseModel):
    """Public customer representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    phone: str | None
    address: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime
