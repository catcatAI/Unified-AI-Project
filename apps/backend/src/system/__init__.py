"""
System Module for Unified-AI-Project:
This module provides hardware detection, deployment management, and system optimization
capabilities for the Unified AI Project.
"""

# Hardware Detection
from .hardware_probe import (
import logging
logger = logging.getLogger(__name__)
    HardwareProbe,
    HardwareProfile,
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    StorageInfo,
    NetworkInfo,
    get_hardware_profile
)

# Deployment Management
from .deployment_manager import (
    DeploymentManager,
    DeploymentConfig,
    DeploymentMode,
    ModelSize,
    ModelConfig,
    CompressionConfig,
    ProcessingConfig,
    get_deployment_config
)

# Integrated Graphics Optimization
from .integrated_graphics_optimizer import (
    IntegratedGraphicsOptimizer,
    optimize_for_integrated_graphics
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
    
    # Deployment Management
    'DeploymentManager',
    'DeploymentConfig',
    'DeploymentMode',
    'ModelSize',
    'ModelConfig',
    'CompressionConfig',
    'ProcessingConfig',
    'get_deployment_config',
    
    # Integrated Graphics Optimization
    'IntegratedGraphicsOptimizer',
    'optimize_for_integrated_graphics'
]
