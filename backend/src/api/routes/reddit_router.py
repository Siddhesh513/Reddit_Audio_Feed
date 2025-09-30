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


@router.get("/posts", response_model=List[RedditPostResponse])
async def fetch_reddit_posts(
    subreddit: str = Query(..., description="Subreddit name"),
    sort_type: str = Query("hot", description="Sort type: hot, new, top, rising"),
    limit: int = Query(10, ge=1, le=100, description="Number of posts"),
    min_score: int = Query(0, ge=0, description="Minimum score filter")
):
    """
    Fetch posts from a subreddit
    
    - **subreddit**: Name of subreddit (without r/)
    - **sort_type**: How to sort posts (hot, new, top, rising)
    - **limit**: Number of posts to fetch (1-100)
    - **min_score**: Minimum score to include
    """
    try:
        reddit = get_reddit_client()
        
        # Validate subreddit
        if not reddit.validate_subreddit(subreddit):
            raise HTTPException(status_code=404, detail=f"Subreddit r/{subreddit} not found or inaccessible")
        
        # Fetch posts
        posts = reddit.fetch_subreddit_posts(subreddit, sort_type, limit)
        
        # Filter by score
        if min_score > 0:
            posts = [p for p in posts if p.get('score', 0) >= min_score]
        
        # Convert to response model
        return [RedditPostResponse(**post) for post in posts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/post/{post_id}", response_model=RedditPostResponse)
async def get_reddit_post(post_id: str):
    """
    Get a specific Reddit post by ID
    
    - **post_id**: Reddit post ID
    """
    try:
        reddit = get_reddit_client()
        post = reddit.get_post_content(post_id)
        
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
        reddit = get_reddit_client()
        all_posts = []
        errors = []
        
        for subreddit in subreddits[:10]:  # Limit to 10 subreddits
            try:
                posts = reddit.fetch_subreddit_posts(subreddit, sort_type, limit_per_sub)
                all_posts.extend(posts)
            except Exception as e:
                errors.append({"subreddit": subreddit, "error": str(e)})
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
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
        reddit = get_reddit_client()
        trending_subs = ["todayilearned", "AskReddit", "Showerthoughts", "LifeProTips", "explainlikeimfive"]
        
        all_posts = []
        posts_per_sub = max(1, limit // len(trending_subs))
        
        for sub in trending_subs:
            try:
                posts = reddit.fetch_subreddit_posts(sub, "hot", posts_per_sub)
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
        reddit = get_reddit_client()
        processor = get_text_processor()
        
        # Fetch post
        post = reddit.get_post_content(post_id)
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
        reddit = get_reddit_client()
        is_valid = reddit.validate_subreddit(name)
        
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
