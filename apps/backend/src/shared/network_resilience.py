import asyncio
import time
import logging
from typing import Callable, Any, Dict, List, Optional, Tuple, Type

logger = logging.getLogger(__name__)

class NetworkError(Exception):
    """Indicates a network-related failure that might be transient."""
    pass

class ProtocolError(Exception):
    """Indicates a protocol-level error that is likely not transient."""
    pass

class CircuitBreakerOpenError(Exception):
    """Exception raised when the circuit breaker is open."""
    pass

CircuitBreakerOpenException = CircuitBreakerOpenError  # Alias for compatibility

class RetryPolicy:
    """Implement retry policy with exponential backoff and maximum attempts."""

    def __init__(self, max_attempts: int = 3, backoff_factor: float = 2.0,
                 max_delay: float = 30.0) -> None:
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(self.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (NetworkError, asyncio.TimeoutError) as e:
                    last_err = e
                    delay = min(self.max_delay, self.backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{self.max_attempts} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                except ProtocolError as e:
                    logger.error(f"Protocol error during {func.__name__}: {e}. Not retrying.")
                    raise
                except Exception as e:
                    logger.error(f"Non-retryable error during {func.__name__}: {e}")
                    raise
            
            logger.error(f"Max retries exceeded for {func.__name__}.")
            raise NetworkError(f"Operation failed after {self.max_attempts} attempts. Last error: {last_err}")
        return wrapper

class CircuitBreaker:
    """Implement circuit breaker pattern to prevent repeated access to failing services."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0, 
                 expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if (time.time() - self.last_failure_time) > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.logger.info(f"Circuit Breaker for {func.__name__} transitioned to HALF_OPEN. Probing...")
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker is OPEN. {func.__name__} is unavailable.")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exceptions as e:
                self.logger.error(f"Failure in {func.__name__}: {e}")
                self._on_failure()
                raise
            except Exception as e:
                # Unexpected exceptions pass through without being counted toward threshold
                # unless they are in expected_exceptions
                self.logger.error(f"Unexpected non-expected exception in {func.__name__}: {e}")
                raise
        return wrapper

    def _on_success(self):
        if self.state == "HALF_OPEN":
            self.logger.info("Circuit Breaker transitioned to CLOSED. Service recovered.")
            self.state = "CLOSED"
        self.failures = 0

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit Breaker transitioned to OPEN after {self.failures} failures.")

class NetworkResilienceManager:
    """Utility class for obtaining predefined resilience patterns."""
    @staticmethod
    def get_retry_policy(max_attempts: int = 3) -> RetryPolicy:
        return RetryPolicy(max_attempts=max_attempts)

    @staticmethod
    def get_circuit_breaker(failure_threshold: int = 5) -> CircuitBreaker:
        return CircuitBreaker(failure_threshold=failure_threshold)
