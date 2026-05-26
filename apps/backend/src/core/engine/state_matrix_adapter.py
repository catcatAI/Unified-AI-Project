"""
State Matrix Adapter — Phase 7 整合適配器
==========================================

雙軌整合：
  - 軌 A（新）：使用 refactored 模組（Axis, TemporalState, InfluenceSpace, AllocationPolicy）
  - 軌 B（舊）：保持現有 StateMatrix4D 所有接口和行為不變

目標：在不破壞任何現有代碼的情況下，讓新模組可以運作。
      當新模組成熟後，逐步遷移。

使用方式:
    from core.engine.state_matrix_adapter import StateMatrixAdapter

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
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime

from core.engine.anchor_learning import AnchorLearningEngine
from core.state.axis_field import AxisFieldRegistry
from core.state.axis import Axis
from core.state.temporal import TemporalState
from core.state.config_loader import StateConfig
from core.allocation.resonance import ResonanceEngine, ResonanceProfile
from core.allocation.policy import AllocationPolicy, AllocationContext, AllocationDecision
from core.allocation.negativity import NegativityDetector
from core.influence.space import InfluenceSpace, GravityRule, EntropyRule, MemoryRule
from core.ripple.node import RippleNode, MathOp, LinearCascade, RippleApplicatorRegistry, RippleAccumulator
from core.state.text_to_vector import text_to_vector


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
        from core.engine.state_matrix import StateMatrix4D
        self._sm = StateMatrix4D()
        self._init_config()
        self._init_temporal()
        self._init_influence()
        self._init_allocation()
        self._init_ripple()
        self._init_learning()
        self._init_port_routing()
        self._init_persistence()
        self._init_eta()
        self._gradient_field = None
        self._BehaviorTone = None

    # === 初始化 ===

    def _init_port_routing(self) -> None:
        """初始化軸端口路由系統"""
        from core.engine.axis_port_registry import PortRegistry, PortDirection
        from core.engine.theta_router import ThetaRouter
        from core.engine.port_channel import AxisOutputManager

        self._port_registry = PortRegistry(state_adapter=self)
        self._theta_router = ThetaRouter(state_adapter=self, port_registry=self._port_registry)
        self._axis_output_manager = AxisOutputManager(state_adapter=self, port_registry=self._port_registry)

    def _init_persistence(self) -> None:
        """初始化持久化層"""
        from core.engine.state_persistence import StatePersistence, PersistenceConfig

        try:
            if self._config:
                redis_enabled = getattr(self._config, 'redis_enabled', True)
                redis_host = getattr(self._config, 'redis_host', 'localhost')
                redis_port = getattr(self._config, 'redis_port', 6379)
                auto_save = getattr(self._config, 'auto_save_interval', 300)
                max_snap = getattr(self._config, 'max_snapshots', 100)
            else:
                redis_enabled = True
                redis_host = "localhost"
                redis_port = 6379
                auto_save = 300
                max_snap = 100

            config = PersistenceConfig(
                redis_enabled=redis_enabled,
                redis_host=redis_host,
                redis_port=redis_port,
                auto_save_interval=auto_save,
                max_snapshots=max_snap,
                checkpoint_every_n_updates=50,
            )
            self._persistence = StatePersistence(config)
        except Exception:
            self._persistence = StatePersistence()

    def _init_eta(self) -> None:
        """初始化 η (Eta) 軸 — 執行/操作層"""
        from core.engine.eta_axis import EtaAxisState, create_default_modules

        self._eta = EtaAxisState()
        for name, config in create_default_modules().items():
            self._eta.register_module(config)

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
            'alpha': {'beta': 0.4, 'gamma': 0.2, 'delta': 0.1, 'epsilon': 0.3, 'theta': 0.2, 'zeta': 0.05},
            'beta': {'alpha': 0.3, 'gamma': 0.5, 'delta': 0.2, 'epsilon': 0.4, 'theta': 0.3, 'zeta': 0.1},
            'gamma': {'alpha': 0.2, 'beta': 0.3, 'delta': 0.4, 'epsilon': 0.2, 'theta': 0.2, 'zeta': 0.1},
            'delta': {'alpha': 0.1, 'beta': 0.2, 'gamma': 0.3, 'epsilon': 0.1, 'theta': 0.2, 'zeta': 0.05},
            'epsilon': {'alpha': 0.2, 'beta': 0.5, 'gamma': 0.3, 'delta': 0.1, 'theta': 0.2, 'zeta': 0.05},
            'theta': {'alpha': 0.2, 'beta': 0.3, 'gamma': 0.2, 'delta': 0.2, 'epsilon': 0.3, 'zeta': 0.05},
            'zeta': {'alpha': 0.05, 'beta': 0.1, 'gamma': 0.1, 'delta': 0.05, 'epsilon': 0.05, 'theta': 0.05},
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
                'zeta': self._sm.zeta,
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
            self._sm.zeta,
        ])
        self._allocation_policy = AllocationPolicy()
        self._negativity_detector = NegativityDetector(timeline=self._temporal)

    def _init_ripple(self) -> None:
        """初始化漣漪系統"""
        self._ripple_accumulator = RippleAccumulator()

    def _init_learning(self) -> None:
        """初始化錨點學習引擎"""
        self._anchor_learning = AnchorLearningEngine(
            resonance_engine=self._resonance_engine,
            temporal=self._temporal,
            ema_alpha=0.9,
            learning_interval=10,
            defer_threshold=0.3,
            assign_lr=0.05,
            misalloc_lr=0.03,
        )

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

    @property
    def anchor_learning(self) -> AnchorLearningEngine:
        """錨點學習引擎"""
        return self._anchor_learning

    @property
    def eta(self) -> "EtaAxisState":
        """η (Eta) 軸 — 執行/操作層"""
        return self._eta

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
    def theta(self):
        return self._sm.theta

    @property
    def zeta(self):
        return self._sm.zeta

    @property
    def history(self):
        return self._sm.history

    @property
    def gradient_field(self):
        """GradientField 實例（延遲初始化）"""
        if self._gradient_field is None:
            self._init_attractor_field()
        return self._gradient_field

    def update_alpha(self, **kwargs) -> None:
        self._sm.update_alpha(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("alpha", kwargs, is_stable=False)

    def update_beta(self, **kwargs) -> None:
        self._sm.update_beta(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("beta", kwargs, is_stable=False)

    def update_gamma(self, **kwargs) -> None:
        self._sm.update_gamma(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("gamma", kwargs, is_stable=False)

    def update_delta(self, **kwargs) -> None:
        self._sm.update_delta(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("delta", kwargs, is_stable=False)

    def update_epsilon(self, **kwargs) -> None:
        self._sm.update_epsilon(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("epsilon", kwargs, is_stable=False)

    def update_theta(self, **kwargs) -> None:
        self._sm.update_theta(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("theta", kwargs, is_stable=False)

    def update_zeta(self, **kwargs) -> None:
        self._sm.update_zeta(**kwargs)
        self._record_to_temporal()
        self._anchor_learning.on_axis_update("zeta", kwargs, is_stable=False)

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
        result = self._sm.meta_allocate(semantic_vector, label)
        action_map = {
            "assign_to_axis": "ASSIGN",
            "composite_assign": "COMPOSITE",
            "create_axis": "CREATE",
            "defer_to_buffer": "DEFER",
        }
        action = action_map.get(result.action, result.action)
        target = result.target
        if result.targets:
            target = result.targets[0][0] if result.targets else None
        self._anchor_learning.on_allocation_decision(
            semantic_vector, action, target, result.confidence
        )
        if label:
            best = self._anchor_learning.get_best_axis(semantic_vector)
            if best:
                self._anchor_learning.on_text_vectorized(label, semantic_vector, best)
        return result

    def trigger_theta_negativity(self, strength: float = 0.1) -> None:
        self._sm.trigger_theta_negativity(strength)
        self._negativity_detector.trigger(strength)

    def trigger_negativity(self, strength: float = 0.1) -> None:
        self.trigger_theta_negativity(strength)

    async def ask_theta_for_analysis(self, context: str = "") -> Dict[str, Any]:
        """
        θ 觸發的 LLM 分析

        當 θ.doubt 或 θ.negativity 超過閾值時，自動調用 LLM 進行分析。
        這是 Angela 的「自我懷疑 → 尋求分析」循環。

        流程：
        1. 檢查 θ.doubt / θ.negativity 是否超過閾值
        2. 如果超過，調用 LLM 生成分析
        3. 根據分析結果更新軸狀態
        4. 如果需要澄清，設置 theta.caution

        Args:
            context: 額外上下文（如 "MathVerifier 不一致"，"代碼檢查 critical"）

        Returns:
            分析結果摘要
        """
        from services.angela_llm_service import get_llm_service

        doubt = self._sm.theta.values.get("doubt", 0.0)
        negativity = self._sm.theta.values.get("theta_negativity", 0.0)

        if doubt < 0.4 and negativity < 0.3:
            return {"status": "skip", "reason": "theta too confident", "doubt": doubt, "negativity": negativity}

        state_summary = self._get_theta_analysis_context()
        prompt = f"""你是 Angela 的 θ 元認知系統。當前狀態：

