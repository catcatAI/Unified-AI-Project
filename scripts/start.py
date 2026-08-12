#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [η] [A] [L1+]
# =============================================================================
"""
Angela AI — Start Script.

Starts both backend and frontend with a single command.

Usage:
    python start.py              # Start backend + web viewer
    python start.py --backend    # Start backend only
    python start.py --frontend   # Start frontend only
"""

import argparse
import logging
import os
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Start")

ROOT = os.path.dirname(os.path.abspath(__file__))


def start_backend(host="127.0.0.1", port=8000):
    """Start the FastAPI backend."""
    logger.info("Starting backend on %s:%d", host, port)
    backend_dir = os.path.join(ROOT, "apps", "backend")

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.services.main_api_server:app",
         "--host", host, "--port", str(port), "--reload"],
        cwd=backend_dir,
    )
    logger.info("Backend PID: %d", proc.pid)
    return proc


def start_web_viewer():
    """Start the web Live2D viewer (simple HTTP server)."""
    web_dir = os.path.join(ROOT, "apps", "web-live2d-viewer")
    if not os.path.exists(web_dir):
        logger.warning("Web viewer not found at %s", web_dir)
        return None

    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080"],
        cwd=web_dir,
    )
    logger.info("Web viewer PID: %d (http://localhost:8080)", proc.pid)
    return proc


def main():
    parser = argparse.ArgumentParser(description="Angela AI — Start")
    parser.add_argument("--backend-only", action="store_true", help="Start backend only")
    parser.add_argument("--frontend-only", action="store_true", help="Start frontend only")
    parser.add_argument("--host", default="127.0.0.1", help="Backend host")
    parser.add_argument("--port", type=int, default=8000, help="Backend port")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Angela AI — Starting")
    logger.info("=" * 60)

    processes = []

    if not args.frontend_only:
        try:
            proc = start_backend(args.host, args.port)
            processes.append(("backend", proc))
        except Exception as e:
            logger.error("Failed to start backend: %s", e)

    if not args.backend_only:
        try:
            proc = start_web_viewer()
            if proc:
                processes.append(("web", proc))
        except Exception as e:
            logger.error("Failed to start web viewer: %s", e)

    if not processes:
        logger.error("No services started")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Angela AI running. Press Ctrl+C to stop.")
    logger.info("=" * 60)

    try:
        while True:
            time.sleep(1)
            for name, proc in processes:
                if proc.poll() is not None:
                    logger.warning("%s exited with code %d", name, proc.returncode)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        for name, proc in processes:
            proc.terminate()
            logger.info("  %s terminated", name)


if __name__ == "__main__":
    main()
