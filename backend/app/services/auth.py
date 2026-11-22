from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister


class EmailAlreadyRegisteredError(Exception):
    """Raised when a registration attempt uses an existing email address."""


async def register_user(db: AsyncSession, payload: UserRegister) -> User:
    """Create a user with a hashed password and a unique email."""
    email = payload.email.lower()

    existing_user_id = await db.scalar(select(User.id).where(User.email == email))
    if existing_user_id is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        username=payload.username,
        email=email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        # Handles a concurrent registration racing the pre-check.
        await db.rollback()
        raise EmailAlreadyRegisteredError from None

    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, payload: UserLogin) -> User | None:
    """Return the user if the identifier and password are valid."""
    if payload.email is not None:
        query = select(User).where(User.email == payload.email.lower())
    else:
        query = select(User).where(User.username == payload.username)

    user = await db.scalar(query)
    if user is None:
        return None
    if not verify_password(payload.password, user.hashed_password):
        return None
    return user
