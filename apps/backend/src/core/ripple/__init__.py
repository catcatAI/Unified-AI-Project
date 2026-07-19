"""
Core Ripple Module — Phase 5
"""

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
