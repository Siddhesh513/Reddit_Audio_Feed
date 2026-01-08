# 🚀 Quick Start Guide

Get Reddit Audio Feed running in 5 minutes!

## Prerequisites

- ✅ Python 3.11+
- ✅ Reddit API credentials ([Get them here](https://www.reddit.com/prefs/apps))

## Setup in 5 Steps

### 1️⃣ Get Reddit API Credentials

1. Visit https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **name**: Reddit Audio Feed
   - **App type**: ✅ script
   - **redirect uri**: http://localhost:8080
4. Click "Create app"
5. Copy:
   - **client ID** (under app name)
   - **client secret**

### 2️⃣ Clone & Configure

```bash
git clone https://github.com/yourusername/Reddit_Audio_Feed.git
cd Reddit_Audio_Feed

# Copy environment template
cp .env.example .env

# Edit .env and add your Reddit credentials
nano .env  # or use your preferred editor
```

Your `.env` should look like:
```bash
REDDIT_CLIENT_ID=your_actual_client_id_here
REDDIT_CLIENT_SECRET=your_actual_secret_here
REDDIT_USER_AGENT=RedditAudioFeed/1.0 by YourRedditUsername
```

### 3️⃣ Install Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4️⃣ Start Backend

```bash
cd src
python -m uvicorn api.app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 5️⃣ Open Frontend

**Option A: Direct File** (Easiest)
```bash
# Open frontend/index.html in your browser
# File -> Open... -> Select index.html
```

**Option B: HTTP Server** (Recommended)
```bash
# In a new terminal
cd frontend
python -m http.server 3000
```

Then visit: **http://localhost:3000**

## 🎉 You're Ready!

1. Enter a subreddit (try: `todayilearned`)
2. Click "Fetch Posts"
3. Select posts
4. Click "Generate Audio"
5. Listen! 🎧

## Quick Commands Cheat Sheet

### Backend

```bash
# Start server
cd backend/src
python -m uvicorn api.app:app --reload --port 8000

# Run tests
cd backend
pytest

# Check code style
black src tests
ruff check src
```

### Frontend

```bash
# Serve with Python
cd frontend
python -m http.server 3000

# Or any other HTTP server
npx serve .
php -S localhost:3000
```

### Docker (Alternative Setup)

```bash
# One-command deploy
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Keyboard Shortcuts

- `Space` - Play/Pause
- `←` - Previous track
- `→` - Next track

## API Quick Test

```bash
# Check health
curl http://localhost:8000/health

# Fetch posts
curl "http://localhost:8000/api/reddit/posts?subreddit=todayilearned&limit=5"

# View API docs
open http://localhost:8000/docs
```

## Troubleshooting

### "Can't connect to backend"
- ✅ Backend running on port 8000?
- ✅ Check `http://localhost:8000/health`
- ✅ CORS issues? Serve frontend with HTTP server

### "Reddit API error"
- ✅ Credentials correct in `.env`?
- ✅ User agent format: `AppName/1.0 by RedditUsername`
- ✅ App type is "script" not "web app"

### "No audio generating"
- ✅ Check backend console for errors
- ✅ Posts have text content?
- ✅ Disk space available?
- ✅ Check `backend/data/audio/` folder

### "Frontend looks broken"
- ✅ Serve via HTTP server (not file://)
- ✅ Check browser console (F12)
- ✅ Clear cache and reload

## Next Steps

- 📚 Read the full [README](README.md)
- 🚀 Check [Deployment Guide](DEPLOYMENT.md)
- 🤝 See [Contributing Guide](CONTRIBUTING.md)
- 📖 Explore [API Documentation](http://localhost:8000/docs)

## Need Help?

- 🐛 [Report a bug](https://github.com/yourusername/Reddit_Audio_Feed/issues)
- 💬 [Ask a question](https://github.com/yourusername/Reddit_Audio_Feed/discussions)
- 📧 Email: your-email@example.com

---

**Made something cool? Share it! ⭐ Star the repo!**
