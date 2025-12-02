import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
) -> None:
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


async def verify_bearer_token(
    authorization: Optional[str] = Header(None),
) -> dict:
    settings = get_settings()

    if not settings.auth_enabled:
        return {}

    if not authorization:
        logger.warning("Request missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid authorization header format: {authorization[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        # Import here to avoid circular imports and handle missing dependencies gracefully
        from jose import JWTError

        from app.core.token_validator import get_token_validator

        validator = get_token_validator()
        if not validator:
            logger.debug("Auth disabled, skipping token verification")
            return {}

        claims = validator.verify_token(token)
        logger.debug(
            f"Token verified for user/client: {claims.get('preferred_username') or claims.get('client_id')}"
        )
        return claims

    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
