# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for ``scripts/probe_content_capacity.py``.

The probe makes two kinds of claim, and both are tested without training:

* the **envelope** arithmetic - a parameter count that matches a real
  ``TokenSNN``, a nested sample that is actually nested and actually spread
  across the corpus rather than taking the first N rows, and row counts that
  add up;
* the **capacity rule** - a size is "stored" only at whole-answer teacher-forced
  accuracy >= 0.90, the verdict cannot round a failure up, and ``--check``
  rejects a report whose stored flags or capacity verdict disagree with its own
  numbers.

No checkpoint is trained and no measured accuracy is asserted: the numbers
belong to ``data/capacity/report.json`` (gitignored), not to this file.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_content_capacity.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load("probe_capacity_under_test", PROBE)


def _run(size: int, whole: float, config: str = "small", epochs: int = 2) -> dict:
    return {
        "config": config,
        "size": size,
        "params": 1_000_000,
        "epochs": epochs,
        "train": {"n": size, "whole": whole, "tf_acc": whole},
        "stored": whole >= 0.90,
        "curve": [{"epoch": i + 1, "loss": 1.0} for i in range(epochs)],
    }


# -- envelope ---------------------------------------------------------------
def test_analytic_params_matches_a_real_stack(probe):
    torch = pytest.importorskip("torch")
    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab

    vocab = TokenVocab([f"w{i}" for i in range(2000)])
    expected = probe.analytic_params(len(vocab), 96, 192)
    model = TokenSNN(vocab, TokenConfig(d_emb=96, d_hidden=192), device="cpu")
    actual = sum(int(p.numel()) for p in model.net.parameters())
    assert actual == expected
    assert len(vocab) == 2005  # 2000 atoms + 5 specials


def test_analytic_params_is_the_documented_108m_shape(probe):
    # The 108M checkpoint was measured as 108,583,431 parameters with 32,773
    # atoms at d_emb=512 / d_hidden=2560 (TRAINING_INTERNALS.md §3).
    assert probe.analytic_params(32_773, 512, 2560) == 108_583_431


def test_nested_sample_is_nested_and_not_the_file_order(probe):
    pairs = [(f"question number {i}", f"answer {i}") for i in range(400)]
    picked = probe.nested_sample(pairs, (10, 40, 100))
    assert set(picked[10]) < set(picked[40]) < set(picked[100])
    assert picked[10] != list(range(10))
    assert len(set(picked[100])) == 100
    # Deterministic across calls (the report must be reproducible).
    again = probe.nested_sample(pairs, (10, 40, 100))
    assert picked == again


def test_nested_sample_refuses_to_invent_rows(probe):
    with pytest.raises(ValueError):
        probe.nested_sample([("q", "a")], (1, 2))


class _FakeVocab:
    """Minimal encoder for the envelope arithmetic (no torch, no vocab build)."""

    stoi = {"a": 0}
    unk_id = 1

    def __init__(self, width: int = 1) -> None:
        self.width = width

    def __len__(self) -> int:
        return len(self.stoi)

    def encode(self, _text: str):
        return [0] * self.width


def test_inventory_counts_and_contradictions(probe):
    train = [("q1", "a"), ("q1", "b"), ("q2", "a"), ("q3", "a")]
    env = probe.inventory(train, [("q", "a")], max_len=1000, vocab=_FakeVocab())
    assert env["train_rows"] == 4
    assert env["rows_fitting_max_len"] == 4
    assert env["unique_prompts"] == 3
    assert env["prompts_with_multiple_answers"] == 1
    assert env["widths"]["small"]["params"] < env["widths"]["medium"]["params"]


def test_inventory_reports_rows_that_do_not_fit(probe):
    env = probe.inventory([("q", "a")], [], max_len=10, vocab=_FakeVocab(width=50))
    assert env["rows_fitting_max_len"] == 0
    assert env["rows_over_max_len"] == 1


