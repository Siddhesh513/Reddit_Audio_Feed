"""
Audio API Routes
Endpoints for audio generation and management
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

from src.api.models import (
    AudioGenerateRequest,
    AudioGenerateResponse,
    BaseResponse,
    ErrorResponse
)
from src.services.audio_generator import get_audio_generator
from src.services.audio_manager import get_audio_manager
from src.services.reddit_service import get_reddit_client
from src.config.settings import config
from src.utils.loggers import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=AudioGenerateResponse)
async def generate_audio(
    request: AudioGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate audio from Reddit post or text

    Accepts one of:
    - **post_id**: Reddit post ID to fetch and convert
    - **post_data**: Complete post data dictionary
    - **text**: Raw text to convert
    """
    try:
        generator = get_audio_generator(request.engine)

        # Determine source of content
        if request.post_id:
            # Fetch post from Reddit
            reddit = get_reddit_client()
            post = reddit.get_post_content(request.post_id)
            if not post:
                raise HTTPException(
                    status_code=404, detail=f"Post {request.post_id} not found")
        elif request.post_data:
            post = request.post_data
        elif request.text:
            # Create a pseudo-post from raw text
            post = {
                'id': 'custom_text',
                'title': request.text[:100],
                'selftext': request.text if len(request.text) > 100 else '',
                'subreddit': 'custom',
                'author': 'user',
                'score': 0
            }
        else:
            raise HTTPException(
                status_code=400, detail="Must provide post_id, post_data, or text")

        # Generate audio
        result = generator.generate_from_post(
            post,
            voice=request.voice,
            speed=request.speed,
            force_regenerate=True
        )

        if result.get('success'):
            # Build download URL
            filename = result.get('filename')
            download_url = f"/api/audio/download/{filename}"

            return AudioGenerateResponse(
                success=True,
                message="Audio generated successfully",
                filename=filename,
                duration_seconds=result.get('duration_seconds'),
                file_size_bytes=result.get('file_size_bytes'),
                download_url=download_url,
                post_id=post.get('id')
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Audio generation failed')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_audio(filename: str):
    """
    Download an audio file

    - **filename**: Name of the audio file
    """
    try:
        # Sanitize filename
        filename = os.path.basename(filename)

        # Check in main audio directory
        file_path = Path(config.DATA_AUDIO_PATH) / filename

        # Also check in organized folders
        if not file_path.exists():
            organized_path = Path(config.DATA_AUDIO_PATH) / 'organized'
            for possible_file in organized_path.rglob(filename):
                file_path = possible_file
                break

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Audio file {filename} not found")

        # Return file
        return FileResponse(
            path=file_path,
            media_type='audio/mpeg',
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{filename}")
async def stream_audio(filename: str):
    """
    Stream an audio file for playback

    - **filename**: Name of the audio file
    """
    try:
        filename = os.path.basename(filename)
        file_path = Path(config.DATA_AUDIO_PATH) / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Audio file {filename} not found")

        def iterfile():
            with open(file_path, 'rb') as f:
                yield from f

        return StreamingResponse(
            iterfile(),
            media_type='audio/mpeg',
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Accept-Ranges": "bytes",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_audio_files(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    subreddit: Optional[str] = None
):
    """
    List available audio files

    - **limit**: Maximum number of files to return
    - **offset**: Number of files to skip
    - **subreddit**: Filter by subreddit
    """
    try:
        manager = get_audio_manager()

        if subreddit:
            files = manager.get_audio_by_subreddit(subreddit)
        else:
            files = manager.get_recent_audio(hours=24*7, limit=limit+offset)

        # Apply pagination
        paginated = files[offset:offset+limit]

        return {
            "success": True,
            "files": paginated,
            "total": len(files),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing audio files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{filename}")
async def delete_audio(filename: str):
    """
    Delete an audio file

    - **filename**: Name of the audio file to delete
    """
    try:
        filename = os.path.basename(filename)
        file_path = Path(config.DATA_AUDIO_PATH) / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Audio file {filename} not found")

        # Delete file
        file_path.unlink()

        return BaseResponse(
            success=True,
            message=f"Audio file {filename} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-generate")
async def batch_generate_audio(
    background_tasks: BackgroundTasks,
    post_ids: List[str],
    voice: Optional[str] = "en-US",
    speed: float = 1.0,

):
    """
    Generate audio for multiple posts

    - **post_ids**: List of Reddit post IDs
    - **voice**: Voice to use for all posts
    - **speed**: Speech speed
    """
    try:
        if len(post_ids) > 20:
            raise HTTPException(
                status_code=400, detail="Maximum 20 posts per batch")

        # This could be moved to a background task for better performance
        reddit = get_reddit_client()
        generator = get_audio_generator('gtts')

        results = []
        for post_id in post_ids:
            try:
                post = reddit.get_post_content(post_id)
                if post:
                    result = generator.generate_from_post(
                        post, voice=voice, speed=speed)
                    results.append({
                        "post_id": post_id,
                        "success": result.get('success', False),
                        "filename": result.get('filename'),
                        "error": result.get('error')
                    })
                else:
                    results.append({
                        "post_id": post_id,
                        "success": False,
                        "error": "Post not found"
                    })
            except Exception as e:
                results.append({
                    "post_id": post_id,
                    "success": False,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r['success'])

        return {
            "success": True,
            "message": f"Generated {successful}/{len(post_ids)} audio files",
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{filename}")
async def get_audio_info(filename: str):
    """
    Get information about an audio file

    - **filename**: Name of the audio file
    """
    try:
        manager = get_audio_manager()

        # Try to find by filename in metadata
        for post_id, info in manager.metadata.items():
            if info.get('filename') == filename:
                return {
                    "success": True,
                    "file_info": info,
                    "post_id": post_id
                }

        raise HTTPException(
            status_code=404, detail=f"Audio file {filename} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting info for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
