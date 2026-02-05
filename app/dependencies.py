from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.config import get_settings, Settings
from app.core.security import validate_access_token
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Optional[str]:
    """Get current user if auth is enabled and token provided."""
    if not settings.auth_enabled:
        return None

    if credentials is None:
        return None

    try:
        username = validate_access_token(credentials.credentials)
        return username
    except AuthenticationException:
        return None


async def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> str:
    """Get current user. Raises 401 if auth is enabled but no valid token."""
    if not settings.auth_enabled:
        return "anonymous"

    if credentials is None:
        logger.warning("auth_missing_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        username = validate_access_token(credentials.credentials)
        return username
    except AuthenticationException as e:
        logger.warning("auth_invalid_token", error=e.message)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
