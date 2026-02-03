"""
Angela AI v6.0 - Desktop Presence System
桌面存在系统

Manages Angela's desktop presence including global mouse tracking,
body collision detection, layer management (click-through), and wallpaper mode.

Features:
- Global mouse position tracking
- Body collision detection with desktop elements
- Layer management with click-through support
- Wallpaper mode for ambient presence
- Screen boundary awareness

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime
import asyncio


class PresenceMode(Enum):
    """存在模式 / Presence modes"""
    INTERACTIVE = ("交互模式", "Interactive")  # Normal desktop pet mode
    WALLPAPER = ("壁纸模式", "Wallpaper")      # Background wallpaper mode
    MINIMAL = ("极简模式", "Minimal")          # Minimal presence
    HIDDEN = ("隐藏", "Hidden")                # Not visible


class LayerMode(Enum):
    """图层模式 / Layer modes"""
    TOPMOST = ("置顶", "Topmost")              # Always on top
    NORMAL = ("普通", "Normal")                # Normal window
    CLICK_THROUGH = ("点击穿透", "Click-through")  # Mouse passes through
    BELOW_ICONS = ("图标下方", "Below Icons")   # Behind desktop icons


@dataclass
class Position:
    """位置 / 2D position"""
    x: float
    y: float
    
    def distance_to(self, other: Position) -> float:
        """Calculate Euclidean distance to another position"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __add__(self, other: Position) -> Position:
        return Position(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: Position) -> Position:
        return Position(self.x - other.x, self.y - other.y)


@dataclass
class Size:
    """尺寸 / 2D size"""
    width: float
    height: float


