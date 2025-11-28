"""Pytest configuration for UNIT TESTS ONLY.

Integration tests have completely separate configuration in tests/integration/conftest.py
and are run independently to avoid any shared state or fixture pollution.
"""
import logging
import os
import sys
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_runtest_setup(item):
    """Reset environment before each test."""
    # If this is an integration test, clear any unit test settings
    if "tests/integration" in str(item.fspath):
        # Integration tests should NOT have AUTH_ENABLED set
        os.environ.pop("AUTH_ENABLED", None)
        try:
            from app.core.config import get_settings
            if hasattr(get_settings, "cache_clear"):
                get_settings.cache_clear()
        except ImportError:
            pass


@pytest.fixture(autouse=True)
def unit_test_isolation(request):
    """Setup isolated unit test environment.
    
    This fixture ensures each unit test runs with:
    - Authentication disabled (AUTH_ENABLED=false)
    - No API key in environment
    - Fresh settings cache
    """
    # Only apply to unit tests
    if "tests/unit" not in str(request.fspath):
        yield
        return
    
    # Disable authentication for unit tests - we test business logic in isolation
    os.environ.pop("API_KEY", None)
    os.environ["AUTH_ENABLED"] = "false"
    
    try:
        from app.core.config import get_settings
        # Clear the cache BEFORE the test runs
        if hasattr(get_settings, "cache_clear"):
            get_settings.cache_clear()
        
        # Force a reload to ensure settings are fresh
        settings = get_settings()
        assert settings.auth_enabled is False, f"AUTH_ENABLED not properly set to False, got: {settings.auth_enabled}"
    except Exception as e:
        logger.error(f"Failed to set unit test isolation: {e}")
        raise
    
    yield
    
    # Cleanup after each test
    os.environ.pop("API_KEY", None)
    os.environ.pop("AUTH_ENABLED", None)
    try:
        from app.core.config import get_settings
        if hasattr(get_settings, "cache_clear"):
            get_settings.cache_clear()
    except ImportError:
        pass

