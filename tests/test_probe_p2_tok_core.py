"""Contracts for scripts/probe_p2_tok_core.py (B1 coverage probe).

The probe reports correct/answered/n per suite; these tests pin the arithmetic
and the reading rules that keep "unreadable" separate from "wrong".
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "probe_p2_tok_core", REPO / "scripts" / "probe_p2_tok_core.py"
)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(probe)


def _row(**kw):
    base = {
        "id": "x",
        "suite": "math",
        "q": "2+2?",
        "gold": "4",
        "pred": "",
        "passed": False,
        "skipped": False,
        "answered": False,
        "prompt_tokens": 4,
        "prompt_unk": 0,
    }
    base.update(kw)
    return base


def _report(rows):
    suites = probe.summarize(rows)
    return {
        "scoring": "strict",
        "suites": suites,
        "totals": probe.totals(suites),
        "items": rows,
    }


def test_summarize_counts_each_suite_separately():
    rows = [
        _row(id="a", passed=True, answered=True),
        _row(id="b", answered=True, pred="5"),
        _row(id="c", suite="knowledge", answered=True, prompt_tokens=6, prompt_unk=2),
    ]
    got = probe.summarize(rows)
    assert got["math"] == {
        "n": 2,
        "correct": 1,
        "answered": 2,
        "prompt_tokens": 8,
        "prompt_unk": 0,
        "unk_share": 0.0,
    }
    assert got["knowledge"]["n"] == 1
    assert got["knowledge"]["unk_share"] == pytest.approx(2 / 6, abs=1e-4)


def test_summarize_of_nothing_is_empty():
    assert probe.summarize([]) == {}


def test_totals_sums_and_guards_division_by_zero():
    suites = probe.summarize([_row(prompt_tokens=0), _row(suite="knowledge", prompt_tokens=0)])
    total = probe.totals(suites)
    assert total["n"] == 2
    assert total["prompt_tokens"] == 0
    assert total["unk_share"] == 0.0


def test_check_accepts_a_consistent_report():
    report = _report([_row(passed=True, answered=True), _row(suite="knowledge")])
    assert probe.check_report(report) == []


def test_check_requires_strict_scoring():
    report = _report([_row()])
    report["scoring"] = "loose"
    assert "scoring must be strict" in probe.check_report(report)


def test_check_rejects_an_empty_report():
    report = _report([])
    assert probe.check_report(report) == ["report has no items"]


def test_check_catches_a_summary_that_disagrees_with_rows():
    report = _report([_row()])
    report["suites"]["math"]["n"] = 99
    assert "suite summary does not match the item rows" in probe.check_report(report)


def test_check_catches_totals_that_disagree_with_suites():
    report = _report([_row()])
    report["totals"]["correct"] = 5
    assert "totals do not match the suite summary" in probe.check_report(report)


def test_check_rejects_a_pass_with_an_empty_answer():
    # An empty generation cannot be a correct answer; if the scorer says it
    # passed, the report is lying about what the model produced.
    report = _report([_row(passed=True, answered=False)])
    assert any("passed with an empty answer" in p for p in probe.check_report(report))


def test_check_rejects_unk_above_token_count():
    report = _report([_row(prompt_tokens=3, prompt_unk=4)])
    assert any("unk count exceeds token count" in p for p in probe.check_report(report))


def test_check_cli_reads_and_validates_a_file(tmp_path, capsys):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(_report([_row(answered=True, pred="4")])), encoding="utf-8")
    assert probe.main(["--check", str(path)]) == 0
    assert "arithmetic agrees" in capsys.readouterr().out


def test_check_cli_fails_on_a_broken_file(tmp_path, capsys):
    path = tmp_path / "report.json"
    broken = _report([_row()])
    broken["scoring"] = "loose"
    path.write_text(json.dumps(broken), encoding="utf-8")
    assert probe.main(["--check", str(path)]) == 1
    assert "strict" in capsys.readouterr().out
