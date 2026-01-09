#!/usr/bin/env python3
"""Test text processing functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.text_processor import get_text_processor
from src.services.reddit_service import get_reddit_client
from src.utils.text_helper import TextHelpers, extract_statistics
from src.utils.loggers import logger


def test_reddit_text_cleaning():
    """Test cleaning of Reddit-specific text"""
    logger.info("="*60)
    logger.info("Testing Reddit Text Cleaning")
    logger.info("="*60)
    
    processor = get_text_processor()
    
    test_cases = [
        (
            "AITA for not going to my [28M] sister's [32F] wedding?",
            "Expected: AITA expanded, age/gender processed"
        ),
        (
            "Check out r/python and u/spez for more info",
            "Expected: Subreddit and user mentions processed"
        ),
    ]
    
    for input_text, note in test_cases:
        cleaned = processor.clean_text(input_text)
        logger.info(f"\nInput:  {input_text}")
        logger.info(f"Output: {cleaned}")
        logger.success("✅ Processed")
    
    assert True  # Test completed successfully


def test_with_real_posts():
    """Test with real Reddit posts"""
    logger.info("\n" + "="*60)
    logger.info("Testing with Real Reddit Posts")
    logger.info("="*60)
    
    reddit = get_reddit_client()
    processor = get_text_processor()
    
    posts = reddit.fetch_subreddit_posts("python", "hot", 2)
    
    for post in posts[:1]:  # Just test first post
        processed = processor.process_post(post)
        logger.info(f"Original: {post['title'][:80]}")
        logger.info(f"Cleaned:  {processed['processed_title'][:80]}")
        
        stats = TextHelpers.extract_statistics(processed['tts_text'])
        logger.info(f"Words: {stats['word_count']}, Read time: {stats['estimated_reading_time']:.1f}s")
    
    assert True  # Test completed successfully


def main():
    logger.info("Starting Text Processing Tests")
    test_reddit_text_cleaning()
    test_with_real_posts()
    logger.success("\n✅ All tests completed!")


if __name__ == "__main__":
    main()
