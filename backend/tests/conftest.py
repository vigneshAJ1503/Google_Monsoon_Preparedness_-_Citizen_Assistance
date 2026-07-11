"""
Pytest configuration and environment overrides.
"""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

# Set environment to testing
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://monsoonprep:monsoonprep_dev_password@localhost:5432/monsoonprep_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
