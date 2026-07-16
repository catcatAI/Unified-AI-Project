"""
=============================================================================
ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
=============================================================================

Unit tests for ai.symbolic_reasoner.route_reasoning — deterministic symbolic
reasoning (transitive / syllogism / calendar / quantity / mass-trick).
"""

import pytest

from ai.symbolic_reasoner import route_reasoning


# ---------------------------------------------------------------------------
# Transitive (taller-than chains)
# ---------------------------------------------------------------------------

def test_transitive_tallest():
    out = route_reasoning("A is taller than B. B is taller than C. Who is the tallest?")
    assert out is not None
    assert "A" in out


def test_transitive_shortest():
    out = route_reasoning("X is shorter than Y. Y is shorter than Z. Who is the shortest?")
    assert out is not None
    assert "X" in out


# ---------------------------------------------------------------------------
# Syllogism (universal premise + membership)
# ---------------------------------------------------------------------------

def test_syllogism_affirmative():
    out = route_reasoning(
        "All mammals are animals. A dog is a mammal. Is a dog an animal?"
    )
    assert out is not None
    assert "yes" in out.lower()


def test_syllogism_negative():
    out = route_reasoning(
        "No birds can swim. A penguin is a bird. Can a penguin swim?"
    )
    assert out is not None
    assert "no" in out.lower()


def test_syllogism_plural_singular_membership():
    # Category given in plural ("birds") but membership in singular ("bird").
    out = route_reasoning(
        "All birds can fly. A sparrow is a bird. Can a sparrow fly?"
    )
    assert out is not None
    assert "yes" in out.lower()


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("today,expected", [
    ("Monday", "Tuesday"),
    ("Friday", "Saturday"),
    ("Sunday", "Monday"),
])
def test_calendar_tomorrow(today, expected):
    out = route_reasoning(f"If today is {today}, what day is tomorrow?")
    assert out is not None
    assert expected.lower() in out.lower()


# ---------------------------------------------------------------------------
# Quantity (word-problem subtraction)
# ---------------------------------------------------------------------------

def test_quantity_subtraction():
    out = route_reasoning(
        "John has 3 apples. He gives 1 away. How many left?"
    )
    assert out is not None
    assert "2" in out


# ---------------------------------------------------------------------------
# Mass trick
# ---------------------------------------------------------------------------

def test_mass_trick_english():
    out = route_reasoning("Which is heavier: 1kg of feathers or 1kg of steel?")
    assert out is not None
    assert "same" in out.lower()


def test_mass_trick_chinese():
    out = route_reasoning("1公斤棉花和1公斤铁哪个更重？")
    assert out is not None
    assert "一样重" in out or "same" in out.lower()


# ---------------------------------------------------------------------------
# Out-of-scope (should fall through -> None)
# ---------------------------------------------------------------------------

def test_out_of_scope_returns_none():
    assert route_reasoning("What is the meaning of life?") is None
    assert route_reasoning("Tell me a joke about cats.") is None
