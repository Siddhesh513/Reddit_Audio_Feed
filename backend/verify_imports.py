#!/usr/bin/env python3
print("Testing imports...")

try:
    import praw
    print("✓ praw imported successfully")
except ImportError as e:
    print(f"✗ praw import failed: {e}")

try:
    import dotenv
    print("✓ dotenv imported successfully")
except ImportError as e:
    print(f"✗ dotenv import failed: {e}")

try:
    import loguru
    print("✓ loguru imported successfully")
except ImportError as e:
    print(f"✗ loguru import failed: {e}")

try:
    import requests
    print("✓ requests imported successfully")
except ImportError as e:
    print(f"✗ requests import failed: {e}")

import sys
print(f"\nPython executable: {sys.executable}")
print(f"Python version: {sys.version}")
