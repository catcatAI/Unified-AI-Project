"""
Angela AI v6.2 - 6D State Matrix System (αβγδεθ)
六維狀態矩陣系統

獨立的狀態矩陣管理系統，整合所有維度的狀態。
Features:
- 6-dimensional state matrix (α, β, γ, δ, ε, θ)
- Inter-dimensional influence modeling
- State persistence and history
- Comprehensive state analysis
- Epsilon (ε) mathematical dimension [N.22-EPSILON]
- Theta (θ) meta-cognitive dimension [N.23-THETA]

Author: Angela AI Development Team
Version: 6.2.1
Date: 2026-05-13
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Callable

from core.autonomous.cognitive_operations import (
    CognitiveOp as _CognitiveOp,
    compute_spatial_influence_factor,
    perform_spatial_reasoning as _psr,
    get_dimension_value as _gdv,
    get_position as _gp,
    execute_thought_chain as _etc,
    evaluate_math_spatially,
    apply_intent_gravity,
    set_intent_target,
    apply_inter_dimensional_drag,
)

from datetime import datetime, timedelta
import asyncio
import json
import logging
import math
import numpy as np


logger = logging.getLogger(__name__)


# Alias CognitiveOp for backwards compatibility
CognitiveOp = _CognitiveOp


@dataclass
class AllocateDecision:
    """θ 轴的分配决策 / Meta-cognitive allocation decision"""
    action: str
    target: Optional[str] = None
    targets: Optional[List[Tuple[str, float]]] = None
    proposed_name: Optional[str] = None
    semantic_anchor: Optional[List[float]] = None
    buffer: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "targets": self.targets,
            "proposed_name": self.proposed_name,
            "buffer": self.buffer,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass
class AxisSemanticAnchor:
    """軸的語義錨點 / Semantic anchor for axis identity"""
    name: str
    label: str
    description: str
    semantic_vector: List[float]
    keywords: List[str]

    def compute_resonance(self, input_vector: List[float]) -> float:
        if len(input_vector) != len(self.semantic_vector):
            return 0.0
        norm_in = np.linalg.norm(input_vector)
        norm_anchor = np.linalg.norm(self.semantic_vector)
        if norm_in == 0 or norm_anchor == 0:
            return 0.0
        dot = sum(a * b for a, b in zip(input_vector, self.semantic_vector))
        return dot / (norm_in * norm_anchor)


# =============================================================================
# ANGELA-MATRIX: [L4] [γ] [A] [L8+]
# [Task N.20.5] 認知操作類型 / Cognitive Spatial Operations
# Extracted to cognitive_operations.py
# =============================================================================
CognitiveOp = None


@dataclass
class DimensionState:
    """
    维度状态 / Dimension State

    Represents the state of a single dimension in the 4D matrix.
    """

    name: str
    cn_name: str
    values: Dict[str, float]
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    # =============================================================================
    # ANGELA-MATRIX: [L3] [αβγδ] [A] [L5+]
    # [Task N.20.1] 座標系 AI：空間定址 (x, y, z)
    # =============================================================================
    coordinate: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    intent_vector: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    stability: float = 1.0

    def compute_coordinate(self) -> Tuple[float, float, float]:
        """根據當前維度值計算實際座標 / Compute actual coordinate from current values"""
        from config_loader import get_formula_config
        proj_conf = get_formula_config("spatial").get("projection_weights", {}).get(self.name, {})
        
        v = self.values
        n = self.name
        
        # 獲取縮放因子，默認為 1.0
        xf = proj_conf.get("x_factor", 1.0)
        yf = proj_conf.get("y_factor", 1.0)
        zf = proj_conf.get("z_factor", 1.0)

        if n == "alpha":
            comfort = v.get("comfort", 0.5)
            tension = v.get("tension", 0.0)
            energy = v.get("energy", 0.5)
            rest_need = v.get("rest_need", 0.5)
            arousal = v.get("arousal", 0.5)
            x = (comfort - tension) * xf
            y = (energy - rest_need) * yf
            z = (arousal - 0.5) * zf
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "beta":
            clarity = v.get("clarity", 0.5)
            confusion = v.get("confusion", 0.0)
            focus = v.get("focus", 0.5)
            learning = v.get("learning", 0.5)
            curiosity = v.get("curiosity", 0.5)
            creativity = v.get("creativity", 0.5)
            x = (clarity - confusion) * xf
            y = (focus + learning + curiosity) / 3.0 * yf
            z = (creativity - 0.5) * zf
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "gamma":
            happiness = v.get("happiness", 0.5)
            sadness = v.get("sadness", 0.0)
            anger = v.get("anger", 0.0)
            fear = v.get("fear", 0.0)
            trust = v.get("trust", 0.5)
            calm = v.get("calm", 0.5)
            love = v.get("love", 0.0)
            x = (happiness - sadness) * 5.0 + (anger - 0.5) * 2.0
            y = (happiness + trust + calm) / 3.0 * 5.0 + 2.0
            z = (love - fear) * 3.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "delta":
            bond = v.get("bond", 0.5)
            attention = v.get("attention", 0.5)
            presence = v.get("presence", 0.5)
            engagement = v.get("engagement", 0.5)
            intimacy = v.get("intimacy", 0.0)
            x = (bond - intimacy) * 3.0
            y = presence * 5.0
            z = (attention + engagement) / 2.0 * 10.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "epsilon":
            logic = v.get("logic", 0.5)
            precision = v.get("precision", 0.5)
            abstraction = v.get("abstraction_level", v.get("abstraction", 0.5))
            certainty = v.get("certainty", 0.5)
            fatigue = v.get("fatigue", 0.0)
            x = (logic + precision) / 2.0 * 5.0
            y = abstraction * 10.0
            z = (certainty - fatigue) * 5.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "theta":
            novelty = v.get("novelty", 0.5)
            creation_urge = v.get("creation_urge", 0.0)
            correction_urge = v.get("correction_urge", 0.0)
            complexity = v.get("complexity", 0.5)
            x = novelty * 5.0 - 2.5
            y = (creation_urge + correction_urge) * 5.0
            z = complexity * 10.0 - 5.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "zeta":
            temporal = v.get("temporal_coherence", 0.8)
            memory = v.get("memory_depth", 0.6)
            narrative = v.get("narrative_flow", 0.7)
            identity = v.get("identity_continuity", 0.75)
            x = (temporal - 0.5) * 10.0
            y = (memory + narrative) / 2.0 * 10.0
            z = (identity - 0.5) * 10.0
            return (round(x, 3), round(y, 3), round(z, 3))
        return (0.0, 0.0, 0.0)

    def get_average(self) -> float:
        """获取维度平均值 / Get average value"""
        if not self.values:
            return 0.0
        return sum(self.values.values()) / len(self.values)

    def get_dominant(self) -> Tuple[str, float]:
        """获取主导指标 / Get dominant metric"""
        if not self.values:
            return ("", 0.0)
        return max(self.values.items(), key=lambda x: x[1])

    def update(self, **kwargs) -> None:
        """更新维度值 / Update dimension values"""
        for key, value in kwargs.items():
            if key in self.values:
                self.values[key] = max(0.0, min(1.0, float(value)))
        self.timestamp = datetime.now()


class StateMatrix4D:
    """
    5D状态矩阵系统（αβγδεθ）/ 5D State Matrix System

    A comprehensive state management system that integrates all dimensions
    of Angela's internal state into a unified multi-dimensional matrix.

    Dimensions (now 6 including θ):
    - α (Alpha): Physiological (生理)
      - energy, comfort, arousal, rest_need
    - β (Beta): Cognitive (认知)
      - curiosity, focus, confusion, learning
    - γ (Gamma): Emotional (情感)
      - happiness, sadness, anger, fear, disgust, surprise, trust, anticipation
    - δ (Delta): Social (社交)
      - attention, bond, trust, presence
    - ε (Epsilon): Mathematical (數理) [Task N.22-EPSILON]
      - logic, precision, abstraction, certainty, complexity, fatigue
    - θ (Theta): Meta-Cognitive (元認知) [Task N.23-THETA]
      - novelty, complexity, ambiguity, dimension_fit, creation_urge

    Features:
    - Real-time state tracking
    - Inter-dimensional influence modeling
    - State history and persistence
    - Comprehensive state analysis
    - Event-driven state changes
    - [θ] Meta-cognitive axis allocation (自动决定输入如何映射到状态空间)
    - [θ] Dynamic axis creation (从经验中自动生成新维度)
    - [θ] Semantic anchor similarity computation (基于语义锚点的相似度分析)

    Example:
        >>> matrix = StateMatrix4D()
        >>>
        >>> # Update individual dimensions
        >>> matrix.update_alpha(energy=0.8, comfort=0.7)
        >>> matrix.update_beta(curiosity=0.9, focus=0.8)
        >>> matrix.update_gamma(happiness=0.85, trust=0.8)
        >>> matrix.update_delta(attention=0.9, bond=0.7)
        >>>
        >>> # Compute influences
        >>> matrix.compute_influences()
        >>>
        >>> # Get comprehensive analysis
        >>> analysis = matrix.get_analysis()
        >>> print(f"Overall state: {analysis['overall_state']}")
    """

    @property
    def precision(self) -> float:
        """獲取當前運算精度 (基於 Beta 維度的聚焦度)"""
        if hasattr(self, "beta"):
            return self.beta.values.get("focus", 1.0)
        return getattr(self, "_precision", 1.0)


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize 4D state matrix
        """
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        
        from config_loader import get_formula_config
        self.formula_config = get_formula_config("spatial")
        self.config = config or {}
        self._precision = 1.0 
        self._temporal_state: Optional[Any] = None
        self._temporal_synced = False

        self._setup_dimensions()
        self._setup_systems()
        self._setup_history()

    def _setup_dimensions(self):
        """設置維度初始狀態 (從分層配置讀取)"""
        from config_loader import get_formula_config
        matrix_conf = get_formula_config("matrix")
        dim_defs = matrix_conf.get("dimensions", {})
        
        # 動態初始化所有定義在配置中的維度
        self.dimensions = {}
        for name, d_cfg in dim_defs.items():
            state = DimensionState(
                name=name,
                cn_name=d_cfg.get("cn_name", name),
                values=d_cfg.get("initial_values", {}).copy(),
                weight=d_cfg.get("weight", 1.0),
                coordinate=tuple(d_cfg.get("initial_coordinate", [0.0, 0.0, 0.0]))
            )
            setattr(self, name, state) # 保持 self.alpha 等屬性兼容性
            self.dimensions[name] = state

    def _setup_systems(self):
        """設置子系統與矩陣常數"""
        from config_loader import get_formula_config
        matrix_conf = get_formula_config("matrix")
        limits = matrix_conf.get("system_limits", {})
        
        self.misallocation_log = []
        self.correction_audit_trail = []
        self.max_misallocation_log = limits.get("max_misallocation_log", 100)
        self.max_audit_trail = limits.get("max_audit_trail", 50)
        self.unclassified_buffer = []
        self.buffer_tracking = {}
        self.axis_creation_log = []
        
        # 加載影響矩陣 (Influence Matrix)
        spatial_conf = get_formula_config("spatial")
        self.influence_matrix = self.config.get(
            "influence_matrix", 
            spatial_conf.get("influence_matrix", {})
        )
        
        self.semantic_anchors = {}
        self._init_semantic_anchors()

    def _setup_history(self):
        """設置歷史紀錄與追蹤"""
        from config_loader import get_formula_config
        matrix_conf = get_formula_config("matrix")
        limits = matrix_conf.get("system_limits", {})

        self.history = []
        self.max_history = self.config.get("max_history", limits.get("max_history", 1000))
        self.update_count = 0
        self.created_at = datetime.now()
        self.last_update = datetime.now()
        self._change_callbacks = []
        self._threshold_callbacks = {}

    def update_alpha(self, **kwargs) -> None:
        """更新α维度 / Update alpha dimension (physiological)"""
        self.alpha.update(**kwargs)
        self.alpha.compute_coordinate()
        self._post_update("alpha")

    def update_beta(self, **kwargs) -> None:
        """更新β维度 / Update beta dimension (cognitive)"""
        self.beta.update(**kwargs)
        self.beta.compute_coordinate()
        self._post_update("beta")

    def update_gamma(self, **kwargs) -> None:
        """更新γ维度 / Update gamma dimension (emotional)"""
        self.gamma.update(**kwargs)
        self.gamma.compute_coordinate()
        self._post_update("gamma")

    def update_delta(self, **kwargs) -> None:
        """更新δ维度 / Update delta dimension (social)"""
        self.delta.update(**kwargs)
        self.delta.compute_coordinate()
        self._post_update("delta")

    def update_epsilon(self, **kwargs) -> None:
        """更新ε维度 / Update epsilon dimension (mathematical/logical)"""
        self.epsilon.update(**kwargs)
        self.epsilon.compute_coordinate()
        self._post_update("epsilon")

    def update_theta(self, **kwargs) -> None:
        """更新θ维度 / Update theta dimension (meta-cognitive)"""
        self.theta.update(**kwargs)
        self.theta.compute_coordinate()
        self._post_update("theta")

    def update_zeta(self, **kwargs) -> None:
        """更新ζ维度 / Update zeta dimension (consciousness flow)"""
        self.zeta.update(**kwargs)
        self.zeta.compute_coordinate()
        self._post_update("zeta")

    def _init_semantic_anchors(self) -> None:
        """初始化軸的語義錨點 / Initialize semantic anchors for all axes"""
        dim_vector_size = 32
        self.semantic_anchors = {
            "alpha": AxisSemanticAnchor(
                name="alpha",
                label="生理",
                description="Physical state: energy, comfort, arousal, rest",
                semantic_vector=self._text_to_vector("energy comfort arousal physical body", dim_vector_size),
                keywords=["energy", "comfort", "arousal", "tired", "body", "physical", "health"],
            ),
            "beta": AxisSemanticAnchor(
                name="beta",
                label="認知",
                description="Cognitive state: curiosity, focus, confusion, learning",
                semantic_vector=self._text_to_vector("think learn focus curiosity understanding", dim_vector_size),
                keywords=["think", "learn", "focus", "curious", "confused", "understand", "remember", "decide"],
            ),
            "gamma": AxisSemanticAnchor(
                name="gamma",
                label="情感",
                description="Emotional state: happiness, sadness, anger, fear, love",
                semantic_vector=self._text_to_vector("happy sad angry fear love emotional", dim_vector_size),
                keywords=["happy", "sad", "angry", "fear", "love", "joy", "hurt", "emotion", "feeling"],
            ),
            "delta": AxisSemanticAnchor(
                name="delta",
                label="社交",
                description="Social state: attention, bond, trust, presence, intimacy",
                semantic_vector=self._text_to_vector("together social trust bond connection", dim_vector_size),
                keywords=["together", "social", "trust", "bond", "connection", "friend", "alone", "community"],
            ),
            "epsilon": AxisSemanticAnchor(
                name="epsilon",
                label="數理",
                description="Mathematical/logical state: precision, abstraction, certainty",
                semantic_vector=self._text_to_vector("number calculation logic precise math", dim_vector_size),
                keywords=["calculate", "number", "math", "precise", "logic", "answer", "compute", "result"],
            ),
            "theta": AxisSemanticAnchor(
                name="theta",
                label="元認知",
                description="Meta-cognitive state: novelty, complexity, abstraction, creation",
                semantic_vector=self._text_to_vector("think about thinking reflection analysis strategy plan", dim_vector_size),
                keywords=["think", "reflection", "analyze", "meta", "novel", "create", "abstract", "complex", "strategy", "plan", "decision"],
            ),
            "zeta": AxisSemanticAnchor(
                name="zeta",
                label="意識流",
                description="Consciousness flow: temporal coherence, memory, narrative, identity",
                semantic_vector=self._text_to_vector("time memory story identity continuous self history", dim_vector_size),
                keywords=["time", "memory", "story", "identity", "continuous", "self", "history", "narrative", "temporal", "flow"],
            ),
        }

    def _text_to_vector(self, text: str, size: int) -> List[float]:
        """将文本转换为低维语义向量（基于词频哈希）/ Convert text to low-dim semantic vector"""
        words = text.lower().split()
        vector = [0.0] * size
        for i, word in enumerate(words):
            hash_val = hash(word) % size
            vector[hash_val] += 0.5 * (1.0 if i % 2 == 0 else -0.3)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def apply_epsilon_influence(self) -> None:
        """
        [Task N.22-EPSILON-RIPPLE] Epsilon→Gamma 情緒漣漪效應
        數理維度的計算結果，以「漣漪」方式影響情感維度。
        而不是直接覆蓋 gamma 座標。
        """
        certainty = self.epsilon.values.get("certainty", 0.5)
        complexity = self.epsilon.values.get("complexity", 0.0)
        fatigue = self.epsilon.values.get("fatigue", 0.0)

        difficulty = min(1.0, complexity)

        self.gamma.values["surprise"] = min(
            1.0, self.gamma.values.get("surprise", 0.0) + difficulty * 0.2
        )
        self.gamma.values["happiness"] = min(
            1.0, self.gamma.values.get("happiness", 0.5) + certainty * 0.15
        )

        if fatigue > 0.7:
            self.beta.values["focus"] = max(
                0, self.beta.values.get("focus", 0.5) - fatigue * 0.1
            )
            self.gamma.values["calm"] = max(
                0, self.gamma.values.get("calm", 0.5) - fatigue * 0.05
            )

    # =============================================================================
    # [Task N.23-THETA] Meta-Cognitive Axis (θ) - 軸管理與分配決策
    # =============================================================================

    def _meta_allocate_policy(self, semantic_vector: List[float], label: str = "") -> AllocateDecision:
        """
        使用 AllocationPolicy 的分配決策（Phase 2 重構結果）

        這是 meta_allocate() 的重構版本，使用可配置的 stages 替代 if-elif 鏈。
        保留給 StateMatrixAdapter 的 allocation_decide() 使用。

        Returns:
            AllocateDecision（與 meta_allocate 相同格式）
        """
        from core.allocation.policy import (
            AllocationPolicy, AllocationContext,
            AllocationAction as PolicyAction,
        )

        axis_similarities: Dict[str, float] = {}
        for axis_name, anchor in self.semantic_anchors.items():
            sim = anchor.compute_resonance(semantic_vector)
            axis_similarities[axis_name] = sim

        max_sim = max(axis_similarities.values()) if axis_similarities else 0.0
        best_axis = max(axis_similarities, key=axis_similarities.get) if axis_similarities else None
        num_high_sim = sum(1 for s in axis_similarities.values() if s > 0.5)
        active_dims = sum(1 for v in axis_similarities.values() if v > 0.1)

        entropy_val = 0.0
        if axis_similarities:
            total = sum(axis_similarities.values())
            if total > 0:
                probs = [s / total for s in axis_similarities.values()]
                for p in probs:
                    if p > 0:
                        entropy_val -= p * math.log(p + 1e-10)
                max_entropy = math.log(len(probs) + 1e-10)
                if max_entropy > 0:
                    entropy_val /= max_entropy

        self.theta.update(
            novelty=1.0 - max_sim,
            complexity=active_dims / max(1, len(self.dimensions)),
            ambiguity=entropy_val,
            dimension_fit=max_sim,
        )

        if label:
            self._track_buffer(label)

        ctx = AllocationContext(
            vector=semantic_vector,
            label=label,
            similarities=axis_similarities,
            max_resonance=max_sim,
            best_axis=best_axis,
            num_high_sim=num_high_sim,
            entropy=entropy_val,
            active_dims=active_dims,
            novelty=1.0 - max_sim,
            complexity=float(active_dims) / max(1, len(self.dimensions)),
            dimension_fit=max_sim,
            buffer_tracking=self.buffer_tracking,
        )

        policy = AllocationPolicy()
        decision = policy.decide(ctx)

        if decision.action == PolicyAction.ASSIGN:
            return AllocateDecision(
                action="assign_to_axis",
                target=decision.target,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )
        elif decision.action == PolicyAction.COMPOSITE:
            top_axes = [(t[0], t[1]) for t in (decision.targets or [])]
            return AllocateDecision(
                action="composite_assign",
                targets=top_axes,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )
        elif decision.action == PolicyAction.CREATE:
            self.theta.update(creation_urge=0.8)
            return AllocateDecision(
                action="create_axis",
                proposed_name=decision.proposed_name or label or "new_axis",
                semantic_anchor=semantic_vector,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )
        else:
            return AllocateDecision(
                action="defer_to_buffer",
                buffer="unclassified_experiences",
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )

    def meta_allocate(self, semantic_vector: List[float], label: str = "") -> AllocateDecision:
        """
        θ 轴分析输入，决定如何分配到状态空间。

        默認使用 AllocationPolicy 重構版本。
        可以切換到 legacy 版本以保持完全向後兼容。

        Args:
            semantic_vector: 输入的语义向量（低维，32维）
            label: 可选的输入标签/关键词

Returns:
            AllocateDecision: 分配決策
        """
        return self._meta_allocate_policy(semantic_vector, label)

    def _track_buffer(self, label: str) -> None:
        """追踪未分类experience的频率 / Track frequency of unclassified experiences"""
        if not label:
            return
        self.buffer_tracking[label] = self.buffer_tracking.get(label, 0) + 1
        count = self.buffer_tracking[label]
        if count >= 5 and self.theta.values.get("creation_urge", 0) < 0.7:
            self.theta.update(creation_urge=min(1.0, 0.5 + count * 0.05))

    def create_axis(
        self, name: str, label: str, semantic_vector: List[float], initial_values: Optional[Dict[str, float]] = None
    ) -> DimensionState:
        """
        动态创建新轴 / Dynamically create a new axis

        Args:
            name: 轴名称（如 "zeta", "eta"）
            label: 中文标签
            semantic_vector: 语义锚点向量
            initial_values: 初始值字典

        Returns:
            新创建的 DimensionState
        """
        if name in self.dimensions:
            logger.warning(f"[Theta] Axis '{name}' already exists, returning existing")
            return self.dimensions[name]

        new_dim = DimensionState(
            name=name,
            cn_name=label,
            values=initial_values or {"value": 0.5},
            weight=0.5,
            coordinate=(0.0, 0.0, 0.0),
        )
        self.dimensions[name] = new_dim
        self.semantic_anchors[name] = AxisSemanticAnchor(
            name=name,
            label=label,
            description=f"Auto-created axis: {label}",
            semantic_vector=semantic_vector,
            keywords=[],
        )
        self.axis_creation_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "name": name,
                "label": label,
                "reason": self.theta.values.copy(),
            }
        )
        logger.info(f"[Theta] Created new axis '{name}' ({label})")
        return new_dim

    def execute_decision(self, decision: AllocateDecision, input_vector: List[float]) -> Dict[str, Any]:
        """
        执行 θ 的分配决策 / Execute the allocation decision made by θ

        Args:
            decision: AllocateDecision from meta_allocate
            input_vector: 语义向量（用于更新）

        Returns:
            执行结果摘要
        """
        results = {"action": decision.action, "applied_to": [], "new_axis_created": None}

        if decision.action == "assign_to_axis" and decision.target:
            if decision.target in self.dimensions:
                avg = sum(input_vector) / len(input_vector) if input_vector else 0.5
                key = self._dominant_key_from_vector(input_vector)
                update_dict = {key: min(1.0, avg)} if key else {}
                self.dimensions[decision.target].update(**update_dict)
                results["applied_to"].append(decision.target)

        elif decision.action == "composite_assign" and decision.targets:
            for target, weight in decision.targets:
                if target in self.dimensions:
                    avg = sum(input_vector) / len(input_vector) if input_vector else 0.5
                    key = self._dominant_key_from_vector(input_vector)
                    update_dict = {key: min(1.0, avg * weight)} if key else {}
                    self.dimensions[target].update(**update_dict)
                    results["applied_to"].append(target)

        elif decision.action == "create_axis" and decision.proposed_name:
            new_dim = self.create_axis(
                name=decision.proposed_name,
                label=decision.proposed_name,
                semantic_vector=decision.semantic_anchor or input_vector,
            )
            results["new_axis_created"] = decision.proposed_name
            results["applied_to"].append(decision.proposed_name)

        elif decision.action == "defer_to_buffer":
            buf_entry = {
                "timestamp": datetime.now().isoformat(),
                "vector": input_vector,
                "label": decision.buffer or "unclassified",
                "confidence": decision.confidence,
            }
            self.unclassified_buffer.append(buf_entry)
            results["applied_to"].append("unclassified_buffer")

        return results

    def _dominant_key_from_vector(self, vector: List[float]) -> str:
        """从向量推断主导键名 / Infer dominant key name from vector"""
        if not vector:
            return "value"
        if not self.semantic_anchors:
            return "value"
        best_axis = None
        best_resonance = -1.0
        for name, anchor in self.semantic_anchors.items():
            resonance = anchor.compute_resonance(vector)
            if resonance > best_resonance:
                best_resonance = resonance
                best_axis = name
        key_map = {
            "alpha": "energy",
            "beta": "focus",
            "gamma": "happiness",
            "delta": "bond",
            "epsilon": "logic",
            "theta": "creation_urge",
            "zeta": "narrative_flow",
        }
        return key_map.get(best_axis, "value")

    def get_theta_analysis(self) -> Dict[str, Any]:
        """获取θ轴分析报告 / Get theta axis analysis report"""
        return {
            "theta_values": self.theta.values.copy(),
            "axis_count": len(self.dimensions),
            "semantic_anchors": {k: {"name": v.name, "label": v.label} for k, v in self.semantic_anchors.items()},
            "buffer_tracking": self.buffer_tracking.copy(),
            "axis_creation_log": self.axis_creation_log[-5:],
            "buffer_size": len(self.unclassified_buffer),
            "misallocation_log_size": len(self.misallocation_log),
            "correction_audit_trail_size": len(self.correction_audit_trail),
            "theta_negativity": self.theta.values.get("theta_negativity", 0.0),
            "correction_urge": self.theta.values.get("correction_urge", 0.0),
        }

    # =============================================================================
    # [Task N.24-THETA-NEG] θ 軸負值檢測與修正系統
    # =============================================================================

    def trigger_theta_negativity(self, strength: float = 0.1) -> None:
        """
        觸發 θ 軸負值 — 表示懷疑當前分配

        當以下情況發生時調用：
          - 用戶反饋顯示分配錯誤
          - 新輸入與舊分配矛盾
          - 長時間未校正的不確定狀態

        Args:
            strength: 負值強度（0-1），越接近1表示懷疑越強
        """
        self.theta.values["theta_negativity"] = min(
            1.0, self.theta.values.get("theta_negativity", 0.0) + strength
        )
        self.theta.values["audit_intensity"] = min(
            1.0, self.theta.values.get("audit_intensity", 0.0) + strength * 0.5
        )
        self.theta.update()

        if self.theta.values["theta_negativity"] > 0.3:
            self.theta.values["correction_urge"] = min(
                1.0, self.theta.values.get("correction_urge", 0.0) + strength * 0.3
            )
            logger.info(f"[Theta-Neg] Negativity triggered: {self.theta.values['theta_negativity']:.2f}, "
                        f"correction_urge: {self.theta.values['correction_urge']:.2f}")

    def detect_misallocated_points(self) -> List[Dict[str, Any]]:
        """
        檢測錯配的點位 — 當 θ_negativity > 0.5 時自動調用

        原理：
          θ_negativity 越高 → 懷疑當前分配 → 遍歷歷史記錄
          對於每個分配：重新計算與當前軸的相似度
          如果相似度下降 > 30% → 標記為可能錯配

        Returns:
            錯配點位列表，每項包含：source_axis, target_axis, point_id, confidence
        """
        if self.theta.values.get("theta_negativity", 0) < 0.5:
            return []

        if len(self.history) == 0:
            return []

        misallocated = []
        audit_intensity = self.theta.values.get("audit_intensity", 0.5)

        subset_size = max(1, int(len(self.history) * audit_intensity))
        history_subset = self.history[-subset_size:]
        absolute_start = len(self.history) - subset_size

        for rel_idx, snapshot in enumerate(history_subset):
            absolute_idx = absolute_start + rel_idx
            for axis_name, values in snapshot.items():
                if axis_name not in ("alpha", "beta", "gamma", "delta", "epsilon", "theta"):
                    continue

                if axis_name not in self.semantic_anchors:
                    continue

                if not values:
                    continue

                anchor = self.semantic_anchors[axis_name]
                dominant_key = max(values.items(), key=lambda x: x[1])[0]

                reconstructed_vector = self._key_to_vector(dominant_key, 32)
                current_resonance = anchor.compute_resonance(reconstructed_vector)

                ideal_resonance = self._estimate_ideal_resonance(axis_name, dominant_key)

                if ideal_resonance > 0 and current_resonance < ideal_resonance * 0.7:
                    misallocated.append({
                        "point_id": f"hist_{absolute_idx}_{axis_name}",
                        "source_axis": axis_name,
                        "original_key": dominant_key,
                        "original_value": values.get(dominant_key, 0.5),
                        "current_resonance": current_resonance,
                        "ideal_resonance": ideal_resonance,
                        "drift_ratio": current_resonance / max(0.01, ideal_resonance),
                        "misallocation_confidence": 1.0 - (current_resonance / max(0.01, ideal_resonance)),
                    })

        self.misallocation_log.extend(misallocated[:20])
        if len(self.misallocation_log) > self.max_misallocation_log:
            self.misallocation_log = self.misallocation_log[-self.max_misallocation_log:]

        logger.info(f"[Theta-Neg] Detected {len(misallocated)} misallocated points, "
                    f"theta_negativity={self.theta.values.get('theta_negativity',0):.2f}")

        return misallocated

    def detect_misallocated_points_indexed(self) -> List[Dict[str, Any]]:
        """
        使用 TemporalState 索引的錯配檢測（相位 2 重構結果）

        不再需要 O(n) 遍歷歷史。使用 TemporalState.get_field_series()
        配合 trend() 和 anomaly detection 直接定位偏移的 field。

        Returns:
            錯配點位列表
        """
        timeline = self._get_temporal_state()
        if timeline.is_empty():
            return []

        if self.theta.values.get("theta_negativity", 0) < 0.5:
            return []

        from core.allocation.negativity import NegativityDetector
        detector = NegativityDetector(timeline=timeline)
        result = detector.detect()
        return result.items

    def correct_misallocation(
        self,
        point_id: str,
        target_axis: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        校正一個錯配的點位 — 將其重新分配到正確的軸

        Args:
            point_id: 錯配點位ID（格式：hist_{idx}_{axis_name}）
            target_axis: 目標軸（自動檢測如果為None）
            dry_run: True=只分析不實際移動

        Returns:
            校正結果摘要
        """
        if not self.theta.values.get("theta_negativity", 0) >= 0.3:
            return {"status": "skip", "reason": "theta_negativity too low"}

        parts = point_id.split("_")
        if len(parts) < 3:
            return {"status": "error", "reason": "invalid point_id format"}

        hist_idx = int(parts[1])
        if len(parts) == 3:
            source_axis = parts[2]
        else:
            source_axis = "_".join(parts[2:])

        if hist_idx >= len(self.history) or hist_idx < 0:
            return {"status": "error", "reason": "history index out of range"}

        snapshot = self.history[hist_idx]
        values = snapshot.get(source_axis, {})
        dominant_key = max(values.items(), key=lambda x: x[1])[0] if values else "value"
        original_value = values.get(dominant_key, 0.5)

        if target_axis is None:
            target_axis = self._find_best_axis_for_key(dominant_key, source_axis)

        if dry_run:
            return {
                "status": "dry_run",
                "point_id": point_id,
                "source_axis": source_axis,
                "target_axis": target_axis,
                "key": dominant_key,
                "value": original_value,
                "reasoning": f"自動檢測：'{dominant_key}' 更適合分配到 {target_axis} 而非 {source_axis}",
            }

        self.dimensions[source_axis].update(**{dominant_key: max(0.0, original_value - 0.1)})
        self.dimensions[target_axis].update(**{dominant_key: min(1.0, original_value + 0.1)})

        correction = {
            "timestamp": datetime.now().isoformat(),
            "point_id": point_id,
            "source_axis": source_axis,
            "target_axis": target_axis,
            "key": dominant_key,
            "original_value": original_value,
            "delta": 0.1,
            "theta_negativity_at_correction": self.theta.values.get("theta_negativity", 0),
        }
        self.correction_audit_trail.append(correction)
        if len(self.correction_audit_trail) > self.max_audit_trail:
            self.correction_audit_trail = self.correction_audit_trail[-self.max_audit_trail:]

        self.theta.values["theta_negativity"] = max(0.0, self.theta.values.get("theta_negativity", 0) - 0.1)
        self.theta.values["correction_urge"] = max(0.0, self.theta.values.get("correction_urge", 0) - 0.15)

        logger.info(f"[Theta-Neg] Corrected {point_id}: {source_axis} → {target_axis}")

        return {"status": "corrected", **correction}

    def auto_correct_all(self, min_confidence: float = 0.5) -> Dict[str, Any]:
        """
        自動校正所有高置信度的錯配點位

        當 correction_urge > 0.6 時調用。
        """
        if self.theta.values.get("correction_urge", 0) < 0.6:
            return {"status": "skip", "reason": "correction_urge too low", "corrected": 0}

        misallocated = self.detect_misallocated_points()
        high_conf = [m for m in misallocated if m["misallocation_confidence"] >= min_confidence]

        corrected_count = 0
        for item in high_conf:
            result = self.correct_misallocation(item["point_id"])
            if result.get("status") == "corrected":
                corrected_count += 1

        self.theta.values["theta_negativity"] = max(0.0, self.theta.values.get("theta_negativity", 0) - corrected_count * 0.05)
        self.theta.values["correction_urge"] = max(0.0, self.theta.values.get("correction_urge", 0) - corrected_count * 0.1)

        return {
            "status": "completed",
            "corrected": corrected_count,
            "total_detected": len(misallocated),
            "theta_negativity_after": self.theta.values.get("theta_negativity", 0),
            "correction_urge_after": self.theta.values.get("correction_urge", 0),
        }

    def _find_best_axis_for_key(self, key: str, current_axis: str) -> str:
        """根據鍵名找到最合適的軸"""
        key_lower = key.lower()

        key_to_axis = {
            "energy": "alpha", "comfort": "alpha", "arousal": "alpha", "tension": "alpha",
            "curiosity": "beta", "focus": "beta", "confusion": "beta", "learning": "beta", "clarity": "beta",
            "happiness": "gamma", "sadness": "gamma", "anger": "gamma", "fear": "gamma",
            "surprise": "gamma", "trust": "gamma", "calm": "gamma",
            "bond": "delta", "attention": "delta", "presence": "delta", "engagement": "delta",
            "logic": "epsilon", "precision": "epsilon", "certainty": "epsilon", "complexity": "epsilon",
        }

        if key_lower in key_to_axis:
            candidate = key_to_axis[key_lower]
            if candidate != current_axis:
                return candidate

        similarities = {}
        for axis_name, anchor in self.semantic_anchors.items():
            if axis_name == current_axis:
                continue
            key_vector = self._key_to_vector(key, 32)
            sim = anchor.compute_resonance(key_vector)
            similarities[axis_name] = sim

        if similarities:
            return max(similarities, key=similarities.get)
        return current_axis

    def _key_to_vector(self, key: str, size: int) -> List[float]:
        """將鍵名轉換為語義向量"""
        return self._text_to_vector(key, size)

    def _estimate_ideal_resonance(self, axis_name: str, key: str) -> float:
        """估計某個鍵在某個軸上的理想共振度"""
        if axis_name not in self.semantic_anchors:
            return 0.0
        anchor = self.semantic_anchors[axis_name]
        key_vector = self._key_to_vector(key, 32)
        return anchor.compute_resonance(key_vector)

    def get_negativity_report(self) -> Dict[str, Any]:
        """獲取 θ 軸負值系統的完整報告"""
        return {
            "theta_negativity": self.theta.values.get("theta_negativity", 0.0),
            "correction_urge": self.theta.values.get("correction_urge", 0.0),
            "audit_intensity": self.theta.values.get("audit_intensity", 0.0),
            "misallocation_count": len(self.misallocation_log),
            "correction_count": len(self.correction_audit_trail),
            "recent_corrections": self.correction_audit_trail[-5:],
            "needs_correction": self.theta.values.get("theta_negativity", 0) > 0.5,
            "ready_to_correct": self.theta.values.get("correction_urge", 0) > 0.6,
        }

    def reset_theta_negativity(self) -> None:
        """重置 θ 軸負值系統"""
        self.theta.values["theta_negativity"] = 0.0
        self.theta.values["correction_urge"] = 0.0
        self.theta.values["audit_intensity"] = 0.0
        logger.info("[Theta-Neg] Negativity system reset")

    def migrate_buffer_to_axis(self, axis_name: str) -> int:
        if axis_name not in self.dimensions:
            return 0
        count = 0
        for entry in self.unclassified_buffer:
            vector = entry.get("vector", [])
            if vector and isinstance(vector, list):
                avg = sum(vector) / len(vector)
                key = self._dominant_key_from_vector(vector)
                self.dimensions[axis_name].update(**{key: min(1.0, avg)})
                count += 1
        self.unclassified_buffer = [e for e in self.unclassified_buffer if e.get("label") != axis_name]
        logger.info(f"[Theta] Migrated {count} buffer entries to axis '{axis_name}'")
        return count

    def _post_update(self, dimension_name: str) -> None:
        """后更新处理 / Post-update processing"""
        self.update_count += 1
        self.last_update = datetime.now()

        # Record to history
        self._record_history()

        # [Task N.21.3] 意圖重力耦合 (Intent Gravity Coupling)
        self.apply_intent_gravity()

        # [Task N.21.7] 維度連動 (Inter-Dimensional Drag)
        # 如果當前維度發生了座標位移，會對其他維度產生微小的「拖拽」
        self.apply_inter_dimensional_drag(dimension_name)

        # --- Phase 2: Global State Store Integration ---
        try:
            from src.core.system.state_store import state_store
            dim_state = self.dimensions[dimension_name]
            state_store.update_state(dimension_name, dim_state.values.copy())
        except Exception as e:
            logger.error(f"[StateStore] Failed to sync {dimension_name}: {e}")

        # Trigger callbacks
        dim_state = self.dimensions[dimension_name]
        for callback in self._change_callbacks:
            try:
                callback(dimension_name, dim_state.values.copy())
            except Exception as e:  # broad exception acceptable: callback errors should not break state updates
                logger.error(f"Error in {__name__}: {e}", exc_info=True)
                pass

        # Check thresholds
        self._check_thresholds(dimension_name)

    def _record_history(self) -> None:
        """记录历史 / Record state to history"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "alpha": self.alpha.values.copy(),
            "beta": self.beta.values.copy(),
            "gamma": self.gamma.values.copy(),
            "delta": self.delta.values.copy(),
            "epsilon": self.epsilon.values.copy(),
            "theta": self.theta.values.copy(),
        }

        self.history.append(snapshot)

        if len(self.history) > self.max_history:
            self.history.pop(0)

    def _get_temporal_state(self):
        """獲取關聯的 TemporalState（用於雙軌整合）"""
        if not hasattr(self, "_temporal_state"):
            from core.state.temporal import TemporalState
            self._temporal_state = TemporalState(max_size=self.max_history)
            self._temporal_synced = False
        return self._temporal_state

    def _sync_to_temporal(self) -> None:
        """將最新快照同步到 TemporalState（延遲初始化）"""
        if not hasattr(self, "_temporal_state"):
            return
        if self._temporal_synced:
            return
        if self.history:
            self._temporal_state.record(self.history[-1])
            self._temporal_synced = True

    def _check_thresholds(self, dimension_name: str) -> None:
        """检查阈值 / Check thresholds for callbacks"""
        if dimension_name not in self._threshold_callbacks:
            return

        dim = self.dimensions[dimension_name]
        avg = dim.get_average()

        for threshold, callback in self._threshold_callbacks[dimension_name]:
            if avg >= threshold:
                try:
                    callback()
                except Exception as e:  # broad exception acceptable: threshold callbacks should not break checks
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    pass

    # =============================================================================
    # ANGELA-MATRIX: [L3] [αβγδ] [A] [L5+]
    # =============================================================================
    def compute_spatial_influence_factor(self, source: str, target: str) -> float:
        """
        [Task N.20.1] 向量場計算 / Vector Field Computation
        Calculates the spatial distance and influence factor between two dimensions
        in the coordinate-based cognitive space.
        """
        source_coord = self.dimensions[source].coordinate
        target_coord = self.dimensions[target].coordinate
        
        # Euclidean distance
        distance = sum((a - b) ** 2 for a, b in zip(source_coord, target_coord)) ** 0.5
        
        # Inverse square law for cognitive gravity (with a softening parameter to avoid division by zero)
        softening = 10.0
        # Normalize so that average distances yield ~1.0, closer > 1.0, further < 1.0
        influence_factor = 25.0 / (distance**2 + softening)
        
        return max(0.5, min(2.0, influence_factor))

    def compute_influences(self) -> Dict[str, Dict[str, float]]:
        """
        计算维度间影响 / Compute inter-dimensional influences

        Calculates and applies how each dimension affects others.

        Returns:
            Dictionary of computed influences
        """
        computed: Dict[str, Dict[str, float]] = {}

        for source_name, targets in self.influence_matrix.items():
            computed[source_name] = {}
            source_dim = self.dimensions[source_name]
            source_avg = source_dim.get_average()

            for target_name, base_strength in targets.items():
                target_dim = self.dimensions[target_name]

                # [Task N.20.1] 結合向量場影響力 (Spatial Influence)
                spatial_factor = self.compute_spatial_influence_factor(source_name, target_name)

                # Calculate actual influence (incorporating spatial topology)
                influence = base_strength * source_avg * source_dim.weight * target_dim.weight * spatial_factor
                computed[source_name][target_name] = influence

                # Apply influence
                self._apply_influence(source_name, target_name, influence)

        return computed

    def _apply_influence(self, source: str, target: str, amount: float) -> None:
        """应用影响 / Apply influence from source to target dimension"""
        try:
            from core.autonomous.influence_applicator import get_applicator
            applier = get_applicator()
            applier.apply(
                source, target,
                self.dimensions[source],
                self.dimensions[target],
                amount
            )
        except Exception:
            pass  # No fallback — influence_applicator handles all cases

    def _apply_influence_fallback(self, source: str, target: str, amount: float) -> None:
        """Deprecated: influence applicator handles all cases now"""
        pass

    def get_state(self, dimension: Optional[str] = None) -> Dict[str, Any]:
        """
        获取状态 / Get current state

        Args:
            dimension: Optional dimension name (returns all if None)

        Returns:
            State dictionary
        """
        if dimension:
            if dimension in self.dimensions:
                return self.dimensions[dimension].values.copy()
            return {}

        return {
            "alpha": {**self.alpha.values.copy(), "coordinate": self.alpha.coordinate},
            "beta": {**self.beta.values.copy(), "coordinate": self.beta.coordinate},
            "gamma": {**self.gamma.values.copy(), "coordinate": self.gamma.coordinate},
            "delta": {**self.delta.values.copy(), "coordinate": self.delta.coordinate},
            "epsilon": {**self.epsilon.values.copy(), "coordinate": self.epsilon.coordinate},
            "theta": {**self.theta.values.copy(), "coordinate": self.theta.coordinate},
            "zeta": {**self.zeta.values.copy(), "coordinate": self.zeta.coordinate},
        }


    def get_dimension_averages(self) -> Dict[str, float]:
        """获取所有维度平均值 / Get averages for all dimensions"""
        return {
            "alpha": self.alpha.get_average(),
            "beta": self.beta.get_average(),
            "gamma": self.gamma.get_average(),
            "delta": self.delta.get_average(),
            "epsilon": self.epsilon.get_average(),
            "theta": self.theta.get_average(),
            "zeta": self.zeta.get_average(),
        }

