from google.cloud import vision
from google.cloud.vision_v1 import types
from typing import Optional, Tuple
import time

from app.core.exceptions import OCRException, NoTextFoundException
from app.core.logging import get_logger
from app.schemas.ocr import OCRResultData

logger = get_logger(__name__)


class OCRService:
    """Google Cloud Vision OCR service"""

    def __init__(self):
        self._client: Optional[vision.ImageAnnotatorClient] = None

    @property
    def client(self) -> vision.ImageAnnotatorClient:
        """Lazy initialization of Vision API client"""
        if self._client is None:
            try:
                self._client = vision.ImageAnnotatorClient()
                logger.info("vision_client_initialized")
            except Exception as e:
                logger.error("vision_client_init_failed", error=str(e))
                raise OCRException(
                    message="Failed to initialize Vision API client",
                    details={"error": str(e)},
                )
        return self._client

    async def extract_text(self, image_content: bytes) -> Tuple[OCRResultData, int]:
        """
        Extract text from image using Cloud Vision API
        """
        start_time = time.perf_counter()

        try:
            image = types.Image(content=image_content)

            response = self.client.document_text_detection(image=image)

            processing_time_ms = int((time.perf_counter() - start_time) * 1000)

            if response.error.message:
                logger.error("vision_api_error", error=response.error.message)
                raise OCRException(
                    message="Vision API returned an error",
                    details={"api_error": response.error.message},
                )

            if not response.full_text_annotation.text:
                logger.info("no_text_detected", processing_time_ms=processing_time_ms)
                raise NoTextFoundException()

            full_text = response.full_text_annotation.text.strip()

            # Calculate confidence
            confidences = []
            for page in response.full_text_annotation.pages:
                if page.confidence:
                    confidences.append(page.confidence)

            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

            word_count = len(full_text.split())

            # Detect language
            language = None
            if response.full_text_annotation.pages:
                first_page = response.full_text_annotation.pages[0]
                if first_page.property and first_page.property.detected_languages:
                    language = first_page.property.detected_languages[0].language_code

            logger.info(
                "text_extracted",
                word_count=word_count,
                confidence=avg_confidence,
                language=language,
                processing_time_ms=processing_time_ms,
            )

            return (
                OCRResultData(
                    text=full_text,
                    confidence=round(avg_confidence, 4),
                    word_count=word_count,
                    language=language,
                ),
                processing_time_ms,
            )

        except NoTextFoundException:
            raise
        except OCRException:
            raise
        except Exception as e:
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                "ocr_extraction_failed",
                error=str(e),
                processing_time_ms=processing_time_ms,
            )
            raise OCRException(
                message="Failed to extract text from image",
                details={"error": str(e)},
            )

    async def health_check(self) -> Tuple[bool, int]:
        """Check if Vision API is accessible"""
        start_time = time.perf_counter()

        try:
            test_image = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
                b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
                b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
            )

            image = types.Image(content=test_image)
            self.client.text_detection(image=image)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return True, latency_ms

        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("vision_health_check_failed", error=str(e))
            return False, latency_ms


ocr_service = OCRService()


def get_ocr_service() -> OCRService:
    return ocr_service
