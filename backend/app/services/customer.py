from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerNotFoundError(Exception):
    """Raised when a customer does not exist for the current owner."""


async def create_customer(db: AsyncSession, owner_id: int, payload: CustomerCreate) -> Customer:
    """Create a customer owned by the given user."""
    customer = Customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        owner_id=owner_id,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def list_customers(db: AsyncSession, owner_id: int) -> list[Customer]:
    """Return all customers owned by the given user, newest first."""
    result = await db.execute(
        select(Customer)
        .where(Customer.owner_id == owner_id)
        .order_by(Customer.created_at.desc(), Customer.id.desc())
    )
    return list(result.scalars().all())


async def get_owned_customer(db: AsyncSession, owner_id: int, customer_id: int) -> Customer:
    """Return a customer only if it belongs to the given user."""
    customer = await db.scalar(
        select(Customer).where(Customer.id == customer_id, Customer.owner_id == owner_id)
    )
    if customer is None:
        raise CustomerNotFoundError
    return customer


async def update_customer(
    db: AsyncSession,
    owner_id: int,
    customer_id: int,
    payload: CustomerUpdate,
) -> Customer:
    """Apply a partial update to a customer owned by the given user."""
    customer = await get_owned_customer(db, owner_id, customer_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)
    return customer


async def delete_customer(db: AsyncSession, owner_id: int, customer_id: int) -> None:
    """Delete a customer owned by the given user."""
    customer = await get_owned_customer(db, owner_id, customer_id)
    await db.delete(customer)
    await db.commit()
