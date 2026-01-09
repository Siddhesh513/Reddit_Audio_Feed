"""
API Request and Response Models
Pydantic models for validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Response status types"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class RedditPostRequest(BaseModel):
    """Request model for fetching Reddit posts"""
    subreddit: str
    sort_type: str = "hot"
    limit: int = Field(default=10, ge=1, le=100)
    min_score: int = Field(default=0, ge=0)
    
    @validator('sort_type')
    def validate_sort_type(cls, v):
        allowed = ['hot', 'new', 'top', 'rising']
        if v not in allowed:
            raise ValueError(f"sort_type must be one of {allowed}")
        return v


class RedditPostResponse(BaseModel):
    """Response model for Reddit post"""
    id: str
    title: str
    author: str
    subreddit: str
    score: int
    num_comments: int
    created_utc: str
    selftext: Optional[str] = None
    url: Optional[str] = None
    is_self: bool
    over_18: bool


class PostsMetadata(BaseModel):
    """Metadata about filtered posts"""
    total_fetched: int
    total_passed_filters: int
    filters_applied: Dict[str, Any]
    filter_reasons: Optional[Dict[str, int]] = None
    message: Optional[str] = None


class RedditPostsResponse(BaseModel):
    """Response with posts and metadata"""
    posts: List[RedditPostResponse]
    metadata: PostsMetadata


class AudioGenerateRequest(BaseModel):
    """Request model for audio generation with enhanced voice/speed options"""
    post_id: Optional[str] = None
    post_data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None

    # Voice selection
    voice: Optional[str] = Field(
        default="en-US",
        description="Voice ID (e.g., en-US, es-ES, fr-FR). See /api/audio/voices for available options."
    )

    # Language override (optional)
    language: Optional[str] = Field(
        default=None,
        description="Language code (e.g., en, es, fr). Overrides voice language if provided."
    )

    # Speech rate
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech rate multiplier. 0.75=slow, 1.0=normal, 1.25=fast. Range: 0.5-2.0"
    )

    # TTS engine
    engine: str = Field(
        default="gtts",
        description="TTS engine to use (gtts, kokoro, mock)"
    )

    @validator('voice')
    def validate_voice(cls, v):
        """Validate voice ID against available voices"""
        if v is None:
            return "en-US"

        # Import here to avoid circular dependency
        try:
            from src.config.settings import config
            available_voices = list(config.TTSConfig.GTTS_VOICES.keys())

            if v not in available_voices:
                from src.utils.loggers import get_logger
                logger = get_logger(__name__)
                logger.warning(
                    f"Voice '{v}' not found in available voices. "
                    f"Falling back to en-US. Available: {available_voices}"
                )
                return "en-US"
        except Exception:
            # If config fails to load, use default
            return "en-US"

        return v

    @validator('speed')
    def validate_speed(cls, v):
        """Clamp speed to valid range"""
        try:
            from src.config.settings import config
            return max(
                config.TTSConfig.MIN_SPEED,
                min(v, config.TTSConfig.MAX_SPEED)
            )
        except Exception:
            # If config fails, use hardcoded range
            return max(0.5, min(v, 2.0))

    @validator('engine')
    def validate_input(cls, v, values):
        """Ensure at least one input source is provided"""
        if not values.get('post_id') and not values.get('post_data') and not values.get('text'):
            raise ValueError("Must provide either post_id, post_data, or text")
        return v


class AudioGenerateResponse(BaseResponse):
    """Response model for audio generation"""
    filename: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    post_id: Optional[str] = None


class QueueAddRequest(BaseModel):
    """Request model for adding to queue"""
    subreddit: Optional[str] = None
    post_ids: Optional[List[str]] = None
    posts: Optional[List[Dict[str, Any]]] = None
    priority: int = Field(default=5, ge=1, le=10)
    limit: Optional[int] = Field(default=10, ge=1, le=50)


class QueueStatusResponse(BaseResponse):
    """Response model for queue status"""
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    by_priority: Dict[int, int]
    by_subreddit: Dict[str, int]


class QueueProcessRequest(BaseModel):
    """Request model for processing queue"""
    max_items: Optional[int] = Field(default=10, ge=1, le=100)
    engine: str = "gtts"


class StatsResponse(BaseResponse):
    """Response model for statistics"""
    audio_files: int
    total_duration_minutes: float
    total_size_mb: float
    posts_processed: int
    queue_items: int
    storage_used_percentage: float
    recent_activity: List[Dict[str, Any]]


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class SortParams(BaseModel):
    """Sorting parameters"""
    sort_by: str = "created_at"
    order: str = "desc"
    
    @validator('order')
    def validate_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError("order must be 'asc' or 'desc'")
        return v
