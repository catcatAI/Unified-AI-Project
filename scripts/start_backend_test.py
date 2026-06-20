"""
Start backend server and test health/chat endpoints.
Run: python scripts/start_backend_test.py
"""

import subprocess
import sys
import os
import time
import urllib.request
import json

# Add src to path
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
sys.path.insert(0, SRC_PATH)

# Start server process
proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import sys
sys.path.insert(0, "apps/backend/src")
from services.main_api_server import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
"""],
    cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print(f"Server PID: {proc.pid}")

# Wait for startup
time.sleep(5)

# Check if process is still running
poll = proc.poll()
if poll is not None:
    print(f"Server exited early with code {poll}")
    output = proc.stdout.read()
    print(f"Output:\n{output[-2000:]}")
    sys.exit(1)

print("Server is running")

# Test health endpoint
try:
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/ops/health")
    resp = urllib.request.urlopen(req, timeout=5)
    print(f"Health: {resp.status}")
    print(resp.read().decode()[:500])
except Exception as e:
    print(f"Health failed: {e}")

# Test chat endpoint
try:
    data = json.dumps({"message": "hello"}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/angela/chat",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    print(f"Chat: {resp.status}")
    print(resp.read().decode()[:1000])
except Exception as e:
    print(f"Chat failed: {e}")

# Stop server
proc.terminate()
try:
    proc.wait(timeout=5)
    print("Server stopped cleanly")
except:
    proc.kill()
    print("Server killed")
