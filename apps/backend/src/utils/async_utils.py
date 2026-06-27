# =============================================================================
# ANGELA-MATRIX: [Shared-Utils] [A]
# =============================================================================
# 職責: 異步任務標準化工具 (Standardized Async Utilities).
# 目的: 防止未捕獲的異常導致後端核心崩潰，並提供任務生命週期管理。
# =============================================================================

import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine, Optional, Set

logger = logging.getLogger(__name__)

# 全域任務追蹤，防止垃圾回收導致任務中斷
_background_tasks: Set[asyncio.Task] = set()

def safe_create_task_sync(coro: Coroutine[Any, Any, Any],
                          name: Optional[str] = None,
                          on_error: Optional[Callable[[Exception], None]] = None) -> Optional[asyncio.Task]:
    """
    [Thread-Safe] 從同步上下文安全建立 async 任務。
    若無 running event loop 則靜默跳過（不崩潰）。
    """
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(coro, name=name)
        _background_tasks.add(task)

        def _handle_result(t: asyncio.Task) -> None:
            _background_tasks.discard(t)
            try:
                t.result()
            except asyncio.CancelledError:
                logger.debug(f"[Async-Task] Task '{name or 'unnamed'}' was cancelled")
            except Exception as e:
                logger.error(f"❌ [Async-Task] Task '{name or 'unnamed'}' failed: {e}", exc_info=True)
                if on_error:
                    on_error(e)

        task.add_done_callback(_handle_result)
        return task
    except RuntimeError:
        logger.debug(f"[Async-Task] No running event loop, skipping task '{name or 'unnamed'}'")
        return None


def safe_create_task(coro: Coroutine[Any, Any, Any], 
                     name: Optional[str] = None,
                     on_error: Optional[Callable[[Exception], None]] = None) -> asyncio.Task:
    """
    [2030 Standard] 安全地建立背景任務。
    - 自動追蹤任務引用。
    - 強制異常捕獲與日誌紀錄。
    - 支援自定義錯誤處理回調。
    """
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)
    
    def _handle_result(t: asyncio.Task) -> None:
        """Handle result request."""
        _background_tasks.discard(t)
        try:
            t.result()
        except asyncio.CancelledError:
            logger.debug(f"[Async-Task] Safe task '{name or 'unnamed'}' was cancelled")
        except Exception as e:  # broad exception acceptable: task result handling must not crash background workers
            logger.error(f"❌ [Async-Task] Task '{name or 'unnamed'}' failed: {e}", exc_info=True)
            if on_error:
                on_error(e)

    task.add_done_callback(_handle_result)
    return task

def run_in_executor(executor=None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    裝飾器：將同步阻塞函數運行在執行器中。
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator wrapper."""
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Inner wrapper function."""
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))
        return wrapper
    return decorator

async def gather_with_concurrency(n: int, *coros: Coroutine) -> List[Any]:
    """
    限制併發數量的 gather。
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro: Coroutine) -> Any:
        """Semaphore-wrapped coroutine."""
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))
