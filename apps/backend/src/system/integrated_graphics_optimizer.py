"""
Integrated Graphics Optimizer for Unified-AI-Project
Provides optimization strategies specifically for integrated graphics.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class IntegratedGraphicsOptimizer:
    """优化器專門用於集成顯卡，確保項目在各種硬體上流暢運行"""

    def __init__(self, hardware_profile) -> None:
        self.hardware_profile = hardware_profile
        self.optimization_strategies = [
            'memory_optimization',
            'batch_size_scaling',
            'precision_adjustment',
            'cpu_gpu_coordination',
            'model_compression'
        ]
        logger.info("Integrated Graphics Optimizer initialized")

    def is_integrated_graphics_system(self) -> bool:
        """檢查是否為集成顯卡系統"""
        if not self.hardware_profile.gpu:
            return False

        for gpu in self.hardware_profile.gpu:
            if self._is_integrated_gpu(gpu):
                return True
        return False

    def _is_integrated_gpu(self, gpu) -> bool:
        """判斷是否為集成顯卡"""
        integrated_keywords = ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']
        return any(keyword in gpu.name.lower() for keyword in integrated_keywords)

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """獲取針對集成顯卡的優化建議"""
        if not self.is_integrated_graphics_system():
            return {"message": "系統不是集成顯卡，無需特殊優化"}

        recommendations = {
            "system_type": "integrated_graphics",
            "total_system_memory_gb": self.hardware_profile.memory.total / 1024,
            "gpu_count": len(self.hardware_profile.gpu),
            "optimizations": []
        }

        # 獲取最佳GPU
        best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
        gpu_memory_gb = best_gpu.memory_total / 1024

        if gpu_memory_gb < 1:
            recommendations["optimizations"].extend([
                "顯存不足1GB，建議使用CPU訓練模式",
                "啟用模型壓縮以減少顯存占用",
                "降低批處理大小到最小值",
                "使用int8量化訓練"
            ])
        elif gpu_memory_gb < 2:
            recommendations["optimizations"].extend([
                "顯存1-2GB，建議使用混合CPU-GPU訓練",
                "啟用混合精度訓練",
                "適度降低批處理大小",
                "使用梯度累加技術"
            ])
        elif gpu_memory_gb < 4:
            recommendations["optimizations"].extend([
                "顯存2-4GB，可啟用GPU加速訓練",
                "使用混合精度訓練",
                "根據模型大小動態調整批處理大小",
                "啟用顯存優化技術"
            ])
        else:
            recommendations["optimizations"].extend([
                "顯存充足，可啟用完整GPU訓練",
                "推薦使用混合精度訓練",
                "可適當增加批處理大小",
                "啟用高級顯存優化技術"
            ])

        system_memory_gb = self.hardware_profile.memory.total / 1024
        if system_memory_gb < 8:
            recommendations["optimizations"].append("系統內存不足8GB，建議啟用內存映射和數據流式處理")
        elif system_memory_gb < 16:
            recommendations["optimizations"].append("系統內存8-16GB，可啟用緩存優化")

        return recommendations

def optimize_for_integrated_graphics(hardware_profile) -> Dict[str, Any]:
    """Helper function to get optimization recommendations"""
    optimizer = IntegratedGraphicsOptimizer(hardware_profile)
    return optimizer.get_optimization_recommendations()
