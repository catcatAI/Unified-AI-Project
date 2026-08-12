# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L3+]
# =============================================================================
"""
Backbone — Unified registration, routing, configuration, and lifecycle.

Replaces ~100 scattered singleton factories with a single access point.

Usage:
    from core.backbone import get_backbone
    bb = get_backbone()
    bb.initialize()
    
    # Unified access
    intent = bb.engine("intent")
    memory = bb.memory()
    emotion = bb.emotion()
"""

from .backbone import Backbone, get_backbone
from .hardware import HardwareProfile

__all__ = ["Backbone", "get_backbone", "HardwareProfile"]
