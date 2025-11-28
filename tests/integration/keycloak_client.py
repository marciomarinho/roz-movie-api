"""Keycloak client helper for integration tests."""
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class KeycloakTestClient:
    """Helper for obtaining tokens from Keycloak for tests."""

    def __init__(
        self,
        keycloak_url: str,
        realm: str,
        client_id: str,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize Keycloak test client.

        Args:
            keycloak_url: Base URL of Keycloak server.
            realm: Keycloak realm name.
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret (optional).
            username: Test user username (for password grant).
            password: Test user password (for password grant).
        """
        self.keycloak_url = keycloak_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.token_endpoint = (
            f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
        )

    def get_token(self) -> str:
        """Get access token using password grant flow.

        Returns:
            str: Access token.

        Raises:
            Exception: If unable to obtain token.
        """
        if not self.username or not self.password:
            raise ValueError("Username and password required for password grant")

        payload = {
            "client_id": self.client_id,
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }

        if self.client_secret:
            payload["client_secret"] = self.client_secret

        try:
            response = requests.post(self.token_endpoint, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            print("----- Keycloak Token Response -----")
            print(token_data)
            print("----- End of Keycloak Token Response -----")
            
            if "access_token" not in token_data:
                raise ValueError("No access_token in response")
            
            logger.info(f"Successfully obtained token for user: {self.username}")
            return token_data["access_token"]
        except Exception as e:
            logger.error(f"Failed to obtain token from Keycloak: {e}")
            raise

    def get_client_credentials_token(self) -> str:
        """Get access token using client credentials grant flow.

        Returns:
            str: Access token.

        Raises:
            Exception: If unable to obtain token.
        """
        if not self.client_secret:
            raise ValueError("Client secret required for client credentials grant")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        try:
            response = requests.post(self.token_endpoint, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            
            if "access_token" not in token_data:
                raise ValueError("No access_token in response")
            
            logger.info("Successfully obtained client credentials token")
            return token_data["access_token"]
        except Exception as e:
            logger.error(f"Failed to obtain client credentials token: {e}")
            raise
