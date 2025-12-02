import json
import logging
from typing import Any, Dict, Optional

import requests
from jose import JWTError, jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class KeycloakTokenValidator:
    _instance = None
    _public_key: Optional[str] = None
    _algorithms: list[str] = ["RS256"]

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_public_key(cls) -> str:
        if cls._public_key is None:
            settings = get_settings()
            jwks_url = (
                f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/"
                "protocol/openid-connect/certs"
            )

            try:
                response = requests.get(jwks_url, timeout=5)
                response.raise_for_status()
                jwks = response.json()

                # Get the signing key (use: sig)
                if "keys" not in jwks or not jwks["keys"]:
                    raise ValueError("No keys found in JWKS")

                # Find the signing key
                key_data = None
                for key in jwks["keys"]:
                    if key.get("use") == "sig" and key.get("kty") == "RSA":
                        key_data = key
                        break
                
                # Fallback to first key if no signing key found
                if key_data is None:
                    logger.warning("No signing key found, using first key")
                    key_data = jwks["keys"][0]

                # Convert JWK to PEM format using cryptography library directly
                from cryptography.hazmat.primitives.asymmetric import rsa
                import base64
                
                # Helper to decode base64url with proper padding
                def decode_base64url(data):
                    # Add padding if needed
                    padding = 4 - len(data) % 4
                    if padding != 4:
                        data += '=' * padding
                    return base64.urlsafe_b64decode(data)
                
                # Extract RSA components from JWK
                n = int.from_bytes(decode_base64url(key_data['n']), 'big')
                e = int.from_bytes(decode_base64url(key_data['e']), 'big')
                
                # Create public key
                public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
                pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                cls._public_key = pem.decode()
                logger.info(f"Keycloak public key loaded successfully (kid: {key_data.get('kid')})")
            except Exception as e:
                logger.error(f"Failed to fetch Keycloak public key: {e}")
                raise

        return cls._public_key

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        settings = get_settings()

        try:
            # Get the public key
            public_key = cls.get_public_key()

            # Decode and verify the token without audience validation first
            # We'll validate audience manually after decoding
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=cls._algorithms,
                options={"verify_aud": False},  # We'll validate audience manually
            )

            # Basic validation
            if "sub" not in decoded:
                raise JWTError("Token missing 'sub' claim")

            # Validate audience: check both 'aud' and 'azp' claims
            # For Keycloak, user tokens have aud="account" and azp=client_id
            aud = decoded.get("aud")
            azp = decoded.get("azp")
            
            # Accept if azp matches our client_id (preferred), or if aud matches
            if azp != settings.keycloak_client_id and aud != settings.keycloak_client_id:
                raise JWTError(
                    f"Invalid audience. Expected azp={settings.keycloak_client_id}, "
                    f"got azp={azp}, aud={aud}"
                )

            logger.debug(f"Token verified for user: {decoded.get('preferred_username')}")
            return decoded

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise JWTError(str(e))


def get_keycloak_token_validator() -> KeycloakTokenValidator:
    return KeycloakTokenValidator()
