/**
 * LocalStorage management for user preferences
 */

class StorageManager {
    constructor() {
        this.storageKeys = CONFIG.STORAGE_KEYS;
    }

    // Generic storage methods
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    }

    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return false;
        }
    }

    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    }

    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }

    // Recent subreddits
    getRecentSubreddits() {
        return this.get(this.storageKeys.RECENT_SUBREDDITS, []);
    }

    addRecentSubreddit(subreddit) {
        const recents = this.getRecentSubreddits();

        // Remove if already exists
        const filtered = recents.filter(s => s !== subreddit);

        // Add to beginning
        filtered.unshift(subreddit);

        // Keep only last 10
        const updated = filtered.slice(0, 10);

        this.set(this.storageKeys.RECENT_SUBREDDITS, updated);
        return updated;
    }

    // User preferences
    getPreferences() {
        return this.get(this.storageKeys.USER_PREFERENCES, {
            theme: 'light',
            playbackSpeed: 1.0,
            volume: 1.0,
            autoPlay: false,
            repeatMode: 'off',
            shuffleEnabled: false
        });
    }

    savePreferences(preferences) {
        const current = this.getPreferences();
        const updated = { ...current, ...preferences };
        return this.set(this.storageKeys.USER_PREFERENCES, updated);
    }

    getPreference(key, defaultValue = null) {
        const prefs = this.getPreferences();
        return prefs[key] !== undefined ? prefs[key] : defaultValue;
    }

    setPreference(key, value) {
        const prefs = this.getPreferences();
        prefs[key] = value;
        return this.savePreferences(prefs);
    }

    // Playlist
    getPlaylist() {
        return this.get(this.storageKeys.PLAYLIST, []);
    }

    savePlaylist(playlist) {
        return this.set(this.storageKeys.PLAYLIST, playlist);
    }

    clearPlaylist() {
        return this.remove(this.storageKeys.PLAYLIST);
    }

    // Theme
    getTheme() {
        return this.getPreference('theme', 'light');
    }

    setTheme(theme) {
        this.setPreference('theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
    }

    // Initialize preferences
    initializePreferences() {
        const prefs = this.getPreferences();

        // Apply theme
        this.setTheme(prefs.theme);

        return prefs;
    }
}

// Create global storage instance
const storage = new StorageManager();
