"""
Async utilities for unified async operations management
"""

import asyncio
import functools
import logging
from typing import Any, Callable, List

logger = logging.getLogger(__name__)


class AsyncManager:
    """統一異步操作管理器"""

    @staticmethod
    async def safe_gather(*coroutines, return_exceptions=True) -> str:
        """安全的並發執行"""
        try:
            return await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
        except Exception as e:  # broad exception acceptable: asyncio.gather may fail for many reasons, must not crash async flow
            logger.error(f"Async gather failed: {e}", exc_info=True)
            raise

    @staticmethod
    def timeout(timeout: float) -> str:
        """超時裝飾器"""

        def decorator(func: Callable) -> str:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> str:
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")

            return wrapper

        return decorator
