#!/usr/bin/env python3
"""Test the FastAPI application"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
