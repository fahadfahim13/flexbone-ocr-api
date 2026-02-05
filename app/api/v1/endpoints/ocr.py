import time
from fastapi import APIRouter, UploadFile, File, Depends, Request
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.dependencies import get_current_user_required
from app.services.image_validator import get_image_validator, ImageValidator
from app.services.ocr_service import get_ocr_service, OCRService
from app.schemas.ocr import (
    OCRSuccessResponse,
    OCRNoTextResponse,
)
from app.schemas.common import ErrorResponse, ErrorDetail, ResponseMetadata
from app.core.exceptions import AppException, NoTextFoundException
from app.core.logging import get_logger, get_request_id
from app.middleware.rate_limit import limiter, get_rate_limit_string

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/extract",
    response_model=OCRSuccessResponse,
    responses={
        200: {"description": "Successful text extraction", "model": OCRSuccessResponse},
        400: {"description": "Invalid file", "model": ErrorResponse},
        401: {"description": "Authentication required", "model": ErrorResponse},
        413: {"description": "File too large", "model": ErrorResponse},
        415: {"description": "Unsupported file type", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
    summary="Extract text from image",
    description="Upload a JPG or PNG image to extract text using OCR.",
)
@limiter.limit(
    get_rate_limit_string(),
    exempt_when=lambda: not get_settings().rate_limit_enabled,
)
async def extract_text(
    request: Request,
    image: UploadFile = File(..., description="JPG or PNG image file (max 10MB)"),
    current_user: str = Depends(get_current_user_required),
    settings: Settings = Depends(get_settings),
    validator: ImageValidator = Depends(get_image_validator),
    ocr: OCRService = Depends(get_ocr_service),
):
    """Extract text from an uploaded image using Google Cloud Vision API."""
    start_time = time.perf_counter()
    request_id = get_request_id() or "unknown"

    logger.info(
        "ocr_request_started",
        filename=image.filename,
        content_type=image.content_type,
        user=current_user,
    )

    try:
        content, width, height = await validator.validate(image)

        result, processing_time_ms = await ocr.extract_text(content)

        logger.info(
            "ocr_request_completed",
            word_count=result.word_count,
            confidence=result.confidence,
            processing_time_ms=processing_time_ms,
        )

        return OCRSuccessResponse(
            success=True,
            text=result.text,
            confidence=result.confidence,
            processing_time_ms=processing_time_ms,
        )

    except NoTextFoundException:
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        return OCRNoTextResponse(
            success=True,
            text="",
            confidence=0.0,
            processing_time_ms=processing_time_ms,
        )

    except AppException as e:
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        logger.warning(
            "ocr_request_failed", error_code=e.code, error_message=e.message
        )

        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=e.code, message=e.message, details=e.details
                ),
                metadata=ResponseMetadata(
                    request_id=request_id, processing_time_ms=processing_time_ms
                ),
            ).model_dump(),
        )
