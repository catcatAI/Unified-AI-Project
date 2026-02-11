#!/usr/bin/env python3
"""
Local Cluster Manager - Simulates distributed cluster on a single machine
使用 multiprocessing 在本地模擬分佈式集群環境
"""

import os
import time
import logging
import multiprocessing as mp
from multiprocessing import Process, Queue, Event
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    """Worker 狀態枚舉"""
    IDLE = "idle"
    BUSY = "busy"
    DEAD = "dead"
    STARTING = "starting"


@dataclass
class WorkerInfo:
    """Worker 進程信息"""
    worker_id: int
    process: Optional[Process]
    status: WorkerStatus
    last_heartbeat: float
    tasks_processed: int = 0


@dataclass
class ClusterTask:
    """集群任務定義"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: int = 0
    timestamp: float = 0.0


class LocalClusterManager:
    """
    本地集群管理器
    在單機上使用 multiprocessing 模擬分佈式 Master-Worker 架構
    """

    def __init__(self, max_workers: Optional[int] = None, 
                 resource_service: Optional[Any] = None):
        """
        初始化本地集群管理器
        
        Args:
            max_workers: 最大 Worker 數量（None 則自動檢測）
            resource_service: ResourceAwarenessService 實例（用於動態調整）
        """
        self.max_workers = max_workers or self._detect_optimal_workers()
        self.resource_service = resource_service
        
        # 進程間通信隊列
        self.task_queue: Queue = mp.Queue()
        self.result_queue: Queue = mp.Queue()
        self.control_queue: Queue = mp.Queue()  # 用於控制指令
        
        # Worker 管理
        self.workers: Dict[int, WorkerInfo] = {}
        self.shutdown_event = mp.Event()
        
        # 統計信息
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        
        logger.info(f"LocalClusterManager initialized with max_workers={self.max_workers}")

    def _detect_optimal_workers(self) -> int:
        """
        根據 CPU 核心數自動檢測最優 Worker 數量
        策略：使用 max(2, cpu_count - 1)，為系統保留至少 1 個核心
        """
        cpu_count = os.cpu_count() or 2
        optimal = max(2, min(cpu_count - 1, 4))  # 最多 4 個 Worker
        logger.info(f"Detected {cpu_count} CPU cores, using {optimal} workers")
        return optimal

    def start(self):
        """啟動集群（同步方法）"""
        logger.info(f"Starting local cluster with {self.max_workers} workers...")
        
        for worker_id in range(self.max_workers):
            self._start_worker(worker_id)
        
        logger.info(f"Local cluster started successfully with {len(self.workers)} workers")

    def _start_worker(self, worker_id: int):
        """啟動單個 Worker 進程"""
        process = Process(
            target=self._worker_loop,
            args=(worker_id, self.task_queue, self.result_queue, 
                  self.control_queue, self.shutdown_event),
            name=f"Worker-{worker_id}"
        )
        process.start()
        
        self.workers[worker_id] = WorkerInfo(
            worker_id=worker_id,
            process=process,
            status=WorkerStatus.STARTING,
            last_heartbeat=time.time()
        )
        
        logger.info(f"Started worker {worker_id} (PID: {process.pid})")

    @staticmethod
    def _worker_loop(worker_id: int, task_queue: Queue, result_queue: Queue,
                     control_queue: Queue, shutdown_event: Event):
        """
        Worker 進程主循環
        在獨立進程中運行，處理任務隊列中的任務
        """
        logger.info(f"[Worker-{worker_id}] Started (PID: {os.getpid()})")
        
        while not shutdown_event.is_set():
            try:
                # 非阻塞檢查控制指令
                try:
                    control_msg = control_queue.get_nowait()
                    if control_msg.get("command") == "shutdown":
                        logger.info(f"[Worker-{worker_id}] Received shutdown command")
                        break
                except (queue.Empty, RuntimeError) as e:
                    # 隊列空或運行時錯誤，繼續運行
                    pass
                
                # 獲取任務（超時 1 秒）
                try:
                    task: ClusterTask = task_queue.get(timeout=1.0)
                except (queue.Empty, RuntimeError):
                    # 隊列為空或運行時錯誤，繼續等待
                    continue
                
                logger.info(f"[Worker-{worker_id}] Processing task {task.task_id}")
                
                # 執行任務（這裡是模擬，實際應調用 Agent）
                result = LocalClusterManager._execute_task(worker_id, task)
                
                # 返回結果
                result_queue.put({
                    "task_id": task.task_id,
                    "worker_id": worker_id,
                    "result": result,
                    "timestamp": time.time()
                })
                
                logger.info(f"[Worker-{worker_id}] Completed task {task.task_id}")
                
            except Exception as e:
                logger.error(f"[Worker-{worker_id}] Error: {e}", exc_info=True)
        
        logger.info(f"[Worker-{worker_id}] Shutting down")

    @staticmethod
    def _execute_task(worker_id: int, task: ClusterTask) -> Dict[str, Any]:
        """
        執行單個任務（在 Worker 進程中調用）
        TODO: 集成真實的 Agent 執行邏輯
        """
        # 模擬任務處理
        time.sleep(0.1)  # 模擬工作負載
        
        return {
            "status": "success",
            "worker_id": worker_id,
            "task_type": task.task_type,
            "processed_at": time.time()
        }

    def submit_task(self, task: ClusterTask):
        """提交任務到集群"""
        if task.timestamp == 0.0:
            task.timestamp = time.time()
        
        self.task_queue.put(task)
        self.total_tasks_submitted += 1
        logger.debug(f"Submitted task {task.task_id} to cluster")

    def get_result(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """獲取一個任務結果（非阻塞）"""
        try:
            result = self.result_queue.get(timeout=timeout)
            self.total_tasks_completed += 1
            return result
        except (queue.Empty, RuntimeError):
            # 隊列為空或運行時錯誤，返回None
            return None

    def get_cluster_status(self) -> Dict[str, Any]:
        """獲取集群狀態"""
        alive_workers = sum(1 for w in self.workers.values() 
                           if w.process and w.process.is_alive())
        
        return {
            "total_workers": len(self.workers),
            "alive_workers": alive_workers,
            "tasks_submitted": self.total_tasks_submitted,
            "tasks_completed": self.total_tasks_completed,
            "tasks_pending": self.task_queue.qsize(),
            "results_pending": self.result_queue.qsize()
        }

    def shutdown(self):
        """關閉集群"""
        logger.info("Shutting down local cluster...")
        
        # 發送關閉信號
        self.shutdown_event.set()
        
        # 向所有 Worker 發送關閉指令
        for _ in range(len(self.workers)):
            self.control_queue.put({"command": "shutdown"})
        
        # 等待所有 Worker 進程結束
        for worker_info in self.workers.values():
            if worker_info.process:
                worker_info.process.join(timeout=5.0)
                if worker_info.process.is_alive():
                    logger.warning(f"Force terminating worker {worker_info.worker_id}")
                    worker_info.process.terminate()
        
        logger.info("Local cluster shutdown complete")

    def __enter__(self):
        """支持 with 語句"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 語句"""
        self.shutdown()


# 測試代碼
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== Local Cluster Manager Test ===\n")
    
    # 使用 with 語句自動管理生命週期
    with LocalClusterManager(max_workers=2) as cluster:
        print(f"Cluster started: {cluster.get_cluster_status()}\n")
        
        # 提交測試任務
        for i in range(5):
            task = ClusterTask(
                task_id=f"test_task_{i}",
                task_type="test",
                payload={"data": f"test_{i}"}
            )
            cluster.submit_task(task)
        
        print(f"Submitted 5 tasks: {cluster.get_cluster_status()}\n")
        
        # 收集結果
        results = []
        for _ in range(5):
            result = cluster.get_result(timeout=5.0)
            if result:
                results.append(result)
                print(f"Got result: {result['task_id']}")
        
        print(f"\nFinal status: {cluster.get_cluster_status()}")
        print(f"Collected {len(results)} results")
    
    print("\n=== Test Complete ===")
