#!/usr/bin/env python3
"""Test script for enhanced minimal backend"""
import sys
import os
sys.path.insert(0, "D:/Projects/Unified-AI-Project/apps/backend")

import uvicorn
import time
import threading
import requests

from enhanced_minimal_backend import app, init_mock_data, _mock_data

# Force initialization
print("Initializing mock data...")
init_mock_data()
print(f"  Pets: {list(_mock_data['pets'].keys())}")
print(f"  Inventory: {list(_mock_data['inventory'].keys())}")

# Add startup event to be sure
@app.on_event("startup")
async def startup():
    print("Startup event triggered")
    init_mock_data()

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8992, log_level="info")

if __name__ == "__main__":
    # Start server in thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3)

    # Test endpoints
    tests = [
        ("GET", "/api/v1/pet/proactive", None),
        ("GET", "/api/v1/economy/balance", None),
        ("GET", "/api/v1/pet/status", None),
        ("POST", "/api/v1/agents/creative_agent/task?task_description=hello", None),
    ]

    for method, path, data in tests:
        try:
            if method == "GET":
                r = requests.get(f"http://127.0.0.1:8992{path}")
            else:
                r = requests.post(f"http://127.0.0.1:8992{path}", json=data)
            print(f"{method} {path}: {r.status_code}")
            if r.status_code == 200:
                print(f"  ✅ {r.json().get('status', 'ok')}")
            else:
                print(f"  ❌ {r.text[:100]}")
        except Exception as e:
            print(f"{method} {path}: ERROR - {e}")

    print("\nDone!")
