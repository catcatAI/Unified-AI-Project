from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from apps.backend.src.core.logging.logger import logger  # New import


# Custom Exceptions
class UnifiedAIException(HTTPException):
    """Base exception for Unified AI Project."""

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(UnifiedAIException):
    """Raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(UnifiedAIException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(UnifiedAIException):
    """Raised when authorization fails."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(UnifiedAIException):
    """Raised when a request is malformed or invalid."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# Global Exception Handler
async def unified_ai_exception_handler(request: Request, exc: UnifiedAIException):
    """Handles custom UnifiedAIExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
        headers=exc.headers,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handles generic unexpected exceptions."""
    from apps.backend.src.core.logging.logger import logger

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred."},
    )


def register_exception_handlers(app: FastAPI):
    """Registers custom exception handlers with the FastAPI application."""
    app.add_exception_handler(UnifiedAIException, unified_ai_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    logger.info("Custom exception handlers registered.")


if __name__ == "__main__":
    # Example Usage (requires FastAPI app context)
    # This block is for demonstration and won't run without a full FastAPI app.
    # You would typically call register_exception_handlers(app) in your main.py
    print("This module defines custom exceptions and handlers. Run within FastAPI app.")
    # Example of how to raise and catch
    raise NotFoundException(detail="Agent not found")

    raise RuntimeError("Something went wrong!")
