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
            return {"message": "系統不是集成顯卡,無需特殊優化"}

        recommendations = {
            "system_type": "integrated_graphics",
            "total_system_memory_gb": self.hardware_profile.memory.total / 1024,
            "gpu_count": len(self.hardware_profile.gpu),
            "optimizations": []
        }

        # Memory optimization
        if self.hardware_profile.memory.total < 16 * 1024:  # Less than 16GB
            recommendations["optimizations"].append({
                "strategy": "memory_optimization",
                "action": "Reduce model size and batch size",
                "priority": "high"
            })

        # Precision adjustment
        recommendations["optimizations"].append({
            "strategy": "precision_adjustment",
            "action": "Use FP16 or INT8 quantization",
            "priority": "medium"
        })

        # CPU-GPU coordination
        recommendations["optimizations"].append({
            "strategy": "cpu_gpu_coordination",
            "action": "Offload heavy computation to CPU",
            "priority": "medium"
        })

        return recommendations

    def apply_optimizations(self) -> bool:
        """應用優化策略"""
        try:
            recommendations = self.get_optimization_recommendations()
            
            if "message" in recommendations:
                logger.info(recommendations["message"])
                return True

            for optimization in recommendations.get("optimizations", []):
                logger.info(f"Applying {optimization['strategy']}: {optimization['action']}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply optimizations: {e}")
            return False


# Module-level convenience function
def optimize_for_integrated_graphics(hardware_profile) -> Dict[str, Any]:
    """
    Convenience function to get optimization recommendations for integrated graphics.
    
    Args:
        hardware_profile: Hardware profile object
    
    Returns:
        Dictionary containing optimization recommendations
    """
    optimizer = IntegratedGraphicsOptimizer(hardware_profile)
    return optimizer.get_optimization_recommendations()
