"""
Configuration for pytest: Add project source directories to the Python path.
"""

import sys
import os
import logging
from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "apps", "backend", "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture(scope="session")
def minimal_app() -> FastAPI:
    """
    Minimal FastAPI app for tests that don't need the full server.
    Provides basic health check and system endpoints without heavy imports.
    Lazy import: only loaded when fixture is actually used, not during collection.
    """
    from fastapi import APIRouter

    router = APIRouter(prefix="/api/v1")

    @router.get("/")
    async def root():
        return {"message": "Unified AI Project API"}

    @router.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @router.get("/system/emergency")
    async def trigger_emergency_mode():
        return {
            "status": "emergency_active",
            "action": "Visual/Audio components suspended",
            "mode": "text-only",
        }

    app = FastAPI(title="Angela AI API", version="6.0.4")
    app.include_router(router)
    return app


@pytest.fixture
def minimal_client(minimal_app: FastAPI) -> TestClient:
    """TestClient for the minimal app"""
    return TestClient(minimal_app)


@pytest.fixture(scope="session")
def heavy_import_available() -> bool:
    """Check if heavy imports (main_api_server) are available"""
    try:
        import services.main_api_server
        return True
    except ImportError:
        return False



