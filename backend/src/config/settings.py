import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Config:
    """Base configuration class"""

    # Reddit API Settings
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

    # Directory paths - ADD THESE LINES
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR  # <-- ADD THIS LINE

    # Data Directories
    DATA_RAW_PATH = DATA_DIR / "raw"
    DATA_PROCESSED_PATH = DATA_DIR / "processed"
    DATA_AUDIO_PATH = DATA_DIR / "audio"

    # Application Settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # API Settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))

    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')

    # Reddit Fetching Defaults
    DEFAULT_POST_LIMIT = 10
    DEFAULT_SORT_TYPE = 'hot'  # hot, new, top

    # Rate Limiting
    REQUESTS_PER_MINUTE = 30

    @classmethod
    def validate(cls):
        """Validate that all required settings are present"""
        errors = []

        if not cls.REDDIT_CLIENT_ID:
            errors.append("REDDIT_CLIENT_ID is missing")
        if not cls.REDDIT_CLIENT_SECRET:
            errors.append("REDDIT_CLIENT_SECRET is missing")
        if not cls.REDDIT_USER_AGENT:
            errors.append("REDDIT_USER_AGENT is missing")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        # Create directories if they don't exist
        cls.DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
        cls.DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
        cls.DATA_AUDIO_PATH.mkdir(parents=True, exist_ok=True)

        return True


# Create a config instance
config = Config()
