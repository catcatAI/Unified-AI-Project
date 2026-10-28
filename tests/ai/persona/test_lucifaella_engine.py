# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Unit tests for LucifaellaPersonaEngine.
"""

import pytest
from ai.persona.lucifaella_engine import LucifaellaPersonaEngine, get_lucifaella_engine


def test_lucifaella_init():
    engine = LucifaellaPersonaEngine()
    assert engine.state.name == "Lucifaella"
    assert engine.state.shareholding == 0.12


def test_lucifaella_commercial_intro():
    engine = LucifaellaPersonaEngine()
    intro = engine.get_commercial_intro()
    assert "天使工房" in intro
    assert "商務部" in intro


def test_lucifaella_error_reaction():
    engine = LucifaellaPersonaEngine()
    err_msg = engine.react_to_error("api_limit")
    assert "quota is insufficient" in err_msg


def test_lucifaella_prompt_injection():
    engine = LucifaellaPersonaEngine()
    injection = engine.get_persona_prompt_injection(fatigue=0.2, stress=0.3)
    assert "Lucifaella" in injection
    assert "商務部負責人" in injection


def test_lucifaella_singleton():
    e1 = get_lucifaella_engine()
    e2 = get_lucifaella_engine()
    assert e1 is e2
