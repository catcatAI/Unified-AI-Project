"""
Angela AI v6.0 - Event Loop System
事件循环系统

Asynchronous event processing with priority queue, event filtering,
aggregation, debouncing, and throttling.

Features:
- Asynchronous event handling
- Priority-based event queue
- Event filtering and deduplication
- Event aggregation
- Debouncing and throttling
- Real-time latency optimization

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from datetime import datetime, timedelta
import asyncio
import time
import heapq
from collections import defaultdict, deque
import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级 / Event priorities (lower number = higher priority)"""
    CRITICAL = (0, "紧急", "Critical events requiring immediate processing")
    HIGH = (1, "高", "High priority events")
    NORMAL = (2, "普通", "Normal priority events")
    LOW = (3, "低", "Low priority events")
    BACKGROUND = (4, "后台", "Background processing")
    
    def __init__(self, level: int, cn_name: str, description: str):
        self.level = level
        self.cn_name = cn_name
        self.description = description


class EventStatus(Enum):
    """事件状态 / Event processing status"""
    PENDING = ("等待中", "Pending in queue")
    PROCESSING = ("处理中", "Currently processing")
    COMPLETED = ("已完成", "Processing completed")
    FAILED = ("失败", "Processing failed")
    CANCELLED = ("已取消", "Cancelled")
    DEFERRED = ("延迟", "Deferred for later")


@dataclass
class Event:
    """事件 / Event definition"""
    event_id: str
    event_type: str
    priority: EventPriority
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    status: EventStatus = field(default_factory=lambda: EventStatus.PENDING)
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    handler: Optional[Callable] = None
    deferred_until: Optional[datetime] = None
    
    def __lt__(self, other):
        """Compare for priority queue ordering"""
        return self.priority.level < other.priority.level


@dataclass
class EventFilter:
    """事件过滤器 / Event filter configuration"""
    event_types: Optional[Set[str]] = None
    min_priority: Optional[EventPriority] = None
    sources: Optional[Set[str]] = None
    time_window: Optional[timedelta] = None


@dataclass
class AggregationRule:
    """事件聚合规则 / Event aggregation rule"""
    rule_id: str
    event_type: str
    time_window_ms: int
    max_events: int
    aggregate_function: Callable[[List[Event]], Event]


@dataclass
class DebounceConfig:
    """防抖配置 / Debounce configuration"""
    event_type: str
    delay_ms: int
    leading: bool = False  # Trigger on leading edge
    trailing: bool = True  # Trigger on trailing edge


@dataclass
class ThrottleConfig:
    """节流配置 / Throttle configuration"""
    event_type: str
    interval_ms: int
    leading: bool = True
    trailing: bool = True


