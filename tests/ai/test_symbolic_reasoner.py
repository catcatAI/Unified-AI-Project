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


@pytest.mark.parametrize(
    "question, a, b",
    [
        # bicycles/tricycles: 20 vehicles, 54 wheels -> 6 bikes (12) + 14 trikes (42)
        ("There are bicycles and tricycles, 20 vehicles and 54 wheels. How many of each?", 6, 14),
        # nickels/dimes: 18 coins, 140 cents -> 8 nickels (40) + 10 dimes (100)
        ("Nickels and dimes, 18 coins worth 140 cents. How many of each?", 8, 10),
        # nickels/quarters with decimal dollar total: 17 coins, $2.05 -> 11 nickels (55) + 6 quarters (150)
        ("I have 17 coins worth $2.05, all nickels and quarters. How many of each?", 11, 6),
        # motorcycles/cars: 30 vehicles, 100 wheels -> 10 motorcycles (20) + 20 cars (80)
        ("A parking lot has motorcycles and cars, 30 vehicles and 100 wheels. How many of each?", 10, 20),
    ],
)
def test_word_problem_extended_kinds(question, a, b):
    out = route_reasoning(question)
    assert out is not None
    assert str(a) in out and str(b) in out


def test_word_problem_coin_chinese():
    # 12 枚硬幣總值 80 分 -> 8 nickel (40) + 4 dime (40)
    out = route_reasoning("有 12 枚硬幣，總值 80 分，全是五分錢和一角硬幣，各有多少枚？")
    assert out is not None
    assert "8" in out and "4" in out


def test_word_problem_rejects_unsolvable():
    # No clean integer solution -> fall through (None).
    out = route_reasoning("I have 25 coins worth $4.10, all nickels and quarters. How many of each?")
    assert out is None


def test_word_problem_out_of_scope_returns_none():
    # Only one entity present or no explicit legs total -> fall through.
    assert route_reasoning("The cage has chickens. How many legs total?") is None
    assert route_reasoning("A chicken has how many legs?") is None
    # Two entities but no totals -> fall through.
    assert route_reasoning("How many chickens and rabbits are there in this picture?") is None


# ---------------------------------------------------------------------------
# Out-of-scope (should fall through -> None)
# ---------------------------------------------------------------------------

def test_out_of_scope_returns_none():
    assert route_reasoning("What is the meaning of life?") is None
    assert route_reasoning("Tell me a joke about cats.") is None
