#!/usr/bin/env python3
"""
from __future__ import annotations
Local Cluster Manager - Simulates distributed cluster on a single machine
使用 multiprocessing 在本地模擬分佈式集群環境
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalClusterManager:
    """Simulates a distributed cluster on a single machine."""

    def __init__(self, num_workers: int = 4, config: Optional[Dict[str, Any]] = None):
        self.num_workers = num_workers
        self.config = config or {}
        self._workers: List[Dict[str, Any]] = []
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._workers = [{"id": i, "status": "idle"} for i in range(self.num_workers)]
        logger.info(f"LocalClusterManager started with {self.num_workers} workers")

    async def stop(self) -> None:
        self._running = False
        self._workers.clear()
        logger.info("LocalClusterManager stopped")

    def submit(self, task: Callable, *args, **kwargs) -> Dict[str, Any]:
        worker_id = hash(task) % self.num_workers
        return {"worker_id": worker_id, "task": str(task), "status": "submitted"}

    def get_worker_status(self) -> List[Dict[str, Any]]:
        return list(self._workers)

    def is_running(self) -> bool:
        return self._running


__all__ = ["LocalClusterManager"]
