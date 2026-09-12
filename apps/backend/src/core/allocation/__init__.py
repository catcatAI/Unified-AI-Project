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

from typing import Any

# 延遲降級綁定先預聲明（R16；同 handlers/__init__ R14 模式）。
ResonanceEngine: Any
ResonanceProfile: Any
ResonanceResult: Any
try:
    from core.allocation.resonance import (
        ResonanceEngine,
        ResonanceProfile,
        ResonanceResult,
    )
except ImportError:
    ResonanceEngine = ResonanceResult = ResonanceProfile = None

AllocationAction: Any
AllocationContext: Any
AllocationDecision: Any
AllocationPolicy: Any
AssignStage: Any
CompositeStage: Any
CreateStage: Any
DeferStage: Any
try:
    from core.allocation.policy import (
        AllocationAction,
        AllocationContext,
        AllocationDecision,
        AllocationPolicy,
        AssignStage,
        CompositeStage,
        CreateStage,
        DeferStage,
    )
except ImportError:
    AllocationPolicy = AllocationAction = AllocationContext = AllocationDecision = None
    AssignStage = CompositeStage = CreateStage = DeferStage = None

CorrectionResult: Any
DetectionResult: Any
NegativityDetector: Any
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
    "AssignStage",
    "CompositeStage",
    "CreateStage",
    "DeferStage",
    "NegativityDetector",
    "DetectionResult",
    "CorrectionResult",
]
