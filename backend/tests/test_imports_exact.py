#!/usr/bin/env python3
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print(f"Python: {sys.executable}")
print(f"Path added: {backend_dir}")

# Now try imports
try:
    from src.services.text_processor import get_text_processor
    from src.services.reddit_service import get_reddit_client
    from src.utils.text_helper import TextHelpers, extract_statistics
    from src.utils.loggers import logger
    print("✓ All imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
