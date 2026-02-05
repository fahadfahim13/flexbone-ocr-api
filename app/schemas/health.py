from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")

    model_config = {
        "json_schema_extra": {"example": {"status": "healthy", "version": "1.0.0"}}
    }
