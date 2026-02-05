import hashlib
from typing import Optional, Tuple
from cachetools import TTLCache

from app.core.logging import get_logger

logger = get_logger(__name__)

# Cache up to 100 results, expire after 1 hour (3600 seconds)
_cache: TTLCache = TTLCache(maxsize=100, ttl=3600)


def get_image_hash(content: bytes) -> str:
    """Generate SHA256 hash of image content."""
    return hashlib.sha256(content).hexdigest()


def get_cached_result(image_hash: str) -> Optional[Tuple[str, float, int, Optional[str]]]:
    """
    Get cached OCR result by image hash.

    Returns tuple of (text, confidence, word_count, language) or None if not cached.
    """
    result = _cache.get(image_hash)
    if result:
        logger.info("cache_hit", image_hash=image_hash[:16])
    return result


def cache_result(
    image_hash: str,
    text: str,
    confidence: float,
    word_count: int,
    language: Optional[str],
) -> None:
    """Cache OCR result by image hash."""
    _cache[image_hash] = (text, confidence, word_count, language)
    logger.info("cache_stored", image_hash=image_hash[:16])


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "size": len(_cache),
        "maxsize": _cache.maxsize,
        "ttl": _cache.ttl,
    }
