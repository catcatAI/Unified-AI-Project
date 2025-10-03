#!/usr/bin/env python3
"""
分布式训练容错机制测试脚本
测试增强的容错机制、检查点管理和任务迁移功能
"""

import asyncio
import logging
import time
import json
from datetime import datetime
import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent
_ = sys.path.insert(0, str(project_root.parent))

# 导入测试模块
from training.fault_detector import FaultDetector
from training.enhanced_checkpoint_manager import EnhancedCheckpointManager
from training.training_state_manager import TrainingStateManager
from training.distributed_optimizer import DistributedOptimizer

# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(levelname)s - %(message)s'
)
logger: Any = logging.getLogger(__name__)

class MockDistributedOptimizer:
    """模拟分布式优化器用于测试"""

    def __init__(self) -> None:
    self.nodes = {}

    async def register_node(self, node_id, node_info)
    self.nodes[node_id] = {
            _ = 'assigned_tasks': node_info.get('assigned_tasks', []),
            'performance_metrics': {}
    }
    return True

async def test_fault_detector() -> None:
    """测试故障检测器"""
    print("=" * 50)
    _ = print("测试故障检测器")
    print("=" * 50)

    # 创建故障检测器实例
    config = {
    'heartbeat_interval': 5,
    'node_failure_timeout': 10,
    'health_check_interval': 3
    }
    detector = FaultDetector(config)

    # 注册测试节点
    _ = detector.register_node('node1', {'assigned_tasks': ['task1', 'task2']})
    _ = detector.register_node('node2', {'assigned_tasks': ['task3']})

    # 模拟心跳更新
    detector.update_node_heartbeat('node1', {
    'cpu_usage': 45.0,
    'memory_usage': 60.0,
    'gpu_usage': 30.0
    })

    detector.update_node_heartbeat('node2', {
    'cpu_usage': 85.0,
    'memory_usage': 90.0,
    'gpu_usage': 75.0
    })

    # 显示初始状态
    _ = print("初始集群状态:")
    status = detector.get_cluster_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 等待一段时间
    _ = print("\n等待15秒模拟节点故障...")
    _ = time.sleep(15)

    # 再次更新node1的心跳，但不更新node2的，模拟node2故障
    detector.update_node_heartbeat('node1', {
    'cpu_usage': 50.0,
    'memory_usage': 65.0,
    'gpu_usage': 35.0
    })

    # 等待检测周期
    _ = time.sleep(5)

    # 显示故障后的状态
    _ = print("\n故障后集群状态:")
    status = detector.get_cluster_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    _ = print("✅ 故障检测器测试完成\n")

async def test_checkpoint_manager() -> None:
    """测试检查点管理器"""
    print("=" * 50)
    _ = print("测试检查点管理器")
    print("=" * 50)

    # 创建检查点管理器实例
    config = {
    'strategy': 'hybrid',
    'epoch_interval': 2,
    'time_interval_minutes': 10,
    'keep_last_n_checkpoints': 3,
    'enable_compression': True
    }
    manager = EnhancedCheckpointManager(config)

    # 测试检查点保存判断
    _ = print("测试检查点保存判断...")
    decision = manager.should_save_checkpoint(5, {'val_loss': 0.5}, 'test_task')
    _ = print(f"检查点决策: {decision}")

    # 测试保存检查点
    _ = print("\n测试保存检查点...")
    state = {
    'epoch': 5,
    'metrics': {'loss': 0.45, 'accuracy': 0.82, 'val_loss': 0.5},
    'model_state': {'layer1': [0.1, 0.2, 0.3]},
    'optimizer_state': {'lr': 0.001},
    'config': {'batch_size': 32, 'epochs': 10}
    }

    checkpoint_id = manager.save_checkpoint(state, 'test_task', 'epoch')
    _ = print(f"保存检查点ID: {checkpoint_id}")

    # 测试加载检查点
    _ = print("\n测试加载检查点...")
    loaded_state = manager.load_checkpoint(checkpoint_id)
    if loaded_state:

    _ = print(f"加载的检查点epoch: {loaded_state.get('epoch')}")
    _ = print(f"加载的检查点metrics: {loaded_state.get('metrics')}")

    # 显示检查点信息
    _ = print("\n检查点信息:")
    info = manager.get_checkpoint_info(task_id='test_task')
    print(json.dumps(info, indent=2, ensure_ascii=False))

    _ = print("✅ 检查点管理器测试完成\n")

