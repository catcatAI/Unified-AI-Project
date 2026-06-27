"""
Core Allocation Module — 決策系統重構 Phase 2-3
================================================

Phase 2: 決策重構
  - resonance.py: ResonanceEngine — 語義共振統一引擎
  - policy.py: AllocationPolicy — 規則化分配策略（替代 if-elif 鏈）
  - negativity.py: NegativityDetector — θ 自糾系統（從 StateMatrix 分離）

Author: Angela AI v6.2
Version: 6.2.1
"""

try:
    from core.allocation.resonance import (
        ResonanceEngine,
        ResonanceProfile,
        ResonanceResult,
    )
except ImportError:
    ResonanceEngine = ResonanceResult = ResonanceProfile = None

try:
    from core.allocation.policy import (
        AllocationAction,
        AllocationContext,
        AllocationDecision,
        AllocationPolicy,
        AllocationStage,
        AssignStage,
        CompositeStage,
        CreateStage,
        DeferStage,
    )
except ImportError:
    AllocationPolicy = AllocationAction = AllocationContext = AllocationDecision = None
    AllocationStage = AssignStage = CompositeStage = CreateStage = DeferStage = None

try:
    from core.allocation.negativity import (
        CorrectionResult,
        DetectionResult,
        NegativityDetector,
    )
except ImportError:
    NegativityDetector = DetectionResult = CorrectionResult = None

__all__ = [
    "ResonanceEngine",
    "ResonanceResult",
    "ResonanceProfile",
    "AllocationPolicy",
    "AllocationAction",
    "AllocationContext",
    "AllocationDecision",
    "AllocationStage",
    "AssignStage",
    "CompositeStage",
    "CreateStage",
    "DeferStage",
    "NegativityDetector",
    "DetectionResult",
    "CorrectionResult",
]