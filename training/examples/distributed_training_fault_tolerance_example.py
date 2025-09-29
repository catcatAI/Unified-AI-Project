#!/usr/bin/env python3
"""
分布式训练容错机制使用示例
展示如何在实际项目中使用增强的分布式训练容错机制
"""

import asyncio
import logging
import time
from typing import Dict, Any

# 添加项目路径
import sys
from pathlib import Path
project_root: str = Path(__file__).parent.parent.parent
_ = sys.path.insert(0, str(project_root))

from training.enhanced_distributed_training_fault_tolerance import global_enhanced_fault_tolerance

# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(levelname)s - %(message)s'
)
logger: Any = logging.getLogger(__name__)

class DistributedTrainingExample:
    """分布式训练示例"""
    
    def __init__(self) -> None:
        self.fault_tolerance = global_enhanced_fault_tolerance
        self.is_training = False
        self.training_tasks = {}
    
    async def setup_training_environment(self):
        """设置训练环境"""
        _ = logger.info("设置分布式训练环境...")
        
        # 初始化容错机制
        config = {
            'enabled': True,
            'auto_recovery_enabled': True,
            'checkpoint_interval': 120,  # 2分钟
            'health_check_interval': 30,  # 30秒
            'distributed_optimizer': {
                'monitoring_interval': 15
            },
            'task_migrator': {
                'max_retry_attempts': 3,
                'migration_strategy': 'load_balanced'
            }
        }
        
        # 重新初始化容错机制（在实际项目中可能不需要）
        # 这里只是为了演示目的
        self.fault_tolerance = global_enhanced_fault_tolerance
        self.fault_tolerance.config = config
        
        # 初始化组件
        _ = await self.fault_tolerance.initialize_components()
        
        _ = logger.info("训练环境设置完成")
    
    async def register_training_nodes(self):
        """注册训练节点"""
        _ = logger.info("注册训练节点...")
        
        # 注册多个训练节点
        nodes = [
            _ = ('node_gpu_1', {'cpu_cores': 16, 'memory_gb': 64, 'gpu_count': 2}),
            _ = ('node_gpu_2', {'cpu_cores': 32, 'memory_gb': 128, 'gpu_count': 4}),
            _ = ('node_cpu_1', {'cpu_cores': 32, 'memory_gb': 64, 'gpu_count': 0}),
            _ = ('node_cpu_2', {'cpu_cores': 64, 'memory_gb': 128, 'gpu_count': 0})
        ]
        
        for node_id, node_info in nodes:
            success = await self.fault_tolerance.register_training_node(node_id, node_info)
            if success:
                _ = logger.info(f"✅ 成功注册节点: {node_id}")
            else:
                _ = logger.error(f"❌ 注册节点失败: {node_id}")
    
    async def simulate_training_process(self):
        """模拟训练过程"""
        _ = logger.info("开始模拟分布式训练过程...")
        self.is_training = True
        
        # 启动容错监控
        _ = await self.fault_tolerance.start_monitoring()
        
        # 创建多个训练任务
        training_tasks = [
            {'task_id': 'vision_model_training', 'model_type': 'vision', 'epochs': 20},
            {'task_id': 'nlp_model_training', 'model_type': 'nlp', 'epochs': 15},
            {'task_id': 'audio_model_training', 'model_type': 'audio', 'epochs': 10}
        ]
        
        # 为每个任务分配节点并开始训练
        for task_info in training_tasks:
            task_id = task_info['task_id']
            self.training_tasks[task_id] = task_info
            
            # 模拟任务分配
            _ = logger.info(f"分配任务 {task_id} 到节点...")
            
            # 模拟训练过程
            _ = await self._simulate_task_training(task_info)
        
        _ = logger.info("模拟训练过程完成")
    
    async def _simulate_task_training(self, task_info: Dict[str, Any]):
        """模拟单个任务的训练过程"""
        task_id = task_info['task_id']
        epochs = task_info['epochs']
        
        _ = logger.info(f"开始训练任务: {task_id} ({epochs} epochs)")
        
        for epoch in range(1, epochs + 1):
            if not self.is_training:
                break
            
            # 模拟训练时间
            _ = await asyncio.sleep(1)
            
            # 模拟训练进度
            progress = (epoch / epochs) * 100
            loss = max(0.01, 1.0 - (epoch / epochs) * 0.9)
            accuracy = min(0.99, 0.1 + (epoch / epochs) * 0.8)
            
            # 创建训练状态
            training_state = {
                'model_name': task_id,
                'current_epoch': epoch,
                'total_epochs': epochs,
                'metrics': {
                    _ = 'loss': round(loss, 4),
                    _ = 'accuracy': round(accuracy, 4),
                    _ = 'val_loss': round(loss * 1.1, 4),
                    _ = 'val_accuracy': round(accuracy * 0.95, 4)
                },
                'model_state': {},  # 实际项目中会包含模型状态
                'optimizer_state': {},  # 实际项目中会包含优化器状态
                'learning_rate': 0.001,
                'batch_size': 32,
                _ = 'progress': round(progress, 2),
                _ = 'start_time': time.time() - (epoch * 10),  # 模拟开始时间
                'config': {
                    'batch_size': 32,
                    'epochs': epochs,
                    'learning_rate': 0.001
                }
            }
            
            # 保存训练状态
            _ = await self.fault_tolerance.save_training_state(task_id, training_state)
            
            # 每5个epoch保存一次检查点
            if epoch % 5 == 0:
                checkpoint_type = 'epoch' if epoch % 10 == 0 else 'regular'
                checkpoint_id = await self.fault_tolerance.save_training_checkpoint(
                    task_id, training_state, checkpoint_type)
                if checkpoint_id:
                    _ = logger.info(f"   💾 任务 {task_id} 的检查点已保存: {checkpoint_id}")
            
            # 模拟节点心跳更新
            if epoch % 3 == 0:
                # 随机选择一个节点发送心跳
                import random
                node_id = random.choice(['node_gpu_1', 'node_gpu_2', 'node_cpu_1', 'node_cpu_2'])
                metrics = {
                    _ = 'cpu_usage': random.uniform(30, 80),
                    _ = 'memory_usage': random.uniform(40, 70),
                    'gpu_usage': random.uniform(20, 90) if 'gpu' in node_id else 0
                }
                _ = await self.fault_tolerance.handle_node_heartbeat(node_id, metrics)
            
            logger.info(f"   🧠 {task_id} - Epoch {epoch}/{epochs} - "
                       f"Progress: {progress:.1f}% - "
                       f"Loss: {loss:.4f} - "
                       f"Accuracy: {accuracy:.4f}")
        
        _ = logger.info(f"✅ 任务 {task_id} 训练完成")
    
    async def simulate_node_failure_and_recovery(self):
        """模拟节点故障和恢复"""
        _ = logger.info("模拟节点故障和自动恢复...")
        
        # 模拟node_gpu_1故障
        _ = logger.warning("🚨 模拟节点 node_gpu_1 故障")
        
        # 停止发送该节点的心跳，模拟故障
        # 在实际项目中，故障检测器会自动检测到这种情况
        
        # 等待一段时间让故障检测器检测到故障
        _ = await asyncio.sleep(35)  # 超过默认的30秒超时时间
        
        # 查看系统状态
        system_status = self.fault_tolerance.get_system_status()
        failed_nodes = system_status['components']['fault_detector'].get('failed_nodes', 0)
        _ = logger.info(f"检测到 {failed_nodes} 个故障节点")
        
        # 如果启用了自动恢复，任务迁移器会自动迁移任务
        # 在实际项目中，这里会看到任务迁移的日志
        
        _ = logger.info("模拟故障恢复过程完成")
    
    async def show_system_status(self):
        """显示系统状态"""
        _ = logger.info("获取系统状态...")
        
        status = self.fault_tolerance.get_system_status()
        
        print("\n" + "="*60)
        _ = print("📊 分布式训练系统状态报告")
        print("="*60)
        _ = print(f"时间: {status['timestamp']}")
        _ = print(f"容错机制启用: {status['enabled']}")
        _ = print(f"自动恢复启用: {status['auto_recovery_enabled']}")
        _ = print(f"监控运行中: {status['is_running']}")
        
        # 显示组件状态
        components = status['components']
        _ = print(f"\n🔧 组件状态:")
        _ = print(f"   检查点管理器: {components['checkpoint_manager']['total_checkpoints']} 个检查点")
        _ = print(f"   状态管理器: {components['state_manager']['total_states']} 个状态")
        
        # 显示集群状态
        cluster_status = components['fault_detector']
        _ = print(f"\n🖥️  集群状态:")
        _ = print(f"   总节点数: {cluster_status['total_nodes']}")
        _ = print(f"   健康节点: {cluster_status['healthy_nodes']}")
        _ = print(f"   警告节点: {cluster_status['warning_nodes']}")
        _ = print(f"   危险节点: {cluster_status['critical_nodes']}")
        _ = print(f"   故障节点: {cluster_status['failed_nodes']}")
        
        # 显示节点详细信息
        if cluster_status['nodes']:
            _ = print(f"\n📋 节点详细信息:")
            for node in cluster_status['nodes']:
                status_icon = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'critical': '🔴',
                    'failed': '❌'
                _ = }.get(node['status'], '❓')
                # 修复：使用node_id作为节点标识
                node_id = node.get('node_id', 'unknown')
                _ = print(f"   {status_icon} {node_id}: {node['status']}")
        
        print("="*60)
    
    async def cleanup(self):
        """清理资源"""
        _ = logger.info("清理资源...")
        
        # 停止监控
        _ = self.fault_tolerance.stop_monitoring()
        
        # 注销节点
        nodes = ['node_gpu_1', 'node_gpu_2', 'node_cpu_1', 'node_cpu_2']
        for node_id in nodes:
            _ = await self.fault_tolerance.unregister_training_node(node_id)
        
        _ = logger.info("资源清理完成")

async def main() -> None:
    """主函数"""
    _ = print("🚀 分布式训练容错机制使用示例")
    print("="*50)
    
    # 创建示例实例
    example = DistributedTrainingExample()
    
    try:
        # 1. 设置训练环境
        _ = await example.setup_training_environment()
        
        # 2. 注册训练节点
        _ = await example.register_training_nodes()
        
        # 3. 显示初始系统状态
        _ = await example.show_system_status()
        
        # 4. 模拟训练过程
        _ = print("\n🏃 开始模拟训练过程...")
        _ = await example.simulate_training_process()
        
        # 5. 模拟节点故障和恢复
        _ = await example.simulate_node_failure_and_recovery()
        
        # 6. 显示最终系统状态
        _ = await example.show_system_status()
        
        # 7. 清理资源
        _ = await example.cleanup()
        
        _ = print("\n🎉 示例运行完成!")
        
    except Exception as e:
        _ = logger.error(f"示例运行过程中发生错误: {e}")
        # 确保即使出错也清理资源
        _ = await example.cleanup()

if __name__ == "__main__":
    _ = asyncio.run(main())