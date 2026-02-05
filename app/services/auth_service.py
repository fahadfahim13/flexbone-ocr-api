from app.config import get_settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
)
from app.core.exceptions import InvalidCredentialsException
from app.core.logging import get_logger
from app.schemas.auth import TokenResponse

logger = get_logger(__name__)


class AuthService:
    """Authentication service (demo implementation without database)"""

    def __init__(self):
        self.settings = get_settings()
        self._users: dict[str, str] = {}
        self._initialize_users()

    def _initialize_users(self):
        """Initialize demo users with hashed passwords"""
        for username, password in self.settings.parsed_demo_users.items():
            self._users[username] = get_password_hash(password)
        logger.info("demo_users_initialized", count=len(self._users))

    def authenticate(self, username: str, password: str) -> TokenResponse:
        """Authenticate user and return tokens"""
        if username not in self._users:
            logger.warning("auth_user_not_found", username=username)
            raise InvalidCredentialsException()

        if not verify_password(password, self._users[username]):
            logger.warning("auth_invalid_password", username=username)
            raise InvalidCredentialsException()

        access_token = create_access_token(subject=username)
        refresh_token = create_refresh_token(subject=username)

        logger.info("auth_success", username=username)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.jwt_expiration_minutes * 60,
        )

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        username = validate_refresh_token(refresh_token)

        if username not in self._users:
            logger.warning("refresh_user_not_found", username=username)
            raise InvalidCredentialsException()

        new_access_token = create_access_token(subject=username)
        new_refresh_token = create_refresh_token(subject=username)

        logger.info("token_refreshed", username=username)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=self.settings.jwt_expiration_minutes * 60,
        )


auth_service = AuthService()


def get_auth_service() -> AuthService:
    return auth_service
