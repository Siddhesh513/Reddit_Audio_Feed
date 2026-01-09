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

    **Voice Options:**
    - English: en-US, en-GB, en-AU, en-IN, en-CA
    - Spanish: es-ES, es-MX
    - French: fr-FR, fr-CA
    - German: de-DE
    - Italian: it-IT
    - Japanese: ja-JP
    - Portuguese: pt-BR, pt-PT

    **Speed Options:**
    - 0.75: Slow, clear speech
    - 1.0: Normal speed (default)
    - 1.25: Fast, efficient listening
    - 1.5+: Very fast (may reduce clarity)

    **Note:** Speed adjustment requires ffmpeg. Install with:
    - macOS: `brew install ffmpeg`
    - Ubuntu: `apt-get install ffmpeg`
    - Windows: Download from ffmpeg.org
    """
    try:
        generator = get_audio_generator(request.engine)

        # Determine source of content
        if request.post_id:
            # Fetch post from Reddit
            reddit = await get_reddit_client()
            post = await reddit.get_post_content(request.post_id)
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
            language=request.language,
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


@router.post("/generate-with-comments")
async def generate_audio_with_comments(
    post_id: str,
    comment_limit: int = 3,
    voice: Optional[str] = None,
    speed: float = 1.0,
    language: Optional[str] = None
):
    """
    Generate audio for post and top comments with different voices

    Args:
        post_id: Reddit post ID
        comment_limit: Number of top comments to include (default: 3)
        voice: Voice for post narration (comments use different voices)
        speed: Playback speed
        language: Language override

    Returns:
        Segments list with audio files and metadata
    """
    try:
        # Fetch post with comments
        reddit = await get_reddit_client()
        post = await reddit.get_post_content(post_id, include_comments=True, comment_limit=comment_limit)

        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

        # Generate audio segments
        generator = get_audio_generator()
        result = generator.generate_with_comments(post, voice, speed, language)

        if result.get('success'):
            # Build download URLs for segments
            for segment in result.get('segments', []):
                if segment.get('audio_file'):
                    segment['download_url'] = f"/api/audio/download/{segment['audio_file']}"
                    segment['stream_url'] = f"/api/audio/stream/{segment['audio_file']}"

            return {
                "success": True,
                "post_id": post_id,
                "segments": result['segments'],
                "total_segments": result['total_segments'],
                "message": f"Generated {result['total_segments']} audio segments"
            }
        else:
            raise HTTPException(status_code=500, detail="Audio generation failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio with comments: {e}")
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

        # Check in main audio directory first
        file_path = Path(config.DATA_AUDIO_PATH) / filename

        # If not found, check in organized folders
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

        # Check in main audio directory first
        file_path = Path(config.DATA_AUDIO_PATH) / filename

        # If not found, check in organized folders
        if not file_path.exists():
            organized_path = Path(config.DATA_AUDIO_PATH) / 'organized'
            for possible_file in organized_path.rglob(filename):
                file_path = possible_file
                break

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

        # Fix file paths and ensure filename is present
        for file in files:
            # Extract filename from full path if needed
            if 'file_path' in file:
                file['filename'] = os.path.basename(file['file_path'])

            # Check if file exists in main directory or organized
            if 'filename' in file:
                main_path = Path(config.DATA_AUDIO_PATH) / file['filename']
                if main_path.exists():
                    file['exists'] = True
                else:
                    # Check in organized folders
                    organized_path = Path(config.DATA_AUDIO_PATH) / 'organized'
                    found = False
                    for possible_file in organized_path.rglob(file['filename']):
                        file['exists'] = True
                        found = True
                        break
                    if not found:
                        file['exists'] = False

        # Filter out non-existent files
        files = [f for f in files if f.get('exists', False)]

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
    language: Optional[str] = None
):
    """
    Generate audio for multiple posts

    - **post_ids**: List of Reddit post IDs
    - **voice**: Voice to use for all posts
    - **speed**: Speech speed
    - **language**: Optional language override
    """
    try:
        if len(post_ids) > 20:
            raise HTTPException(
                status_code=400, detail="Maximum 20 posts per batch")

        # This could be moved to a background task for better performance
        reddit = await get_reddit_client()
        generator = get_audio_generator('gtts')

        results = []
        for post_id in post_ids:
            try:
                post = await reddit.get_post_content(post_id)
                if post:
                    result = generator.generate_from_post(
                        post, voice=voice, speed=speed, language=language)
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


@router.get("/voices")
async def get_available_voices():
    """
    Get list of available TTS voices.

    Returns available voices with metadata including:
    - Voice ID
    - Language
    - Accent/Region
    - Display name

    Example response:
    {
        "voices": [
            {
                "id": "en-US",
                "name": "English (US)",
                "language": "en",
                "tld": "com"
            },
            ...
        ],
        "default_voice": "en-US",
        "speed_presets": {
            "slow": 0.75,
            "normal": 1.0,
            "fast": 1.25
        }
    }
    """
    try:
        voices = []
        for voice_id, voice_config in config.TTSConfig.GTTS_VOICES.items():
            voices.append({
                'id': voice_id,
                'name': voice_config['name'],
                'language': voice_config['language'],
                'tld': voice_config.get('tld', 'com')
            })

        return {
            'voices': voices,
            'default_voice': config.TTSConfig.DEFAULT_VOICE,
            'speed_presets': config.TTSConfig.SPEED_PRESETS,
            'speed_range': {
                'min': config.TTSConfig.MIN_SPEED,
                'max': config.TTSConfig.MAX_SPEED
            }
        }
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/speed-presets")
async def get_speed_presets():
    """
    Get available speech rate presets.

    Returns:
    {
        "slow": 0.75,
        "normal": 1.0,
        "fast": 1.25,
        "very_fast": 1.5
    }
    """
    try:
        return config.TTSConfig.SPEED_PRESETS
    except Exception as e:
        logger.error(f"Error fetching speed presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_tts_capabilities():
    """
    Get current TTS system capabilities and configuration.

    Returns information about:
    - Available engines
    - Speed adjustment support
    - Required dependencies status
    - Voice options

    Useful for frontend to adapt UI based on capabilities.
    """
    try:
        from src.utils.system_check import get_tts_capabilities

        caps = get_tts_capabilities()

        return {
            'engines': {
                'gtts': caps['gtts_available'],
                'kokoro': False,  # Placeholder
                'mock': True
            },
            'features': {
                'speed_adjustment': caps['speed_adjustment'],
                'voice_selection': True,
                'language_selection': True,
                'batch_generation': True
            },
            'dependencies': {
                'ffmpeg': caps['ffmpeg_installed'],
                'pydub': caps['pydub_available']
            },
            'voice_count': len(config.TTSConfig.GTTS_VOICES),
            'speed_range': {
                'min': config.TTSConfig.MIN_SPEED,
                'max': config.TTSConfig.MAX_SPEED
            },
            'warnings': [
                'Speed adjustment requires ffmpeg and pydub'
            ] if not caps['speed_adjustment'] else []
        }
    except Exception as e:
        logger.error(f"Error fetching capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
