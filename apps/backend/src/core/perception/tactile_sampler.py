import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
logger = logging.getLogger(__name__)

class MaterialType(Enum):
    METAL = auto()
    WOOD = auto()
    PLASTIC = auto()
    FABRIC = auto()
    GLASS = auto()
    SKIN = auto()
    UNKNOWN = auto()

@dataclass
class TactileProperties:
    """觸覺物理屬性"""
    roughness: float = 0.0  # 粗糙度 (0.0 - 1.0)
    hardness: float = 0.5   # 硬度 (0.0 - 1.0)
    temperature: float = 25.0 # 溫度 (攝氏度)
    friction: float = 0.5   # 摩擦係數
    elasticity: float = 0.1 # 彈性
    vibration_pattern: List[float] = field(default_factory=list) # 觸碰時的震動紋理

@dataclass
class TactileContactPoint:
    """精確的觸覺接觸點"""
    position: Tuple[float, float, float] # 相對物體的 3D 座標 (x, y, z)
    body_part: str # 接觸的部位 (如 "index_finger_tip", "palm")
    pressure: float # 壓力大小
    area: float # 接觸面積
    timestamp: float = field(default_factory=lambda: 0.0)

class TactileSampler:
    """觸覺採樣器：負責將視覺特徵 (紋理、光影) 映射為觸覺屬性建模"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def infer_properties_from_visuals(self, visual_features: Dict[str, Any]) -> TactileProperties:
        """
        核心邏輯：根據物體的模型、紋理、色彩、光影等特徵，建模相應的質感
        """
        # 模擬 AI 推斷過程
        texture_complexity = visual_features.get('texture_complexity', 0.5)
        specular_reflection = visual_features.get('specular_reflection', 0.5) # 光澤度
        color_warmth = visual_features.get('color_warmth', 0.5)
        
        # 推斷材質類型
        material = self._classify_material(visual_features)
        
        # 根據材質與視覺特徵建模屬性
        props = TactileProperties()
        
        if material == MaterialType.METAL:
            props.roughness = texture_complexity * 0.2
            props.hardness = 0.9
            props.temperature = 18.0 if specular_reflection > 0.6 else 22.0 # 金屬通常感覺較涼
            props.friction = 0.3
        elif material == MaterialType.WOOD:
            props.roughness = texture_complexity * 0.8
            props.hardness = 0.7
            props.temperature = 24.0
            props.friction = 0.6
        elif material == MaterialType.FABRIC:
            props.roughness = texture_complexity * 0.9
            props.hardness = 0.1
            props.temperature = 26.0
            props.friction = 0.8
            props.elasticity = 0.6
        else:
            props.roughness = texture_complexity
            props.hardness = 0.5
            props.temperature = 25.0
            
        return props

    def _classify_material(self, visual_features: Dict[str, Any]) -> MaterialType:
        """根據視覺資訊分類材質 (模擬)"""
        name = visual_features.get('name', '').lower()
        if 'metal' in name or 'steel' in name: return MaterialType.METAL
        if 'wood' in name or 'table' in name: return MaterialType.WOOD
        if 'cloth' in name or 'shirt' in name: return MaterialType.FABRIC
        if 'glass' in name: return MaterialType.GLASS
        return MaterialType.UNKNOWN

    def generate_contact_feedback(self, props: TactileProperties, contact: TactileContactPoint) -> Dict[str, Any]:
        """產生細緻到部位的觸覺反饋數據"""
        # 結合壓力、硬度與粗糙度計算即時感覺
        felt_roughness = props.roughness * (1.0 + contact.pressure)
        felt_hardness = props.hardness * contact.pressure
        
        return {
            "body_part": contact.body_part,
            "location": contact.position,
            "sensations": {
                "texture_feel": "rough" if felt_roughness > 0.7 else "smooth",
                "resistance": felt_hardness,
                "temperature_delta": props.temperature - 36.5, # 相對於人體體溫
                "vibration": "subtle" if props.friction < 0.4 else "strong"
            },
            "intensity": contact.pressure * 100
        }
