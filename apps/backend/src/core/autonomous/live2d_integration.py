"""
Angela AI v6.0 - Live2D Integration
Live2D集成系统

Manages Live2D model control, expression parameters, motion control,
and lip-sync for Angela AI's visual representation.

Features:
- Live2D model loading and control
- Facial expression parameter management
- Motion and animation control
- Lip synchronization with speech
- Parameter interpolation

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
import asyncio
import math


class ExpressionType(Enum):
    """表情类型 / Expression types"""
    NEUTRAL = ("自然", "Neutral")
    HAPPY = ("开心", "Happy")
    SAD = ("悲伤", "Sad")
    ANGRY = ("生气", "Angry")
    SURPRISED = ("惊讶", "Surprised")
    SHY = ("害羞", "Shy")
    CONFUSED = ("困惑", "Confused")
    EXCITED = ("兴奋", "Excited")
    TIRED = ("疲倦", "Tired")
    LOVE = ("爱慕", "Love")


class MotionType(Enum):
    """动作类型 / Motion types"""
    IDLE = ("待机", "Idle")
    GREETING = ("问候", "Greeting")
    THINKING = ("思考", "Thinking")
    DANCING = ("跳舞", "Dancing")
    WAVING = ("挥手", "Waving")
    NODDING = ("点头", "Nodding")
    SHAKING_HEAD = ("摇头", "Shaking Head")
    CLAPPING = ("拍手", "Clapping")
    CELEBRATING = ("庆祝", "Celebrating")
    SLEEPING = ("睡觉", "Sleeping")


@dataclass
class Live2DParameter:
    """Live2D参数 / Live2D parameter"""
    name: str
    value: float
    min_value: float = 0.0
    max_value: float = 1.0
    default_value: float = 0.0
    
    def __post_init__(self):
        self.value = max(self.min_value, min(self.max_value, self.value))
    
    def set_value(self, value: float):
        """Set parameter value with clamping"""
        self.value = max(self.min_value, min(self.max_value, value))


@dataclass
class Live2DExpression:
    """Live2D表情 / Live2D expression"""
    expression_type: ExpressionType
    parameters: Dict[str, float]  # Parameter name -> value
    blend_duration: float = 0.3   # Seconds to blend to this expression
    priority: int = 0


@dataclass
class Live2DAction:
    """Live2D动作 / Live2D action/motion"""
    motion_type: MotionType
    duration: float              # Duration in seconds
    loop: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0


@dataclass
class LipSyncState:
    """口型同步状态 / Lip synchronization state"""
    is_active: bool = False
    current_phoneme: str = "silence"  # Current phoneme being spoken
    mouth_openness: float = 0.0       # 0-1, how open the mouth is
    mouth_width: float = 0.5          # 0-1, mouth width
    vowel_sound: Optional[str] = None  # a, i, u, e, o for Japanese lip sync


class Live2DIntegration:
    """
    Live2D集成系统主类 / Main Live2D integration class
    
    Manages Angela's Live2D model including expressions, motions, and lip-sync.
    Provides a high-level interface for controlling the visual representation.
    
    Attributes:
        model_loaded: Whether a model is currently loaded
        current_expression: Current facial expression
        current_motion: Current playing motion
        parameters: All Live2D parameters
        lip_sync: Current lip-sync state
    
    Example:
        >>> live2d = Live2DIntegration()
        >>> await live2d.initialize()
        >>> 
        >>> # Load model
        >>> await live2d.load_model("path/to/angela_model.model3.json")
        >>> 
        >>> # Set expression
        >>> live2d.set_expression(ExpressionType.HAPPY)
        >>> 
        >>> # Play motion
        >>> await live2d.play_motion(MotionType.GREETING)
        >>> 
        >>> # Start lip-sync
        >>> live2d.start_lip_sync()
        >>> live2d.update_lip_sync("a", mouth_openness=0.8)  # 'a' sound
        >>> 
        >>> # Set specific parameter
        >>> live2d.set_parameter("ParamAngleX", 15.0)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Model state
        self.model_loaded: bool = False
        self.model_path: Optional[str] = None
        
        # Current state
        self.current_expression: ExpressionType = ExpressionType.NEUTRAL
        self.current_motion: Optional[MotionType] = None
        self.is_motion_playing: bool = False
        
        # Parameters
        self.parameters: Dict[str, Live2DParameter] = {}
        self._default_parameters()
        
        # Lip sync
        self.lip_sync: LipSyncState = LipSyncState()
        self._lip_sync_active: bool = False
        
        # Expression blending
        self._target_expression: Optional[Live2DExpression] = None
        self._current_expression_obj: Optional[Live2DExpression] = None
        self._expression_blend_progress: float = 1.0
        
        # Motion queue
        self._motion_queue: List[Live2DAction] = []
        self._current_motion_obj: Optional[Live2DAction] = None
        
        # Running state
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._parameter_callbacks: Dict[str, List[Callable[[float], None]]] = {}
        self._expression_callbacks: List[Callable[[ExpressionType], None]] = []
        self._motion_callbacks: List[Callable[[MotionType], None]] = []
    
    def _default_parameters(self):
        """Initialize default Live2D parameters"""
        # Facial angle
        self.parameters["ParamAngleX"] = Live2DParameter("ParamAngleX", 0.0, -30.0, 30.0)
        self.parameters["ParamAngleY"] = Live2DParameter("ParamAngleY", 0.0, -30.0, 30.0)
        self.parameters["ParamAngleZ"] = Live2DParameter("ParamAngleZ", 0.0, -30.0, 30.0)
        
        # Eye control
        self.parameters["ParamEyeLOpen"] = Live2DParameter("ParamEyeLOpen", 1.0, 0.0, 1.0)
        self.parameters["ParamEyeROpen"] = Live2DParameter("ParamEyeROpen", 1.0, 0.0, 1.0)
        self.parameters["ParamEyeLSmile"] = Live2DParameter("ParamEyeLSmile", 0.0, 0.0, 1.0)
        self.parameters["ParamEyeRSmile"] = Live2DParameter("ParamEyeRSmile", 0.0, 0.0, 1.0)
        
        # Eye movement
        self.parameters["ParamEyeBallX"] = Live2DParameter("ParamEyeBallX", 0.0, -1.0, 1.0)
        self.parameters["ParamEyeBallY"] = Live2DParameter("ParamEyeBallY", 0.0, -1.0, 1.0)
        
        # Eyebrows
        self.parameters["ParamBrowLY"] = Live2DParameter("ParamBrowLY", 0.0, -1.0, 1.0)
        self.parameters["ParamBrowRY"] = Live2DParameter("ParamBrowRY", 0.0, -1.0, 1.0)
        self.parameters["ParamBrowLAngle"] = Live2DParameter("ParamBrowLAngle", 0.0, -1.0, 1.0)
        self.parameters["ParamBrowRAngle"] = Live2DParameter("ParamBrowRAngle", 0.0, -1.0, 1.0)
        self.parameters["ParamBrowLForm"] = Live2DParameter("ParamBrowLForm", 0.0, -1.0, 1.0)
        self.parameters["ParamBrowRForm"] = Live2DParameter("ParamBrowRForm", 0.0, -1.0, 1.0)
        
        # Mouth
        self.parameters["ParamMouthForm"] = Live2DParameter("ParamMouthForm", 0.0, -1.0, 1.0)
        self.parameters["ParamMouthOpenY"] = Live2DParameter("ParamMouthOpenY", 0.0, 0.0, 1.0)
        
        # Cheeks and blush
        self.parameters["ParamCheek"] = Live2DParameter("ParamCheek", 0.0, 0.0, 1.0)
        
        # Body
        self.parameters["ParamBodyAngleX"] = Live2DParameter("ParamBodyAngleX", 0.0, -10.0, 10.0)
        self.parameters["ParamBodyAngleY"] = Live2DParameter("ParamBodyAngleY", 0.0, -10.0, 10.0)
        self.parameters["ParamBodyAngleZ"] = Live2DParameter("ParamBodyAngleZ", 0.0, -10.0, 10.0)
        
        # Breathing
        self.parameters["ParamBreath"] = Live2DParameter("ParamBreath", 0.0, 0.0, 1.0)
        
        # Hair
        self.parameters["ParamHairFront"] = Live2DParameter("ParamHairFront", 0.0, -1.0, 1.0)
        self.parameters["ParamHairSide"] = Live2DParameter("ParamHairSide", 0.0, -1.0, 1.0)
        self.parameters["ParamHairBack"] = Live2DParameter("ParamHairBack", 0.0, -1.0, 1.0)
        
        # Arms (if present)
        self.parameters["ParamArmLA"] = Live2DParameter("ParamArmLA", 0.0, -1.0, 1.0)
        self.parameters["ParamArmRA"] = Live2DParameter("ParamArmRA", 0.0, -1.0, 1.0)
    
    async def initialize(self):
        """Initialize the Live2D integration"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the system"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop for animations and blending"""
        while self._running:
            await self._update_expression_blending()
            await self._update_motion()
            await self._update_breathing()
            await self._update_lip_sync()
            await asyncio.sleep(0.033)  # ~30 FPS
    
    async def _update_expression_blending(self):
        """Update expression parameter blending"""
        if self._target_expression and self._expression_blend_progress < 1.0:
            self._expression_blend_progress += 0.05  # Blend speed
            self._expression_blend_progress = min(1.0, self._expression_blend_progress)
            
            # Interpolate parameters
            if self._current_expression_obj:
                for param_name, target_value in self._target_expression.parameters.items():
                    if param_name in self.parameters:
                        current_value = self._current_expression_obj.parameters.get(
                            param_name, 
                            self.parameters[param_name].default_value
                        )
                        
                        # Linear interpolation
                        new_value = current_value + (target_value - current_value) * 0.05
                        self.parameters[param_name].set_value(new_value)
    
    async def _update_motion(self):
        """Update motion playback"""
        if self.is_motion_playing and self._current_motion_obj:
            # Check if motion should end
            if not self._current_motion_obj.loop:
                # This would integrate with actual motion playback
                pass
    
    async def _update_breathing(self):
        """Update breathing animation"""
        # Sine wave breathing
        import time
        breath = (math.sin(time.time() * 2) + 1) / 2  # 0 to 1
        self.parameters["ParamBreath"].set_value(breath * 0.3)  # Subtle breathing
    
    async def _update_lip_sync(self):
        """Update lip sync animation"""
        if self._lip_sync_active and self.lip_sync.is_active:
            # Update mouth parameters based on current phoneme
            self._apply_phoneme_to_mouth(self.lip_sync.current_phoneme)
    
    def _apply_phoneme_to_mouth(self, phoneme: str):
        """Apply phoneme to mouth parameters"""
        phoneme_shapes = {
            "silence": {"ParamMouthOpenY": 0.0, "ParamMouthForm": 0.0},
            "a": {"ParamMouthOpenY": 0.8, "ParamMouthForm": 0.0},   # Wide open
            "i": {"ParamMouthOpenY": 0.3, "ParamMouthForm": 0.5},   # Spread
            "u": {"ParamMouthOpenY": 0.2, "ParamMouthForm": -0.5},  # Rounded
            "e": {"ParamMouthOpenY": 0.4, "ParamMouthForm": 0.0},   # Neutral open
            "o": {"ParamMouthOpenY": 0.5, "ParamMouthForm": -0.8},  # O shape
            "n": {"ParamMouthOpenY": 0.1, "ParamMouthForm": 0.0},   # Closed
        }
        
        shapes = phoneme_shapes.get(phoneme, phoneme_shapes["silence"])
        
        for param_name, value in shapes.items():
            if param_name in self.parameters:
                # Smooth transition
                current = self.parameters[param_name].value
                target = value * self.lip_sync.mouth_openness
                self.parameters[param_name].set_value(current + (target - current) * 0.3)
    
    async def load_model(self, model_path: str) -> bool:
        """
        Load a Live2D model
        
        Args:
            model_path: Path to model file
            
        Returns:
            True if successful
        """
        # This would integrate with actual Live2D SDK
        self.model_path = model_path
        self.model_loaded = True
        return True
    
    def set_expression(
        self, 
        expression: ExpressionType, 
        blend_duration: float = 0.3
    ):
        """
        Set facial expression
        
        Args:
            expression: Expression to set
            blend_duration: Time to blend to new expression
        """
        self.current_expression = expression
        
        # Create expression parameters
        expr_params = self._get_expression_parameters(expression)
        self._target_expression = Live2DExpression(
            expression_type=expression,
            parameters=expr_params,
            blend_duration=blend_duration
        )
        
        self._current_expression_obj = Live2DExpression(
            expression_type=self.current_expression,
            parameters={
                k: self.parameters[k].value 
                for k in self.parameters.keys()
            }
        )
        
        self._expression_blend_progress = 0.0
        
        # Notify callbacks
        for callback in self._expression_callbacks:
            try:
                callback(expression)
            except Exception:
                pass
    
    def _get_expression_parameters(self, expression: ExpressionType) -> Dict[str, float]:
        """Get parameter values for an expression"""
        expressions = {
            ExpressionType.NEUTRAL: {
                "ParamEyeLOpen": 1.0, "ParamEyeROpen": 1.0,
                "ParamMouthForm": 0.0, "ParamMouthOpenY": 0.0,
                "ParamBrowLY": 0.0, "ParamBrowRY": 0.0,
                "ParamCheek": 0.0
            },
            ExpressionType.HAPPY: {
                "ParamEyeLOpen": 0.8, "ParamEyeROpen": 0.8,
                "ParamEyeLSmile": 1.0, "ParamEyeRSmile": 1.0,
                "ParamMouthForm": 0.5, "ParamMouthOpenY": 0.3,
                "ParamBrowLY": 0.3, "ParamBrowRY": 0.3,
                "ParamCheek": 0.5
            },
            ExpressionType.SAD: {
                "ParamEyeLOpen": 0.7, "ParamEyeROpen": 0.7,
                "ParamMouthForm": -0.3, "ParamMouthOpenY": 0.0,
                "ParamBrowLY": -0.5, "ParamBrowRY": -0.5,
                "ParamBrowLAngle": -0.5, "ParamBrowRAngle": -0.5,
                "ParamCheek": 0.0
            },
            ExpressionType.ANGRY: {
                "ParamEyeLOpen": 0.9, "ParamEyeROpen": 0.9,
                "ParamMouthForm": -0.5, "ParamMouthOpenY": 0.1,
                "ParamBrowLY": 0.2, "ParamBrowRY": 0.2,
                "ParamBrowLAngle": 0.8, "ParamBrowRAngle": 0.8,
                "ParamCheek": 0.3
            },
            ExpressionType.SURPRISED: {
                "ParamEyeLOpen": 1.0, "ParamEyeROpen": 1.0,
                "ParamMouthForm": 0.0, "ParamMouthOpenY": 0.8,
                "ParamBrowLY": -0.8, "ParamBrowRY": -0.8,
                "ParamCheek": 0.0
            },
            ExpressionType.SHY: {
                "ParamEyeLOpen": 0.5, "ParamEyeROpen": 0.5,
                "ParamEyeBallY": 0.3,
                "ParamMouthForm": 0.2, "ParamMouthOpenY": 0.0,
                "ParamCheek": 0.8
            },
            ExpressionType.LOVE: {
                "ParamEyeLOpen": 0.7, "ParamEyeROpen": 0.7,
                "ParamEyeLSmile": 0.8, "ParamEyeRSmile": 0.8,
                "ParamMouthForm": 0.4, "ParamMouthOpenY": 0.1,
                "ParamBrowLY": 0.2, "ParamBrowRY": 0.2,
                "ParamCheek": 0.6
            },
        }
        
        return expressions.get(expression, expressions[ExpressionType.NEUTRAL])
    
    async def play_motion(self, motion: MotionType, loop: bool = False) -> bool:
        """
        Play a motion/animation
        
        Args:
            motion: Motion type to play
            loop: Whether to loop the motion
            
        Returns:
            True if motion started
        """
        action = Live2DAction(
            motion_type=motion,
            duration=2.0,  # Default duration
            loop=loop
        )
        
        self._motion_queue.append(action)
        self.current_motion = motion
        self.is_motion_playing = True
        
        # Notify callbacks
        for callback in self._motion_callbacks:
            try:
                callback(motion)
            except Exception:
                pass
        
        return True
    
    def stop_motion(self):
        """Stop current motion"""
        self.is_motion_playing = False
        self._current_motion_obj = None
        self._motion_queue.clear()
    
    def start_lip_sync(self):
        """Start lip synchronization"""
        self._lip_sync_active = True
        self.lip_sync.is_active = True
    
    def stop_lip_sync(self):
        """Stop lip synchronization"""
        self._lip_sync_active = False
        self.lip_sync.is_active = False
        self.lip_sync.current_phoneme = "silence"
        self.lip_sync.mouth_openness = 0.0
        
        # Reset mouth
        self.parameters["ParamMouthOpenY"].set_value(0.0)
    
    def update_lip_sync(self, phoneme: str, mouth_openness: float = 1.0):
        """
        Update lip sync with current phoneme
        
        Args:
            phoneme: Current phoneme (a, i, u, e, o, n, or silence)
            mouth_openness: How open the mouth should be (0-1)
        """
        self.lip_sync.current_phoneme = phoneme
        self.lip_sync.mouth_openness = max(0.0, min(1.0, mouth_openness))
    
    def set_parameter(self, name: str, value: float):
        """
        Set a specific parameter value
        
        Args:
            name: Parameter name
            value: Parameter value
        """
        if name in self.parameters:
            self.parameters[name].set_value(value)
            
            # Notify callbacks
            if name in self._parameter_callbacks:
                for callback in self._parameter_callbacks[name]:
                    try:
                        callback(value)
                    except Exception:
                        pass
    
    def get_parameter(self, name: str) -> float:
        """Get current parameter value"""
        if name in self.parameters:
            return self.parameters[name].value
        return 0.0
    
    def look_at(self, x: float, y: float):
        """
        Make model look at a point
        
        Args:
            x: X coordinate (-1 to 1, where 0 is center)
            y: Y coordinate (-1 to 1, where 0 is center)
        """
        # Clamp to valid range
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        # Update eye and head tracking
        self.set_parameter("ParamEyeBallX", x)
        self.set_parameter("ParamEyeBallY", y)
        self.set_parameter("ParamAngleX", x * 15)  # Subtle head movement
        self.set_parameter("ParamAngleY", y * 10)
    
    def reset_pose(self):
        """Reset all parameters to default values"""
        for param in self.parameters.values():
            param.set_value(param.default_value)
        
        self.current_expression = ExpressionType.NEUTRAL
    
    def register_expression_callback(self, callback: Callable[[ExpressionType], None]):
        """Register expression change callback"""
        self._expression_callbacks.append(callback)
    
    def register_motion_callback(self, callback: Callable[[MotionType], None]):
        """Register motion change callback"""
        self._motion_callbacks.append(callback)
    
    def register_parameter_callback(
        self, 
        param_name: str, 
        callback: Callable[[float], None]
    ):
        """Register parameter change callback"""
        if param_name not in self._parameter_callbacks:
            self._parameter_callbacks[param_name] = []
        self._parameter_callbacks[param_name].append(callback)
    
    def get_all_parameters(self) -> Dict[str, float]:
        """Get all current parameter values"""
        return {name: param.value for name, param in self.parameters.items()}
    
    # Body-to-Live2D Integration Methods
    def apply_body_touch(
        self,
        body_part: str,
        touch_type: str = "pat",
        intensity: float = 0.5,
        duration: float = 1.0
    ) -> Dict[str, float]:
        """
        Apply body touch to Live2D parameters
        
        Args:
            body_part: Body part being touched (e.g., "top_of_head", "face")
            touch_type: Type of touch (pat, stroke, poke, pinch, etc.)
            intensity: Touch intensity (0-1)
            duration: Animation duration in seconds
            
        Returns:
            Applied parameter values
        """
        # Get parameter changes based on body part and touch type
        param_changes = self._get_body_touch_parameters(body_part, touch_type, intensity)
        
        # Apply parameters
        for param_name, value in param_changes.items():
            if param_name in self.parameters:
                self.set_parameter(param_name, value)
        
        return param_changes
    
    def _get_body_touch_parameters(
        self,
        body_part: str,
        touch_type: str,
        intensity: float
    ) -> Dict[str, float]:
        """Get parameter changes for body touch (using physiological mapping)"""
        # Import from physiological_tactile to ensure consistency
        from .physiological_tactile import BODY_TO_LIVE2D_MAPPING
        
        if body_part not in BODY_TO_LIVE2D_MAPPING:
            return {}
        
        part_mapping = BODY_TO_LIVE2D_MAPPING[body_part]
        touch_mapping = part_mapping.get(touch_type, part_mapping.get("pat", {}))
        
        params = {}
        for param_name, (min_val, max_val) in touch_mapping.items():
            value = min_val + (max_val - min_val) * intensity
            params[param_name] = value
        
        return params
    
    def apply_emotion_to_expression(self, emotion: str, intensity: float = 0.8):
        """
        Apply emotion to Live2D expression parameters
        
        Args:
            emotion: Emotion name (happy, sad, angry, surprised, shy, love)
            intensity: Expression intensity (0-1)
        """
        emotion_to_expression = {
            "happy": ExpressionType.HAPPY,
            "joy": ExpressionType.HAPPY,
            "sad": ExpressionType.SAD,
            "sadness": ExpressionType.SAD,
            "angry": ExpressionType.ANGRY,
            "anger": ExpressionType.ANGRY,
            "surprised": ExpressionType.SURPRISED,
            "shocked": ExpressionType.SURPRISED,
            "shy": ExpressionType.SHY,
            "embarrassed": ExpressionType.SHY,
            "love": ExpressionType.LOVE,
            "loving": ExpressionType.LOVE,
        }
        
        expr_type = emotion_to_expression.get(emotion.lower())
        if expr_type:
            self.set_expression(expr_type, blend_duration=0.3 * intensity)
    
    def set_body_angle_from_touch(self, body_part: str, touch_intensity: float = 0.5):
        """
        Set body angle parameters based on touch location
        
        Args:
            body_part: Body part touched
            touch_intensity: Touch intensity
        """
        body_part_angles = {
            "top_of_head": {"ParamAngleX": 0, "ParamAngleY": -5},
            "face": {"ParamAngleX": 0, "ParamAngleY": 0},
            "neck": {"ParamAngleY": 8},
            "chest": {"ParamBodyAngleX": 0, "ParamBodyAngleY": -3},
            "back": {"ParamBodyAngleX": 0, "ParamBodyAngleY": 5},
            "shoulders": {"ParamBodyAngleZ": 0},
            "left": {"ParamAngleX": -15, "ParamBodyAngleX": -8},
            "right": {"ParamAngleX": 15, "ParamBodyAngleX": 8},
        }
        
        angles = body_part_angles.get(body_part, {})
        for param, base_value in angles.items():
            if param in self.parameters:
                # Apply with some randomness for natural feel
                variation = (random.random() - 0.5) * 5 * touch_intensity
                value = base_value + variation
                self.set_parameter(param, value)
    
    def get_body_parameter_mapping(self) -> Dict[str, List[str]]:
        """
        Get mapping of body parts to Live2D parameters
        
        Returns:
            Dictionary of body parts to parameter lists
        """
        from .physiological_tactile import BODY_TO_LIVE2D_MAPPING
        
        mapping = {}
        for body_part, touch_types in BODY_TO_LIVE2D_MAPPING.items():
            params = set()
            for touch_type, param_ranges in touch_types.items():
                params.update(param_ranges.keys())
            mapping[body_part] = list(params)
        
        return mapping
    
    def create_touch_animation(
        self,
        body_part: str,
        touch_type: str = "pat",
        intensity: float = 0.5
    ) -> List[Dict[str, float]]:
        """
        Create animation keyframes for a touch interaction
        
        Args:
            body_part: Body part touched
            touch_type: Type of touch
            intensity: Touch intensity
            
        Returns:
            List of parameter states for animation keyframes
        """
        keyframes = []
        
        # Get touch parameters
        touch_params = self._get_body_touch_parameters(body_part, touch_type, intensity)
        
        # Frame 1: Initial touch (peak intensity)
        keyframes.append({
            "time": 0.0,
            "params": touch_params,
            "easing": "ease_out"
        })
        
        # Frame 2: Sustain
        sustain_params = {k: v * 0.7 for k, v in touch_params.items()}
        keyframes.append({
            "time": 0.2,
            "params": sustain_params,
            "easing": "linear"
        })
        
        # Frame 3: Release (return to default)
        release_params = {k: 0.0 for k in touch_params.keys()}
        keyframes.append({
            "time": 0.5,
            "params": release_params,
            "easing": "ease_in"
        })
        
        return keyframes
    
    def sync_with_physiological_state(
        self,
        arousal_level: float,
        active_body_parts: List[str] = None
    ):
        """
        Sync Live2D with physiological state
        
        Args:
            arousal_level: Arousal level (0-100)
            active_body_parts: List of currently stimulated body parts
        """
        # Adjust breathing based on arousal
        breath_intensity = 0.3 + (arousal_level / 100.0) * 0.4
        self.set_parameter("ParamBreath", breath_intensity)
        
        # Adjust eye openness based on arousal
        eye_openness = 0.6 + (arousal_level / 100.0) * 0.4
        self.set_parameter("ParamEyeLOpen", eye_openness)
        self.set_parameter("ParamEyeROpen", eye_openness)
        
        # Apply subtle body movement based on active body parts
        if active_body_parts:
            for part in active_body_parts:
                self.set_body_angle_from_touch(part, 0.3)