# =============================================================================
    # ANGELA-MATRIX: [L4] [αβγδ] [A] [L9+]
    # [Task N.20.1] 原生空間推理 — delegated to cognitive_operations.py
    # =============================================================================
    def perform_spatial_reasoning(
        self, target_dim: str, op: "CognitiveOp", magnitude: float
    ) -> Tuple[float, float, float]:
        return _psr(self.dimensions, target_dim, op, magnitude)

    def get_dimension_value(self, dim_name: str) -> float:
        return _gdv(self.dimensions, dim_name)

    def get_position(self) -> Dict[str, Any]:
        return _gp(self.dimensions)

    def get_coordinates(self) -> Dict[str, Any]:
        """獲取 4D 矩陣的完整座標映射"""
        return {name: state.coordinate for name, state in self.dimensions.items()}


    def execute_thought_chain(self, dimension: str, instructions: List[Tuple[CognitiveOp, float]]) -> float:
        """
        順暢地執行一連串的「空間思維鏈」。
        Execute a chain of "Spatial Thoughts" smoothly.
        """
        logger.info(f"🧠 [ThoughtChain] Starting reasoning chain on '{dimension}' with {len(instructions)} steps.")
        for op, magnitude in instructions:
            self.perform_spatial_reasoning(dimension, op, magnitude)
        
        result = self.get_dimension_value(dimension)
        logger.info(f"✨ [ThoughtChain] Reasoning complete. Resulting scalar: {result}")
        return result

    def evaluate_math_spatially(self, expression: str) -> float:
        """[L4-Reasoning] 數學表達式評估 — delegated to cognitive_operations.py"""
        evaluator = evaluate_math_spatially(self.dimensions)
        result = evaluator(expression)
        self.apply_epsilon_influence()
        return result

    def apply_intent_gravity(self, pull_factor: float = 0.05):
        apply_intent_gravity(self.dimensions, pull_factor)

    def set_intent_target(self, dimension: str, target: Tuple[float, float, float]):
        set_intent_target(self.dimensions, dimension, target)

    def apply_inter_dimensional_drag(self, trigger_dim: str, drag_factor: float = 0.02):
        apply_inter_dimensional_drag(self.dimensions, trigger_dim, drag_factor)

    def compute_wellbeing(self) -> float:
        """計算維度加權幸福感 / Compute dimension-weighted wellbeing score."""
        averages = self.get_dimension_averages()
        return (
            averages.get("alpha", 0.5) * 0.20
            + averages.get("beta", 0.5) * 0.15
            + averages.get("gamma", 0.5) * 0.25
            + averages.get("delta", 0.5) * 0.15
            + averages.get("epsilon", 0.5) * 0.15
            + averages.get("theta", 0.5) * 0.10
        )

    def get_analysis(self) -> Dict[str, Any]:
        """
        回傳完整狀態分析 / Return comprehensive state analysis.
        Used by digital_life_integrator, llm_decision_loop, and adapter.
        """
        return {
            "state": self.get_state(),
            "coordinates": self.get_coordinates(),
            "averages": self.get_dimension_averages(),
            "wellbeing": self.compute_wellbeing(),
            "arousal": self.alpha.values.get("arousal", 0.5),
            "valence": (
                self.gamma.values.get("happiness", 0.5)
                - self.gamma.values.get("sadness", 0.0)
            ),
            "dominant_emotion": self.gamma.get_dominant(),
            "alpha": self.alpha.values.copy(),
            "beta": self.beta.values.copy(),
            "gamma": self.gamma.values.copy(),
            "delta": self.delta.values.copy(),
            "epsilon": self.epsilon.values.copy(),
            "theta": self.theta.values.copy(),
            "zeta": self.zeta.values.copy(),
            "dimension_count": len(self.dimensions),
        }

    def get_history(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取历史记录 / Get state history

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of historical state snapshots
        """
        filtered = self.history.copy()

        if start_time:
            filtered = [h for h in filtered if datetime.fromisoformat(h["timestamp"]) >= start_time]

        if end_time:
            filtered = [h for h in filtered if datetime.fromisoformat(h["timestamp"]) <= end_time]

        return filtered

    def set_dimension_weight(self, dimension: str, weight: float) -> None:
        """设置维度权重 / Set dimension weight"""
        if dimension in self.dimensions:
            self.dimensions[dimension].weight = weight

    def set_influence_strength(self, source: str, target: str, strength: float) -> None:
        """设置影响强度 / Set influence strength between dimensions"""
        if source in self.influence_matrix and target in self.influence_matrix[source]:
            self.influence_matrix[source][target] = max(0.0, min(1.0, strength))

    def register_change_callback(self, callback: Callable[[str, Dict[str, float]], None]) -> None:
        """注册变化回调 / Register change callback"""
        self._change_callbacks.append(callback)

    def register_threshold_callback(
        self, dimension: str, threshold: float, callback: Callable[[], None]
    ) -> None:
        """注册阈值回调 / Register threshold callback"""
        if dimension not in self._threshold_callbacks:
            self._threshold_callbacks[dimension] = []
        self._threshold_callbacks[dimension].append((threshold, callback))

    def reset(self) -> None:
        """重置所有维度 / Reset all dimensions to default values"""
        for dim in self.dimensions.values():
            for key in dim.values:
                dim.values[key] = (
                    0.5
                    if key
                    not in [
                        "sadness",
                        "anger",
                        "fear",
                        "disgust",
                        "confusion",
                        "tension",
                        "intimacy",
                    ]
                    else 0.0
                )
            dim.timestamp = datetime.now()

        self.update_count = 0
        self.history.clear()
        self.last_update = datetime.now()

    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典 / Export state to dictionary"""
        return {
            "alpha": self.alpha.values,
            "beta": self.beta.values,
            "gamma": self.gamma.values,
            "delta": self.delta.values,
            "epsilon": self.epsilon.values,
            "theta": self.theta.values,
            "zeta": self.zeta.values,
            "weights": {name: dim.weight for name, dim in self.dimensions.items()},
            "influence_matrix": self.influence_matrix,
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_update": self.last_update.isoformat(),
                "update_count": self.update_count,
            },
        }

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典导入 / Import state from dictionary"""
        if "alpha" in data:
            self.alpha.values.update(data["alpha"])
        if "beta" in data:
            self.beta.values.update(data["beta"])
        if "gamma" in data:
            self.gamma.values.update(data["gamma"])
        if "delta" in data:
            self.delta.values.update(data["delta"])
        if "epsilon" in data:
            self.epsilon.values.update(data["epsilon"])
        if "theta" in data:
            self.theta.values.update(data["theta"])
        if "zeta" in data:
            self.zeta.values.update(data["zeta"])

        if "weights" in data:
            for name, weight in data["weights"].items():
                if name in self.dimensions:
                    self.dimensions[name].weight = weight

        if "influence_matrix" in data:
            self.influence_matrix = data["influence_matrix"]

        self.last_update = datetime.now()

    def export_to_json(self) -> str:
        """导出为JSON / Export state to JSON string"""
        return json.dumps(self.export_to_dict(), indent=2)

    def import_from_json(self, json_str: str) -> None:
        """从JSON导入 / Import state from JSON string"""
        data = json.loads(json_str)
        self.import_from_dict(data)

    def set_dimension_weight(self, dimension: str, weight: float) -> None:
        """设置维度权重 / Set dimension weight"""
        if dimension in self.dimensions:
            self.dimensions[dimension].weight = weight

    def set_influence_strength(self, source: str, target: str, strength: float) -> None:
        """设置影响强度 / Set influence strength between dimensions"""
        if source in self.influence_matrix and target in self.influence_matrix[source]:
            self.influence_matrix[source][target] = max(0.0, min(1.0, strength))

    def register_change_callback(self, callback: Callable[[str, Dict[str, float]], None]) -> None:
        """注册变化回调 / Register change callback"""
        self._change_callbacks.append(callback)

    def trigger_threshold_callback(self, dimension: str, value: float) -> None:
        """触发阈值回调 / Trigger threshold callback"""
        if dimension in self._threshold_callbacks:
            for threshold, callback in self._threshold_callbacks[dimension]:
                if value >= threshold:
                    try:
                        callback()
                    except Exception:
                        pass

    def export_for_llm(self, eta_state: Optional[Any] = None) -> Dict[str, Any]:
        """導出完整 7 維狀態 + θ + η，供 LLM prompt 使用。"""
        axes_data = {}
        for name in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta"):
            dim = self.dimensions.get(name)
            if dim:
                coord = getattr(dim, "coordinate", None)
                axes_data[name] = {
                    "values": dim.values.copy(),
                    "coordinate": list(coord) if coord else [0.0, 0.0, 0.0],
                    "weight": dim.weight,
                }

        theta_values = axes_data.get("theta", {}).get("values", {})
        novelty = theta_values.get("novelty", 0.0)
        negativity = theta_values.get("theta_negativity", 0.0)
        creation_urge = theta_values.get("creation_urge", 0.0)
        correction_urge = theta_values.get("correction_urge", 0.0)

        eta_data = {}
        if eta_state:
            eta_data = {
                "active_modules": eta_state.active_modules,
                "module_count": len(eta_state.active_modules),
                "execution_count": eta_state.execution_count,
                "success_rate": round(eta_state.success_rate, 3),
                "structural_drift": round(eta_state.structural_drift, 3),
            }

        avg_energy = self.alpha.values.get("energy", 0.5)
        avg_happiness = self.gamma.values.get("happiness", 0.5)
        avg_calm = self.gamma.values.get("calm", 0.5)

        guidance = []
        from core.system.config.tiered_loader import get_config
        _beh_conf = get_config("standard/behavior/behavior")
        _bio_thresh = _beh_conf.get("biological_thresholds", {})
        if avg_energy < _bio_thresh.get("energy_tone_low", 0.4):
            guidance.append("能量偏低，選擇溫柔安撫的語氣")
        elif avg_energy > _bio_thresh.get("energy_tone_high", 0.7):
            guidance.append("能量充沛，選擇活潑開朗的語氣")
        if avg_happiness < 0.4:
            guidance.append("用戶情緒偏負，選擇同理支持的角色")
        if novelty > 0.5:
            guidance.append("θ 新穎度較高，嘗試新的表達方式")
        if eta_state and eta_state.success_rate > 0.9:
            guidance.append("η 執行穩定，回應可以包含行動建議")

        return {
            "axes": axes_data,
            "theta": {
                "novelty": novelty,
                "theta_negativity": negativity,
                "creation_urge": creation_urge,
                "correction_urge": correction_urge,
            },
            "eta": eta_data,
            "temporal_trend": self._get_temporal_state().get_trend() if hasattr(self, "_temporal_state") and self._temporal_state else "stable",
            "wellbeing_score": self.compute_wellbeing(),
            "guidance": guidance,
        }

# Example usage
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Angela AI v6.0 - 4D状态矩阵系统演示")
    logger.info("4D State Matrix System Demo")
    logger.info("=" * 60)

    # Initialize matrix
    matrix = StateMatrix4D()

    logger.info("\n1. 初始维度状态 / Initial dimension states:")
    for name, dim in matrix.dimensions.items():
        logger.info(f"   {name} ({dim.cn_name}): {dim.get_average():.2f}")

    logger.info("\n2. 更新各维度 / Updating dimensions:")
    matrix.update_alpha(energy=0.8, comfort=0.7, arousal=0.6)
    matrix.update_beta(curiosity=0.9, focus=0.85, learning=0.7)
    matrix.update_gamma(happiness=0.85, trust=0.8, calm=0.75)
    matrix.update_delta(attention=0.9, bond=0.7, presence=0.6)

    for name, dim in matrix.dimensions.items():
        logger.info(f"   {name}: {dim.get_average():.2f}")

    logger.info("\n3. 计算维度间影响 / Computing inter-dimensional influences:")
    influences = matrix.compute_influences()
    for source, targets in influences.items():
        logger.info(f"   {source} -> {targets}")

    logger.info("\n4. 影响后的维度状态 / States after influences:")
    for name, dim in matrix.dimensions.items():
        logger.info(f"   {name}: {dim.get_average():.2f}")

    logger.info("\n5. 综合分析 / Comprehensive analysis:")
    analysis = matrix.get_analysis()
    logger.info(f"   总体状态 / Overall: {analysis['overall']:.2f}")
    logger.info(f"   幸福感 / Wellbeing: {analysis['wellbeing']:.2f}")
    logger.info(f"   唤醒度 / Arousal: {analysis['arousal']:.2f}")
    logger.info(f"   情感效价 / Valence: {analysis['valence']:.2f}")
    logger.info(f"   主导维度 / Dominant dimension: {analysis['dominant_dimension']}")
    logger.info(f"   主导情感 / Dominant emotion: {analysis['dominant_emotion']}")

    logger.info("\n6. 历史记录 / History:")
    logger.info(f"   记录数量 / Records: {len(matrix.history)}")
    logger.info(f"   更新次数 / Updates: {matrix.update_count}")

    logger.info("\n7. 导出状态 / Export state:")
    state_json = matrix.export_to_json()
    logger.info(f"   JSON长度 / JSON length: {len(state_json)} chars")

    logger.info("\n8. θ 元認知軸測試 / Theta Meta-Cognitive Axis Test:")
    matrix.update_theta(creation_urge=0.5)

    test_vector = matrix._text_to_vector("被老闆罵了", 32)
    decision = matrix.meta_allocate(test_vector, "boss_criticism")
    logger.info(f"   Input: '被老闆罵了'")
    logger.info(f"   θ Decision: {decision.action} | confidence={decision.confidence:.2f}")
    logger.info(f"   Reasoning: {decision.reasoning}")

    matrix.update_epsilon(certainty=0.7, complexity=0.5)
    matrix.apply_epsilon_influence()

    theta_analysis = matrix.get_theta_analysis()
    logger.info(f"   θ State: novelty={theta_analysis['theta_values']['novelty']:.2f}, "
                f"creation_urge={theta_analysis['theta_values']['creation_urge']:.2f}")
    logger.info(f"   Axis count: {theta_analysis['axis_count']}")

    logger.info("\n系統演示完成 / Demo complete")

    logger.info("\n系统演示完成 / Demo complete")
