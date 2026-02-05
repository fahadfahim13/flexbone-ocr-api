from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentHealth(BaseModel):
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[int] = None


class LivenessResponse(BaseModel):
    status: HealthStatus = Field(..., description="Service liveness status")
    version: str = Field(..., description="Application version")

    model_config = {
        "json_schema_extra": {"example": {"status": "healthy", "version": "1.0.0"}}
    }


class ReadinessResponse(BaseModel):
    status: HealthStatus = Field(..., description="Overall readiness status")
    version: str = Field(..., description="Application version")
    components: dict[str, ComponentHealth] = Field(
        ..., description="Component health status"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "components": {"vision_api": {"status": "healthy", "latency_ms": 145}},
            }
        }
    }
