"""
Reddit Service Module
Handles all interactions with Reddit API using PRAW
"""

import praw
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import time

from src.config.settings import config
from src.utils.loggers import get_logger
from src.models.post_filter_config import PostFilterConfig

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

    def _get_post_text_length(self, post: Dict[str, Any]) -> int:
        """
        Calculate total text content length (title + selftext).

        Args:
            post: Post dictionary containing title and selftext

        Returns:
            Total character count of title and selftext combined
        """
        title_len = len(post.get('title', ''))
        selftext_len = len(post.get('selftext', ''))
        return title_len + selftext_len

    def _has_meaningful_text(self, post: Dict[str, Any], threshold: int = 50) -> bool:
        """
        Check if post has meaningful text content.

        Used for image-only and link-only detection.

        Args:
            post: Post dictionary
            threshold: Minimum character count for "meaningful" text

        Returns:
            True if selftext has >= threshold characters, False otherwise
        """
        return len(post.get('selftext', '').strip()) >= threshold

    def _is_deleted_or_removed(self, post: Dict[str, Any]) -> bool:
        """
        Check if post is deleted or removed.

        Checks for [deleted] or [removed] markers in selftext, title, or author.

        Args:
            post: Post dictionary

        Returns:
            True if post appears to be deleted or removed, False otherwise
        """
        text = post.get('selftext', '').lower()
        title = post.get('title', '').lower()
        author = post.get('author', '').lower()

        return (
            '[deleted]' in text or '[removed]' in text or
            '[deleted]' in title or '[removed]' in title or
            author == '[deleted]'
        )

    def _should_include_post(
        self,
        post: Dict[str, Any],
        filter_config: PostFilterConfig
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if post passes all filter criteria.

        Filters are checked in order of computational efficiency:
        1. Quick checks first (upvotes, NSFW, deleted)
        2. Expensive checks last (text length calculations)

        Args:
            post: Post dictionary to check
            filter_config: Filter configuration with criteria

        Returns:
            Tuple of (should_include: bool, reason_excluded: Optional[str])
            - (True, None) if post passes all filters
            - (False, "reason") if post fails any filter
        """
        # Quick checks first (no calculation needed)
        if filter_config.min_upvotes is not None:
            if post.get('score', 0) < filter_config.min_upvotes:
                return (False, 'min_upvotes')

        if filter_config.exclude_nsfw and post.get('over_18', False):
            return (False, 'nsfw')

        if filter_config.exclude_deleted_removed and self._is_deleted_or_removed(post):
            return (False, 'deleted_removed')

        # Expensive checks last (require text length calculation)
        if any([filter_config.min_char_count, filter_config.max_char_count,
                filter_config.exclude_image_only, filter_config.exclude_link_only]):
            text_length = self._get_post_text_length(post)

            if filter_config.min_char_count is not None:
                if text_length < filter_config.min_char_count:
                    return (False, 'min_char_count')

            if filter_config.max_char_count is not None:
                if text_length > filter_config.max_char_count:
                    return (False, 'max_char_count')

            # Image-only: not self post, not video, no meaningful text
            if filter_config.exclude_image_only:
                if (not post.get('is_self', False) and
                    not post.get('is_video', False) and
                    not self._has_meaningful_text(post, filter_config.MEANINGFUL_TEXT_THRESHOLD)):
                    return (False, 'image_only')

            # Link-only: not self post, no meaningful text
            if filter_config.exclude_link_only:
                if (not post.get('is_self', False) and
                    not self._has_meaningful_text(post, filter_config.MEANINGFUL_TEXT_THRESHOLD)):
                    return (False, 'link_only')

        return (True, None)

    def fetch_subreddit_posts(
        self,
        subreddit_name: str,
        sort_type: str = "hot",
        limit: int = 10,
        filter_config: Optional[PostFilterConfig] = None
    ) -> Dict[str, Any]:
        """
        Fetch posts from a subreddit with optional filtering.

        Args:
            subreddit_name: Name of the subreddit (without r/)
            sort_type: How to sort posts ('hot', 'new', 'top', 'rising')
            limit: Number of posts to fetch (max 100)
            filter_config: Optional filter configuration for content filtering

        Returns:
            Dictionary containing:
            - If filter_config is None: Returns list of posts (backwards compatibility)
            - If filter_config provided: Returns dict with 'posts' and 'metadata'
              {
                  'posts': List[Dict],
                  'metadata': {
                      'total_fetched': int,
                      'total_passed_filters': int,
                      'filters_applied': Dict,
                      'filter_reasons': Dict[str, int],
                      'message': Optional[str]
                  }
              }
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

        # Apply filters if provided
        if filter_config is None:
            # Backwards compatibility: return list for no filters
            return posts

        # Filter posts
        filtered_posts = []
        filter_reasons = {}  # Track why posts were filtered

        for post in posts:
            should_include, reason = self._should_include_post(post, filter_config)
            if should_include:
                filtered_posts.append(post)
            elif reason:
                filter_reasons[reason] = filter_reasons.get(reason, 0) + 1

        # Log filtering results
        logger.info(
            f"Filtered {len(posts)} -> {len(filtered_posts)} posts from r/{subreddit_name}"
        )

        if len(filtered_posts) == 0 and len(posts) > 0:
            logger.warning(
                f"All {len(posts)} posts filtered out. Reasons: {filter_reasons}"
            )

        # Return with metadata
        return {
            'posts': filtered_posts,
            'metadata': {
                'total_fetched': len(posts),
                'total_passed_filters': len(filtered_posts),
                'filters_applied': filter_config.to_dict(),
                'filter_reasons': filter_reasons,
                'message': (
                    'No posts passed the specified filters'
                    if len(filtered_posts) == 0 and len(posts) > 0
                    else None
                )
            }
        }

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
