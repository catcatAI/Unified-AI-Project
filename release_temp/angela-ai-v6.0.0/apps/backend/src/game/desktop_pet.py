"""
Angela AI v6.0 - Desktop Pet
桌面宠物系统

Complete implementation of Angela's Desktop Pet with:
- Live2D model loading and display
- Real-time expression updates based on emotional state
- Action execution based on behavior library
- Voice lip-sync
- Mouse interaction response
- Desktop presence awareness
- Integration with autonomous system

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
import ray

from apps.backend.src.game.desktop_pet_actor import DesktopPetActor
from apps.backend.src.game.economy_manager import EconomyManager
from apps.backend.src.core.autonomous.live2d_integration import (
    Live2DIntegration, ExpressionType, MotionType
)
from apps.backend.src.core.autonomous.physiological_tactile import (
    PhysiologicalTactileSystem, TactileStimulus, TactileType, BodyPart
)
from apps.backend.src.core.autonomous.emotional_blending import (
    EmotionalBlendingSystem, BasicEmotion, PADEmotion
)
from apps.backend.src.core.autonomous.extended_behavior_library import (
    ExtendedBehaviorLibrary, BehaviorCategory
)

logger = logging.getLogger(__name__)


class DesktopPetState(Enum):
    """桌面宠物状态 / Desktop pet states"""
    IDLE = "idle"
    INTERACTING = "interacting"
    SLEEPING = "sleeping"
    THINKING = "thinking"
    PERFORMING = "performing"
    MOVED = "moved"


class DesktopPet:
    """
    Desktop Pet - Complete implementation with biological systems integration
    
    Features:
    - Live2D model display with real-time expressions
    - Physiological tactile system for touch interactions
    - Emotional blending system for authentic emotions
    - Extended behavior library with 25+ behaviors
    - Voice synchronization with lip-sync
    - Mouse interaction handling
    - Desktop presence awareness
    - Autonomous behavior triggering
    
    Example:
        >>> pet = DesktopPet("Angela", orchestrator=orch, economy_manager=econ)
        >>> await pet.initialize()
        >>> 
        >>> # Handle user input
        >>> response = await pet.handle_user_input("click", {"x": 100, "y": 200})
        >>> 
        >>> # Get current expression
        >>> expression = pet.get_current_expression()
        >>> 
        >>> # Trigger autonomous behavior
        >>> await pet.trigger_autonomous_behavior()
    """

    def __init__(
        self, 
        name: str, 
        orchestrator: Any = None, 
        economy_manager: EconomyManager | None = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize Desktop Pet
        
        Args:
            name: Pet name
            orchestrator: Cognitive orchestrator actor handle
            economy_manager: Economy manager actor handle
            config: Configuration dictionary
        """
        # Initialize Ray if not already done
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            
        self.name = name
        self.config = config or {}
        
        # Create the remote actor
        self.actor = DesktopPetActor.remote(name, orchestrator, economy_manager)
        
        # Biological systems
        self.live2d = Live2DIntegration(config=self.config.get("live2d"))
        self.tactile_system = PhysiologicalTactileSystem(config=self.config.get("tactile"))
        self.emotional_system = EmotionalBlendingSystem(config=self.config.get("emotional"))
        self.behavior_library = ExtendedBehaviorLibrary(config=self.config.get("behavior"))
        
        # State tracking
        self.state = DesktopPetState.IDLE
        self.position = {"x": 0, "y": 0}
        self.scale = self.config.get("scale", 1.0)
        self.visible = True
        self._running = False
        
        # Interaction tracking
        self.last_interaction_time = datetime.now()
        self.interaction_count = 0
        self.mouse_trail = []  # Track mouse movement for trajectory analysis
        
        # Callbacks
        self._state_change_callbacks: List[Callable] = []
        self._expression_callbacks: List[Callable] = []
        
        logger.info(f"DesktopPet '{name}' initialized with full biological systems")

    async def initialize(self):
        """Initialize all biological systems"""
        self._running = True
        
        # Initialize Live2D
        await self.live2d.initialize()
        model_path = self.config.get("model_path", "models/angela/angela.model3.json")
        await self.live2d.load_model(model_path)
        
        # Initialize tactile system
        await self.tactile_system.initialize()
        
        # Initialize emotional system
        await self.emotional_system.initialize()
        
        # Initialize behavior library
        await self.behavior_library.initialize()
        
        # Register callbacks
        self.emotional_system.register_expression_callback(self._on_expression_change)
        self.tactile_system.register_stimulus_callback(self._on_tactile_stimulus)
        
        # Set initial expression
        self.live2d.set_expression(ExpressionType.NEUTRAL)
        
        logger.info(f"DesktopPet '{self.name}' systems initialized")

    async def shutdown(self):
        """Shutdown all systems gracefully"""
        self._running = False
        
        await self.live2d.shutdown()
        await self.tactile_system.shutdown()
        await self.emotional_system.shutdown()
        await self.behavior_library.shutdown()
        
        logger.info(f"DesktopPet '{self.name}' shutdown complete")

    def _on_expression_change(self, expression):
        """Handle emotional expression changes"""
        # Map emotional expression to Live2D expression
        facial = expression.facial
        if facial.smile > 0.5:
            self.live2d.set_expression(ExpressionType.HAPPY)
        elif facial.smile < -0.3:
            self.live2d.set_expression(ExpressionType.SAD)
        elif expression.vocal.tremor > 0.3:
            self.live2d.set_expression(ExpressionType.SURPRISED)
        elif facial.blush > 0.5:
            self.live2d.set_expression(ExpressionType.SHY)
        
        # Notify callbacks
        for callback in self._expression_callbacks:
            try:
                callback(expression)
            except Exception:
                pass

    def _on_tactile_stimulus(self, stimulus: TactileStimulus):
        """Handle tactile stimulus events"""
        # Convert tactile to emotional influence
        if stimulus.tactile_type == TactileType.LIGHT_TOUCH:
            self.emotional_system.apply_influence("physiological", "comfort", 0.3, 0.5)
        elif stimulus.tactile_type == TactileType.PRESSURE:
            self.emotional_system.apply_influence("physiological", "comfort", 0.2, 0.4)
        elif stimulus.tactile_type == TactileType.PAIN:
            self.emotional_system.apply_influence("physiological", "pain", -0.5, 0.8)
        
        logger.debug(f"Tactile stimulus processed: {stimulus.tactile_type.name} at {stimulus.location.cn_name}")

    def set_state(self, new_state: DesktopPetState):
        """Set desktop pet state and notify callbacks"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            # Notify callbacks
            for callback in self._state_change_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception:
                    pass
            
            logger.debug(f"State changed: {old_state.value} -> {new_state.value}")

    async def handle_user_input(
        self,
        input_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle user input with biological system integration
        
        Args:
            input_type: Type of input (click, message, drag, gift, hover, etc.)
            payload: Input data
            
        Returns:
            Response dictionary with visual and emotional feedback
        """
        logger.debug(f"Pet '{self.name}' received input: {input_type}")
        
        response = {
            "status": "processed", 
            "pet_response": "",
            "expression_change": None,
            "motion_triggered": None
        }
        
        # Update interaction tracking
        self.last_interaction_time = datetime.now()
        self.interaction_count += 1
        
        # Process based on input type
        if input_type == "click":
            response.update(await self._handle_click(payload))
        elif input_type == "double_click":
            response.update(await self._handle_double_click(payload))
        elif input_type == "message":
            response.update(await self._handle_message(payload))
        elif input_type == "drag":
            response.update(await self._handle_drag(payload))
        elif input_type == "gift":
            response.update(await self._handle_gift(payload))
        elif input_type == "hover":
            response.update(await self._handle_hover(payload))
        elif input_type == "voice":
            response.update(await self._handle_voice(payload))
        else:
            response["status"] = "unsupported_input"
            response["pet_response"] = "I don't understand that interaction."
        
        # Trigger appropriate behavior based on input
        await self._trigger_behavior_for_input(input_type, response)
        
        return response

    async def _handle_click(self, payload: dict) -> dict:
        """Handle click interaction with tactile and emotional response"""
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        
        # Determine body part from click location (simplified)
        body_part = self._get_body_part_from_position(x, y)
        
        # Create tactile stimulus
        stimulus = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=3.0,
            location=body_part,
            duration=0.5,
            source="user_click",
            emotional_tag="comfort"
        )
        
        # Process tactile
        tactile_response = await self.tactile_system.process_stimulus(stimulus)
        
        # Emotional response
        self.emotional_system.apply_influence("cognitive", "positive_interaction", 0.4, 0.6)
        
        # Update favorability via actor
        await self.actor.increase_favorability.remote(1, quality_score=0.8)
        
        # Visual feedback
        self.live2d.set_expression(ExpressionType.HAPPY)
        await self.live2d.play_motion(MotionType.NODDING)
        
        return {
            "pet_response": f"*giggles* You clicked my {body_part.cn_name}!",
            "tactile_intensity": tactile_response.perceived_intensity,
            "body_part": body_part.cn_name
        }

    async def _handle_double_click(self, payload: dict) -> dict:
        """Handle double click - stronger interaction"""
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        body_part = self._get_body_part_from_position(x, y)
        
        stimulus = TactileStimulus(
            tactile_type=TactileType.PRESSURE,
            intensity=5.0,
            location=body_part,
            duration=1.0,
            source="user_double_click",
            emotional_tag="excitement"
        )
        
        await self.tactile_system.process_stimulus(stimulus)
        self.emotional_system.apply_influence("cognitive", "playful_interaction", 0.6, 0.7)
        await self.actor.increase_favorability.remote(2, quality_score=0.9)
        
        self.live2d.set_expression(ExpressionType.EXCITED)
        await self.live2d.play_motion(MotionType.CELEBRATING)
        
        return {
            "pet_response": "Oh! Double click! That tickles!",
            "expression": "excited"
        }

    async def _handle_message(self, payload: dict) -> dict:
        """Handle message input with emotional analysis"""
        result = await self.actor.handle_user_input.remote("message", payload)
        
        # Analyze message sentiment (simplified)
        user_message = payload.get("text", "").lower()
        if any(word in user_message for word in ["happy", "great", "awesome", "love"]):
            self.emotional_system.set_emotion_from_basic(BasicEmotion.JOY, intensity=0.7)
            self.live2d.set_expression(ExpressionType.HAPPY)
        elif any(word in user_message for word in ["sad", "sorry", "miss", "cry"]):
            self.emotional_system.set_emotion_from_basic(BasicEmotion.SADNESS, intensity=0.6)
            self.live2d.set_expression(ExpressionType.SAD)
        elif any(word in user_message for word in ["angry", "hate", "mad", "annoying"]):
            self.emotional_system.set_emotion_from_basic(BasicEmotion.ANGER, intensity=0.5)
            self.live2d.set_expression(ExpressionType.ANGRY)
        
        return ray.get(result)

    async def _handle_drag(self, payload: dict) -> dict:
        """Handle drag interaction"""
        new_x = payload.get("x", self.position["x"])
        new_y = payload.get("y", self.position["y"])
        
        # Calculate drag distance
        dx = new_x - self.position["x"]
        dy = new_y - self.position["y"]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        self.position = {"x": new_x, "y": new_y}
        
        # Tactile feedback
        stimulus = TactileStimulus(
            tactile_type=TactileType.VIBRATION,
            intensity=min(distance / 10, 5.0),
            location=BodyPart.HANDS,
            duration=0.3,
            source="user_drag"
        )
        await self.tactile_system.process_stimulus(stimulus)
        
        # Slight favorability decrease (being moved)
        await self.actor.decrease_favorability.remote(1)
        
        # Update emotional state
        if distance > 50:
            self.emotional_system.set_emotion_from_basic(BasicEmotion.SURPRISE, intensity=0.4)
            self.live2d.set_expression(ExpressionType.SURPRISED)
        
        self.set_state(DesktopPetState.MOVED)
        
        return {
            "pet_response": f"Whee! You moved me to ({new_x}, {new_y})!",
            "distance": distance
        }

    async def _handle_gift(self, payload: dict) -> dict:
        """Handle gift interaction"""
        result = await self.actor.handle_user_input.remote("gift", payload)
        
        # Happy response to gift
        self.emotional_system.set_emotion_from_basic(BasicEmotion.JOY, intensity=0.8)
        self.live2d.set_expression(ExpressionType.LOVE)
        await self.live2d.play_motion(MotionType.CLAPPING)
        
        return ray.get(result)

    async def _handle_hover(self, payload: dict) -> dict:
        """Handle mouse hover with gaze tracking"""
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        
        # Track mouse position for eye tracking
        # Convert screen coordinates to normalized (-1 to 1)
        center_x = self.position["x"] + 100  # Approximate center
        center_y = self.position["y"] + 150
        
        norm_x = (x - center_x) / 200  # Normalize
        norm_y = (y - center_y) / 200
        
        # Clamp to valid range
        norm_x = max(-1, min(1, norm_x))
        norm_y = max(-1, min(1, norm_y))
        
        # Make Live2D model look at cursor
        self.live2d.look_at(norm_x, norm_y)
        
        return {
            "pet_response": "",
            "gaze_x": norm_x,
            "gaze_y": norm_y
        }

    async def _handle_voice(self, payload: dict) -> dict:
        """Handle voice input with lip-sync"""
        text = payload.get("text", "")
        phonemes = payload.get("phonemes", [])
        
        # Start lip-sync
        self.live2d.start_lip_sync()
        
        # Process phonemes for lip-sync
        for phoneme in phonemes:
            self.live2d.update_lip_sync(phoneme, mouth_openness=0.8)
            await asyncio.sleep(0.1)  # Simulate timing
        
        self.live2d.stop_lip_sync()
        
        return {
            "pet_response": f"I heard you say: '{text}'",
            "lip_sync_duration": len(phonemes) * 0.1
        }

    def _get_body_part_from_position(self, x: int, y: int) -> BodyPart:
        """Map click position to body part (simplified)"""
        # Simplified mapping based on typical Live2D model regions
        rel_x = x - self.position["x"]
        rel_y = y - self.position["y"]
        
        if rel_y < 50:
            return BodyPart.FACE
        elif rel_y < 120:
            return BodyPart.CHEST
        elif rel_x < 100:
            return BodyPart.HANDS
        else:
            return BodyPart.SHOULDERS

    async def _trigger_behavior_for_input(self, input_type: str, response: dict):
        """Trigger appropriate behavior based on input type"""
        behavior_map = {
            "click": "greeting_wave",
            "double_click": "celebration_dance",
            "message": "listening_nod",
            "drag": "surprise_reaction",
            "gift": "celebration_dance",
        }
        
        behavior_id = behavior_map.get(input_type)
        if behavior_id:
            await self.behavior_library.start_behavior(behavior_id)
            response["motion_triggered"] = behavior_id

    async def trigger_autonomous_behavior(self):
        """Trigger autonomous behavior based on internal state"""
        # Check emotional state
        emotion_summary = self.emotional_system.get_emotion_summary()
        dominant_emotion = emotion_summary["dominant_emotion"]
        
        # Check time since last interaction
        idle_time = (datetime.now() - self.last_interaction_time).total_seconds()
        
        context = {
            "time": idle_time,
            "emotion": emotion_summary["confidence"],
            "stimulus": 1.0 if idle_time > 300 else 0.0,
            "proximity": 1.0,  # Assume user nearby for now
        }
        
        # Check for triggerable behaviors
        triggerable = self.behavior_library.check_triggers(context)
        
        if triggerable:
            behavior = triggerable[0]  # Get highest priority
            await self.behavior_library.start_behavior(behavior.behavior_id)
            
            # Set appropriate expression
            if behavior.category == BehaviorCategory.IDLE:
                self.live2d.set_expression(ExpressionType.NEUTRAL)
            elif behavior.category == BehaviorCategory.SOCIAL:
                self.live2d.set_expression(ExpressionType.HAPPY)
            
            logger.info(f"Autonomous behavior triggered: {behavior.name}")
            return behavior.behavior_id
        
        return None

    def get_current_expression(self) -> ExpressionType:
        """Get current Live2D expression"""
        return self.live2d.current_expression

    def get_emotional_state(self) -> dict:
        """Get current emotional state summary"""
        return self.emotional_system.get_emotion_summary()

    def get_tactile_state(self) -> dict:
        """Get current tactile system state"""
        return {
            "arousal_level": self.tactile_system.arousal_level,
            "active_stimuli": len(self.tactile_system.active_stimuli),
        }

    def register_state_change_callback(self, callback: Callable):
        """Register callback for state changes"""
        self._state_change_callbacks.append(callback)

    def register_expression_callback(self, callback: Callable):
        """Register callback for expression changes"""
        self._expression_callbacks.append(callback)

    async def save_state(self) -> dict:
        """Save current state for persistence"""
        return {
            "name": self.name,
            "position": self.position,
            "state": self.state.value,
            "expression": self.live2d.current_expression.name,
            "emotion": self.emotional_system.get_emotion_summary(),
            "last_interaction": self.last_interaction_time.isoformat(),
            "interaction_count": self.interaction_count,
        }

    async def load_state(self, state_data: dict):
        """Load state from saved data"""
        self.position = state_data.get("position", {"x": 0, "y": 0})
        self.state = DesktopPetState(state_data.get("state", "idle"))
        self.last_interaction_time = datetime.fromisoformat(
            state_data.get("last_interaction", datetime.now().isoformat())
        )
        self.interaction_count = state_data.get("interaction_count", 0)
        
        # Restore expression
        expr_name = state_data.get("expression", "NEUTRAL")
        try:
            self.live2d.set_expression(ExpressionType[expr_name])
        except KeyError:
            self.live2d.set_expression(ExpressionType.NEUTRAL)
        
        logger.info(f"State loaded for '{self.name}'")

    async def check_and_queue_proactive_messages(self):
        return await self.actor.check_and_queue_proactive_messages.remote()

    def get_proactive_messages(self, clear_queue: bool = True) -> list:
        return ray.get(self.actor.get_proactive_messages.remote(clear_queue))

    async def handle_user_input(
        self,
        input_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.actor.handle_user_input.remote(input_type, payload)

    async def increase_favorability(self, amount: int, quality_score: float = 1.0):
        return await self.actor.increase_favorability.remote(amount, quality_score)

    async def decrease_favorability(self, amount: int):
        return await self.actor.decrease_favorability.remote(amount)

    async def check_for_proactive_interaction(self) -> str:
        return await self.actor.check_for_proactive_interaction.remote()

    async def update_state(self):
        return await self.actor.update_state.remote()
