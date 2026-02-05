from fastapi import APIRouter, Depends

from app.config import get_settings, Settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service is running.",
)
async def health_check(settings: Settings = Depends(get_settings)):
    """Simple health check endpoint"""
    return HealthResponse(status="healthy", version=settings.app_version)
