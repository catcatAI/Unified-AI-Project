# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [B] [L3]
# =============================================================================
"""A why-question needs an explanation, not an attribute.

Pre-registration: docs/06-project-management/HIERARCHICAL_PLAN_FILL_GENERATION.md
§8.6 (written before the change, measured with run_benchmarks.py).

These are contract tests for the *general* rule, not the benchmark item:
a causal question must not be answered by a bare attribute, and a retrieved
topical sentence must not count as causal evidence.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import pytest  # noqa: E402
from ai.knowledge_base import route_knowledge  # noqa: E402
from ai.reasoning.question_shape import has_causal_evidence, is_why_question  # noqa: E402


@pytest.mark.parametrize(
    "text",
    [
        "為什麼天空是藍的？",
        "为什么天空是蓝色？",
        "天空為何是藍色？",
        "天空为什么是蓝色",
        "原因是什麼？",
        "why is the sky blue?",
        "Why do leaves look green?",
    ],
)
def test_why_questions_are_recognised(text):
    assert is_why_question(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "天空是什麼顏色？",
        "what color is the sky?",
        "水的沸點是多少？",
        "2加3等於多少",
        "How many legs does a spider have?",
        "",
    ],
)
def test_non_causal_questions_are_not_misclassified(text):
    assert is_why_question(text) is False


@pytest.mark.parametrize(
    "answer",
    [
        "The sky is blue because of Rayleigh scattering.",
        "Sky appears blue due to shorter wavelengths being scattered more.",
        "天空是藍色的，因為瑞利散射。",
        "所以天空看起來是藍色的。",
        "這導致了藍色。",
        "原因是光線散射。",
    ],
)
def test_explanations_carry_causal_evidence(answer):
    assert has_causal_evidence(answer) is True


@pytest.mark.parametrize(
    "answer",
    [
        "blue",
        "蓝色",
        "Blue Sky is a 1994 drama movie.",
        "The sky is blue.",
        "An ice cream float is a beverage.",
    ],
)
def test_related_facts_are_not_causal_evidence(answer):
    assert has_causal_evidence(answer) is False


def test_curated_attribute_is_not_served_for_a_why_question():
    """The store has sky -> blue; that answers 'what colour', not 'why'."""
    assert route_knowledge("為什麼天空是藍的？") is None
    assert route_knowledge("Why is the sky blue?") is None


def test_a_non_causal_attribute_question_still_answers():
    """No regression: the guard is about explanation shapes, not colour."""
    assert route_knowledge("What color is the sky?") == "blue"
    assert route_knowledge("天空是什麼顏色？") == "blue"


def test_encyclopedia_topical_match_abstains_for_a_why_question(monkeypatch):
    """'Blue Sky is a 1994 drama movie' is topical, not an explanation."""
    import ai.knowledge.wiki_facts as wiki

    monkeypatch.setattr(
        wiki,
        "route_general_knowledge",
        lambda text: "Blue Sky is a 1994 drama movie. The movie is about mental illness.",
    )
    assert route_knowledge("Why is the sky blue?") is None


def test_encyclopedia_explanation_is_accepted(monkeypatch):
    """When the sentence states the cause, the retrieval is real evidence."""
    import ai.knowledge.wiki_facts as wiki

    expected = "The sky is blue because air scatters short wavelengths of light."
    monkeypatch.setattr(wiki, "route_general_knowledge", lambda text: expected)
    assert route_knowledge("Why is the sky blue?") == expected
