"""
Statistics API Routes
Endpoints for system statistics and monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.api.models import StatsResponse
from src.services.audio_manager import get_audio_manager
from src.services.audio_queue import get_audio_queue
from src.services.storage_service import get_storage_service
from src.utils.loggers import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/summary", response_model=StatsResponse)
async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        # Get audio statistics
        audio_manager = get_audio_manager()
        audio_stats = audio_manager.get_storage_summary()
        
        # Get queue statistics
        queue = get_audio_queue()
        queue_stats = queue.get_queue_stats()
        
        # Get storage statistics
        storage = get_storage_service()
        storage_stats = storage.get_storage_stats()
        
        # Calculate storage percentage (mock calculation)
        total_storage_mb = 1000  # Assume 1GB allocation
        used_storage_mb = audio_stats.get('total_size_mb', 0)
        storage_percentage = (used_storage_mb / total_storage_mb) * 100
        
        # Get recent activity
        recent_audio = audio_manager.get_recent_audio(hours=24, limit=5)
        recent_activity = [
            {
                "type": "audio_generated",
                "filename": audio.get('filename'),
                "timestamp": audio.get('generated_at'),
                "subreddit": audio.get('subreddit')
            }
            for audio in recent_audio
        ]
        
        return StatsResponse(
            success=True,
            message="Statistics retrieved successfully",
            audio_files=audio_stats.get('total_files', 0),
            total_duration_minutes=audio_stats.get('total_duration_minutes', 0),
            total_size_mb=audio_stats.get('total_size_mb', 0),
            posts_processed=queue_stats.get('completed', 0),
            queue_items=queue_stats.get('total', 0),
            storage_used_percentage=min(100, storage_percentage),
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio")
async def get_audio_stats():
    """Get detailed audio statistics"""
    try:
        manager = get_audio_manager()
        summary = manager.get_storage_summary()
        
        # Add more detailed stats
        by_format = summary.get('by_format', {})
        
        return {
            "success": True,
            "total_files": summary.get('total_files', 0),
            "total_size_mb": summary.get('total_size_mb', 0),
            "total_duration_minutes": summary.get('total_duration_minutes', 0),
            "average_file_size_mb": summary.get('average_file_size_mb', 0),
            "average_duration_seconds": summary.get('average_duration', 0),
            "by_format": by_format,
            "oldest_file": summary.get('oldest_file'),
            "newest_file": summary.get('newest_file')
        }
        
    except Exception as e:
        logger.error(f"Error getting audio stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue")
async def get_queue_stats():
    """Get detailed queue statistics"""
    try:
        queue = get_audio_queue()
        stats = queue.get_queue_stats()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        storage = get_storage_service()
        stats = storage.get_storage_stats()
        
        return {
            "success": True,
            "storage_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Detailed health check of all services"""
    try:
        health_status = {
            "api": "healthy",
            "services": {}
        }
        
        # Check audio service
        try:
            manager = get_audio_manager()
            health_status["services"]["audio_manager"] = "healthy"
        except:
            health_status["services"]["audio_manager"] = "unhealthy"
        
        # Check queue service
        try:
            queue = get_audio_queue()
            health_status["services"]["queue"] = "healthy"
        except:
            health_status["services"]["queue"] = "unhealthy"
        
        # Check storage service
        try:
            storage = get_storage_service()
            health_status["services"]["storage"] = "healthy"
        except:
            health_status["services"]["storage"] = "unhealthy"
        
        # Overall health
        all_healthy = all(s == "healthy" for s in health_status["services"].values())
        health_status["overall"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "overall": "unhealthy",
            "error": str(e)
        }
