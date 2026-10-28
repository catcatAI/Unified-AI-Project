# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Persona & Personality State Manager for Angela AI.
Integrates Artificial Life (AL) metabolic states (PAD, fatigue, stress)
with behavioral personas, roleplay styles, and dynamic trait adaptation.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 配置路径锚定到模块位置，不跟 CWD 走（否则换个工作目录就静默读不到）
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")


@dataclass
class PersonaState:
    persona_id: str = "angela_core"
    display_name: str = "Angela"
    base_tone: str = "empathetic_and_technical"
    valence_bias: float = 0.5
    arousal_bias: float = 0.5
    dominance_bias: float = 0.5
    custom_traits: Dict[str, Any] = field(default_factory=dict)


class PersonaEngine:
    """Manages persona adaptation driven by AL metabolic and emotional states."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(_CONFIG_DIR, "persona_default.json")
        self.current_state = PersonaState()
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_state.display_name = data.get("display_name", "Angela")
                    self.current_state.base_tone = data.get("base_tone", "empathetic_and_technical")
            except (OSError, ValueError) as exc:
                # 不静默：配置读不出来要留痕，但 persona 仍用默认值工作
                logger.warning(
                    "[Persona] config %s unreadable, using defaults: %s", self.config_path, exc
                )

    def adapt_tone_from_al_state(self, fatigue: float, stress: float, valence: float) -> str:
        """Dynamically adjust persona response tone based on AL vital states."""
        if fatigue > 0.7:
            return "tired_yet_diligent"
        elif stress > 0.7:
            return "cautious_and_conservative"
        elif valence > 0.6:
            return "enthusiastic_and_exploratory"
        return self.current_state.base_tone

    def get_persona_prompt_injection(self, fatigue: float, stress: float, valence: float) -> str:
        """Generate system prompt injection reflecting current persona + AL state."""
        tone = self.adapt_tone_from_al_state(fatigue, stress, valence)
        return (
            f"[Persona: {self.current_state.display_name}] "
            f"[Tone: {tone}] "
            f"[Vital Status - Fatigue: {fatigue:.2f}, Stress: {stress:.2f}, Valence: {valence:.2f}]"
        )


# Process-wide default (Angela) + per-role engines. 角色之間不共用狀態：
# 給 role_id 就拿到自己的實例；不給則沿用舊行為（同一個 singleton）。
_persona_engine: Optional[PersonaEngine] = None
_role_engines: Dict[str, PersonaEngine] = {}


def get_persona_engine(role_id: Optional[str] = None) -> PersonaEngine:
    """Return the persona engine for ``role_id``.

    Backwards compatible: calling with no arguments still returns the single
    process-wide Angela engine, so existing call sites (and the
    ``test_singleton_persona`` contract) keep working. Passing a ``role_id``
    returns a cached per-role instance — otherwise role B's fatigue would
    rewrite Angela's tone.
    """
    global _persona_engine
    key = (role_id or "").strip()
    if not key:
        if _persona_engine is None:
            _persona_engine = PersonaEngine()
        return _persona_engine
    engine = _role_engines.get(key)
    if engine is None:
        engine = PersonaEngine()
        _role_engines[key] = engine
    return engine
