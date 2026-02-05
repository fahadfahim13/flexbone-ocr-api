from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # GCP Settings
    gcp_project_id: str = Field(..., description="Google Cloud Project ID")
    google_application_credentials: str | None = Field(
        None, description="Path to service account JSON"
    )

    # App Settings
    app_name: str = Field(default="Flexbone OCR API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # File Upload Settings
    max_file_size_mb: int = Field(default=10)
    allowed_extensions: List[str] = Field(default=["jpg", "jpeg", "png"])
    allowed_mime_types: List[str] = Field(default=["image/jpeg", "image/png"])

    # Auth Settings (toggleable)
    auth_enabled: bool = Field(default=False)
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=30)
    jwt_refresh_expiration_days: int = Field(default=7)

    # Demo users (since no database) - format: "user1:pass1,user2:pass2"
    demo_users: str = Field(default="demo:demo123,admin:admin123")

    # Rate Limiting (toggleable)
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_requests: int = Field(default=100)
    rate_limit_window_seconds: int = Field(default=60)

    # Cloud Run Settings
    port: int = Field(default=8080)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def parsed_demo_users(self) -> dict[str, str]:
        """Parse demo users string into dict"""
        users = {}
        for pair in self.demo_users.split(","):
            if ":" in pair:
                username, password = pair.split(":", 1)
                users[username.strip()] = password.strip()
        return users


@lru_cache
def get_settings() -> Settings:
    return Settings()
