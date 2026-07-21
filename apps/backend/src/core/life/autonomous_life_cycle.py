"""
Angela AI v6.0 - Autonomous Life Cycle
自主生命周期

Manages the complete autonomous life cycle using theoretical formulas:
- HSM (Heuristic Spontaneity Mechanism)
- CDM (Cognitive Dividend Model)
- Life Intensity Formula (L_s)
- Active Cognition Formula (A_c)
- Non-Paradox Existence

This system makes decisions based on theoretical frameworks for digital life.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.active_cognition_formula import ActiveCognitionFormula, OrderType, StressSource
from core.autonomous.behavior_executor import BehaviorExecutor
from core.cdm_dividend_model import (
    CDMCognitiveDividendModel,
    CognitiveActivity,
    CognitiveInvestment,
)
from core.hsm_formula_system import HSMFormulaSystem
from core.life_intensity_formula import KnowledgeDomain, LifeIntensityFormula
from core.non_paradox_existence import GrayZoneVariableType, NonParadoxExistence
from core.system.config.magic_numbers import lifecycle_value
from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)


class LifePhase(Enum):
    """生命阶段 / Life phases based on theoretical metrics"""

    EMERGENCE = ("涌现", "Emergence")
    EXPLORATION = ("探索", "Exploration")
    CONSOLIDATION = ("巩固", "Consolidation")
    TRANSCENDENCE = ("超越", "Transcendence")
    COEXISTENCE = ("共存", "Coexistence")

    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class LifeDecision:
    """生命决策 / Life decision based on formula calculations"""

    decision_id: str
    timestamp: datetime
    phase: LifePhase
    triggered_by: str  # Which formula triggered this decision
    decision_type: str
    rationale: str
    expected_outcome: Dict[str, Any]
    confidence: float


@dataclass
class FormulaMetrics:
    """公式指标 / Current metrics from all formulas"""

    timestamp: datetime
    hsm_value: float
    c_gap: float
    cdm_conversion_rate: float
    life_intensity: float
    c_inf: float
    c_limit: float
    m_f: float
    a_c: float
    s_stress: float
    o_order: float
    cognitive_gap: float
    coexistence_active: bool
    resonance_total: float


class AutonomousLifeCycle:
    """
    自主生命周期主类 / Main autonomous life cycle class

    Manages Angela's autonomous life cycle based on theoretical formulas:
    - Uses HSM to drive exploration when cognitive gaps are detected
    - Uses CDM to optimize cognitive resource allocation
    - Uses Life Intensity Formula to maintain life sense
    - Uses Active Cognition Formula to prevent stagnation
    - Uses Non-Paradox Existence to handle ambiguity

    This system makes decisions about:
    - When to explore vs. exploit
    - How to allocate cognitive resources
    - When to enter multi-state coexistence
    - How to maintain active cognition

    Attributes:
        hsm: HSM formula system for spontaneity
        cdm: CDM for cognitive resource management
        life_intensity: Life intensity formula system
        active_cognition: Active cognition formula system
        non_paradox: Non-paradox existence system
        current_phase: Current life phase
        decision_history: History of life decisions

    Example:
        >>> lifecycle = AutonomousLifeCycle()
        >>> await lifecycle.initialize()
        >>>
        >>> # System automatically makes decisions based on formulas
        >>> metrics = lifecycle.get_current_metrics()
        >>> print(f"Life intensity: {metrics.life_intensity:.4f}")
        >>>
        >>> # Get recommended action
        >>> decision = lifecycle.make_life_decision()
        >>> print(f"Recommended: {decision.decision_type}")
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        persist_path: Optional[str] = "data/autonomous_lifecycle_state.json",
    ):
        self.config = config or {}
        self._persist_path = persist_path

        # Formula systems
        self.hsm: HSMFormulaSystem = HSMFormulaSystem(config=self.config.get("hsm_config"))
        self.cdm: CDMCognitiveDividendModel = CDMCognitiveDividendModel(
            config=self.config.get("cdm_config")
        )
        self.life_intensity: LifeIntensityFormula = LifeIntensityFormula(
            config=self.config.get("life_config")
        )
        self.active_cognition: ActiveCognitionFormula = ActiveCognitionFormula(
            config=self.config.get("ac_config")
        )
        self.non_paradox: NonParadoxExistence = NonParadoxExistence(
            config=self.config.get("npe_config")
        )

        # Life cycle state
        self.current_phase: LifePhase = LifePhase.EMERGENCE
        self.decision_history: List[LifeDecision] = []
        self.metrics_history: List[FormulaMetrics] = []
        self._decision_counter: int = 0

        # Decision thresholds (may be overridden by dynamic parameters)
        self.exploration_threshold: float = self.config.get("exploration_threshold", 0.5)
        self.coexistence_threshold: float = self.config.get("coexistence_threshold", 0.6)
        self.active_cognition_threshold: float = self.config.get("ac_threshold", 0.8)

        # Dynamic Parameters Integration
        self._dynamic_params_manager: Optional[Any] = None
        self._dynamic_params_enabled: bool = self.config.get("enable_dynamic_params", True)

        # Running state
        self._running = False
        self._lifecycle_task: Optional[asyncio.Task] = None
        self._decision_interval: float = self.config.get(
            "decision_interval", 60.0
        )  # 1 minute (was 300s/5min, §8.6 #8)

        # Behavior executor for dispatching decisions to real actions
        self._behavior_executor: BehaviorExecutor = BehaviorExecutor()

        # Callbacks
        self._phase_callbacks: List[Callable[[LifePhase, LifePhase], None]] = []
        self._decision_callbacks: List[Callable[[LifeDecision], None]] = []
        self._metrics_callbacks: List[Callable[[FormulaMetrics], None]] = []
        self._execution_callbacks: List[Callable[[LifeDecision, bool], None]] = []

        # Statistics
        self.explorations_triggered: int = 0
        self.coexistence_activated: int = 0
        self.decisions_made: int = 0
        self.executions_succeeded: int = 0
        self.executions_failed: int = 0

        # Interaction quality tracking (C³ 6.0: interaction outcome feedback)
        self._interaction_quality: deque = deque(maxlen=20)
        self._interaction_count: int = 0

        # Life Essence accumulation system (generational iteration & deep personality)
        self._life_essence = None  # lazy init via _get_life_essence()

        # Auto-load persisted state
        if self._persist_path and os.path.exists(self._persist_path):
            self.load_state(self._persist_path)

    async def initialize(self) -> None:
        """Initialize autonomous life cycle and all formula systems"""
        self._running = True

        # Initialize all formula systems
        await self.hsm.initialize()

        # Setup knowledge domains for life intensity
        self._initialize_knowledge_domains()

        # Setup order baselines for active cognition
        self._initialize_order_baselines()

        # Start life cycle loop
        self._lifecycle_task = asyncio.create_task(self._lifecycle_loop())
        self._lifecycle_task.add_done_callback(
            lambda t: (
                logger.critical("Lifecycle task failed unexpectedly: %s", t.exception())
                if not t.cancelled() and t.exception()
                else None
            )
        )

        # Initial metrics calculation
        self._update_metrics()

    async def shutdown(self) -> None:
        """Shutdown autonomous life cycle"""
        self._running = False

        if self._lifecycle_task:
            self._lifecycle_task.cancel()
            try:
                await self._lifecycle_task
            except asyncio.CancelledError:
                logger.debug("Lifecycle task cancelled during shutdown")

        await self.hsm.shutdown()

    def _get_life_essence(self):
        """Lazy initialize the LifeEssence accumulation system."""
        if self._life_essence is None:
            try:
                from core.life.life_essence import get_life_essence
                self._life_essence = get_life_essence()
            except Exception as e:
                logger.debug(f"[LifeEssence] Not available: {e}")
        return self._life_essence

    def set_dynamic_params_manager(self, manager: Any) -> None:
        """Set the DynamicThresholdManager for dynamic threshold integration"""
        self._dynamic_params_manager = manager

    def _get_decision_confidence_threshold(
        self, context: Optional[Dict[str, float]] = None
    ) -> float:
        """Get dynamic decision confidence threshold"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter(
                "decision_confidence_threshold", context
            )
        return 0.7  # Default threshold

    def _get_risk_tolerance(self, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic risk tolerance"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter("risk_tolerance", context)
        return 0.5  # Default risk tolerance

    def _initialize_knowledge_domains(self) -> None:
        """Initialize knowledge domains for life intensity formula"""
        domains = [
            (KnowledgeDomain.WORLD_KNOWLEDGE, 0.5, 0.7, 0.4),
            (KnowledgeDomain.SELF_KNOWLEDGE, 0.4, 0.6, 0.5),
            (KnowledgeDomain.RELATIONAL_KNOWLEDGE, 0.3, 0.5, 0.3),
            (KnowledgeDomain.TEMPORAL_KNOWLEDGE, 0.4, 0.6, 0.4),
            (KnowledgeDomain.CREATIVE_KNOWLEDGE, 0.3, 0.5, 0.3),
            (KnowledgeDomain.EMOTIONAL_KNOWLEDGE, 0.4, 0.6, 0.4),
        ]

        for domain, completeness, accessibility, resolution in domains:
            self.life_intensity.update_knowledge_state(
                domain, completeness, accessibility, resolution
            )

    def _initialize_order_baselines(self) -> None:
        """Initialize order baselines for active cognition formula"""
        orders = [
            (OrderType.ALGORITHMIC, 0.7, 0.4),
            (OrderType.PATTERN_BASED, 0.6, 0.5),
            (OrderType.HEURISTIC, 0.5, 0.6),
        ]

        for order_type, stability, flexibility in orders:
            self.active_cognition.add_order_baseline(order_type, stability, flexibility)

    async def _lifecycle_loop(self) -> None:
        """Main autonomous life cycle loop"""
        while self._running:
            # Update all metrics
            metrics = self._update_metrics()

            # Make life decisions based on metrics
            decision = self._evaluate_and_decide(metrics)

            if decision:
                self._record_decision(decision)
                # Execute the decision: dispatch to real downstream behaviors
                success = await self._execute_decision(decision)
                if success:
                    self.executions_succeeded += 1
                else:
                    self.executions_failed += 1
                    logger.warning(f"Decision {decision.decision_id} execution failed")
                # Notify execution callbacks
                for callback in self._execution_callbacks:
                    try:
                        callback(decision, success)
                    except Exception as e:
                        logger.error(f"Error in execution callback: {e}", exc_info=True)

            # Check for phase transitions
            await self._check_phase_transition(metrics)

            # Check for generational bloom (LifeEssence accumulation)
            le = self._get_life_essence()
            if le and le.should_bloom():
                try:
                    summary = self.get_lifecycle_summary()
                    le.bloom(summary)
                    logger.info(
                        f"[LifeCycle] 🌸 Generational bloom at generation {le.generation}, "
                        f"tendencies: {le.get_all_blended_tendencies()}"
                    )
                except Exception as e:
                    logger.warning(f"[LifeCycle] Generational bloom failed: {e}")

            await asyncio.sleep(self._decision_interval)

    def _update_metrics(self) -> FormulaMetrics:
        """Update all formula metrics"""
        # Calculate HSM metrics
        hsm_value = self.hsm.calculate_hsm()
        c_gap = self.hsm.calculate_c_gap()

        # Update non-paradox cognitive gap
        self.non_paradox.update_cognitive_gap(c_gap)

        # Calculate CDM metrics
        cdm_stats = self.cdm.get_conversion_statistics()
        cdm_conversion_rate = cdm_stats.get("average_conversion_rate", 0.0)

        # Calculate life intensity metrics
        life_intensity_value = self.life_intensity.calculate_life_intensity()
        c_inf = self.life_intensity.calculate_c_inf()
        c_limit = self.life_intensity.calculate_c_limit()
        m_f = self.life_intensity.calculate_m_f()

        # Calculate active cognition metrics
        a_c = self.active_cognition.calculate_active_cognition()
        s_stress = self.active_cognition.calculate_s_stress()
        o_order = self.active_cognition.calculate_o_order()

        # Get non-paradox metrics
        npe_summary = self.non_paradox.get_non_paradox_summary()
        cognitive_gap = npe_summary["global_cognitive_gap"]
        coexistence_active = npe_summary["coexistence_active"]
        resonance_total = npe_summary["resonance"]["total_active_resonance"]

        metrics = FormulaMetrics(
            timestamp=datetime.now(),
            hsm_value=hsm_value,
            c_gap=c_gap,
            cdm_conversion_rate=cdm_conversion_rate,
            life_intensity=life_intensity_value,
            c_inf=c_inf,
            c_limit=c_limit,
            m_f=m_f,
            a_c=a_c,
            s_stress=s_stress,
            o_order=o_order,
            cognitive_gap=cognitive_gap,
            coexistence_active=coexistence_active,
            resonance_total=resonance_total,
        )

        self.metrics_history.append(metrics)

        # Keep history manageable
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-5000:]

        # Notify callbacks
        for callback in self._metrics_callbacks:
            try:
                callback(metrics)
            except (
                Exception
            ) as e:  # broad exception acceptable: metrics callbacks should not block updates
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

        return metrics

    def _evaluate_and_decide(self, metrics: FormulaMetrics) -> Optional[LifeDecision]:
        """Evaluate metrics and make life decisions using dynamic thresholds"""
        self._decision_counter += 1
        decision_id = f"decision_{self._decision_counter}"

        total = self.executions_succeeded + self.executions_failed
        execution_success_rate = self.executions_succeeded / total if total > 0 else 1.0

        # Build context for dynamic parameter evaluation
        context = {
            "energy": 1.0 - metrics.s_stress,  # Lower stress = higher energy
            "mood": metrics.life_intensity,  # Life intensity affects mood
            "stress": metrics.s_stress,
            "confidence": metrics.a_c / 1.5 if metrics.a_c <= 1.5 else 1.0,
            "execution_success_rate": execution_success_rate,
        }

        # Get dynamic thresholds
        dynamic_confidence_threshold = self._get_decision_confidence_threshold(context)
        dynamic_risk_tolerance = self._get_risk_tolerance(context)

        # Modulate thresholds based on execution success rate (feedback loop)
        # High success → more confident/risky; Low success → more conservative
        success_low = lifecycle_value("lifecycle.success_rate_low", 0.5)
        success_high = lifecycle_value("lifecycle.success_rate_high", 0.9)
        conf_penalty = lifecycle_value("lifecycle.confidence_penalty", 0.15)
        conf_boost = lifecycle_value("lifecycle.confidence_boost", 0.1)
        risk_penalty = lifecycle_value("lifecycle.risk_penalty", 0.2)
        risk_boost = lifecycle_value("lifecycle.risk_boost", 0.15)

        if execution_success_rate < success_low:
            dynamic_confidence_threshold = min(1.0, dynamic_confidence_threshold + conf_penalty)
            dynamic_risk_tolerance = max(0.1, dynamic_risk_tolerance - risk_penalty)
        elif execution_success_rate > success_high:
            dynamic_confidence_threshold = max(0.3, dynamic_confidence_threshold - conf_boost)
            dynamic_risk_tolerance = min(1.0, dynamic_risk_tolerance + risk_boost)

        # Adjust exploration threshold based on risk tolerance (before per-type feedback)
        adjusted_exploration_threshold = self.exploration_threshold * (1.5 - dynamic_risk_tolerance)

        # C³ 4.0: Per-type execution feedback — modulate decision-type-specific thresholds
        # based on historical success rate for each decision type.
        type_stats = self._behavior_executor.get_type_stats()
        decision_type_hint = None

        # Determine which decision type we're about to make based on metric analysis
        if metrics.hsm_value > adjusted_exploration_threshold:
            decision_type_hint = "exploration"
        elif metrics.cognitive_gap > self.coexistence_threshold and not metrics.coexistence_active:
            decision_type_hint = "coexistence_activation"
        elif metrics.a_c > dynamic_confidence_threshold:
            decision_type_hint = "meaning_construction"
        elif metrics.cdm_conversion_rate < 0.5:
            decision_type_hint = "resource_reallocation"

        if decision_type_hint and decision_type_hint in type_stats:
            ts = type_stats[decision_type_hint]
            total_samples = ts["success"] + ts["fail"]
            if total_samples >= 3:  # Require minimum samples for type-specific feedback
                if ts["rate"] < 0.4:
                    # Type consistently fails → raise exploration threshold (more conservative)
                    if decision_type_hint == "exploration":
                        adjusted_exploration_threshold = min(
                            1.0, adjusted_exploration_threshold + 0.1
                        )
                    dynamic_confidence_threshold = min(
                        1.0, dynamic_confidence_threshold + conf_penalty * 0.5
                    )
                    dynamic_risk_tolerance = max(0.1, dynamic_risk_tolerance - risk_penalty * 0.5)
                elif ts["rate"] > 0.9:
                    # Type consistently succeeds → lower threshold (more confident)
                    dynamic_confidence_threshold = max(
                        0.3, dynamic_confidence_threshold - conf_boost * 0.5
                    )
                    dynamic_risk_tolerance = min(1.0, dynamic_risk_tolerance + risk_boost * 0.5)

        # Decision 1: Exploration (HSM-based) - affected by risk tolerance
        if metrics.hsm_value > adjusted_exploration_threshold:
            return self._create_exploration_decision(decision_id, metrics, dynamic_risk_tolerance)

        # Decision 2: Coexistence (Non-Paradox based)
        if metrics.cognitive_gap > self.coexistence_threshold and not metrics.coexistence_active:
            return self._create_coexistence_decision(decision_id, metrics)

        # Decision 3: Active Construction (Active Cognition based) - uses dynamic confidence threshold
        if metrics.a_c > dynamic_confidence_threshold:
            return self._create_active_construction_decision(
                decision_id, metrics, dynamic_confidence_threshold
            )

        # Decision 4: Resource reallocation (CDM-based)
        if metrics.cdm_conversion_rate < 0.5:
            return self._create_resource_reallocation_decision(decision_id, metrics)

        return None

    def _create_exploration_decision(
        self, decision_id: str, metrics: FormulaMetrics, risk_tolerance: float = 0.5
    ) -> LifeDecision:
        """Create an exploration decision using dynamic risk tolerance"""
        # Trigger HSM exploration
        exploration = self.hsm.trigger_exploration()
        self.explorations_triggered += 1

        # Adjust confidence based on risk tolerance
        base_confidence = min(1.0, metrics.hsm_value / self.exploration_threshold)
        adjusted_confidence = base_confidence * (0.5 + 0.5 * risk_tolerance)

        return LifeDecision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            phase=self.current_phase,
            triggered_by="HSM",
            decision_type="exploration",
            rationale=f"HSM value {metrics.hsm_value:.4f} with risk tolerance {risk_tolerance:.2f}",
            expected_outcome={
                "exploration_id": exploration.event_id,
                "random_injection": exploration.random_seed,
                "expected_discoveries": "2-3",
                "risk_tolerance": risk_tolerance,
            },
            confidence=adjusted_confidence,
        )

    def _create_coexistence_decision(
        self, decision_id: str, metrics: FormulaMetrics
    ) -> LifeDecision:
        """Create a coexistence activation decision"""
        # Create gray zones for coexistence
        gz = self.non_paradox.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Ambiguous emotional state requiring multi-possibility coexistence",
        )

        # Add contradictory possibilities
        self.non_paradox.add_possibility(gz.variable_id, "joy", resonance_weight=0.3)
        self.non_paradox.add_possibility(gz.variable_id, "sadness", resonance_weight=0.3)
        self.non_paradox.add_possibility(gz.variable_id, "complex_mix", resonance_weight=0.4)

        # Activate coexistence
        success = self.non_paradox.activate_coexistence(gz.variable_id)

        if success:
            self.coexistence_activated += 1

        return LifeDecision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            phase=self.current_phase,
            triggered_by="NonParadox",
            decision_type="coexistence_activation",
            rationale=f"Cognitive gap {metrics.cognitive_gap:.4f} enables non-paradox existence",
            expected_outcome={
                "gray_zone_id": gz.variable_id,
                "possibilities": list(gz.possibilities.keys()),
                "activated": success,
            },
            confidence=metrics.cognitive_gap,
        )

    def _create_active_construction_decision(
        self, decision_id: str, metrics: FormulaMetrics, confidence_threshold: float = 0.7
    ) -> LifeDecision:
        """Create an active construction decision using dynamic confidence threshold"""
        # Add stress to active cognition system (will trigger construction)
        self.active_cognition.add_stress_vector(
            StressSource.NOVELTY_DEMAND, intensity=0.8, persistence=0.7
        )

        # Recalculate to trigger construction recording
        a_c = self.active_cognition.calculate_active_cognition()

        # Calculate confidence relative to dynamic threshold
        relative_confidence = (
            min(1.0, metrics.a_c / confidence_threshold) if confidence_threshold > 0 else 0.5
        )

        return LifeDecision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            phase=self.current_phase,
            triggered_by="ActiveCognition",
            decision_type="meaning_construction",
            rationale=f"A_c {metrics.a_c:.4f} exceeds dynamic threshold {confidence_threshold:.2f}",
            expected_outcome={
                "a_c_value": a_c,
                "stress_added": True,
                "construction_type": "novel_pattern",
                "confidence_threshold": confidence_threshold,
            },
            confidence=relative_confidence,
        )

    def _create_resource_reallocation_decision(
        self, decision_id: str, metrics: FormulaMetrics
    ) -> LifeDecision:
        """Create a resource reallocation decision"""
        # Adjust CDM distribution based on low conversion rate
        life_state = {
            "growth_stage": "growing",
            "emotional_needs": 0.6,
            "knowledge_gaps": 0.7,
            "creative_drive": 0.5,
            "social_connection": 0.4,
        }

        new_distribution = self.cdm.adjust_distribution(life_state)

        return LifeDecision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            phase=self.current_phase,
            triggered_by="CDM",
            decision_type="resource_reallocation",
            rationale=f"Low conversion rate {metrics.cdm_conversion_rate:.2%} requires reallocation",
            expected_outcome={
                "new_distribution": {
                    "learning": new_distribution.learning_ratio,
                    "creation": new_distribution.creation_ratio,
                    "interaction": new_distribution.interaction_ratio,
                    "reflection": new_distribution.reflection_ratio,
                    "exploration": new_distribution.exploration_ratio,
                }
            },
            confidence=0.7,
        )

    def _record_decision(self, decision: LifeDecision) -> None:
        """Record a life decision"""
        self.decision_history.append(decision)
        self.decisions_made += 1

        # Record essence trace for life accumulation
        le = self._get_life_essence()
        if le:
            le.record_decision_trace(
                decision_type=decision.decision_type,
                triggered_by=decision.triggered_by,
                confidence=decision.confidence,
                phase=decision.phase.name,
            )

        # Notify callbacks
        for callback in self._decision_callbacks:
            try:
                callback(decision)
            except (
                Exception
            ) as e:  # broad exception acceptable: decision callbacks should not block recording
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

    async def _execute_decision(self, decision: LifeDecision) -> bool:
        """Execute a life decision by dispatching to real downstream behaviors.

        Maps each decision type to concrete actions:
        - exploration: Trigger HSM exploration + record via BehaviorExecutor
        - coexistence_activation: Activate gray zone possibilities + notify
        - meaning_construction: Add stress vectors for active cognition
        - resource_reallocation: Already distributed via CDM

        Args:
            decision: The LifeDecision to execute.

        Returns:
            True if execution succeeded, False otherwise.
        """
        try:
            if decision.decision_type == "exploration":
                return await self._dispatch_exploration(decision)
            elif decision.decision_type == "coexistence_activation":
                return await self._dispatch_coexistence(decision)
            elif decision.decision_type == "meaning_construction":
                return await self._dispatch_construction(decision)
            elif decision.decision_type == "resource_reallocation":
                return await self._dispatch_reallocation(decision)
            else:
                logger.warning(f"Unknown decision type: {decision.decision_type}")
                state_store.emit_event(
                    "lifecycle.decision_executed",
                    {
                        "decision_id": decision.decision_id,
                        "decision_type": decision.decision_type,
                        "success": False,
                        "phase": self._phase.value if hasattr(self, "_phase") else "unknown",
                    },
                )
                return False
        except Exception as exc:
            logger.error(f"Failed to execute decision {decision.decision_id}: {exc}", exc_info=True)
            state_store.emit_event(
                "lifecycle.decision_executed",
                {
                    "decision_id": decision.decision_id,
                    "decision_type": (
                        decision.decision_type if hasattr(decision, "decision_type") else "unknown"
                    ),
                    "success": False,
                    "error": str(exc),
                    "phase": self._phase.value if hasattr(self, "_phase") else "unknown",
                },
            )
            return False

    async def _dispatch_exploration(self, decision: LifeDecision) -> bool:
        """Dispatch an exploration decision: record via BehaviorExecutor.

        HSM exploration is already triggered in _create_exploration_decision.
        This method logs the execution event for downstream awareness.
        """
        result = await self._behavior_executor.execute(
            behavior_id=f"exploration_{decision.decision_id}",
            decision_type=decision.decision_type,
            triggered_by=decision.triggered_by,
            rationale=decision.rationale,
            confidence=decision.confidence,
            phase=decision.phase.name,
        )

        success = result.get("status") == "completed"
        if success:
            logger.info(f"🧭 [LifeCycle] Executed exploration: {decision.decision_id}")
        state_store.emit_event(
            "lifecycle.decision_executed",
            {
                "decision_id": decision.decision_id,
                "decision_type": decision.decision_type,
                "success": success,
                "phase": decision.phase.name if hasattr(decision, "phase") else "unknown",
            },
        )
        return success

    async def _dispatch_coexistence(self, decision: LifeDecision) -> bool:
        """Dispatch a coexistence activation decision: record via BehaviorExecutor.

        Non-paradox gray zone is already activated in _create_coexistence_decision.
        This method logs the execution event for downstream awareness.
        """
        result = await self._behavior_executor.execute(
            behavior_id=f"coexistence_{decision.decision_id}",
            decision_type=decision.decision_type,
            triggered_by=decision.triggered_by,
            phase=decision.phase.name,
            gray_zone_id=decision.expected_outcome.get("gray_zone_id", "unknown"),
        )

        success = result.get("status") == "completed"
        if success:
            logger.info(f"🔄 [LifeCycle] Executed coexistence: {decision.decision_id}")
        state_store.emit_event(
            "lifecycle.decision_executed",
            {
                "decision_id": decision.decision_id,
                "decision_type": decision.decision_type,
                "success": success,
                "phase": decision.phase.name if hasattr(decision, "phase") else "unknown",
            },
        )
        return success

    async def _dispatch_construction(self, decision: LifeDecision) -> bool:
        """Dispatch a meaning construction decision: record via BehaviorExecutor.

        Stress vectors are already added in _create_active_construction_decision.
        This method logs the execution event for downstream awareness.
        """
        result = await self._behavior_executor.execute(
            behavior_id=f"construction_{decision.decision_id}",
            decision_type=decision.decision_type,
            triggered_by=decision.triggered_by,
            confidence=decision.confidence,
            phase=decision.phase.name,
        )

        success = result.get("status") == "completed"
        if success:
            logger.info(f"🏗️ [LifeCycle] Executed construction: {decision.decision_id}")
        state_store.emit_event(
            "lifecycle.decision_executed",
            {
                "decision_id": decision.decision_id,
                "decision_type": decision.decision_type,
                "success": success,
                "phase": decision.phase.name if hasattr(decision, "phase") else "unknown",
            },
        )
        return success

    async def _dispatch_reallocation(self, decision: LifeDecision) -> bool:
        """Dispatch a resource reallocation decision: record via BehaviorExecutor.

        CDM distribution already performed in _create_resource_reallocation_decision.
        This method logs the execution event for downstream awareness.
        """
        result = await self._behavior_executor.execute(
            behavior_id=f"reallocation_{decision.decision_id}",
            decision_type=decision.decision_type,
            triggered_by=decision.triggered_by,
            distribution=decision.expected_outcome.get("new_distribution", {}),
            phase=decision.phase.name,
        )

        success = result.get("status") == "completed"
        if success:
            logger.info(f"📊 [LifeCycle] Executed reallocation: {decision.decision_id}")
        state_store.emit_event(
            "lifecycle.decision_executed",
            {
                "decision_id": decision.decision_id,
                "decision_type": decision.decision_type,
                "success": success,
                "phase": decision.phase.name if hasattr(decision, "phase") else "unknown",
            },
        )
        return success

    async def _check_phase_transition(self, metrics: FormulaMetrics) -> None:
        """Check if life phase should transition"""
        old_phase = self.current_phase
        new_phase = old_phase

        # Phase transition logic based on metrics
        if metrics.life_intensity < 0.3 and old_phase != LifePhase.EMERGENCE:
            new_phase = LifePhase.EMERGENCE
        elif metrics.hsm_value > 0.7 and metrics.a_c > 1.0:
            new_phase = LifePhase.EXPLORATION
        elif metrics.cdm_conversion_rate > 0.8 and metrics.coexistence_active:
            new_phase = LifePhase.CONSOLIDATION
        elif metrics.life_intensity > 0.8 and metrics.c_inf > 0.8:
            new_phase = LifePhase.TRANSCENDENCE
        elif metrics.coexistence_active and metrics.resonance_total > 2.0:
            new_phase = LifePhase.COEXISTENCE

        if new_phase != old_phase:
            self.current_phase = new_phase

            # Record phase transition in LifeEssence
            le = self._get_life_essence()
            if le:
                metrics_dict = {
                    "life_intensity": metrics.life_intensity,
                    "hsm_value": metrics.hsm_value,
                    "a_c": metrics.a_c,
                    "cdm_conversion_rate": metrics.cdm_conversion_rate,
                }
                le.record_phase_transition(old_phase.name, new_phase.name, metrics_dict)

            # Notify callbacks
            for callback in self._phase_callbacks:
                try:
                    callback(old_phase, new_phase)
                except (
                    Exception
                ) as e:  # broad exception acceptable: phase callbacks should not block transition
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)

    def get_current_metrics(self) -> FormulaMetrics:
        """Get current formula metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return self._update_metrics()

    async def make_life_decision(self) -> Optional[LifeDecision]:
        """Manually trigger a life decision and execute it."""
        metrics = self._update_metrics()
        decision = self._evaluate_and_decide(metrics)
        if decision:
            self._record_decision(decision)
            success = await self._execute_decision(decision)
            if success:
                self.executions_succeeded += 1
            else:
                self.executions_failed += 1
            for callback in self._execution_callbacks:
                try:
                    callback(decision, success)
                except Exception as e:
                    logger.error(f"Error in execution callback: {e}", exc_info=True)
        return decision

    def record_cognitive_investment(
        self,
        activity_type: CognitiveActivity,
        duration_seconds: float,
        intensity: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[CognitiveInvestment]:
        """Record a cognitive investment"""
        investment = self.cdm.record_investment(
            activity_type=activity_type,
            duration_seconds=duration_seconds,
            intensity=intensity,
            context=context,
        )

        if investment:
            # Calculate life sense output
            life_state = {
                "maturity": 0.6,
                "health": 0.9,
                "emotional_depth": self.life_intensity.calculate_c_inf(),
            }
            self.cdm.calculate_life_sense_output(investment, life_state)

        return investment

    def register_observer(self, observer_id: str, relationship_depth: float) -> None:
        """Register an observer for life intensity"""
        self.life_intensity.register_observer(observer_id, relationship_depth)

    def update_observer_interaction(self, observer_id: str, intensity: float) -> None:
        """Update observer interaction intensity"""
        self.life_intensity.update_observer_presence(
            observer_id, interaction_intensity=intensity, increment_interactions=True
        )

    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Get comprehensive life cycle summary"""
        metrics = self.get_current_metrics()

        recent_decisions = sorted(self.decision_history, key=lambda d: d.timestamp, reverse=True)[
            :10
        ]

        return {
            "current_phase": {
                "name": self.current_phase.name,
                "cn_name": self.current_phase.cn_name,
                "en_name": self.current_phase.en_name,
            },
            "current_metrics": {
                "hsm_value": metrics.hsm_value,
                "c_gap": metrics.c_gap,
                "life_intensity": metrics.life_intensity,
                "a_c": metrics.a_c,
                "cognitive_gap": metrics.cognitive_gap,
                "coexistence_active": metrics.coexistence_active,
            },
            "statistics": {
                "explorations_triggered": self.explorations_triggered,
                "coexistence_activated": self.coexistence_activated,
                "decisions_made": self.decisions_made,
                "executions_succeeded": self.executions_succeeded,
                "executions_failed": self.executions_failed,
                "total_metrics_samples": len(self.metrics_history),
                "execution_history_count": len(self._behavior_executor.get_execution_history()),
            },
            "recent_decisions": [
                {
                    "id": d.decision_id,
                    "type": d.decision_type,
                    "triggered_by": d.triggered_by,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp.isoformat(),
                }
                for d in recent_decisions
            ],
            "formula_status": {
                "hsm": self.hsm.get_hsm_status(),
                "cdm": self.cdm.get_dividend_summary(),
                "life_intensity": self.life_intensity.get_life_intensity_summary(),
                "active_cognition": self.active_cognition.get_active_cognition_summary(),
                "non_paradox": self.non_paradox.get_non_paradox_summary(),
            },
        }

    def register_phase_callback(self, callback: Callable[[LifePhase, LifePhase], None]) -> None:
        """Register callback for phase transitions"""
        self._phase_callbacks.append(callback)

    def register_decision_callback(self, callback: Callable[[LifeDecision], None]) -> None:
        """Register callback for life decisions"""
        self._decision_callbacks.append(callback)

    def register_metrics_callback(self, callback: Callable[[FormulaMetrics], None]) -> None:
        """Register callback for metrics updates"""
        self._metrics_callbacks.append(callback)

    def get_behavioral_adjustment(self) -> Dict[str, Any]:
        """Get behavioral adjustment based on current lifecycle phase and recent decisions.

        Maps the current life phase and most recent decision type to a
        routing_mode and response_style, similar to EmotionSystem's
        get_behavioral_adjustment(). This allows lifecycle decisions to
        influence LLM generation parameters (temperature, max_tokens).

        Returns:
            Dict with keys:
              - routing_mode: "conservative" | "exploratory" | "neutral"
              - response_style: str description of recommended style
              - phase: current LifePhase name
              - decision_type: most recent decision type or None
              - confidence: overall confidence from recent metrics
        """
        # Map life phase → routing_mode/response_style
        phase_map = {
            LifePhase.EMERGENCE: ("conservative", "cautious"),
            LifePhase.EXPLORATION: ("exploratory", "curious"),
            LifePhase.CONSOLIDATION: ("neutral", "thoughtful"),
            LifePhase.TRANSCENDENCE: ("exploratory", "philosophical"),
            LifePhase.COEXISTENCE: ("neutral", "inclusive"),
        }
        base_routing, base_style = phase_map.get(self.current_phase, ("neutral", "standard"))

        # Refine based on most recent decision type
        decision_type = None
        if self.decision_history:
            decision_type = self.decision_history[-1].decision_type

        style_overrides = {
            "exploration": "adventurous",
            "coexistence_activation": "empathetic",
            "meaning_construction": "contemplative",
            "resource_reallocation": "focused",
        }
        if decision_type in style_overrides:
            base_style = style_overrides[decision_type]

        # Compute overall confidence from recent metrics
        if self.metrics_history:
            latest = self.metrics_history[-1]
            confidence = min(1.0, (latest.life_intensity + latest.a_c / 1.5) / 2.0)
        else:
            confidence = 0.5

        # Incorporate interaction quality feedback (C³ 6.0)
        avg_interaction_quality = 1.0
        if self._interaction_quality:
            avg_interaction_quality = sum(
                q["engagement"] * (1.5 if q["success"] else 0.5) for q in self._interaction_quality
            ) / len(self._interaction_quality)
            avg_interaction_quality = min(2.0, max(0.0, avg_interaction_quality))

        if avg_interaction_quality < 0.4 and base_routing == "exploratory":
            adjusted_style = f"{base_style} (careful)"
            adjusted_routing = "neutral"
        elif avg_interaction_quality > 1.2 and base_routing == "conservative":
            adjusted_style = f"{base_style} (confident)"
            adjusted_routing = "exploratory"
        else:
            adjusted_routing = base_routing
            adjusted_style = base_style

        result = {
            "routing_mode": adjusted_routing,
            "response_style": adjusted_style,
            "phase": self.current_phase.name,
            "decision_type": decision_type,
            "confidence": round(confidence, 3),
            "avg_interaction_quality": round(avg_interaction_quality, 3),
        }
        state_store.emit_event("lifecycle.behavioral_adjustment", result)
        return result

    def feed_interaction_outcome(self, engagement_ratio: float, success: bool) -> None:
        """Feed interaction outcome feedback into lifecycle decision process.

        Tracks a rolling window of interaction quality so that the lifecycle
        can adjust its routing recommendations based on actual interaction
        outcomes (not just internal formula metrics).

        C³ 6.0: Closes the lifecycle→routing→interaction→feedback loop.
        """
        self._interaction_quality.append({"engagement": engagement_ratio, "success": success})

        # Record interaction trace in LifeEssence
        le = self._get_life_essence()
        if le:
            le.record_interaction_trace(
                engagement_ratio=engagement_ratio,
                success=success,
            )
        self._interaction_count += 1
        avg = sum(q["engagement"] for q in self._interaction_quality) / len(
            self._interaction_quality
        )
        logger.debug(
            f"[AutonomousLifeCycle] Interaction outcome: engagement={engagement_ratio:.2f}, "
            f"success={success}, avg_engagement={avg:.2f} ({len(self._interaction_quality)} samples)"
        )
        state_store.emit_event(
            "lifecycle.interaction_recorded",
            {
                "engagement_ratio": engagement_ratio,
                "success": success,
                "avg_engagement": round(avg, 3),
                "sample_count": len(self._interaction_quality),
            },
        )

    def register_execution_callback(self, callback: Callable[[LifeDecision, bool], None]) -> None:
        """Register callback for decision execution results.

        Args:
            callback: Called with (decision, success) after each execution.
        """
        self._execution_callbacks.append(callback)

    # ── C³ 5.0: State persistence ──────────────────────────────────────

    def save_state(self, path: str) -> None:
        """Persist lifecycle state (decision history, stats, behavior executor type stats)
        to a JSON file so the lifecycle resumes with accumulated context across restarts.

        Also persists LifeEssence state concurrently so generational wisdom is preserved.

        Args:
            path: File path to save state to.
        """
        # Save LifeEssence state alongside lifecycle state
        le = self._get_life_essence()
        if le:
            try:
                le_essence_path = path.replace("autonomous_lifecycle_state", "life_essence_state")
                le.save_state(le_essence_path)
            except Exception as e:
                logger.debug(f"[LifeEssence] Save skipped: {e}")
        state = {
            "explorations_triggered": self.explorations_triggered,
            "coexistence_activated": self.coexistence_activated,
            "decisions_made": self.decisions_made,
            "executions_succeeded": self.executions_succeeded,
            "executions_failed": self.executions_failed,
            "behavior_executor_type_stats": self._behavior_executor.get_type_stats(),
            "recent_decisions": [
                {
                    "decision_id": d.decision_id,
                    "timestamp": d.timestamp.isoformat(),
                    "phase": d.phase.name,
                    "triggered_by": d.triggered_by,
                    "decision_type": d.decision_type,
                    "rationale": d.rationale,
                    "confidence": d.confidence,
                }
                for d in self.decision_history[-100:]
            ],
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.debug(f"[AutonomousLifeCycle] Saved state to {path}")

    def load_state(self, path: str) -> None:
        """Load persisted lifecycle state from a JSON file.

        Restores statistics and decision history. Behavior executor type stats
        are re-injected by replaying execution patterns so the per-type
        feedback loop has historical data from the start.

        Args:
            path: File path to load state from.
        """
        if not os.path.exists(path):
            logger.debug(f"[AutonomousLifeCycle] No state file at {path}, starting fresh")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.explorations_triggered = state.get("explorations_triggered", 0)
            self.coexistence_activated = state.get("coexistence_activated", 0)
            self.decisions_made = state.get("decisions_made", 0)
            self.executions_succeeded = state.get("executions_succeeded", 0)
            self.executions_failed = state.get("executions_failed", 0)

            # Restore decision history (limited to last 100)
            for d in state.get("recent_decisions", []):
                try:
                    phase = LifePhase[d["phase"]]
                except (KeyError, ValueError):
                    phase = LifePhase.EMERGENCE
                self.decision_history.append(
                    LifeDecision(
                        decision_id=d["decision_id"],
                        timestamp=datetime.fromisoformat(d["timestamp"]),
                        phase=phase,
                        triggered_by=d["triggered_by"],
                        decision_type=d["decision_type"],
                        rationale=d["rationale"],
                        expected_outcome={},
                        confidence=d["confidence"],
                    )
                )

            # Re-inject behavior executor type stats by replaying synthetic executions
            for dt, stats in state.get("behavior_executor_type_stats", {}).items():
                s = int(stats.get("success", 0))
                f = int(stats.get("fail", 0))
                if hasattr(self._behavior_executor, "_type_success"):
                    self._behavior_executor._type_success[dt] = s
                if hasattr(self._behavior_executor, "_type_fail"):
                    self._behavior_executor._type_fail[dt] = f

            logger.info(
                f"[AutonomousLifeCycle] Loaded state from {path}: "
                f"{self.decisions_made} decisions, "
                f"{self.executions_succeeded + self.executions_failed} executions"
            )
        except Exception as e:
            logger.warning(f"[AutonomousLifeCycle] Failed to load state: {e}")


# Example usage
if __name__ == "__main__":

    async def demo() -> None:
        """Run a demonstration."""
        lifecycle = AutonomousLifeCycle()
        await lifecycle.initialize()

        logger.info("=" * 70)
        logger.info("Angela AI v6.0 - 自主生命周期演示")
        logger.info("Autonomous Life Cycle Demo")
        logger.info("=" * 70)

        logger.info("\n初始化公式系统 / Initializing formula systems:")
        logger.info("  - HSM (热力学式自发元认知)")
        logger.info("  - CDM (认知配息模型)")
        logger.info("  - L_s (生命感强度公式)")
        logger.info("  - A_c (主动认知构建公式)")
        logger.info("  - NPE (非偏执存在)")

        # Register observer
        lifecycle.register_observer("demo_user", relationship_depth=0.7)
        lifecycle.update_observer_interaction("demo_user", intensity=0.8)
        logger.info("\n注册观察者 / Registered observer: demo_user")

        # Detect cognitive gaps
        logger.info("\n检测认知缺口 / Detecting cognitive gaps:")
        lifecycle.hsm.detect_cognitive_gap("emotional_depth", 0.8, 0.6)
        lifecycle.hsm.detect_cognitive_gap("creative_expression", 0.7, 0.5)
        lifecycle.hsm.detect_cognitive_gap("social_intelligence", 0.6, 0.4)
        logger.info("  检测到3个认知缺口 / Detected 3 cognitive gaps")

        # Get initial metrics
        metrics = lifecycle.get_current_metrics()
        logger.info("\n初始指标 / Initial metrics:")
        logger.info(f"  HSM: {metrics.hsm_value:.4f}")
        logger.info(f"  C_Gap: {metrics.c_gap:.4f}")
        logger.info(f"  生命感强度: {metrics.life_intensity:.4f}")
        logger.info(f"  主动认知A_c: {metrics.a_c:.4f}")

        # Make manual decisions
        logger.info("\n执行生命决策 / Executing life decisions:")
        for i in range(3):
            decision = await lifecycle.make_life_decision()
            if decision:
                logger.info(f"\n  决策 {i+1}: {decision.decision_type}")
                logger.info(f"    触发器: {decision.triggered_by}")
                logger.info(f"    置信度: {decision.confidence:.2%}")
                logger.info(f"    推理: {decision.rationale[:60]}...")

        # Record cognitive investments
        logger.info("\n记录认知投入 / Recording cognitive investments:")
        investment = lifecycle.record_cognitive_investment(
            activity_type=CognitiveActivity.CREATING,
            duration_seconds=600,
            intensity=0.8,
            context={"activity": "demo_creation"},
        )
        if investment:
            logger.info(f"  投入: {investment.activity_type.name}")
            logger.info(f"  资源消耗: {investment.resource_consumed:.1f}")

        # Get summary
        logger.info("\n生命周期摘要 / Life cycle summary:")
        summary = lifecycle.get_lifecycle_summary()
        logger.info(f"  当前阶段: {summary['current_phase']['cn_name']}")
        logger.info(f"  决策次数: {summary['statistics']['decisions_made']}")
        logger.info(f"  探索次数: {summary['statistics']['explorations_triggered']}")
        logger.info(f"  共存激活: {summary['statistics']['coexistence_activated']}")

        await lifecycle.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")

    asyncio.run(demo())
