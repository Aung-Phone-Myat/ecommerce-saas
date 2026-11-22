from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product as product_service
from app.services.product import ProductNotFoundError

router = APIRouter(prefix="/products", tags=["products"])


def product_not_found_error() -> HTTPException:
    """Return the same 404 whether the product is missing or owned by someone else."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Product not found",
    )


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductRead:
    """Create a product owned by the authenticated user."""
    product = await product_service.create_product(db, current_user.id, payload)
    return ProductRead.model_validate(product)


@router.get("", response_model=list[ProductRead])
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ProductRead]:
    """List all products belonging to the authenticated user."""
    products = await product_service.list_products(db, current_user.id)
    return [ProductRead.model_validate(product) for product in products]


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductRead:
    """Return one product if it belongs to the authenticated user."""
    try:
        product = await product_service.get_owned_product(db, current_user.id, product_id)
    except ProductNotFoundError:
        raise product_not_found_error() from None
    return ProductRead.model_validate(product)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductRead:
    """Update a product if it belongs to the authenticated user."""
    try:
        product = await product_service.update_product(db, current_user.id, product_id, payload)
    except ProductNotFoundError:
        raise product_not_found_error() from None
    return ProductRead.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a product if it belongs to the authenticated user."""
    try:
        await product_service.delete_product(db, current_user.id, product_id)
    except ProductNotFoundError:
        raise product_not_found_error() from None
