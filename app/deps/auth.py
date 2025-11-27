"""Authentication and authorization dependencies."""
import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
) -> None:
    """Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header.

    Raises:
        HTTPException: 401 if API key is missing or invalid.
    """
    settings = get_settings()

    # If no API key is configured, skip verification
    if not settings.api_key:
        return

    if not x_api_key:
        logger.warning("Request missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    if x_api_key != settings.api_key:
        logger.warning(f"Request with invalid API key: {x_api_key[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
