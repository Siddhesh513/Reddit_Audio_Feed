#!/usr/bin/env python3
"""Debug import issues"""

import sys
from pathlib import Path

print("Current file:", __file__)
print("Parent dir:", Path(__file__).parent)
print("Backend dir:", Path(__file__).parent.parent)

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

print("\nPython path:")
for p in sys.path[:3]:
    print(f"  - {p}")

print("\nTrying imports...")

try:
    import src
    print("✓ src module found")
except ImportError as e:
    print(f"✗ src import failed: {e}")

try:
    from src.utils import loggers
    print("✓ loggers module found")
except ImportError as e:
    print(f"✗ loggers import failed: {e}")

try:
    from src.utils.loggers import logger
    print("✓ logger imported successfully")
except ImportError as e:
    print(f"✗ logger import failed: {e}")
