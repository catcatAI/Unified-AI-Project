"""
性能优化模块初始化文件
"""

import logging
logger = logging.getLogger(__name__)

from .performance_optimizer import (
    PerformanceOptimizer,
    get_performance_optimizer,
    cache_result,
    start_performance_monitoring,
    stop_performance_monitoring
)

__all__ = [
    'PerformanceOptimizer',
    'get_performance_optimizer',
    'cache_result',
    'start_performance_monitoring',
    'stop_performance_monitoring'
]
