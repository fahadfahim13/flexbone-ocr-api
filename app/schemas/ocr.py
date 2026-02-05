from pydantic import BaseModel, Field
from typing import Optional, List


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


class BatchItemResult(BaseModel):
    """Result for a single image in batch processing"""

    filename: str = Field(..., description="Original filename")
    success: bool = Field(..., description="Whether extraction succeeded")
    text: Optional[str] = Field(None, description="Extracted text content")
    confidence: Optional[float] = Field(None, description="Confidence score")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchOCRResponse(BaseModel):
    """Response for batch OCR processing"""

    success: bool = Field(default=True)
    total_images: int = Field(..., description="Total images processed")
    successful: int = Field(..., description="Successfully processed count")
    failed: int = Field(..., description="Failed processing count")
    total_processing_time_ms: int = Field(..., description="Total processing time")
    results: List[BatchItemResult] = Field(..., description="Individual results")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "total_images": 3,
                "successful": 2,
                "failed": 1,
                "total_processing_time_ms": 2500,
                "results": [
                    {
                        "filename": "image1.jpg",
                        "success": True,
                        "text": "Hello World",
                        "confidence": 0.95,
                        "processing_time_ms": 800,
                        "error": None,
                    },
                    {
                        "filename": "image2.jpg",
                        "success": True,
                        "text": "Sample Text",
                        "confidence": 0.92,
                        "processing_time_ms": 750,
                        "error": None,
                    },
                    {
                        "filename": "invalid.txt",
                        "success": False,
                        "text": None,
                        "confidence": None,
                        "processing_time_ms": None,
                        "error": "Unsupported file type",
                    },
                ],
            }
        }
    }
