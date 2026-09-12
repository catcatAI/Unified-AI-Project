"""
Core Influence Module — Phase 6
"""

from typing import Any

# 延遲降級綁定先預聲明（R16；同 handlers/__init__ R14 模式）。
ConflictStrategy: Any
EntropyRule: Any
GravityRule: Any
InfluenceResult: Any
InfluenceRule: Any
InfluenceRuleSet: Any
InfluenceSpace: Any
MemoryRule: Any
WeightRule: Any
try:
    from core.influence.space import (
        ConflictStrategy,
        EntropyRule,
        GravityRule,
        InfluenceResult,
        InfluenceRule,
        InfluenceRuleSet,
        InfluenceSpace,
        MemoryRule,
        WeightRule,
    )
except ImportError:
    InfluenceSpace = InfluenceRule = InfluenceRuleSet = InfluenceResult = None
    GravityRule = EntropyRule = MemoryRule = WeightRule = ConflictStrategy = None

__all__ = [
    "InfluenceSpace",
    "InfluenceRule",
    "InfluenceRuleSet",
    "InfluenceResult",
    "GravityRule",
    "EntropyRule",
    "MemoryRule",
    "WeightRule",
    "ConflictStrategy",
]
