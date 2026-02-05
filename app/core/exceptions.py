from fastapi import status
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationException(AppException):
    """Validation related errors"""

    def __init__(
        self, code: str, message: str, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(code, message, status.HTTP_400_BAD_REQUEST, details)


class FileValidationException(ValidationException):
    """File upload validation errors"""

    pass


class FileTooLargeException(FileValidationException):
    def __init__(self, max_size_mb: int, actual_size_mb: float):
        super().__init__(
            code="FILE_TOO_LARGE",
            message=f"File size exceeds maximum allowed size of {max_size_mb}MB",
            details={
                "max_size_mb": max_size_mb,
                "actual_size_mb": round(actual_size_mb, 2),
            },
        )


class UnsupportedFileTypeException(FileValidationException):
    def __init__(self, received_type: str, allowed_types: list[str]):
        super().__init__(
            code="UNSUPPORTED_FILE_TYPE",
            message=f"File type '{received_type}' is not supported",
            details={"received_type": received_type, "allowed_types": allowed_types},
        )


class InvalidFileException(FileValidationException):
    def __init__(self, reason: str):
        super().__init__(
            code="INVALID_FILE",
            message=f"Invalid file: {reason}",
            details={"reason": reason},
        )


class OCRException(AppException):
    """OCR processing errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="OCR_PROCESSING_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class NoTextFoundException(AppException):
    """No text detected in image"""

    def __init__(self):
        super().__init__(
            code="NO_TEXT_FOUND",
            message="No text could be detected in the uploaded image",
            status_code=status.HTTP_200_OK,
            details={},
        )


class AuthenticationException(AppException):
    """Authentication errors"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={},
        )


class InvalidCredentialsException(AuthenticationException):
    def __init__(self):
        super().__init__(message="Invalid username or password")


class TokenExpiredException(AuthenticationException):
    def __init__(self):
        super().__init__(message="Token has expired")


class InvalidTokenException(AuthenticationException):
    def __init__(self):
        super().__init__(message="Invalid or malformed token")


class RateLimitExceededException(AppException):
    def __init__(self, retry_after: int):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after_seconds": retry_after},
        )
