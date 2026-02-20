"""
Tests for config.py Settings class.
"""
import pytest
from unittest.mock import patch

from config import Settings


class TestSettings:
    """Tests for Settings class."""
    
    def test_redis_uri_without_password(self):
        """Test REDIS_URI computed field without password."""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0,
            REDIS_PASSWORD=None
        )
        
        assert settings.REDIS_URI == "redis://localhost:6379/0"
    
    def test_redis_uri_with_password(self):
        """Test REDIS_URI computed field with password."""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0,
            REDIS_PASSWORD="secret123"
        )
        
        assert settings.REDIS_URI == "redis://:secret123@localhost:6379/0"

