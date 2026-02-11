"""
Angela AI v6.0 - Real-Time Monitor
实时监测器

Monitors all system inputs in real-time with 16ms update requirement:
- Global mouse position tracking (16ms updates)
- File system change monitoring
- Time and schedule monitoring
- System state monitoring
- User activity pattern recognition

Features:
- 16ms latency target for mouse tracking
- Event-driven file system monitoring
- User activity pattern analysis
- System resource tracking
- Multi-threaded monitoring architecture

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
import json
from pathlib import Path
from collections import deque


class MonitorType(Enum):
    """监测器类型 / Monitor types"""
    MOUSE = ("鼠标", "Global mouse position")
    FILE_SYSTEM = ("文件系统", "File system changes")
    TIME = ("时间", "Time and schedule events")
    SYSTEM_STATE = ("系统状态", "System resource state")
    USER_ACTIVITY = ("用户活动", "User activity patterns")
    AUDIO_STATE = ("音频状态", "Audio system state")


class ActivityState(Enum):
    """用户活动状态 / User activity states"""
    IDLE = ("空闲", "idle")
    ACTIVE = ("活跃", "active")
    WORKING = ("工作中", "working")
    GAMING = ("游戏中", "gaming")
    READING = ("阅读中", "reading")
    TYPING = ("打字中", "typing")
    UNKNOWN = ("未知", "unknown")


@dataclass
class MouseData:
    """鼠标数据 / Mouse tracking data"""
    x: float
    y: float
    is_pressed: bool = False
    button: Optional[str] = None
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    screen_width: int = 1920
    screen_height: int = 1080
    
    @property
    def velocity(self) -> float:
        """Calculate velocity magnitude"""
        return (self.velocity_x ** 2 + self.velocity_y ** 2) ** 0.5
    
    @property
    def screen_region(self) -> str:
        """Get screen region (quadrant)"""
        mid_x, mid_y = self.screen_width / 2, self.screen_height / 2
        if self.x < mid_x:
            return "left" if self.y < mid_y else "top_left"
        else:
            return "right" if self.y < mid_y else "bottom_right"


@dataclass
class FileSystemEvent:
    """文件系统事件 / File system change event"""
    event_id: str
    path: Path
    event_type: str  # created, modified, deleted, moved
    is_directory: bool
    timestamp: datetime
    file_size: Optional[int] = None
    file_hash: Optional[str] = None


@dataclass
class SystemStateData:
    """系统状态数据 / System state information"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    uptime_seconds: float
    timestamp: datetime
    process_count: int = 0
    load_average: Optional[Tuple[float, float, float]] = None


@dataclass
class UserActivityData:
    """用户活动数据 / User activity information"""
    activity_state: ActivityState
    active_window: Optional[str]
    idle_time_seconds: float
    input_events_per_minute: int
    session_duration_seconds: float
    timestamp: datetime
    focus_score: float = 0.0  # 0-1, higher = more focused


@dataclass
class TimeEvent:
    """时间事件 / Time-based event"""
    event_id: str
    event_type: str  # schedule, alarm, periodic
    trigger_time: datetime
    description: str
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None


