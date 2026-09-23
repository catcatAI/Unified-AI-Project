# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================
"""
Hormonal modulation system for SNN threshold adjustment.
"""

import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class HormonalModulator:
    """
    Global modulation signal that affects all SNN neuron thresholds.
    Does NOT participate in spike transmission, but modulates thresholds.

    - High cortisol -> threshold LOWER -> neurons fire easier -> Angela more sensitive
    - High serotonin -> threshold HIGHER -> more stable, focused
    - High dopamine -> threshold LOWER -> more exploratory
    - High adrenaline -> threshold LOWER -> faster reflexes
    """

    def __init__(self):
        self.hormones: Dict[str, float] = {
            "cortisol": 0.5,
            "serotonin": 0.5,
            "dopamine": 0.5,
            "adrenaline": 0.3,
            "oxytocin": 0.4,
            "noradrenaline": 0.3,
        }
        self._endocrine_system: Any = None
        self._last_sync: float = 0.0

    def connect_endocrine_system(self, endocrine_system: Any) -> None:
        """Connect to the real EndocrineSystem for live hormone readings."""
        self._endocrine_system = endocrine_system
        logger.info("HormonalModulator connected to EndocrineSystem")

    def sync_from_endocrine(self) -> None:
        """Pull latest hormone levels from EndocrineSystem."""
        if self._endocrine_system is None:
            return
        try:
            from core.bio.endocrine_types import HormoneType

            # 生產者（EndocrineSystemCore.get_hormonal_profile）的 hormones 鍵是
            # ht.en_name（如 "Cortisol"）；用 en_name 查表一次到位。
            hormone_map = {
                "cortisol": HormoneType.CORTISOL.en_name,
                "serotonin": HormoneType.SEROTONIN.en_name,
                "dopamine": HormoneType.DOPAMINE.en_name,
                "adrenaline": HormoneType.ADRENALINE.en_name,
                "oxytocin": HormoneType.OXYTOCIN.en_name,
                # 注意：內分泌系統的枚舉成員是 NOREPINEPHRINE（藥典名），
                # 不是 NORADRENALINE——曾誤寫成不存在的成員，AttributeError 被
                # except 吞掉，live 同步從未成功、永遠只用靜態預設值。
                "noradrenaline": HormoneType.NOREPINEPHRINE.en_name,
            }
            profile = self._endocrine_system.get_hormonal_profile()
            hormones_profile = profile.get("hormones", {})
            for our_key, profile_key in hormone_map.items():
                entry = hormones_profile.get(profile_key)
                if isinstance(entry, dict):
                    normalized = entry.get("normalized")
                    if normalized is not None:
                        self.hormones[our_key] = min(max(float(normalized), 0.0), 1.0)
            self._last_sync = time.time()
        except Exception as e:
            logger.warning("Failed to sync from EndocrineSystem: %s", e)

    def set_hormone(self, name: str, level: float) -> None:
        """Manually set a hormone level (0-1)."""
        if name in self.hormones:
            self.hormones[name] = min(max(level, 0.0), 1.0)

    def modulate_threshold(self, base_threshold: float) -> float:
        """
        Apply hormonal modulation to a base threshold.
        Cortisol lowers threshold (more sensitive).
        Serotonin raises threshold (more stable).
        """
        cortisol_effect = self.hormones.get("cortisol", 0.5) * 0.3
        serotonin_effect = self.hormones.get("serotonin", 0.5) * 0.2
        dopamine_effect = self.hormones.get("dopamine", 0.5) * 0.1
        adrenaline_effect = self.hormones.get("adrenaline", 0.3) * 0.15

        total_mod = 1.0 - cortisol_effect - dopamine_effect - adrenaline_effect + serotonin_effect
        return base_threshold * max(total_mod, 0.3)

    def get_modulation_factor(self) -> float:
        """Return the current global modulation factor."""
        return self.modulate_threshold(1.0) / 1.0

    def get_profile_summary(self) -> Dict[str, Any]:
        return {
            "hormones": dict(self.hormones),
            "modulation_factor": round(self.get_modulation_factor(), 3),
            "endocrine_connected": self._endocrine_system is not None,
            "last_sync": self._last_sync,
        }
