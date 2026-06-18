"""Shared dependency functions for FastAPI Depends injection (A5)."""

from integrations.google_drive_service import get_drive_service

__all__ = ["get_drive_service", "set_economy_manager"]

_economy_manager = None


def set_economy_manager(mgr):
    """Store the economy manager for cross-service access."""
    global _economy_manager
    _economy_manager = mgr


def get_economy_manager():
    """Return the stored economy manager."""
    return _economy_manager
