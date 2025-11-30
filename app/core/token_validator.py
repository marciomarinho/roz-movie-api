"""Token validation for both Keycloak and AWS Cognito."""
import json
import logging
from typing import Any, Optional
from urllib.request import urlopen

from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TokenValidator:
    """Base token validator interface."""

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a token.

        Args:
            token: JWT token string.

        Returns:
            dict: Decoded token claims.

        Raises:
            JWTError: If token is invalid or verification fails.
        """
        raise NotImplementedError


class KeycloakTokenValidator(TokenValidator):
    """Validator for Keycloak JWT tokens."""

    def __init__(self):
        """Initialize Keycloak validator."""
        self.settings = get_settings()
        self._public_key: Optional[str] = None

    def _fetch_public_key(self) -> str:
        """Fetch Keycloak public key from JWKS endpoint.

        Returns:
            str: RSA public key in PEM format.

        Raises:
            Exception: If key fetch fails.
        """
        if self._public_key:
            return self._public_key

        try:
            jwks_url = (
                f"{self.settings.keycloak_url}/realms/{self.settings.keycloak_realm}/"
                "protocol/openid-connect/certs"
            )
            logger.debug(f"Fetching Keycloak JWKS from: {jwks_url}")

            with urlopen(jwks_url, timeout=10) as response:
                jwks = json.load(response)

            # Extract the first key (assumes single key)
            if not jwks.get("keys"):
                raise ValueError("No keys found in Keycloak JWKS response")

            key_data = jwks["keys"][0]
            # Convert JWK to PEM format
            from jose.backends.rsa_backend import RSAKey

            rsa_key = RSAKey.from_jwk(json.dumps(key_data))
            self._public_key = rsa_key.to_pem()
            return self._public_key

        except Exception as e:
            logger.error(f"Failed to fetch Keycloak public key: {e}")
            raise

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify Keycloak JWT token.

        Args:
            token: JWT token string.

        Returns:
            dict: Decoded token claims.

        Raises:
            JWTError: If token is invalid.
        """
        try:
            public_key = self._fetch_public_key()
            # Decode without audience validation first, but verify expiration
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False, "verify_exp": True},  # Verify expiration
            )
            
            logger.debug(f"Token claims: {claims}")
            
            # Manually validate azp (authorized party) or aud claim
            azp = claims.get("azp")
            aud = claims.get("aud")
            
            logger.debug(
                f"Token audience validation: azp={azp}, aud={aud}, "
                f"expected_client_id={self.settings.keycloak_client_id}"
            )
            
            # Accept if azp matches client_id (preferred for user tokens)
            # or if aud matches (for service account tokens)
            if azp != self.settings.keycloak_client_id and aud != self.settings.keycloak_client_id:
                raise JWTError(
                    f"Invalid audience. Expected client_id={self.settings.keycloak_client_id}, "
                    f"got azp={azp}, aud={aud}"
                )
            
            logger.debug(f"Keycloak token verified for user: {claims.get('preferred_username')}")
            return claims

        except JWTError as e:
            logger.warning(f"Keycloak token verification failed: {e}")
            raise


class CognitoTokenValidator(TokenValidator):
    """Validator for AWS Cognito JWT tokens."""

    def __init__(self):
        """Initialize Cognito validator."""
        self.settings = get_settings()
        self._jwks: Optional[dict] = None

    def _fetch_jwks(self) -> dict:
        """Fetch Cognito public keys from JWKS endpoint.

        Returns:
            dict: JWKS data containing public keys.

        Raises:
            Exception: If JWKS fetch fails.
        """
        if self._jwks:
            return self._jwks

        try:
            # Construct JWKS URL from Cognito pool ID and region
            if not self.settings.cognito_jwks_url:
                self.settings.cognito_jwks_url = (
                    f"https://cognito-idp.{self.settings.cognito_region}.amazonaws.com/"
                    f"{self.settings.cognito_user_pool_id}/.well-known/jwks.json"
                )

            logger.debug(f"Fetching Cognito JWKS from: {self.settings.cognito_jwks_url}")

            with urlopen(self.settings.cognito_jwks_url, timeout=10) as response:
                self._jwks = json.load(response)

            return self._jwks

        except Exception as e:
            logger.error(f"Failed to fetch Cognito JWKS: {e}")
            raise

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify AWS Cognito JWT token.

        Args:
            token: JWT token string.

        Returns:
            dict: Decoded token claims.

        Raises:
            JWTError: If token is invalid.
        """
        try:
            # Get header to extract kid (key ID)
            headers = jwt.get_unverified_header(token)
            kid = headers.get("kid")

            if not kid:
                raise JWTError("No key ID in token header")

            # Fetch JWKS and find matching key
            jwks = self._fetch_jwks()
            key_data = None

            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    key_data = key
                    break

            if not key_data:
                raise JWTError(f"No key found with kid: {kid}")

            # Verify token
            claims = jwt.decode(
                token,
                json.dumps(key_data),
                algorithms=["RS256"],
                options={"verify_signature": True, "verify_aud": False},
            )

            # Verify token_use is 'access'
            if claims.get("token_use") != "access":
                raise JWTError("Invalid token_use")

            logger.debug(f"Cognito token verified for client: {claims.get('client_id')}")
            return claims

        except JWTError as e:
            logger.warning(f"Cognito token verification failed: {e}")
            raise


def get_token_validator() -> TokenValidator:
    """Get appropriate token validator based on configuration.

    Returns:
        TokenValidator: Keycloak or Cognito validator instance.

    Raises:
        ValueError: If auth provider is not configured properly.
    """
    settings = get_settings()

    if not settings.auth_enabled:
        logger.debug("Authentication is disabled")
        return None

    if settings.auth_provider.lower() == "cognito":
        if not settings.cognito_user_pool_id:
            raise ValueError("COGNITO_USER_POOL_ID not configured")
        logger.debug("Using Cognito token validator")
        return CognitoTokenValidator()

    elif settings.auth_provider.lower() == "keycloak":
        logger.debug("Using Keycloak token validator")
        return KeycloakTokenValidator()

    else:
        raise ValueError(f"Unknown auth provider: {settings.auth_provider}")
