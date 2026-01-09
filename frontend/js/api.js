/**
 * API Client for Reddit Audio Feed
 */

class APIClient {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
    }

    /**
     * Sleep for specified milliseconds
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Make a fetch request with error handling and retry logic
     */
    async request(endpoint, options = {}, retryCount = 0) {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                // Try to get error message from response
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (e) {
                    // Response wasn't JSON, use default message
                }

                const error = new Error(errorMessage);
                error.status = response.status;
                throw error;
            }

            return await response.json();
        } catch (error) {
            // Retry logic for network errors and 5xx errors
            const shouldRetry = (
                retryCount < this.maxRetries &&
                (error.name === 'TypeError' || // Network error
                 error.status >= 500) // Server error
            );

            if (shouldRetry) {
                console.warn(`Request failed, retrying (${retryCount + 1}/${this.maxRetries})...`);
                await this.sleep(this.retryDelay * (retryCount + 1)); // Exponential backoff
                return this.request(endpoint, options, retryCount + 1);
            }

            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Check if API is reachable
     */
    async isOnline() {
        try {
            await this.checkHealth();
            return true;
        } catch {
            return false;
        }
    }

    // Reddit API methods
    async fetchPosts(subreddit, sortType = 'hot', limit = 10) {
        const params = new URLSearchParams({
            subreddit: subreddit,
            sort_type: sortType,
            limit: limit
        });

        const response = await this.request(`${CONFIG.API_ENDPOINTS.FETCH_POSTS}?${params}`);
        // Backend returns {posts: [...], metadata: {...}}, extract posts array
        return response.posts || response;
    }

    async validateSubreddit(name) {
        const params = new URLSearchParams({ name: name });
        return this.request(`${CONFIG.API_ENDPOINTS.VALIDATE_SUBREDDIT}?${params}`);
    }

    // Audio API methods
    async generateAudio(postId = null, postData = null, text = null) {
        const body = {};
        
        if (postId) body.post_id = postId;
        else if (postData) body.post_data = postData;
        else if (text) body.text = text;
        
        body.voice = CONFIG.DEFAULT_VOICE;
        body.speed = CONFIG.DEFAULT_SPEED;
        
        return this.request(CONFIG.API_ENDPOINTS.GENERATE_AUDIO, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    async listAudioFiles(limit = 20, offset = 0, subreddit = null) {
        const params = new URLSearchParams({
            limit: limit,
            offset: offset
        });
        
        if (subreddit) params.append('subreddit', subreddit);
        
        return this.request(`${CONFIG.API_ENDPOINTS.LIST_AUDIO}?${params}`);
    }

    getAudioDownloadURL(filename) {
        return `${this.baseURL}${CONFIG.API_ENDPOINTS.DOWNLOAD_AUDIO}/${filename}`;
    }

    getAudioStreamURL(filename) {
        return `${this.baseURL}${CONFIG.API_ENDPOINTS.STREAM_AUDIO}/${filename}`;
    }

    // Queue API methods
    async getQueueStatus() {
        return this.request(CONFIG.API_ENDPOINTS.QUEUE_STATUS);
    }

    async getQueueItems() {
        return this.request(CONFIG.API_ENDPOINTS.QUEUE_ITEMS || '/api/queue/items');
    }

    async addToQueue(subreddit = null, postIds = null, posts = null) {
        const body = {};
        
        if (subreddit) body.subreddit = subreddit;
        else if (postIds) body.post_ids = postIds;
        else if (posts) body.posts = posts;
        
        body.priority = 5;
        
        return this.request(CONFIG.API_ENDPOINTS.QUEUE_ADD, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    async processQueue(maxItems = 10) {
        return this.request(CONFIG.API_ENDPOINTS.QUEUE_PROCESS, {
            method: 'POST',
            body: JSON.stringify({
                max_items: maxItems,
                engine: 'gtts'
            })
        });
    }

    async clearQueue(status = 'completed') {
        const params = new URLSearchParams({ status: status });
        return this.request(`${CONFIG.API_ENDPOINTS.QUEUE_CLEAR}?${params}`, {
            method: 'DELETE'
        });
    }

    // Stats API methods
    async getStats() {
        return this.request(CONFIG.API_ENDPOINTS.STATS_SUMMARY);
    }

    // Health check
    async checkHealth() {
        return this.request(CONFIG.API_ENDPOINTS.HEALTH);
    }
}

// Create global API instance
const api = new APIClient();
