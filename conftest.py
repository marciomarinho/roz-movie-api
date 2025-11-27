"""Pytest configuration."""
import sys
from pathlib import Path

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session", autouse=True)
def disable_api_key_for_tests():
    """Disable API key validation for tests by setting empty API_KEY."""
    import os
    os.environ["API_KEY"] = ""
    # Clear the cached settings so it reloads with the new env var
    from app.core.config import get_settings
    get_settings.cache_clear()

