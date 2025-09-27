#!/usr/bin/env python3
"""
Test Reddit Service functionality
"""

from src.utils.loggers import logger
from src.services.reddit_service import get_reddit_client
from pprint import pprint
import json
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_reddit_connection():
    """Test basic Reddit connection"""
    logger.info("Testing Reddit connection...")
    try:
        client = get_reddit_client()
        logger.success("✅ Reddit client created successfully")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to create Reddit client: {e}")
        return None


def test_subreddit_validation(client):
    """Test subreddit validation"""
    logger.info("\n" + "="*50)
    logger.info("Testing subreddit validation...")

    test_cases = [
        ("python", True),  # Valid public subreddit
        ("askreddit", True),  # Another valid subreddit
        ("thisdoesnotexist12345", False),  # Invalid subreddit
    ]

    for subreddit, expected in test_cases:
        result = client.validate_subreddit(subreddit)
        status = "✅" if result == expected else "❌"
        logger.info(f"{status} r/{subreddit}: {result} (expected: {expected})")


def test_fetch_posts(client):
    """Test fetching posts from different subreddits"""
    logger.info("\n" + "="*50)
    logger.info("Testing post fetching...")

    # Test different subreddits and sort types
    test_configs = [
        ("python", "hot", 5),
        ("askreddit", "new", 3),
        ("todayilearned", "top", 2),
    ]

    all_posts = []

    for subreddit, sort_type, limit in test_configs:
        logger.info(f"\nFetching {limit} {sort_type} posts from r/{subreddit}")

        posts = client.fetch_subreddit_posts(
            subreddit_name=subreddit,
            sort_type=sort_type,
            limit=limit
        )

        if posts:
            logger.success(f"✅ Fetched {len(posts)} posts from r/{subreddit}")
            all_posts.extend(posts)

            # Display first post as sample
            logger.info("Sample post:")
            first_post = posts[0]
            logger.info(f"  Title: {first_post['title'][:80]}...")
            logger.info(f"  Author: {first_post['author']}")
            logger.info(f"  Score: {first_post['score']}")
            logger.info(f"  Comments: {first_post['num_comments']}")
            if first_post['is_self'] and first_post['selftext']:
                preview = first_post['selftext'][:100].replace('\n', ' ')
                logger.info(f"  Text preview: {preview}...")
        else:
            logger.warning(f"❌ No posts fetched from r/{subreddit}")

    return all_posts


def test_save_to_json(posts):
    """Save fetched posts to JSON file"""
    logger.info("\n" + "="*50)
    logger.info("Testing JSON save...")

    if not posts:
        logger.warning("No posts to save")
        return

    try:
        filename = "data/raw/test_posts.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

        logger.success(f"✅ Saved {len(posts)} posts to {filename}")

        # Verify file was created
        with open(filename, 'r', encoding='utf-8') as f:
            loaded_posts = json.load(f)
            logger.info(f"Verified: File contains {len(loaded_posts)} posts")

    except Exception as e:
        logger.error(f"❌ Error saving posts to JSON: {e}")


def test_single_post(client):
    """Test fetching a single post by ID"""
    logger.info("\n" + "="*50)
    logger.info("Testing single post fetch...")

    # First get a post ID from a subreddit
    posts = client.fetch_subreddit_posts("python", "hot", 1)
    if posts:
        post_id = posts[0]['id']
        logger.info(f"Fetching post with ID: {post_id}")

        single_post = client.get_post_content(post_id)
        if single_post:
            logger.success(
                f"✅ Successfully fetched post: {single_post['title'][:50]}...")
        else:
            logger.error(f"❌ Failed to fetch post {post_id}")


def main():
    """Run all tests"""
    logger.info("Starting Reddit Service Tests")
    logger.info("="*50)

    # Test 1: Connection
    client = test_reddit_connection()
    if not client:
        logger.error("Cannot proceed without Reddit client")
        return

    # Test 2: Subreddit validation
    test_subreddit_validation(client)

    # Test 3: Fetch posts
    posts = test_fetch_posts(client)

    # Test 4: Save to JSON
    test_save_to_json(posts)

    # Test 5: Single post
    test_single_post(client)

    logger.info("\n" + "="*50)
    logger.success("✅ All Reddit Service tests completed!")

    # Summary statistics
    if posts:
        logger.info(f"\nSummary:")
        logger.info(f"  Total posts fetched: {len(posts)}")
        subreddits = set(p['subreddit'] for p in posts)
        logger.info(f"  Subreddits: {', '.join(subreddits)}")
        self_posts = sum(1 for p in posts if p['is_self'])
        logger.info(f"  Self posts (with text): {self_posts}")
        logger.info(f"  Link posts: {len(posts) - self_posts}")


if __name__ == "__main__":
    main()
