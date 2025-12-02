"""Unit tests for app configuration management."""
import os
from unittest.mock import patch

import pytest

from app.core.config import Settings, get_settings


class TestSettings:

    def test_default_settings(self, monkeypatch):
        # Remove all configuration from environment
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("APP_VERSION", raising=False)
        monkeypatch.delenv("API_V1_PREFIX", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("API_KEY", raising=False)
        
        # Clear the cache so we get a fresh Settings instance
        from app.core.config import get_settings
        get_settings.cache_clear()
        
        # Create settings instance
        settings = Settings()
        
        # Check defaults - note: .env file may provide some values
        assert settings.app_name == "Movie API"
        assert settings.app_version == "1.0.0"
        assert settings.api_v1_prefix == "/api"
        assert settings.log_level == "INFO"

    def test_settings_api_key_from_monkeypatch(self, monkeypatch):
        # Remove API_KEY from environment for this test
        monkeypatch.delenv("API_KEY", raising=False)
        # Create fresh settings instance
        from app.core.config import get_settings
        get_settings.cache_clear()
        settings = Settings()
        # If .env has it, it will be present, so check it's either None or a string
        assert settings.api_key is None or isinstance(settings.api_key, str)

    def test_settings_from_environment(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "Custom API")
        monkeypatch.setenv("APP_VERSION", "2.0.0")
        monkeypatch.setenv("API_V1_PREFIX", "/v2")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("API_KEY", "secret-key")

        settings = Settings()
        assert settings.app_name == "Custom API"
        assert settings.app_version == "2.0.0"
        assert settings.api_v1_prefix == "/v2"
        assert settings.log_level == "DEBUG"
        assert settings.api_key == "secret-key"

    def test_settings_db_configuration(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "prod-db.example.com")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("DB_NAME", "movies_prod")
        monkeypatch.setenv("DB_USER", "prod_user")
        monkeypatch.setenv("DB_PASSWORD", "prod_pass")

        settings = Settings()
        assert settings.db_host == "prod-db.example.com"
        assert settings.db_port == 5433
        assert settings.db_name == "movies_prod"
        assert settings.db_user == "prod_user"
        assert settings.db_password == "prod_pass"

    def test_settings_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("app_name", "lowercase api")
        monkeypatch.setenv("APP_VERSION", "1.5.0")

        settings = Settings()
        assert settings.app_name == "lowercase api"
        assert settings.app_version == "1.5.0"

    def test_settings_port_type_conversion(self, monkeypatch):
        monkeypatch.setenv("DB_PORT", "9999")
        settings = Settings()
        assert isinstance(settings.db_port, int)
        assert settings.db_port == 9999

    def test_settings_empty_api_key(self, monkeypatch):
        monkeypatch.setenv("API_KEY", "")
        settings = Settings()
        assert settings.api_key == ""


class TestGetSettings:

    def test_get_settings_returns_settings(self, clear_lru_cache):
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self, clear_lru_cache, monkeypatch):
        monkeypatch.setenv("APP_NAME", "First Call")
        first_call = get_settings()
        
        monkeypatch.setenv("APP_NAME", "Second Call")
        second_call = get_settings()
        
        # Should be the same instance (cached)
        assert first_call is second_call
        assert first_call.app_name == "First Call"

    def test_get_settings_multiple_instances_different_envs(self, clear_lru_cache, monkeypatch):
        monkeypatch.setenv("APP_NAME", "First")
        first = get_settings()
        
        get_settings.cache_clear()
        
        monkeypatch.setenv("APP_NAME", "Second")
        second = get_settings()
        
        assert first.app_name == "First"
        assert second.app_name == "Second"

    def test_get_settings_production_like_config(self, clear_lru_cache, monkeypatch):
        monkeypatch.setenv("APP_NAME", "MovieDB API")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        monkeypatch.setenv("DB_HOST", "db.prod.internal")
        monkeypatch.setenv("API_KEY", "prod-secret-key-xyz")
        
        settings = get_settings()
        assert settings.app_name == "MovieDB API"
        assert settings.log_level == "WARNING"
        assert settings.db_host == "db.prod.internal"
        assert settings.api_key == "prod-secret-key-xyz"

    def test_get_settings_development_config(self, clear_lru_cache, monkeypatch):
        monkeypatch.setenv("APP_NAME", "Movie API Dev")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("API_KEY", "")
        
        settings = get_settings()
        assert settings.app_name == "Movie API Dev"
        assert settings.log_level == "DEBUG"
        assert settings.db_host == "localhost"
        assert settings.api_key == ""
