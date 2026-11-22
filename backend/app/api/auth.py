from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.user import TokenRead, UserLogin, UserRead, UserRegister
from app.services.auth import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    """Register a new user."""
    try:
        user = await register_user(db, payload)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from None

    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenRead)
async def login(
    payload: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenRead:
    """Exchange valid credentials for a JWT access token."""
    user = await authenticate_user(db, payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenRead(access_token=create_access_token(str(user.id)))
