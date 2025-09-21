"""
System Module for Unified-AI-Project

This module provides hardware detection, deployment management, and system optimization
capabilities for the Unified AI Project. It enables adaptive deployment across different
hardware configurations and operating systems.

Key Components:
- HardwareProbe: Comprehensive hardware detection and profiling
- DeploymentManager: Intelligent deployment configuration based on hardware
- Adaptive configuration for different performance tiers
"""

from .hardware_probe import (
    HardwareProbe,
    HardwareProfile,
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    StorageInfo,
    NetworkInfo,
    get_hardware_profile,
    get_performance_tier,
    get_ai_capability_score
)

from .deployment_manager import (
    DeploymentManager,
    DeploymentConfig,
    DeploymentMode,
    ModelSize,
    ModelConfig,
    CompressionConfig,
    ProcessingConfig,
    get_deployment_config,
    apply_optimal_config,
    get_deployment_mode
)

from .integrated_graphics_optimizer import (
    IntegratedGraphicsOptimizer,
    optimize_for_integrated_graphics,
    get_integrated_graphics_recommendations
)

__all__ = [
    # Hardware Detection
    'HardwareProbe',
    'HardwareProfile',
    'CPUInfo',
    'GPUInfo', 
    'MemoryInfo',
    'StorageInfo',
    'NetworkInfo',
    'get_hardware_profile',
    'get_performance_tier',
    'get_ai_capability_score',
    
    # Deployment Management
    'DeploymentManager',
    'DeploymentConfig',
    'DeploymentMode',
    'ModelSize',
    'ModelConfig',
    'CompressionConfig',
    'ProcessingConfig',
    'get_deployment_config',
    'apply_optimal_config',
    'get_deployment_mode',
    
    # Integrated Graphics Optimization
    'IntegratedGraphicsOptimizer',
    'optimize_for_integrated_graphics',
    'get_integrated_graphics_recommendations'
]