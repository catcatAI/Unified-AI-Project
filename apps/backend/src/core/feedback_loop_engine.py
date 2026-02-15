"""
Angela AI v6.0 - Feedback Loop Engine
实时反馈循环引擎

The core real-time feedback loop system connecting perception and action.
Implements a complete perception-action cycle with multi-level feedback:
- Physiological layer (tactile → hormone → emotion)
- Cognitive layer (attention → thinking → decision)
- Emotional layer (stimulus → evaluation → expression)
- Social layer (interaction → relationship → trust)

Features:
- Real-time monitoring (16ms latency requirement)
- Multi-layer feedback system
- Closed-loop learning mechanism
- Integration with HSM/CDM for memory and learning updates
- Connection to all biological systems

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import uuid
import json
import time
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..action_execution_bridge import ActionExecutionBridge
    from .autonomous.desktop_presence import DesktopPresence
    from .autonomous.desktop_interaction import DesktopInteraction
    from .autonomous.audio_system import AudioSystem
    from .autonomous.action_executor import ActionExecutor
    from .real_time_monitor import RealTimeMonitor
    from .feedback_processor import FeedbackProcessor
    from .event_loop_system import EventLoopSystem


class FeedbackLayer(Enum):
    """反馈层级 / Feedback layers"""
    PHYSIOLOGICAL = ("生理层", "Physiological - Tactile, Hormone, Emotion")
    COGNITIVE = ("认知层", "Cognitive - Attention, Thinking, Decision")
    EMOTIONAL = ("情感层", "Emotional - Stimulus, Evaluation, Expression")
    SOCIAL = ("社交层", "Social - Interaction, Relationship, Trust")
    
    def __init__(self, cn_name: str, description: str):
        self.cn_name = cn_name
        self.description = description


class FeedbackType(Enum):
    """反馈类型 / Feedback types"""
    IMMEDIATE = ("即时反馈", "Immediate feedback during action")
    DELAYED = ("延迟反馈", "Delayed feedback after action completion")
    PREDICTIVE = ("预测反馈", "Predictive feedback before action")
    RETROSPECTIVE = ("回顾反馈", "Retrospective feedback for learning")


class PerceptionType(Enum):
    """感知类型 / Perception types monitored"""
    VOICE = ("语音", "Voice input from microphone")
    MOUSE = ("鼠标", "Mouse position and interaction")
    FILE_SYSTEM = ("文件系统", "File system changes")
    TIME = ("时间", "Time and schedule events")
    SYSTEM_STATE = ("系统状态", "System resource and health state")
    USER_ACTIVITY = ("用户活动", "User activity patterns")
    AUDIO_OUTPUT = ("音频输出", "Audio system state")
    VISUAL_OUTPUT = ("视觉输出", "Visual/Live2D state")


@dataclass
class PerceptionEvent:
    """感知事件 / Perception event from environment"""
    event_id: str
    perception_type: PerceptionType
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: int = 5  # 1-10, lower is higher priority
    processed: bool = False
    
    @classmethod
    def create(
        cls,
        perception_type: PerceptionType,
        source: str,
        data: Dict[str, Any],
        priority: int = 5
    ) -> PerceptionEvent:
        """Factory method to create perception event"""
        return cls(
            event_id=str(uuid.uuid4()),
            perception_type=perception_type,
            source=source,
            data=data,
            timestamp=datetime.now(),
            priority=priority
        )


@dataclass
class ActionDecision:
    """行动决策 / Action decision generated from perception"""
    decision_id: str
    trigger_event: str  # ID of triggering perception event
    action_type: str
    target: str
    urgency: float  # 0-1
    confidence: float  # 0-1
    parameters: Dict[str, Any]
    timestamp: datetime
    expected_outcome: Optional[str] = None


@dataclass
class FeedbackSignal:
    """反馈信号 / Feedback signal from action execution"""
    signal_id: str
    action_id: str
    layer: FeedbackLayer
    feedback_type: FeedbackType
    value: float  # Feedback intensity/value
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False


@dataclass
class LearningUpdate:
    """学习更新 / Learning update for HSM/CDM"""
    update_id: str
    source_action: str
    prediction_error: float  # Difference between prediction and actual
    performance_delta: float  # Change in performance
    strategy_adjustment: Dict[str, Any]
    timestamp: datetime
    hsm_update: Optional[Dict[str, Any]] = None
    cdm_update: Optional[Dict[str, Any]] = None


@dataclass
class PerceptionActionCycle:
    """感知-行动周期 / Complete perception-action cycle"""
    cycle_id: str
    perception_event: PerceptionEvent
    decision: Optional[ActionDecision] = None
    action_id: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    feedback_signals: List[FeedbackSignal] = field(default_factory=list)
    learning_update: Optional[LearningUpdate] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    latency_ms: float = 0.0


class FeedbackLoopEngine:
    """
    实时反馈循环引擎主类 / Main real-time feedback loop engine
    
    The core system that creates a continuous loop between perception and action.
    This is the key component connecting Angela's senses to her actions.
    
    Architecture:
    ```
    Perception → Cognitive Processing → Action Decision → Execution → Feedback → Learning
         ↑                                                                     ↓
         └────────────────── Next Cycle ←────────────────────────────────────┘
    ```
    
    Key Features:
    1. Real-time monitoring with 16ms latency target
    2. Multi-layer feedback system (Physiological, Cognitive, Emotional, Social)
    3. Closed-loop learning integrating with HSM/CDM
    4. Event-driven architecture with priority queue
    5. Comprehensive connection to all biological systems
    
    Example:
        >>> engine = FeedbackLoopEngine(
        ...     desktop_presence=desktop_presence,
        ...     desktop_interaction=desktop_interaction,
        ...     audio_system=audio_system,
        ...     action_bridge=action_bridge,
        ...     hsm=hsm,
        ...     cdm=cdm
        ... )
        >>> await engine.initialize()
        >>> 
        >>> # System automatically starts perception-action cycles
        >>> # Manual trigger example:
        >>> await engine.process_perception_event(
        ...     PerceptionEvent.create(
        ...         PerceptionType.MOUSE,
        ...         "desktop_presence",
        ...         {"position": {"x": 100, "y": 200}}
        ...     )
        ... )
    """
    
    def __init__(
        self,
        desktop_presence: Optional[Any] = None,
        desktop_interaction: Optional[Any] = None,
        audio_system: Optional[Any] = None,
        action_bridge: Optional[Any] = None,
        action_executor: Optional[Any] = None,
        hsm: Optional[Any] = None,
        cdm: Optional[Any] = None,
        temporal_evolution: Optional[Any] = None,
        real_time_monitor: Optional[Any] = None,
        feedback_processor: Optional[Any] = None,
        event_loop_system: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # System references
        self.desktop_presence = desktop_presence
        self.desktop_interaction = desktop_interaction
        self.audio_system = audio_system
        self.action_bridge = action_bridge
        self.action_executor = action_executor
        self.hsm = hsm
        self.cdm = cdm
        self.temporal_evolution = temporal_evolution
        
        # Sub-systems
        self.real_time_monitor = real_time_monitor
        self.feedback_processor = feedback_processor
        self.event_loop_system = event_loop_system
        
        # Cycle tracking
        self.active_cycles: Dict[str, PerceptionActionCycle] = {}
        self.completed_cycles: List[PerceptionActionCycle] = []
        self.max_completed_history = self.config.get("max_completed_history", 1000)
        
        # Running state
        self._running = False
        self._initialized = False
        self._main_loop_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.performance_metrics = {
            "cycles_completed": 0,
            "average_latency_ms": 0.0,
            "min_latency_ms": float('inf'),
            "max_latency_ms": 0.0,
            "feedback_processed": 0,
            "learning_updates": 0,
            "start_time": None
        }
        
        # Callbacks
        self._cycle_start_callbacks: List[Callable[[PerceptionActionCycle], None]] = []
        self._cycle_end_callbacks: List[Callable[[PerceptionActionCycle], None]] = []
        self._feedback_callbacks: Dict[FeedbackLayer, List[Callable[[FeedbackSignal], None]]] = {
            layer: [] for layer in FeedbackLayer
        }
        
        # Thresholds
        self.latency_threshold_ms = self.config.get("latency_threshold_ms", 16.0)
        self.feedback_sensitivity = self.config.get("feedback_sensitivity", 0.5)
    
    async def initialize(self):
        """Initialize the feedback loop engine and all subsystems"""
        if self._initialized:
            return
        
        logger.info("[FeedbackLoopEngine] Initializing real-time feedback loop system...")
        
        # Initialize sub-systems if not provided
        if not self.real_time_monitor:
            from real_time_monitor import RealTimeMonitor
            self.real_time_monitor = RealTimeMonitor(
                desktop_presence=self.desktop_presence,
                desktop_interaction=self.desktop_interaction,
                audio_system=self.audio_system
            )
        
        if not self.feedback_processor:
            from feedback_processor import FeedbackProcessor
            self.feedback_processor = FeedbackProcessor(
                hsm=self.hsm,
                cdm=self.cdm,
                feedback_loop_engine=self
            )
        
        if not self.event_loop_system:
            from event_loop_system import EventLoopSystem
            self.event_loop_system = EventLoopSystem(
                latency_target_ms=self.latency_threshold_ms
            )
        
        # Initialize all subsystems
        await self.real_time_monitor.initialize()
        await self.feedback_processor.initialize()
        await self.event_loop_system.initialize()
        
        # Register callbacks
        self._register_monitor_callbacks()
        self._register_bridge_callbacks()
        
        # Start main loop
        self._running = True
        self._main_loop_task = asyncio.create_task(self._main_loop())
        self.performance_metrics["start_time"] = datetime.now()
        
        self._initialized = True
        logger.info("[FeedbackLoopEngine] Initialization complete")
    
    async def shutdown(self):
        """Shutdown the feedback loop engine"""
        logger.info("[FeedbackLoopEngine] Shutting down...")
        
        self._running = False
        
        # Cancel main loop
        if self._main_loop_task:
            self._main_loop_task.cancel()
            try:
                await self._main_loop_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown subsystems
        if self.real_time_monitor:
            await self.real_time_monitor.shutdown()
        
        if self.feedback_processor:
            await self.feedback_processor.shutdown()
        
        if self.event_loop_system:
            await self.event_loop_system.shutdown()
        
        logger.info("[FeedbackLoopEngine] Shutdown complete")
    
    def _register_monitor_callbacks(self):
        """Register callbacks with the real-time monitor"""
        if self.real_time_monitor:
            self.real_time_monitor.register_callback(
                "mouse_position",
                lambda data: self._handle_perception(PerceptionType.MOUSE, data)
            )
            self.real_time_monitor.register_callback(
                "file_change",
                lambda data: self._handle_perception(PerceptionType.FILE_SYSTEM, data)
            )
            self.real_time_monitor.register_callback(
                "time_event",
                lambda data: self._handle_perception(PerceptionType.TIME, data)
            )
            self.real_time_monitor.register_callback(
                "system_state",
                lambda data: self._handle_perception(PerceptionType.SYSTEM_STATE, data)
            )
            self.real_time_monitor.register_callback(
                "user_activity",
                lambda data: self._handle_perception(PerceptionType.USER_ACTIVITY, data)
            )
    
    def _register_bridge_callbacks(self):
        """Register callbacks with the action bridge"""
        if self.action_bridge:
            # Register post-execution callback for feedback collection
            if hasattr(self.action_bridge, 'register_post_execution_callback'):
                self.action_bridge.register_post_execution_callback(
                    self._handle_action_result
                )
    
    async def _main_loop(self):
        """Main feedback loop - runs continuously"""
        while self._running:
            loop_start = time.perf_counter()
            
            # Process pending perception events
            await self._process_pending_events()
            
            # Update active cycles
            await self._update_active_cycles()
            
            # Generate and process feedback
            await self._generate_feedback()
            
            # Calculate and check latency
            loop_duration_ms = (time.perf_counter() - loop_start) * 1000
            
            # Ensure minimum latency target
            if loop_duration_ms < self.latency_threshold_ms:
                sleep_time = (self.latency_threshold_ms - loop_duration_ms) / 1000
                await asyncio.sleep(sleep_time)
    
    async def _process_pending_events(self):
        """Process pending perception events from the event loop system"""
        if not self.event_loop_system:
            return
        
        # Get pending events
        events = await self.event_loop_system.get_pending_events()
        
        for event in events:
            if isinstance(event, PerceptionEvent):
                await self._start_cycle(event)
    
    async def _start_cycle(self, perception_event: PerceptionEvent):
        """Start a new perception-action cycle"""
        # Create cycle
        cycle = PerceptionActionCycle(
            cycle_id=str(uuid.uuid4()),
            perception_event=perception_event
        )
        
        self.active_cycles[cycle.cycle_id] = cycle
        
        # Notify cycle start callbacks
        for callback in self._cycle_start_callbacks:
            try:
                callback(cycle)
            except Exception as e:
                logger.error(f"[FeedbackLoopEngine] Cycle start callback error: {e}")
        
        # Trigger cognitive processing
        decision = await self._cognitive_processing(perception_event)
        
        if decision:
            cycle.decision = decision
            
            # Execute action
            action_id = await self._execute_action(decision)
            if action_id:
                cycle.action_id = action_id
    
    async def _cognitive_processing(self, perception_event: PerceptionEvent) -> Optional[ActionDecision]:
        """
        Process perception through cognitive system
        
        This simulates the cognitive processing that transforms
        perception into action decisions.
        """
        # Get context from HSM if available
        context = {}
        if self.hsm and hasattr(self.hsm, 'get_relevant_context'):
            try:
                context = await self.hsm.get_relevant_context(perception_event.data)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        # Use CDM for decision making if available
        if self.cdm and hasattr(self.cdm, 'generate_decision'):
            try:
                decision_data = await self.cdm.generate_decision(
                    perception_event.data,
                    context
                )
                
                return ActionDecision(
                    decision_id=str(uuid.uuid4()),
                    trigger_event=perception_event.event_id,
                    action_type=decision_data.get("action_type", "system_query"),
                    target=decision_data.get("target", ""),
                    urgency=decision_data.get("urgency", 0.5),
                    confidence=decision_data.get("confidence", 0.5),
                    parameters=decision_data.get("parameters", {}),
                    timestamp=datetime.now(),
                    expected_outcome=decision_data.get("expected_outcome")
                )
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        # Fallback: simple rule-based decision
        return await self._generate_fallback_decision(perception_event)
    
    async def _generate_fallback_decision(self, perception_event: PerceptionEvent) -> ActionDecision:
        """Generate fallback decision when cognitive systems unavailable"""
        action_type = "system_query"
        urgency = 0.3
        
        # Simple rule-based mapping
        if perception_event.perception_type == PerceptionType.MOUSE:
            action_type = "system_query"  # Just monitor
            urgency = 0.1
        elif perception_event.perception_type == PerceptionType.FILE_SYSTEM:
            action_type = "file_operation"
            urgency = 0.5
        elif perception_event.perception_type == PerceptionType.TIME:
            action_type = "satisfy_need"
            urgency = 0.4
        elif perception_event.perception_type == PerceptionType.USER_ACTIVITY:
            action_type = "initiate_conversation"
            urgency = 0.6
        
        return ActionDecision(
            decision_id=str(uuid.uuid4()),
            trigger_event=perception_event.event_id,
            action_type=action_type,
            target="auto_generated",
            urgency=urgency,
            confidence=0.5,
            parameters=perception_event.data,
            timestamp=datetime.now()
        )
    
    async def _execute_action(self, decision: ActionDecision) -> Optional[str]:
        """Execute action decision through action bridge or executor"""
        # Try action bridge first
        if self.action_bridge and hasattr(self.action_bridge, 'execute_action'):
            try:
                result = await self.action_bridge.execute_action(
                    action_type=decision.action_type,
                    parameters=decision.parameters,
                    priority=int(10 - decision.urgency * 10),  # Convert urgency to priority
                    trigger_source="feedback_loop",
                    wait_for_completion=False  # Non-blocking for real-time
                )
                return result.action_id if hasattr(result, 'action_id') else str(uuid.uuid4())
            except Exception as e:
                logger.error(f"[FeedbackLoopEngine] Action bridge execution error: {e}")
        
        # Fallback to action executor
        if self.action_executor and hasattr(self.action_executor, 'handle_autonomous_action'):
            try:
                result = await self.action_executor.handle_autonomous_action(
                    action_type=decision.action_type,
                    parameters=decision.parameters
                )
                return result.action_id if hasattr(result, 'action_id') else str(uuid.uuid4())
            except Exception as e:
                logger.error(f"[FeedbackLoopEngine] Action executor error: {e}")
        
        return None
    
    async def _handle_action_result(self, context: Any, result: Any):
        """Handle action execution result from action bridge"""
        # Find matching cycle
        action_id = getattr(context, 'action_id', None)
        if not action_id:
            return
        
        for cycle in self.active_cycles.values():
            if cycle.action_id == action_id:
                cycle.execution_result = {
                    "success": getattr(result, 'success', False),
                    "data": getattr(result, 'data', {}),
                    "error": getattr(result, 'error_message', None)
                }
                
                # Generate feedback signals
                await self._generate_cycle_feedback(cycle, result)
                break
    
    async def _generate_cycle_feedback(self, cycle: PerceptionActionCycle, result: Any):
        """Generate feedback signals for completed cycle"""
        # Multi-layer feedback generation
        
        # 1. Physiological layer feedback
        physiological_signal = FeedbackSignal(
            signal_id=str(uuid.uuid4()),
            action_id=cycle.action_id or "",
            layer=FeedbackLayer.PHYSIOLOGICAL,
            feedback_type=FeedbackType.IMMEDIATE,
            value=1.0 if getattr(result, 'success', False) else 0.0,
            data={"reaction": "satisfaction" if getattr(result, 'success', False) else "disappointment"},
            timestamp=datetime.now()
        )
        cycle.feedback_signals.append(physiological_signal)
        
        # 2. Cognitive layer feedback
        cognitive_signal = FeedbackSignal(
            signal_id=str(uuid.uuid4()),
            action_id=cycle.action_id or "",
            layer=FeedbackLayer.COGNITIVE,
            feedback_type=FeedbackType.DELAYED,
            value=0.8 if getattr(result, 'success', False) else 0.2,
            data={"attention_shift": "completed", "thinking_result": "validated"},
            timestamp=datetime.now()
        )
        cycle.feedback_signals.append(cognitive_signal)
        
        # 3. Emotional layer feedback
        emotion = "happy" if getattr(result, 'success', False) else "disappointed"
        emotional_signal = FeedbackSignal(
            signal_id=str(uuid.uuid4()),
            action_id=cycle.action_id or "",
            layer=FeedbackLayer.EMOTIONAL,
            feedback_type=FeedbackType.IMMEDIATE,
            value=0.7 if getattr(result, 'success', False) else 0.3,
            data={"emotion": emotion, "intensity": 0.6},
            timestamp=datetime.now()
        )
        cycle.feedback_signals.append(emotional_signal)
        
        # 4. Social layer feedback (if user interaction)
        if cycle.perception_event.perception_type in [PerceptionType.USER_ACTIVITY, PerceptionType.VOICE]:
            social_signal = FeedbackSignal(
                signal_id=str(uuid.uuid4()),
                action_id=cycle.action_id or "",
                layer=FeedbackLayer.SOCIAL,
                feedback_type=FeedbackType.DELAYED,
                value=0.6 if getattr(result, 'success', False) else 0.4,
                data={"relationship_impact": "positive" if getattr(result, 'success', False) else "neutral"},
                timestamp=datetime.now()
            )
            cycle.feedback_signals.append(social_signal)
        
        # Notify feedback callbacks
        for signal in cycle.feedback_signals:
            await self._notify_feedback(signal)
        
        # Send to feedback processor for learning
        if self.feedback_processor:
            for signal in cycle.feedback_signals:
                await self.feedback_processor.process_feedback(signal)
    
    async def _notify_feedback(self, signal: FeedbackSignal):
        """Notify feedback callbacks"""
        callbacks = self._feedback_callbacks.get(signal.layer, [])
        for callback in callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"[FeedbackLoopEngine] Feedback callback error: {e}")
    
    async def _update_active_cycles(self):
        """Update active cycles and complete finished ones"""
        completed_cycles = []
        
        for cycle_id, cycle in list(self.active_cycles.items()):
            # Check if cycle has completed (has result and feedback)
            if cycle.execution_result is not None and len(cycle.feedback_signals) > 0:
                # Complete the cycle
                cycle.end_time = datetime.now()
                cycle.latency_ms = (cycle.end_time - cycle.start_time).total_seconds() * 1000
                
                # Generate learning update
                await self._generate_learning_update(cycle)
                
                # Move to completed
                completed_cycles.append(cycle)
                del self.active_cycles[cycle_id]
                
                # Notify end callbacks
                for callback in self._cycle_end_callbacks:
                    try:
                        callback(cycle)
                    except Exception as e:
                        logger.error(f"[FeedbackLoopEngine] Cycle end callback error: {e}")
                
                # Update metrics
                self._update_performance_metrics(cycle)
        
        # Add to completed history
        self.completed_cycles.extend(completed_cycles)
        if len(self.completed_cycles) > self.max_completed_history:
            self.completed_cycles = self.completed_cycles[-self.max_completed_history:]
    
    async def _generate_learning_update(self, cycle: PerceptionActionCycle):
        """Generate learning update from completed cycle"""
        if not cycle.decision or not cycle.execution_result:
            return
        
        # Calculate prediction error
        expected_success = cycle.decision.confidence
        actual_success = 1.0 if cycle.execution_result.get("success") else 0.0
        prediction_error = abs(expected_success - actual_success)
        
        # Calculate performance delta
        performance_delta = actual_success - expected_success
        
        # Generate strategy adjustment
        strategy_adjustment = {
            "urgency_modifier": 0.1 if prediction_error > 0.5 else 0.0,
            "confidence_update": actual_success,
            "pattern_reinforcement": actual_success > expected_success
        }
        
        # Create learning update
        learning_update = LearningUpdate(
            update_id=str(uuid.uuid4()),
            source_action=cycle.action_id or "",
            prediction_error=prediction_error,
            performance_delta=performance_delta,
            strategy_adjustment=strategy_adjustment,
            timestamp=datetime.now()
        )
        
        cycle.learning_update = learning_update
        
        # Update HSM if available
        if self.hsm and hasattr(self.hsm, 'update_from_feedback'):
            try:
                await self.hsm.update_from_feedback({
                    "perception_type": cycle.perception_event.perception_type.value[0],
                    "action_type": cycle.decision.action_type,
                    "outcome": cycle.execution_result,
                    "latency_ms": cycle.latency_ms
                })
                learning_update.hsm_update = {"status": "updated"}
            except Exception as e:
                logger.error(f"[FeedbackLoopEngine] HSM update error: {e}")
        
        # Update CDM if available
        if self.cdm and hasattr(self.cdm, 'integrate_execution_feedback'):
            try:
                await self.cdm.integrate_execution_feedback({
                    "type": "perception_action_cycle",
                    "success": cycle.execution_result.get("success", False),
                    "prediction_error": prediction_error,
                    "context": cycle.perception_event.data
                })
                learning_update.cdm_update = {"status": "updated"}
            except Exception as e:
                logger.error(f"[FeedbackLoopEngine] CDM update error: {e}")
        
        self.performance_metrics["learning_updates"] += 1
    
    def _update_performance_metrics(self, cycle: PerceptionActionCycle):
        """Update performance metrics from completed cycle"""
        self.performance_metrics["cycles_completed"] += 1
        
        # Update latency metrics
        latency = cycle.latency_ms
        
        # Update average
        n = self.performance_metrics["cycles_completed"]
        current_avg = self.performance_metrics["average_latency_ms"]
        self.performance_metrics["average_latency_ms"] = (
            (current_avg * (n - 1) + latency) / n
        )
        
        # Update min/max
        if latency < self.performance_metrics["min_latency_ms"]:
            self.performance_metrics["min_latency_ms"] = latency
        if latency > self.performance_metrics["max_latency_ms"]:
            self.performance_metrics["max_latency_ms"] = latency
    
    async def _generate_feedback(self):
        """Generate system-wide feedback (periodic health checks, etc.)"""
        # This runs periodically to generate feedback from system state
        pass
    
    def _handle_perception(self, perception_type: PerceptionType, data: Dict[str, Any]):
        """Handle perception data from monitors"""
        # Create and process perception event
        event = PerceptionEvent.create(
            perception_type=perception_type,
            source="monitor",
            data=data,
            priority=5
        )
        
        # Add to event loop system
        if self.event_loop_system:
            asyncio.create_task(self.event_loop_system.add_event(event))
    
    # ========== Public API ==========
    
    async def process_perception_event(self, event: PerceptionEvent) -> str:
        """
        Manually process a perception event
        
        Args:
            event: Perception event to process
            
        Returns:
            Cycle ID
        """
        await self._start_cycle(event)
        return list(self.active_cycles.keys())[-1] if self.active_cycles else ""
    
    def register_cycle_start_callback(self, callback: Callable[[PerceptionActionCycle], None]):
        """Register callback for cycle start"""
        self._cycle_start_callbacks.append(callback)
    
    def register_cycle_end_callback(self, callback: Callable[[PerceptionActionCycle], None]):
        """Register callback for cycle end"""
        self._cycle_end_callbacks.append(callback)
    
    def register_feedback_callback(
        self, 
        layer: FeedbackLayer, 
        callback: Callable[[FeedbackSignal], None]
    ):
        """Register feedback callback for specific layer"""
        if layer in self._feedback_callbacks:
            self._feedback_callbacks[layer].append(callback)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = self.performance_metrics.copy()
        
        # Add current state
        metrics.update({
            "active_cycles": len(self.active_cycles),
            "completed_cycles_total": len(self.completed_cycles),
            "is_running": self._running,
            "uptime_seconds": (
                (datetime.now() - metrics["start_time"]).total_seconds()
                if metrics["start_time"] else 0
            )
        })
        
        return metrics
    
    def get_active_cycles(self) -> List[PerceptionActionCycle]:
        """Get list of currently active cycles"""
        return list(self.active_cycles.values())
    
    def get_completed_cycles(self, limit: int = 100) -> List[PerceptionActionCycle]:
        """Get recently completed cycles"""
        return self.completed_cycles[-limit:]
    
    async def force_feedback(self, action_id: str, layer: FeedbackLayer, value: float):
        """
        Force manual feedback for an action
        
        Args:
            action_id: ID of the action to feedback
            layer: Feedback layer
            value: Feedback value
        """
        signal = FeedbackSignal(
            signal_id=str(uuid.uuid4()),
            action_id=action_id,
            layer=layer,
            feedback_type=FeedbackType.IMMEDIATE,
            value=value,
            data={"manual": True},
            timestamp=datetime.now()
        )
        
        if self.feedback_processor:
            await self.feedback_processor.process_feedback(signal)
    
    async def wait_for_cycle(self, cycle_id: str, timeout: float = 10.0) -> Optional[PerceptionActionCycle]:
        """
        Wait for a cycle to complete
        
        Args:
            cycle_id: ID of the cycle to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Completed cycle or None if timeout
        """
        start_time = time.perf_counter()
        
        while time.perf_counter() - start_time < timeout:
            # Check if in completed cycles
            for cycle in self.completed_cycles:
                if cycle.cycle_id == cycle_id:
                    return cycle
            
            await asyncio.sleep(0.01)  # 10ms check interval
        
        return None


# ========== Integration Helpers ==========

class FeedbackLoopEngineFactory:
    """Factory for creating FeedbackLoopEngine with common configurations"""
    
    @staticmethod
    def create_basic_engine(config: Optional[Dict[str, Any]] = None) -> FeedbackLoopEngine:
        """Create basic engine without external dependencies"""
        return FeedbackLoopEngine(config=config)
    
    @staticmethod
    def create_full_engine(
        desktop_presence: Any,
        desktop_interaction: Any,
        audio_system: Any,
        action_bridge: Any,
        action_executor: Any,
        hsm: Any,
        cdm: Any,
        temporal_evolution: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> FeedbackLoopEngine:
        """Create fully configured engine with all dependencies"""
        return FeedbackLoopEngine(
            desktop_presence=desktop_presence,
            desktop_interaction=desktop_interaction,
            audio_system=audio_system,
            action_bridge=action_bridge,
            action_executor=action_executor,
            hsm=hsm,
            cdm=cdm,
            temporal_evolution=temporal_evolution,
            config=config
        )


# Example usage
if __name__ == "__main__":
    async def demo():
        logger.info("=" * 70)
        logger.info("Angela AI v6.0 - Feedback Loop Engine Demo")
        logger.info("实时反馈循环引擎演示")
        logger.info("=" * 70)
        
        # Create engine
        engine = FeedbackLoopEngine()
        await engine.initialize()
        
        # Register some callbacks
        def on_cycle_start(cycle):
            logger.info(f"\n[Cycle Started] ID: {cycle.cycle_id}")
            logger.info(f"  Perception: {cycle.perception_event.perception_type.value[0]}")
        
        def on_cycle_end(cycle):
            logger.info(f"\n[Cycle Completed] ID: {cycle.cycle_id}")
            logger.info(f"  Latency: {cycle.latency_ms:.2f}ms")
            logger.info(f"  Success: {cycle.execution_result.get('success', False) if cycle.execution_result else 'N/A'}")
        
        engine.register_cycle_start_callback(on_cycle_start)
        engine.register_cycle_end_callback(on_cycle_end)
        
        # Create and process test perception event
        logger.info("\n1. Testing perception processing:")
        event = PerceptionEvent.create(
            PerceptionType.MOUSE,
            "test",
            {"position": {"x": 100, "y": 200}},
            priority=5
        )
        
        cycle_id = await engine.process_perception_event(event)
        logger.info(f"   Cycle ID: {cycle_id}")
        
        # Wait for cycle to complete
        completed = await engine.wait_for_cycle(cycle_id, timeout=2.0)
        if completed:
            logger.info(f"   Cycle completed successfully")
        
        # Show metrics
        logger.info("\n2. Performance metrics:")
        metrics = engine.get_performance_metrics()
        logger.info(f"   Cycles completed: {metrics['cycles_completed']}")
        logger.info(f"   Average latency: {metrics['average_latency_ms']:.2f}ms")
        logger.info(f"   Min latency: {metrics['min_latency_ms']:.2f}ms")
        logger.info(f"   Max latency: {metrics['max_latency_ms']:.2f}ms")
        
        # Test another perception type
        logger.info("\n3. Testing file system perception:")
        event2 = PerceptionEvent.create(
            PerceptionType.FILE_SYSTEM,
            "test",
            {"file": "test.txt", "operation": "created"},
            priority=3
        )
        
        cycle_id2 = await engine.process_perception_event(event2)
        await asyncio.sleep(1)
        
        await engine.shutdown()
        
        logger.info("\n" + "=" * 70)
        logger.info("Demo completed successfully!")
        logger.info("=" * 70)
    
    asyncio.run(demo())
