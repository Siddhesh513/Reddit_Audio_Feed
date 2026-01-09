"""
System dependency checks for TTS functionality.

This module provides utilities to check if required system dependencies
are installed and available for TTS features like speed adjustment.
"""

import subprocess
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def check_ffmpeg_installed() -> bool:
    """
    Check if ffmpeg is installed and available.

    ffmpeg is required for audio speed adjustment via pydub.

    Returns:
        True if ffmpeg is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_pydub_available() -> bool:
    """
    Check if pydub library is installed.

    pydub is required for audio speed adjustment.

    Returns:
        True if pydub is available, False otherwise
    """
    try:
        import pydub
        return True
    except ImportError:
        return False


def get_tts_capabilities() -> Dict[str, bool]:
    """
    Get current TTS system capabilities.

    Checks for availability of TTS engines and audio processing dependencies.

    Returns:
        Dictionary with capability flags:
        {
            'gtts_available': bool,
            'speed_adjustment': bool,
            'ffmpeg_installed': bool,
            'pydub_available': bool
        }

    Example:
        >>> caps = get_tts_capabilities()
        >>> if caps['speed_adjustment']:
        ...     print("Speed adjustment is available")
    """
    capabilities = {
        'gtts_available': False,
        'speed_adjustment': False,
        'ffmpeg_installed': check_ffmpeg_installed(),
        'pydub_available': check_pydub_available()
    }

    # Check gTTS
    try:
        import gtts
        capabilities['gtts_available'] = True
    except ImportError:
        pass

    # Speed adjustment requires both pydub and ffmpeg
    capabilities['speed_adjustment'] = (
        capabilities['pydub_available'] and
        capabilities['ffmpeg_installed']
    )

    return capabilities


def log_tts_capabilities():
    """
    Log TTS system capabilities at startup.

    This provides visibility into which TTS features are available
    based on installed dependencies.
    """
    caps = get_tts_capabilities()

    logger.info("TTS System Capabilities:")
    logger.info(f"  - gTTS: {'✓' if caps['gtts_available'] else '✗'}")
    logger.info(f"  - Speed Adjustment: {'✓' if caps['speed_adjustment'] else '✗'}")
    logger.info(f"  - ffmpeg: {'✓' if caps['ffmpeg_installed'] else '✗'}")
    logger.info(f"  - pydub: {'✓' if caps['pydub_available'] else '✗'}")

    if not caps['speed_adjustment']:
        logger.warning(
            "Speed adjustment not available. Install pydub and ffmpeg for granular speed control."
        )
        if not caps['pydub_available']:
            logger.warning("  Install pydub: pip install pydub")
        if not caps['ffmpeg_installed']:
            logger.warning(
                "  Install ffmpeg:\n"
                "    macOS: brew install ffmpeg\n"
                "    Ubuntu: sudo apt-get install ffmpeg\n"
                "    Windows: Download from ffmpeg.org"
            )
