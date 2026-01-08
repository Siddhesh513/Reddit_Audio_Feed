# 🎧 Reddit Audio Feed

Convert Reddit posts to audio format for hands-free listening. Perfect for consuming Reddit content while commuting, exercising, or doing chores!

![Project Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### Core Functionality
- 📱 **Reddit Integration** - Fetch posts from any subreddit with flexible sorting (hot, new, top, rising)
- 🎙️ **Text-to-Speech** - Convert text posts to natural-sounding audio using gTTS
- 🎵 **Audio Player** - Built-in web player with playlist support
- ⬇️ **Download** - Save audio files for offline listening
- 📊 **Queue Management** - Process multiple posts efficiently with priority queue
- 📈 **Statistics** - Track your audio library size and usage

### User Experience
- 🌓 **Dark Mode** - Easy on the eyes with automatic theme persistence
- ⌨️ **Keyboard Shortcuts** - Control playback with Space, ← and → keys
- 🔀 **Shuffle & Repeat** - Full playlist management
- 👁️ **Post Preview** - Read before generating audio
- 💾 **Persistent Preferences** - Saves your settings locally
- 📱 **Responsive Design** - Works on desktop and mobile

### Developer Features
- 🚀 **FastAPI Backend** - Modern, fast, and well-documented API
- 🎨 **Clean Architecture** - Modular design with separation of concerns
- 🧪 **Test Coverage** - Comprehensive test suite
- 📝 **Type Hints** - Full Python type annotations
- 🔍 **Logging** - Structured logging with Loguru

## 📋 Table of Contents

- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Architecture](#-architecture)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 📸 Screenshots

> *Screenshots to be added*

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Reddit API credentials ([Get them here](https://www.reddit.com/prefs/apps))
- Modern web browser

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Reddit_Audio_Feed.git
cd Reddit_Audio_Feed

# 2. Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp ../.env.example .env
# Edit .env with your Reddit API credentials

# 4. Run the backend
cd src
python -m uvicorn api.app:app --reload --port 8000

# 5. Open frontend (in a new terminal)
# Simply open frontend/index.html in your browser
# Or serve it with:
cd ../../frontend
python -m http.server 3000
```

Visit `http://localhost:3000` and start converting Reddit posts to audio! 🎉

## 📦 Installation

### Manual Installation

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/raw data/processed data/audio
```

#### Frontend Setup

The frontend is vanilla JavaScript - no build step required! Simply:

```bash
cd frontend
# Open index.html in your browser, or serve with any HTTP server
python -m http.server 3000
```

### Docker Installation (Recommended for Production)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=RedditAudioFeed/1.0 by YourUsername

# Application Settings
DEBUG=True                    # Set to False in production
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR

# Data Paths (relative to backend directory)
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
DATA_AUDIO_PATH=data/audio

# API Settings (Optional)
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Getting Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the details:
   - **name**: Reddit Audio Feed
   - **App type**: script
   - **description**: Convert Reddit posts to audio
   - **redirect uri**: http://localhost:8080
4. Click "Create app"
5. Copy the **client ID** (under the app name) and **client secret**

## 📖 Usage

### Basic Workflow

1. **Fetch Posts**
   - Enter a subreddit name (e.g., "todayilearned")
   - Select sorting method (hot, new, top, rising)
   - Set the number of posts to fetch
   - Click "Fetch Posts"

2. **Select Posts**
   - Preview posts by clicking the 👁️ icon
   - Check boxes to select posts for audio generation
   - Or click "Select All" to select all posts

3. **Generate Audio**
   - Click "Generate Audio" for immediate processing
   - Or click "Add to Queue" to batch process later
   - Click "Process Queue" when ready

4. **Listen**
   - Audio files appear in the "Generated Audio Files" section
   - Click ▶️ Play to listen
   - Use keyboard shortcuts: Space (play/pause), ← (previous), → (next)

5. **Download**
   - Click ⬇️ Download on individual files
   - Or "Download All" to get a ZIP archive

### Keyboard Shortcuts

- `Space` - Play/Pause
- `←` - Previous track
- `→` - Next track

### Audio Player Features

- **Volume Control** - Adjust volume with slider
- **Playback Speed** - 0.75x to 2x speed options
- **Shuffle** - Random playback order
- **Repeat** - Off / Repeat All / Repeat One

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive API Docs
Visit `http://localhost:8000/docs` for the full Swagger UI documentation.

### Quick Reference

#### Reddit Endpoints

**Fetch Posts**
```http
GET /api/reddit/posts?subreddit=todayilearned&sort_type=hot&limit=10
```

**Validate Subreddit**
```http
GET /api/reddit/subreddit/validate?name=todayilearned
```

#### Audio Endpoints

**Generate Audio**
```http
POST /api/audio/generate
Content-Type: application/json

{
  "post_data": {
    "title": "Post Title",
    "text_content": "Post content here..."
  },
  "voice": "en-US",
  "speed": 1.0
}
```

**List Audio Files**
```http
GET /api/audio/list?limit=20&offset=0
```

**Stream Audio**
```http
GET /api/audio/stream/{filename}
```

**Download Audio**
```http
GET /api/audio/download/{filename}
```

#### Queue Endpoints

**Get Queue Status**
```http
GET /api/queue/status
```

**Add to Queue**
```http
POST /api/queue/add
Content-Type: application/json

{
  "post_ids": ["post1", "post2"],
  "priority": 5
}
```

**Process Queue**
```http
POST /api/queue/process
Content-Type: application/json

{
  "max_items": 10,
  "engine": "gtts"
}
```

#### Stats Endpoints

**Get Summary**
```http
GET /api/stats/summary
```

### Example: Complete Workflow

```python
import requests

API_URL = "http://localhost:8000"

# 1. Fetch posts
response = requests.get(f"{API_URL}/api/reddit/posts", params={
    "subreddit": "todayilearned",
    "sort_type": "hot",
    "limit": 5
})
posts = response.json()

# 2. Generate audio for first post
response = requests.post(f"{API_URL}/api/audio/generate", json={
    "post_data": posts[0],
    "voice": "en-US",
    "speed": 1.0
})
result = response.json()
print(f"Generated: {result['filename']}")

# 3. Get audio file
audio_url = f"{API_URL}/api/audio/stream/{result['filename']}"
print(f"Listen at: {audio_url}")
```

## 🛠️ Development

### Project Structure

```
Reddit_Audio_Feed/
├── backend/
│   ├── src/
│   │   ├── api/            # FastAPI routes and models
│   │   ├── services/       # Business logic
│   │   ├── models/         # Data models
│   │   ├── config/         # Configuration
│   │   └── utils/          # Utilities and helpers
│   ├── tests/              # Test suite
│   ├── data/               # Data storage
│   └── requirements.txt
├── frontend/
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript modules
│   │   ├── api.js         # API client
│   │   ├── ui.js          # UI management
│   │   ├── main.js        # Main app logic
│   │   ├── storage.js     # LocalStorage
│   │   └── config.js      # Configuration
│   └── index.html          # Main HTML
├── docs/                   # Documentation
├── .env.example            # Environment template
└── README.md
```

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_reddit_service.py

# Run with verbose output
pytest -v
```

### Code Style

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Adding New Features

1. **Backend**:
   - Add service logic in `backend/src/services/`
   - Create API endpoints in `backend/src/api/routes/`
   - Add tests in `backend/tests/`

2. **Frontend**:
   - Add UI logic in `frontend/js/ui.js`
   - Add API calls in `frontend/js/api.js`
   - Update styles in `frontend/css/styles.css`

## 🏗️ Architecture

### Backend Architecture

```
┌─────────────┐
│   FastAPI   │ - API Layer (routes, validation)
└──────┬──────┘
       │
┌──────▼──────┐
│  Services   │ - Business Logic
│             │
│  - Reddit   │ - Fetch posts via PRAW
│  - TTS      │ - Text-to-speech conversion
│  - Queue    │ - Job management
│  - Storage  │ - File management
└──────┬──────┘
       │
┌──────▼──────┐
│   Models    │ - Data structures
└──────┬──────┘
       │
┌──────▼──────┐
│  Storage    │ - File system (future: database)
└─────────────┘
```

### Key Technologies

- **Backend**: FastAPI, PRAW, gTTS, Loguru
- **Frontend**: Vanilla JavaScript (ES6+), CSS3
- **TTS Engine**: Google Text-to-Speech (gTTS)
- **Storage**: File system (JSON + audio files)

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check environment variables
cat .env
```

**Reddit API errors**
- Verify your credentials in `.env`
- Check Reddit app settings at https://www.reddit.com/prefs/apps
- Ensure user agent is properly formatted
- Check rate limits (60 requests/minute for scripts)

**CORS errors in browser**
- Ensure backend is running on port 8000
- Check `CORS_ORIGINS` in `.env`
- Try opening frontend with `python -m http.server 3000`

**No audio playing**
- Check browser console for errors
- Verify audio files exist in `backend/data/audio/`
- Try downloading the file directly
- Check browser audio permissions

**Queue not processing**
- Check backend logs for errors
- Verify posts have text content
- Check disk space for audio storage

### Debug Mode

Enable detailed logging:

```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG
```

Then check logs in `backend/logs/` or console output.

### Getting Help

- Check existing [Issues](https://github.com/yourusername/Reddit_Audio_Feed/issues)
- Read the [API Documentation](http://localhost:8000/docs)
- Review test files for usage examples

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Guidelines

- Follow PEP 8 for Python code
- Add docstrings to all functions/classes
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PRAW](https://praw.readthedocs.io/) - Python Reddit API Wrapper
- [gTTS](https://gtts.readthedocs.io/) - Google Text-to-Speech
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- Reddit community for endless content

## 📮 Contact

Project Link: [https://github.com/yourusername/Reddit_Audio_Feed](https://github.com/yourusername/Reddit_Audio_Feed)

---

**Made with ❤️ and ☕ by [Siddhesh]**
