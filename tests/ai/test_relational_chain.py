"""Tests for offline relational-chain reasoning (shared resolver + engines).

These verify genuine multi-hop transitive-closure derivation over explicitly
stated comparison edges, independent of any pre-trained neural association.
"""
import pytest

from ai.reasoning.relational_chain import (
    ask_direction,
    parse_and_resolve_relational_chain,
    parse_comparison_edges,
    resolve_relational_chain,
)


def _edges(*triples):
    return list(triples)


def test_parse_detects_comparison_edges():
    edges, entities = parse_comparison_edges(
        "X is warmer than Y. Y is warmer than Z."
    )
    assert ("X", "Y", 1.0) in edges
    assert ("Y", "Z", 1.0) in edges
    assert set(entities) >= {"X", "Y", "Z"}


def test_parse_reverses_lesser_comparator():
    edges, _ = parse_comparison_edges("M is shorter than N.")
    # "shorter" => M < N, stored as (M, N, -1.0); the resolver reverses it.
    assert ("M", "N", -1.0) in edges


def test_resolve_greatest():
    edges = _edges(("X", "Y", 1.0), ("Y", "Z", 1.0))
    assert resolve_relational_chain(edges, ["X", "Y", "Z"], ask_max=True) == "X"


def test_resolve_least():
    edges = _edges(("X", "Y", 1.0), ("Y", "Z", 1.0))
    assert resolve_relational_chain(edges, ["X", "Y", "Z"], ask_max=False) == "Z"


def test_resolve_ambiguous_returns_none():
    # X > Y and Y > X conflict -> no unique solution
    edges = _edges(("X", "Y", 1.0), ("Y", "X", 1.0))
    assert resolve_relational_chain(edges, ["X", "Y"], ask_max=True) is None


def test_ask_direction_detects_least():
    assert ask_direction("Who is the richest?") is True
    assert ask_direction("Who is the poorest?") is False
    assert ask_direction("Who is coldest?") is False


def test_parse_and_resolve_greatest_question():
    out = parse_and_resolve_relational_chain(
        "X is warmer than Y. Y is warmer than Z. Who is warmest?",
        resolver=resolve_relational_chain,
    )
    assert out == "X is the greatest"


def test_parse_and_resolve_least_question():
    out = parse_and_resolve_relational_chain(
        "X is richer than Y. Y is richer than Z. Who is the poorest?",
        resolver=resolve_relational_chain,
    )
    assert out == "Z is the least"


def test_parse_and_resolve_no_structure():
    assert (
        parse_and_resolve_relational_chain(
            "What color is the sky?", resolver=resolve_relational_chain
        )
        is None
    )


def test_ed3n_chain_stage():
    from ai.ed3n.ed3n_engine import ED3NEngine

    engine = ED3NEngine()
    engine.load_presets()
    # The full process() must route relational chains correctly.
    assert "Z" in engine.process(
        "X is richer than Y. Y is richer than Z. Who is the poorest?"
    )
    assert "A" in engine.process(
        "A is warmer than B. B is warmer than C. Who is warmest?"
    )


def test_garden_chain_stage():
    from ai.garden.garden_engine import GARDENEngine

    engine = GARDENEngine()
    engine.load_presets()
    assert "Z" in engine.process(
        "X is richer than Y. Y is richer than Z. Who is the poorest?"
    )
    # Novel proper-noun comparators (Alpha/Beta/Gamma) the regex reasoner misses.
    assert "Gamma" in engine.process(
        "Alpha is faster than Beta. Beta is faster than Gamma. Who is slowest?"
    )
