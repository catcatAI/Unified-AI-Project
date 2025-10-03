#!/usr/bin/env python3
"""
增强的检查点管理器
负责管理训练过程中的检查点保存、恢复和清理
"""

import logging
import json
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

# 添加项目路径
import sys
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

# 创建基本模拟类
ErrorContext = type('ErrorContext', (), {
    '__init__': lambda self, component, operation, details=None: (
    setattr(self, 'component', component),
    setattr(self, 'operation', operation),
    setattr(self, 'details', details or {})
    )[-1]
})

class GlobalErrorHandler:
    @staticmethod
    def handle_error(error, context, strategy=None)
    print(f"Error in {context.component}.{context.operation}: {error}")

global_error_handler = GlobalErrorHandler()

logger = logging.getLogger(__name__)

# 确保检查点目录存在
CHECKPOINTS_DIR = project_root / "training" / "checkpoints"
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class CheckpointInfo:
    """检查点信息"""
    checkpoint_id: str
    task_id: str
    epoch: int
    timestamp: float
    file_path: str
    metrics: Dict[str, Any]
    checkpoint_type: str  # 'regular', 'epoch', 'time_based', 'event_triggered'
    size_bytes: int = 0
    is_compressed: bool = False

class EnhancedCheckpointManager:
    """增强的检查点管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
    self.config = config or {}
    self.error_handler = global_error_handler
    self.checkpoints: Dict[str, CheckpointInfo] = {}
    self.checkpoint_history: List[CheckpointInfo] = []

    # 配置参数
    self.strategy = self.config.get('strategy', 'hybrid')  # 'epoch_only', 'time_based', 'hybrid'
    self.epoch_interval = self.config.get('epoch_interval', 5)  # epoch检查点间隔
    self.time_interval_minutes = self.config.get('time_interval_minutes', 30)  # 时间检查点间隔（分钟）
    self.keep_last_n_checkpoints = self.config.get('keep_last_n_checkpoints', 5)  # 保留最近N个检查点
    self.enable_compression = self.config.get('enable_compression', True)  # 启用压缩
    self.compression_threshold_mb = self.config.get('compression_threshold_mb', 100)  # 压缩阈值（MB）
    self.last_time_checkpoint = time.time()  # 上次时间检查点时间

    _ = logger.info("增强的检查点管理器初始化完成")

    def should_save_checkpoint(self, epoch: int, metrics: Dict[...]
    """判断是否应该保存检查点"""
    context = ErrorContext("EnhancedCheckpointManager", "should_save_checkpoint", {"epoch": epoch, "task_id": task_id})
        try:

            should_save = False
            checkpoint_type = "regular"
            reasons = []

            # 根据策略判断
            if self.strategy == 'epoch_only':
                # 仅在epoch间隔时保存
                if epoch % self.epoch_interval == 0:

    should_save = True
                    checkpoint_type = "epoch"
                    _ = reasons.append(f"Epoch {epoch} 是 {self.epoch_interval} 的倍数")

            elif self.strategy == 'time_based':
                # 仅在时间间隔时保存
                current_time = time.time()
                if (current_time - self.last_time_checkpoint) >= (self.time_interval_minutes * 60):

    should_save = True
                    checkpoint_type = "time_based"
                    _ = reasons.append(f"距离上次检查点已超过 {self.time_interval_minutes} 分钟")
                    self.last_time_checkpoint = current_time

            elif self.strategy == 'hybrid':
                # 混合策略：epoch间隔或时间间隔时保存
                epoch_checkpoint = epoch % self.epoch_interval == 0
                time_checkpoint = False
                current_time = time.time()
                if (current_time - self.last_time_checkpoint) >= (self.time_interval_minutes * 60):

    time_checkpoint = True
                    self.last_time_checkpoint = current_time

                if epoch_checkpoint or time_checkpoint:


    should_save = True
                    if epoch_checkpoint and time_checkpoint:

    checkpoint_type = "epoch_and_time"
                        _ = reasons.append(f"Epoch {epoch} 是 {self.epoch_interval} 的倍数且时间间隔已到")
                    elif epoch_checkpoint:

    checkpoint_type = "epoch"
                        _ = reasons.append(f"Epoch {epoch} 是 {self.epoch_interval} 的倍数")
                    else:

                        checkpoint_type = "time_based"
                        _ = reasons.append(f"距离上次检查点已超过 {self.time_interval_minutes} 分钟")

            # 特殊事件触发检查点（例如验证损失改善）
            if metrics and 'val_loss' in metrics:
                # 检查是否有显著改善
                if self._should_save_for_improvement(metrics, task_id)

    should_save = True
                    checkpoint_type = "event_triggered"
                    _ = reasons.append("验证损失显著改善")

            return {
                'should_save': should_save,
                'checkpoint_type': checkpoint_type,
                'reasons': reasons
            }

        except Exception as e:


            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"判断是否保存检查点失败: {e}")
            return {'should_save': False, 'checkpoint_type': 'regular', 'reasons': []}

    def _should_save_for_improvement(self, metrics: Dict[str, Any], task_id: str = None) -> bool:
    """判断是否因改善而保存检查点"""
        try:
            # 获取该任务的最新检查点
            task_checkpoints = [cp for cp in self.checkpoint_history if cp.task_id == task_id] if task_id else self.checkpoint_history:
    if not task_checkpoints:

    return True  # 如果没有之前的检查点，保存第一个

            # 获取最新的检查点
            latest_checkpoint = max(task_checkpoints, key=lambda x: x.timestamp)

            # 比较验证损失
            current_val_loss = metrics.get('val_loss', float('inf'))
            previous_val_loss = latest_checkpoint.metrics.get('val_loss', float('inf'))

            # 如果验证损失改善超过阈值，则保存检查点
            improvement_threshold = 0.05  # 5%的改善
            if previous_val_loss != float('inf') and current_val_loss < previous_val_loss * (1 - improvement_threshold):

    return True

            return False
        except Exception as e:

            _ = logger.warning(f"检查改善情况时出错: {e}")
            return False

    def save_checkpoint(self, state: Dict[...]
    """保存检查点"""
    context = ErrorContext("EnhancedCheckpointManager", "save_checkpoint", {"task_id": task_id, "checkpoint_type": checkpoint_type})
        try:
            # 生成检查点ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            checkpoint_id = f"ckpt_{task_id or 'default'}_{timestamp}_{int(time.time())}"

            # 创建检查点文件路径
            checkpoint_filename = f"{checkpoint_id}.json"
            checkpoint_path = CHECKPOINTS_DIR / checkpoint_filename

            # 准备检查点数据
            checkpoint_data = {
                'checkpoint_id': checkpoint_id,
                'task_id': task_id or 'default',
                _ = 'epoch': state.get('epoch', 0),
                _ = 'timestamp': time.time(),
                _ = 'metrics': state.get('metrics', {}),
                _ = 'model_state': state.get('model_state', {}),
                _ = 'optimizer_state': state.get('optimizer_state', {}),
                _ = 'config': state.get('config', {}),
                _ = 'additional_data': state.get('additional_data', {})
            }

            # 压缩大数据
            if self.enable_compression:

    checkpoint_data = self._compress_checkpoint_data(checkpoint_data)

            # 保存检查点到文件
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
    json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

            # 获取文件大小
            file_size = os.path.getsize(checkpoint_path)

            # 创建检查点信息
            checkpoint_info = CheckpointInfo(
                checkpoint_id=checkpoint_id,
                task_id=task_id or 'default',
                epoch=state.get('epoch', 0),
                timestamp=time.time(),
                file_path=str(checkpoint_path),
                metrics=state.get('metrics', {}),
                checkpoint_type=checkpoint_type,
                size_bytes=file_size,
                is_compressed=self.enable_compression
            )

            # 记录检查点
            self.checkpoints[checkpoint_id] = checkpoint_info
            _ = self.checkpoint_history.append(checkpoint_info)

            _ = logger.info(f"保存检查点: {checkpoint_id} (类型: {checkpoint_type}, 大小: {file_size} 字节)")

            # 清理旧检查点
            _ = self._cleanup_old_checkpoints(task_id)

            return checkpoint_id

        except Exception as e:


            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"保存检查点失败: {e}")
            return None

    def _compress_checkpoint_data(self, checkpoint_data: Dict[...]
    """压缩检查点数据"""
    # 这里应该实现实际的数据压缩逻辑
    # 为了示例，我们只是标记数据已被处理
    checkpoint_data['_compressed'] = True
    return checkpoint_data

    def load_checkpoint(self, checkpoint_id: str = None, task_id: str = None) -> Optional[Dict[str, Any]]:
    """加载检查点"""
    context = ErrorContext("EnhancedCheckpointManager", "load_checkpoint", {"checkpoint_id": checkpoint_id, "task_id": task_id})
        try:
            # 确定要加载的检查点
            target_checkpoint = None

            if checkpoint_id:
                # 根据ID加载特定检查点
                target_checkpoint = self.checkpoints.get(checkpoint_id)
            elif task_id:
                # 加载指定任务的最新检查点
                task_checkpoints = [cp for cp in self.checkpoint_history if cp.task_id == task_id]:
    if task_checkpoints:

    target_checkpoint = max(task_checkpoints, key=lambda x: x.timestamp)
            else:
                # 加载最新的检查点
                if self.checkpoint_history:

    target_checkpoint = max(self.checkpoint_history, key=lambda x: x.timestamp)

            if not target_checkpoint:


    _ = logger.warning("未找到要加载的检查点")
                return None

            # 读取检查点文件
            checkpoint_path = Path(target_checkpoint.file_path)
            if not checkpoint_path.exists()

    _ = logger.error(f"检查点文件不存在: {checkpoint_path}")
                return None

            with open(checkpoint_path, 'r', encoding='utf-8') as f:
    checkpoint_data = json.load(f)

            # 解压缩数据（如果需要）
            if checkpoint_data.get('_compressed')

    checkpoint_data = self._decompress_checkpoint_data(checkpoint_data)

            _ = logger.info(f"加载检查点: {target_checkpoint.checkpoint_id}")
            return checkpoint_data

        except Exception as e:


            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"加载检查点失败: {e}")
            return None

    def _decompress_checkpoint_data(self, checkpoint_data: Dict[...]
    """解压缩检查点数据"""
    # 这里应该实现实际的数据解压缩逻辑
    # 为了示例，我们只是移除压缩标记
    _ = checkpoint_data.pop('_compressed', None)
    return checkpoint_data

    def _cleanup_old_checkpoints(self, task_id: str = None)
    """清理旧检查点"""
    context = ErrorContext("EnhancedCheckpointManager", "_cleanup_old_checkpoints", {"task_id": task_id})
        try:
            # 获取特定任务的检查点或所有检查点
            if task_id:

    task_checkpoints = [cp for cp in self.checkpoint_history if cp.task_id == task_id]:
    else:

    task_checkpoints = self.checkpoint_history

            # 如果检查点数量超过保留数量，删除最旧的
            if len(task_checkpoints) > self.keep_last_n_checkpoints:
                # 按时间排序
                sorted_checkpoints = sorted(task_checkpoints, key=lambda x: x.timestamp)
                # 确定要删除的检查点
                checkpoints_to_remove = sorted_checkpoints[:-self.keep_last_n_checkpoints]

                # 删除文件和记录
                for checkpoint_info in checkpoints_to_remove:

    try:
                        # 删除文件
                        checkpoint_path = Path(checkpoint_info.file_path)
                        if checkpoint_path.exists()

    _ = checkpoint_path.unlink()
                            _ = logger.info(f"删除旧检查点文件: {checkpoint_path}")

                        # 从记录中移除
                        if checkpoint_info.checkpoint_id in self.checkpoints:

    del self.checkpoints[checkpoint_info.checkpoint_id]

                        # 从历史记录中移除
                        if checkpoint_info in self.checkpoint_history:

    _ = self.checkpoint_history.remove(checkpoint_info)
                    except Exception as e:

                        _ = logger.warning(f"删除检查点失败: {checkpoint_info.checkpoint_id} - {e}")

                _ = logger.info(f"清理了 {len(checkpoints_to_remove)} 个旧检查点")

        except Exception as e:


            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"清理旧检查点失败: {e}")

    def get_checkpoint_info(self, checkpoint_id: str = None, task_id: str = None) -> Dict[str, Any]:
    """获取检查点信息"""
    context = ErrorContext("EnhancedCheckpointManager", "get_checkpoint_info", {"checkpoint_id": checkpoint_id, "task_id": task_id})
        try:

            if checkpoint_id:


    if checkpoint_id in self.checkpoints:
    return asdict(self.checkpoints[checkpoint_id])
                else:

                    return {}

            # 返回任务的检查点信息或所有检查点信息
            if task_id:

    task_checkpoints = [cp for cp in self.checkpoint_history if cp.task_id == task_id]:
    return {
                    'task_id': task_id,
                    _ = 'total_checkpoints': len(task_checkpoints),
                    'checkpoints': [asdict(cp) for cp in task_checkpoints]
                }
            else:

    return {
                    _ = 'total_checkpoints': len(self.checkpoints),
                    'checkpoints': [asdict(cp) for cp in self.checkpoint_history]
                }

        except Exception as e:


    _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"获取检查点信息失败: {e}")
            return {}

# 全局检查点管理器实例
global_checkpoint_manager = EnhancedCheckpointManager()

def main() -> None:
    """主函数，用于测试检查点管理器"""
    _ = print("🔬 测试增强的检查点管理器...")

    # 配置日志
    logging.basicConfig(level=logging.INFO)

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

if __name__ == "__main__":


    _ = main()