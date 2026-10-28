# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Unit tests for PersonaIntegrationBridge.
"""

import pytest
from ai.persona.persona_integration_bridge import PersonaIntegrationBridge, get_persona_bridge


def test_bridge_default_angela():
    bridge = PersonaIntegrationBridge(active_persona="angela")
    injection = bridge.get_prompt_injection(fatigue=0.3, stress=0.2, valence=0.7)
    assert "Angela" in injection
    assert "Fatigue: 0.30" in injection


def test_bridge_lucifaella_switch():
    bridge = PersonaIntegrationBridge(active_persona="lucifaella")
    injection = bridge.get_prompt_injection(fatigue=0.4, stress=0.5, valence=0.5)
    assert "Lucifaella" in injection
    assert "天使工房商務部負責人" in injection


def test_bridge_special_responses():
    bridge = PersonaIntegrationBridge(active_persona="lucifaella")
    intro = bridge.get_special_response("greeting")
    assert "天使工房" in intro

    err_resp = bridge.get_special_response("error", error_type="api_limit")
    assert "quota is insufficient" in err_resp


def test_bridge_singleton():
    b1 = get_persona_bridge()
    b2 = get_persona_bridge()
    assert b1 is b2
