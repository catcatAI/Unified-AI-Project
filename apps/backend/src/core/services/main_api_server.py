"""
DEPRECATED SHIM MODULE
This module is kept for backward compatibility only.
It re-exports the FastAPI application and helpers from
apps.backend.src.services.main_api_server.

All new code should import from:
    apps.backend.src.services.main_api_server

This file can be removed after dependent imports are migrated.
"""
from apps.backend.src.services.main_api_server import *  # noqa: F401,F403