# ANGELA-MATRIX: L2 [βγδ] [A] [L3+]
"""Cross-process restart probe: are the weights + state files enough on their own?

``scripts/probe_state_restart.py`` is self-verifying (it exits non-zero when a
check fails), so this test only pins the *mechanics* on a smoke budget — two
fresh interpreters, ~6 s — and deliberately does not require the probe's
sensitivity guard: with an under-trained GRU the query answer is dominated by
the input tokens, so a zeroed state looks similar and
``reset_state_is_measurably_different`` fails for a reason that has nothing to
do with restarting. The registered run (2,000 sessions, 10 epochs) is what
clears it, and that result is recorded in ``CORE_GAP_ANALYSIS.md``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def restart():
    return _load("probe_state_restart")


def test_resume_in_a_new_process_is_bit_identical(restart, tmp_path) -> None:
    report = restart.run(tmp_path / "restart", ["gru"], train_sessions=64, train_epochs=1)

    entry = report["arms"]["gru"]
    assert entry["max_prob_delta"] <= restart.REGISTERED["max_prob_delta"]
    assert entry["checks"]["weights_hash_survives"] is True
    assert entry["checks"]["model_kind_survives"] is True
    assert entry["checks"]["ticks_survive"] is True
    assert entry["checks"]["last_dt_s_survives"] is True
    assert entry["checks"]["state_version_survives"] is True
    assert entry["checks"]["refuses_state_from_the_other_arm"] is True
    assert entry["checks"]["attach_refuses_the_wrong_arm"] is True
    assert entry["checks"]["refuses_tampered_state"] is True
    # A cost/restart probe must never be readable as a capability run.
    assert report["registered"] is False