# -- the rule ---------------------------------------------------------------
def test_capacity_rule_cannot_round_a_failure_up(probe):
    runs = [_run(128, 0.95), _run(512, 0.96), _run(2048, 0.60)]
    # Deliberately unsorted input: the rule sorts by size, not by file order.
    got = probe.capacity_of([runs[1], runs[2], runs[0]])["small"]
    assert got["failed_sizes"] == [2048]
    assert got["stored_sizes"] == [128, 512]
    assert got["capacity"] == "between-512-and-2048"
    assert got["non_monotonic"] is False


def test_capacity_rule_does_not_smooth_a_non_monotonic_curve(probe):
    # 128 fails but 512 passes: the contiguous prefix ends at 128, so the
    # verdict says so and the inversion is flagged instead of ignored.
    got = probe.capacity_of([_run(128, 0.4), _run(512, 0.95)])["small"]
    assert got["capacity"] == "not-even-128"
    assert got["non_monotonic"] is True


def test_capacity_rule_names_the_two_edge_cases(probe):
    assert probe.capacity_of([_run(128, 0.2), _run(512, 0.3)])["small"]["capacity"] == (
        "not-even-128"
    )
    assert probe.capacity_of([_run(128, 0.95), _run(512, 0.99)])["small"]["capacity"] == (
        "at-least-512"
    )


def test_threshold_is_the_preregistered_one(probe):
    assert probe.STORED == 0.90


def test_effective_epochs_guarantee_the_step_floor(probe):
    # 128 rows / batch 32 = 4 steps per epoch: 8 epochs would be 32 steps.
    assert probe.effective_epochs(128, 32, 8, 800) == 200
    assert 4 * probe.effective_epochs(128, 32, 8, 800) >= 800
    # Larger N keeps its 8 epochs when that already clears the floor.
    assert probe.effective_epochs(4096, 32, 8, 800) == 8
    assert probe.effective_epochs(2048, 32, 8, 800) == 13
    assert 64 * probe.effective_epochs(2048, 32, 8, 800) >= 800


# -- --check ----------------------------------------------------------------
def test_check_accepts_a_consistent_report(probe):
    runs = [_run(128, 0.95), _run(512, 0.60)]
    report = {"runs": runs, "capacity": probe.capacity_of(runs)}
    assert probe.check_report(report) == []


def test_check_rejects_a_stored_flag_that_disagrees(probe):
    runs = [_run(128, 0.95)]
    runs[0]["stored"] = False
    report = {"runs": runs, "capacity": probe.capacity_of(runs)}
    problems = probe.check_report(report)
    assert any("stored flag" in p for p in problems)


def test_check_rejects_a_capacity_that_was_rounded_up(probe):
    runs = [_run(128, 0.50)]
    report = {"runs": runs, "capacity": {"small": {"capacity": "at-least-128"}}}
    problems = probe.check_report(report)
    assert any("recomputed" in p for p in problems)


def test_check_rejects_a_curve_shorter_than_the_epochs(probe):
    runs = [_run(128, 0.95, epochs=3)]
    runs[0]["curve"] = runs[0]["curve"][:2]
    report = {"runs": runs, "capacity": probe.capacity_of(runs)}
    problems = probe.check_report(report)
    assert any("curve points" in p for p in problems)


def test_check_rejects_an_empty_report(probe):
    assert probe.check_report({"runs": [], "capacity": {}}) == ["report has no runs"]


def test_build_report_keeps_the_arms_that_finished(probe):
    # A run stopped for budget/machine limits must keep its completed arms;
    # writing only at the end (the first version) lost them.
    env = {"train_rows": 1}
    protocol = {"stored_threshold": probe.STORED}
    first = probe.build_report(env, [_run(128, 0.95)], protocol)
    assert [r["size"] for r in first["runs"]] == [128]
    assert first["capacity"]["small"]["capacity"] == "at-least-128"
    second = probe.build_report(env, [_run(128, 0.95), _run(512, 0.40)], protocol)
    assert [r["size"] for r in second["runs"]] == [128, 512]
    assert second["capacity"]["small"]["capacity"] == "between-128-and-512"
    assert probe.check_report(second) == []
