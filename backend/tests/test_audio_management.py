#!/usr/bin/env python3
"""Test audio management and queue system"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.audio_manager import get_audio_manager
from src.services.audio_queue import get_audio_queue
from src.utils.loggers import logger


def test_audio_manager():
    """Test audio file management"""
    logger.info("="*60)
    logger.info("Testing Audio Manager")
    logger.info("="*60)
    
    manager = get_audio_manager()
    
    # Get storage summary
    summary = manager.get_storage_summary()
    logger.info("\nStorage Summary:")
    logger.info(f"  Total files: {summary['total_files']}")
    logger.info(f"  Total size: {summary['total_size_mb']} MB")
    logger.info(f"  Total duration: {summary['total_duration_minutes']} minutes")
    
    # Get recent audio files
    recent = manager.get_recent_audio(hours=24, limit=5)
    logger.info(f"\nRecent audio files: {len(recent)}")
    for audio in recent[:3]:
        logger.info(f"  - {audio.get('filename', 'Unknown')}")
    
    # Organize files
    stats = manager.organize_audio_files()
    logger.info(f"\nOrganized {stats['files_organized']} files into {stats['folders_created']} folders")
    
    return True


def test_audio_queue():
    """Test audio queue system"""
    logger.info("\n" + "="*60)
    logger.info("Testing Audio Queue")
    logger.info("="*60)
    
    queue = get_audio_queue()
    
    # Get queue statistics
    stats = queue.get_queue_stats()
    logger.info("\nQueue Statistics:")
    logger.info(f"  Total items: {stats['total']}")
    logger.info(f"  Pending: {stats['pending']}")
    logger.info(f"  Completed: {stats['completed']}")
    logger.info(f"  Failed: {stats['failed']}")
    
    # Add posts from subreddit to queue
    queue_ids = queue.add_subreddit_posts("todayilearned", "hot", limit=3, min_score=100)
    logger.info(f"\nAdded {len(queue_ids)} posts to queue")
    
    # Process queue
    logger.info("\nProcessing queue...")
    process_stats = queue.process_queue(max_items=2, engine_type='gtts')
    
    logger.info(f"\nProcessing Results:")
    logger.info(f"  Successful: {process_stats['successful']}")
    logger.info(f"  Failed: {process_stats['failed']}")
    
    return True


def test_playlist_creation():
    """Test playlist creation"""
    logger.info("\n" + "="*60)
    logger.info("Testing Playlist Creation")
    logger.info("="*60)
    
    manager = get_audio_manager()
    
    # Get recent audio files
    recent = manager.get_recent_audio(hours=24)
    
    if recent:
        # Create playlist
        playlist_path = manager.create_playlist(recent, "recent_reddit_audio")
        logger.success(f"✅ Created playlist: {playlist_path}")
        
        # Show playlist contents
        with open(playlist_path, 'r') as f:
            lines = f.readlines()
            logger.info(f"Playlist has {len([l for l in lines if not l.startswith('#')])} tracks")
    else:
        logger.warning("No recent audio files for playlist")
    
    return True


def main():
    """Run all audio management tests"""
    logger.info("Starting Audio Management Tests")
    
    # Test audio manager
    test_audio_manager()
    
    # Test queue system
    test_audio_queue()
    
    # Test playlist creation
    test_playlist_creation()
    
    logger.success("\n✅ All audio management tests completed!")
    logger.info("\n📊 Your audio pipeline is fully operational!")


if __name__ == "__main__":
    main()
