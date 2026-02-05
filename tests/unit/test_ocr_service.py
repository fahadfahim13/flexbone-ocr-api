import pytest
from unittest.mock import MagicMock, patch
from app.services.ocr_service import OCRService
from app.core.exceptions import NoTextFoundException


class TestOCRService:
    @pytest.fixture
    def service(self):
        return OCRService()

    @pytest.mark.asyncio
    async def test_extract_text_success(self, service):
        """Test successful text extraction"""
        mock_response = MagicMock()
        mock_response.error.message = ""
        mock_response.full_text_annotation.text = "Hello World"

        page = MagicMock()
        page.confidence = 0.95
        page.property.detected_languages = [MagicMock(language_code="en")]
        mock_response.full_text_annotation.pages = [page]

        with patch.object(service, "client") as mock_client:
            mock_client.document_text_detection.return_value = mock_response

            result, processing_time = await service.extract_text(b"fake_image_content")

            assert result.text == "Hello World"
            assert result.confidence == 0.95
            assert result.language == "en"

    @pytest.mark.asyncio
    async def test_extract_text_no_text_found(self, service):
        """Test NoTextFoundException when no text detected"""
        mock_response = MagicMock()
        mock_response.error.message = ""
        mock_response.full_text_annotation.text = ""
        mock_response.full_text_annotation.pages = []

        with patch.object(service, "client") as mock_client:
            mock_client.document_text_detection.return_value = mock_response

            with pytest.raises(NoTextFoundException):
                await service.extract_text(b"fake_image_content")
