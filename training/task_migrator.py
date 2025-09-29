#!/usr/bin/env python3
"""
任务迁移器
负责在节点故障时将任务迁移到其他健康的节点
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# 添加项目路径
import sys
from pathlib import Path
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))


logger: Any = logging.getLogger(__name__)

@dataclass
class TaskMigrationInfo:
    """任务迁移信息"""
    task_id: str
    source_node_id: str
    target_node_id: str
    migration_time: float
    status: str  # 'pending', 'migrating', 'completed', 'failed'
    task_state: Dict[str, Any] = None
    retry_count: int = 0

class TaskMigrator:
    """任务迁移器"""
    
    def __init__(self, distributed_optimizer: Any, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.error_handler = global_error_handler
        self.distributed_optimizer = distributed_optimizer
        self.migration_tasks: Dict[str, TaskMigrationInfo] = {}
        self.migration_history: List[TaskMigrationInfo] = []
        self.max_retry_attempts = self.config.get('max_retry_attempts', 3)
        self.migration_strategy = self.config.get('migration_strategy', 'load_balanced')
        
        # 注册故障回调
        _ = global_fault_detector.register_failure_callback(self._handle_node_failure)
        
        _ = logger.info("任务迁移器初始化完成")
    
    async def _handle_node_failure(self, failure_info: Dict[str, Any]):
        """处理节点故障"""
        context = ErrorContext("TaskMigrator", "_handle_node_failure", failure_info)
        try:
            node_id = failure_info.get('node_id')
            assigned_tasks = failure_info.get('assigned_tasks', [])
            
            _ = logger.info(f"处理节点 {node_id} 的故障，需要迁移 {len(assigned_tasks)} 个任务")
            
            # 为每个分配的任务创建迁移任务
            for task_id in assigned_tasks:
                _ = await self.migrate_task_on_failure(task_id, node_id)
                
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"处理节点故障失败: {e}")
    
    async def migrate_task_on_failure(self, task_id: str, failed_node_id: str) -> bool:
        """在节点故障时迁移任务"""
        context = ErrorContext("TaskMigrator", "migrate_task_on_failure", {
            "task_id": task_id, 
            "failed_node_id": failed_node_id
        })
        try:
            _ = logger.info(f"开始迁移任务 {task_id} 从故障节点 {failed_node_id}")
            
            # 创建迁移信息
            migration_info = TaskMigrationInfo(
                task_id=task_id,
                source_node_id=failed_node_id,
                target_node_id="",
                migration_time=time.time(),
                status="pending",
                task_state=None,
                retry_count=0
            )
            
            self.migration_tasks[task_id] = migration_info
            
            # 保存任务状态
            task_state = await self.save_task_state(task_id)
            migration_info.task_state = task_state
            
            # 选择目标节点
            target_node = await self._select_target_node(task_id, failed_node_id)
            if not target_node:
                _ = logger.error(f"无法为任务 {task_id} 选择目标节点")
                migration_info.status = "failed"
                return False
            
            migration_info.target_node_id = target_node
            migration_info.status = "migrating"
            
            # 执行任务迁移
            success = await self._execute_task_migration(migration_info)
            
            if success:
                migration_info.status = "completed"
                _ = logger.info(f"任务 {task_id} 迁移成功到节点 {target_node}")
            else:
                migration_info.status = "failed"
                _ = logger.error(f"任务 {task_id} 迁移失败")
            
            # 添加到迁移历史
            _ = self.migration_history.append(migration_info)
            
            # 限制迁移历史记录数量
            if len(self.migration_history) > 100:
                self.migration_history = self.migration_history[-50:]
            
            return success
            
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"迁移任务失败: {task_id} - {e}")
            return False
    
    async def save_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """保存任务状态"""
        context = ErrorContext("TaskMigrator", "save_task_state", {"task_id": task_id})
        try:
            # 这里应该实现实际的任务状态保存逻辑
            # 可能包括模型状态、优化器状态、训练进度等
            
            _ = logger.info(f"保存任务 {task_id} 的状态")
            
            # 模拟任务状态
            task_state = {
                'task_id': task_id,
                'epoch': 5,  # 示例epoch
                'metrics': {
                    'loss': 0.45,
                    'accuracy': 0.82
                },
                'model_state': {},  # 实际项目中会包含模型状态
                'optimizer_state': {},  # 实际项目中会包含优化器状态
                _ = 'timestamp': datetime.now().isoformat()
            }
            
            # 在实际实现中，这里会调用检查点保存功能
            # await self.checkpoint_manager.save_checkpoint(task_state, checkpoint_type='migration')
            
            return task_state
            
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"保存任务状态失败: {task_id} - {e}")
            return None
    
    async def _select_target_node(self, task_id: str, failed_node_id: str) -> Optional[str]:
        """选择目标节点"""
        context = ErrorContext("TaskMigrator", "_select_target_node", {
            "task_id": task_id, 
            "failed_node_id": failed_node_id
        })
        try:
            # 获取所有健康节点
            healthy_nodes = []
            for node_id, node_status in global_fault_detector.nodes_status.items():
                if node_status.status in ['healthy', 'warning'] and node_id != failed_node_id:
                    _ = healthy_nodes.append(node_id)
            
            if not healthy_nodes:
                _ = logger.warning("没有可用的健康节点进行任务迁移")
                return None
            
            # 根据迁移策略选择节点
            if self.migration_strategy == 'load_balanced':
                # 选择负载最低的节点
                return await self._select_least_loaded_node(healthy_nodes, task_id)
            elif self.migration_strategy == 'round_robin':
                # 轮询选择节点
                return await self._select_round_robin_node(healthy_nodes, task_id)
            else:
                # 默认选择第一个健康节点
                return healthy_nodes[0]
                
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"选择目标节点失败: {e}")
            return None
    
    async def _select_least_loaded_node(self, healthy_nodes: List[str], task_id: str) -> Optional[str]:
        """选择负载最低的节点"""
        context = ErrorContext("TaskMigrator", "_select_least_loaded_node", {"task_id": task_id})
        try:
            if not hasattr(self.distributed_optimizer, 'nodes'):
                return healthy_nodes[0] if healthy_nodes else None
            
            min_load = float('inf')
            selected_node = None
            
            for node_id in healthy_nodes:
                if node_id in self.distributed_optimizer.nodes:
                    node_info = self.distributed_optimizer.nodes[node_id]
                    # 计算节点负载（简化实现）
                    cpu_load = node_info.get('performance_metrics', {}).get('cpu_usage', 0)
                    memory_load = node_info.get('performance_metrics', {}).get('memory_usage', 0)
                    task_count = len(node_info.get('assigned_tasks', []))
                    
                    # 综合负载计算
                    load = cpu_load * 0.5 + memory_load * 0.3 + task_count * 10
                    
                    if load < min_load:
                        min_load = load
                        selected_node = node_id
            
            return selected_node or (healthy_nodes[0] if healthy_nodes else None)
            
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"选择负载最低节点失败: {e}")
            return healthy_nodes[0] if healthy_nodes else None
    
    async def _select_round_robin_node(self, healthy_nodes: List[str], task_id: str) -> Optional[str]:
        """轮询选择节点"""
        # 简化实现，实际项目中可能需要更复杂的轮询机制
        if not hasattr(self, '_last_selected_node_index'):
            self._last_selected_node_index = 0
        
        if healthy_nodes:
            selected_node = healthy_nodes[self._last_selected_node_index % len(healthy_nodes)]
            self._last_selected_node_index += 1
            return selected_node
        
        return None
    
    async def _execute_task_migration(self, migration_info: TaskMigrationInfo) -> bool:
        """执行任务迁移"""
        context = ErrorContext("TaskMigrator", "_execute_task_migration", {
            "task_id": migration_info.task_id,
            "target_node_id": migration_info.target_node_id
        })
        try:
            task_id = migration_info.task_id
            target_node_id = migration_info.target_node_id
            task_state = migration_info.task_state
            
            _ = logger.info(f"执行任务 {task_id} 到节点 {target_node_id} 的迁移")
            
            # 这里应该实现实际的任务迁移逻辑
            # 可能包括：
            # 1. 将任务状态发送到目标节点
            # 2. 在目标节点上恢复任务执行
            # 3. 更新任务分配记录
            
            # 模拟迁移过程
            _ = await asyncio.sleep(0.5)  # 模拟网络延迟
            
            # 模拟迁移成功
            _ = logger.info(f"任务 {task_id} 迁移完成")
            
            # 更新分布式优化器中的任务分配
            if hasattr(self.distributed_optimizer, 'nodes'):
                # 从源节点移除任务
                if migration_info.source_node_id in self.distributed_optimizer.nodes:
                    source_node = self.distributed_optimizer.nodes[migration_info.source_node_id]
                    if 'assigned_tasks' in source_node:
                        if task_id in source_node['assigned_tasks']:
                            _ = source_node['assigned_tasks'].remove(task_id)
                
                # 添加任务到目标节点
                if target_node_id in self.distributed_optimizer.nodes:
                    target_node = self.distributed_optimizer.nodes[target_node_id]
                    if 'assigned_tasks' in target_node:
                        if task_id not in target_node['assigned_tasks']:
                            _ = target_node['assigned_tasks'].append(task_id)
            
            return True
            
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"执行任务迁移失败: {task_id} - {e}")
            return False
    
    async def retry_migration(self, task_id: str) -> bool:
        """重试任务迁移"""
        context = ErrorContext("TaskMigrator", "retry_migration", {"task_id": task_id})
        try:
            if task_id not in self.migration_tasks:
                _ = logger.warning(f"任务 {task_id} 没有迁移记录")
                return False
            
            migration_info = self.migration_tasks[task_id]
            
            # 检查重试次数
            if migration_info.retry_count >= self.max_retry_attempts:
                _ = logger.error(f"任务 {task_id} 迁移重试次数已达上限")
                return False
            
            migration_info.retry_count += 1
            _ = logger.info(f"重试任务 {task_id} 的迁移 (第 {migration_info.retry_count} 次)")
            
            # 重新选择目标节点
            target_node = await self._select_target_node(task_id, migration_info.source_node_id)
            if not target_node:
                _ = logger.error(f"无法为任务 {task_id} 重新选择目标节点")
                return False
            
            migration_info.target_node_id = target_node
            
            # 执行迁移
            success = await self._execute_task_migration(migration_info)
            
            if success:
                migration_info.status = "completed"
                _ = logger.info(f"任务 {task_id} 重试迁移成功")
            else:
                migration_info.status = "failed"
                _ = logger.error(f"任务 {task_id} 重试迁移失败")
            
            return success
            
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"重试任务迁移失败: {task_id} - {e}")
            return False
    
    def get_migration_status(self, task_id: str = None) -> Dict[str, Any]:
        """获取迁移状态"""
        context = ErrorContext("TaskMigrator", "get_migration_status", {"task_id": task_id})
        try:
            if task_id:
                if task_id in self.migration_tasks:
                    return asdict(self.migration_tasks[task_id])
                else:
                    return {}
            
            # 返回所有迁移任务的状态
            status = {
                _ = 'total_migrations': len(self.migration_tasks),
                'pending_migrations': len([t for t in self.migration_tasks.values() if t.status == 'pending']),
                'migrating_tasks': len([t for t in self.migration_tasks.values() if t.status == 'migrating']),
                'completed_migrations': len([t for t in self.migration_tasks.values() if t.status == 'completed']),
                'failed_migrations': len([t for t in self.migration_tasks.values() if t.status == 'failed']),
                'migration_tasks': [asdict(task_info) for task_info in self.migration_tasks.values()]
            }
            
            return status
            
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"获取迁移状态失败: {e}")
            return {}

# 全局任务迁移器实例（需要在实际使用时初始化）
global_task_migrator = None

def initialize_task_migrator(distributed_optimizer: Any, config: Optional[Dict[str, Any]] = None):
    """初始化全局任务迁移器"""
    global global_task_migrator
    global_task_migrator = TaskMigrator(distributed_optimizer, config)
    return global_task_migrator

def main() -> None:
    """主函数，用于测试任务迁移器"""
    _ = print("🔬 测试任务迁移器...")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建模拟的分布式优化器
    class MockDistributedOptimizer:
        def __init__(self) -> None:
            self.nodes = {
                'node1': {
                    'assigned_tasks': ['task1', 'task2'],
                    'performance_metrics': {'cpu_usage': 45.0, 'memory_usage': 60.0}
                },
                'node2': {
                    'assigned_tasks': ['task3'],
                    'performance_metrics': {'cpu_usage': 30.0, 'memory_usage': 40.0}
                }
            }
    
    mock_optimizer = MockDistributedOptimizer()
    
    # 初始化任务迁移器
    config = {
        'max_retry_attempts': 3,
        'migration_strategy': 'load_balanced'
    }
    migrator = TaskMigrator(mock_optimizer, config)
    
    # 模拟任务迁移
    _ = print("模拟任务迁移...")
    _ = asyncio.run(migrator.migrate_task_on_failure('task1', 'node1'))
    
    # 显示迁移状态
    _ = print("\n迁移状态:")
    status = migrator.get_migration_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    _ = main()