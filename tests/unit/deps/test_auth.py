from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.deps.auth import verify_api_key


class TestVerifyAPIKey:

    @pytest.mark.asyncio
    async def test_verify_api_key_no_key_configured(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = None
            mock_settings_func.return_value = mock_settings
            
            # Should not raise when key not configured
            await verify_api_key(x_api_key=None)

    @pytest.mark.asyncio
    async def test_verify_api_key_no_key_configured_with_header(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = None
            mock_settings_func.return_value = mock_settings
            
            # Should not raise even when header provided if key not configured
            await verify_api_key(x_api_key="any-key")

    @pytest.mark.asyncio
    async def test_verify_api_key_empty_string_configured(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = ""
            mock_settings_func.return_value = mock_settings
            
            # Empty string is falsy, so should not enforce key
            await verify_api_key(x_api_key=None)

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "valid-key-12345"
            mock_settings_func.return_value = mock_settings
            
            # Should not raise with correct key
            await verify_api_key(x_api_key="valid-key-12345")

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "valid-key-12345"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key="wrong-key")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_api_key_missing_header(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "required-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key=None)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_api_key_case_sensitive(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "MyKey"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="mykey")

    @pytest.mark.asyncio
    async def test_verify_api_key_whitespace_sensitive(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "my-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="my-key ")  # Extra space
    @pytest.mark.asyncio
    async def test_verify_api_key_empty_string_header(self):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "required-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key="")

    @pytest.mark.asyncio
    async def test_verify_api_key_long_key(self):
        long_key = "x" * 1000
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = long_key
            mock_settings_func.return_value = mock_settings
            
            # Should work with long key
            await verify_api_key(x_api_key=long_key)

    @pytest.mark.asyncio
    async def test_verify_api_key_special_characters(self):
        special_key = "!@#$%^&*()"
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = special_key
            mock_settings_func.return_value = mock_settings
            
            await verify_api_key(x_api_key=special_key)

    @pytest.mark.asyncio
    async def test_verify_api_key_logs_warning_on_missing(self, caplog):
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = "required-key"
            mock_settings_func.return_value = mock_settings
            
            with pytest.raises(HTTPException):
                await verify_api_key(x_api_key=None)

    @pytest.mark.asyncio
    async def test_verify_api_key_production_scenario(self):
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
        with patch("app.deps.auth.get_settings") as mock_settings_func:
            mock_settings = MagicMock()
            mock_settings.api_key = None
            mock_settings_func.return_value = mock_settings
            
            # Should work without key in development
            await verify_api_key(x_api_key=None)
            await verify_api_key(x_api_key="any-key")  # Any key works when not required
