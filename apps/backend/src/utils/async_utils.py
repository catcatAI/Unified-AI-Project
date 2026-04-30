# =============================================================================
# ANGELA-MATRIX: [Shared-Utils] [A]
# =============================================================================
# 職責: 異步任務標準化工具 (Standardized Async Utilities).
# 目的: 防止未捕獲的異常導致後端核心崩潰，並提供任務生命週期管理。
# =============================================================================

import asyncio
import logging
import functools
from typing import Coroutine, Any, Optional, Set, Callable

logger = logging.getLogger(__name__)

# 全域任務追蹤，防止垃圾回收導致任務中斷
_background_tasks: Set[asyncio.Task] = set()

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
    
    def _handle_result(t: asyncio.Task):
        _background_tasks.discard(t)
        try:
            t.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ [Async-Task] Task '{name or 'unnamed'}' failed: {e}", exc_info=True)
            if on_error:
                on_error(e)

    task.add_done_callback(_handle_result)
    return task

def run_in_executor(executor=None):
    """
    裝飾器：將同步阻塞函數運行在執行器中。
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))
        return wrapper
    return decorator

async def gather_with_concurrency(n: int, *coros: Coroutine):
    """
    限制併發數量的 gather。
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))
