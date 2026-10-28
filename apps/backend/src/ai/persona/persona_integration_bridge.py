# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Persona Manager & Integration Bridge.
Unifies PersonaEngine and LucifaellaPersonaEngine with the prompt builder
and chat pipeline, injecting AL (Artificial Life) state into LLM context.
"""

from typing import Any, Optional

from ai.persona.lucifaella_engine import LucifaellaPersonaEngine, get_lucifaella_engine
from ai.persona.persona_engine import PersonaEngine, get_persona_engine


class PersonaIntegrationBridge:
    """Bridges persona engines with chat context and prompt generation."""

    def __init__(self, active_persona: str = "angela"):
        self.active_persona = active_persona
        self.angela_engine = get_persona_engine()
        self.lucifaella_engine = get_lucifaella_engine()

    def set_active_persona(self, persona_name: str) -> None:
        self.active_persona = persona_name.lower()

    def get_prompt_injection(
        self, fatigue: float = 0.2, stress: float = 0.1, valence: float = 0.5
    ) -> str:
        """Get the appropriate persona system prompt injection based on active persona and AL state."""
        if "lucifaella" in self.active_persona or "茜法拉" in self.active_persona:
            return self.lucifaella_engine.get_persona_prompt_injection(fatigue, stress)
        return self.angela_engine.get_persona_prompt_injection(fatigue, stress, valence)

    def get_special_response(self, event_type: str, **kwargs: Any) -> Optional[str]:
        """Get specialized persona responses (e.g. commercial intro, error reaction)."""
        if "lucifaella" in self.active_persona:
            if event_type == "greeting":
                return self.lucifaella_engine.get_commercial_intro()
            elif event_type == "error":
                return self.lucifaella_engine.react_to_error(kwargs.get("error_type", "api_limit"))
        return None


# Singleton factory
_bridge_instance: Optional[PersonaIntegrationBridge] = None


def get_persona_bridge() -> PersonaIntegrationBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = PersonaIntegrationBridge()
    return _bridge_instance
