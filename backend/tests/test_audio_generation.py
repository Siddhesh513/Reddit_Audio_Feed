#!/usr/bin/env python3
"""Test audio generation functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.audio_generator import get_audio_generator
from src.services.reddit_service import get_reddit_client
from src.utils.loggers import logger


def test_tts_engines():
    """Test different TTS engines"""
    logger.info("="*60)
    logger.info("Testing TTS Engines")
    logger.info("="*60)
    
    # Test gTTS engine
    generator = get_audio_generator('gtts')
    
    # Get available voices
    voices = generator.engine.get_available_voices()
    logger.info(f"\nAvailable voices: {len(voices)}")
    for voice in voices[:3]:
        logger.info(f"  - {voice['id']}: {voice['name']}")
    
    # Test text validation
    test_text = "Hello, this is a test of the audio generation system."
    is_valid = generator.engine.validate_text(test_text)
    logger.info(f"\nText validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Estimate duration
    duration = generator.engine.estimate_duration(test_text)
    logger.info(f"Estimated duration: {duration:.1f} seconds")
    
    return True


def test_single_post_audio():
    """Test generating audio from a single post"""
    logger.info("\n" + "="*60)
    logger.info("Testing Single Post Audio Generation")
    logger.info("="*60)
    
    # Create a test post
    test_post = {
        'id': 'test123',
        'title': 'Test Post: Can AI generate good audio from Reddit posts?',
        'selftext': 'This is a test post to see if our TTS system works correctly. It should handle various types of content.',
        'subreddit': 'test',
        'author': 'testuser',
        'created_utc': '2024-01-01T12:00:00',
        'score': 100,
        'num_comments': 10
    }
    
    # Generate audio
    generator = get_audio_generator('gtts')
    result = generator.generate_from_post(test_post, voice='en-US', speed=1.0)
    
    if result.get('success'):
        logger.success(f"✅ Audio generated successfully!")
        logger.info(f"  File: {result.get('filename')}")
        logger.info(f"  Duration: {result.get('duration_seconds', 0):.1f}s")
        logger.info(f"  Size: {result.get('file_size_bytes', 0)/1024:.1f}KB")
    else:
        logger.error(f"❌ Audio generation failed: {result.get('error')}")
    
    return result.get('success', False)


def test_real_reddit_audio():
    """Test with real Reddit posts"""
    logger.info("\n" + "="*60)
    logger.info("Testing with Real Reddit Posts")
    logger.info("="*60)
    
    # Get Reddit posts
    reddit = get_reddit_client()
    posts = reddit.fetch_subreddit_posts("todayilearned", "hot", 3)
    
    if not posts:
        logger.warning("No posts fetched from Reddit")
        return False
    
    # Generate audio for posts
    generator = get_audio_generator('gtts')
    results = generator.generate_batch(posts, voice='en-US', speed=1.0)
    
    # Show results
    for i, result in enumerate(results, 1):
        if result.get('success'):
            logger.success(f"✅ Post {i}: {result.get('filename', 'unknown')}")
        else:
            logger.error(f"❌ Post {i}: {result.get('reason', result.get('error', 'Unknown error'))}")
    
    # Show statistics
    stats = generator.get_audio_stats()
    logger.info(f"\nAudio Generation Statistics:")
    logger.info(f"  Total files: {stats['total_audio_files']}")
    logger.info(f"  Total duration: {stats.get('total_duration_minutes', 0):.1f} minutes")
    logger.info(f"  Total size: {stats.get('total_size_mb', 0):.2f} MB")
    
    if stats['recent_files']:
        logger.info(f"  Recent files:")
        for file in stats['recent_files'][:3]:
            logger.info(f"    - {file}")
    
    return True


def main():
    """Run all audio generation tests"""
    logger.info("Starting Audio Generation Tests")
    
    # Test TTS engines
    test_tts_engines()
    
    # Test single post
    test_single_post_audio()
    
    # Test with real Reddit posts
    test_real_reddit_audio()
    
    logger.success("\n✅ All audio generation tests completed!")
    logger.info("\n📁 Check backend/data/audio/ for generated MP3 files")


if __name__ == "__main__":
    main()
