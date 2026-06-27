"""
Core Influence Module — Phase 6
"""

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