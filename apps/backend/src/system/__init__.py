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
    'get_deployment_mode'
]

# Quick setup function for easy integration
def initialize_system() -> dict:
    """
    Initialize the system with optimal configuration based on hardware.
    Returns a dictionary with system information and applied settings.
    """
    try:
        # Get hardware profile
        hardware_profile = get_hardware_profile()
        
        # Apply optimal configuration
        settings = apply_optimal_config()
        
        # Return summary
        return {
            'hardware_profile': hardware_profile,
            'deployment_settings': settings,
            'performance_tier': hardware_profile.performance_tier,
            'ai_capability_score': hardware_profile.ai_capability_score,
            'deployment_mode': get_deployment_mode().value,
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'fallback': True
        }

# Version info
__version__ = "1.0.0"
__author__ = "Unified AI Project Team"
__description__ = "Hardware-adaptive AI deployment system"