# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Unit tests for PersonaEngine and Persona integration with AL states.
"""

import pytest
from ai.persona.persona_engine import PersonaEngine, get_persona_engine


def test_persona_engine_init():
    engine = PersonaEngine()
    assert engine.current_state.display_name == "Angela"


def test_tone_adaptation_fatigue():
    engine = PersonaEngine()
    tone = engine.adapt_tone_from_al_state(fatigue=0.8, stress=0.2, valence=0.5)
    assert tone == "tired_yet_diligent"


def test_tone_adaptation_stress():
    engine = PersonaEngine()
    tone = engine.adapt_tone_from_al_state(fatigue=0.2, stress=0.85, valence=0.5)
    assert tone == "cautious_and_conservative"


def test_tone_adaptation_enthusiastic():
    engine = PersonaEngine()
    tone = engine.adapt_tone_from_al_state(fatigue=0.1, stress=0.1, valence=0.8)
    assert tone == "enthusiastic_and_exploratory"


def test_prompt_injection_format():
    engine = PersonaEngine()
    injection = engine.get_persona_prompt_injection(fatigue=0.5, stress=0.3, valence=0.6)
    assert "Angela" in injection
    assert "Fatigue: 0.50" in injection


def test_singleton_persona():
    e1 = get_persona_engine()
    e2 = get_persona_engine()
    assert e1 is e2


def test_role_engine_is_cached_per_role():
    default = get_persona_engine()
    role_b = get_persona_engine("role_b_factory_test")
    assert role_b is not default
    assert role_b is get_persona_engine("role_b_factory_test")


def test_role_engines_do_not_share_persona_state():
    role_a = get_persona_engine("role_a_factory_test")
    role_b = get_persona_engine("role_b_factory_test")
    role_a.current_state.display_name = "Gemma 角色"
    assert role_b.current_state.display_name == "Angela"
