import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    validate_access_token,
    validate_refresh_token,
)
from app.core.exceptions import InvalidTokenException, TokenExpiredException


class TestPasswordHashing:
    def test_hash_and_verify_password(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)


class TestJWTTokens:
    def test_create_and_validate_access_token(self):
        """Test access token creation and validation"""
        username = "testuser"
        token = create_access_token(subject=username)

        validated_username = validate_access_token(token)
        assert validated_username == username

    def test_create_and_validate_refresh_token(self):
        """Test refresh token creation and validation"""
        username = "testuser"
        token = create_refresh_token(subject=username)

        validated_username = validate_refresh_token(token)
        assert validated_username == username

    def test_invalid_token_raises_exception(self):
        """Test that invalid tokens raise InvalidTokenException"""
        with pytest.raises(InvalidTokenException):
            validate_access_token("invalid_token")

    def test_refresh_token_cannot_be_used_as_access(self):
        """Test that refresh tokens cannot be validated as access tokens"""
        refresh_token = create_refresh_token(subject="testuser")

        with pytest.raises(InvalidTokenException):
            validate_access_token(refresh_token)
