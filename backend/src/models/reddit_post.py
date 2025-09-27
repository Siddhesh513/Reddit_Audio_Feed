"""
Reddit Post Data Model
Defines the structure and validation for Reddit posts
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class RedditPost:
    """Data model for a Reddit post"""

    # Required fields
    id: str
    title: str
    subreddit: str
    created_utc: str
    fetched_at: str

    # Author information
    author: str = '[deleted]'
    author_flair_text: Optional[str] = None

    # Post content
    selftext: str = ""
    selftext_html: Optional[str] = None
    is_self: bool = False

    # Engagement metrics
    score: int = 0
    upvote_ratio: float = 0.0
    num_comments: int = 0
    total_awards_received: int = 0

    # Post properties
    permalink: str = ""
    url: str = ""
    is_video: bool = False
    over_18: bool = False
    spoiler: bool = False
    stickied: bool = False
    locked: bool = False

    # Flair and categories
    link_flair_text: Optional[str] = None
    content_categories: Optional[List[str]] = None

    # Processing metadata
    processing_status: str = "pending"  # pending, processed, failed
    audio_file_path: Optional[str] = None
    processing_notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RedditPost':
        """Create a RedditPost from a dictionary"""
        # Filter out any keys that aren't in our dataclass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert RedditPost to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'subreddit': self.subreddit,
            'created_utc': self.created_utc,
            'fetched_at': self.fetched_at,
            'selftext': self.selftext,
            'selftext_html': self.selftext_html,
            'is_self': self.is_self,
            'score': self.score,
            'upvote_ratio': self.upvote_ratio,
            'num_comments': self.num_comments,
            'total_awards_received': self.total_awards_received,
            'permalink': self.permalink,
            'url': self.url,
            'is_video': self.is_video,
            'over_18': self.over_18,
            'spoiler': self.spoiler,
            'stickied': self.stickied,
            'locked': self.locked,
            'link_flair_text': self.link_flair_text,
            'author_flair_text': self.author_flair_text,
            'content_categories': self.content_categories,
            'processing_status': self.processing_status,
            'audio_file_path': self.audio_file_path,
            'processing_notes': self.processing_notes
        }

    def to_json(self) -> str:
        """Convert RedditPost to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @property
    def content_length(self) -> int:
        """Calculate the total content length for TTS"""
        return len(self.title) + len(self.selftext)

    @property
    def estimated_audio_duration(self) -> float:
        """Estimate audio duration (rough estimate: 150 words per minute)"""
        word_count = self.content_length / 5  # Rough estimate: 5 chars per word
        return word_count / 150 * 60  # Convert to seconds

    @property
    def has_text_content(self) -> bool:
        """Check if post has text content for TTS"""
        return bool(self.selftext and self.selftext.strip())

    @property
    def display_title(self) -> str:
        """Get a display-friendly title (truncated if needed)"""
        max_length = 80
        if len(self.title) > max_length:
            return f"{self.title[:max_length-3]}..."
        return self.title

    @property
    def created_datetime(self) -> datetime:
        """Convert created_utc string to datetime object"""
        return datetime.fromisoformat(self.created_utc)

    @property
    def age_in_hours(self) -> float:
        """Calculate how old the post is in hours"""
        created = self.created_datetime
        now = datetime.now()
        # Handle timezone-aware datetime
        if created.tzinfo is not None:
            now = now.replace(tzinfo=created.tzinfo)
        delta = now - created
        return delta.total_seconds() / 3600

    def __str__(self) -> str:
        """String representation"""
        return f"RedditPost(id={self.id}, title='{self.display_title}', subreddit=r/{self.subreddit})"

    def __repr__(self) -> str:
        """Detailed representation"""
        return (f"RedditPost(id='{self.id}', title='{self.display_title}', "
                f"author='{self.author}', score={self.score}, "
                f"comments={self.num_comments})")


class PostCollection:
    """Collection of Reddit posts with utility methods"""

    def __init__(self, posts: List[RedditPost] = None):
        self.posts = posts or []

    def add_post(self, post: RedditPost):
        """Add a post to the collection"""
        self.posts.append(post)

    def get_post_by_id(self, post_id: str) -> Optional[RedditPost]:
        """Find a post by ID"""
        for post in self.posts:
            if post.id == post_id:
                return post
        return None

    def filter_by_subreddit(self, subreddit: str) -> List[RedditPost]:
        """Filter posts by subreddit"""
        return [p for p in self.posts if p.subreddit.lower() == subreddit.lower()]

    def filter_has_text(self) -> List[RedditPost]:
        """Filter posts that have text content"""
        return [p for p in self.posts if p.has_text_content]

    def filter_by_status(self, status: str) -> List[RedditPost]:
        """Filter posts by processing status"""
        return [p for p in self.posts if p.processing_status == status]

    def sort_by_score(self, reverse: bool = True) -> List[RedditPost]:
        """Sort posts by score"""
        return sorted(self.posts, key=lambda p: p.score, reverse=reverse)

    def sort_by_comments(self, reverse: bool = True) -> List[RedditPost]:
        """Sort posts by number of comments"""
        return sorted(self.posts, key=lambda p: p.num_comments, reverse=reverse)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        if not self.posts:
            return {"total": 0}

        return {
            "total": len(self.posts),
            "subreddits": list(set(p.subreddit for p in self.posts)),
            "with_text": sum(1 for p in self.posts if p.has_text_content),
            "avg_score": sum(p.score for p in self.posts) / len(self.posts),
            "avg_comments": sum(p.num_comments for p in self.posts) / len(self.posts),
            "nsfw_count": sum(1 for p in self.posts if p.over_18),
            "spoiler_count": sum(1 for p in self.posts if p.spoiler),
            "processing_status": {
                "pending": sum(1 for p in self.posts if p.processing_status == "pending"),
                "processed": sum(1 for p in self.posts if p.processing_status == "processed"),
                "failed": sum(1 for p in self.posts if p.processing_status == "failed")
            }
        }

    def to_json(self) -> str:
        """Convert collection to JSON"""
        return json.dumps(
            [post.to_dict() for post in self.posts],
            indent=2,
            ensure_ascii=False
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'PostCollection':
        """Create collection from JSON string"""
        data = json.loads(json_str)
        posts = [RedditPost.from_dict(item) for item in data]
        return cls(posts)
