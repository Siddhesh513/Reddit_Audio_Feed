#!/usr/bin/env python3
"""Test that audio generation is fixed"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.audio_generator import get_audio_generator
from src.utils.loggers import logger


def test_fixed_audio():
    """Test audio generation with problematic text"""
    
    test_post = {
        'id': 'test_fix',
        'title': 'TIL rolling your tongue like a taco is NOT a genetic trait',
        'selftext': '',
        'subreddit': 'todayilearned',
        'author': 'testuser',
        'score': 1000
    }
    
    logger.info("Testing fixed audio generation...")
    
    # Generate audio
    generator = get_audio_generator('gtts')
    result = generator.generate_from_post(test_post, force_regenerate=True)
    
    if result.get('success'):
        logger.success(f"✅ Audio generated: {result['filename']}")
        logger.info(f"Play it with: afplay backend/data/audio/{result['filename']}")
    else:
        logger.error(f"Failed: {result.get('error')}")


if __name__ == "__main__":
    test_fixed_audio()
