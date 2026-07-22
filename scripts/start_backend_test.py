"""
Start backend server and test health/chat endpoints.
Uses :mod:`scripts._server_helper` for robust server lifecycle management.

Usage::

    python scripts/start_backend_test.py
"""

import sys
import os

# Add project root to sys.path so we can import _server_helper
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from scripts._server_helper import start_server, stop_server, wait_for_server, test_health, test_chat

WAIT_SECONDS=10.0


def main():
    print("=== Backend Server Test ===")
    print(f"Starting server (wait {WAIT_SECONDS}s for readiness)...")

    proc = start_server(wait_seconds=WAIT_SECONDS)
    print(f"Server PID: {proc.pid}")

    # Wait for server to accept connections
    ready = wait_for_server(timeout=WAIT_SECONDS)
    if not ready:
        print("❌ Server did not become ready within timeout.")
        stop_server(proc)
        sys.exit(1)

    print("✅ Server is accepting connections.\n")

    # Health check
    print("--- Health Check ---")
    ok, data = test_health()
    print(f"{'✅' if ok else '❌'} {data}\n")

    # Chat test
    print("--- Chat Test ---")
    ok, data = test_chat("hello")
    print(f"{'✅' if ok else '❌'} {str(data)[:500]}\n")

    # Stop
    stop_server(proc)
    print("✅ Server stopped cleanly")


if __name__ == "__main__":
    main()
