#!/usr/bin/env python
"""Quick test to verify AUTH_ENABLED is being read."""
import os
os.environ["AUTH_ENABLED"] = "false"

from app.core.config import get_settings
s = get_settings()
print(f"auth_enabled={s.auth_enabled}")
print(f"type={type(s.auth_enabled)}")
