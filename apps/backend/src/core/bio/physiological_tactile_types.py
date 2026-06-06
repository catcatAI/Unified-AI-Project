"""
Angela AI v6.0 - Physiological Tactile Types
生理触觉系统类型定义

Shared types, enums, dataclasses and data structures for the tactile system.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import math
import logging

logger = logging.getLogger(__name__)


class ReceptorType(Enum):
    """6种皮肤受体类型 / 6 types of skin receptors"""

    MEISSNER = auto()  # 迈斯纳小体 - 轻触、快速适应 / Light touch, rapid adapting
    MERKEL = auto()  # 默克尔细胞 - 压力、持续刺激 / Pressure, sustained stimulus
    PACINIAN = auto()  # 帕西尼小体 - 震动、深层压力 / Vibration, deep pressure
    RUFFINI = auto()  # 鲁菲尼小体 - 皮肤拉伸 / Skin stretch
    FREE_NERVE = auto()  # 游离神经末梢 - 痛觉、温度 / Pain, temperature
    HAIR_FOLLICLE = auto()  # 毛囊感受器 - 毛发运动 / Hair movement


class TactileType(Enum):
    """6种触觉类型 / 6 types of tactile sensations"""

    LIGHT_TOUCH = auto()  # 轻触 / Light touch
    PRESSURE = auto()  # 压力 / Pressure
    TEMPERATURE = auto()  # 温度 / Temperature
    VIBRATION = auto()  # 震动 / Vibration
    PAIN = auto()  # 疼痛 / Pain
    ITCH = auto()  # 瘙痒 / Itch


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
    TOP_OF_HEAD = ("头顶", BodyRegion.HEAD, 0.7, (0.0, 20.0, 0.0))
    FOREHEAD = ("额头", BodyRegion.HEAD, 0.8, (0.0, 19.0, 1.0))
    FACE = ("面部", BodyRegion.HEAD, 0.9, (0.0, 18.0, 2.0))
    NECK = ("颈部", BodyRegion.HEAD, 0.6, (0.0, 16.0, 0.0))

    # Upper body (上身)
    CHEST = ("胸部", BodyRegion.UPPER_BODY, 0.5, (0.0, 14.0, 1.0))
    BACK = ("背部", BodyRegion.UPPER_BODY, 0.4, (0.0, 14.0, -1.0))
    ABDOMEN = ("腹部", BodyRegion.UPPER_BODY, 0.5, (0.0, 10.0, 1.0))
    WAIST = ("腰部", BodyRegion.UPPER_BODY, 0.5, (0.0, 8.0, 0.0))

    # Lower body (下身)
    HIPS = ("臀部", BodyRegion.LOWER_BODY, 0.4, (0.0, 6.0, -1.0))
    THIGHS = ("大腿", BodyRegion.LOWER_BODY, 0.4, (2.0, 4.0, 0.0))

    # Upper limbs (上肢)
    SHOULDERS = ("肩膀", BodyRegion.UPPER_LIMBS, 0.6, (4.0, 15.0, 0.0))
    UPPER_ARMS = ("上臂", BodyRegion.UPPER_LIMBS, 0.5, (5.0, 12.0, 0.0))
    FOREARMS = ("前臂", BodyRegion.UPPER_LIMBS, 0.6, (6.0, 9.0, 0.0))
    HANDS = ("手掌", BodyRegion.UPPER_LIMBS, 1.0, (7.0, 7.0, 1.0))
    FINGERS = ("手指", BodyRegion.UPPER_LIMBS, 1.0, (7.5, 6.0, 1.0))

    # Lower limbs (下肢)
    KNEES = ("膝盖", BodyRegion.LOWER_LIMBS, 0.6, (2.0, 2.0, 1.0))
    CALVES = ("小腿", BodyRegion.LOWER_LIMBS, 0.5, (2.0, 1.0, 0.0))
    FEET = ("脚底", BodyRegion.LOWER_LIMBS, 0.8, (2.0, 0.0, 0.0))

    def __init__(self, cn_name: str, region: BodyRegion, base_sensitivity: float, coordinate: Tuple[float, float, float]):
        self.cn_name = cn_name
        self.region = region
        self.base_sensitivity = base_sensitivity
        self.coordinate = coordinate


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

    def __post_init__(self) -> None:
        """Execute the   post init   operation."""
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

    def __post_init__(self) -> None:
        """Execute the   post init   operation."""
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


@dataclass
class TactileResponse:
    """触觉响应 / Tactile response"""

    stimulus: TactileStimulus
    perceived_intensity: float
    activated_receptors: int
    duration: float
    timestamp: datetime
    live2d_parameters: Dict[str, float] = field(
        default_factory=dict
    )  # Added for Live2D integration
    # =============================================================================
    # ANGELA-MATRIX: [L3] [αβγδ] [A] [L5+]
    # [Task N.20.3] 空間標籤 [x, y, z, t]
    # =============================================================================
    spatial_token: Tuple[float, float, float, float] = field(
        default_factory=lambda: (0.0, 0.0, 0.0, 0.0)
    )

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
        "poke": {
            "ParamEyeLOpen": (0.5, 0.8),
            "ParamEyeROpen": (0.5, 0.8),
            "ParamCheek": (0.3, 0.6),
        },
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
