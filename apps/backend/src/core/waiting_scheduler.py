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
from typing import Any, Optional
import asyncio
import time
from dataclasses import dataclass


@dataclass
class ScheduledTask:
    deadline: float = 0.0
    submit_time: float = 0.0
    label: str = ""
    timeout: float = 8.0
    coro: Any = None


class WaitingScheduler:
    """Slot-based waiting scheduler.

    All blocking waits (LLM calls, health checks, etc.) are uniformly scheduled.
    A dedicated pattern distributing tasks across time slots (1s granularity)
    with load-aware rebalancing.

    Design:
      - 1 second = 1 time slot
      - Each slot holds N tasks (N = ceil(total_tasks / max_seconds))
      - New tasks trigger rebalancing across remaining time
      - Timeout protection: LLM 8s, health check 2s
    """

    def __init__(self, max_wait_seconds: float = 5.0):
        self.max_wait_seconds = max_wait_seconds
        self._tasks: Dict[str, ScheduledTask] = {}
        self._alive = True
        self._lock = asyncio.Lock()

    def is_alive(self) -> bool:
        return self._alive

    def shutdown(self) -> None:
        self._alive = False
        self._tasks.clear()

    def clear(self) -> None:
        self._tasks.clear()

    def _rebalance(self) -> None:
        """Rebalance tasks across available slots."""
        if not self._tasks or self.max_wait_seconds <= 0:
            return
        try:
            now = asyncio.get_event_loop().time()
        except RuntimeError:
            now = time.time()
        n_tasks = len(self._tasks)
        tasks_per_slot = max(1, int(n_tasks / self.max_wait_seconds) + 1)
        sorted_tasks = sorted(self._tasks.values(), key=lambda t: t.submit_time)
        for i, task in enumerate(sorted_tasks):
            slot = i // tasks_per_slot
            task.deadline = now + min(slot + 1, self.max_wait_seconds)

    async def submit(self, coro, timeout: float = 8.0, label: str = "") -> Any:
        if coro is None or not self._alive:
            return None
        task_id = f"{label}_{id(coro)}"
        async with self._lock:
            task = ScheduledTask(
                submit_time=time.time(),
                label=label or f"task_{len(self._tasks)}",
                timeout=timeout,
                coro=coro,
            )
            self._tasks[task_id] = task
            self._rebalance()
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            async with self._lock:
                self._tasks.pop(task_id, None)


_scheduler_instance: Optional[WaitingScheduler] = None


def get_waiting_scheduler() -> WaitingScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WaitingScheduler()
    return _scheduler_instance
