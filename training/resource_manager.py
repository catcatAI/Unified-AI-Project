#!/usr/bin/env python3
"""
资源管理器
负责管理计算资源（CPU、GPU、内存）并动态分配给不同模型
"""

import os
import logging
import psutil
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import json
from datetime import datetime

# 添加项目路径
import sys
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# 导入路径配置模块
try:
    from apps.backend.src.path_config import (
        PROJECT_ROOT, 
        DATA_DIR, 
        TRAINING_DIR, 
        get_data_path, 
        resolve_path
    )
except ImportError:
    # 如果路径配置模块不可用，使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR = PROJECT_ROOT / "data"
    TRAINING_DIR = PROJECT_ROOT / "training"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResourceManager:
    """资源管理器，负责管理计算资源并动态分配给不同模型"""
    
    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.physical_cpu_count = psutil.cpu_count(logical=False)
        self.total_memory = psutil.virtual_memory().total
        self.available_memory = psutil.virtual_memory().available
        self.gpu_info = self._detect_gpus()
        self.resource_allocation = {}  # 记录资源分配情况
        self.resource_usage_history = []  # 资源使用历史
        
        logger.info(f"🖥️  系统资源信息:")
        logger.info(f"   CPU核心数: {self.cpu_count} (物理核心: {self.physical_cpu_count})")
        logger.info(f"   总内存: {self.total_memory / (1024**3):.2f} GB")
        logger.info(f"   GPU信息: {self.gpu_info}")
    
    def _detect_gpus(self) -> List[Dict[str, Any]]:
        """检测可用GPU"""
        gpus = []
        
        # 首先尝试检测NVIDIA GPU
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                gpu_info = {
                    'id': i,
                    'name': name.decode('utf-8') if isinstance(name, bytes) else name,
                    'total_memory': memory_info.total,
                    'free_memory': memory_info.free,
                    'used_memory': memory_info.used
                }
                gpus.append(gpu_info)
                
            logger.info(f"✅ 检测到 {len(gpus)} 个NVIDIA GPU")
        except ImportError:
            logger.warning("⚠️  未安装pynvml库，无法检测NVIDIA GPU")
        except Exception as e:
            logger.warning(f"⚠️  检测NVIDIA GPU时出错: {e}")
        
        # 如果没有检测到NVIDIA GPU，尝试检测其他GPU
        if not gpus:
            try:
                # 尝试使用torch检测GPU
                import torch
                if torch.cuda.is_available():
                    for i in range(torch.cuda.device_count()):
                        gpu_info = {
                            'id': i,
                            'name': torch.cuda.get_device_name(i),
                            'total_memory': torch.cuda.get_device_properties(i).total_memory,
                            'free_memory': torch.cuda.get_device_properties(i).total_memory,  # 简化处理
                            'used_memory': 0
                        }
                        gpus.append(gpu_info)
                    logger.info(f"✅ 通过PyTorch检测到 {len(gpus)} 个GPU")
            except ImportError:
                logger.warning("⚠️  未安装torch库，无法检测GPU")
            except Exception as e:
                logger.warning(f"⚠️  通过PyTorch检测GPU时出错: {e}")
        
        return gpus
    
    def get_system_resources(self) -> Dict[str, Any]:
        """获取当前系统资源状态"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        
        # 更新GPU信息
        gpu_info = self._update_gpu_info()
        
        resources = {
            'cpu': {
                'count': self.cpu_count,
                'physical_count': self.physical_cpu_count,
                'usage_percent': cpu_percent,
                'available_cores': self.cpu_count * (100 - cpu_percent) / 100
            },
            'memory': {
                'total': memory_info.total,
                'available': memory_info.available,
                'used': memory_info.used,
                'usage_percent': memory_info.percent
            },
            'gpu': gpu_info,
            'timestamp': datetime.now().isoformat()
        }
        
        # 记录资源使用历史
        self.resource_usage_history.append(resources)
        if len(self.resource_usage_history) > 100:  # 限制历史记录数量
            self.resource_usage_history.pop(0)
        
        return resources
    
    def _update_gpu_info(self) -> List[Dict[str, Any]]:
        """更新GPU信息"""
        updated_gpus = []
        
        try:
            import pynvml
            for gpu in self.gpu_info:
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu['id'])
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                updated_gpu = gpu.copy()
                updated_gpu['free_memory'] = memory_info.free
                updated_gpu['used_memory'] = memory_info.used
                updated_gpus.append(updated_gpu)
        except Exception:
            # 如果无法更新，返回原有信息
            updated_gpus = self.gpu_info
        
        return updated_gpus
    
    def get_model_resource_requirements(self, model_type: str) -> Dict[str, Any]:
        """获取模型的资源需求"""
        # 定义不同模型的资源需求
        requirements = {
            'vision_service': {
                'cpu_cores': 1,  # 降低CPU需求
                'memory_gb': 1,  # 降低内存需求
                'gpu_memory_gb': 1,
                'priority': 2
            },
            'audio_service': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,  # 音频处理通常不需要GPU
                'priority': 1
            },
            'causal_reasoning_engine': {
                'cpu_cores': 1,  # 降低CPU需求
                'memory_gb': 1,  # 降低内存需求
                'gpu_memory_gb': 0,  # 逻辑推理主要使用CPU
                'priority': 3
            },
            'multimodal_service': {
                'cpu_cores': 1,  # 降低CPU需求
                'memory_gb': 1,  # 降低内存需求
                'gpu_memory_gb': 1,
                'priority': 4
            },
            'math_model': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 1
            },
            'logic_model': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 2
            },
            'concept_models': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 3
            },
            'environment_simulator': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 2
            },
            'adaptive_learning_controller': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 3
            },
            'alpha_deep_model': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 4
            }
        }
        
        return requirements.get(model_type, {
            'cpu_cores': 1,
            'memory_gb': 1,
            'gpu_memory_gb': 0,
            'priority': 1
        })
    
    def allocate_resources(self, requirements: Dict[str, Any], model_name: str = None) -> Optional[Dict[str, Any]]:
        """为模型分配资源"""
        if not requirements:
            return None
        
        # 获取当前系统资源
        system_resources = self.get_system_resources()
        cpu_info = system_resources['cpu']
        memory_info = system_resources['memory']
        
        # 检查CPU资源
        required_cpu = requirements.get('cpu_cores', 1)
        available_cpu = cpu_info['available_cores']
        
        if required_cpu > available_cpu:
            logger.warning(f"⚠️  CPU资源不足: 需要 {required_cpu} 核心，可用 {available_cpu:.2f} 核心")
            return None
        
        # 检查内存资源
        required_memory_gb = requirements.get('memory_gb', 1)
        available_memory_gb = memory_info['available'] / (1024**3)
        
        if required_memory_gb > available_memory_gb:
            logger.warning(f"⚠️  内存资源不足: 需要 {required_memory_gb:.2f} GB，可用 {available_memory_gb:.2f} GB")
            return None
        
        # 检查GPU资源（如果需要）
        required_gpu_memory_gb = requirements.get('gpu_memory_gb', 0)
        if required_gpu_memory_gb > 0 and self.gpu_info:
            total_gpu_memory_gb = sum(gpu['free_memory'] for gpu in self.gpu_info) / (1024**3)
            if required_gpu_memory_gb > total_gpu_memory_gb:
                logger.warning(f"⚠️  GPU内存资源不足: 需要 {required_gpu_memory_gb:.2f} GB，可用 {total_gpu_memory_gb:.2f} GB")
                # 如果GPU内存不足，但模型可以使用CPU运行，则继续分配
                required_gpu_memory_gb = 0
        
        # 分配资源
        allocation = {
            'cpu_cores': required_cpu,
            'memory_gb': required_memory_gb,
            'gpu_memory_gb': required_gpu_memory_gb,
            'allocated_at': datetime.now().isoformat()
        }
        
        # 记录资源分配
        if model_name:
            self.resource_allocation[model_name] = allocation
        
        logger.info(f"✅ 资源分配成功: CPU {required_cpu} 核心, 内存 {required_memory_gb} GB, GPU {required_gpu_memory_gb} GB")
        return allocation
    
    def release_resources(self, model_name: str):
        """释放模型占用的资源"""
        if model_name in self.resource_allocation:
            del self.resource_allocation[model_name]
            logger.info(f"🔄 释放模型 {model_name} 的资源")
    
    def get_resource_utilization(self) -> Dict[str, Any]:
        """获取资源利用率报告"""
        system_resources = self.get_system_resources()
        cpu_info = system_resources['cpu']
        memory_info = system_resources['memory']
        
        utilization = {
            'cpu_utilization': {
                'used_cores': self.cpu_count - cpu_info['available_cores'],
                'total_cores': self.cpu_count,
                'utilization_percent': (self.cpu_count - cpu_info['available_cores']) / self.cpu_count * 100
            },
            'memory_utilization': {
                'used_gb': (memory_info['total'] - memory_info['available']) / (1024**3),
                'total_gb': memory_info['total'] / (1024**3),
                'utilization_percent': memory_info['percent']
            },
            'allocated_models': list(self.resource_allocation.keys())
        }
        
        return utilization