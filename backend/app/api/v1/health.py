from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check. Database connectivity will be added later."""
    return {"status": "ok", "environment": settings.environment}
