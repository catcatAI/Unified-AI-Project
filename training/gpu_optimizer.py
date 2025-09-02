#!/usr/bin/env python3
"""
GPU优化器
负责优化GPU资源使用，包括内存管理、计算优化等
"""

import logging
import os
from typing import Dict, Any, List, Optional
import gc

logger = logging.getLogger(__name__)

class GPUOptimizer:
    """GPU优化器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.gpu_available = self._check_gpu_availability()
        self.optimization_strategies = self.config.get('optimization_strategies', [
            'memory_growth',
            'mixed_precision',
            'gradient_checkpointing',
            'layer_fusion'
        ])
        
        logger.info(f"GPU优化器初始化完成，GPU可用: {self.gpu_available}")
    
    def _check_gpu_availability(self) -> bool:
        """检查GPU是否可用"""
        try:
            import tensorflow as tf
            # 检查TensorFlow版本兼容性
            if hasattr(tf.config, 'list_physical_devices'):
                gpus = tf.config.list_physical_devices('GPU')
            else:
                # 兼容旧版本TensorFlow
                gpus = tf.config.experimental.list_physical_devices('GPU')
            return len(gpus) > 0
        except ImportError:
            logger.warning("TensorFlow未安装，无法使用GPU")
            return False
        except Exception as e:
            logger.warning(f"检查GPU可用性时出错: {e}")
            return False
    
    def optimize_gpu_memory(self):
        """优化GPU内存使用"""
        if not self.gpu_available:
            logger.warning("GPU不可用，跳过GPU内存优化")
            return False
        
        try:
            import tensorflow as tf
            # 兼容不同版本的TensorFlow
            if hasattr(tf.config, 'list_physical_devices'):
                gpus = tf.config.list_physical_devices('GPU')
            else:
                gpus = tf.config.experimental.list_physical_devices('GPU')
            
            if not gpus:
                logger.warning("未检测到GPU设备")
                return False
            
            # 为每个GPU设置内存增长
            for gpu in gpus:
                # 兼容不同版本的TensorFlow
                if hasattr(tf.config, 'experimental') and hasattr(tf.config.experimental, 'set_memory_growth'):
                    tf.config.experimental.set_memory_growth(gpu, True)
                elif hasattr(tf.config, 'set_memory_growth'):
                    tf.config.set_memory_growth(gpu, True)
                else:
                    # 兼容旧版本
                    tf.config.experimental.set_memory_growth(gpu, True)
            
            logger.info(f"GPU内存优化完成，配置了 {len(gpus)} 个GPU设备的内存增长")
            return True
        except Exception as e:
            logger.error(f"GPU内存优化失败: {e}")
            return False
    
    def enable_mixed_precision(self):
        """启用混合精度训练"""
        if not self.gpu_available:
            logger.warning("GPU不可用，跳过混合精度训练")
            return False
        
        try:
            import tensorflow as tf
            
            # 检查是否支持混合精度
            if hasattr(tf.keras.mixed_precision, 'Policy'):
                # 新版本API
                policy = tf.keras.mixed_precision.Policy('mixed_float16')
                tf.keras.mixed_precision.set_global_policy(policy)
            elif hasattr(tf.keras.mixed_precision, 'experimental'):
                # 旧版本API
                policy = tf.keras.mixed_precision.experimental.Policy('mixed_float16')
                tf.keras.mixed_precision.experimental.set_policy(policy)
            else:
                logger.warning("当前TensorFlow版本不支持混合精度训练")
                return False
            
            logger.info("混合精度训练已启用")
            return True
        except Exception as e:
            logger.error(f"启用混合精度训练失败: {e}")
            return False
    
    def enable_gradient_checkpointing(self, model):
        """启用梯度检查点以节省内存"""
        try:
            # 对于TensorFlow模型，可以通过设置checkpoint来实现
            # 这里提供一个通用的接口
            if hasattr(model, 'enable_gradient_checkpointing'):
                model.enable_gradient_checkpointing()
                logger.info("梯度检查点已启用")
                return True
            else:
                logger.warning("模型不支持梯度检查点")
                return False
        except Exception as e:
            logger.error(f"启用梯度检查点失败: {e}")
            return False
    
    def optimize_model_for_inference(self, model):
        """优化模型用于推理"""
        try:
            import tensorflow as tf
            
            # 转换为TensorFlow Lite模型以优化推理
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            # 启用混合量化
            converter.representative_dataset = self._get_representative_dataset
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.int8
            converter.inference_output_type = tf.int8
            
            tflite_model = converter.convert()
            
            logger.info("模型已优化用于推理")
            return tflite_model
        except Exception as e:
            logger.error(f"模型推理优化失败: {e}")
            return None
    
    def _get_representative_dataset(self):
        """获取代表性数据集用于量化"""
        # 这里应该返回一个小型数据集用于量化校准
        # 为了示例，我们返回一个简单的生成器
        import numpy as np
        
        for _ in range(100):
            yield [np.random.random((1, 224, 224, 3)).astype(np.float32)]
    
    def clear_gpu_memory(self):
        """清理GPU内存"""
        try:
            import tensorflow as tf
            
            # 清理TensorFlow会话
            tf.keras.backend.clear_session()
            
            # 强制垃圾回收
            gc.collect()
            
            logger.info("GPU内存已清理")
            return True
        except Exception as e:
            logger.error(f"清理GPU内存失败: {e}")
            return False
    
    def get_gpu_utilization(self) -> Dict[str, Any]:
        """获取GPU利用率信息"""
        if not self.gpu_available:
            return {}
        
        try:
            import pynvml
            pynvml.nvmlInit()
            
            device_count = pynvml.nvmlDeviceGetCount()
            gpu_info = []
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                gpu_info.append({
                    'id': i,
                    'name': name.decode('utf-8') if isinstance(name, bytes) else name,
                    'memory_total_gb': memory_info.total / (1024**3),
                    'memory_used_gb': memory_info.used / (1024**3),
                    'memory_free_gb': memory_info.free / (1024**3),
                    'gpu_utilization': utilization.gpu,
                    'memory_utilization': utilization.memory
                })
            
            return {
                'timestamp': self._get_current_timestamp(),
                'gpus': gpu_info
            }
        except Exception as e:
            logger.error(f"获取GPU利用率信息失败: {e}")
            return {}
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def apply_optimization_strategies(self):
        """应用所有优化策略"""
        results = {}
        
        for strategy in self.optimization_strategies:
            if strategy == 'memory_growth':
                results[strategy] = self.optimize_gpu_memory()
            elif strategy == 'mixed_precision':
                results[strategy] = self.enable_mixed_precision()
            elif strategy == 'gradient_checkpointing':
                # 梯度检查点需要模型实例，这里只是示例
                results[strategy] = "需要模型实例"
            elif strategy == 'layer_fusion':
                results[strategy] = self.enable_layer_fusion()
            else:
                logger.warning(f"未知的优化策略: {strategy}")
                results[strategy] = False
        
        logger.info(f"应用优化策略结果: {results}")
        return results
    
    def enable_layer_fusion(self):
        """启用层融合优化"""
        try:
            import tensorflow as tf
            
            # 启用TensorFlow的图优化
            tf.config.optimizer.set_jit(True)
            
            logger.info("层融合优化已启用")
            return True
        except Exception as e:
            logger.error(f"启用层融合优化失败: {e}")
            return False

if __name__ == "__main__":
    # 测试GPU优化器
    logging.basicConfig(level=logging.INFO)
    optimizer = GPUOptimizer()
    
    # 应用优化策略
    results = optimizer.apply_optimization_strategies()
    print(f"优化策略应用结果: {results}")
    
    # 获取GPU利用率
    gpu_util = optimizer.get_gpu_utilization()
    print(f"GPU利用率: {gpu_util}")