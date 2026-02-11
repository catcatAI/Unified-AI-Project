"""
分布式协调器
管理Level 5 ASI的混合分布式计算架构

Angela Matrix: α=0.92 β=0.88 γ=0.85 δ=0.95 | L5-ASI | V=4.2 L=3 P=5 M=6
"""

import asyncio
import logging
import json
import uuid
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ComputeNodeType(Enum):
    """计算节点类型"""
    LOCAL = "local"           # 本地计算节点
    SERVER = "server"         # 服务器节点
    DISTRIBUTED = "distributed"  # 分布式节点
    CLOUD = "cloud"          # 云端节点


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ComputeTask:
    """计算任务数据结构"""
    task_id: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    node_type_preference: Optional[ComputeNodeType] = None
    estimated_resources: Optional[Dict[str, float]] = None
    created_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_node_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ComputeNode:
    """计算节点数据结构"""
    node_id: str
    node_type: ComputeNodeType
    address: str
    port: int
    available_resources: Dict[str, float]
    current_load: float = 0.0
    is_active: bool = True
    last_heartbeat: Optional[datetime] = None
    capabilities: Optional[List[str]] = None


class DistributedCoordinator:
    """
    分布式协调器

    负责：
    - 管理本地计算池
    - 协调服务器桥接
    - 分发分布式计算任务
    - 动态负载均衡
    - 故障恢复
    """

    def __init__(self, coordinator_id: str = "distributed_coordinator"):
        self.coordinator_id = coordinator_id

        # 计算节点管理
        self.compute_nodes: Dict[str, ComputeNode] = {}
        self.node_status_monitor = None

        # 任务管理
        self.pending_tasks: List[ComputeTask] = []
        self.running_tasks: Dict[str, ComputeTask] = {}
        self.completed_tasks: Dict[str, ComputeTask] = {}

        # 组件管理
        self.local_pool_manager = None
        self.server_bridge = None

        # 配置
        self.max_concurrent_tasks = 100
        self.load_balancing_strategy = "round_robin"
        self.heartbeat_interval = 30.0
        self.task_timeout = 300.0  # 5分钟

        # 统计信息
        self.statistics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_completion_time": 0.0,
            "node_utilization": {}
        }

        self._running = False
        self._monitor_task = None

    async def initialize(self):
        """初始化分布式协调器"""
        try:
            from .local_pool_manager import LocalPoolManager
            from .server_bridge import ServerBridge

            # 初始化本地池管理器
            self.local_pool_manager = LocalPoolManager(
                coordinator_id=f"{self.coordinator_id}_local_pool"
            )
            await self.local_pool_manager.initialize()

            # 初始化服务器桥接
            self.server_bridge = ServerBridge(
                coordinator_id=f"{self.coordinator_id}_server_bridge"
            )
            await self.server_bridge.initialize()

            # 注册本地计算节点
            await self._register_local_nodes()

            # 启动监控任务
            self._running = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())

            logger.info(f"[{self.coordinator_id}] 分布式协调器初始化完成")

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 初始化失败: {e}")
            raise

    async def shutdown(self):
        """关闭分布式协调器"""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self.local_pool_manager:
            await self.local_pool_manager.shutdown()

        if self.server_bridge:
            await self.server_bridge.shutdown()

        logger.info(f"[{self.coordinator_id}] 分布式协调器已关闭")

    async def submit_task(self, task: ComputeTask) -> str:
        """提交计算任务"""
        try:
            # 设置任务ID和创建时间
            if not task.task_id:
                task.task_id = str(uuid.uuid4())

            task.created_at = datetime.now()
            task.status = TaskStatus.PENDING

            # 添加到待处理队列
            self.pending_tasks.append(task)
            self.statistics["total_tasks"] += 1

            logger.info(f"[{self.coordinator_id}] 任务已提交: {task.task_id}")

            # 尝试立即分配任务
            await self._assign_pending_tasks()

            return task.task_id
        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 任务提交失败: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            return asdict(self.running_tasks[task_id])

        # 检查已完成的任务
        if task_id in self.completed_tasks:
            return asdict(self.completed_tasks[task_id])

        # 检查待处理的任务
        for task in self.pending_tasks:
            if task.task_id == task_id:
                return asdict(task)

        return None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            # 检查待处理的任务
            for i, task in enumerate(self.pending_tasks):
                if task.task_id == task_id:
                    task.status = TaskStatus.CANCELLED
                    self.pending_tasks.pop(i)
                    logger.info(f"[{self.coordinator_id}] 已取消待处理任务: {task_id}")
                    return True

            # 检查运行中的任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                # 通知节点取消任务
                if task.assigned_node_id:
                    await self._cancel_task_on_node(task.assigned_node_id, task_id)

                del self.running_tasks[task_id]
                logger.info(f"[{self.coordinator_id}] 已取消运行中任务: {task_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 取消任务失败: {e}")
            return False

    async def register_compute_node(self, node: ComputeNode) -> bool:
        """注册计算节点"""
        try:
            node.last_heartbeat = datetime.now()
            self.compute_nodes[node.node_id] = node

            logger.info(f"[{self.coordinator_id}] 计算节点已注册: {node.node_id} ({node.node_type.value})")

            # 尝试分配待处理任务
            await self._assign_pending_tasks()

            return True

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 节点注册失败: {e}")
            return False

    async def unregister_compute_node(self, node_id: str) -> bool:
        """注销计算节点"""
        try:
            if node_id in self.compute_nodes:
                node = self.compute_nodes[node_id]

                # 重新分配该节点上的任务
                await self._reassign_node_tasks(node_id)

                del self.compute_nodes[node_id]
                logger.info(f"[{self.coordinator_id}] 计算节点已注销: {node_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 节点注销失败: {e}")
            return False

    async def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        active_nodes = sum(1 for node in self.compute_nodes.values() if node.is_active)
        total_resources = {}

        for node in self.compute_nodes.values():
            if node.is_active:
                for resource, amount in node.available_resources.items():
                    total_resources[resource] = total_resources.get(resource, 0) + amount

        return {
            "coordinator_id": self.coordinator_id,
            "active_nodes": active_nodes,
            "total_nodes": len(self.compute_nodes),
            "pending_tasks": len(self.pending_tasks),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "total_resources": total_resources,
            "statistics": self.statistics
        }

    async def _register_local_nodes(self):
        """注册本地计算节点"""
        if not self.local_pool_manager:
            return

        # 获取本地计算节点信息
        local_nodes = await self.local_pool_manager.get_compute_nodes()

        for node_info in local_nodes:
            node = ComputeNode(
                node_id=node_info["node_id"],
                node_type=ComputeNodeType.LOCAL,
                address=node_info["address"],
                port=node_info["port"],
                available_resources=node_info["resources"],
                capabilities=node_info.get("capabilities", [])
            )

            await self.register_compute_node(node)

    async def _assign_pending_tasks(self):
        """分配待处理任务"""
        if not self.pending_tasks:
            return

        # 按优先级排序
        self.pending_tasks.sort(key=lambda t: t.priority, reverse=True)

        # 尝试分配任务
        tasks_to_remove = []

        for i, task in enumerate(self.pending_tasks):
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                break

            # 找到合适的节点
            suitable_node = await self._find_suitable_node(task)

            if suitable_node:
                # 分配任务到节点
                success = await self._assign_task_to_node(task, suitable_node)

                if success:
                    tasks_to_remove.append(i)
                    self.running_tasks[task.task_id] = task
                    logger.info(f"[{self.coordinator_id}] 任务 {task.task_id} 已分配到节点 {suitable_node}")

        # 从待处理队列中移除已分配的任务
        for i in reversed(tasks_to_remove):
            self.pending_tasks.pop(i)

    async def _find_suitable_node(self, task: ComputeTask) -> Optional[str]:
        """找到适合执行任务的节点"""
        suitable_nodes = []

        for node_id, node in self.compute_nodes.items():
            if not node.is_active:
                continue

            # 检查节点类型偏好
            if task.node_type_preference and node.node_type != task.node_type_preference:
                continue

            # 检查资源可用性
            if task.estimated_resources:
                can_handle = True
                for resource, required_amount in task.estimated_resources.items():
                    available = node.available_resources.get(resource, 0)
                    if available < required_amount:
                        can_handle = False
                        break

                if not can_handle:
                    continue

            # 检查负载
            if node.current_load >= 0.9:  # 90%负载阈值
                continue

            suitable_nodes.append((node_id, node.current_load))

        if not suitable_nodes:
            return None

        # 根据负载均衡策略选择节点
        if self.load_balancing_strategy == "round_robin":
            return suitable_nodes[0][0]
        elif self.load_balancing_strategy == "least_loaded":
            return min(suitable_nodes, key=lambda x: x[1])[0]
        else:
            return suitable_nodes[0][0]

    async def _assign_task_to_node(self, task: ComputeTask, node_id: str) -> bool:
        """将任务分配到指定节点"""
        try:
            node = self.compute_nodes[node_id]

            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.assigned_node_id = node_id

            # 更新节点负载
            node.current_load += 0.1  # 简化的负载计算

            # 根据节点类型执行任务
            if node.node_type == ComputeNodeType.LOCAL:
                success = await self.local_pool_manager.execute_task(task)
            elif node.node_type == ComputeNodeType.SERVER:
                success = await self.server_bridge.execute_task(task, node)
            else:
                # 分布式节点处理
                success = await self._execute_distributed_task(task, node)

            if success:
                # 启动任务监控
                asyncio.create_task(self._monitor_task(task, node_id))
                return True
            else:
                # 分配失败，回滚状态
                task.status = TaskStatus.PENDING
                task.assigned_node_id = None
                node.current_load -= 0.1
                return False

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 任务分配失败: {e}")
            return False

    async def _monitor_task(self, task: ComputeTask, node_id: str):
        """监控任务执行"""
        try:
            start_time = asyncio.get_event_loop().time()

            # 等待任务完成或超时
            timeout = self.task_timeout
            while task.status == TaskStatus.RUNNING:
                await asyncio.sleep(1.0)

                # 检查超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    await self._handle_task_timeout(task, node_id)
                    break

                # 检查节点状态
                if node_id not in self.compute_nodes or not self.compute_nodes[node_id].is_active:
                    await self._handle_node_failure(task, node_id)
                    break

            # 任务完成处理
            if task.status == TaskStatus.COMPLETED:
                await self._handle_task_completion(task, node_id)
            elif task.status == TaskStatus.FAILED:
                await self._handle_task_failure(task, node_id)

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 任务监控失败: {e}")

    async def _handle_task_completion(self, task: ComputeTask, node_id: str):
        """处理任务完成"""
        try:
            # 从运行任务列表移除
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # 添加到完成列表
            self.completed_tasks[task.task_id] = task

            # 更新节点负载
            if node_id in self.compute_nodes:
                self.compute_nodes[node_id].current_load -= 0.1

            # 更新统计信息
            self.statistics["completed_tasks"] += 1

            logger.info(f"[{self.coordinator_id}] 任务 {task.task_id} 已完成")

            # 尝试分配新任务
            await self._assign_pending_tasks()

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 任务完成处理失败: {e}")

    async def _handle_task_failure(self, task: ComputeTask, node_id: str):
        """处理任务失败"""
        try:
            # 从运行任务列表移除
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # 添加到完成列表(失败状态)
            self.completed_tasks[task.task_id] = task

            # 更新节点负载
            if node_id in self.compute_nodes:
                self.compute_nodes[node_id].current_load -= 0.1

            # 更新统计信息
            self.statistics["failed_tasks"] += 1

            logger.error(f"[{self.coordinator_id}] 任务 {task.task_id} 失败: {task.error_message}")

            # 尝试分配新任务
            await self._assign_pending_tasks()

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 任务失败处理失败: {e}")

    async def _handle_task_timeout(self, task: ComputeTask, node_id: str):
        """处理任务超时"""
        task.status = TaskStatus.FAILED
        task.error_message = "任务执行超时"
        await self._handle_task_failure(task, node_id)

    async def _handle_node_failure(self, task: ComputeTask, node_id: str):
        """处理节点故障"""
        task.status = TaskStatus.FAILED
        task.error_message = f"计算节点 {node_id} 故障"
        await self._handle_task_failure(task, node_id)

    async def _reassign_node_tasks(self, node_id: str):
        """重新分配节点上的任务"""
        # 找到该节点上的所有任务
        node_tasks = [
            task for task in self.running_tasks.values()
            if task.assigned_node_id == node_id
        ]

        # 将任务重新加入待处理队列
        for task in node_tasks:
            task.status = TaskStatus.PENDING
            task.assigned_node_id = None
            self.pending_tasks.append(task)

            # 从运行任务列表移除
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

        logger.info(f"[{self.coordinator_id}] 已重新分配节点 {node_id} 上的 {len(node_tasks)} 个任务")

    async def _cancel_task_on_node(self, node_id: str, task_id: str):
        """在节点上取消任务"""
        try:
            node = self.compute_nodes.get(node_id)
            if not node:
                return

            # 根据节点类型取消任务
            if node.node_type == ComputeNodeType.LOCAL:
                await self.local_pool_manager.cancel_task(task_id)
            elif node.node_type == ComputeNodeType.SERVER:
                await self.server_bridge.cancel_task(task_id, node)

        except Exception as e:
            logger.error(f"[{self.coordinator_id}] 节点任务取消失败: {e}")

    async def _execute_distributed_task(self, task: ComputeTask, node: ComputeNode) -> bool:
        """在分布式节点上执行任务"""
        # 这里应该实现分布式节点通信逻辑
        # 为了示例，我们模拟执行
        await asyncio.sleep(1.0)

        task.status = TaskStatus.COMPLETED
        task.result = {"message": f"任务 {task.task_id} 在分布式节点 {node.node_id} 上完成"}

        return True

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 检查节点心跳
                await self._check_node_heartbeats()

                # 分配待处理任务
                await self._assign_pending_tasks()

                # 清理旧的任务记录
                await self._cleanup_old_tasks()

                # 更新统计信息
                await self._update_statistics()

                await asyncio.sleep(5.0)  # 5秒监控间隔

            except Exception as e:
                logger.error(f"[{self.coordinator_id}] 监控循环错误: {e}")
                await asyncio.sleep(10.0)

    async def _check_node_heartbeats(self):
        """检查节点心跳"""
        current_time = datetime.now()

        for node_id, node in list(self.compute_nodes.items()):
            if not node.last_heartbeat:
                continue

            # 检查是否超时
            time_diff = (current_time - node.last_heartbeat).total_seconds()
            if time_diff > self.heartbeat_interval * 2:
                logger.warning(f"[{self.coordinator_id}] 节点 {node_id} 心跳超时，标记为非活跃")
                node.is_active = False

                # 重新分配该节点上的任务
                await self._reassign_node_tasks(node_id)

    async def _cleanup_old_tasks(self):
        """清理旧的任务记录"""
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - 3600  # 1小时前

        tasks_to_remove = []

        for task_id, task in self.completed_tasks.items():
            if task.created_at and task.created_at.timestamp() < cutoff_time:
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.completed_tasks[task_id]

        if tasks_to_remove:
            logger.info(f"[{self.coordinator_id}] 清理了 {len(tasks_to_remove)} 个旧任务记录")

    async def _update_statistics(self):
        """更新统计信息"""
        # 计算平均完成时间
        if self.completed_tasks:
            completion_times = []
            for task in self.completed_tasks.values():
                if task.created_at and task.status == TaskStatus.COMPLETED:
                    # 这里应该记录任务完成时间，简化处理
                    completion_times.append(60.0)  # 假设平均60秒

            if completion_times:
                self.statistics["average_completion_time"] = sum(completion_times) / len(completion_times)

        # 更新节点利用率
        for node_id, node in self.compute_nodes.items():
            self.statistics["node_utilization"][node_id] = node.current_load


if __name__ == "__main__":
    # 基本测试/示例实例化
    async def main():
        coordinator = DistributedCoordinator()
        print(f"分布式协调器已创建: {coordinator.coordinator_id}")
        print(f"初始状态: {coordinator.get_cluster_status()}")

    asyncio.run(main())