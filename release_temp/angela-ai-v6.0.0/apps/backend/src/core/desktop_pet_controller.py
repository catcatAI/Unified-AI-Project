"""
Angela AI v6.0 - Desktop Pet Controller
桌面宠物控制器

Unified controller for Desktop Pet with complete biological system integration.
Manages all Desktop Pet functionality including:
- Live2D model display and animation
- Physiological tactile system
- Emotional blending system
- Extended behavior library
- Autonomous behavior triggering
- User input handling
- Lifecycle management

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
import asyncio
import logging

from apps.backend.src.game.desktop_pet import DesktopPet, DesktopPetState
from apps.backend.src.core.autonomous.live2d_integration import (
    Live2DIntegration, ExpressionType, MotionType, LipSyncState
)
from apps.backend.src.core.autonomous.physiological_tactile import (
    PhysiologicalTactileSystem, TactileStimulus, TactileType, 
    BodyPart, TrajectoryAnalyzer
)
from apps.backend.src.core.autonomous.emotional_blending import (
    EmotionalBlendingSystem, BasicEmotion, PADEmotion, 
    EmotionalExpression, MultidimensionalStateMatrix
)
from apps.backend.src.core.autonomous.extended_behavior_library import (
    ExtendedBehaviorLibrary, BehaviorDefinition, BehaviorCategory,
    BehaviorPriority, BehaviorTrigger
)

logger = logging.getLogger(__name__)


class PetLifecycleState(Enum):
    """宠物生命周期状态 / Pet lifecycle states"""
    INITIALIZING = auto()
    ACTIVE = auto()
    IDLE = auto()
    SLEEPING = auto()
    PAUSED = auto()
    SHUTTING_DOWN = auto()
    ERROR = auto()


@dataclass
class PetConfiguration:
    """宠物配置 / Pet configuration"""
    name: str = "Angela"
    model_path: str = "models/angela/angela.model3.json"
    scale: float = 1.0
    position: Dict[str, int] = field(default_factory=lambda: {"x": 100, "y": 100})
    
    # System configurations
    live2d_config: Dict[str, Any] = field(default_factory=dict)
    tactile_config: Dict[str, Any] = field(default_factory=dict)
    emotional_config: Dict[str, Any] = field(default_factory=dict)
    behavior_config: Dict[str, Any] = field(default_factory=dict)
    
    # Autonomous behavior settings
    autonomous_check_interval: float = 5.0  # seconds
    idle_timeout: float = 300.0  # seconds before sleep
    proactive_message_interval: float = 60.0  # seconds
    
    # Interaction settings
    enable_mouse_tracking: bool = True
    enable_voice_lipsync: bool = True
    enable_tactile_feedback: bool = True


@dataclass
class SystemStatus:
    """系统状态报告 / System status report"""
    lifecycle_state: PetLifecycleState
    pet_state: DesktopPetState
    is_running: bool
    last_error: Optional[str] = None
    error_count: int = 0
    uptime_seconds: float = 0.0
    
    # Biological systems status
    live2d_loaded: bool = False
    tactile_active: bool = False
    emotional_active: bool = False
    behavior_active: bool = False
    
    # Interaction metrics
    total_interactions: int = 0
    last_interaction_time: Optional[datetime] = None
    current_expression: str = "NEUTRAL"
    current_motion: Optional[str] = None


class DesktopPetController:
    """
    Desktop Pet Controller - 统一控制Desktop Pet所有功能
    
    Features:
    - 统一控制Desktop Pet的所有功能
    - 整合PhysiologicalTactileSystem的输入
    - 整合EmotionalBlendingSystem的情绪
    - 整合ExtendedBehaviorLibrary的行为
    - 实时更新Live2D参数
    - 处理用户输入（语音、鼠标、键盘）
    - 自主行为触发（基于内在状态）
    - 完整的生命周期管理
    
    Example:
        >>> config = PetConfiguration(name="Angela")
        >>> controller = DesktopPetController(config, orchestrator=orch)
        >>> 
        >>> # Initialize
        >>> await controller.initialize()
        >>> 
        >>> # Handle user input
        >>> response = await controller.handle_interaction("click", {"x": 100, "y": 200})
        >>> 
        >>> # Get current status
        >>> status = controller.get_status()
        >>> 
        >>> # Shutdown
        >>> await controller.shutdown()
    """
    
    def __init__(
        self, 
        config: PetConfiguration,
        orchestrator: Any = None,
        economy_manager: Any = None
    ):
        """
        Initialize Desktop Pet Controller
        
        Args:
            config: Pet configuration
            orchestrator: Cognitive orchestrator for AI processing
            economy_manager: Economy manager for rewards
        """
        self.config = config
        self.orchestrator = orchestrator
        self.economy_manager = economy_manager
        
        # Lifecycle state
        self.lifecycle_state = PetLifecycleState.INITIALIZING
        self._running = False
        self._initialized = False
        self._start_time: Optional[datetime] = None
        
        # Main pet instance
        self.pet: Optional[DesktopPet] = None
        
        # Background tasks
        self._autonomy_task: Optional[asyncio.Task] = None
        self._update_task: Optional[asyncio.Task] = None
        self._resource_monitor_task: Optional[asyncio.Task] = None
        
        # State tracking
        self._last_autonomy_check = datetime.now()
        self._last_proactive_message = datetime.now()
        self._error_count = 0
        self._last_error: Optional[str] = None
        
        # Mouse tracking
        self._mouse_tracker = TrajectoryAnalyzer()
        self._last_mouse_position: Optional[Tuple[int, int]] = None
        
        # Callbacks
        self._status_callbacks: List[Callable[[SystemStatus], None]] = []
        self._interaction_callbacks: List[Callable[[str, dict], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []
        
        # 4D State Matrix for comprehensive state management
        self.state_matrix = MultidimensionalStateMatrix()
        
        logger.info(f"DesktopPetController created for '{config.name}'")

    async def initialize(self) -> bool:
        """
        Initialize all systems and start the controller
        
        Returns:
            True if initialization successful
        """
        try:
            self.lifecycle_state = PetLifecycleState.INITIALIZING
            logger.info(f"Initializing DesktopPetController for '{self.config.name}'")
            
            # Create and initialize pet
            pet_config = {
                "model_path": self.config.model_path,
                "scale": self.config.scale,
                "live2d": self.config.live2d_config,
                "tactile": self.config.tactile_config,
                "emotional": self.config.emotional_config,
                "behavior": self.config.behavior_config,
            }
            
            self.pet = DesktopPet(
                name=self.config.name,
                orchestrator=self.orchestrator,
                economy_manager=self.economy_manager,
                config=pet_config
            )
            
            await self.pet.initialize()
            
            # Set initial position
            self.pet.position = self.config.position.copy()
            
            # Start background tasks
            self._running = True
            self._start_time = datetime.now()
            
            self._autonomy_task = asyncio.create_task(self._autonomy_loop())
            self._update_task = asyncio.create_task(self._update_loop())
            self._resource_monitor_task = asyncio.create_task(self._resource_monitor_loop())
            
            # Register callbacks
            self.pet.register_state_change_callback(self._on_pet_state_change)
            self.pet.register_expression_callback(self._on_expression_change)
            
            self.lifecycle_state = PetLifecycleState.ACTIVE
            self._initialized = True
            
            logger.info(f"DesktopPetController for '{self.config.name}' initialized successfully")
            return True
            
        except Exception as e:
            self._handle_error(e, "initialization")
            self.lifecycle_state = PetLifecycleState.ERROR
            return False

    async def shutdown(self) -> bool:
        """
        Gracefully shutdown all systems
        
        Returns:
            True if shutdown successful
        """
        try:
            self.lifecycle_state = PetLifecycleState.SHUTTING_DOWN
            logger.info(f"Shutting down DesktopPetController for '{self.config.name}'")
            
            self._running = False
            
            # Cancel background tasks
            tasks = [
                self._autonomy_task,
                self._update_task,
                self._resource_monitor_task
            ]
            
            for task in tasks:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Shutdown pet
            if self.pet:
                await self.pet.shutdown()
            
            self.lifecycle_state = PetLifecycleState.IDLE
            self._initialized = False
            
            logger.info(f"DesktopPetController for '{self.config.name}' shutdown complete")
            return True
            
        except Exception as e:
            self._handle_error(e, "shutdown")
            return False

    async def pause(self):
        """Pause autonomous behaviors (pet stays visible but less active)"""
        self.lifecycle_state = PetLifecycleState.PAUSED
        if self.pet:
            self.pet.set_state(DesktopPetState.IDLE)
        logger.info("Desktop Pet paused")

    async def resume(self):
        """Resume from paused state"""
        if self.lifecycle_state == PetLifecycleState.PAUSED:
            self.lifecycle_state = PetLifecycleState.ACTIVE
            logger.info("Desktop Pet resumed")

    async def handle_interaction(
        self, 
        interaction_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle user interaction
        
        Args:
            interaction_type: Type of interaction (click, message, drag, etc.)
            data: Interaction data
            
        Returns:
            Response dictionary
        """
        if not self._initialized or not self.pet:
            return {"status": "error", "message": "Controller not initialized"}
        
        try:
            # Update state matrix
            self._update_state_matrix_from_interaction(interaction_type, data)
            
            # Handle via pet
            response = await self.pet.handle_user_input(interaction_type, data)
            
            # Notify callbacks
            for callback in self._interaction_callbacks:
                try:
                    callback(interaction_type, data)
                except Exception:
                    pass
            
            return response
            
        except Exception as e:
            self._handle_error(e, f"handle_interaction_{interaction_type}")
            return {"status": "error", "message": str(e)}

    async def handle_mouse_move(self, x: int, y: int):
        """
        Handle mouse movement for tracking and gaze following
        
        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
        """
        if not self.config.enable_mouse_tracking or not self.pet:
            return
        
        # Track trajectory
        self._mouse_tracker.add_point(x, y)
        
        # Check for hover over pet
        pet_rect = self._get_pet_bounding_box()
        if self._is_point_in_rect(x, y, pet_rect):
            await self.handle_interaction("hover", {"x": x, "y": y})
        
        self._last_mouse_position = (x, y)

    async def handle_voice_input(self, text: str, phonemes: List[str] = None):
        """
        Handle voice input with lip-sync
        
        Args:
            text: Recognized text
            phonemes: List of phonemes for lip-sync (optional)
        """
        if not self.pet:
            return
        
        payload = {
            "text": text,
            "phonemes": phonemes or self._extract_phonemes_from_text(text)
        }
        
        return await self.handle_interaction("voice", payload)

    async def trigger_expression(self, expression: ExpressionType, duration: float = 3.0):
        """
        Manually trigger an expression
        
        Args:
            expression: Expression to show
            duration: How long to show the expression (seconds)
        """
        if self.pet:
            self.pet.live2d.set_expression(expression)
            
            # Schedule return to neutral
            async def return_to_neutral():
                await asyncio.sleep(duration)
                if self.pet:
                    self.pet.live2d.set_expression(ExpressionType.NEUTRAL)
            
            asyncio.create_task(return_to_neutral())

    async def trigger_motion(self, motion: MotionType, loop: bool = False):
        """
        Manually trigger a motion
        
        Args:
            motion: Motion to play
            loop: Whether to loop the motion
        """
        if self.pet:
            await self.pet.live2d.play_motion(motion, loop=loop)

    def get_status(self) -> SystemStatus:
        """Get current system status"""
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()
        
        status = SystemStatus(
            lifecycle_state=self.lifecycle_state,
            pet_state=self.pet.state if self.pet else DesktopPetState.IDLE,
            is_running=self._running,
            last_error=self._last_error,
            error_count=self._error_count,
            uptime_seconds=uptime,
            live2d_loaded=self.pet.live2d.model_loaded if self.pet else False,
            tactile_active=self.pet.tactile_system._running if self.pet else False,
            emotional_active=self.pet.emotional_system._running if self.pet else False,
            behavior_active=self.pet.behavior_library._running if self.pet else False,
            total_interactions=self.pet.interaction_count if self.pet else 0,
            last_interaction_time=self.pet.last_interaction_time if self.pet else None,
            current_expression=self.pet.live2d.current_expression.name if self.pet else "NEUTRAL",
            current_motion=self.pet.live2d.current_motion.name if self.pet and self.pet.live2d.current_motion else None
        )
        
        return status

    def get_4d_state_summary(self) -> Dict[str, Any]:
        """Get 4D state matrix summary"""
        return self.state_matrix.get_state_summary()

    async def save_state(self) -> Dict[str, Any]:
        """Save complete state for persistence"""
        if not self.pet:
            return {}
        
        return {
            "controller": {
                "lifecycle_state": self.lifecycle_state.name,
                "error_count": self._error_count,
                "uptime": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
            },
            "pet": await self.pet.save_state(),
            "state_matrix": self.state_matrix.get_state_summary(),
            "timestamp": datetime.now().isoformat()
        }

    async def load_state(self, state_data: Dict[str, Any]) -> bool:
        """Load complete state from saved data"""
        try:
            if "pet" in state_data and self.pet:
                await self.pet.load_state(state_data["pet"])
            
            # Restore state matrix if present
            if "state_matrix" in state_data:
                matrix_data = state_data["state_matrix"]
                self.state_matrix.set_alpha_dimension(**matrix_data.get("alpha", {}))
                self.state_matrix.set_beta_dimension(**matrix_data.get("beta", {}))
                self.state_matrix.set_gamma_dimension(**matrix_data.get("gamma", {}))
                self.state_matrix.set_delta_dimension(**matrix_data.get("delta", {}))
            
            logger.info("State loaded successfully")
            return True
        except Exception as e:
            self._handle_error(e, "load_state")
            return False

    def register_status_callback(self, callback: Callable[[SystemStatus], None]):
        """Register callback for status updates"""
        self._status_callbacks.append(callback)

    def register_interaction_callback(self, callback: Callable[[str, dict], None]):
        """Register callback for interactions"""
        self._interaction_callbacks.append(callback)

    def register_error_callback(self, callback: Callable[[Exception], None]):
        """Register callback for errors"""
        self._error_callbacks.append(callback)

    # === Internal Methods ===

    async def _autonomy_loop(self):
        """Background loop for autonomous behaviors"""
        while self._running:
            try:
                if self.lifecycle_state == PetLifecycleState.ACTIVE and self.pet:
                    # Check for autonomous behavior triggers
                    await self.pet.trigger_autonomous_behavior()
                    
                    # Check for proactive messages
                    await self._check_proactive_messages()
                    
                    # Check idle timeout
                    await self._check_idle_timeout()
                
                await asyncio.sleep(self.config.autonomous_check_interval)
            except Exception as e:
                self._handle_error(e, "autonomy_loop")
                await asyncio.sleep(5.0)  # Wait longer after error

    async def _update_loop(self):
        """Background loop for state updates"""
        while self._running:
            try:
                if self.pet:
                    # Compute inter-dimensional influences
                    self.state_matrix.compute_inter_influences()
                    
                    # Apply emotional influences from state matrix
                    gamma = self.state_matrix.get_dimension_state("gamma")
                    if gamma.get("happiness", 0) > 0.7:
                        self.pet.emotional_system.apply_influence(
                            "cognitive", "positive_environment", 0.3, 0.5
                        )
                    
                    # Update 4D state matrix from biological systems
                    self._sync_state_matrix()
                
                # Notify status callbacks
                status = self.get_status()
                for callback in self._status_callbacks:
                    try:
                        callback(status)
                    except Exception:
                        pass
                
                await asyncio.sleep(1.0)
            except Exception as e:
                self._handle_error(e, "update_loop")
                await asyncio.sleep(5.0)

    async def _resource_monitor_loop(self):
        """Monitor system resources"""
        while self._running:
            try:
                # Check if pet systems are healthy
                if self.pet:
                    systems_healthy = (
                        self.pet.live2d._running and
                        self.pet.tactile_system._running and
                        self.pet.emotional_system._running and
                        self.pet.behavior_library._running
                    )
                    
                    if not systems_healthy and self.lifecycle_state == PetLifecycleState.ACTIVE:
                        logger.warning("Some biological systems are not running, attempting recovery")
                        await self._recover_systems()
                
                await asyncio.sleep(10.0)
            except Exception as e:
                self._handle_error(e, "resource_monitor")
                await asyncio.sleep(30.0)

    async def _check_proactive_messages(self):
        """Check if it's time for a proactive message"""
        elapsed = (datetime.now() - self._last_proactive_message).total_seconds()
        
        if elapsed >= self.config.proactive_message_interval:
            # Trigger proactive message via actor
            if self.pet:
                await self.pet.actor.check_and_queue_proactive_messages.remote()
                messages = await self.pet.actor.get_proactive_messages.remote()
                
                if messages:
                    # Display first message
                    msg = messages[0]
                    logger.info(f"Proactive message: {msg.get('text', '')}")
                    
                    # Set appropriate expression
                    if msg.get("tone") == "cheerful":
                        self.pet.live2d.set_expression(ExpressionType.HAPPY)
                    elif msg.get("tone") == "concerned":
                        self.pet.live2d.set_expression(ExpressionType.SAD)
            
            self._last_proactive_message = datetime.now()

    async def _check_idle_timeout(self):
        """Check if pet should enter sleep mode due to inactivity"""
        if not self.pet:
            return
        
        idle_time = (datetime.now() - self.pet.last_interaction_time).total_seconds()
        
        if idle_time >= self.config.idle_timeout:
            if self.pet.state != DesktopPetState.SLEEPING:
                self.pet.set_state(DesktopPetState.SLEEPING)
                self.pet.live2d.set_expression(ExpressionType.TIRED)
                await self.pet.behavior_library.start_behavior("sleep_mode")
                logger.info("Pet entered sleep mode due to inactivity")
        elif idle_time >= self.config.idle_timeout / 2:
            if self.pet.state == DesktopPetState.IDLE:
                # Start seeking attention
                await self.pet.behavior_library.start_behavior("attention_seek")

    async def _recover_systems(self):
        """Attempt to recover failed systems"""
        try:
            if self.pet:
                if not self.pet.live2d._running:
                    logger.info("Recovering Live2D system")
                    await self.pet.live2d.initialize()
                
                if not self.pet.tactile_system._running:
                    logger.info("Recovering tactile system")
                    await self.pet.tactile_system.initialize()
                
                if not self.pet.emotional_system._running:
                    logger.info("Recovering emotional system")
                    await self.pet.emotional_system.initialize()
                
                if not self.pet.behavior_library._running:
                    logger.info("Recovering behavior library")
                    await self.pet.behavior_library.initialize()
        except Exception as e:
            logger.error(f"System recovery failed: {e}")

    def _sync_state_matrix(self):
        """Sync 4D state matrix with biological systems"""
        if not self.pet:
            return
        
        # Alpha: Physiological
        tactile_state = self.pet.tactile_system
        self.state_matrix.set_alpha_dimension(
            energy=1.0 - (tactile_state.arousal_level / 100),
            comfort=0.8 if len(tactile_state.active_stimuli) > 0 else 0.5,
            arousal=tactile_state.arousal_level / 100,
            rest_need=0.3 if self.pet.state == DesktopPetState.SLEEPING else 0.1
        )
        
        # Gamma: Emotional
        emotion = self.pet.emotional_system.current_emotion
        dominant, _ = self.pet.emotional_system.get_dominant_emotion()
        
        self.state_matrix.set_gamma_dimension(
            happiness=max(0, emotion.pleasure * emotion.intensity),
            sadness=max(0, -emotion.pleasure * emotion.intensity) if emotion.pleasure < 0 else 0,
            anger=1.0 if dominant.name == "ANGER" else 0.1,
            fear=1.0 if dominant.name == "FEAR" else 0.1,
            trust=0.8 if dominant.name == "TRUST" else 0.5,
        )
        
        # Delta: Social
        idle_time = (datetime.now() - self.pet.last_interaction_time).total_seconds()
        self.state_matrix.set_delta_dimension(
            attention=1.0 if idle_time < 60 else 0.3,
            bond=0.7,  # Would come from relationship system
            trust=0.8,
            presence=1.0 if self.pet.visible else 0.0
        )

    def _update_state_matrix_from_interaction(self, interaction_type: str, data: Dict):
        """Update state matrix based on user interaction"""
        # Beta: Cognitive
        if interaction_type == "message":
            self.state_matrix.set_beta_dimension(
                curiosity=0.8,
                focus=0.9,
                learning=0.7
            )
        elif interaction_type == "click":
            self.state_matrix.set_beta_dimension(
                curiosity=0.6,
                focus=0.7
            )

    def _on_pet_state_change(self, old_state: DesktopPetState, new_state: DesktopPetState):
        """Handle pet state changes"""
        logger.debug(f"Pet state changed: {old_state.value} -> {new_state.value}")

    def _on_expression_change(self, expression):
        """Handle expression changes"""
        # Could trigger additional actions here
        pass

    def _get_pet_bounding_box(self) -> Tuple[int, int, int, int]:
        """Get pet's bounding box (x, y, width, height)"""
        if not self.pet:
            return (0, 0, 0, 0)
        
        scale = self.pet.scale
        x = self.pet.position["x"]
        y = self.pet.position["y"]
        width = int(200 * scale)  # Approximate size
        height = int(300 * scale)
        
        return (x, y, width, height)

    def _is_point_in_rect(self, x: int, y: int, rect: Tuple[int, int, int, int]) -> bool:
        """Check if point is inside rectangle"""
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def _extract_phonemes_from_text(self, text: str) -> List[str]:
        """Extract simplified phonemes from text for lip-sync"""
        # Simplified phoneme extraction
        phonemes = []
        vowels = {'a', 'e', 'i', 'o', 'u'}
        
        for char in text.lower():
            if char in vowels:
                phonemes.append(char)
            elif char == ' ':
                phonemes.append('silence')
            elif char in 'nm':
                phonemes.append('n')
        
        return phonemes if phonemes else ['silence']

    def _handle_error(self, error: Exception, context: str):
        """Handle and log errors"""
        self._error_count += 1
        self._last_error = f"{context}: {str(error)}"
        logger.error(f"Error in {context}: {error}")
        
        # Notify error callbacks
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception:
                pass


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 60)
        print("Angela AI v6.0 - Desktop Pet Controller Demo")
        print("=" * 60)
        
        # Create configuration
        config = PetConfiguration(
            name="Angela",
            model_path="models/angela/angela.model3.json",
            enable_mouse_tracking=True,
            enable_voice_lipsync=True
        )
        
        # Create controller
        controller = DesktopPetController(config)
        
        # Register callbacks
        def on_status(status: SystemStatus):
            print(f"Status: {status.lifecycle_state.name}, Expression: {status.current_expression}")
        
        def on_interaction(interaction_type: str, data: dict):
            print(f"Interaction: {interaction_type}")
        
        controller.register_status_callback(on_status)
        controller.register_interaction_callback(on_interaction)
        
        # Initialize
        print("\n1. Initializing controller...")
        success = await controller.initialize()
        print(f"   Initialization: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Get status
            print("\n2. Getting status...")
            status = controller.get_status()
            print(f"   State: {status.lifecycle_state.name}")
            print(f"   Live2D Loaded: {status.live2d_loaded}")
            
            # Simulate interactions
            print("\n3. Simulating interactions...")
            
            # Click
            response = await controller.handle_interaction("click", {"x": 150, "y": 200})
            print(f"   Click response: {response.get('pet_response', 'N/A')[:50]}...")
            
            # Hover
            await controller.handle_mouse_move(160, 210)
            
            # Message
            response = await controller.handle_interaction("message", {"text": "Hello Angela!"})
            print(f"   Message handled")
            
            # Get 4D state
            print("\n4. 4D State Matrix Summary:")
            summary = controller.get_4d_state_summary()
            print(f"   Wellbeing: {summary['computed']['wellbeing']:.2f}")
            print(f"   Arousal: {summary['computed']['arousal']:.2f}")
            
            # Save state
            print("\n5. Saving state...")
            state = await controller.save_state()
            print(f"   State saved with {len(state)} keys")
            
            # Let it run for a bit
            print("\n6. Running autonomous behaviors for 3 seconds...")
            await asyncio.sleep(3)
            
            # Final status
            final_status = controller.get_status()
            print(f"   Total interactions: {final_status.total_interactions}")
            print(f"   Uptime: {final_status.uptime_seconds:.1f}s")
            
            # Shutdown
            print("\n7. Shutting down...")
            await controller.shutdown()
            print("   Shutdown complete")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)
    
    asyncio.run(demo())
