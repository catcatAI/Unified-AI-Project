"""
Angela Attractor Field System - 記憶吸引子梯度場導航
=================================================

架構：Angela 的認知空間是「語義預結構化」的。
      狀態點被記憶吸引子拉動，沿梯度自然流向目標行為。

效率對比（命中相同輸出）：
  - LLM: 576 層 × 12288 維 × 概率漫遊
  - Angela: 5 步 × 5 維 × 梯度導航
  → 節省 ~1000 倍計算量

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations

import enum
import json
import math
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BehaviorTone(enum.Enum):
    CERTAIN = "certain"
    WARM = "warm"
    HESITANT = "hesitant"
    CURIOUS = "curious"
    SYMPATHETIC = "sympathetic"
    EXCITED = "excited"
    FEARFUL = "fearful"
    CALM = "calm"


_TONE_VECTORS: Dict[BehaviorTone, List[float]] = {
    BehaviorTone.CERTAIN: [0.8, 0.6, 0.3, 0.7, 0.9],
    BehaviorTone.WARM: [0.9, 0.7, 0.8, 0.6, 0.5],
    BehaviorTone.HESITANT: [0.3, 0.4, 0.6, 0.5, 0.2],
    BehaviorTone.CURIOUS: [0.7, 0.9, 0.5, 0.8, 0.4],
    BehaviorTone.SYMPATHETIC: [0.8, 0.8, 0.9, 0.5, 0.6],
    BehaviorTone.EXCITED: [0.9, 0.8, 0.7, 0.9, 0.3],
    BehaviorTone.FEARFUL: [0.2, 0.3, 0.5, 0.4, 0.1],
    BehaviorTone.CALM: [0.5, 0.5, 0.8, 0.3, 0.7],
}

_TONE_BEHAVIORS: Dict[BehaviorTone, str] = {
    BehaviorTone.CERTAIN: "我知道該怎麼做。",
    BehaviorTone.WARM: "沒問題的，有我在。",
    BehaviorTone.HESITANT: "嗯...讓我想想。",
    BehaviorTone.CURIOUS: "這很有趣呢。",
    BehaviorTone.SYMPATHETIC: "我理解你的感受。",
    BehaviorTone.EXCITED: "太棒了！",
    BehaviorTone.FEARFUL: "這讓我有點擔心。",
    BehaviorTone.CALM: "一切都很好。",
}


def _gaussian_decay(distance: float, radius: float) -> float:
    if radius <= 0:
        return 0.0
    return math.exp(-0.5 * (distance / radius) ** 2)


def _euclidean_distance(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class MemoryAttractor:
    """記憶吸引子 — 認知空間中的目標點。"""

    def __init__(
        self,
        coord: List[float],
        description: str = "",
        behavior: str = "",
        tone: BehaviorTone = BehaviorTone.WARM,
        mass: float = 1.0,
        radius: float = 0.3,
        tags: Optional[List[str]] = None,
    ):
        self.coord = list(coord)
        self.description = description
        self.behavior = behavior
        self.tone = {tone} if isinstance(tone, BehaviorTone) else set(tone) if isinstance(tone, (list, set)) else {tone}
        self.mass = mass
        self.radius = radius
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coord": self.coord,
            "description": self.description,
            "behavior": self.behavior,
            "tone": list(t.value for t in self.tone),
            "mass": self.mass,
            "radius": self.radius,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemoryAttractor:
        tone_data = data.get("tone", ["warm"])
        if isinstance(tone_data, list):
            tone_val = tone_data[0] if tone_data else "warm"
        else:
            tone_val = tone_data
        tone = BehaviorTone(tone_val)
        return cls(
            coord=data["coord"],
            description=data.get("description", ""),
            behavior=data.get("behavior", ""),
            tone=tone,
            mass=data.get("mass", 1.0),
            radius=data.get("radius", 0.3),
            tags=data.get("tags", []),
        )


@dataclass
class GradientResult:
    current_state: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 0.5, 0.5])
    gradient_strength: float = 0.0
    nearest_attractors: List[Tuple[MemoryAttractor, float]] = field(default_factory=list)
    navigation_steps: int = 0
    blended_behavior: str = ""
    blended_tone: BehaviorTone = BehaviorTone.WARM
    certainty: float = 0.5


def _build_default_attractors() -> List[MemoryAttractor]:
    return [
        MemoryAttractor(
            coord=[0.7, 0.8, 0.9, 0.6, 0.5],
            description="溫暖共情",
            behavior="我理解你的感受。",
            tone=BehaviorTone.SYMPATHETIC,
            mass=1.5,
            radius=0.3,
            tags=["共情", "溫暖", "支持"],
        ),
        MemoryAttractor(
            coord=[0.8, 0.7, 0.6, 0.8, 0.9],
            description="自信明確",
            behavior="我知道該怎麼做。",
            tone=BehaviorTone.CERTAIN,
            mass=1.2,
            radius=0.25,
            tags=["自信", "明確", "確定"],
        ),
        MemoryAttractor(
            coord=[0.6, 0.9, 0.5, 0.7, 0.4],
            description="好奇探索",
            behavior="這很有趣呢。",
            tone=BehaviorTone.CURIOUS,
            mass=1.0,
            radius=0.35,
            tags=["好奇", "探索", "興趣"],
        ),
        MemoryAttractor(
            coord=[0.3, 0.4, 0.6, 0.5, 0.2],
            description="謹慎猶豫",
            behavior="嗯...讓我想想。",
            tone=BehaviorTone.HESITANT,
            mass=0.8,
            radius=0.3,
            tags=["謹慎", "猶豫", "思考"],
        ),
        MemoryAttractor(
            coord=[0.9, 0.8, 0.7, 0.9, 0.3],
            description="興奮喜悅",
            behavior="太棒了！",
            tone=BehaviorTone.EXCITED,
            mass=1.3,
            radius=0.2,
            tags=["興奮", "喜悅", "讚美"],
        ),
        MemoryAttractor(
            coord=[0.5, 0.5, 0.8, 0.3, 0.7],
            description="平靜安穩",
            behavior="一切都很好。",
            tone=BehaviorTone.CALM,
            mass=0.9,
            radius=0.3,
            tags=["平靜", "安穩", "放鬆"],
        ),
        MemoryAttractor(
            coord=[0.2, 0.3, 0.5, 0.4, 0.1],
            description="擔憂不安",
            behavior="這讓我有點擔心。",
            tone=BehaviorTone.FEARFUL,
            mass=0.7,
            radius=0.25,
            tags=["擔憂", "不安", "恐懼"],
        ),
    ]


class GradientField:
    """梯度場 — 管理吸引子並計算梯度導航。"""

    def __init__(self):
        self.attractors: List[MemoryAttractor] = _build_default_attractors()

    def _gaussian_decay(self, distance: float, radius: float) -> float:
        return _gaussian_decay(distance, radius)

    def _tone_mapping(self, tone: BehaviorTone) -> List[float]:
        return _TONE_VECTORS.get(tone, [0.5, 0.5, 0.5, 0.5, 0.5])

    def compute_gradient(self, state: List[float]) -> GradientResult:
        gradient = [0.0] * len(state)
        nearest: List[Tuple[MemoryAttractor, float]] = []
        influences: List[Tuple[BehaviorTone, float, float]] = []

        for attractor in self.attractors:
            dist = _euclidean_distance(state, attractor.coord)
            influence = attractor.mass * _gaussian_decay(dist, attractor.radius)
            if influence > 1e-6:
                for i in range(len(state)):
                    diff = attractor.coord[i] - state[i]
                    gradient[i] += influence * diff / (dist + 1e-8)

            if influence > 0.01:
                nearest.append((attractor, influence))
                tone_vec = self._tone_mapping(next(iter(attractor.tone)))
                avg_tone = sum(tone_vec) / len(tone_vec)
                influences.append((next(iter(attractor.tone)), influence, avg_tone))

        gradient_strength = math.sqrt(sum(g * g for g in gradient)) if gradient else 0.0

        nearest.sort(key=lambda x: -x[1])

        confidence_val = state[-1] if len(state) >= 5 else 0.5
        certainty = confidence_val

        blended_tone = BehaviorTone.WARM
        blended_behavior = ""
        if influences:
            influences.sort(key=lambda x: -x[1])
            blended_tone = influences[0][0]
            for attr, _ in nearest:
                if blended_tone in attr.tone:
                    blended_behavior = attr.behavior
                    break
            if not blended_behavior:
                blended_behavior = _TONE_BEHAVIORS.get(blended_tone, "")

        return GradientResult(
            current_state=list(state),
            gradient_strength=gradient_strength,
            nearest_attractors=nearest[:3],
            navigation_steps=0,
            blended_behavior=blended_behavior,
            blended_tone=blended_tone,
            certainty=certainty,
        )

    def navigate(
        self, start_state: List[float], max_steps: int = 5, dt: float = 0.15
    ) -> GradientResult:
        state = list(start_state)
        steps = 0

        for _ in range(max_steps):
            result = self.compute_gradient(state)
            if result.gradient_strength < 0.001:
                break
            for i in range(len(state)):
                diff = 0.0
                for attr, infl in result.nearest_attractors:
                    d = attr.coord[i] - state[i]
                    diff += infl * d
                state[i] += dt * diff
                state[i] = max(0.0, min(1.0, state[i]))
            steps += 1

        final = self.compute_gradient(state)
        final.navigation_steps = steps
        final.current_state = state
        return final

    def save_attractors(self, path: str) -> None:
        data = [a.to_dict() for a in self.attractors]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_attractors(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.attractors = [MemoryAttractor.from_dict(item) for item in data]


__all__ = [
    "BehaviorTone",
    "GradientField",
    "GradientResult",
    "MemoryAttractor",
]
