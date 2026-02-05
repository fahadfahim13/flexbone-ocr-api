from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.services.auth_service import get_auth_service, AuthService
from app.schemas.auth import TokenRequest, TokenResponse, RefreshTokenRequest
from app.schemas.common import ErrorResponse, ErrorDetail, ResponseMetadata
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger, get_request_id

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/token",
    response_model=TokenResponse,
    responses={
        200: {"description": "Successful authentication", "model": TokenResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        503: {"description": "Auth disabled", "model": ErrorResponse},
    },
    summary="Get access token",
    description="Authenticate with username and password to receive JWT tokens.",
)
async def login(
    credentials: TokenRequest,
    settings: Settings = Depends(get_settings),
    auth: AuthService = Depends(get_auth_service),
):
    """Authenticate and receive JWT tokens."""
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled on this instance",
        )

    try:
        return auth.authenticate(credentials.username, credentials.password)
    except AuthenticationException as e:
        request_id = get_request_id() or "unknown"
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code=e.code, message=e.message, details=e.details),
                metadata=ResponseMetadata(
                    request_id=request_id, processing_time_ms=0
                ),
            ).model_dump(),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        200: {"description": "Token refreshed", "model": TokenResponse},
        401: {"description": "Invalid refresh token", "model": ErrorResponse},
    },
    summary="Refresh access token",
    description="Use a valid refresh token to get a new access token.",
)
async def refresh(
    request: RefreshTokenRequest,
    settings: Settings = Depends(get_settings),
    auth: AuthService = Depends(get_auth_service),
):
    """Exchange a refresh token for new tokens"""
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled on this instance",
        )

    try:
        return auth.refresh_tokens(request.refresh_token)
    except AuthenticationException as e:
        request_id = get_request_id() or "unknown"
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code=e.code, message=e.message, details=e.details),
                metadata=ResponseMetadata(
                    request_id=request_id, processing_time_ms=0
                ),
            ).model_dump(),
        )
