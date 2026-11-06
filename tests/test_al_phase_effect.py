"""Tests for the phase-effect gate (``scripts/al_phase_effect.py``).

The gate answers "does the phase change a decision". Its value is entirely in the
controls, so the tests pin those: remove the rhythm and the decision must not
move; shuffle the activations against the phases and the explained variance must
collapse even though the spread stays the same.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_phase_effect.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_phase_effect_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_phase_effect_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def result(gate):
    return gate.run()


def test_gate_reaches_a_positive_verdict(result):
    assert result["verdict"] == "phase-affects-decision"
    assert all(result["checks"].values()) is True


def test_the_effect_is_big_enough_to_matter(result):
    assert result["spread"] > 0.03
    assert max(result["weights"]) > min(result["weights"])


def test_phase_explains_the_weight(result):
    assert result["phase_explained"] > 0.9
    # 置換後變異一樣大，但相位不再解釋它 —— 差分就在這裡。
    assert result["permutation"]["phase_explained"] < 0.2
    assert result["permutation"]["spread"] > 0.05


def test_without_the_rhythm_nothing_moves(result):
    assert result["control_spread"] == 0.0


def test_forgeries_are_refused(result):
    assert result["forgeries"]["constant"]["spread"] == 0.0
    assert result["forgeries"]["clock"]["reproducible"] is False
