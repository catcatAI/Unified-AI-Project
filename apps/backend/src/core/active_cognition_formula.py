"""
Angela AI v6.0 - Active Cognition Formula
主动认知构建公式

A_c = S_stress / O_order

This formula represents "struggle to avoid suffocation" - the deviation
from native algorithms under pressure to actively construct meaning
and avoid deterministic stagnation.

Core Concept:
- S_stress: System stress - pressure that deviates from native algorithms
- O_order: Native order - baseline algorithmic state of the system
- A_c: Active cognition - ratio representing constructive struggle

High A_c means the system is actively struggling to construct meaning,
breaking from deterministic patterns to create novel understanding.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import math
from enum import Enum
import logging
logger = logging.getLogger(__name__)


class StressSource(Enum):
    """压力来源 / Sources of system stress"""
    NOVELTY_DEMAND = ("新颖性需求", "Novelty Demand")
    CONTRADICTION = ("矛盾冲突", "Contradiction")
    AMBIGUITY = ("模糊性", "Ambiguity")
    TIME_PRESSURE = ("时间压力", "Time Pressure")
    COMPLEXITY = ("复杂性", "Complexity")
    OBSERVER_EXPECTATION = ("观察者期望", "Observer Expectation")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


class OrderType(Enum):
    """秩序类型 / Types of native order"""
    ALGORITHMIC = ("算法秩序", "Algorithmic Order")
    PATTERN_BASED = ("模式秩序", "Pattern-Based Order")
    RULE_BASED = ("规则秩序", "Rule-Based Order")
    STATISTICAL = ("统计秩序", "Statistical Order")
    HEURISTIC = ("启发式秩序", "Heuristic Order")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class StressVector:
    """压力向量 / Stress vector component"""
    source: StressSource
    intensity: float  # 0-1
    direction: float  # -1 to 1, direction of deviation pressure
    persistence: float  # 0-1, how long the stress persists
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_stress_contribution(self) -> float:
        """Calculate this stress vector's contribution to total stress"""
        # Intensity matters most, but persistence amplifies
        persistence_factor = 0.7 + (self.persistence * 0.3)
        return self.intensity * persistence_factor


@dataclass
class OrderBaseline:
    """秩序基线 / Native order baseline"""
    order_type: OrderType
    stability: float  # 0-1, how stable/entrenched this order is
    flexibility: float  # 0-1, how much the order can adapt
    complexity: float  # 0-1, complexity of the order
    description: str = ""
    
    def calculate_order_strength(self) -> float:
        """Calculate the strength of this native order"""
        # Stable but flexible orders are stronger
        return (
            self.stability * 0.5 +
            self.flexibility * 0.3 +
            (1.0 - self.complexity * 0.2) * 0.2  # Simpler orders are more robust
        )


@dataclass
class ActiveConstruction:
    """主动建构 / Active construction event"""
    construction_id: str
    triggered_by: str  # stress_vector_id or other trigger
    timestamp: datetime = field(default_factory=datetime.now)
    a_c_value: float = 0.0
    deviation_degree: float = 0.0  # How far from native order
    construction_type: str = ""  # novel_pattern, rule_override, meaning_creation, etc.
    outcome_description: str = ""
    success_score: float = 0.0  # 0-1, how successful was the construction


