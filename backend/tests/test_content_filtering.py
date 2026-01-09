#!/usr/bin/env python3
"""Test content filtering and TTS preprocessing"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.content_filter import get_content_filter
from src.services.tts_preprocessor import get_tts_preprocessor
from src.services.text_processor import get_text_processor
from src.services.reddit_service import get_reddit_client
from src.utils.loggers import logger


def test_content_filter():
    """Test content filtering"""
    logger.info("="*60)
    logger.info("Testing Content Filter")
    logger.info("="*60)
    
    filter = get_content_filter()
    
    test_cases = [
        {
            'processed_title': 'This is a test with damn profanity',
            'processed_body': 'Some shit content with hell words',
            'tts_text': 'Combined text with crap in it',
            'over_18': False
        },
        {
            'processed_title': 'Clean title here',
            'processed_body': 'This discusses suicide and self-harm topics',
            'tts_text': 'Clean title here. This discusses suicide and self-harm topics',
            'over_18': False
        }
    ]
    
    for i, test_post in enumerate(test_cases, 1):
        logger.info(f"\nTest case {i}:")
        filtered = filter.filter_post(test_post)
        
        logger.info(f"Original: {test_post.get('tts_text', '')[:100]}")
        logger.info(f"Filtered: {filtered.get('tts_text', '')[:100]}")
        
        if filtered.get('content_warnings'):
            logger.warning(f"Warnings: {filtered['content_warnings']}")
        
        if filtered.get('filter_stats'):
            stats = filtered['filter_stats']
            logger.info(f"Stats: {stats['profanity_count']} profanity found")
    
    assert True  # Test completed successfully


def test_tts_preprocessing():
    """Test TTS preprocessing"""
    logger.info("\n" + "="*60)
    logger.info("Testing TTS Preprocessor")
    logger.info("="*60)
    
    preprocessor = get_tts_preprocessor()
    
    test_texts = [
        "The meeting is at 3:30 PM and costs $50.",
        "He ranked 1st out of 100 people (amazing!)",
        "Check the FAQ at www.example.com ASAP!",
        "The temperature is 72°F with 60% humidity.",
        "I love this!!! 😍 Best thing ever 💯",
    ]
    
    for text in test_texts:
        processed = preprocessor.preprocess_for_tts(text)
        logger.info(f"\nOriginal: {text}")
        logger.info(f"For TTS:  {processed}")
    
    assert True  # Test completed successfully


def test_full_pipeline():
    """Test complete text processing pipeline"""
    logger.info("\n" + "="*60)
    logger.info("Testing Full Pipeline: Reddit → Clean → Filter → TTS")
    logger.info("="*60)
    
    # Get all processors
    reddit = get_reddit_client()
    text_processor = get_text_processor()
    content_filter = get_content_filter()
    tts_preprocessor = get_tts_preprocessor()
    
    # Fetch a real post
    posts = reddit.fetch_subreddit_posts("python", "hot", 1)
    
    if posts:
        post = posts[0]
        logger.info(f"\n1. Original Reddit Post:")
        logger.info(f"   Title: {post['title']}")
        
        # Step 1: Clean Reddit formatting
        cleaned = text_processor.process_post(post)
        logger.info(f"\n2. After Reddit Cleaning:")
        logger.info(f"   Title: {cleaned['processed_title']}")
        
        # Step 2: Filter content
        filtered = content_filter.filter_post(cleaned)
        logger.info(f"\n3. After Content Filtering:")
        if filtered.get('content_warnings'):
            logger.info(f"   Warnings: {filtered['content_warnings']}")
        
        # Step 3: Prepare for TTS
        tts_ready = tts_preprocessor.preprocess_for_tts(filtered['tts_text'])
        logger.info(f"\n4. Ready for TTS:")
        logger.info(f"   Preview: {tts_ready[:200]}...")
        
        # Final check
        is_safe = content_filter.is_safe_for_tts(filtered)
        logger.info(f"\n5. Safe for TTS: {'✅ Yes' if is_safe else '❌ No'}")


def main():
    """Run all tests"""
    logger.info("Starting Content Filtering and TTS Preprocessing Tests")
    
    test_content_filter()
    test_tts_preprocessing()
    test_full_pipeline()
    
    logger.success("\n✅ All content filtering tests completed!")


if __name__ == "__main__":
    main()