{state_summary}

{context}

請分析：
1. 當前最主要的問題是什麼？
2. 應該如何調整軸狀態？
3. 是否需要觸發校正？

只返回 JSON：
{{"problem": "...", "adjustments": {{...}}, "needs_correction": true/false, "confidence": 0.0-1.0}}
"""

        try:
            service = await get_llm_service()
            response = await service.generate_response(
                prompt,
                {"history": [], "user_name": "θ-MetaCognition", "origin": "theta_analysis"}
            )
            text = response.text

            import json
            try:
                text_stripped = text.strip()
                if text_stripped.startswith("{"):
                    analysis = json.loads(text_stripped)
                else:
                    import re
                    match = re.search(r'\{[^{}]*\}', text_stripped)
                    if match:
                        analysis = json.loads(match.group())
                    else:
                        analysis = {}
            except Exception:
                analysis = {"raw": text[:200]}

            adjustments = analysis.get("adjustments", {})
            for axis_name, values in adjustments.items():
                if axis_name in self._sm.dimensions:
                    for field, delta in values.items():
                        current = self._sm.dimensions[axis_name].values.get(field, 0.5)
                        new_val = max(0.0, min(1.0, current + delta))
                        getattr(self, f"update_{axis_name}")(**{field: new_val})

            if analysis.get("needs_correction"):
                self.trigger_theta_negativity(strength=0.15)

            return {
                "status": "analyzed",
                "doubt": doubt,
                "negativity": negativity,
                "analysis": analysis,
                "response_preview": text[:100] if text else "",
            }
        except Exception as e:
            return {"status": "error", "reason": str(e), "doubt": doubt, "negativity": negativity}

    def _get_theta_analysis_context(self) -> str:
        """構建 θ 分析所需的上下文"""
        lines = []
        for axis_name, dim in self._sm.dimensions.items():
            avg = dim.get_average()
            lines.append(f"  {axis_name}: avg={avg:.3f}")
        lines.append(f"  θ.negativity={self._sm.theta.values.get('theta_negativity', 0):.3f}")
        lines.append(f"  θ.audit_intensity={self._sm.theta.values.get('audit_intensity', 0):.3f}")
        lines.append(f"  θ.complexity={self._sm.theta.values.get('complexity', 0):.3f}")
        lines.append(f"  update_count={self._sm.update_count}")
        return "\n".join(lines)

    def detect_misallocated_points(self) -> List[Dict[str, Any]]:
        return self._sm.detect_misallocated_points()

    def correct_misallocation(self, point_id: str, target_axis: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        result = self._sm.correct_misallocation(point_id, target_axis, dry_run)
        if result.get("status") == "corrected":
            source_axis = result.get("source_axis", "")
            tgt_axis = result.get("target_axis", "")
            key = result.get("key", "")
            confidence = self._sm.theta.values.get("theta_negativity", 0.3)
            input_vector = self._sm._key_to_vector(key, 32)
            self._anchor_learning.on_misallocation_detected(
                input_vector, source_axis, tgt_axis, confidence
            )
        return result

    def auto_correct_all(self, min_confidence: float = 0.5) -> Dict[str, Any]:
        result = self._sm.auto_correct_all(min_confidence)
        corrected = result.get("corrected", 0)
        if corrected > 0:
            for item in self._sm.detect_misallocated_points():
                source = item.get("source_axis", "")
                tgt = item.get("target_axis", "")
                key = item.get("original_key", "")
                conf = item.get("misallocation_confidence", 0.5)
                vec = self._sm._key_to_vector(key, 32)
                self._anchor_learning.on_misallocation_detected(vec, source, tgt, conf)
        return result

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
        decision = self._allocation_policy.decide_from_profile(
            vector=vector,
            profile=profile,
            label=label,
            buffer_tracking=self._sm.buffer_tracking,
        )
        self._anchor_learning.on_allocation_decision(
            vector, decision.action.value.upper(), decision.target, decision.confidence
        )
        if label:
            best = self._anchor_learning.get_best_axis(vector)
            if best:
                self._anchor_learning.on_text_vectorized(label, vector, best)
        return decision

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
            'port_routing': self._port_registry.get_report() if hasattr(self, '_port_registry') else {},
            'eta': {
                'module_count': len(self._eta.module_registry),
                'active_count': len(self._eta.active_modules),
                'execution_count': self._eta.execution_count,
                'success_rate': self._eta.success_rate,
                'structural_drift': self._eta.structural_drift,
                'pending_updates': len(self._eta.pending_updates),
            },
        }

    # === 端口路由 API ===

    def register_port(
        self,
        name: str,
        direction: str,
        semantic_vector: List[float],
        priority: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_bind: bool = True,
    ) -> Any:
        """註冊端口（自動 θ 路由綁定）"""
        from core.engine.axis_port_registry import PortDirection as PD
        direction_map = {"in": PD.IN, "out": PD.OUT, "io": PD.IO}
        port_dir = direction_map.get(direction, PD.IO)
        return self._port_registry.register(
            name=name,
            direction=port_dir,
            semantic_vector=semantic_vector,
            priority=priority,
            tags=tags,
            metadata=metadata,
            auto_bind=auto_bind,
        )

    def unregister_port(self, name: str) -> bool:
        """註銷端口"""
        return self._port_registry.unregister(name)

    def list_ports(
        self,
        direction: Optional[str] = None,
        bound: Optional[bool] = None,
        axis: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """列舉端口"""
        from core.engine.axis_port_registry import PortDirection as PD
        direction_map = {"in": PD.IN, "out": PD.OUT, "io": PD.IO}
        dir_filter = direction_map.get(direction) if direction else None
        return [p.to_dict() for p in self._port_registry.list_ports(
            direction=dir_filter, bound=bound, axis=axis
        )]

    def output_to_port(self, port_name: str, data: Any) -> bool:
        """寫入數據到端口緩衝區"""
        return self._axis_output_manager.push_to_port(port_name, data)

    def input_from_port(self, port_name: str) -> Optional[Any]:
        """從端口緩衝區讀取數據"""
        return self._axis_output_manager.pull_from_port(port_name)

    def cascade_output(self, axis_name: str, data: Any) -> Dict[str, Any]:
        """將軸數據廣播到所有輸出端口"""
        return self._theta_router.cascade_output(axis_name, data)

    def merge_input(self, axis_name: str) -> Dict[str, Any]:
        """從所有輸入端口合併數據到軸"""
        return self._axis_output_manager.input(axis_name)

    def auto_allocate_ports(self) -> int:
        """自動為所有未綁定端口分配軸"""
        return len(self._theta_router.auto_allocate())

    def re_evaluate_routing(self) -> List[Dict[str, Any]]:
        """重新評估所有端口的路由"""
        decisions = self._theta_router.re_evaluate_routing()
        return [d.to_dict() for d in decisions]

    # === η (Eta) Axis API ===

    def update_eta(self, **kwargs) -> None:
        """更新 η 軸字段"""
        if 'active_modules' in kwargs:
            self._eta.active_modules = kwargs['active_modules']
        if 'success_rate' in kwargs:
            self._eta.success_rate = max(0.0, min(1.0, kwargs['success_rate']))
        if 'structural_drift' in kwargs:
            self._eta.structural_drift = max(0.0, min(1.0, kwargs['structural_drift']))
        self._eta.update_composition()

    def invoke_eta_modules(self, inputs: Dict[str, Any], count: Optional[int] = None) -> List[Tuple[str, Any]]:
        """
        調用 η 軸模組

        Args:
            inputs: 模組輸入
            count: 調用數量（None=全部活躍模組）

        Returns:
            [(module_name, result), ...]
        """
        if count is None:
            return self._eta.execute_active_modules(inputs)
        active = self._eta.active_modules[:count]
        results = []
        for name in active:
            result = self._eta.execute(name, inputs)
            if result is not None:
                results.append((name, result))
        return results

    def eta_signals_from_theta(self) -> Dict[str, float]:
        """
        從 θ 狀態提取信號，用於觸發 η

        Returns:
            信號字典：update_frequency, complexity_delta, novelty_peak,
                     misallocation_rate, buffer_pressure
        """
        theta = self._sm.theta.values
        complexity = theta.get('complexity', 0.5)
        novelty = theta.get('novelty', 0.5)

        update_freq = min(1.0, self._sm.update_count / 1000)
        misalloc_rate = len(self._sm.misallocation_log) / max(1, self._sm.update_count)
        buffer_pressure = len(self._sm.buffer_tracking) / 50

        return {
            'update_frequency': update_freq,
            'complexity_delta': complexity,
            'novelty_peak': novelty,
            'misallocation_rate': min(1.0, misalloc_rate),
            'buffer_pressure': min(1.0, buffer_pressure),
        }

    def apply_theta_to_eta(self) -> Dict[str, Any]:
        """
        θ → η 信號應用：根據 θ 狀態計算 η 應執行的操作

        Returns:
            Dict with modules_to_call, delta, triggered, threshold
        """
        signals = self.eta_signals_from_theta()
        return self._eta.apply_theta_signals(signals)

    def eta_feedback_to_theta(self, success: bool) -> None:
        """
        η → θ 反饋：將 η 執行結果反饋給 θ

        Args:
            success: 執行是否成功
        """
        if success:
            self._sm.theta.values['dimension_fit'] = min(1.0, self._sm.theta.values.get('dimension_fit', 0.5) + 0.01)
        else:
            self._sm.theta.values['theta_negativity'] = min(1.0, self._sm.theta.values.get('theta_negativity', 0) + 0.05)

    def register_eta_module(
        self,
        name: str,
        module_type: str,
        sub_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """註冊新的 η 模組"""
        from core.engine.eta_axis import (
            ModuleConfig, AtomicModuleType,
            LogicGateType, ArithmeticOpType,
            AggregatorType, RouterType,
        )

        type_map = {
            'LOGIC_GATE': AtomicModuleType.LOGIC_GATE,
            'ARITHMETIC_OP': AtomicModuleType.ARITHMETIC_OP,
            'AGGREGATOR': AtomicModuleType.AGGREGATOR,
            'ROUTER': AtomicModuleType.ROUTER,
        }
        sub_map = {
            'LOGIC_GATE': {
                'AND': LogicGateType.AND, 'OR': LogicGateType.OR,
                'NOT': LogicGateType.NOT, 'XOR': LogicGateType.XOR,
                'THRESHOLD': LogicGateType.THRESHOLD,
            },
            'ARITHMETIC_OP': {
                'ADD': ArithmeticOpType.ADD, 'SUB': ArithmeticOpType.SUB,
                'MUL': ArithmeticOpType.MUL, 'DIV': ArithmeticOpType.DIV,
                'CUSTOM_EXPR': ArithmeticOpType.CUSTOM_EXPR,
            },
            'AGGREGATOR': {
                'SUM': AggregatorType.SUM, 'MEAN': AggregatorType.MEAN,
                'MAX': AggregatorType.MAX, 'MIN': AggregatorType.MIN,
                'WEIGHTED_AVG': AggregatorType.WEIGHTED_AVG,
            },
            'ROUTER': {
                'DIRECT': RouterType.DIRECT, 'FANOUT': RouterType.FANOUT,
                'MERGE': RouterType.MERGE, 'SPLIT': RouterType.SPLIT,
            },
        }

        mt = type_map.get(module_type)
        st = sub_map.get(module_type, {}).get(sub_type)
        if not mt or not st:
            return False

        config = ModuleConfig(
            name=name,
            module_type=mt,
            sub_type=st,
            parameters=parameters or {},
            tags=tags or [],
        )
        self._eta.register_module(config)
        return True

    def get_eta_report(self) -> Dict[str, Any]:
        """獲取 η 軸完整報告"""
        return self._eta.to_dict()

    # === θ-η Feedback Loop (P10.5) ===

    def theta_to_eta_cycle(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        完整的 θ → η → θ 迴路

        流程：
        1. θ 觀測信號
        2. η 計算模組調用
        3. η 執行模組
        4. η → θ 反饋
        5. θ 更新評估標準

        Args:
            context: 可選上下文（如用戶輸入）

        Returns:
            Dict with: signals, trigger_result, execution_results, feedback, theta_updates
        """
        signals = self.eta_signals_from_theta()
        trigger_result = self.apply_theta_to_eta()

        execution_results = []
        if trigger_result["triggered"]:
            count = trigger_result["modules_to_call"]
            inputs = self._build_eta_inputs(signals, context)
            execution_results = self.invoke_eta_modules(inputs, count)
            success = len(execution_results) > 0
            self.eta_feedback_to_theta(success)

        feedback = self._compute_eta_feedback(signals, trigger_result, execution_results)
        theta_updates = self._update_theta_from_feedback(feedback)

        return {
            "signals": signals,
            "trigger_result": trigger_result,
            "execution_results": [(name, r) for name, r in execution_results],
            "feedback": feedback,
            "theta_updates": theta_updates,
        }

    def _build_eta_inputs(self, signals: Dict[str, float], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """從 θ 信號構建 η 模組輸入"""
        weights = {
            "update_frequency": 0.2,
            "complexity_delta": 0.3,
            "novelty_peak": 0.2,
            "misallocation_rate": 0.2,
            "buffer_pressure": 0.1,
        }
        total, weight_sum = 0.0, 0.0
        for key, weight in weights.items():
            if key in signals:
                total += signals[key] * weight
                weight_sum += weight
        signal_strength = total / weight_sum if weight_sum > 0 else 0.0
        inputs = {
            "values": [
                signals.get("update_frequency", 0.5),
                signals.get("complexity_delta", 0.5),
                signals.get("novelty_peak", 0.5),
            ],
            "signal_strength": signal_strength,
        }
        if context:
            inputs.update(context)
        return inputs

    def _compute_eta_feedback(
        self,
        signals: Dict[str, float],
        trigger_result: Dict[str, Any],
        execution_results: List[Tuple[str, Any]],
    ) -> Dict[str, Any]:
        """計算 η 反饋"""
        return {
            "triggered": trigger_result.get("triggered", False),
            "modules_called": len(execution_results),
            "modules_to_call": trigger_result.get("modules_to_call", 0),
            "delta_applied": trigger_result.get("delta", 0.0),
            "signal_strength": trigger_result.get("signal_strength", 0.0),
            "threshold": trigger_result.get("threshold", 0.5),
            "execution_count": self._eta.execution_count,
            "success_rate": self._eta.success_rate,
            "structural_drift": self._eta.structural_drift,
        }

    def _update_theta_from_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """根據 η 反饋更新 θ"""
        updates = {}
        if feedback["triggered"]:
            dim_fit = self._sm.theta.values.get("dimension_fit", 0.5)
            if dim_fit < 0.6:
                new_dim_fit = min(1.0, dim_fit + 0.02)
                self._sm.theta.values["dimension_fit"] = new_dim_fit
                updates["dimension_fit"] = new_dim_fit

        if feedback["structural_drift"] > 0.3:
            self._sm.theta.values["complexity"] = max(0.0, self._sm.theta.values.get("complexity", 0.5) - 0.01)
            updates["complexity_adjusted"] = True

        if feedback["modules_called"] > 5:
            self._sm.theta.values["audit_intensity"] = min(1.0, self._sm.theta.values.get("audit_intensity", 0) + 0.05)
            updates["audit_intensity_increased"] = True

        return updates

    def execute_theta_eta_loop(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        執行 θ-η 迴路（主入口）

        這是 Angela 的主迴路：
        θ 觀測 → η 執行 → θ 調整

        Args:
            input_data: 可選的輸入數據（如用戶請求）

        Returns:
            迴路執行結果
        """
        self._sm.theta.values["creation_urge"] = max(0.0, self._sm.theta.values.get("creation_urge", 0) - 0.01)
        self._sm.theta.values["correction_urge"] = max(0.0, self._sm.theta.values.get("correction_urge", 0) - 0.01)

        result = self.theta_to_eta_cycle(input_data)
        result["theta_state"] = {
            "novelty": self._sm.theta.values.get("novelty", 0),
            "complexity": self._sm.theta.values.get("complexity", 0),
            "dimension_fit": self._sm.theta.values.get("dimension_fit", 0),
            "creation_urge": self._sm.theta.values.get("creation_urge", 0),
            "correction_urge": self._sm.theta.values.get("correction_urge", 0),
        }

        self._record_to_temporal()
        return result

    # === Attractor Field Integration ===

    def _init_attractor_field(self) -> None:
        """初始化吸引子場"""
        try:
            from ai.memory.attractor_field import GradientField, BehaviorTone
            self._gradient_field = GradientField(dimension_names=["alpha", "beta", "gamma", "delta", "epsilon"])
            self._BehaviorTone = BehaviorTone
        except ImportError:
            self._gradient_field = None
            self._BehaviorTone = None

    def _get_state_vector(self) -> List[float]:
        """將當前軸狀態轉為向量"""
        return [
            self._sm.alpha.get_average(),
            self._sm.beta.get_average(),
            self._sm.gamma.get_average(),
            self._sm.delta.get_average(),
            self._sm.epsilon.get_average(),
        ]

    def compute_gradient(self) -> Optional[Dict[str, Any]]:
        """計算當前狀態的梯度（不需要導航）"""
        if not self._gradient_field:
            self._init_attractor_field()
        if not self._gradient_field:
            return None

        state = self._get_state_vector()
        result = self._gradient_field.compute_gradient(state)

        return {
            "gradient": result.gradient,
            "gradient_strength": result.gradient_strength,
            "nearest_attractors": [
                {"description": a.description, "tone": a.tone.value, "distance": d}
                for a, d in result.nearest_attractors
            ],
            "blended_tone": result.blended_tone.value if result.blended_tone else None,
            "blended_behavior": result.blended_behavior,
            "blended_coord": result.blended_coord,
            "certainty": result.certainty,
        }

    def navigate_to_attractor(
        self,
        target_tags: Optional[List[str]] = None,
        max_steps: int = 5,
        dt: float = 0.15,
        threshold: float = 0.05,
    ) -> Optional[Dict[str, Any]]:
        """
        沿梯度導航到吸引子，並將結果應用到軸狀態

        Args:
            target_tags: 目標吸引子的標籤（None=最近的）
            max_steps: 最大導航步數
            dt: 步長
            threshold: 收斂閾值

        Returns:
            導航結果（new_state, gradient, nearest_attractors）
        """
        if not self._gradient_field:
            self._init_attractor_field()
        if not self._gradient_field:
            return None

        state = self._get_state_vector()

        if target_tags:
            for attractor in self._gradient_field.attractors:
                if any(t in attractor.tags for t in target_tags):
                    target_coord = list(attractor.coord[:5])
                    state = target_coord
                    break

        new_state, result = self._gradient_field.navigate(state, max_steps, dt, threshold)

        self._sm.alpha.update(value=max(0, min(1, new_state[0])))
        self._sm.beta.update(value=max(0, min(1, new_state[1])))
        self._sm.gamma.update(value=max(0, min(1, new_state[2])))
        self._sm.delta.update(value=max(0, min(1, new_state[3])))
        self._sm.epsilon.update(value=max(0, min(1, new_state[4])))

        self._record_to_temporal()

        return {
            "navigation_steps": result.navigation_steps,
            "new_state": new_state,
            "gradient": result.gradient,
            "gradient_strength": result.gradient_strength,
            "nearest_attractors": [
                {"description": a.description, "tone": a.tone.value, "distance": d}
                for a, d in result.nearest_attractors
            ],
            "blended_tone": result.blended_tone.value if result.blended_tone else None,
            "blended_behavior": result.blended_behavior,
        }

    def add_attractor(
        self,
        coord: Tuple[float, float, float, float, float],
        behavior: str,
        tone: str = "warm",
        mass: float = 1.0,
        radius: float = 0.4,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """添加自定義吸引子"""
        if not self._gradient_field:
            self._init_attractor_field()
        if not self._gradient_field:
            return False

        try:
            if self._BehaviorTone:
                tone_enum = self._BehaviorTone(tone)
            else:
                tone_enum = "warm"
        except (ValueError, TypeError):
            tone_enum = "warm"

        from ai.memory.attractor_field import MemoryAttractor
        attractor = MemoryAttractor(
            coord=coord,
            behavior=behavior,
            tone=tone_enum if hasattr(tone_enum, "value") else tone_enum,
            mass=mass,
            radius=radius,
            tags=tags or [],
            description=f"Custom: {behavior[:50]}",
        )
        self._gradient_field.add_attractor(attractor)
        return True

    def remove_attractor_by_tags(self, tags: List[str]) -> int:
        """移除指定標籤的吸引子"""
        if not self._gradient_field:
            self._init_attractor_field()
        if not self._gradient_field:
            return 0

        before = len(self._gradient_field.attractors)
        self._gradient_field.remove_attractor(tags)
        after = len(self._gradient_field.attractors)
        return before - after

    # === Persistable State ===

    def save_state(self) -> Dict[str, Any]:
        """序列化解壓縮的狀態（不含 GradientField 等不可序列化對象）"""
        return {
            "dimensions": {
                name: dim.values.copy()
                for name, dim in [
                    ("alpha", self._sm.alpha),
                    ("beta", self._sm.beta),
                    ("gamma", self._sm.gamma),
                    ("delta", self._sm.delta),
                    ("epsilon", self._sm.epsilon),
                    ("theta", self._sm.theta),
                ]
            },
            "theta_negativity": self._sm.theta.values.get("theta_negativity", 0),
            "theta_negativity_correction_urge": self._sm.theta.values.get("correction_urge", 0),
            "update_count": self._sm.update_count,
            "axis_creation_log": self._sm.axis_creation_log[-20:],
            "misallocation_log": self._sm.misallocation_log[-20:],
            "correction_audit_trail": self._sm.correction_audit_trail[-20:],
            "eta": self._eta.to_dict(),
        }

    def load_state(self, data: Dict[str, Any]) -> None:
        """從序列化的狀態恢復"""
        dims = data.get("dimensions", {})
        for name, values in dims.items():
            if name == "alpha":
                self._sm.update_alpha(**values)
            elif name == "beta":
                self._sm.update_beta(**values)
            elif name == "gamma":
                self._sm.update_gamma(**values)
            elif name == "delta":
                self._sm.update_delta(**values)
            elif name == "epsilon":
                self._sm.update_epsilon(**values)
            elif name == "theta":
                self._sm.update_theta(**values)

        tn = data.get("theta_negativity", 0)
        if tn > 0:
            self._sm.trigger_theta_negativity(strength=tn)

        eta_data = data.get("eta")
        if eta_data:
            from core.engine.eta_axis import EtaAxisState
            self._eta = EtaAxisState.from_dict(eta_data)

    async def save_state(self, key: str, data: Dict[str, Any]) -> bool:
        """StatePersistence protocol: persist data under key."""
        try:
            data_dir = self._get_protocol_data_dir()
            filepath = data_dir / f"{key}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, default=str)
            return True
        except Exception:
            return False

    async def load_state(self, key: str) -> Optional[Dict[str, Any]]:
        """StatePersistence protocol: load data by key."""
        try:
            data_dir = self._get_protocol_data_dir()
            filepath = data_dir / f"{key}.json"
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    async def delete_state(self, key: str) -> bool:
        """StatePersistence protocol: remove persisted state by key."""
        try:
            data_dir = self._get_protocol_data_dir()
            filepath = data_dir / f"{key}.json"
            if filepath.exists():
                filepath.unlink()
                return True
            return False
        except Exception:
            return False

    async def list_keys(self, prefix: str = "") -> list:
        """StatePersistence protocol: list keys matching prefix."""
        try:
            data_dir = self._get_protocol_data_dir()
            if not data_dir.exists():
                return []
            keys = []
            for f in data_dir.iterdir():
                if f.suffix == ".json":
                    k = f.stem
                    if k.startswith(prefix):
                        keys.append(k)
            return sorted(keys)
        except Exception:
            return []

    def _get_protocol_data_dir(self) -> Path:
        """Get directory for StatePersistence protocol data files."""
        base = Path(self._persistence.config.json_storage_path)
        data_dir = base / "protocol_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    async def init_persistence(self) -> None:
        """初始化持久化層（異步）"""
        await self._persistence.initialize()

    async def save_checkpoint(
        self,
        label: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        保存狀態快照到 Redis/JSON

        Args:
            label: 快照標籤（如 "manual", "auto", "critical_fix"）
            force: 是否強制保存

        Returns:
            保存結果摘要
        """
        return await self._persistence.save_checkpoint(self, label=label, force=force)

    async def load_checkpoint(
        self,
        checkpoint_id: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        加載狀態快照

        Args:
            checkpoint_id: 指定快照 ID
            tag: 指定標籤

        Returns:
            加載結果摘要
        """
        return await self._persistence.load_checkpoint(self, checkpoint_id=checkpoint_id, tag=tag)

    async def list_checkpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """列舉最近的快照"""
        return await self._persistence.list_checkpoints(limit=limit)

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """刪除指定快照"""
        return await self._persistence.delete_checkpoint(checkpoint_id)

    def set_checkpoint_tag(self, tag: str) -> None:
        """設置即將保存的 checkpoint 標籤"""
        self._persistence.set_checkpoint_id(tag)

    async def auto_checkpoint(self) -> Optional[Dict[str, Any]]:
        """自動 checkpoint（如果滿足條件）"""
        return await self._persistence.auto_checkpoint(self, self._sm.update_count)

    def get_persistence_stats(self) -> Dict[str, Any]:
        """獲取持久化層狀態"""
        return self._persistence.get_stats()

    # === Code Inspector Integration ===

    def integrate_code_inspect(self, inspect_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        將代碼檢查結果整合到狀態矩陣

        封裝 CodeInspectorBridge.integrate_inspect()
        將檢查結果轉化為軸狀態更新 + 漣漪觸發 + 分配決策

        Args:
            inspect_result: CodeInspectorInterface.inspect() 的返回值

        Returns:
            整合結果摘要
        """
        try:
            from ai.code_inspection.code_inspector_integration import CodeInspectorBridge
            bridge = CodeInspectorBridge(state_adapter=self)
            return bridge.integrate_inspect(inspect_result)
        except ImportError:
            return {"status": "skip", "reason": "code_inspector_integration not available"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    # === Math Verifier Integration ===

    def integrate_verification_result(self, verification_result: "VerificationResult") -> Dict[str, Any]:
        """
        將 MathVerifier 的驗證結果整合到狀態矩陣

        流程：
        1. 如果 matches=True → epsilon.confidence +=，epsilon.awareness +=
        2. 如果 matches=False → epsilon.confidence -=，theta.doubt +=
        3. 觸發漣漪（gamma.excitement 根據 discrepancy 大小）
        4. 如果 needs_clarification → theta.self_awareness +=

        Args:
            verification_result: MathVerifier.verify() 的返回值

        Returns:
            整合結果摘要
        """
        if verification_result.expression:
            expr_len = len(verification_result.expression)
            self._sm.epsilon.update(complexity=min(1.0, expr_len / 100.0))

        if verification_result.matches:
            delta = 0.05
            current = self._sm.epsilon.values.get("certainty", 0.5)
            self._sm.epsilon.update(certainty=min(1.0, current + delta))
            status = "trusted"
        else:
            delta = -0.1
            current = self._sm.epsilon.values.get("certainty", 0.5)
            self._sm.epsilon.update(certainty=max(0.0, current + delta))
            doubt_delta = 0.15
            current_d = self._sm.theta.values.get("theta_negativity", 0.0)
            self._sm.theta.values["theta_negativity"] = min(1.0, current_d + doubt_delta)
            self._sm.theta.values["audit_intensity"] = min(
                1.0, self._sm.theta.values.get("audit_intensity", 0) + 0.1
            )
            status = "corrected"

        if verification_result.discrepancy > 0.01:
            gamma_delta = min(0.2, verification_result.discrepancy * 0.5)
            current_e = self._sm.gamma.values.get("excitement", 0.0)
            self._sm.gamma.update(excitement=min(1.0, current_e + gamma_delta))

        if verification_result.needs_clarification:
            self._sm.theta.values["theta_negativity"] = min(
                1.0, self._sm.theta.values.get("theta_negativity", 0) + 0.05
            )
            status = "clarification_needed"

        return {
            "status": status,
            "expression": verification_result.expression,
            "llm_answer": verification_result.llm_answer,
            "engine_answer": verification_result.engine_answer,
            "matches": verification_result.matches,
            "discrepancy": verification_result.discrepancy,
            "epsilon_certainty": self._sm.epsilon.values.get("certainty", 0),
            "theta_negativity": self._sm.theta.values.get("theta_negativity", 0),
        }

    def code_inspect_report(self) -> Dict[str, Any]:
        """獲取當前代碼檢查狀態摘要"""
        return {
            "last_temporal_snapshot": self._temporal.size(),
            "epsilon_complexity": self._sm.epsilon.values.get("complexity", 0),
            "theta_negativity": self._sm.theta.values.get("theta_negativity", 0),
            "alpha_stability": self._sm.alpha.values.get("tension", 0),
            "beta_clarity": self._sm.beta.values.get("confusion", 0),
            "audit_intensity": self._sm.theta.values.get("audit_intensity", 0),
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

    def __init__(self):
        if getattr(self, "_adapter", None) is None:
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
            elif axis == 'zeta':
                self._adapter.update_zeta(**values)

    def _group_kwargs_by_axis(self, kwargs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        key_map = {
            # Alpha
            'energy': 'alpha', 'comfort': 'alpha', 'arousal': 'alpha', 'tension': 'alpha',
            'rest_need': 'alpha', 'vitality': 'alpha',
            # Beta
            'curiosity': 'beta', 'focus': 'beta', 'confusion': 'beta', 'learning': 'beta',
            'clarity': 'beta', 'creativity': 'beta',
            # Gamma
            'happiness': 'gamma', 'sadness': 'gamma', 'anger': 'gamma', 'fear': 'gamma',
            'disgust': 'gamma', 'surprise': 'gamma', 'trust': 'gamma',
            'anticipation': 'gamma', 'love': 'gamma', 'calm': 'gamma',
            # Delta
            'bond': 'delta', 'attention': 'delta', 'presence': 'delta',
            'intimacy': 'delta', 'engagement': 'delta',
            # Epsilon
            'logic': 'epsilon', 'precision': 'epsilon',
            'abstraction': 'epsilon', 'certainty': 'epsilon',
            'complexity': 'epsilon', 'fatigue': 'epsilon',
            # Theta (prefix complexity_theta to avoid collision with epsilon.complexity)
            'novelty': 'theta', 'creation_urge': 'theta', 'theta_negativity': 'theta',
            'complexity_theta': 'theta', 'ambiguity': 'theta',
            'abstraction_level': 'theta', 'dimension_fit': 'theta',
            'correction_urge': 'theta', 'audit_intensity': 'theta',
            # Zeta
            'temporal_coherence': 'zeta', 'memory_depth': 'zeta',
            'narrative_flow': 'zeta', 'identity_continuity': 'zeta',
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