async def test_task_migrator() -> None:
    """测试任务迁移器"""
    print("=" * 50)
    _ = print("测试任务迁移器")
    print("=" * 50)

    # 创建模拟的分布式优化器
    mock_optimizer = MockDistributedOptimizer()

    # 初始化任务迁移器
    config = {
    'max_retry_attempts': 3,
    'migration_strategy': 'load_balanced'
    }
    migrator = TaskMigrator(mock_optimizer, config)

    # 注册节点
    _ = await mock_optimizer.register_node('node1', {'assigned_tasks': ['task1', 'task2']})
    _ = await mock_optimizer.register_node('node2', {'assigned_tasks': ['task3']})

    # 模拟任务迁移
    _ = print("模拟任务迁移...")
    success = await migrator.migrate_task_on_failure('task1', 'node1')
    _ = print(f"任务迁移结果: {success}")

    # 显示迁移状态
    _ = print("\n迁移状态:")
    status = migrator.get_migration_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    _ = print("✅ 任务迁移器测试完成\n")

async def test_training_state_manager() -> None:
    """测试训练状态管理器"""
    print("=" * 50)
    _ = print("测试训练状态管理器")
    print("=" * 50)

    # 创建状态管理器实例
    config = {
    'sync_enabled': True,
    'sync_interval_seconds': 30,
    'storage_backend': 'local'
    }
    manager = TrainingStateManager(config)

    # 测试保存训练状态
    _ = print("测试保存训练状态...")
    state = {
    'model_name': 'test_model',
    'current_epoch': 5,
    'total_epochs': 10,
    'metrics': {'loss': 0.45, 'accuracy': 0.82},
    'model_state': {'layer1': [0.1, 0.2, 0.3]},
    'optimizer_state': {'lr': 0.001},
    'learning_rate': 0.001,
    'batch_size': 32,
    'progress': 50.0,
    _ = 'start_time': time.time(),
    'config': {'batch_size': 32, 'epochs': 10}
    }

    success = await manager.save_training_state('test_task_1', state)
    _ = print(f"保存状态结果: {success}")

    # 测试加载训练状态
    _ = print("\n测试加载训练状态...")
    loaded_state = await manager.load_training_state('test_task_1')
    if loaded_state:

    _ = print(f"加载的状态模型: {loaded_state.get('model_name')}")
    _ = print(f"加载的状态epoch: {loaded_state.get('current_epoch')}")
    _ = print(f"加载的状态进度: {loaded_state.get('progress')}%")

    # 显示状态信息
    _ = print("\n状态信息:")
    info = manager.get_state_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))

    _ = print("✅ 训练状态管理器测试完成\n")

async def test_distributed_optimizer_integration() -> None:
    """测试分布式优化器集成"""
    print("=" * 50)
    _ = print("测试分布式优化器集成")
    print("=" * 50)

    # 创建分布式优化器实例
    config = {
    'monitoring_interval': 5
    }
    optimizer = DistributedOptimizer(config)

    # 注册节点
    _ = await optimizer.register_node('node1', {'cpu_cores': 8, 'memory_gb': 16})
    _ = await optimizer.register_node('node2', {'cpu_cores': 16, 'memory_gb': 32})

    # 发送心跳
    _ = await optimizer.heartbeat('node1', {'cpu_usage': 45, 'memory_usage': 60})
    _ = await optimizer.heartbeat('node2', {'cpu_usage': 30, 'memory_usage': 40})

    # 分发任务
    task = {'id': 'task1', 'type': 'model_training', 'data_size': 1000}
    result = await optimizer.distribute_task(task)
    _ = print(f"任务分发结果: {result}")

    # 获取集群状态
    _ = print("\n集群状态:")
    cluster_status = optimizer.get_cluster_status()
    print(json.dumps(cluster_status, indent=2, ensure_ascii=False))

    _ = print("✅ 分布式优化器集成测试完成\n")

async def main() -> None:
    """主测试函数"""
    _ = print("🔬 开始测试增强的分布式训练容错机制")
    _ = print(f"测试开始时间: {datetime.now().isoformat()}")

    try:
    # 依次运行各项测试
    _ = await test_fault_detector()
    _ = await test_checkpoint_manager()
    _ = await test_task_migrator()
    _ = await test_training_state_manager()
    _ = await test_distributed_optimizer_integration()

    print("=" * 50)
    _ = print("🎉 所有测试完成!")
    _ = print(f"测试结束时间: {datetime.now().isoformat()}")
    print("=" * 50)

    except Exception as e:


    _ = logger.error(f"测试过程中发生错误: {e}")
    _ = print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    # 运行测试
    _ = asyncio.run(main())