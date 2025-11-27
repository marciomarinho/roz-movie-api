"""Security utilities including API key validation."""
import logging
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


async def validate_api_key(
    x_api_key: Optional[str] = Header(None),
    required_key: Optional[str] = None,
) -> None:
    """Validate X-API-Key header.

    Args:
        x_api_key: API key from X-API-Key header.
        required_key: Required API key (from settings).

    Raises:
        HTTPException: If API key validation fails.
    """
    # If no API key is configured, skip validation
    if not required_key:
        return

    # If API key is required but not provided
    if not x_api_key:
        logger.warning("Request missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # If API key doesn't match
    if x_api_key != required_key:
        logger.warning(f"Invalid X-API-Key provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
