"""
ANGELA-MATRIX: [L1] [β] [B] [L0]
Server Helper Module
====================
Shared utilities for backend server diagnostic scripts.
Replaces fragile inline subprocess Python code with importable helpers.

Usage:
    from scripts._server_helper import start_server, test_health, test_chat
"""

import os
import sys
import time
import json
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List


# ---- Path resolution ----

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def get_src_path() -> Path:
    """Return apps/backend/src path."""
    return get_project_root() / "apps" / "backend" / "src"


# ---- Server lifecycle ----

def start_server(
    host: str="127.0.0.1",
    port: int=8000,
    wait_seconds: float=30.0,
    log_level: str="info",
) -> subprocess.Popen:
    """Start the backend server using uvicorn.

    Uses ``python -m uvicorn`` (the same approach as ``scripts/start_backend.bat``)
    which avoids the subprocess quoting issues of inline Python code.

    Returns the Popen object so the caller can terminate it later.
    """
    backend_dir = get_project_root() / "apps" / "backend"
    cmd=[
        sys.executable,
        "-m", "uvicorn",
        "src.services.main_api_server:app",
        "--host", host,
        "--port", str(port),
        "--log-level", log_level,
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Wait for startup, reading initial output
    output = _read_output_until(proc, "Uvicorn running on", timeout=wait_seconds)

    # Check if the process died during startup
    exit_code = proc.poll()
    if exit_code is not None:
        raise RuntimeError(
            f"Server exited during startup with code {exit_code}.\n{output[-1000:]}"
        )

    return proc


def stop_server(proc: subprocess.Popen, timeout: float=5.0) -> None:
    """Gracefully stop a server process."""
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _read_output_until(
    proc: subprocess.Popen,
    marker: str,
    timeout: float=10.0,
) -> str:
    """Read server output until a marker appears or timeout.

    Uses a background thread to avoid blocking on ``readline()``.
    """
    output: List[str] = []
    done_event = threading.Event()

    def _reader():
        try:
            for raw_line in iter(proc.stdout.readline, ""):
                line = raw_line.rstrip()
                output.append(line)
                if marker and marker in line:
                    done_event.set()
                    return
        except (ValueError, OSError):
            pass
        finally:
            done_event.set()

    reader = threading.Thread(target=_reader, daemon=True)
    reader.start()

    # Wait for either completion or timeout
    done_event.wait(timeout=timeout)

    # Don't terminate the thread — it'll exit when the pipe closes
    return "\n".join(output)


def wait_for_server(
    host: str="127.0.0.1",
    port: int=8000,
    timeout: float=40.0,
    interval: float=1.0,
) -> bool:
    """Wait until the server is accepting connections.

    Returns True if the server becomes available within the timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"http://{host}:{port}/api/v1/ops/health")
            urllib.request.urlopen(req, timeout=2)
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(interval)
    return False


# ---- Endpoint tests ----

def test_health(
    host: str="127.0.0.1",
    port: int=8000,
    timeout: float=5.0,
) -> Tuple[bool, Dict[str, Any]]:
    """Test the health endpoint. Returns (ok, data)."""
    try:
        req = urllib.request.Request(f"http://{host}:{port}/api/v1/ops/health")
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode())
        return True, data
    except Exception as e:
        return False, {"error": str(e)}


def test_chat(
    message: str="hello",
    host: str="127.0.0.1",
    port: int=8000,
    timeout: float=15.0,
) -> Tuple[bool, Dict[str, Any]]:
    """Test the chat endpoint. Returns (ok, data)."""
    try:
        payload = json.dumps({"message": message}).encode()
        req = urllib.request.Request(
            f"http://{host}:{port}/api/v1/angela/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode())
        return True, data
    except Exception as e:
        return False, {"error": str(e)}


# ---- LLM config inspection ----

def get_llm_config() -> Dict[str, Any]:
    """Load the LLM config YAML and return providers with their enabled status."""
    import yaml
    config_path = get_project_root() / "apps" / "backend" / "configs" / "system" / "llm.default.yaml"
    try:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ---- Quick run (standalone) ----

if __name__ == "__main__":
    print(" === Server Helper — Quick Test === ")
    print(f"Project root: {get_project_root()}")
    print(f"Src path: {get_src_path()}")

    # Start server (default 30s startup wait)
    print("\nStarting server (30s init timeout)...")
    proc = start_server()
    print(f"Server PID: {proc.pid}")

    # Wait for it to be ready (default 40s poll timeout)
    ready = wait_for_server()
    if ready:
        print("Server is accepting connections.")

        # Health check
        ok, data = test_health()
        print(f"Health: {'✅' if ok else '❌'} {data}")

        # Chat test
        ok, data = test_chat()
        print(f"Chat: {'✅' if ok else '❌'} {str(data)[:200]}")
    else:
        print("Server did not become ready within timeout.")

    stop_server(proc)
    print("\nDone.")
