# =============================================================================
# ANGELA-MATRIX: L1-L6[小腦] γ [A] L3
# =============================================================================
# 職責: 小腦反射系統 (Tickle Reflex System).
# 維度: 物理維度 (γ) 的觸覺反射、快速回應與安全邊界。
# 設計: 配置驅動、雙層安全、Phase1(反射) + Phase2(LLM)
# =============================================================================

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_BODY_PARTS = {
    "abdomen": {"sensitivity": 0.9, "region": "core", "reflex_type": "squirm"},
    "arms": {"sensitivity": 0.6, "region": "upper", "reflex_type": "pull_away"},
    "back": {"sensitivity": 0.3, "region": "core", "reflex_type": "arch"},
    "chest": {"sensitivity": 0.9, "region": "core", "reflex_type": "protect"},
    "ears": {"sensitivity": 0.5, "region": "head", "reflex_type": "flinch"},
    "face": {"sensitivity": 0.7, "region": "head", "reflex_type": "flinch"},
    "feet": {"sensitivity": 0.8, "region": "lower", "reflex_type": "withdraw"},
    "forehead": {"sensitivity": 0.5, "region": "head", "reflex_type": "flinch"},
    "hands": {"sensitivity": 0.7, "region": "upper", "reflex_type": "grasp"},
    "knees": {"sensitivity": 0.3, "region": "lower", "reflex_type": "buckle"},
    "neck": {"sensitivity": 0.8, "region": "head", "reflex_type": "tilt"},
    "shoulders": {"sensitivity": 0.8, "region": "upper", "reflex_type": "shrug"},
    "sides": {"sensitivity": 0.9, "region": "core", "reflex_type": "squirm"},
    "thighs": {"sensitivity": 0.5, "region": "lower", "reflex_type": "tense"},
}


class TickleReflexSystem:
    """小腦反射系統 — Phase1(反射) + Phase2(LLM) 雙層安全架構."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg = config or {}
        self._body_parts: Dict[str, Dict[str, Any]] = cfg.get(
            "body_parts", dict(_DEFAULT_BODY_PARTS)
        )
        self._light_threshold: float = cfg.get("light_threshold", 0.3)
        self._medium_threshold: float = cfg.get("medium_threshold", 0.5)
        self._intense_threshold: float = cfg.get("intense_threshold", 0.58)
        self._reflex_timeout_ms: int = cfg.get("reflex_timeout_ms", 5000)
        self._max_llm_words: int = cfg.get("max_llm_words", 50)
        self._initialized = True
        logger.info("TickleReflexSystem initialized: %d body parts", len(self._body_parts))

    # ------------------------------------------------------------------
    # Intensity helpers
    # ------------------------------------------------------------------

    def get_intensity_level(self, value: float) -> str:
        if value < self._light_threshold:
            return "none"
        if value < self._medium_threshold:
            return "light"
        if value < self._intense_threshold:
            return "medium"
        return "intense"

    def get_intensity_thresholds(self) -> Dict[str, float]:
        return {
            "light": self._light_threshold,
            "medium": self._medium_threshold,
            "intense": self._intense_threshold,
        }

    # ------------------------------------------------------------------
    # Body part queries
    # ------------------------------------------------------------------

    def get_all_body_parts(self) -> List[str]:
        return list(self._body_parts.keys())

    def get_sensitive_parts(self, threshold: float = 0.7) -> List[str]:
        return [p for p, c in self._body_parts.items() if c.get("sensitivity", 0) >= threshold]

    def get_reflex_config(self, part: str) -> Dict[str, Any]:
        return self._body_parts.get(part, {})

    # ------------------------------------------------------------------
    # Core reflex
    # ------------------------------------------------------------------

    async def trigger_tickles(
        self,
        body_part: str,
        intensity: float,
        duration_seconds: float = 1.0,
        origin: str = "System",
        state_matrix: Optional[Any] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        intensity = max(0.0, min(1.0, intensity))
        level = self.get_intensity_level(intensity)
        part_cfg = self._body_parts.get(body_part, {})
        is_sensitive = part_cfg.get("sensitivity", 0) >= 0.7
        sustained = duration_seconds > 5.0

        # Phase1: reflex output (always present)
        if sustained or (is_sensitive and intensity >= 0.6):
            output_mode = "comfort_seek"
        elif intensity >= 0.8:
            output_mode = "scream"
        elif is_sensitive:
            output_mode = "comfort_seek"
        elif level == "light":
            output_mode = "giggle"
        elif level == "medium":
            output_mode = "laugh"
        else:
            output_mode = "scream"

        reflex_type = part_cfg.get("reflex_type", "flinch")
        phase1 = {
            "animation": reflex_type,
            "output_mode": output_mode,
            "intensity": intensity,
        }

        # Phase2: LLM prompt preparation for refined response generation
        # Phase2 constructs the LLM input; actual LLM call is handled upstream
        phase2 = {
            "prompt": f"Tickle reflex on {body_part} ({level}, {output_mode}) from {origin}",
            "llm_words": self._max_llm_words,
        }

        # Gamma axis invasion for sustained / sensitive stimuli
        if state_matrix is not None and (sustained or is_sensitive):
            try:
                state_matrix.shift_axis("gamma", -0.1 if sustained else -0.05)
            except Exception:
                logger.warning("Failed to shift gamma axis for tickle reflex", exc_info=True)

        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "body_part": body_part,
            "intensity_level": level,
            "is_sensitive": is_sensitive,
            "sustained": sustained,
            "phase1": phase1,
            "phase2": phase2,
            "elapsed_ms": round(elapsed, 2),
            "origin": origin,
        }


# ------------------------------------------------------------------
# Singleton factory
# ------------------------------------------------------------------

_REFLEX_INSTANCE: Optional[TickleReflexSystem] = None


def get_reflex_system(config: Optional[Dict[str, Any]] = None) -> TickleReflexSystem:
    global _REFLEX_INSTANCE
    if _REFLEX_INSTANCE is None:
        _REFLEX_INSTANCE = TickleReflexSystem(config)
    return _REFLEX_INSTANCE
