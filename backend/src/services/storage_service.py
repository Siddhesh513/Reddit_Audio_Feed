"""
Storage Service Module
Handles saving and loading Reddit posts to/from JSON files
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.config.settings import config
from src.utils.loggers import get_logger
from src.models.reddit_post import RedditPost, PostCollection

logger = get_logger(__name__)


class StorageService:
    """Service for managing post storage"""

    def __init__(self):
        """Initialize storage service"""
        self.raw_data_path = Path(config.DATA_RAW_PATH)
        self.processed_data_path = Path(config.DATA_PROCESSED_PATH)
        self.audio_data_path = Path(config.DATA_AUDIO_PATH)

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all data directories exist"""
        for path in [self.raw_data_path, self.processed_data_path, self.audio_data_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")

    def save_posts(self, posts: List[Dict], subreddit: str, filename: Optional[str] = None) -> str:
        """
        Save posts to JSON file

        Args:
            posts: List of post dictionaries
            subreddit: Name of the subreddit
            filename: Optional custom filename

        Returns:
            Path to the saved file
        """
        if not posts:
            logger.warning("No posts to save")
            return ""

        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{subreddit}_{timestamp}.json"

        filepath = self.raw_data_path / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)

            logger.success(f"Saved {len(posts)} posts to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving posts to {filepath}: {e}")
            raise

    def load_posts(self, filename: str) -> List[Dict]:
        """
        Load posts from JSON file

        Args:
            filename: Name of the file to load

        Returns:
            List of post dictionaries
        """
        filepath = self.raw_data_path / filename

        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                posts = json.load(f)

            logger.info(f"Loaded {len(posts)} posts from {filepath}")
            return posts

        except Exception as e:
            logger.error(f"Error loading posts from {filepath}: {e}")
            return []

    def save_post_collection(self, collection: PostCollection, filename: Optional[str] = None) -> str:
        """
        Save a PostCollection to JSON file

        Args:
            collection: PostCollection object
            filename: Optional custom filename

        Returns:
            Path to the saved file
        """
        if not collection.posts:
            logger.warning("No posts in collection to save")
            return ""

        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # First 3 unique subreddits
            subreddits = "_".join(
                set(p.subreddit for p in collection.posts[:3]))
            filename = f"collection_{subreddits}_{timestamp}.json"

        filepath = self.processed_data_path / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(collection.to_json())

            logger.success(
                f"Saved collection with {len(collection.posts)} posts to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving collection to {filepath}: {e}")
            raise

    def load_post_collection(self, filename: str) -> Optional[PostCollection]:
        """
        Load a PostCollection from JSON file

        Args:
            filename: Name of the file to load

        Returns:
            PostCollection object or None if error
        """
        # Try both raw and processed directories
        for base_path in [self.processed_data_path, self.raw_data_path]:
            filepath = base_path / filename

            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json_str = f.read()

                    collection = PostCollection.from_json(json_str)
                    logger.info(
                        f"Loaded collection with {len(collection.posts)} posts from {filepath}")
                    return collection

                except Exception as e:
                    logger.error(
                        f"Error loading collection from {filepath}: {e}")
                    return None

        logger.error(f"File not found in any data directory: {filename}")
        return None

    def list_saved_files(self, directory: str = "raw") -> List[Dict[str, Any]]:
        """
        List all saved JSON files

        Args:
            directory: Which directory to list ('raw', 'processed', 'audio')

        Returns:
            List of file information dictionaries
        """
        if directory == "raw":
            path = self.raw_data_path
        elif directory == "processed":
            path = self.processed_data_path
        elif directory == "audio":
            path = self.audio_data_path
        else:
            logger.error(f"Invalid directory: {directory}")
            return []

        files = []
        for filepath in path.glob("*.json"):
            stat = filepath.stat()
            files.append({
                "filename": filepath.name,
                "path": str(filepath),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })

        files.sort(key=lambda x: x["modified"], reverse=True)
        logger.info(f"Found {len(files)} files in {directory} directory")
        return files

    def cleanup_old_files(self, days: int = 7, directory: str = "raw") -> int:
        """
        Remove files older than specified days

        Args:
            days: Number of days to keep files
            directory: Which directory to clean

        Returns:
            Number of files deleted
        """
        if directory == "raw":
            path = self.raw_data_path
        elif directory == "processed":
            path = self.processed_data_path
        else:
            logger.error(f"Invalid directory for cleanup: {directory}")
            return 0

        deleted = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for filepath in path.glob("*.json"):
            if filepath.stat().st_mtime < cutoff:
                try:
                    filepath.unlink()
                    deleted += 1
                    logger.info(f"Deleted old file: {filepath.name}")
                except Exception as e:
                    logger.error(f"Error deleting {filepath}: {e}")

        logger.info(
            f"Cleanup completed: deleted {deleted} files older than {days} days")
        return deleted

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about storage usage"""
        stats = {}

        for name, path in [("raw", self.raw_data_path),
                           ("processed", self.processed_data_path),
                           ("audio", self.audio_data_path)]:

            files = list(path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            stats[name] = {
                "file_count": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2)
            }

        return stats


# Create a singleton instance
_storage_service = None


def get_storage_service() -> StorageService:
    """Get or create storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
