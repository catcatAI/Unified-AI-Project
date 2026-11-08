"""定義多重釋義的棘輪（ambiguity budget）測試。

WHY：多重釋義原本是 INFO——也就是說它可以一直長，而沒有任何門會因此變紅。
11 條就是這樣累積出來的。棘輪的語意是「只減不增」：要新增，必須同時上調
`scripts/ambiguity_budget.txt` 並說明理由，否則門禁紅。

這裡守三件事：
1. 預算檔是單一整數（不是散文，不會被寫成「約 10 條」）。
2. 門禁真的讀這個檔（不是把數字抄在程式裡）。
3. 檔案讀不到時回 0（fail-closed），而不是默默放行。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="gate")
def _gate():
    return _load("check_fact_gates")


def test_budget_file_is_a_single_integer():
    text = (SCRIPTS / "ambiguity_budget.txt").read_text(encoding="utf-8")

    assert text.strip().isdigit(), f"預算必須是單一整數，實際是 {text!r}"


def test_the_gate_reads_the_budget_file(gate, tmp_path, monkeypatch):
    budget = tmp_path / "ambiguity_budget.txt"
    budget.write_text("7\n", encoding="utf-8")
    monkeypatch.setattr(gate, "AMBIGUITY_BUDGET", budget)

    assert gate._ambiguity_budget() == 7


def test_a_missing_budget_fails_closed(gate, tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "AMBIGUITY_BUDGET", tmp_path / "nope.txt")

    assert gate._ambiguity_budget() == 0


def test_a_corrupt_budget_fails_closed(gate, tmp_path, monkeypatch):
    budget = tmp_path / "ambiguity_budget.txt"
    budget.write_text("大約十條\n", encoding="utf-8")
    monkeypatch.setattr(gate, "AMBIGUITY_BUDGET", budget)

    assert gate._ambiguity_budget() == 0
