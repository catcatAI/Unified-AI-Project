import asyncio
import time
import logging

logger: Any = logging.getLogger(__name__)

class NetworkError(Exception):
    """Indicates a network-related failure that might be transient."""
    pass

class ProtocolError(Exception):
    """Indicates a protocol-level error that is likely not transient."""
    pass

class RetryPolicy:
    """實現帶有指數退避和最大嘗試次數的重試策略。"""

    def __init__(self, max_attempts: int = 3, backoff_factor: float = 2.0, max_delay: float = 30.0) -> None:
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            for attempt in range(self.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except NetworkError as e:
                    delay = min(self.max_delay, self.backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{self.max_attempts}: Network error during {func.__name__}. Retrying in {delay:.2f}s... Error: {e}")
                    _ = await asyncio.sleep(delay)
                except ProtocolError:
                    logger.error(f"Protocol error during {func.__name__}. Not retrying.")
                    raise # Re-raise non-retryable errors immediately
                except Exception as e:
                    logger.error(f"Unexpected error during {func.__name__}: {e}. Not retrying.")
                    raise
            logger.error(f"Max retries exceeded for {func.__name__}.")
            raise NetworkError(f"Operation failed after {self.max_attempts} attempts due to network issues.")
        return wrapper

class CircuitBreaker:
    """實現熔斷模式以防止重複訪問失敗的服務。"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.logger.info("Circuit Breaker: State changed to HALF_OPEN. Probing service...")
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker is OPEN. Service {func.__name__} is unavailable.")

            try:
                result = await func(*args, **kwargs)
                self._success
                return result
            except Exception as e:
                self._fail
                raise # Re-raise original exception

        return wrapper

    def _success(self):
        if self.state == "HALF_OPEN":
            self.logger.info("Circuit Breaker: Service recovered. State changed to CLOSED.")
            self.state = "CLOSED"
        self.failures = 0

    def _fail(self):
        self.failures += 1
        self.last_failure_time = time.time
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit Breaker: Failure threshold reached ({self.failures} failures). State changed to OPEN.")

class CircuitBreakerOpenError(Exception):
    """Exception raised when the circuit breaker is open."""
    pass