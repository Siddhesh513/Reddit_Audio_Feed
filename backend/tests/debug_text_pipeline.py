#!/usr/bin/env python3
"""Debug text processing pipeline to see what's being sent to TTS"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.reddit_service import get_reddit_client
from src.services.text_processor import get_text_processor
from src.services.content_filter import get_content_filter
from src.services.tts_preprocessor import get_tts_preprocessor
from src.utils.loggers import logger


def debug_text_pipeline():
    """Debug each step of text processing"""
    logger.info("="*70)
    logger.info("DEBUGGING TEXT PIPELINE - STEP BY STEP")
    logger.info("="*70)
    
    # Fetch a real Reddit post
    reddit = get_reddit_client()
    posts = reddit.fetch_subreddit_posts("todayilearned", "hot", 1)
    
    if not posts:
        logger.error("No posts fetched")
        return
    
    post = posts[0]
    
    # Step 1: Show raw Reddit data
    logger.info("\n" + "="*50)
    logger.info("STEP 1: RAW REDDIT DATA")
    logger.info("="*50)
    logger.info(f"Title: {post['title']}")
    logger.info(f"Selftext: {post.get('selftext', 'NO BODY TEXT')[:200]}")
    
    # Step 2: After text processor
    text_processor = get_text_processor()
    processed = text_processor.process_post(post)
    
    logger.info("\n" + "="*50)
    logger.info("STEP 2: AFTER TEXT PROCESSOR")
    logger.info("="*50)
    logger.info(f"Processed Title: {processed['processed_title']}")
    logger.info(f"Processed Body: {processed.get('processed_body', 'NO BODY')[:200]}")
    logger.info(f"TTS Text: {processed['tts_text'][:300]}")
    
    # Step 3: After content filter
    content_filter = get_content_filter()
    filtered = content_filter.filter_post(processed)
    
    logger.info("\n" + "="*50)
    logger.info("STEP 3: AFTER CONTENT FILTER")
    logger.info("="*50)
    logger.info(f"Filtered TTS: {filtered['tts_text'][:300]}")
    
    # Step 4: After TTS preprocessor
    tts_preprocessor = get_tts_preprocessor()
    final_text = tts_preprocessor.preprocess_for_tts(filtered['tts_text'])
    
    logger.info("\n" + "="*50)
    logger.info("STEP 4: FINAL TEXT SENT TO gTTS")
    logger.info("="*50)
    logger.info(f"FINAL TEXT:\n{final_text[:500]}")
    
    # Show what might be causing issues
    logger.info("\n" + "="*50)
    logger.info("POTENTIAL ISSUES FOUND")
    logger.info("="*50)
    
    # Check for SSML tags
    if '<' in final_text and '>' in final_text:
        logger.warning("⚠️ SSML tags found in text - gTTS doesn't support these!")
        import re
        tags = re.findall(r'<[^>]+>', final_text)
        logger.info(f"Tags found: {tags[:5]}")
    
    # Check for special characters
    special_chars = [char for char in final_text if ord(char) > 127]
    if special_chars:
        logger.warning(f"⚠️ Special Unicode characters found: {set(special_chars)}")
    
    # Check for Reddit artifacts
    reddit_patterns = ['[', ']', '(', ')', 'http', 'www', '/r/', '/u/', 'edit:', 'Edit:']
    for pattern in reddit_patterns:
        if pattern in final_text:
            logger.warning(f"⚠️ Reddit artifact found: '{pattern}'")
    
    # Save the text for inspection
    debug_file = Path('debug_tts_text.txt')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write("RAW REDDIT TITLE:\n")
        f.write(post['title'] + "\n\n")
        f.write("RAW REDDIT BODY:\n")
        f.write(post.get('selftext', 'NO BODY') + "\n\n")
        f.write("="*50 + "\n")
        f.write("FINAL TEXT SENT TO TTS:\n")
        f.write(final_text)
    
    logger.info(f"\n💾 Full text saved to: {debug_file}")
    
    return final_text


def test_specific_problem_text():
    """Test specific problematic text patterns"""
    logger.info("\n" + "="*70)
    logger.info("TESTING SPECIFIC PROBLEM PATTERNS")
    logger.info("="*70)
    
    problem_texts = [
        "This has <break time='0.5s'/> SSML tags",
        "URLs like https://example.com should be removed",
        "Reddit stuff: r/python and u/spez and [deleted]",
        "Special chars: — … " " €",
        "Numbers: $50, 3:30 PM, 1st place, 99%",
    ]
    
    text_processor = get_text_processor()
    tts_preprocessor = get_tts_preprocessor()
    
    for text in problem_texts:
        logger.info(f"\nOriginal: {text}")
        
        # Process through pipeline
        cleaned = text_processor.clean_text(text)
        final = tts_preprocessor.preprocess_for_tts(cleaned)
        
        logger.info(f"Final:    {final}")
        
        # Show what changed
        if text != final:
            logger.success("✅ Text was modified")
        else:
            logger.warning("⚠️ Text unchanged")


if __name__ == "__main__":
    # Debug the pipeline
    final_text = debug_text_pipeline()
    
    # Test specific patterns
    test_specific_problem_text()
    
    logger.info("\n" + "="*70)
    logger.info("Check 'debug_tts_text.txt' to see exactly what's being sent to TTS")
    logger.info("="*70)
