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
            BodyPart.KNEES: [ceptorType.FREE_NERVE, ReceptorType.PACINIAN],
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
            except Exception:
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
                except Exception:
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


@dataclass
class TactileResponse:
    """触觉响应 / Tactile response"""
    stimulus: TactileStimulus
    perceived_intensity: float
    activated_receptors: int
    duration: float
    timestamp: datetime
    
    def __repr__(self) -> str:
        return (
            f"TactileResponse({self.stimulus.tactile_type.name} at "
            f"{self.stimulus.location.cn_name}, intensity={self.perceived_intensity:.2f})"
        )


# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize the system
        system = PhysiologicalTactileSystem()
        await system.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 生理触觉系统演示")
        print("Physiological Tactile System Demo")
        print("=" * 60)
        
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
        
        print("\n处理触觉刺激 / Processing tactile stimuli:\n")
        for i, stimulus in enumerate(stimuli, 1):
            print(f"{i}. {stimulus.tactile_type.name} on {stimulus.location.cn_name}")
            response = await system.process_stimulus(stimulus)
            print(f"   感知强度: {response.perceived_intensity:.2f}")
            print(f"   激活受体数: {response.activated_receptors}")
            print()
        
        # Show receptor status
        print("手掌受体状态 / Hand receptor status:")
        status = system.get_receptor_status(BodyPart.HANDS)
        for receptor_type, activation in status.items():
            print(f"  - {receptor_type.name}: {activation:.3f}")
        
        # Change arousal and show effect
        print("\n改变唤醒水平 / Changing arousal level to 80...")
        system.set_arousal_level(80)
        print(f"手部敏感度: {system.get_body_part_sensitivity(BodyPart.HANDS):.3f}")
        
        await system.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    # Run demo
    asyncio.run(demo())