class MouseMonitor:
    """
    鼠标监测器 / Mouse position monitor
    
    Tracks global mouse position with 16ms update interval.
    Calculates velocity and detects movement patterns.
    """
    
    def __init__(self, update_interval_ms: float = 16.0):
        self.update_interval_ms = update_interval_ms
        self.current_position: Optional[MouseData] = None
        self.position_history: deque = deque(maxlen=1000)  # Last 1000 positions
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[MouseData], None]] = []
        
        # Movement detection
        self.movement_threshold = 5.0  # pixels
        self.last_movement_time = datetime.now()
        self.is_moving = False
    
    async def initialize(self):
        """Initialize mouse monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def shutdown(self):
        """Shutdown mouse monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Main monitoring loop - updates every 16ms"""
        last_x, last_y = 0.0, 0.0
        
        while self._running:
            loop_start = time.perf_counter()
            
            # Get current mouse position (platform-specific implementation)
            x, y = await self._get_mouse_position()
            
            # Calculate velocity
            time_delta = self.update_interval_ms / 1000  # seconds
            velocity_x = (x - last_x) / time_delta if time_delta > 0 else 0
            velocity_y = (y - last_y) / time_delta if time_delta > 0 else 0
            
            # Detect movement
            movement = abs(x - last_x) + abs(y - last_y)
            if movement > self.movement_threshold:
                self.is_moving = True
                self.last_movement_time = datetime.now()
            else:
                # Check if stopped moving (300ms threshold)
                if (datetime.now() - self.last_movement_time).total_seconds() > 0.3:
                    self.is_moving = False
            
            # Create mouse data
            mouse_data = MouseData(
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                timestamp=datetime.now()
            )
            
            self.current_position = mouse_data
            self.position_history.append(mouse_data)
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(mouse_data)
                except Exception as e:
                    print(f"[MouseMonitor] Callback error: {e}")
            
            # Update last position
            last_x, last_y = x, y
            
            # Ensure 16ms interval
            elapsed_ms = (time.perf_counter() - loop_start) * 1000
            if elapsed_ms < self.update_interval_ms:
                await asyncio.sleep((self.update_interval_ms - elapsed_ms) / 1000)
    
    async def _get_mouse_position(self) -> Tuple[float, float]:
        """Get current mouse position (stub - platform specific)"""
        # This would integrate with OS-specific APIs
        # For now, return default or simulate
        if self.current_position:
            return self.current_position.x, self.current_position.y
        return 0.0, 0.0
    
    def register_callback(self, callback: Callable[[MouseData], None]):
        """Register position update callback"""
        self._callbacks.append(callback)
    
    def get_current_position(self) -> Optional[MouseData]:
        """Get current mouse position"""
        return self.current_position
    
    def get_position_history(self, duration_ms: int = 1000) -> List[MouseData]:
        """Get position history for specified duration"""
        cutoff_time = datetime.now() - timedelta(milliseconds=duration_ms)
        return [p for p in self.position_history if p.timestamp > cutoff_time]
    
    def get_velocity_statistics(self) -> Dict[str, float]:
        """Get velocity statistics from history"""
        if not self.position_history:
            return {"avg_velocity": 0.0, "max_velocity": 0.0}
        
        velocities = [p.velocity for p in self.position_history]
        return {
            "avg_velocity": sum(velocities) / len(velocities),
            "max_velocity": max(velocities),
            "current_velocity": self.current_position.velocity if self.current_position else 0.0
        }
    
    def is_user_active(self, threshold_seconds: float = 60.0) -> bool:
        """Check if user has been active recently"""
        return (datetime.now() - self.last_movement_time).total_seconds() < threshold_seconds


class FileSystemMonitor:
    """
    文件系统监测器 / File system change monitor
    
    Monitors file system changes using polling or OS-specific APIs.
    Tracks file creation, modification, deletion, and moves.
    """
    
    def __init__(self, watch_paths: Optional[List[Path]] = None, poll_interval: float = 1.0):
        self.watch_paths = watch_paths or [Path.home() / "Desktop"]
        self.poll_interval = poll_interval
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[FileSystemEvent], None]] = []
        
        # File state tracking
        self._file_states: Dict[str, Dict[str, Any]] = {}
        self._ignored_patterns = ["*.tmp", "*.log", ".*", "~*"]
    
    async def initialize(self):
        """Initialize file system monitoring"""
        self._running = True
        
        # Initial scan
        await self._scan_all_paths()
        
        # Start monitoring
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def shutdown(self):
        """Shutdown file system monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _scan_all_paths(self):
        """Initial scan of all watched paths"""
        for path in self.watch_paths:
            if path.exists():
                await self._scan_path(path)
    
    async def _scan_path(self, path: Path):
        """Scan a specific path and update state"""
        try:
            for item in path.iterdir():
                if item.is_file() and not self._should_ignore(item):
                    stat = item.stat()
                    self._file_states[str(item)] = {
                        "mtime": stat.st_mtime,
                        "size": stat.st_size
                    }
        except Exception as e:
            print(f"[FileSystemMonitor] Scan error: {e}")
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if file should be ignored"""
        name = path.name
        for pattern in self._ignored_patterns:
            if pattern.startswith("*") and name.endswith(pattern[1:]):
                return True
            if pattern.startswith(".") and name.startswith("."):
                return True
        return False
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            for path in self.watch_paths:
                if path.exists():
                    await self._check_path_changes(path)
            
            await asyncio.sleep(self.poll_interval)
    
    async def _check_path_changes(self, path: Path):
        """Check for changes in a path"""
        try:
            current_files = set()
            
            for item in path.iterdir():
                if item.is_file() and not self._should_ignore(item):
                    item_str = str(item)
                    current_files.add(item_str)
                    
                    try:
                        stat = item.stat()
                        current_state = {
                            "mtime": stat.st_mtime,
                            "size": stat.st_size
                        }
                        
                        # Check if new or modified
                        if item_str not in self._file_states:
                            # New file
                            await self._emit_event(FileSystemEvent(
                                event_id=f"fs_{time.time()}",
                                path=item,
                                event_type="created",
                                is_directory=False,
                                timestamp=datetime.now(),
                                file_size=stat.st_size
                            ))
                        elif self._file_states[item_str]["mtime"] != current_state["mtime"]:
                            # Modified
                            await self._emit_event(FileSystemEvent(
                                event_id=f"fs_{time.time()}",
                                path=item,
                                event_type="modified",
                                is_directory=False,
                                timestamp=datetime.now(),
                                file_size=stat.st_size
                            ))
                        
                        self._file_states[item_str] = current_state
                        
                    except Exception:
                        pass
            
            # Check for deleted files
            for old_file in list(self._file_states.keys()):
                if old_file not in current_files:
                    await self._emit_event(FileSystemEvent(
                        event_id=f"fs_{time.time()}",
                        path=Path(old_file),
                        event_type="deleted",
                        is_directory=False,
                        timestamp=datetime.now()
                    ))
                    del self._file_states[old_file]
                    
        except Exception as e:
            print(f"[FileSystemMonitor] Check error: {e}")
    
    async def _emit_event(self, event: FileSystemEvent):
        """Emit file system event to callbacks"""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[FileSystemMonitor] Callback error: {e}")
    
    def register_callback(self, callback: Callable[[FileSystemEvent], None]):
        """Register file change callback"""
        self._callbacks.append(callback)
    
    def add_watch_path(self, path: Path):
        """Add a path to watch"""
        if path not in self.watch_paths:
            self.watch_paths.append(path)
    
    def remove_watch_path(self, path: Path):
        """Remove a watched path"""
        if path in self.watch_paths:
            self.watch_paths.remove(path)


class TimeMonitor:
    """
    时间监测器 / Time and schedule monitor
    
    Monitors time-based events, schedules, and triggers.
    """
    
    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[TimeEvent], None]] = []
        
        # Scheduled events
        self._scheduled_events: List[TimeEvent] = []
        self._last_check_time = datetime.now()
    
    async def initialize(self):
        """Initialize time monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def shutdown(self):
        """Shutdown time monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            current_time = datetime.now()
            
            # Check scheduled events
            for event in self._scheduled_events[:]:
                if event.trigger_time <= current_time:
                    # Trigger event
                    for callback in self._callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            print(f"[TimeMonitor] Callback error: {e}")
                    
                    # Remove or reschedule
                    if event.is_recurring and event.recurrence_pattern:
                        # Reschedule based on pattern (simplified)
                        event.trigger_time = current_time + timedelta(hours=1)
                    else:
                        self._scheduled_events.remove(event)
            
            self._last_check_time = current_time
            await asyncio.sleep(self.check_interval)
    
    def schedule_event(self, event: TimeEvent):
        """Schedule a new time event"""
        self._scheduled_events.append(event)
        # Sort by trigger time
        self._scheduled_events.sort(key=lambda e: e.trigger_time)
    
    def register_callback(self, callback: Callable[[TimeEvent], None]):
        """Register time event callback"""
        self._callbacks.append(callback)
    
    def get_upcoming_events(self, within_minutes: int = 60) -> List[TimeEvent]:
        """Get events scheduled within specified minutes"""
        cutoff = datetime.now() + timedelta(minutes=within_minutes)
        return [e for e in self._scheduled_events if e.trigger_time <= cutoff]


class SystemStateMonitor:
    """
    系统状态监测器 / System resource monitor
    
    Monitors system resources: CPU, memory, disk, network.
    """
    
    def __init__(self, update_interval: float = 5.0):
        self.update_interval = update_interval
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[SystemStateData], None]] = []
        
        self.current_state: Optional[SystemStateData] = None
        self._state_history: deque = deque(maxlen=100)
        self._start_time = datetime.now()
    
    async def initialize(self):
        """Initialize system monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def shutdown(self):
        """Shutdown system monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                state = await self._collect_system_state()
                self.current_state = state
                self._state_history.append(state)
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(state)
                    except Exception as e:
                        print(f"[SystemStateMonitor] Callback error: {e}")
                
            except Exception as e:
                print(f"[SystemStateMonitor] Collection error: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    async def _collect_system_state(self) -> SystemStateData:
        """Collect current system state"""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network
            net_io = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            }
            
            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except (AttributeError, OSError) as e:
                logger.debug(f"負載平均值獲取失敗（可忽略）: {e}")
                pass
            
            # Process count
            process_count = len(psutil.pids())
            
            return SystemStateData(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                uptime_seconds=(datetime.now() - self._start_time).total_seconds(),
                timestamp=datetime.now(),
                process_count=process_count,
                load_average=load_avg
            )
            
        except ImportError:
            # psutil not available, return default
            return SystemStateData(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={"bytes_sent": 0, "bytes_recv": 0},
                uptime_seconds=(datetime.now() - self._start_time).total_seconds(),
                timestamp=datetime.now()
            )
    
    def register_callback(self, callback: Callable[[SystemStateData], None]):
        """Register state update callback"""
        self._callbacks.append(callback)
    
    def get_current_state(self) -> Optional[SystemStateData]:
        """Get current system state"""
        return self.current_state
    
    def get_state_history(self) -> List[SystemStateData]:
        """Get state history"""
        return list(self._state_history)


class UserActivityMonitor:
    """
    用户活动监测器 / User activity pattern monitor
    
    Monitors and analyzes user activity patterns.
    Detects work, idle, gaming, and other activity states.
    """
    
    def __init__(self, analysis_interval: float = 10.0):
        self.analysis_interval = analysis_interval
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[UserActivityData], None]] = []
        
        # Activity tracking
        self._input_events: deque = deque(maxlen=1000)
        self._last_input_time = datetime.now()
        self._session_start = datetime.now()
        self._current_state = ActivityState.UNKNOWN
        self._window_history: deque = deque(maxlen=100)
        
        # Pattern analysis
        self._activity_patterns: Dict[str, List[datetime]] = {}
    
    async def initialize(self):
        """Initialize user activity monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def shutdown(self):
        """Shutdown user activity monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Analyze current activity
                activity_data = await self._analyze_activity()
                
                # Update current state
                if activity_data.activity_state != self._current_state:
                    self._current_state = activity_data.activity_state
                    
                    # Notify callbacks on state change
                    for callback in self._callbacks:
                        try:
                            callback(activity_data)
                        except Exception as e:
                            print(f"[UserActivityMonitor] Callback error: {e}")
                
            except Exception as e:
                print(f"[UserActivityMonitor] Analysis error: {e}")
            
            await asyncio.sleep(self.analysis_interval)
    
    async def _analyze_activity(self) -> UserActivityData:
        """Analyze current user activity"""
        current_time = datetime.now()
        
        # Calculate idle time
        idle_seconds = (current_time - self._last_input_time).total_seconds()
        
        # Count recent input events
        recent_events = [e for e in self._input_events 
                        if (current_time - e).total_seconds() < 60]
        events_per_minute = len(recent_events)
        
        # Determine activity state
        if idle_seconds > 300:  # 5 minutes
            activity_state = ActivityState.IDLE
        elif events_per_minute > 100:
            activity_state = ActivityState.GAMING
        elif events_per_minute > 50:
            activity_state = ActivityState.TYPING
        elif events_per_minute > 10:
            activity_state = ActivityState.WORKING
        elif idle_seconds > 30:
            activity_state = ActivityState.READING
        else:
            activity_state = ActivityState.ACTIVE
        
        # Calculate focus score
        focus_score = min(1.0, events_per_minute / 100.0)
        if idle_seconds > 60:
            focus_score *= 0.5
        
        # Get active window (stub)
        active_window = await self._get_active_window()
        
        return UserActivityData(
            activity_state=activity_state,
            active_window=active_window,
            idle_time_seconds=idle_seconds,
            input_events_per_minute=events_per_minute,
            session_duration_seconds=(current_time - self._session_start).total_seconds(),
            timestamp=current_time,
            focus_score=focus_score
        )
    
    async def _get_active_window(self) -> Optional[str]:
        """Get currently active window title (stub - platform specific)"""
        # Platform-specific implementation would go here
        return None
    
    def record_input_event(self):
        """Record an input event (keyboard, mouse)"""
        self._last_input_time = datetime.now()
        self._input_events.append(datetime.now())
    
    def register_callback(self, callback: Callable[[UserActivityData], None]):
        """Register activity change callback"""
        self._callbacks.append(callback)
    
    def get_current_activity(self) -> UserActivityData:
        """Get current activity analysis"""
        return asyncio.run(self._analyze_activity())


class RealTimeMonitor:
    """
    实时监测器主类 / Main real-time monitor
    
    Coordinates all monitoring subsystems with unified interface.
    
    Features:
    - 16ms mouse position tracking
    - File system change detection
    - Time-based event monitoring
    - System resource tracking
    - User activity pattern analysis
    """
    
    def __init__(
        self,
        desktop_presence: Optional[Any] = None,
        desktop_interaction: Optional[Any] = None,
        audio_system: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # External system references
        self.desktop_presence = desktop_presence
        self.desktop_interaction = desktop_interaction
        self.audio_system = audio_system
        
        # Sub-monitors
        self.mouse_monitor = MouseMonitor(
            update_interval_ms=self.config.get("mouse_update_interval_ms", 16.0)
        )
        self.file_monitor = FileSystemMonitor(
            watch_paths=self.config.get("watch_paths"),
            poll_interval=self.config.get("file_poll_interval", 1.0)
        )
        self.time_monitor = TimeMonitor(
            check_interval=self.config.get("time_check_interval", 1.0)
        )
        self.system_monitor = SystemStateMonitor(
            update_interval=self.config.get("system_update_interval", 5.0)
        )
        self.activity_monitor = UserActivityMonitor(
            analysis_interval=self.config.get("activity_analysis_interval", 10.0)
        )
        
        # Unified callbacks
        self._callbacks: Dict[str, List[Callable[[Any], None]]] = {
            "mouse_position": [],
            "file_change": [],
            "time_event": [],
            "system_state": [],
            "user_activity": [],
        }
        
        self._running = False
    
    async def initialize(self):
        """Initialize all monitoring subsystems"""
        print("[RealTimeMonitor] Initializing monitoring subsystems...")
        
        # Initialize all monitors
        await self.mouse_monitor.initialize()
        await self.file_monitor.initialize()
        await self.time_monitor.initialize()
        await self.system_monitor.initialize()
        await self.activity_monitor.initialize()
        
        # Setup callback bridges
        self._setup_callback_bridges()
        
        self._running = True
        print("[RealTimeMonitor] All subsystems initialized")
    
    async def shutdown(self):
        """Shutdown all monitoring subsystems"""
        print("[RealTimeMonitor] Shutting down...")
        
        self._running = False
        
        await self.mouse_monitor.shutdown()
        await self.file_monitor.shutdown()
        await self.time_monitor.shutdown()
        await self.system_monitor.shutdown()
        await self.activity_monitor.shutdown()
        
        print("[RealTimeMonitor] Shutdown complete")
    
    def _setup_callback_bridges(self):
        """Setup bridges between sub-monitors and unified callbacks"""
        # Mouse position -> unified callback
        self.mouse_monitor.register_callback(
            lambda data: self._dispatch("mouse_position", {
                "x": data.x,
                "y": data.y,
                "velocity": data.velocity,
                "is_moving": self.mouse_monitor.is_moving
            })
        )
        
        # File changes -> unified callback
        self.file_monitor.register_callback(
            lambda event: self._dispatch("file_change", {
                "path": str(event.path),
                "type": event.event_type,
                "size": event.file_size
            })
        )
        
        # Time events -> unified callback
        self.time_monitor.register_callback(
            lambda event: self._dispatch("time_event", {
                "type": event.event_type,
                "description": event.description
            })
        )
        
        # System state -> unified callback
        self.system_monitor.register_callback(
            lambda state: self._dispatch("system_state", {
                "cpu": state.cpu_percent,
                "memory": state.memory_percent,
                "disk": state.disk_percent
            })
        )
        
        # User activity -> unified callback
        self.activity_monitor.register_callback(
            lambda data: self._dispatch("user_activity", {
                "state": data.activity_state.value[1],
                "idle_time": data.idle_time_seconds,
                "focus_score": data.focus_score
            })
        )
    
    def _dispatch(self, event_type: str, data: Dict[str, Any]):
        """Dispatch event to registered callbacks"""
        callbacks = self._callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"[RealTimeMonitor] Dispatch error: {e}")
    
    def register_callback(self, event_type: str, callback: Callable[[Any], None]):
        """
        Register callback for specific event type
        
        Args:
            event_type: One of "mouse_position", "file_change", "time_event",
                       "system_state", "user_activity"
            callback: Function to call when event occurs
        """
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def get_monitor(self, monitor_type: str) -> Optional[Any]:
        """Get specific sub-monitor by type"""
        monitors = {
            "mouse": self.mouse_monitor,
            "file_system": self.file_monitor,
            "time": self.time_monitor,
            "system": self.system_monitor,
            "activity": self.activity_monitor
        }
        return monitors.get(monitor_type)
    
    def get_current_mouse_position(self) -> Optional[MouseData]:
        """Get current mouse position"""
        return self.mouse_monitor.get_current_position()
    
    def get_user_activity(self) -> UserActivityData:
        """Get current user activity analysis"""
        return self.activity_monitor.get_current_activity()
    
    def get_system_state(self) -> Optional[SystemStateData]:
        """Get current system state"""
        return self.system_monitor.get_current_state()
    
    def schedule_time_event(self, event: TimeEvent):
        """Schedule a time-based event"""
        self.time_monitor.schedule_event(event)
    
    def is_user_active(self, threshold_seconds: float = 60.0) -> bool:
        """Check if user has been active recently"""
        return self.mouse_monitor.is_user_active(threshold_seconds)


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 70)
        print("Angela AI v6.0 - Real-Time Monitor Demo")
        print("实时监测器演示")
        print("=" * 70)
        
        monitor = RealTimeMonitor()
        await monitor.initialize()
        
        # Register some callbacks
        def on_mouse_move(data):
            print(f"[Mouse] Position: ({data['x']:.0f}, {data['y']:.0f}), "
                  f"Velocity: {data['velocity']:.1f}")
        
        def on_file_change(data):
            print(f"[File] {data['type']}: {data['path']}")
        
        def on_user_activity(data):
            print(f"[Activity] State: {data['state']}, "
                  f"Focus: {data['focus_score']:.2f}")
        
        monitor.register_callback("mouse_position", on_mouse_move)
        monitor.register_callback("file_change", on_file_change)
        monitor.register_callback("user_activity", on_user_activity)
        
        # Schedule a test time event
        from datetime import timedelta
        future_event = TimeEvent(
            event_id="test_1",
            event_type="test",
            trigger_time=datetime.now() + timedelta(seconds=3),
            description="Test scheduled event"
        )
        monitor.schedule_time_event(future_event)
        
        def on_time_event(data):
            print(f"[Time] Event: {data['description']}")
        
        monitor.register_callback("time_event", on_time_event)
        
        # Run for 5 seconds
        print("\nMonitoring for 5 seconds...")
        await asyncio.sleep(5)
        
        # Show current state
        print("\n--- Current State ---")
        mouse_pos = monitor.get_current_mouse_position()
        if mouse_pos:
            print(f"Mouse: ({mouse_pos.x:.0f}, {mouse_pos.y:.0f})")
        
        activity = monitor.get_user_activity()
        print(f"Activity: {activity.activity_state.value[1]}")
        
        system = monitor.get_system_state()
        if system:
            print(f"System: CPU {system.cpu_percent:.1f}%, "
                  f"Memory {system.memory_percent:.1f}%")
        
        await monitor.shutdown()
        
        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
    
    asyncio.run(demo())
