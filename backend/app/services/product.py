from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductNotFoundError(Exception):
    """Raised when a product does not exist for the current owner."""


async def create_product(db: AsyncSession, owner_id: int, payload: ProductCreate) -> Product:
    """Create a product owned by the given user."""
    product = Product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        owner_id=owner_id,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def list_products(db: AsyncSession, owner_id: int) -> list[Product]:
    """Return all products owned by the given user, newest first."""
    result = await db.execute(
        select(Product)
        .where(Product.owner_id == owner_id)
        .order_by(Product.created_at.desc(), Product.id.desc())
    )
    return list(result.scalars().all())


async def get_owned_product(db: AsyncSession, owner_id: int, product_id: int) -> Product:
    """Return a product only if it belongs to the given user."""
    product = await db.scalar(
        select(Product).where(Product.id == product_id, Product.owner_id == owner_id)
    )
    if product is None:
        raise ProductNotFoundError
    return product


async def update_product(
    db: AsyncSession,
    owner_id: int,
    product_id: int,
    payload: ProductUpdate,
) -> Product:
    """Apply a partial update to a product owned by the given user."""
    product = await get_owned_product(db, owner_id, product_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, owner_id: int, product_id: int) -> None:
    """Delete a product owned by the given user."""
    product = await get_owned_product(db, owner_id, product_id)
    await db.delete(product)
    await db.commit()
