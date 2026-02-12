from typing import Callable, Any
import asyncio
import logging
logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    A simple circuit breaker implementation.
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30, expected_exceptions: tuple = (Exception,)):
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def _can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if (asyncio.get_event_loop().time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF-OPEN"
                return True
            return False
        elif self.state == "HALF-OPEN":
            return True
        return False

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            if not self._can_execute():
                raise CircuitBreakerOpenException("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                self.failures = 0 # Reset on success
                self.state = "CLOSED"
                return result
            except self.expected_exceptions as e:
                self.failures += 1
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    self.last_failure_time = asyncio.get_event_loop().time()
                raise e
        return wrapper

class CircuitBreakerOpenException(Exception):
    """
    Exception raised when the circuit breaker is open.
    """
    pass
