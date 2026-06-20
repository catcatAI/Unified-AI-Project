"""
Start the backend server and capture ALL startup output.
This helps diagnose why the server starts but endpoints aren't accessible.
"""
import subprocess
import sys
import os
import time

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
PROJECT = os.path.dirname(SRC)

# Start server and capture output
proc = subprocess.Popen(
    [sys.executable, "-u", "-c", """
import sys
sys.path.insert(0, "apps/backend/src")
print("=== SERVER STARTING ===", flush=True)
from services.main_api_server import app
print(f"App created: {len(app.routes)} routes", flush=True)
import uvicorn
print("Starting uvicorn...", flush=True)
uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
"""],
    cwd=PROJECT,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print(f"Server PID: {proc.pid}")
print("Waiting for startup output...", flush=True)

# Read output line by line for 10 seconds
start = time.time()
lines = []
while time.time() - start < 10:
    ret = proc.poll()
    if ret is not None:
        remaining = proc.stdout.read()
        lines.append(f"[EXIT code {ret}] {remaining}")
        break
    try:
        line = proc.stdout.readline()
        if line:
            lines.append(line.rstrip())
            print(f"  > {line.rstrip()}")
    except:
        break

# Print full log
print(f"\n=== Full log ({len(lines)} lines) ===")
for line in lines:
    print(line)

# Check if still running
if proc.poll() is None:
    print("\nServer still running - testing endpoints...")
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/ops/health")
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"HEALTH OK: {resp.status}")
        print(resp.read().decode()[:500])
    except Exception as e:
        print(f"HEALTH FAILED: {e}")
    proc.terminate()
    proc.wait()
    print("Server stopped")

print("\n=== Done ===")
