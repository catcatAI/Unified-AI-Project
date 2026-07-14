# =============================================================================
# ANGELA-MATRIX: [L3] [αδ] [B] [L2]
# =============================================================================

"""
Tests for CognitivePipeline math cognition.

Principle under test:
  * Stateless, meaningless arithmetic (e.g. "917 * 814") is computed and
    answered but produces NO emotion/state change.
  * Meaningful math (a posed problem, or math tied to a stateful RPG
    attribute) may produce bounded cognitions (joy, repetition dampening,
    waiting, RPG-high -> happiness).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "apps", "backend", "src"
    ),
)


class _Axis:
    def __init__(self):
        self.values = {
            "happiness": 0.5,
            "excitement": 0.5,
            "focus": 0.6,
            "clarity": 0.5,
            "anticipation": 0.5,
            "arousal": 0.5,
            "fatigue": 0.0,
            "certainty": 0.5,
            "fear": 0.0,
            "surprise": 0.0,
            "tension": 0.0,
            "confusion": 0.0,
        }


class _FakeStateMatrix:
    def __init__(self):
        self.alpha = _Axis()
        self.beta = _Axis()
        self.gamma = _Axis()
        self.delta = _Axis()
        self.epsilon = _Axis()


def _make_pipeline():
    from ai.memory.cognitive_pipeline import CognitivePipeline
    from ai.memory.math_ripple_engine import MathRippleEngine

    sm = _FakeStateMatrix()
    engine = MathRippleEngine(state_matrix=sm)
    pipeline = CognitivePipeline(state_matrix=sm, math_ripple_engine=engine)
    return pipeline, sm


@pytest.mark.asyncio
async def test_stateless_math_produces_no_emotion():
    pipeline, sm = _make_pipeline()
    before = sm.gamma.values["happiness"]
    result = await pipeline.process("917 * 814")
    after = sm.gamma.values["happiness"]
    # Answered, but emotion/state untouched for stateless arithmetic.
    assert result["math_result"] is not None
    assert before == after


@pytest.mark.asyncio
async def test_stateless_number_expression_no_emotion():
    pipeline, sm = _make_pipeline()
    before = sm.gamma.values["happiness"]
    await pipeline.process("1+1")
    after = sm.gamma.values["happiness"]
    assert before == after


@pytest.mark.asyncio
async def test_meaningful_question_produces_joy():
    pipeline, sm = _make_pipeline()
    before = sm.gamma.values["happiness"]
    cog = await pipeline.process("what is 2+2?")
    after = sm.gamma.values["happiness"]
    assert cog["math_cognition"]["meaningful"] is True
    assert after > before  # joy at a correctly solved problem


@pytest.mark.asyncio
async def test_rpg_attribute_high_produces_happiness():
    pipeline, sm = _make_pipeline()
    before = sm.gamma.values["happiness"]
    cog = await pipeline.process("hp + 200")
    after = sm.gamma.values["happiness"]
    assert cog["math_cognition"]["attribute"] == "hp"
    assert after > before  # big number -> happy


@pytest.mark.asyncio
async def test_repeated_problem_detected():
    pipeline, sm = _make_pipeline()
    first = await pipeline.process("what is 3+3?")
    assert first["math_cognition"]["is_repetition"] is False
    second = await pipeline.process("what is 3+3?")
    assert second["math_cognition"]["is_repetition"] is True


@pytest.mark.asyncio
async def test_non_math_text_ignored():
    pipeline, sm = _make_pipeline()
    result = await pipeline.process("你好今天天氣真好")
    assert result["math_result"] is None
