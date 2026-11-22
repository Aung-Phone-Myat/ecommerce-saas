from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, customers, orders, products, users
from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Release pooled database connections when the application stops."""
    yield
    await db_manager.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        """Confirm that the API process is up and serving requests."""
        return {"message": "E-commerce API is running"}

    # Serve the health check at both /health and the versioned /api/v1/health.
    app.include_router(health.router)
    app.include_router(api_router, prefix="/api/v1")

    # /api/auth, /api/users/me, /api/products, /api/customers, /api/orders, /api/analytics
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(products.router, prefix="/api")
    app.include_router(customers.router, prefix="/api")
    app.include_router(orders.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    return app


app = create_app()

