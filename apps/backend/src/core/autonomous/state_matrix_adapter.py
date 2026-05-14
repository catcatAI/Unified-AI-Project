"""
State Matrix Adapter — Phase 7 整合適配器
==========================================

雙軌整合：
  - 軌 A（新）：使用 refactored 模組（Axis, TemporalState, InfluenceSpace, AllocationPolicy）
  - 軌 B（舊）：保持現有 StateMatrix4D 所有接口和行為不變

目標：在不破壞任何現有代碼的情況下，讓新模組可以運作。
      當新模組成熟後，逐步遷移。

使用方式:
    from core.autonomous.state_matrix_adapter import StateMatrixAdapter

    sm = StateMatrixAdapter()

    # 舊 API（保持不變）
    sm.update_alpha(focus=0.8)
    sm.update_beta(curiosity=0.6)
    sm.compute_influences()

    # 新 API（使用 refactored 模組）
    sm.temporal.trend('alpha', 'focus', window=30)
    sm.influence_space.compute('alpha', 'beta')
    sm.allocation_decide([0.1]*32, 'test')

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime

from core.state.axis_field import AxisFieldRegistry
from core.state.axis import Axis
from core.state.temporal import TemporalState
from core.state.config_loader import StateConfig
from core.allocation.resonance import ResonanceEngine, ResonanceProfile
from core.allocation.policy import AllocationPolicy, AllocationContext, AllocationDecision
from core.allocation.negativity import NegativityDetector
from core.influence.space import InfluenceSpace, GravityRule, EntropyRule, MemoryRule
from core.ripple.node import RippleNode, MathOp, LinearCascade, RippleApplicatorRegistry, RippleAccumulator


class StateMatrixAdapter:
    """
    狀態矩陣整合適配器
    =================

    將所有 refactored 模組整合到一個統一的介面。
    內部委託給 StateMatrix4D 的實例，同時提供新模組的查詢介面。

    雙軌策略：
    1. 保留所有舊 API（update_alpha/beta/gamma/delta, compute_influences 等）
    2. 新 API 提供對 refactored 模組的直接訪問
    """

    def __init__(self):
        from core.autonomous.state_matrix import StateMatrix4D
        self._sm = StateMatrix4D()
        self._init_config()
        self._init_temporal()
        self._init_influence()
        self._init_allocation()
        self._init_ripple()

    # === 初始化 ===

    def _init_config(self) -> None:
        """初始化配置"""
        try:
            self._config = StateConfig()
        except Exception:
            self._config = None

    def _init_temporal(self) -> None:
        """初始化時間查詢引擎"""
        max_size = 500
        if self._config:
            max_size = self._config.state_matrix.max_history
        self._temporal = TemporalState(max_size=max_size)

    def _init_influence(self) -> None:
        """初始化影響空間"""
        base_matrix = {
            'alpha': {'beta': 0.4, 'gamma': 0.2, 'delta': 0.1, 'epsilon': 0.3, 'theta': 0.2},
            'beta': {'alpha': 0.3, 'gamma': 0.5, 'delta': 0.2, 'epsilon': 0.4, 'theta': 0.3},
            'gamma': {'alpha': 0.2, 'beta': 0.3, 'delta': 0.4, 'epsilon': 0.2, 'theta': 0.2},
            'delta': {'alpha': 0.1, 'beta': 0.2, 'gamma': 0.3, 'epsilon': 0.1, 'theta': 0.2},
            'epsilon': {'alpha': 0.2, 'beta': 0.5, 'gamma': 0.3, 'delta': 0.1, 'theta': 0.2},
            'theta': {'alpha': 0.2, 'beta': 0.3, 'gamma': 0.2, 'delta': 0.2, 'epsilon': 0.3},
        }

        if self._config and self._config.influence_matrix:
            base_matrix = self._config.influence_matrix

        self._influence_space = InfluenceSpace(
            axes={
                'alpha': self._sm.alpha,
                'beta': self._sm.beta,
                'gamma': self._sm.gamma,
                'delta': self._sm.delta,
                'epsilon': self._sm.epsilon,
                'theta': self._sm.theta,
            },
            base_matrix=base_matrix,
        )
        self._influence_space.add_rule(GravityRule())
        self._influence_space.add_rule(EntropyRule())
        self._influence_space.add_rule(MemoryRule())

    def _init_allocation(self) -> None:
        """初始化分配決策系統"""
        self._resonance_engine = ResonanceEngine(axes=[
            self._sm.alpha, self._sm.beta, self._sm.gamma,
            self._sm.delta, self._sm.epsilon, self._sm.theta,
        ])
        self._allocation_policy = AllocationPolicy()
        self._negativity_detector = NegativityDetector(timeline=self._temporal)

    def _init_ripple(self) -> None:
        """初始化漣漪系統"""
        self._ripple_accumulator = RippleAccumulator()

    # === 屬性訪問 ===

    @property
    def temporal(self) -> TemporalState:
        """時間查詢引擎"""
        return self._temporal

    @property
    def influence_space(self) -> InfluenceSpace:
        """影響空間"""
        return self._influence_space

    @property
    def resonance_engine(self) -> ResonanceEngine:
        """共振引擎"""
        return self._resonance_engine

    @property
    def allocation_policy(self) -> AllocationPolicy:
        """分配策略"""
        return self._allocation_policy

    @property
    def negativity_detector(self) -> NegativityDetector:
        """負值檢測器"""
        return self._negativity_detector

    @property
    def config(self) -> Optional[StateConfig]:
        """配置"""
        return self._config

    # === 舊 API 委託 ===

    @property
    def alpha(self):
        return self._sm.alpha

    @property
    def beta(self):
        return self._sm.beta

    @property
    def gamma(self):
        return self._sm.gamma

    @property
    def delta(self):
        return self._sm.delta

    @property
    def epsilon(self):
        return self._sm.epsilon

    @property
    def theta(self):
        return self._sm.theta

    @property
    def dimensions(self):
        return self._sm.dimensions

    @property
    def history(self):
        return self._sm.history

    def update_alpha(self, **kwargs) -> None:
        self._sm.update_alpha(**kwargs)
        self._record_to_temporal()

    def update_beta(self, **kwargs) -> None:
        self._sm.update_beta(**kwargs)
        self._record_to_temporal()

    def update_gamma(self, **kwargs) -> None:
        self._sm.update_gamma(**kwargs)
        self._record_to_temporal()

    def update_delta(self, **kwargs) -> None:
        self._sm.update_delta(**kwargs)
        self._record_to_temporal()

    def update_epsilon(self, **kwargs) -> None:
        self._sm.update_epsilon(**kwargs)
        self._record_to_temporal()

    def update_theta(self, **kwargs) -> None:
        self._sm.update_theta(**kwargs)
        self._record_to_temporal()

    def compute_influences(self) -> Dict[str, Dict[str, float]]:
        return self._sm.compute_influences()

    def get_state(self, dimension: Optional[str] = None) -> Dict[str, Any]:
        return self._sm.get_state(dimension)

    def get_analysis(self) -> Dict[str, Any]:
        return self._sm.get_analysis()

    def export_to_dict(self) -> Dict[str, Any]:
        return self._sm.export_to_dict()

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        self._sm.import_from_dict(data)

    def meta_allocate(self, semantic_vector: List[float], label: str = "") -> Any:
        return self._sm.meta_allocate(semantic_vector, label)

    def trigger_theta_negativity(self, strength: float = 0.1) -> None:
        self._sm.trigger_theta_negativity(strength)
        self._negativity_detector.trigger(strength)

    def detect_misallocated_points(self) -> List[Dict[str, Any]]:
        return self._sm.detect_misallocated_points()

    def correct_misallocation(self, point_id: str, target_axis: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        return self._sm.correct_misallocation(point_id, target_axis, dry_run)

    def auto_correct_all(self, min_confidence: float = 0.5) -> Dict[str, Any]:
        return self._sm.auto_correct_all(min_confidence)

    def get_negativity_report(self) -> Dict[str, Any]:
        return self._sm.get_negativity_report()

    # === 新 API ===

    def _record_to_temporal(self) -> None:
        """將當前狀態記錄到時間線"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'alpha': self._sm.alpha.values.copy() if hasattr(self._sm.alpha, 'values') else {},
            'beta': self._sm.beta.values.copy() if hasattr(self._sm.beta, 'values') else {},
            'gamma': self._sm.gamma.values.copy() if hasattr(self._sm.gamma, 'values') else {},
            'delta': self._sm.delta.values.copy() if hasattr(self._sm.delta, 'values') else {},
            'epsilon': self._sm.epsilon.values.copy() if hasattr(self._sm.epsilon, 'values') else {},
            'theta': self._sm.theta.values.copy() if hasattr(self._sm.theta, 'values') else {},
        }
        self._temporal.record(snapshot)

    def allocation_decide(self, vector: List[float], label: str = "") -> AllocationDecision:
        """
        新 API：使用 AllocationPolicy 進行分配決策

        與 meta_allocate() 的區別：
        - meta_allocate() 返回舊的 AllocateDecision（str-based）
        - allocation_decide() 返回新的 AllocationDecision（typed）
        - allocation_decide() 使用 ResonanceEngine 計算 profile
        """
        profile = self._resonance_engine.compute_profile(vector)
        return self._allocation_policy.decide_from_profile(
            vector=vector,
            profile=profile,
            label=label,
            buffer_tracking=self._sm.buffer_tracking,
        )

    def compute_resonance(self, vector: List[float]) -> ResonanceProfile:
        """新 API：計算向量與所有軸的共振配置"""
        return self._resonance_engine.compute_profile(vector)

    def temporal_trend(self, axis: str, field: str, window: int = 50) -> Any:
        """新 API：查詢某個軸/field 的趨勢"""
        return self._temporal.trend(axis, field, window)

    def temporal_anomalies(self, axis: str, field: str, threshold: float = 0.3, window: int = 50) -> List[Any]:
        """新 API：檢測某個軸/field 的異常"""
        return self._temporal.anomalies(axis, field, threshold, window)

    def temporal_correlation(self, axis_a: str, field_a: str, axis_b: str, field_b: str, window: int = 50) -> Any:
        """新 API：計算兩個 field 的相關性"""
        return self._temporal.correlation(axis_a, field_a, axis_b, field_b, window)

    def influence_compute(self, source: str, target: str, context: Optional[Dict[str, Any]] = None) -> float:
        """新 API：計算 source -> target 的影響力"""
        return self._influence_space.compute(source, target, context)

    def influence_compute_all(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
        """新 API：計算所有軸對的影響力"""
        return self._influence_space.compute_all(context)

    def apply_ripple(
        self,
        operator: MathOp,
        result: float,
        epsilon_delta: float = 0.0,
        alpha_arousal: float = 0.0,
        beta_focus: float = 0.0,
        gamma_excitement: float = 0.0,
        delta_engagement: float = 0.0,
        theta_delta: float = 0.0,
        cascade_targets: Optional[List[str]] = None,
    ) -> List[RippleNode]:
        """
        新 API：創建並應用漣漪

        Args:
            operator: 數學運算類型
            result: 計算結果
            *_delta: 各軸效應
            cascade_targets: 級聯目標列表

        Returns:
            級聯產生的 RippleNode 列表
        """
        node = RippleNode(
            operator=operator,
            result=result,
            epsilon_delta=epsilon_delta,
            alpha_arousal=alpha_arousal,
            beta_focus=beta_focus,
            gamma_excitement=gamma_excitement,
            delta_engagement=delta_engagement,
            theta_delta=theta_delta,
        )

        if cascade_targets:
            cascaded = node.cascade(targets=cascade_targets, strategy=LinearCascade())
            for n in cascaded:
                RippleApplicatorRegistry.apply_node_to_axes(n, self._sm)
            self._ripple_accumulator.add(node)
            return cascaded

        RippleApplicatorRegistry.apply_node_to_axes(node, self._sm)
        self._ripple_accumulator.add(node)
        return [node]

    def ripple_summary(self) -> Dict[str, Any]:
        """新 API：獲取漣漪累積摘要"""
        return self._ripple_accumulator.summary()

    # === 狀態報告 ===

    def full_report(self) -> Dict[str, Any]:
        """
        完整狀態報告（新 + 舊）

        包含：
        - 舊 StateMatrix4D 的 get_analysis()
        - 新 TemporalState 統計
        - 新 InfluenceSpace 配置
        - 新 AllocationPolicy 配置
        - 新 NegativityDetector 狀態
        """
        return {
            'state_matrix': self._sm.get_analysis(),
            'temporal': {
                'size': self._temporal.size(),
                'max_size': 500,
            },
            'influence': {
                'rules_count': len(self._influence_space._rules._rules),
                'axes_count': len(self._influence_space._axes),
            },
            'allocation': {
                'stages': [s.name for s in self._allocation_policy.stages],
            },
            'negativity': self._negativity_detector.report(),
        }

    def __repr__(self) -> str:
        return (
            f"StateMatrixAdapter("
            f"temporal={self._temporal.size()} snapshots, "
            f"influence={len(self._influence_space._rules._rules)} rules, "
            f"neg={self._negativity_detector.negativity:.2f})"
        )


class StateMatrixFacade:
    """
    便捷外觀類 — 讓代碼更容易遷移到新架構

    用法:
        sm = StateMatrixFacade()
        sm.update(focus=0.8)  # 自動選擇軸
        trend = sm.trend('alpha', 'focus')
        inf = sm.influence('alpha', 'beta')
        decision = sm.allocate(vector)
    """

    _instance: Optional["StateMatrixFacade"] = None

    def __new__(cls) -> "StateMatrixFacade":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._adapter = None
        return cls._instance

    def __init__(self):
        if self._adapter is None:
            self._adapter = StateMatrixAdapter()

    @property
    def adapter(self) -> StateMatrixAdapter:
        return self._adapter

    def update(self, **kwargs) -> None:
        """通用更新（自動路由到正確的軸）"""
        grouped = self._group_kwargs_by_axis(kwargs)
        for axis, values in grouped.items():
            if axis == 'alpha':
                self._adapter.update_alpha(**values)
            elif axis == 'beta':
                self._adapter.update_beta(**values)
            elif axis == 'gamma':
                self._adapter.update_gamma(**values)
            elif axis == 'delta':
                self._adapter.update_delta(**values)
            elif axis == 'epsilon':
                self._adapter.update_epsilon(**values)
            elif axis == 'theta':
                self._adapter.update_theta(**values)

    def _group_kwargs_by_axis(self, kwargs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        key_map = {
            'energy': 'alpha', 'comfort': 'alpha', 'arousal': 'alpha', 'tension': 'alpha',
            'curiosity': 'beta', 'focus': 'beta', 'confusion': 'beta', 'learning': 'beta',
            'happiness': 'gamma', 'sadness': 'gamma', 'anger': 'gamma', 'fear': 'gamma',
            'bond': 'delta', 'attention': 'delta', 'presence': 'delta',
            'logic': 'epsilon', 'precision': 'epsilon',
            'novelty': 'theta', 'creation_urge': 'theta', 'theta_negativity': 'theta',
        }
        result: Dict[str, Dict[str, Any]] = {}
        for key, value in kwargs.items():
            axis = key_map.get(key, 'alpha')
            if axis not in result:
                result[axis] = {}
            result[axis][key] = value
        return result

    def trend(self, axis: str, field: str, window: int = 50) -> Any:
        return self._adapter.temporal_trend(axis, field, window)

    def influence(self, source: str, target: str) -> float:
        return self._adapter.influence_compute(source, target)

    def allocate(self, vector: List[float], label: str = "") -> AllocationDecision:
        return self._adapter.allocation_decide(vector, label)

    def __getattr__(self, name: str):
        return getattr(self._adapter, name)