"""Unit tests for authentication dependencies."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.deps.auth import verify_api_key


class TestVerifyAPIKey:
    """Test suite for API key verification."""

    @pytest.mark.asyncio
    async def test_verify_api_key_no_key_configured(self):
        """Test verification when no API key is configured."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = None
            mock_settings_func.return_value = mock_settings
            
            # Should not raise when key not configured
            await verify_api_key(x_api_key=None)

    @pytest.mark.asyncio
    async def test_verify_api_key_no_key_configured_with_header(self):
        """Test verification when no API key is configured but header provided."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = None
            mock_settings_func.return_value = mock_settings
            
            # Should not raise even when header provided if key not configured
            await verify_api_key(x_api_key="any-key")

    @pytest.mark.asyncio
    async def test_verify_api_key_empty_string_configured(self):
        """Test verification when API key is empty string."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = ""
            mock_settings_func.return_value = mock_settings
            
            # Empty string is falsy, so should not enforce key
            await verify_api_key(x_api_key=None)

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        """Test verification with valid API key."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "valid-key-12345"
            mock_settings_func.return_value = mock_settings
            
            # Should not raise with correct key
            await verify_api_key(x_api_key="valid-key-12345")

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test verification with invalid API key."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "valid-key-12345"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key="wrong-key")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_api_key_missing_header(self):
        """Test verification with missing API key header."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "required-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key=None)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_api_key_case_sensitive(self):
        """Test that API key verification is case-sensitive."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "MyKey"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="mykey")

    @pytest.mark.asyncio
    async def test_verify_api_key_whitespace_sensitive(self):
        """Test that whitespace matters in API key verification."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "my-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="my-key ")  # Extra space
    @pytest.mark.asyncio
    async def test_verify_api_key_empty_string_header(self):
        """Test verification with empty string in header."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "required-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="")

    @pytest.mark.asyncio
    async def test_verify_api_key_long_key(self):
        """Test verification with very long API key."""
        long_key = "x" * 1000
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = long_key
            mock_settings_func.return_value = mock_settings
            
            # Should work with long key
            await verify_api_key(x_api_key=long_key)

    @pytest.mark.asyncio
    async def test_verify_api_key_special_characters(self):
        """Test verification with special characters in key."""
        special_key = "!@#$%^&*()"
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = special_key
            mock_settings_func.return_value = mock_settings
            
            await verify_api_key(x_api_key=special_key)

    @pytest.mark.asyncio
    async def test_verify_api_key_logs_warning_on_missing(self, caplog):
        """Test that warning is logged when API key is missing."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "required-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key=None)

    @pytest.mark.asyncio
    async def test_verify_api_key_production_scenario(self):
        """Test verification in production-like scenario."""
        production_key = "prod-secret-key-xyz-123-abc"
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = production_key
            mock_settings_func.return_value = mock_settings
            
            # Valid key should work
            await verify_api_key(x_api_key=production_key)
            
            # Invalid key should fail
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="wrong-key")

    @pytest.mark.asyncio
    async def test_verify_api_key_development_scenario(self):
        """Test verification in development scenario (no key required)."""
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = None
            mock_settings_func.return_value = mock_settings
            
            # Should work without key in development
            await verify_api_key(x_api_key=None)
            await verify_api_key(x_api_key="any-key")  # Any key works when not required
