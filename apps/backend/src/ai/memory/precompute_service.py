"""
预计算服务
============
在用户空闲时预先生成回應模板，提高对话响应速度。

设计目标：
1. 在后台预计算用户可能的问题
2. 不影响用户交互体验
3. 根据系统资源动态调整预计算策略
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from queue import Queue, Empty
from dataclasses import dataclass

from .memory_template import MemoryTemplate, ResponseCategory, AngelaState, UserImpression

logger = logging.getLogger(__name__)


@dataclass
class PrecomputeTask:
    """
    预计算任务
    """
    query: str
    category: ResponseCategory
    keywords: List[str]
    angela_state: AngelaState
    user_impression: UserImpression
    context: Dict[str, Any]
    priority: int = 1  # 优先级，数字越大优先级越高


class PrecomputeService:
    """
    预计算服务
    ===========
    在后台预先生成回應模板，提高对话响应速度
    """

    def __init__(
        self,
        llm_service,
        memory_manager,
        idle_threshold: float = 5.0,
        cpu_threshold: float = 70.0,
        max_queue_size: int = 50,
        llm_timeout: float = 180.0
    ):
        """
        初始化预计算服务

        Args:
            llm_service: LLM 服务实例
            memory_manager: 记忆管理器实例
            idle_threshold: 空闲时间阈值（秒）
            cpu_threshold: CPU 使用率阈值（%）
            max_queue_size: 任务队列最大长度
            llm_timeout: LLM 调用超时时间（秒）
        """
        self.llm_service = llm_service
        self.memory_manager = memory_manager

        self.idle_threshold = idle_threshold
        self.cpu_threshold = cpu_threshold
        self.max_queue_size = max_queue_size
        self.llm_timeout = llm_timeout

        # 任务队列
        self.task_queue: Queue[PrecomputeTask] = Queue(maxsize=max_queue_size)

        # 状态管理
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None

        # 活动跟踪
        self.last_activity_time: float = time.time()
        self.processed_count = 0
        self.failed_count = 0

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "processed_tasks": 0,
            "failed_tasks": 0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0
        }

    async def start(self):
        """
        启动预计算服务（后台任务）
        """
        if self.is_running:
            logger.warning("Precompute service is already running")
            return

        self.is_running = True
        self.worker_task = asyncio.create_task(self._precompute_loop())
        logger.info("Precompute service started")

    async def stop(self):
        """
        停止预计算服务
        """
        if not self.is_running:
            return

        self.is_running = False

        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        logger.info("Precompute service stopped")

    def record_activity(self):
        """
        记录用户活动
        """
        self.last_activity_time = time.time()

    def add_precompute_task(self, task: PrecomputeTask) -> bool:
        """
        添加预计算任务

        Args:
            task: 预计算任务

        Returns:
            bool: 是否成功添加
        """
        if not self.is_running:
            logger.warning("Precompute service is not running")
            return False

        if self.task_queue.full():
            logger.debug("Precompute task queue is full, dropping task")
            return False

        try:
            self.task_queue.put_nowait(task)
            self.stats["total_tasks"] += 1
            return True
        except Exception as e:
            logger.error(f"Error adding precompute task: {e}")
            return False

    async def _precompute_loop(self):
        """
        预计算循环
        ==========
        1. 检查空闲时间（5秒空闲阈值）
        2. 检查 CPU 使用率（70% 阈值）
        3. 处理任务队列
        """
        while self.is_running:
            try:
                # 检查是否应该开始预计算
                if not self._should_precompute():
                    await asyncio.sleep(1.0)
                    continue

                # 处理下一个任务
                await self._process_next_task()

                # 短暂休息，避免过度占用资源
                await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                logger.info("Precompute loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in precompute loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    def _should_precompute(self) -> bool:
        """
        检查是否应该开始预计算

        Returns:
            bool: 是否应该预计算
        """
        # 1. 检查空闲时间
        idle_time = time.time() - self.last_activity_time
        if idle_time < self.idle_threshold:
            return False

        # 2. 检查 CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > self.cpu_threshold:
            logger.debug(f"CPU usage too high: {cpu_percent}%")
            return False

        # 3. 检查任务队列
        if self.task_queue.empty():
            return False

        return True

    async def _process_next_task(self):
        """
        处理预计算任务
        ==============
        1. 调用 LLM 生成回應（超时 3-5 分钟）
        2. 创建模板
        3. 存储到记忆系统
        """
        try:
            # 从队列获取任务
            task = self.task_queue.get_nowait()

            start_time = time.time()

            # 调用 LLM 生成回應
            response = await self._generate_with_timeout(
                task.query,
                task.context,
                self.llm_timeout
            )

            if response.error:
                logger.warning(f"LLM generation failed: {response.error}")
                self.failed_count += 1
                self.stats["failed_tasks"] += 1
                return

            # 创建模板
            template = MemoryTemplate(
                id="",  # 将在存储时生成
                category=task.category,
                content=response.text,
                keywords=task.keywords,
                angela_state=task.angela_state,
                user_impression=task.user_impression,
                metadata={
                    "precomputed": True,
                    "generated_at": datetime.utcnow().isoformat(),
                    "llm_backend": response.backend,
                    "llm_model": response.model,
                    "response_time_ms": response.response_time_ms
                }
            )

            # 存储到记忆系统
            success = await self.memory_manager.store_template(template)

            if success:
                self.processed_count += 1
                self.stats["processed_tasks"] += 1
                logger.info(f"Precomputed template for query: '{task.query}'")
            else:
                self.failed_count += 1
                self.stats["failed_tasks"] += 1

            # 更新统计信息
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            self.stats["average_processing_time"] = (
                self.stats["total_processing_time"] /
                self.stats["processed_tasks"]
                if self.stats["processed_tasks"] > 0
                else 0.0
            )

        except Empty:
            # 队列为空，正常情况
            pass
        except Exception as e:
            logger.error(f"Error processing precompute task: {e}", exc_info=True)
            self.failed_count += 1
            self.stats["failed_tasks"] += 1

    async def _generate_with_timeout(
        self,
        query: str,
        context: Dict[str, Any],
        timeout: float
    ):
        """
        带超时的 LLM 生成

        Args:
            query: 查询
            context: 上下文
            timeout: 超时时间（秒）

        Returns:
            LLMResponse 对象
        """
        try:
            # 使用 asyncio.wait_for 设置超时
            response = await asyncio.wait_for(
                self.llm_service.generate_response(query, context),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(f"LLM generation timeout after {timeout}s")
            from ..services.angela_llm_service import LLMResponse
            return LLMResponse(
                text="",
                backend="timeout",
                model="",
                error=f"Timeout after {timeout}s"
            )
        except Exception as e:
            logger.error(f"LLM generation error: {e}", exc_info=True)
            from ..services.angela_llm_service import LLMResponse
            return LLMResponse(
                text="",
                backend="error",
                model="",
                error=str(e)
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        idle_time = time.time() - self.last_activity_time
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return {
            **self.stats,
            "is_running": self.is_running,
            "queue_size": self.task_queue.qsize(),
            "idle_time": idle_time,
            "cpu_percent": cpu_percent,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count
        }

    def clear_queue(self):
        """
        清空任务队列
        """
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except Empty:
                break
        logger.info("Precompute task queue cleared")