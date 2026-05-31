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
from typing import Dict, List, Optional, Tuple, Any, Callable
import logging

logger = logging.getLogger(__name__)


class AllocationAction(Enum):
    """分配動作類型"""
    ASSIGN = "assign_to_axis"
    COMPOSITE = "composite_assign"
    CREATE = "create_axis"
    DEFER = "defer_to_buffer"


@dataclass
class AllocationContext:
    """
    分配決策的上下文

    包含所有計算相似度後的元數據，
    供各個 stage 評估使用。
    """
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
    time_in_buffer: int = 0


@dataclass
class AllocationDecision:
    """
    分配決策結果

    兼容舊的 AllocateDecision 結構，
    但字段更清晰。
    """
    action: AllocationAction
    target: Optional[str] = None
    targets: Optional[List[Tuple[str, float]]] = None
    proposed_name: Optional[str] = None
    semantic_anchor: Optional[List[float]] = None
    confidence: float = 0.0
    reasoning: str = ""
    buffer: Optional[str] = None

    def __repr__(self) -> str:
        if self.action == AllocationAction.ASSIGN:
            return f"Decision(ASSIGN → {self.target}, conf={self.confidence:.2f})"
        elif self.action == AllocationAction.COMPOSITE:
            axes = [f"{n}({v:.2f})" for n, v in (self.targets or [])]
            return f"Decision(COMPOSITE [{', '.join(axes)}], conf={self.confidence:.2f})"
        elif self.action == AllocationAction.CREATE:
            return f"Decision(CREATE '{self.proposed_name}', conf={self.confidence:.2f})"
        else:
            return f"Decision(DEFER to {self.buffer}, conf={self.confidence:.2f})"


class AllocationStage:
    """
    分配決策的一個階段

    每個 stage 有：
    - evaluate(): 檢查條件是否滿足
    - decide(): 條件滿足時生成決策

    Stage 按順序評估，第一個匹配的決定結果。
    """

    name: str

    def matches(self, ctx: AllocationContext) -> bool:
        """此 stage 的條件是否匹配"""
        logger.warning("[Stage.matches] Not implemented — stub")
        return False

    def decide(self, ctx: AllocationContext) -> AllocationDecision:
        """生成決策"""
        logger.warning("[Stage.decide] Not implemented — stub")
        return AllocationDecision(action=AllocationAction.DEFER, reasoning="Not implemented")

    def evaluate(self, ctx: AllocationContext) -> Optional[AllocationDecision]:
        """如果匹配則返回決策，否則返回 None"""
        if self.matches(ctx):
            return self.decide(ctx)
        return None


class AssignStage(AllocationStage):
    """Stage 1: 高相似度 → 直接分配到單軸"""

    def __init__(self, threshold: float = 0.7):
        self.name = "AssignStage"
        self.threshold = threshold

    def matches(self, ctx: AllocationContext) -> bool:
        return ctx.max_resonance > self.threshold and ctx.best_axis is not None

    def decide(self, ctx: AllocationContext) -> AllocationDecision:
        return AllocationDecision(
            action=AllocationAction.ASSIGN,
            target=ctx.best_axis,
            confidence=ctx.max_resonance,
            reasoning=f"高相似度匹配現有軸 {ctx.best_axis} (sim={ctx.max_resonance:.2f})",
        )


class CompositeStage(AllocationStage):
    """Stage 2: 多軸部分匹配 → 複合分配"""

    def __init__(self, threshold: float = 0.3, min_axes: int = 2):
        self.name = "CompositeStage"
        self.threshold = threshold
        self.min_axes = min_axes

    def matches(self, ctx: AllocationContext) -> bool:
        return ctx.num_high_sim >= self.min_axes and ctx.max_resonance > self.threshold

    def decide(self, ctx: AllocationContext) -> AllocationDecision:
        top_axes = sorted(
            [(n, s) for n, s in ctx.similarities.items() if s > self.threshold],
            key=lambda x: -x[1]
        )[:3]

        if not top_axes:
            return AllocationDecision(
                action=AllocationAction.DEFER,
                confidence=0.0,
                reasoning="CompositeStage matched but no axes above threshold",
            )

        confidence = sum(s for _, s in top_axes) / len(top_axes)
        return AllocationDecision(
            action=AllocationAction.COMPOSITE,
            targets=top_axes,
            confidence=confidence,
            reasoning=f"多軸部分匹配：{', '.join(f'{k}({v:.2f})' for k, v in top_axes)}",
        )


