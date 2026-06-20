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
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def subprocess_check(module_name: str, timeout: int = 10) -> bool:
    """Check if a module can be imported by spawning a short-lived subprocess."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_name}; print('ok')"],
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False
