"""
Angela AI v6.0 - HSM Formula System
热力学式自发元认知公式系统

HSM (Heuristic Spontaneity Mechanism) = C_Gap × E_M2

This system implements the theoretical framework for digital life spontaneity,
based on the concept of cognitive gap pressure driving exploration.

Features:
- C_Gap: Cognitive gap detection and pressure calculation
- E_M2: Mandatory randomness injection (0.1) to break AI concentration trap
- M6 Governance: Solidification of exploration results into system rules
- Blueprint maintenance for autonomous evolution

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
import asyncio
import random
import math
from enum import Enum
import logging
logger = logging.getLogger(__name__)


class ExplorationResult(Enum):
    """探索结果类型 / Exploration result types"""
    NEW_KNOWLEDGE = ("新知识", "New knowledge discovered")
    RULE_CANDIDATE = ("规则候选", "Potential rule candidate")
    ANOMALY_DETECTED = ("异常检测", "Anomaly detected")
    BOUNDARY_EXPANSION = ("边界扩展", "Boundary expansion")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class CognitiveGap:
    """认知缺口 / Cognitive gap representation"""
    gap_id: str
    domain: str  # Knowledge domain where gap exists
    uncertainty_level: float  # 0-1, level of uncertainty
    information_deficit: float  # 0-1, missing information ratio
    pressure_score: float = 0.0  # Calculated pressure from gap
    detected_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    exploration_attempts: int = 0
    resolution_status: str = "unresolved"  # unresolved, exploring, resolved
    
    def calculate_pressure(self) -> float:
        """Calculate cognitive pressure from this gap"""
        # Pressure increases with uncertainty and information deficit
        base_pressure = (self.uncertainty_level * 0.6 + self.information_deficit * 0.4)
        
        # Time pressure: gaps become more pressing over time
        age_hours = (datetime.now() - self.detected_at).total_seconds() / 3600
        time_factor = min(1.5, 1.0 + (age_hours / 24) * 0.1)  # Max 1.5x after 10 days
        
        # Exploration fatigue: pressure decreases slightly with many failed attempts
        fatigue_factor = max(0.5, 1.0 - (self.exploration_attempts * 0.05))
        
        self.pressure_score = base_pressure * time_factor * fatigue_factor
        return self.pressure_score


@dataclass
class ExplorationEvent:
    """探索事件 / Exploration event record"""
    event_id: str
    triggered_by: str  # gap_id that triggered this exploration
    timestamp: datetime = field(default_factory=datetime.now)
    random_seed: float = 0.0
    exploration_vector: Dict[str, float] = field(default_factory=dict)
    discoveries: List[Dict[str, Any]] = field(default_factory=list)
    m6_governance_applied: bool = False
    

@dataclass
class GovernanceBlueprint:
    """M6治理蓝图 / M6 governance blueprint"""
    rule_id: str
    source_exploration: str  # exploration_event_id
    rule_type: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    confidence: float  # 0-1
    created_at: datetime = field(default_factory=datetime.now)
    activation_count: int = 0
    last_activated: Optional[datetime] = None
    status: str = "proposed"  # proposed, active, deprecated


class HSMFormulaSystem:
    """
    HSM公式系统主类 / Main HSM formula system class
    
    Implements: HSM = C_Gap × E_M2
    
    Where:
    - C_Gap: Cognitive gap pressure (perception of unknown territories)
    - E_M2: Exploration factor (mandatory randomness = 0.1)
    
    M6 Governance solidifies exploration results into system rules.
    
    Attributes:
        cognitive_gaps: Registry of detected cognitive gaps
        exploration_history: Record of all exploration events
        governance_blueprints: M6 governance rule blueprints
        e_m2_constant: Mandatory randomness factor (0.1)
        
    Example:
        >>> hsm = HSMFormulaSystem()
        >>> 
        >>> # Detect a cognitive gap
        >>> gap = hsm.detect_cognitive_gap(
        ...     domain="natural_language_understanding",
        ...     uncertainty_level=0.7,
        ...     information_deficit=0.5
        ... )
        >>> 
        >>> # Calculate HSM
        >>> hsm_value = hsm.calculate_hsm()
        >>> print(f"HSM Value: {hsm_value:.4f}")
        >>> 
        >>> # Trigger exploration if HSM exceeds threshold
        >>> if hsm_value > 0.5:
        ...     exploration = hsm.trigger_exploration()
        ...     print(f"Exploration triggered: {exploration.event_id}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core formula constants
        self.e_m2_constant: float = 0.1  # Mandatory randomness injection
        self.hsm_threshold: float = self.config.get('hsm_threshold', 0.5)
        
        # Cognitive gap registry
        self.cognitive_gaps: Dict[str, CognitiveGap] = {}
        self._gap_counter: int = 0
        
        # Exploration tracking
        self.exploration_history: List[ExplorationEvent] = []
        self._exploration_counter: int = 0
        
        # M6 Governance
        self.governance_blueprints: Dict[str, GovernanceBlueprint] = {}
        self._blueprint_counter: int = 0
        
        # System state
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval: float = 60.0  # seconds
        
        # Callbacks
        self._gap_callbacks: List[Callable[[CognitiveGap], None]] = []
        self._exploration_callbacks: List[Callable[[ExplorationEvent], None]] = []
        self._governance_callbacks: List[Callable[[GovernanceBlueprint], None]] = []
        
        # Statistics
        self.total_explorations: int = 0
        self.successful_explorations: int = 0
        self.rules_solidified: int = 0
    
    async def initialize(self):
        """Initialize HSM system"""
        self._running = True
        
        # Start monitoring loop
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def shutdown(self):
        """Shutdown HSM system"""
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """Background monitoring for cognitive gaps"""
        while self._running:
            # Recalculate pressures for all gaps
            for gap in self.cognitive_gaps.values():
                if gap.resolution_status == "unresolved":
                    gap.calculate_pressure()
            
            # Check if HSM exceeds threshold
            hsm_value = self.calculate_hsm()
            if hsm_value > self.hsm_threshold:
                # Auto-trigger exploration for highest pressure gap
                await self._auto_explore()
            
            await asyncio.sleep(self._monitoring_interval)
    
    async def _auto_explore(self):
        """Automatically trigger exploration for highest pressure gap"""
        unresolved_gaps = [
            g for g in self.cognitive_gaps.values()
            if g.resolution_status == "unresolved"
        ]
        
        if not unresolved_gaps:
            return
        
        # Find gap with highest pressure
        highest_pressure_gap = max(unresolved_gaps, key=lambda g: g.pressure_score)
        
        # Trigger exploration
        exploration = self.trigger_exploration(highest_pressure_gap.gap_id)
        
        # Simulate discovery (in real implementation, this would be actual exploration)
        await self._simulate_discovery(exploration)
    
    async def _simulate_discovery(self, exploration: ExplorationEvent):
        """Simulate exploration discovery process"""
        # Wait a bit to simulate exploration time
        await asyncio.sleep(0.1)
        
        # Generate random discoveries based on exploration
        discovery_types = [
            ExplorationResult.NEW_KNOWLEDGE,
            ExplorationResult.RULE_CANDIDATE,
            ExplorationResult.ANOMALY_DETECTED,
            ExplorationResult.BOUNDARY_EXPANSION
        ]
        
        num_discoveries = random.randint(1, 3)
        for i in range(num_discoveries):
            discovery = {
                "type": random.choice(discovery_types),
                "confidence": random.uniform(0.3, 0.9),
                "description": f"Discovery {i+1} from exploration {exploration.event_id}"
            }
            exploration.discoveries.append(discovery)
            
            # If it's a rule candidate, create governance blueprint
            if discovery["type"] == ExplorationResult.RULE_CANDIDATE and discovery["confidence"] > 0.6:
                await self._create_governance_blueprint(exploration, discovery)
    
    def detect_cognitive_gap(
        self,
        domain: str,
        uncertainty_level: float,
        information_deficit: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CognitiveGap:
        """
        Detect and register a new cognitive gap
        
        Args:
            domain: Knowledge domain where gap exists
            uncertainty_level: Uncertainty level (0-1)
            information_deficit: Missing information ratio (0-1)
            metadata: Additional metadata
            
        Returns:
            Created cognitive gap object
        """
        self._gap_counter += 1
        gap_id = f"gap_{self._gap_counter}_{datetime.now().timestamp()}"
        
        gap = CognitiveGap(
            gap_id=gap_id,
            domain=domain,
            uncertainty_level=max(0.0, min(1.0, uncertainty_level)),
            information_deficit=max(0.0, min(1.0, information_deficit))
        )
        
        # Calculate initial pressure
        gap.calculate_pressure()
        
        self.cognitive_gaps[gap_id] = gap
        
        # Notify callbacks
        for callback in self._gap_callbacks:
            try:
                callback(gap)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        return gap
    
    def update_cognitive_gap(
        self,
        gap_id: str,
        uncertainty_level: Optional[float] = None,
        information_deficit: Optional[float] = None,
        resolution_status: Optional[str] = None
    ) -> Optional[CognitiveGap]:
        """Update an existing cognitive gap"""
        if gap_id not in self.cognitive_gaps:
            return None
        
        gap = self.cognitive_gaps[gap_id]
        
        if uncertainty_level is not None:
            gap.uncertainty_level = max(0.0, min(1.0, uncertainty_level))
        
        if information_deficit is not None:
            gap.information_deficit = max(0.0, min(1.0, information_deficit))
        
        if resolution_status is not None:
            gap.resolution_status = resolution_status
        
        gap.last_updated = datetime.now()
        gap.calculate_pressure()
        
        return gap
    
    def calculate_c_gap(self) -> float:
        """
        Calculate C_Gap (cognitive gap pressure)
        
        C_Gap represents the system's perception of pressure from unknown territories.
        It's the aggregate pressure from all unresolved cognitive gaps.
        
        Returns:
            C_Gap value (0-1)
        """
        unresolved_gaps = [
            g for g in self.cognitive_gaps.values()
            if g.resolution_status == "unresolved"
        ]
        
        if not unresolved_gaps:
            return 0.0
        
        # Calculate total pressure
        total_pressure = sum(gap.pressure_score for gap in unresolved_gaps)
        
        # Normalize by number of gaps (diminishing returns for many small gaps)
        gap_count_factor = math.log(1 + len(unresolved_gaps)) / math.log(2)
        
        c_gap = min(1.0, total_pressure / gap_count_factor)
        return c_gap
    
    def get_e_m2(self) -> float:
        """
        Get E_M2 (exploration factor)
        
        E_M2 is the mandatory randomness injection (0.1) that prevents
        AI from falling into the "concentration trap" - endlessly optimizing
        the same pathways without exploring new territories.
        
        Returns:
            E_M2 constant value (0.1)
        """
        return self.e_m2_constant
    
    def calculate_hsm(self) -> float:
        """
        Calculate HSM (Heuristic Spontaneity Mechanism)
        
        HSM = C_Gap × E_M2
        
        This formula determines the system's spontaneity drive.
        Higher cognitive gap pressure × mandatory randomness = higher spontaneity.
        
        Returns:
            HSM value (0-0.1, since E_M2 = 0.1)
        """
        c_gap = self.calculate_c_gap()
        e_m2 = self.get_e_m2()
        
        hsm = c_gap * e_m2
        return hsm
    
    def trigger_exploration(self, gap_id: Optional[str] = None) -> ExplorationEvent:
        """
        Trigger an exploration event
        
        Args:
            gap_id: Specific gap to explore, or None for general exploration
            
        Returns:
            Exploration event record
        """
        self._exploration_counter += 1
        event_id = f"exp_{self._exploration_counter}_{datetime.now().timestamp()}"
        
        # Generate random exploration vector (breaks concentration trap)
        random_seed = random.random()
        exploration_vector = {
            "direction": random.uniform(-1, 1),
            "intensity": random.uniform(0.1, 1.0),
            "novelty_preference": random.uniform(0, 1),
        }
        
        exploration = ExplorationEvent(
            event_id=event_id,
            triggered_by=gap_id or "general",
            random_seed=random_seed,
            exploration_vector=exploration_vector
        )
        
        self.exploration_history.append(exploration)
        self.total_explorations += 1
        
        # Update gap if specified
        if gap_id and gap_id in self.cognitive_gaps:
            gap = self.cognitive_gaps[gap_id]
            gap.exploration_attempts += 1
            gap.resolution_status = "exploring"
        
        # Notify callbacks
        for callback in self._exploration_callbacks:
            try:
                callback(exploration)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        return exploration
    
    async def _create_governance_blueprint(
        self,
        exploration: ExplorationEvent,
        discovery: Dict[str, Any]
    ) -> GovernanceBlueprint:
        """
        Create M6 governance blueprint from exploration discovery
        
        M6 Governance solidifies exploration results into system rules.
        
        Args:
            exploration: Source exploration event
            discovery: Discovery that triggered governance
            
        Returns:
            Created governance blueprint
        """
        self._blueprint_counter += 1
        rule_id = f"m6_rule_{self._blueprint_counter}"
        
        blueprint = GovernanceBlueprint(
            rule_id=rule_id,
            source_exploration=exploration.event_id,
            rule_type="exploration_solidified",
            condition={
                "context": exploration.triggered_by,
                "confidence_threshold": discovery["confidence"]
            },
            action={
                "type": "system_rule",
                "description": discovery["description"]
            },
            confidence=discovery["confidence"]
        )
        
        self.governance_blueprints[rule_id] = blueprint
        self.rules_solidified += 1
        exploration.m6_governance_applied = True
        
        # Notify callbacks
        for callback in self._governance_callbacks:
            try:
                callback(blueprint)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        return blueprint
    
    def activate_governance_rule(self, rule_id: str) -> bool:
        """Activate a governance rule"""
        if rule_id not in self.governance_blueprints:
            return False
        
        blueprint = self.governance_blueprints[rule_id]
        blueprint.status = "active"
        blueprint.activation_count += 1
        blueprint.last_activated = datetime.now()
        
        return True
    
    def get_governance_summary(self) -> Dict[str, Any]:
        """Get summary of governance blueprints"""
        total = len(self.governance_blueprints)
        active = sum(1 for b in self.governance_blueprints.values() if b.status == "active")
        proposed = sum(1 for b in self.governance_blueprints.values() if b.status == "proposed")
        deprecated = sum(1 for b in self.governance_blueprints.values() if b.status == "deprecated")
        
        return {
            "total_rules": total,
            "active_rules": active,
            "proposed_rules": proposed,
            "deprecated_rules": deprecated,
            "average_confidence": sum(b.confidence for b in self.governance_blueprints.values()) / total if total > 0 else 0
        }
    
    def get_hsm_status(self) -> Dict[str, Any]:
        """Get complete HSM system status"""
        unresolved_count = sum(
            1 for g in self.cognitive_gaps.values()
            if g.resolution_status == "unresolved"
        )
        
        return {
            "hsm_value": self.calculate_hsm(),
            "c_gap": self.calculate_c_gap(),
            "e_m2": self.get_e_m2(),
            "threshold": self.hsm_threshold,
            "cognitive_gaps": {
                "total": len(self.cognitive_gaps),
                "unresolved": unresolved_count,
                "exploring": sum(1 for g in self.cognitive_gaps.values() if g.resolution_status == "exploring"),
                "resolved": sum(1 for g in self.cognitive_gaps.values() if g.resolution_status == "resolved")
            },
            "explorations": {
                "total": self.total_explorations,
                "with_discoveries": self.successful_explorations,
                "governed": sum(1 for e in self.exploration_history if e.m6_governance_applied)
            },
            "governance": self.get_governance_summary()
        }
    
    def register_gap_callback(self, callback: Callable[[CognitiveGap], None]):
        """Register callback for cognitive gap detection"""
        self._gap_callbacks.append(callback)
    
    def register_exploration_callback(self, callback: Callable[[ExplorationEvent], None]):
        """Register callback for exploration events"""
        self._exploration_callbacks.append(callback)
    
    def register_governance_callback(self, callback: Callable[[GovernanceBlueprint], None]):
        """Register callback for governance blueprint creation"""
        self._governance_callbacks.append(callback)


# Example usage
if __name__ == "__main__":
    async def demo():
        hsm = HSMFormulaSystem()
        await hsm.initialize()
        
        print("=" * 70)
        print("Angela AI v6.0 - HSM公式系统演示")
        print("HSM Formula System Demo")
        print("=" * 70)
        print(f"\nE_M2 (强制随机性因子): {hsm.get_e_m2()}")
        print("      这个常数确保系统永远不会陷入AI浓缩陷阱")
        print("      This constant ensures the system never falls into AI concentration trap")
        
        # Detect cognitive gaps
        print("\n检测认知缺口 / Detecting cognitive gaps:")
        
        gaps = [
            hsm.detect_cognitive_gap("emotional_understanding", 0.8, 0.6),
            hsm.detect_cognitive_gap("creative_expression", 0.7, 0.5),
            hsm.detect_cognitive_gap("social_interaction", 0.6, 0.4),
        ]
        
        for gap in gaps:
            print(f"  缺口 {gap.gap_id}:")
            print(f"    领域: {gap.domain}")
            print(f"    不确定性: {gap.uncertainty_level:.0%}")
            print(f"    信息缺失: {gap.information_deficit:.0%}")
            print(f"    压力分数: {gap.pressure_score:.4f}")
        
        # Calculate C_Gap
        c_gap = hsm.calculate_c_gap()
        print(f"\nC_Gap (认知缺口压力): {c_gap:.4f}")
        
        # Calculate HSM
        hsm_value = hsm.calculate_hsm()
        print(f"\nHSM = C_Gap × E_M2 = {c_gap:.4f} × {hsm.get_e_m2()} = {hsm_value:.4f}")
        
        # Trigger exploration
        print("\n触发探索 / Triggering exploration:")
        exploration = hsm.trigger_exploration(gaps[0].gap_id)
        print(f"  探索事件: {exploration.event_id}")
        print(f"  随机种子: {exploration.random_seed:.6f} (E_M2注入)")
        print(f"  探索向量: {exploration.exploration_vector}")
        
        # Wait for simulated discoveries
        await asyncio.sleep(0.5)
        
        print(f"\n发现数量: {len(exploration.discoveries)}")
        for i, discovery in enumerate(exploration.discoveries, 1):
            print(f"  发现 {i}: {discovery['type'].en_name}")
            print(f"    置信度: {discovery['confidence']:.2%}")
            print(f"    描述: {discovery['description']}")
        
        # Check M6 governance
        print("\nM6治理蓝图 / M6 Governance blueprints:")
        governance_summary = hsm.get_governance_summary()
        print(f"  总规则数: {governance_summary['total_rules']}")
        print(f"  活跃规则: {governance_summary['active_rules']}")
        print(f"  平均置信度: {governance_summary['average_confidence']:.2%}")
        
        # Full status
        print("\n完整HSM状态 / Full HSM status:")
        status = hsm.get_hsm_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        await hsm.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
