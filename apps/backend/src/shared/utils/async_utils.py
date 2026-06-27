"""
Async utilities for unified async operations management
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional, Set

logger = logging.getLogger(__name__)

_background_tasks: Set[asyncio.Task] = set()


def safe_create_task(coro: Coroutine[Any, Any, Any],
                     name: Optional[str] = None,
                     on_error: Optional[Callable[[Exception], None]] = None) -> asyncio.Task:
    """安全地创建并追踪异步任务"""
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)

    def _done(t: asyncio.Task) -> None:
        _background_tasks.discard(t)
        try:
            t.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[Shared-Async] Task '{name}' failed: {e}", exc_info=True)
            if on_error:
                on_error(e)

    task.add_done_callback(_done)
    return task


def safe_create_task_sync(coro: Coroutine[Any, Any, Any],
                          name: Optional[str] = None,
                          on_error: Optional[Callable[[Exception], None]] = None) -> Optional[asyncio.Task]:
    """从同步上下文安全创建异步任务"""
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(coro, name=name)
        _background_tasks.add(task)

        def _done(t: asyncio.Task) -> None:
            _background_tasks.discard(t)
            try:
                t.result()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[Shared-Async] Task '{name}' failed: {e}", exc_info=True)
                if on_error:
                    on_error(e)

        task.add_done_callback(_done)
        return task
    except RuntimeError:
        logger.debug(f"[Shared-Async] No event loop, skipping task '{name}'")
        return None


async def gather_with_concurrency(n: int, *coros: Coroutine) -> list:
    """限制并发数的 gather"""
    semaphore = asyncio.Semaphore(n)

    async def _sem_coro(coro: Coroutine) -> Any:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_sem_coro(c) for c in coros))

