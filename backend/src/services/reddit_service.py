"""
Reddit Service Module
Handles all interactions with Reddit API using PRAW
"""

import praw
from typing import List, Dict, Optional, Any
from datetime import datetime
import time

from src.config.settings import config
from src.utils.loggers import get_logger

# Create logger for this module
logger = get_logger(__name__)


class RedditClient:
    """Reddit API client wrapper"""

    def __init__(self):
        """Initialize Reddit client with credentials from config"""
        try:
            self.reddit = praw.Reddit(
                client_id=config.REDDIT_CLIENT_ID,
                client_secret=config.REDDIT_CLIENT_SECRET,
                user_agent=config.REDDIT_USER_AGENT
            )
            # Test the connection
            self._verify_connection()
            logger.success("Reddit client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise

    def _verify_connection(self):
        """Verify Reddit API connection is working"""
        try:
            # Simple API call to verify credentials
            self.reddit.user.me()
        except Exception:
            # For read-only mode, we can't call user.me(), so try a different approach
            try:
                test = self.reddit.subreddit("test")
                _ = test.display_name
            except Exception as e:
                logger.error(f"Connection verification failed: {e}")
                raise ConnectionError(f"Unable to connect to Reddit API: {e}")

    def validate_subreddit(self, subreddit_name: str) -> bool:
        """
        Check if a subreddit exists and is accessible

        Args:
            subreddit_name: Name of the subreddit (without r/)

        Returns:
            bool: True if subreddit is valid and accessible
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            # Try to access a property to trigger any errors
            _ = subreddit.display_name
            logger.info(f"Subreddit r/{subreddit_name} validated successfully")
            return True

        except praw.exceptions.InvalidSubreddit:
            logger.warning(f"Invalid subreddit: r/{subreddit_name}")
            return False
        except praw.exceptions.Forbidden:
            logger.warning(
                f"Subreddit r/{subreddit_name} is private or banned")
            return False
        except Exception as e:
            logger.error(f"Error validating subreddit r/{subreddit_name}: {e}")
            return False

    def fetch_subreddit_posts(
        self,
        subreddit_name: str,
        sort_type: str = "hot",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a subreddit

        Args:
            subreddit_name: Name of the subreddit (without r/)
            sort_type: How to sort posts ('hot', 'new', 'top', 'rising')
            limit: Number of posts to fetch (max 100)

        Returns:
            List of dictionaries containing post data
        """
        posts = []

        # Validate inputs
        if not self.validate_subreddit(subreddit_name):
            logger.error(
                f"Cannot fetch posts from invalid subreddit: r/{subreddit_name}")
            return posts

        if sort_type not in ['hot', 'new', 'top', 'rising']:
            logger.warning(
                f"Invalid sort_type '{sort_type}', defaulting to 'hot'")
            sort_type = 'hot'

        if limit > 100:
            logger.warning(
                f"Limit {limit} exceeds maximum (100), capping at 100")
            limit = 100

        try:
            logger.info(
                f"Fetching {limit} {sort_type} posts from r/{subreddit_name}")
            subreddit = self.reddit.subreddit(subreddit_name)

            # Get the appropriate sorting method
            if sort_type == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort_type == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort_type == 'top':
                submissions = subreddit.top(limit=limit)
            elif sort_type == 'rising':
                submissions = subreddit.rising(limit=limit)

            # Process each submission
            for submission in submissions:
                post_data = self._extract_post_data(submission)
                posts.append(post_data)

            logger.success(
                f"Successfully fetched {len(posts)} posts from r/{subreddit_name}")

        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")

        return posts

    def _extract_post_data(self, submission) -> Dict[str, Any]:
        """
        Extract relevant data from a Reddit submission

        Args:
            submission: PRAW Submission object

        Returns:
            Dictionary containing post data
        """
        try:
            # Basic post data
            post_data = {
                'id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'subreddit': submission.subreddit.display_name,
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'permalink': f"https://reddit.com{submission.permalink}",
                'url': submission.url,
                'is_self': submission.is_self,
                'is_video': submission.is_video,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'stickied': submission.stickied,
                'locked': submission.locked,
                'fetched_at': datetime.now().isoformat()
            }

            # Get text content for self posts
            if submission.is_self:
                post_data['selftext'] = submission.selftext
                post_data['selftext_html'] = submission.selftext_html
            else:
                post_data['selftext'] = ""
                post_data['selftext_html'] = None

            # Awards (if any)
            post_data['total_awards_received'] = submission.total_awards_received

            # Flair information
            post_data['link_flair_text'] = submission.link_flair_text
            post_data['author_flair_text'] = submission.author_flair_text

            # Content warnings/tags
            post_data['content_categories'] = submission.content_categories if hasattr(
                submission, 'content_categories') else None

            return post_data

        except Exception as e:
            logger.error(
                f"Error extracting data from post {submission.id}: {e}")
            # Return minimal data if extraction fails
            return {
                'id': submission.id if hasattr(submission, 'id') else 'unknown',
                'title': submission.title if hasattr(submission, 'title') else 'Error extracting title',
                'error': str(e),
                'fetched_at': datetime.now().isoformat()
            }

    def get_post_content(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single post by ID

        Args:
            post_id: Reddit post ID

        Returns:
            Dictionary containing post data or None if not found
        """
        try:
            submission = self.reddit.submission(id=post_id)
            # Force load the submission data
            submission._fetch()
            return self._extract_post_data(submission)

        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            return None


# Create a singleton instance
_reddit_client = None


def get_reddit_client() -> RedditClient:
    """Get or create Reddit client instance"""
    global _reddit_client
    if _reddit_client is None:
        _reddit_client = RedditClient()
    return _reddit_client
