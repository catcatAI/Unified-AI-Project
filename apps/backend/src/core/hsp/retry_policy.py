from typing import Callable, Any
import asyncio

class RetryPolicy:
    """
    A simple retry policy for network operations.
    """
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    async def apply(self, func: Callable, *args, **kwargs) -> Any:
        """
        Applies the retry policy to an asynchronous function.
        """
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.initial_delay * (self.backoff_factor ** attempt)
                    print(f"Attempt {attempt + 1} failed. Retrying in {delay:.2f} seconds... Error: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"Attempt {attempt + 1} failed. No more retries. Error: {e}")
                    raise
