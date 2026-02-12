"""
Core Services Module

Provides core services for Angela AI Matrix.
"""

import logging
logger = logging.getLogger(__name__)

from .hardware_detector import HardwareDetector, HardwareAdapter, AcceleratorType
from .dynamic_scheduler import DynamicScheduler, get_scheduler, ComputeResource, ModelRequirement
from .multi_llm_service import MultiLLMService, ModelConfig

__all__ = [
    'HardwareDetector',
    'HardwareAdapter',
    'AcceleratorType',
    'DynamicScheduler',
    'get_scheduler',
    'ComputeResource',
    'ModelRequirement',
    'MultiLLMService',
    'ModelConfig'
]
