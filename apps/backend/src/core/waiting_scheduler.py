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
from typing import Any, Coroutine, Dict, List, Optional