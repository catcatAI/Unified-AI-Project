"""
Angela AI v6.0 - Extended Behavior Library
扩展行为库

Defines 25+ pre-defined behaviors with triggers, parameters, and execution logic.
Behaviors range from basic idle animations to complex social interactions.

Features:
- 25+ predefined behaviors
- Behavior triggering conditions
- Configurable behavior parameters
- Behavior priority and interruption

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.system.config.magic_numbers import behavior_threshold as _bt

logger = logging.getLogger(__name__)


class BehaviorCategory(Enum):
    """行为类别 / Behavior categories"""

    IDLE = ("待机", "Idle behaviors")
    SOCIAL = ("社交", "Social interactions")
    REACTION = ("反应", "Reactive behaviors")
    EXPRESSION = ("表达", "Emotional expressions")
    MOVEMENT = ("移动", "Movement behaviors")
    SPECIAL = ("特殊", "Special behaviors")


class BehaviorPriority(Enum):
    """行为优先级 / Behavior priorities"""

    CRITICAL = 0  # Must execute immediately
    HIGH = 1  # Interrupt current behavior
    NORMAL = 2  # Queue after current
    LOW = 3  # Only when idle
    BACKGROUND = 4  # Ambient, can be interrupted


@dataclass
class BehaviorTrigger:
    """行为触发条件 / Behavior trigger condition"""

    trigger_type: str  # time, emotion, stimulus, random, proximity
    condition: str  # specific condition
    threshold: float  # threshold value
    cooldown: float  # seconds between triggers
    last_triggered: Optional[datetime] = None

    def can_trigger(self) -> bool:
        """Check if trigger is ready (cooldown elapsed)"""
        if self.last_triggered is None:
            return True
        elapsed = (datetime.now() - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown

    def mark_triggered(self) -> None:
        """Mark trigger as just fired"""
        self.last_triggered = datetime.now()


@dataclass
class BehaviorDefinition:
    """行为定义 / Behavior definition"""

    behavior_id: str
    name: str
    name_cn: str
    category: BehaviorCategory
    priority: BehaviorPriority
    duration: float  # seconds, 0 = indefinite
    triggers: List[BehaviorTrigger] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    interruptible: bool = True
    loop: bool = False


class ExtendedBehaviorLibrary:
    """
    扩展行为库主类 / Main extended behavior library class

    Manages Angela's behavior repertoire with 25+ predefined behaviors,
    including triggers, parameters, and execution logic.

    Attributes:
        behaviors: Dictionary of all registered behaviors
        active_behavior: Currently executing behavior
        behavior_queue: Queue of pending behaviors
        default_behavior: Fallback behavior when idle

    Example:
        >>> library = ExtendedBehaviorLibrary()
        >>> await library.initialize()
        >>>
        >>> # Get behavior by ID
        >>> behavior = library.get_behavior("idle_breathing")
        >>> print(f"Behavior: {behavior.name_cn}")
        >>>
        >>> # Check triggers
        >>> triggerable = library.check_triggers(context={"time": 10.5})
        >>> for behavior in triggerable:
        ...     print(f"Can trigger: {behavior.name}")
        >>>
        >>> # Start behavior
        >>> await library.start_behavior("greeting_wave")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Behavior storage
        self.behaviors: Dict[str, BehaviorDefinition] = {}

        # Execution state
        self.active_behavior: Optional[BehaviorDefinition] = None
        self.behavior_queue: List[BehaviorDefinition] = []
        self.default_behavior_id: str = "idle_breathing"

        # Running state
        self._running = False

        # Callbacks
        self._behavior_start_callbacks: Dict[str, List[Callable[[], None]]] = {}
        self._behavior_end_callbacks: Dict[str, List[Callable[[], None]]] = {}

        # Dynamic Parameters Integration
        self._dynamic_params_manager: Optional[Any] = None
        self._dynamic_params_enabled: bool = self.config.get("enable_dynamic_params", True)

        # Initialize built-in behaviors
        self._initialize_behaviors()

    async def initialize(self) -> None:
        """Initialize the behavior library"""
        self._running = True

    async def shutdown(self) -> None:
        """Shutdown the behavior library"""
        self._running = False
        self.active_behavior = None
        self.behavior_queue.clear()

    def set_dynamic_params_manager(self, manager: Any) -> None:
        """Set the DynamicThresholdManager for dynamic threshold integration"""
        self._dynamic_params_manager = manager

    def _get_dynamic_threshold(
        self, param_name: str, default_value: float, context: Optional[Dict[str, float]] = None
    ) -> float:
        """Get dynamic threshold value from manager or return default"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter(param_name, context)
        return default_value

    def _get_emotion_threshold(
        self, emotion_type: str = "happiness", context: Optional[Dict[str, float]] = None
    ) -> float:
        """Get dynamic emotion threshold"""
        param_map = {
            "happiness": "emotion_happiness_threshold",
            "joy": "emotion_happiness_threshold",
            "sadness": "emotion_sadness_threshold",
            "anger": "emotion_anger_threshold",
        }
        param_name = param_map.get(emotion_type, "emotion_happiness_threshold")
        return self._get_dynamic_threshold(param_name, 0.6, context)

    def _get_social_threshold(self, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic social initiative threshold"""
        return self._get_dynamic_threshold("social_initiative_threshold", 0.5, context)

    def _initialize_behaviors(self) -> None:
        """Initialize all 25+ predefined behaviors from JSON data file"""
        import json
        import os
        data_path = os.path.join(os.path.dirname(__file__), "behaviors_data.json")
        with open(data_path, "r", encoding="utf-8") as f:
            behaviors = json.load(f)
        for bhv in behaviors:
            bhv["category"] = BehaviorCategory[bhv["category"]]
            bhv["priority"] = BehaviorPriority[bhv["priority"]]
            bhv["triggers"] = [BehaviorTrigger(**t) for t in bhv.get("triggers", [])]
            self._add_behavior(BehaviorDefinition(**bhv))

    def _add_behavior(self, behavior: BehaviorDefinition) -> None:
        """Add a behavior to the library"""
        self.behaviors[behavior.behavior_id] = behavior

    def get_behavior(self, behavior_id: str) -> Optional[BehaviorDefinition]:
        """Get a behavior by ID"""
        return self.behaviors.get(behavior_id)

    def get_behaviors_by_category(self, category: BehaviorCategory) -> List[BehaviorDefinition]:
        """Get all behaviors in a category"""
        return [b for b in self.behaviors.values() if b.category == category]

    def check_triggers(self, context: Dict[str, Any]) -> List[BehaviorDefinition]:
        """
        Check which behaviors can be triggered based on context
        Uses dynamic thresholds when available

        Args:
            context: Current context containing triggers like:
                - time: current time
                - emotion: current emotional state
                - stimulus: recent stimuli
                - proximity: proximity data

        Returns:
            List of triggerable behaviors
        """
        triggerable = []

        # Build context for dynamic parameter evaluation
        param_context = {}
        if "emotion" in context and isinstance(context["emotion"], (int, float)):
            param_context["mood"] = context["emotion"]
        if "energy" in context:
            param_context["energy"] = context["energy"]

        for behavior in self.behaviors.values():
            for trigger in behavior.triggers:
                if not trigger.can_trigger():
                    continue

                # Check if context matches trigger
                if trigger.trigger_type in context:
                    value = context[trigger.trigger_type]

                    # Get dynamic threshold based on trigger type
                    if trigger.trigger_type == "emotion":
                        dynamic_threshold = self._get_emotion_threshold(
                            emotion_type=trigger.condition, context=param_context
                        )
                    elif trigger.trigger_type == "proximity" or trigger.trigger_type == "stimulus":
                        # For social behaviors, use social initiative threshold
                        if behavior.category == BehaviorCategory.SOCIAL:
                            dynamic_threshold = self._get_social_threshold(param_context)
                        else:
                            dynamic_threshold = trigger.threshold
                    else:
                        dynamic_threshold = trigger.threshold

                    if isinstance(value, (int, float)) and value >= dynamic_threshold:
                        triggerable.append(behavior)
                        trigger.mark_triggered()
                        break
                    elif value == trigger.condition or value == dynamic_threshold:
                        triggerable.append(behavior)
                        trigger.mark_triggered()
                        break

        # Sort by priority
        triggerable.sort(key=lambda b: b.priority.value)
        return triggerable

    async def start_behavior(self, behavior_id: str) -> bool:
        """
        Start a behavior

        Args:
            behavior_id: Behavior to start

        Returns:
            True if started successfully
        """
        behavior = self.get_behavior(behavior_id)
        if not behavior:
            return False

        # Check if we should interrupt current behavior
        if self.active_behavior:
            if not self.active_behavior.interruptible:
                if behavior.priority.value >= self.active_behavior.priority.value:
                    # Queue instead of interrupting
                    self.behavior_queue.append(behavior)
                    return False

            # End current behavior
            await self._end_behavior(self.active_behavior)

        # Start new behavior
        self.active_behavior = behavior

        # Notify callbacks
        if behavior_id in self._behavior_start_callbacks:
            for callback in self._behavior_start_callbacks[behavior_id]:
                try:
                    callback()
                except Exception as e:  # broad exception acceptable: callback errors should not break behavior execution
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)

        return True

    async def _end_behavior(self, behavior: BehaviorDefinition) -> None:
        """End a behavior"""
        # Notify callbacks
        if behavior.behavior_id in self._behavior_end_callbacks:
            for callback in self._behavior_end_callbacks[behavior.behavior_id]:
                try:
                    callback()
                except Exception as e:  # broad exception acceptable: callback errors should not break behavior cleanup
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)

        self.active_behavior = None

    def queue_behavior(self, behavior_id: str) -> bool:
        """Queue a behavior to execute after current"""
        behavior = self.get_behavior(behavior_id)
        if behavior:
            self.behavior_queue.append(behavior)
            return True
        return False

    def get_next_queued_behavior(self) -> Optional[BehaviorDefinition]:
        """Get next behavior from queue"""
        if self.behavior_queue:
            # Sort by priority
            self.behavior_queue.sort(key=lambda b: b.priority.value)
            return self.behavior_queue.pop(0)
        return None

    def register_behavior_start_callback(self, behavior_id: str, callback: Callable[[], None]) -> None:
        """Register callback for when a behavior starts"""
        if behavior_id not in self._behavior_start_callbacks:
            self._behavior_start_callbacks[behavior_id] = []
        self._behavior_start_callbacks[behavior_id].append(callback)

    def register_behavior_end_callback(self, behavior_id: str, callback: Callable[[], None]) -> None:
        """Register callback for when a behavior ends"""
        if behavior_id not in self._behavior_end_callbacks:
            self._behavior_end_callbacks[behavior_id] = []
        self._behavior_end_callbacks[behavior_id].append(callback)

    def get_library_summary(self) -> Dict[str, Any]:
        """Get library summary statistics"""
        return {
            "total_behaviors": len(self.behaviors),
            "by_category": {
                cat.name: len(self.get_behaviors_by_category(cat)) for cat in BehaviorCategory
            },
            "active_behavior": self.active_behavior.behavior_id if self.active_behavior else None,
            "queued_behaviors": len(self.behavior_queue),
        }

    def get_default_behavior(self) -> Optional[BehaviorDefinition]:
        """Get default idle behavior"""
        return self.behaviors.get(self.default_behavior_id, self.behaviors.get("idle_breathing"))


