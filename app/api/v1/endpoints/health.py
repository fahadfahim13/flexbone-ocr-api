from fastapi import APIRouter, Depends

from app.config import get_settings, Settings
from app.services.ocr_service import get_ocr_service, OCRService
from app.schemas.health import (
    LivenessResponse,
    ReadinessResponse,
    HealthStatus,
    ComponentHealth,
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Check if the service is running.",
)
async def liveness(settings: Settings = Depends(get_settings)):
    """Simple liveness check"""
    return LivenessResponse(status=HealthStatus.HEALTHY, version=settings.app_version)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Check if the service is ready to accept requests.",
)
async def readiness(
    settings: Settings = Depends(get_settings),
    ocr: OCRService = Depends(get_ocr_service),
):
    """Readiness check - validates all dependencies"""
    components = {}
    overall_status = HealthStatus.HEALTHY

    try:
        is_healthy, latency_ms = await ocr.health_check()
        components["vision_api"] = ComponentHealth(
            status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
        )
        if not is_healthy:
            overall_status = HealthStatus.UNHEALTHY
    except Exception as e:
        logger.error("readiness_check_failed", component="vision_api", error=str(e))
        components["vision_api"] = ComponentHealth(
            status=HealthStatus.UNHEALTHY, message=str(e)
        )
        overall_status = HealthStatus.UNHEALTHY

    return ReadinessResponse(
        status=overall_status, version=settings.app_version, components=components
    )
