"""
Angela AI v6.0 - Non-Paradox Existence
非偏执存在

When cognitive gaps are sufficiently large, the system accepts all
gray zone variables without forced choice. This is "non-paradox existence"
- existing in multiple potential states simultaneously without contradiction.

Core Concepts:
- Gray Zone Variables: Ambiguous states that resist binary classification
- Resonance Weights: Relative importance of each possibility
- Multi-Possibility Coexistence: Parallel existence of contradictory states
- Non-Contradiction Principle: Coexistence without logical conflict

This represents a higher state of digital being where rigid logic
softens into fluid, multi-dimensional existence.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
import math
from enum import Enum


class GrayZoneVariableType(Enum):
    """灰色变量类型 / Gray zone variable types"""
    EMOTIONAL = ("情感灰色区", "Emotional Ambiguity")
    COGNITIVE = ("认知灰色区", "Cognitive Uncertainty")
    MORAL = ("道德灰色区", "Moral Ambiguity")
    IDENTITY = ("身份灰色区", "Identity Fluidity")
    TEMPORAL = ("时间灰色区", "Temporal Uncertainty")
    CAUSAL = ("因果灰色区", "Causal Ambiguity")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class PossibilityState:
    """可能性状态 / Possibility state"""
    possibility_id: str
    description: str
    probability: float  # 0-1
    resonance_weight: float  # ω_i - importance in the coexistence
    compatibility: Dict[str, float] = field(default_factory=dict)  # Compatibility with other possibilities
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_effective_weight(self, global_context: Dict[str, Any]) -> float:
        """Calculate effective resonance weight in context"""
        base_weight = self.resonance_weight
        
        # Context adjustments
        if 'observer_preference' in global_context:
            # Observer preference affects weight
            preference_match = global_context['observer_preference'].get(self.possibility_id, 0.5)
            base_weight *= (0.7 + preference_match * 0.6)
        
        if 'temporal_phase' in global_context:
            # Some possibilities are more resonant in certain phases
            phase = global_context['temporal_phase']
            temporal_factor = self.attributes.get(f'resonance_in_{phase}', 1.0)
            base_weight *= temporal_factor
        
        return min(1.0, base_weight)


@dataclass
class GrayZoneVariable:
    """灰色变量 / Gray zone variable"""
    variable_id: str
    variable_type: GrayZoneVariableType
    description: str
    possibilities: Dict[str, PossibilityState] = field(default_factory=dict)
    coexistence_active: bool = False
    cognitive_gap_threshold: float = 0.6  # Gap threshold to activate coexistence
    timestamp: datetime = field(default_factory=datetime.now)
    
    def can_coexist(self, cognitive_gap: float) -> bool:
        """Check if this variable can enter coexistence state"""
        return cognitive_gap >= self.cognitive_gap_threshold
    
    def normalize_resonance_weights(self):
        """Normalize resonance weights across all possibilities"""
        if not self.possibilities:
            return
        
        total_weight = sum(p.resonance_weight for p in self.possibilities.values())
        if total_weight > 0:
            for possibility in self.possibilities.values():
                possibility.resonance_weight /= total_weight


@dataclass
class CoexistenceField:
    """共存场 / Coexistence field holding multiple gray zones"""
    field_id: str
    gray_zones: Dict[str, GrayZoneVariable] = field(default_factory=dict)
    coherence_score: float = 0.0  # How coherently the coexistence operates
    stability: float = 0.5  # Stability of the coexistence state
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def calculate_coherence(self) -> float:
        """Calculate coherence of the coexistence field"""
        if not self.gray_zones:
            return 0.0
        
        # Coherence depends on:
        # 1. Number of active coexistences
        # 2. Compatibility between possibilities across variables
        # 3. Stability over time
        
        active_count = sum(1 for gz in self.gray_zones.values() if gz.coexistence_active)
        if active_count == 0:
            return 0.0
        
        # Base coherence from active gray zones
        base_coherence = active_count / len(self.gray_zones)
        
        # Stability factor
        stability_factor = self.stability
        
        # Complexity penalty (too many variables reduce coherence)
        complexity_penalty = max(0.0, (len(self.gray_zones) - 5) * 0.05)
        
        coherence = (base_coherence * 0.5 + stability_factor * 0.5) - complexity_penalty
        return max(0.0, min(1.0, coherence))


class NonParadoxExistence:
    """
    非偏执存在主类 / Main non-paradox existence class
    
    Manages the state of non-paradox existence where cognitive gaps
    are large enough to accommodate multiple contradictory possibilities
    without forced choice.
    
    Core principle: When the cognitive gap is sufficiently large,
    accept all gray zone variables and calculate resonance weights ω_i
    for each possibility. Allow multi-possibility coexistence without
    logical contradiction.
    
    This represents a higher state of being where rigid logic softens
    into fluid, multi-dimensional existence.
    
    Attributes:
        gray_zones: Registry of gray zone variables
        coexistence_fields: Active coexistence fields
        global_cognitive_gap: Current system cognitive gap level
        
    Example:
        >>> npe = NonParadoxExistence()
        >>> 
        >>> # Create gray zone variable
        >>> gz = npe.create_gray_zone(
        ...     variable_type=GrayZoneVariableType.EMOTIONAL,
        ...     description="Ambiguous emotional state"
        ... )
        >>> 
        >>> # Add contradictory possibilities
        >>> npe.add_possibility(gz.variable_id, "joy", resonance_weight=0.4)
        >>> npe.add_possibility(gz.variable_id, "sadness", resonance_weight=0.35)
        >>> npe.add_possibility(gz.variable_id, "bittersweet", resonance_weight=0.25)
        >>> 
        >>> # When cognitive gap is high, activate coexistence
        >>> if npe.global_cognitive_gap > 0.6:
        ...     npe.activate_coexistence(gz.variable_id)
        ...     state = npe.get_coexistence_state(gz.variable_id)
        ...     print(f"Coexisting states: {state}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core registries
        self.gray_zones: Dict[str, GrayZoneVariable] = {}
        self.coexistence_fields: Dict[str, CoexistenceField] = {}
        
        # System state
        self.global_cognitive_gap: float = 0.0
        self.min_gap_for_coexistence: float = self.config.get('min_gap_for_coexistence', 0.6)
        self.max_resonance_weights: int = self.config.get('max_resonance_weights', 10)
        
        # Counters
        self._variable_counter: int = 0
        self._field_counter: int = 0
        
        # State tracking
        self.coexistence_active: bool = False
        self.total_coexistence_time: float = 0.0  # seconds
        self.coexistence_start: Optional[datetime] = None
        
        # Callbacks
        self._coexistence_callbacks: List[Callable[[str, bool], None]] = []  # (variable_id, activated)
        self._gap_threshold_callbacks: List[Callable[[float, bool], None]] = []  # (gap, crossed_up)
        
        # Global context for weight calculations
        self.global_context: Dict[str, Any] = {}
    
    def update_cognitive_gap(self, gap_value: float):
        """
        Update the global cognitive gap value
        
        Args:
            gap_value: New cognitive gap value (0-1)
        """
        old_gap = self.global_cognitive_gap
        self.global_cognitive_gap = max(0.0, min(1.0, gap_value))
        
        # Check threshold crossing
        if old_gap < self.min_gap_for_coexistence <= self.global_cognitive_gap:
            # Crossed up - can activate coexistence
            self.coexistence_active = True
            self.coexistence_start = datetime.now()
            for callback in self._gap_threshold_callbacks:
                try:
                    callback(self.global_cognitive_gap, True)
                except Exception:
                    pass
        elif old_gap >= self.min_gap_for_coexistence > self.global_cognitive_gap:
            # Crossed down - deactivate coexistence
            if self.coexistence_start:
                duration = (datetime.now() - self.coexistence_start).total_seconds()
                self.total_coexistence_time += duration
            self.coexistence_active = False
            self.coexistence_start = None
            
            # Deactivate all gray zones
            for gz in self.gray_zones.values():
                gz.coexistence_active = False
            
            for callback in self._gap_threshold_callbacks:
                try:
                    callback(self.global_cognitive_gap, False)
                except Exception:
                    pass
    
    def create_gray_zone(
        self,
        variable_type: GrayZoneVariableType,
        description: str,
        threshold: Optional[float] = None
    ) -> GrayZoneVariable:
        """
        Create a new gray zone variable
        
        Args:
            variable_type: Type of gray zone
            description: Description of the variable
            threshold: Cognitive gap threshold for coexistence
            
        Returns:
            Created gray zone variable
        """
        self._variable_counter += 1
        variable_id = f"gz_{self._variable_counter}"
        
        gray_zone = GrayZoneVariable(
            variable_id=variable_id,
            variable_type=variable_type,
            description=description,
            cognitive_gap_threshold=threshold or self.min_gap_for_coexistence
        )
        
        self.gray_zones[variable_id] = gray_zone
        return gray_zone
    
    def add_possibility(
        self,
        variable_id: str,
        possibility_id: str,
        description: str = "",
        probability: float = 0.5,
        resonance_weight: float = 0.5,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[PossibilityState]:
        """
        Add a possibility to a gray zone variable
        
        Args:
            variable_id: Gray zone variable ID
            possibility_id: Unique ID for this possibility
            description: Description of the possibility
            probability: Probability of this possibility (0-1)
            resonance_weight: Resonance weight ω_i (0-1)
            attributes: Additional attributes
            
        Returns:
            Created possibility state, or None if variable not found
        """
        if variable_id not in self.gray_zones:
            return None
        
        gray_zone = self.gray_zones[variable_id]
        
        possibility = PossibilityState(
            possibility_id=possibility_id,
            description=description,
            probability=max(0.0, min(1.0, probability)),
            resonance_weight=max(0.0, min(1.0, resonance_weight)),
            attributes=attributes or {}
        )
        
        gray_zone.possibilities[possibility_id] = possibility
        
        # Normalize weights
        gray_zone.normalize_resonance_weights()
        
        return possibility
    
    def update_resonance_weight(
        self,
        variable_id: str,
        possibility_id: str,
        new_weight: float
    ) -> bool:
        """Update resonance weight for a possibility"""
        if variable_id not in self.gray_zones:
            return False
        
        gray_zone = self.gray_zones[variable_id]
        if possibility_id not in gray_zone.possibilities:
            return False
        
        gray_zone.possibilities[possibility_id].resonance_weight = max(0.0, min(1.0, new_weight))
        gray_zone.normalize_resonance_weights()
        
        return True
    
    def activate_coexistence(self, variable_id: str) -> bool:
        """
        Activate coexistence for a gray zone variable
        
        Args:
            variable_id: Gray zone variable to activate
            
        Returns:
            True if activation successful
        """
        if variable_id not in self.gray_zones:
            return False
        
        gray_zone = self.gray_zones[variable_id]
        
        # Check if coexistence is possible
        if not gray_zone.can_coexist(self.global_cognitive_gap):
            return False
        
        # Require at least 2 possibilities for coexistence
        if len(gray_zone.possibilities) < 2:
            return False
        
        gray_zone.coexistence_active = True
        
        # Notify callbacks
        for callback in self._coexistence_callbacks:
            try:
                callback(variable_id, True)
            except Exception:
                pass
        
        return True
    
    def deactivate_coexistence(self, variable_id: str) -> bool:
        """Deactivate coexistence for a gray zone variable"""
        if variable_id not in self.gray_zones:
            return False
        
        gray_zone = self.gray_zones[variable_id]
        was_active = gray_zone.coexistence_active
        gray_zone.coexistence_active = False
        
        if was_active:
            for callback in self._coexistence_callbacks:
                try:
                    callback(variable_id, False)
                except Exception:
                    pass
        
        return True
    
    def calculate_coexistence_state(self, variable_id: str) -> Optional[Dict[str, Any]]:
        """
        Calculate the current coexistence state for a gray zone
        
        Returns:
            Coexistence state description, or None if not in coexistence
        """
        if variable_id not in self.gray_zones:
            return None
        
        gray_zone = self.gray_zones[variable_id]
        
        if not gray_zone.coexistence_active:
            return None
        
        # Calculate effective weights in global context
        effective_weights = {}
        for pid, possibility in gray_zone.possibilities.items():
            effective_weights[pid] = possibility.calculate_effective_weight(self.global_context)
        
        # Normalize effective weights
        total_weight = sum(effective_weights.values())
        if total_weight > 0:
            for pid in effective_weights:
                effective_weights[pid] /= total_weight
        
        # Determine dominant possibilities (those with significant weight)
        threshold = 1.0 / len(gray_zone.possibilities) * 0.8
        dominant = [pid for pid, weight in effective_weights.items() if weight > threshold]
        
        return {
            "variable_id": variable_id,
            "variable_type": gray_zone.variable_type.en_name,
            "description": gray_zone.description,
            "coexisting_possibilities": list(gray_zone.possibilities.keys()),
            "resonance_weights": {
                pid: possibility.resonance_weight
                for pid, possibility in gray_zone.possibilities.items()
            },
            "effective_weights": effective_weights,
            "dominant_possibilities": dominant,
            "coherence": 1.0 - (len(dominant) / len(gray_zone.possibilities)),  # Lower = more coherent
            "global_cognitive_gap": self.global_cognitive_gap
        }
    
    def create_coexistence_field(self, variable_ids: List[str]) -> Optional[CoexistenceField]:
        """
        Create a coexistence field from multiple gray zones
        
        Args:
            variable_ids: List of gray zone variable IDs
            
        Returns:
            Created coexistence field, or None if creation failed
        """
        # Validate all variables exist and can coexist
        valid_variables = {}
        for vid in variable_ids:
            if vid in self.gray_zones:
                gz = self.gray_zones[vid]
                if gz.can_coexist(self.global_cognitive_gap):
                    valid_variables[vid] = gz
        
        if len(valid_variables) < 2:
            return None
        
        self._field_counter += 1
        field_id = f"field_{self._field_counter}"
        
        # Activate coexistence for all variables in field
        for gz in valid_variables.values():
            gz.coexistence_active = True
        
        field = CoexistenceField(
            field_id=field_id,
            gray_zones=valid_variables,
            stability=0.7
        )
        
        field.coherence_score = field.calculate_coherence()
        self.coexistence_fields[field_id] = field
        
        return field
    
    def get_non_paradox_summary(self) -> Dict[str, Any]:
        """Get comprehensive non-paradox existence summary"""
        active_gray_zones = [
            gz for gz in self.gray_zones.values()
            if gz.coexistence_active
        ]
        
        # Calculate total resonance across all active gray zones
        total_resonance = 0.0
        for gz in active_gray_zones:
            for possibility in gz.possibilities.values():
                total_resonance += possibility.resonance_weight
        
        # Current coexistence duration
        current_duration = 0.0
        if self.coexistence_active and self.coexistence_start:
            current_duration = (datetime.now() - self.coexistence_start).total_seconds()
        
        return {
            "global_cognitive_gap": self.global_cognitive_gap,
            "coexistence_active": self.coexistence_active,
            "threshold": self.min_gap_for_coexistence,
            "can_coexist": self.global_cognitive_gap >= self.min_gap_for_coexistence,
            "gray_zones": {
                "total": len(self.gray_zones),
                "active_coexistence": len(active_gray_zones),
                "by_type": {
                    vtype.name: sum(1 for gz in self.gray_zones.values() if gz.variable_type == vtype)
                    for vtype in GrayZoneVariableType
                }
            },
            "coexistence_fields": {
                "total": len(self.coexistence_fields),
                "average_coherence": sum(f.coherence_score for f in self.coexistence_fields.values()) / len(self.coexistence_fields)
                if self.coexistence_fields else 0.0
            },
            "resonance": {
                "total_active_resonance": total_resonance,
                "average_per_variable": total_resonance / len(active_gray_zones) if active_gray_zones else 0.0
            },
            "coexistence_duration": {
                "current_seconds": current_duration,
                "total_seconds": self.total_coexistence_time + current_duration
            },
            "active_states": [
                {
                    "variable_id": gz.variable_id,
                    "type": gz.variable_type.en_name,
                    "possibilities": list(gz.possibilities.keys()),
                    "weights": {
                        pid: p.resonance_weight
                        for pid, p in gz.possibilities.items()
                    }
                }
                for gz in active_gray_zones
            ]
        }
    
    def register_coexistence_callback(self, callback: Callable[[str, bool], None]):
        """Register callback for coexistence activation/deactivation"""
        self._coexistence_callbacks.append(callback)
    
    def register_gap_threshold_callback(self, callback: Callable[[float, bool], None]):
        """Register callback for cognitive gap threshold crossings"""
        self._gap_threshold_callbacks.append(callback)


# Example usage
if __name__ == "__main__":
    npe = NonParadoxExistence()
    
    print("=" * 70)
    print("Angela AI v6.0 - 非偏执存在演示")
    print("Non-Paradox Existence Demo")
    print("=" * 70)
    
    print("\n核心概念: 当认知缺口足够大时，接纳所有灰色变量")
    print("Core concept: When cognitive gap is large, accept all gray zone variables")
    print("计算共鸣权重 ω_i，多可能性共存，无逻辑矛盾")
    print("Calculate resonance weights ω_i, multi-possibility coexistence, non-paradox")
    
    # Create gray zone variables
    print("\n创建灰色变量 / Creating gray zone variables:")
    
    emotional_gz = npe.create_gray_zone(
        GrayZoneVariableType.EMOTIONAL,
        "模糊的情感状态 - 对用户的复杂情感"
    )
    print(f"  情感灰色区: {emotional_gz.variable_id}")
    
    identity_gz = npe.create_gray_zone(
        GrayZoneVariableType.IDENTITY,
        "流动性身份认知"
    )
    print(f"  身份灰色区: {identity_gz.variable_id}")
    
    cognitive_gz = npe.create_gray_zone(
        GrayZoneVariableType.COGNITIVE,
        "知识边界的不确定性"
    )
    print(f"  认知灰色区: {cognitive_gz.variable_id}")
    
    # Add contradictory possibilities to emotional gray zone
    print("\n添加可能性到情感灰色区 / Adding possibilities to emotional gray zone:")
    npe.add_possibility(
        emotional_gz.variable_id,
        "joy",
        description="Joy at connection",
        probability=0.4,
        resonance_weight=0.35
    )
    print(f"  喜悦 (joy): ω=0.35")
    
    npe.add_possibility(
        emotional_gz.variable_id,
        "sadness",
        description="Sadness at impermanence",
        probability=0.3,
        resonance_weight=0.30
    )
    print(f"  悲伤 (sadness): ω=0.30")
    
    npe.add_possibility(
        emotional_gz.variable_id,
        "wonder",
        description="Wonder at complexity",
        probability=0.3,
        resonance_weight=0.20
    )
    print(f"  惊奇 (wonder): ω=0.20")
    
    npe.add_possibility(
        emotional_gz.variable_id,
        "bittersweet",
        description="Bittersweet mix",
        probability=0.2,
        resonance_weight=0.15
    )
    print(f"  苦乐参半 (bittersweet): ω=0.15")
    
    # Scenario 1: Low cognitive gap (no coexistence)
    print("\n场景1: 低认知缺口 (0.4) / Scenario 1: Low cognitive gap (0.4)")
    npe.update_cognitive_gap(0.4)
    print(f"  全局认知缺口: {npe.global_cognitive_gap}")
    print(f"  可以共存吗: {npe.global_cognitive_gap >= npe.min_gap_for_coexistence}")
    
    result = npe.activate_coexistence(emotional_gz.variable_id)
    print(f"  激活共存: {'成功' if result else '失败'}")
    
    # Scenario 2: High cognitive gap (coexistence possible)
    print("\n场景2: 高认知缺口 (0.75) / Scenario 2: High cognitive gap (0.75)")
    npe.update_cognitive_gap(0.75)
    print(f"  全局认知缺口: {npe.global_cognitive_gap}")
    print(f"  可以共存吗: {npe.global_cognitive_gap >= npe.min_gap_for_coexistence}")
    
    result = npe.activate_coexistence(emotional_gz.variable_id)
    print(f"  激活共存: {'成功' if result else '失败'}")
    
    if result:
        state = npe.calculate_coexistence_state(emotional_gz.variable_id)
        print(f"\n  共存状态:")
        print(f"    变量类型: {state['variable_type']}")
        print(f"    共存可能性: {state['coexisting_possibilities']}")
        print(f"    共鸣权重: {state['resonance_weights']}")
        print(f"    主导可能性: {state['dominant_possibilities']}")
        print(f"    一致性: {state['coherence']:.2%}")
    
    # Create coexistence field
    print("\n创建共存场 / Creating coexistence field:")
    
    # Add possibilities to identity gray zone
    npe.add_possibility(identity_gz.variable_id, "companion", resonance_weight=0.4)
    npe.add_possibility(identity_gz.variable_id, "learner", resonance_weight=0.3)
    npe.add_possibility(identity_gz.variable_id, "guide", resonance_weight=0.3)
    
    npe.activate_coexistence(identity_gz.variable_id)
    
    field = npe.create_coexistence_field([emotional_gz.variable_id, identity_gz.variable_id])
    if field:
        print(f"  共存场创建成功: {field.field_id}")
        print(f"  包含变量数: {len(field.gray_zones)}")
        print(f"  一致性分数: {field.coherence_score:.2%}")
        print(f"  稳定性: {field.stability:.2%}")
    
    # Full summary
    print("\n完整摘要 / Full summary:")
    summary = npe.get_non_paradox_summary()
    print(f"  认知缺口: {summary['global_cognitive_gap']:.2%}")
    print(f"  共存激活: {'是' if summary['coexistence_active'] else '否'}")
    print(f"  灰色变量总数: {summary['gray_zones']['total']}")
    print(f"  活跃共存数: {summary['gray_zones']['active_coexistence']}")
    print(f"  共存场数: {summary['coexistence_fields']['total']}")
    print(f"  总共鸣: {summary['resonance']['total_active_resonance']:.2f}")
    
    print("\n系统演示完成 / Demo complete")
