"""
Audio Generator Service
Manages audio generation from processed Reddit posts
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from src.services.tts_engine import get_tts_engine, TTSEngine
from src.services.text_processor import get_text_processor
from src.services.content_filter import get_content_filter
from src.services.tts_preprocessor import get_tts_preprocessor
from src.models.reddit_post import RedditPost, PostCollection
from src.config.settings import config
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class AudioGenerator:
    """Generate audio files from Reddit posts"""

    def __init__(self, engine_type: str = 'gtts', engine_config: Optional[Dict] = None):
        """
        Initialize audio generator

        Args:
            engine_type: TTS engine to use ('gtts', 'kokoro', 'mock')
            engine_config: Configuration for the TTS engine
        """
        self.engine_type = engine_type
        self.engine = get_tts_engine(engine_type, engine_config)
        self.text_processor = get_text_processor()
        self.content_filter = get_content_filter()
        self.tts_preprocessor = get_tts_preprocessor()

        # Audio output directory
        self.audio_dir = Path(config.DATA_AUDIO_PATH)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        # Metadata storage
        self.metadata_file = self.audio_dir / 'audio_metadata.json'
        self.metadata = self._load_metadata()

        logger.info(f"Audio generator initialized with {engine_type} engine")

    def generate_from_post(
        self,
        post: Dict[str, Any],
        voice: Optional[str] = None,
        speed: float = 1.0,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate audio from a single Reddit post

        Args:
            post: Reddit post dictionary
            voice: Voice to use
            speed: Speech speed
            force_regenerate: Regenerate even if audio exists

        Returns:
            Audio generation result
        """
        post_id = post.get('id', 'unknown')

        # Check if audio already exists
        if not force_regenerate and self._audio_exists(post_id):
            logger.info(f"Audio already exists for post {post_id}")
            return self.metadata.get(post_id, {})

        logger.info(
            f"Generating audio for post {post_id}: {post.get('title', '')[:50]}...")

        # Step 1: Process the post text
        processed_post = self.text_processor.process_post(post)

        # Step 2: Filter content
        filtered_post = self.content_filter.filter_post(processed_post)

        # Step 3: Preprocess for TTS
        tts_text = self.tts_preprocessor.preprocess_for_tts(
            filtered_post.get('tts_text', ''),
            {'expand_numbers': True, 'add_pauses': False}  # Change to False
        )

        # CRITICAL: Remove all SSML/XML tags for gTTS
        import re
        tts_text = re.sub(r'<[^>]+>', '', tts_text)  # Strip all XML/SSML tags
        tts_text = re.sub(r'\s+', ' ', tts_text)  # Clean up extra spaces

        # Check if safe for TTS
        if not self.content_filter.is_safe_for_tts(filtered_post):
            logger.warning(f"Post {post_id} not safe for TTS")
            return {
                'post_id': post_id,
                'success': False,
                'reason': 'Content filtered as unsafe'
            }

        # Step 4: Generate filename
        filename = self._generate_filename(post, filtered_post)
        output_path = str(self.audio_dir / filename)

        # Step 5: Generate audio
        try:
            result = self.engine.generate_audio(
                text=tts_text,
                output_path=output_path,
                voice=voice,
                speed=speed
            )

            if result.get('success'):
                # Add post metadata
                result.update({
                    'post_id': post_id,
                    'title': post.get('title', ''),
                    'subreddit': post.get('subreddit', ''),
                    'author': post.get('author', ''),
                    'created_utc': post.get('created_utc', ''),
                    'generated_at': datetime.now().isoformat(),
                    'filename': filename,
                    'text_hash': self._hash_text(tts_text),
                    'content_warnings': filtered_post.get('content_warnings', [])
                })

                # Save metadata
                self._save_audio_metadata(post_id, result)

                logger.success(f"✅ Audio generated: {filename}")
            else:
                logger.error(f"❌ Audio generation failed for post {post_id}")

            return result

        except Exception as e:
            logger.error(f"Error generating audio for post {post_id}: {e}")
            return {
                'post_id': post_id,
                'success': False,
                'error': str(e)
            }

    def generate_batch(
        self,
        posts: List[Dict[str, Any]],
        voice: Optional[str] = None,
        speed: float = 1.0,
        max_posts: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate audio for multiple posts

        Args:
            posts: List of Reddit posts
            voice: Voice to use
            speed: Speech speed
            max_posts: Maximum number of posts to process

        Returns:
            List of generation results
        """
        results = []
        posts_to_process = posts[:max_posts] if max_posts else posts

        logger.info(
            f"Starting batch audio generation for {len(posts_to_process)} posts")

        for i, post in enumerate(posts_to_process, 1):
            logger.info(f"Processing post {i}/{len(posts_to_process)}")

            result = self.generate_from_post(post, voice, speed)
            results.append(result)

            # Log progress
            if i % 5 == 0:
                successful = sum(1 for r in results if r.get('success'))
                logger.info(
                    f"Progress: {i}/{len(posts_to_process)} posts, {successful} successful")

        # Summary
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful

        logger.info(f"\nBatch generation complete:")
        logger.info(f"  ✅ Successful: {successful}")
        logger.info(f"  ❌ Failed: {failed}")
        logger.info(f"  📊 Success rate: {successful/len(results)*100:.1f}%")

        return results

    def _generate_filename(self, post: Dict, processed_post: Dict) -> str:
        """Generate filename for audio file"""
        # Use subreddit, truncated title, and timestamp
        subreddit = post.get('subreddit', 'unknown').lower()
        title = processed_post.get('processed_title', 'untitled')

        # Clean title for filename
        clean_title = ''.join(
            c for c in title if c.isalnum() or c in ' -')[:30]
        clean_title = clean_title.strip().replace(' ', '_')

        # Add timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create filename
        filename = f"{subreddit}_{clean_title}_{timestamp}.mp3"

        return filename.lower()

    def _audio_exists(self, post_id: str) -> bool:
        """Check if audio already exists for post"""
        if post_id in self.metadata:
            audio_path = self.metadata[post_id].get('file_path')
            if audio_path and Path(audio_path).exists():
                return True
        return False

    def _hash_text(self, text: str) -> str:
        """Generate hash of text for deduplication"""
        return hashlib.md5(text.encode()).hexdigest()[:8]

    def _load_metadata(self) -> Dict:
        """Load audio metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {}

    def _save_audio_metadata(self, post_id: str, metadata: Dict):
        """Save audio metadata"""
        self.metadata[post_id] = metadata
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def get_audio_stats(self) -> Dict:
        """Get statistics about generated audio"""
        stats = {
            'total_audio_files': 0,
            'total_duration_seconds': 0,
            'total_size_bytes': 0,
            'by_subreddit': {},
            'by_engine': {},
            'recent_files': []
        }

        for post_id, meta in self.metadata.items():
            if meta.get('success'):
                stats['total_audio_files'] += 1
                stats['total_duration_seconds'] += meta.get(
                    'duration_seconds', 0)
                stats['total_size_bytes'] += meta.get('file_size_bytes', 0)

                # By subreddit
                subreddit = meta.get('subreddit', 'unknown')
                if subreddit not in stats['by_subreddit']:
                    stats['by_subreddit'][subreddit] = 0
                stats['by_subreddit'][subreddit] += 1

                # By engine
                engine = meta.get('engine', 'unknown')
                if engine not in stats['by_engine']:
                    stats['by_engine'][engine] = 0
                stats['by_engine'][engine] += 1

        # Get recent files
        audio_files = list(self.audio_dir.glob('*.mp3'))
        audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        stats['recent_files'] = [f.name for f in audio_files[:5]]

        # Convert to human-readable
        stats['total_duration_minutes'] = stats['total_duration_seconds'] / 60
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)

        return stats

    def cleanup_old_audio(self, days: int = 7) -> int:
        """
        Remove audio files older than specified days

        Args:
            days: Number of days to keep files

        Returns:
            Number of files deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for audio_file in self.audio_dir.glob('*.mp3'):
            if audio_file.stat().st_mtime < cutoff:
                try:
                    audio_file.unlink()
                    deleted += 1
                    logger.info(f"Deleted old audio file: {audio_file.name}")

                    # Remove from metadata
                    for post_id, meta in list(self.metadata.items()):
                        if meta.get('filename') == audio_file.name:
                            del self.metadata[post_id]

                except Exception as e:
                    logger.error(f"Error deleting {audio_file}: {e}")

        if deleted > 0:
            self._save_audio_metadata('_cleanup', {'deleted': deleted})

        logger.info(
            f"Cleanup complete: deleted {deleted} audio files older than {days} days")
        return deleted


# Singleton instance
_audio_generator = None


def get_audio_generator(engine_type: str = 'gtts', config: Optional[Dict] = None) -> AudioGenerator:
    """Get or create audio generator instance"""
    global _audio_generator
    if _audio_generator is None or engine_type:
        _audio_generator = AudioGenerator(engine_type, config)
    return _audio_generator
