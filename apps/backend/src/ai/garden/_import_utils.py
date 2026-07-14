# =============================================================================
# ANGELA-MATRIX: [L2] [] [B] [L1]
# =============================================================================
"""
Safe import utilities for GARDEN.

On Windows/Python 3.14, torch and chromadb imports hang indefinitely
in-process. This module provides a subprocess-based probe that can be
killed cleanly, avoiding process-level deadlocks.
"""

import logging
import os
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_PROBE_TIMEOUT = 60


def _resolve_timeout(timeout: Optional[int]) -> int:
    """Resolve the probe timeout, honoring the GARDEN_IMPORT_PROBE_TIMEOUT env var.

    A generous default (60s) is used so that slow-but-working imports
    (e.g. torch ~25s, chromadb ~15s on some Windows/Python 3.14 setups)
    are not mis-classified as unavailable, while still bounding true
    indefinite hangs.
    """
    if timeout is not None:
        return timeout
    env_val = os.environ.get("GARDEN_IMPORT_PROBE_TIMEOUT")
    if env_val:
        try:
            return int(env_val)
        except ValueError:
            logger.warning("Invalid GARDEN_IMPORT_PROBE_TIMEOUT=%r; using default", env_val)
    return _DEFAULT_PROBE_TIMEOUT


def subprocess_check(module_name: str, timeout: Optional[int] = None) -> bool:
    """Check if a module can be imported by spawning a short-lived subprocess."""
    timeout = _resolve_timeout(timeout)
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_name}; print('ok')"],
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False
