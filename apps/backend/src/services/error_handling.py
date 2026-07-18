# =============================================================================
# ANGELA-MATRIX: [L2] [β] [C] [L0]
# =============================================================================
"""Centralized error-handling helpers for service-layer code.

Provides ``safe_error`` (sanitizes exception text for user-facing output) and
a small set of shared error types. Previously some modules imported this from
``services.error_handling``; the implementation lives in ``core.utils`` and is
re-exported here so both import paths work.
"""

from core.utils import safe_error as _safe_error

__all__ = ["safe_error", "ServiceError"]


class ServiceError(Exception):
    """Base class for recoverable service-layer errors."""


def safe_error(e: Exception, max_length: int = 200) -> str:
    """Sanitize an exception message for safe user-facing display.

    Delegates to :func:`core.utils.safe_error`.
    """
    return _safe_error(e, max_length)
