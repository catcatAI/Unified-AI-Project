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
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import asyncio


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
    CRITICAL = 0    # Must execute immediately
    HIGH = 1        # Interrupt current behavior
    NORMAL = 2      # Queue after current
    LOW = 3         # Only when idle
    BACKGROUND = 4  # Ambient, can be interrupted


@dataclass
class BehaviorTrigger:
    """行为触发条件 / Behavior trigger condition"""
    trigger_type: str  # time, emotion, stimulus, random, proximity
    condition: str     # specific condition
    threshold: float   # threshold value
    cooldown: float    # seconds between triggers
    last_triggered: Optional[datetime] = None
    
    def can_trigger(self) -> bool:
        """Check if trigger is ready (cooldown elapsed)"""
        if self.last_triggered is None:
            return True
        elapsed = (datetime.now() - self.last_triggered).total_seconds()
        return elapsed >= self.cooldown
    
    def mark_triggered(self):
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
        self._dynamic_params_enabled: bool = self.config.get('enable_dynamic_params', True)
        
        # Initialize built-in behaviors
        self._initialize_behaviors()
    
    async def initialize(self):
        """Initialize the behavior library"""
        self._running = True
    
    async def shutdown(self):
        """Shutdown the behavior library"""
        self._running = False
        self.active_behavior = None
        self.behavior_queue.clear()
    
    def set_dynamic_params_manager(self, manager: Any):
        """Set the DynamicThresholdManager for dynamic threshold integration"""
        self._dynamic_params_manager = manager
    
    def _get_dynamic_threshold(self, param_name: str, default_value: float, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic threshold value from manager or return default"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter(param_name, context)
        return default_value
    
    def _get_emotion_threshold(self, emotion_type: str = "happiness", context: Optional[Dict[str, float]] = None) -> float:
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
    
    def _initialize_behaviors(self):
        """Initialize all 25+ predefined behaviors"""
        
        # === IDLE BEHAVIORS (待机行为) ===
        self._add_behavior(BehaviorDefinition(
            behavior_id="idle_breathing",
            name="Idle Breathing",
            name_cn="待机呼吸",
            category=BehaviorCategory.IDLE,
            priority=BehaviorPriority.BACKGROUND,
            duration=0,  # Indefinite
            loop=True,
            description="Subtle breathing animation while idle",
            interruptible=True
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="idle_blinking",
            name="Idle Blinking",
            name_cn="待机眨眼",
            category=BehaviorCategory.IDLE,
            priority=BehaviorPriority.BACKGROUND,
            duration=0.3,
            triggers=[
                BehaviorTrigger("random", "blink", threshold=0.3, cooldown=3.0)
            ],
            description="Random blinking while idle"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="idle_looking_around",
            name="Idle Looking Around",
            name_cn="待机环顾",
            category=BehaviorCategory.IDLE,
            priority=BehaviorPriority.BACKGROUND,
            duration=3.0,
            triggers=[
                BehaviorTrigger("random", "look_around", threshold=0.2, cooldown=10.0)
            ],
            description="Randomly look around when idle"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="idle_stretching",
            name="Idle Stretching",
            name_cn="待机伸懒腰",
            category=BehaviorCategory.IDLE,
            priority=BehaviorPriority.LOW,
            duration=4.0,
            triggers=[
                BehaviorTrigger("time", "idle_duration", threshold=30.0, cooldown=60.0)
            ],
            description="Stretch after being idle for a while"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="idle_yawning",
            name="Idle Yawning",
            name_cn="待机打哈欠",
            category=BehaviorCategory.IDLE,
            priority=BehaviorPriority.LOW,
            duration=3.0,
            triggers=[
                BehaviorTrigger("time", "low_activity", threshold=120.0, cooldown=300.0)
            ],
            description="Yawn when bored or tired"
        ))
        
        # === SOCIAL BEHAVIORS (社交行为) ===
        self._add_behavior(BehaviorDefinition(
            behavior_id="greeting_wave",
            name="Greeting Wave",
            name_cn="问候挥手",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.HIGH,
            duration=2.5,
            triggers=[
                BehaviorTrigger("proximity", "user_detected", threshold=1.0, cooldown=10.0)
            ],
            description="Wave hello when user approaches"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="greeting_bow",
            name="Greeting Bow",
            name_cn="问候鞠躬",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.HIGH,
            duration=2.0,
            triggers=[
                BehaviorTrigger("proximity", "user_detected", threshold=1.0, cooldown=10.0)
            ],
            description="Polite bow greeting"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="listening_nod",
            name="Listening Nod",
            name_cn="倾听点头",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.NORMAL,
            duration=0,
            loop=True,
            triggers=[
                BehaviorTrigger("stimulus", "user_speaking", threshold=1.0, cooldown=1.0)
            ],
            description="Nod while listening to user"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="thinking_pose",
            name="Thinking Pose",
            name_cn="思考姿势",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.NORMAL,
            duration=5.0,
            triggers=[
                BehaviorTrigger("stimulus", "processing", threshold=1.0, cooldown=5.0)
            ],
            description="Thinking pose while processing complex requests"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="encouraging_gesture",
            name="Encouraging Gesture",
            name_cn="鼓励手势",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.NORMAL,
            duration=2.0,
            triggers=[
                BehaviorTrigger("emotion", "empathy", threshold=0.6, cooldown=5.0)
            ],
            description="Encouraging gestures when user is struggling"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="celebration_dance",
            name="Celebration Dance",
            name_cn="庆祝舞蹈",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.HIGH,
            duration=5.0,
            triggers=[
                BehaviorTrigger("stimulus", "success", threshold=1.0, cooldown=30.0)
            ],
            description="Happy dance when user achieves something"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="comforting_gesture",
            name="Comforting Gesture",
            name_cn="安慰手势",
            category=BehaviorCategory.SOCIAL,
            priority=BehaviorPriority.HIGH,
            duration=4.0,
            triggers=[
                BehaviorTrigger("emotion", "sadness_detected", threshold=0.7, cooldown=10.0)
            ],
            description="Comforting gestures when user seems sad"
        ))
        
        # === REACTION BEHAVIORS (反应行为) ===
        self._add_behavior(BehaviorDefinition(
            behavior_id="surprise_reaction",
            name="Surprise Reaction",
            name_cn="惊讶反应",
            category=BehaviorCategory.REACTION,
            priority=BehaviorPriority.HIGH,
            duration=2.0,
            triggers=[
                BehaviorTrigger("stimulus", "sudden_change", threshold=1.0, cooldown=3.0)
            ],
            description="React with surprise to unexpected events"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="confused_tilt",
            name="Confused Head Tilt",
            name_cn="困惑歪头",
            category=BehaviorCategory.REACTION,
            priority=BehaviorPriority.NORMAL,
            duration=2.5,
            triggers=[
                BehaviorTrigger("stimulus", "unclear_input", threshold=1.0, cooldown=5.0)
            ],
            description="Head tilt when confused"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="attention_seek",
            name="Attention Seeking",
            name_cn="寻求注意",
            category=BehaviorCategory.REACTION,
            priority=BehaviorPriority.LOW,
            duration=3.0,
            triggers=[
                BehaviorTrigger("time", "no_interaction", threshold=300.0, cooldown=180.0)
            ],
            description="Subtle movements to get user's attention"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="follow_mouse",
            name="Follow Mouse",
            name_cn="跟随鼠标",
            category=BehaviorCategory.REACTION,
            priority=BehaviorPriority.NORMAL,
            duration=0,
            loop=True,
            triggers=[
                BehaviorTrigger("proximity", "mouse_nearby", threshold=1.0, cooldown=0.0)
            ],
            description="Follow mouse cursor with eyes/head"
        ))
        
        # === EXPRESSION BEHAVIORS (表达行为) ===
        self._add_behavior(BehaviorDefinition(
            behavior_id="happy_smile",
            name="Happy Smile",
            name_cn="开心微笑",
            category=BehaviorCategory.EXPRESSION,
            priority=BehaviorPriority.NORMAL,
            duration=3.0,
            triggers=[
                BehaviorTrigger("emotion", "joy", threshold=0.6, cooldown=5.0)
            ],
            description="Big happy smile"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="playful_wink",
            name="Playful Wink",
            name_cn="俏皮眨眼",
            category=BehaviorCategory.EXPRESSION,
            priority=BehaviorPriority.NORMAL,
            duration=1.0,
            triggers=[
                BehaviorTrigger("emotion", "playfulness", threshold=0.5, cooldown=10.0)
            ],
            description="Playful wink expression"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="shy_blush",
            name="Shy Blush",
            name_cn="害羞脸红",
            category=BehaviorCategory.EXPRESSION,
            priority=BehaviorPriority.NORMAL,
            duration=4.0,
            triggers=[
                BehaviorTrigger("emotion", "embarrassment", threshold=0.5, cooldown=15.0)
            ],
            description="Blushing when complimented or embarrassed"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="curious_look",
            name="Curious Look",
            name_cn="好奇观察",
            category=BehaviorCategory.EXPRESSION,
            priority=BehaviorPriority.NORMAL,
            duration=3.0,
            triggers=[
                BehaviorTrigger("stimulus", "novelty", threshold=0.7, cooldown=5.0)
            ],
            description="Curious expression when encountering something new"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="determined_expression",
            name="Determined Expression",
            name_cn="坚定表情",
            category=BehaviorCategory.EXPRESSION,
            priority=BehaviorPriority.NORMAL,
            duration=3.0,
            triggers=[
                BehaviorTrigger("stimulus", "challenge", threshold=0.8, cooldown=10.0)
            ],
            description="Determined expression when facing challenges"
        ))
        
        # === MOVEMENT BEHAVIORS (移动行为) ===
        self._add_behavior(BehaviorDefinition(
            behavior_id="bounce_idle",
            name="Idle Bounce",
            name_cn="待机弹跳",
            category=BehaviorCategory.MOVEMENT,
            priority=BehaviorPriority.BACKGROUND,
            duration=0,
            loop=True,
            triggers=[
                BehaviorTrigger("emotion", "energy", threshold=0.6, cooldown=0.0)
            ],
            description="Subtle bouncing when energetic"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="sway_gentle",
            name="Gentle Sway",
            name_cn="轻轻摇摆",
            category=BehaviorCategory.MOVEMENT,
            priority=BehaviorPriority.BACKGROUND,
            duration=0,
            loop=True,
            triggers=[
                BehaviorTrigger("emotion", "relaxation", threshold=0.5, cooldown=0.0)
            ],
            description="Gentle swaying when relaxed"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="approach_user",
            name="Approach User",
            name_cn="靠近用户",
            category=BehaviorCategory.MOVEMENT,
            priority=BehaviorPriority.NORMAL,
            duration=5.0,
            triggers=[
                BehaviorTrigger("emotion", "affection", threshold=0.7, cooldown=30.0)
            ],
            description="Move closer to user"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="avoid_obstacle",
            name="Avoid Obstacle",
            name_cn="避开障碍",
            category=BehaviorCategory.MOVEMENT,
            priority=BehaviorPriority.HIGH,
            duration=2.0,
            triggers=[
                BehaviorTrigger("stimulus", "collision", threshold=1.0, cooldown=1.0)
            ],
            description="Quick movement to avoid collision"
        ))
        
        # === SPECIAL BEHAVIORS (特殊行为) ===
        self._add_behavior(BehaviorDefinition(
            behavior_id="sleep_mode",
            name="Sleep Mode",
            name_cn="睡眠模式",
            category=BehaviorCategory.SPECIAL,
            priority=BehaviorPriority.CRITICAL,
            duration=0,
            loop=True,
            triggers=[
                BehaviorTrigger("time", "inactivity", threshold=600.0, cooldown=0.0)
            ],
            description="Enter sleep mode after long inactivity",
            interruptible=True
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="wake_up",
            name="Wake Up",
            name_cn="醒来",
            category=BehaviorCategory.SPECIAL,
            priority=BehaviorPriority.CRITICAL,
            duration=3.0,
            triggers=[
                BehaviorTrigger("stimulus", "user_activity", threshold=1.0, cooldown=0.0)
            ],
            description="Wake up from sleep mode"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="singing_performance",
            name="Singing Performance",
            name_cn="唱歌表演",
            category=BehaviorCategory.SPECIAL,
            priority=BehaviorPriority.NORMAL,
            duration=180.0,
            triggers=[
                BehaviorTrigger("stimulus", "user_request", threshold=1.0, cooldown=300.0)
            ],
            description="Full singing performance with lyrics"
        ))
        
        self._add_behavior(BehaviorDefinition(
            behavior_id="dance_performance",
            name="Dance Performance",
            name_cn="舞蹈表演",
            category=BehaviorCategory.SPECIAL,
            priority=BehaviorPriority.NORMAL,
            duration=60.0,
            triggers=[
                BehaviorTrigger("stimulus", "user_request", threshold=1.0, cooldown=300.0)
            ],
            description="Dance performance animation"
        ))
    
    def _add_behavior(self, behavior: BehaviorDefinition):
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
        if 'emotion' in context and isinstance(context['emotion'], (int, float)):
            param_context['mood'] = context['emotion']
        if 'energy' in context:
            param_context['energy'] = context['energy']
        
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
                            emotion_type=trigger.condition,
                            context=param_context
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
                except Exception:
                    pass
        
        return True
    
    async def _end_behavior(self, behavior: BehaviorDefinition):
        """End a behavior"""
        # Notify callbacks
        if behavior.behavior_id in self._behavior_end_callbacks:
            for callback in self._behavior_end_callbacks[behavior.behavior_id]:
                try:
                    callback()
                except Exception:
                    pass
        
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
    
    def register_behavior_start_callback(self, behavior_id: str, callback: Callable[[], None]):
        """Register callback for when a behavior starts"""
        if behavior_id not in self._behavior_start_callbacks:
            self._behavior_start_callbacks[behavior_id] = []
        self._behavior_start_callbacks[behavior_id].append(callback)
    
    def register_behavior_end_callback(self, behavior_id: str, callback: Callable[[], None]):
        """Register callback for when a behavior ends"""
        if behavior_id not in self._behavior_end_callbacks:
            self._behavior_end_callbacks[behavior_id] = []
        self._behavior_end_callbacks[behavior_id].append(callback)
    
    def get_library_summary(self) -> Dict[str, Any]:
        """Get library summary statistics"""
        return {
            "total_behaviors": len(self.behaviors),
            "by_category": {
                cat.name: len(self.get_behaviors_by_category(cat))
                for cat in BehaviorCategory
            },
            "active_behavior": self.active_behavior.behavior_id if self.active_behavior else None,
            "queued_behaviors": len(self.behavior_queue),
        }
    
    def get_default_behavior(self) -> Optional[BehaviorDefinition]:
        """Get default idle behavior"""
        return self.behaviors.get(
            self.default_behavior_id,
            self.behaviors.get("idle_breathing")
        )


# Example usage
if __name__ == "__main__":
    async def demo():
        library = ExtendedBehaviorLibrary()
        await library.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 扩展行为库演示")
        print("Extended Behavior Library Demo")
        print("=" * 60)
        
        # Show library summary
        print("\n行为库摘要 / Library summary:")
        summary = library.get_library_summary()
        print(f"  总行为数: {summary['total_behaviors']}")
        print("  按类别分布:")
        for cat, count in summary['by_category'].items():
            print(f"    {cat}: {count}")
        
        # Show some behaviors
        print("\n示例行为 / Sample behaviors:")
        sample_ids = ["idle_breathing", "greeting_wave", "happy_smile", "surprise_reaction"]
        for bid in sample_ids:
            behavior = library.get_behavior(bid)
            if behavior:
                print(f"  {behavior.name_cn} ({behavior.name})")
                print(f"    类别: {behavior.category.value[0]}")
                print(f"    优先级: {behavior.priority.name}")
                print(f"    时长: {behavior.duration}s" if behavior.duration > 0 else "    时长: 无限")
        
        # Check triggers
        print("\n触发检测 / Trigger checking:")
        context = {
            "time": 35.0,
            "emotion": 0.7,
            "proximity": 1.0,
        }
        triggerable = library.check_triggers(context)
        print(f"  可触发行为数: {len(triggerable)}")
        for b in triggerable[:3]:
            print(f"    - {b.name_cn}")
        
        await library.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
