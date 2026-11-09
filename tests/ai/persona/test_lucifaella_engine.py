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
    assert not hasattr(engine.state, "shareholding")


def test_lucifaella_commercial_intro():
    engine = LucifaellaPersonaEngine()
    intro = engine.get_commercial_intro()
    assert intro == ""


def test_lucifaella_error_reaction():
    engine = LucifaellaPersonaEngine()
    err_msg = engine.react_to_error("api_limit")
    assert err_msg == ""


def test_lucifaella_prompt_injection():
    engine = LucifaellaPersonaEngine()
    injection = engine.get_persona_prompt_injection(fatigue=0.2, stress=0.3)
    assert "Lucifaella" in injection
    assert "public-facing host" in injection
    assert "receptionist/showcase host" in injection
    assert engine.state.title == "迎賓主持／看板娘"
    assert "does not replace" in injection
    assert "fixed or copied replies" in injection
    assert "12%" not in injection


def test_lucifaella_singleton():
    e1 = get_lucifaella_engine()
    e2 = get_lucifaella_engine()
    assert e1 is e2
