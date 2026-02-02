"""
Angela AI v6.0 - Visual Manager
视觉管理器

Central visual management system for Angela AI. Manages visual assets,
real-time rendering, visual effects, and connects to all biological systems.

Features:
- Visual asset management (Live2D models, expressions, motions, backgrounds)
- Real-time rendering control and parameter updates
- Visual expression system based on emotional and physiological states
- Resource loading and optimization with async support
- Integration with EmotionalBlendingSystem, PhysiologicalTactileSystem, and more

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import logging
import time

from apps.backend.src.core.visual_config import (
    VisualConfiguration, ModelConfiguration, RenderQuality
)
from apps.backend.src.core.visual_effect_generator import (
    VisualEffectGenerator, EffectType
)

# Import biological systems
try:
    from apps.backend.src.core.autonomous.live2d_integration import (
        Live2DIntegration, ExpressionType, MotionType, LipSyncState
    )
    from apps.backend.src.core.autonomous.self_generation import (
        SelfGeneration, GenerationMode, VisualAttributes
    )
    LIVE2D_AVAILABLE = True
except ImportError:
    LIVE2D_AVAILABLE = False
    # Define placeholder classes
    class ExpressionType(Enum):
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
        IDLE = ("待机", "Idle")
        GREETING = ("问候", "Greeting")
        THINKING = ("思考", "Thinking")
    
    class Live2DIntegration:
        pass
    
    class SelfGeneration:
        pass

try:
    from apps.backend.src.core.autonomous.emotional_blending import (
        EmotionalBlendingSystem, BasicEmotion, PADEmotion
    )
    EMOTION_AVAILABLE = True
except ImportError:
    EMOTION_AVAILABLE = False
    EmotionalBlendingSystem = None

try:
    from apps.backend.src.core.autonomous.physiological_tactile import (
        PhysiologicalTactileSystem, TactileStimulus, BodyPart
    )
    TACTILE_AVAILABLE = True
except ImportError:
    TACTILE_AVAILABLE = False
    PhysiologicalTactileSystem = None

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """资源类型 / Asset types"""
    MODEL = "model"
    EXPRESSION = "expression"
    MOTION = "motion"
    BACKGROUND = "background"
    TEXTURE = "texture"
    AUDIO = "audio"
    EFFECT = "effect"


class VisualState(Enum):
    """视觉状态 / Visual states"""
    IDLE = "idle"
    TALKING = "talking"
    REACTING = "reacting"
    ANIMATING = "animating"
    TRANSITIONING = "transitioning"
    ERROR = "error"


@dataclass
class AssetMetadata:
    """资源元数据 / Asset metadata"""
    asset_id: str
    asset_type: AssetType
    name: str
    path: str
    size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    is_loaded: bool = False
    lod_level: int = 0


@dataclass
class CachedAsset:
    """缓存的资源 / Cached asset"""
    metadata: AssetMetadata
    data: Any
    load_time: datetime
    last_used: datetime
    memory_usage: int = 0


@dataclass
class VisualPresentation:
    """视觉表现状态 / Visual presentation state"""
    current_expression: ExpressionType = ExpressionType.NEUTRAL
    current_motion: Optional[MotionType] = None
    target_expression: Optional[ExpressionType] = None
    expression_blend_progress: float = 1.0
    is_speaking: bool = False
    eye_target: Tuple[float, float] = (0.0, 0.0)
    body_position: Tuple[float, float] = (0.0, 0.0)
    scale: float = 1.0
    opacity: float = 1.0


@dataclass
class RenderMetrics:
    """渲染指标 / Render metrics"""
    fps: float = 60.0
    frame_time_ms: float = 16.67
    draw_calls: int = 0
    triangle_count: int = 0
    texture_memory_mb: float = 0.0
    active_lights: int = 0
    last_update: datetime = field(default_factory=datetime.now)


class AssetCache:
    """
    资源缓存系统 / Asset cache system
    
    Manages loaded assets with LRU eviction policy and memory limits.
    """
    
    def __init__(self, max_size_mb: int = 512):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size_bytes = 0
        self.assets: Dict[str, CachedAsset] = {}
        self.access_order: List[str] = []
        self._lock = asyncio.Lock()
    
    async def get(self, asset_id: str) -> Optional[CachedAsset]:
        """Get asset from cache"""
        async with self._lock:
            if asset_id in self.assets:
                asset = self.assets[asset_id]
                asset.last_used = datetime.now()
                asset.metadata.last_accessed = datetime.now()
                asset.metadata.access_count += 1
                
                # Move to front of access order
                if asset_id in self.access_order:
                    self.access_order.remove(asset_id)
                self.access_order.append(asset_id)
                
                return asset
        return None
    
    async def put(self, asset_id: str, asset: CachedAsset):
        """Add asset to cache"""
        async with self._lock:
            # Check if we need to evict
            while (self.current_size_bytes + asset.memory_usage > self.max_size_bytes 
                   and self.assets):
                await self._evict_oldest()
            
            self.assets[asset_id] = asset
            self.current_size_bytes += asset.memory_usage
            self.access_order.append(asset_id)
    
    async def remove(self, asset_id: str):
        """Remove asset from cache"""
        async with self._lock:
            if asset_id in self.assets:
                asset = self.assets.pop(asset_id)
                self.current_size_bytes -= asset.memory_usage
                if asset_id in self.access_order:
                    self.access_order.remove(asset_id)
    
    async def _evict_oldest(self):
        """Evict least recently used asset"""
        if self.access_order:
            oldest_id = self.access_order.pop(0)
            if oldest_id in self.assets:
                asset = self.assets.pop(oldest_id)
                self.current_size_bytes -= asset.memory_usage
                logger.debug(f"Evicted asset: {oldest_id}")
    
    async def clear(self):
        """Clear all cached assets"""
        async with self._lock:
            self.assets.clear()
            self.access_order.clear()
            self.current_size_bytes = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "asset_count": len(self.assets),
            "current_size_mb": self.current_size_bytes / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_percent": (self.current_size_bytes / self.max_size_bytes) * 100
        }


class VisualManager:
    """
    视觉管理器主类 / Main visual manager class
    
    Central management system for all visual aspects of Angela AI.
    Connects to biological systems and manages rendering pipeline.
    
    Attributes:
        config: Visual system configuration
        live2d: Live2D integration instance
        effect_generator: Visual effect generator
        asset_cache: Resource cache system
        current_presentation: Current visual presentation state
        metrics: Render performance metrics
    
    Example:
        >>> vm = VisualManager()
        >>> await vm.initialize()
        >>> 
        >>> # Connect to biological systems
        >>> vm.connect_emotional_system(emotion_system)
        >>> vm.connect_tactile_system(tactile_system)
        >>> 
        >>> # Set expression based on emotion
        >>> await vm.set_expression(ExpressionType.HAPPY)
        >>> 
        >>> # Play motion
        >>> await vm.play_motion(MotionType.GREETING)
        >>> 
        >>> # Start lip sync
        >>> vm.start_lip_sync()
    """
    
    def __init__(self, config: Optional[VisualConfiguration] = None):
        self.config = config or VisualConfiguration()
        
        # Core systems
        self.live2d: Optional[Live2DIntegration] = None
        self.self_generation: Optional[SelfGeneration] = None
        self.effect_generator: VisualEffectGenerator = VisualEffectGenerator()
        
        # Biological system connections
        self.emotional_system: Optional[Any] = None
        self.tactile_system: Optional[Any] = None
        self.desktop_pet: Optional[Any] = None
        
        # Asset management
        self.asset_cache: AssetCache = AssetCache(
            max_size_mb=self.config.cache.max_cache_size_mb
        )
        self.asset_registry: Dict[str, AssetMetadata] = {}
        self.loading_queue: asyncio.Queue = asyncio.Queue()
        self._preload_task: Optional[asyncio.Task] = None
        
        # Visual state
        self.current_presentation: VisualPresentation = VisualPresentation()
        self.visual_state: VisualState = VisualState.IDLE
        self.state_history: List[Tuple[datetime, VisualState]] = []
        
        # Render metrics
        self.metrics: RenderMetrics = RenderMetrics()
        self._fps_counter: int = 0
        self._fps_time: float = time.time()
        
        # Callbacks
        self._expression_callbacks: List[Callable[[ExpressionType], None]] = []
        self._motion_callbacks: List[Callable[[MotionType], None]] = []
        self._state_callbacks: List[Callable[[VisualState], None]] = []
        
        # Running state
        self._running: bool = False
        self._update_task: Optional[asyncio.Task] = None
        self._render_task: Optional[asyncio.Task] = None
        
        logger.info("VisualManager created")
    
    async def initialize(self):
        """Initialize the visual manager and all subsystems"""
        logger.info("Initializing VisualManager...")
        
        self._running = True
        
        # Initialize Live2D
        if LIVE2D_AVAILABLE:
            self.live2d = Live2DIntegration()
            await self.live2d.initialize()
            logger.info("Live2D integration initialized")
        
        # Initialize self generation (if available and working)
        if LIVE2D_AVAILABLE:
            try:
                self.self_generation = SelfGeneration()
                await self.self_generation.initialize()
                logger.info("Self generation system initialized")
            except Exception as e:
                logger.warning(f"Self generation initialization failed: {e}")
                self.self_generation = None
        
        # Initialize effect generator
        await self.effect_generator.initialize()
        logger.info("Effect generator initialized")
        
        # Start background tasks
        self._update_task = asyncio.create_task(self._update_loop())
        self._render_task = asyncio.create_task(self._render_loop())
        self._preload_task = asyncio.create_task(self._preload_worker())
        
        # Register default model
        await self._register_default_assets()
        
        logger.info("VisualManager initialization complete")
    
    async def shutdown(self):
        """Shutdown the visual manager and all subsystems"""
        logger.info("Shutting down VisualManager...")
        
        self._running = False
        
        # Cancel background tasks
        tasks = [self._update_task, self._render_task, self._preload_task]
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Clear cache
        await self.asset_cache.clear()
        
        # Shutdown subsystems
        if self.effect_generator:
            await self.effect_generator.shutdown()
        
        if self.live2d:
            await self.live2d.shutdown()
        
        if self.self_generation:
            await self.self_generation.shutdown()
        
        logger.info("VisualManager shutdown complete")
    
    # ==================== System Connections ====================
    
    def connect_emotional_system(self, emotional_system: Any):
        """
        Connect to emotional blending system
        
        Args:
            emotional_system: EmotionalBlendingSystem instance
        """
        self.emotional_system = emotional_system
        
        # Register callback for emotion changes
        if hasattr(emotional_system, 'register_emotion_callback'):
            emotional_system.register_emotion_callback(
                self._on_emotion_changed
            )
        
        logger.info("Connected to emotional system")
    
    def connect_tactile_system(self, tactile_system: Any):
        """
        Connect to physiological tactile system
        
        Args:
            tactile_system: PhysiologicalTactileSystem instance
        """
        self.tactile_system = tactile_system
        
        # Register callback for tactile stimuli
        if hasattr(tactile_system, 'register_stimulus_callback'):
            tactile_system.register_stimulus_callback(
                self._on_tactile_stimulus
            )
        
        logger.info("Connected to tactile system")
    
    def connect_desktop_pet(self, desktop_pet: Any):
        """
        Connect to desktop pet controller
        
        Args:
            desktop_pet: DesktopPetController instance
        """
        self.desktop_pet = desktop_pet
        logger.info("Connected to desktop pet")
    
    def connect_self_generation(self, self_generation: Any):
        """
        Connect to self generation system
        
        Args:
            self_generation: SelfGeneration instance
        """
        self.self_generation = self_generation
        logger.info("Connected to self generation")
    
    # ==================== Asset Management ====================
    
    async def _register_default_assets(self):
        """Register default assets"""
        # Register model
        model_meta = AssetMetadata(
            asset_id="model_default",
            asset_type=AssetType.MODEL,
            name=self.config.model.model_name,
            path=self.config.get_model_path(),
            tags=["default", "live2d"]
        )
        self.asset_registry["model_default"] = model_meta
        
        # Preload default model
        await self.load_model("model_default")
    
    async def load_model(self, asset_id: str) -> bool:
        """
        Load a Live2D model
        
        Args:
            asset_id: Asset ID of the model
            
        Returns:
            True if successful
        """
        if asset_id not in self.asset_registry:
            logger.error(f"Model asset not found: {asset_id}")
            return False
        
        metadata = self.asset_registry[asset_id]
        
        # Check cache first
        cached = await self.asset_cache.get(asset_id)
        if cached:
            logger.debug(f"Model loaded from cache: {asset_id}")
            metadata.is_loaded = True
            return True
        
        # Load model
        if self.live2d:
            success = await self.live2d.load_model(metadata.path)
            if success:
                metadata.is_loaded = True
                metadata.last_accessed = datetime.now()
                logger.info(f"Model loaded: {asset_id}")
                return True
        
        return False
    
    async def preload_assets(self, asset_ids: List[str]):
        """
        Preload assets in background
        
        Args:
            asset_ids: List of asset IDs to preload
        """
        for asset_id in asset_ids:
            await self.loading_queue.put(asset_id)
    
    async def _preload_worker(self):
        """Background worker for preloading assets"""
        while self._running:
            try:
                asset_id = await asyncio.wait_for(
                    self.loading_queue.get(), 
                    timeout=1.0
                )
                
                if asset_id in self.asset_registry:
                    metadata = self.asset_registry[asset_id]
                    
                    # Simulate loading (in real implementation, load actual data)
                    await asyncio.sleep(0.1)
                    
                    # Create cached asset
                    cached = CachedAsset(
                        metadata=metadata,
                        data=None,  # Actual data would be loaded here
                        load_time=datetime.now(),
                        last_used=datetime.now(),
                        memory_usage=1024 * 1024  # Placeholder: 1MB
                    )
                    
                    await self.asset_cache.put(asset_id, cached)
                    logger.debug(f"Preloaded asset: {asset_id}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error preloading asset: {e}")
    
    def register_asset(
        self,
        asset_id: str,
        asset_type: AssetType,
        name: str,
        path: str,
        tags: Optional[List[str]] = None
    ):
        """
        Register a new asset
        
        Args:
            asset_id: Unique asset identifier
            asset_type: Type of asset
            name: Display name
            path: Asset file path
            tags: Optional tags for categorization
        """
        metadata = AssetMetadata(
            asset_id=asset_id,
            asset_type=asset_type,
            name=name,
            path=path,
            tags=tags or []
        )
        self.asset_registry[asset_id] = metadata
        logger.debug(f"Registered asset: {asset_id} ({asset_type.value})")
    
    # ==================== Real-time Rendering Control ====================
    
    async def _update_loop(self):
        """Background update loop for visual state"""
        while self._running:
            try:
                await self._update_expression_blending()
                await self._update_eye_tracking()
                await self._update_metrics()
                await asyncio.sleep(1.0 / 60)  # 60 FPS update
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
    
    async def _render_loop(self):
        """Background render loop"""
        while self._running:
            try:
                self._fps_counter += 1
                current_time = time.time()
                
                # Calculate FPS every second
                if current_time - self._fps_time >= 1.0:
                    self.metrics.fps = self._fps_counter
                    self.metrics.frame_time_ms = 1000.0 / max(self._fps_counter, 1)
                    self._fps_counter = 0
                    self._fps_time = current_time
                
                await asyncio.sleep(1.0 / self.config.performance.target_fps)
            except Exception as e:
                logger.error(f"Error in render loop: {e}")
    
    async def _update_expression_blending(self):
        """Update expression blending"""
        if self.current_presentation.target_expression is None:
            return
        
        if self.current_presentation.expression_blend_progress < 1.0:
            # Continue blending
            blend_speed = 0.05
            self.current_presentation.expression_blend_progress += blend_speed
            
            if self.current_presentation.expression_blend_progress >= 1.0:
                self.current_presentation.expression_blend_progress = 1.0
                self.current_presentation.current_expression = \
                    self.current_presentation.target_expression
                self.current_presentation.target_expression = None
                
                # Notify callbacks
                for callback in self._expression_callbacks:
                    try:
                        callback(self.current_presentation.current_expression)
                    except Exception:
                        pass
    
    async def _update_eye_tracking(self):
        """Update eye tracking"""
        if self.live2d and self.config.eye_tracking.enabled:
            target_x, target_y = self.current_presentation.eye_target
            self.live2d.look_at(target_x, target_y)
    
    async def _update_metrics(self):
        """Update render metrics"""
        self.metrics.last_update = datetime.now()
        
        # Update texture memory
        cache_stats = self.asset_cache.get_stats()
        self.metrics.texture_memory_mb = cache_stats["current_size_mb"]
    
    async def set_expression(
        self,
        expression: ExpressionType,
        blend_duration: Optional[float] = None,
        immediate: bool = False
    ):
        """
        Set facial expression
        
        Args:
            expression: Expression to set
            blend_duration: Time to blend (uses config if None)
            immediate: Skip blending if True
        """
        if immediate:
            self.current_presentation.current_expression = expression
            self.current_presentation.target_expression = None
            self.current_presentation.expression_blend_progress = 1.0
        else:
            self.current_presentation.target_expression = expression
            self.current_presentation.expression_blend_progress = 0.0
        
        # Update Live2D
        if self.live2d:
            duration = blend_duration or self.config.expression.blend_duration
            self.live2d.set_expression(expression, duration)
        
        logger.debug(f"Expression set: {expression.name}")
    
    async def play_motion(
        self,
        motion: MotionType,
        loop: bool = False,
        priority: int = 0
    ):
        """
        Play a motion/animation
        
        Args:
            motion: Motion to play
            loop: Whether to loop
            priority: Motion priority
        """
        self.current_presentation.current_motion = motion
        self._set_visual_state(VisualState.ANIMATING)
        
        # Play in Live2D
        if self.live2d:
            await self.live2d.play_motion(motion, loop)
        
        # Notify callbacks
        for callback in self._motion_callbacks:
            try:
                callback(motion)
            except Exception:
                pass
        
        logger.debug(f"Motion played: {motion.name}")
    
    def start_lip_sync(self):
        """Start lip synchronization"""
        self.current_presentation.is_speaking = True
        if self.live2d:
            self.live2d.start_lip_sync()
        logger.debug("Lip sync started")
    
    def stop_lip_sync(self):
        """Stop lip synchronization"""
        self.current_presentation.is_speaking = False
        if self.live2d:
            self.live2d.stop_lip_sync()
        logger.debug("Lip sync stopped")
    
    def update_lip_sync(self, phoneme: str, mouth_openness: float = 1.0):
        """
        Update lip sync with current phoneme
        
        Args:
            phoneme: Current phoneme
            mouth_openness: Mouth openness (0-1)
        """
        if self.live2d:
            self.live2d.update_lip_sync(phoneme, mouth_openness)
    
    def set_eye_target(self, x: float, y: float):
        """
        Set eye tracking target
        
        Args:
            x: X coordinate (-1 to 1)
            y: Y coordinate (-1 to 1)
        """
        self.current_presentation.eye_target = (x, y)
    
    # ==================== Visual Presentation System ====================
    
    def _on_emotion_changed(self, emotion_data: Any):
        """Handle emotion change from emotional system"""
        if isinstance(emotion_data, dict):
            emotion_name = emotion_data.get("emotion", "neutral")
            intensity = emotion_data.get("intensity", 0.5)
        else:
            emotion_name = str(emotion_data).lower()
            intensity = 0.5
        
        # Map emotion to expression
        emotion_to_expression = {
            "joy": ExpressionType.HAPPY,
            "happy": ExpressionType.HAPPY,
            "sadness": ExpressionType.SAD,
            "sad": ExpressionType.SAD,
            "anger": ExpressionType.ANGRY,
            "angry": ExpressionType.ANGRY,
            "fear": ExpressionType.SURPRISED,
            "surprise": ExpressionType.SURPRISED,
            "surprised": ExpressionType.SURPRISED,
            "disgust": ExpressionType.CONFUSED,
            "trust": ExpressionType.LOVE,
            "love": ExpressionType.LOVE,
            "anticipation": ExpressionType.EXCITED,
            "excited": ExpressionType.EXCITED,
        }
        
        expression = emotion_to_expression.get(emotion_name, ExpressionType.NEUTRAL)
        
        # Create async task for expression change
        asyncio.create_task(self.set_expression(expression))
        
        # Trigger emotional effect
        if intensity > 0.7:
            self.effect_generator.create_emotional_effect(
                emotion_name, intensity, x=100, y=100
            )
        
        logger.debug(f"Emotion changed: {emotion_name} -> {expression.name}")
    
    def _on_tactile_stimulus(self, stimulus: Any):
        """Handle tactile stimulus from tactile system"""
        if hasattr(stimulus, 'body_part'):
            body_part = stimulus.body_part
            stimulus_type = getattr(stimulus, 'stimulus_type', 'unknown')
            intensity = getattr(stimulus, 'intensity', 0.5)
            
            # Map body part and stimulus to reaction
            if intensity > 0.6:
                if stimulus_type == 'pleasant':
                    asyncio.create_task(self.set_expression(ExpressionType.HAPPY))
                    asyncio.create_task(self.play_motion(MotionType.CLAPPING))
                elif stimulus_type == 'unpleasant':
                    asyncio.create_task(self.set_expression(ExpressionType.SURPRISED))
                    asyncio.create_task(self.play_motion(MotionType.SHAKE_HEAD))
                elif body_part in ['head', 'face']:
                    asyncio.create_task(self.set_expression(ExpressionType.SHY))
            
            logger.debug(f"Tactile stimulus: {body_part} ({stimulus_type})")
    
    async def update_from_biological_state(
        self,
        emotional_state: Optional[Dict[str, Any]] = None,
        physiological_state: Optional[Dict[str, Any]] = None,
        cognitive_state: Optional[Dict[str, Any]] = None
    ):
        """
        Update visual presentation from biological states
        
        Args:
            emotional_state: Current emotional state
            physiological_state: Current physiological state
            cognitive_state: Current cognitive state
        """
        # Update from emotional state
        if emotional_state:
            dominant_emotion = emotional_state.get("dominant_emotion", "neutral")
            intensity = emotional_state.get("intensity", 0.5)
            
            # Trigger visual effect for strong emotions
            if intensity > 0.8:
                self.effect_generator.create_emotional_effect(
                    dominant_emotion, intensity
                )
        
        # Update from physiological state
        if physiological_state:
            energy_level = physiological_state.get("energy", 0.5)
            
            # Adjust animation speed based on energy
            if energy_level < 0.2:
                await self.set_expression(ExpressionType.TIRED)
        
        # Update from cognitive state
        if cognitive_state:
            is_thinking = cognitive_state.get("is_thinking", False)
            
            if is_thinking:
                await self.play_motion(MotionType.THINKING)
    
    # ==================== Visual Effects ====================
    
    async def trigger_transition(self, effect_type: EffectType, duration: float = 0.5):
        """Trigger a visual transition effect"""
        self._set_visual_state(VisualState.TRANSITIONING)
        await self.effect_generator.trigger_transition(effect_type, duration)
        self._set_visual_state(VisualState.IDLE)
    
    def set_atmosphere(self, effect_type: EffectType, intensity: float = 0.5):
        """Set atmospheric effect"""
        self.effect_generator.set_atmosphere(effect_type, intensity)
    
    def create_particle_effect(
        self,
        effect_type: EffectType,
        x: float = 0.0,
        y: float = 0.0,
        duration: Optional[float] = None
    ) -> str:
        """Create a particle effect"""
        return self.effect_generator.start_particle_effect(
            effect_type, x, y, duration
        )
    
    # ==================== Utility Methods ====================
    
    def _set_visual_state(self, state: VisualState):
        """Set and track visual state"""
        if self.visual_state != state:
            self.visual_state = state
            self.state_history.append((datetime.now(), state))
            
            # Notify callbacks
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception:
                    pass
            
            logger.debug(f"Visual state: {state.value}")
    
    def register_expression_callback(self, callback: Callable[[ExpressionType], None]):
        """Register expression change callback"""
        self._expression_callbacks.append(callback)
    
    def register_motion_callback(self, callback: Callable[[MotionType], None]):
        """Register motion change callback"""
        self._motion_callbacks.append(callback)
    
    def register_state_callback(self, callback: Callable[[VisualState], None]):
        """Register state change callback"""
        self._state_callbacks.append(callback)
    
    def get_current_presentation(self) -> VisualPresentation:
        """Get current presentation state"""
        return self.current_presentation
    
    def get_metrics(self) -> RenderMetrics:
        """Get current render metrics"""
        return self.metrics
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get asset cache statistics"""
        return self.asset_cache.get_stats()
    
    def get_visual_summary(self) -> Dict[str, Any]:
        """Get complete visual system summary"""
        return {
            "state": self.visual_state.value,
            "expression": self.current_presentation.current_expression.name,
            "motion": self.current_presentation.current_motion.name if self.current_presentation.current_motion else None,
            "is_speaking": self.current_presentation.is_speaking,
            "fps": self.metrics.fps,
            "cache": self.asset_cache.get_stats(),
            "effects": self.effect_generator.get_effect_summary(),
            "live2d_loaded": self.live2d.model_loaded if self.live2d else False,
            "connected_systems": {
                "emotional": self.emotional_system is not None,
                "tactile": self.tactile_system is not None,
                "desktop_pet": self.desktop_pet is not None,
            },
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 60)
        print("Angela AI v6.0 - 视觉管理器演示")
        print("Visual Manager Demo")
        print("=" * 60)
        
        # Create visual manager
        vm = VisualManager()
        await vm.initialize()
        
        print("\n视觉管理器初始化完成 / VisualManager initialized")
        
        # Show initial state
        summary = vm.get_visual_summary()
        print(f"\n初始状态 / Initial state:")
        print(f"  当前表情: {summary['expression']}")
        print(f"  当前状态: {summary['state']}")
        print(f"  FPS: {summary['fps']}")
        
        # Set expression
        print("\n设置表情 / Setting expressions:")
        await vm.set_expression(ExpressionType.HAPPY)
        print(f"  设置为: HAPPY")
        await asyncio.sleep(0.5)
        
        await vm.set_expression(ExpressionType.SURPRISED)
        print(f"  设置为: SURPRISED")
        await asyncio.sleep(0.5)
        
        # Play motion
        print("\n播放动作 / Playing motions:")
        await vm.play_motion(MotionType.GREETING)
        print(f"  播放: GREETING")
        await asyncio.sleep(0.5)
        
        # Particle effect
        print("\n粒子效果 / Particle effects:")
        effect_id = vm.create_particle_effect(EffectType.PARTICLE_HEART, x=100, y=100, duration=2.0)
        print(f"  创建爱心粒子效果: {effect_id}")
        
        await asyncio.sleep(1.0)
        
        # Atmosphere
        print("\n氛围效果 / Atmosphere:")
        vm.set_atmosphere(EffectType.AMBIENCE_WARM, intensity=0.6)
        print(f"  设置温暖氛围")
        
        # Final summary
        print("\n最终摘要 / Final summary:")
        final_summary = vm.get_visual_summary()
        for key, value in final_summary.items():
            print(f"  {key}: {value}")
        
        await vm.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
