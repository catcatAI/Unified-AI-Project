"""
Hardware Module - Angela AI Matrix
==================================
統一硬件資源總控中心

主要類:
- UnifiedHardwareCenter: 總控中心單例
- HardwareDetector: 硬件檢測
- PrecisionManager: 精度管理
- CodeTranspiler: 代碼轉譯
- ModelRepository: 模型倉庫

使用方式:
    from core.hardware import get_hardware_center

    center = await get_hardware_center()
    profile = center.get_hardware_profile()
"""

import logging

logger = logging.getLogger(__name__)

from .gpu_accelerator import (  # noqa: E402
    GPUAcceleratorService,
    GPUContext,
    GPUMetrics,
    GPUPriority,
    RenderQuality,
    get_gpu_service,
    gpu_available,
    initialize_gpu_service,
)
from .unified_hardware_center import (  # noqa: E402
    AcceleratorType,
    CodeTranspiler,
    ComputeResource,
    CPUInfo,
    GPUInfo,
    HardwareDetector,
    HardwareProfile,
    MemoryInfo,
    ModelRepository,
    ModelRequirement,
    PerformanceMode,
    PrecisionLevel,
    PrecisionManager,
    UnifiedHardwareCenter,
    get_hardware_center,
)
from .webgl_bridge import (  # noqa: E402
    WebGLBridge,
    WebGLGPUInfo,
    get_webgl_bridge,
    handle_gpu_info_message,
)

__all__ = [
    # 類
    "UnifiedHardwareCenter",
    "HardwareDetector",
    "PrecisionManager",
    "CodeTranspiler",
    "ModelRepository",
    "GPUAcceleratorService",
    "WebGLBridge",
    # 枚舉
    "AcceleratorType",
    "PrecisionLevel",
    "PerformanceMode",
    "GPUPriority",
    "RenderQuality",
    # 數據類
    "ComputeResource",
    "CPUInfo",
    "GPUInfo",
    "MemoryInfo",
    "HardwareProfile",
    "ModelRequirement",
    "GPUContext",
    "GPUMetrics",
    "WebGLGPUInfo",
    # 函數
    "get_hardware_center",
    "get_gpu_service",
    "initialize_gpu_service",
    "gpu_available",
    "get_webgl_bridge",
    "handle_gpu_info_message",
]
