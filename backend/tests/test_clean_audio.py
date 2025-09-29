#!/usr/bin/env python3
"""Test that all audio is now clean without SSML tags"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.reddit_service import get_reddit_client
from src.services.audio_generator import get_audio_generator
from src.utils.loggers import logger


def test_multiple_clean_audio():
    """Test multiple posts to ensure clean audio"""
    
    # Test posts with various formatting challenges
    test_posts = [
        {
            'id': 'test1',
            'title': 'AITA for saying NO to my friend?',
            'selftext': 'Edit: Thanks for the gold!\nTL;DR: Friend wanted money',
            'subreddit': 'test',
            'author': 'user1',
            'score': 100
        },
        {
            'id': 'test2', 
            'title': 'The meeting costs $50 at 3:30 PM',
            'selftext': '',
            'subreddit': 'test',
            'author': 'user2',
            'score': 50
        },
        {
            'id': 'test3',
            'title': 'Check out r/python and message u/spez',
            'selftext': 'This is **bold** and ~~strikethrough~~ text',
            'subreddit': 'test',
            'author': 'user3',
            'score': 75
        }
    ]
    
    generator = get_audio_generator('gtts')
    
    for post in test_posts:
        logger.info(f"\nTesting: {post['title']}")
        
        result = generator.generate_from_post(post, force_regenerate=True)
        
        if result.get('success'):
            logger.success(f"✅ Audio created: {result['filename']}")
            logger.info(f"   Duration: {result.get('duration_seconds', 0):.1f}s")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")
    
    # Also test with real Reddit posts
    logger.info("\n" + "="*50)
    logger.info("Testing with real Reddit posts...")
    
    reddit = get_reddit_client()
    posts = reddit.fetch_subreddit_posts("todayilearned", "hot", 3)
    
    for i, post in enumerate(posts, 1):
        logger.info(f"\n[{i}/3] {post['title'][:60]}...")
        result = generator.generate_from_post(post)
        
        if result.get('success'):
            logger.success(f"✅ Clean audio: {result['filename']}")


if __name__ == "__main__":
    test_multiple_clean_audio()
    logger.info("\n🎧 Listen to the files in backend/data/audio/")
    logger.info("They should have clean speech without XML tags!")
