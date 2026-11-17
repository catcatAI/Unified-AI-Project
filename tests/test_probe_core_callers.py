# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§89's contract is the decision rule, not the scores.

The registered rule (``CORE_GAP_ANALYSIS.md`` §89.5) asks two questions and
introduces no tunable number:

* Q2: does the production producer (``TokenSNN.generate``) reproduce §88's
  published ``exact_raw`` count of 28 on the 248-row hold-out?
* Q1: is the core score's 0.00 true of every loadable checkpoint (``core-gap``)
  or only of the checkpoint the report cites (``checkpoint-selection``)?

What is tested here:

* the four registered suite checkpoints and the one hold-out arm, and that the
  65 frozen items still hash to the registered digest;
* the hold-out rows still hash to §88's digest (the two stages measure the same
  rows, in the same order);
* the branch table, including the case where the cited checkpoint is also
  non-zero (that is still ``checkpoint-selection`` by the registration's order);
* that ``skipped`` is not folded into ``passed``;
* ``--check`` refuses a report from another stage.

No checkpoint is loaded and no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_callers.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_core_callers_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_core_callers_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


# -- registration -----------------------------------------------------------
def test_registered_arms_and_checkpoints(probe):
    assert probe.ARMS == (
        "distill_suites",
        "default_suites",
        "core149k_suites",
        "m108_suites",
        "holdout_generate",
    )
    assert probe.ARM_SPECS["holdout_generate"]["kind"] == "holdout"
    assert all(
        probe.ARM_SPECS[name]["kind"] == "suites"
        for name in probe.ARMS
        if name != "holdout_generate"
    )
    assert {probe.ARM_SPECS[name]["checkpoint"].name for name in probe.ARMS} == {
        "token_snn_distill.pt",
        "token_snn.pt",
        "token_snn_core149k.pt",
        "token_snn_108m.pt",
    }


def test_frozen_items_are_the_registered_ones(probe):
    items = probe._registered_items()
    assert len(items) == 65
    assert [item.suite for item in items].count("math") == 40
    assert [item.suite for item in items].count("knowledge") == 15
    assert [item.suite for item in items].count("code") == 10
    assert probe.items_digest([item.id for item in items]) == probe.ITEMS_DIGEST
    assert probe.ITEMS_DIGEST == "f67a454de8594115"


def test_holdout_rows_are_section_88_rows(probe):
    pairs = probe.read_pairs(probe.HOLDOUT)
    assert len(pairs) == 248
    assert probe.rows_digest(pairs) == probe.EXPECTED_HOLDOUT_DIGEST
    assert probe.EXPECTED_HOLDOUT_EXACT == 28


# -- the decision rule ------------------------------------------------------
@pytest.mark.parametrize(
    "counts, expected",
    [
        (
            {"distill_suites": 0, "default_suites": 0, "core149k_suites": 0, "m108_suites": 0},
            "core-gap",
        ),
        (
            {"distill_suites": 3, "default_suites": 0, "core149k_suites": 0, "m108_suites": 0},
            "checkpoint-selection",
        ),
        (
            {"distill_suites": 0, "default_suites": 1, "core149k_suites": 0, "m108_suites": 0},
            "checkpoint-selection",
        ),
        (
            {"distill_suites": 0, "default_suites": 0, "core149k_suites": 0, "m108_suites": 2},
            "single-checkpoint",
        ),
        # Registration order: "at least one non-zero that is not the cited
        # checkpoint" wins even when the cited one also moved.
        (
            {"distill_suites": 1, "default_suites": 0, "core149k_suites": 0, "m108_suites": 2},
            "checkpoint-selection",
        ),
    ],
)
def test_q1_verdict_branches(probe, counts, expected):
    assert probe.q1_verdict(counts) == expected


@pytest.mark.parametrize(
    "exact, expected",
    [
        (28, "caller-consistent"),
        (27, "caller-mismatch"),
        (0, "caller-mismatch"),
        (30, "caller-mismatch"),
    ],
)
def test_q2_verdict_is_equality_not_an_interval(probe, exact, expected):
    assert probe.q2_verdict(exact) == expected


# -- aggregates -------------------------------------------------------------
def test_suite_aggregate_does_not_fold_skipped_into_passed(probe):
    rows = [
        {
            "suite": "math",
            "passed": True,
            "answered": True,
            "skipped": False,
            "unreadable": False,
            "truncated": False,
            "answer": "1",
        },
        {
            "suite": "math",
            "passed": False,
            "answered": True,
            "skipped": True,
            "unreadable": False,
            "truncated": False,
            "answer": "",
        },
        {
            "suite": "knowledge",
            "passed": False,
            "answered": True,
            "skipped": False,
            "unreadable": True,
            "truncated": False,
            "answer": "x",
        },
    ]
    aggregate = probe._aggregate_suites(rows)
    assert aggregate["n"] == 3
    assert aggregate["passed"] == 1
    assert aggregate["skipped"] == 1
    assert aggregate["unreadable"] == 1
    assert aggregate["math"] == 1
    assert aggregate["knowledge"] == 0
    assert aggregate["by_suite"]["math"]["distinct"] == 2


def test_holdout_aggregate_counts_raw_string_equality(probe):
    rows = [
        {
            "exact_raw": True,
            "answered": True,
            "unreadable": False,
            "truncated": False,
            "answer": "a",
        },
        {"exact_raw": False, "answered": True, "unreadable": True, "truncated": True, "answer": ""},
    ]
    aggregate = probe._aggregate_holdout(rows)
    assert aggregate["n"] == 2
    assert aggregate["exact_raw"] == 1
    assert aggregate["distinct"] == 2
    assert aggregate["truncated"] == 1
    assert aggregate["truncation_rate"] == 0.5


def test_aggregates_survive_the_json_round_trip(probe):
    rows = [
        {
            "suite": "code",
            "passed": True,
            "answered": True,
            "skipped": False,
            "unreadable": False,
            "truncated": False,
            "answer": "def f(): pass",
        },
    ]
    aggregate = probe._aggregate_suites(rows)
    assert probe._canonical(aggregate) == aggregate


# -- truncation rule --------------------------------------------------------
def test_truncation_rule_is_registered_at_five_percent(probe):
    assert probe.MAX_TRUNCATION == 0.05
    assert probe.MAX_NEW == 48
    assert probe.MAX_SECONDS == 1200.0


def test_truncation_checks_prompt_plus_structural_tokens(probe):
    class _Vocab:
        @staticmethod
        def encode(_prompt):
            return [1] * 143

    class _Config:
        max_len = 192

    class _Model:
        vocab = _Vocab
        config = _Config

    # 143 + [BOS] + [NL] = 145 <= 191: the prompt survives.
    assert probe._truncated(_Model, "q") is False

    _Vocab.encode = staticmethod(lambda _prompt: [1] * 190)
    # 190 + 2 = 192 > 191: generate() will clip before decoding.
    assert probe._truncated(_Model, "q") is True


# -- check ------------------------------------------------------------------
def test_check_refuses_a_foreign_report(probe, tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"stage": "§88", "arms": {}}), encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False
    assert "§89" in message
