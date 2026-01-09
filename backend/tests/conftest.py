"""
Pytest fixtures for Reddit Audio Feed tests
Provides reusable test data and mocked services
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


@pytest.fixture
def mock_reddit_post():
    """Single mock Reddit post for testing"""
    return {
        'id': 'test123',
        'title': 'Test Post: This is a sample Reddit post',
        'selftext': 'This is the body text of the test post. It contains enough content to test TTS generation.',
        'subreddit': 'test',
        'author': 'testuser',
        'created_utc': datetime.now().isoformat(),
        'fetched_at': datetime.now().isoformat(),
        'score': 100,
        'upvote_ratio': 0.95,
        'num_comments': 25,
        'total_awards_received': 2,
        'permalink': '/r/test/comments/test123/test_post',
        'url': 'https://reddit.com/r/test/comments/test123',
        'is_self': True,
        'is_video': False,
        'over_18': False,
        'spoiler': False,
        'stickied': False,
        'locked': False,
        'link_flair_text': None,
        'author_flair_text': None,
        'content_categories': None
    }


@pytest.fixture
def posts(mock_reddit_post):
    """List of mock Reddit posts for testing"""
    # Return a list with multiple posts
    post1 = mock_reddit_post.copy()

    post2 = mock_reddit_post.copy()
    post2['id'] = 'test456'
    post2['title'] = 'Another Test Post'
    post2['selftext'] = 'Different body text for variety.'
    post2['score'] = 200

    post3 = mock_reddit_post.copy()
    post3['id'] = 'test789'
    post3['title'] = 'Third Test Post'
    post3['selftext'] = 'Yet another post with different content.'
    post3['score'] = 50

    return [post1, post2, post3]


@pytest.fixture
def client(monkeypatch):
    """Mock Reddit client that doesn't make real API calls"""
    # Create mock client
    mock_client = Mock()

    # Mock validate_subreddit method
    def mock_validate_subreddit(subreddit):
        # Return False for obviously invalid subreddits
        invalid_names = ['this_definitely_does_not_exist_12345', 'thisdoesnotexist12345']
        return subreddit.lower() not in invalid_names

    mock_client.validate_subreddit = mock_validate_subreddit

    # Mock fetch_subreddit_posts method
    def mock_fetch_posts(subreddit_name, sort_type='hot', limit=10, **kwargs):
        # Return deterministic mock data
        if subreddit_name.lower() in ['this_definitely_does_not_exist_12345', 'thisdoesnotexist12345']:
            return []

        # Return mock posts
        posts = []
        for i in range(min(limit, 3)):  # Return up to 3 posts
            posts.append({
                'id': f'mock{i}',
                'title': f'Mock post {i} from r/{subreddit_name}',
                'selftext': f'This is mock content for post {i}.',
                'subreddit': subreddit_name,
                'author': f'mockuser{i}',
                'created_utc': datetime.now().isoformat(),
                'fetched_at': datetime.now().isoformat(),
                'score': 100 + i * 10,
                'upvote_ratio': 0.95,
                'num_comments': 25 + i,
                'is_self': True,
                'url': f'https://reddit.com/r/{subreddit_name}/comments/mock{i}',
                'permalink': f'/r/{subreddit_name}/comments/mock{i}',
                'is_video': False,
                'over_18': False,
                'spoiler': False,
                'stickied': False,
                'locked': False
            })
        return posts

    mock_client.fetch_subreddit_posts = mock_fetch_posts

    # Mock get_post_content method
    def mock_get_post_content(post_id):
        return {
            'id': post_id,
            'title': f'Mock post {post_id}',
            'selftext': f'Mock content for post {post_id}',
            'subreddit': 'test',
            'author': 'mockuser',
            'created_utc': datetime.now().isoformat(),
            'score': 100,
            'num_comments': 25,
            'is_self': True
        }

    mock_client.get_post_content = mock_get_post_content

    # Monkeypatch the get_reddit_client function to return our mock
    monkeypatch.setattr('src.services.reddit_service.get_reddit_client', lambda: mock_client)

    return mock_client
