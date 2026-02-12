"""
Angela AI v6.0 - Visual Configuration
视觉配置系统

Manages visual system configuration, asset paths, rendering parameters,
and performance settings for the VisualManager.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


class RenderQuality(Enum):
    """渲染质量级别 / Render quality levels"""
    LOW = ("低", "Low quality, high performance")
    MEDIUM = ("中", "Balanced quality and performance")
    HIGH = ("高", "High quality, moderate performance")
    ULTRA = ("超", "Maximum quality, lower performance")


class TextureFormat(Enum):
    """纹理格式 / Texture formats"""
    PNG = ("png", "PNG with transparency")
    DDS = ("dds", "DirectDraw Surface (compressed)")
    KTX = ("ktx", "Khronos Texture format")
    BASIS = ("basis", "Basis Universal compressed")


@dataclass
class ModelConfiguration:
    """Live2D模型配置 / Live2D model configuration"""
    model_name: str = "angela_default"
    model_path: str = "assets/models/live2d/angela"
    model_file: str = "angela.model3.json"
    texture_resolution: int = 2048
    max_texture_size: int = 4096
    enable_mipmap: bool = True
    
    # LOD settings
    lod_levels: int = 3
    lod_distances: List[float] = field(default_factory=lambda: [0.0, 50.0, 100.0])
    lod_scales: List[float] = field(default_factory=lambda: [1.0, 0.5, 0.25])


@dataclass
class ExpressionConfiguration:
    """表情配置 / Expression configuration"""
    blend_duration: float = 0.3
    max_blend_layers: int = 3
    enable_smooth_blend: bool = True
    blend_curve: str = "ease_in_out"
    
    # Expression priority levels
    priority_system: bool = True
    default_priority: int = 5
    override_priority: int = 10


@dataclass
class MotionConfiguration:
    """动作配置 / Motion configuration"""
    default_duration: float = 2.0
    max_queue_size: int = 5
    enable_looping: bool = True
    transition_duration: float = 0.2
    
    # Motion blending
    enable_motion_blend: bool = True
    blend_duration: float = 0.15


@dataclass
class LipSyncConfiguration:
    """口型同步配置 / Lip sync configuration"""
    enabled: bool = True
    update_rate: int = 30  # Hz
    smoothing_factor: float = 0.3
    phoneme_set: str = "japanese"  # japanese, english, chinese
    
    # Mouth shape intensity
    max_mouth_openness: float = 0.9
    min_mouth_openness: float = 0.1


@dataclass
class EyeTrackingConfiguration:
    """视线追踪配置 / Eye tracking configuration"""
    enabled: bool = True
    tracking_speed: float = 0.1
    max_eye_movement: float = 1.0
    head_follow_ratio: float = 0.3
    idle_movement: bool = True
    idle_range: float = 0.1
    idle_speed: float = 0.5


@dataclass
class ResourceCacheConfiguration:
    """资源缓存配置 / Resource cache configuration"""
    max_cache_size_mb: int = 512
    texture_cache_size: int = 100
    model_cache_size: int = 5
    preload_distance: int = 3
    enable_compression: bool = True
    compression_format: TextureFormat = TextureFormat.DDS
    
    # Cache eviction policy
    eviction_policy: str = "lru"  # lru, fifo, lfu
    ttl_seconds: int = 3600


@dataclass
class PerformanceConfiguration:
    """性能配置 / Performance configuration"""
    target_fps: int = 60
    adaptive_quality: bool = True
    quality_threshold_low: float = 30.0  # FPS
    quality_threshold_high: float = 55.0  # FPS
    
    # GPU settings
    enable_gpu_acceleration: bool = True
    max_gpu_memory_mb: int = 1024
    texture_streaming: bool = True
    
    # CPU settings
    max_update_threads: int = 4
    enable_multithreading: bool = True


@dataclass
class EffectConfiguration:
    """特效配置 / Effect configuration"""
    enable_particles: bool = True
    max_particles: int = 1000
    enable_bloom: bool = False
    enable_blur: bool = False
    enable_glow: bool = True
    
    # Transition effects
    transition_duration: float = 0.5
    transition_type: str = "fade"  # fade, slide, dissolve
    
    # Emotional atmosphere
    atmosphere_intensity: float = 0.5
    color_grading: bool = True


@dataclass
class VisualConfiguration:
    """
    视觉系统完整配置 / Complete visual system configuration
    
    Central configuration class for all visual system settings.
    
    Example:
        >>> config = VisualConfiguration()
        >>> config.model.model_name = "angela_custom"
        >>> config.render_quality = RenderQuality.HIGH
        >>> config.performance.target_fps = 60
    """
    
    # Quality settings
    render_quality: RenderQuality = RenderQuality.HIGH
    
    # Sub-configurations
    model: ModelConfiguration = field(default_factory=ModelConfiguration)
    expression: ExpressionConfiguration = field(default_factory=ExpressionConfiguration)
    motion: MotionConfiguration = field(default_factory=MotionConfiguration)
    lip_sync: LipSyncConfiguration = field(default_factory=LipSyncConfiguration)
    eye_tracking: EyeTrackingConfiguration = field(default_factory=EyeTrackingConfiguration)
    cache: ResourceCacheConfiguration = field(default_factory=ResourceCacheConfiguration)
    performance: PerformanceConfiguration = field(default_factory=PerformanceConfiguration)
    effects: EffectConfiguration = field(default_factory=EffectConfiguration)
    
    # Asset paths
    assets_base_path: str = "assets"
    models_path: str = "assets/models/live2d"
    expressions_path: str = "assets/expressions"
    motions_path: str = "assets/motions"
    backgrounds_path: str = "assets/backgrounds"
    effects_path: str = "assets/effects"
    
    # Runtime settings
    enable_logging: bool = True
    log_level: str = "INFO"
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate and adjust configuration"""
        # Ensure paths are valid
        self.assets_base_path = str(Path(self.assets_base_path))
        self.models_path = str(Path(self.models_path))
        self.expressions_path = str(Path(self.expressions_path))
        self.motions_path = str(Path(self.motions_path))
        self.backgrounds_path = str(Path(self.backgrounds_path))
        self.effects_path = str(Path(self.effects_path))
    
    def get_model_path(self, model_name: Optional[str] = None) -> str:
        """Get full model path"""
        name = model_name or self.model.model_name
        return str(Path(self.models_path) / name / self.model.model_file)
    
    def get_asset_path(self, asset_type: str, asset_name: str) -> str:
        """Get full asset path"""
        paths = {
            "model": self.models_path,
            "expression": self.expressions_path,
            "motion": self.motions_path,
            "background": self.backgrounds_path,
            "effect": self.effects_path,
        }
        base = paths.get(asset_type, self.assets_base_path)
        return str(Path(base) / asset_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "render_quality": self.render_quality.name,
            "model": {
                "model_name": self.model.model_name,
                "texture_resolution": self.model.texture_resolution,
                "lod_levels": self.model.lod_levels,
            },
            "expression": {
                "blend_duration": self.expression.blend_duration,
                "max_blend_layers": self.expression.max_blend_layers,
            },
            "motion": {
                "default_duration": self.motion.default_duration,
                "max_queue_size": self.motion.max_queue_size,
            },
            "lip_sync": {
                "enabled": self.lip_sync.enabled,
                "update_rate": self.lip_sync.update_rate,
            },
            "eye_tracking": {
                "enabled": self.eye_tracking.enabled,
                "tracking_speed": self.eye_tracking.tracking_speed,
            },
            "performance": {
                "target_fps": self.performance.target_fps,
                "adaptive_quality": self.performance.adaptive_quality,
            },
            "effects": {
                "enable_particles": self.effects.enable_particles,
                "max_particles": self.effects.max_particles,
            },
            "paths": {
                "assets_base": self.assets_base_path,
                "models": self.models_path,
                "expressions": self.expressions_path,
                "motions": self.motions_path,
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualConfiguration":
        """Create configuration from dictionary"""
        config = cls()
        
        if "render_quality" in data:
            config.render_quality = RenderQuality[data["render_quality"]]
        
        if "model" in data:
            model_data = data["model"]
            config.model.model_name = model_data.get("model_name", config.model.model_name)
            config.model.texture_resolution = model_data.get("texture_resolution", config.model.texture_resolution)
        
        if "performance" in data:
            perf_data = data["performance"]
            config.performance.target_fps = perf_data.get("target_fps", config.performance.target_fps)
            config.performance.adaptive_quality = perf_data.get("adaptive_quality", config.performance.adaptive_quality)
        
        if "paths" in data:
            paths_data = data["paths"]
            config.assets_base_path = paths_data.get("assets_base", config.assets_base_path)
            config.models_path = paths_data.get("models", config.models_path)
        
        return config
    
    def optimize_for_quality(self, quality: RenderQuality):
        """Optimize all settings for specific quality level"""
        self.render_quality = quality
        
        if quality == RenderQuality.LOW:
            self.model.texture_resolution = 1024
            self.model.lod_levels = 2
            self.effects.enable_particles = False
            self.effects.enable_bloom = False
            self.performance.target_fps = 30
            self.lip_sync.update_rate = 15
            
        elif quality == RenderQuality.MEDIUM:
            self.model.texture_resolution = 2048
            self.model.lod_levels = 3
            self.effects.enable_particles = True
            self.effects.max_particles = 500
            self.effects.enable_bloom = False
            self.performance.target_fps = 60
            self.lip_sync.update_rate = 30
            
        elif quality == RenderQuality.HIGH:
            self.model.texture_resolution = 2048
            self.model.lod_levels = 4
            self.effects.enable_particles = True
            self.effects.max_particles = 1000
            self.effects.enable_bloom = True
            self.performance.target_fps = 60
            self.lip_sync.update_rate = 60
            
        elif quality == RenderQuality.ULTRA:
            self.model.texture_resolution = 4096
            self.model.lod_levels = 5
            self.effects.enable_particles = True
            self.effects.max_particles = 2000
            self.effects.enable_bloom = True
            self.effects.enable_blur = True
            self.performance.target_fps = 60
            self.lip_sync.update_rate = 60


# Default configurations for different scenarios
HIGH_PERFORMANCE_CONFIG = VisualConfiguration()
HIGH_PERFORMANCE_CONFIG.optimize_for_quality(RenderQuality.LOW)

BALANCED_CONFIG = VisualConfiguration()
BALANCED_CONFIG.optimize_for_quality(RenderQuality.MEDIUM)

HIGH_QUALITY_CONFIG = VisualConfiguration()
HIGH_QUALITY_CONFIG.optimize_for_quality(RenderQuality.HIGH)

ULTRA_QUALITY_CONFIG = VisualConfiguration()
ULTRA_QUALITY_CONFIG.optimize_for_quality(RenderQuality.ULTRA)


def get_preset_config(preset: str) -> VisualConfiguration:
    """Get a preset configuration"""
    presets = {
        "performance": HIGH_PERFORMANCE_CONFIG,
        "balanced": BALANCED_CONFIG,
        "quality": HIGH_QUALITY_CONFIG,
        "ultra": ULTRA_QUALITY_CONFIG,
    }
    return presets.get(preset, BALANCED_CONFIG)


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Angela AI v6.0 - 视觉配置系统")
    print("Visual Configuration System")
    print("=" * 60)
    
    # Default configuration
    config = VisualConfiguration()
    print("\n默认配置 / Default configuration:")
    print(f"  渲染质量: {config.render_quality.value[0]}")
    print(f"  模型名称: {config.model.model_name}")
    print(f"  纹理分辨率: {config.model.texture_resolution}")
    print(f"  目标FPS: {config.performance.target_fps}")
    
    # High quality preset
    hq_config = get_preset_config("quality")
    print("\n高质量预设 / High quality preset:")
    print(f"  渲染质量: {hq_config.render_quality.value[0]}")
    print(f"  粒子效果: {'启用' if hq_config.effects.enable_particles else '禁用'}")
    print(f"  最大粒子数: {hq_config.effects.max_particles}")
    
    # Custom configuration
    custom = VisualConfiguration()
    custom.model.model_name = "angela_custom"
    custom.performance.target_fps = 144
    custom.effects.enable_glow = True
    
    print("\n自定义配置 / Custom configuration:")
    print(f"  模型名称: {custom.model.model_name}")
    print(f"  目标FPS: {custom.performance.target_fps}")
    print(f"  发光效果: {'启用' if custom.effects.enable_glow else '禁用'}")
    
    # Configuration to dict
    print("\n配置字典 / Configuration dict:")
    config_dict = custom.to_dict()
    for key, value in config_dict.items():
        print(f"  {key}: {value}")
