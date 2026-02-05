import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io


class TestOCREndpoint:
    """Integration tests for OCR endpoint"""

    def test_extract_text_success(
        self,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_vision_response_with_text,
    ):
        """Test successful text extraction"""
        with patch(
            "app.services.ocr_service.vision.ImageAnnotatorClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.document_text_detection.return_value = (
                mock_vision_response_with_text
            )
            mock_client.return_value = mock_instance

            response = client.post(
                "/api/v1/ocr/extract",
                files={
                    "image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Hello World" in data["text"]
            assert data["confidence"] > 0
            assert data["processing_time_ms"] >= 0

    def test_extract_text_no_text_found(
        self,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_vision_response_no_text,
    ):
        """Test response when no text is found"""
        with patch(
            "app.services.ocr_service.vision.ImageAnnotatorClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.document_text_detection.return_value = (
                mock_vision_response_no_text
            )
            mock_client.return_value = mock_instance

            response = client.post(
                "/api/v1/ocr/extract",
                files={
                    "image": ("test.jpg", io.BytesIO(sample_image_bytes), "image/jpeg")
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["text"] == ""
            assert data["confidence"] == 0.0
            assert "No text" in data["message"]

    def test_extract_text_file_too_large(self, client: TestClient):
        """Test rejection of files exceeding size limit"""
        large_content = b"x" * (11 * 1024 * 1024)

        response = client.post(
            "/api/v1/ocr/extract",
            files={"image": ("large.jpg", io.BytesIO(large_content), "image/jpeg")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FILE_TOO_LARGE"

    def test_extract_text_unsupported_format(self, client: TestClient):
        """Test rejection of unsupported file formats"""
        gif_content = b"GIF89a"

        response = client.post(
            "/api/v1/ocr/extract",
            files={"image": ("test.gif", io.BytesIO(gif_content), "image/gif")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

    def test_extract_text_missing_file(self, client: TestClient):
        """Test error when no file uploaded"""
        response = client.post("/api/v1/ocr/extract")
        assert response.status_code == 422


class TestHealthEndpoints:
    """Tests for health check endpoint"""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
