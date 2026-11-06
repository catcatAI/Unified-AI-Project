"""Gate test for C-logit (``scripts/al_c_logit.py``).

This one loads a real 1.5B model, so it is marked slow and skipped when the
checkpoint is absent. It is worth the cost because the failure it catches is the
one that actually happened: a logits processor that records pre-bias values, or
that mutates a copy without returning it, reads as "no effect" and would make the
whole claim look killed when the wiring was simply wrong.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_c_logit.py"
MODEL = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not MODEL.exists(), reason="local GGUF checkpoint not present"),
]


@pytest.fixture(scope="module")
def result():
    spec = importlib.util.spec_from_file_location("al_c_logit_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_c_logit_test"] = module
    spec.loader.exec_module(module)
    return module.run(MODEL, n_phases=4)


def test_verdict(result):
    assert result["verdict"] == "phase-reaches-logits"
    assert all(result["checks"].values()) is True


def test_the_bias_changes_the_distribution(result):
    assert result["kl_range"][1] > 0.01
    deltas = [row["delta"] for row in result["rows"]]
    assert min(deltas) < 0.0 < max(deltas)


def test_neutral_bias_leaves_the_logits_alone(result):
    assert result["checks"]["neutral_is_bit_identical"] is True


def test_it_is_not_wall_clock(result):
    assert result["clock_forgery_reproducible"] is False
    assert abs(result["permutation_correlation"]) < 0.5
