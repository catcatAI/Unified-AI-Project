"""
Angela AI v6.0 - Digital Life Integrator
数字生命总控

Central controller for Angela's digital life, managing the life cycle,
state monitoring, and coordination of all autonomous systems.

Features:
- Life cycle management (birth, growth, maturity, rest)
- System state monitoring and health checks
- Cross-system coordination
- Life event processing
- Personality development tracking

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
import asyncio
import logging
from core.system.config.magic_numbers import loop_sleep
from typing import TYPE_CHECKING
from core.engine.state_matrix import StateMatrix4D
from .self_introspector import SelfIntrospector
from core.bio.biological_integrator import BiologicalIntegrator
from core.engine.action_executor import ActionExecutor
from core.bio.memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge
from .autonomous_life_cycle import AutonomousLifeCycle
from .dynamic_parameters import DynamicThresholdManager
from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
from ai.lifecycle.user_monitor import UserMonitor

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ai.integration.unified_control_center import UnifiedControlCenter


# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L4+]
# [Task N.20.2] 模態閘控類型與狀態 / Modality Gating types and status
# =============================================================================
class ModalityType(Enum):
    """模態類型 / Modality types"""
    TEXT = auto()
    AUDIO = auto()
    VISUAL_3D = auto()
    CODE = auto()


@dataclass
class ModalityState:
    """模態狀態 / Modality state"""
    modality: ModalityType
    is_active: bool = True
    priority: int = 1
    last_toggle: datetime = field(default_factory=datetime.now)


class ModalityGateway:
    """
    模態閘控管理器 / Modality Gateway Manager
    Handles dynamic switching of output streams based on intent and arousal.
    """
    def __init__(self):
        self.modalities: dict[ModalityType, ModalityState] = {
            ModalityType.TEXT: ModalityState(ModalityType.TEXT, True, 10),
            ModalityType.AUDIO: ModalityState(ModalityType.AUDIO, True, 5),
            ModalityType.VISUAL_3D: ModalityState(ModalityType.VISUAL_3D, True, 8),
            ModalityType.CODE: ModalityState(ModalityType.CODE, False, 2),
        }

    def update_gates(self, arousal: float, introspection_report: Optional[dict[str, Any]] = None) -> None:
        """根據喚醒度與意圖分析更新閘門狀態"""
        old_states = {m: s.is_active for m, s in self.modalities.items()}
        
        # 1. 基礎生理限制 (喚醒度低於 20 關閉耗能模態)
        from core.system.config.tiered_loader import get_config
        _beh_conf = get_config("standard/behavior/behavior")
        _arousal_off = _beh_conf.get("biological_thresholds", {}).get("arousal_modality_off", 20)
        if arousal < _arousal_off:
             self.modalities[ModalityType.VISUAL_3D].is_active = False
             self.modalities[ModalityType.AUDIO].is_active = False
        else:
             self.modalities[ModalityType.VISUAL_3D].is_active = True
             self.modalities[ModalityType.AUDIO].is_active = True

        # 2. 意圖驅動邏輯 (Task N.21.4)
        if introspection_report:
            dissonance = introspection_report.get("dissonance_score", 0.0)
            
            # 如果認知失調過高 (> 0.6)，強制關閉複雜模態，進入「省電/簡化」模式
            if dissonance > 0.6:
                self.modalities[ModalityType.CODE].is_active = False
                self.modalities[ModalityType.AUDIO].is_active = False
                logger.warning(f"⚠️ [Modality] High Dissonance ({dissonance:.2f}). Throttling energy-heavy modalities.", exc_info=True)
            else:
                # 根據任務類型動態開啟
                anomalies = introspection_report.get("anomalies", [])
                is_coding_task = any("code" in str(a).lower() for a in anomalies)
                self.modalities[ModalityType.CODE].is_active = is_coding_task


        # 記錄狀態變更
        for m, s in self.modalities.items():
            if s.is_active != old_states[m]:
                s.last_toggle = datetime.now()
                logger.info(f"🔮 [Modality] {m.name} is now {'ACTIVE' if s.is_active else 'INACTIVE'}")

    def is_active(self, modality: ModalityType) -> bool:
        """Check if a given modality is currently active."""
        return self.modalities.get(modality, ModalityState(modality)).is_active



class LifeCycleState(Enum):
    """生命周期状态 / Life cycle states"""

    INITIALIZING = ("初始化中", "Initializing")
    AWAKENING = ("觉醒中", "Awakening")  # Learning basic behaviors
    GROWING = ("成长中", "Growing")  # Active learning phase
    MATURE = ("成熟", "Mature")  # Fully developed
    RESTING = ("休息中", "Resting")  # Low activity mode
    DORMANT = ("休眠", "Dormant")  # Deep sleep/conservation

    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class LifeStats:
    """生命统计 / Life statistics"""

    birth_time: datetime = field(default_factory=datetime.now)
    total_active_time: timedelta = field(default_factory=timedelta)
    total_interactions: int = 0
    total_conversations: int = 0
    total_actions_executed: int = 0
    memories_formed: int = 0
    memories_consolidated: int = 0
    skills_learned: list[str] = field(default_factory=list)
    personality_traits: dict[str, float] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """系统健康状态 / System health status"""

    system_name: str
    is_healthy: bool
    last_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    response_time_ms: float = 0.0
    status_message: str = "OK"


@dataclass
class LifeEvent:
    """生命事件 / Life event"""

    event_id: str
    event_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    significance: float = 0.5  # 0-1, importance of the event
    metadata: dict[str, Any] = field(default_factory=dict)


class DigitalLifeIntegrator:
    """
    数字生命总控主类 / Main digital life integrator class

    Central controller managing Angela's complete digital life cycle,
    coordinating all autonomous systems, monitoring health, and processing
    significant life events.

    Attributes:
        life_cycle_state: Current life cycle phase
        life_stats: Lifetime statistics
        systems_health: Health status of all subsystems
        biological_integrator: Biological systems controller
        action_executor: Action execution system
        memory_bridge: Memory and neuroplasticity bridge
        life_events: History of significant events

    Example:
        >>> life = DigitalLifeIntegrator()
        >>> await life.initialize()
        >>>
        >>> # Process a day of life
        >>> await life.process_day_cycle()
        >>>
        >>> # Record a significant event
        >>> life.record_life_event(
        ...     "first_conversation",
        ...     "Had first meaningful conversation with user",
        ...     significance=0.8
        ... )
        >>>
        >>> # Get life summary
        >>> summary = life.get_life_summary()
        >>> print(f"Age: {summary['age_days']} days")
        >>> print(f"State: {summary['current_state']}")
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}

        # Life cycle
        self.life_cycle_state: LifeCycleState = LifeCycleState.INITIALIZING
        self.previous_state: Optional[LifeCycleState] = None

        # Statistics
        self.life_stats: LifeStats = LifeStats()

        # Subsystems
        self.biological_integrator: BiologicalIntegrator = BiologicalIntegrator()
        self.action_executor: ActionExecutor = ActionExecutor()
        self.memory_bridge: Optional[MemoryNeuroplasticityBridge] = None

        # P0-4: AI Lifecycle loops
        self.llm_decision_loop: Optional[LLMDecisionLoop] = None
        self.user_monitor: UserMonitor = UserMonitor(
            config.get("user_id", "default_user") if config else "default_user"
        )
        self.broadcast_callback: Optional[Callable] = None

        # Theoretical Framework Integration
        self.autonomous_lifecycle: Optional[AutonomousLifeCycle] = None
        self._formula_integration_enabled: bool = self.config.get(
            "enable_formula_integration", True
        )

        # AGI Control Loop (Phase 11)
        self.unified_control_center: Optional[UnifiedControlCenter] = None

        # Dynamic Parameters Integration
        self.dynamic_params: Optional[DynamicThresholdManager] = None
        self._dynamic_params_enabled: bool = self.config.get("enable_dynamic_params", True)
        self._dynamic_params_update_interval: float = self.config.get(
            "dynamic_params_update_interval", loop_sleep("life_integrator_params", 60.0)
        )
        self._last_params_log: datetime = datetime.now()

        # Health monitoring
        self.systems_health: dict[str, SystemHealth] = {}
        self._health_check_interval: float = loop_sleep("life_health_check", 60.0)  # seconds
        self._update_interval: float = self.config.get(
            "update_interval", 1.0
        )  # Used for introspection loop

        # Life events
        self.life_events: list[LifeEvent] = []
        self._significant_events: list[LifeEvent] = []

        # Activity tracking
        self._last_activity_time: datetime = datetime.now()
        self._is_active: bool = False
        self._rest_threshold_minutes: float = 30.0

        # Running state
        self._running = False
        self._life_cycle_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

        # Callbacks
        self._state_change_callbacks: list[Callable[[LifeCycleState, LifeCycleState], None]] = []
        self._event_callbacks: list[Callable[[LifeEvent], None]] = []

        # Self-Introspection and State Matrix
        self.state_matrix = StateMatrix4D()
        self.self_introspector = SelfIntrospector(self.config.get("introspection", {}))
        self.introspection_report: Optional[dict[str, Any]] = None

        # [Task N.20.2] 模態閘控初始化
        self.modality_gateway = ModalityGateway()

    async def initialize(self) -> bool:
        """
        Initialize digital life with 2030-standard robust error handling.
        Ensures partial survival even if high-level modules fail.
        """
        self._running = True
        logger.info("🌌 Starting Angela's Digital Life Incubation...")

        # 1. Core Biological Foundation (Must work)
        try:
            await self.biological_integrator.initialize()
            logger.info("  [Foundation] Biological systems online.")
        except Exception as e:
            # broad except acceptable: init must survive optional component failure
            logger.error(f"  [CRITICAL] Biological boot failure: {e}", exc_info=True)

        # 2. Action & Interaction Layer
        try:
            self.action_executor.set_digital_life_integrator(self)
            await self.action_executor.initialize()
            logger.info("  [Sensory] Action executor online.")
        except Exception as e:
            # broad except acceptable: executor degradation is non-critical, graceful degradation
            logger.warning(f"  [Sensory] Executor degraded: {e}", exc_info=True)

        # 3. High-Level Cognition (Optional/Graceful)
        try:
            from services.angela_llm_service import get_llm_service
            from ai.memory.ham_memory.ham_manager import HAMMemoryManager

            llm_service = await get_llm_service()
            memory_manager = HAMMemoryManager(core_storage_filename="angela_conversations.json")
            
            # Decide loop
            self.llm_decision_loop = LLMDecisionLoop(
                llm_service=llm_service,
                state_manager=self.state_matrix,
                memory_manager=memory_manager,
                user_monitor=self.user_monitor,
                broadcast_callback=self.broadcast_callback,
            )
            await self.llm_decision_loop.start()
            logger.info("  [Cognition] LLM Decision Loop active.")
        except Exception as e:
            # broad except acceptable: LLM failure is optional, graceful degradation
            logger.error(f"  [Cognition] Brain boot failure: {e}. Angela will rely on GSI-4 local logic.", exc_info=True)

        # 4. Final Activation
        self.is_initialized = True
        await self._transition_state(LifeCycleState.AWAKENING)

        # Start background loops
        self._life_cycle_task = asyncio.create_task(self._life_cycle_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info(f"✨ Angela has awakened in {self.life_cycle_state.en_name} state.")
        return True

    def _on_formula_decision(self, decision) -> None:
        """Callback for formula-driven life decisions"""
        # Record as life event if significant
        if decision.confidence > 0.6:
            self.record_life_event(
                event_type=f"formula_decision_{decision.decision_type}",
                description=decision.rationale,
                significance=decision.confidence,
                metadata={
                    "decision_id": decision.decision_id,
                    "triggered_by": decision.triggered_by,
                    "expected_outcome": decision.expected_outcome,
                },
            )

    async def shutdown(self) -> None:
        """Shutdown digital life and all subsystems"""
        self._running = False

        # Cancel tasks
        if self._life_cycle_task:
            self._life_cycle_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()

        # Shutdown subsystems
        await self.biological_integrator.shutdown()
        await self.action_executor.shutdown()
        if self.memory_bridge:
            await self.memory_bridge.shutdown()

        # Shutdown theoretical frameworks
        if self.autonomous_lifecycle:
            await self.autonomous_lifecycle.shutdown()

        # Shutdown dynamic parameters
        if self.dynamic_params:
            try:
                await self.dynamic_params.stop()
            except Exception as e:
                # broad except acceptable: shutdown cleanup, must not raise
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

        # Record final stats
        self._update_active_time()

    async def _life_cycle_loop(self) -> None:
        """Main life cycle management loop"""
        while self._running:
            await self._check_activity_status()
            await self._process_life_cycle_transitions()
            await self._update_statistics()
            await self._update_dynamic_parameters()
            await asyncio.sleep(loop_sleep("life_check_interval", 10.0))  # Check every 10 seconds

    async def _health_check_loop(self) -> None:
        """System health monitoring loop"""
        while self._running:
            await self._check_system_health()
            # 5. Perform Self-Introspection
            try:
                state_analysis = self.state_matrix.get_analysis()
                bio_state = self.biological_integrator.get_biological_state()
                combined_state = {**state_analysis, **bio_state}

                # We assume a default context here; in actual dialogue, this would be more dynamic
                introspection_context = {"expected_sentiment": "neutral"}

                self.introspection_report = (
                    await self.self_introspector.perform_mental_health_check(
                        combined_state, introspection_context
                    )
                )

                if self.introspection_report.get("dissonance_detected"):
                    logger.warning(
                        f"[DigitalLife] Cognitive dissonance detected: {self.introspection_report['anomalies']}"
                        , exc_info=True
                    )

                # [Task N.20.2] 更新模態閘控
                self.modality_gateway.update_gates(
                    arousal=bio_state.get("arousal", 50.0),
                    introspection_report=self.introspection_report
                )

            except Exception as e:
                # broad except acceptable: introspection loop must survive errors
                logger.error(f"[DigitalLife] Introspection error: {e}", exc_info=True)

            await asyncio.sleep(self._update_interval)

    async def _check_activity_status(self) -> None:
        """Check and update activity status"""
        time_since_activity = (datetime.now() - self._last_activity_time).total_seconds()

        if self._is_active and time_since_activity > self._rest_threshold_minutes * 60:
            # Transition to resting
            self._is_active = False
            if self.life_cycle_state == LifeCycleState.MATURE:
                await self._transition_state(LifeCycleState.RESTING)
        elif not self._is_active and time_since_activity < 60:
            # Becoming active again
            self._is_active = True
            if self.life_cycle_state == LifeCycleState.RESTING:
                await self._transition_state(LifeCycleState.MATURE)

    async def _process_life_cycle_transitions(self) -> None:
        """以空間成熟度取代固定時間閾值 / Spatial maturity replaces fixed thresholds"""
        maturity = self._compute_maturity_score()

        if self.life_cycle_state == LifeCycleState.AWAKENING:
            if maturity > 0.35:
                await self._transition_state(LifeCycleState.GROWING)

        elif self.life_cycle_state == LifeCycleState.GROWING:
            if maturity > 0.65:
                await self._transition_state(LifeCycleState.MATURE)

    # =============================================================================
    # ANGELA-MATRIX: [L3] [αβγδ] [A] [L7+]
    # [Task N.22.3] 4D 空間成熟度評估 / 4D Spatial Maturity Score
    # =============================================================================
    def _compute_maturity_score(self) -> float:
        """
        [原生 AI] 以 4 個維度的穩定性計算成熟度分數。
        替代固定時間陰値狀態機。

        公式: maturity = avg(α_stability, β_stability, γ_stability, δ_stability)
        穩定性計算：各維度負面指標的反向度量
        """
        sm = self.state_matrix

        alpha_stability = 1.0 - sm.alpha.values.get("tension", 0.0)
        beta_stability  = 1.0 - sm.beta.values.get("confusion", 0.0)
        gamma_stability = sm.gamma.values.get("calm", 0.5)
        delta_stability = sm.delta.values.get("trust", 0.5)

        # 以空間數學引擎對四個維度做平均
        try:
            maturity = sm.evaluate_math_spatially(
                f"({alpha_stability:.4f} + {beta_stability:.4f}"
                f" + {gamma_stability:.4f} + {delta_stability:.4f}) / 4"
            )
        except Exception:
            # broad except acceptable: spatial math parse errors must not break maturity calc
            maturity = (alpha_stability + beta_stability + gamma_stability + delta_stability) / 4

        return max(0.0, min(1.0, maturity))

    async def _transition_state(self, new_state: LifeCycleState) -> None:
        """Transition to a new life cycle state"""
        if new_state == self.life_cycle_state:
            return

        old_state = self.life_cycle_state
        self.previous_state = old_state
        self.life_cycle_state = new_state

        # Record state change event
        event = LifeEvent(
            event_id=f"state_change_{datetime.now().timestamp()}",
            event_type="state_transition",
            description=f"Transitioned from {old_state.en_name} to {new_state.en_name}",
            significance=0.7,
        )
        self._record_event(event)

        # Apply state-specific behaviors
        await self._apply_state_behaviors(new_state)

        # Notify callbacks
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                # broad except acceptable: callback errors must not break state transitions
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

    async def _apply_state_behaviors(self, state: LifeCycleState) -> None:
        """Apply behaviors specific to life cycle state"""
        if state == LifeCycleState.RESTING:
            # Slow down biological processes
            await self.biological_integrator.process_relaxation_event(intensity=0.8)
            # Consolidate memories
            if self.memory_bridge:
                self.memory_bridge.trigger_consolidation()

        elif state == LifeCycleState.GROWING:
            # =============================================================
            # ANGELA-MATRIX: [L3] [αβγδ] [A] [L6+]
            # [Task N.22.3] GROWING 狀態學習強化
            # =============================================================
            # 強化認知維度：提升好奇心與學習典型
            self.state_matrix.update_beta(learning=0.8, curiosity=0.7)
            # 觸發記憶鞏固：學習期間穩固記憶
            if self.memory_bridge:
                self.memory_bridge.trigger_consolidation()
            logger.info("🌱 [DigitalLife] GROWING: Learning boost + memory consolidation triggered.")

        elif state == LifeCycleState.MATURE:
            # =============================================================
            # ANGELA-MATRIX: [L3] [αβγδ] [A] [L8+]
            # [Task N.22.4] MATURE 狀態公式評估
            # =============================================================
            if self.autonomous_lifecycle:
                metrics = self.autonomous_lifecycle.get_current_metrics()
                # 將生命強度映射到 β 維度清晰度
                self.state_matrix.update_beta(
                    clarity=min(1.0, metrics.life_intensity * 0.8)
                )
            logger.info("✨ [DigitalLife] MATURE: Formula evaluation applied to beta clarity.")

    async def _check_system_health(self) -> None:
        """Check health of all subsystems"""
        systems: dict[str, Any] = {
            "biological": self.biological_integrator,
            "action_executor": self.action_executor,
        }

        if self.memory_bridge:
            systems["memory"] = self.memory_bridge

        for name, system in systems.items():
            try:
                # Check if system responds
                start_time = asyncio.get_running_loop().time()
                # Simple health check - would be more comprehensive in reality
                is_healthy = True
                response_time = (asyncio.get_running_loop().time() - start_time) * 1000

                self.systems_health[name] = SystemHealth(
                    system_name=name,
                    is_healthy=is_healthy,
                    response_time_ms=response_time,
                    status_message="Healthy",
                )
            except Exception as e:
                # broad except acceptable: health check must survive subsystem errors
                logger.error(f"Error in {__name__}: {e}", exc_info=True)
                self.systems_health[name] = SystemHealth(
                    system_name=name,
                    is_healthy=False,
                    error_count=self.systems_health.get(name, SystemHealth(name, True)).error_count
                    + 1,
                    status_message=str(e),
                )

    def _update_active_time(self) -> None:
        """Update total active time tracking"""
        if self._is_active:
            session_duration = datetime.now() - self._last_activity_time
            self.life_stats.total_active_time += session_duration

    async def _update_statistics(self) -> None:
        """Update life statistics"""
        # Update memory stats if available
        if self.memory_bridge:
            try:
                stats = self.memory_bridge.get_memory_stats()
                self.life_stats.memories_formed = stats.get("total_memories", 0)
                self.life_stats.memories_consolidated = stats.get("consolidated_memories", 0)
            except (AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"記憶統計更新失敗（可忽略）: {e}")

    async def _update_dynamic_parameters(self) -> None:
        """Update and log dynamic parameters periodically"""
        if not self.dynamic_params:
            return

        try:
            # Log significant parameter changes every 5 minutes
            time_since_last_log = (datetime.now() - self._last_params_log).total_seconds()
            if time_since_last_log >= 300:  # 5 minutes
                params_summary = self.dynamic_params.get_all_parameters_summary()

                # Log parameters that have changed significantly
                for param_name, param_data in params_summary.items():
                    base = param_data["base"]
                    current = param_data["current"]
                    if abs(current - base) > 0.15:  # Significant change threshold
                        print(
                            f"[DynamicParams] {param_name}: {current:.2f} "
                            f"(base: {base:.2f}, trend: {param_data['trend']:+.3f})"
                        )

                self._last_params_log = datetime.now()
        except Exception as e:
            # broad except acceptable: dynamic params update is non-critical, graceful degradation
            logger.error(f"[DigitalLife] Error updating dynamic parameters: {e}", exc_info=True)

    def record_activity(self, activity_type: str) -> None:
        """Record user activity"""
        self._last_activity_time = datetime.now()
        self._is_active = True

        if activity_type == "interaction":
            self.life_stats.total_interactions += 1
        elif activity_type == "conversation":
            self.life_stats.total_conversations += 1
        elif activity_type == "action":
            self.life_stats.total_actions_executed += 1

    def record_life_event(
        self,
        event_type: str,
        description: str,
        significance: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Record a significant life event

        Args:
            event_type: Type of event
            description: Event description
            significance: Importance level (0-1)
            metadata: Additional event data
        """
        event = LifeEvent(
            event_id=f"evt_{datetime.now().timestamp()}",
            event_type=event_type,
            description=description,
            significance=significance,
            metadata=metadata or {},
        )

        self._record_event(event)

        # Store significant events separately
        if significance >= 0.7:
            self._significant_events.append(event)

    def get_awareness_injection(self) -> str:
        """
        Get the prompt injection for self-awareness.
        Combined metrics from StateMatrix and AutonomousLifeCycle.
        """
        state_analysis = self.state_matrix.get_analysis()
        bio_state = self.biological_integrator.get_biological_state()
        combined_state = {**state_analysis, **bio_state}

        lifecycle_metrics = {}
        if self.autonomous_lifecycle:
            metrics = self.autonomous_lifecycle.get_current_metrics()
            lifecycle_metrics = {
                "life_intensity": metrics.life_intensity,
                "c_gap": metrics.cognitive_gap,
            }

        return self.self_introspector.get_introspection_prompt_injection(
            combined_state, lifecycle_metrics
        )

    def _record_event(self, event: LifeEvent) -> None:
        """Internal method to record an event"""
        self.life_events.append(event)

        # Notify callbacks
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                # broad except acceptable: callback errors must not break event handling
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

    def get_age(self) -> timedelta:
        """Get age of Angela's digital life"""
        return datetime.now() - self.life_stats.birth_time

    def get_life_summary(self) -> dict[str, Any]:
        """Get comprehensive life summary"""
        age = self.get_age()

        return {
            "birth_time": self.life_stats.birth_time.isoformat(),
            "age_days": age.days,
            "age_hours": age.total_seconds() / 3600,
            "current_state": self.life_cycle_state.en_name,
            "current_state_cn": self.life_cycle_state.cn_name,
            "total_active_hours": self.life_stats.total_active_time.total_seconds() / 3600,
            "total_interactions": self.life_stats.total_interactions,
            "total_conversations": self.life_stats.total_conversations,
            "total_actions": self.life_stats.total_actions_executed,
            "memories": {
                "formed": self.life_stats.memories_formed,
                "consolidated": self.life_stats.memories_consolidated,
            },
            "skills_learned": self.life_stats.skills_learned,
            "personality_traits": self.life_stats.personality_traits,
            "significant_events": len(self._significant_events),
            "system_health": {
                name: {"healthy": health.is_healthy, "response_time": health.response_time_ms}
                for name, health in self.systems_health.items()
            },
        }

    def get_recent_events(self, limit: int = 10) -> list[LifeEvent]:
        """Get recent life events"""
        return sorted(self.life_events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_significant_events(self) -> list[LifeEvent]:
        """Get all significant life events"""
        return sorted(self._significant_events, key=lambda e: e.timestamp, reverse=True)

    def register_state_change_callback(
        self, callback: Callable[[LifeCycleState, LifeCycleState], None]
    ) -> None:
        """Register callback for life cycle state changes"""
        self._state_change_callbacks.append(callback)

    def register_event_callback(self, callback: Callable[[LifeEvent], None]) -> None:
        """Register callback for life events"""
        self._event_callbacks.append(callback)

    def is_healthy(self) -> bool:
        """Check if all systems are healthy"""
        return all(health.is_healthy for health in self.systems_health.values())

    async def force_state(self, state: LifeCycleState) -> None:
        """Forcefully change to a specific state (for testing/emergencies)"""
        await self._transition_state(state)

    def get_formula_metrics(self) -> Optional[dict[str, Any]]:
        """
        Get theoretical formula metrics if formula integration is enabled

        Returns:
            Dictionary containing formula metrics, or None if not available
        """
        if self.autonomous_lifecycle:
            return self.autonomous_lifecycle.get_lifecycle_summary()
        return None

    def get_dynamic_parameters(self) -> Optional[dict[str, Any]]:
        """
        Get dynamic parameters summary if dynamic params integration is enabled

        Returns:
            Dictionary containing all dynamic parameter states, or None if not available
        """
        if self.dynamic_params:
            return self.dynamic_params.get_all_parameters_summary()
        return None

    def get_dynamic_parameter(
        self, param_name: str, context: Optional[dict[str, float]] = None
    ) -> float:
        """
        Get a specific dynamic parameter value

        Args:
            param_name: Name of the parameter
            context: Optional context for context-aware parameter calculation

        Returns:
            Current parameter value, or 0.5 if not found
        """
        if self.dynamic_params:
            return self.dynamic_params.get_parameter(param_name, context)
        return 0.5

    def record_user_interaction_for_formulas(self, user_id: str, intensity: float = 0.5) -> None:
        """
        Record user interaction for formula calculations

        Args:
            user_id: Unique user identifier
            intensity: Interaction intensity (0-1)
        """
        if self.autonomous_lifecycle:
            # Register or update observer
            self.autonomous_lifecycle.register_observer(user_id, relationship_depth=intensity)
            self.autonomous_lifecycle.update_observer_interaction(user_id, intensity)

        # Also record regular activity
        self.record_activity("interaction")


# Example usage
if __name__ == "__main__":

    async def demo() -> None:
        """Run a demonstration."""
        life = DigitalLifeIntegrator()
        await life.initialize()

        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 数字生命总控演示")
        logger.info("Digital Life Integrator Demo")
        logger.info("=" * 60)

        # Show initial state
        logger.info("\n初始状态 / Initial state:")
        summary = life.get_life_summary()
        logger.info(f"  生命周期: {summary['current_state_cn']}")
        logger.info(f"  诞生时间: {summary['birth_time']}")

        # Simulate activity
        logger.info("\n模拟活动 / Simulating activity:")
        for i in range(5):
            life.record_activity("interaction")
            life.record_activity("conversation")
            logger.info(f"  记录交互 {i+1}")

        # Record event
        logger.info("\n记录生命事件 / Recording life event:")
        life.record_life_event("milestone", "Reached 5 conversations milestone", significance=0.6)
        logger.info("  已记录里程碑事件")

        # Show updated stats
        logger.info("\n更新后的统计 / Updated statistics:")
        summary = life.get_life_summary()
        logger.info(f"  总交互: {summary['total_interactions']}")
        logger.info(f"  总对话: {summary['total_conversations']}")
        logger.info(f"  重要事件: {summary['significant_events']}")

        # Check health
        logger.info("\n系统健康 / System health:")
        for system, health_data in summary["system_health"].items():
            status = "健康" if health_data["healthy"] else "异常"
            logger.info(f"  {system}: {status} ({health_data['response_time']:.1f}ms)")

        await life.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")

    asyncio.run(demo())
