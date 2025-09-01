#!/usr/bin/env python3
"""
协作式训练管理器
负责协调所有模型的训练过程，实现模型间的协作训练
"""

import os
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import threading
import time
import numpy as np

# 添加项目路径
import sys
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# 导入项目模块
try:
    from apps.backend.src.path_config import (
        PROJECT_ROOT, 
        DATA_DIR, 
        TRAINING_DIR, 
        MODELS_DIR,
        get_data_path, 
        resolve_path
    )
except ImportError:
    # 如果路径配置模块不可用，使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR = PROJECT_ROOT / "data"
    TRAINING_DIR = PROJECT_ROOT / "training"
    MODELS_DIR = TRAINING_DIR / "models"

# 导入数据管理器和资源管理器
from .data_manager import DataManager
from .resource_manager import ResourceManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class ModelTrainingTask:
    """模型训练任务"""
    model_name: str
    model_instance: Any
    data: List[Dict]
    resources: Dict
    epochs: int = 10
    batch_size: int = 32
    status: str = "pending"  # pending, running, completed, failed, cancelled
    current_epoch: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    thread: Optional[threading.Thread] = None
    progress: float = 0.0
    metrics: Optional[Dict[str, Any]] = None

class CollaborativeTrainingManager:
    """协作式训练管理器，负责协调所有模型的训练过程"""
    
    def __init__(self):
        self.models = {}
        self.training_tasks = {}
        self.data_manager = DataManager()
        self.resource_manager = ResourceManager()
        self.training_progress = {}
        self.is_training = False
        self.training_thread = None
        self.stop_requested = False
        # 添加知识共享机制
        self.shared_knowledge = {}  # 存储模型间共享的知识
        # 添加检查点管理
        self.checkpoints = {}
        
        logger.info("🔄 协作式训练管理器初始化完成")
    
    def register_model(self, model_name: str, model_instance: Any):
        """注册模型"""
        self.models[model_name] = model_instance
        logger.info(f"✅ 注册模型: {model_name}")
    
    def unregister_model(self, model_name: str):
        """注销模型"""
        if model_name in self.models:
            del self.models[model_name]
            logger.info(f"🗑️  注销模型: {model_name}")
    
    def prepare_training_data(self) -> Dict[str, List[Dict]]:
        """为所有模型准备训练数据"""
        logger.info("📦 开始准备训练数据...")
        
        # 扫描所有数据
        self.data_manager.scan_data()
        
        # 为每个模型准备数据
        model_data = {}
        for model_name in self.models.keys():
            data = self.data_manager.prepare_training_data(model_name)
            model_data[model_name] = data
            logger.info(f"   为模型 {model_name} 准备了 {len(data)} 个训练文件")
        
        return model_data
    
    def allocate_resources_for_models(self) -> Dict[str, Dict]:
        """为所有模型分配资源"""
        logger.info("🖥️  开始分配资源...")
        
        model_resources = {}
        for model_name in self.models.keys():
            requirements = self.resource_manager.get_model_resource_requirements(model_name)
            allocation = self.resource_manager.allocate_resources(requirements, model_name)
            model_resources[model_name] = allocation
            
            if allocation:
                logger.info(f"   为模型 {model_name} 分配资源成功")
            else:
                logger.warning(f"   为模型 {model_name} 分配资源失败")
        
        return model_resources
    
    def create_training_tasks(self, model_data: Dict[str, List[Dict]], 
                            model_resources: Dict[str, Dict]) -> List[ModelTrainingTask]:
        """创建训练任务"""
        tasks = []
        
        for model_name, model_instance in self.models.items():
            data = model_data.get(model_name, [])
            resources = model_resources.get(model_name)
            
            if resources:
                task = ModelTrainingTask(model_name, model_instance, data, resources)
                tasks.append(task)
                self.training_tasks[model_name] = task
                logger.info(f"✅ 创建训练任务: {model_name}")
            else:
                logger.warning(f"⚠️  无法为模型 {model_name} 创建训练任务，资源分配失败")
        
        return tasks
    
    def _train_model_task(self, task: 'ModelTrainingTask'):
        """训练单个模型任务"""
        try:
            model_name = task.model_name
            logger.info(f"🏃 开始训练模型 {model_name}")
            task.status = "running"
            task.start_time = datetime.now()
            
            # 检查是否存在检查点
            checkpoint = self._load_checkpoint(model_name)
            start_epoch = checkpoint.get('epoch', 0) if checkpoint else 0
            
            # 如果从检查点开始，恢复训练状态
            if start_epoch > 0:
                logger.info(f"🔄 从检查点恢复训练: {model_name} - Epoch {start_epoch}")
                task.current_epoch = start_epoch
                self.training_progress[model_name] = checkpoint.get('progress', {})
            
            # 模拟训练过程
            for epoch in range(start_epoch, task.epochs):
                if self.stop_requested:
                    task.status = "cancelled"
                    # 保存检查点
                    self._save_checkpoint(model_name, epoch, self.training_progress.get(model_name, {}))
                    logger.info(f"⏹️  训练被取消: {model_name}")
                    return
                
                # 模拟训练一个epoch
                time.sleep(0.1)  # 模拟训练时间
                
                # 更新进度
                task.current_epoch = epoch + 1
                progress = (epoch + 1) / task.epochs * 100
                self.training_progress[model_name] = {
                    'epoch': epoch + 1,
                    'progress': progress,
                    'loss': 1.0 - (epoch + 1) / task.epochs * 0.9,  # 模拟损失下降
                    'accuracy': 0.1 + (epoch + 1) / task.epochs * 0.9  # 模拟准确率上升
                }
                # 更新任务的进度和指标
                task.progress = progress
                task.metrics = {
                    'loss': self.training_progress[model_name]['loss'],
                    'accuracy': self.training_progress[model_name]['accuracy']
                }
                
                # 每10个epoch共享一次知识
                if (epoch + 1) % 10 == 0:
                    self._share_knowledge(model_name, self.training_progress[model_name])
                
                # 每5个epoch保存一次检查点
                if (epoch + 1) % 5 == 0:
                    self._save_checkpoint(model_name, epoch + 1, self.training_progress[model_name])
                
                logger.info(f"📊 {model_name} - Epoch {epoch + 1}/{task.epochs} - "
                           f"Progress: {progress:.1f}% - "
                           f"Loss: {self.training_progress[model_name]['loss']:.4f} - "
                           f"Accuracy: {self.training_progress[model_name]['accuracy']:.4f}")
            
            # 训练完成
            task.status = "completed"
            task.end_time = datetime.now()
            task.result = {
                'final_loss': self.training_progress[model_name]['loss'],
                'final_accuracy': self.training_progress[model_name]['accuracy'],
                'training_time': (task.end_time - task.start_time).total_seconds()
            }
            
            # 保存模型
            self._save_model(model_name, task.result)
            
            # 删除检查点（训练完成）
            self._delete_checkpoint(model_name)
            
            logger.info(f"✅ 模型 {model_name} 训练完成")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            # 保存检查点
            current_epoch = task.current_epoch
            self._save_checkpoint(model_name, current_epoch, self.training_progress.get(model_name, {}))
            logger.error(f"❌ 模型 {model_name} 训练失败: {e}")
            # 记录错误日志
            self._log_error(model_name, e)
    
    def _share_knowledge(self, model_name: str, training_stats: Dict[str, Any]):
        """在模型间共享知识"""
        logger.info(f"🧠 模型 {model_name} 正在共享知识")
        
        # 将当前模型的训练统计信息添加到共享知识中
        if model_name not in self.shared_knowledge:
            self.shared_knowledge[model_name] = []
        
        # 记录当前训练状态
        knowledge_entry = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat(),
            'training_stats': training_stats.copy(),
            'knowledge_vector': self._extract_knowledge_vector(training_stats)
        }
        
        self.shared_knowledge[model_name].append(knowledge_entry)
        
        # 与其他模型共享知识
        for other_model_name in self.models.keys():
            if other_model_name != model_name:
                self._apply_shared_knowledge(other_model_name, knowledge_entry)
    
    def _extract_knowledge_vector(self, training_stats: Dict[str, Any]) -> List[float]:
        """从训练统计中提取知识向量"""
        # 简化实现，实际应用中需要更复杂的知识提取机制
        knowledge_vector = [
            training_stats.get('loss', 0.0),
            training_stats.get('accuracy', 0.0),
            training_stats.get('progress', 0.0)
        ]
        return knowledge_vector
    
    def _apply_shared_knowledge(self, model_name: str, knowledge_entry: Dict[str, Any]):
        """将共享知识应用到指定模型"""
        logger.debug(f"🔄 将知识从 {knowledge_entry['model_name']} 应用到 {model_name}")
        
        # 在实际实现中，这里会更新模型的参数或训练策略
        # 简化实现，仅记录日志
        pass
    
    def _save_model(self, model_name: str, training_result: Dict[str, Any]):
        """保存训练好的模型"""
        model_dir = MODELS_DIR / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存模型元数据
        metadata = {
            'model_name': model_name,
            'training_result': training_result,
            'saved_at': datetime.now().isoformat(),
            'shared_knowledge_count': len(self.shared_knowledge.get(model_name, []))
        }
        
        metadata_file = model_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 模型 {model_name} 已保存到 {model_dir}")
    
    def _save_checkpoint(self, model_name: str, epoch: int, progress: Dict[str, Any]):
        """保存训练检查点"""
        checkpoint_dir = TRAINING_DIR / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_data = {
            'model_name': model_name,
            'epoch': epoch,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        
        checkpoint_file = checkpoint_dir / f"{model_name}_checkpoint_epoch_{epoch}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        # 更新最新的检查点记录
        self.checkpoints[model_name] = checkpoint_file
        logger.info(f"💾 检查点已保存: {checkpoint_file}")
    
    def _load_checkpoint(self, model_name: str) -> Optional[Dict[str, Any]]:
        """加载训练检查点"""
        checkpoint_file = self.checkpoints.get(model_name)
        if checkpoint_file and checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                logger.info(f"📂 检查点已加载: {checkpoint_file}")
                return checkpoint_data
            except Exception as e:
                logger.error(f"❌ 加载检查点失败: {e}")
                return None
        return None
    
    def _delete_checkpoint(self, model_name: str):
        """删除训练检查点"""
        checkpoint_file = self.checkpoints.get(model_name)
        if checkpoint_file and checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                del self.checkpoints[model_name]
                logger.info(f"🗑️  检查点已删除: {checkpoint_file}")
            except Exception as e:
                logger.error(f"❌ 删除检查点失败: {e}")
    
    def _log_error(self, model_name: str, error: Exception):
        """记录错误日志"""
        error_log_dir = TRAINING_DIR / "error_logs"
        error_log_dir.mkdir(parents=True, exist_ok=True)
        
        error_data = {
            'model_name': model_name,
            'error': str(error),
            'timestamp': datetime.now().isoformat(),
            'traceback': str(error.__traceback__) if error.__traceback__ else None
        }
        
        error_file = error_log_dir / f"{model_name}_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📝 错误日志已保存: {error_file}")
    
    def start_collaborative_training(self, scenario: Dict[str, Any] = None) -> bool:
        """开始协作式训练"""
        if self.is_training:
            logger.warning("⚠️  训练已在进行中")
            return False
        
        logger.info("🔄 开始协作式训练...")
        self.is_training = True
        self.stop_requested = False
        
        try:
            # 1. 准备训练数据
            model_data = self.prepare_training_data()
            
            # 2. 分配资源
            model_resources = self.allocate_resources_for_models()
            
            # 3. 创建训练任务
            tasks = self.create_training_tasks(model_data, model_resources)
            
            if not tasks:
                logger.error("❌ 没有可执行的训练任务")
                self.is_training = False
                return False
            
            # 4. 并行执行训练任务
            logger.info(f"🏃 开始并行训练 {len(tasks)} 个模型...")
            
            # 创建并启动训练线程
            threads = []
            for task in tasks:
                thread = threading.Thread(target=self._train_model_task, args=(task,))
                thread.start()
                threads.append(thread)
                task.thread = thread
            
            # 等待所有训练完成
            for thread in threads:
                thread.join()
            
            # 5. 检查训练结果
            success_count = 0
            for task in tasks:
                if task.status == "completed":
                    success_count += 1
                    logger.info(f"✅ 模型 {task.model_name} 训练成功")
                else:
                    logger.error(f"❌ 模型 {task.model_name} 训练失败")
            
            logger.info(f"🏁 协作式训练完成: {success_count}/{len(tasks)} 个模型训练成功")
            
            # 6. 保存训练结果
            self._save_training_results(tasks, scenario)
            
            self.is_training = False
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 协作式训练过程中发生错误: {e}")
            self.is_training = False
            return False
    
    def _save_training_results(self, tasks: List[ModelTrainingTask], scenario: Dict[str, Any] = None):
        """保存训练结果"""
        results = {
            'training_date': datetime.now().isoformat(),
            'total_models': len(tasks),
            'successful_models': 0,
            'failed_models': 0,
            'model_results': []
        }
        
        for task in tasks:
            model_result = {
                'model_name': task.model_name,
                'status': task.status,
                'progress': task.progress,
                'metrics': task.metrics,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'data_files_count': len(task.data)
            }
            
            results['model_results'].append(model_result)
            
            if task.status == "completed":
                results['successful_models'] += 1
            else:
                results['failed_models'] += 1
        
        # 保存结果到文件
        results_file = TRAINING_DIR / f"collaborative_training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 训练结果已保存到: {results_file}")
        except Exception as e:
            logger.error(f"❌ 保存训练结果失败: {e}")
    
    def stop_training(self):
        """停止训练"""
        if self.is_training:
            logger.info("⏹️  请求停止训练...")
            self.stop_requested = True
            
            # 等待训练线程结束
            if self.training_thread and self.training_thread.is_alive():
                self.training_thread.join(timeout=5)
            
            self.is_training = False
            logger.info("✅ 训练已停止")
        else:
            logger.info("ℹ️  当前没有正在进行的训练")
    
    def get_training_status(self) -> Dict[str, Any]:
        """获取训练状态"""
        status = {
            'is_training': self.is_training,
            'total_models': len(self.training_tasks),
            'model_statuses': {}
        }
        
        for model_name, task in self.training_tasks.items():
            status['model_statuses'][model_name] = {
                'status': task.status,
                'progress': task.progress,
                'metrics': task.metrics
            }
        
        return status
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        return self.resource_manager.get_resource_allocation_status()
    
    def optimize_training_process(self):
        """优化训练过程"""
        # 这里可以实现训练过程的优化逻辑
        # 例如：根据模型训练进度动态调整资源分配
        logger.info("⚙️  优化训练过程...")
        
        optimization_result = self.resource_manager.optimize_resource_allocation()
        logger.info("✅ 训练过程优化完成")
        
        return optimization_result
    
    def enable_model_collaboration(self):
        """启用模型间的协作"""
        # 这里可以实现模型间的知识共享和协作机制
        logger.info("🤝 启用模型间协作...")
        
        # 示例：实现简单的模型间知识共享
        for model_name, task in self.training_tasks.items():
            if task.status == "completed" and task.metrics:
                # 将训练指标共享给其他模型
                logger.info(f"   模型 {model_name} 分享训练经验")
        
        logger.info("✅ 模型间协作启用完成")
    
    def save_training_state(self, state_path: str = None):
        """保存训练状态"""
        if not state_path:
            state_path = TRAINING_DIR / "collaborative_training_state.json"
        
        state_data = {
            'is_training': self.is_training,
            'training_tasks': {},
            'training_progress': self.training_progress,
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存任务状态
        for model_name, task in self.training_tasks.items():
            state_data['training_tasks'][model_name] = {
                'status': task.status,
                'progress': task.progress,
                'metrics': task.metrics,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None
            }
        
        try:
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 训练状态已保存到: {state_path}")
        except Exception as e:
            logger.error(f"❌ 保存训练状态失败: {e}")
    
    def load_training_state(self, state_path: str = None):
        """加载训练状态"""
        if not state_path:
            state_path = TRAINING_DIR / "collaborative_training_state.json"
        
        if not Path(state_path).exists():
            logger.warning(f"⚠️ 训练状态文件不存在: {state_path}")
            return False
        
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            self.is_training = state_data.get('is_training', False)
            self.training_progress = state_data.get('training_progress', {})
            
            # 加载任务状态
            task_states = state_data.get('training_tasks', {})
            for model_name, task_state in task_states.items():
                if model_name in self.training_tasks:
                    task = self.training_tasks[model_name]
                    task.status = task_state.get('status', 'pending')
                    task.progress = task_state.get('progress', 0)
                    task.metrics = task_state.get('metrics', {})
                    
                    start_time = task_state.get('start_time')
                    if start_time:
                        task.start_time = datetime.fromisoformat(start_time)
                    
                    end_time = task_state.get('end_time')
                    if end_time:
                        task.end_time = datetime.fromisoformat(end_time)
            
            logger.info(f"✅ 训练状态已从 {state_path} 加载")
            return True
        except Exception as e:
            logger.error(f"❌ 加载训练状态失败: {e}")
            return False


def main():
    """主函数，用于测试协作式训练管理器"""
    print("🔄 测试协作式训练管理器...")
    
    # 初始化协作式训练管理器
    manager = CollaborativeTrainingManager()
    
    # 模拟注册一些模型
    print("📋 注册模型...")
    manager.register_model("vision_service", "VisionModelInstance")
    manager.register_model("audio_service", "AudioModelInstance")
    manager.register_model("causal_reasoning_engine", "CausalReasoningInstance")
    manager.register_model("concept_models", "ConceptModelsInstance")
    
    # 显示注册的模型
    print(f"✅ 已注册 {len(manager.models)} 个模型:")
    for model_name in manager.models.keys():
        print(f"   - {model_name}")
    
    # 准备训练数据
    print("\n📦 准备训练数据...")
    model_data = manager.prepare_training_data()
    for model_name, data in model_data.items():
        print(f"   {model_name}: {len(data)} 个训练文件")
    
    # 分配资源
    print("\n🖥️  分配资源...")
    model_resources = manager.allocate_resources_for_models()
    for model_name, resources in model_resources.items():
        if resources:
            print(f"   {model_name}: 资源分配成功")
        else:
            print(f"   {model_name}: 资源分配失败")
    
    # 显示资源分配状态
    resource_status = manager.get_resource_usage()
    print(f"\n📈 资源分配状态:")
    print(f"   已分配CPU: {resource_status['allocated_cpu']} 核心")
    print(f"   可用CPU: {resource_status['available_cpu']:.1f} 核心")
    print(f"   已分配内存: {resource_status['allocated_memory_gb']:.2f} GB")
    
    # 获取训练状态
    training_status = manager.get_training_status()
    print(f"\n📊 训练状态:")
    print(f"   是否正在训练: {training_status['is_training']}")
    print(f"   模型数量: {training_status['total_models']}")
    
    print(f"\n✅ 协作式训练管理器测试完成")


if __name__ == "__main__":
    main()



