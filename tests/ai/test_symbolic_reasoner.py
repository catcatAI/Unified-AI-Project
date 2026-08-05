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
# Two-object linear pair (chicken-rabbit cage)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "question, a, b",
    [
        # heads + legs, English (35 heads / 94 legs -> 23 chicken, 12 rabbit)
        ("The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?", 23, 12),
        # 籠中共有雞和兔子 35 隻, 腳 94 隻
        ("籠中共有雞和兔子 35 隻，腳 94 隻，問雞兔各幾隻？", 23, 12),
        # 共 35 頭, 94 腳
        ("雞兔同籠，共 35 頭，94 腳，問雞和兔各有多少？", 23, 12),
    ],
)
def test_chicken_rabbit_solved(question, a, b):
    out = route_reasoning(question)
    assert out is not None
    assert str(a) in out and str(b) in out


def test_chicken_rabbit_small_case():
    # 10 heads / 28 legs -> 6 chickens, 4 rabbits (6*2 + 4*4 = 12 + 16 = 28)
    out = route_reasoning("There are chickens and rabbits. 10 heads and 28 legs. How many each?")
    assert out is not None
    assert "6" in out and "4" in out


def test_word_problem_out_of_scope_returns_none():
    # Only one entity present or no explicit legs total -> fall through.
    assert route_reasoning("The cage has chickens. How many legs total?") is None
    assert route_reasoning("A chicken has how many legs?") is None


# ---------------------------------------------------------------------------
# Out-of-scope (should fall through -> None)
# ---------------------------------------------------------------------------

def test_out_of_scope_returns_none():
    assert route_reasoning("What is the meaning of life?") is None
    assert route_reasoning("Tell me a joke about cats.") is None
