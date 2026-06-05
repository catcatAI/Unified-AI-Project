#!/usr/bin/env python3
"""
Angela AI - Unified Error Handling System
统一错误处理系统

提供统一的错误类型和错误处理机制，便于错误追踪和调试。
"""


class AngelaError(Exception):
    """Base exception for all Angela AI errors."""

    def __init__(self, message: str = "", code: str = "ANGELA_ERR", details: dict = None):
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(AngelaError):
    """Configuration related errors."""

    def __init__(self, message: str = "", details: dict = None):
        super().__init__(message, code="CONFIG_ERR", details=details)


class ValidationError(AngelaError):
    """Data validation errors."""

    def __init__(self, message: str = "", details: dict = None):
        super().__init__(message, code="VALIDATION_ERR", details=details)


class ResourceNotFoundError(AngelaError):
    """Resource not found errors."""

    def __init__(self, message: str = "", resource: str = "", details: dict = None):
        d = {"resource": resource}
        if details:
            d.update(details)
        super().__init__(message, code="NOT_FOUND_ERR", details=d)


class ServiceError(AngelaError):
    """Service layer errors."""

    def __init__(self, message: str = "", service: str = "", details: dict = None):
        d = {"service": service}
        if details:
            d.update(details)
        super().__init__(message, code="SERVICE_ERR", details=d)


class MemoryError(AngelaError):
    """Memory system errors."""

    def __init__(self, message: str = "", details: dict = None):
        super().__init__(message, code="MEMORY_ERR", details=details)


class IntentError(AngelaError):
    """Intent detection errors."""

    def __init__(self, message: str = "", details: dict = None):
        super().__init__(message, code="INTENT_ERR", details=details)


class CardError(AngelaError):
    """Card import pipeline errors."""

    def __init__(self, message: str = "", details: dict = None):
        super().__init__(message, code="CARD_ERR", details=details)


class MonitoringError(AngelaError):
    """Monitoring system errors."""

    def __init__(self, message: str = "", details: dict = None):
        super().__init__(message, code="MONITOR_ERR", details=details)


__all__ = [
    "AngelaError",
    "ConfigurationError",
    "ValidationError",
    "ResourceNotFoundError",
    "ServiceError",
    "MemoryError",
    "IntentError",
    "CardError",
    "MonitoringError",
]
