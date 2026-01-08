/**
 * UI Management for Reddit Audio Feed
 */

class UIManager {
    constructor() {
        this.currentPosts = [];
        this.selectedPosts = new Set();
        this.playlist = [];
        this.currentAudioIndex = 0;
        this.isShuffleEnabled = false;
        this.repeatMode = 'off'; // 'off', 'all', 'one'
        this.originalPlaylist = [];
    }

    // Loading overlay
    showLoading(message = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        messageEl.textContent = message;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    // Toast notifications
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">✕</button>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, CONFIG.TOAST_DURATION);
    }

    // Posts display
    displayPosts(posts) {
        this.currentPosts = posts;
        this.selectedPosts.clear();

        const postsSection = document.getElementById('posts-section');
        const postsList = document.getElementById('posts-list');

        postsSection.style.display = 'block';

        if (!posts || posts.length === 0) {
            postsList.innerHTML = '<p class="text-center">No posts found</p>';
            return;
        }

        postsList.innerHTML = posts.map((post, index) => `
            <div class="post-item" data-index="${index}">
                <div class="post-header">
                    <input type="checkbox" class="post-checkbox" data-post-id="${post.id}">
                    <div class="post-title">${this.escapeHtml(post.title)}</div>
                    <button class="btn-preview" data-index="${index}" title="Preview">👁️</button>
                </div>
                <div class="post-meta">
                    <span>r/${post.subreddit}</span>
                    <span>👤 ${post.author}</span>
                    <span>⬆️ ${post.score}</span>
                    <span>💬 ${post.num_comments}</span>
                    ${post.text_content ? `<span>📝 ${post.text_content.split(' ').length} words</span>` : ''}
                </div>
            </div>
        `).join('');
        
        // Add click handlers
        postsList.querySelectorAll('.post-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.classList.contains('post-checkbox') && !e.target.classList.contains('btn-preview')) {
                    const checkbox = item.querySelector('.post-checkbox');
                    checkbox.checked = !checkbox.checked;
                    this.handlePostSelection(checkbox);
                }
            });

            const checkbox = item.querySelector('.post-checkbox');
            checkbox.addEventListener('change', () => this.handlePostSelection(checkbox));

            const previewBtn = item.querySelector('.btn-preview');
            if (previewBtn) {
                previewBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const index = parseInt(previewBtn.dataset.index);
                    this.showPreview(this.currentPosts[index]);
                });
            }
        });

        this.updateGenerateButton();
    }

    handlePostSelection(checkbox) {
        const postId = checkbox.dataset.postId;
        const postItem = checkbox.closest('.post-item');
        
        if (checkbox.checked) {
            this.selectedPosts.add(postId);
            postItem.classList.add('selected');
        } else {
            this.selectedPosts.delete(postId);
            postItem.classList.remove('selected');
        }
        
        this.updateGenerateButton();
    }

    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-selected-btn');
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        const count = this.selectedPosts.size;
        
        generateBtn.disabled = count === 0;
        addToQueueBtn.disabled = count === 0;
        
        if (count > 0) {
            generateBtn.textContent = `Generate Audio (${count})`;
            addToQueueBtn.textContent = `Add to Queue (${count})`;
        } else {
            generateBtn.textContent = 'Generate Audio';
            addToQueueBtn.textContent = 'Add to Queue';
        }
    }

    // Audio player
    updatePlayer(audioFile) {
        const player = document.getElementById('audio-player');
        const nowPlaying = document.getElementById('now-playing');
        const audioInfo = document.getElementById('audio-info');
        const playerSection = document.getElementById('player-section');
        
        playerSection.style.display = 'block';
        
        if (audioFile) {
            player.src = api.getAudioStreamURL(audioFile.filename);
            nowPlaying.textContent = audioFile.title || audioFile.filename;
            audioInfo.textContent = `Duration: ${Math.round(audioFile.duration_seconds || 0)}s | Size: ${Math.round((audioFile.file_size_bytes || 0) / 1024)}KB`;
        }
    }

    updatePlaylist(files) {
        this.playlist = files;
        const playlistItems = document.getElementById('playlist-items');
        
        if (!files || files.length === 0) {
            playlistItems.innerHTML = '<p class="text-center">No audio files</p>';
            return;
        }
        
        playlistItems.innerHTML = files.map((file, index) => `
            <div class="playlist-item ${index === this.currentAudioIndex ? 'active' : ''}" data-index="${index}">
                <span>${file.title || file.filename}</span>
                <div>
                    <button class="btn-small" onclick="ui.playAudio(${index})">▶️</button>
                    <a href="${api.getAudioDownloadURL(file.filename)}" class="btn-small" download>⬇️</a>
                </div>
            </div>
        `).join('');
    }

    playAudio(index) {
        if (index >= 0 && index < this.playlist.length) {
            this.currentAudioIndex = index;
            this.updatePlayer(this.playlist[index]);
            this.updatePlaylist(this.playlist);
            document.getElementById('audio-player').play();
        }
    }

    // Queue display
    updateQueueDisplay(stats) {
        document.getElementById('queue-total').textContent = stats.total || 0;
        document.getElementById('queue-pending').textContent = stats.pending || 0;
        document.getElementById('queue-processing').textContent = stats.processing || 0;
        document.getElementById('queue-completed').textContent = stats.completed || 0;
    }

    displayQueueItems(items) {
        const queueItemsContainer = document.getElementById('queue-items');

        if (!items || items.length === 0) {
            queueItemsContainer.innerHTML = '<p class="text-center">Queue is empty</p>';
            return;
        }

        queueItemsContainer.innerHTML = items.map(item => `
            <div class="queue-item-card ${item.status}">
                <div class="queue-item-header">
                    <span class="queue-item-title">${this.escapeHtml(item.title || item.post_id || 'Unknown')}</span>
                    <span class="status ${item.status}">${item.status}</span>
                </div>
                <div class="queue-item-meta">
                    ${item.subreddit ? `<span>r/${item.subreddit}</span>` : ''}
                    <span>Priority: ${item.priority || 5}</span>
                    ${item.progress ? `<span>Progress: ${Math.round(item.progress * 100)}%</span>` : ''}
                </div>
                ${item.status === 'processing' && item.progress ? `
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${item.progress * 100}%"></div>
                    </div>
                ` : ''}
                ${item.error ? `<div class="queue-item-error">Error: ${this.escapeHtml(item.error)}</div>` : ''}
            </div>
        `).join('');
    }

    // Files display
    displayAudioFiles(files) {
        const filesList = document.getElementById('files-list');
        
        if (!files || files.length === 0) {
            filesList.innerHTML = '<p class="text-center">No audio files generated yet</p>';
            return;
        }
        
        filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-meta">
                        Duration: ${Math.round(file.duration_seconds || 0)}s | 
                        Size: ${Math.round((file.file_size_bytes || 0) / 1024)}KB |
                        Subreddit: r/${file.subreddit || 'unknown'}
                    </div>
                </div>
                <div class="file-actions">
                    <button class="btn btn-secondary" onclick="ui.playAudioFile('${file.filename}')">▶️ Play</button>
                    <a href="${api.getAudioDownloadURL(file.filename)}" class="btn btn-primary" download>⬇️ Download</a>
                </div>
            </div>
        `).join('');
    }

    playAudioFile(filename) {
        const file = { filename: filename };
        this.updatePlayer(file);
        document.getElementById('audio-player').play();
    }

    // Stats display
    updateStats(stats) {
        document.getElementById('stat-files').textContent = stats.audio_files || 0;
        document.getElementById('stat-duration').textContent = `${Math.round(stats.total_duration_minutes || 0)} min`;
        document.getElementById('stat-storage').textContent = `${(stats.total_size_mb || 0).toFixed(1)} MB`;
        document.getElementById('stat-processed').textContent = stats.posts_processed || 0;
    }

    // Shuffle and Repeat
    toggleShuffle() {
        this.isShuffleEnabled = !this.isShuffleEnabled;
        const shuffleBtn = document.getElementById('shuffle-btn');

        if (this.isShuffleEnabled) {
            shuffleBtn.classList.add('active');
            this.originalPlaylist = [...this.playlist];
            this.shufflePlaylist();
        } else {
            shuffleBtn.classList.remove('active');
            this.playlist = [...this.originalPlaylist];
            this.updatePlaylist(this.playlist);
        }

        storage.setPreference('shuffleEnabled', this.isShuffleEnabled);
        this.showToast(`Shuffle ${this.isShuffleEnabled ? 'enabled' : 'disabled'}`, 'info');
    }

    shufflePlaylist() {
        // Fisher-Yates shuffle
        const shuffled = [...this.playlist];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        this.playlist = shuffled;
        this.currentAudioIndex = 0;
        this.updatePlaylist(this.playlist);
    }

    toggleRepeat() {
        // Cycle through: off -> all -> one -> off
        const modes = ['off', 'all', 'one'];
        const currentIndex = modes.indexOf(this.repeatMode);
        this.repeatMode = modes[(currentIndex + 1) % modes.length];

        const repeatBtn = document.getElementById('repeat-btn');
        repeatBtn.classList.remove('repeat-off', 'repeat-all', 'repeat-one');
        repeatBtn.classList.add(`repeat-${this.repeatMode}`);

        const icons = { off: '🔁', all: '🔁', one: '🔂' };
        repeatBtn.innerHTML = icons[this.repeatMode];

        storage.setPreference('repeatMode', this.repeatMode);
        this.showToast(`Repeat: ${this.repeatMode}`, 'info');
    }

    handleTrackEnd() {
        if (this.repeatMode === 'one') {
            // Repeat current track
            const audio = document.getElementById('audio-player');
            audio.currentTime = 0;
            audio.play();
        } else if (this.currentAudioIndex < this.playlist.length - 1) {
            // Play next track
            this.playAudio(this.currentAudioIndex + 1);
        } else if (this.repeatMode === 'all') {
            // Repeat from beginning
            this.playAudio(0);
        }
    }

    // Preview Modal
    showPreview(post) {
        const modal = document.getElementById('preview-modal');
        const title = document.getElementById('preview-title');
        const meta = document.getElementById('preview-meta');
        const text = document.getElementById('preview-text');
        const generateBtn = document.getElementById('preview-generate-btn');

        title.textContent = post.title;
        meta.innerHTML = `
            <div class="preview-stat">
                <strong>Subreddit:</strong> r/${post.subreddit}
            </div>
            <div class="preview-stat">
                <strong>Author:</strong> u/${post.author}
            </div>
            <div class="preview-stat">
                <strong>Score:</strong> ${post.score} | <strong>Comments:</strong> ${post.num_comments}
            </div>
            ${post.text_content ? `<div class="preview-stat"><strong>Word Count:</strong> ${post.text_content.split(' ').length}</div>` : ''}
        `;

        text.textContent = post.text_content || 'No text content available';

        // Set up generate button
        generateBtn.onclick = async () => {
            this.closePreview();
            this.showLoading('Generating audio...');
            try {
                const result = await api.generateAudio(null, post);
                this.showToast(`Generated audio: ${result.filename}`, 'success');
                setTimeout(async () => {
                    await window.refreshAudioFiles();
                }, 1000);
            } catch (error) {
                this.showToast('Failed to generate audio', 'error');
            } finally {
                this.hideLoading();
            }
        };

        modal.style.display = 'flex';
    }

    closePreview() {
        document.getElementById('preview-modal').style.display = 'none';
    }

    // Utility
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global UI instance
const ui = new UIManager();
