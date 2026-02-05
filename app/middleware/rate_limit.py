from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.logging import get_logger, get_request_id

logger = get_logger(__name__)
settings = get_settings()

limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_string() -> str:
    """Get rate limit string from settings"""
    return f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}seconds"


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Custom handler for rate limit exceeded"""
    request_id = get_request_id() or "unknown"

    logger.warning(
        "rate_limit_exceeded",
        client_ip=get_remote_address(request),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {"retry_after_seconds": settings.rate_limit_window_seconds},
            },
            "metadata": {"request_id": request_id, "processing_time_ms": 0},
        },
        headers={"Retry-After": str(settings.rate_limit_window_seconds)},
    )
