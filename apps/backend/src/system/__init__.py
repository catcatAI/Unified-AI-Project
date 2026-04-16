"""
System Module for Unified-AI-Project:
This module provides hardware detection, deployment management, and system optimization
capabilities for the Unified AI Project.
"""

import logging

logger = logging.getLogger(__name__)

# Hardware detection was moved to core.hardware.unified_hardware_center

# Deployment Management (Moved/Consolidated)

# Integrated Graphics Optimization
from .integrated_graphics_optimizer import (
    IntegratedGraphicsOptimizer,
    optimize_for_integrated_graphics,
)

__all__ = [
    # Integrated Graphics Optimization
    "IntegratedGraphicsOptimizer",
    "optimize_for_integrated_graphics",
]
