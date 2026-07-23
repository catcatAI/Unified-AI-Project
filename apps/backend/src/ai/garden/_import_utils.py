# =============================================================================
# ANGELA-MATRIX: [L2] [] [B] [L1]
# =============================================================================
"""
Safe import utilities for GARDEN.

On Windows/Python 3.14, torch and chromadb imports hang indefinitely
in-process. This module provides a subprocess-based probe that can be
killed cleanly, avoiding process-level deadlocks.
"""

import importlib.util
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


def _find_spec_fast(module_name: str) -> Optional[bool]:
    """Fast, non-executing availability probe via importlib.find_spec.

    ``find_spec`` only *locates* the module; it does not execute module code,
    so it returns instantly and never triggers the heavy in-process init that
    can hang on Windows/Python 3.14. Returns True/False when determinable, or
    None when the result is inconclusive (e.g. a namespace/implicit package).
    """
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        # A spec with a loader means the module is importable without running it.
        if getattr(spec, "loader", None) is not None:
            return True
        return None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False
    except Exception:
        logger.debug("find_spec failed for %r", module_name, exc_info=True)
        return None


def subprocess_check(module_name: str, timeout: Optional[int] = None) -> bool:
    """Check if a module can be imported.

    Uses a fast ``importlib.util.find_spec`` probe first (instant, no
    subprocess, no hang). Falls back to a bounded subprocess probe only when
    the spec check is inconclusive — preserving the ability to cleanly kill
    genuinely hanging in-process imports on Windows/Python 3.14.
    """
    fast = _find_spec_fast(module_name)
    if fast is not None:
        return fast
    # Inconclusive: fall back to the subprocess probe.
    timeout = _resolve_timeout(timeout)
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_name}; print('ok')"],
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        logger.debug("subprocess import check failed for %r", module_name, exc_info=True)
        return False
