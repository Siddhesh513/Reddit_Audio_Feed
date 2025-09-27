#!/usr/bin/env python3
"""Find subreddits with text posts"""

from src.utils.loggers import logger
from src.services.reddit_service import get_reddit_client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Subreddits known for text posts
TEXT_HEAVY_SUBS = [
    "tifu",           # Today I F***ed Up - stories
    "AmItheAsshole",  # AITA - judgment posts
    "relationship_advice",  # Advice posts
    "nosleep",        # Horror stories
    "WritingPrompts",  # Story responses
]

reddit = get_reddit_client()

logger.info("Finding posts with text content...")
for sub in TEXT_HEAVY_SUBS:
    posts = reddit.fetch_subreddit_posts(sub, "hot", 2)
    if posts:
        for post in posts:
            if post.get('selftext'):
                logger.success(f"✅ r/{sub}: Found text post!")
                logger.info(f"   Title: {post['title'][:60]}...")
                logger.info(f"   Text length: {len(post['selftext'])} chars")
                break
        else:
            logger.warning(f"❌ r/{sub}: No text in posts")
