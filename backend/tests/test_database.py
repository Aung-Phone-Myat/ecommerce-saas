import os

import pytest
from sqlalchemy import text

from app.db.session import db_manager

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Set RUN_DB_TESTS=1 to run PostgreSQL integration tests.",
)


@pytest.mark.anyio
async def test_database_connection() -> None:
    """Open a real session and execute a query against PostgreSQL."""
    async with db_manager.session() as session:
        assert await session.scalar(text("SELECT 1")) == 1
