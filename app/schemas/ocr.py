from pydantic import BaseModel, Field
from typing import Optional


class OCRResultData(BaseModel):
    """Internal data model for OCR service results"""

    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score (0-1)"
    )
    word_count: int = Field(..., ge=0, description="Number of words detected")
    language: Optional[str] = Field(None, description="Detected language code")


class OCRSuccessResponse(BaseModel):
    """Successful OCR extraction response - matches spec format"""

    success: bool = Field(default=True)
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score (0-1)"
    )
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "text": "Invoice #12345\nDate: 2024-01-15\nTotal: $1,234.56",
                "confidence": 0.94,
                "processing_time_ms": 847,
            }
        }
    }


class OCRNoTextResponse(BaseModel):
    """Response when no text is found in image"""

    success: bool = Field(default=True)
    text: str = Field(default="", description="Empty string when no text found")
    confidence: float = Field(default=0.0, description="Zero confidence when no text")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    message: Optional[str] = Field(
        default="No text could be detected in the uploaded image"
    )
