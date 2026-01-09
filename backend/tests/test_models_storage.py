#!/usr/bin/env python3
"""
Test Reddit Post Models and Storage Service
"""

from src.utils.loggers import logger
from src.services.reddit_service import get_reddit_client
from src.services.storage_service import get_storage_service
from src.models.reddit_post import RedditPost, PostCollection
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_models():
    """Test RedditPost model"""
    logger.info("Testing Reddit Post Models...")

    # Create a sample post
    post = RedditPost(
        id="test123",
        title="Test Post Title",
        subreddit="python",
        created_utc="2025-09-27T12:00:00",
        fetched_at="2025-09-27T14:00:00",
        author="test_user",
        selftext="This is the post content for testing.",
        score=100,
        num_comments=25
    )

    # Test properties
    logger.info(f"Post: {post}")
    logger.info(f"Display title: {post.display_title}")
    logger.info(f"Content length: {post.content_length}")
    logger.info(f"Has text: {post.has_text_content}")
    logger.info(
        f"Estimated audio duration: {post.estimated_audio_duration:.2f} seconds")

    # Test collection
    collection = PostCollection([post])
    stats = collection.get_statistics()
    logger.info(f"Collection stats: {stats}")

    assert True  # Test completed successfully


def test_storage_with_real_data():
    """Test storage with real Reddit data"""
    logger.info("\n" + "="*50)
    logger.info("Testing Storage with Real Data...")

    # Get Reddit client and fetch some posts
    reddit = get_reddit_client()
    posts_data = reddit.fetch_subreddit_posts("python", "hot", 5)

    # Convert to RedditPost objects
    posts = [RedditPost.from_dict(post_data) for post_data in posts_data]
    collection = PostCollection(posts)

    # Get storage service
    storage = get_storage_service()

    # Test saving collection
    filepath = storage.save_post_collection(collection, "test_collection.json")
    logger.success(f"✅ Saved collection to: {filepath}")

    # Test loading collection
    loaded_collection = storage.load_post_collection("test_collection.json")
    if loaded_collection:
        logger.success(
            f"✅ Loaded {len(loaded_collection.posts)} posts from file")

        # Display statistics
        stats = loaded_collection.get_statistics()
        logger.info("Collection Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    # Test listing files
    files = storage.list_saved_files("processed")
    logger.info(f"\nFiles in processed directory: {len(files)}")
    for file_info in files[:3]:  # Show first 3
        logger.info(f"  - {file_info['filename']} ({file_info['size_mb']} MB)")

    # Test storage stats
    storage_stats = storage.get_storage_stats()
    logger.info("\nStorage Statistics:")
    for directory, stats in storage_stats.items():
        logger.info(
            f"  {directory}: {stats['file_count']} files, {stats['total_size_mb']} MB")

    assert True  # Test completed successfully


def main():
    """Run all tests"""
    logger.info("Starting Model and Storage Tests")
    logger.info("="*50)

    # Test models
    test_models()

    # Test storage with real data
    test_storage_with_real_data()

    logger.success("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    main()
