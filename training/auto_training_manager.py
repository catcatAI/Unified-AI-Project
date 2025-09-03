#!/usr/bin/env python3
"""
自动训练管理器
实现自动识别训练数据、自动建立训练和自动训练的功能
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

# 导入数据管理器
from training.data_manager import DataManager
from training.collaborative_training_manager import CollaborativeTrainingManager

# 延迟导入ModelTrainer以避免循环导入
ModelTrainer = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(TRAINING_DIR / 'auto_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrainingMonitor:
    """训练监控器，用于监控训练过程的进度和性能"""
    
    def __init__(self):
        self.training_progress = defaultdict(dict)
        self.training_metrics = defaultdict(list)
        self.training_logs = defaultdict(list)
        self.lock = threading.Lock()
        
    def update_progress(self, scenario_name: str, epoch: int, progress: float, metrics: Dict[str, Any]):
        """更新训练进度"""
        with self.lock:
            self.training_progress[scenario_name] = {
                'epoch': epoch,
                'progress': progress,
                'metrics': metrics,
                'updated_at': datetime.now().isoformat()
            }
            self.training_metrics[scenario_name].append({
                'epoch': epoch,
                'progress': progress,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            })
    
    def log_event(self, scenario_name: str, event_type: str, message: str, details: Dict[str, Any] = None):
        """记录训练事件"""
        with self.lock:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'message': message,
                'details': details or {}
            }
            self.training_logs[scenario_name].append(log_entry)
            # 同时打印到控制台
            logger.info(f"[{scenario_name}] {event_type}: {message}")
    
    def get_progress(self, scenario_name: str) -> Dict[str, Any]:
        """获取训练进度"""
        with self.lock:
            return self.training_progress.get(scenario_name, {})
    
    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """获取所有训练进度"""
        with self.lock:
            return dict(self.training_progress)
    
    def get_logs(self, scenario_name: str = None) -> Dict[str, List]:
        """获取训练日志"""
        with self.lock:
            if scenario_name:
                return {scenario_name: self.training_logs.get(scenario_name, [])}
            return dict(self.training_logs)
    
    def reset(self):
        """重置监控器"""
        with self.lock:
            self.training_progress.clear()
            self.training_metrics.clear()
            self.training_logs.clear()

class AutoTrainingManager:
    """自动训练管理器，实现自动识别训练数据、自动建立训练和自动训练的功能"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.training_dir = TRAINING_DIR
        self.data_dir = DATA_DIR
        self.models_dir = MODELS_DIR
        self.data_manager = DataManager()
        # 延迟导入ModelTrainer以避免循环导入
        global ModelTrainer
        if ModelTrainer is None:
            from training.train_model import ModelTrainer
        self.model_trainer = ModelTrainer()
        self.collaborative_manager = CollaborativeTrainingManager()
        self.training_monitor = TrainingMonitor()
        
        # 确保必要的目录存在
        self._ensure_directories()
        
        logger.info("🔄 自动训练管理器初始化完成")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.models_dir,
            self.training_dir / "checkpoints",
            self.training_dir / "reports",
            self.training_dir / "configs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def auto_identify_training_data(self) -> Dict[str, Any]:
        """
        自动识别训练数据
        返回数据分类和统计信息
        """
        logger.info("🔍 开始自动识别训练数据...")
        
        # 扫描数据
        data_catalog = self.data_manager.scan_data()
        
        # 分析数据类型分布
        data_stats = {}
        for file_info in data_catalog.values():
            data_type = file_info['type']
            if data_type not in data_stats:
                data_stats[data_type] = {
                    'count': 0,
                    'total_size': 0,
                    'files': []
                }
            data_stats[data_type]['count'] += 1
            data_stats[data_type]['total_size'] += file_info['size']
            data_stats[data_type]['files'].append(file_info)
        
        # 评估数据质量
        logger.info("📊 评估数据质量...")
        for file_path in data_catalog.keys():
            self.data_manager.assess_data_quality(file_path)
        
        # 获取高质量数据
        high_quality_data = self.data_manager.get_high_quality_data()
        
        result = {
            'data_catalog': data_catalog,
            'data_stats': data_stats,
            'high_quality_data': high_quality_data,
            'total_files': len(data_catalog),
            'scan_time': datetime.now().isoformat()
        }
        
        logger.info(f"✅ 数据识别完成，共发现 {len(data_catalog)} 个文件")
        return result
    
    def auto_create_training_config(self, data_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据识别的数据自动创建训练配置
        """
        logger.info("⚙️  开始自动创建训练配置...")
        
        # 分析可用的数据类型和质量
        available_data_types = list(data_analysis['data_stats'].keys())
        logger.info(f"📋 可用数据类型: {available_data_types}")
        
        # 获取高质量数据信息
        high_quality_data = data_analysis.get('high_quality_data', {})
        
        # 根据数据类型和质量确定训练场景
        training_scenarios = []
        
        # 检查视觉数据
        if 'image' in available_data_types or 'document' in available_data_types:
            # 检查高质量视觉数据数量
            vision_data_count = 0
            if 'image' in high_quality_data:
                vision_data_count += len(high_quality_data['image'])
            if 'document' in high_quality_data:
                vision_data_count += len(high_quality_data['document'])
            
            if vision_data_count > 100:
                training_scenarios.append('vision_focus')
            elif vision_data_count > 50:
                training_scenarios.append('comprehensive_training')
            elif vision_data_count > 10:
                training_scenarios.append('quick_start')
            
        # 检查音频数据
        if 'audio' in available_data_types:
            # 检查高质量音频数据数量
            audio_data_count = len(high_quality_data.get('audio', []))
            
            if audio_data_count > 50:
                training_scenarios.append('audio_focus')
            elif audio_data_count > 20:
                training_scenarios.append('comprehensive_training')
            elif audio_data_count > 5:
                training_scenarios.append('quick_start')
            
        # 检查文本数据
        if 'text' in available_data_types:
            # 检查高质量文本数据数量
            text_data_count = len(high_quality_data.get('text', []))
            
            if text_data_count > 200:
                training_scenarios.extend(['math_model_training', 'logic_model_training', 'comprehensive_training', 'causal_reasoning_training'])
            elif text_data_count > 100:
                training_scenarios.extend(['math_model_training', 'logic_model_training', 'comprehensive_training'])
            elif text_data_count > 50:
                training_scenarios.extend(['math_model_training', 'logic_model_training'])
            elif text_data_count > 10:
                training_scenarios.append('quick_start')
            
        # 检查代码数据
        if 'code' in available_data_types:
            code_data_count = len(high_quality_data.get('code', []))
            
            if code_data_count > 100:
                training_scenarios.extend(['code_model_training', 'comprehensive_training'])
            elif code_data_count > 50:
                training_scenarios.append('code_model_training')
            elif code_data_count > 10:
                training_scenarios.append('quick_start')
            
        # 检查概念模型相关数据
        if 'json' in available_data_types:
            json_data_count = len(high_quality_data.get('json', []))
            
            if json_data_count > 50:
                training_scenarios.extend(['concept_models_training', 'environment_simulator_training', 'causal_reasoning_training'])
            elif json_data_count > 30:
                training_scenarios.append('concept_models_training')
            elif json_data_count > 10:
                training_scenarios.append('quick_start')
            
        # 检查模型数据
        if 'model' in available_data_types:
            model_data_count = len(high_quality_data.get('model', []))
            
            if model_data_count > 10:
                training_scenarios.append('collaborative_training')
            
        # 检查数据文件
        if 'data' in available_data_types:
            data_file_count = len(high_quality_data.get('data', []))
            
            if data_file_count > 50:
                training_scenarios.append('data_analysis_model_training')
            elif data_file_count > 10:
                training_scenarios.append('quick_start')
                
        # 如果有多种高质量数据类型，使用综合训练
        high_quality_types = [t for t in high_quality_data.keys() if len(high_quality_data[t]) > 10]
        if len(high_quality_types) > 3:
            training_scenarios.append('comprehensive_training')
        elif len(high_quality_types) > 2:
            training_scenarios.append('full_dataset_training')
            
        # 根据数据量选择训练场景
        total_files = data_analysis['total_files']
        high_quality_file_count = sum(len(files) for files in high_quality_data.values())
        
        # 如果高质量数据充足，使用完整数据集训练
        if high_quality_file_count > 1000:
            training_scenarios.append('full_dataset_training')
        elif high_quality_file_count > 500:
            training_scenarios.append('comprehensive_training')
        elif high_quality_file_count > 100:
            training_scenarios.append('quick_start')
        elif high_quality_file_count > 20:
            training_scenarios.append('quick_start')
        else:
            # 如果数据较少，使用快速训练
            training_scenarios.append('quick_start')
            
        # 去重并排序训练场景
        training_scenarios = sorted(list(set(training_scenarios)))
        
        # 如果没有推荐的场景，使用默认场景
        if not training_scenarios:
            training_scenarios = ['quick_start']
            
        # 智能调整训练参数
        training_params = self._optimize_training_parameters(data_analysis, training_scenarios)
            
        # 创建训练配置
        training_config = {
            'selected_scenarios': training_scenarios,
            'data_mapping': self._map_data_to_models(available_data_types),
            'resource_requirements': self._estimate_resource_requirements(data_analysis),
            'estimated_training_time': self._estimate_training_time(data_analysis),
            'training_params': training_params,  # 新增优化的训练参数
            'data_quality_info': {
                'total_files': total_files,
                'high_quality_files': high_quality_file_count,
                'quality_ratio': high_quality_file_count / total_files if total_files > 0 else 0
            },
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ 训练配置创建完成，推荐训练场景: {training_scenarios}")
        return training_config
    
    def _map_data_to_models(self, data_types: List[str]) -> Dict[str, List[str]]:
        """将数据类型映射到模型"""
        model_mapping = {}
        
        if 'image' in data_types or 'document' in data_types:
            model_mapping['vision_service'] = ['image', 'document']
            
        if 'audio' in data_types:
            model_mapping['audio_service'] = ['audio']
            
        if 'text' in data_types:
            model_mapping['causal_reasoning_engine'] = ['text']
            model_mapping['math_model'] = ['text']
            model_mapping['logic_model'] = ['text']
            
        if 'json' in data_types:
            model_mapping['concept_models'] = ['text', 'json']
            model_mapping['environment_simulator'] = ['text', 'json']
            model_mapping['adaptive_learning_controller'] = ['text', 'json']
            model_mapping['alpha_deep_model'] = ['text', 'json']
            
        if 'code' in data_types:
            model_mapping['code_model'] = ['code']
            
        if 'data' in data_types:
            model_mapping['data_analysis_model'] = ['data', 'text']
            
        # 多模态服务
        if len(data_types) > 2:
            model_mapping['multimodal_service'] = data_types
            
        return model_mapping
    
    def _estimate_resource_requirements(self, data_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """估算资源需求"""
        total_files = data_analysis['total_files']
        total_size = sum(stat['total_size'] for stat in data_analysis['data_stats'].values())
        
        # 获取高质量数据信息
        high_quality_data = data_analysis.get('high_quality_data', {})
        high_quality_size = sum(
            sum(file_info['size'] for file_info in files)
            for files in high_quality_data.values()
        )
        
        # 基于数据量和质量估算资源需求
        effective_files = len([file for files in high_quality_data.values() for file in files])
        effective_size = high_quality_size if high_quality_size > 0 else total_size
        
        if effective_files > 5000 or effective_size > 5 * 1024 * 1024 * 1024:  # 5GB高质量数据
            cpu_cores = 8
            memory_gb = 16
            gpu_memory_gb = 8
        elif effective_files > 1000 or effective_size > 1 * 1024 * 1024 * 1024:  # 1GB高质量数据
            cpu_cores = 4
            memory_gb = 8
            gpu_memory_gb = 4
        elif effective_files > 100 or effective_size > 100 * 1024 * 1024:  # 100MB高质量数据
            cpu_cores = 2
            memory_gb = 4
            gpu_memory_gb = 2
        else:
            cpu_cores = 2
            memory_gb = 4
            gpu_memory_gb = 0  # 不需要GPU
            
        return {
            'cpu_cores': cpu_cores,
            'memory_gb': memory_gb,
            'gpu_memory_gb': gpu_memory_gb,
            'estimated_disk_space_gb': (effective_size * 3) / (1024 * 1024 * 1024),  # 估算需要3倍空间
            'data_quality_info': {
                'total_files': total_files,
                'high_quality_files': effective_files,
                'total_size_gb': total_size / (1024 * 1024 * 1024),
                'high_quality_size_gb': effective_size / (1024 * 1024 * 1024)
            }
        }
    
    def _estimate_training_time(self, data_analysis: Dict[str, Any]) -> Dict[str, float]:
        """估算训练时间"""
        total_files = data_analysis['total_files']
        
        # 获取高质量数据信息
        high_quality_data = data_analysis.get('high_quality_data', {})
        high_quality_files = sum(len(files) for files in high_quality_data.values())
        
        # 基于高质量数据量估算训练时间（小时）
        effective_files = high_quality_files if high_quality_files > 0 else total_files
        
        if effective_files > 5000:
            quick_train = 2.0
            comprehensive_train = 48.0
            full_train = 240.0
        elif effective_files > 1000:
            quick_train = 1.0
            comprehensive_train = 24.0
            full_train = 120.0
        elif effective_files > 100:
            quick_train = 0.5
            comprehensive_train = 8.0
            full_train = 48.0
        elif effective_files > 20:
            quick_train = 0.2
            comprehensive_train = 2.0
            full_train = 12.0
        else:
            quick_train = 0.1
            comprehensive_train = 0.5
            full_train = 2.0
            
        # 考虑GPU可用性调整训练时间
        try:
            import tensorflow as tf
            gpu_available = len(tf.config.list_physical_devices('GPU')) > 0
            if gpu_available:
                # GPU加速，训练时间减半
                quick_train *= 0.5
                comprehensive_train *= 0.5
                full_train *= 0.5
        except ImportError:
            pass  # TensorFlow不可用，使用CPU训练时间
        
        return {
            'quick_start': quick_train,
            'comprehensive_training': comprehensive_train,
            'full_dataset_training': full_train,
            'data_quality_info': {
                'total_files': total_files,
                'high_quality_files': high_quality_files,
                'quality_ratio': high_quality_files / total_files if total_files > 0 else 0
            }
        }
    
    def _optimize_training_parameters(self, data_analysis: Dict[str, Any], training_scenarios: List[str]) -> Dict[str, Any]:
        """
        根据数据特征优化训练参数
        """
        # 获取高质量数据信息
        high_quality_data = data_analysis.get('high_quality_data', {})
        high_quality_files = sum(len(files) for files in high_quality_data.values())
        
        # 基于数据量调整批次大小
        if high_quality_files > 1000:
            batch_size = 64
        elif high_quality_files > 500:
            batch_size = 32
        elif high_quality_files > 100:
            batch_size = 16
        else:
            batch_size = 8
            
        # 基于数据复杂度调整学习率
        # 简单估算数据复杂度（基于文件类型多样性）
        data_types_count = len(data_analysis.get('data_stats', {}))
        if data_types_count > 5:
            learning_rate = 0.0005  # 复杂数据使用较小学习率
        elif data_types_count > 3:
            learning_rate = 0.001
        else:
            learning_rate = 0.002  # 简单数据可以使用较大学习率
            
        # 基于训练场景调整训练轮数
        if 'full_dataset_training' in training_scenarios:
            epochs = 100
        elif 'comprehensive_training' in training_scenarios:
            epochs = 50
        elif 'quick_start' in training_scenarios:
            epochs = 10
        else:
            epochs = 30
            
        # 检查GPU可用性
        try:
            import tensorflow as tf
            gpu_available = len(tf.config.list_physical_devices('GPU')) > 0
        except ImportError:
            gpu_available = False
            
        # 根据GPU可用性调整参数
        if gpu_available:
            # GPU可用时可以使用更大的批次大小
            batch_size = min(batch_size * 2, 128)
            # GPU训练可以使用更多的训练轮数
            epochs = int(epochs * 1.2)
            
        return {
            'batch_size': batch_size,
            'learning_rate': learning_rate,
            'epochs': epochs,
            'gpu_available': gpu_available,
            'optimized_at': datetime.now().isoformat()
        }
    
    def auto_train(self, training_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据训练配置自动执行训练
        """
        logger.info("🚀 开始自动训练...")
        
        # 重置训练监控器
        self.training_monitor.reset()
        
        results = {}
        
        # 获取推荐的训练场景
        scenarios = training_config.get('selected_scenarios', ['quick_start'])
        
        # 获取数据映射信息
        data_mapping = training_config.get('data_mapping', {})
        
        # 获取优化的训练参数
        training_params = training_config.get('training_params', {})
        
        for scenario_name in scenarios:
            logger.info(f"🏋️  开始训练场景: {scenario_name}")
            
            try:
                # 根据场景类型执行不同的训练策略
                if scenario_name in ['code_model_training', 'data_analysis_model_training']:
                    # 对于代码模型和数据分析模型，使用真实训练
                    success = self._train_real_model(scenario_name, data_mapping)
                elif scenario_name in ['environment_simulator_training', 'causal_reasoning_training', 
                                     'adaptive_learning_training', 'alpha_deep_model_training']:
                    # 对于概念模型的特定训练，使用专门的训练方法
                    success = self._train_concept_model(scenario_name)
                elif scenario_name in ['math_model_training', 'logic_model_training']:
                    # 对于数学和逻辑模型，使用真实训练
                    success = self._train_math_logic_model(scenario_name)
                elif scenario_name == 'collaborative_training':
                    # 协作式训练
                    success = self._train_collaborative_model(training_params)
                else:
                    # 使用默认训练方法
                    success = self.model_trainer.train_with_preset(scenario_name)
                
                # 记录结果
                results[scenario_name] = {
                    'success': success,
                    'completed_at': datetime.now().isoformat(),
                    'model_path': str(self.models_dir),
                    'scenario_type': scenario_name,
                    'training_progress': self.training_monitor.get_progress(scenario_name)
                }
                
                if success:
                    logger.info(f"✅ 训练场景 {scenario_name} 完成")
                else:
                    logger.error(f"❌ 训练场景 {scenario_name} 失败")
                    
            except Exception as e:
                logger.error(f"❌ 训练场景 {scenario_name} 执行出错: {e}")
                results[scenario_name] = {
                    'success': False,
                    'error': str(e),
                    'completed_at': datetime.now().isoformat(),
                    'scenario_type': scenario_name,
                    'training_progress': self.training_monitor.get_progress(scenario_name)
                }
        
        # 执行协作式训练（如果有多个模型）
        if len(scenarios) > 1:
            logger.info("🔄 开始协作式训练...")
            try:
                collaborative_success = self.collaborative_manager.start_collaborative_training({
                    'target_models': list(training_config.get('data_mapping', {}).keys())
                })
                results['collaborative_training'] = {
                    'success': collaborative_success,
                    'completed_at': datetime.now().isoformat(),
                    'training_progress': self.training_monitor.get_progress('collaborative_training')
                }
                if collaborative_success:
                    logger.info("✅ 协作式训练完成")
                else:
                    logger.error("❌ 协作式训练失败")
            except Exception as e:
                logger.error(f"❌ 协作式训练执行出错: {e}")
                results['collaborative_training'] = {
                    'success': False,
                    'error': str(e),
                    'completed_at': datetime.now().isoformat(),
                    'training_progress': self.training_monitor.get_progress('collaborative_training')
                }
        
        logger.info("🏁 自动训练流程完成")
        return results
    
    def _train_real_model(self, scenario_name: str, data_mapping: Dict[str, list]) -> bool:
        """
        训练真实模型（代码模型、数据分析模型等）
        """
        logger.info(f"🔬 开始真实模型训练: {scenario_name}")
        
        try:
            # 根据场景名称确定目标模型
            target_model = None
            if scenario_name == 'code_model_training':
                target_model = 'code_model'
            elif scenario_name == 'data_analysis_model_training':
                target_model = 'data_analysis_model'
            
            if target_model:
                # 准备训练数据
                training_data = self.data_manager.prepare_training_data(target_model)
                logger.info(f"📦 为 {target_model} 准备了 {len(training_data)} 个训练文件")
                
                # 执行真实训练
                success = self.model_trainer.train_with_preset(scenario_name)
                return success
            else:
                # 如果无法确定目标模型，使用默认训练方法
                return self.model_trainer.train_with_preset(scenario_name)
                
        except Exception as e:
            logger.error(f"❌ 真实模型训练失败: {e}")
            return False
    
    def _train_concept_model(self, scenario_name: str) -> bool:
        """
        训练概念模型的特定场景
        """
        logger.info(f"🧠 开始概念模型训练: {scenario_name}")
        
        try:
            # 执行概念模型训练
            success = self.model_trainer.train_with_preset(scenario_name)
            return success
        except Exception as e:
            logger.error(f"❌ 概念模型训练失败: {e}")
            return False
    
    def _train_math_logic_model(self, scenario_name: str) -> bool:
        """
        训练数学和逻辑模型
        """
        logger.info(f"🧮 开始数学/逻辑模型训练: {scenario_name}")
        
        try:
            # 执行数学/逻辑模型训练
            success = self.model_trainer.train_with_preset(scenario_name)
            return success
        except Exception as e:
            logger.error(f"❌ 数学/逻辑模型训练失败: {e}")
            return False
    
    def _train_collaborative_model(self, training_params: Dict[str, Any]) -> bool:
        """
        执行协作式训练
        """
        logger.info("🔄 开始协作式训练...")
        
        try:
            # 使用优化的参数执行协作式训练
            success = self.collaborative_manager.start_collaborative_training({
                'epochs': training_params.get('epochs', 10),
                'batch_size': training_params.get('batch_size', 16),
                'learning_rate': training_params.get('learning_rate', 0.001)
            })
            return success
        except Exception as e:
            logger.error(f"❌ 协作式训练失败: {e}")
            return False
    
    def run_full_auto_training_pipeline(self) -> Dict[str, Any]:
        """
        运行完整的自动训练流水线
        1. 自动识别训练数据
        2. 自动创建训练配置
        3. 自动执行训练
        """
        logger.info("🚀 启动完整的自动训练流水线...")
        
        # 步骤1: 自动识别训练数据
        data_analysis = self.auto_identify_training_data()
        
        # 步骤2: 自动创建训练配置
        training_config = self.auto_create_training_config(data_analysis)
        
        # 步骤3: 自动执行训练
        training_results = self.auto_train(training_config)
        
        # 步骤4: 分析训练结果
        result_analysis = self._analyze_training_results(training_results)
        
        # 生成报告
        report = {
            'pipeline_completed_at': datetime.now().isoformat(),
            'data_analysis': data_analysis,
            'training_config': training_config,
            'training_results': training_results,
            'result_analysis': result_analysis,
            'summary': {
                'total_scenarios': len(training_config.get('selected_scenarios', [])),
                'successful_scenarios': len([r for r in training_results.values() if r.get('success', False)]),
                'failed_scenarios': len([r for r in training_results.values() if not r.get('success', True)]),
                'overall_success_rate': result_analysis.get('overall_success_rate', 0)
            }
        }
        
        # 保存报告
        report_path = self.training_dir / "reports" / f"auto_training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成详细报告
        detailed_report_path = self._generate_detailed_report(report)
        
        logger.info(f"✅ 自动训练流水线完成，报告已保存至: {report_path}")
        if detailed_report_path:
            logger.info(f"📋 详细报告已保存至: {detailed_report_path}")
        
        return report
    
    def _analyze_training_results(self, training_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析训练结果
        """
        logger.info("🔍 开始分析训练结果...")
        
        analysis = {
            'total_scenarios': len(training_results),
            'successful_scenarios': 0,
            'failed_scenarios': 0,
            'success_rate_by_type': {},
            'performance_metrics': {},
            'error_analysis': {},
            'model_performance': {}
        }
        
        # 分析每个场景的结果
        for scenario_name, result in training_results.items():
            if result.get('success', False):
                analysis['successful_scenarios'] += 1
            else:
                analysis['failed_scenarios'] += 1
                
            # 记录错误信息
            if 'error' in result:
                error_type = type(result['error']).__name__
                if error_type not in analysis['error_analysis']:
                    analysis['error_analysis'][error_type] = []
                analysis['error_analysis'][error_type].append({
                    'scenario': scenario_name,
                    'error': result['error']
                })
            
            # 分析模型性能
            if 'training_progress' in result:
                progress = result['training_progress']
                if progress and 'metrics' in progress:
                    metrics = progress['metrics']
                    analysis['model_performance'][scenario_name] = {
                        'final_loss': metrics.get('loss', 0),
                        'final_accuracy': metrics.get('accuracy', 0),
                        'training_completed': result.get('success', False)
                    }
        
        # 计算总体成功率
        if analysis['total_scenarios'] > 0:
            analysis['overall_success_rate'] = analysis['successful_scenarios'] / analysis['total_scenarios']
        
        # 分析性能指标（如果有的话）
        for scenario_name, result in training_results.items():
            if 'training_progress' in result:
                progress = result['training_progress']
                if progress and 'metrics' in progress:
                    metrics = progress['metrics']
                    analysis['performance_metrics'][scenario_name] = metrics
        
        # 分析最佳模型
        best_model = None
        best_accuracy = -1
        for model_name, performance in analysis['model_performance'].items():
            if performance['final_accuracy'] > best_accuracy:
                best_accuracy = performance['final_accuracy']
                best_model = model_name
        
        analysis['best_model'] = {
            'model_name': best_model,
            'accuracy': best_accuracy
        }
        
        logger.info(f"✅ 训练结果分析完成: {analysis['successful_scenarios']}/{analysis['total_scenarios']} 场景成功")
        return analysis
    
    def _generate_detailed_report(self, report: Dict[str, Any]) -> Optional[Path]:
        """
        生成详细的训练报告
        """
        try:
            # 创建详细的Markdown报告
            detailed_report = "# Unified AI Project 自动训练详细报告\n\n"
            
            # 基本信息
            detailed_report += f"## 基本信息\n"
            detailed_report += f"- 报告生成时间: {report.get('pipeline_completed_at', 'N/A')}\n"
            detailed_report += f"- 总训练场景数: {report.get('summary', {}).get('total_scenarios', 0)}\n"
            detailed_report += f"- 成功场景数: {report.get('summary', {}).get('successful_scenarios', 0)}\n"
            detailed_report += f"- 失败场景数: {report.get('summary', {}).get('failed_scenarios', 0)}\n"
            detailed_report += f"- 总体成功率: {report.get('summary', {}).get('overall_success_rate', 0):.2%}\n\n"
            
            # 数据分析
            data_analysis = report.get('data_analysis', {})
            detailed_report += f"## 数据分析\n"
            detailed_report += f"- 总文件数: {data_analysis.get('total_files', 0)}\n"
            
            data_stats = data_analysis.get('data_stats', {})
            detailed_report += f"- 数据类型分布:\n"
            for data_type, stats in data_stats.items():
                detailed_report += f"  - {data_type}: {stats.get('count', 0)} 个文件\n"
            
            # 训练配置
            training_config = report.get('training_config', {})
            detailed_report += f"\n## 训练配置\n"
            detailed_report += f"- 推荐训练场景: {', '.join(training_config.get('selected_scenarios', []))}\n"
            
            # 优化的训练参数
            training_params = training_config.get('training_params', {})
            if training_params:
                detailed_report += f"- 优化的训练参数:\n"
                detailed_report += f"  - 批次大小: {training_params.get('batch_size', 'N/A')}\n"
                detailed_report += f"  - 学习率: {training_params.get('learning_rate', 'N/A')}\n"
                detailed_report += f"  - 训练轮数: {training_params.get('epochs', 'N/A')}\n"
                detailed_report += f"  - GPU可用性: {'是' if training_params.get('gpu_available', False) else '否'}\n"
            
            # 模型性能分析
            result_analysis = report.get('result_analysis', {})
            model_performance = result_analysis.get('model_performance', {})
            if model_performance:
                detailed_report += f"\n## 模型性能分析\n"
                for model_name, performance in model_performance.items():
                    detailed_report += f"- {model_name}:\n"
                    detailed_report += f"  - 最终损失: {performance.get('final_loss', 'N/A'):.4f}\n"
                    detailed_report += f"  - 最终准确率: {performance.get('final_accuracy', 0):.2%}\n"
                    detailed_report += f"  - 训练完成: {'是' if performance.get('training_completed', False) else '否'}\n"
            
            # 最佳模型
            best_model = result_analysis.get('best_model', {})
            if best_model.get('model_name'):
                detailed_report += f"\n## 最佳模型\n"
                detailed_report += f"- 模型名称: {best_model.get('model_name', 'N/A')}\n"
                detailed_report += f"- 准确率: {best_model.get('accuracy', 0):.2%}\n"
            
            # 训练结果
            training_results = report.get('training_results', {})
            detailed_report += f"\n## 训练结果\n"
            for scenario_name, result in training_results.items():
                success = result.get('success', False)
                status = "✅ 成功" if success else "❌ 失败"
                detailed_report += f"- {scenario_name}: {status}\n"
                if 'error' in result:
                    detailed_report += f"  - 错误信息: {result['error']}\n"
            
            # 错误分析
            error_analysis = result_analysis.get('error_analysis', {})
            if error_analysis:
                detailed_report += f"\n## 错误分析\n"
                for error_type, errors in error_analysis.items():
                    detailed_report += f"- {error_type}:\n"
                    for error in errors:
                        detailed_report += f"  - 场景: {error['scenario']}, 错误: {error['error']}\n"
            
            # 保存详细报告
            detailed_report_path = self.training_dir / "reports" / f"detailed_auto_training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(detailed_report_path, 'w', encoding='utf-8') as f:
                f.write(detailed_report)
            
            return detailed_report_path
            
        except Exception as e:
            logger.error(f"❌ 生成详细报告时出错: {e}")
            return None

def main():
    """主函数"""
    logger.info("🤖 Unified AI Project 自动训练系统启动")
    
    # 创建自动训练管理器
    auto_trainer = AutoTrainingManager()
    
    # 运行完整的自动训练流水线
    report = auto_trainer.run_full_auto_training_pipeline()
    
    # 输出摘要
    summary = report.get('summary', {})
    logger.info("📋 训练摘要:")
    logger.info(f"   总训练场景数: {summary.get('total_scenarios', 0)}")
    logger.info(f"   成功场景数: {summary.get('successful_scenarios', 0)}")
    logger.info(f"   失败场景数: {summary.get('failed_scenarios', 0)}")
    
    logger.info("🏁 自动训练系统执行完成")

if __name__ == "__main__":
    main()