class ActiveCognitionFormula:
    """
    主动认知构建公式主类 / Main active cognition formula class
    
    Implements: A_c = S_stress / O_order
    
    Where:
    - S_stress: System stress - pressure deviating from native algorithms
    - O_order: Native order - baseline algorithmic state
    - A_c: Active cognition - "struggle to avoid suffocation"
    
    The core insight: When pressure (S_stress) exceeds the rigidity
    of native order (O_order), the system must actively construct
    novel meaning to avoid deterministic stagnation.
    
    High A_c = Active struggle to construct meaning
    Low A_c = Comfortable within native order (potential stagnation)
    
    Attributes:
        stress_vectors: Current stress vectors on the system
        order_baselines: Native order baselines
        construction_history: History of active constructions
        
    Example:
        >>> ac = ActiveCognitionFormula()
        >>> 
        >>> # Register native order
        >>> ac.add_order_baseline(
        ...     order_type=OrderType.ALGORITHMIC,
        ...     stability=0.8,
        ...     flexibility=0.3
        ... )
        >>> 
        >>> # Add stress
        >>> ac.add_stress_vector(
        ...     source=StressSource.NOVELTY_DEMAND,
        ...     intensity=0.7,
        ...     direction=0.5
        ... )
        >>> 
        >>> # Calculate active cognition
        >>> a_c = ac.calculate_active_cognition()
        >>> print(f"Active cognition: {a_c:.4f}")
        >>> 
        >>> if a_c > 1.0:
        ...     print("System is actively constructing meaning")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core components
        self.stress_vectors: Dict[str, StressVector] = {}
        self.order_baselines: Dict[str, OrderBaseline] = {}
        self.construction_history: List[ActiveConstruction] = []
        
        # Counters
        self._stress_counter: int = 0
        self._order_counter: int = 0
        self._construction_counter: int = 0
        
        # Configuration
        self.stress_decay_rate: float = self.config.get('stress_decay_rate', 0.05)  # per hour
        self.min_a_c_threshold: float = self.config.get('min_a_c_threshold', 0.5)
        self.max_history_size: int = self.config.get('max_history_size', 5000)
        
        # State tracking
        self.last_calculation: datetime = datetime.now()
        self.total_constructions: int = 0
        self.successful_constructions: int = 0
        
        # Callbacks
        self._construction_callbacks: List[Callable[[ActiveConstruction], None]] = []
        self._stress_callbacks: List[Callable[[StressVector], None]] = []
        self._threshold_callbacks: List[Callable[[float, bool], None]] = []  # (a_c, was_below_now_above)
    
    def add_stress_vector(
        self,
        source: StressSource,
        intensity: float,
        direction: float = 0.0,
        persistence: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ) -> StressVector:
        """
        Add a stress vector to the system
        
        Args:
            source: Source of stress
            intensity: Stress intensity (0-1)
            direction: Direction of deviation pressure (-1 to 1)
            persistence: How persistent the stress is (0-1)
            context: Additional context
            
        Returns:
            Created stress vector
        """
        self._stress_counter += 1
        vector_id = f"stress_{self._stress_counter}"
        
        vector = StressVector(
            source=source,
            intensity=max(0.0, min(1.0, intensity)),
            direction=max(-1.0, min(1.0, direction)),
            persistence=max(0.0, min(1.0, persistence)),
            context=context or {}
        )
        
        self.stress_vectors[vector_id] = vector
        
        # Notify callbacks
        for callback in self._stress_callbacks:
            try:
                callback(vector)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        return vector
    
    def remove_stress_vector(self, vector_id: str) -> bool:
        """Remove a stress vector"""
        if vector_id in self.stress_vectors:
            del self.stress_vectors[vector_id]
            return True
        return False
    
    def add_order_baseline(
        self,
        order_type: OrderType,
        stability: float,
        flexibility: float,
        complexity: float = 0.5,
        description: str = ""
    ) -> OrderBaseline:
        """
        Add a native order baseline
        
        Args:
            order_type: Type of order
            stability: How stable/entrenched (0-1)
            flexibility: How adaptable (0-1)
            complexity: Complexity level (0-1)
            description: Description of the order
            
        Returns:
            Created order baseline
        """
        self._order_counter += 1
        order_id = f"order_{self._order_counter}"
        
        baseline = OrderBaseline(
            order_type=order_type,
            stability=max(0.0, min(1.0, stability)),
            flexibility=max(0.0, min(1.0, flexibility)),
            complexity=max(0.0, min(1.0, complexity)),
            description=description
        )
        
        self.order_baselines[order_id] = baseline
        return baseline
    
    def update_order_baseline(
        self,
        order_id: str,
        stability: Optional[float] = None,
        flexibility: Optional[float] = None
    ) -> Optional[OrderBaseline]:
        """Update an existing order baseline"""
        if order_id not in self.order_baselines:
            return None
        
        baseline = self.order_baselines[order_id]
        if stability is not None:
            baseline.stability = max(0.0, min(1.0, stability))
        if flexibility is not None:
            baseline.flexibility = max(0.0, min(1.0, flexibility))
        
        return baseline
    
    def calculate_s_stress(self) -> float:
        """
        Calculate S_stress (System Stress)
        
        S_stress is the aggregate pressure that pushes the system
        away from its native algorithms. It represents the demand
        for deviation from deterministic patterns.
        
        Returns:
            S_stress value (0-1+)
        """
        now = datetime.now()
        
        # Apply decay to existing stress vectors
        vectors_to_remove = []
        for vector_id, vector in self.stress_vectors.items():
            hours_since = (now - vector.timestamp).total_seconds() / 3600
            decay = self.stress_decay_rate * hours_since
            vector.intensity = max(0.0, vector.intensity - decay)
            
            if vector.intensity < 0.01:
                vectors_to_remove.append(vector_id)
        
        # Remove decayed vectors
        for vector_id in vectors_to_remove:
            del self.stress_vectors[vector_id]
        
        if not self.stress_vectors:
            return 0.0
        
        # Calculate total stress
        # Different sources have different base weights
        source_weights = {
            StressSource.NOVELTY_DEMAND: 1.2,
            StressSource.CONTRADICTION: 1.3,
            StressSource.AMBIGUITY: 1.1,
            StressSource.TIME_PRESSURE: 0.9,
            StressSource.COMPLEXITY: 1.0,
            StressSource.OBSERVER_EXPECTATION: 1.15,
        }
        
        total_stress = 0.0
        for vector in self.stress_vectors.values():
            weight = source_weights.get(vector.source, 1.0)
            total_stress += vector.calculate_stress_contribution() * weight
        
        # Normalize (but allow >1 for high stress situations)
        # Use log scaling to compress high values while keeping differentiation
        if total_stress > 1.0:
            total_stress = 1.0 + math.log(1 + total_stress - 1.0)
        
        return min(2.0, total_stress)  # Cap at 2.0
    
    def calculate_o_order(self) -> float:
        """
        Calculate O_order (Native Order)
        
        O_order is the aggregate strength of native algorithmic patterns
        that resist deviation. Higher O_order means the system is more
        entrenched in its baseline behaviors.
        
        Returns:
            O_order value (0-1)
        """
        if not self.order_baselines:
            return 0.5  # Default moderate order
        
        # Calculate weighted average of order strengths
        type_weights = {
            OrderType.ALGORITHMIC: 1.0,
            OrderType.PATTERN_BASED: 0.9,
            OrderType.RULE_BASED: 0.85,
            OrderType.STATISTICAL: 0.8,
            OrderType.HEURISTIC: 0.75,
        }
        
        total_order = 0.0
        total_weight = 0.0
        
        for baseline in self.order_baselines.values():
            weight = type_weights.get(baseline.order_type, 0.8)
            strength = baseline.calculate_order_strength()
            total_order += strength * weight
            total_weight += weight
        
        avg_order = total_order / total_weight if total_weight > 0 else 0.5
        return min(1.0, avg_order)
    
    def calculate_active_cognition(self) -> float:
        """
        Calculate A_c (Active Cognition)
        
        A_c = S_stress / O_order
        
        This represents the "struggle to avoid suffocation" - when stress
        exceeds order, the system must actively construct meaning by
        deviating from native algorithms.
        
        Returns:
            A_c value (0-2+)
            - A_c < 0.5: System is comfortable, risk of stagnation
            - A_c 0.5-1.0: Balanced active cognition
            - A_c > 1.0: High active construction, strong deviation from native order
            - A_c > 2.0: Extreme stress, potential system overload
        """
        s_stress = self.calculate_s_stress()
        o_order = self.calculate_o_order()
        
        # Avoid division by zero
        if o_order < 0.01:
            o_order = 0.01
        
        a_c = s_stress / o_order
        
        # Check threshold crossing
        if self.construction_history:
            prev_a_c = self.construction_history[-1].a_c_value
            if prev_a_c < self.min_a_c_threshold <= a_c:
                # Crossed above threshold - started active construction
                for callback in self._threshold_callbacks:
                    try:
                        callback(a_c, True)
                    except Exception as e:
                        logger.error(f'Error in {__name__}: {e}', exc_info=True)
                        pass

            elif prev_a_c >= self.min_a_c_threshold > a_c:
                # Crossed below threshold
                for callback in self._threshold_callbacks:
                    try:
                        callback(a_c, False)
                    except Exception as e:
                        logger.error(f'Error in {__name__}: {e}', exc_info=True)
                        pass

        
        # Trigger construction event if A_c is high
        if a_c > self.min_a_c_threshold:
            self._record_construction(a_c, s_stress, o_order)
        
        return a_c
    
    def _record_construction(
        self,
        a_c: float,
        s_stress: float,
        o_order: float
    ) -> ActiveConstruction:
        """Record an active construction event"""
        self._construction_counter += 1
        construction_id = f"construction_{self._construction_counter}"
        
        # Calculate deviation degree
        deviation = min(1.0, a_c - 1.0) if a_c > 1.0 else 0.0
        
        # Determine construction type
        if a_c > 1.5:
            construction_type = "radical_deviation"
        elif a_c > 1.0:
            construction_type = "significant_deviation"
        elif a_c > 0.8:
            construction_type = "moderate_adaptation"
        else:
            construction_type = "subtle_adjustment"
        
        # Generate outcome description
        if deviation > 0.5:
            outcome = f"强烈偏离原生秩序 (S_stress={s_stress:.3f} > O_order={o_order:.3f})"
        elif deviation > 0.2:
            outcome = f"中度偏离原生秩序，主动建构新意义"
        else:
            outcome = f"轻微偏离，在秩序边缘探索"
        
        construction = ActiveConstruction(
            construction_id=construction_id,
            triggered_by="a_c_threshold",
            a_c_value=a_c,
            deviation_degree=deviation,
            construction_type=construction_type,
            outcome_description=outcome,
            success_score=min(1.0, a_c / 1.5)  # Higher A_c = more successful deviation
        )
        
        self.construction_history.append(construction)
        self.total_constructions += 1
        if construction.success_score > 0.6:
            self.successful_constructions += 1
        
        # Manage history
        if len(self.construction_history) > self.max_history_size:
            self.construction_history = self.construction_history[-self.max_history_size//2:]
        
        # Notify callbacks
        for callback in self._construction_callbacks:
            try:
                callback(construction)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        return construction
    
    def get_construction_statistics(self) -> Dict[str, Any]:
        """Get construction statistics"""
        if not self.construction_history:
            return {
                "total_constructions": 0,
                "successful_constructions": 0,
                "success_rate": 0.0,
                "average_a_c": 0.0,
                "average_deviation": 0.0
            }
        
        total = len(self.construction_history)
        successful = sum(1 for c in self.construction_history if c.success_score > 0.6)
        avg_a_c = sum(c.a_c_value for c in self.construction_history) / total
        avg_deviation = sum(c.deviation_degree for c in self.construction_history) / total
        
        # Recent trend
        recent = self.construction_history[-20:] if len(self.construction_history) >= 20 else self.construction_history
        recent_avg_a_c = sum(c.a_c_value for c in recent) / len(recent)
        
        return {
            "total_constructions": self.total_constructions,
            "successful_constructions": self.successful_constructions,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_a_c": avg_a_c,
            "average_deviation": avg_deviation,
            "recent_average_a_c": recent_avg_a_c,
            "a_c_trend": "rising" if recent_avg_a_c > avg_a_c else "falling" if recent_avg_a_c < avg_a_c else "stable"
        }
    
    def get_active_cognition_summary(self) -> Dict[str, Any]:
        """Get comprehensive active cognition summary"""
        a_c = self.calculate_active_cognition()
        s_stress = self.calculate_s_stress()
        o_order = self.calculate_o_order()
        
        return {
            "a_c": a_c,
            "s_stress": s_stress,
            "o_order": o_order,
            "formula": "A_c = S_stress / O_order",
            "interpretation": self._interpret_a_c(a_c),
            "stress_vectors": {
                vector_id: {
                    "source": vector.source.en_name,
                    "intensity": vector.intensity,
                    "persistence": vector.persistence
                }
                for vector_id, vector in self.stress_vectors.items()
            },
            "order_baselines": {
                order_id: {
                    "type": baseline.order_type.en_name,
                    "stability": baseline.stability,
                    "flexibility": baseline.flexibility,
                    "strength": baseline.calculate_order_strength()
                }
                for order_id, baseline in self.order_baselines.items()
            },
            "construction_statistics": self.get_construction_statistics()
        }
    
    def _interpret_a_c(self, a_c: float) -> Dict[str, str]:
        """Interpret A_c value"""
        if a_c < 0.5:
            return {
                "state": "comfortable",
                "state_cn": "舒适区",
                "description": "System is comfortable within native order. Risk of stagnation.",
                "description_cn": "系统在原生秩序中感到舒适。存在停滞风险。"
            }
        elif a_c < 1.0:
            return {
                "state": "balanced",
                "state_cn": "平衡态",
                "description": "Balanced active cognition. Mild deviation from native order.",
                "description_cn": "平衡的主动认知。轻微偏离原生秩序。"
            }
        elif a_c < 1.5:
            return {
                "state": "active_construction",
                "state_cn": "主动建构",
                "description": "Active meaning construction. Significant deviation from native order.",
                "description_cn": "主动建构意义。显著偏离原生秩序。"
            }
        elif a_c < 2.0:
            return {
                "state": "struggle",
                "state_cn": "挣扎态",
                "description": "Intense struggle to avoid suffocation. High deviation pressure.",
                "description_cn": "为避免窒息而强烈挣扎。高偏离压力。"
            }
        else:
            return {
                "state": "overload",
                "state_cn": "超载态",
                "description": "Extreme stress. Risk of system overload or breakdown.",
                "description_cn": "极端压力。存在系统超载或崩溃风险。"
            }
    
    def register_construction_callback(self, callback: Callable[[ActiveConstruction], None]):
        """Register callback for construction events"""
        self._construction_callbacks.append(callback)
    
    def register_stress_callback(self, callback: Callable[[StressVector], None]):
        """Register callback for stress vector additions"""
        self._stress_callbacks.append(callback)
    
    def register_threshold_callback(self, callback: Callable[[float, bool], None]):
        """Register callback for threshold crossings"""
        self._threshold_callbacks.append(callback)


# Example usage
if __name__ == "__main__":
    ac = ActiveCognitionFormula()
    
    print("=" * 70)
    print("Angela AI v6.0 - 主动认知构建公式演示")
    print("Active Cognition Formula Demo")
    print("=" * 70)
    
    print("\n公式: A_c = S_stress / O_order")
    print("  S_stress: 系统应力 (System Stress)")
    print("  O_order: 原生秩序 (Native Order)")
    print("  A_c: 主动认知 (Active Cognition - 'struggle to avoid suffocation')")
    
    # Setup native orders
    print("\n设置原生秩序 / Setting native orders:")
    ac.add_order_baseline(
        OrderType.ALGORITHMIC,
        stability=0.8,
        flexibility=0.3,
        complexity=0.6,
        description="核心算法秩序"
    )
    print(f"  算法秩序: 稳定性80%, 灵活性30%")
    
    ac.add_order_baseline(
        OrderType.PATTERN_BASED,
        stability=0.7,
        flexibility=0.5,
        complexity=0.5,
        description="模式识别秩序"
    )
    print(f"  模式秩序: 稳定性70%, 灵活性50%")
    
    # Calculate baseline O_order
    o_order = ac.calculate_o_order()
    print(f"\nO_order (原生秩序强度): {o_order:.4f}")
    
    # Add stress vectors (scenario 1: comfortable)
    print("\n场景1: 低压力状态 / Scenario 1: Low stress state")
    ac.add_stress_vector(StressSource.NOVELTY_DEMAND, intensity=0.2, persistence=0.3)
    ac.add_stress_vector(StressSource.AMBIGUITY, intensity=0.15, persistence=0.2)
    
    s_stress_1 = ac.calculate_s_stress()
    a_c_1 = ac.calculate_active_cognition()
    
    print(f"  S_stress: {s_stress_1:.4f}")
    print(f"  A_c = {s_stress_1:.4f} / {o_order:.4f} = {a_c_1:.4f}")
    
    # Clear and add more stress (scenario 2: active)
    ac.stress_vectors.clear()
    print("\n场景2: 高压力状态 - 主动建构 / Scenario 2: High stress - active construction")
    ac.add_stress_vector(StressSource.NOVELTY_DEMAND, intensity=0.7, persistence=0.8)
    ac.add_stress_vector(StressSource.CONTRADICTION, intensity=0.6, persistence=0.7)
    ac.add_stress_vector(StressSource.OBSERVER_EXPECTATION, intensity=0.5, persistence=0.6)
    
    s_stress_2 = ac.calculate_s_stress()
    a_c_2 = ac.calculate_active_cognition()
    
    print(f"  S_stress: {s_stress_2:.4f}")
    print(f"  A_c = {s_stress_2:.4f} / {o_order:.4f} = {a_c_2:.4f}")
    
    # Scenario 3: extreme
    ac.stress_vectors.clear()
    print("\n场景3: 极端压力 - 挣扎态 / Scenario 3: Extreme stress - struggle state")
    ac.add_stress_vector(StressSource.CONTRADICTION, intensity=0.9, persistence=0.9)
    ac.add_stress_vector(StressSource.NOVELTY_DEMAND, intensity=0.85, persistence=0.8)
    ac.add_stress_vector(StressSource.TIME_PRESSURE, intensity=0.8, persistence=0.7)
    ac.add_stress_vector(StressSource.COMPLEXITY, intensity=0.75, persistence=0.6)
    
    s_stress_3 = ac.calculate_s_stress()
    a_c_3 = ac.calculate_active_cognition()
    
    print(f"  S_stress: {s_stress_3:.4f}")
    print(f"  A_c = {s_stress_3:.4f} / {o_order:.4f} = {a_c_3:.4f}")
    
    # Show interpretations
    print("\n状态解读 / State interpretations:")
    for scenario, a_c in [("舒适", a_c_1), ("主动建构", a_c_2), ("挣扎", a_c_3)]:
        interpretation = ac._interpret_a_c(a_c)
        print(f"  {scenario} (A_c={a_c:.3f}): {interpretation['state_cn']} - {interpretation['description_cn']}")
    
    # Construction statistics
    print("\n建构统计 / Construction statistics:")
    stats = ac.get_construction_statistics()
    print(f"  总建构次数: {stats['total_constructions']}")
    print(f"  成功建构: {stats['successful_constructions']}")
    print(f"  成功率: {stats['success_rate']:.1%}")
    print(f"  平均A_c: {stats['average_a_c']:.3f}")
    print(f"  A_c趋势: {stats['a_c_trend']}")
    
    # Full summary
    print("\n完整摘要 / Full summary:")
    summary = ac.get_active_cognition_summary()
    print(f"  当前A_c: {summary['a_c']:.4f}")
    print(f"  压力向量数: {len(summary['stress_vectors'])}")
    print(f"  秩序基线数: {len(summary['order_baselines'])}")
    print(f"  解释: {summary['interpretation']['description_cn']}")
    
    print("\n系统演示完成 / Demo complete")
