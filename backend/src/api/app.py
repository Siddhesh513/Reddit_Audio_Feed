"""
Reddit Audio Feed API
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from src.utils.loggers import get_logger
from src.config.settings import config

# Import routers (we'll create these next)
from src.api.routes import reddit_router, audio_router, queue_router, stats_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting Reddit Audio Feed API...")
    logger.info(f"Environment: {config.DEBUG and 'Development' or 'Production'}")
    yield
    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="Reddit Audio Feed API",
    description="Convert Reddit posts to audio files",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if config.DEBUG else "An error occurred"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Reddit Audio Feed API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "reddit": "/api/reddit",
            "audio": "/api/audio",
            "queue": "/api/queue",
            "stats": "/api/stats",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": "operational",
        "debug_mode": config.DEBUG
    }


# Include routers
app.include_router(reddit_router.router, prefix="/api/reddit", tags=["Reddit"])
app.include_router(audio_router.router, prefix="/api/audio", tags=["Audio"])
app.include_router(queue_router.router, prefix="/api/queue", tags=["Queue"])
app.include_router(stats_router.router, prefix="/api/stats", tags=["Statistics"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
