"""
Angela AI v6.0 - Live2D Avatar Generator
Live2D头像生成器

Generates anime-style Live2D avatars with proper rigging and parameter setup.
Creates layered PSD/PNG files and model3.json configurations.

Features:
- AI image generation for anime-style characters
- Multi-angle generation (front, side, 3/4)
- Automatic Live2D layer separation
- model3.json configuration generation
- 18 body part parameter binding

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from datetime import datetime
from pathlib import Path
import asyncio
import json
import math
import random
import logging
logger = logging.getLogger(__name__)


class GenerationStage(Enum):
    """生成阶段 / Generation stages"""
    INITIALIZING = ("初始化", "Initializing")
    GENERATING_BASE = ("生成基础图像", "Generating base images")
    CREATING_LAYERS = ("创建分层", "Creating layers")
    SETUP_RIGGING = ("设置绑定", "Setting up rigging")
    CONFIGURING_MODEL = ("配置模型", "Configuring model")
    FINALIZING = ("完成", "Finalizing")


class ViewAngle(Enum):
    """视角 / View angles"""
    FRONT = ("正面", "front", 0.0)
    THREE_QUARTER = ("3/4侧面", "three_quarter", 45.0)
    SIDE = ("侧面", "side", 90.0)
    
    def __init__(self, cn_name: str, en_name: str, angle_degrees: float):
        self.cn_name = cn_name
        self.en_name = en_name
        self.angle_degrees = angle_degrees


class BodyLayer(Enum):
    """身体分层 / Body layer hierarchy"""
    BODY_BACK = ("身体后层", 0)
    HAIR_BACK = ("头发后层", 1)
    BODY = ("身体", 2)
    ARMS = ("手臂", 3)
    HEAD_BASE = ("头部基础", 4)
    FACE = ("面部", 5)
    EYES_BACK = ("眼睛后层", 6)
    EYES = ("眼睛", 7)
    EYES_FRONT = ("眼睛前层", 8)
    MOUTH = ("嘴巴", 9)
    NOSE = ("鼻子", 10)
    EYEBROWS = ("眉毛", 11)
    HAIR_FRONT = ("头发前层", 12)
    FRONT_ACCESSORIES = ("前配饰", 13)
    
    def __init__(self, cn_name: str, order: int):
        self.cn_name = cn_name
        self.order = order


@dataclass
class LayerDefinition:
    """图层定义 / Layer definition"""
    layer_name: str
    body_layer: BodyLayer
    description: str
    parameters: List[str] = field(default_factory=list)
    parent_layer: Optional[str] = None
    clipping: Optional[str] = None  # Layer to clip to


@dataclass
class Live2DModelConfig:
    """Live2D模型配置 / Live2D model configuration"""
    model_name: str
    version: str = "1.0.0"
    
    # Texture settings
    texture_width: int = 2048
    texture_height: int = 2048
    texture_count: int = 1
    
    # Layout
    center_x: float = 0.0
    center_y: float = 0.0
    
    # Physics
    physics_enabled: bool = True
    physics_fps: int = 60
    
    # Hit areas
    hit_areas: Dict[str, Tuple[float, float, float, float]] = field(default_factory=dict)


@dataclass
class GeneratedLayer:
    """生成的图层 / Generated layer"""
    layer_id: str
    layer_name: str
    definition: LayerDefinition
    image_path: Optional[str] = None
    
    # Live2D specific
    mesh_vertices: List[Tuple[float, float]] = field(default_factory=list)
    uv_coordinates: List[Tuple[float, float]] = field(default_factory=list)
    
    # Position
    position_x: float = 0.0
    position_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0


@dataclass
class Live2DParameter:
    """Live2D参数 / Live2D parameter"""
    id: str
    type: str = "Normal"
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 1.0
    default_value: float = 0.0
    
    # Rigging
    affected_layers: List[str] = field(default_factory=list)
    deformation_type: str = "translate"  # translate, rotate, scale, deform


@dataclass
class GeneratedAvatar:
    """生成的头像 / Generated avatar"""
    avatar_id: str
    model_name: str
    
    # Paths
    output_directory: str = ""
    model_json_path: Optional[str] = None
    texture_paths: List[str] = field(default_factory=list)
    
    # Generated content
    layers: List[GeneratedLayer] = field(default_factory=list)
    parameters: Dict[str, Live2DParameter] = field(default_factory=dict)
    body_mappings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    view_angles: List[ViewAngle] = field(default_factory=list)
    generation_quality: float = 0.0
    
    def get_layer_by_name(self, name: str) -> Optional[GeneratedLayer]:
        """Get layer by name"""
        for layer in self.layers:
            if layer.layer_name == name:
                return layer
        return None


@dataclass
class GenerationProgress:
    """生成进度 / Generation progress"""
    stage: GenerationStage
    progress_percent: float  # 0-100
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class Live2DAvatarGenerator:
    """
    Live2D头像生成器主类 / Main Live2D avatar generator class
    
    Generates complete Live2D avatars with:
    - AI-generated anime-style images
    - Automatic layer separation
    - Proper Live2D rigging with 18 body parts
    - model3.json configuration
    - Multi-angle support
    
    Attributes:
        image_generator: Service for generating images
        art_learning_system: Art learning system for style knowledge
        output_path: Directory for generated files
        current_generation: Current generation in progress
    
    Example:
        >>> generator = Live2DAvatarGenerator(image_gen_service, art_system)
        >>> await generator.initialize()
        >>> 
        >>> # Generate avatar
        >>> avatar = await generator.generate_avatar(
        ...     model_name="angela_custom",
        ...     attributes={"hair_color": "pink", "eye_color": "blue"}
        ... )
        >>> 
        >>> # Generate with specific angles
        >>> avatar = await generator.generate_multi_angle_avatar(
        ...     model_name="angela_3d",
        ...     angles=[ViewAngle.FRONT, ViewAngle.THREE_QUARTER]
        ... )
    """
    
    # Standard layer definitions for anime character
    STANDARD_LAYERS = [
        LayerDefinition("body_back", BodyLayer.BODY_BACK, "Body back part", ["ParamBodyAngleX", "ParamBodyAngleY"]),
        LayerDefinition("hair_back", BodyLayer.HAIR_BACK, "Back hair", ["ParamHairBack", "ParamAngleX", "ParamAngleY"]),
        LayerDefinition("body", BodyLayer.BODY, "Main body", ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"]),
        LayerDefinition("arms", BodyLayer.ARMS, "Arms", ["ParamArmLA", "ParamArmRA"]),
        LayerDefinition("head_base", BodyLayer.HEAD_BASE, "Head base shape", ["ParamAngleX", "ParamAngleY", "ParamAngleZ"]),
        LayerDefinition("face", BodyLayer.FACE, "Face base", ["ParamAngleX", "ParamAngleY", "ParamCheek", "ParamFaceColor"]),
        LayerDefinition("eyes_back", BodyLayer.EYES_BACK, "Eyes back layer", ["ParamEyeBallX", "ParamEyeBallY"]),
        LayerDefinition("eye_l", BodyLayer.EYES, "Left eye", ["ParamEyeLOpen", "ParamEyeLSmile", "ParamEyeBallX", "ParamEyeBallY"]),
        LayerDefinition("eye_r", BodyLayer.EYES, "Right eye", ["ParamEyeROpen", "ParamEyeRSmile", "ParamEyeBallX", "ParamEyeBallY"]),
        LayerDefinition("eyes_front", BodyLayer.EYES_FRONT, "Eyes highlight", ["ParamEyeBallX", "ParamEyeBallY"]),
        LayerDefinition("mouth", BodyLayer.MOUTH, "Mouth", ["ParamMouthOpenY", "ParamMouthForm"]),
        LayerDefinition("nose", BodyLayer.NOSE, "Nose", []),
        LayerDefinition("eyebrow_l", BodyLayer.EYEBROWS, "Left eyebrow", ["ParamBrowLY", "ParamBrowLAngle", "ParamBrowLForm"]),
        LayerDefinition("eyebrow_r", BodyLayer.EYEBROWS, "Right eyebrow", ["ParamBrowRY", "ParamBrowRAngle", "ParamBrowRForm"]),
        LayerDefinition("hair_front", BodyLayer.HAIR_FRONT, "Front hair", ["ParamHairFront", "ParamHairSwing", "ParamAngleX", "ParamAngleY"]),
        LayerDefinition("hair_side", BodyLayer.HAIR_FRONT, "Side hair", ["ParamHairSide", "ParamAngleX", "ParamHairSwing"]),
        LayerDefinition("accessories", BodyLayer.FRONT_ACCESSORIES, "Accessories", ["ParamBodyAngleX", "ParamBodyAngleY"]),
    ]
    
    # Standard Live2D parameters
    STANDARD_PARAMETERS = {
        # Face angle (head tracking)
        "ParamAngleX": {"min": -30, "max": 30, "default": 0},
        "ParamAngleY": {"min": -30, "max": 30, "default": 0},
        "ParamAngleZ": {"min": -30, "max": 30, "default": 0},
        
        # Eye control
        "ParamEyeLOpen": {"min": 0, "max": 1, "default": 1},
        "ParamEyeROpen": {"min": 0, "max": 1, "default": 1},
        "ParamEyeLSmile": {"min": 0, "max": 1, "default": 0},
        "ParamEyeRSmile": {"min": 0, "max": 1, "default": 0},
        "ParamEyeBallX": {"min": -1, "max": 1, "default": 0},
        "ParamEyeBallY": {"min": -1, "max": 1, "default": 0},
        
        # Eyebrows
        "ParamBrowLY": {"min": -1, "max": 1, "default": 0},
        "ParamBrowRY": {"min": -1, "max": 1, "default": 0},
        "ParamBrowLAngle": {"min": -1, "max": 1, "default": 0},
        "ParamBrowRAngle": {"min": -1, "max": 1, "default": 0},
        "ParamBrowLForm": {"min": -1, "max": 1, "default": 0},
        "ParamBrowRForm": {"min": -1, "max": 1, "default": 0},
        
        # Mouth
        "ParamMouthForm": {"min": -1, "max": 1, "default": 0},
        "ParamMouthOpenY": {"min": 0, "max": 1, "default": 0},
        
        # Cheeks and blush
        "ParamCheek": {"min": 0, "max": 1, "default": 0},
        "ParamFaceColor": {"min": 0, "max": 1, "default": 0},
        
        # Body
        "ParamBodyAngleX": {"min": -10, "max": 10, "default": 0},
        "ParamBodyAngleY": {"min": -10, "max": 10, "default": 0},
        "ParamBodyAngleZ": {"min": -10, "max": 10, "default": 0},
        
        # Breathing
        "ParamBreath": {"min": 0, "max": 1, "default": 0},
        
        # Hair
        "ParamHairFront": {"min": -1, "max": 1, "default": 0},
        "ParamHairSide": {"min": -1, "max": 1, "default": 0},
        "ParamHairBack": {"min": -1, "max": 1, "default": 0},
        "ParamHairSwing": {"min": 0, "max": 1, "default": 0},
        
        # Arms
        "ParamArmLA": {"min": -1, "max": 1, "default": 0},
        "ParamArmRA": {"min": -1, "max": 1, "default": 0},
        "ParamHandL": {"min": -1, "max": 1, "default": 0},
        "ParamHandR": {"min": -1, "max": 1, "default": 0},
    }
    
    # 18 body parts to Live2D parameter mapping
    BODY_PART_MAPPING = {
        "top_of_head": {
            "parameters": ["ParamAngleX", "ParamAngleY", "ParamHairSwing"],
            "touch_response": {
                "pat": {"ParamAngleX": (-10, 10), "ParamAngleY": (-5, 5), "ParamHairSwing": (0, 0.5)},
                "stroke": {"ParamHairSwing": (0, 0.8), "ParamHairFront": (-0.2, 0.2)},
            }
        },
        "forehead": {
            "parameters": ["ParamBrowLY", "ParamBrowRY", "ParamAngleY"],
            "touch_response": {
                "pat": {"ParamBrowLY": (-0.3, 0.5), "ParamBrowRY": (-0.3, 0.5)},
                "poke": {"ParamBrowLY": (0.5, 0.8), "ParamBrowRY": (0.5, 0.8)},
            }
        },
        "face": {
            "parameters": ["ParamCheek", "ParamFaceColor", "ParamEyeLOpen", "ParamEyeROpen"],
            "touch_response": {
                "pat": {"ParamCheek": (0.2, 0.6), "ParamFaceColor": (0.1, 0.4)},
                "stroke": {"ParamCheek": (0.1, 0.3), "ParamFaceColor": (0.05, 0.15)},
                "poke": {"ParamEyeLOpen": (0.5, 0.8), "ParamEyeROpen": (0.5, 0.8), "ParamCheek": (0.3, 0.5)},
                "pinch": {"ParamMouthForm": (-0.5, 0.5), "ParamCheek": (0.4, 0.7)},
            }
        },
        "neck": {
            "parameters": ["ParamAngleX", "ParamAngleY", "ParamBodyAngleY"],
            "touch_response": {
                "stroke": {"ParamAngleX": (-5, 5), "ParamBodyAngleY": (-2, 2)},
                "pat": {"ParamAngleY": (3, 8)},
            }
        },
        "chest": {
            "parameters": ["ParamBodyAngleX", "ParamBreath"],
            "touch_response": {
                "pat": {"ParamBodyAngleX": (-5, 5), "ParamBreath": (0.1, 0.3)},
                "press": {"ParamBreath": (0.2, 0.5)},
            }
        },
        "back": {
            "parameters": ["ParamBodyAngleX", "ParamBodyAngleZ"],
            "touch_response": {
                "pat": {"ParamBodyAngleX": (-8, 8)},
                "stroke": {"ParamBodyAngleZ": (-3, 3)},
                "scratch": {"ParamBodyAngleX": (-5, 5), "ParamBodyAngleZ": (-2, 2)},
            }
        },
        "abdomen": {
            "parameters": ["ParamBodyAngleY", "ParamBreath"],
            "touch_response": {
                "pat": {"ParamBodyAngleY": (3, 6)},
                "press": {"ParamBreath": (0.1, 0.4)},
                "tickle": {"ParamBodyAngleY": (-5, 5), "ParamBreath": (0.2, 0.6)},
            }
        },
        "waist": {
            "parameters": ["ParamBodyAngleX", "ParamBodyAngleZ"],
            "touch_response": {
                "pat": {"ParamBodyAngleX": (-6, 6)},
                "stroke": {"ParamBodyAngleZ": (-4, 4)},
            }
        },
        "hips": {
            "parameters": ["ParamBodyAngleX", "ParamBodyAngleZ"],
            "touch_response": {
                "pat": {"ParamBodyAngleX": (-8, 8), "ParamBodyAngleZ": (-5, 5)},
            }
        },
        "thighs": {
            "parameters": ["ParamBodyAngleY"],
            "touch_response": {
                "pat": {"ParamBodyAngleY": (-2, 2)},
                "stroke": {"ParamBodyAngleY": (-1, 1)},
            }
        },
        "shoulders": {
            "parameters": ["ParamBodyAngleZ", "ParamArmLA", "ParamArmRA"],
            "touch_response": {
                "pat": {"ParamBodyAngleZ": (-5, 5)},
                "massage": {"ParamArmLA": (-0.3, 0.3), "ParamArmRA": (-0.3, 0.3)},
            }
        },
        "upper_arms": {
            "parameters": ["ParamArmLA", "ParamArmRA"],
            "touch_response": {
                "pat": {"ParamArmLA": (-0.5, 0.5), "ParamArmRA": (-0.5, 0.5)},
                "stroke": {"ParamArmLA": (-0.2, 0.2), "ParamArmRA": (-0.2, 0.2)},
            }
        },
        "forearms": {
            "parameters": ["ParamArmLA", "ParamArmRA", "ParamHandL", "ParamHandR"],
            "touch_response": {
                "pat": {"ParamArmLA": (-0.6, 0.6), "ParamArmRA": (-0.6, 0.6)},
                "stroke": {"ParamHandL": (-0.2, 0.2), "ParamHandR": (-0.2, 0.2)},
            }
        },
        "hands": {
            "parameters": ["ParamHandL", "ParamHandR"],
            "touch_response": {
                "pat": {"ParamHandL": (-0.8, 0.8), "ParamHandR": (-0.8, 0.8)},
                "hold": {"ParamHandL": (0.3, 0.7), "ParamHandR": (0.3, 0.7)},
                "stroke": {"ParamHandL": (-0.3, 0.3), "ParamHandR": (-0.3, 0.3)},
            }
        },
        "fingers": {
            "parameters": ["ParamHandL", "ParamHandR"],
            "touch_response": {
                "pat": {"ParamHandL": (-0.5, 0.5), "ParamHandR": (-0.5, 0.5)},
                "stroke": {"ParamHandL": (-0.2, 0.2), "ParamHandR": (-0.2, 0.2)},
            }
        },
        "knees": {
            "parameters": ["ParamBodyAngleY"],
            "touch_response": {
                "pat": {"ParamBodyAngleY": (-2, 2)},
            }
        },
        "calves": {
            "parameters": ["ParamBodyAngleY"],
            "touch_response": {
                "pat": {"ParamBodyAngleY": (-1, 1)},
                "stroke": {"ParamBodyAngleY": (-0.5, 0.5)},
            }
        },
        "feet": {
            "parameters": ["ParamBodyAngleY"],
            "touch_response": {
                "pat": {"ParamBodyAngleY": (-1, 1)},
                "tickle": {"ParamBodyAngleY": (-2, 2)},
            }
        },
    }
    
    def __init__(
        self,
        image_generator: Any,
        art_learning_system: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Live2D avatar generator
        
        Args:
            image_generator: Service for generating images
            art_learning_system: Art learning system for style knowledge
            config: Configuration dictionary
        """
        self.config = config or {}
        self.image_generator = image_generator
        self.art_learning_system = art_learning_system
        
        # Output configuration
        self.output_path = Path(self.config.get("output_path", "./live2d_models"))
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Generation state
        self._current_generation: Optional[GeneratedAvatar] = None
        self._generation_stage: GenerationStage = GenerationStage.INITIALIZING
        self._progress_callbacks: List[Callable[[GenerationProgress], None]] = []
        
        # Default configuration
        self.default_config = Live2DModelConfig(
            model_name=self.config.get("default_model_name", "angela"),
            texture_width=self.config.get("texture_width", 2048),
            texture_height=self.config.get("texture_height", 2048)
        )
    
    async def initialize(self):
        """Initialize the generator"""
        pass  # No async initialization needed
    
    async def shutdown(self):
        """Shutdown the generator"""
        pass
    
    def register_progress_callback(self, callback: Callable[[GenerationProgress], None]):
        """Register callback for generation progress updates"""
        self._progress_callbacks.append(callback)
    
    def _notify_progress(self, stage: GenerationStage, progress: float, message: str, details: Dict = None):
        """Notify progress callbacks"""
        progress_obj = GenerationProgress(
            stage=stage,
            progress_percent=progress,
            message=message,
            details=details or {}
        )
        
        for callback in self._progress_callbacks:
            try:
                callback(progress_obj)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

    
    async def generate_avatar(
        self,
        model_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        view_angle: ViewAngle = ViewAngle.FRONT,
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> GeneratedAvatar:
        """
        Generate a Live2D avatar
        
        Args:
            model_name: Name for the model
            attributes: Visual attributes (hair_color, eye_color, etc.)
            view_angle: View angle for generation
            style_preferences: Style preferences from art learning
            
        Returns:
            Generated avatar with layers and configuration
        """
        avatar_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        avatar = GeneratedAvatar(
            avatar_id=avatar_id,
            model_name=model_name,
            output_directory=str(self.output_path / avatar_id),
            view_angles=[view_angle]
        )
        
        self._current_generation = avatar
        
        try:
            # Stage 1: Initialize
            self._notify_progress(GenerationStage.INITIALIZING, 0, "Initializing generation...")
            await self._initialize_generation(avatar)
            
            # Stage 2: Generate base images
            self._notify_progress(GenerationStage.GENERATING_BASE, 10, "Generating base images...")
            await self._generate_base_images(avatar, attributes, view_angle)
            
            # Stage 3: Create layers
            self._notify_progress(GenerationStage.CREATING_LAYERS, 40, "Creating Live2D layers...")
            await self._create_layers(avatar, style_preferences)
            
            # Stage 4: Setup rigging
            self._notify_progress(GenerationStage.SETUP_RIGGING, 60, "Setting up body rigging...")
            await self._setup_rigging(avatar)
            
            # Stage 5: Configure model
            self._notify_progress(GenerationStage.CONFIGURING_MODEL, 80, "Configuring model3.json...")
            await self._configure_model(avatar)
            
            # Stage 6: Finalize
            self._notify_progress(GenerationStage.FINALIZING, 95, "Finalizing...")
            await self._finalize_generation(avatar)
            
            self._notify_progress(GenerationStage.FINALIZING, 100, "Generation complete!")
            
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self._notify_progress(GenerationStage.FINALIZING, 0, f"Generation failed: {str(e)}")

            raise
        
        finally:
            self._current_generation = None
        
        return avatar
    
    async def generate_multi_angle_avatar(
        self,
        model_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        angles: List[ViewAngle] = None,
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> GeneratedAvatar:
        """
        Generate Live2D avatar with multiple view angles
        
        Args:
            model_name: Name for the model
            attributes: Visual attributes
            angles: List of view angles to generate
            style_preferences: Style preferences
            
        Returns:
            Generated avatar with multi-angle support
        """
        if angles is None:
            angles = [ViewAngle.FRONT, ViewAngle.THREE_QUARTER]
        
        # Start with front view
        avatar = await self.generate_avatar(
            model_name=model_name,
            attributes=attributes,
            view_angle=angles[0],
            style_preferences=style_preferences
        )
        
        # Generate additional angles
        for i, angle in enumerate(angles[1:], 1):
            self._notify_progress(
                GenerationStage.GENERATING_BASE,
                10 + (i * 30 / len(angles)),
                f"Generating {angle.cn_name} view..."
            )
            
            # Generate angle-specific images
            await self._generate_angle_specific_layers(avatar, angle, attributes)
        
        avatar.view_angles = angles
        
        return avatar
    
    async def _initialize_generation(self, avatar: GeneratedAvatar):
        """Initialize generation directory and structure"""
        output_dir = Path(avatar.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (output_dir / "textures").mkdir(exist_ok=True)
        (output_dir / "layers").mkdir(exist_ok=True)
    
    async def _generate_base_images(
        self,
        avatar: GeneratedAvatar,
        attributes: Optional[Dict[str, Any]],
        view_angle: ViewAngle
    ):
        """Generate base anime-style images"""
        if not self.image_generator:
            return
        
        # Build generation prompt
        prompt = self._build_generation_prompt(attributes, view_angle)
        
        # Generate main character image
        try:
            if hasattr(self.image_generator, 'generate_image'):
                image_result = await self.image_generator.generate_image(
                    prompt=prompt,
                    width=self.default_config.texture_width,
                    height=self.default_config.texture_height,
                    style="anime"
                )
                
                # Store result path
                base_image_path = Path(avatar.output_directory) / "base_image.png"
                if hasattr(image_result, 'save'):
                    image_result.save(base_image_path)
                elif isinstance(image_result, str):
                    base_image_path = image_result
                
                avatar.texture_paths.append(str(base_image_path))
        except Exception as e:
            print(f"Image generation failed: {e}")
    
    def _build_generation_prompt(
        self,
        attributes: Optional[Dict[str, Any]],
        view_angle: ViewAngle
    ) -> str:
        """Build image generation prompt"""
        attrs = attributes or {}
        
        # Base description
        hair_color = attrs.get("hair_color", "pink")
        hair_style = attrs.get("hair_style", "long")
        eye_color = attrs.get("eye_color", "blue")
        outfit = attrs.get("outfit", "casual modern clothes")
        expression = attrs.get("expression", "gentle smile")
        
        # View angle description
        angle_desc = {
            ViewAngle.FRONT: "front view",
            ViewAngle.THREE_QUARTER: "three-quarter view, slightly turned",
            ViewAngle.SIDE: "side profile view"
        }.get(view_angle, "front view")
        
        # Build prompt
        prompt = (
            f"anime style character, {angle_desc}, {hair_color} {hair_style} hair, "
            f"{eye_color} eyes, {outfit}, {expression}, "
            f"high quality, detailed, clean line art, "
            f"suitable for Live2D rigging, transparent background"
        )
        
        return prompt
    
    async def _create_layers(
        self,
        avatar: GeneratedAvatar,
        style_preferences: Optional[Dict[str, Any]]
    ):
        """Create Live2D-compatible layers"""
        layers = []
        
        for layer_def in self.STANDARD_LAYERS:
            layer_id = f"{avatar.avatar_id}_{layer_def.layer_name}"
            
            layer = GeneratedLayer(
                layer_id=layer_id,
                layer_name=layer_def.layer_name,
                definition=layer_def,
                image_path=str(Path(avatar.output_directory) / "layers" / f"{layer_def.layer_name}.png")
            )
            
            # Generate or extract layer image
            await self._generate_layer_image(layer, style_preferences)
            
            layers.append(layer)
        
        avatar.layers = sorted(layers, key=lambda l: l.definition.body_layer.order)
    
    async def _generate_layer_image(
        self,
        layer: GeneratedLayer,
        style_preferences: Optional[Dict[str, Any]]
    ):
        """Generate or extract individual layer image"""
        # In a real implementation, this would:
        # 1. Use image segmentation to extract layers
        # 2. Or generate each layer separately
        # 3. Apply style preferences from art learning
        
        # For now, create placeholder
        layer.image_path = str(
            Path(self.output_path) / "placeholder_layers" / f"{layer.layer_name}.png"
        )
    
    async def _setup_rigging(self, avatar: GeneratedAvatar):
        """Setup Live2D rigging with body mappings"""
        # Create parameters
        for param_id, config in self.STANDARD_PARAMETERS.items():
            param = Live2DParameter(
                id=param_id,
                type="Normal",
                value=config["default"],
                min_value=config["min"],
                max_value=config["max"],
                default_value=config["default"]
            )
            
            # Associate with layers
            for layer in avatar.layers:
                if param_id in layer.definition.parameters:
                    param.affected_layers.append(layer.layer_id)
            
            avatar.parameters[param_id] = param
        
        # Store body mappings
        avatar.body_mappings = self.BODY_PART_MAPPING.copy()
    
    async def _configure_model(self, avatar: GeneratedAvatar):
        """Generate model3.json configuration"""
        model_config = {
            "Version": 3,
            "FileReferences": {
                "Moc": f"{avatar.model_name}.moc3",
                "Textures": [f"textures/texture_{i:02d}.png" for i in range(len(avatar.texture_paths))],
                "Physics": f"{avatar.model_name}.physics3.json",
                "DisplayInfo": f"{avatar.model_name}.cdi3.json"
            },
            "Groups": [
                {
                    "Target": "Parameter",
                    "Name": "EyeBlink",
                    "Ids": ["ParamEyeLOpen", "ParamEyeROpen"]
                },
                {
                    "Target": "Parameter",
                    "Name": "LipSync",
                    "Ids": ["ParamMouthOpenY"]
                }
            ],
            "HitAreas": []
        }
        
        # Add parameters
        model_config["Parameters"] = []
        for param_id, param in avatar.parameters.items():
            model_config["Parameters"].append({
                "Id": param_id,
                "Type": param.type,
                "Value": param.value,
                "Min": param.min_value,
                "Max": param.max_value,
                "Default": param.default_value
            })
        
        # Add parts (layers)
        model_config["Parts"] = []
        for layer in avatar.layers:
            model_config["Parts"].append({
                "Id": layer.layer_id,
                "Name": layer.layer_name
            })
        
        # Save configuration
        config_path = Path(avatar.output_directory) / f"{avatar.model_name}.model3.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, indent=2, ensure_ascii=False)
        
        avatar.model_json_path = str(config_path)
    
    async def _generate_angle_specific_layers(
        self,
        avatar: GeneratedAvatar,
        angle: ViewAngle,
        attributes: Optional[Dict[str, Any]]
    ):
        """Generate layers for specific view angle"""
        # Generate angle-specific images for key layers
        angle_suffix = f"_{angle.en_name}"
        
        key_layers = ["head_base", "face", "hair_front", "hair_side", "hair_back"]
        
        for layer_name in key_layers:
            layer = avatar.get_layer_by_name(layer_name)
            if layer:
                # Update image path for angle
                base_path = Path(layer.image_path)
                angle_path = base_path.parent / f"{base_path.stem}{angle_suffix}{base_path.suffix}"
                layer.image_path = str(angle_path)
                
                # Generate angle-specific image
                # (Implementation would generate or transform the image)
    
    async def _finalize_generation(self, avatar: GeneratedAvatar):
        """Finalize generation and create output files"""
        # Generate physics configuration
        await self._generate_physics_config(avatar)
        
        # Generate display info
        await self._generate_display_info(avatar)
        
        # Calculate quality score
        avatar.generation_quality = self._calculate_quality_score(avatar)
    
    async def _generate_physics_config(self, avatar: GeneratedAvatar):
        """Generate physics3.json for hair and accessories"""
        physics_config = {
            "Version": 3,
            "Meta": {
                "PhysicsSettingCount": 2,
                "TotalInputCount": 4,
                "TotalOutputCount": 4,
                "VertexCount": 6,
                "EffectiveForces": {
                    "Gravity": {"X": 0, "Y": -1},
                    "Wind": {"X": 0, "Y": 0}
                },
                "PhysicsDictionary": [
                    {"Id": "PhysicsHair", "Name": "Hair Physics"},
                    {"Id": "PhysicsBody", "Name": "Body Physics"}
                ]
            },
            "PhysicsSettings": [
                {
                    "Id": "PhysicsHair",
                    "Input": [
                        {
                            "Source": {"Target": "Parameter", "Id": "ParamAngleX"},
                            "Weight": 60,
                            "Type": "X"
                        },
                        {
                            "Source": {"Target": "Parameter", "Id": "ParamAngleY"},
                            "Weight": 40,
                            "Type": "Y"
                        }
                    ],
                    "Output": [
                        {
                            "Destination": {"Target": "Parameter", "Id": "ParamHairFront"},
                            "Weight": 80,
                            "Type": "Angle"
                        },
                        {
                            "Destination": {"Target": "Parameter", "Id": "ParamHairSide"},
                            "Weight": 60,
                            "Type": "Angle"
                        },
                        {
                            "Destination": {"Target": "Parameter", "Id": "ParamHairBack"},
                            "Weight": 40,
                            "Type": "Angle"
                        }
                    ],
                    "Vertices": [
                        {"Position": {"X": 0, "Y": 0}, "Mobility": 1, "Delay": 0, "Acceleration": 0, "Radius": 0},
                        {"Position": {"X": 0, "Y": 10}, "Mobility": 0.9, "Delay": 0.1, "Acceleration": 1, "Radius": 10},
                        {"Position": {"X": 0, "Y": 20}, "Mobility": 0.8, "Delay": 0.2, "Acceleration": 1.2, "Radius": 20}
                    ],
                    "Normalization": {
                        "Position": {"Minimum": -10, "Maximum": 10},
                        "Angle": {"Minimum": -10, "Maximum": 10}
                    }
                }
            ]
        }
        
        physics_path = Path(avatar.output_directory) / f"{avatar.model_name}.physics3.json"
        with open(physics_path, 'w', encoding='utf-8') as f:
            json.dump(physics_config, f, indent=2)
    
    async def _generate_display_info(self, avatar: GeneratedAvatar):
        """Generate cdi3.json (Cubism Display Information)"""
        display_info = {
            "Version": 3,
            "Parameters": [],
            "Parts": []
        }
        
        # Add parameter display info
        for param_id, param in avatar.parameters.items():
            display_info["Parameters"].append({
                "Id": param_id,
                "GroupId": "",
                "Name": param_id.replace("Param", "")
            })
        
        # Add part display info
        for layer in avatar.layers:
            display_info["Parts"].append({
                "Id": layer.layer_id,
                "Name": layer.layer_name
            })
        
        cdi_path = Path(avatar.output_directory) / f"{avatar.model_name}.cdi3.json"
        with open(cdi_path, 'w', encoding='utf-8') as f:
            json.dump(display_info, f, indent=2)
    
    def _calculate_quality_score(self, avatar: GeneratedAvatar) -> float:
        """Calculate generation quality score"""
        scores = []
        
        # Layer count
        scores.append(min(1.0, len(avatar.layers) / 15))
        
        # Parameter count
        scores.append(min(1.0, len(avatar.parameters) / 30))
        
        # Body mapping completeness
        scores.append(min(1.0, len(avatar.body_mappings) / 18))
        
        # Texture availability
        scores.append(1.0 if avatar.texture_paths else 0.5)
        
        # Config file existence
        scores.append(1.0 if avatar.model_json_path else 0.0)
        
        return sum(scores) / len(scores)
    
    def get_body_parameter_mapping(self, body_part: str) -> Dict[str, Any]:
        """Get Live2D parameter mapping for a body part"""
        return self.BODY_PART_MAPPING.get(body_part, {})
    
    def get_touch_response(
        self,
        body_part: str,
        touch_type: str,
        intensity: float = 0.5
    ) -> Dict[str, float]:
        """
        Get parameter values for touch response
        
        Args:
            body_part: Body part being touched
            touch_type: Type of touch
            intensity: Touch intensity (0-1)
            
        Returns:
            Parameter values for the touch
        """
        mapping = self.BODY_PART_MAPPING.get(body_part, {})
        touch_response = mapping.get("touch_response", {})
        
        params = touch_response.get(touch_type, touch_response.get("pat", {}))
        
        # Scale by intensity
        result = {}
        for param, (min_val, max_val) in params.items():
            value = min_val + (max_val - min_val) * intensity
            result[param] = value
        
        return result
    
    def get_all_body_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get all body part to parameter mappings"""
        return self.BODY_PART_MAPPING.copy()
    
    async def export_for_desktop_pet(self, avatar: GeneratedAvatar, export_path: str) -> str:
        """
        Export avatar for Desktop Pet integration
        
        Args:
            avatar: Generated avatar
            export_path: Export directory
            
        Returns:
            Path to exported model
        """
        export_dir = Path(export_path)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy essential files
        import shutil
        
        if avatar.model_json_path:
            shutil.copy2(avatar.model_json_path, export_dir)
        
        for texture_path in avatar.texture_paths:
            if Path(texture_path).exists():
                shutil.copy2(texture_path, export_dir / "textures")
        
        # Generate integration config
        integration_config = {
            "model_name": avatar.model_name,
            "model_path": str(export_dir / f"{avatar.model_name}.model3.json"),
            "body_mappings": avatar.body_mappings,
            "parameters": {k: v.default_value for k, v in avatar.parameters.items()},
            "touch_zones": self._generate_touch_zones(avatar)
        }
        
        config_path = export_dir / "desktop_pet_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(integration_config, f, indent=2)
        
        return str(export_dir)
    
    def _generate_touch_zones(self, avatar: GeneratedAvatar) -> Dict[str, Dict[str, Any]]:
        """Generate touch zone definitions for Desktop Pet"""
        zones = {}
        
        for body_part, mapping in avatar.body_mappings.items():
            zones[body_part] = {
                "parameters": mapping.get("parameters", []),
                "touch_types": list(mapping.get("touch_response", {}).keys()),
                "sensitivity": 1.0
            }
        
        return zones


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 60)
        print("Angela AI v6.0 - Live2D Avatar Generator Demo")
        print("=" * 60)
        
        # Mock image generator
        class MockImageGenerator:
            async def generate_image(self, prompt, width=2048, height=2048, style="anime"):
                print(f"   Generating: {prompt[:50]}...")
                return type('Image', (), {
                    'save': lambda path: print(f"   Saved to {path}")
                })()
        
        # Initialize generator
        generator = Live2DAvatarGenerator(
            image_generator=MockImageGenerator(),
            config={"output_path": "./demo_models"}
        )
        
        # Progress callback
        def on_progress(progress):
            print(f"[{progress.progress_percent:3.0f}%] {progress.message}")
        
        generator.register_progress_callback(on_progress)
        
        # Generate avatar
        print("\n1. Generating Live2D avatar...")
        avatar = await generator.generate_avatar(
            model_name="angela_demo",
            attributes={
                "hair_color": "pink",
                "hair_style": "long",
                "eye_color": "blue",
                "outfit": "white dress",
                "expression": "smile"
            }
        )
        
        print(f"\n2. Generated avatar: {avatar.avatar_id}")
        print(f"   Layers: {len(avatar.layers)}")
        print(f"   Parameters: {len(avatar.parameters)}")
        print(f"   Quality: {avatar.generation_quality:.2%}")
        
        # Show body mappings
        print(f"\n3. Body mappings (18 parts):")
        for i, (body_part, mapping) in enumerate(avatar.body_mappings.items(), 1):
            params = mapping.get("parameters", [])
            print(f"   {i:2d}. {body_part}: {len(params)} parameters")
        
        # Show touch response
        print(f"\n4. Touch response example (pat on head):")
        response = generator.get_touch_response("top_of_head", "pat", 0.7)
        for param, value in response.items():
            print(f"   {param}: {value:.2f}")
        
        # Multi-angle generation
        print(f"\n5. Multi-angle avatar generation...")
        multi_avatar = await generator.generate_multi_angle_avatar(
            model_name="angela_multi",
            angles=[ViewAngle.FRONT, ViewAngle.THREE_QUARTER],
            attributes={"hair_color": "blue"}
        )
        print(f"   Generated {len(multi_avatar.view_angles)} angles")
        
        # Export for Desktop Pet
        print(f"\n6. Exporting for Desktop Pet...")
        export_path = await generator.export_for_desktop_pet(
            avatar,
            "./demo_models/desktop_pet_export"
        )
        print(f"   Exported to: {export_path}")
        
        print("\nDemo complete!")
    
    asyncio.run(demo())
