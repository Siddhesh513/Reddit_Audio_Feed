/**
 * Main application logic
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize preferences from localStorage
    initializePreferences();

    // Check API health
    checkAPIHealth();

    // Initialize event listeners
    initializeEventListeners();

    // Load initial data
    await loadInitialData();
});

function initializePreferences() {
    const prefs = storage.initializePreferences();

    // Apply volume
    const audioPlayer = document.getElementById('audio-player');
    const volumeSlider = document.getElementById('volume-slider');
    if (prefs.volume !== undefined) {
        audioPlayer.volume = prefs.volume;
        volumeSlider.value = prefs.volume * 100;
    }

    // Apply playback speed
    const speedSelect = document.getElementById('speed-select');
    if (prefs.playbackSpeed !== undefined) {
        speedSelect.value = prefs.playbackSpeed;
        audioPlayer.playbackRate = prefs.playbackSpeed;
    }

    // Apply shuffle and repeat
    if (prefs.shuffleEnabled) {
        ui.isShuffleEnabled = true;
        document.getElementById('shuffle-btn').classList.add('active');
    }

    if (prefs.repeatMode && prefs.repeatMode !== 'off') {
        ui.repeatMode = prefs.repeatMode;
        const repeatBtn = document.getElementById('repeat-btn');
        repeatBtn.classList.add(`repeat-${prefs.repeatMode}`);
        const icons = { off: '🔁', all: '🔁', one: '🔂' };
        repeatBtn.innerHTML = icons[prefs.repeatMode];
    }

    // Load recent subreddits
    updateRecentSubreddits();

    // Update theme icon
    updateThemeIcon(prefs.theme);
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
}

async function checkAPIHealth() {
    try {
        const health = await api.checkHealth();
        const statusEl = document.getElementById('api-status');
        statusEl.textContent = 'Online';
        statusEl.style.color = '#46a049';
    } catch (error) {
        const statusEl = document.getElementById('api-status');
        statusEl.textContent = 'Offline';
        statusEl.style.color = '#dc3545';
        ui.showToast('API is offline. Please start the backend server.', 'error');
    }
}

function initializeEventListeners() {
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const currentTheme = storage.getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        storage.setTheme(newTheme);
        updateThemeIcon(newTheme);
        ui.showToast(`${newTheme === 'dark' ? 'Dark' : 'Light'} mode enabled`, 'info');
    });

    // Fetch posts
    document.getElementById('fetch-posts-btn').addEventListener('click', fetchPosts);

    // Quick access subreddit buttons
    document.querySelectorAll('.quick-access button').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('subreddit-input').value = btn.dataset.subreddit;
            fetchPosts();
        });
    });
    
    // Select all posts
    document.getElementById('select-all-btn').addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('.post-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        
        checkboxes.forEach(cb => {
            cb.checked = !allChecked;
            ui.handlePostSelection(cb);
        });
    });
    
    // Generate audio for selected posts
    document.getElementById('generate-selected-btn').addEventListener('click', generateSelectedAudio);
    
    // Add to queue
    document.getElementById('add-to-queue-btn').addEventListener('click', addSelectedToQueue);
    
    // Queue operations
    document.getElementById('process-queue-btn').addEventListener('click', processQueue);
    document.getElementById('clear-completed-btn').addEventListener('click', clearCompletedQueue);
    document.getElementById('refresh-queue-btn').addEventListener('click', refreshQueueStatus);
    
    // Files operations
    document.getElementById('refresh-files-btn').addEventListener('click', refreshAudioFiles);
    
    // Audio player controls
    const audioPlayer = document.getElementById('audio-player');
    audioPlayer.addEventListener('ended', () => {
        ui.handleTrackEnd();
    });
    
    document.getElementById('prev-btn').addEventListener('click', () => {
        if (ui.currentAudioIndex > 0) {
            ui.playAudio(ui.currentAudioIndex - 1);
        }
    });
    
    document.getElementById('next-btn').addEventListener('click', () => {
        if (ui.currentAudioIndex < ui.playlist.length - 1) {
            ui.playAudio(ui.currentAudioIndex + 1);
        }
    });
    
    document.getElementById('speed-select').addEventListener('change', (e) => {
        audioPlayer.playbackRate = parseFloat(e.target.value);
    });

    // Volume control
    const volumeSlider = document.getElementById('volume-slider');
    volumeSlider.addEventListener('input', (e) => {
        const volume = e.target.value / 100;
        audioPlayer.volume = volume;
        storage.setPreference('volume', volume);
    });

    // Shuffle button
    document.getElementById('shuffle-btn').addEventListener('click', () => {
        ui.toggleShuffle();
    });

    // Repeat button
    document.getElementById('repeat-btn').addEventListener('click', () => {
        ui.toggleRepeat();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Don't trigger if user is typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        switch(e.code) {
            case 'Space':
                e.preventDefault();
                document.getElementById('play-pause-btn').click();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                document.getElementById('prev-btn').click();
                break;
            case 'ArrowRight':
                e.preventDefault();
                document.getElementById('next-btn').click();
                break;
        }
    });

    // Update play/pause button when audio state changes
    audioPlayer.addEventListener('play', () => {
        document.getElementById('play-pause-btn').innerHTML = '⏸️ Pause';
    });

    audioPlayer.addEventListener('pause', () => {
        document.getElementById('play-pause-btn').innerHTML = '▶️ Play';
    });

    // Play/pause button toggle
    document.getElementById('play-pause-btn').addEventListener('click', () => {
        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    });
}

async function fetchPosts() {
    const subreddit = document.getElementById('subreddit-input').value.trim();
    const sortType = document.getElementById('sort-select').value;
    const limit = parseInt(document.getElementById('limit-input').value) || 10;

    if (!subreddit) {
        ui.showToast('Please enter a subreddit name', 'error');
        return;
    }

    ui.showLoading('Fetching posts...');

    try {
        const posts = await api.fetchPosts(subreddit, sortType, limit);
        ui.displayPosts(posts);
        ui.showToast(`Fetched ${posts.length} posts from r/${subreddit}`, 'success');

        // Save to recent subreddits
        storage.addRecentSubreddit(subreddit);
        updateRecentSubreddits();
    } catch (error) {
        ui.showToast('Failed to fetch posts', 'error');
        console.error(error);
    } finally {
        ui.hideLoading();
    }
}

function updateRecentSubreddits() {
    const recents = storage.getRecentSubreddits();
    const quickAccess = document.querySelector('.quick-access');

    if (recents.length > 0) {
        // Add recent subreddits to quick access if not already there
        const existingButtons = Array.from(quickAccess.querySelectorAll('button'))
            .map(btn => btn.dataset.subreddit);

        recents.slice(0, 3).forEach(subreddit => {
            if (!existingButtons.includes(subreddit)) {
                const btn = document.createElement('button');
                btn.className = 'btn-small recent-subreddit';
                btn.dataset.subreddit = subreddit;
                btn.textContent = subreddit;
                btn.addEventListener('click', () => {
                    document.getElementById('subreddit-input').value = subreddit;
                    fetchPosts();
                });
                quickAccess.appendChild(btn);
            }
        });
    }
}

async function generateSelectedAudio() {
    const selectedIds = Array.from(ui.selectedPosts);
    if (selectedIds.length === 0) return;
    
    ui.showLoading(`Generating audio for ${selectedIds.length} posts...`);
    
    let successCount = 0;
    
    for (const postId of selectedIds) {
        const post = ui.currentPosts.find(p => p.id === postId);
        if (!post) continue;
        
        try {
            const result = await api.generateAudio(null, post);
            if (result.success) {
                successCount++;
                ui.showToast(`Generated audio: ${result.filename}`, 'success');
            }
        } catch (error) {
            ui.showToast(`Failed to generate audio for post: ${postId}`, 'error');
        }
    }
    
    ui.hideLoading();
    setTimeout(async () => {
    await refreshAudioFiles();
    await refreshQueueStatus();
    }, 1000);
    ui.showToast(`Generated ${successCount}/${selectedIds.length} audio files`, 'success');
    
    // Refresh audio files list
    await refreshAudioFiles();
}

async function addSelectedToQueue() {
    const selectedIds = Array.from(ui.selectedPosts);
    if (selectedIds.length === 0) return;
    
    try {
        const result = await api.addToQueue(null, selectedIds);
        ui.showToast(`Added ${selectedIds.length} posts to queue`, 'success');
        await refreshQueueStatus();
    } catch (error) {
        ui.showToast('Failed to add posts to queue', 'error');
    }
}

async function processQueue() {
    ui.showLoading('Processing queue...');
    
    try {
        const result = await api.processQueue(10);
        ui.showToast(`Processed ${result.processed} items (${result.successful} successful)`, 'success');
        await refreshQueueStatus();
        await refreshAudioFiles();
    } catch (error) {
        ui.showToast('Failed to process queue', 'error');
    } finally {
        ui.hideLoading();
    }
}

async function clearCompletedQueue() {
    try {
        await api.clearQueue('completed');
        ui.showToast('Cleared completed items from queue', 'success');
        await refreshQueueStatus();
    } catch (error) {
        ui.showToast('Failed to clear queue', 'error');
    }
}

async function refreshQueueStatus() {
    try {
        const status = await api.getQueueStatus();
        ui.updateQueueDisplay(status);
    } catch (error) {
        console.error('Failed to refresh queue status:', error);
    }
}

async function refreshAudioFiles() {
    try {
        const result = await api.listAudioFiles(50, 0);  // Get more files
        console.log('Audio files received:', result);  // Debug log
        if (result && result.files) {
            ui.displayAudioFiles(result.files);
            ui.updatePlaylist(result.files);
        }
    } catch (error) {
        console.error('Failed to refresh audio files:', error);
        ui.showToast('Failed to refresh audio files', 'error');
    }
}

async function loadInitialData() {
    // Load queue status
    await refreshQueueStatus();

    // Load audio files
    await refreshAudioFiles();

    // Load stats
    try {
        const stats = await api.getStats();
        ui.updateStats(stats);
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Make refreshAudioFiles available globally for modal
window.refreshAudioFiles = refreshAudioFiles;

// Auto-refresh queue status
setInterval(refreshQueueStatus, CONFIG.AUTO_REFRESH_INTERVAL);
