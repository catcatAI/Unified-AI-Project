"""Shared dependency functions for FastAPI Depends injection (A5)."""

from integrations.google_drive_service import get_drive_service

__all__ = ["get_drive_service"]
