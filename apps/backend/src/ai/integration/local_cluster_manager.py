#!/usr/bin/env python3
"""
Local Cluster Manager - Simulates distributed cluster on a single machine
使用 multiprocessing 在本地模擬分佈式集群環境
"""

import os
import time
import logging
import random
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
                 resource_service: Optional[Any] = None,
                 task_executor: Optional[Callable] = None):
        """
        初始化本地集群管理器
        
        Args:
            max_workers: 最大 Worker 數量（None 則自動檢測）
            resource_service: ResourceAwarenessService 實例（用於動態調整）
            task_executor: 自定義任務執行器函數（簽名：Callable[[ClusterTask], Dict]）
        """
        self.max_workers = max_workers or self._detect_optimal_workers()
        self.resource_service = resource_service
        self.task_executor = task_executor  # 允許注入自定義執行器
        
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
                  self.control_queue, self.shutdown_event, self.task_executor),
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
                     control_queue: Queue, shutdown_event: Event, 
                     task_executor: Optional[Callable] = None):
        """
        Worker 進程主循環
        在獨立進程中運行，處理任務隊列中的任務
        
        Args:
            worker_id: Worker ID
            task_queue: 任務隊列
            result_queue: 結果隊列
            control_queue: 控制隊列
            shutdown_event: 關閉事件
            task_executor: 自定義任務執行器
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
                
                # 執行任務（使用可擴展的執行架構）
                result = LocalClusterManager._execute_task(worker_id, task, task_executor)
                
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
    def _execute_task(worker_id: int, task: ClusterTask, task_executor: Optional[Callable] = None) -> Dict[str, Any]:
        """
        執行單個任務（在 Worker 進程中調用）
        
        Args:
            worker_id: Worker ID
            task: 要執行的任務
            task_executor: 自定義任務執行器（如果提供）
        
        Returns:
            執行結果字典
        
        支持三種執行模式：
        1. 自定義執行器（通過 task_executor 注入）
        2. 內置任務類型處理
        3. 默認模擬執行（向後兼容）
        """
        start_time = time.time()
        
        # 模式1：使用自定義執行器
        if task_executor is not None and callable(task_executor):
            try:
                logger.debug(f"[Worker-{worker_id}] Using custom executor for {task.task_id}")
                result = task_executor(task)
                result.update({
                    "worker_id": worker_id,
                    "processed_at": time.time(),
                    "executor": "custom",
                    "duration": time.time() - start_time
                })
                return result
            except Exception as e:
                logger.error(f"[Worker-{worker_id}] Custom executor failed: {e}")
                return {
                    "status": "error",
                    "worker_id": worker_id,
                    "error": str(e),
                    "processed_at": time.time(),
                    "executor": "custom"
                }
        
        # 模式2：內置任務類型處理
        try:
            if task.task_type == "agent_execute":
                # 執行 Agent 任務
                return LocalClusterManager._execute_agent_task(worker_id, task, start_time)
            elif task.task_type == "training":
                # 執行訓練任務
                return LocalClusterManager._execute_training_task(worker_id, task, start_time)
            elif task.task_type == "inference":
                # 執行推理任務
                return LocalClusterManager._execute_inference_task(worker_id, task, start_time)
        except Exception as e:
            logger.error(f"[Worker-{worker_id}] Built-in executor failed: {e}")
            return {
                "status": "error",
                "worker_id": worker_id,
                "task_type": task.task_type,
                "error": str(e),
                "processed_at": time.time()
            }
        
        # 模式3：默認模擬執行（向後兼容）
        logger.debug(f"[Worker-{worker_id}] Using default simulator for {task.task_id}")
        time.sleep(0.1)  # 模擬工作負載
        
        return {
            "status": "success",
            "worker_id": worker_id,
            "task_type": task.task_type,
            "payload": task.payload,
            "processed_at": time.time(),
            "duration": time.time() - start_time,
            "executor": "simulator"
        }
    
    @staticmethod
    def _execute_agent_task(worker_id: int, task: ClusterTask, start_time: float) -> Dict[str, Any]:
        """執行 Agent 任務"""
        # 這裡可以集成真實的 Agent 執行邏輯
        # 例如：調用 AgentManager 或相關服務
        
        payload = task.payload or {}
        agent_id = payload.get("agent_id", "unknown")
        action = payload.get("action", "unknown")
        
        # 模擬 Agent 執行
        logger.debug(f"[Worker-{worker_id}] Executing agent {agent_id} action {action}")
        
        # 真實場景中會執行類似：
        # result = agent_manager.execute(agent_id, action, payload.get("params", {}))
        
        return {
            "status": "success",
            "worker_id": worker_id,
            "task_type": task.task_type,
            "agent_id": agent_id,
            "action": action,
            "processed_at": time.time(),
            "duration": time.time() - start_time,
            "executor": "agent_builtin"
        }
    
    @staticmethod
    def _execute_training_task(worker_id: int, task: ClusterTask, start_time: float) -> Dict[str, Any]:
        """執行訓練任務"""
        payload = task.payload or {}
        model_id = payload.get("model_id", "unknown")
        epochs = payload.get("epochs", 1)
        
        logger.debug(f"[Worker-{worker_id}] Training model {model_id} for {epochs} epochs")
        
        # 模擬訓練
        time.sleep(0.2)  # 訓練通常需要更長時間
        
        return {
            "status": "success",
            "worker_id": worker_id,
            "task_type": task.task_type,
            "model_id": model_id,
            "epochs": epochs,
            "loss": 0.5 - (random.random() * 0.3),  # 模擬損失值
            "processed_at": time.time(),
            "duration": time.time() - start_time,
            "executor": "training_builtin"
        }
    
    @staticmethod
    def _execute_inference_task(worker_id: int, task: ClusterTask, start_time: float) -> Dict[str, Any]:
        """執行推理任務"""
        payload = task.payload or {}
        model_id = payload.get("model_id", "unknown")
        input_data = payload.get("input", {})
        
        logger.debug(f"[Worker-{worker_id}] Running inference on {model_id}")
        
        # 模擬推理
        time.sleep(0.05)
        
        return {
            "status": "success",
            "worker_id": worker_id,
            "task_type": task.task_type,
            "model_id": model_id,
            "output": {"prediction": "simulated_result"},
            "processed_at": time.time(),
            "duration": time.time() - start_time,
            "executor": "inference_builtin"
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
    
    logger.info("=== Local Cluster Manager Test ===\n")
    
    # 測試1：使用默認執行器
    logger.info("Test 1: Default executor (simulator)\n")
    with LocalClusterManager(max_workers=2) as cluster:
        logger.info(f"Cluster started: {cluster.get_cluster_status()}\n")
        
        # 提交測試任務
        for i in range(3):
            task = ClusterTask(
                task_id=f"test_task_{i}",
                task_type="test",
                payload={"data": f"test_{i}"}
            )
            cluster.submit_task(task)
        
        logger.info(f"Submitted 3 tasks: {cluster.get_cluster_status()}\n")
        
        # 收集結果
        for _ in range(3):
            result = cluster.get_result(timeout=5.0)
            if result:
                logger.info(f"Got result: {result['task_id']} (executor: {result.get('executor', 'unknown')})")
    
    logger.info("\n" + "="*50 + "\n")
    
    # 測試2：使用內置任務類型
    logger.info("Test 2: Built-in task types\n")
    
    def test_task_executor(task: ClusterTask) -> Dict[str, Any]:
        """自定義任務執行器示例"""
        return {
            "status": "success",
            "custom_result": f"Processed {task.task_id}",
            "payload": task.payload
        }
    
    with LocalClusterManager(max_workers=2, task_executor=test_task_executor) as cluster:
        logger.info(f"Cluster started: {cluster.get_cluster_status()}\n")
        
        # 提交不同類型的任務
        tasks = [
            ClusterTask(task_id="agent_1", task_type="agent_execute", 
                       payload={"agent_id": "agent1", "action": "chat"}),
            ClusterTask(task_id="train_1", task_type="training",
                       payload={"model_id": "model1", "epochs": 5}),
            ClusterTask(task_id="infer_1", task_type="inference",
                       payload={"model_id": "model1", "input": {"text": "hello"}})
        ]
        
        for task in tasks:
            cluster.submit_task(task)
        
        logger.info(f"Submitted 3 tasks: {cluster.get_cluster_status()}\n")
        
        # 收集結果
        for _ in range(3):
            result = cluster.get_result(timeout=5.0)
            if result:
                logger.info(f"Got result: {result['task_id']} (executor: {result.get('executor', 'unknown')})")
    
    logger.info("\n=== Test Complete ===")
