"""
Angela AI v6.0 - Hardware Support Module
硬件支持模块

Multi-architecture, multi-hardware, multi-precision support system.
跨架构、跨硬件、跨精度支持系统。

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from .hal import (
    ArchitectureType,
    InstructionSet,
    HardwareVendor,
    ComputeUnit,
    PrecisionLevel,
    OperatingSystem,
    HardwareCapabilities,
    HardwareMetrics,
    HardwareDetector,
    HardwareManager,
    HardwareFactory,
    detect_hardware,
    create_hardware_manager,
)

from .precision_matrix import (
    PrecisionConfig,
    PrecisionMatrix,
    PrecisionManager,
    ConversionInfo,
    convert_precision,
    optimize_for_hardware,
    create_precision_manager,
)

from .compute_matrix import (
    OptimizationStrategy,
    MemoryLayout,
    KernelConfig,
    OptimizationResult,
    ComputationMatrix,
    ComputeOptimizer,
    get_optimization,
    create_compute_optimizer,
)

__version__ = "6.0.0"
__author__ = "Angela AI Development Team"

__all__ = [
    # Architecture & Hardware
    "ArchitectureType",
    "InstructionSet",
    "HardwareVendor",
    "ComputeUnit",
    "PrecisionLevel",
    "OperatingSystem",
    "HardwareCapabilities",
    "HardwareMetrics",
    "HardwareDetector",
    "HardwareManager",
    "HardwareFactory",
    "detect_hardware",
    "create_hardware_manager",
    
    # Precision Management
    "PrecisionConfig",
    "PrecisionMatrix",
    "PrecisionManager",
    "ConversionInfo",
    "convert_precision",
    "optimize_for_hardware",
    "create_precision_manager",
    
    # Computation Optimization
    "OptimizationStrategy",
    "MemoryLayout",
    "KernelConfig",
    "OptimizationResult",
    "ComputationMatrix",
    "ComputeOptimizer",
    "get_optimization",
    "create_compute_optimizer",
]
