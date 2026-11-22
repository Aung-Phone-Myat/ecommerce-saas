from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import customer as customer_service
from app.services.customer import CustomerNotFoundError

router = APIRouter(prefix="/customers", tags=["customers"])


def customer_not_found_error() -> HTTPException:
    """Return the same 404 whether the customer is missing or owned by someone else."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Customer not found",
    )


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CustomerRead:
    """Create a customer owned by the authenticated user."""
    customer = await customer_service.create_customer(db, current_user.id, payload)
    return CustomerRead.model_validate(customer)


@router.get("", response_model=list[CustomerRead])
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CustomerRead]:
    """List all customers belonging to the authenticated user."""
    customers = await customer_service.list_customers(db, current_user.id)
    return [CustomerRead.model_validate(customer) for customer in customers]


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CustomerRead:
    """Return one customer if it belongs to the authenticated user."""
    try:
        customer = await customer_service.get_owned_customer(db, current_user.id, customer_id)
    except CustomerNotFoundError:
        raise customer_not_found_error() from None
    return CustomerRead.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CustomerRead:
    """Update a customer if it belongs to the authenticated user."""
    try:
        customer = await customer_service.update_customer(
            db, current_user.id, customer_id, payload
        )
    except CustomerNotFoundError:
        raise customer_not_found_error() from None
    return CustomerRead.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a customer if it belongs to the authenticated user."""
    try:
        await customer_service.delete_customer(db, current_user.id, customer_id)
    except CustomerNotFoundError:
        raise customer_not_found_error() from None
