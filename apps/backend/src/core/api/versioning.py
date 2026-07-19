"""
Angela AI - API Versioning Middleware
Provides version negotiation and deprecation headers
"""

import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    API Versioning Middleware

    Supports:
    - Header-based versioning: Accept: application/vnd.angela.v1+json
    - Query parameter versioning: ?version=1
    - Deprecation headers for old versions
    """

    CURRENT_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1"]
    DEPRECATED_VERSIONS = []

    async def dispatch(self, request: Request, call_next):
        # Extract version from header
        version = self._extract_version_from_header(request)

        # Fallback to query parameter
        if not version:
            version = request.query_params.get("version")

        # Default to current version
        if not version:
            version = self.CURRENT_VERSION

        # Validate version
        if version not in self.SUPPORTED_VERSIONS:
            return Response(
                content=f"API version {version} not supported. Supported: {self.SUPPORTED_VERSIONS}",
                status_code=400,
            )

        # Add version to request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers
        response.headers["X-API-Version"] = version
        response.headers["X-API-Supported-Versions"] = ", ".join(self.SUPPORTED_VERSIONS)

        # Add deprecation header if needed
        if version in self.DEPRECATED_VERSIONS:
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2027-01-01"
            response.headers["X-API-Deprecation-Notice"] = f"API version {version} is deprecated"

        return response

    def _extract_version_from_header(self, request: Request) -> Optional[str]:
        """Extract version from Accept header."""
        accept = request.headers.get("Accept", "")

        # Parse: application/vnd.angela.v1+json
        if "application/vnd.angela." in accept:
            parts = accept.split(".")
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    return part

        return None


def add_version_header(response: Response, version: str) -> None:
    """Add version header to response."""
    response.headers["X-API-Version"] = version


def add_deprecation_header(
    response: Response, version: str, sunset_date: str = "2027-01-01"
) -> None:
    """Add deprecation header to response."""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = sunset_date
    response.headers["X-API-Deprecation-Notice"] = f"API version {version} is deprecated"
