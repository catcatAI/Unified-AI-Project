"""
Angela AI v6.0 - Multidimensional Trigger System
多维度行为触发器

Evaluates triggers across multiple dimensions (time, environment, emotion, physiology)
to determine which behaviors should be activated.

Features:
- Multi-dimensional trigger evaluation
- Time-based triggers (hour, day, season)
- Environment triggers (desktop state, weather, light)
- Emotion triggers (current mood, arousal)
- Physiology triggers (hormones, arousal, fatigue)

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
logger = logging.getLogger(__name__)


class TriggerDimension(Enum):
    """触发维度 / Trigger dimensions"""
    TIME = ("时间", "Time-based triggers")
    ENVIRONMENT = ("环境", "Environment triggers")
    EMOTION = ("情绪", "Emotional triggers")
    PHYSIOLOGY = ("生理", "Physiological triggers")
    SOCIAL = ("社交", "Social triggers")
    COGNITIVE = ("认知", "Cognitive triggers")
    RANDOM = ("随机", "Random triggers")


@dataclass
class DimensionValue:
    """维度值 / Dimension value"""
    dimension: TriggerDimension
    value: float  # 0-1 normalized
    raw_value: Any  # Original value
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TriggerCondition:
    """触发条件 / Trigger condition"""
    dimension: TriggerDimension
    operator: str  # eq, gt, lt, gte, lte, range
    threshold: float
    weight: float = 1.0  # Importance weight
    cooldown: float = 0.0  # Seconds
    last_triggered: Optional[datetime] = None
    
    def evaluate(self, value: DimensionValue) -> float:
        """
        Evaluate condition against dimension value
        Returns match score 0-1
        """
        # Check cooldown
        if self.last_triggered:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown:
                return 0.0
        
        if value.dimension != self.dimension:
            return 0.0
        
        # Calculate match based on operator
        match_score = 0.0
        
        if self.operator == "eq":
            match_score = 1.0 if abs(value.value - self.threshold) < 0.1 else 0.0
        elif self.operator == "gt":
            match_score = 1.0 if value.value > self.threshold else max(0, value.value / self.threshold)
        elif self.operator == "lt":
            match_score = 1.0 if value.value < self.threshold else max(0, (1 - value.value) / (1 - self.threshold))
        elif self.operator == "gte":
            match_score = min(1.0, value.value / self.threshold) if self.threshold > 0 else 1.0
        elif self.operator == "lte":
            match_score = 1.0 if value.value <= self.threshold else max(0, 1 - (value.value - self.threshold) / 0.3)
        elif self.operator == "range":
            # Threshold represents center of range
            range_size = 0.2  # +/- 0.1
            distance = abs(value.value - self.threshold)
            match_score = max(0, 1 - distance / range_size)
        
        return match_score * self.weight


@dataclass
class MultidimensionalTrigger:
    """多维度触发器 / Multidimensional trigger"""
    trigger_id: str
    name: str
    behavior_id: str
    conditions: List[TriggerCondition]
    min_score: float = 0.5  # Minimum score to trigger
    priority: int = 0
    
    def evaluate(self, dimension_values: List[DimensionValue]) -> float:
        """
        Evaluate trigger against all dimension values
        Returns total score 0-1
        """
        if not self.conditions:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for condition in self.conditions:
            # Find matching dimension value
            for value in dimension_values:
                if value.dimension == condition.dimension:
                    score = condition.evaluate(value)
                    total_score += score
                    total_weight += condition.weight
                    break
        
        if total_weight > 0:
            normalized_score = total_score / total_weight
            
            # Mark triggered conditions
            if normalized_score >= self.min_score:
                for condition in self.conditions:
                    condition.last_triggered = datetime.now()
            
            return normalized_score
        
        return 0.0


class MultidimensionalTriggerSystem:
    """
    多维度行为触发系统主类 / Main multidimensional trigger system class
    
    Evaluates triggers across multiple dimensions to determine appropriate
    behaviors for Angela based on current context.
    
    Attributes:
        triggers: List of registered triggers
        dimension_values: Current values for each dimension
        evaluation_interval: How often to evaluate triggers
    
    Example:
        >>> trigger_system = MultidimensionalTriggerSystem()
        >>> await trigger_system.initialize()
        >>> 
        >>> # Update dimension values
        >>> trigger_system.update_dimension(
        ...     TriggerDimension.TIME,
        ...     0.5,  # Noon (0.5 of day)
        ...     raw_value=12.0  # 12:00
        ... )
        >>> 
        >>> # Evaluate triggers
        >>> results = trigger_system.evaluate_all()
        >>> for trigger_id, score in results:
        ...     if score > 0.7:
        ...         print(f"Trigger {trigger_id}: {score:.2f}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Triggers
        self.triggers: List[MultidimensionalTrigger] = []
        
        # Dimension tracking
        self.dimension_values: Dict[TriggerDimension, DimensionValue] = {}
        
        # Configuration
        self.evaluation_interval: float = self.config.get("evaluation_interval", 1.0)
        
        # Running state
        self._running = False
        self._evaluation_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._trigger_callbacks: Dict[str, List[Callable[[float], None]]] = {}
        self._dimension_change_callbacks: Dict[TriggerDimension, List[Callable[[DimensionValue], None]]] = {}
        
        # Initialize with default triggers
        self._initialize_default_triggers()
    
    def _initialize_default_triggers(self):
        """Initialize default triggers for common behaviors"""
        
        # Morning greeting trigger
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="morning_greeting",
            name="Morning Greeting",
            behavior_id="greeting_wave",
            conditions=[
                TriggerCondition(TriggerDimension.TIME, "range", 0.25, weight=2.0, cooldown=3600),  # ~6am
                TriggerCondition(TriggerDimension.EMOTION, "gte", 0.3, weight=1.0),
            ],
            min_score=0.6,
            priority=5
        ))
        
        # Sleepy evening behavior
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="evening_sleepy",
            name="Evening Sleepy",
            behavior_id="idle_yawning",
            conditions=[
                TriggerCondition(TriggerDimension.TIME, "gte", 0.8, weight=2.0),  # Evening
                TriggerCondition(TriggerDimension.PHYSIOLOGY, "lte", 0.4, weight=1.5),  # Low energy
            ],
            min_score=0.5,
            priority=3
        ))
        
        # Happy celebration trigger
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="happy_celebration",
            name="Happy Celebration",
            behavior_id="celebration_dance",
            conditions=[
                TriggerCondition(TriggerDimension.EMOTION, "gte", 0.8, weight=2.0),  # Very happy
                TriggerCondition(TriggerDimension.SOCIAL, "gte", 0.5, weight=1.0),  # Social context
            ],
            min_score=0.7,
            priority=8
        ))
        
        # Stress relief trigger
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="stress_relief",
            name="Stress Relief",
            behavior_id="comforting_gesture",
            conditions=[
                TriggerCondition(TriggerDimension.EMOTION, "lte", 0.3, weight=2.0),  # Low mood
                TriggerCondition(TriggerDimension.PHYSIOLOGY, "gte", 0.7, weight=1.5),  # High arousal
            ],
            min_score=0.6,
            priority=9
        ))
        
        # Idle stretch trigger
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="idle_stretch",
            name="Idle Stretch",
            behavior_id="idle_stretching",
            conditions=[
                TriggerCondition(TriggerDimension.TIME, "gte", 0.5, weight=1.0),  # Been idle
                TriggerCondition(TriggerDimension.PHYSIOLOGY, "range", 0.5, weight=1.0),  # Normal energy
            ],
            min_score=0.4,
            priority=2
        ))
        
        # Surprise reaction trigger
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="surprise_reaction",
            name="Surprise Reaction",
            behavior_id="surprise_reaction",
            conditions=[
                TriggerCondition(TriggerDimension.ENVIRONMENT, "gte", 0.8, weight=2.0),  # Sudden change
                TriggerCondition(TriggerDimension.COGNITIVE, "gte", 0.6, weight=1.0),  # Alert
            ],
            min_score=0.7,
            priority=10
        ))
        
        # Attention seeking trigger
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="attention_seek",
            name="Attention Seeking",
            behavior_id="attention_seek",
            conditions=[
                TriggerCondition(TriggerDimension.SOCIAL, "lte", 0.2, weight=2.0, cooldown=180),  # Lonely
                TriggerCondition(TriggerDimension.EMOTION, "gte", 0.4, weight=1.0),  # Wants interaction
            ],
            min_score=0.5,
            priority=4
        ))
        
        # Random playful behavior
        self.add_trigger(MultidimensionalTrigger(
            trigger_id="random_playful",
            name="Random Playful",
            behavior_id="playful_wink",
            conditions=[
                TriggerCondition(TriggerDimension.RANDOM, "gte", 0.95, weight=2.0, cooldown=300),  # Rare random
                TriggerCondition(TriggerDimension.EMOTION, "gte", 0.5, weight=1.0),  # Good mood
            ],
            min_score=0.8,
            priority=3
        ))
    
    async def initialize(self):
        """Initialize the trigger system"""
        self._running = True
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
    
    async def shutdown(self):
        """Shutdown the trigger system"""
        self._running = False
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
    
    async def _evaluation_loop(self):
        """Background evaluation loop"""
        while self._running:
            await self._update_time_dimension()
            await self._update_random_dimension()
            await asyncio.sleep(self.evaluation_interval)
    
    async def _update_time_dimension(self):
        """Update time-based dimension"""
        now = datetime.now()
        
        # Day progress (0-1)
        seconds_in_day = now.hour * 3600 + now.minute * 60 + now.second
        day_progress = seconds_in_day / 86400.0
        
        self.update_dimension(TriggerDimension.TIME, day_progress, raw_value=now)
    
    async def _update_random_dimension(self):
        """Update random dimension"""
        import random
        self.update_dimension(TriggerDimension.RANDOM, random.random(), raw_value=None)
    
    def add_trigger(self, trigger: MultidimensionalTrigger):
        """Add a new trigger"""
        self.triggers.append(trigger)
        
        # Sort by priority
        self.triggers.sort(key=lambda t: t.priority, reverse=True)
    
    def remove_trigger(self, trigger_id: str) -> bool:
        """Remove a trigger by ID"""
        for i, trigger in enumerate(self.triggers):
            if trigger.trigger_id == trigger_id:
                self.triggers.pop(i)
                return True
        return False
    
    def update_dimension(
        self, 
        dimension: TriggerDimension, 
        value: float,
        raw_value: Any = None
    ):
        """
        Update a dimension value
        
        Args:
            dimension: Dimension to update
            value: Normalized value (0-1)
            raw_value: Original unnormalized value
        """
        old_value = self.dimension_values.get(dimension)
        
        self.dimension_values[dimension] = DimensionValue(
            dimension=dimension,
            value=max(0.0, min(1.0, value)),
            raw_value=raw_value
        )
        
        # Notify callbacks
        if dimension in self._dimension_change_callbacks:
            for callback in self._dimension_change_callbacks[dimension]:
                try:
                    callback(self.dimension_values[dimension])
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

    
    def update_dimensions(self, values: Dict[TriggerDimension, Tuple[float, Any]]):
        """Update multiple dimensions at once"""
        for dimension, (value, raw) in values.items():
            self.update_dimension(dimension, value, raw)
    
    def evaluate_all(self) -> List[Tuple[str, float]]:
        """
        Evaluate all triggers against current dimension values
        
        Returns:
            List of (trigger_id, score) tuples, sorted by score
        """
        results = []
        dimension_values = list(self.dimension_values.values())
        
        for trigger in self.triggers:
            score = trigger.evaluate(dimension_values)
            if score >= trigger.min_score:
                results.append((trigger.trigger_id, score))
                
                # Notify callbacks
                if trigger.trigger_id in self._trigger_callbacks:
                    for callback in self._trigger_callbacks[trigger.trigger_id]:
                        try:
                            callback(score)
                        except Exception as e:
                            logger.error(f'Error in {__name__}: {e}', exc_info=True)
                            pass

        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def evaluate_trigger(self, trigger_id: str) -> float:
        """Evaluate a specific trigger"""
        for trigger in self.triggers:
            if trigger.trigger_id == trigger_id:
                dimension_values = list(self.dimension_values.values())
                return trigger.evaluate(dimension_values)
        return 0.0
    
    def get_triggered_behaviors(self, threshold: float = 0.5) -> List[Tuple[str, str, float]]:
        """
        Get list of behaviors that should trigger
        
        Returns:
            List of (behavior_id, trigger_name, score) tuples
        """
        results = []
        dimension_values = list(self.dimension_values.values())
        
        for trigger in self.triggers:
            score = trigger.evaluate(dimension_values)
            if score >= max(threshold, trigger.min_score):
                results.append((trigger.behavior_id, trigger.name, score))
        
        # Sort by score
        results.sort(key=lambda x: x[2], reverse=True)
        return results
    
    def register_trigger_callback(self, trigger_id: str, callback: Callable[[float], None]):
        """Register callback for when a trigger is evaluated"""
        if trigger_id not in self._trigger_callbacks:
            self._trigger_callbacks[trigger_id] = []
        self._trigger_callbacks[trigger_id].append(callback)
    
    def register_dimension_callback(
        self, 
        dimension: TriggerDimension, 
        callback: Callable[[DimensionValue], None]
    ):
        """Register callback for dimension value changes"""
        if dimension not in self._dimension_change_callbacks:
            self._dimension_change_callbacks[dimension] = []
        self._dimension_change_callbacks[dimension].append(callback)
    
    def get_dimension_value(self, dimension: TriggerDimension) -> Optional[DimensionValue]:
        """Get current value for a dimension"""
        return self.dimension_values.get(dimension)
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system summary"""
        return {
            "registered_triggers": len(self.triggers),
            "active_dimensions": len(self.dimension_values),
            "dimension_values": {
                dim.value[0]: val.value
                for dim, val in self.dimension_values.items()
            },
            "evaluation_interval": self.evaluation_interval,
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        trigger_system = MultidimensionalTriggerSystem()
        await trigger_system.initialize()
        
        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 多维度触发器系统演示")
        logger.info("Multidimensional Trigger System Demo")
        logger.info("=" * 60)
        
        # Update dimensions
        logger.info("\n更新维度值 / Updating dimension values:")
        trigger_system.update_dimension(TriggerDimension.TIME, 0.25)  # Morning
        trigger_system.update_dimension(TriggerDimension.EMOTION, 0.8)  # Happy
        trigger_system.update_dimension(TriggerDimension.PHYSIOLOGY, 0.6)  # Normal energy
        trigger_system.update_dimension(TriggerDimension.SOCIAL, 0.7)  # Social
        
        for dim in [TriggerDimension.TIME, TriggerDimension.EMOTION, 
                    TriggerDimension.PHYSIOLOGY, TriggerDimension.SOCIAL]:
            val = trigger_system.get_dimension_value(dim)
            if val:
                logger.info(f"  {dim.value[0]}: {val.value:.2f}")
        
        # Evaluate triggers
        logger.info("\n评估触发器 / Evaluating triggers:")
        results = trigger_system.evaluate_all()
        for trigger_id, score in results[:5]:
            logger.info(f"  {trigger_id}: {score:.2f}")
        
        # Get triggered behaviors
        logger.info("\n触发的行为 / Triggered behaviors:")
        behaviors = trigger_system.get_triggered_behaviors()
        for behavior_id, name, score in behaviors[:5]:
            logger.info(f"  {behavior_id} ({name}): {score:.2f}")
        
        # System summary
        logger.info("\n系统摘要 / System summary:")
        summary = trigger_system.get_system_summary()
        logger.info(f"  注册触发器: {summary['registered_triggers']}")
        logger.info(f"  活跃维度: {summary['active_dimensions']}")
        
        await trigger_system.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
