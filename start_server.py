import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn
import main

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
