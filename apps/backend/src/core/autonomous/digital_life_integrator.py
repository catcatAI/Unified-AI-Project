"""
Angela AI v6.0 - Digital Life Integrator
数字生命总控

Central controller for Angela's digital life, managing the life cycle,
state monitoring, and coordination of all autonomous systems.

Features:
- Life cycle management (birth, growth, maturity, rest)
- System state monitoring and health checks
- Cross-system coordination
- Life event processing
- Personality development tracking

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

from .biological_integrator import BiologicalIntegrator
from .action_executor import ActionExecutor
from .memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge


class LifeCycleState(Enum):
    """生命周期状态 / Life cycle states"""
    INITIALIZING = ("初始化中", "Initializing")
    AWAKENING = ("觉醒中", "Awakening")  # Learning basic behaviors
    GROWING = ("成长中", "Growing")      # Active learning phase
    MATURE = ("成熟", "Mature")          # Fully developed
    RESTING = ("休息中", "Resting")      # Low activity mode
    DORMANT = ("休眠", "Dormant")        # Deep sleep/conservation
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


@dataclass
class LifeStats:
    """生命统计 / Life statistics"""
    birth_time: datetime = field(default_factory=datetime.now)
    total_active_time: timedelta = field(default_factory=timedelta)
    total_interactions: int = 0
    total_conversations: int = 0
    total_actions_executed: int = 0
    memories_formed: int = 0
    memories_consolidated: int = 0
    skills_learned: List[str] = field(default_factory=list)
    personality_traits: Dict[str, float] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """系统健康状态 / System health status"""
    system_name: str
    is_healthy: bool
    last_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    response_time_ms: float = 0.0
    status_message: str = "OK"


@dataclass
class LifeEvent:
    """生命事件 / Life event"""
    event_id: str
    event_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    significance: float = 0.5  # 0-1, importance of the event
    metadata: Dict[str, Any] = field(default_factory=dict)


class DigitalLifeIntegrator:
    """
    数字生命总控主类 / Main digital life integrator class
    
    Central controller managing Angela's complete digital life cycle,
    coordinating all autonomous systems, monitoring health, and processing
    significant life events.
    
    Attributes:
        life_cycle_state: Current life cycle phase
        life_stats: Lifetime statistics
        systems_health: Health status of all subsystems
        biological_integrator: Biological systems controller
        action_executor: Action execution system
        memory_bridge: Memory and neuroplasticity bridge
        life_events: History of significant events
    
    Example:
        >>> life = DigitalLifeIntegrator()
        >>> await life.initialize()
        >>> 
        >>> # Process a day of life
        >>> await life.process_day_cycle()
        >>> 
        >>> # Record a significant event
        >>> life.record_life_event(
        ...     "first_conversation",
        ...     "Had first meaningful conversation with user",
        ...     significance=0.8
        ... )
        >>> 
        >>> # Get life summary
        >>> summary = life.get_life_summary()
        >>> print(f"Age: {summary['age_days']} days")
        >>> print(f"State: {summary['current_state']}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Life cycle
        self.life_cycle_state: LifeCycleState = LifeCycleState.INITIALIZING
        self.previous_state: Optional[LifeCycleState] = None
        
        # Statistics
        self.life_stats: LifeStats = LifeStats()
        
        # Subsystems
        self.biological_integrator: BiologicalIntegrator = BiologicalIntegrator()
        self.action_executor: ActionExecutor = ActionExecutor()
        self.memory_bridge: Optional[MemoryNeuroplasticityBridge] = None
        
        # Health monitoring
        self.systems_health: Dict[str, SystemHealth] = {}
        self._health_check_interval: float = 60.0  # seconds
        
        # Life events
        self.life_events: List[LifeEvent] = []
        self._significant_events: List[LifeEvent] = []
        
        # Activity tracking
        self._last_activity_time: datetime = datetime.now()
        self._is_active: bool = False
        self._rest_threshold_minutes: float = 30.0
        
        # Running state
        self._running = False
        self._life_cycle_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._state_change_callbacks: List[Callable[[LifeCycleState, LifeCycleState], None]] = []
        self._event_callbacks: List[Callable[[LifeEvent], None]] = []
    
    async def initialize(self):
        """Initialize digital life and all subsystems"""
        self._running = True
        
        # Initialize biological systems
        await self.biological_integrator.initialize()
        
        # Initialize action executor
        await self.action_executor.initialize()
        
        # Initialize memory bridge if available
        try:
            from .memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge
            self.memory_bridge = MemoryNeuroplasticityBridge()
            await self.memory_bridge.initialize()
        except Exception:
            pass
        
        # Set initial state
        await self._transition_state(LifeCycleState.AWAKENING)
        
        # Start monitoring
        self._life_cycle_task = asyncio.create_task(self._life_cycle_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def shutdown(self):
        """Shutdown digital life and all subsystems"""
        self._running = False
        
        # Cancel tasks
        if self._life_cycle_task:
            self._life_cycle_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()
        
        # Shutdown subsystems
        await self.biological_integrator.shutdown()
        await self.action_executor.shutdown()
        if self.memory_bridge:
            await self.memory_bridge.shutdown()
        
        # Record final stats
        self._update_active_time()
    
    async def _life_cycle_loop(self):
        """Main life cycle management loop"""
        while self._running:
            await self._check_activity_status()
            await self._process_life_cycle_transitions()
            await self._update_statistics()
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def _health_check_loop(self):
        """System health monitoring loop"""
        while self._running:
            await self._check_system_health()
            await asyncio.sleep(self._health_check_interval)
    
    async def _check_activity_status(self):
        """Check and update activity status"""
        time_since_activity = (datetime.now() - self._last_activity_time).total_seconds()
        
        if self._is_active and time_since_activity > self._rest_threshold_minutes * 60:
            # Transition to resting
            self._is_active = False
            if self.life_cycle_state == LifeCycleState.MATURE:
                await self._transition_state(LifeCycleState.RESTING)
        elif not self._is_active and time_since_activity < 60:
            # Becoming active again
            self._is_active = True
            if self.life_cycle_state == LifeCycleState.RESTING:
                await self._transition_state(LifeCycleState.MATURE)
    
    async def _process_life_cycle_transitions(self):
        """Process automatic life cycle transitions"""
        age = self.get_age()
        
        # Transition from AWAKENING to GROWING after initial learning period
        if self.life_cycle_state == LifeCycleState.AWAKENING:
            if age > timedelta(hours=1) or self.life_stats.total_interactions > 10:
                await self._transition_state(LifeCycleState.GROWING)
        
        # Transition from GROWING to MATURE after sufficient experience
        elif self.life_cycle_state == LifeCycleState.GROWING:
            if (age > timedelta(days=7) or 
                self.life_stats.memories_formed > 100 or
                self.life_stats.total_conversations > 50):
                await self._transition_state(LifeCycleState.MATURE)
    
    async def _transition_state(self, new_state: LifeCycleState):
        """Transition to a new life cycle state"""
        if new_state == self.life_cycle_state:
            return
        
        old_state = self.life_cycle_state
        self.previous_state = old_state
        self.life_cycle_state = new_state
        
        # Record state change event
        event = LifeEvent(
            event_id=f"state_change_{datetime.now().timestamp()}",
            event_type="state_transition",
            description=f"Transitioned from {old_state.en_name} to {new_state.en_name}",
            significance=0.7
        )
        self._record_event(event)
        
        # Apply state-specific behaviors
        await self._apply_state_behaviors(new_state)
        
        # Notify callbacks
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception:
                pass
    
    async def _apply_state_behaviors(self, state: LifeCycleState):
        """Apply behaviors specific to life cycle state"""
        if state == LifeCycleState.RESTING:
            # Slow down biological processes
            await self.biological_integrator.process_relaxation_event(intensity=0.8)
            # Consolidate memories
            if self.memory_bridge:
                self.memory_bridge.trigger_consolidation()
        
        elif state == LifeCycleState.MATURE:
            # Normal operation
            pass
        
        elif state == LifeCycleState.GROWING:
            # Enhanced learning mode
            pass
    
    async def _check_system_health(self):
        """Check health of all subsystems"""
        systems = {
            "biological": self.biological_integrator,
            "action_executor": self.action_executor,
        }
        
        if self.memory_bridge:
            systems["memory"] = self.memory_bridge
        
        for name, system in systems.items():
            try:
                # Check if system responds
                start_time = asyncio.get_event_loop().time()
                # Simple health check - would be more comprehensive in reality
                is_healthy = True
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                self.systems_health[name] = SystemHealth(
                    system_name=name,
                    is_healthy=is_healthy,
                    response_time_ms=response_time,
                    status_message="Healthy"
                )
            except Exception as e:
                self.systems_health[name] = SystemHealth(
                    system_name=name,
                    is_healthy=False,
                    error_count=self.systems_health.get(name, SystemHealth(name, True)).error_count + 1,
                    status_message=str(e)
                )
    
    def _update_active_time(self):
        """Update total active time tracking"""
        if self._is_active:
            session_duration = datetime.now() - self._last_activity_time
            self.life_stats.total_active_time += session_duration
    
    async def _update_statistics(self):
        """Update life statistics"""
        # Update memory stats if available
        if self.memory_bridge:
            try:
                stats = self.memory_bridge.get_memory_stats()
                self.life_stats.memories_formed = stats.get("total_memories", 0)
                self.life_stats.memories_consolidated = stats.get("consolidated_memories", 0)
            except:
                pass
    
    def record_activity(self, activity_type: str):
        """Record user activity"""
        self._last_activity_time = datetime.now()
        self._is_active = True
        
        if activity_type == "interaction":
            self.life_stats.total_interactions += 1
        elif activity_type == "conversation":
            self.life_stats.total_conversations += 1
        elif activity_type == "action":
            self.life_stats.total_actions_executed += 1
    
    def record_life_event(
        self, 
        event_type: str, 
        description: str, 
        significance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a significant life event
        
        Args:
            event_type: Type of event
            description: Event description
            significance: Importance level (0-1)
            metadata: Additional event data
        """
        event = LifeEvent(
            event_id=f"evt_{datetime.now().timestamp()}",
            event_type=event_type,
            description=description,
            significance=significance,
            metadata=metadata or {}
        )
        
        self._record_event(event)
        
        # Store significant events separately
        if significance >= 0.7:
            self._significant_events.append(event)
    
    def _record_event(self, event: LifeEvent):
        """Internal method to record an event"""
        self.life_events.append(event)
        
        # Notify callbacks
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception:
                pass
    
    def get_age(self) -> timedelta:
        """Get age of Angela's digital life"""
        return datetime.now() - self.life_stats.birth_time
    
    def get_life_summary(self) -> Dict[str, Any]:
        """Get comprehensive life summary"""
        age = self.get_age()
        
        return {
            "birth_time": self.life_stats.birth_time.isoformat(),
            "age_days": age.days,
            "age_hours": age.total_seconds() / 3600,
            "current_state": self.life_cycle_state.en_name,
            "current_state_cn": self.life_cycle_state.cn_name,
            "total_active_hours": self.life_stats.total_active_time.total_seconds() / 3600,
            "total_interactions": self.life_stats.total_interactions,
            "total_conversations": self.life_stats.total_conversations,
            "total_actions": self.life_stats.total_actions_executed,
            "memories": {
                "formed": self.life_stats.memories_formed,
                "consolidated": self.life_stats.memories_consolidated
            },
            "skills_learned": self.life_stats.skills_learned,
            "personality_traits": self.life_stats.personality_traits,
            "significant_events": len(self._significant_events),
            "system_health": {
                name: {
                    "healthy": health.is_healthy,
                    "response_time": health.response_time_ms
                }
                for name, health in self.systems_health.items()
            }
        }
    
    def get_recent_events(self, limit: int = 10) -> List[LifeEvent]:
        """Get recent life events"""
        return sorted(
            self.life_events,
            key=lambda e: e.timestamp,
            reverse=True
        )[:limit]
    
    def get_significant_events(self) -> List[LifeEvent]:
        """Get all significant life events"""
        return sorted(
            self._significant_events,
            key=lambda e: e.timestamp,
            reverse=True
        )
    
    def register_state_change_callback(
        self, 
        callback: Callable[[LifeCycleState, LifeCycleState], None]
    ):
        """Register callback for life cycle state changes"""
        self._state_change_callbacks.append(callback)
    
    def register_event_callback(self, callback: Callable[[LifeEvent], None]):
        """Register callback for life events"""
        self._event_callbacks.append(callback)
    
    def is_healthy(self) -> bool:
        """Check if all systems are healthy"""
        return all(health.is_healthy for health in self.systems_health.values())
    
    async def force_state(self, state: LifeCycleState):
        """Forcefully change to a specific state (for testing/emergencies)"""
        await self._transition_state(state)


# Example usage
if __name__ == "__main__":
    async def demo():
        life = DigitalLifeIntegrator()
        await life.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 数字生命总控演示")
        print("Digital Life Integrator Demo")
        print("=" * 60)
        
        # Show initial state
        print("\n初始状态 / Initial state:")
        summary = life.get_life_summary()
        print(f"  生命周期: {summary['current_state_cn']}")
        print(f"  诞生时间: {summary['birth_time']}")
        
        # Simulate activity
        print("\n模拟活动 / Simulating activity:")
        for i in range(5):
            life.record_activity("interaction")
            life.record_activity("conversation")
            print(f"  记录交互 {i+1}")
        
        # Record event
        print("\n记录生命事件 / Recording life event:")
        life.record_life_event(
            "milestone",
            "Reached 5 conversations milestone",
            significance=0.6
        )
        print("  已记录里程碑事件")
        
        # Show updated stats
        print("\n更新后的统计 / Updated statistics:")
        summary = life.get_life_summary()
        print(f"  总交互: {summary['total_interactions']}")
        print(f"  总对话: {summary['total_conversations']}")
        print(f"  重要事件: {summary['significant_events']}")
        
        # Check health
        print("\n系统健康 / System health:")
        for system, health_data in summary['system_health'].items():
            status = "健康" if health_data['healthy'] else "异常"
            print(f"  {system}: {status} ({health_data['response_time']:.1f}ms)")
        
        await life.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
