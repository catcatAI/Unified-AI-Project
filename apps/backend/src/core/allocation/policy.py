"""
Allocation Policy — 分配策略系統
=================================

將 meta_allocate 的 if-elif 鏈重構為規則化 stages。
每個 stage 是獨立的條件評估器，結果可組合、可測試、可配置。

使用方式:
    from core.allocation.policy import AllocationPolicy, AllocationAction

    policy = AllocationPolicy()
    decision = policy.decide(context=AllocationContext(
        vector=input_vector,
        label='user_query',
        entropy=0.3,
        novelty=0.4,
        active_dims=3,
    ))

    if decision.action == AllocationAction.ASSIGN:
        axis = decision.target

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AllocationAction(Enum):
    """分配動作枚舉 / Allocation action types"""
    ASSIGN = "assign"
    COMPOSITE = "composite"
    CREATE = "create"
    DEFER = "defer"


@dataclass
class AllocationContext:
    """分配上下文 / Context for allocation decision"""
    vector: List[float]
    label: str = ""
    similarities: Dict[str, float] = field(default_factory=dict)
    max_resonance: float = 0.0
    best_axis: Optional[str] = None
    num_high_sim: int = 0
    entropy: float = 0.0
    active_dims: int = 0
    novelty: float = 0.0
    complexity: float = 0.0
    dimension_fit: float = 0.0
    buffer_tracking: Dict[str, int] = field(default_factory=dict)


@dataclass
class AllocationDecision:
    """分配決策結果 / Result of allocation decision"""
    action: AllocationAction
    target: Optional[str] = None
    targets: Optional[List[Tuple[str, float]]] = None
    proposed_name: Optional[str] = None
    buffer: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""

    def __repr__(self) -> str:
        parts = [f"AllocationDecision({self.action.name}"]
        if self.target:
            parts.append(f"target={self.target}")
        if self.buffer:
            parts.append(f"buffer={self.buffer}")
        parts.append(f"conf={self.confidence:.2f})")
        return " ".join(parts)


class BaseStage:
    """基本評估階段 / Base evaluation stage"""

    name: str = "BaseStage"

    def matches(self, context: AllocationContext) -> bool:
        raise NotImplementedError

    def decide(self, context: AllocationContext) -> AllocationDecision:
        raise NotImplementedError


class AssignStage(BaseStage):
    """分配階段 / Assign stage"""

    name = "AssignStage"

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def matches(self, context: AllocationContext) -> bool:
        return context.max_resonance >= self.threshold and context.best_axis is not None

    def decide(self, context: AllocationContext) -> AllocationDecision:
        return AllocationDecision(
            action=AllocationAction.ASSIGN,
            target=context.best_axis,
            confidence=context.max_resonance,
            reasoning=f"AssignStage: resonance {context.max_resonance:.2f} >= {self.threshold}",
        )


class CompositeStage(BaseStage):
    """複合分配階段 / Composite assign stage"""

    name = "CompositeStage"

    def __init__(self, threshold: float = 0.3, min_axes: int = 2):
        self.threshold = threshold
        self.min_axes = min_axes

    def matches(self, context: AllocationContext) -> bool:
        return context.num_high_sim >= self.min_axes

    def decide(self, context: AllocationContext) -> AllocationDecision:
        sorted_axes = sorted(
            context.similarities.items(), key=lambda x: x[1], reverse=True
        )[:context.num_high_sim]
        avg_sim = sum(s for _, s in sorted_axes) / max(1, len(sorted_axes))
        return AllocationDecision(
            action=AllocationAction.COMPOSITE,
            targets=[(name, sim) for name, sim in sorted_axes],
            confidence=avg_sim,
            reasoning=f"CompositeStage: {context.num_high_sim} axes above threshold",
        )


class CreateStage(BaseStage):
    """創建階段 / Create stage"""

    name = "CreateStage"

    def __init__(self, novelty_threshold: float = 0.8, complexity_min: int = 3):
        self.novelty_threshold = novelty_threshold
        self.complexity_min = complexity_min

    def matches(self, context: AllocationContext) -> bool:
        return context.novelty >= self.novelty_threshold and context.active_dims >= self.complexity_min

    def decide(self, context: AllocationContext) -> AllocationDecision:
        return AllocationDecision(
            action=AllocationAction.CREATE,
            proposed_name=context.label or "new_axis",
            confidence=min(1.0, context.novelty * 1.2),
            reasoning=f"CreateStage: novelty {context.novelty:.2f} >= {self.novelty_threshold}",
        )


class DeferStage(BaseStage):
    """延遲階段 / Defer stage"""

    name = "DeferStage"

    def __init__(self, fallback: bool = True):
        self.fallback = fallback

    def matches(self, context: AllocationContext) -> bool:
        return self.fallback

    def decide(self, context: AllocationContext) -> AllocationDecision:
        return AllocationDecision(
            action=AllocationAction.DEFER,
            buffer="unclassified_experiences",
            confidence=0.3,
            reasoning=f"DeferStage: no stage matched (resonance {context.max_resonance:.2f})",
        )


class AllocationPolicy:
    """
    分配策略 / Allocation Policy

    實現分階段的分配邏輯，替換 meta_allocate 的 if-elif 鏈。
    提供可配置的 stages，每個 stage 獨立評估條件並返回動作。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.config.update(kwargs)
        self._stages: List[BaseStage] = self._build_default_stages()

    def _build_default_stages(self) -> List[BaseStage]:
        stages: List[BaseStage] = []
        if self.config.get("enable_composite", True):
            stages.append(CompositeStage(
                threshold=self.config.get("composite_threshold", 0.3),
                min_axes=self.config.get("composite_min_axes", 2),
            ))
        if self.config.get("enable_assign", True):
            stages.append(AssignStage(threshold=self.config.get("assign_threshold", 0.5)))
        if self.config.get("enable_create", True):
            stages.append(CreateStage(
                novelty_threshold=self.config.get("create_novelty_threshold", 0.8),
                complexity_min=self.config.get("create_complexity_min", 3),
            ))
        stages.append(DeferStage(fallback=True))
        return stages

    @property
    def stages(self) -> List[BaseStage]:
        return self._stages

    def add_stage(self, stage: BaseStage) -> None:
        self._stages.append(stage)

    def remove_stage(self, name: str) -> bool:
        for i, s in enumerate(self._stages):
            if s.name == name:
                self._stages.pop(i)
                return True
        return False

    def decide(self, context: AllocationContext) -> AllocationDecision:
        """
        執行分配決策 / Execute allocation decision

        Args:
            context: 分配上下文

        Returns:
            AllocationDecision: 分配決策結果
        """
        for stage in self._stages:
            if stage.matches(context):
                return stage.decide(context)
        return DeferStage(fallback=True).decide(context)

    def decide_from_profile(self, vector: List[float], profile: Any, label: str = "") -> AllocationDecision:
        """
        從配置文件執行分配決策 / Execute decision from a profile object

        Args:
            vector: 輸入向量
            profile: 配置對象（需有 similarities, best_axis, max_resonance 等屬性）
            label: 可選標籤

        Returns:
            AllocationDecision: 分配決策結果
        """
        ctx = AllocationContext(
            vector=vector,
            label=label,
            similarities=getattr(profile, "similarities", {}),
            max_resonance=getattr(profile, "max_resonance", 0.0),
            best_axis=getattr(profile, "best_axis", None),
            num_high_sim=getattr(profile, "num_high_sim", 0),
            entropy=getattr(profile, "entropy", 0.0),
            active_dims=getattr(profile, "active_count", 0),
            novelty=getattr(profile, "novelty", 0.0),
            complexity=getattr(profile, "complexity", 0.0),
        )
        return self.decide(ctx)
