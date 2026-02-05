import time
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, Request
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.dependencies import get_current_user_required
from app.services.image_validator import get_image_validator, ImageValidator
from app.services.ocr_service import get_ocr_service, OCRService
from app.services.cache_service import get_image_hash, get_cached_result, cache_result
from app.schemas.ocr import (
    OCRSuccessResponse,
    OCRNoTextResponse,
    BatchOCRResponse,
    BatchItemResult,
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
    description="Upload a JPG, PNG, or GIF image to extract text using OCR.",
)
@limiter.limit(
    get_rate_limit_string(),
    exempt_when=lambda: not get_settings().rate_limit_enabled,
)
async def extract_text(
    request: Request,
    image: UploadFile = File(..., description="JPG, PNG, or GIF image file (max 10MB)"),
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

        # Check cache first
        image_hash = get_image_hash(content)
        cached = get_cached_result(image_hash)

        if cached:
            text, confidence, word_count, language = cached
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)

            logger.info(
                "ocr_request_completed_from_cache",
                word_count=word_count,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
            )

            return OCRSuccessResponse(
                success=True,
                text=text,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
            )

        # Process with OCR
        result, processing_time_ms = await ocr.extract_text(content)

        # Cache the result
        cache_result(
            image_hash,
            result.text,
            result.confidence,
            result.word_count,
            result.language,
        )

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


@router.post(
    "/batch",
    response_model=BatchOCRResponse,
    responses={
        200: {"description": "Batch processing completed", "model": BatchOCRResponse},
        401: {"description": "Authentication required", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
    },
    summary="Batch extract text from multiple images",
    description="Upload multiple images to extract text from all of them in a single request.",
)
@limiter.limit(
    get_rate_limit_string(),
    exempt_when=lambda: not get_settings().rate_limit_enabled,
)
async def batch_extract_text(
    request: Request,
    images: List[UploadFile] = File(..., description="Multiple image files (max 10 images, 10MB each)"),
    current_user: str = Depends(get_current_user_required),
    settings: Settings = Depends(get_settings),
    validator: ImageValidator = Depends(get_image_validator),
    ocr: OCRService = Depends(get_ocr_service),
):
    """Extract text from multiple images in a single request."""
    total_start_time = time.perf_counter()

    # Limit batch size
    max_batch_size = 10
    if len(images) > max_batch_size:
        images = images[:max_batch_size]
        logger.warning("batch_size_limited", original_count=len(images), max_count=max_batch_size)

    logger.info(
        "batch_ocr_started",
        image_count=len(images),
        user=current_user,
    )

    results: List[BatchItemResult] = []
    successful = 0
    failed = 0

    for image in images:
        start_time = time.perf_counter()
        filename = image.filename or "unknown"

        try:
            content, width, height = await validator.validate(image)

            # Check cache first
            image_hash = get_image_hash(content)
            cached = get_cached_result(image_hash)

            if cached:
                text, confidence, word_count, language = cached
                processing_time_ms = int((time.perf_counter() - start_time) * 1000)

                results.append(
                    BatchItemResult(
                        filename=filename,
                        success=True,
                        text=text,
                        confidence=confidence,
                        processing_time_ms=processing_time_ms,
                        error_code=None,
                        error=None,
                    )
                )
                successful += 1
                continue

            # Process with OCR
            result, processing_time_ms = await ocr.extract_text(content)

            # Cache the result
            cache_result(
                image_hash,
                result.text,
                result.confidence,
                result.word_count,
                result.language,
            )

            results.append(
                BatchItemResult(
                    filename=filename,
                    success=True,
                    text=result.text,
                    confidence=result.confidence,
                    processing_time_ms=processing_time_ms,
                    error_code=None,
                    error=None,
                )
            )
            successful += 1

        except NoTextFoundException:
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            results.append(
                BatchItemResult(
                    filename=filename,
                    success=True,
                    text="",
                    confidence=0.0,
                    processing_time_ms=processing_time_ms,
                    error_code=None,
                    error=None,
                )
            )
            successful += 1

        except AppException as e:
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            results.append(
                BatchItemResult(
                    filename=filename,
                    success=False,
                    text=None,
                    confidence=None,
                    processing_time_ms=processing_time_ms,
                    error_code=e.code,
                    error=e.message,
                )
            )
            failed += 1

        except Exception as e:
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            results.append(
                BatchItemResult(
                    filename=filename,
                    success=False,
                    text=None,
                    confidence=None,
                    processing_time_ms=processing_time_ms,
                    error_code="INTERNAL_ERROR",
                    error=str(e),
                )
            )
            failed += 1

    total_processing_time_ms = int((time.perf_counter() - total_start_time) * 1000)

    logger.info(
        "batch_ocr_completed",
        total_images=len(images),
        successful=successful,
        failed=failed,
        total_processing_time_ms=total_processing_time_ms,
    )

    return BatchOCRResponse(
        success=True,
        total_images=len(images),
        successful=successful,
        failed=failed,
        total_processing_time_ms=total_processing_time_ms,
        results=results,
    )
