import asyncio
import functools
import logging
logger: Any = logging.getLogger(__name__)

class AsyncManager:
    """統一異步操作管理器"""
    
    @staticmethod
    async def safe_gather(*coroutines, return_exceptions=True):
        """安全的並發執行"""
        try:
            return await asyncio.gather(*coroutines, return_exceptions=return_exceptions)
        except Exception as e:
            logger.error(f"Async gather failed: {e}")
            raise
    
    @staticmethod
    def timeout_wrapper(timeout: float):
        """超時裝飾器"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")
            return wrapper
        return decorator