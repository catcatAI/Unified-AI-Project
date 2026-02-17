#!/usr/bin/env python3
"""Test backend import to verify no AI system errors"""

import sys
import os

# Add apps/backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps', 'backend')
sys.path.insert(0, backend_path)

print("Testing backend import...")
try:
    from src.services.main_api_server import app
    print("✓ Backend import successful - no AI system errors")
    sys.exit(0)
except Exception as e:
    print(f"✗ Backend import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
