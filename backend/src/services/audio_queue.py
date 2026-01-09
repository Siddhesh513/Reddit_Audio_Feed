"""
Audio Queue Service
Manages queue of posts to be converted to audio
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from src.services.audio_generator import get_audio_generator
from src.services.reddit_service import get_reddit_client
from src.config.settings import config
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class QueueStatus(Enum):
    """Queue item status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AudioQueue:
    """Manage queue of posts for audio generation"""
    
    def __init__(self):
        """Initialize audio queue"""
        self.queue_file = Path(config.DATA_DIR) / 'audio_queue.json'
        self.queue = self._load_queue()
        self.audio_generator = None  # Lazy load
        self.reddit_client = None  # Lazy load
        
        logger.info("Audio queue initialized")
    
    def add_post(self, post: Dict[str, Any], priority: int = 5) -> str:
        """
        Add a post to the queue
        
        Args:
            post: Reddit post dictionary
            priority: Priority level (1-10, higher = more important)
            
        Returns:
            Queue item ID
        """
        queue_id = f"{post.get('id', 'unknown')}_{int(time.time())}"
        
        queue_item = {
            'id': queue_id,
            'post_id': post.get('id'),
            'post_data': post,
            'priority': max(1, min(10, priority)),  # Clamp to 1-10
            'status': QueueStatus.PENDING.value,
            'added_at': datetime.now().isoformat(),
            'processed_at': None,
            'attempts': 0,
            'error': None,
            'result': None
        }
        
        self.queue[queue_id] = queue_item
        self._save_queue()
        
        logger.info(f"Added post {post.get('id')} to queue with priority {priority}")
        return queue_id
    
    async def add_subreddit_posts(
        self,
        subreddit: str,
        sort_type: str = 'hot',
        limit: int = 10,
        min_score: int = 0
    ) -> List[str]:
        """
        Add posts from a subreddit to the queue
        
        Args:
            subreddit: Subreddit name
            sort_type: Sort type (hot, new, top)
            limit: Number of posts to fetch
            min_score: Minimum score to include
            
        Returns:
            List of queue IDs
        """
        if not self.reddit_client:
            self.reddit_client = await get_reddit_client()

        queue_ids = []

        # Fetch posts
        posts = await self.reddit_client.fetch_subreddit_posts(subreddit, sort_type, limit)
        
        for post in posts:
            # Filter by score
            if post.get('score', 0) >= min_score:
                # Higher score = higher priority
                priority = min(10, max(1, post.get('score', 0) // 100))
                queue_id = self.add_post(post, priority)
                queue_ids.append(queue_id)
        
        logger.info(f"Added {len(queue_ids)} posts from r/{subreddit} to queue")
        return queue_ids
    
    def process_queue(
        self,
        max_items: Optional[int] = None,
        engine_type: str = 'gtts'
    ) -> Dict[str, Any]:
        """
        Process pending items in the queue
        
        Args:
            max_items: Maximum items to process
            engine_type: TTS engine to use
            
        Returns:
            Processing statistics
        """
        if not self.audio_generator:
            self.audio_generator = get_audio_generator(engine_type)
        
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Get pending items sorted by priority
        pending_items = self.get_pending_items()
        
        if max_items:
            pending_items = pending_items[:max_items]
        
        logger.info(f"Processing {len(pending_items)} items from queue")
        
        for item in pending_items:
            queue_id = item['id']
            post = item['post_data']
            
            # Update status to processing
            self.update_status(queue_id, QueueStatus.PROCESSING)
            
            try:
                # Generate audio
                result = self.audio_generator.generate_from_post(post)
                
                if result.get('success'):
                    self.update_status(queue_id, QueueStatus.COMPLETED, result=result)
                    stats['successful'] += 1
                    logger.success(f"✅ Processed: {post.get('title', '')[:50]}")
                else:
                    self.update_status(queue_id, QueueStatus.FAILED, error=result.get('error'))
                    stats['failed'] += 1
                    logger.error(f"❌ Failed: {post.get('title', '')[:50]}")
                
            except Exception as e:
                self.update_status(queue_id, QueueStatus.FAILED, error=str(e))
                stats['failed'] += 1
                logger.error(f"Error processing queue item {queue_id}: {e}")
            
            stats['processed'] += 1
            
            # Progress update
            if stats['processed'] % 5 == 0:
                logger.info(f"Progress: {stats['processed']}/{len(pending_items)}")
        
        stats['end_time'] = datetime.now().isoformat()
        
        # Log summary
        logger.info(f"\nQueue Processing Complete:")
        logger.info(f"  Processed: {stats['processed']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        
        return stats
    
    def get_pending_items(self) -> List[Dict[str, Any]]:
        """
        Get pending items sorted by priority
        
        Returns:
            List of pending queue items
        """
        pending = [
            item for item in self.queue.values()
            if item['status'] == QueueStatus.PENDING.value
        ]
        
        # Sort by priority (descending) then by added time (ascending)
        pending.sort(key=lambda x: (-x['priority'], x['added_at']))
        
        return pending
    
    def update_status(
        self,
        queue_id: str,
        status: QueueStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update queue item status"""
        if queue_id in self.queue:
            self.queue[queue_id]['status'] = status.value
            self.queue[queue_id]['attempts'] += 1
            
            if status in [QueueStatus.COMPLETED, QueueStatus.FAILED]:
                self.queue[queue_id]['processed_at'] = datetime.now().isoformat()
            
            if result:
                self.queue[queue_id]['result'] = result
            
            if error:
                self.queue[queue_id]['error'] = error
            
            self._save_queue()
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            'total': len(self.queue),
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'by_priority': {},
            'by_subreddit': {}
        }
        
        for item in self.queue.values():
            # Count by status
            status = item['status']
            if status == QueueStatus.PENDING.value:
                stats['pending'] += 1
            elif status == QueueStatus.PROCESSING.value:
                stats['processing'] += 1
            elif status == QueueStatus.COMPLETED.value:
                stats['completed'] += 1
            elif status == QueueStatus.FAILED.value:
                stats['failed'] += 1
            
            # Count by priority
            priority = item['priority']
            if priority not in stats['by_priority']:
                stats['by_priority'][priority] = 0
            stats['by_priority'][priority] += 1
            
            # Count by subreddit
            subreddit = item['post_data'].get('subreddit', 'unknown')
            if subreddit not in stats['by_subreddit']:
                stats['by_subreddit'][subreddit] = 0
            stats['by_subreddit'][subreddit] += 1
        
        return stats
    
    def clear_completed(self) -> int:
        """
        Remove completed items from queue
        
        Returns:
            Number of items removed
        """
        to_remove = [
            queue_id for queue_id, item in self.queue.items()
            if item['status'] == QueueStatus.COMPLETED.value
        ]
        
        for queue_id in to_remove:
            del self.queue[queue_id]
        
        if to_remove:
            self._save_queue()
            logger.info(f"Cleared {len(to_remove)} completed items from queue")
        
        return len(to_remove)
    
    def retry_failed(self) -> List[str]:
        """
        Reset failed items to pending for retry
        
        Returns:
            List of queue IDs reset
        """
        reset_ids = []
        
        for queue_id, item in self.queue.items():
            if item['status'] == QueueStatus.FAILED.value and item['attempts'] < 3:
                item['status'] = QueueStatus.PENDING.value
                item['error'] = None
                reset_ids.append(queue_id)
        
        if reset_ids:
            self._save_queue()
            logger.info(f"Reset {len(reset_ids)} failed items for retry")
        
        return reset_ids
    
    def _load_queue(self) -> Dict:
        """Load queue from file"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading queue: {e}")
        return {}
    
    def _save_queue(self):
        """Save queue to file"""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(self.queue, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving queue: {e}")


# Singleton instance
_audio_queue = None

def get_audio_queue() -> AudioQueue:
    """Get or create audio queue instance"""
    global _audio_queue
    if _audio_queue is None:
        _audio_queue = AudioQueue()
    return _audio_queue
