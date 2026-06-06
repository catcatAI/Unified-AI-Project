"""
Angela AI v7.5.0-dev - State Matrix Types
狀態矩陣類型定義

Contains data classes for the 6D State Matrix System:
- AllocateDecision: Meta-cognitive allocation decisions
- AxisSemanticAnchor: Semantic anchors for axis identity
- DimensionState: Dimension state for the 4D matrix

Author: Angela AI Development Team
Version: 6.2.1
Date: 2026-05-13
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from datetime import datetime
import logging
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class AllocateDecision:
    """θ 轴的分配决策 / Meta-cognitive allocation decision"""
    action: str
    target: Optional[str] = None
    targets: Optional[List[Tuple[str, float]]] = None
    proposed_name: Optional[str] = None
    semantic_anchor: Optional[List[float]] = None
    buffer: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format."""
        return {
            "action": self.action,
            "target": self.target,
            "targets": self.targets,
            "proposed_name": self.proposed_name,
            "buffer": self.buffer,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }



@dataclass
class AxisSemanticAnchor:
    """軸的語義錨點 / Semantic anchor for axis identity"""
    name: str
    label: str
    description: str
    semantic_vector: List[float]
    keywords: List[str]

    def compute_resonance(self, input_vector: List[float]) -> float:
        """Compute resonance."""
        if len(input_vector) != len(self.semantic_vector):
            return 0.0
        norm_in = np.linalg.norm(input_vector)
        norm_anchor = np.linalg.norm(self.semantic_vector)
        if norm_in == 0 or norm_anchor == 0:
            return 0.0
        dot = sum(a * b for a, b in zip(input_vector, self.semantic_vector))
        return dot / (norm_in * norm_anchor)


@dataclass
class DimensionState:
    """
    维度状态 / Dimension State

    Represents the state of a single dimension in the 4D matrix.
    """

    name: str
    cn_name: str
    values: Dict[str, float]
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    # =============================================================================
    # ANGELA-MATRIX: [L3] [αβγδ] [A] [L5+]
    # [Task N.20.1] 座標系 AI：空間定址 (x, y, z)
    # =============================================================================
    coordinate: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    intent_vector: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    stability: float = 1.0

    def compute_coordinate(self) -> Tuple[float, float, float]:
        """根據當前維度值計算實際座標 / Compute actual coordinate from current values"""
        from app_config_loader import get_formula_config
        proj_conf = get_formula_config("spatial").get("projection_weights", {}).get(self.name, {})
        
        v = self.values
        n = self.name
        
        # 獲取縮放因子，默認為 1.0
        xf = proj_conf.get("x_factor", 1.0)
        yf = proj_conf.get("y_factor", 1.0)
        zf = proj_conf.get("z_factor", 1.0)

        if n == "alpha":
            comfort = v.get("comfort", 0.5)
            tension = v.get("tension", 0.0)
            energy = v.get("energy", 0.5)
            rest_need = v.get("rest_need", 0.5)
            arousal = v.get("arousal", 0.5)
            x = (comfort - tension) * xf
            y = (energy - rest_need) * yf
            z = (arousal - 0.5) * zf
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "beta":
            clarity = v.get("clarity", 0.5)
            confusion = v.get("confusion", 0.0)
            focus = v.get("focus", 0.5)
            learning = v.get("learning", 0.5)
            curiosity = v.get("curiosity", 0.5)
            creativity = v.get("creativity", 0.5)
            x = (clarity - confusion) * xf
            y = (focus + learning + curiosity) / 3.0 * yf
            z = (creativity - 0.5) * zf
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "gamma":
            happiness = v.get("happiness", 0.5)
            sadness = v.get("sadness", 0.0)
            anger = v.get("anger", 0.0)
            fear = v.get("fear", 0.0)
            trust = v.get("trust", 0.5)
            calm = v.get("calm", 0.5)
            love = v.get("love", 0.0)
            x = (happiness - sadness) * 5.0 + (anger - 0.5) * 2.0
            y = (happiness + trust + calm) / 3.0 * 5.0 + 2.0
            z = (love - fear) * 3.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "delta":
            bond = v.get("bond", 0.5)
            attention = v.get("attention", 0.5)
            presence = v.get("presence", 0.5)
            engagement = v.get("engagement", 0.5)
            intimacy = v.get("intimacy", 0.0)
            x = (bond - intimacy) * 3.0
            y = presence * 5.0
            z = (attention + engagement) / 2.0 * 10.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "epsilon":
            logic = v.get("logic", 0.5)
            precision = v.get("precision", 0.5)
            abstraction = v.get("abstraction_level", v.get("abstraction", 0.5))
            certainty = v.get("certainty", 0.5)
            fatigue = v.get("fatigue", 0.0)
            x = (logic + precision) / 2.0 * 5.0
            y = abstraction * 10.0
            z = (certainty - fatigue) * 5.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "theta":
            novelty = v.get("novelty", 0.5)
            creation_urge = v.get("creation_urge", 0.0)
            correction_urge = v.get("correction_urge", 0.0)
            complexity = v.get("complexity", 0.5)
            x = novelty * 5.0 - 2.5
            y = (creation_urge + correction_urge) * 5.0
            z = complexity * 10.0 - 5.0
            return (round(x, 3), round(y, 3), round(z, 3))
        elif n == "zeta":
            temporal = v.get("temporal_coherence", 0.8)
            memory = v.get("memory_depth", 0.6)
            narrative = v.get("narrative_flow", 0.7)
            identity = v.get("identity_continuity", 0.75)
            x = (temporal - 0.5) * 10.0
            y = (memory + narrative) / 2.0 * 10.0
            z = (identity - 0.5) * 10.0
            return (round(x, 3), round(y, 3), round(z, 3))
        return (0.0, 0.0, 0.0)

    def get_average(self) -> float:
        """获取维度平均值 / Get average value"""
        if not self.values:
            return 0.0
        return sum(self.values.values()) / len(self.values)

    def get_dominant(self) -> Tuple[str, float]:
        """获取主导指标 / Get dominant metric"""
        if not self.values:
            return ("", 0.0)
        return max(self.values.items(), key=lambda x: x[1])

    def update(self, **kwargs) -> None:
        """更新维度值 / Update dimension values"""
        for key, value in kwargs.items():
            if key in self.values:
                self.values[key] = max(0.0, min(1.0, float(value)))
        self.timestamp = datetime.now()


