import magic
from fastapi import UploadFile
from typing import Tuple
from PIL import Image
import io

from app.config import get_settings
from app.core.exceptions import (
    FileTooLargeException,
    UnsupportedFileTypeException,
    InvalidFileException,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageValidator:
    """Validates uploaded image files"""

    def __init__(self):
        self.settings = get_settings()

    async def validate(self, file: UploadFile) -> Tuple[bytes, int, int]:
        """
        Validate uploaded file and return (content, width, height)
        """
        content = await file.read()
        await file.seek(0)

        file_size = len(content)

        # Check file size
        if file_size > self.settings.max_file_size_bytes:
            logger.warning(
                "file_too_large",
                file_size=file_size,
                max_size=self.settings.max_file_size_bytes,
            )
            raise FileTooLargeException(
                max_size_mb=self.settings.max_file_size_mb,
                actual_size_mb=file_size / (1024 * 1024),
            )

        # Check file extension
        if file.filename:
            extension = (
                file.filename.rsplit(".", 1)[-1].lower()
                if "." in file.filename
                else ""
            )
            if extension not in self.settings.allowed_extensions:
                logger.warning(
                    "unsupported_extension",
                    extension=extension,
                    allowed=self.settings.allowed_extensions,
                )
                raise UnsupportedFileTypeException(
                    received_type=extension,
                    allowed_types=self.settings.allowed_extensions,
                )

        # Check MIME type using magic bytes
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.settings.allowed_mime_types:
            logger.warning(
                "unsupported_mime_type",
                mime_type=mime_type,
                allowed=self.settings.allowed_mime_types,
            )
            raise UnsupportedFileTypeException(
                received_type=mime_type,
                allowed_types=self.settings.allowed_mime_types,
            )

        # Validate image can be opened and get dimensions
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()

            image = Image.open(io.BytesIO(content))
            width, height = image.size

            logger.debug(
                "image_validated",
                width=width,
                height=height,
                mime_type=mime_type,
                file_size=file_size,
            )

            return content, width, height

        except Exception as e:
            logger.error("invalid_image_file", error=str(e))
            raise InvalidFileException(
                reason="File appears to be corrupted or not a valid image"
            )


image_validator = ImageValidator()


def get_image_validator() -> ImageValidator:
    return image_validator
