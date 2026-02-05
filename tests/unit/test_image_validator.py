import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.image_validator import ImageValidator
from app.core.exceptions import (
    FileTooLargeException,
    UnsupportedFileTypeException,
)


class TestImageValidator:
    @pytest.fixture
    def validator(self):
        return ImageValidator()

    @pytest.mark.asyncio
    async def test_file_too_large(self, validator):
        """Test rejection of files exceeding size limit"""
        large_content = b"x" * (11 * 1024 * 1024)

        mock_file = MagicMock()
        mock_file.read = AsyncMock(return_value=large_content)
        mock_file.seek = AsyncMock()
        mock_file.filename = "test.jpg"

        with pytest.raises(FileTooLargeException):
            await validator.validate(mock_file)

    @pytest.mark.asyncio
    async def test_unsupported_extension(self, validator):
        """Test rejection of unsupported file extensions"""
        mock_file = MagicMock()
        mock_file.read = AsyncMock(return_value=b"small content")
        mock_file.seek = AsyncMock()
        mock_file.filename = "test.gif"

        with pytest.raises(UnsupportedFileTypeException):
            await validator.validate(mock_file)
