# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [B] [L3]
# =============================================================================
"""Semantic-QA must not answer a why-question with a retrieved attribute.

Pre-registration: HIERARCHICAL_PLAN_FILL_GENERATION.md §8.6. The store used
to match "天空為什麼是藍色的?" to the seeded pair "天空是什麼顏色" -> "蓝色"
at similarity 0.95; that is an answer to a different question. The guard uses
the shared question-shape predicate so the native knowledge path and this
layer cannot drift apart.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BACKEND_SRC = REPO / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from ai.unified_engine.unified_engine import UnifiedEngine  # noqa: E402


class _FakeQA:
    def __init__(self, answer, similarity=0.99):
        self._answer = answer
        self._similarity = similarity

    def answer(self, _question):
        return (self._answer, self._similarity)


def _engine(answer, similarity=0.99):
    """A bare engine: only the attributes _try_semantic_qa touches."""
    engine = object.__new__(UnifiedEngine)
    engine.semantic_qa = _FakeQA(answer, similarity)
    engine._turns = []
    engine._last_route = ""
    engine._last_confidence = 0.0
    return engine


def test_causal_question_declines_a_retrieved_attribute():
    engine = _engine("蓝色")
    assert engine._try_semantic_qa("天空為什麼是藍色的?") is None
    assert engine._last_route == "", "a declined retrieval must not claim a route"


def test_causal_question_accepts_an_explanation():
    engine = _engine("天空是藍色的，因為瑞利散射。")
    result = engine._try_semantic_qa("天空為什麼是藍色的?")
    assert result is not None
    assert "因為" in result
    assert engine._last_route == "semantic-qa"


def test_non_causal_question_still_uses_the_retrieved_attribute():
    engine = _engine("蓝色")
    result = engine._try_semantic_qa("天空是什麼顏色？")
    assert result is not None
    assert "蓝色" in result
