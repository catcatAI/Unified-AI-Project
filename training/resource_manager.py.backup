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
import heapq

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

# 导入智能资源分配器
from .smart_resource_allocator import SmartResourceAllocator

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
        self.task_queue = []  # 任务队列，按优先级排序
        
        # 智能资源分配器
        self.smart_allocator = SmartResourceAllocator()
        self.running_tasks = {}  # 正在运行的任务
        
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
                        props = torch.cuda.get_device_properties(i)
                        gpu_info = {
                            'id': i,
                            'name': torch.cuda.get_device_name(i),
                            'total_memory': props.total_memory,
                            'free_memory': props.total_memory,  # 简化处理
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
        try:
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
        except Exception as e:
            logger.error(f"❌ 获取系统资源信息失败: {e}")
            # 返回默认资源信息
            return {
                'cpu': {
                    'count': self.cpu_count,
                    'physical_count': self.physical_cpu_count,
                    'usage_percent': 0,
                    'available_cores': self.cpu_count
                },
                'memory': {
                    'total': self.total_memory,
                    'available': self.available_memory,
                    'used': 0,
                    'usage_percent': 0
                },
                'gpu': self.gpu_info,
                'timestamp': datetime.now().isoformat()
            }
    
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
                'cpu_cores': 2,
                'memory_gb': 2,
                'gpu_memory_gb': 2,
                'priority': 2,
                'estimated_time_hours': 2
            },
            'audio_service': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,  # 音频处理通常不需要GPU
                'priority': 1,
                'estimated_time_hours': 1
            },
            'causal_reasoning_engine': {
                'cpu_cores': 2,
                'memory_gb': 2,
                'gpu_memory_gb': 0,  # 逻辑推理主要使用CPU
                'priority': 3,
                'estimated_time_hours': 3
            },
            'multimodal_service': {
                'cpu_cores': 3,
                'memory_gb': 3,
                'gpu_memory_gb': 3,
                'priority': 4,
                'estimated_time_hours': 4
            },
            'math_model': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 1,
                'estimated_time_hours': 1
            },
            'logic_model': {
                'cpu_cores': 2,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 2,
                'estimated_time_hours': 2
            },
            'concept_models': {
                'cpu_cores': 2,
                'memory_gb': 2,
                'gpu_memory_gb': 1,
                'priority': 3,
                'estimated_time_hours': 3
            },
            'environment_simulator': {
                'cpu_cores': 2,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 2,
                'estimated_time_hours': 2
            },
            'adaptive_learning_controller': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 3,
                'estimated_time_hours': 1
            },
            'alpha_deep_model': {
                'cpu_cores': 3,
                'memory_gb': 3,
                'gpu_memory_gb': 2,
                'priority': 4,
                'estimated_time_hours': 4
            }
        }
        
        return requirements.get(model_type, {
            'cpu_cores': 1,
            'memory_gb': 1,
            'gpu_memory_gb': 0,
            'priority': 1,
            'estimated_time_hours': 1
        })
    
    def add_task_to_queue(self, task_info: Dict[str, Any]):
        """将任务添加到队列中"""
        # 使用优先级和预计时间作为排序依据
        priority = task_info.get('requirements', {}).get('priority', 1)
        estimated_time = task_info.get('requirements', {}).get('estimated_time_hours', 1)
        
        # 创建任务元组：(优先级负值, 预计时间, 任务信息)
        # 使用负值是因为heapq是最小堆，我们需要最大优先级先执行
        task_tuple = (-priority, estimated_time, task_info)
        heapq.heappush(self.task_queue, task_tuple)
        logger.info(f"📥 任务已添加到队列: {task_info.get('model_name', 'Unknown')}")
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """获取下一个要执行的任务"""
        if not self.task_queue:
            return None
        
        # 弹出优先级最高的任务
        priority, estimated_time, task_info = heapq.heappop(self.task_queue)
        return task_info
    
    def allocate_resources(self, requirements: Dict[str, Any], model_name: str = None) -> Optional[Dict[str, Any]]:
        """为模型分配资源"""
        if not requirements:
            return None
        
        # 使用智能资源分配器进行资源分配
        from .smart_resource_allocator import ResourceRequest
        
        # 创建资源请求
        resource_request = ResourceRequest(
            task_id=model_name or f"task_{int(datetime.now().timestamp())}",
            cpu_cores=requirements.get('cpu_cores', 1),
            memory_gb=requirements.get('memory_gb', 1),
            gpu_memory_gb=requirements.get('gpu_memory_gb', 0),
            priority=requirements.get('priority', 1),
            estimated_time_hours=requirements.get('estimated_time_hours', 1),
            resource_type="gpu" if requirements.get('gpu_memory_gb', 0) > 0 else "cpu"
        )
        
        # 请求资源
        self.smart_allocator.request_resources(resource_request)
        
        # 分配资源
        allocations = self.smart_allocator.allocate_resources()
        
        if not allocations:
            logger.warning(f"⚠️  资源分配失败: {model_name}")
            return None
        
        # 获取分配结果
        allocation_result = allocations[0]  # 假设第一个分配就是我们需要的
        
        # 转换为原有格式
        allocation = {
            'cpu_cores': allocation_result.allocated_cpu_cores,
            'memory_gb': allocation_result.allocated_memory_gb,
            'gpu_memory_gb': allocation_result.allocated_gpu_memory_gb,
            'allocated_at': datetime.now().isoformat()
        }
        
        # 记录资源分配
        if model_name:
            self.resource_allocation[model_name] = allocation
        
        logger.info(f"✅ 资源分配成功: CPU {allocation_result.allocated_cpu_cores} 核心, 内存 {allocation_result.allocated_memory_gb} GB, GPU {allocation_result.allocated_gpu_memory_gb} GB")
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
    
    def get_resource_allocation_status(self) -> Dict[str, Any]:
        """获取资源分配状态"""
        system_resources = self.get_system_resources()
        cpu_info = system_resources['cpu']
        memory_info = system_resources['memory']
        
        allocated_cpu = sum(allocation.get('cpu_cores', 0) for allocation in self.resource_allocation.values())
        allocated_memory = sum(allocation.get('memory_gb', 0) for allocation in self.resource_allocation.values())
        
        status = {
            'total_cpu': self.cpu_count,
            'allocated_cpu': allocated_cpu,
            'available_cpu': self.cpu_count - allocated_cpu,
            'total_memory_gb': self.total_memory / (1024**3),
            'allocated_memory_gb': allocated_memory,
            'available_memory_gb': (self.total_memory / (1024**3)) - allocated_memory,
            'gpu_info': self.gpu_info,
            'allocated_models': list(self.resource_allocation.keys()),
            'pending_tasks': len(self.task_queue)
        }
        
        return status
    
    def optimize_resource_allocation(self) -> Dict[str, Any]:
        """优化资源分配"""
        logger.info("⚙️  开始优化资源分配...")
        
        # 获取当前资源使用情况
        status = self.get_resource_allocation_status()
        
        optimization_result = {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': [],
            'current_status': status
        }
        
        # 如果有大量空闲资源，可以考虑增加并行任务
        if status['available_cpu'] > status['total_cpu'] * 0.5:
            optimization_result['actions_taken'].append("系统有大量空闲CPU资源，可以增加并行任务")
        
        if status['available_memory_gb'] > status['total_memory_gb'] * 0.5:
            optimization_result['actions_taken'].append("系统有大量空闲内存资源，可以增加并行任务")
        
        # 如果资源紧张，考虑暂停低优先级任务
        if status['available_cpu'] < 1 or status['available_memory_gb'] < 1:
            optimization_result['actions_taken'].append("系统资源紧张，建议暂停低优先级任务")
        
        logger.info("✅ 资源分配优化完成")
        return optimization_result
    
    def dynamic_resource_scaling(self, model_name: str, current_performance: Dict[str, Any]) -> bool:
        """动态调整模型资源分配"""
        logger.info(f"📈 动态调整模型 {model_name} 的资源分配")
        
        if model_name not in self.resource_allocation:
            logger.warning(f"⚠️  模型 {model_name} 未分配资源")
            return False
        
        # 获取当前资源分配
        current_allocation = self.resource_allocation[model_name]
        cpu_cores = current_allocation['cpu_cores']
        memory_gb = current_allocation['memory_gb']
        
        # 根据性能指标调整资源
        accuracy = current_performance.get('accuracy', 0.0)
        loss = current_performance.get('loss', 1.0)
        processing_time = current_performance.get('processing_time', 1.0)
        
        # 如果准确率低且损失高，增加资源
        if accuracy < 0.8 and loss > 0.5:
            # 增加CPU核心
            if cpu_cores < self.cpu_count:
                current_allocation['cpu_cores'] = min(cpu_cores + 1, self.cpu_count)
                logger.info(f"   增加CPU核心: {cpu_cores} -> {current_allocation['cpu_cores']}")
            
            # 增加内存
            current_allocation['memory_gb'] = memory_gb * 1.2
            logger.info(f"   增加内存: {memory_gb:.2f}GB -> {current_allocation['memory_gb']:.2f}GB")
        
        # 如果处理时间过长，增加资源
        elif processing_time > 10.0:  # 超过10秒
            if cpu_cores < self.cpu_count:
                current_allocation['cpu_cores'] = min(cpu_cores + 1, self.cpu_count)
                logger.info(f"   增加CPU核心: {cpu_cores} -> {current_allocation['cpu_cores']}")
        
        # 如果准确率高且损失低，可以减少资源以节省资源
        elif accuracy > 0.95 and loss < 0.1:
            # 减少CPU核心
            if cpu_cores > 1:
                current_allocation['cpu_cores'] = max(cpu_cores - 1, 1)
                logger.info(f"   减少CPU核心: {cpu_cores} -> {current_allocation['cpu_cores']}")
            
            # 减少内存
            current_allocation['memory_gb'] = max(memory_gb * 0.8, 1.0)
            logger.info(f"   减少内存: {memory_gb:.2f}GB -> {current_allocation['memory_gb']:.2f}GB")
        
        # 更新资源分配记录
        self.resource_allocation[model_name] = current_allocation
        logger.info(f"✅ 模型 {model_name} 资源调整完成")
        return True