@dataclass
class BoundingBox:
    """边界框 / Bounding box"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def center(self) -> Position:
        """Get center position"""
        return Position(self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def corners(self) -> List[Position]:
        """Get all four corners"""
        return [
            Position(self.x, self.y),
            Position(self.x + self.width, self.y),
            Position(self.x, self.y + self.height),
            Position(self.x + self.width, self.y + self.height)
        ]
    
    def contains(self, point: Position) -> bool:
        """Check if point is inside bounding box"""
        return (self.x <= point.x <= self.x + self.width and
                self.y <= point.y <= self.y + self.height)
    
    def intersects(self, other: BoundingBox) -> bool:
        """Check if this bounding box intersects with another"""
        return not (self.x + self.width < other.x or
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or
                   other.y + other.height < self.y)


@dataclass
class CollisionInfo:
    """碰撞信息 / Collision information"""
    is_colliding: bool
    collision_point: Optional[Position] = None
    collision_object: Optional[str] = None
    penetration_depth: float = 0.0
    normal: Optional[Position] = None


@dataclass
class MouseState:
    """鼠标状态 / Mouse state"""
    position: Position
    is_pressed: bool = False
    button: Optional[str] = None  # left, right, middle
    velocity: Position = field(default_factory=lambda: Position(0, 0))
    timestamp: datetime = field(default_factory=datetime.now)


class DesktopPresence:
    """
    桌面存在系统主类 / Main desktop presence system class
    
    Manages Angela's physical presence on the desktop including position tracking,
    collision detection, layer management, and interaction modes.
    
    Attributes:
        current_position: Current position on screen
        body_size: Size of Angela's body
        screen_bounds: Screen boundary dimensions
        presence_mode: Current presence mode
        layer_mode: Current layer mode
        mouse_tracker: Global mouse tracking state
    
    Example:
        >>> presence = DesktopPresence()
        >>> await presence.initialize()
        >>> 
        >>> # Set position
        >>> presence.set_position(Position(100, 100))
        >>> 
        >>> # Check collision with desktop icon
        >>> icon_box = BoundingBox(150, 150, 64, 64)
        >>> collision = presence.check_collision(icon_box)
        >>> if collision.is_colliding:
        ...     print(f"Colliding with icon at {collision.collision_point}")
        >>> 
        >>> # Enable click-through mode
        >>> presence.set_layer_mode(LayerMode.CLICK_THROUGH)
        >>> 
        >>> # Enter wallpaper mode
        >>> presence.set_presence_mode(PresenceMode.WALLPAPER)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Position and size
        self.current_position: Position = Position(100, 100)
        self.body_size: Size = Size(
            self.config.get("body_width", 200),
            self.config.get("body_height", 300)
        )
        
        # Screen boundaries
        self.screen_bounds: Size = Size(
            self.config.get("screen_width", 1920),
            self.config.get("screen_height", 1080)
        )
        
        # Modes
        self.presence_mode: PresenceMode = PresenceMode.INTERACTIVE
        self.layer_mode: LayerMode = LayerMode.TOPMOST
        self.opacity: float = 1.0
        
        # Mouse tracking
        self.mouse_tracker: MouseTracker = MouseTracker()
        self.last_mouse_position: Optional[Position] = None
        
        # Collision
        self.collision_enabled: bool = True
        self.collision_callbacks: List[Callable[[CollisionInfo], None]] = []
        self.collision_objects: Dict[str, BoundingBox] = {}
        
        # Running state
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._position_callbacks: List[Callable[[Position, Position], None]] = []
        self._mode_change_callbacks: List[Callable[[Any, Any], None]] = []
    
    async def initialize(self):
        """Initialize the desktop presence system"""
        self._running = True
        
        # Start mouse tracking
        await self.mouse_tracker.initialize()
        self.mouse_tracker.register_callback(self._on_mouse_move)
        
        # Start update loop
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the system"""
        self._running = False
        
        await self.mouse_tracker.shutdown()
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop"""
        while self._running:
            await self._update_collision_detection()
            await self._enforce_screen_boundaries()
            await asyncio.sleep(0.033)  # ~30 FPS
    
    async def _update_collision_detection(self):
        """Update collision detection"""
        if not self.collision_enabled:
            return
        
        my_bounds = self.get_bounding_box()
        
        for obj_name, obj_bounds in self.collision_objects.items():
            if my_bounds.intersects(obj_bounds):
                # Calculate collision info
                collision = self._calculate_collision(my_bounds, obj_bounds, obj_name)
                
                # Notify callbacks
                for callback in self.collision_callbacks:
                    try:
                        callback(collision)
                    except Exception:
                        pass
    
    def _calculate_collision(
        self, 
        my_bounds: BoundingBox, 
        other_bounds: BoundingBox,
        obj_name: str
    ) -> CollisionInfo:
        """Calculate collision details between two bounding boxes"""
        # Calculate overlap
        left = max(my_bounds.x, other_bounds.x)
        right = min(my_bounds.x + my_bounds.width, 
                    other_bounds.x + other_bounds.width)
        top = max(my_bounds.y, other_bounds.y)
        bottom = min(my_bounds.y + my_bounds.height,
                     other_bounds.y + other_bounds.height)
        
        overlap_width = right - left
        overlap_height = bottom - top
        
        # Collision center
        collision_x = left + overlap_width / 2
        collision_y = top + overlap_height / 2
        
        # Calculate normal (direction to resolve collision)
        dx = my_bounds.center.x - other_bounds.center.x
        dy = my_bounds.center.y - other_bounds.center.y
        
        # Normalize
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length > 0:
            dx /= length
            dy /= length
        
        return CollisionInfo(
            is_colliding=True,
            collision_point=Position(collision_x, collision_y),
            collision_object=obj_name,
            penetration_depth=min(overlap_width, overlap_height),
            normal=Position(dx, dy)
        )
    
    async def _enforce_screen_boundaries(self):
        """Keep Angela within screen boundaries"""
        x = max(0, min(self.current_position.x, 
                       self.screen_bounds.width - self.body_size.width))
        y = max(0, min(self.current_position.y,
                       self.screen_bounds.height - self.body_size.height))
        
        if x != self.current_position.x or y != self.current_position.y:
            self.set_position(Position(x, y))
    
    def _on_mouse_move(self, position: Position):
        """Handle mouse movement"""
        if self.last_mouse_position:
            velocity = Position(
                position.x - self.last_mouse_position.x,
                position.y - self.last_mouse_position.y
            )
            # Store for velocity-based interactions
            pass
        
        self.last_mouse_position = position
    
    def set_position(self, position: Position):
        """
        Set Angela's position on screen
        
        Args:
            position: New position
        """
        old_position = self.current_position
        self.current_position = position
        
        # Notify callbacks
        for callback in self._position_callbacks:
            try:
                callback(old_position, position)
            except Exception:
                pass
    
    def move_by(self, delta: Position):
        """Move by relative amount"""
        new_position = Position(
            self.current_position.x + delta.x,
            self.current_position.y + delta.y
        )
        self.set_position(new_position)
    
    def get_bounding_box(self) -> BoundingBox:
        """Get current bounding box"""
        return BoundingBox(
            x=self.current_position.x,
            y=self.current_position.y,
            width=self.body_size.width,
            height=self.body_size.height
        )
    
    def set_presence_mode(self, mode: PresenceMode):
        """
        Set presence mode
        
        Args:
            mode: New presence mode
        """
        old_mode = self.presence_mode
        self.presence_mode = mode
        
        # Adjust properties based on mode
        if mode == PresenceMode.WALLPAPER:
            self.opacity = 0.6
            self.layer_mode = LayerMode.BELOW_ICONS
            self.collision_enabled = False
        elif mode == PresenceMode.MINIMAL:
            self.body_size = Size(50, 75)
        elif mode == PresenceMode.INTERACTIVE:
            self.opacity = 1.0
            self.layer_mode = LayerMode.TOPMOST
            self.collision_enabled = True
            self.body_size = Size(
                self.config.get("body_width", 200),
                self.config.get("body_height", 300)
            )
        
        # Notify callbacks
        for callback in self._mode_change_callbacks:
            try:
                callback(old_mode, mode)
            except Exception:
                pass
    
    def set_layer_mode(self, mode: LayerMode):
        """
        Set layer mode (affects mouse interaction)
        
        Args:
            mode: New layer mode
        """
        old_mode = self.layer_mode
        self.layer_mode = mode
        
        # Notify callbacks
        for callback in self._mode_change_callbacks:
            try:
                callback(old_mode, mode)
            except Exception:
                pass
    
    def set_opacity(self, opacity: float):
        """Set opacity level (0-1)"""
        self.opacity = max(0.0, min(1.0, opacity))
    
    def register_collision_object(self, name: str, bounds: BoundingBox):
        """Register an object for collision detection"""
        self.collision_objects[name] = bounds
    
    def unregister_collision_object(self, name: str):
        """Unregister a collision object"""
        if name in self.collision_objects:
            del self.collision_objects[name]
    
    def check_collision(self, other_bounds: BoundingBox) -> CollisionInfo:
        """Check collision with a specific bounding box"""
        my_bounds = self.get_bounding_box()
        
        if my_bounds.intersects(other_bounds):
            return self._calculate_collision(my_bounds, other_bounds, "external")
        
        return CollisionInfo(is_colliding=False)
    
    def is_point_inside(self, point: Position) -> bool:
        """Check if a point is inside Angela's body"""
        return self.get_bounding_box().contains(point)
    
    def register_position_callback(
        self, 
        callback: Callable[[Position, Position], None]
    ):
        """Register callback for position changes"""
        self._position_callbacks.append(callback)
    
    def register_collision_callback(self, callback: Callable[[CollisionInfo], None]):
        """Register callback for collision events"""
        self.collision_callbacks.append(callback)
    
    def register_mode_change_callback(self, callback: Callable[[Any, Any], None]):
        """Register callback for mode changes"""
        self._mode_change_callbacks.append(callback)
    
    def get_screen_center(self) -> Position:
        """Get screen center position"""
        return Position(
            self.screen_bounds.width / 2 - self.body_size.width / 2,
            self.screen_bounds.height / 2 - self.body_size.height / 2
        )
    
    def snap_to_edge(self, edge: str):
        """Snap Angela to screen edge"""
        if edge == "left":
            self.set_position(Position(0, self.current_position.y))
        elif edge == "right":
            self.set_position(Position(
                self.screen_bounds.width - self.body_size.width,
                self.current_position.y
            ))
        elif edge == "top":
            self.set_position(Position(self.current_position.x, 0))
        elif edge == "bottom":
            self.set_position(Position(
                self.current_position.x,
                self.screen_bounds.height - self.body_size.height
            ))


