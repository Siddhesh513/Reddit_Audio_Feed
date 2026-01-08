# 🚀 Deployment Guide

This guide covers various deployment options for the Reddit Audio Feed application.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)

## Local Development

### Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd Reddit_Audio_Feed

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp ../.env.example .env
# Edit .env with your Reddit API credentials

# 4. Create data directories
mkdir -p data/raw data/processed data/audio

# 5. Run backend
cd src
python -m uvicorn api.app:app --reload --port 8000

# 6. Run frontend (new terminal)
cd ../../frontend
python -m http.server 3000
```

Visit http://localhost:3000

## Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose installed
- Reddit API credentials

### Quick Deploy

```bash
# 1. Clone repository
git clone <your-repo-url>
cd Reddit_Audio_Feed

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Build and run
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Stop
docker-compose down
```

### Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Remove containers and volumes
docker-compose down -v

# Access backend shell
docker-compose exec backend /bin/bash
```

### Accessing Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Production Deployment

### Option 1: VPS Deployment (DigitalOcean, AWS EC2, etc.)

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 2. Application Deployment

```bash
# Clone repository
git clone <your-repo-url>
cd Reddit_Audio_Feed

# Configure for production
cp .env.example .env
nano .env  # Edit with production values
```

Production `.env` settings:
```bash
DEBUG=False
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
API_HOST=0.0.0.0
API_PORT=8000
```

#### 3. Deploy with Docker Compose

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Or use docker-compose with production overrides
docker-compose up -d
```

#### 4. Setup Nginx Reverse Proxy (Optional)

If you want to use port 80/443:

```nginx
# /etc/nginx/sites-available/reddit-audio-feed
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/reddit-audio-feed /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Option 2: Cloud Platform Deployment

#### Heroku

**backend (Procfile):**
```
web: uvicorn src.api.app:app --host 0.0.0.0 --port $PORT
```

Deploy:
```bash
heroku create your-app-name
heroku config:set REDDIT_CLIENT_ID=xxx
heroku config:set REDDIT_CLIENT_SECRET=xxx
heroku config:set REDDIT_USER_AGENT=xxx
git push heroku main
```

#### Railway.app

1. Connect GitHub repository
2. Add environment variables
3. Deploy automatically

#### Render.com

1. Create new Web Service
2. Link GitHub repository
3. Set build command: `cd backend && pip install -r requirements.txt`
4. Set start command: `cd backend/src && uvicorn api.app:app --host 0.0.0.0 --port $PORT`

### Option 3: Kubernetes Deployment

Coming soon...

## Environment Configuration

### Required Variables

```bash
REDDIT_CLIENT_ID=xxx          # Required
REDDIT_CLIENT_SECRET=xxx      # Required
REDDIT_USER_AGENT=xxx         # Required
```

### Optional Variables

```bash
# Application
DEBUG=False                   # Set to False in production
LOG_LEVEL=WARNING            # DEBUG, INFO, WARNING, ERROR

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com

# Storage
MAX_AUDIO_FILE_SIZE=50       # MB
MAX_TOTAL_STORAGE=10         # GB
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check with Docker
docker-compose exec backend curl http://localhost:8000/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Backup Data

```bash
# Backup audio files
docker-compose exec backend tar -czf /tmp/audio-backup.tar.gz data/audio/
docker cp reddit-audio-backend:/tmp/audio-backup.tar.gz ./backups/

# Or directly from volume
tar -czf backup-$(date +%Y%m%d).tar.gz backend/data/
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Security Checklist

- [ ] Change default DEBUG to False in production
- [ ] Set specific CORS_ORIGINS (not wildcard)
- [ ] Use HTTPS in production
- [ ] Keep Reddit API credentials secret
- [ ] Regularly update dependencies
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Use strong passwords for any admin features
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Verify environment variables
docker-compose config

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use

```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Permission denied errors

```bash
# Fix ownership
sudo chown -R $USER:$USER backend/data
```

## Performance Optimization

### For Production

1. **Use production WSGI server** (Gunicorn with uvicorn workers):
```bash
pip install gunicorn
gunicorn src.api.app:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Enable caching** in nginx config

3. **Set up CDN** for audio files

4. **Use Redis** for queue management (future enhancement)

5. **Database** for metadata storage (future enhancement)

## Getting Help

- Check logs: `docker-compose logs -f`
- Backend API docs: http://localhost:8000/docs
- GitHub Issues: <your-repo-url>/issues

---

Happy deploying! 🚀
