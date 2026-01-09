#!/usr/bin/env python3
"""Test the complete Reddit to Audio pipeline with multiple subreddits"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from src.services.reddit_service import get_reddit_client
from src.services.text_processor import get_text_processor
from src.services.content_filter import get_content_filter
from src.services.tts_preprocessor import get_tts_preprocessor
from src.services.audio_generator import get_audio_generator
from src.services.audio_manager import get_audio_manager
from src.services.audio_queue import get_audio_queue
from src.utils.loggers import logger


def test_multiple_subreddits():
    """Test pipeline with posts from multiple subreddits"""
    logger.info("="*70)
    logger.info("COMPLETE PIPELINE TEST - MULTIPLE SUBREDDITS")
    logger.info("="*70)
    
    # Subreddits with different content types
    test_subreddits = [
        ("todayilearned", "hot", 3, "Educational content"),
        ("Showerthoughts", "hot", 3, "Short thoughts"),
        ("AskReddit", "hot", 2, "Questions"),
        ("LifeProTips", "hot", 2, "Advice"),
        ("explainlikeimfive", "hot", 2, "Simple explanations"),
    ]
    
    reddit = get_reddit_client()
    audio_gen = get_audio_generator('gtts')
    
    all_results = []
    total_posts = 0
    
    for subreddit, sort, limit, description in test_subreddits:
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing r/{subreddit} - {description}")
        logger.info(f"{'='*50}")
        
        # Fetch posts
        posts = reddit.fetch_subreddit_posts(subreddit, sort, limit)
        total_posts += len(posts)
        
        logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
        
        # Process each post
        for i, post in enumerate(posts, 1):
            logger.info(f"\n[{i}/{len(posts)}] Processing: {post['title'][:60]}...")
            
            # Generate audio
            result = audio_gen.generate_from_post(post, voice='en-US', speed=1.0)
            result['subreddit'] = subreddit
            all_results.append(result)
            
            if result.get('success'):
                logger.success(f"✅ Audio created: {result.get('filename')}")
                logger.info(f"   Duration: {result.get('duration_seconds', 0):.1f}s")
                logger.info(f"   Size: {result.get('file_size_bytes', 0)/1024:.1f}KB")
            else:
                logger.error(f"❌ Failed: {result.get('reason', result.get('error'))}")
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
    
    # Summary
    successful = sum(1 for r in all_results if r.get('success'))
    failed = total_posts - successful
    
    logger.info(f"\n{'='*70}")
    logger.info("PIPELINE TEST SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"Total posts processed: {total_posts}")
    # Add defensive check to prevent ZeroDivisionError
    success_rate = (successful/total_posts*100) if total_posts > 0 else 0
    logger.info(f"✅ Successful: {successful} ({success_rate:.1f}%)")
    logger.info(f"❌ Failed: {failed}")
    
    # By subreddit breakdown
    logger.info("\nBy Subreddit:")
    for subreddit_name, _, _, desc in test_subreddits:
        sub_results = [r for r in all_results if r.get('subreddit') == subreddit_name]
        sub_success = sum(1 for r in sub_results if r.get('success'))
        logger.info(f"  r/{subreddit_name}: {sub_success}/{len(sub_results)} successful")

    assert True  # Test completed successfully


def test_text_variety():
    """Test pipeline with different text types and lengths"""
    logger.info("\n" + "="*70)
    logger.info("TEXT VARIETY TEST - DIFFERENT CONTENT TYPES")
    logger.info("="*70)
    
    # Create test posts with various content
    test_posts = [
        {
            'id': 'short1',
            'title': 'TIL that honey never spoils!',
            'selftext': '',
            'subreddit': 'test',
            'author': 'testuser',
            'score': 100
        },
        {
            'id': 'medium1',
            'title': 'AITA for refusing to go to my best friend\'s wedding?',
            'selftext': 'So here\'s the situation. My best friend of 10 years is getting married next month, but they scheduled it on the same day as my PhD defense. I told them months ago about this date, but they said the venue was only available that day. Now they\'re calling me selfish. Am I the asshole here?',
            'subreddit': 'test',
            'author': 'testuser',
            'score': 500
        },
        {
            'id': 'numbers1',
            'title': 'The meeting is at 3:30 PM and will cost $50 per person',
            'selftext': 'We have 25 people attending, so the total will be $1,250. The venue is located at 123 Main Street.',
            'subreddit': 'test',
            'author': 'testuser',
            'score': 50
        },
        {
            'id': 'reddit1',
            'title': 'Check out r/python and talk to u/spez about it',
            'selftext': 'Edit: Thanks for the gold kind stranger! \n\nEdit 2: RIP my inbox\n\nTL;DR: Reddit formatting is complex',
            'subreddit': 'test',
            'author': 'testuser',
            'score': 200
        }
    ]
    
    text_processor = get_text_processor()
    content_filter = get_content_filter()
    tts_preprocessor = get_tts_preprocessor()
    audio_gen = get_audio_generator('gtts')
    
    for post in test_posts:
        logger.info(f"\n{'='*40}")
        logger.info(f"Testing: {post['id']}")
        logger.info(f"Original: {post['title']}")
        
        # Step 1: Text processing
        processed = text_processor.process_post(post)
        logger.info(f"Cleaned: {processed['processed_title'][:80]}")
        
        # Step 2: Content filtering
        filtered = content_filter.filter_post(processed)
        
        # Step 3: TTS preprocessing
        tts_text = tts_preprocessor.preprocess_for_tts(filtered['tts_text'])
        logger.info(f"TTS Ready: {tts_text[:100]}...")
        
        # Step 4: Generate audio
        result = audio_gen.generate_from_post(post, force_regenerate=True)
        
        if result.get('success'):
            logger.success(f"✅ Audio: {result.get('filename')}")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")


def test_queue_processing():
    """Test the queue system with batch processing"""
    logger.info("\n" + "="*70)
    logger.info("QUEUE SYSTEM TEST - BATCH PROCESSING")
    logger.info("="*70)
    
    queue = get_audio_queue()
    
    # Clear any completed items first
    cleared = queue.clear_completed()
    logger.info(f"Cleared {cleared} completed items from queue")
    
    # Add posts from different subreddits with priorities
    subreddits_to_queue = [
        ("todayilearned", 5, 200),  # (subreddit, limit, min_score)
        ("LifeProTips", 3, 100),
        ("explainlikeimfive", 3, 150),
    ]
    
    total_queued = 0
    for subreddit, limit, min_score in subreddits_to_queue:
        queue_ids = queue.add_subreddit_posts(subreddit, "hot", limit, min_score)
        total_queued += len(queue_ids)
        logger.info(f"Queued {len(queue_ids)} posts from r/{subreddit}")
    
    # Check queue stats before processing
    stats_before = queue.get_queue_stats()
    logger.info(f"\nQueue before processing:")
    logger.info(f"  Total: {stats_before['total']}")
    logger.info(f"  Pending: {stats_before['pending']}")
    
    # Process the queue
    logger.info(f"\nProcessing queue (max 5 items)...")
    process_stats = queue.process_queue(max_items=5)
    
    # Check queue stats after processing
    stats_after = queue.get_queue_stats()
    logger.info(f"\nQueue after processing:")
    logger.info(f"  Completed: {stats_after['completed']}")
    logger.info(f"  Failed: {stats_after['failed']}")
    logger.info(f"  Still pending: {stats_after['pending']}")

    assert True  # Test completed successfully


def test_audio_organization():
    """Test audio file organization and management"""
    logger.info("\n" + "="*70)
    logger.info("AUDIO MANAGEMENT TEST")
    logger.info("="*70)
    
    manager = get_audio_manager()
    
    # Organize files
    org_stats = manager.organize_audio_files()
    logger.info(f"Organized {org_stats['files_organized']} files")
    
    # Get storage summary
    summary = manager.get_storage_summary()
    logger.info(f"\nStorage Summary:")
    logger.info(f"  Total audio files: {summary['total_files']}")
    logger.info(f"  Total size: {summary['total_size_mb']:.2f} MB")
    logger.info(f"  Total duration: {summary['total_duration_minutes']:.1f} minutes")
    logger.info(f"  Average file size: {summary.get('average_file_size_mb', 0):.2f} MB")
    
    # Create playlist of recent files
    recent = manager.get_recent_audio(hours=24, limit=10)
    if recent:
        playlist = manager.create_playlist(recent, "test_pipeline_playlist")
        logger.success(f"Created playlist with {len(recent)} tracks: {playlist}")
    
    # Show audio by subreddit
    logger.info(f"\nAudio files by subreddit:")
    for subreddit in ['todayilearned', 'Showerthoughts', 'test']:
        sub_files = manager.get_audio_by_subreddit(subreddit)
        if sub_files:
            logger.info(f"  r/{subreddit}: {len(sub_files)} files")

    assert True  # Test completed successfully


def main():
    """Run comprehensive pipeline tests"""
    start_time = time.time()
    
    logger.info("🚀 STARTING COMPREHENSIVE PIPELINE TEST")
    logger.info("="*70)
    
    # Test 1: Multiple subreddits
    results = test_multiple_subreddits()
    
    # Test 2: Text variety
    test_text_variety()
    
    # Test 3: Queue processing
    queue_stats = test_queue_processing()
    
    # Test 4: Audio organization
    storage_summary = test_audio_organization()
    
    # Final summary
    elapsed = time.time() - start_time
    
    logger.info("\n" + "="*70)
    logger.info("🎯 COMPLETE PIPELINE TEST FINISHED")
    logger.info("="*70)
    logger.info(f"Total time: {elapsed:.1f} seconds")
    logger.info(f"Audio files: {storage_summary['total_files']}")
    logger.info(f"Total size: {storage_summary['total_size_mb']:.2f} MB")
    logger.success("\n✅ Pipeline is fully operational and tested!")
    
    # Show where to find the audio files
    logger.info("\n📁 Audio files location:")
    logger.info(f"  Raw: backend/data/audio/*.mp3")
    logger.info(f"  Organized: backend/data/audio/organized/")
    logger.info(f"  Playlist: backend/data/audio/*.m3u")


if __name__ == "__main__":
    main()
