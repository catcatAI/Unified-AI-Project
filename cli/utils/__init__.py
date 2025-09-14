#!/usr/bin/env python3
"""
Unified AI Project CLI 工具模块初始化文件
"""

from .logger import debug, info, warning, error, critical, set_level, get_level
from .environment import check_environment, setup_environment

__all__ = [
    'debug', 'info', 'warning', 'error', 'critical', 
    'set_level', 'get_level',
    'check_environment', 'setup_environment'
]