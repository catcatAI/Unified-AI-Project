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
    from src.path_config import (
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
                'cpu_cores': 2,
                'memory_gb': 4,
                'gpu_memory_gb': 2,
                'priority': 2
            },
            'audio_service': {
                'cpu_cores': 1,
                'memory_gb': 2,
                'gpu_memory_gb': 0,  # 音频处理通常不需要GPU
                'priority': 1
            },
            'causal_reasoning_engine': {
                'cpu_cores': 4,
                'memory_gb': 8,
                'gpu_memory_gb': 0,  # 逻辑推理主要使用CPU
                'priority': 3
            },
            'multimodal_service': {
                'cpu_cores': 4,
                'memory_gb': 8,
                'gpu_memory_gb': 4,
                'priority': 4
            },
            'math_model': {
                'cpu_cores': 1,
                'memory_gb': 1,
                'gpu_memory_gb': 0,
                'priority': 1
            },
            'logic_model': {
                'cpu_cores': 2,
                'memory_gb': 2,
                'gpu_memory_gb': 0,
                'priority': 2
            },
            'concept_models': {
                'cpu_cores': 3,
                'memory_gb': 4,
                'gpu_memory_gb': 1,
                'priority': 3
            },
            'environment_simulator': {
                'cpu_cores': 2,
                'memory_gb': 3,
                'gpu_memory_gb': 0,
                'priority': 2
            },
            'causal_reasoning_engine': {
                'cpu_cores': 3,
                'memory_gb': 4,
                'gpu_memory_gb': 0,
                'priority': 3
            },
            'adaptive_learning_controller': {
                'cpu_cores': 1,
                'memory_gb': 2,
                'gpu_memory_gb': 0,
                'priority': 1
            },
            'alpha_deep_model': {
                'cpu_cores': 2,
                'memory_gb': 3,
                'gpu_memory_gb': 1,
                'priority': 2
            }
        }
        
        return requirements.get(model_type, {
            'cpu_cores': 1,
            'memory_gb': 1,
            'gpu_memory_gb': 0,
            'priority': 1
        })
    
    def allocate_resources(self, model_requirements: Dict[str, Any], model_name: str) -> Optional[Dict[str, Any]]:
        """根据模型需求分配资源"""
        current_resources = self.get_system_resources()
        
        required_cpu = model_requirements.get('cpu_cores', 1)
        required_memory = model_requirements.get('memory_gb', 1) * (1024**3)  # 转换为字节
        required_gpu_memory = model_requirements.get('gpu_memory_gb', 0) * (1024**3)
        
        # 检查CPU资源
        available_cpu = current_resources['cpu']['available_cores']
        if available_cpu < required_cpu:
            logger.warning(f"⚠️  CPU资源不足: 需要 {required_cpu} 核心，可用 {available_cpu:.2f} 核心")
            return None
        
        # 检查内存资源
        available_memory = current_resources['memory']['available']
        if available_memory < required_memory:
            logger.warning(f"⚠️  内存资源不足: 需要 {required_memory / (1024**3):.2f} GB，可用 {available_memory / (1024**3):.2f} GB")
            return None
        
        # 检查GPU资源
        allocated_gpu = None
        if required_gpu_memory > 0 and current_resources['gpu']:
            for gpu in current_resources['gpu']:
                if gpu['free_memory'] >= required_gpu_memory:
                    allocated_gpu = gpu
                    break
        
        if required_gpu_memory > 0 and not allocated_gpu:
            logger.warning(f"⚠️  GPU内存资源不足: 需要 {required_gpu_memory / (1024**3):.2f} GB")
            # 如果模型需要GPU但没有可用GPU，可以考虑是否继续使用CPU
        
        # 分配资源
        allocation = {
            'model_name': model_name,
            'cpu_cores': required_cpu,
            'memory_bytes': required_memory,
            'gpu': allocated_gpu,
            'allocated_at': datetime.now().isoformat()
        }
        
        # 记录资源分配
        self.resource_allocation[model_name] = allocation
        
        logger.info(f"✅ 为模型 {model_name} 分配资源成功:")
        logger.info(f"   CPU核心: {required_cpu}")
        logger.info(f"   内存: {required_memory / (1024**3):.2f} GB")
        if allocated_gpu:
            logger.info(f"   GPU: {allocated_gpu['name']} ({required_gpu_memory / (1024**3):.2f} GB)")
        
        return allocation
    
    def release_resources(self, model_name: str):
        """释放模型占用的资源"""
        if model_name in self.resource_allocation:
            allocation = self.resource_allocation.pop(model_name)
            logger.info(f"🔄 释放模型 {model_name} 的资源: CPU {allocation['cpu_cores']} 核心, 内存 {allocation['memory_bytes'] / (1024**3):.2f} GB")
        else:
            logger.warning(f"⚠️ 未找到模型 {model_name} 的资源分配记录")
    
    def get_resource_allocation_status(self) -> Dict[str, Any]:
        """获取资源分配状态"""
        total_allocated_cpu = sum(allocation['cpu_cores'] for allocation in self.resource_allocation.values())
        total_allocated_memory = sum(allocation['memory_bytes'] for allocation in self.resource_allocation.values())
        
        status = {
            'total_system_cpu': self.cpu_count,
            'allocated_cpu': total_allocated_cpu,
            'available_cpu': self.cpu_count - total_allocated_cpu,
            'total_system_memory_gb': self.total_memory / (1024**3),
            'allocated_memory_gb': total_allocated_memory / (1024**3),
            'available_memory_gb': (self.total_memory - total_allocated_memory) / (1024**3),
            'active_allocations': self.resource_allocation,
            'gpu_count': len(self.gpu_info)
        }
        
        return status
    
    def optimize_resource_allocation(self) -> Dict[str, Any]:
        """优化资源分配"""
        # 获取当前资源使用情况
        current_resources = self.get_system_resources()
        
        # 根据优先级重新分配资源
        sorted_allocations = sorted(
            self.resource_allocation.items(),
            key=lambda x: self.get_model_resource_requirements(x[0]).get('priority', 1),
            reverse=True
        )
        
        optimization_result = {
            'reallocations': [],
            'resource_status': self.get_resource_allocation_status(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 这里可以实现更复杂的资源优化逻辑
        # 例如：根据模型优先级和资源使用情况动态调整资源分配
        
        return optimization_result
    
    def monitor_resources(self) -> Dict[str, Any]:
        """监控资源使用情况"""
        current_resources = self.get_system_resources()
        allocation_status = self.get_resource_allocation_status()
        
        # 检查是否有资源瓶颈
        issues = []
        if current_resources['cpu']['usage_percent'] > 90:
            issues.append("CPU使用率过高")
        
        if current_resources['memory']['usage_percent'] > 90:
            issues.append("内存使用率过高")
        
        if self.gpu_info:
            for gpu in current_resources['gpu']:
                if gpu['used_memory'] / gpu['total_memory'] > 0.9:
                    issues.append(f"GPU {gpu['id']} 内存使用率过高")
        
        monitoring_result = {
            'current_resources': current_resources,
            'allocation_status': allocation_status,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
        if issues:
            logger.warning(f"⚠️  资源监控发现问题: {', '.join(issues)}")
        
        return monitoring_result
    
    def save_resource_status(self, status_path: str = None):
        """保存资源状态到文件"""
        if not status_path:
            status_path = TRAINING_DIR / "resource_status.json"
        
        status_data = {
            'resource_allocation': self.resource_allocation,
            'resource_usage_history': self.resource_usage_history[-20:],  # 只保存最近20条记录
            'generated_at': datetime.now().isoformat()
        }
        
        try:
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 资源状态已保存到: {status_path}")
        except Exception as e:
            logger.error(f"❌ 保存资源状态失败: {e}")
    
    def load_resource_status(self, status_path: str = None):
        """从文件加载资源状态"""
        if not status_path:
            status_path = TRAINING_DIR / "resource_status.json"
        
        if not Path(status_path).exists():
            logger.warning(f"⚠️ 资源状态文件不存在: {status_path}")
            return False
        
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            
            self.resource_allocation = status_data.get('resource_allocation', {})
            self.resource_usage_history = status_data.get('resource_usage_history', [])
            logger.info(f"✅ 资源状态已从 {status_path} 加载")
            return True
        except Exception as e:
            logger.error(f"❌ 加载资源状态失败: {e}")
            return False


def main():
    """主函数，用于测试ResourceManager"""
    print("🖥️  测试资源管理器...")
    
    # 初始化资源管理器
    resource_manager = ResourceManager()
    
    # 显示系统资源
    resources = resource_manager.get_system_resources()
    print(f"📊 系统资源状态:")
    print(f"  CPU使用率: {resources['cpu']['usage_percent']:.1f}%")
    print(f"  可用CPU核心: {resources['cpu']['available_cores']:.1f}")
    print(f"  内存使用率: {resources['memory']['usage_percent']:.1f}%")
    print(f"  可用内存: {resources['memory']['available'] / (1024**3):.2f} GB")
    print(f"  GPU数量: {len(resources['gpu'])}")
    
    # 测试模型资源分配
    print(f"\n🔧 模型资源分配测试:")
    for model_type in ['vision_service', 'causal_reasoning_engine', 'multimodal_service']:
        requirements = resource_manager.get_model_resource_requirements(model_type)
        allocation = resource_manager.allocate_resources(requirements, model_type)
        if allocation:
            print(f"  {model_type}: 分配成功")
        else:
            print(f"  {model_type}: 分配失败")
    
    # 显示资源分配状态
    status = resource_manager.get_resource_allocation_status()
    print(f"\n📈 资源分配状态:")
    print(f"  已分配CPU: {status['allocated_cpu']} 核心")
    print(f"  可用CPU: {status['available_cpu']:.1f} 核心")
    print(f"  已分配内存: {status['allocated_memory_gb']:.2f} GB")
    print(f"  可用内存: {status['available_memory_gb']:.2f} GB")
    
    # 监控资源
    monitoring_result = resource_manager.monitor_resources()
    if monitoring_result['issues']:
        print(f"\n⚠️  资源监控发现问题:")
        for issue in monitoring_result['issues']:
            print(f"  - {issue}")
    else:
        print(f"\n✅ 资源监控正常")
    
    # 保存资源状态
    resource_manager.save_resource_status()
    print(f"\n✅ 资源管理器测试完成")


if __name__ == "__main__":
    main()