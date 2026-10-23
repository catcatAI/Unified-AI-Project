"""The control probe must not confuse "answered wrongly" with "did not answer"."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_core_control.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("probe_core_control_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cell(passed: bool = False, answered: bool = True, answer: str = "x") -> dict:
    return {
        "answer": answer if answered else "",
        "answered": answered,
        "passed": passed and answered,
        "skipped": False,
    }


def _rows(producer_cells: list) -> dict:
    suite_rows = []
    for index, cells in enumerate(producer_cells):
        row = {"id": f"i{index}", "suite": "math", "q": "q"}
        row.update(cells)
        suite_rows.append(row)
    return {"math": suite_rows}


def test_empty_answers_are_abstentions_not_wrong_answers(probe):
    rows = _rows(
        [
            {name: _cell(passed=(name == "performance")) for name in probe.PRODUCERS}
            | {"snn": _cell(passed=False, answered=False)}
            for _ in range(3)
        ]
    )
    cell = probe._summarize(rows)["math"]
    assert cell["snn"] == 0.0  # the old rule: an abstention is not correct
    assert cell["coverage"]["snn"] == 0.0  # ...but it is visibly not an answer
    assert cell["accuracy_answered"]["snn"] is None
    assert cell["answered"]["snn"] == 0
    assert cell["coverage"]["performance"] == 1.0


def test_accuracy_answered_differs_when_some_answers_are_empty(probe):
    rows = _rows(
        [
            {
                "llm": _cell(passed=True, answer="a"),
                **{n: _cell() for n in probe.PRODUCERS if n != "llm"},
            },
            {
                "llm": _cell(passed=False, answer="b"),
                **{n: _cell() for n in probe.PRODUCERS if n != "llm"},
            },
            {
                "llm": _cell(passed=False, answered=False),
                **{n: _cell() for n in probe.PRODUCERS if n != "llm"},
            },
        ]
    )
    cell = probe._summarize(rows)["math"]
    assert cell["llm"] == pytest.approx(1 / 3)
    assert cell["accuracy_answered"]["llm"] == pytest.approx(1 / 2)
    assert cell["coverage"]["llm"] == pytest.approx(2 / 3)


def test_distinct_answers_detects_collapse(probe):
    rows = _rows([{n: _cell(answer="何为") for n in probe.PRODUCERS} for _ in range(4)])
    cell = probe._summarize(rows)["math"]
    assert cell["distinct"]["ed3n"] == 1


def test_gaps_are_reported_for_every_core_backend(probe):
    rows = _rows(
        [
            {
                "llm": _cell(passed=True, answer="a"),
                **{n: _cell() for n in probe.PRODUCERS if n != "llm"},
            },
            {
                "llm": _cell(passed=True, answer="b"),
                **{n: _cell() for n in probe.PRODUCERS if n != "llm"},
            },
        ]
    )
    cell = probe._summarize(rows)["math"]
    assert cell["gaps"] == {"snn": 2, "ed3n": 2, "tok": 2}
    assert cell["snn_gap"] == 2
