"""
Queue API Routes
Endpoints for queue management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional

from src.api.models import (
    QueueAddRequest,
    QueueStatusResponse,
    QueueProcessRequest,
    BaseResponse
)
from src.services.audio_queue import get_audio_queue
from src.utils.loggers import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get current queue status and statistics"""
    try:
        queue = get_audio_queue()
        stats = queue.get_queue_stats()
        
        return QueueStatusResponse(
            success=True,
            message="Queue status retrieved",
            total=stats['total'],
            pending=stats['pending'],
            processing=stats['processing'],
            completed=stats['completed'],
            failed=stats['failed'],
            by_priority=stats.get('by_priority', {}),
            by_subreddit=stats.get('by_subreddit', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_to_queue(request: QueueAddRequest):
    """
    Add posts to the processing queue
    
    Can provide:
    - **subreddit**: Fetch and queue posts from a subreddit
    - **post_ids**: Queue specific post IDs
    - **posts**: Queue complete post data
    """
    try:
        queue = get_audio_queue()
        queue_ids = []
        
        if request.subreddit:
            # Add posts from subreddit
            queue_ids = queue.add_subreddit_posts(
                request.subreddit,
                limit=request.limit or 10,
                min_score=0
            )
        elif request.post_ids:
            # Add specific posts
            for post_id in request.post_ids:
                queue_id = queue.add_post(
                    {'id': post_id},
                    priority=request.priority
                )
                queue_ids.append(queue_id)
        elif request.posts:
            # Add complete post data
            for post in request.posts:
                queue_id = queue.add_post(post, priority=request.priority)
                queue_ids.append(queue_id)
        else:
            raise HTTPException(status_code=400, detail="Must provide subreddit, post_ids, or posts")
        
        return {
            "success": True,
            "message": f"Added {len(queue_ids)} items to queue",
            "queue_ids": queue_ids,
            "total_in_queue": queue.get_queue_stats()['total']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_queue(
    request: QueueProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Process items in the queue
    
    - **max_items**: Maximum number of items to process
    - **engine**: TTS engine to use
    """
    try:
        queue = get_audio_queue()
        
        # Get pending count before processing
        pending_before = queue.get_queue_stats()['pending']
        
        if pending_before == 0:
            return {
                "success": True,
                "message": "No items to process",
                "processed": 0
            }
        
        # Process queue (in production, this should be a background task)
        results = queue.process_queue(
            max_items=request.max_items,
            engine_type=request.engine
        )
        
        return {
            "success": True,
            "message": f"Processed {results['processed']} items",
            "processed": results['processed'],
            "successful": results['successful'],
            "failed": results['failed']
        }
        
    except Exception as e:
        logger.error(f"Error processing queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_queue(status: Optional[str] = Query(None, description="Status to clear: completed, failed, all")):
    """
    Clear items from the queue
    
    - **status**: Which items to clear (completed, failed, or all)
    """
    try:
        queue = get_audio_queue()
        
        if status == "completed":
            cleared = queue.clear_completed()
            message = f"Cleared {cleared} completed items"
        elif status == "failed":
            # Reset failed items to pending for retry
            reset = queue.retry_failed()
            message = f"Reset {len(reset)} failed items for retry"
            cleared = len(reset)
        elif status == "all":
            # Clear entire queue
            before = len(queue.queue)
            queue.queue = {}
            queue._save_queue()
            cleared = before
            message = f"Cleared all {cleared} items from queue"
        else:
            raise HTTPException(status_code=400, detail="Status must be: completed, failed, or all")
        
        return BaseResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items")
async def get_queue_items(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get items in the queue
    
    - **status**: Filter by status (pending, processing, completed, failed)
    - **limit**: Maximum number of items to return
    """
    try:
        queue = get_audio_queue()
        
        items = list(queue.queue.values())
        
        # Filter by status if provided
        if status:
            items = [item for item in items if item['status'] == status]
        
        # Sort by priority and added time
        items.sort(key=lambda x: (-x.get('priority', 5), x.get('added_at', '')))
        
        # Limit results
        items = items[:limit]
        
        return {
            "success": True,
            "items": items,
            "total": len(items)
        }
        
    except Exception as e:
        logger.error(f"Error getting queue items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
