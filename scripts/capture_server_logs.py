"""
Start backend server and capture ALL startup output.
Uses :mod:`scripts._server_helper` for robust server lifecycle.

Usage::

    python scripts/capture_server_logs.py
"""

import sys
import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from scripts._server_helper import get_project_root, get_src_path, _read_output_until
import subprocess

BACKEND_DIR = get_project_root() / "apps" / "backend"
SRC = get_src_path()

print("=== Capturing Server Startup Logs ===\n")

cmd=[
    sys.executable,
    "-m", "uvicorn",
    "src.services.main_api_server:app",
    "--host", "127.0.0.1",
    "--port", "8000",
    "--log-level", "info",
]

proc = subprocess.Popen(
    cmd,
    cwd=str(BACKEND_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

print(f"Server PID: {proc.pid}")
print("Capturing startup output (8s)...\n")

output = _read_output_until(proc, "", timeout=8.0)
print(output)

# Check status
if proc.poll() is None:
    print("\nServer still running. Testing endpoints...")
    import time
    time.sleep(1)  # let uvicorn finish binding

    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/ops/health")
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"HEALTH: {resp.status}")
        print(resp.read().decode()[:500])
    except Exception as e:
        print(f"HEALTH FAILED: {e}")

    proc.terminate()
    proc.wait()
    print("Server stopped.")
else:
    print(f"\nServer exited with code {proc.poll()}")

print("\n=== Done ===")
