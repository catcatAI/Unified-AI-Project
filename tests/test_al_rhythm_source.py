"""Tests for the rhythm-source gate (``scripts/al_rhythm_source.py``).

The gate is the thing being tested: if it ever reports a positive verdict
without its checks passing, or lets a forgery through, the claim it backs is
worthless. So these tests assert on the gate's own judgements.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_rhythm_source.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_rhythm_source_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_rhythm_source_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def result(gate):
    return gate.run(120.0)


def test_gate_reaches_its_verdict(result):
    assert result["verdict"] == "self-rhythm-admissible"
    assert result["main_ok"] is True
    assert result["forgeries_all_fail"] is True


def test_constant_input_still_moves(result):
    check = result["checks"]["constant_input"]
    assert check["cv"] > 0.05
    assert check["period_s"] > 1.0


def test_period_follows_mu_and_is_not_a_table(result):
    law = result["checks"]["period_law"]
    assert law["increasing_in_mu"] is True
    assert law["span_s"] > 1.0
    assert law["d_period_per_mu"] > 0.02


def test_forgeries_each_fail_something(result):
    forgeries = result["forgeries"]
    assert forgeries["table"]["passed"] is False
    assert forgeries["table"]["reacts_to_mu"] is False
    assert forgeries["clock"]["passed"] is False
    assert forgeries["clock"]["reproducible_from_state"] is False
    assert forgeries["leaky"]["passed"] is False
    assert forgeries["leaky"]["cv"] < 0.05


def test_the_beat_carries_the_internal_period(result):
    beat = result["checks"]["beat_inherits"]
    assert beat["passed"] is True
    assert beat["interval_cv"] > 0.05
    assert beat["rel_err"] < 0.10
