#!/usr/bin/env python3
"""
增量学习管理器
实现增量数据识别、增量模型训练、智能训练触发和自动模型整理功能
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import threading
from collections import defaultdict
import hashlib

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))

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

# 导入数据管理器和模型训练器
from training.data_manager import DataManager
from training.train_model import ModelTrainer
from training.collaborative_training_manager import CollaborativeTrainingManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(TRAINING_DIR / 'incremental_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataTracker:
    """数据跟踪器，负责跟踪和管理训练数据状态"""
    
    def __init__(self, tracking_file: str = None, config_file: str = None):
        self.data_dir = DATA_DIR
        self.tracking_file = Path(tracking_file) if tracking_file else TRAINING_DIR / "data_tracking.json"
        self.config_file = Path(config_file) if config_file else TRAINING_DIR / "configs" / "performance_config.json"
        self.processed_files = {}
        self.new_files = set()
        self.max_scan_files = 10000  # 默认值
        self._load_performance_config()
        self._load_tracking_data()
    
    def _load_performance_config(self):
        """加载性能配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.max_scan_files = config.get('data_scanning', {}).get('max_files_per_scan', 10000)
                logger.info(f"✅ 加载性能配置: {self.config_file}")
            except Exception as e:
                logger.error(f"❌ 加载性能配置失败: {e}")
    
    def _load_tracking_data(self):
        """加载数据跟踪信息"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_files = {k: datetime.fromisoformat(v) for k, v in data.get('processed_files', {}).items()}
                logger.info(f"✅ 加载数据跟踪信息: {self.tracking_file}")
            except Exception as e:
                logger.error(f"❌ 加载数据跟踪信息失败: {e}")
    
    def _save_tracking_data(self):
        """保存数据跟踪信息"""
        try:
            data = {
                'processed_files': {k: v.isoformat() for k, v in self.processed_files.items()},
                'updated_at': datetime.now().isoformat()
            }
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存数据跟踪信息失败: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"❌ 计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def scan_for_new_data(self) -> List[Dict[str, Any]]:
        """扫描新增数据"""
        logger.info("🔍 开始扫描新增数据...")
        
        # 使用DataManager扫描数据，但限制文件数量
        data_manager = DataManager()
        data_catalog = data_manager.scan_data()
        
        # 如果文件数量过多，只处理最近修改的文件
        if len(data_catalog) > self.max_scan_files:
            logger.warning(f"⚠️  发现 {len(data_catalog)} 个文件，超过限制 {self.max_scan_files} 个，将只处理最近修改的文件")
            # 按修改时间排序，取最新的文件
            sorted_files = sorted(data_catalog.items(), key=lambda x: x[1]['modified_time'], reverse=True)
            data_catalog = dict(sorted_files[:self.max_scan_files])
        
        new_data_files = []
        processed_count = 0
        
        # 检查每个文件是否为新增或修改的
        for file_path, file_info in data_catalog.items():
            full_path = Path(file_info['path'])
            
            # 检查文件是否已处理
            file_hash = self._calculate_file_hash(full_path)
            if not file_hash:
                continue
                
            # 检查文件修改时间
            modified_time = datetime.fromtimestamp(file_info['modified_time'])
            
            # 如果文件未处理过或已修改，则标记为新增
            if file_hash not in self.processed_files or self.processed_files[file_hash] < modified_time:
                new_data_files.append({
                    'path': str(full_path),
                    'relative_path': file_path,
                    'hash': file_hash,
                    'modified_time': modified_time.isoformat(),
                    'size': file_info['size'],
                    'type': file_info['type']
                })
                logger.debug(f"   发现新增/修改文件: {file_path}")
            
            processed_count += 1
            # 每处理1000个文件输出一次进度
            if processed_count % 1000 == 0:
                logger.info(f"   已处理 {processed_count} 个文件...")
        
        logger.info(f"✅ 扫描完成，发现 {len(new_data_files)} 个新增/修改文件 (总共检查 {processed_count} 个文件)")
        return new_data_files
    
    def mark_as_processed(self, file_hash: str):
        """标记文件为已处理"""
        self.processed_files[file_hash] = datetime.now()
        self._save_tracking_data()
        logger.debug(f"✅ 标记文件为已处理: {file_hash}")


class ModelManager:
    """模型管理器，负责模型版本管理和增量更新"""
    
    def __init__(self, models_dir: str = None):
        self.models_dir = Path(models_dir) if models_dir else MODELS_DIR
        self.model_versions = {}
        self._load_model_versions()
    
    def _load_model_versions(self):
        """加载模型版本信息"""
        version_file = self.models_dir / "model_versions.json"
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    self.model_versions = json.load(f)
                logger.info(f"✅ 加载模型版本信息: {version_file}")
            except Exception as e:
                logger.error(f"❌ 加载模型版本信息失败: {e}")
    
    def _save_model_versions(self):
        """保存模型版本信息"""
        try:
            version_file = self.models_dir / "model_versions.json"
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_versions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存模型版本信息失败: {e}")
    
    def get_latest_model(self, model_name: str) -> Optional[Path]:
        """获取最新版本的模型"""
        if model_name in self.model_versions:
            latest_version = self.model_versions[model_name].get('latest')
            if latest_version:
                model_path = self.models_dir / latest_version
                if model_path.exists():
                    return model_path
        return None
    
    def save_incremental_model(self, model_name: str, model_path: Path, metrics: Dict[str, Any]):
        """保存增量更新的模型"""
        # 生成版本号
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_name = f"{model_name}_v{timestamp}.pth"
        version_path = self.models_dir / version_name
        
        try:
            # 复制模型文件
            import shutil
            shutil.copy2(model_path, version_path)
            
            # 更新版本信息
            if model_name not in self.model_versions:
                self.model_versions[model_name] = {
                    'versions': [],
                    'latest': version_name,
                    'created_at': datetime.now().isoformat()
                }
            
            self.model_versions[model_name]['versions'].append({
                'version': version_name,
                'path': str(version_path),
                'created_at': datetime.now().isoformat(),
                'metrics': metrics
            })
            self.model_versions[model_name]['latest'] = version_name
            self.model_versions[model_name]['updated_at'] = datetime.now().isoformat()
            
            # 保存版本信息
            self._save_model_versions()
            
            logger.info(f"✅ 保存增量模型: {version_name}")
            return version_path
        except Exception as e:
            logger.error(f"❌ 保存增量模型失败: {e}")
            return None
    
    def cleanup_old_models(self, model_name: str, keep_versions: int = 5):
        """清理旧版本模型"""
        if model_name in self.model_versions:
            versions = self.model_versions[model_name].get('versions', [])
            if len(versions) > keep_versions:
                # 按创建时间排序，保留最新的几个版本
                versions.sort(key=lambda x: x['created_at'], reverse=True)
                old_versions = versions[keep_versions:]
                
                # 删除旧版本文件
                for version_info in old_versions:
                    version_path = Path(version_info['path'])
                    if version_path.exists():
                        try:
                            version_path.unlink()
                            logger.info(f"🗑️  删除旧版本模型: {version_path.name}")
                        except Exception as e:
                            logger.error(f"❌ 删除旧版本模型失败 {version_path.name}: {e}")
                
                # 更新版本列表
                self.model_versions[model_name]['versions'] = versions[:keep_versions]
                self._save_model_versions()
    
    def auto_cleanup_models(self, keep_versions: int = 5):
        """自动清理所有模型的旧版本"""
        for model_name in self.model_versions.keys():
            self.cleanup_old_models(model_name, keep_versions)
        logger.info(f"✅ 自动清理完成，每个模型保留最新 {keep_versions} 个版本")


class TrainingScheduler:
    """训练调度器，负责训练任务的调度和执行"""
    
    def __init__(self):
        self.pending_tasks = []
        self.is_idle = True
        self.idle_threshold = 0.3  # CPU使用率阈值
        self.idle_duration = 0
        self.idle_check_interval = 60  # 检查间隔（秒）
        self.min_idle_duration = 300  # 最小空闲持续时间（秒）
        self.failed_tasks = []  # 存储失败的任务
        self.max_retry_attempts = 3  # 最大重试次数
        self.resource_manager = None  # 资源管理器
        self._init_resource_manager()
    
    def _init_resource_manager(self):
        """初始化资源管理器"""
        try:
            from training.resource_manager import ResourceManager
            self.resource_manager = ResourceManager()
            logger.info("✅ 资源管理器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  资源管理器初始化失败: {e}")
    
    def is_system_idle(self) -> bool:
        """检查系统是否空闲"""
        try:
            import psutil
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent < self.idle_threshold * 100
        except ImportError:
            # 如果没有psutil，使用简化的方法
            logger.warning("⚠️  无法检测系统资源使用情况，假设系统空闲")
            return True
        except Exception as e:
            logger.error(f"❌ 检查系统空闲状态时出错: {e}")
            return False
    
    def _get_available_resources(self) -> Dict[str, Any]:
        """获取可用系统资源"""
        if self.resource_manager:
            try:
                return self.resource_manager.get_system_resources()
            except Exception as e:
                logger.error(f"❌ 获取系统资源信息失败: {e}")
        
        # 默认资源信息
        return {
            'cpu_percent': 0,
            'memory_available': 0,
            'memory_total': 0,
            'gpu_available': False,
            'disk_space_available': 0
        }
    
    def _can_execute_task(self, task: Dict[str, Any]) -> bool:
        """检查是否有足够资源执行任务"""
        resources = self._get_available_resources()
        
        # 检查CPU使用率
        if resources['cpu_percent'] > 80:
            logger.debug("💻 CPU使用率过高，暂不执行任务")
            return False
        
        # 检查内存
        if resources['memory_available'] < 1024 * 1024 * 1024:  # 少于1GB可用内存
            logger.debug("💾 内存不足，暂不执行任务")
            return False
        
        # 对于需要GPU的任务，检查GPU可用性
        model_name = task.get('model_name', '')
        if model_name in ['vision_service', 'audio_service'] and not resources['gpu_available']:
            logger.debug("🎮 GPU不可用，暂不执行需要GPU的任务")
            return False
        
        return True
    
    def schedule_training(self, task: Dict[str, Any]):
        """调度训练任务"""
        # 初始化任务属性
        if 'retry_count' not in task:
            task['retry_count'] = 0
        if 'status' not in task:
            task['status'] = 'scheduled'
            
        self.pending_tasks.append(task)
        logger.info(f"📅 调度训练任务: {task.get('model_name', 'unknown')} (ID: {task.get('task_id', 'unknown')})")
    
    def execute_when_idle(self):
        """在系统空闲时执行训练任务"""
        if not self.pending_tasks:
            return
        
        # 检查系统是否空闲
        if self.is_system_idle():
            self.idle_duration += self.idle_check_interval
            logger.debug(f"🕒 系统空闲持续时间: {self.idle_duration}秒")
            
            # 如果空闲时间足够长，执行训练任务
            if self.idle_duration >= self.min_idle_duration:
                task = self.pending_tasks.pop(0)
                logger.info(f"🚀 系统空闲，开始执行训练任务: {task.get('model_name', 'unknown')} (ID: {task.get('task_id', 'unknown')})")
                
                # 检查资源是否足够执行任务
                if not self._can_execute_task(task):
                    logger.warning(f"⚠️  系统资源不足，推迟执行任务: {task.get('model_name', 'unknown')}")
                    # 将任务重新放回队列
                    self.pending_tasks.insert(0, task)
                    self.idle_duration = 0  # 重置空闲时间
                    return
                
                # 执行训练任务
                success = self._execute_training_task(task)
                
                # 如果任务失败且重试次数未达到上限，则重新调度
                if not success:
                    task['retry_count'] += 1
                    if task['retry_count'] < self.max_retry_attempts:
                        logger.warning(f"⚠️  训练任务失败，将在下次重试: {task.get('model_name', 'unknown')} (重试次数: {task['retry_count']})")
                        self.pending_tasks.append(task)
                    else:
                        logger.error(f"❌ 训练任务失败且达到最大重试次数: {task.get('model_name', 'unknown')}")
                        self.failed_tasks.append(task)
                
                # 重置空闲时间
                self.idle_duration = 0
        else:
            # 系统忙碌，重置空闲时间
            self.idle_duration = 0
            logger.debug("💻 系统忙碌，等待空闲...")
    
    def _execute_training_task(self, task: Dict[str, Any]) -> bool:
        """执行训练任务"""
        try:
            model_name = task.get('model_name')
            data_files = task.get('data_files', [])
            
            logger.info(f"🏋️  开始增量训练模型: {model_name}")
            
            # 更新任务状态
            task['status'] = 'running'
            task['started_time'] = datetime.now().isoformat()
            
            # 初始化模型训练器
            model_trainer = ModelTrainer()
            
            # 根据模型类型执行相应的训练
            if model_name == 'concept_models':
                success = model_trainer.train_with_preset('concept_models_training')
            elif model_name == 'vision_service':
                success = model_trainer.train_with_preset('vision_focus')
            elif model_name == 'audio_service':
                success = model_trainer.train_with_preset('audio_focus')
            else:
                # 默认使用快速训练
                success = model_trainer.train_with_preset('quick_start')
            
            if success:
                logger.info(f"✅ 增量训练完成: {model_name}")
                # 更新任务状态
                task['status'] = 'completed'
                task['completed_time'] = datetime.now().isoformat()
                return True
            else:
                logger.error(f"❌ 增量训练失败: {model_name}")
                task['status'] = 'failed'
                task['error'] = 'Training failed'
                return False
                
        except Exception as e:
            logger.error(f"❌ 执行训练任务时出错: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            return False
    
    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """获取失败的任务列表"""
        return self.failed_tasks.copy()
    
    def retry_failed_tasks(self):
        """重试失败的任务"""
        if self.failed_tasks:
            logger.info(f"🔄 重试 {len(self.failed_tasks)} 个失败的任务")
            for task in self.failed_tasks:
                task['retry_count'] = 0  # 重置重试次数
                self.schedule_training(task)
            self.failed_tasks.clear()


class MemoryBuffer:
    """内存缓冲区，负责在非空闲时间存储待处理数据"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = []
        self.max_size = max_size
        self.buffer_file = TRAINING_DIR / "memory_buffer.json"
        self._load_buffer()
    
    def _load_buffer(self):
        """加载缓冲区数据"""
        if self.buffer_file.exists():
            try:
                with open(self.buffer_file, 'r', encoding='utf-8') as f:
                    self.buffer = json.load(f)
                logger.info(f"✅ 加载内存缓冲区数据: {self.buffer_file}")
            except Exception as e:
                logger.error(f"❌ 加载内存缓冲区数据失败: {e}")
    
    def _save_buffer(self):
        """保存缓冲区数据"""
        try:
            with open(self.buffer_file, 'w', encoding='utf-8') as f:
                json.dump(self.buffer, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存内存缓冲区数据失败: {e}")
    
    def add_data(self, data: Dict[str, Any]):
        """添加数据到缓冲区"""
        if len(self.buffer) >= self.max_size:
            # 如果缓冲区已满，移除最旧的数据
            self.buffer.pop(0)
        
        self.buffer.append(data)
        self._save_buffer()
        logger.debug(f"📦 添加数据到缓冲区，当前大小: {len(self.buffer)}")
    
    def get_buffered_data(self) -> List[Dict[str, Any]]:
        """获取缓冲区数据"""
        data = self.buffer.copy()
        self.buffer.clear()
        self._save_buffer()
        logger.info(f"📦 获取缓冲区数据，数量: {len(data)}")
        return data


class IncrementalLearningManager:
    """增量学习管理器，协调整个增量学习流程"""
    
    def __init__(self, config_file: str = None):
        self.config_file = Path(config_file) if config_file else TRAINING_DIR / "configs" / "performance_config.json"
        self.config = self._load_performance_config()
        
        self.data_tracker = DataTracker(config_file=str(self.config_file))
        self.model_manager = ModelManager()
        self.training_scheduler = TrainingScheduler()
        self.memory_buffer = MemoryBuffer()
        self.is_monitoring = False
        self.monitoring_thread = None
        self.monitoring_interval = self.config.get('data_scanning', {}).get('scan_interval_seconds', 300)  # 监控间隔（秒）
        self.auto_cleanup_enabled = self.config.get('model_management', {}).get('auto_cleanup_enabled', True)  # 自动清理开关
        self.auto_cleanup_interval = self.config.get('model_management', {}).get('auto_cleanup_interval_seconds', 3600)  # 自动清理间隔（秒）
        self.last_cleanup_time = time.time()  # 上次清理时间
        
        logger.info("🔄 增量学习管理器初始化完成")
    
    def _load_performance_config(self) -> Dict[str, Any]:
        """加载性能配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ 加载性能配置: {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"❌ 加载性能配置失败: {e}")
                return {}
        return {}
    
    def start_monitoring(self):
        """启动数据监控"""
        if self.is_monitoring:
            logger.warning("⚠️  数据监控已在运行中")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("👀 启动数据监控...")
    
    def stop_monitoring(self):
        """停止数据监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("✋ 停止数据监控")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 扫描新增数据
                new_data = self.data_tracker.scan_for_new_data()
                
                if new_data:
                    logger.info(f"🔍 发现 {len(new_data)} 个新增数据文件")
                    
                    # 检查系统是否空闲
                    if self.training_scheduler.is_system_idle():
                        # 系统空闲，直接处理数据
                        self._process_new_data(new_data)
                    else:
                        # 系统忙碌，将数据添加到缓冲区
                        for data_item in new_data:
                            self.memory_buffer.add_data(data_item)
                        logger.info(f"💾 系统忙碌，将 {len(new_data)} 个数据文件添加到缓冲区")
                
                # 检查缓冲区并尝试执行训练
                self._check_buffer_and_train()
                
                # 检查是否有待执行的训练任务
                self.training_scheduler.execute_when_idle()
                
                # 检查是否需要自动清理模型
                self._check_auto_cleanup()
                
                # 等待下次监控
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ 监控循环中发生错误: {e}")
                time.sleep(self.monitoring_interval)
    
    def _process_new_data(self, new_data: List[Dict[str, Any]]):
        """处理新增数据"""
        logger.info(f"📦 开始处理 {len(new_data)} 个新增数据文件")
        
        # 按模型类型分组数据
        data_by_model = defaultdict(list)
        for data_item in new_data:
            # 根据文件类型确定目标模型
            file_type = data_item['type']
            if file_type in ['image', 'document']:
                model_name = 'vision_service'
            elif file_type == 'audio':
                model_name = 'audio_service'
            elif file_type in ['text', 'json', 'code']:
                model_name = 'concept_models'
            else:
                model_name = 'concept_models'  # 默认模型
            
            data_by_model[model_name].append(data_item)
        
        # 为每种模型类型创建训练任务
        for model_name, data_files in data_by_model.items():
            task = {
                'task_id': f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.training_scheduler.pending_tasks)}",
                'model_name': model_name,
                'data_files': data_files,
                'status': 'scheduled',
                'scheduled_time': datetime.now().isoformat()
            }
            
            # 调度训练任务
            self.training_scheduler.schedule_training(task)
            logger.info(f"📅 为模型 {model_name} 调度训练任务，包含 {len(data_files)} 个数据文件")
            
            # 标记文件为已处理
            for data_item in data_files:
                self.data_tracker.mark_as_processed(data_item['hash'])
    
    def _check_buffer_and_train(self):
        """检查缓冲区并尝试执行训练"""
        buffered_data = self.memory_buffer.get_buffered_data()
        if buffered_data:
            logger.info(f"📦 从缓冲区获取 {len(buffered_data)} 个数据文件")
            self._process_new_data(buffered_data)
    
    def trigger_incremental_training(self):
        """立即触发增量训练"""
        logger.info("🚀 立即触发增量训练...")
        
        # 扫描新增数据
        new_data = self.data_tracker.scan_for_new_data()
        
        if new_data:
            self._process_new_data(new_data)
        else:
            logger.info("ℹ️  没有发现新增数据")
    
    def get_status(self) -> Dict[str, Any]:
        """获取增量学习状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'pending_tasks': len(self.training_scheduler.pending_tasks),
            'failed_tasks': len(self.training_scheduler.failed_tasks),
            'buffered_data': len(self.memory_buffer.buffer),
            'processed_files': len(self.data_tracker.processed_files),
            'model_versions': self.model_manager.model_versions,
            'auto_cleanup_enabled': self.auto_cleanup_enabled
        }
    
    def _check_auto_cleanup(self):
        """检查并执行自动模型清理"""
        if self.auto_cleanup_enabled and time.time() - self.last_cleanup_time > self.auto_cleanup_interval:
            logger.info("🧹 执行自动模型清理...")
            self.model_manager.auto_cleanup_models()
            self.last_cleanup_time = time.time()
    
    def enable_auto_cleanup(self, enabled: bool = True):
        """启用或禁用自动模型清理"""
        self.auto_cleanup_enabled = enabled
        logger.info(f"{'✅ 启用' if enabled else '❌ 禁用'} 自动模型清理")
    
    def manual_cleanup_models(self, keep_versions: int = 5):
        """手动清理模型"""
        logger.info(f"🧹 手动清理模型，每个模型保留最新 {keep_versions} 个版本...")
        self.model_manager.auto_cleanup_models(keep_versions)
        self.last_cleanup_time = time.time()


def main():
    """主函数"""
    logger.info("🤖 Unified AI Project 增量学习系统")
    logger.info("=" * 50)
    
    # 创建增量学习管理器
    incremental_learner = IncrementalLearningManager()
    
    # 启动监控
    incremental_learner.start_monitoring()
    
    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⏹️  收到停止信号")
        incremental_learner.stop_monitoring()
        logger.info("👋 增量学习系统已停止")


if __name__ == "__main__":
    main()