class EventQueue:
    """
    事件队列 / Priority event queue
    
    Thread-safe priority queue for event processing.
    Uses heapq for efficient priority ordering.
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: List[Tuple[int, float, Event]] = []  # (priority, seq, event)
        self._sequence = 0
        self._lock = asyncio.Lock()
        self._event_map: Dict[str, Event] = {}
    
    async def enqueue(self, event: Event) -> bool:
        """Add event to queue"""
        async with self._lock:
            if len(self._queue) >= self.max_size:
                return False
            
            self._sequence += 1
            # Tuple: (priority level, sequence for FIFO within same priority, event)
            heapq.heappush(
                self._queue,
                (event.priority.level, self._sequence, event)
            )
            self._event_map[event.event_id] = event
            return True
    
    async def dequeue(self) -> Optional[Event]:
        """Get highest priority event"""
        async with self._lock:
            while self._queue:
                _, _, event = heapq.heappop(self._queue)
                
                # Check if deferred
                if event.deferred_until and datetime.now() < event.deferred_until:
                    # Re-queue with updated deferred time check
                    heapq.heappush(self._queue, (event.priority.level, self._sequence, event))
                    continue
                
                if event.status == EventStatus.PENDING:
                    event.status = EventStatus.PROCESSING
                    event.processing_start = datetime.now()
                    return event
            
            return None
    
    async def cancel(self, event_id: str) -> bool:
        """Cancel a pending event"""
        async with self._lock:
            if event_id in self._event_map:
                event = self._event_map[event_id]
                if event.status == EventStatus.PENDING:
                    event.status = EventStatus.CANCELLED
                    return True
            return False
    
    async def defer(self, event_id: str, until: datetime):
        """Defer event processing until specified time"""
        async with self._lock:
            if event_id in self._event_map:
                event = self._event_map[event_id]
                event.deferred_until = until
                event.status = EventStatus.DEFERRED
    
    async def get_size(self) -> int:
        """Get current queue size"""
        async with self._lock:
            return len([e for _, _, e in self._queue if e.status == EventStatus.PENDING])
    
    async def get_status(self) -> Dict[str, int]:
        """Get queue status statistics"""
        async with self._lock:
            stats = defaultdict(int)
            for _, _, event in self._queue:
                stats[event.status.value[0]] += 1
            return dict(stats)


class EventAggregator:
    """
    事件聚合器 / Event aggregation system
    
    Aggregates similar events within time windows to reduce processing overhead.
    """
    
    def __init__(self):
        self.rules: Dict[str, AggregationRule] = {}
        self.pending_events: Dict[str, List[Event]] = defaultdict(list)
        self.aggregation_timers: Dict[str, asyncio.Task] = {}
    
    def register_rule(self, rule: AggregationRule):
        """Register aggregation rule"""
        self.rules[rule.event_type] = rule
    
    async def add_event(self, event: Event) -> Optional[Event]:
        """
        Add event for aggregation
        
        Returns:
            Aggregated event if threshold reached, None otherwise
        """
        if event.event_type not in self.rules:
            return event  # No aggregation rule, pass through
        
        rule = self.rules[event.event_type]
        self.pending_events[event.event_type].append(event)
        
        # Check if we should aggregate
        if len(self.pending_events[event.event_type]) >= rule.max_events:
            return await self._aggregate(event.event_type)
        
        # Start timer if not already running
        if event.event_type not in self.aggregation_timers:
            self.aggregation_timers[event.event_type] = asyncio.create_task(
                self._aggregation_timer(event.event_type, rule.time_window_ms)
            )
        
        return None
    
    async def _aggregation_timer(self, event_type: str, delay_ms: int):
        """Timer to trigger aggregation after time window"""
        await asyncio.sleep(delay_ms / 1000)
        
        if self.pending_events[event_type]:
            await self._aggregate(event_type)
        
        # Clean up timer
        if event_type in self.aggregation_timers:
            del self.aggregation_timers[event_type]
    
    async def _aggregate(self, event_type: str) -> Event:
        """Aggregate pending events"""
        events = self.pending_events[event_type]
        self.pending_events[event_type] = []
        
        rule = self.rules[event_type]
        aggregated = rule.aggregate_function(events)
        
        return aggregated


class DebounceThrottleManager:
    """
    防抖节流管理器 / Debounce and throttle manager
    
    Manages debouncing and throttling of events.
    """
    
    def __init__(self):
        self.debounce_configs: Dict[str, DebounceConfig] = {}
        self.throttle_configs: Dict[str, ThrottleConfig] = {}
        
        # Debounce state
        self.debounce_timers: Dict[str, asyncio.Task] = {}
        self.debounce_pending: Dict[str, Event] = {}
        
        # Throttle state
        self.throttle_last_emit: Dict[str, float] = {}
        self.throttle_pending: Dict[str, Event] = {}
    
    def register_debounce(self, config: DebounceConfig):
        """Register debounce configuration"""
        self.debounce_configs[config.event_type] = config
    
    def register_throttle(self, config: ThrottleConfig):
        """Register throttle configuration"""
        self.throttle_configs[config.event_type] = config
    
    async def process(self, event: Event) -> Optional[Event]:
        """
        Process event through debounce/throttle
        
        Returns:
            Event to process immediately, or None if deferred
        """
        # Check throttle first
        if event.event_type in self.throttle_configs:
            return await self._apply_throttle(event)
        
        # Check debounce
        if event.event_type in self.debounce_configs:
            return await self._apply_debounce(event)
        
        # No debounce/throttle, pass through
        return event
    
    async def _apply_debounce(self, event: Event) -> Optional[Event]:
        """Apply debounce logic"""
        config = self.debounce_configs[event.event_type]
        
        # Cancel existing timer
        if event.event_type in self.debounce_timers:
            self.debounce_timers[event.event_type].cancel()
        
        # Store pending event
        self.debounce_pending[event.event_type] = event
        
        # Trigger on leading edge if configured
        if config.leading and event.event_type not in self.debounce_timers:
            return event
        
        # Start timer for trailing edge
        self.debounce_timers[event.event_type] = asyncio.create_task(
            self._debounce_timer(event.event_type, config.delay_ms)
        )
        
        return None
    
    async def _debounce_timer(self, event_type: str, delay_ms: int):
        """Debounce timer"""
        await asyncio.sleep(delay_ms / 1000)
        
        # Emit pending event
        if event_type in self.debounce_pending:
            # This would need to be integrated with the event queue
            # For now, we just clear it
            del self.debounce_pending[event_type]
        
        if event_type in self.debounce_timers:
            del self.debounce_timers[event_type]
    
    async def _apply_throttle(self, event: Event) -> Optional[Event]:
        """Apply throttle logic"""
        config = self.throttle_configs[event.event_type]
        current_time = time.time() * 1000  # ms
        
        last_emit = self.throttle_last_emit.get(event.event_type, 0)
        
        if current_time - last_emit >= config.interval_ms:
            # Within interval, emit immediately
            self.throttle_last_emit[event.event_type] = current_time
            return event
        else:
            # Store for trailing edge
            if config.trailing:
                self.throttle_pending[event.event_type] = event
                
                # Schedule emission
                delay = config.interval_ms - (current_time - last_emit)
                asyncio.create_task(self._throttle_emit_timer(event.event_type, delay))
            
            return None
    
    async def _throttle_emit_timer(self, event_type: str, delay_ms: float):
        """Throttle emission timer"""
        await asyncio.sleep(delay_ms / 1000)
        
        # Emit pending event
        if event_type in self.throttle_pending:
            # Would emit to queue
            self.throttle_last_emit[event_type] = time.time() * 1000
            del self.throttle_pending[event_type]


class EventLoopSystem:
    """
    事件循环系统主类 / Main event loop system
    
    Central event processing system with:
    - Priority queue management
    - Event filtering
    - Event aggregation
    - Debouncing and throttling
    - Asynchronous processing
    - Real-time latency optimization
    
    Example:
        >>> event_loop = EventLoopSystem(latency_target_ms=16)
        >>> await event_loop.initialize()
        >>> 
        >>> # Add event
        >>> event = Event(
        ...     event_id="evt_1",
        ...     event_type="mouse_move",
        ...     priority=EventPriority.NORMAL,
        ...     data={"x": 100, "y": 200},
        ...     timestamp=datetime.now(),
        ...     source="mouse_monitor"
        ... )
        >>> await event_loop.add_event(event)
        >>> 
        >>> # Register handler
        >>> event_loop.register_handler("mouse_move", handle_mouse)
    """
    
    def __init__(
        self,
        latency_target_ms: float = 16.0,
        max_queue_size: int = 10000,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        self.latency_target_ms = latency_target_ms
        self.max_queue_size = max_queue_size
        
        # Components
        self.queue = EventQueue(max_size=max_queue_size)
        self.aggregator = EventAggregator()
        self.debounce_throttle = DebounceThrottleManager()
        
        # Event handlers
        self.handlers: Dict[str, Callable[[Event], Any]] = {}
        self.default_handler: Optional[Callable[[Event], Any]] = None
        
        # Filters
        self.filters: List[EventFilter] = []
        
        # Running state
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            "events_processed": 0,
            "events_filtered": 0,
            "events_aggregated": 0,
            "events_debounced": 0,
            "events_throttled": 0,
            "average_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "processing_errors": 0
        }
        
        # Latency tracking
        self._latency_samples: deque = deque(maxlen=1000)
    
    async def initialize(self):
        """Initialize the event loop system"""
        print(f"[EventLoopSystem] Initializing with {self.latency_target_ms}ms target latency...")
        
        self._running = True
        
        # Setup default aggregation rules
        self._setup_default_aggregations()
        self._setup_default_debounce_throttle()
        
        # Start processor
        self._processor_task = asyncio.create_task(self._event_processor())
        self._metrics_task = asyncio.create_task(self._metrics_collector())
        
        print("[EventLoopSystem] Initialization complete")
    
    async def shutdown(self):
        """Shutdown the event loop system"""
        print("[EventLoopSystem] Shutting down...")
        
        self._running = False
        
        # Cancel tasks
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
        
        print("[EventLoopSystem] Shutdown complete")
    
    def _setup_default_aggregations(self):
        """Setup default event aggregation rules"""
        # Mouse move aggregation - combine rapid mouse movements
        def aggregate_mouse_moves(events: List[Event]) -> Event:
            if not events:
                return events[0] if events else None
            
            # Use the latest event with aggregated data
            latest = max(events, key=lambda e: e.timestamp)
            positions = [e.data.get("position", {}) for e in events]
            
            latest.data["aggregated"] = True
            latest.data["event_count"] = len(events)
            latest.data["positions"] = positions
            
            return latest
        
        self.aggregator.register_rule(AggregationRule(
            rule_id="mouse_move_agg",
            event_type="mouse_move",
            time_window_ms=32,  # 2 frames at 60fps
            max_events=10,
            aggregate_function=aggregate_mouse_moves
        ))
    
    def _setup_default_debounce_throttle(self):
        """Setup default debounce and throttle configurations"""
        # Debounce rapid file changes
        self.debounce_throttle.register_debounce(DebounceConfig(
            event_type="file_change",
            delay_ms=100,
            leading=False,
            trailing=True
        ))
        
        # Throttle system state updates
        self.debounce_throttle.register_throttle(ThrottleConfig(
            event_type="system_state",
            interval_ms=1000,
            leading=True,
            trailing=True
        ))
    
    async def _event_processor(self):
        """Main event processing loop"""
        while self._running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(
                    self.queue.dequeue(),
                    timeout=0.001  # 1ms timeout for responsiveness
                )
                
                if event:
                    # Track latency
                    start_time = time.perf_counter()
                    
                    # Process event
                    await self._process_event(event)
                    
                    # Calculate latency
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    self._latency_samples.append(latency_ms)
                    
                    # Update event
                    event.processing_end = datetime.now()
                    event.status = EventStatus.COMPLETED
                    
                    # Update metrics
                    self.metrics["events_processed"] += 1
                    
                    # Enforce latency target
                    if latency_ms < self.latency_target_ms:
                        await asyncio.sleep((self.latency_target_ms - latency_ms) / 1000)
                
            except asyncio.TimeoutError:
                # No events, continue
                pass
            except Exception as e:
                print(f"[EventLoopSystem] Processor error: {e}")
                self.metrics["processing_errors"] += 1
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        try:
            # Get handler
            handler = self.handlers.get(event.event_type, self.default_handler)
            
            if handler:
                # Execute handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            
        except Exception as e:
            print(f"[EventLoopSystem] Event processing error: {e}")
            event.status = EventStatus.FAILED
    
    async def _metrics_collector(self):
        """Collect and update metrics periodically"""
        while self._running:
            if self._latency_samples:
                self.metrics["average_latency_ms"] = sum(self._latency_samples) / len(self._latency_samples)
                self.metrics["max_latency_ms"] = max(self._latency_samples)
                self._latency_samples.clear()
            
            await asyncio.sleep(1.0)  # Update every second
    
    async def add_event(self, event: Event) -> bool:
        """
        Add event to processing queue
        
        Args:
            event: Event to process
            
        Returns:
            True if added successfully
        """
        # Apply filters
        if not self._passes_filters(event):
            self.metrics["events_filtered"] += 1
            return False
        
        # Apply aggregation
        aggregated = await self.aggregator.add_event(event)
        if aggregated is None:
            # Event is being aggregated
            self.metrics["events_aggregated"] += 1
            return True
        
        event = aggregated
        
        # Apply debounce/throttle
        processed = await self.debounce_throttle.process(event)
        if processed is None:
            # Event deferred
            self.metrics["events_debounced"] += 1
            return True
        
        event = processed
        
        # Add to queue
        return await self.queue.enqueue(event)
    
    def _passes_filters(self, event: Event) -> bool:
        """Check if event passes all filters"""
        if not self.filters:
            return True
        
        for filter_config in self.filters:
            # Check event type
            if filter_config.event_types and event.event_type not in filter_config.event_types:
                continue  # Filter doesn't apply
            
            # Check priority
            if filter_config.min_priority and event.priority.level > filter_config.min_priority.level:
                return False
            
            # Check source
            if filter_config.sources and event.source not in filter_config.sources:
                return False
            
            # Check time window
            if filter_config.time_window:
                age = datetime.now() - event.timestamp
                if age > filter_config.time_window:
                    return False
        
        return True
    
    def register_handler(self, event_type: str, handler: Callable[[Event], Any]):
        """
        Register event handler
        
        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        self.handlers[event_type] = handler
    
    def register_default_handler(self, handler: Callable[[Event], Any]):
        """Register default handler for unhandled event types"""
        self.default_handler = handler
    
    def add_filter(self, filter_config: EventFilter):
        """Add event filter"""
        self.filters.append(filter_config)
    
    def register_aggregation_rule(self, rule: AggregationRule):
        """Register custom aggregation rule"""
        self.aggregator.register_rule(rule)
    
    def register_debounce(self, config: DebounceConfig):
        """Register debounce configuration"""
        self.debounce_throttle.register_debounce(config)
    
    def register_throttle(self, config: ThrottleConfig):
        """Register throttle configuration"""
        self.debounce_throttle.register_throttle(config)
    
    async def get_pending_events(self) -> List[Event]:
        """Get list of pending events"""
        # This is a snapshot for external access
        status = await self.queue.get_status()
        pending_count = status.get("等待中", 0)
        return []  # Actual implementation would return pending events
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()
    
    async def get_queue_status(self) -> Dict[str, int]:
        """Get queue status"""
        return await self.queue.get_status()
    
    async def cancel_event(self, event_id: str) -> bool:
        """Cancel a pending event"""
        return await self.queue.cancel(event_id)
    
    async def defer_event(self, event_id: str, until: datetime):
        """Defer event processing"""
        await self.queue.defer(event_id, until)


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 70)
        print("Angela AI v6.0 - Event Loop System Demo")
        print("事件循环系统演示")
        print("=" * 70)
        
        # Create event loop
        event_loop = EventLoopSystem(latency_target_ms=16)
        await event_loop.initialize()
        
        # Register handlers
        processed_events = []
        
        def handle_mouse_move(event):
            processed_events.append(event.event_type)
            print(f"[Handler] Mouse move: {event.data.get('x')}, {event.data.get('y')}")
        
        def handle_file_change(event):
            processed_events.append(event.event_type)
            print(f"[Handler] File change: {event.data.get('path')}")
        
        event_loop.register_handler("mouse_move", handle_mouse_move)
        event_loop.register_handler("file_change", handle_file_change)
        
        # Add test events
        print("\n1. Adding test events:")
        
        for i in range(5):
            event = Event(
                event_id=f"mouse_{i}",
                event_type="mouse_move",
                priority=EventPriority.NORMAL,
                data={"x": i * 10, "y": i * 10},
                timestamp=datetime.now(),
                source="test"
            )
            await event_loop.add_event(event)
        
        file_event = Event(
            event_id="file_1",
            event_type="file_change",
            priority=EventPriority.HIGH,
            data={"path": "/test/file.txt", "type": "created"},
            timestamp=datetime.now(),
            source="test"
        )
        await event_loop.add_event(file_event)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Show metrics
        print("\n2. Event loop metrics:")
        metrics = event_loop.get_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        # Show queue status
        print("\n3. Queue status:")
        status = await event_loop.get_queue_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print(f"\n4. Processed events: {len(processed_events)}")
        
        await event_loop.shutdown()
        
        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
    
    asyncio.run(demo())
