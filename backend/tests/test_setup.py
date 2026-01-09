#!/usr/bin/env python3
"""Test configuration and logging setup"""

import pytest
from src.utils.loggers import logger, get_logger
from src.config.settings import Config
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config(monkeypatch):
    """Test configuration loading"""
    logger.info("Testing configuration...")

    # Patch Config CLASS attributes (not instance)
    # Config.validate() is a classmethod that checks cls.REDDIT_CLIENT_ID, etc.
    monkeypatch.setattr(Config, "REDDIT_CLIENT_ID", "test_client_id_12345")
    monkeypatch.setattr(Config, "REDDIT_CLIENT_SECRET", "test_client_secret_67890")
    monkeypatch.setattr(Config, "REDDIT_USER_AGENT", "test_user_agent/1.0")

    try:
        Config.validate()
        logger.success("✅ Configuration validated successfully!")

        logger.info(f"Reddit Client ID: {Config.REDDIT_CLIENT_ID[:7]}...")
        logger.info(f"Raw data directory: {Config.DATA_RAW_PATH}")
        logger.info(f"Processed data directory: {Config.DATA_PROCESSED_PATH}")
        logger.info(f"Audio data directory: {Config.DATA_AUDIO_PATH}")
        logger.info(f"Debug mode: {Config.DEBUG}")
        logger.info(f"Log level: {Config.LOG_LEVEL}")

    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        pytest.fail(f"Configuration validation failed: {e}")

    assert True  # Test completed successfully


def test_logging():
    """Test logging system"""
    test_logger = get_logger("test_module")

    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error(
        "This is an error message (not a real error, just testing)")
    test_logger.success("This is a success message")

    assert True  # Test completed successfully


if __name__ == "__main__":
    logger.info("Starting setup tests...")

    # Test configuration
    if test_config():
        logger.success("Configuration test passed!")

    # Test logging
    if test_logging():
        logger.success("Logging test passed!")

    logger.info("✅ All setup tests completed!")
