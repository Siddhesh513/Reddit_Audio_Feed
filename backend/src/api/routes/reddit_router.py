"""
Reddit API Routes
Endpoints for Reddit post fetching and management
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import time

from src.api.models import (
    RedditPostRequest,
    RedditPostResponse,
    RedditPostsResponse,
    PostsMetadata,
    BaseResponse,
    ErrorResponse,
    PaginationParams
)
from src.services.reddit_service import get_reddit_client
from src.services.text_processor import get_text_processor
from src.services.storage_service import get_storage_service
from src.utils.loggers import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/posts", response_model=RedditPostsResponse)
async def fetch_reddit_posts(
    subreddit: str = Query(..., description="Subreddit name"),
    sort_type: str = Query("hot", description="Sort type: hot, new, top, rising"),
    limit: int = Query(10, ge=1, le=100, description="Number of posts"),

    # Filter parameters (all optional)
    min_upvotes: Optional[int] = Query(None, ge=0, description="Minimum upvotes threshold"),
    min_char_count: Optional[int] = Query(None, ge=0, description="Minimum character count (title + selftext)"),
    max_char_count: Optional[int] = Query(None, ge=1, description="Maximum character count (title + selftext)"),
    exclude_nsfw: bool = Query(False, description="Exclude NSFW posts"),
    exclude_deleted_removed: bool = Query(True, description="Exclude deleted/removed posts"),
    exclude_image_only: bool = Query(False, description="Exclude image-only posts (no meaningful text)"),
    exclude_link_only: bool = Query(False, description="Exclude link-only posts (no meaningful text)"),
):
    """
    Fetch posts from a subreddit with optional content filtering.

    **Basic Parameters:**
    - **subreddit**: Name of subreddit (without r/)
    - **sort_type**: How to sort posts (hot, new, top, rising)
    - **limit**: Number of posts to fetch (1-100)

    **Filter Parameters (all optional):**
    - **min_upvotes**: Only include posts with this many upvotes or more
    - **min_char_count**: Minimum total character count (title + selftext)
    - **max_char_count**: Maximum total character count (title + selftext)
    - **exclude_nsfw**: Exclude NSFW/18+ posts
    - **exclude_deleted_removed**: Exclude posts marked as [deleted] or [removed]
    - **exclude_image_only**: Exclude image posts without meaningful text (< 50 chars)
    - **exclude_link_only**: Exclude link posts without meaningful text (< 50 chars)

    **Returns:**
    Posts list with metadata including total fetched, total passed filters, and filter statistics.
    """
    try:
        logger.info(f"API request: Fetching posts from r/{subreddit}")
        reddit = await get_reddit_client()

        # Validate subreddit
        if not await reddit.validate_subreddit(subreddit):
            raise HTTPException(status_code=404, detail=f"Subreddit r/{subreddit} not found or inaccessible")

        # Build filter config if any filters are specified
        filter_config = None
        if any([min_upvotes is not None, min_char_count, max_char_count,
                exclude_nsfw, exclude_deleted_removed, exclude_image_only, exclude_link_only]):
            from src.models.post_filter_config import PostFilterConfig
            filter_config = PostFilterConfig(
                min_upvotes=min_upvotes,
                min_char_count=min_char_count,
                max_char_count=max_char_count,
                exclude_nsfw=exclude_nsfw,
                exclude_deleted_removed=exclude_deleted_removed,
                exclude_image_only=exclude_image_only,
                exclude_link_only=exclude_link_only
            )

        # Fetch posts (with or without filters)
        result = await reddit.fetch_subreddit_posts(subreddit, sort_type, limit, filter_config)

        # Handle backwards compatibility
        if isinstance(result, list):
            # Old format (no filters) - wrap in new format
            logger.success(f"Successfully returning {len(result)} posts from r/{subreddit}")
            return {
                'posts': [RedditPostResponse(**post) for post in result],
                'metadata': {
                    'total_fetched': len(result),
                    'total_passed_filters': len(result),
                    'filters_applied': {},
                    'filter_reasons': None,
                    'message': None
                }
            }
        else:
            # New format (with filters)
            logger.success(f"Successfully returning {len(result['posts'])} posts from r/{subreddit}")
            return {
                'posts': [RedditPostResponse(**post) for post in result['posts']],
                'metadata': result['metadata']
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching posts from r/{subreddit}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/post/{post_id}", response_model=RedditPostResponse)
async def get_reddit_post(post_id: str):
    """
    Get a specific Reddit post by ID

    - **post_id**: Reddit post ID
    """
    try:
        reddit = await get_reddit_client()
        post = await reddit.get_post_content(post_id)

        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

        return RedditPostResponse(**post)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/batch")
async def fetch_multiple_subreddits(
    subreddits: List[str],
    sort_type: str = "hot",
    limit_per_sub: int = Query(5, ge=1, le=20)
):
    """
    Fetch posts from multiple subreddits

    - **subreddits**: List of subreddit names
    - **sort_type**: How to sort posts
    - **limit_per_sub**: Posts per subreddit
    """
    try:
        reddit = await get_reddit_client()
        all_posts = []
        errors = []

        for subreddit in subreddits[:10]:  # Limit to 10 subreddits
            try:
                result = await reddit.fetch_subreddit_posts(subreddit, sort_type, limit_per_sub)
                posts = result if isinstance(result, list) else result.get('posts', [])
                all_posts.extend(posts)
            except Exception as e:
                errors.append({"subreddit": subreddit, "error": str(e)})

            # Small delay to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.5)

        return {
            "success": True,
            "posts": [RedditPostResponse(**post) for post in all_posts],
            "errors": errors if errors else None,
            "total": len(all_posts)
        }

    except Exception as e:
        logger.error(f"Error in batch fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_posts(limit: int = Query(10, ge=1, le=50)):
    """
    Get trending posts from popular subreddits

    - **limit**: Total number of posts to return
    """
    try:
        reddit = await get_reddit_client()
        trending_subs = ["todayilearned", "AskReddit", "Showerthoughts", "LifeProTips", "explainlikeimfive"]

        all_posts = []
        posts_per_sub = max(1, limit // len(trending_subs))

        for sub in trending_subs:
            try:
                result = await reddit.fetch_subreddit_posts(sub, "hot", posts_per_sub)
                posts = result if isinstance(result, list) else result.get('posts', [])
                all_posts.extend(posts)
            except:
                continue  # Skip failed subreddits

        # Sort by score and return top posts
        all_posts.sort(key=lambda x: x.get('score', 0), reverse=True)

        return {
            "success": True,
            "posts": [RedditPostResponse(**post) for post in all_posts[:limit]],
            "total": len(all_posts[:limit])
        }

    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=BaseResponse)
async def process_reddit_post(post_id: str):
    """
    Process a Reddit post through the text pipeline

    - **post_id**: Reddit post ID to process
    """
    try:
        reddit = await get_reddit_client()
        processor = get_text_processor()

        # Fetch post
        post = await reddit.get_post_content(post_id)
        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

        # Process text
        processed = processor.process_post(post)

        # Save processed post
        storage = get_storage_service()
        storage.save_posts([processed], post.get('subreddit', 'unknown'), f"processed_{post_id}.json")

        return BaseResponse(
            success=True,
            message=f"Post {post_id} processed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subreddit/validate")
async def validate_subreddit(name: str = Query(..., description="Subreddit name")):
    """
    Check if a subreddit exists and is accessible

    - **name**: Subreddit name to validate
    """
    try:
        reddit = await get_reddit_client()
        is_valid = await reddit.validate_subreddit(name)

        return {
            "success": True,
            "subreddit": name,
            "valid": is_valid,
            "message": f"r/{name} is {'valid and accessible' if is_valid else 'invalid or inaccessible'}"
        }

    except Exception as e:
        logger.error(f"Error validating subreddit {name}: {e}")
        return {
            "success": False,
            "subreddit": name,
            "valid": False,
            "error": str(e)
        }


@router.get("/search")
async def search_posts(
    query: str = Query(..., description="Search query"),
    subreddit: Optional[str] = Query(None, description="Limit to specific subreddit"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search for Reddit posts
    
    - **query**: Search terms
    - **subreddit**: Optional subreddit to search within
    - **limit**: Number of results
    """
    try:
        # This is a placeholder - implement actual Reddit search if needed
        return {
            "success": True,
            "message": "Search functionality not yet implemented",
            "query": query,
            "subreddit": subreddit
        }
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))