# Example usage
if __name__ == "__main__":
    async def demo():
        live2d = Live2DIntegration()
        await live2d.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - Live2D集成系统演示")
        print("Live2D Integration System Demo")
        print("=" * 60)
        
        # Load model
        print("\n加载模型 / Loading model:")
        success = await live2d.load_model("models/angela/angela.model3.json")
        print(f"  模型加载: {'成功' if success else '失败'}")
        
        # Set expressions
        print("\n表情设置 / Expression settings:")
        for expr in [ExpressionType.HAPPY, ExpressionType.SURPRISED, ExpressionType.SHY]:
            live2d.set_expression(expr)
            print(f"  设置表情: {expr.value[0]} ({expr.value[1]})")
            await asyncio.sleep(0.5)
        
        # Play motion
        print("\n动作播放 / Motion playback:")
        await live2d.play_motion(MotionType.GREETING)
        print(f"  播放动作: {MotionType.GREETING.value[0]}")
        await asyncio.sleep(0.5)
        
        # Lip sync
        print("\n口型同步 / Lip sync:")
        live2d.start_lip_sync()
        for phoneme in ["a", "i", "u", "e", "o", "silence"]:
            live2d.update_lip_sync(phoneme, mouth_openness=0.8)
            print(f"  音素: {phoneme}, 嘴型开放度: {live2d.get_parameter('ParamMouthOpenY'):.2f}")
            await asyncio.sleep(0.3)
        live2d.stop_lip_sync()
        
        # Look at point
        print("\n视线跟踪 / Eye tracking:")
        live2d.look_at(0.5, -0.3)
        print(f"  看向: (0.5, -0.3)")
        print(f"  眼球X: {live2d.get_parameter('ParamEyeBallX'):.2f}")
        print(f"  眼球Y: {live2d.get_parameter('ParamEyeBallY'):.2f}")
        
        # Reset
        print("\n重置姿态 / Reset pose:")
        live2d.reset_pose()
        print("  所有参数已重置")
        
        await live2d.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
