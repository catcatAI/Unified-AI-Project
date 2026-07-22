"""
企業級錯誤處理系統
統一錯誤處理、錯誤分類和自動恢復機制
"""

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ErrorSeverity(enum.IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class ErrorCategory(enum.Enum):
    SYSTEM = "system"
    NETWORK = "network"
    SECURITY = "security"
    DATA = "data"
    INTEGRATION = "integration"
    CONFIGURATION = "configuration"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


class RecoveryStrategy(enum.Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_DEGRADE = "graceful_degrade"
    MANUAL_INTERVENTION = "manual_intervention"
    RESTART = "restart"


@dataclass
class CircuitBreaker:
    service_name: str
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    _failure_count: int = 0
    _last_failure_time: float = 0.0
    _is_open: bool = False

    def record_failure(self) -> None:
        import time

        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._is_open = True
            logger.warning(f"Circuit breaker '{self.service_name}' opened")

    def record_success(self) -> None:
        self._failure_count = 0
        self._is_open = False

    @property
    def is_open(self) -> bool:
        if not self._is_open:
            return False
        import time

        if time.time() - self._last_failure_time > self.recovery_timeout:
            self._is_open = False
            self._failure_count = 0
            return False
        return True


class ErrorHandler:
    def __init__(self, name: str = "default"):
        self.name = name
        self.handlers: Dict[ErrorCategory, Any] = {}

    def handle(self, error: Exception, category: ErrorCategory = ErrorCategory.RUNTIME) -> None:
        logger.debug(f"[{self.name}] Handling {category.value} error: {error}")
        handler = self.handlers.get(category)
        if handler:
            handler(error)
        else:
            logger.warning(f"No handler registered for {category.value}")
