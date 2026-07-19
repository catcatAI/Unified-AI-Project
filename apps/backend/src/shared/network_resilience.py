import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        last_exception = None
        delay = self.base_delay
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries} failed: {e}")
                    await asyncio.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
        raise last_exception


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self._state == "open":
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        try:
            result = await func(*args, **kwargs)
            self._failure_count = 0
            self._state = "closed"
            return result
        except Exception as e:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = "open"
                logger.warning(
                    "Circuit breaker opened after %d failures: %s", self._failure_count, e
                )
            raise
