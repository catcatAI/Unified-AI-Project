"""
Angela AI v6.0 - Visual Effect Generator
视觉效果生成器

Manages particle effects, scene transitions, emotional atmosphere rendering,
and special effects for Angela AI's visual presentation.

Features:
- Particle system for various effects
- Scene transition animations
- Emotional atmosphere rendering
- Special effects (glow, blur, bloom)

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import math
import random
import logging
logger = logging.getLogger(__name__)


class EffectType(Enum):
    """特效类型 / Effect types"""
    PARTICLE_HEART = ("爱心粒子", "Heart particles for love/affection")
    PARTICLE_SPARKLE = ("闪光粒子", "Sparkle particles for magic/wonder")
    PARTICLE_SNOW = ("雪花粒子", "Snow particles for cold/calm")
    PARTICLE_FIRE = ("火焰粒子", "Fire particles for anger/passion")
    PARTICLE_BUBBLE = ("气泡粒子", "Bubble particles for joy/playfulness")
    PARTICLE_LEAF = ("落叶粒子", "Falling leaf particles for sadness/autumn")
    PARTICLE_STAR = ("星星粒子", "Star particles for dreams/hope")
    TRANSITION_FADE = ("淡入淡出", "Fade transition")
    TRANSITION_SLIDE = ("滑动过渡", "Slide transition")
    TRANSITION_DISSOLVE = ("溶解过渡", "Dissolve transition")
    TRANSITION_BLUR = ("模糊过渡", "Blur transition")
    AMBIENCE_WARM = ("温暖氛围", "Warm color atmosphere")
    AMBIENCE_COOL = ("冷色氛围", "Cool color atmosphere")
    AMBIENCE_DARK = ("昏暗氛围", "Dark atmosphere")
    AMBIENCE_BRIGHT = ("明亮氛围", "Bright atmosphere")
    GLOW_SOFT = ("柔和发光", "Soft glow effect")
    GLOW_INTENSE = ("强烈发光", "Intense glow effect")


class ParticleShape(Enum):
    """粒子形状 / Particle shapes"""
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    STAR = "star"
    HEART = "heart"
    CUSTOM = "custom"


@dataclass
class Particle:
    """单个粒子 / Single particle"""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    size: float = 1.0
    life: float = 1.0  # 0-1, remaining life
    max_life: float = 1.0
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    rotation: float = 0.0
    rotation_speed: float = 0.0
    scale: float = 1.0
    shape: ParticleShape = ParticleShape.CIRCLE
    
    def update(self, dt: float):
        """Update particle state"""
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Rotate
        self.rotation += self.rotation_speed * dt
        
        # Decay
        self.life -= dt / self.max_life if self.max_life > 0 else 0
        
        # Scale based on life
        life_ratio = max(0, self.life)
        self.scale = self.size * life_ratio
    
    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.life > 0


@dataclass
class ParticleEmitter:
    """粒子发射器 / Particle emitter"""
    effect_type: EffectType
    x: float = 0.0
    y: float = 0.0
    emission_rate: float = 10.0  # particles per second
    max_particles: int = 100
    particle_life: float = 2.0  # seconds
    particle_size: Tuple[float, float] = (0.5, 2.0)
    particle_velocity: Tuple[float, float] = (10.0, 50.0)
    particle_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    gravity: Tuple[float, float] = (0.0, -9.8)
    shape: ParticleShape = ParticleShape.CIRCLE
    
    def create_particle(self) -> Particle:
        """Create a new particle"""
        velocity = random.uniform(*self.particle_velocity)
        angle = random.uniform(0, 2 * math.pi)
        
        return Particle(
            x=self.x + random.uniform(-10, 10),
            y=self.y + random.uniform(-10, 10),
            vx=velocity * math.cos(angle),
            vy=velocity * math.sin(angle),
            size=random.uniform(*self.particle_size),
            life=1.0,
            max_life=self.particle_life,
            color=self.particle_color,
            rotation=random.uniform(0, 360),
            rotation_speed=random.uniform(-180, 180),
            shape=self.shape
        )


@dataclass
class TransitionEffect:
    """过渡效果 / Transition effect"""
    effect_type: EffectType
    duration: float = 0.5
    progress: float = 0.0
    easing: str = "ease_in_out"
    callback: Optional[Callable[[], None]] = None
    
    def update(self, dt: float) -> bool:
        """Update transition progress, returns True if complete"""
        self.progress += dt / self.duration
        
        if self.progress >= 1.0:
            self.progress = 1.0
            if self.callback:
                self.callback()
            return True
        return False
    
    def get_eased_progress(self) -> float:
        """Get eased progress value"""
        if self.easing == "linear":
            return self.progress
        elif self.easing == "ease_in":
            return self.progress ** 2
        elif self.easing == "ease_out":
            return 1 - (1 - self.progress) ** 2
        elif self.easing == "ease_in_out":
            if self.progress < 0.5:
                return 2 * self.progress ** 2
            else:
                return 1 - (-2 * self.progress + 2) ** 2 / 2
        return self.progress


@dataclass
class AtmosphereEffect:
    """氛围效果 / Atmosphere effect"""
    effect_type: EffectType
    intensity: float = 0.5
    color_overlay: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 0.0)
    vignette: float = 0.0
    blur_amount: float = 0.0
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0


@dataclass
class GlowEffect:
    """发光效果 / Glow effect"""
    intensity: float = 0.5
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    radius: float = 20.0
    spread: float = 0.5
    quality: int = 4


class VisualEffectGenerator:
    """
    视觉效果生成器主类 / Main visual effect generator class
    
    Manages all visual effects including particles, transitions,
    atmosphere, and special effects.
    
    Attributes:
        active_particles: Currently active particles
        active_emitters: Currently active particle emitters
        active_transitions: Currently active transitions
        atmosphere: Current atmosphere effect
    
    Example:
        >>> generator = VisualEffectGenerator()
        >>> await generator.initialize()
        >>> 
        >>> # Start particle effect
        >>> generator.start_particle_effect(EffectType.PARTICLE_HEART, x=100, y=100)
        >>> 
        >>> # Trigger transition
        >>> await generator.trigger_transition(EffectType.TRANSITION_FADE)
        >>> 
        >>> # Set atmosphere
        >>> generator.set_atmosphere(EffectType.AMBIENCE_WARM, intensity=0.7)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Particle system
        self.active_particles: List[Particle] = []
        self.active_emitters: Dict[str, ParticleEmitter] = {}
        self._particle_id_counter: int = 0
        
        # Transition system
        self.active_transitions: List[TransitionEffect] = []
        
        # Atmosphere
        self.atmosphere: Optional[AtmosphereEffect] = None
        
        # Glow effect
        self.glow: Optional[GlowEffect] = None
        
        # Running state
        self._running: bool = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.max_particles: int = self.config.get("max_particles", 1000)
        self.update_rate: int = self.config.get("update_rate", 60)
        
        # Callbacks
        self._effect_callbacks: Dict[EffectType, List[Callable[[Any], None]]] = {}
    
    async def initialize(self):
        """Initialize the effect generator"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the effect generator"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop"""
        dt = 1.0 / self.update_rate
        
        while self._running:
            await self._update_particles(dt)
            await self._update_transitions(dt)
            await asyncio.sleep(dt)
    
    async def _update_particles(self, dt: float):
        """Update all particles"""
        # Emit new particles
        for emitter in self.active_emitters.values():
            emission_count = int(emitter.emission_rate * dt)
            for _ in range(emission_count):
                if len(self.active_particles) < self.max_particles:
                    particle = emitter.create_particle()
                    self.active_particles.append(particle)
        
        # Update existing particles
        for particle in self.active_particles:
            particle.update(dt)
            
            # Apply gravity
            if emitter := self.active_emitters.get(str(id(particle)), None):
                particle.vx += emitter.gravity[0] * dt
                particle.vy += emitter.gravity[1] * dt
        
        # Remove dead particles
        self.active_particles = [p for p in self.active_particles if p.is_alive()]
    
    async def _update_transitions(self, dt: float):
        """Update all transitions"""
        completed = []
        for transition in self.active_transitions:
            if transition.update(dt):
                completed.append(transition)
        
        for transition in completed:
            self.active_transitions.remove(transition)
    
    def start_particle_effect(
        self,
        effect_type: EffectType,
        x: float = 0.0,
        y: float = 0.0,
        duration: Optional[float] = None,
        intensity: float = 1.0
    ) -> str:
        """
        Start a particle effect
        
        Args:
            effect_type: Type of particle effect
            x: X position
            y: Y position
            duration: Effect duration (None for indefinite)
            intensity: Effect intensity (0-1)
            
        Returns:
            Effect ID for later control
        """
        effect_id = f"particle_{self._particle_id_counter}"
        self._particle_id_counter += 1
        
        # Configure emitter based on effect type
        emitter_config = self._get_particle_config(effect_type)
        emitter_config.x = x
        emitter_config.y = y
        emitter_config.emission_rate *= intensity
        
        self.active_emitters[effect_id] = emitter_config
        
        # Auto-stop after duration if specified
        if duration:
            asyncio.create_task(self._stop_after_duration(effect_id, duration))
        
        return effect_id
    
    def _get_particle_config(self, effect_type: EffectType) -> ParticleEmitter:
        """Get particle configuration for effect type"""
        configs = {
            EffectType.PARTICLE_HEART: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=20.0,
                max_particles=50,
                particle_life=2.0,
                particle_size=(0.8, 1.5),
                particle_velocity=(20.0, 40.0),
                particle_color=(1.0, 0.4, 0.6, 0.8),
                gravity=(0.0, -20.0),
                shape=ParticleShape.HEART
            ),
            EffectType.PARTICLE_SPARKLE: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=30.0,
                max_particles=100,
                particle_life=1.5,
                particle_size=(0.3, 0.8),
                particle_velocity=(30.0, 60.0),
                particle_color=(1.0, 1.0, 0.8, 1.0),
                gravity=(0.0, 0.0),
                shape=ParticleShape.STAR
            ),
            EffectType.PARTICLE_SNOW: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=15.0,
                max_particles=200,
                particle_life=5.0,
                particle_size=(0.5, 1.2),
                particle_velocity=(5.0, 15.0),
                particle_color=(0.95, 0.97, 1.0, 0.7),
                gravity=(2.0, -5.0),
                shape=ParticleShape.CIRCLE
            ),
            EffectType.PARTICLE_FIRE: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=25.0,
                max_particles=80,
                particle_life=1.2,
                particle_size=(0.5, 2.0),
                particle_velocity=(10.0, 30.0),
                particle_color=(1.0, 0.5, 0.1, 0.9),
                gravity=(0.0, 30.0),
                shape=ParticleShape.CIRCLE
            ),
            EffectType.PARTICLE_BUBBLE: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=12.0,
                max_particles=60,
                particle_life=3.0,
                particle_size=(1.0, 2.5),
                particle_velocity=(5.0, 20.0),
                particle_color=(0.7, 0.9, 1.0, 0.6),
                gravity=(0.0, -15.0),
                shape=ParticleShape.CIRCLE
            ),
            EffectType.PARTICLE_LEAF: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=10.0,
                max_particles=40,
                particle_life=4.0,
                particle_size=(1.0, 1.8),
                particle_velocity=(15.0, 35.0),
                particle_color=(0.8, 0.6, 0.3, 0.8),
                gravity=(3.0, -8.0),
                shape=ParticleShape.CUSTOM
            ),
            EffectType.PARTICLE_STAR: ParticleEmitter(
                effect_type=effect_type,
                emission_rate=18.0,
                max_particles=70,
                particle_life=2.5,
                particle_size=(0.4, 1.0),
                particle_velocity=(25.0, 50.0),
                particle_color=(1.0, 0.95, 0.6, 1.0),
                gravity=(0.0, -10.0),
                shape=ParticleShape.STAR
            ),
        }
        
        return configs.get(effect_type, configs[EffectType.PARTICLE_SPARKLE])
    
    async def _stop_after_duration(self, effect_id: str, duration: float):
        """Stop effect after specified duration"""
        await asyncio.sleep(duration)
        self.stop_particle_effect(effect_id)
    
    def stop_particle_effect(self, effect_id: str):
        """Stop a particle effect"""
        if effect_id in self.active_emitters:
            del self.active_emitters[effect_id]
    
    def stop_all_particle_effects(self):
        """Stop all particle effects"""
        self.active_emitters.clear()
        self.active_particles.clear()
    
    async def trigger_transition(
        self,
        effect_type: EffectType,
        duration: float = 0.5,
        callback: Optional[Callable[[], None]] = None
    ):
        """
        Trigger a transition effect
        
        Args:
            effect_type: Type of transition
            duration: Transition duration in seconds
            callback: Callback when transition completes
        """
        transition = TransitionEffect(
            effect_type=effect_type,
            duration=duration,
            callback=callback
        )
        self.active_transitions.append(transition)
        
        # Wait for completion if no callback
        if not callback:
            while transition.progress < 1.0:
                await asyncio.sleep(0.016)
    
    def set_atmosphere(
        self,
        effect_type: EffectType,
        intensity: float = 0.5,
        transition_duration: float = 1.0
    ):
        """
        Set atmospheric effect
        
        Args:
            effect_type: Type of atmosphere
            intensity: Atmosphere intensity (0-1)
            transition_duration: Transition time to new atmosphere
        """
        atmosphere_config = self._get_atmosphere_config(effect_type)
        atmosphere_config.intensity = intensity
        self.atmosphere = atmosphere_config
    
    def _get_atmosphere_config(self, effect_type: EffectType) -> AtmosphereEffect:
        """Get atmosphere configuration for effect type"""
        configs = {
            EffectType.AMBIENCE_WARM: AtmosphereEffect(
                effect_type=effect_type,
                color_overlay=(1.0, 0.9, 0.7, 0.3),
                brightness=1.1,
                saturation=1.1
            ),
            EffectType.AMBIENCE_COOL: AtmosphereEffect(
                effect_type=effect_type,
                color_overlay=(0.7, 0.8, 1.0, 0.3),
                brightness=0.95,
                saturation=0.95
            ),
            EffectType.AMBIENCE_DARK: AtmosphereEffect(
                effect_type=effect_type,
                color_overlay=(0.2, 0.2, 0.3, 0.4),
                brightness=0.7,
                contrast=1.1,
                vignette=0.5
            ),
            EffectType.AMBIENCE_BRIGHT: AtmosphereEffect(
                effect_type=effect_type,
                color_overlay=(1.0, 1.0, 1.0, 0.2),
                brightness=1.2,
                contrast=0.95
            ),
        }
        
        return configs.get(effect_type, AtmosphereEffect(effect_type=effect_type))
    
    def clear_atmosphere(self, transition_duration: float = 1.0):
        """Clear current atmosphere"""
        self.atmosphere = None
    
    def set_glow(
        self,
        intensity: float = 0.5,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        radius: float = 20.0
    ):
        """
        Set glow effect
        
        Args:
            intensity: Glow intensity (0-1)
            color: RGB color tuple
            radius: Glow radius in pixels
        """
        self.glow = GlowEffect(
            intensity=intensity,
            color=color,
            radius=radius
        )
    
    def clear_glow(self):
        """Clear glow effect"""
        self.glow = None
    
    def create_emotional_effect(
        self,
        emotion: str,
        intensity: float = 0.5,
        x: float = 0.0,
        y: float = 0.0
    ) -> str:
        """
        Create effect based on emotion
        
        Args:
            emotion: Emotion name (happy, sad, angry, etc.)
            intensity: Effect intensity
            x: Effect position X
            y: Effect position Y
            
        Returns:
            Effect ID
        """
        emotion_effects = {
            "happy": EffectType.PARTICLE_SPARKLE,
            "excited": EffectType.PARTICLE_STAR,
            "love": EffectType.PARTICLE_HEART,
            "sad": EffectType.PARTICLE_LEAF,
            "angry": EffectType.PARTICLE_FIRE,
            "surprised": EffectType.PARTICLE_BUBBLE,
            "calm": EffectType.PARTICLE_SNOW,
        }
        
        effect_type = emotion_effects.get(emotion.lower(), EffectType.PARTICLE_SPARKLE)
        return self.start_particle_effect(effect_type, x, y, intensity=intensity)
    
    def get_particle_count(self) -> int:
        """Get current active particle count"""
        return len(self.active_particles)
    
    def get_active_emitter_count(self) -> int:
        """Get number of active emitters"""
        return len(self.active_emitters)
    
    def get_effect_summary(self) -> Dict[str, Any]:
        """Get summary of current effects"""
        return {
            "active_particles": len(self.active_particles),
            "active_emitters": len(self.active_emitters),
            "active_transitions": len(self.active_transitions),
            "has_atmosphere": self.atmosphere is not None,
            "has_glow": self.glow is not None,
            "atmosphere_type": self.atmosphere.effect_type.name if self.atmosphere else None,
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        generator = VisualEffectGenerator()
        await generator.initialize()
        
        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 视觉效果生成器演示")
        logger.info("Visual Effect Generator Demo")
        logger.info("=" * 60)
        
        # Particle effects
        logger.info("\n粒子效果 / Particle effects:")
        
        heart_id = generator.start_particle_effect(
            EffectType.PARTICLE_HEART, x=100, y=100, duration=3.0
        )
        logger.info(f"  启动爱心粒子: {heart_id}")
        
        sparkle_id = generator.start_particle_effect(
            EffectType.PARTICLE_SPARKLE, x=200, y=150, duration=2.0
        )
        logger.info(f"  启动闪光粒子: {sparkle_id}")
        
        await asyncio.sleep(1.0)
        logger.info(f"  当前粒子数: {generator.get_particle_count()}")
        
        # Emotional effect
        logger.info("\n情绪效果 / Emotional effects:")
        happy_id = generator.create_emotional_effect("happy", intensity=0.8, x=150, y=200)
        logger.info(f"  快乐效果: {happy_id}")
        
        await asyncio.sleep(1.0)
        
        # Atmosphere
        logger.info("\n氛围效果 / Atmosphere effects:")
        generator.set_atmosphere(EffectType.AMBIENCE_WARM, intensity=0.6)
        logger.info("  设置温暖氛围")
        
        # Glow
        logger.info("\n发光效果 / Glow effects:")
        generator.set_glow(intensity=0.7, color=(1.0, 0.8, 0.6), radius=30.0)
        logger.info("  设置柔和发光")
        
        # Summary
        logger.info("\n效果摘要 / Effect summary:")
        summary = generator.get_effect_summary()
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")
        
        await asyncio.sleep(2.0)
        
        await generator.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
