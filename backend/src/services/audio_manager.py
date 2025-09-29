"""
Audio Manager Service
Manages audio file organization, metadata, and retrieval
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import mimetypes
from src.config.settings import config
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class AudioManager:
    """Manage audio files and their metadata"""
    
    def __init__(self):
        """Initialize audio manager"""
        self.audio_dir = Path(config.DATA_AUDIO_PATH)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Organize by date and subreddit
        self.organized_dir = self.audio_dir / 'organized'
        self.organized_dir.mkdir(exist_ok=True)
        
        # Metadata database
        self.metadata_file = self.audio_dir / 'audio_metadata.json'
        self.metadata = self._load_metadata()
        
        logger.info("Audio manager initialized")
    
    def organize_audio_files(self) -> Dict[str, int]:
        """
        Organize audio files into folders by date and subreddit
        
        Returns:
            Statistics about organized files
        """
        stats = {
            'files_organized': 0,
            'folders_created': 0,
            'errors': 0
        }
        
        # Get all MP3 files in root audio directory
        audio_files = list(self.audio_dir.glob('*.mp3'))
        
        for audio_file in audio_files:
            try:
                # Get file metadata
                file_stat = audio_file.stat()
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                # Extract subreddit from filename (format: subreddit_title_timestamp.mp3)
                filename_parts = audio_file.stem.split('_')
                subreddit = filename_parts[0] if filename_parts else 'unknown'
                
                # Create organized path: organized/YYYY-MM-DD/subreddit/
                date_folder = file_date.strftime('%Y-%m-%d')
                target_dir = self.organized_dir / date_folder / subreddit
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file
                target_path = target_dir / audio_file.name
                if not target_path.exists():
                    shutil.move(str(audio_file), str(target_path))
                    stats['files_organized'] += 1
                    logger.debug(f"Organized: {audio_file.name} -> {date_folder}/{subreddit}/")
                
            except Exception as e:
                logger.error(f"Error organizing {audio_file.name}: {e}")
                stats['errors'] += 1
        
        # Count folders created
        stats['folders_created'] = sum(1 for _ in self.organized_dir.rglob('*/'))
        
        logger.info(f"Organization complete: {stats['files_organized']} files organized")
        return stats
    
    def get_audio_by_post_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get audio file information by post ID
        
        Args:
            post_id: Reddit post ID
            
        Returns:
            Audio file information or None
        """
        if post_id in self.metadata:
            audio_info = self.metadata[post_id].copy()
            
            # Check if file exists
            file_path = audio_info.get('file_path')
            if file_path and Path(file_path).exists():
                audio_info['exists'] = True
                audio_info['file_size_current'] = Path(file_path).stat().st_size
            else:
                audio_info['exists'] = False
            
            return audio_info
        
        return None
    
    def get_audio_by_subreddit(self, subreddit: str) -> List[Dict[str, Any]]:
        """
        Get all audio files for a subreddit
        
        Args:
            subreddit: Subreddit name
            
        Returns:
            List of audio file information
        """
        audio_files = []
        
        for post_id, info in self.metadata.items():
            if info.get('subreddit', '').lower() == subreddit.lower():
                info['post_id'] = post_id
                audio_files.append(info)
        
        # Sort by creation time
        audio_files.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        return audio_files
    
    def get_recent_audio(self, hours: int = 24, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recently generated audio files
        
        Args:
            hours: How many hours back to look
            limit: Maximum number of files to return
            
        Returns:
            List of recent audio files
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_files = []
        
        for post_id, info in self.metadata.items():
            generated_at = info.get('generated_at', '')
            if generated_at:
                try:
                    file_time = datetime.fromisoformat(generated_at)
                    if file_time > cutoff:
                        info['post_id'] = post_id
                        recent_files.append(info)
                except:
                    pass
        
        # Sort by generation time
        recent_files.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        if limit:
            recent_files = recent_files[:limit]
        
        return recent_files
    
    def create_playlist(self, audio_files: List[Dict[str, Any]], name: str = "playlist") -> str:
        """
        Create an M3U playlist file
        
        Args:
            audio_files: List of audio file information
            name: Playlist name
            
        Returns:
            Path to playlist file
        """
        playlist_path = self.audio_dir / f"{name}.m3u"
        
        with open(playlist_path, 'w') as f:
            f.write("#EXTM3U\n")
            
            for audio in audio_files:
                if audio.get('file_path') and Path(audio['file_path']).exists():
                    duration = int(audio.get('duration_seconds', 0))
                    title = audio.get('title', 'Unknown Title')[:50]
                    
                    f.write(f"#EXTINF:{duration},{title}\n")
                    f.write(f"{audio['file_path']}\n")
        
        logger.info(f"Created playlist: {playlist_path} with {len(audio_files)} tracks")
        return str(playlist_path)
    
    def get_storage_summary(self) -> Dict[str, Any]:
        """
        Get summary of audio storage usage
        
        Returns:
            Storage summary statistics
        """
        summary = {
            'total_files': 0,
            'total_size_bytes': 0,
            'total_duration_seconds': 0,
            'by_format': {},
            'by_date': {},
            'oldest_file': None,
            'newest_file': None,
            'average_file_size': 0,
            'average_duration': 0
        }
        
        # Scan all audio files
        audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg']
        all_files = []
        
        for ext in audio_extensions:
            all_files.extend(self.audio_dir.rglob(f'*{ext}'))
        
        if not all_files:
            return summary
        
        file_dates = []
        total_size = 0
        total_duration = 0
        
        for audio_file in all_files:
            try:
                stat = audio_file.stat()
                total_size += stat.st_size
                file_dates.append(stat.st_mtime)
                
                # Count by format
                ext = audio_file.suffix.lower()
                if ext not in summary['by_format']:
                    summary['by_format'][ext] = 0
                summary['by_format'][ext] += 1
                
                # Get duration from metadata if available
                for info in self.metadata.values():
                    if info.get('filename') == audio_file.name:
                        total_duration += info.get('duration_seconds', 0)
                        break
                
            except Exception as e:
                logger.error(f"Error processing {audio_file}: {e}")
        
        # Calculate summary
        summary['total_files'] = len(all_files)
        summary['total_size_bytes'] = total_size
        summary['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        summary['total_duration_seconds'] = total_duration
        summary['total_duration_minutes'] = round(total_duration / 60, 1)
        
        if file_dates:
            summary['oldest_file'] = datetime.fromtimestamp(min(file_dates)).isoformat()
            summary['newest_file'] = datetime.fromtimestamp(max(file_dates)).isoformat()
        
        if summary['total_files'] > 0:
            summary['average_file_size'] = total_size // summary['total_files']
            summary['average_file_size_mb'] = round(summary['average_file_size'] / (1024 * 1024), 2)
            summary['average_duration'] = total_duration / summary['total_files']
        
        return summary
    
    def export_metadata(self, output_path: Optional[str] = None) -> str:
        """
        Export metadata to JSON file
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to exported file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.audio_dir / f'metadata_export_{timestamp}.json'
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_entries': len(self.metadata),
            'audio_files': self.metadata
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported metadata to {output_path}")
        return str(output_path)
    
    def _load_metadata(self) -> Dict:
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {}
    
    def cleanup_orphaned_files(self) -> int:
        """
        Remove audio files that don't have metadata entries
        
        Returns:
            Number of files removed
        """
        removed = 0
        audio_files = list(self.audio_dir.glob('*.mp3'))
        
        # Get all filenames from metadata
        metadata_filenames = set()
        for info in self.metadata.values():
            if info.get('filename'):
                metadata_filenames.add(info['filename'])
        
        for audio_file in audio_files:
            if audio_file.name not in metadata_filenames:
                try:
                    audio_file.unlink()
                    removed += 1
                    logger.info(f"Removed orphaned file: {audio_file.name}")
                except Exception as e:
                    logger.error(f"Error removing {audio_file.name}: {e}")
        
        if removed > 0:
            logger.info(f"Cleanup complete: removed {removed} orphaned files")
        
        return removed


# Singleton instance
_audio_manager = None

def get_audio_manager() -> AudioManager:
    """Get or create audio manager instance"""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager
