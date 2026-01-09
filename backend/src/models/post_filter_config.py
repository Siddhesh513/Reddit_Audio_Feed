"""
Filter configuration for Reddit post fetching.

This module provides the PostFilterConfig dataclass for configuring
content filtering options when fetching posts from Reddit.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PostFilterConfig:
    """
    Configuration for filtering Reddit posts during fetch.

    This class encapsulates all filter parameters with validation logic.
    All filters are optional - when not specified, no filtering is applied.

    Attributes:
        min_upvotes: Minimum upvote score threshold
        min_char_count: Minimum character count (title + selftext)
        max_char_count: Maximum character count (title + selftext)
        exclude_nsfw: Whether to exclude NSFW posts
        exclude_deleted_removed: Whether to exclude deleted/removed posts
        exclude_image_only: Whether to exclude image-only posts (no meaningful text)
        exclude_link_only: Whether to exclude link-only posts (no meaningful text)
        MEANINGFUL_TEXT_THRESHOLD: Character threshold for "meaningful text"

    Examples:
        >>> # Filter for high-quality text posts
        >>> config = PostFilterConfig(
        ...     min_upvotes=500,
        ...     min_char_count=200,
        ...     exclude_nsfw=True,
        ...     exclude_image_only=True,
        ...     exclude_link_only=True
        ... )

        >>> # Filter for family-friendly content
        >>> config = PostFilterConfig(
        ...     exclude_nsfw=True,
        ...     exclude_deleted_removed=True
        ... )
    """

    # Score filtering
    min_upvotes: Optional[int] = None

    # Content length filtering (character count)
    min_char_count: Optional[int] = None
    max_char_count: Optional[int] = None

    # Content type filtering
    exclude_nsfw: bool = False
    exclude_deleted_removed: bool = True
    exclude_image_only: bool = False
    exclude_link_only: bool = False

    # Constant for meaningful text detection
    MEANINGFUL_TEXT_THRESHOLD: int = 50

    def __post_init__(self):
        """
        Validate filter configuration after initialization.

        Raises:
            ValueError: If filter parameters are invalid
        """
        if self.min_char_count is not None and self.max_char_count is not None:
            if self.max_char_count < self.min_char_count:
                raise ValueError(
                    f"max_char_count ({self.max_char_count}) must be >= "
                    f"min_char_count ({self.min_char_count})"
                )

        if self.min_upvotes is not None and self.min_upvotes < 0:
            raise ValueError(f"min_upvotes must be >= 0, got {self.min_upvotes}")

        if self.min_char_count is not None and self.min_char_count < 0:
            raise ValueError(f"min_char_count must be >= 0, got {self.min_char_count}")

        if self.max_char_count is not None and self.max_char_count < 1:
            raise ValueError(f"max_char_count must be >= 1, got {self.max_char_count}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert filter configuration to dictionary.

        This is useful for API responses and logging.

        Returns:
            Dictionary containing all filter parameters
        """
        return {
            'min_upvotes': self.min_upvotes,
            'min_char_count': self.min_char_count,
            'max_char_count': self.max_char_count,
            'exclude_nsfw': self.exclude_nsfw,
            'exclude_deleted_removed': self.exclude_deleted_removed,
            'exclude_image_only': self.exclude_image_only,
            'exclude_link_only': self.exclude_link_only
        }

    def has_any_filters(self) -> bool:
        """
        Check if any filters are active.

        Returns:
            True if at least one filter is enabled, False otherwise
        """
        return any([
            self.min_upvotes is not None,
            self.min_char_count is not None,
            self.max_char_count is not None,
            self.exclude_nsfw,
            self.exclude_deleted_removed,
            self.exclude_image_only,
            self.exclude_link_only
        ])

    def __repr__(self) -> str:
        """String representation for debugging."""
        active_filters = []
        if self.min_upvotes is not None:
            active_filters.append(f"min_upvotes={self.min_upvotes}")
        if self.min_char_count is not None:
            active_filters.append(f"min_chars={self.min_char_count}")
        if self.max_char_count is not None:
            active_filters.append(f"max_chars={self.max_char_count}")
        if self.exclude_nsfw:
            active_filters.append("no_nsfw")
        if self.exclude_deleted_removed:
            active_filters.append("no_deleted")
        if self.exclude_image_only:
            active_filters.append("no_images")
        if self.exclude_link_only:
            active_filters.append("no_links")

        filters_str = ", ".join(active_filters) if active_filters else "no filters"
        return f"PostFilterConfig({filters_str})"
