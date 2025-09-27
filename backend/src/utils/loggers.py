import sys
from pathlib import Path
from loguru import logger
from src.config.settings import config

# Remove default logger
logger.remove()

# Create logs directory
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logger based on settings
log_level = config.LOG_LEVEL

# Console logging with color
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=log_level
)

# File logging (more detailed)
logger.add(
    LOG_DIR / "reddit_audio_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # New file each day
    retention="7 days",  # Keep logs for 7 days
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",  # File logs are more detailed
    backtrace=True,
    diagnose=True
)

# Create a function to get logger for specific modules


def get_logger(name: str):
    """Get a logger instance for a specific module"""
    return logger.bind(module=name)


# Export the main logger
__all__ = ['logger', 'get_logger']
