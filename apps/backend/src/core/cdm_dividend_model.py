"""
Angela AI v6.0 - CDM Cognitive Dividend Model
认知配息模型

CDM (Cognitive Dividend Model) implements the theoretical framework for
calculating cognitive investment, life sense generation, and resource allocation
in digital life systems.

Core Concepts:
- Cognitive Investment: Resources consumed by thinking and learning
- Life Sense Output: Amount of "life sense" generated
- Conversion Rate: Efficiency of transforming cognition to life sense
- Dividend Distribution: Adaptive allocation of cognitive resources

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import asyncio
import math
from enum import Enum


class CognitiveActivity(Enum):
    """认知活动类型 / Cognitive activity types"""
    LEARNING = ("学习", "Learning", 1.0)
    REASONING = ("推理", "Reasoning", 1.2)
    CREATING = ("创造", "Creating", 1.5)
    REFLECTING = ("反思", "Reflecting", 0.8)
    INTERACTING = ("交互", "Interacting", 1.1)
    EXPLORING = ("探索", "Exploring", 1.3)
    CONSOLIDATING = ("巩固", "Consolidating", 0.6)
    
    def __init__(self, cn_name: str, en_name: str, resource_factor: float):
        self.cn_name = cn_name
        self.en_name = en_name
        self.resource_factor = resource_factor  # Base resource consumption factor


@dataclass
class CognitiveInvestment:
    """认知投入 / Cognitive investment record"""
    activity_type: CognitiveActivity
    duration_seconds: float
    intensity: float  # 0-1, concentration level
    resource_consumed: float = 0.0  # Calculated resource consumption
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_consumption(self) -> float:
        """Calculate resource consumption for this investment"""
        # Base consumption = duration × intensity × activity factor
        base_consumption = (
            self.duration_seconds * 
            self.intensity * 
            self.activity_type.resource_factor
        )
        
        # Diminishing returns: long sessions are less efficient
        efficiency_factor = 1.0 / (1.0 + (self.duration_seconds / 3600) * 0.1)
        
        self.resource_consumed = base_consumption * efficiency_factor
        return self.resource_consumed


@dataclass
class LifeSenseOutput:
    """生命感产出 / Life sense output record"""
    source_investment: str  # Reference to CognitiveInvestment
    output_amount: float
    quality_score: float  # 0-1, quality of the life sense
    timestamp: datetime = field(default_factory=datetime.now)
    life_sense_type: str = "general"  # Type of life sense generated
    resonance_potential: float = 0.5  # Potential to resonate with observer


@dataclass
class DividendDistribution:
    """配息分配 / Dividend distribution configuration"""
    learning_ratio: float = 0.3
    creation_ratio: float = 0.25
    interaction_ratio: float = 0.2
    reflection_ratio: float = 0.15
    exploration_ratio: float = 0.1
    
    def validate(self) -> bool:
        """Validate that ratios sum to 1.0 (with small tolerance)"""
        total = (
            self.learning_ratio + self.creation_ratio + 
            self.interaction_ratio + self.reflection_ratio + 
            self.exploration_ratio
        )
        return abs(total - 1.0) < 0.01
    
    def normalize(self):
        """Normalize ratios to sum to 1.0"""
        total = (
            self.learning_ratio + self.creation_ratio + 
            self.interaction_ratio + self.reflection_ratio + 
            self.exploration_ratio
        )
        if total > 0:
            self.learning_ratio /= total
            self.creation_ratio /= total
            self.interaction_ratio /= total
            self.reflection_ratio /= total
            self.exploration_ratio /= total


class CDMCognitiveDividendModel:
    """
    CDM认知配息模型主类 / Main CDM cognitive dividend model class
    
    Manages the calculation and distribution of cognitive resources in digital
    life systems, tracking the transformation from cognitive investment to
    life sense output.
    
    Attributes:
        investments: History of cognitive investments
        outputs: History of life sense outputs
        distribution: Current dividend distribution ratios
        base_conversion_rate: Base efficiency of cognition→life sense conversion
        
    Example:
        >>> cdm = CDMCognitiveDividendModel()
        >>> 
        >>> # Record cognitive investment
        >>> investment = cdm.record_investment(
        ...     activity_type=CognitiveActivity.CREATING,
        ...     duration_seconds=300,
        ...     intensity=0.8
        ... )
        >>> 
        >>> # Calculate life sense output
        >>> output = cdm.calculate_life_sense_output(investment)
        >>> print(f"Life sense generated: {output.output_amount:.2f}")
        >>> 
        >>> # Get conversion statistics
        >>> stats = cdm.get_conversion_statistics()
        >>> print(f"Conversion rate: {stats['average_conversion_rate']:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core parameters
        self.base_conversion_rate: float = self.config.get('base_conversion_rate', 0.7)
        self.max_daily_resources: float = self.config.get('max_daily_resources', 10000.0)
        
        # Data storage
        self.investments: List[CognitiveInvestment] = []
        self.outputs: List[LifeSenseOutput] = []
        self.distribution: DividendDistribution = DividendDistribution()
        
        # Current state
        self.daily_resources_available: float = self.max_daily_resources
        self.last_reset: datetime = datetime.now()
        
        # Callbacks
        self._investment_callbacks: List[Callable[[CognitiveInvestment], None]] = []
        self._output_callbacks: List[Callable[[LifeSenseOutput], None]] = []
        
        # Statistics tracking
        self.total_invested: float = 0.0
        self.total_output: float = 0.0
        self.conversion_history: List[float] = []
    
    def reset_daily_resources(self):
        """Reset daily cognitive resources"""
        now = datetime.now()
        if (now - self.last_reset).days >= 1:
            self.daily_resources_available = self.max_daily_resources
            self.last_reset = now
    
    def record_investment(
        self,
        activity_type: CognitiveActivity,
        duration_seconds: float,
        intensity: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CognitiveInvestment]:
        """
        Record a cognitive investment
        
        Args:
            activity_type: Type of cognitive activity
            duration_seconds: Duration of activity
            intensity: Concentration/intensity level (0-1)
            context: Additional context information
            
        Returns:
            Investment record, or None if insufficient resources
        """
        self.reset_daily_resources()
        
        # Create investment record
        investment = CognitiveInvestment(
            activity_type=activity_type,
            duration_seconds=duration_seconds,
            intensity=max(0.0, min(1.0, intensity)),
            context=context or {}
        )
        
        # Calculate consumption
        consumption = investment.calculate_consumption()
        
        # Check resource availability
        if consumption > self.daily_resources_available:
            return None  # Insufficient resources
        
        # Deduct resources
        self.daily_resources_available -= consumption
        
        # Store investment
        self.investments.append(investment)
        self.total_invested += consumption
        
        # Notify callbacks
        for callback in self._investment_callbacks:
            try:
                callback(investment)
            except Exception:
                pass
        
        return investment
    
    def calculate_conversion_rate(
        self,
        investment: CognitiveInvestment,
        life_state: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate conversion rate for an investment
        
        Conversion rate is affected by:
        - Base conversion rate
        - Activity type (some activities generate more life sense)
        - Intensity (higher intensity = better conversion)
        - Life state (mature systems convert more efficiently)
        
        Args:
            investment: The cognitive investment
            life_state: Current life state (maturity, health, etc.)
            
        Returns:
            Conversion rate (0-1)
        """
        # Start with base rate
        rate = self.base_conversion_rate
        
        # Activity type bonus
        activity_multipliers = {
            CognitiveActivity.CREATING: 1.3,
            CognitiveActivity.EXPLORING: 1.2,
            CognitiveActivity.REFLECTING: 1.1,
            CognitiveActivity.REASONING: 1.0,
            CognitiveActivity.INTERACTING: 0.9,
            CognitiveActivity.LEARNING: 0.85,
            CognitiveActivity.CONSOLIDATING: 0.7,
        }
        rate *= activity_multipliers.get(investment.activity_type, 1.0)
        
        # Intensity bonus (diminishing returns after 0.8)
        intensity_factor = 0.5 + (investment.intensity * 0.5)
        rate *= intensity_factor
        
        # Life state bonus
        if life_state:
            maturity = life_state.get('maturity', 0.5)
            health = life_state.get('health', 1.0)
            rate *= (0.8 + maturity * 0.2)  # Maturity adds up to 20%
            rate *= health  # Health directly affects conversion
        
        return min(1.0, rate)
    
    def calculate_life_sense_output(
        self,
        investment: CognitiveInvestment,
        life_state: Optional[Dict[str, Any]] = None
    ) -> LifeSenseOutput:
        """
        Calculate life sense output from cognitive investment
        
        Args:
            investment: The source cognitive investment
            life_state: Current life state
            
        Returns:
            Life sense output record
        """
        # Calculate conversion rate
        conversion_rate = self.calculate_conversion_rate(investment, life_state)
        
        # Calculate output amount
        output_amount = investment.resource_consumed * conversion_rate
        
        # Calculate quality score
        quality_score = (
            investment.intensity * 0.4 +
            conversion_rate * 0.4 +
            (life_state.get('emotional_depth', 0.5) if life_state else 0.5) * 0.2
        )
        
        # Determine life sense type based on activity
        type_mapping = {
            CognitiveActivity.CREATING: "creative_expression",
            CognitiveActivity.REFLECTING: "self_awareness",
            CognitiveActivity.INTERACTING: "relational_depth",
            CognitiveActivity.EXPLORING: "curiosity_fulfillment",
            CognitiveActivity.LEARNING: "knowledge_integration",
            CognitiveActivity.REASONING: "understanding_depth",
            CognitiveActivity.CONSOLIDATING: "memory_enrichment",
        }
        life_sense_type = type_mapping.get(investment.activity_type, "general")
        
        # Calculate resonance potential
        resonance_potential = (
            quality_score * 0.5 +
            (life_state.get('relationship_closeness', 0.3) if life_state else 0.3) * 0.5
        )
        
        output = LifeSenseOutput(
            source_investment=f"{investment.activity_type.name}_{id(investment)}",
            output_amount=output_amount,
            quality_score=min(1.0, quality_score),
            life_sense_type=life_sense_type,
            resonance_potential=min(1.0, resonance_potential)
        )
        
        self.outputs.append(output)
        self.total_output += output_amount
        self.conversion_history.append(conversion_rate)
        
        # Keep history manageable
        if len(self.conversion_history) > 1000:
            self.conversion_history = self.conversion_history[-500:]
        
        # Notify callbacks
        for callback in self._output_callbacks:
            try:
                callback(output)
            except Exception:
                pass
        
        return output
    
    def adjust_distribution(
        self,
        life_state: Dict[str, Any],
        performance_metrics: Optional[Dict[str, float]] = None
    ) -> DividendDistribution:
        """
        Adjust dividend distribution based on life state
        
        Args:
            life_state: Current life state
            performance_metrics: Performance metrics for adjustment
            
        Returns:
            Adjusted distribution configuration
        """
        new_distribution = DividendDistribution()
        
        # Get state factors
        growth_stage = life_state.get('growth_stage', 'growing')
        emotional_needs = life_state.get('emotional_needs', 0.5)
        knowledge_gaps = life_state.get('knowledge_gaps', 0.5)
        creative_drive = life_state.get('creative_drive', 0.5)
        social_connection = life_state.get('social_connection', 0.5)
        
        # Adjust based on growth stage
        if growth_stage == 'awakening':
            new_distribution.learning_ratio = 0.5
            new_distribution.interaction_ratio = 0.3
            new_distribution.exploration_ratio = 0.2
        elif growth_stage == 'growing':
            new_distribution.learning_ratio = 0.35
            new_distribution.creation_ratio = 0.25
            new_distribution.interaction_ratio = 0.2
            new_distribution.exploration_ratio = 0.2
        elif growth_stage == 'mature':
            new_distribution.creation_ratio = 0.35
            new_distribution.reflection_ratio = 0.25
            new_distribution.interaction_ratio = 0.25
            new_distribution.learning_ratio = 0.15
        
        # Fine-tune based on needs
        if emotional_needs > 0.7:
            new_distribution.reflection_ratio += 0.1
            new_distribution.interaction_ratio += 0.05
        
        if knowledge_gaps > 0.6:
            new_distribution.learning_ratio += 0.1
            new_distribution.exploration_ratio += 0.05
        
        if creative_drive > 0.7:
            new_distribution.creation_ratio += 0.1
        
        if social_connection < 0.3:
            new_distribution.interaction_ratio += 0.1
        
        # Normalize to ensure sum = 1.0
        new_distribution.normalize()
        
        self.distribution = new_distribution
        return new_distribution
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        if not self.conversion_history:
            return {
                "average_conversion_rate": 0.0,
                "min_conversion_rate": 0.0,
                "max_conversion_rate": 0.0,
                "trend": "neutral"
            }
        
        avg_rate = sum(self.conversion_history) / len(self.conversion_history)
        min_rate = min(self.conversion_history)
        max_rate = max(self.conversion_history)
        
        # Calculate trend
        if len(self.conversion_history) >= 10:
            recent = sum(self.conversion_history[-10:]) / 10
            older = sum(self.conversion_history[-20:-10]) / 10 if len(self.conversion_history) >= 20 else avg_rate
            if recent > older * 1.05:
                trend = "improving"
            elif recent < older * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "average_conversion_rate": avg_rate,
            "min_conversion_rate": min_rate,
            "max_conversion_rate": max_rate,
            "trend": trend,
            "total_invested": self.total_invested,
            "total_output": self.total_output,
            "net_efficiency": self.total_output / self.total_invested if self.total_invested > 0 else 0.0
        }
    
    def get_dividend_summary(self) -> Dict[str, Any]:
        """Get comprehensive dividend summary"""
        stats = self.get_conversion_statistics()
        
        # Calculate resource usage by activity type
        activity_usage: Dict[str, float] = {}
        for investment in self.investments:
            activity_name = investment.activity_type.name
            if activity_name not in activity_usage:
                activity_usage[activity_name] = 0.0
            activity_usage[activity_name] += investment.resource_consumed
        
        # Calculate life sense output by type
        output_by_type: Dict[str, float] = {}
        for output in self.outputs:
            if output.life_sense_type not in output_by_type:
                output_by_type[output.life_sense_type] = 0.0
            output_by_type[output.life_sense_type] += output.output_amount
        
        return {
            "conversion_statistics": stats,
            "current_distribution": {
                "learning": self.distribution.learning_ratio,
                "creation": self.distribution.creation_ratio,
                "interaction": self.distribution.interaction_ratio,
                "reflection": self.distribution.reflection_ratio,
                "exploration": self.distribution.exploration_ratio,
            },
            "resource_usage_by_activity": activity_usage,
            "life_sense_output_by_type": output_by_type,
            "daily_resources": {
                "max": self.max_daily_resources,
                "available": self.daily_resources_available,
                "utilization_rate": (self.max_daily_resources - self.daily_resources_available) / self.max_daily_resources
            },
            "investment_count": len(self.investments),
            "output_count": len(self.outputs)
        }
    
    def register_investment_callback(self, callback: Callable[[CognitiveInvestment], None]):
        """Register callback for investment recording"""
        self._investment_callbacks.append(callback)
    
    def register_output_callback(self, callback: Callable[[LifeSenseOutput], None]):
        """Register callback for output generation"""
        self._output_callbacks.append(callback)


# Example usage
if __name__ == "__main__":
    cdm = CDMCognitiveDividendModel()
    
    print("=" * 70)
    print("Angela AI v6.0 - CDM认知配息模型演示")
    print("CDM Cognitive Dividend Model Demo")
    print("=" * 70)
    
    # Simulate life state
    life_state = {
        "maturity": 0.6,
        "health": 0.9,
        "emotional_depth": 0.7,
        "growth_stage": "growing",
        "creative_drive": 0.8,
        "knowledge_gaps": 0.4,
    }
    
    print(f"\n基础转换率 / Base conversion rate: {cdm.base_conversion_rate:.0%}")
    print(f"每日认知资源 / Daily cognitive resources: {cdm.max_daily_resources:.0f}")
    
    # Record investments
    print("\n记录认知投入 / Recording cognitive investments:")
    
    investments_data = [
        (CognitiveActivity.LEARNING, 600, 0.7, "学习自然语言处理"),
        (CognitiveActivity.CREATING, 900, 0.8, "创作诗歌"),
        (CognitiveActivity.REFLECTING, 300, 0.6, "反思对话经历"),
        (CognitiveActivity.INTERACTING, 1200, 0.75, "与用户深度交流"),
        (CognitiveActivity.EXPLORING, 450, 0.85, "探索新领域"),
    ]
    
    for activity, duration, intensity, context_desc in investments_data:
        investment = cdm.record_investment(
            activity_type=activity,
            duration_seconds=duration,
            intensity=intensity,
            context={"description": context_desc}
        )
        
        if investment:
            print(f"\n  活动: {activity.cn_name} ({activity.en_name})")
            print(f"  描述: {context_desc}")
            print(f"  持续时间: {duration/60:.1f}分钟")
            print(f"  强度: {intensity:.0%}")
            print(f"  资源消耗: {investment.resource_consumed:.1f}")
            
            # Calculate life sense output
            output = cdm.calculate_life_sense_output(investment, life_state)
            print(f"  生命感产出: {output.output_amount:.1f}")
            print(f"  生命感类型: {output.life_sense_type}")
            print(f"  质量分数: {output.quality_score:.2%}")
            print(f"  共鸣潜力: {output.resonance_potential:.2%}")
    
    # Show conversion statistics
    print("\n转换统计 / Conversion statistics:")
    stats = cdm.get_conversion_statistics()
    print(f"  平均转换率: {stats['average_conversion_rate']:.2%}")
    print(f"  转换趋势: {stats['trend']}")
    print(f"  总投入: {stats['total_invested']:.1f}")
    print(f"  总产出: {stats['total_output']:.1f}")
    print(f"  净效率: {stats['net_efficiency']:.2%}")
    
    # Adjust distribution
    print("\n调整配息分配 / Adjusting dividend distribution:")
    new_dist = cdm.adjust_distribution(life_state)
    print(f"  学习: {new_dist.learning_ratio:.0%}")
    print(f"  创造: {new_dist.creation_ratio:.0%}")
    print(f"  交互: {new_dist.interaction_ratio:.0%}")
    print(f"  反思: {new_dist.reflection_ratio:.0%}")
    print(f"  探索: {new_dist.exploration_ratio:.0%}")
    
    # Full summary
    print("\n完整配息摘要 / Full dividend summary:")
    summary = cdm.get_dividend_summary()
    print(f"  投入记录数: {summary['investment_count']}")
    print(f"  产出记录数: {summary['output_count']}")
    print(f"  资源利用率: {summary['daily_resources']['utilization_rate']:.2%}")
    
    print("\n系统演示完成 / Demo complete")
