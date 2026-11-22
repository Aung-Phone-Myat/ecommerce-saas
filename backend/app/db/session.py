from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


class DatabaseSessionManager:
    """Own the async engine and hand out short-lived database sessions."""

    def __init__(
        self,
        database_url: str,
        *,
        echo: bool = False,
        require_ssl: bool = True,
        disable_prepared_statements: bool = False,
        pool_size: int = 5,
        max_overflow: int = 5,
    ) -> None:
        connect_args: dict[str, Any] = {}

        if require_ssl:
            connect_args["ssl"] = "require"

        if disable_prepared_statements:
            # asyncpg's cache and SQLAlchemy's prepared-statement cache.
            connect_args["statement_cache_size"] = 0
            connect_args["prepared_statement_cache_size"] = 0

        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=pool_size,
            max_overflow=max_overflow,
            connect_args=connect_args,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Expose the engine for startup/shutdown wiring and diagnostics."""
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Provide a session that rolls back on error and always closes."""
        session = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def dispose(self) -> None:
        """Close pooled connections. Call this when the application shuts down."""
        await self._engine.dispose()


db_manager = DatabaseSessionManager(
    settings.database_url,
    echo=settings.sql_echo,
    require_ssl=settings.db_ssl,
    disable_prepared_statements=settings.db_disable_prepared_statements,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session per request."""
    async with db_manager.session() as session:
        yield session