class MouseTracker:
    """
    鼠标追踪器 / Global mouse tracker
    
    Tracks global mouse position and state across the entire desktop.
    """
    
    def __init__(self):
        self.current_position: Position = Position(0, 0)
        self.is_tracking: bool = False
        self._callbacks: List[Callable[[Position], None]] = []
        self._tracking_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize mouse tracking"""
        self.is_tracking = True
        self._tracking_task = asyncio.create_task(self._track_loop())
    
    async def shutdown(self):
        """Shutdown mouse tracking"""
        self.is_tracking = False
        if self._tracking_task:
            self._tracking_task.cancel()
            try:
                await self._tracking_task
            except asyncio.CancelledError:
                pass
    
    async def _track_loop(self):
        """Track mouse position"""
        while self.is_tracking:
            # This would integrate with OS-level mouse tracking
            # For now, simulate tracking
            await self._update_mouse_position()
            await asyncio.sleep(0.033)  # ~30 FPS
    
    async def _update_mouse_position(self):
        """Update current mouse position"""
        # Platform-specific mouse tracking would go here
        # For demonstration, keeping position static
        pass
    
    def get_position(self) -> Position:
        """Get current mouse position"""
        return self.current_position
    
    def register_callback(self, callback: Callable[[Position], None]):
        """Register position update callback"""
        self._callbacks.append(callback)
    
    def update_position(self, position: Position):
        """Update position (called by OS integration)"""
        if position != self.current_position:
            self.current_position = position
            for callback in self._callbacks:
                try:
                    callback(position)
                except Exception:
                    pass


# Example usage
if __name__ == "__main__":
    async def demo():
        presence = DesktopPresence()
        await presence.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 桌面存在系统演示")
        print("Desktop Presence System Demo")
        print("=" * 60)
        
        # Set position
        print("\n设置位置 / Setting position:")
        presence.set_position(Position(500, 300))
        print(f"  位置: ({presence.current_position.x}, {presence.current_position.y})")
        
        # Check bounding box
        bounds = presence.get_bounding_box()
        print(f"  边界框: x={bounds.x}, y={bounds.y}, w={bounds.width}, h={bounds.height}")
        
        # Collision detection
        print("\n碰撞检测 / Collision detection:")
        icon_box = BoundingBox(400, 250, 64, 64)
        collision = presence.check_collision(icon_box)
        print(f"  与图标碰撞: {collision.is_colliding}")
        if collision.is_colliding and collision.collision_point:
            print(f"  碰撞点: ({collision.collision_point.x}, {collision.collision_point.y})")
        
        # Change modes
        print("\n模式切换 / Mode switching:")
        presence.set_presence_mode(PresenceMode.WALLPAPER)
        print(f"  壁纸模式: opacity={presence.opacity}, layer={presence.layer_mode.name}")
        
        presence.set_presence_mode(PresenceMode.INTERACTIVE)
        print(f"  交互模式: opacity={presence.opacity}, layer={presence.layer_mode.name}")
        
        # Layer mode
        print("\n图层模式 / Layer modes:")
        for mode in LayerMode:
            print(f"  {mode.value[0]} ({mode.value[1]})")
        
        await presence.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
