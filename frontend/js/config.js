/**
 * Configuration for the Reddit Audio Feed application
 */

const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    API_ENDPOINTS: {
        // Reddit endpoints
        FETCH_POSTS: '/api/reddit/posts',
        GET_POST: '/api/reddit/post',
        VALIDATE_SUBREDDIT: '/api/reddit/subreddit/validate',
        
        // Audio endpoints
        GENERATE_AUDIO: '/api/audio/generate',
        LIST_AUDIO: '/api/audio/list',
        DOWNLOAD_AUDIO: '/api/audio/download',
        STREAM_AUDIO: '/api/audio/stream',
        
        // Queue endpoints
        QUEUE_STATUS: '/api/queue/status',
        QUEUE_ADD: '/api/queue/add',
        QUEUE_PROCESS: '/api/queue/process',
        QUEUE_CLEAR: '/api/queue/clear',
        
        // Stats endpoints
        STATS_SUMMARY: '/api/stats/summary',
        
        // Health check
        HEALTH: '/health'
    },
    
    // UI Settings
    DEFAULT_SUBREDDIT: 'todayilearned',
    DEFAULT_LIMIT: 10,
    AUTO_REFRESH_INTERVAL: 30000, // 30 seconds
    TOAST_DURATION: 3000, // 3 seconds
    
    // Audio Settings
    DEFAULT_VOICE: 'en-US',
    DEFAULT_SPEED: 1.0,
    
    // Storage Keys
    STORAGE_KEYS: {
        RECENT_SUBREDDITS: 'reddit_audio_recent_subreddits',
        USER_PREFERENCES: 'reddit_audio_preferences',
        PLAYLIST: 'reddit_audio_playlist'
    }
};

// Freeze config to prevent modifications
Object.freeze(CONFIG);
