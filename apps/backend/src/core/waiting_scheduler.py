"""
WaitingScheduler — 統一把等待線程
==================================

所有會阻塞的等待（LLM 呼叫、健康檢查等）全部統一排程。
一個獨立線程，均勻分布在 1 秒時間槽中。
新的等待插入時，現有任務重新平衡分配。

設計：
  - 1 秒 = 1 個時間槽（slot）
  - 每個 slot 可容納 N 個任務（N = ceil(總任務數 / 最大秒數)）
  - 新任務插入時，所有任務在剩餘時間內均勻重新分配
  - 超時保護：LLM 8s，健康檢查 2s

用法：
  scheduler = WaitingScheduler()
  result = await scheduler.submit(llm_call_coro, timeout=8.0, label="llm:喵")
"""

from __future__ import annotations
import asyncio
import logging
import time
import threading
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import heapq
from core.interfaces.service_registry import get_registry

logger = logging.getLogger(__name__)


@dataclass(order=True)
class ScheduledTask:
    """排程任務 / Scheduled task with priority (deadline)"""
    deadline: float = field(compare=True)
    submit_time: float = field(compare=True)
    label: str = ""
    timeout: float = 8.0
    coro: Optional[Coroutine] = field(default=None, compare=False)
    future: Optional[asyncio.Future] = field(default=None, compare=False)
    slot_index: int = 0


class WaitingScheduler:
    """
    統一等待線程管理器
    =================

    所有阻塞等待任務在一個獨立線程中排程執行。
    避免多個 asyncio task 同時等待、後端超時把整個 event loop 卡死。

    核心邏輯：
      - 任務按 deadline 排列（最早的先執行）
      - 新任務插入時，根據剩餘時間均勻分配到各 slot
      - 每個 slot 的任務數量均衡：ceil(total_tasks / remaining_seconds)
      - 單一工作者線程，不阻塞主 event loop
    """

    def __init__(self, max_wait_seconds: float = 30.0):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.max_wait_seconds = max_wait_seconds
        self._queue: List[ScheduledTask] = []
        self._active_count = 0
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._results: Dict[str, Any] = {}
        self._futures_map: Dict[str, asyncio.Future] = {}

        self._start_worker()

    def _start_worker(self) -> None:
        """啟動統一工作者線程"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="WaitingScheduler-Worker")
        self._thread.start()
        logger.info("[WaitingScheduler] Worker thread started")

    def _worker_loop(self) -> None:
        """工作者線程主迴圈"""
        while not self._stop_event.is_set():
            task_to_run = None

            with self._lock:
                while len(self._queue) == 0 and not self._stop_event.is_set():
                    self._cond.wait(timeout=0.5)

                if self._stop_event.is_set():
                    break

                if len(self._queue) == 0:
                    continue

                heapq.heapify(self._queue)
                task = heapq.heappop(self._queue)
                deadline = task.deadline
                now = time.monotonic()
                wait_remaining = deadline - now

                if wait_remaining > 0:
                    heapq.heappush(self._queue, task)
                    self._cond.wait(timeout=min(wait_remaining, 0.5))
                    continue

                task_to_run = task

            if task_to_run:
                self._execute_task(task_to_run)

    def _execute_task(self, task: ScheduledTask) -> None:
        """在工作者線程中執行任務（同步包裝 async）"""
        label = task.label
        timeout = task.timeout

        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._run_coro_with_timeout(task.coro, timeout))
            self._results[label] = result
        except Exception as e:
            logger.warning(f"[WaitingScheduler] Task '{label}' failed: {e}")
            self._results[label] = None
        finally:
            if loop:
                loop.close()

            future = self._futures_map.pop(label, None)
            if future and not future.done():
                result = self._results.get(label)
                future.set_result(result)

    async def _run_coro_with_timeout(self, coro: Optional[Coroutine], timeout: float) -> Any:
        """執行 coroutine 並超時"""
        if coro is None:
            return None
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"[WaitingScheduler] Task timed out after {timeout}s")
            return None
        except Exception as e:
            logger.warning(f"[WaitingScheduler] Task error: {e}")
            return None

    def submit(
        self,
        coro: Coroutine,
        timeout: float = 8.0,
        label: str = "",
    ) -> asyncio.Future:
        """
        提交一個等待任務到排程器

        Args:
            coro: 要執行的 coroutine
            timeout: 超時秒數（預設 8s）
            label: 任務標籤（用於識別結果）

        Returns:
            asyncio.Future，任務完成時 result 存在 future.result() 中
        """
        if not label:
            label = f"task_{time.time():.0f}"

        now = time.monotonic()
        remaining = self.max_wait_seconds

        with self._lock:
            self._active_count = len(self._queue) + 1

            if self._active_count > 1:
                per_slot = max(1, self._active_count // max(1, int(remaining)))
                for i, t in enumerate(self._queue):
                    remaining_seconds = max(0.1, t.deadline - now)
                    base_interval = remaining_seconds / self._active_count
                    slot_offset = (i % self._active_count) * base_interval
                    t.deadline = now + remaining_seconds - slot_offset

            deadline = now + remaining

            task = ScheduledTask(
                deadline=deadline,
                submit_time=now,
                label=label,
                timeout=timeout,
                coro=coro,
            )

            heapq.heappush(self._queue, task)
            self._cond.notify()

        future = asyncio.Future()
        self._futures_map[label] = future
        return future

    def submit_blocking(
        self,
        coro: Coroutine,
        timeout: float = 8.0,
        label: str = "",
    ) -> asyncio.Future:
        """
        提交並確保工作者線程活著（自動重啟如果死了）
        """
        if not self.is_alive():
            logger.warning("[WaitingScheduler] Worker dead, restarting...")
            self._start_worker()

        return self.submit(coro, timeout=timeout, label=label)

    def is_alive(self) -> bool:
        """檢查工作者線程是否還在運行"""
        return self._thread is not None and self._thread.is_alive()

    def get_result(self, label: str, default: Any = None) -> Any:
        """獲取已完成任務的結果（非阻塞）"""
        return self._results.pop(label, default)

    def clear(self) -> None:
        """清除所有排程任務"""
        with self._lock:
            self._queue.clear()
            self._active_count = 0

    def shutdown(self) -> None:
        """關閉排程器"""
        self._stop_event.set()
        with self._lock:
            self._cond.notify_all()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("[WaitingScheduler] Worker thread stopped")


_scheduler_instance: Optional[WaitingScheduler] = None


def get_waiting_scheduler() -> WaitingScheduler:
    """取得全域 WaitingScheduler 實例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WaitingScheduler(max_wait_seconds=30.0)
        get_registry().register("waiting_scheduler", _scheduler_instance)
    return _scheduler_instance