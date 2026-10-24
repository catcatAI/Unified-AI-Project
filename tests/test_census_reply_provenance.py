# LAYER: surface
# -*- coding: utf-8 -*-
"""The provenance census must never count a pre-stored answer as produced.

A template, a distilled solution rule, a taught fact or a dictionary gloss
served as the *first* producer means the answer existed before the question
arrived: that is leakage, not intelligence. The census classifies by the first
producer that returned a value, and these tests pin the contract that keeps
the "produced by the system (computed/other)" bucket honest.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "census_reply_provenance.py"


@pytest.fixture(scope="module")
def census():
    spec = importlib.util.spec_from_file_location("census_reply_provenance_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prestored_categories_are_named(census):
    assert set(census.PRESTORED) == {"template", "rule-store", "memory", "dictionary"}


@pytest.mark.parametrize("producer", ["template", "rule-store", "memory", "dictionary"])
def test_prestored_first_hit_is_never_produced(census, producer):
    verdict = census._classify("math", "The stored answer.", "a question", [producer])
    assert verdict["content"] == producer
    assert verdict["content"] not in ("computed", "other")


def test_computed_and_other_stay_produced(census):
    assert census._classify("math", "13", "q", ["computed"])["content"] == "computed"
    assert census._classify("math", "some novel text", "q", [])["content"] == "other"


def test_echo_and_abstain_are_not_produced(census):
    question = "What keeps objects on the ground?"
    echoed = census._classify("math", question, question, [])
    assert echoed["content"] == "echo"
    assert census._classify("math", "", "q", [])["content"] == "abstain"


def test_first_producer_decides(census):
    """A rule hit followed by a computed hit is a served rule, not a computation."""
    verdict = census._classify("math", "13", "q", ["rule-store", "computed"])
    assert verdict["content"] == "rule-store"
