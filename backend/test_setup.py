#!/usr/bin/env python3
"""Test configuration and logging setup"""

from src.utils.loggers import logger, get_logger
from src.config.settings import config
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_config():
    """Test configuration loading"""
    logger.info("Testing configuration...")

    try:
        config.validate()
        logger.success("✅ Configuration validated successfully!")

        logger.info(f"Reddit Client ID: {config.REDDIT_CLIENT_ID[:7]}...")
        logger.info(f"Raw data directory: {config.DATA_RAW_PATH}")
        logger.info(f"Processed data directory: {config.DATA_PROCESSED_PATH}")
        logger.info(f"Audio data directory: {config.DATA_AUDIO_PATH}")
        logger.info(f"Debug mode: {config.DEBUG}")
        logger.info(f"Log level: {config.LOG_LEVEL}")

    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False

    return True


def test_logging():
    """Test logging system"""
    test_logger = get_logger("test_module")

    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error(
        "This is an error message (not a real error, just testing)")
    test_logger.success("This is a success message")

    return True


if __name__ == "__main__":
    logger.info("Starting setup tests...")

    # Test configuration
    if test_config():
        logger.success("Configuration test passed!")

    # Test logging
    if test_logging():
        logger.success("Logging test passed!")

    logger.info("✅ All setup tests completed!")
