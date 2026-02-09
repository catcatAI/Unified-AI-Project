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

from .unified_hardware_center import (
    UnifiedHardwareCenter,
    HardwareDetector,
    PrecisionManager,
    CodeTranspiler,
    ModelRepository,
    AcceleratorType,
    PrecisionLevel,
    PerformanceMode,
    ComputeResource,
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    HardwareProfile,
    ModelRequirement,
    get_hardware_center,
    create_hardware_center
)

from .gpu_accelerator import (
    GPUAcceleratorService,
    GPUPriority,
    RenderQuality,
    GPUContext,
    GPUMetrics,
    get_gpu_service,
    initialize_gpu_service,
    gpu_available
)

from .webgl_bridge import (
    WebGLBridge,
    WebGLGPUInfo,
    get_webgl_bridge,
    handle_gpu_info_message
)

__all__ = [
    # 類
    'UnifiedHardwareCenter',
    'HardwareDetector',
    'PrecisionManager',
    'CodeTranspiler',
    'ModelRepository',
    'GPUAcceleratorService',
    'WebGLBridge',
    # 枚舉
    'AcceleratorType',
    'PrecisionLevel',
    'PerformanceMode',
    'GPUPriority',
    'RenderQuality',
    # 數據類
    'ComputeResource',
    'CPUInfo',
    'GPUInfo',
    'MemoryInfo',
    'HardwareProfile',
    'ModelRequirement',
    'GPUContext',
    'GPUMetrics',
    'WebGLGPUInfo',
    # 函數
    'get_hardware_center',
    'create_hardware_center',
    'get_gpu_service',
    'initialize_gpu_service',
    'gpu_available',
    'get_webgl_bridge',
    'handle_gpu_info_message'
]