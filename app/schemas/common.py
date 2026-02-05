from pydantic import BaseModel, Field
from typing import Any, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Indicates successful operation")
    data: T = Field(..., description="Response data")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Indicates failed operation")
    error: ErrorDetail = Field(..., description="Error information")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
