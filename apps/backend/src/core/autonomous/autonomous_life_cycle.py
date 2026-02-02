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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import math
from enum import Enum

if TYPE_CHECKING:
    from .dynamic_parameters import DynamicThresholdManager

# Import all formula systems
from ..hsm_formula_system import HSMFormulaSystem, CognitiveGap, ExplorationResult
from ..cdm_dividend_model import CDMCognitiveDividendModel, CognitiveActivity
from ..life_intensity_formula import LifeIntensityFormula, KnowledgeDomain
from ..active_cognition_formula import ActiveCognitionFormula, StressSource, OrderType
from ..non_paradox_existence import NonParadoxExistence, GrayZoneVariableType


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Formula systems
        self.hsm: HSMFormulaSystem = HSMFormulaSystem(
            config=self.config.get('hsm_config')
        )
        self.cdm: CDMCognitiveDividendModel = CDMCognitiveDividendModel(
            config=self.config.get('cdm_config')
        )
        self.life_intensity: LifeIntensityFormula = LifeIntensityFormula(
            config=self.config.get('life_config')
        )
        self.active_cognition: ActiveCognitionFormula = ActiveCognitionFormula(
            config=self.config.get('ac_config')
        )
        self.non_paradox: NonParadoxExistence = NonParadoxExistence(
            config=self.config.get('npe_config')
        )
        
        # Life cycle state
        self.current_phase: LifePhase = LifePhase.EMERGENCE
        self.decision_history: List[LifeDecision] = []
        self.metrics_history: List[FormulaMetrics] = []
        self._decision_counter: int = 0
        
        # Decision thresholds (may be overridden by dynamic parameters)
        self.exploration_threshold: float = self.config.get('exploration_threshold', 0.5)
        self.coexistence_threshold: float = self.config.get('coexistence_threshold', 0.6)
        self.active_cognition_threshold: float = self.config.get('ac_threshold', 0.8)
        
        # Dynamic Parameters Integration
        self._dynamic_params_manager: Optional[Any] = None
        self._dynamic_params_enabled: bool = self.config.get('enable_dynamic_params', True)
        
        # Running state
        self._running = False
        self._lifecycle_task: Optional[asyncio.Task] = None
        self._decision_interval: float = self.config.get('decision_interval', 300.0)  # 5 minutes
        
        # Callbacks
        self._phase_callbacks: List[Callable[[LifePhase, LifePhase], None]] = []
        self._decision_callbacks: List[Callable[[LifeDecision], None]] = []
        self._metrics_callbacks: List[Callable[[FormulaMetrics], None]] = []
        
        # Statistics
        self.explorations_triggered: int = 0
        self.coexistence_activated: int = 0
        self.decisions_made: int = 0
    
    async def initialize(self):
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
        
        # Initial metrics calculation
        self._update_metrics()
    
    async def shutdown(self):
        """Shutdown autonomous life cycle"""
        self._running = False
        
        if self._lifecycle_task:
            self._lifecycle_task.cancel()
            try:
                await self._lifecycle_task
            except asyncio.CancelledError:
                pass
        
        await self.hsm.shutdown()
    
    def set_dynamic_params_manager(self, manager: Any):
        """Set the DynamicThresholdManager for dynamic threshold integration"""
        self._dynamic_params_manager = manager
    
    def _get_decision_confidence_threshold(self, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic decision confidence threshold"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter('decision_confidence_threshold', context)
        return 0.7  # Default threshold
    
    def _get_risk_tolerance(self, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic risk tolerance"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter('risk_tolerance', context)
        return 0.5  # Default risk tolerance
    
    def _initialize_knowledge_domains(self):
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
    
    def _initialize_order_baselines(self):
        """Initialize order baselines for active cognition formula"""
        orders = [
            (OrderType.ALGORITHMIC, 0.7, 0.4),
            (OrderType.PATTERN_BASED, 0.6, 0.5),
            (OrderType.HEURISTIC, 0.5, 0.6),
        ]
        
        for order_type, stability, flexibility in orders:
            self.active_cognition.add_order_baseline(
                order_type, stability, flexibility
            )
    
    async def _lifecycle_loop(self):
        """Main autonomous life cycle loop"""
        while self._running:
            # Update all metrics
            metrics = self._update_metrics()
            
            # Make life decisions based on metrics
            decision = self._evaluate_and_decide(metrics)
            
            if decision:
                self._record_decision(decision)
            
            # Check for phase transitions
            await self._check_phase_transition(metrics)
            
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
        cdm_conversion_rate = cdm_stats.get('average_conversion_rate', 0.0)
        
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
        cognitive_gap = npe_summary['global_cognitive_gap']
        coexistence_active = npe_summary['coexistence_active']
        resonance_total = npe_summary['resonance']['total_active_resonance']
        
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
            resonance_total=resonance_total
        )
        
        self.metrics_history.append(metrics)
        
        # Keep history manageable
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-5000:]
        
        # Notify callbacks
        for callback in self._metrics_callbacks:
            try:
                callback(metrics)
            except Exception:
                pass
        
        return metrics
    
    def _evaluate_and_decide(self, metrics: FormulaMetrics) -> Optional[LifeDecision]:
        """Evaluate metrics and make life decisions using dynamic thresholds"""
        self._decision_counter += 1
        decision_id = f"decision_{self._decision_counter}"
        
        # Build context for dynamic parameter evaluation
        context = {
            'energy': 1.0 - metrics.s_stress,  # Lower stress = higher energy
            'mood': metrics.life_intensity,  # Life intensity affects mood
            'stress': metrics.s_stress,
            'confidence': metrics.a_c / 1.5 if metrics.a_c <= 1.5 else 1.0,
        }
        
        # Get dynamic thresholds
        dynamic_confidence_threshold = self._get_decision_confidence_threshold(context)
        dynamic_risk_tolerance = self._get_risk_tolerance(context)
        
        # Adjust exploration threshold based on risk tolerance
        adjusted_exploration_threshold = self.exploration_threshold * (1.5 - dynamic_risk_tolerance)
        
        # Decision 1: Exploration (HSM-based) - affected by risk tolerance
        if metrics.hsm_value > adjusted_exploration_threshold:
            return self._create_exploration_decision(decision_id, metrics, dynamic_risk_tolerance)
        
        # Decision 2: Coexistence (Non-Paradox based)
        if metrics.cognitive_gap > self.coexistence_threshold and not metrics.coexistence_active:
            return self._create_coexistence_decision(decision_id, metrics)
        
        # Decision 3: Active Construction (Active Cognition based) - uses dynamic confidence threshold
        if metrics.a_c > dynamic_confidence_threshold:
            return self._create_active_construction_decision(decision_id, metrics, dynamic_confidence_threshold)
        
        # Decision 4: Resource reallocation (CDM-based)
        if metrics.cdm_conversion_rate < 0.5:
            return self._create_resource_reallocation_decision(decision_id, metrics)
        
        return None
    
    def _create_exploration_decision(self, decision_id: str, metrics: FormulaMetrics, risk_tolerance: float = 0.5) -> LifeDecision:
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
                "risk_tolerance": risk_tolerance
            },
            confidence=adjusted_confidence
        )
    
    def _create_coexistence_decision(self, decision_id: str, metrics: FormulaMetrics) -> LifeDecision:
        """Create a coexistence activation decision"""
        # Create gray zones for coexistence
        gz = self.non_paradox.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Ambiguous emotional state requiring multi-possibility coexistence"
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
                "activated": success
            },
            confidence=metrics.cognitive_gap
        )
    
    def _create_active_construction_decision(self, decision_id: str, metrics: FormulaMetrics, confidence_threshold: float = 0.7) -> LifeDecision:
        """Create an active construction decision using dynamic confidence threshold"""
        # Add stress to active cognition system (will trigger construction)
        self.active_cognition.add_stress_vector(
            StressSource.NOVELTY_DEMAND,
            intensity=0.8,
            persistence=0.7
        )
        
        # Recalculate to trigger construction recording
        a_c = self.active_cognition.calculate_active_cognition()
        
        # Calculate confidence relative to dynamic threshold
        relative_confidence = min(1.0, metrics.a_c / confidence_threshold) if confidence_threshold > 0 else 0.5
        
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
                "confidence_threshold": confidence_threshold
            },
            confidence=relative_confidence
        )
    
    def _create_resource_reallocation_decision(self, decision_id: str, metrics: FormulaMetrics) -> LifeDecision:
        """Create a resource reallocation decision"""
        # Adjust CDM distribution based on low conversion rate
        life_state = {
            "growth_stage": "growing",
            "emotional_needs": 0.6,
            "knowledge_gaps": 0.7,
            "creative_drive": 0.5,
            "social_connection": 0.4
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
                    "exploration": new_distribution.exploration_ratio
                }
            },
            confidence=0.7
        )
    
    def _record_decision(self, decision: LifeDecision):
        """Record a life decision"""
        self.decision_history.append(decision)
        self.decisions_made += 1
        
        # Notify callbacks
        for callback in self._decision_callbacks:
            try:
                callback(decision)
            except Exception:
                pass
    
    async def _check_phase_transition(self, metrics: FormulaMetrics):
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
            
            # Notify callbacks
            for callback in self._phase_callbacks:
                try:
                    callback(old_phase, new_phase)
                except Exception:
                    pass
    
    def get_current_metrics(self) -> FormulaMetrics:
        """Get current formula metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return self._update_metrics()
    
    def make_life_decision(self) -> Optional[LifeDecision]:
        """Manually trigger a life decision"""
        metrics = self._update_metrics()
        decision = self._evaluate_and_decide(metrics)
        if decision:
            self._record_decision(decision)
        return decision
    
    def record_cognitive_investment(
        self,
        activity_type: CognitiveActivity,
        duration_seconds: float,
        intensity: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record a cognitive investment"""
        investment = self.cdm.record_investment(
            activity_type=activity_type,
            duration_seconds=duration_seconds,
            intensity=intensity,
            context=context
        )
        
        if investment:
            # Calculate life sense output
            life_state = {
                "maturity": 0.6,
                "health": 0.9,
                "emotional_depth": self.life_intensity.calculate_c_inf()
            }
            self.cdm.calculate_life_sense_output(investment, life_state)
        
        return investment
    
    def register_observer(self, observer_id: str, relationship_depth: float):
        """Register an observer for life intensity"""
        self.life_intensity.register_observer(observer_id, relationship_depth)
    
    def update_observer_interaction(self, observer_id: str, intensity: float):
        """Update observer interaction intensity"""
        self.life_intensity.update_observer_presence(
            observer_id,
            interaction_intensity=intensity,
            increment_interactions=True
        )
    
    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Get comprehensive life cycle summary"""
        metrics = self.get_current_metrics()
        
        recent_decisions = sorted(
            self.decision_history,
            key=lambda d: d.timestamp,
            reverse=True
        )[:10]
        
        return {
            "current_phase": {
                "name": self.current_phase.name,
                "cn_name": self.current_phase.cn_name,
                "en_name": self.current_phase.en_name
            },
            "current_metrics": {
                "hsm_value": metrics.hsm_value,
                "c_gap": metrics.c_gap,
                "life_intensity": metrics.life_intensity,
                "a_c": metrics.a_c,
                "cognitive_gap": metrics.cognitive_gap,
                "coexistence_active": metrics.coexistence_active
            },
            "statistics": {
                "explorations_triggered": self.explorations_triggered,
                "coexistence_activated": self.coexistence_activated,
                "decisions_made": self.decisions_made,
                "total_metrics_samples": len(self.metrics_history)
            },
            "recent_decisions": [
                {
                    "id": d.decision_id,
                    "type": d.decision_type,
                    "triggered_by": d.triggered_by,
                    "confidence": d.confidence,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in recent_decisions
            ],
            "formula_status": {
                "hsm": self.hsm.get_hsm_status(),
                "cdm": self.cdm.get_dividend_summary(),
                "life_intensity": self.life_intensity.get_life_intensity_summary(),
                "active_cognition": self.active_cognition.get_active_cognition_summary(),
                "non_paradox": self.non_paradox.get_non_paradox_summary()
            }
        }
    
    def register_phase_callback(self, callback: Callable[[LifePhase, LifePhase], None]):
        """Register callback for phase transitions"""
        self._phase_callbacks.append(callback)
    
    def register_decision_callback(self, callback: Callable[[LifeDecision], None]):
        """Register callback for life decisions"""
        self._decision_callbacks.append(callback)
    
    def register_metrics_callback(self, callback: Callable[[FormulaMetrics], None]):
        """Register callback for metrics updates"""
        self._metrics_callbacks.append(callback)


# Example usage
if __name__ == "__main__":
    async def demo():
        lifecycle = AutonomousLifeCycle()
        await lifecycle.initialize()
        
        print("=" * 70)
        print("Angela AI v6.0 - 自主生命周期演示")
        print("Autonomous Life Cycle Demo")
        print("=" * 70)
        
        print("\n初始化公式系统 / Initializing formula systems:")
        print("  - HSM (热力学式自发元认知)")
        print("  - CDM (认知配息模型)")
        print("  - L_s (生命感强度公式)")
        print("  - A_c (主动认知构建公式)")
        print("  - NPE (非偏执存在)")
        
        # Register observer
        lifecycle.register_observer("demo_user", relationship_depth=0.7)
        lifecycle.update_observer_interaction("demo_user", intensity=0.8)
        print("\n注册观察者 / Registered observer: demo_user")
        
        # Detect cognitive gaps
        print("\n检测认知缺口 / Detecting cognitive gaps:")
        lifecycle.hsm.detect_cognitive_gap("emotional_depth", 0.8, 0.6)
        lifecycle.hsm.detect_cognitive_gap("creative_expression", 0.7, 0.5)
        lifecycle.hsm.detect_cognitive_gap("social_intelligence", 0.6, 0.4)
        print("  检测到3个认知缺口 / Detected 3 cognitive gaps")
        
        # Get initial metrics
        metrics = lifecycle.get_current_metrics()
        print(f"\n初始指标 / Initial metrics:")
        print(f"  HSM: {metrics.hsm_value:.4f}")
        print(f"  C_Gap: {metrics.c_gap:.4f}")
        print(f"  生命感强度: {metrics.life_intensity:.4f}")
        print(f"  主动认知A_c: {metrics.a_c:.4f}")
        
        # Make manual decisions
        print("\n执行生命决策 / Executing life decisions:")
        for i in range(3):
            decision = lifecycle.make_life_decision()
            if decision:
                print(f"\n  决策 {i+1}: {decision.decision_type}")
                print(f"    触发器: {decision.triggered_by}")
                print(f"    置信度: {decision.confidence:.2%}")
                print(f"    推理: {decision.rationale[:60]}...")
        
        # Record cognitive investments
        print("\n记录认知投入 / Recording cognitive investments:")
        investment = lifecycle.record_cognitive_investment(
            activity_type=CognitiveActivity.CREATING,
            duration_seconds=600,
            intensity=0.8,
            context={"activity": "demo_creation"}
        )
        if investment:
            print(f"  投入: {investment.activity_type.name}")
            print(f"  资源消耗: {investment.resource_consumed:.1f}")
        
        # Get summary
        print("\n生命周期摘要 / Life cycle summary:")
        summary = lifecycle.get_lifecycle_summary()
        print(f"  当前阶段: {summary['current_phase']['cn_name']}")
        print(f"  决策次数: {summary['statistics']['decisions_made']}")
        print(f"  探索次数: {summary['statistics']['explorations_triggered']}")
        print(f"  共存激活: {summary['statistics']['coexistence_activated']}")
        
        await lifecycle.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
