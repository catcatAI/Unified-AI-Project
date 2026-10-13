# =============================================================================
# ANGELA-MATRIX: L1 [γ] [A] [L0]
# =============================================================================
"""Regression tests for ``scripts/utils/process_test_results.py``.

Why this exists
---------------
The script used to be a placeholder: it logged ``"Processing test results..."``
and returned ``True`` without ever opening the file it was handed, so the CLI
exited **0** even when the path did not exist.  Anything wiring it into CI
would have read that as "results processed fine".

These tests pin the contract at both levels:

* the function -- unusable input (missing / malformed / wrong shape) returns
  ``False``; a real JUnit report is parsed and summarised;
* the CLI -- the documented ``main()`` interface exits non-zero for unusable
  input, which is the exit code the old version got wrong.

Hermetic: the module is loaded by explicit path (the repo's convention for
testing ``scripts/``), and every fixture is built under ``tmp_path``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "utils" / "process_test_results.py"

JUNIT_ONE_PASS_ONE_FAIL = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="2">
<testcase classname="tests.a" name="test_ok" time="0.01"/>
<testcase classname="tests.a" name="test_break" time="0.02"><failure message="boom">assert 1==2</failure></testcase>
</testsuite>
"""

JUNIT_ALL_PASS = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="2">
<testcase classname="tests.a" name="test_ok" time="0.01"/>
<testcase classname="tests.a" name="test_break" time="0.02"/>
</testsuite>
"""


def load_tool():
    spec = importlib.util.spec_from_file_location("process_test_results", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def tool():
    return load_tool()


@pytest.fixture()
def junit_file(tmp_path):
    def _write(name: str, content: str):
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    return _write


def test_missing_file_returns_false(tool, tmp_path):
    """The original defect: a missing input used to return True."""
    assert tool.process_test_results(results_file=str(tmp_path / "nope.xml")) is False


def test_malformed_input_returns_false(tool, junit_file):
    assert tool.process_test_results(results_file=junit_file("bad.json", "not json")) is False


def test_json_without_test_cases_returns_false(tool, junit_file):
    path = junit_file("shape.json", json.dumps({"foo": 1}))
    assert tool.process_test_results(results_file=path) is False


def test_empty_junit_returns_false(tool, junit_file):
    """A report with no testcases proves nothing, so it must not report success."""
    path = junit_file("empty.xml", "<testsuite name='pytest' tests='0'></testsuite>")
    assert tool.process_test_results(results_file=path) is False


def test_valid_junit_is_summarised(tool, junit_file):
    path = junit_file("cur.xml", JUNIT_ONE_PASS_ONE_FAIL)
    assert tool.process_test_results(results_file=path) is True

    loaded = tool._load_results(path)
    counts = tool._summarise(loaded)
    assert counts == {"total": 2, "passed": 1, "failed": 1, "skipped": 0, "pass_rate": 0.5}


def test_json_with_test_cases_is_accepted(tool, junit_file):
    payload = {
        "timestamp": "2026-10-13T00:00:00",
        "test_cases": [
            {"name": "test_ok", "module": "tests.a", "outcome": "passed"},
            {"name": "test_skip", "module": "tests.a", "outcome": "skipped"},
        ],
    }
    path = junit_file("cur.json", json.dumps(payload))
    assert tool.process_test_results(results_file=path) is True
    counts = tool._summarise(tool._load_results(path))
    assert counts["passed"] == 1 and counts["skipped"] == 1


def test_unknown_outcome_counts_as_failure(tool):
    """An unrecognised outcome must not be silently rounded up to 'passed'."""
    counts = tool._summarise({"test_cases": [{"name": "t", "module": "m", "outcome": "flaky?"}]})
    assert counts["failed"] == 1 and counts["passed"] == 0


def test_baseline_detects_regression_and_fix(tool, junit_file):
    baseline = junit_file("base.xml", JUNIT_ALL_PASS)
    current = junit_file("cur.xml", JUNIT_ONE_PASS_ONE_FAIL)

    regressions, fixed, new_tests = tool._compare_baseline(
        tool._load_results(current), tool._load_results(baseline)
    )
    assert regressions == ["tests.a::test_break"]
    assert fixed == [] and new_tests == []


def test_unusable_baseline_fails(tool, junit_file, tmp_path):
    current = junit_file("cur.xml", JUNIT_ONE_PASS_ONE_FAIL)
    ok = tool.process_test_results(
        results_file=current, baseline_file=str(tmp_path / "missing_baseline.xml")
    )
    assert ok is False


def test_send_email_without_recipients_fails(tool, junit_file):
    current = junit_file("cur.xml", JUNIT_ONE_PASS_ONE_FAIL)
    assert tool.process_test_results(results_file=current, send_email=True) is False


def test_cli_exit_codes(tmp_path):
    """The documented interface: unusable input must exit non-zero."""
    missing = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "absent.xml")],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert missing.returncode == 1, missing.stdout + missing.stderr

    good = tmp_path / "good.xml"
    good.write_text(JUNIT_ALL_PASS, encoding="utf-8")
    ok = subprocess.run(
        [sys.executable, str(SCRIPT), str(good)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "Passed:  2" in ok.stdout + ok.stderr
