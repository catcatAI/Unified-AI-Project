# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

"""
Tests for the domain ripple / state propagation framework.

Covers the user's design questions:
  * which tokens ripple vs not (stateless math -> no ripple/emotion),
  * the generalized domain engines (math / physics / chemistry),
  * the full ripple schema is applied (epsilon / fear / confusion / overload),
  * no spurious StateMatrix keys are created (e.g. "excitement"),
  * bounded-cognition magnitudes are principled and clamped.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "apps", "backend", "src"),
)


class _Axis:
    def __init__(self, keys):
        self.values = {k: 0.5 for k in keys}


class _FakeStateMatrix:
    def __init__(self):
        self.alpha = _Axis(["energy", "comfort", "arousal", "rest_need", "tension"])
        self.beta = _Axis(["curiosity", "focus", "confusion", "learning", "clarity"])
        self.gamma = _Axis(
            [
                "happiness", "sadness", "anger", "fear", "disgust",
                "surprise", "trust", "anticipation", "calm",
            ]
        )
        self.delta = _Axis(["attention", "bond", "trust", "presence", "engagement"])
        self.epsilon = _Axis(
            ["logic", "precision", "abstraction", "certainty", "complexity", "fatigue"]
        )
        self.theta = _Axis(
            [
                "novelty", "complexity", "ambiguity", "dimension_fit",
                "creation_urge", "theta_negativity", "correction_urge", "audit_intensity",
            ]
        )


def _make_pipeline():
    from ai.memory.cognitive_pipeline import CognitivePipeline

    sm = _FakeStateMatrix()
    pipeline = CognitivePipeline(state_matrix=sm)
    return pipeline, sm


# ---------------------------------------------------------------------------
# Router + classification: which tokens ripple, which don't
# ---------------------------------------------------------------------------

def test_stateless_math_is_not_meaningful():
    from ai.memory.domain_ripple import route_domain

    engine, value, cls = route_domain("917 * 814")
    assert value is not None
    assert cls["meaningful"] is False
    assert cls["domain"] == "math"


def test_posed_question_is_meaningful():
    from ai.memory.domain_ripple import route_domain

    engine, value, cls = route_domain("what is 2+2?")
    assert cls["meaningful"] is True
    assert cls["is_question"] is True


def test_router_picks_chemistry_for_formula():
    from ai.memory.domain_ripple import route_domain

    engine, value, cls = route_domain("molar mass of H2O")
    assert cls["domain"] == "chemistry"
    assert abs(value - 18.015) < 1e-6


def test_router_picks_physics_for_force():
    from ai.memory.domain_ripple import route_domain

    engine, value, cls = route_domain("force = 10 * 5 newtons")
    assert cls["domain"] == "physics"
    assert value == 50.0


def test_chit_chat_is_not_a_domain():
    from ai.memory.domain_ripple import route_domain

    engine, value, cls = route_domain("你好今天天氣真好")
    assert engine is None
    assert value is None


# ---------------------------------------------------------------------------
# Domain engine correctness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "formula,expected",
    [("H2O", 18.015), ("CO2", 44.009), ("NaCl", 58.44), ("O2", 31.998)],
)
def test_chemistry_molar_mass(formula, expected):
    from ai.memory.domain_ripple import ChemistryDomainEngine

    eng = ChemistryDomainEngine()
    assert eng.can_handle(formula) is True
    assert abs(eng.compute(formula) - expected) < 1e-2


def test_chemistry_rejects_unknown_element():
    from ai.memory.domain_ripple import ChemistryDomainEngine

    eng = ChemistryDomainEngine()
    assert eng.can_handle("Xx2") is False


def test_physics_ripple_shape_for_force():
    from ai.memory.domain_ripple import PhysicsDomainEngine

    eng = PhysicsDomainEngine()
    ripples = eng.make_ripples("force = 10 * 5", 50.0)
    assert ripples
    r = ripples[0]
    assert r.get("alpha_tension") is not None
    assert r.get("gamma_fear") is not None


# ---------------------------------------------------------------------------
# Full ripple application to the StateMatrix (no dropped keys, no spurious keys)
# ---------------------------------------------------------------------------

def test_full_ripple_applies_negative_valence():
    from ai.memory.domain_ripple import apply_ripple_to_state

    sm = _FakeStateMatrix()
    before_beta_confusion = sm.beta.values["confusion"]
    before_clarity = sm.beta.values["clarity"]
    before_gamma_fear = sm.gamma.values["fear"]
    before_certainty = sm.epsilon.values["certainty"]

    ripple = {
        "epsilon_delta": 0.5,
        "alpha_arousal": 0.3,
        "beta_focus": 0.2,
        "gamma_excitement": 0.1,
        "confusion": True,
        "fear": True,
        "overload": True,
    }
    apply_ripple_to_state(sm, ripple)

    assert sm.beta.values["confusion"] > before_beta_confusion
    assert sm.beta.values["clarity"] < before_clarity
    assert sm.gamma.values["fear"] > before_gamma_fear
    assert sm.epsilon.values["certainty"] < before_certainty
    assert sm.epsilon.values["fatigue"] > 0.5
    # No spurious dimension key created.
    assert "excitement" not in sm.gamma.values
    # Values stay clamped in [0, 1].
    for axis in (sm.alpha, sm.beta, sm.gamma, sm.delta, sm.epsilon):
        for v in axis.values.values():
            assert 0.0 <= v <= 1.0


def test_full_ripple_clamps_and_uses_schema():
    from ai.memory.domain_ripple import apply_ripple_to_state

    sm = _FakeStateMatrix()
    # A huge epsilon_delta must not blow past 1.0.
    apply_ripple_to_state(sm, {"epsilon_delta": 100.0, "gamma_excitement": 100.0})
    assert sm.epsilon.values["logic"] <= 1.0
    assert sm.gamma.values["happiness"] <= 1.0


# ---------------------------------------------------------------------------
# Bounded-cognition magnitudes are principled
# ---------------------------------------------------------------------------

def test_joy_only_for_posed_question():
    from ai.memory.domain_ripple import MathDomainEngine

    eng = MathDomainEngine()
    cls = eng.classify("what is 2+2?", 4.0, set())
    deltas = eng.cognition_deltas(cls, 4.0, [])
    # Joy at solving a problem.
    assert deltas["gamma_happiness"] == 0.12
    assert "gamma_excitement" in deltas


def test_high_attribute_value_happiness_is_capped():
    from ai.memory.domain_ripple import MathDomainEngine

    eng = MathDomainEngine()
    # "hp + 200": attribute present, not a question -> only high-value boost.
    cls = eng.classify("hp + 200", 200.0, set())
    deltas = eng.cognition_deltas(cls, 200.0, [])
    boost = deltas["gamma_happiness"]
    # 0.04 + 200/4000 = 0.09, capped at 0.15.
    assert abs(boost - 0.09) < 1e-9
    assert boost <= 0.15


def test_negative_valence_suppresses_joy():
    from ai.memory.domain_ripple import MathDomainEngine

    eng = MathDomainEngine()
    cls = eng.classify("what is 5 - 8?", -3.0, set())
    ripples = [{"confusion": True}]
    deltas = eng.cognition_deltas(cls, -3.0, ripples)
    # No joy; instead a happiness penalty + fear.
    assert deltas["gamma_happiness"] < 0
    assert deltas["gamma_fear"] > 0
    assert "gamma_excitement" not in deltas


def test_stateless_returns_no_deltas():
    from ai.memory.domain_ripple import MathDomainEngine

    eng = MathDomainEngine()
    cls = eng.classify("917 * 814", 746438.0, set())
    assert eng.cognition_deltas(cls, 746438.0, []) == {}


# ---------------------------------------------------------------------------
# End-to-end through CognitivePipeline (stateless -> no emotion)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_stateless_no_emotion():
    pipeline, sm = _make_pipeline()
    before = sm.gamma.values["happiness"]
    result = await pipeline.process("917 * 814")
    after = sm.gamma.values["happiness"]
    assert result["math_result"] is not None
    assert before == after


@pytest.mark.asyncio
async def test_pipeline_chemistry_ripples_state():
    pipeline, sm = _make_pipeline()
    before = sm.gamma.values["happiness"]
    result = await pipeline.process("molar mass of H2O")
    after = sm.gamma.values["happiness"]
    assert result["math_result"] is not None
    assert result["math_cognition"]["domain"] == "chemistry"
    # Meaningful chemistry computation -> bounded happiness bump.
    assert after > before
