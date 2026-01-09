import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Load environment variables from .env file (check multiple locations)
env_paths = [
    BASE_DIR / ".env",  # backend/.env
    BASE_DIR.parent / ".env",  # project root/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break


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

    # Post Filtering Defaults
    DEFAULT_MIN_UPVOTES = 500
    MEANINGFUL_TEXT_THRESHOLD = 50  # Characters for "meaningful text"

    # TTS Configuration
    class TTSConfig:
        """Text-to-Speech configuration and voice options"""
        DEFAULT_VOICE = "en-US"
        DEFAULT_LANGUAGE = "en"
        DEFAULT_SPEED = 1.0
        DEFAULT_ENGINE = "gtts"

        # Supported voices for gTTS (accent via TLD)
        GTTS_VOICES = {
            # English variants
            'en-US': {'language': 'en', 'tld': 'com', 'name': 'English (US)'},
            'en-GB': {'language': 'en', 'tld': 'co.uk', 'name': 'English (UK)'},
            'en-AU': {'language': 'en', 'tld': 'com.au', 'name': 'English (Australia)'},
            'en-IN': {'language': 'en', 'tld': 'co.in', 'name': 'English (India)'},
            'en-CA': {'language': 'en', 'tld': 'ca', 'name': 'English (Canada)'},

            # Additional languages
            'es-ES': {'language': 'es', 'tld': 'es', 'name': 'Spanish (Spain)'},
            'es-MX': {'language': 'es', 'tld': 'com.mx', 'name': 'Spanish (Mexico)'},
            'fr-FR': {'language': 'fr', 'tld': 'fr', 'name': 'French (France)'},
            'fr-CA': {'language': 'fr', 'tld': 'ca', 'name': 'French (Canada)'},
            'de-DE': {'language': 'de', 'tld': 'de', 'name': 'German'},
            'it-IT': {'language': 'it', 'tld': 'it', 'name': 'Italian'},
            'ja-JP': {'language': 'ja', 'tld': 'co.jp', 'name': 'Japanese'},
            'pt-BR': {'language': 'pt', 'tld': 'com.br', 'name': 'Portuguese (Brazil)'},
            'pt-PT': {'language': 'pt', 'tld': 'pt', 'name': 'Portuguese (Portugal)'},
        }

        # Supported speech rates
        SPEED_PRESETS = {
            'slow': 0.75,
            'normal': 1.0,
            'fast': 1.25,
            'very_fast': 1.5
        }

        # Valid speed range
        MIN_SPEED = 0.5
        MAX_SPEED = 2.0

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
