"""Contract tests for the training-readiness probe's pure helpers.

The probe itself needs a teacher model, a checkpoint and 3 minutes, so it is not
a unit test. What *can* silently break are the arithmetic pieces it uses to
decide pass/fail: the bigram floor, the teacher's atom log-probability, and the
exit-code logic. Each is pinned here against a hand-computed value — a probe
whose arithmetic drifts is worse than no probe, because it keeps printing
numbers.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_training_readiness.py"


def _load():
    spec = importlib.util.spec_from_file_location("probe_training_readiness_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


# ---------------------------------------------------------------------------
# exit codes: the probe must not report "ready" when it is not
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["PASS", "PASS", "INFO"], 0),
        (["PASS", "FAIL", "BLOCKED"], 1),
        (["PASS", "BLOCKED", "INFO"], 2),
        ([], 0),
    ],
)
def test_verdict_maps_statuses_to_exit_codes(probe, statuses, expected) -> None:
    rep = probe.Report()
    for status in statuses:
        rep.add(status.lower(), status)
    assert rep.verdict() == expected


def test_counts_are_per_status(probe) -> None:
    rep = probe.Report()
    rep.add("a", "PASS")
    rep.add("b", "PASS")
    rep.add("c", "FAIL")
    assert rep.counts() == {"PASS": 2, "FAIL": 1}


def test_add_rejects_unknown_status(probe) -> None:
    with pytest.raises(AssertionError):
        probe.Report().add("x", "READY")


# ---------------------------------------------------------------------------
# bigram floor
# ---------------------------------------------------------------------------
def test_bigram_floor_beats_the_unigram_on_a_deterministic_sequence(probe) -> None:
    train = [[0, 1, 2], [0, 1, 2]]
    val = [[0, 1, 2]]
    lam, floor = probe._interpolated_bigram_floor(train, val)

    # Hand-computed unigram CE with add-0.1 over the 3 observed atoms:
    total = 6
    p_uni = (2 + 0.1) / (total + 0.1 * 3)
    unigram_ce = -math.log(p_uni)
    assert floor < unigram_ce
    assert 0.0 < floor < 0.5, "a perfectly predictable sequence must be cheap"
    assert lam in (0.3, 0.5, 0.7, 0.9, 0.97)


def test_bigram_floor_is_infinite_free_on_unseen_atoms(probe) -> None:
    """An unseen atom gets the unigram branch, not ``log(0)``."""
    _, floor = probe._interpolated_bigram_floor([[0, 1]], [[0, 1, 9]])
    assert math.isfinite(floor)


# ---------------------------------------------------------------------------
# the teacher arithmetic lives in ai/ed3n/kd_teacher.py and is pinned there
# (tests/ai/test_kd_teacher.py) against a fake tokeniser. Here we only assert the
# probe *delegates*: a second hand-rolled copy is how a 0.84 gold agreement was
# once measured as 0.32.
# ---------------------------------------------------------------------------
def test_probe_uses_the_shared_teacher(probe) -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "from ai.ed3n.kd_teacher import KdTeacher" in source
    # The helpers that duplicated the teacher arithmetic must stay gone.
    for gone in (
        "def _atom_boundaries(",
        "def _char_spans(",
        "def _token_logprobs(",
        "def _atom_logprob(",
        "def _teacher_token_texts(",
    ):
        assert gone not in source, f"{gone} duplicates kd_teacher"


def test_probe_uses_the_shared_mapper(probe) -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "from ai.ed3n.kd_targets import AtomPrefixIndex" in source


def test_probe_uses_the_trainers_kd_loss(probe) -> None:
    """The probe must not own a second copy of the distillation objective."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "from ai.ed3n.kd_cache import KdCache" in source
    assert "kd_cache.batch_loss(" in source
    # The subset-softmax form that was quoted in the docs must stay gone.
    assert "log_softmax(logits[0, pos]" not in source
