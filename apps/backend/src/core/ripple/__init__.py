"""
Core Ripple Module — Phase 5
"""

from typing import Any

# 延遲降級綁定先預聲明（R16；同 handlers/__init__ R14 模式）。
RippleNode: Any
RippleDepth: Any
AlgorithmDepth: Any
MathOp: Any
CascadeStrategy: Any
LinearCascade: Any
ExponentialCascade: Any
AdaptiveCascade: Any
AxisRippleApplicator: Any
AlphaRippleApplicator: Any
BetaRippleApplicator: Any
GammaRippleApplicator: Any
DeltaRippleApplicator: Any
ThetaRippleApplicator: Any
EpsilonRippleApplicator: Any
RippleApplicatorRegistry: Any
RippleAccumulator: Any
try:
    from core.ripple.node import (
        AdaptiveCascade,
        AlgorithmDepth,
        AlphaRippleApplicator,
        AxisRippleApplicator,
        BetaRippleApplicator,
        CascadeStrategy,
        DeltaRippleApplicator,
        EpsilonRippleApplicator,
        ExponentialCascade,
        GammaRippleApplicator,
        LinearCascade,
        MathOp,
        RippleAccumulator,
        RippleApplicatorRegistry,
        RippleDepth,
        RippleNode,
        ThetaRippleApplicator,
    )
except ImportError:
    RippleNode = RippleDepth = AlgorithmDepth = MathOp = CascadeStrategy = None
    LinearCascade = ExponentialCascade = AdaptiveCascade = None
    AxisRippleApplicator = AlphaRippleApplicator = BetaRippleApplicator = None
    GammaRippleApplicator = DeltaRippleApplicator = ThetaRippleApplicator = None
    EpsilonRippleApplicator = RippleApplicatorRegistry = RippleAccumulator = None

__all__ = [
    "RippleNode",
    "RippleDepth",
    "AlgorithmDepth",
    "MathOp",
    "CascadeStrategy",
    "LinearCascade",
    "ExponentialCascade",
    "AdaptiveCascade",
    "AxisRippleApplicator",
    "AlphaRippleApplicator",
    "BetaRippleApplicator",
    "GammaRippleApplicator",
    "DeltaRippleApplicator",
    "ThetaRippleApplicator",
    "EpsilonRippleApplicator",
    "RippleApplicatorRegistry",
    "RippleAccumulator",
]