# Example usage
if __name__ == "__main__":

    async def demo() -> None:
        """Run a demonstration."""
        library = ExtendedBehaviorLibrary()
        await library.initialize()

        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 扩展行为库演示")
        logger.info("Extended Behavior Library Demo")
        logger.info("=" * 60)

        # Show library summary
        logger.info("\n行为库摘要 / Library summary:")
        summary = library.get_library_summary()
        logger.info(f"  总行为数: {summary['total_behaviors']}")
        logger.info("  按类别分布:")
        for cat, count in summary["by_category"].items():
            logger.info(f"    {cat}: {count}")

        # Show some behaviors
        logger.info("\n示例行为 / Sample behaviors:")
        sample_ids = ["idle_breathing", "greeting_wave", "happy_smile", "surprise_reaction"]
        for bid in sample_ids:
            behavior = library.get_behavior(bid)
            if behavior:
                logger.info(f"  {behavior.name_cn} ({behavior.name})")
                logger.info(f"    类别: {behavior.category.value[0]}")
                logger.info(f"    优先级: {behavior.priority.name}")
                logger.info(
                    f"    时长: {behavior.duration}s" if behavior.duration > 0 else "    时长: 无限"
                )

        # Check triggers
        logger.info("\n触发检测 / Trigger checking:")
        context = {
            "time": 35.0,
            "emotion": 0.7,
            "proximity": 1.0,
        }
        triggerable = library.check_triggers(context)
        logger.info(f"  可触发行为数: {len(triggerable)}")
        for b in triggerable[:3]:
            logger.info(f"    - {b.name_cn}")

        await library.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")

    asyncio.run(demo())
