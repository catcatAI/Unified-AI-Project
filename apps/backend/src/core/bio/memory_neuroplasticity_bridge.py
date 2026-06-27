"""
Angela AI v6.0 - Memory-Neuroplasticity Bridge
记忆-神经可塑性桥接

Bridges the gap between explicit memory systems (CDM/LU/HSM/HAM) and the
biological neuroplasticity system for memory reinforcement and forgetting.

Features:
- Connects memory systems with neuroplasticity
- Memory reinforcement through biological mechanisms
- Biologically-inspired forgetting
- Memory consolidation triggers

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

# Backward compatibility alias (2026-06-07)
# Real implementation is NeuroplasticitySystem in neuroplasticity_core.py
try:
    from .neuroplasticity_core import NeuroplasticitySystem as MemoryConsolidation
    from .neuroplasticity_core import NeuroplasticitySystem as MemoryNeuroplasticityBridge
except ImportError:
    MemoryNeuroplasticityBridge = None
    MemoryConsolidation = None
