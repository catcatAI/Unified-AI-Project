"""
Angela AI v6.0 - Art Learning System
艺术学习系统

Comprehensive art learning system for Live2D and anime art creation.
Searches tutorials, analyzes images, and accumulates knowledge through neuroplasticity.

Features:
- Tutorial search via browser controller
- Image analysis with visual AI
- Knowledge accumulation with neuroplasticity
- Explicit and implicit learning
- Power law skill acquisition

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import json
import math
import re
import logging
logger = logging.getLogger(__name__)


class LearningType(Enum):
    """学习类型 / Learning types"""
    EXPLICIT = ("显性学习", "Conscious learning of techniques")
    IMPLICIT = ("隐性学习", "Unconscious style absorption")
    SKILL_ACQUISITION = ("技能习得", "Motor/skill learning through practice")


class ArtDomain(Enum):
    """艺术领域 / Art domains"""
    LIVE2D = ("Live2D", "Live2D model creation")
    ANIME_ART = ("动漫绘画", "Anime art and illustration")
    CHARACTER_DESIGN = ("角色设计", "Character design principles")
    COLOR_THEORY = ("色彩理论", "Color theory and application")
    COMPOSITION = ("构图", "Composition techniques")
    LINE_ART = ("线稿", "Line art and inking")
    SHADING = ("光影", "Shading and lighting")
    RIGGING = ("绑定", "Live2D rigging and parameters")


@dataclass
class Live2DParameter:
    """Live2D参数定义 / Live2D parameter definition"""
    name: str
    min_value: float
    max_value: float
    default_value: float
    description: str = ""
    body_part: Optional[str] = None  # Associated body part
    
    def normalize_value(self, value: float) -> float:
        """Normalize value to 0-1 range"""
        return (value - self.min_value) / (self.max_value - self.min_value)
    
    def denormalize_value(self, normalized: float) -> float:
        """Convert normalized value back to parameter range"""
        return normalized * (self.max_value - self.min_value) + self.min_value


@dataclass
class BodyPartMapping:
    """身体部位映射 / Body part to Live2D mapping"""
    body_part: str
    live2d_params: Dict[str, Tuple[float, float]]  # param_name -> (min_effect, max_effect)
    touch_types: Dict[str, Dict[str, Any]]  # touch_type -> parameter changes
    sensitivity: float = 1.0


@dataclass
class StyleFeature:
    """风格特征 / Style feature"""
    feature_type: str  # color, line, composition, etc.
    description: str
    examples: List[str] = field(default_factory=list)
    confidence: float = 0.5  # 0-1, how confident we are about this feature


@dataclass
class ImageAnalysis:
    """图像分析结果 / Image analysis result"""
    image_id: str
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    
    # Style analysis
    style_features: List[StyleFeature] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    line_style: str = ""
    composition_type: str = ""
    
    # Live2D specific
    has_live2d_structure: bool = False
    layer_count: int = 0
    parameter_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    body_part_visibility: Dict[str, float] = field(default_factory=dict)  # body part -> visibility score
    
    # Analysis metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    analysis_confidence: float = 0.0


@dataclass
class TutorialContent:
    """教程内容 / Tutorial content"""
    tutorial_id: str
    title: str
    url: str
    source: str  # YouTube, Bilibili, etc.
    
    # Content
    summary: str = ""
    steps: List[str] = field(default_factory=list)
    key_techniques: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    
    # Metadata
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    duration_minutes: float = 0.0
    language: str = "en"
    view_count: int = 0
    
    # Learning state
    is_learned: bool = False
    learned_at: Optional[datetime] = None
    mastery_level: float = 0.0  # 0-1


@dataclass
class ArtKnowledge:
    """艺术知识 / Art knowledge"""
    knowledge_id: str
    technique: str  # Technique name
    domain: ArtDomain
    
    # Knowledge content
    style_features: Dict[str, Any] = field(default_factory=dict)
    body_part_mapping: Dict[str, BodyPartMapping] = field(default_factory=dict)
    examples: List[ImageAnalysis] = field(default_factory=list)
    tutorials: List[str] = field(default_factory=list)  # Tutorial IDs
    
    # Learning progress
    mastery_level: float = 0.0  # 0-1
    practice_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_practiced: Optional[datetime] = None
    
    # Neuroplasticity tracking
    memory_trace_id: Optional[str] = None
    consolidation_level: float = 0.0


@dataclass
class LearningSession:
    """学习会话 / Learning session"""
    session_id: str
    domain: ArtDomain
    learning_type: LearningType
    
    # Content
    tutorials_studied: List[str] = field(default_factory=list)
    images_analyzed: List[str] = field(default_factory=list)
    techniques_learned: List[str] = field(default_factory=list)
    
    # Progress
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_minutes: float = 0.0
    knowledge_gained: List[str] = field(default_factory=list)
    
    # Assessment
    self_assessment_score: float = 0.0  # 0-1
    quality_improvement: float = 0.0  # Measured improvement


class ArtLearningSystem:
    """
    艺术学习系统主类 / Main art learning system class
    
    Comprehensive system for learning anime art and Live2D creation through:
    1. Tutorial search and content extraction
    2. Image analysis with visual AI
    3. Knowledge accumulation via neuroplasticity
    
    Attributes:
        browser_controller: For searching tutorials
        vision_service: For analyzing images
        neuroplasticity: For knowledge retention
        knowledge_base: Accumulated art knowledge
        learning_history: Record of learning sessions
    
    Example:
        >>> art_system = ArtLearningSystem(browser_controller, vision_service)
        >>> await art_system.initialize()
        >>> 
        >>> # Search for tutorials
        >>> tutorials = await art_system.search_tutorials("Live2D rigging guide")
        >>> 
        >>> # Analyze images
        >>> analysis = await art_system.analyze_image("path/to/anime_art.png")
        >>> 
        >>> # Learn from content
        >>> knowledge = await art_system.learn_from_tutorial(tutorials[0])
    """
    
    # Standard Live2D parameter definitions
    STANDARD_LIVE2D_PARAMS = {
        # Facial angle
        "ParamAngleX": Live2DParameter("ParamAngleX", -30.0, 30.0, 0.0, "Head horizontal rotation", "face"),
        "ParamAngleY": Live2DParameter("ParamAngleY", -30.0, 30.0, 0.0, "Head vertical rotation", "face"),
        "ParamAngleZ": Live2DParameter("ParamAngleZ", -30.0, 30.0, 0.0, "Head tilt", "face"),
        
        # Eye control
        "ParamEyeLOpen": Live2DParameter("ParamEyeLOpen", 0.0, 1.0, 1.0, "Left eye open", "left_eye"),
        "ParamEyeROpen": Live2DParameter("ParamEyeROpen", 0.0, 1.0, 1.0, "Right eye open", "right_eye"),
        "ParamEyeLSmile": Live2DParameter("ParamEyeLSmile", 0.0, 1.0, 0.0, "Left eye smile", "left_eye"),
        "ParamEyeRSmile": Live2DParameter("ParamEyeRSmile", 0.0, 1.0, 0.0, "Right eye smile", "right_eye"),
        "ParamEyeBallX": Live2DParameter("ParamEyeBallX", -1.0, 1.0, 0.0, "Eye gaze horizontal", "eyes"),
        "ParamEyeBallY": Live2DParameter("ParamEyeBallY", -1.0, 1.0, 0.0, "Eye gaze vertical", "eyes"),
        
        # Eyebrows
        "ParamBrowLY": Live2DParameter("ParamBrowLY", -1.0, 1.0, 0.0, "Left eyebrow vertical", "left_eyebrow"),
        "ParamBrowRY": Live2DParameter("ParamBrowRY", -1.0, 1.0, 0.0, "Right eyebrow vertical", "right_eyebrow"),
        "ParamBrowLAngle": Live2DParameter("ParamBrowLAngle", -1.0, 1.0, 0.0, "Left eyebrow angle", "left_eyebrow"),
        "ParamBrowRAngle": Live2DParameter("ParamBrowRAngle", -1.0, 1.0, 0.0, "Right eyebrow angle", "right_eyebrow"),
        "ParamBrowLForm": Live2DParameter("ParamBrowLForm", -1.0, 1.0, 0.0, "Left eyebrow shape", "left_eyebrow"),
        "ParamBrowRForm": Live2DParameter("ParamBrowRForm", -1.0, 1.0, 0.0, "Right eyebrow shape", "right_eyebrow"),
        
        # Mouth
        "ParamMouthForm": Live2DParameter("ParamMouthForm", -1.0, 1.0, 0.0, "Mouth shape", "mouth"),
        "ParamMouthOpenY": Live2DParameter("ParamMouthOpenY", 0.0, 1.0, 0.0, "Mouth openness", "mouth"),
        
        # Cheeks and blush
        "ParamCheek": Live2DParameter("ParamCheek", 0.0, 1.0, 0.0, "Blush/cheek intensity", "face"),
        "ParamFaceColor": Live2DParameter("ParamFaceColor", 0.0, 1.0, 0.0, "Face color change", "face"),
        
        # Body
        "ParamBodyAngleX": Live2DParameter("ParamBodyAngleX", -10.0, 10.0, 0.0, "Body horizontal rotation", "body"),
        "ParamBodyAngleY": Live2DParameter("ParamBodyAngleY", -10.0, 10.0, 0.0, "Body vertical rotation", "body"),
        "ParamBodyAngleZ": Live2DParameter("ParamBodyAngleZ", -10.0, 10.0, 0.0, "Body tilt", "body"),
        
        # Breathing
        "ParamBreath": Live2DParameter("ParamBreath", 0.0, 1.0, 0.0, "Breathing animation", "body"),
        
        # Hair
        "ParamHairFront": Live2DParameter("ParamHairFront", -1.0, 1.0, 0.0, "Front hair movement", "hair"),
        "ParamHairSide": Live2DParameter("ParamHairSide", -1.0, 1.0, 0.0, "Side hair movement", "hair"),
        "ParamHairBack": Live2DParameter("ParamHairBack", -1.0, 1.0, 0.0, "Back hair movement", "hair"),
        "ParamHairSwing": Live2DParameter("ParamHairSwing", 0.0, 1.0, 0.0, "Hair swing animation", "hair"),
        
        # Arms
        "ParamArmLA": Live2DParameter("ParamArmLA", -1.0, 1.0, 0.0, "Left arm angle", "left_arm"),
        "ParamArmRA": Live2DParameter("ParamArmRA", -1.0, 1.0, 0.0, "Right arm angle", "right_arm"),
        "ParamHandL": Live2DParameter("ParamHandL", -1.0, 1.0, 0.0, "Left hand gesture", "left_hand"),
        "ParamHandR": Live2DParameter("ParamHandR", -1.0, 1.0, 0.0, "Right hand gesture", "right_hand"),
    }
    
    # 18 Body parts mapping to Live2D parameters
    BODY_TO_LIVE2D_MAPPING = {
        "top_of_head": BodyPartMapping(
            body_part="top_of_head",
            live2d_params={
                "ParamAngleX": (-5.0, 5.0),
                "ParamAngleY": (-3.0, 3.0),
                "ParamHairSwing": (0.0, 0.3),
            },
            touch_types={
                "pat": {"ParamAngleX": (-10.0, 10.0), "ParamAngleY": (-5.0, 5.0), "ParamHairSwing": (0.0, 0.5)},
                "stroke": {"ParamHairSwing": (0.0, 0.8), "ParamHairFront": (-0.2, 0.2)},
                "rub": {"ParamAngleX": (-3.0, 3.0), "ParamHairSwing": (0.0, 0.2)},
            },
            sensitivity=0.8
        ),
        "forehead": BodyPartMapping(
            body_part="forehead",
            live2d_params={
                "ParamBrowLY": (-0.2, 0.2),
                "ParamBrowRY": (-0.2, 0.2),
                "ParamAngleY": (-2.0, 2.0),
            },
            touch_types={
                "pat": {"ParamBrowLY": (-0.3, 0.5), "ParamBrowRY": (-0.3, 0.5)},
                "stroke": {"ParamAngleY": (-3.0, 3.0)},
                "poke": {"ParamBrowLY": (0.5, 0.8), "ParamBrowRY": (0.5, 0.8)},
            },
            sensitivity=0.7
        ),
        "face": BodyPartMapping(
            body_part="face",
            live2d_params={
                "ParamCheek": (0.0, 0.3),
                "ParamFaceColor": (0.0, 0.2),
                "ParamEyeLOpen": (0.9, 1.0),
                "ParamEyeROpen": (0.9, 1.0),
            },
            touch_types={
                "pat": {"ParamCheek": (0.2, 0.6), "ParamFaceColor": (0.1, 0.4)},
                "stroke": {"ParamCheek": (0.1, 0.3), "ParamFaceColor": (0.05, 0.15)},
                "poke": {"ParamEyeLOpen": (0.5, 0.8), "ParamEyeROpen": (0.5, 0.8), "ParamCheek": (0.3, 0.5)},
                "pinch": {"ParamMouthForm": (-0.5, 0.5), "ParamCheek": (0.4, 0.7)},
            },
            sensitivity=1.0
        ),
        "neck": BodyPartMapping(
            body_part="neck",
            live2d_params={
                "ParamAngleX": (-3.0, 3.0),
                "ParamAngleY": (-2.0, 2.0),
                "ParamBodyAngleY": (-1.0, 1.0),
            },
            touch_types={
                "stroke": {"ParamAngleX": (-5.0, 5.0), "ParamBodyAngleY": (-2.0, 2.0)},
                "pat": {"ParamAngleY": (3.0, 8.0)},  # Head tilt back when patting neck
            },
            sensitivity=0.6
        ),
        "chest": BodyPartMapping(
            body_part="chest",
            live2d_params={
                "ParamBodyAngleX": (-3.0, 3.0),
                "ParamBreath": (0.0, 0.1),
            },
            touch_types={
                "pat": {"ParamBodyAngleX": (-5.0, 5.0), "ParamBreath": (0.1, 0.3)},
                "press": {"ParamBreath": (0.2, 0.5)},
            },
            sensitivity=0.5
        ),
        "back": BodyPartMapping(
            body_part="back",
            live2d_params={
                "ParamBodyAngleX": (-5.0, 5.0),
                "ParamBodyAngleZ": (-3.0, 3.0),
            },
            touch_types={
                "pat": {"ParamBodyAngleX": (-8.0, 8.0)},
                "stroke": {"ParamBodyAngleZ": (-3.0, 3.0)},
                "scratch": {"ParamBodyAngleX": (-5.0, 5.0), "ParamBodyAngleZ": (-2.0, 2.0)},
            },
            sensitivity=0.4
        ),
        "abdomen": BodyPartMapping(
            body_part="abdomen",
            live2d_params={
                "ParamBodyAngleY": (-2.0, 2.0),
                "ParamBreath": (0.0, 0.15),
            },
            touch_types={
                "pat": {"ParamBodyAngleY": (3.0, 6.0)},
                "press": {"ParamBreath": (0.1, 0.4)},
                "tickle": {"ParamBodyAngleY": (-5.0, 5.0), "ParamBreath": (0.2, 0.6)},
            },
            sensitivity=0.5
        ),
        "waist": BodyPartMapping(
            body_part="waist",
            live2d_params={
                "ParamBodyAngleX": (-4.0, 4.0),
                "ParamBodyAngleZ": (-3.0, 3.0),
            },
            touch_types={
                "pat": {"ParamBodyAngleX": (-6.0, 6.0)},
                "stroke": {"ParamBodyAngleZ": (-4.0, 4.0)},
            },
            sensitivity=0.5
        ),
        "hips": BodyPartMapping(
            body_part="hips",
            live2d_params={
                "ParamBodyAngleX": (-5.0, 5.0),
                "ParamBodyAngleZ": (-4.0, 4.0),
            },
            touch_types={
                "pat": {"ParamBodyAngleX": (-8.0, 8.0), "ParamBodyAngleZ": (-5.0, 5.0)},
            },
            sensitivity=0.4
        ),
        "thighs": BodyPartMapping(
            body_part="thighs",
            live2d_params={
                "ParamBodyAngleY": (-1.0, 1.0),
            },
            touch_types={
                "pat": {"ParamBodyAngleY": (-2.0, 2.0)},
                "stroke": {"ParamBodyAngleY": (-1.0, 1.0)},
            },
            sensitivity=0.4
        ),
        "shoulders": BodyPartMapping(
            body_part="shoulders",
            live2d_params={
                "ParamBodyAngleZ": (-3.0, 3.0),
                "ParamArmLA": (-0.2, 0.2),
                "ParamArmRA": (-0.2, 0.2),
            },
            touch_types={
                "pat": {"ParamBodyAngleZ": (-5.0, 5.0)},
                "massage": {"ParamArmLA": (-0.3, 0.3), "ParamArmRA": (-0.3, 0.3)},
            },
            sensitivity=0.6
        ),
        "upper_arms": BodyPartMapping(
            body_part="upper_arms",
            live2d_params={
                "ParamArmLA": (-0.3, 0.3),
                "ParamArmRA": (-0.3, 0.3),
            },
            touch_types={
                "pat": {"ParamArmLA": (-0.5, 0.5), "ParamArmRA": (-0.5, 0.5)},
                "stroke": {"ParamArmLA": (-0.2, 0.2), "ParamArmRA": (-0.2, 0.2)},
            },
            sensitivity=0.5
        ),
        "forearms": BodyPartMapping(
            body_part="forearms",
            live2d_params={
                "ParamArmLA": (-0.4, 0.4),
                "ParamArmRA": (-0.4, 0.4),
                "ParamHandL": (-0.1, 0.1),
                "ParamHandR": (-0.1, 0.1),
            },
            touch_types={
                "pat": {"ParamArmLA": (-0.6, 0.6), "ParamArmRA": (-0.6, 0.6)},
                "stroke": {"ParamHandL": (-0.2, 0.2), "ParamHandR": (-0.2, 0.2)},
            },
            sensitivity=0.6
        ),
        "hands": BodyPartMapping(
            body_part="hands",
            live2d_params={
                "ParamHandL": (-0.5, 0.5),
                "ParamHandR": (-0.5, 0.5),
            },
            touch_types={
                "pat": {"ParamHandL": (-0.8, 0.8), "ParamHandR": (-0.8, 0.8)},
                "hold": {"ParamHandL": (0.3, 0.7), "ParamHandR": (0.3, 0.7)},
                "stroke": {"ParamHandL": (-0.3, 0.3), "ParamHandR": (-0.3, 0.3)},
            },
            sensitivity=1.0
        ),
        "fingers": BodyPartMapping(
            body_part="fingers",
            live2d_params={
                "ParamHandL": (-0.3, 0.3),
                "ParamHandR": (-0.3, 0.3),
            },
            touch_types={
                "pat": {"ParamHandL": (-0.5, 0.5), "ParamHandR": (-0.5, 0.5)},
                "stroke": {"ParamHandL": (-0.2, 0.2), "ParamHandR": (-0.2, 0.2)},
            },
            sensitivity=1.0
        ),
        "knees": BodyPartMapping(
            body_part="knees",
            live2d_params={
                "ParamBodyAngleY": (-1.0, 1.0),
            },
            touch_types={
                "pat": {"ParamBodyAngleY": (-2.0, 2.0)},
            },
            sensitivity=0.6
        ),
        "calves": BodyPartMapping(
            body_part="calves",
            live2d_params={
                "ParamBodyAngleY": (-0.5, 0.5),
            },
            touch_types={
                "pat": {"ParamBodyAngleY": (-1.0, 1.0)},
                "stroke": {"ParamBodyAngleY": (-0.5, 0.5)},
            },
            sensitivity=0.5
        ),
        "feet": BodyPartMapping(
            body_part="feet",
            live2d_params={
                "ParamBodyAngleY": (-0.5, 0.5),
            },
            touch_types={
                "pat": {"ParamBodyAngleY": (-1.0, 1.0)},
                "tickle": {"ParamBodyAngleY": (-2.0, 2.0)},
            },
            sensitivity=0.8
        ),
    }
    
    def __init__(
        self,
        browser_controller: Any,
        vision_service: Any,
        neuroplasticity: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize art learning system
        
        Args:
            browser_controller: Browser controller for web search
            vision_service: Vision service for image analysis
            neuroplasticity: Neuroplasticity system for learning
            config: Configuration dictionary
        """
        self.config = config or {}
        self.browser_controller = browser_controller
        self.vision_service = vision_service
        self.neuroplasticity = neuroplasticity
        
        # Knowledge storage
        self.knowledge_base: Dict[str, ArtKnowledge] = {}
        self.tutorials: Dict[str, TutorialContent] = {}
        self.image_analyses: Dict[str, ImageAnalysis] = {}
        self.learning_sessions: List[LearningSession] = []
        
        # Search configuration
        self.search_keywords = {
            ArtDomain.LIVE2D: ["Live2D tutorial", "Live2D rigging guide", "Live2D model creation"],
            ArtDomain.ANIME_ART: ["anime art tutorial", "anime drawing guide", "manga art tutorial"],
            ArtDomain.CHARACTER_DESIGN: ["character design tutorial", "anime character design"],
            ArtDomain.COLOR_THEORY: ["anime coloring tutorial", "digital painting color theory"],
            ArtDomain.RIGGING: ["Live2D parameter setup", "Live2D physics tutorial"],
        }
        
        # Learning configuration
        self.power_law_exponent = self.config.get("power_law_exponent", 0.3)  # For skill acquisition
        self.min_practice_for_mastery = self.config.get("min_practice_for_mastery", 100)
        
        # Running state
        self._running = False
        self._current_session: Optional[LearningSession] = None
        
        # Statistics
        self.learning_stats = {
            "total_tutorials_searched": 0,
            "total_images_analyzed": 0,
            "total_knowledge_entries": 0,
            "total_learning_hours": 0.0,
        }
    
    async def initialize(self):
        """Initialize the art learning system"""
        self._running = True
        
        # Initialize neuroplasticity if available
        if self.neuroplasticity and hasattr(self.neuroplasticity, 'initialize'):
            await self.neuroplasticity.initialize()
    
    async def shutdown(self):
        """Shutdown the art learning system"""
        self._running = False
        
        if self._current_session:
            await self.end_learning_session()
    
    async def search_tutorials(
        self,
        query: str,
        domain: Optional[ArtDomain] = None,
        max_results: int = 10
    ) -> List[TutorialContent]:
        """
        Search for art tutorials using browser controller
        
        Args:
            query: Search query
            domain: Art domain (optional)
            max_results: Maximum results to return
            
        Returns:
            List of tutorial content
        """
        if not self.browser_controller:
            return []
        
        # Use browser controller to search
        search_results = await self.browser_controller.search(query, max_results=max_results)
        
        tutorials = []
        for result in search_results:
            # Extract tutorial content
            tutorial = await self._extract_tutorial_content(result, domain)
            if tutorial:
                tutorials.append(tutorial)
                self.tutorials[tutorial.tutorial_id] = tutorial
        
        self.learning_stats["total_tutorials_searched"] += len(tutorials)
        
        return tutorials
    
    async def search_domain_tutorials(
        self,
        domain: ArtDomain,
        max_results_per_keyword: int = 5
    ) -> List[TutorialContent]:
        """
        Search tutorials for a specific art domain
        
        Args:
            domain: Art domain to search
            max_results_per_keyword: Max results per keyword
            
        Returns:
            Combined list of tutorials
        """
        all_tutorials = []
        
        keywords = self.search_keywords.get(domain, [])
        for keyword in keywords:
            tutorials = await self.search_tutorials(
                keyword,
                domain=domain,
                max_results=max_results_per_keyword
            )
            all_tutorials.extend(tutorials)
        
        return all_tutorials
    
    async def _extract_tutorial_content(
        self,
        search_result: Any,
        domain: Optional[ArtDomain] = None
    ) -> Optional[TutorialContent]:
        """Extract tutorial content from search result"""
        # Generate unique ID
        tutorial_id = f"tutorial_{datetime.now().timestamp()}_{hash(search_result.url) % 10000}"
        
        # Extract content using browser controller
        content = None
        if hasattr(self.browser_controller, 'extract_content'):
            content = await self.browser_controller.extract_content(search_result.url)
        
        # Determine source
        source = "unknown"
        if "youtube" in search_result.url.lower():
            source = "YouTube"
        elif "bilibili" in search_result.url.lower():
            source = "Bilibili"
        elif "tutorial" in search_result.url.lower():
            source = "Tutorial Site"
        
        # Parse steps and techniques from content
        steps = []
        techniques = []
        
        if content and content.text_content:
            # Extract numbered steps
            step_pattern = r'(?:step|步骤|Step)\s*(\d+)[:.\s]+([^\n]+)'
            steps = [match[1] for match in re.findall(step_pattern, content.text_content, re.IGNORECASE)]
            
            # Extract techniques
            technique_keywords = [
                "layer", "mask", "blend", "gradient", "shadow", "highlight",
                "rigging", "parameter", "physics", "mesh", "texture",
                "color", "line", "stroke", "brush", "pen"
            ]
            
            for keyword in technique_keywords:
                if keyword.lower() in content.text_content.lower():
                    techniques.append(keyword)
        
        tutorial = TutorialContent(
            tutorial_id=tutorial_id,
            title=search_result.title,
            url=search_result.url,
            source=source,
            summary=content.summary if content else "",
            steps=steps[:20],  # Limit steps
            key_techniques=list(set(techniques))[:10],  # Limit techniques
            difficulty="beginner",  # Default
            language="en" if "en" in search_result.url else "unknown"
        )
        
        return tutorial
    
    async def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        analysis_type: str = "full"
    ) -> ImageAnalysis:
        """
        Analyze image using vision service
        
        Args:
            image_path: Local image path
            image_url: Image URL
            analysis_type: Type of analysis (full, style, live2d)
            
        Returns:
            Image analysis result
        """
        image_id = f"img_{datetime.now().timestamp()}_{hash(image_path or image_url) % 10000}"
        
        analysis = ImageAnalysis(
            image_id=image_id,
            image_path=image_path,
            image_url=image_url
        )
        
        if not self.vision_service:
            return analysis
        
        try:
            # Use vision service to analyze image
            if hasattr(self.vision_service, 'analyze_image'):
                vision_result = await self.vision_service.analyze_image(
                    image_path=image_path,
                    image_url=image_url
                )
                
                # Parse vision results
                analysis = self._parse_vision_results(analysis, vision_result)
            
            # Perform Live2D-specific analysis if requested
            if analysis_type in ["full", "live2d"]:
                analysis = await self._analyze_live2d_structure(analysis)
            
            self.image_analyses[image_id] = analysis
            self.learning_stats["total_images_analyzed"] += 1
            
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            analysis.analysis_confidence = 0.0

        
        return analysis
    
    def _parse_vision_results(
        self,
        analysis: ImageAnalysis,
        vision_result: Any
    ) -> ImageAnalysis:
        """Parse vision service results into image analysis"""
        # Extract style features
        if hasattr(vision_result, 'style_features'):
            for feature in vision_result.style_features:
                analysis.style_features.append(StyleFeature(
                    feature_type=feature.get("type", "unknown"),
                    description=feature.get("description", ""),
                    confidence=feature.get("confidence", 0.5)
                ))
        
        # Extract color palette
        if hasattr(vision_result, 'color_palette'):
            analysis.color_palette = vision_result.color_palette[:10]
        
        # Detect line style
        if hasattr(vision_result, 'line_style'):
            analysis.line_style = vision_result.line_style
        
        # Detect composition
        if hasattr(vision_result, 'composition'):
            analysis.composition_type = vision_result.composition
        
        analysis.analysis_confidence = getattr(vision_result, 'confidence', 0.5)
        
        return analysis
    
    async def _analyze_live2d_structure(self, analysis: ImageAnalysis) -> ImageAnalysis:
        """Analyze image for Live2D structure and parameters"""
        # Check if image has Live2D characteristics
        has_live2d_markers = False
        layer_count = 0
        
        # Check for layer indicators in style features
        for feature in analysis.style_features:
            if "layer" in feature.description.lower() or "separate" in feature.description.lower():
                has_live2d_markers = True
            if "layer count" in feature.feature_type.lower():
                try:
                    layer_count = int(re.search(r'\d+', feature.description).group())
                except (AttributeError, ValueError) as e:
                    logger.debug(f"層數提取失敗（可忽略）: {e}")
                    pass
        
        analysis.has_live2d_structure = has_live2d_markers
        analysis.layer_count = max(layer_count, 5)  # Assume at least 5 layers for Live2D
        
        # Suggest parameters based on visible body parts
        analysis.body_part_visibility = self._detect_body_parts(analysis)
        
        # Generate parameter suggestions
        analysis.parameter_suggestions = self._suggest_parameters(analysis.body_part_visibility)
        
        return analysis
    
    def _detect_body_parts(self, analysis: ImageAnalysis) -> Dict[str, float]:
        """Detect visible body parts in image"""
        visibility = {}
        
        # Check style features for body part mentions
        body_keywords = {
            "head": ["head", "hair", "top"],
            "face": ["face", "eyes", "mouth", "nose", "cheek"],
            "eyes": ["eye", "eyes", "gaze"],
            "body": ["body", "torso", "chest"],
            "arms": ["arm", "arms", "hand", "hands"],
            "hands": ["hand", "hands", "finger", "fingers"],
        }
        
        for part, keywords in body_keywords.items():
            score = 0.0
            for feature in analysis.style_features:
                desc = feature.description.lower()
                if any(kw in desc for kw in keywords):
                    score = max(score, feature.confidence)
            
            if score > 0.3:
                visibility[part] = score
        
        return visibility
    
    def _suggest_parameters(self, body_part_visibility: Dict[str, float]) -> List[Dict[str, Any]]:
        """Suggest Live2D parameters based on visible body parts"""
        suggestions = []
        
        # Map body parts to parameters
        part_to_params = {
            "head": ["ParamAngleX", "ParamAngleY", "ParamAngleZ"],
            "face": ["ParamCheek", "ParamFaceColor"],
            "eyes": ["ParamEyeLOpen", "ParamEyeROpen", "ParamEyeBallX", "ParamEyeBallY"],
            "body": ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ", "ParamBreath"],
            "arms": ["ParamArmLA", "ParamArmRA"],
            "hands": ["ParamHandL", "ParamHandR"],
        }
        
        for part, visibility in body_part_visibility.items():
            if part in part_to_params:
                for param_name in part_to_params[part]:
                    if param_name in self.STANDARD_LIVE2D_PARAMS:
                        param_def = self.STANDARD_LIVE2D_PARAMS[param_name]
                        suggestions.append({
                            "parameter": param_name,
                            "priority": visibility,
                            "range": (param_def.min_value, param_def.max_value),
                            "description": param_def.description,
                        })
        
        # Sort by priority
        suggestions.sort(key=lambda x: x["priority"], reverse=True)
        
        return suggestions
    
    async def learn_from_tutorial(
        self,
        tutorial: TutorialContent,
        learning_type: LearningType = LearningType.EXPLICIT
    ) -> ArtKnowledge:
        """
        Learn from a tutorial and create knowledge entry
        
        Args:
            tutorial: Tutorial to learn from
            learning_type: Type of learning
            
        Returns:
            Created knowledge entry
        """
        # Create knowledge ID
        knowledge_id = f"knowledge_{tutorial.tutorial_id}"
        
        # Determine domain
        domain = ArtDomain.LIVE2D
        for d in ArtDomain:
            if d.value[0].lower() in tutorial.title.lower():
                domain = d
                break
        
        # Create knowledge entry
        knowledge = ArtKnowledge(
            knowledge_id=knowledge_id,
            technique=tutorial.key_techniques[0] if tutorial.key_techniques else "general",
            domain=domain,
            style_features={"steps": tutorial.steps, "techniques": tutorial.key_techniques},
            tutorials=[tutorial.tutorial_id],
            mastery_level=0.1  # Initial low mastery
        )
        
        # Add body part mapping if relevant
        if domain == ArtDomain.LIVE2D or domain == ArtDomain.RIGGING:
            knowledge.body_part_mapping = self.BODY_TO_LIVE2D_MAPPING.copy()
        
        # Store in neuroplasticity if available
        if self.neuroplasticity and hasattr(self.neuroplasticity, 'create_memory_trace'):
            trace_id = self.neuroplasticity.create_memory_trace(
                content=knowledge,
                initial_weight=0.3,
                emotional_tags=["learning", "art", domain.value[0]]
            )
            knowledge.memory_trace_id = trace_id
        
        # Store knowledge
        self.knowledge_base[knowledge_id] = knowledge
        self.learning_stats["total_knowledge_entries"] += 1
        
        # Mark tutorial as learned
        tutorial.is_learned = True
        tutorial.learned_at = datetime.now()
        
        return knowledge
    
    async def learn_from_image_batch(
        self,
        image_analyses: List[ImageAnalysis],
        learning_type: LearningType = LearningType.IMPLICIT
    ) -> ArtKnowledge:
        """
        Implicit learning from batch of images (style absorption)
        
        Args:
            image_analyses: List of analyzed images
            learning_type: Should be IMPLICIT for style learning
            
        Returns:
            Aggregated knowledge
        """
        knowledge_id = f"implicit_{datetime.now().timestamp()}"
        
        # Aggregate style features
        aggregated_features: Dict[str, List[float]] = {}
        all_colors = []
        
        for analysis in image_analyses:
            for feature in analysis.style_features:
                if feature.feature_type not in aggregated_features:
                    aggregated_features[feature.feature_type] = []
                aggregated_features[feature.feature_type].append(feature.confidence)
            
            all_colors.extend(analysis.color_palette)
        
        # Calculate average features
        style_features = {}
        for feature_type, confidences in aggregated_features.items():
            style_features[feature_type] = {
                "average_confidence": sum(confidences) / len(confidences),
                "frequency": len(confidences) / len(image_analyses)
            }
        
        # Most common colors
        from collections import Counter
        color_counts = Counter(all_colors)
        common_colors = [color for color, _ in color_counts.most_common(10)]
        
        knowledge = ArtKnowledge(
            knowledge_id=knowledge_id,
            technique="style_absorption",
            domain=ArtDomain.ANIME_ART,
            style_features={
                "aggregated": style_features,
                "common_colors": common_colors,
                "sample_count": len(image_analyses)
            },
            examples=image_analyses[:5],  # Store top 5 examples
            mastery_level=0.2  # Implicit learning starts with moderate mastery
        )
        
        # Store in knowledge base
        self.knowledge_base[knowledge_id] = knowledge
        
        return knowledge
    
    def calculate_mastery_level(
        self,
        practice_count: int,
        success_rate: float,
        days_since_learning: float
    ) -> float:
        """
        Calculate mastery level using power law of learning
        
        Formula: Mastery = Success_Rate * (Practice_Count ^ exponent) / (1 + decay * days)
        
        Args:
            practice_count: Number of practice attempts
            success_rate: Success rate (0-1)
            days_since_learning: Days since first learning
            
        Returns:
            Mastery level (0-1)
        """
        # Power law component
        practice_component = math.pow(practice_count, self.power_law_exponent)
        
        # Normalization factor (reaches ~0.8 at 100 practices)
        normalization = practice_component / (practice_component + 20)
        
        # Decay component (forgetting)
        decay_rate = 0.01  # 1% per day
        retention = math.exp(-decay_rate * days_since_learning)
        
        # Calculate mastery
        mastery = success_rate * normalization * retention
        
        return min(1.0, max(0.0, mastery))
    
    async def practice_technique(
        self,
        knowledge_id: str,
        practice_quality: float,  # 0-1, how well the practice went
        duration_minutes: float
    ) -> float:
        """
        Record practice session and update mastery
        
        Args:
            knowledge_id: Knowledge entry ID
            practice_quality: Quality of practice (0-1)
            duration_minutes: Practice duration
            
        Returns:
            Updated mastery level
        """
        if knowledge_id not in self.knowledge_base:
            return 0.0
        
        knowledge = self.knowledge_base[knowledge_id]
        knowledge.practice_count += 1
        knowledge.last_practiced = datetime.now()
        
        # Calculate new mastery
        days_since = (datetime.now() - knowledge.created_at).days
        knowledge.mastery_level = self.calculate_mastery_level(
            knowledge.practice_count,
            practice_quality,
            days_since
        )
        
        # Update neuroplasticity
        if knowledge.memory_trace_id and self.neuroplasticity:
            if hasattr(self.neuroplasticity, 'apply_ltp'):
                self.neuroplasticity.apply_ltp(knowledge.memory_trace_id, practice_quality)
        
        self.learning_stats["total_learning_hours"] += duration_minutes / 60.0
        
        return knowledge.mastery_level
    
    async def start_learning_session(
        self,
        domain: ArtDomain,
        learning_type: LearningType
    ) -> LearningSession:
        """Start a new learning session"""
        session_id = f"session_{datetime.now().timestamp()}"
        
        self._current_session = LearningSession(
            session_id=session_id,
            domain=domain,
            learning_type=learning_type
        )
        
        return self._current_session
    
    async def end_learning_session(self) -> LearningSession:
        """End current learning session"""
        if not self._current_session:
            raise ValueError("No active learning session")
        
        session = self._current_session
        session.end_time = datetime.now()
        session.duration_minutes = (
            session.end_time - session.start_time
        ).total_seconds() / 60.0
        
        self.learning_sessions.append(session)
        self._current_session = None
        
        return session
    
    def get_body_mapping(self, body_part: str) -> Optional[BodyPartMapping]:
        """Get Live2D mapping for a body part"""
        return self.BODY_TO_LIVE2D_MAPPING.get(body_part)
    
    def get_all_body_mappings(self) -> Dict[str, BodyPartMapping]:
        """Get all body part to Live2D mappings"""
        return self.BODY_TO_LIVE2D_MAPPING.copy()
    
    def get_parameter_for_body_touch(
        self,
        body_part: str,
        touch_type: str,
        intensity: float = 0.5
    ) -> Dict[str, float]:
        """
        Get Live2D parameter changes for a body touch
        
        Args:
            body_part: Body part being touched
            touch_type: Type of touch (pat, stroke, poke, etc.)
            intensity: Touch intensity (0-1)
            
        Returns:
            Dictionary of parameter names to values
        """
        mapping = self.BODY_TO_LIVE2D_MAPPING.get(body_part)
        if not mapping:
            return {}
        
        touch_params = mapping.touch_types.get(touch_type, mapping.touch_types.get("pat", {}))
        
        # Scale by intensity and sensitivity
        result = {}
        for param, (min_val, max_val) in touch_params.items():
            value = min_val + (max_val - min_val) * intensity
            result[param] = value * mapping.sensitivity
        
        return result
    
    def get_knowledge_by_domain(self, domain: ArtDomain) -> List[ArtKnowledge]:
        """Get all knowledge entries for a domain"""
        return [k for k in self.knowledge_base.values() if k.domain == domain]
    
    def get_knowledge_by_mastery(self, min_mastery: float = 0.0) -> List[ArtKnowledge]:
        """Get knowledge entries above a mastery threshold"""
        return [k for k in self.knowledge_base.values() if k.mastery_level >= min_mastery]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        return {
            **self.learning_stats,
            "knowledge_by_domain": {
                domain.value[0]: len(self.get_knowledge_by_domain(domain))
                for domain in ArtDomain
            },
            "average_mastery": (
                sum(k.mastery_level for k in self.knowledge_base.values()) / len(self.knowledge_base)
                if self.knowledge_base else 0.0
            ),
            "total_sessions": len(self.learning_sessions),
            "body_parts_mapped": len(self.BODY_TO_LIVE2D_MAPPING),
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 60)
        print("Angela AI v6.0 - Art Learning System Demo")
        print("=" * 60)
        
        # Create mock services
        class MockBrowserController:
            async def search(self, query, max_results=10):
                return [type('Result', (), {
                    'title': f'{query} - Result {i+1}',
                    'url': f'https://example.com/{query.replace(" ", "-")}-{i+1}'
                })() for i in range(min(3, max_results))]
            
            async def extract_content(self, url):
                return type('Content', (), {
                    'summary': f'Summary of {url}',
                    'text_content': 'Step 1: Do this. Step 2: Do that. Layer masking technique.',
                })()
        
        class MockVisionService:
            async def analyze_image(self, image_path=None, image_url=None):
                return type('VisionResult', (), {
                    'style_features': [
                        {'type': 'line', 'description': 'Clean line art', 'confidence': 0.8},
                        {'type': 'color', 'description': 'Vibrant colors', 'confidence': 0.9},
                    ],
                    'color_palette': ['#FF6B6B', '#4ECDC4', '#45B7D1'],
                    'confidence': 0.85
                })()
        
        # Initialize system
        art_system = ArtLearningSystem(
            browser_controller=MockBrowserController(),
            vision_service=MockVisionService()
        )
        await art_system.initialize()
        
        # Search for tutorials
        print("\n1. Searching for Live2D tutorials...")
        tutorials = await art_system.search_domain_tutorials(ArtDomain.LIVE2D)
        print(f"   Found {len(tutorials)} tutorials")
        
        # Learn from tutorial
        if tutorials:
            print("\n2. Learning from tutorial...")
            knowledge = await art_system.learn_from_tutorial(tutorials[0])
            print(f"   Knowledge ID: {knowledge.knowledge_id}")
            print(f"   Technique: {knowledge.technique}")
            print(f"   Initial mastery: {knowledge.mastery_level:.2f}")
        
        # Analyze images
        print("\n3. Analyzing images...")
        analyses = []
        for i in range(3):
            analysis = await art_system.analyze_image(
                image_path=f"anime_art_{i}.png"
            )
            analyses.append(analysis)
            print(f"   Image {i+1}: {len(analysis.style_features)} features detected")
        
        # Implicit learning
        print("\n4. Implicit learning from image batch...")
        implicit_knowledge = await art_system.learn_from_image_batch(analyses)
        print(f"   Absorbed style from {implicit_knowledge.style_features.get('sample_count', 0)} images")
        
        # Practice
        if tutorials:
            print("\n5. Practicing technique...")
            new_mastery = await art_system.practice_technique(
                knowledge.knowledge_id,
                practice_quality=0.8,
                duration_minutes=30.0
            )
            print(f"   New mastery level: {new_mastery:.2f}")
        
        # Body mapping demo
        print("\n6. Body-to-Live2D mapping...")
        mapping = art_system.get_body_mapping("face")
        if mapping:
            print(f"   Face mapped to {len(mapping.live2d_params)} parameters")
            print(f"   Touch types: {list(mapping.touch_types.keys())}")
        
        # Get touch response
        touch_response = art_system.get_parameter_for_body_touch("top_of_head", "pat", 0.7)
        print(f"\n7. Touch response for 'pat on head':")
        for param, value in touch_response.items():
            print(f"   {param}: {value:.2f}")
        
        # Statistics
        print("\n8. Learning statistics:")
        stats = art_system.get_learning_statistics()
        print(f"   Total tutorials: {stats['total_tutorials_searched']}")
        print(f"   Total images: {stats['total_images_analyzed']}")
        print(f"   Knowledge entries: {stats['total_knowledge_entries']}")
        print(f"   Body parts mapped: {stats['body_parts_mapped']}")
        
        await art_system.shutdown()
        print("\nSystem shutdown complete")
    
    asyncio.run(demo())
