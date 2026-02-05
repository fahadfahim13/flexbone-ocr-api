import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    def test_auth_disabled_returns_503(self, client: TestClient):
        """Test that auth endpoints return 503 when auth disabled"""
        response = client.post(
            "/api/v1/auth/token",
            json={"username": "demo", "password": "demo123"},
        )
        assert response.status_code == 503

    def test_login_success(self, auth_client: TestClient):
        """Test successful login"""
        response = auth_client.post(
            "/api/v1/auth/token",
            json={"username": "demo", "password": "demo123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, auth_client: TestClient):
        """Test login with invalid credentials"""
        response = auth_client.post(
            "/api/v1/auth/token",
            json={"username": "demo", "password": "wrong"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_FAILED"

    def test_protected_endpoint_without_token(self, auth_client: TestClient):
        """Test accessing protected endpoint without token"""
        from unittest.mock import patch

        with patch("app.services.ocr_service.vision.ImageAnnotatorClient"):
            response = auth_client.post(
                "/api/v1/ocr/extract",
                files={"image": ("test.jpg", b"fake", "image/jpeg")},
            )
            assert response.status_code == 401
