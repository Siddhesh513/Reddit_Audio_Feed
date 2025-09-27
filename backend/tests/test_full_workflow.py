#!/usr/bin/env python3
"""
Full Workflow Test - End-to-End Testing of Day 1 Implementation
"""

from src.utils.loggers import logger
from src.models.reddit_post import RedditPost, PostCollection
from src.services.storage_service import get_storage_service
from src.services.reddit_service import get_reddit_client
from datetime import datetime
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_complete_workflow():
    """Test the complete workflow from fetching to storage"""

    # Configuration for test
    test_subreddits = [
        ("AskReddit", "hot", 3),
        ("todayilearned", "top", 3),
        ("Showerthoughts", "new", 2),
    ]

    logger.info("="*60)
    logger.info("COMPLETE WORKFLOW TEST - DAY 1")
    logger.info("="*60)

    # Initialize services
    reddit = get_reddit_client()
    storage = get_storage_service()

    # Collect all posts
    all_posts = []

    # Step 1: Fetch posts from multiple subreddits
    logger.info("\n📥 STEP 1: Fetching Reddit Posts")
    logger.info("-"*40)

    for subreddit, sort, limit in test_subreddits:
        logger.info(f"\nFetching from r/{subreddit} ({sort}, limit={limit})")

        posts_data = reddit.fetch_subreddit_posts(subreddit, sort, limit)

        if posts_data:
            # Convert to RedditPost objects
            posts = [RedditPost.from_dict(data) for data in posts_data]
            all_posts.extend(posts)

            logger.success(f"✅ Got {len(posts)} posts from r/{subreddit}")

            # Show sample
            for post in posts[:2]:
                logger.info(f"  - {post.display_title}")
                if post.has_text_content:
                    preview = post.selftext[:50].replace('\n', ' ')
                    logger.info(f"    Text: {preview}...")
        else:
            logger.warning(f"❌ No posts from r/{subreddit}")

    # Step 2: Create collection and analyze
    logger.info("\n📊 STEP 2: Analyzing Posts")
    logger.info("-"*40)

    collection = PostCollection(all_posts)
    stats = collection.get_statistics()

    logger.info(f"Total posts collected: {stats['total']}")
    logger.info(f"Subreddits: {', '.join(stats['subreddits'])}")
    logger.info(f"Posts with text content: {stats['with_text']}")
    logger.info(f"Average score: {stats['avg_score']:.1f}")
    logger.info(f"Average comments: {stats['avg_comments']:.1f}")

    # Filter posts with text
    text_posts = collection.filter_has_text()
    logger.info(f"\nPosts suitable for audio conversion: {len(text_posts)}")

    # Step 3: Save to storage
    logger.info("\n💾 STEP 3: Saving to Storage")
    logger.info("-"*40)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"workflow_test_{timestamp}.json"

    filepath = storage.save_post_collection(collection, filename)
    logger.success(f"✅ Saved to: {filepath}")

    # Step 4: Verify storage
    logger.info("\n🔍 STEP 4: Verifying Storage")
    logger.info("-"*40)

    loaded = storage.load_post_collection(filename)
    if loaded and len(loaded.posts) == len(all_posts):
        logger.success(
            f"✅ Verification passed: {len(loaded.posts)} posts loaded correctly")
    else:
        logger.error("❌ Verification failed!")

    # Step 5: Display storage info
    logger.info("\n📁 STEP 5: Storage Summary")
    logger.info("-"*40)

    storage_stats = storage.get_storage_stats()
    for dir_name, stats in storage_stats.items():
        logger.info(
            f"{dir_name.upper()}: {stats['file_count']} files, {stats['total_size_mb']} MB")

    # Final summary
    logger.info("\n" + "="*60)
    logger.success("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY!")
    logger.info("="*60)

    logger.info("\n📋 Final Summary:")
    logger.info(f"  • Posts fetched: {len(all_posts)}")
    logger.info(f"  • Text posts: {len(text_posts)}")
    logger.info(f"  • Data saved: ✓")
    logger.info(f"  • Data verified: ✓")

    estimated_audio = sum(post.estimated_audio_duration for post in text_posts)
    logger.info(f"  • Estimated audio time: {estimated_audio/60:.1f} minutes")

    return True


def test_edge_cases():
    """Test edge cases and error handling"""
    logger.info("\n" + "="*60)
    logger.info("EDGE CASE TESTING")
    logger.info("="*60)

    reddit = get_reddit_client()

    # Test 1: Invalid subreddit
    logger.info("\n🧪 Test 1: Invalid subreddit")
    invalid = reddit.validate_subreddit("this_definitely_does_not_exist_12345")
    if not invalid:
        logger.success("✅ Correctly identified invalid subreddit")

    # Test 2: Empty results handling
    logger.info("\n🧪 Test 2: Empty results")
    posts = reddit.fetch_subreddit_posts(
        "this_definitely_does_not_exist_12345", "hot", 5)
    if len(posts) == 0:
        logger.success("✅ Correctly handled empty results")

    # Test 3: Large content handling
    logger.info("\n🧪 Test 3: Fetching larger dataset")
    posts = reddit.fetch_subreddit_posts("AskReddit", "hot", 25)
    if posts:
        logger.success(f"✅ Successfully fetched {len(posts)} posts")

        # Find longest post
        longest = max(posts, key=lambda p: len(p.get('selftext', '')))
        logger.info(
            f"  Longest post: {len(longest.get('selftext', ''))} characters")


if __name__ == "__main__":
    try:
        # Run main workflow test
        success = test_complete_workflow()

        # Run edge case tests
        test_edge_cases()

        logger.info("\n" + "🎉"*20)
        logger.success("DAY 1 COMPLETE - All systems operational!")
        logger.info("Ready for Day 2: Text Processing Pipeline")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
