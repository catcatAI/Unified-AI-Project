"""
Angela AI v6.0 - Precision Conversion Matrix
精度转换矩阵

Manages precision conversions between native and translated representations
across different hardware architectures and precision levels.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import math
import logging
logger = logging.getLogger(__name__)


@dataclass
class ConversionInfo:
    """转换信息 / Conversion Information"""
    source_precision: str
    target_precision: str
    loss_rate: float  # 精度损失率 (0-1)
    performance_factor: float  # 性能影响因子
    hardware_supported: List[str]
    loss_function: str
    reversible: bool


@dataclass
class PrecisionConfig:
    """精度配置 / Precision Configuration"""
    working_precision: str
    storage_precision: str
    computation_precision: str
    cache_precision: str
    network_precision: str


class PrecisionMatrix:
    """
    精度转换矩阵 / Precision Conversion Matrix
    
    Manages precision conversions with minimal loss.
    管理精度转换，最小化损失。
    
    Attributes:
        conversion_table: 转换表 / Conversion table
        loss_profiles: 损失配置 / Loss profiles
    """
    
    def __init__(self):
        self._initialize_matrix()
    
    def _initialize_matrix(self):
        """初始化矩阵 / Initialize matrix"""
        self.conversion_table: Dict[Tuple[str, str], ConversionInfo] = {}
        
        # 定义精度级别
        precision_levels = ["fp64", "fp32", "fp16", "bf16", "tf32", "int8", "int4", "int1"]
        
        for src in precision_levels:
            for tgt in precision_levels:
                info = self._calculate_conversion(src, tgt)
                self.conversion_table[(src, tgt)] = info
    
    def _calculate_conversion(
        self,
        source: str,
        target: str
    ) -> ConversionInfo:
        """计算转换信息 / Calculate conversion info"""
        src_bits = self._get_bit_width(source)
        tgt_bits = self._get_bit_width(target)
        
        loss_rate = max(0, (src_bits - tgt_bits) / src_bits) if src_bits > tgt_bits else 0
        perf_factor = 2.0 if tgt_bits < src_bits else 1.0
        
        hardware = self._get_supported_hardware(source, target)
        
        return ConversionInfo(
            source_precision=source,
            target_precision=target,
            loss_rate=loss_rate,
            performance_factor=perf_factor,
            hardware_supported=hardware,
            loss_function=self._get_loss_function(source, target),
            reversible=src_bits <= tgt_bits
        )
    
    def _get_bit_width(self, precision: str) -> int:
        """获取位宽 / Get bit width"""
        width_map = {
            "fp64": 64,
            "fp32": 32,
            "fp16": 16,
            "bf16": 16,
            "tf32": 19,
            "int8": 8,
            "int4": 4,
            "int1": 1,
        }
        return width_map.get(precision, 32)
    
    def _get_supported_hardware(
        self,
        source: str,
        target: str
    ) -> List[str]:
        """获取支持的硬件 / Get supported hardware"""
        hardware = []
        
        if target in ["fp16", "bf16", "tf32"]:
            hardware.extend(["nvidia_gpu", "apple_silicon", "google_tpu"])
        
        if target in ["int8", "int4", "int1"]:
            hardware.extend(["nvidia_gpu", "google_tpu", "edge_devices"])
        
        if source == "fp64" and target in ["fp32", "fp16"]:
            hardware.extend(["cpu", "all"])
        
        return hardware if hardware else ["all"]
    
    def _get_loss_function(
        self,
        source: str,
        target: str
    ) -> str:
        """获取损失函数 / Get loss function"""
        src_bits = self._get_bit_width(source)
        tgt_bits = self._get_bit_width(target)
        
        if tgt_bits >= src_bits:
            return "identity"
        elif tgt_bits >= 16:
            return "round_to_nearest"
        elif tgt_bits >= 8:
            return "quantize_symmetric"
        else:
            return "binary_quantize"
    
    def get_conversion(
        self,
        source: str,
        target: str
    ) -> Optional[ConversionInfo]:
        """获取转换信息 / Get conversion info"""
        return self.conversion_table.get((source, target))
    
    def get_path(
        self,
        source: str,
        target: str
    ) -> List[Tuple[str, str]]:
        """获取最优转换路径 / Get optimal conversion path"""
        if source == target:
            return [(source, source)]
        
        direct = self.get_conversion(source, target)
        if direct and direct.loss_rate < 0.01:
            return [(source, target)]
        
        intermediate = self._find_intermediate(source, target)
        return [(source, intermediate), (intermediate, target)]
    
    def _find_intermediate(
        self,
        source: str,
        target: str
    ) -> str:
        """找中间精度 / Find intermediate precision"""
        candidates = ["fp32", "fp16", "int8"]
        best = source
        
        for cand in candidates:
            if cand != source and cand != target:
                if self.get_conversion(source, cand) and self.get_conversion(cand, target):
                    return cand
        
        return "fp32"
    
    def convert_value(
        self,
        value: float,
        source: str,
        target: str
    ) -> float:
        """转换数值 / Convert value"""
        info = self.get_conversion(source, target)
        if not info:
            return value
        
        src_bits = self._get_bit_width(source)
        tgt_bits = self._get_bit_width(target)
        
        if tgt_bits >= src_bits:
            return float(value)
        
        if tgt_bits >= 16:
            max_val = (2 ** (tgt_bits - 1) - 1) if "int" in target else (2 ** tgt_bits)
            return max(min(value, max_val), -max_val)
        
        elif tgt_bits >= 8:
            scale = 127.0 if "int8" in target else 15.0
            return round(value * scale) / scale
        
        else:
            return 1.0 if value > 0 else -1.0
    
    def estimate_loss(
        self,
        original: float,
        converted: float,
        context: str = "relative"
    ) -> Dict[str, float]:
        """估计精度损失 / Estimate precision loss"""
        if original == 0:
            return {"absolute": 0, "relative": 0, "db": float("inf")}
        
        abs_loss = abs(original - converted)
        rel_loss = abs_loss / abs(original)
        
        if rel_loss > 0:
            db = 20 * math.log10(abs(original) / abs_loss) if abs(converted) > 1e-10 else 0
        else:
            db = float("inf")
        
        return {
            "absolute": abs_loss,
            "relative": rel_loss,
            "db": db,
        }
    
    def get_precision_chain(
        self,
        storage: str = "fp32",
        computation: str = "fp16",
        network: str = "int8",
        cache: str = "fp16"
    ) -> List[Dict[str, Any]]:
        """获取精度链 / Get precision chain"""
        return [
            {"stage": "storage", "precision": storage, "bits": self._get_bit_width(storage)},
            {"stage": "computation", "precision": computation, "bits": self._get_bit_width(computation)},
            {"stage": "network", "precision": network, "bits": self._get_bit_width(network)},
            {"stage": "cache", "precision": cache, "bits": self._get_bit_width(cache)},
        ]
    
    def validate_precision(
        self,
        precision: str,
        hardware_capabilities: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """验证精度支持 / Validate precision support"""
        required_bits = self._get_bit_width(precision)
        info = {"supported": True, "warnings": [], "recommendations": []}
        
        if hardware_capabilities:
            if required_bits > 32 and not hardware_capabilities.get("fp64"):
                info["supported"] = False
                info["warnings"].append("Hardware may not support FP64")
            
            if precision in ["fp16", "bf16"]:
                if not hardware_capabilities.get("fp16"):
                    info["warnings"].append("FP16 not natively supported, will emulate")
                    info["recommendations"].append("Use FP32 for computation")
        
        return info


class PrecisionManager:
    """
    精度管理器 / Precision Manager
    
    High-level interface for precision management.
    精度管理的高级接口。
    
    Attributes:
        matrix: 精度矩阵 / Precision matrix
        config: 当前配置 / Current config
    """
    
    def __init__(self):
        self.matrix = PrecisionMatrix()
        self.config = PrecisionConfig(
            working_precision="fp32",
            storage_precision="fp32",
            computation_precision="fp16",
            cache_precision="fp16",
            network_precision="int8",
        )
    
    def set_precision_config(
        self,
        working: str = None,
        storage: str = None,
        computation: str = None,
        cache: str = None,
        network: str = None
    ):
        """设置精度配置 / Set precision config"""
        if working:
            self.config.working_precision = working
        if storage:
            self.config.storage_precision = storage
        if computation:
            self.config.computation_precision = computation
        if cache:
            self.config.cache_precision = cache
        if network:
            self.config.network_precision = network
    
    def optimize_for_hardware(
        self,
        hardware_info: Dict[str, Any]
    ) -> Dict[str, str]:
        """为硬件优化精度 / Optimize precision for hardware"""
        recommendations = {}
        
        if hardware_info.get("tensor_cores"):
            recommendations["computation"] = "tf32"
            recommendations["storage"] = "fp16"
        elif hardware_info.get("fp16"):
            recommendations["computation"] = "fp16"
            recommendations["storage"] = "fp32"
        elif hardware_info.get("bf16"):
            recommendations["computation"] = "bf16"
            recommendations["storage"] = "fp32"
        else:
            recommendations["computation"] = "fp32"
            recommendations["storage"] = "fp32"
        
        if hardware_info.get("memory_gb", 0) < 8:
            recommendations["cache"] = "int8"
            recommendations["network"] = "int4"
        else:
            recommendations["cache"] = "fp16"
            recommendations["network"] = "int8"
        
        self.set_precision_config(**recommendations)
        return recommendations
    
    def convert_for_inference(
        self,
        value: float,
        source_precision: str = "fp32"
    ) -> Dict[str, float]:
        """转换为推理精度 / Convert for inference"""
        result = {}
        
        for stage in ["storage", "computation", "network", "cache"]:
            precision = getattr(self.config, f"{stage}_precision")
            converted = self.matrix.convert_value(value, source_precision, precision)
            loss = self.matrix.estimate_loss(value, converted)
            result[stage] = {
                "value": converted,
                "precision": precision,
                "loss": loss,
            }
        
        return result
    
    def get_conversion_report(
        self,
        source: str,
        target: str
    ) -> Dict[str, Any]:
        """获取转换报告 / Get conversion report"""
        info = self.matrix.get_conversion(source, target)
        path = self.matrix.get_path(source, target)
        
        return {
            "direct_conversion": info,
            "optimal_path": path,
            "estimated_loss": info.loss_rate * 100 if info else 0,
            "performance_impact": info.performance_factor if info else 1.0,
        }


# 便捷函数
_precision_manager: Optional[PrecisionManager] = None


def _get_manager() -> PrecisionManager:
    """获取精度管理器 / Get precision manager"""
    global _precision_manager
    if _precision_manager is None:
        _precision_manager = PrecisionManager()
    return _precision_manager


def convert_precision(value: float, source: str, target: str) -> float:
    """便捷函数：转换精度 / Convert precision"""
    return _get_manager().matrix.convert_value(value, source, target)


def optimize_for_hardware(hardware_info: Dict[str, Any]) -> Dict[str, str]:
    """便捷函数：为硬件优化 / Optimize for hardware"""
    return _get_manager().optimize_for_hardware(hardware_info)


def create_precision_manager() -> PrecisionManager:
    """便捷函数：创建精度管理器"""
    return PrecisionManager()


def demo():
    """演示 / Demo"""
    print("🔢 精度转换矩阵演示")
    print("=" * 50)
    
    pm = PrecisionManager()
    matrix = pm.matrix
    
    print("\n📊 精度级别:")
    levels = ["fp64", "fp32", "fp16", "bf16", "int8", "int4"]
    for level in levels:
        bits = matrix._get_bit_width(level)
        print(f"  {level}: {bits} bits")
    
    print("\n🔄 转换示例 (FP32 -> FP16):")
    test_value = 3.14159265358979
    converted = matrix.convert_value(test_value, "fp32", "fp16")
    loss = matrix.estimate_loss(test_value, converted)
    
    print(f"  原始值: {test_value:.10f}")
    print(f"  转换值: {converted:.10f}")
    print(f"  绝对损失: {loss['absolute']:.10f}")
    print(f"  相对损失: {loss['relative']*100:.6f}%")
    print(f"  信噪比: {loss['db']:.2f} dB")
    
    print("\n📋 转换路径 (FP64 -> INT8):")
    path = matrix.get_path("fp64", "int8")
    for src, tgt in path:
        info = matrix.get_conversion(src, tgt)
        print(f"  {src} -> {tgt}: 损失={info.loss_rate*100:.2f}%, 性能={info.performance_factor:.1f}x")
    
    print("\n🎯 优化配置:")
    hardware = {
        "tensor_cores": True,
        "memory_gb": 16,
    }
    recommendations = pm.optimize_for_hardware(hardware)
    for stage, precision in recommendations.items():
        print(f"  {stage}: {precision}")
    
    print("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
