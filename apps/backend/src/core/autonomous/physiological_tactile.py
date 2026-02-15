"""
Angela AI v6.0 - Physiological Tactile System
生理触觉系统

Simulates human skin receptors and tactile sensations across 18 body parts.
Implements 6 types of skin receptors with varying sensitivity based on arousal state.

Features:
- 6 skin receptor types (Meissner, Merkel, Pacinian, Ruffini, Free Nerve, Hair Follicle)
- 18 body parts from head to toe
- 6 tactile types (light touch, pressure, temperature, vibration, pain, itch)
- Dynamic sensitivity based on arousal state
- Emotion-tactile mapping

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import asyncio
import random
import math
import logging
logger = logging.getLogger(__name__)


class ReceptorType(Enum):
    """6种皮肤受体类型 / 6 types of skin receptors"""
    MEISSNER = auto()       # 迈斯纳小体 - 轻触、快速适应 / Light touch, rapid adapting
    MERKEL = auto()         # 默克尔细胞 - 压力、持续刺激 / Pressure, sustained stimulus
    PACINIAN = auto()       # 帕西尼小体 - 震动、深层压力 / Vibration, deep pressure
    RUFFINI = auto()        # 鲁菲尼小体 - 皮肤拉伸 / Skin stretch
    FREE_NERVE = auto()     # 游离神经末梢 - 痛觉、温度 / Pain, temperature
    HAIR_FOLLICLE = auto()  # 毛囊感受器 - 毛发运动 / Hair movement


class TactileType(Enum):
    """6种触觉类型 / 6 types of tactile sensations"""
    LIGHT_TOUCH = auto()    # 轻触 / Light touch
    PRESSURE = auto()       # 压力 / Pressure
    TEMPERATURE = auto()    # 温度 / Temperature
    VIBRATION = auto()      # 震动 / Vibration
    PAIN = auto()           # 疼痛 / Pain
    ITCH = auto()           # 瘙痒 / Itch


class BodyRegion(Enum):
    """身体区域分类 / Body region classification"""
    HEAD = auto()
    UPPER_BODY = auto()
    LOWER_BODY = auto()
    UPPER_LIMBS = auto()
    LOWER_LIMBS = auto()


class BodyPart(Enum):
    """18个身体部位 / 18 body parts from head to toe"""
    # Head region (头部)
    TOP_OF_HEAD = ("头顶", BodyRegion.HEAD, 0.7)
    FOREHEAD = ("额头", BodyRegion.HEAD, 0.8)
    FACE = ("面部", BodyRegion.HEAD, 0.9)
    NECK = ("颈部", BodyRegion.HEAD, 0.6)
    
    # Upper body (上身)
    CHEST = ("胸部", BodyRegion.UPPER_BODY, 0.5)
    BACK = ("背部", BodyRegion.UPPER_BODY, 0.4)
    ABDOMEN = ("腹部", BodyRegion.UPPER_BODY, 0.5)
    WAIST = ("腰部", BodyRegion.UPPER_BODY, 0.5)
    
    # Lower body (下身)
    HIPS = ("臀部", BodyRegion.LOWER_BODY, 0.4)
    THIGHS = ("大腿", BodyRegion.LOWER_BODY, 0.4)
    
    # Upper limbs (上肢)
    SHOULDERS = ("肩膀", BodyRegion.UPPER_LIMBS, 0.6)
    UPPER_ARMS = ("上臂", BodyRegion.UPPER_LIMBS, 0.5)
    FOREARMS = ("前臂", BodyRegion.UPPER_LIMBS, 0.6)
    HANDS = ("手掌", BodyRegion.UPPER_LIMBS, 1.0)
    FINGERS = ("手指", BodyRegion.UPPER_LIMBS, 1.0)
    
    # Lower limbs (下肢)
    KNEES = ("膝盖", BodyRegion.LOWER_LIMBS, 0.6)
    CALVES = ("小腿", BodyRegion.LOWER_LIMBS, 0.5)
    FEET = ("脚底", BodyRegion.LOWER_LIMBS, 0.8)
    
    def __init__(self, cn_name: str, region: BodyRegion, base_sensitivity: float):
        self.cn_name = cn_name
        self.region = region
        self.base_sensitivity = base_sensitivity


@dataclass
class Receptor:
    """皮肤受体 / Skin receptor"""
    receptor_type: ReceptorType
    body_part: BodyPart
    density: float  # 受体密度 / Receptor density (0-1)
    sensitivity: float  # 敏感度 / Sensitivity (0-1)
    adaptation_rate: float  # 适应速度 / Adaptation rate (0-1)
    last_stimulus: Optional[datetime] = None
    current_activation: float = 0.0
    
    def __post_init__(self):
        if self.density < 0 or self.density > 1:
            raise ValueError("Density must be between 0 and 1")
        if self.sensitivity < 0 or self.sensitivity > 1:
            raise ValueError("Sensitivity must be between 0 and 1")


@dataclass
class TactileStimulus:
    """触觉刺激 / Tactile stimulus"""
    tactile_type: TactileType
    intensity: float  # 强度 (0-10)
    location: BodyPart
    receptor_types: List[ReceptorType] = field(default_factory=list)
    duration: float = 0.0  # 持续时间(秒)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    emotional_tag: Optional[str] = None
    
    def __post_init__(self):
        if not self.receptor_types:
            self.receptor_types = self._get_receptors_for_tactile()
    
    def _get_receptors_for_tactile(self) -> List[ReceptorType]:
        """根据触觉类型获取相关受体"""
        mapping = {
            TactileType.LIGHT_TOUCH: [ReceptorType.MEISSNER, ReceptorType.HAIR_FOLLICLE],
            TactileType.PRESSURE: [ReceptorType.MERKEL, ReceptorType.PACINIAN],
            TactileType.TEMPERATURE: [ReceptorType.FREE_NERVE],
            TactileType.VIBRATION: [ReceptorType.PACINIAN, ReceptorType.MEISSNER],
            TactileType.PAIN: [ReceptorType.FREE_NERVE],
            TactileType.ITCH: [ReceptorType.FREE_NERVE],
        }
        return mapping.get(self.tactile_type, [ReceptorType.FREE_NERVE])


@dataclass
class EmotionalTactileMapping:
    """情绪-触觉映射 / Emotion-tactile mapping"""
    emotion: str
    associated_tactile: List[TactileType]
    intensity_modifier: float
    preferred_locations: List[BodyPart]
    

class PhysiologicalTactileSystem:
    """
    生理触觉系统主类 / Main physiological tactile system class
    
    Simulates a comprehensive tactile system with 6 receptor types across 18 body parts.
    Implements dynamic sensitivity modulation based on arousal state and emotional context.
    
    Attributes:
        receptors: Dictionary mapping body parts to their receptor arrays
        arousal_level: Current arousal state (0-100)
        active_stimuli: Currently active tactile stimuli
        emotional_mappings: Mapping between emotions and tactile preferences
    
    Example:
        >>> system = PhysiologicalTactileSystem()
        >>> await system.initialize()
        >>> 
        >>> # Create a touch stimulus
        >>> stimulus = TactileStimulus(
        ...     tactile_type=TactileType.LIGHT_TOUCH,
        ...     intensity=5.0,
        ...     location=BodyPart.HANDS,
        ...     duration=2.0
        ... )
        >>> 
        >>> # Process the stimulus
        >>> response = await system.process_stimulus(stimulus)
        >>> print(f"Perceived intensity: {response.perceived_intensity}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.receptors: Dict[BodyPart, List[Receptor]] = {}
        self.arousal_level: float = 50.0  # 0-100
        self.active_stimuli: List[TactileStimulus] = []
        self.emotional_mappings: Dict[str, EmotionalTactileMapping] = {}
        self._stimulus_history: List[TactileStimulus] = []
        self._max_history_size = 1000
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Callbacks for various events
        self._on_stimulus_callbacks: List[Callable[[TactileStimulus], None]] = []
        self._on_threshold_callbacks: Dict[BodyPart, List[Callable[[float], None]]] = {}
        
        self._initialize_receptors()
        self._initialize_emotional_mappings()
    
    def _initialize_receptors(self):
        """初始化所有身体部位的受体"""
        receptor_configs = {
            ReceptorType.MEISSNER: {"density": 0.8, "adaptation": 0.9},
            ReceptorType.MERKEL: {"density": 0.6, "adaptation": 0.2},
            ReceptorType.PACINIAN: {"density": 0.4, "adaptation": 0.8},
            ReceptorType.RUFFINI: {"density": 0.3, "adaptation": 0.3},
            ReceptorType.FREE_NERVE: {"density": 1.0, "adaptation": 0.1},
            ReceptorType.HAIR_FOLLICLE: {"density": 0.7, "adaptation": 0.7},
        }
        
        # Define receptor distribution per body part
        distribution = {
            BodyPart.HANDS: [ReceptorType.MEISSNER, ReceptorType.MERKEL, 
                           ReceptorType.PACINIAN, ReceptorType.FREE_NERVE],
            BodyPart.FINGERS: [ReceptorType.MEISSNER, ReceptorType.MERKEL, 
                             ReceptorType.PACINIAN],
            BodyPart.FACE: [ReceptorType.MEISSNER, ReceptorType.FREE_NERVE,
                          ReceptorType.HAIR_FOLLICLE],
            BodyPart.FEET: [ReceptorType.MEISSNER, ReceptorType.PACINIAN,
                          ReceptorType.FREE_NERVE],
            BodyPart.FOREHEAD: [ReceptorType.MEISSNER, ReceptorType.FREE_NERVE],
            BodyPart.NECK: [ReceptorType.RUFFINI, ReceptorType.FREE_NERVE],
            BodyPart.FOREARMS: [ReceptorType.MEISSNER, ReceptorType.PACINIAN,
                              ReceptorType.RUFFINI],
            BodyPart.UPPER_ARMS: [ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.SHOULDERS: [ReceptorType.RUFFINI, ReceptorType.FREE_NERVE],
            BodyPart.CHEST: [ReceptorType.FREE_NERVE, ReceptorType.RUFFINI],
            BodyPart.BACK: [ReceptorType.FREE_NERVE, ReceptorType.RUFFINI],
            BodyPart.ABDOMEN: [ReceptorType.FREE_NERVE],
            BodyPart.WAIST: [ReceptorType.FREE_NERVE, ReceptorType.RUFFINI],
            BodyPart.HIPS: [ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.THIGHS: [ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.KNEES: [ReceptorType.FREE_NERVE, ReceptorType.PACINIAN],
            BodyPart.CALVES: [ReceptorType.PACINIAN, ReceptorType.FREE_NERVE],
            BodyPart.TOP_OF_HEAD: [ReceptorType.HAIR_FOLLICLE, ReceptorType.FREE_NERVE],
        }
        
        for body_part in BodyPart:
            self.receptors[body_part] = []
            receptor_types = distribution.get(body_part, [ReceptorType.FREE_NERVE])
            
            for r_type in receptor_types:
                config = receptor_configs[r_type]
                receptor = Receptor(
                    receptor_type=r_type,
                    body_part=body_part,
                    density=config["density"] * body_part.base_sensitivity,
                    sensitivity=body_part.base_sensitivity,
                    adaptation_rate=config["adaptation"]
                )
                self.receptors[body_part].append(receptor)
    
    def _initialize_emotional_mappings(self):
        """初始化情绪-触觉映射"""
        self.emotional_mappings = {
            "joy": EmotionalTactileMapping(
                emotion="joy",
                associated_tactile=[TactileType.LIGHT_TOUCH, TactileType.TEMPERATURE],
                intensity_modifier=1.2,
                preferred_locations=[BodyPart.HANDS, BodyPart.FACE]
            ),
            "comfort": EmotionalTactileMapping(
                emotion="comfort",
                associated_tactile=[TactileType.LIGHT_TOUCH, TactileType.PRESSURE],
                intensity_modifier=0.9,
                preferred_locations=[BodyPart.BACK, BodyPart.SHOULDERS, BodyPart.HANDS]
            ),
            "anxiety": EmotionalTactileMapping(
                emotion="anxiety",
                associated_tactile=[TactileType.TEMPERATURE, TactileType.PAIN],
                intensity_modifier=1.5,
                preferred_locations=[BodyPart.CHEST, BodyPart.ABDOMEN, BodyPart.HANDS]
            ),
            "relaxation": EmotionalTactileMapping(
                emotion="relaxation",
                associated_tactile=[TactileType.PRESSURE, TactileType.TEMPERATURE],
                intensity_modifier=0.7,
                preferred_locations=[BodyPart.BACK, BodyPart.SHOULDERS, BodyPart.NECK]
            ),
            "excitement": EmotionalTactileMapping(
                emotion="excitement",
                associated_tactile=[TactileType.VIBRATION, TactileType.LIGHT_TOUCH],
                intensity_modifier=1.3,
                preferred_locations=[BodyPart.HANDS, BodyPart.FACE, BodyPart.FOREARMS]
            ),
            "sadness": EmotionalTactileMapping(
                emotion="sadness",
                associated_tactile=[TactileType.TEMPERATURE, TactileType.PRESSURE],
                intensity_modifier=0.8,
                preferred_locations=[BodyPart.SHOULDERS, BodyPart.BACK]
            ),
            "anger": EmotionalTactileMapping(
                emotion="anger",
                associated_tactile=[TactileType.PAIN, TactileType.TEMPERATURE],
                intensity_modifier=1.4,
                preferred_locations=[BodyPart.HANDS, BodyPart.FACE, BodyPart.CHEST]
            ),
        }
    
    async def initialize(self):
        """Initialize the tactile system"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the tactile system"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop for receptor adaptation"""
        while self._running:
            await self._adapt_receptors()
            await self._decay_stimuli()
            await asyncio.sleep(0.1)  # 100ms update interval
    
    async def _adapt_receptors(self):
        """Adapt receptor sensitivity based on continuous stimulation"""
        for body_part, receptors in self.receptors.items():
            for receptor in receptors:
                if receptor.last_stimulus:
                    time_since = (datetime.now() - receptor.last_stimulus).total_seconds()
                    if time_since > 0:
                        # Adaptation formula: exponential decay
                        receptor.current_activation *= (
                            1 - receptor.adaptation_rate * 0.1
                        )
                        if receptor.current_activation < 0.01:
                            receptor.current_activation = 0.0
    
    async def _decay_stimuli(self):
        """Decay active stimuli over time"""
        current_time = datetime.now()
        remaining_stimuli = []
        
        for stimulus in self.active_stimuli:
            elapsed = (current_time - stimulus.timestamp).total_seconds()
            if elapsed < stimulus.duration:
                remaining_stimuli.append(stimulus)
        
        self.active_stimuli = remaining_stimuli
    
    def set_arousal_level(self, level: float):
        """
        Set the arousal level which affects tactile sensitivity
        
        Args:
            level: Arousal level from 0 (deeply relaxed) to 100 (highly aroused)
        """
        self.arousal_level = max(0.0, min(100.0, level))
        self._update_sensitivities()
    
    def _update_sensitivities(self):
        """Update receptor sensitivities based on arousal"""
        # Higher arousal = increased sensitivity for most receptors
        arousal_factor = 0.5 + (self.arousal_level / 100.0) * 1.0
        
        for body_part, receptors in self.receptors.items():
            for receptor in receptors:
                base = body_part.base_sensitivity
                # Pain receptors are more sensitive at high arousal
                if receptor.receptor_type == ReceptorType.FREE_NERVE:
                    receptor.sensitivity = base * arousal_factor * 1.2
                else:
                    receptor.sensitivity = base * arousal_factor
    
    async def process_stimulus(self, stimulus: TactileStimulus) -> 'TactileResponse':
        """
        Process a tactile stimulus and generate a response
        
        Args:
            stimulus: The tactile stimulus to process
            
        Returns:
            TactileResponse: The system's response to the stimulus
        """
        # Add to history
        self._stimulus_history.append(stimulus)
        if len(self._stimulus_history) > self._max_history_size:
            self._stimulus_history.pop(0)
        
        # Add to active stimuli
        self.active_stimuli.append(stimulus)
        
        # Calculate perceived intensity
        location_receptors = self.receptors.get(stimulus.location, [])
        relevant_receptors = [
            r for r in location_receptors 
            if r.receptor_type in stimulus.receptor_types
        ]
        
        if not relevant_receptors:
            relevant_receptors = location_receptors
        
        # Calculate activation
        total_activation = 0.0
        max_density = 0.0
        
        for receptor in relevant_receptors:
            activation = (
                stimulus.intensity * 
                receptor.sensitivity * 
                receptor.density
            )
            receptor.current_activation = max(
                receptor.current_activation, 
                activation
            )
            receptor.last_stimulus = datetime.now()
            total_activation += activation
            max_density += receptor.density
        
        # Normalize by receptor density
        if max_density > 0:
            perceived_intensity = total_activation / max_density
        else:
            perceived_intensity = stimulus.intensity
        
        # Apply emotional modulation
        if stimulus.emotional_tag and stimulus.emotional_tag in self.emotional_mappings:
            mapping = self.emotional_mappings[stimulus.emotional_tag]
            perceived_intensity *= mapping.intensity_modifier
        
        # Trigger callbacks
        for callback in self._on_stimulus_callbacks:
            try:
                callback(stimulus)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        # Check thresholds
        self._check_thresholds(stimulus.location, perceived_intensity)
        
        return TactileResponse(
            stimulus=stimulus,
            perceived_intensity=min(10.0, perceived_intensity),
            activated_receptors=len(relevant_receptors),
            duration=stimulus.duration,
            timestamp=datetime.now()
        )
    
    def _check_thresholds(self, body_part: BodyPart, intensity: float):
        """Check if any thresholds are exceeded"""
        if body_part in self._on_threshold_callbacks:
            for callback in self._on_threshold_callbacks[body_part]:
                try:
                    callback(intensity)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

    
    def register_stimulus_callback(self, callback: Callable[[TactileStimulus], None]):
        """Register a callback for stimulus events"""
        self._on_stimulus_callbacks.append(callback)
    
    def register_threshold_callback(
        self, 
        body_part: BodyPart, 
        callback: Callable[[float], None]
    ):
        """Register a callback for threshold events on a specific body part"""
        if body_part not in self._on_threshold_callbacks:
            self._on_threshold_callbacks[body_part] = []
        self._on_threshold_callbacks[body_part].append(callback)
    
    def get_body_part_sensitivity(self, body_part: BodyPart) -> float:
        """Get current sensitivity for a body part"""
        receptors = self.receptors.get(body_part, [])
        if not receptors:
            return 0.0
        return sum(r.sensitivity for r in receptors) / len(receptors)
    
    def get_active_stimuli_by_location(self, location: BodyPart) -> List[TactileStimulus]:
        """Get all active stimuli for a specific body part"""
        return [s for s in self.active_stimuli if s.location == location]
    
    def get_receptor_status(self, body_part: BodyPart) -> Dict[ReceptorType, float]:
        """Get current activation status of receptors for a body part"""
        receptors = self.receptors.get(body_part, [])
        return {r.receptor_type: r.current_activation for r in receptors}
    
    def apply_emotional_context(self, emotion: str, intensity: float = 1.0):
        """
        Apply emotional context to tactile processing
        
        Args:
            emotion: Emotion name
            intensity: Emotional intensity (0-1)
        """
        if emotion in self.emotional_mappings:
            mapping = self.emotional_mappings[emotion]
            # Temporarily increase sensitivity for preferred locations
            for location in mapping.preferred_locations:
                for receptor in self.receptors.get(location, []):
                    receptor.sensitivity *= (1 + 0.3 * intensity)
    
    # Live2D Integration Methods
    def get_live2d_response_for_touch(
        self,
        body_part: BodyPart,
        touch_type: str = "pat",
        intensity: float = 0.5
    ) -> Dict[str, float]:
        """
        Get Live2D parameter response for a body touch
        
        Args:
            body_part: Body part being touched
            touch_type: Type of touch (pat, stroke, poke, pinch, etc.)
            intensity: Touch intensity (0-1)
            
        Returns:
            Dictionary of Live2D parameter names to values
        """
        body_part_key = body_part.name.lower()
        
        # Map BodyPart enum names to mapping keys
        mapping_key = self._get_body_part_mapping_key(body_part)
        
        if mapping_key not in BODY_TO_LIVE2D_MAPPING:
            return {}
        
        part_mapping = BODY_TO_LIVE2D_MAPPING[mapping_key]
        
        # Get touch response (default to "pat" if touch type not found)
        touch_mapping = part_mapping.get(touch_type, part_mapping.get("pat", {}))
        
        # Calculate parameter values based on intensity
        live2d_params = {}
        for param_name, (min_val, max_val) in touch_mapping.items():
            # Interpolate based on intensity
            value = min_val + (max_val - min_val) * intensity
            
            # Apply body part sensitivity
            sensitivity = body_part.base_sensitivity
            value = value * sensitivity
            
            live2d_params[param_name] = value
        
        return live2d_params
    
    def _get_body_part_mapping_key(self, body_part: BodyPart) -> str:
        """Map BodyPart enum to BODY_TO_LIVE2D_MAPPING keys"""
        mapping = {
            BodyPart.TOP_OF_HEAD: "top_of_head",
            BodyPart.FOREHEAD: "forehead",
            BodyPart.FACE: "face",
            BodyPart.NECK: "neck",
            BodyPart.CHEST: "chest",
            BodyPart.BACK: "back",
            BodyPart.ABDOMEN: "abdomen",
            BodyPart.WAIST: "waist",
            BodyPart.HIPS: "hips",
            BodyPart.THIGHS: "thighs",
            BodyPart.SHOULDERS: "shoulders",
            BodyPart.UPPER_ARMS: "upper_arms",
            BodyPart.FOREARMS: "forearms",
            BodyPart.HANDS: "hands",
            BodyPart.FINGERS: "fingers",
            BodyPart.KNEES: "knees",
            BodyPart.CALVES: "calves",
            BodyPart.FEET: "feet",
        }
        return mapping.get(body_part, body_part.name.lower())
    
    async def process_stimulus_with_live2d(
        self,
        stimulus: TactileStimulus,
        touch_type: str = "pat"
    ) -> TactileResponse:
        """
        Process tactile stimulus and return response with Live2D parameters
        
        Args:
            stimulus: Tactile stimulus
            touch_type: Type of touch interaction
            
        Returns:
            TactileResponse with live2d_parameters
        """
        # Process normally first
        response = await self.process_stimulus(stimulus)
        
        # Add Live2D parameters
        intensity = stimulus.intensity / 10.0  # Normalize to 0-1
        live2d_params = self.get_live2d_response_for_touch(
            stimulus.location,
            touch_type,
            intensity
        )
        
        # Add emotional modifiers
        if stimulus.emotional_tag:
            live2d_params = self._apply_emotional_to_live2d(
                live2d_params,
                stimulus.emotional_tag,
                intensity
            )
        
        response.live2d_parameters = live2d_params
        
        return response
    
    def _apply_emotional_to_live2d(
        self,
        params: Dict[str, float],
        emotion: str,
        intensity: float
    ) -> Dict[str, float]:
        """Apply emotional context to Live2D parameters"""
        modified = params.copy()
        
        # Emotion-specific parameter adjustments
        emotion_modifiers = {
            "joy": {"ParamCheek": 0.3, "ParamEyeLSmile": 0.5, "ParamEyeRSmile": 0.5},
            "comfort": {"ParamEyeLOpen": -0.1, "ParamEyeROpen": -0.1, "ParamCheek": 0.2},
            "anxiety": {"ParamBrowLY": 0.3, "ParamBrowRY": 0.3, "ParamEyeLOpen": 0.2},
            "relaxation": {"ParamEyeLOpen": -0.2, "ParamEyeROpen": -0.2, "ParamBreath": 0.3},
            "excitement": {"ParamEyeLOpen": 0.2, "ParamEyeROpen": 0.2, "ParamCheek": 0.4},
            "sadness": {"ParamBrowLY": -0.3, "ParamBrowRY": -0.3, "ParamMouthForm": -0.3},
            "anger": {"ParamBrowLAngle": 0.5, "ParamBrowRAngle": 0.5, "ParamEyeLOpen": 0.1},
            "love": {"ParamCheek": 0.6, "ParamEyeLSmile": 0.6, "ParamEyeRSmile": 0.6},
        }
        
        if emotion in emotion_modifiers:
            for param, modifier in emotion_modifiers[emotion].items():
                if param in modified:
                    modified[param] = max(-1.0, min(1.0, modified[param] + modifier * intensity))
                else:
                    modified[param] = modifier * intensity
        
        return modified
    
    def get_all_body_live2d_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get all body part to Live2D mappings"""
        return BODY_TO_LIVE2D_MAPPING.copy()
    
    def get_live2d_touch_zones(self) -> List[Dict[str, Any]]:
        """
        Get touch zone definitions for Live2D integration
        
        Returns:
            List of touch zone definitions with body parts and parameters
        """
        zones = []
        
        for body_part in BodyPart:
            mapping_key = self._get_body_part_mapping_key(body_part)
            
            if mapping_key in BODY_TO_LIVE2D_MAPPING:
                part_mapping = BODY_TO_LIVE2D_MAPPING[mapping_key]
                
                # Collect all parameters for this body part
                all_params = set()
                for touch_type, params in part_mapping.items():
                    all_params.update(params.keys())
                
                zones.append({
                    "body_part": body_part.name,
                    "cn_name": body_part.cn_name,
                    "sensitivity": body_part.base_sensitivity,
                    "touch_types": list(part_mapping.keys()),
                    "parameters": list(all_params),
                    "region": body_part.region.name
                })
        
        return zones


@dataclass
class TactileResponse:
    """触觉响应 / Tactile response"""
    stimulus: TactileStimulus
    perceived_intensity: float
    activated_receptors: int
    duration: float
    timestamp: datetime
    live2d_parameters: Dict[str, float] = field(default_factory=dict)  # Added for Live2D integration
    
    def __repr__(self) -> str:
        return (
            f"TactileResponse({self.stimulus.tactile_type.name} at "
            f"{self.stimulus.location.cn_name}, intensity={self.perceived_intensity:.2f})"
        )


# Live2D Integration Mapping
# Maps 18 body parts to Live2D parameter changes
BODY_TO_LIVE2D_MAPPING = {
    "top_of_head": {
        "pat": {"ParamAngleX": (-15, 15), "ParamAngleY": (-10, 10), "ParamHairSwing": (0, 0.8)},
        "stroke": {"ParamHairSwing": (0, 0.5), "ParamHairFront": (-0.3, 0.3)},
        "rub": {"ParamAngleX": (-8, 8), "ParamHairSwing": (0, 0.3)},
    },
    "forehead": {
        "pat": {"ParamBrowLY": (-0.5, 0.5), "ParamBrowRY": (-0.5, 0.5)},
        "stroke": {"ParamAngleY": (-5, 5)},
        "poke": {"ParamBrowLY": (0.3, 0.8), "ParamBrowRY": (0.3, 0.8)},
    },
    "face": {
        "pat": {"ParamCheek": (0.2, 0.8), "ParamFaceColor": (0.1, 0.5), "ParamEyeScale": (1, 1.2)},
        "stroke": {"ParamCheek": (0.1, 0.4), "ParamFaceColor": (0.05, 0.2)},
        "poke": {"ParamEyeLOpen": (0.5, 0.8), "ParamEyeROpen": (0.5, 0.8), "ParamCheek": (0.3, 0.6)},
        "pinch": {"ParamMouthForm": (-0.6, 0.6), "ParamCheek": (0.5, 0.9)},
    },
    "neck": {
        "pat": {"ParamAngleY": (5, 15)},
        "stroke": {"ParamAngleX": (-10, 10), "ParamBodyAngleY": (-3, 3)},
    },
    "chest": {
        "pat": {"ParamBodyAngleX": (-8, 8), "ParamBreath": (0.1, 0.4)},
        "press": {"ParamBreath": (0.2, 0.6)},
    },
    "back": {
        "pat": {"ParamBodyAngleX": (-12, 12)},
        "stroke": {"ParamBodyAngleZ": (-5, 5)},
    },
    "abdomen": {
        "pat": {"ParamBodyAngleY": (5, 10)},
        "press": {"ParamBreath": (0.2, 0.5)},
        "tickle": {"ParamBodyAngleY": (-8, 8), "ParamBreath": (0.3, 0.8)},
    },
    "waist": {
        "pat": {"ParamBodyAngleX": (-10, 10)},
        "stroke": {"ParamBodyAngleZ": (-6, 6)},
    },
    "hips": {
        "pat": {"ParamBodyAngleX": (-12, 12), "ParamBodyAngleZ": (-8, 8)},
    },
    "thighs": {
        "pat": {"ParamBodyAngleY": (-3, 3)},
        "stroke": {"ParamBodyAngleY": (-2, 2)},
    },
    "shoulders": {
        "pat": {"ParamBodyAngleZ": (-8, 8)},
        "massage": {"ParamArmLA": (-0.4, 0.4), "ParamArmRA": (-0.4, 0.4)},
    },
    "upper_arms": {
        "pat": {"ParamArmLA": (-0.6, 0.6), "ParamArmRA": (-0.6, 0.6)},
        "stroke": {"ParamArmLA": (-0.3, 0.3), "ParamArmRA": (-0.3, 0.3)},
    },
    "forearms": {
        "pat": {"ParamArmLA": (-0.7, 0.7), "ParamArmRA": (-0.7, 0.7)},
        "stroke": {"ParamHandL": (-0.3, 0.3), "ParamHandR": (-0.3, 0.3)},
    },
    "hands": {
        "pat": {"ParamHandL": (-1.0, 1.0), "ParamHandR": (-1.0, 1.0)},
        "hold": {"ParamHandL": (0.4, 0.8), "ParamHandR": (0.4, 0.8)},
        "stroke": {"ParamHandL": (-0.4, 0.4), "ParamHandR": (-0.4, 0.4)},
    },
    "fingers": {
        "pat": {"ParamHandL": (-0.6, 0.6), "ParamHandR": (-0.6, 0.6)},
        "stroke": {"ParamHandL": (-0.3, 0.3), "ParamHandR": (-0.3, 0.3)},
    },
    "knees": {
        "pat": {"ParamBodyAngleY": (-3, 3)},
    },
    "calves": {
        "pat": {"ParamBodyAngleY": (-2, 2)},
        "stroke": {"ParamBodyAngleY": (-1, 1)},
    },
    "feet": {
        "pat": {"ParamBodyAngleY": (-2, 2)},
        "tickle": {"ParamBodyAngleY": (-4, 4)},
    },
}


@dataclass
class Live2DTouchResponse:
    """Live2D触摸响应 / Live2D touch response"""
    body_part: str
    touch_type: str
    intensity: float
    parameters: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrajectoryPoint:
    """轨迹点 / Trajectory point"""
    x: float
    y: float
    timestamp: datetime = field(default_factory=datetime.now)
    pressure: float = 0.0  # 压力值 (0-1)


@dataclass
class TrajectoryAnalysis:
    """轨迹分析结果 / Trajectory analysis result"""
    velocity: float  # 速度 (px/s)
    acceleration: float  # 加速度 (px/s²)
    curvature: float  # 曲率
    movement_pattern: str  # 运动模式
    pattern_confidence: float  # 模式置信度 (0-1)
    total_distance: float  # 总距离 (px)
    duration: float  # 持续时间 (s)


class TrajectoryAnalyzer:
    """
    轨迹分析器 / Trajectory Analyzer
    
    Analyzes touch trajectory data to compute velocity, acceleration, 
    curvature, and classify movement patterns.
    
    Features:
    - Velocity calculation (px/s)
    - Acceleration calculation (px/s²)
    - 7 movement pattern recognition (line, curve, fast, slow, jitter, slide, still)
    - Curvature analysis
    
    Example:
        >>> analyzer = TrajectoryAnalyzer()
        >>> 
        >>> # Add trajectory points
        >>> analyzer.add_point(0, 0)
        >>> analyzer.add_point(10, 5)
        >>> analyzer.add_point(25, 12)
        >>> 
        >>> # Analyze trajectory
        >>> analysis = analyzer.analyze()
        >>> print(f"Velocity: {analysis.velocity:.2f} px/s")
        >>> print(f"Pattern: {analysis.movement_pattern}")
    """
    
    # 运动模式定义 / Movement pattern definitions
    MOVEMENT_PATTERNS = {
        "line": {"cn": "直线", "velocity_var": 0.1, "curvature_max": 0.05},
        "curve": {"cn": "曲线", "velocity_var": 0.2, "curvature_min": 0.05},
        "fast": {"cn": "快速", "velocity_min": 300.0},
        "slow": {"cn": "慢速", "velocity_max": 50.0},
        "jitter": {"cn": "抖动", "accel_var": 5000.0, "direction_changes": 3},
        "slide": {"cn": "滑动", "velocity_stable": 0.15, "duration_min": 0.5},
        "still": {"cn": "静止", "velocity_max": 5.0, "duration_min": 1.0},
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize trajectory analyzer
        
        Args:
            config: Configuration dictionary with optional parameters
        """
        self.config = config or {}
        self.points: List[TrajectoryPoint] = []
        self.max_points: int = self.config.get("max_points", 1000)
        self.min_points_for_analysis: int = self.config.get("min_points", 3)
        
        # Analysis cache
        self._last_analysis: Optional[TrajectoryAnalysis] = None
        self._analysis_timestamp: Optional[datetime] = None
    
    def add_point(self, x: float, y: float, pressure: float = 0.0) -> None:
        """
        Add a trajectory point
        
        Args:
            x: X coordinate
            y: Y coordinate
            pressure: Pressure value (0-1)
        """
        point = TrajectoryPoint(x=x, y=y, pressure=pressure)
        self.points.append(point)
        
        # Maintain maximum size
        if len(self.points) > self.max_points:
            self.points.pop(0)
    
    def add_points(self, points: List[Tuple[float, float, float]]) -> None:
        """
        Add multiple trajectory points at once
        
        Args:
            points: List of (x, y, pressure) tuples
        """
        for x, y, pressure in points:
            self.add_point(x, y, pressure)
    
    def clear(self) -> None:
        """Clear all trajectory points"""
        self.points.clear()
        self._last_analysis = None
        self._analysis_timestamp = None
    
    def analyze(self) -> TrajectoryAnalysis:
        """
        Analyze the complete trajectory and return analysis results
        
        Returns:
            TrajectoryAnalysis object containing computed metrics
        """
        if len(self.points) < self.min_points_for_analysis:
            return TrajectoryAnalysis(
                velocity=0.0,
                acceleration=0.0,
                curvature=0.0,
                movement_pattern="insufficient_data",
                pattern_confidence=0.0,
                total_distance=0.0,
                duration=0.0
            )
        
        # Calculate basic metrics
        velocities = self._calculate_velocities()
        accelerations = self._calculate_accelerations()
        
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0.0
        avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0.0
        
        # Calculate curvature
        curvature = self._calculate_curvature()
        
        # Calculate total distance and duration
        total_distance = self._calculate_total_distance()
        duration = self._calculate_duration()
        
        # Classify movement pattern
        pattern, confidence = self._classify_pattern(
            velocities, accelerations, curvature, duration
        )
        
        analysis = TrajectoryAnalysis(
            velocity=avg_velocity,
            acceleration=avg_acceleration,
            curvature=curvature,
            movement_pattern=pattern,
            pattern_confidence=confidence,
            total_distance=total_distance,
            duration=duration
        )
        
        self._last_analysis = analysis
        self._analysis_timestamp = datetime.now()
        
        return analysis
    
    def _calculate_velocities(self) -> List[float]:
        """计算每段速度 / Calculate velocities between consecutive points"""
        velocities = []
        
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            
            # Distance
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            # Time
            dt = (p2.timestamp - p1.timestamp).total_seconds()
            if dt > 0:
                velocity = distance / dt
                velocities.append(velocity)
        
        return velocities
    
    def _calculate_accelerations(self) -> List[float]:
        """计算加速度 / Calculate accelerations"""
        velocities = self._calculate_velocities()
        accelerations = []
        
        for i in range(1, len(velocities)):
            dv = velocities[i] - velocities[i - 1]
            dt = (self.points[i + 1].timestamp - self.points[i].timestamp).total_seconds()
            if dt > 0:
                acceleration = dv / dt
                accelerations.append(acceleration)
        
        return accelerations
    
    def _calculate_curvature(self) -> float:
        """计算平均曲率 / Calculate average curvature"""
        if len(self.points) < 3:
            return 0.0
        
        curvatures = []
        
        for i in range(1, len(self.points) - 1):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            p3 = self.points[i + 1]
            
            # Calculate curvature using three points
            curvature = self._compute_curvature_three_points(p1, p2, p3)
            curvatures.append(curvature)
        
        return sum(curvatures) / len(curvatures) if curvatures else 0.0
    
    def _compute_curvature_three_points(
        self, p1: TrajectoryPoint, p2: TrajectoryPoint, p3: TrajectoryPoint
    ) -> float:
        """计算三点曲率 / Compute curvature from three points"""
        # Vector from p1 to p2
        v1x = p2.x - p1.x
        v1y = p2.y - p1.y
        
        # Vector from p2 to p3
        v2x = p3.x - p2.x
        v2y = p3.y - p2.y
        
        # Cross product magnitude (area of parallelogram)
        cross = abs(v1x * v2y - v1y * v2x)
        
        # Product of magnitudes
        mag1 = math.sqrt(v1x ** 2 + v1y ** 2)
        mag2 = math.sqrt(v2x ** 2 + v2y ** 2)
        
        if mag1 * mag2 == 0:
            return 0.0
        
        # Curvature = 2 * area / (|v1| * |v2| * |v1 + v2|)
        # Simplified: use cross product
        curvature = cross / (mag1 * mag2)
        
        return curvature
    
    def _calculate_total_distance(self) -> float:
        """计算总距离 / Calculate total trajectory distance"""
        total = 0.0
        
        for i in range(1, len(self.points)):
            dx = self.points[i].x - self.points[i - 1].x
            dy = self.points[i].y - self.points[i - 1].y
            total += math.sqrt(dx ** 2 + dy ** 2)
        
        return total
    
    def _calculate_duration(self) -> float:
        """计算持续时间 / Calculate total duration"""
        if len(self.points) < 2:
            return 0.0
        
        return (self.points[-1].timestamp - self.points[0].timestamp).total_seconds()
    
    def _classify_pattern(
        self,
        velocities: List[float],
        accelerations: List[float],
        curvature: float,
        duration: float
    ) -> Tuple[str, float]:
        """
        分类运动模式 / Classify movement pattern
        
        Returns:
            Tuple of (pattern_name, confidence)
        """
        if not velocities:
            return "insufficient_data", 0.0
        
        avg_velocity = sum(velocities) / len(velocities)
        max_velocity = max(velocities)
        min_velocity = min(velocities)
        velocity_variance = self._calculate_variance(velocities)
        
        avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0.0
        accel_variance = self._calculate_variance(accelerations) if accelerations else 0.0
        
        # Count direction changes (for jitter detection)
        direction_changes = self._count_direction_changes()
        
        # Pattern scoring
        scores = {}
        
        # Still pattern
        if avg_velocity < 5.0 and duration > 0.5:
            scores["still"] = 1.0 - (avg_velocity / 5.0)
        
        # Fast pattern
        if avg_velocity > 300.0:
            scores["fast"] = min(1.0, avg_velocity / 500.0)
        
        # Slow pattern
        if avg_velocity < 50.0 and duration > 0.3:
            scores["slow"] = 1.0 - (avg_velocity / 50.0)
        
        # Jitter pattern
        if direction_changes >= 3 or accel_variance > 5000.0:
            jitter_score = min(1.0, direction_changes / 5.0)
            jitter_score = max(jitter_score, min(1.0, accel_variance / 10000.0))
            scores["jitter"] = jitter_score
        
        # Slide pattern
        if velocity_variance < 0.15 and duration > 0.5 and avg_velocity > 20.0:
            scores["slide"] = 1.0 - velocity_variance / 0.15
        
        # Line pattern
        if curvature < 0.05 and velocity_variance < 0.2:
            scores["line"] = 1.0 - curvature / 0.05
        
        # Curve pattern
        if curvature > 0.05:
            scores["curve"] = min(1.0, curvature / 0.2)
        
        # Select best pattern
        if not scores:
            return "unclassified", 0.0
        
        best_pattern = max(scores.items(), key=lambda x: x[1])[0]
        return best_pattern, scores[best_pattern]
    
    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差 / Calculate variance"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        squared_diffs = [(x - mean) ** 2 for x in values]
        return sum(squared_diffs) / len(squared_diffs)
    
    def _count_direction_changes(self) -> int:
        """统计方向变化次数 / Count direction changes"""
        if len(self.points) < 3:
            return 0
        
        changes = 0
        
        for i in range(2, len(self.points)):
            # Vectors
            v1x = self.points[i - 1].x - self.points[i - 2].x
            v1y = self.points[i - 1].y - self.points[i - 2].y
            v2x = self.points[i].x - self.points[i - 1].x
            v2y = self.points[i].y - self.points[i - 1].y
            
            # Dot product
            dot = v1x * v2x + v1y * v2y
            
            # If dot product is negative, direction changed significantly
            mag1 = math.sqrt(v1x ** 2 + v1y ** 2)
            mag2 = math.sqrt(v2x ** 2 + v2y ** 2)
            
            if mag1 > 0 and mag2 > 0:
                cos_angle = dot / (mag1 * mag2)
                # Significant direction change (angle > 90 degrees)
                if cos_angle < 0:
                    changes += 1
        
        return changes
    
    def get_realtime_metrics(self) -> Dict[str, float]:
        """
        获取实时指标 / Get real-time trajectory metrics
        
        Returns:
            Dictionary with current velocity, acceleration, etc.
        """
        if len(self.points) < 2:
            return {"velocity": 0.0, "acceleration": 0.0, "curvature": 0.0}
        
        # Use last few points for real-time metrics
        recent_points = self.points[-10:] if len(self.points) >= 10 else self.points
        
        # Calculate velocity from last segment
        p1 = recent_points[-2]
        p2 = recent_points[-1]
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dt = (p2.timestamp - p1.timestamp).total_seconds()
        
        velocity = math.sqrt(dx ** 2 + dy ** 2) / dt if dt > 0 else 0.0
        
        # Calculate acceleration if possible
        acceleration = 0.0
        if len(recent_points) >= 3:
            p0 = recent_points[-3]
            dt1 = (p1.timestamp - p0.timestamp).total_seconds()
            dt2 = dt
            
            if dt1 > 0 and dt2 > 0:
                v1 = math.sqrt(
                    (p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2
                ) / dt1
                v2 = velocity
                acceleration = (v2 - v1) / ((dt1 + dt2) / 2)
        
        return {
            "velocity": velocity,
            "acceleration": acceleration,
            "curvature": self._calculate_curvature(),
        }


@dataclass
class ReceptorAdaptationState:
    """受体适应状态 / Receptor adaptation state"""
    receptor_id: str
    base_sensitivity: float
    current_sensitivity: float
    habituation_level: float  # 习惯化水平 (0-1)
    last_stimulus_type: Optional[str] = None
    stimulus_count: int = 0
    last_adaptation_time: datetime = field(default_factory=datetime.now)


class AdaptationMechanism:
    """
    适应机制 / Adaptation Mechanism
    
    Implements dynamic receptor sensitivity adjustment, habituation (reduced 
    sensitivity to repeated stimuli), dishabituation (recovery to new stimuli),
    and adaptation speed control.
    
    Features:
    - Dynamic receptor sensitivity adjustment
    - Habituation (reduced sensitivity to repeated stimuli)
    - Dishabituation (recovery when new stimulus detected)
    - Adaptation speed control
    
    Example:
        >>> mechanism = AdaptationMechanism()
        >>> 
        >>> # Register a receptor
        >>> mechanism.register_receptor("hand_meissner", base_sensitivity=0.8)
        >>> 
        >>> # Process repeated stimulus (habituation)
        >>> for _ in range(10):
        ...     state = mechanism.process_stimulus("hand_meissner", "touch")
        ...     print(f"Sensitivity: {state.current_sensitivity:.3f}")
        
        >>> # New stimulus triggers dishabituation
        >>> state = mechanism.process_stimulus("hand_meissner", "vibration")
        >>> print(f"Recovered sensitivity: {state.current_sensitivity:.3f}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adaptation mechanism
        
        Args:
            config: Configuration dictionary with optional parameters
        """
        self.config = config or {}
        
        # Adaptation parameters
        self.habituation_rate: float = self.config.get("habituation_rate", 0.05)
        self.dishabituation_boost: float = self.config.get("dishabituation_boost", 0.3)
        self.recovery_rate: float = self.config.get("recovery_rate", 0.02)
        self.min_sensitivity: float = self.config.get("min_sensitivity", 0.1)
        self.max_sensitivity: float = self.config.get("max_sensitivity", 1.0)
        
        # Receptor states
        self.receptor_states: Dict[str, ReceptorAdaptationState] = {}
        
        # Stimulus history for pattern detection
        self.stimulus_history: Dict[str, List[Tuple[str, datetime]]] = {}
        self.max_history: int = self.config.get("max_history", 50)
    
    def register_receptor(
        self,
        receptor_id: str,
        base_sensitivity: float = 0.5,
        initial_habituation: float = 0.0
    ) -> ReceptorAdaptationState:
        """
        注册受体 / Register a receptor for adaptation tracking
        
        Args:
            receptor_id: Unique receptor identifier
            base_sensitivity: Base sensitivity level (0-1)
            initial_habituation: Initial habituation level (0-1)
            
        Returns:
            ReceptorAdaptationState object
        """
        state = ReceptorAdaptationState(
            receptor_id=receptor_id,
            base_sensitivity=base_sensitivity,
            current_sensitivity=base_sensitivity * (1 - initial_habituation),
            habituation_level=initial_habituation,
        )
        
        self.receptor_states[receptor_id] = state
        self.stimulus_history[receptor_id] = []
        
        return state
    
    def process_stimulus(
        self,
        receptor_id: str,
        stimulus_type: str,
        intensity: float = 1.0
    ) -> ReceptorAdaptationState:
        """
        处理刺激并更新适应状态 / Process stimulus and update adaptation state
        
        Args:
            receptor_id: Receptor identifier
            stimulus_type: Type of stimulus
            intensity: Stimulus intensity (0-1)
            
        Returns:
            Updated ReceptorAdaptationState
        """
        # Ensure receptor is registered
        if receptor_id not in self.receptor_states:
            self.register_receptor(receptor_id)
        
        state = self.receptor_states[receptor_id]
        
        # Update history
        self._update_stimulus_history(receptor_id, stimulus_type)
        
        # Check for stimulus change (dishabituation trigger)
        if (state.last_stimulus_type is not None and 
            state.last_stimulus_type != stimulus_type):
            # Dishabituation - new stimulus type detected
            self._apply_dishabituation(state, intensity)
        else:
            # Habituation - repeated stimulus
            self._apply_habituation(state, stimulus_type, intensity)
        
        # Update metadata
        state.last_stimulus_type = stimulus_type
        state.stimulus_count += 1
        state.last_adaptation_time = datetime.now()
        
        return state
    
    def _update_stimulus_history(self, receptor_id: str, stimulus_type: str) -> None:
        """更新刺激历史 / Update stimulus history"""
        if receptor_id not in self.stimulus_history:
            self.stimulus_history[receptor_id] = []
        
        history = self.stimulus_history[receptor_id]
        history.append((stimulus_type, datetime.now()))
        
        # Maintain maximum size
        if len(history) > self.max_history:
            history.pop(0)
    
    def _apply_habituation(
        self,
        state: ReceptorAdaptationState,
        stimulus_type: str,
        intensity: float
    ) -> None:
        """
        应用习惯化 / Apply habituation (sensitivity reduction)
        
        Repeated stimuli reduce receptor sensitivity.
        """
        # Count recent repetitions
        history = self.stimulus_history.get(state.receptor_id, [])
        recent_repetitions = self._count_recent_repetitions(history, stimulus_type)
        
        # Calculate habituation amount based on repetition count
        # More repetitions = stronger habituation, but with diminishing returns
        habituation_factor = 1 - math.exp(-recent_repetitions * self.habituation_rate)
        
        # Apply habituation
        state.habituation_level = min(1.0, habituation_factor)
        
        # Calculate new sensitivity
        target_sensitivity = state.base_sensitivity * (1 - state.habituation_level)
        
        # Gradual adaptation (don't change too quickly)
        state.current_sensitivity = (
            state.current_sensitivity * 0.7 + target_sensitivity * 0.3
        )
        
        # Ensure bounds
        state.current_sensitivity = max(
            self.min_sensitivity,
            min(self.max_sensitivity, state.current_sensitivity)
        )
    
    def _apply_dishabituation(
        self,
        state: ReceptorAdaptationState,
        intensity: float
    ) -> None:
        """
        应用去习惯化 / Apply dishabituation (sensitivity recovery)
        
        New stimuli trigger sensitivity recovery.
        """
        # Calculate recovery amount based on stimulus intensity
        recovery = self.dishabituation_boost * intensity
        
        # Reduce habituation level
        state.habituation_level = max(0.0, state.habituation_level - recovery)
        
        # Boost sensitivity
        target_sensitivity = state.base_sensitivity * (1 - state.habituation_level)
        boosted_sensitivity = target_sensitivity * (1 + recovery * 0.5)
        
        # Apply with some immediate effect and some gradual
        state.current_sensitivity = min(
            self.max_sensitivity,
            max(target_sensitivity, boosted_sensitivity)
        )
    
    def _count_recent_repetitions(
        self,
        history: List[Tuple[str, datetime]],
        stimulus_type: str,
        window_seconds: float = 30.0
    ) -> int:
        """统计近期重复次数 / Count recent repetitions of a stimulus type"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        return sum(
            1 for st, ts in history
            if st == stimulus_type and ts > cutoff
        )
    
    async def update(self, delta_time: float = 1.0) -> None:
        """
        更新适应状态（恢复） / Update adaptation states (recovery)
        
        Gradually recovers sensitivity when no stimuli present.
        
        Args:
            delta_time: Time since last update (seconds)
        """
        for state in self.receptor_states.values():
            # Calculate time since last stimulus
            time_since = (datetime.now() - state.last_adaptation_time).total_seconds()
            
            # Gradual recovery if no recent stimuli
            if time_since > 5.0:  # 5 seconds without stimulus
                # Gradually reduce habituation
                recovery_amount = self.recovery_rate * delta_time
                state.habituation_level = max(0.0, state.habituation_level - recovery_amount)
                
                # Gradually restore sensitivity toward base
                target = state.base_sensitivity * (1 - state.habituation_level)
                state.current_sensitivity = (
                    state.current_sensitivity * 0.95 + target * 0.05
                )
    
    def get_adaptation_state(self, receptor_id: str) -> Optional[ReceptorAdaptationState]:
        """获取受体适应状态 / Get adaptation state for a receptor"""
        return self.receptor_states.get(receptor_id)
    
    def get_all_states(self) -> Dict[str, ReceptorAdaptationState]:
        """获取所有受体状态 / Get all receptor states"""
        return self.receptor_states.copy()
    
    def reset_receptor(self, receptor_id: str) -> None:
        """重置受体到初始状态 / Reset receptor to initial state"""
        if receptor_id in self.receptor_states:
            state = self.receptor_states[receptor_id]
            state.current_sensitivity = state.base_sensitivity
            state.habituation_level = 0.0
            state.stimulus_count = 0
            state.last_stimulus_type = None
            self.stimulus_history[receptor_id] = []
    
    def set_adaptation_speed(
        self,
        habituation_rate: Optional[float] = None,
        recovery_rate: Optional[float] = None
    ) -> None:
        """
        设置适应速度 / Set adaptation speed parameters
        
        Args:
            habituation_rate: New habituation rate (optional)
            recovery_rate: New recovery rate (optional)
        """
        if habituation_rate is not None:
            self.habituation_rate = habituation_rate
        if recovery_rate is not None:
            self.recovery_rate = recovery_rate


# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize the system
        system = PhysiologicalTactileSystem()
        await system.initialize()
        
        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 生理触觉系统演示")
        logger.info("Physiological Tactile System Demo")
        logger.info("=" * 60)
        
        # Simulate different tactile sensations
        stimuli = [
            TactileStimulus(
                tactile_type=TactileType.LIGHT_TOUCH,
                intensity=3.0,
                location=BodyPart.HANDS,
                duration=2.0,
                source="user_interaction",
                emotional_tag="comfort"
            ),
            TactileStimulus(
                tactile_type=TactileType.PRESSURE,
                intensity=5.0,
                location=BodyPart.SHOULDERS,
                duration=5.0,
                source="massage",
                emotional_tag="relaxation"
            ),
            TactileStimulus(
                tactile_type=TactileType.TEMPERATURE,
                intensity=7.0,
                location=BodyPart.FACE,
                duration=1.0,
                source="environment",
                emotional_tag="anxiety"
            ),
        ]
        
        logger.info("\n处理触觉刺激 / Processing tactile stimuli:\n")
        for i, stimulus in enumerate(stimuli, 1):
            logger.info(f"{i}. {stimulus.tactile_type.name} on {stimulus.location.cn_name}")
            response = await system.process_stimulus(stimulus)
            logger.info(f"   感知强度: {response.perceived_intensity:.2f}")
            logger.info(f"   激活受体数: {response.activated_receptors}")
            logger.info()
        
        # Show receptor status
        logger.info("手掌受体状态 / Hand receptor status:")
        status = system.get_receptor_status(BodyPart.HANDS)
        for receptor_type, activation in status.items():
            logger.info(f"  - {receptor_type.name}: {activation:.3f}")
        
        # Change arousal and show effect
        logger.info("\n改变唤醒水平 / Changing arousal level to 80...")
        system.set_arousal_level(80)
        logger.info(f"手部敏感度: {system.get_body_part_sensitivity(BodyPart.HANDS):.3f}")
        
        await system.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")
        
        # Trajectory Analyzer Demo
        logger.info("\n" + "=" * 60)
        logger.info("轨迹分析器演示 / Trajectory Analyzer Demo")
        logger.info("=" * 60)
        
        analyzer = TrajectoryAnalyzer()
        
        # Simulate a curved trajectory
        logger.info("\n1. 模拟曲线轨迹 / Simulating curved trajectory:")
        import math
        for i in range(20):
            angle = i * 0.3
            x = math.cos(angle) * 50 + 100
            y = math.sin(angle) * 30 + 100
            analyzer.add_point(x, y, pressure=0.5 + i * 0.02)
        
        analysis = analyzer.analyze()
        logger.info(f"   运动模式: {analysis.movement_pattern} ({analyzer.MOVEMENT_PATTERNS[analysis.movement_pattern]['cn']})")
        logger.info(f"   平均速度: {analysis.velocity:.2f} px/s")
        logger.info(f"   曲率: {analysis.curvature:.4f}")
        logger.info(f"   置信度: {analysis.pattern_confidence:.2%}")
        
        # Simulate a straight line
        logger.info("\n2. 模拟直线轨迹 / Simulating straight trajectory:")
        analyzer.clear()
        for i in range(20):
            analyzer.add_point(100 + i * 5, 100, pressure=0.8)
        
        analysis = analyzer.analyze()
        logger.info(f"   运动模式: {analysis.movement_pattern} ({analyzer.MOVEMENT_PATTERNS[analysis.movement_pattern]['cn']})")
        logger.info(f"   平均速度: {analysis.velocity:.2f} px/s")
        
        # Adaptation Mechanism Demo
        logger.info("\n" + "=" * 60)
        logger.info("适应机制演示 / Adaptation Mechanism Demo")
        logger.info("=" * 60)
        
        mechanism = AdaptationMechanism()
        
        # Register receptor
        mechanism.register_receptor("hand_touch", base_sensitivity=0.8)
        
        logger.info("\n3. 习惯化演示 / Habituation demonstration:")
        logger.info("   重复触摸刺激 / Repeated touch stimuli:")
        for i in range(5):
            state = mechanism.process_stimulus("hand_touch", "touch", intensity=0.6)
            logger.info(f"   刺激 #{i+1}: 敏感度={state.current_sensitivity:.3f}, 习惯化={state.habituation_level:.3f}")
        
        logger.info("\n4. 去习惯化演示 / Dishabituation demonstration:")
        logger.info("   新刺激类型（振动）/ New stimulus type (vibration):")
        state = mechanism.process_stimulus("hand_touch", "vibration", intensity=0.8)
        logger.info(f"   敏感度恢复: {state.current_sensitivity:.3f}, 习惯化降低: {state.habituation_level:.3f}")
    
    # Run demo
    asyncio.run(demo())