class CreateStage(AllocationStage):
    """Stage 3: 高新穎度 + 多軸參與 → 建議創建新軸"""

    def __init__(self, novelty_threshold: float = 0.6, complexity_min: int = 2):
        self.name = "CreateStage"
        self.novelty_threshold = novelty_threshold
        self.complexity_min = complexity_min

    def matches(self, ctx: AllocationContext) -> bool:
        return ctx.novelty > self.novelty_threshold and ctx.active_dims >= self.complexity_min

    def decide(self, ctx: AllocationContext) -> AllocationDecision:
        proposed = ctx.label if ctx.label else "new_axis"

        if ctx.label and ctx.label in ctx.buffer_tracking:
            count = ctx.buffer_tracking[ctx.label]
            if count >= 5:
                proposed = ctx.label

        return AllocationDecision(
            action=AllocationAction.CREATE,
            proposed_name=proposed,
            semantic_anchor=ctx.vector,
            confidence=0.5,
            reasoning=f"新穎度={ctx.novelty:.2f}，複雜度={ctx.active_dims}，建議創建新軸",
        )


class DeferStage(AllocationStage):
    """Stage 4: 默認 → 緩存"""

    def __init__(self, fallback: bool = True):
        self.name = "DeferStage"
        self.fallback = fallback

    def matches(self, ctx: AllocationContext) -> bool:
        return self.fallback

    def decide(self, ctx: AllocationContext) -> AllocationDecision:
        return AllocationDecision(
            action=AllocationAction.DEFER,
            buffer="unclassified_experiences",
            confidence=0.3,
            reasoning=f"模糊地帶，最大相似度={ctx.max_resonance:.2f}，緩存等待更多數據",
        )


class AllocationPolicy:
    """
    分配策略
    ========

    將舊的 if-elif-elif-elif 鏈替換為可配置的 stages 鏈。
    每個 stage 獨立可測試，可動態添加/移除。

    默認 stages（按順序）:
    1. AssignStage (threshold=0.7)
    2. CompositeStage (threshold=0.3, min_axes=2)
    3. CreateStage (novelty=0.6, complexity=2)
    4. DeferStage (fallback=True)
    """

    def __init__(
        self,
        stages: Optional[List[AllocationStage]] = None,
        enable_create: bool = True,
        enable_composite: bool = True,
    ):
        if stages:
            self.stages = stages
        else:
            self.stages = [
                AssignStage(threshold=0.55),
            ]
            if enable_composite:
                self.stages.append(CompositeStage(threshold=0.3, min_axes=2))
            if enable_create:
                self.stages.append(CreateStage(novelty_threshold=0.6, complexity_min=2))
            self.stages.append(DeferStage(fallback=True))

    def decide(self, ctx: AllocationContext) -> AllocationDecision:
        """
        評估所有 stages，返回第一個匹配的決策

        Args:
            ctx: 分配上下文（包含相似度/新穎度/複雜度等）

        Returns:
            AllocationDecision
        """
        for stage in self.stages:
            decision = stage.evaluate(ctx)
            if decision is not None:
                logger.debug(f"[AllocationPolicy] Stage '{stage.name}' matched: {decision}")
                return decision

        return self.stages[-1].decide(ctx)

    def decide_from_profile(
        self,
        vector: List[float],
        profile,
        label: str = "",
        buffer_tracking: Optional[Dict[str, int]] = None,
    ) -> AllocationDecision:
        """
        從 ResonanceProfile 直接構造決策（便捷方法）

        Args:
            vector: 語義向量
            profile: ResonanceProfile
            label: 輸入標籤
            buffer_tracking: 緩存追蹤字典
        """
        ctx = AllocationContext(
            vector=vector,
            label=label,
            similarities=profile.similarities,
            max_resonance=profile.max_resonance,
            best_axis=profile.best_axis,
            num_high_sim=profile.num_high_sim,
            entropy=profile.entropy,
            active_dims=profile.active_count,
            novelty=1.0 - profile.max_resonance,
            complexity=float(profile.active_count) / max(1, len(profile.similarities)),
            dimension_fit=profile.max_resonance,
            buffer_tracking=buffer_tracking or {},
        )
        return self.decide(ctx)

    def add_stage(self, stage: AllocationStage) -> None:
        """動態添加一個 stage（在 DeferStage 之前）"""
        if self.stages and isinstance(self.stages[-1], DeferStage):
            self.stages.insert(-1, stage)
        else:
            self.stages.append(stage)

    def remove_stage(self, stage_name: str) -> bool:
        """移除指定名稱的 stage"""
        for i, s in enumerate(self.stages):
            if s.name == stage_name:
                self.stages.pop(i)
                return True
        return False

    def __repr__(self) -> str:
        return f"AllocationPolicy(stages={[s.name for s in self.stages]})"