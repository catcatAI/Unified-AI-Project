# =============================================================================
# ANGELA-MATRIX: L3 βδ A L3
# =============================================================================

"""
EvolutionEngine — 性格演化引擎
===============================

根據情感/安全性反饋調整人格參數與動態閾值。

EvolutionEngine 改為直接與
DigitalLifeIntegrator 的 life_stats.personality_traits 及 DynamicThresholdManager 協作。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TRAITS: Dict[str, float] = {
    "openness": 0.5,
    "conscientiousness": 0.5,
    "extraversion": 0.5,
    "agreeableness": 0.5,
    "neuroticism": 0.5,
}


class EvolutionEngine:
    """
    性格演化引擎 — 根據情感/安全性反饋調整人格參數。

    與 DynamicThresholdManager 及 personality_traits dict 協作，
    不依賴已移除的 PersonalityManager。
    """

    def __init__(
        self,
        dynamic_threshold_manager: Optional[Any] = None,
        personality_traits: Optional[Dict[str, float]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.dtm = dynamic_threshold_manager
        self._traits: Dict[str, float] = dict(
            personality_traits or _DEFAULT_TRAITS
        )
        self.config = config or {}
        self._learning_rate: float = self.config.get("learning_rate", 0.05)
        self._decay_rate: float = self.config.get("decay_rate", 0.001)
        self._last_update: Optional[datetime] = None

    @property
    def traits(self) -> Dict[str, float]:
        return dict(self._traits)

    def get_trait(self, name: str, default: float = 0.5) -> float:
        return self._traits.get(name, default)

    def set_trait(self, name: str, value: float) -> None:
        self._traits[name] = max(0.0, min(1.0, value))

    def evolve_from_feedback(
        self,
        emotion_state: Optional[Dict[str, float]] = None,
        safety_score: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        根據情感狀態與安全性分數調整人格參數。

        - 正向情感（happiness, valence）→ 增加 openness, extraversion
        - 負向情感（anger, fear）→ 增加 neuroticism，降低 agreeableness
        - 安全性高 → 增加 conscientiousness, agreeableness
        - 安全性低 → 增加 neuroticism，降低 extraversion
        - 隨時間自然回歸默認值（decay）
        """
        now = datetime.now()
        if self._last_update:
            elapsed_hours = (now - self._last_update).total_seconds() / 3600.0
            decay = self._decay_rate * elapsed_hours
            for trait in self._traits:
                default = _DEFAULT_TRAITS.get(trait, 0.5)
                if self._traits[trait] > default:
                    self._traits[trait] = max(default, self._traits[trait] - decay)
                elif self._traits[trait] < default:
                    self._traits[trait] = min(default, self._traits[trait] + decay)
        self._last_update = now

        lr = self._learning_rate

        if emotion_state:
            happiness = emotion_state.get("happiness", 0.5)
            anger = emotion_state.get("anger", 0.0)
            fear = emotion_state.get("fear", 0.0)
            valence = emotion_state.get("valence", 0.5)
            arousal = emotion_state.get("arousal", 0.5)

            delta_open = (happiness - 0.5) * lr + (valence - 0.5) * lr * 0.5
            self._traits["openness"] = max(0.0, min(1.0, self._traits["openness"] + delta_open))

            delta_extra = (happiness - 0.3) * lr * 0.8 + (arousal - 0.5) * lr * 0.3
            self._traits["extraversion"] = max(0.0, min(1.0, self._traits["extraversion"] + delta_extra))

            delta_neuro = (fear * 0.4 + anger * 0.3) * lr
            self._traits["neuroticism"] = max(0.0, min(1.0, self._traits["neuroticism"] + delta_neuro))

            if anger > 0.5:
                self._traits["agreeableness"] = max(0.0, self._traits["agreeableness"] - anger * lr * 0.5)

        if safety_score is not None:
            safe = max(0.0, min(1.0, safety_score))
            unsafe = 1.0 - safe

            self._traits["conscientiousness"] = max(0.0, min(1.0,
                self._traits["conscientiousness"] + (safe - 0.5) * lr * 0.6))

            self._traits["agreeableness"] = max(0.0, min(1.0,
                self._traits["agreeableness"] + (safe - 0.5) * lr * 0.4))

            self._traits["neuroticism"] = max(0.0, min(1.0,
                self._traits["neuroticism"] + unsafe * lr * 0.3))

            self._traits["extraversion"] = max(0.0, min(1.0,
                self._traits["extraversion"] - unsafe * lr * 0.2))

        if self.dtm is not None:
            try:
                extra = self._traits.get("extraversion", 0.5)
                neuro = self._traits.get("neuroticism", 0.5)
                self.dtm.set_parameter("social_initiative_threshold", max(0.1, min(0.9, 0.5 - extra * 0.15 + neuro * 0.1)))
            except Exception:
                logger.debug("Failed to propagate traits to DTM", exc_info=True)

        return self.traits

    def sync_to_life_stats(self, life_stats: Any) -> None:
        """Sync current traits into a LifeStats personality_traits dict."""
        if life_stats is None:
            return
        try:
            for key, val in self._traits.items():
                life_stats.personality_traits[key] = val
        except Exception:
            logger.debug("Failed to sync traits to life_stats", exc_info=True)


__all__ = ["EvolutionEngine"]
