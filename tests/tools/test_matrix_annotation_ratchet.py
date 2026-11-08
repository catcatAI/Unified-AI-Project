"""ANGELA-MATRIX 標註棘輪測試。

WHY：AGENTS.md 把「新程式碼一律要 ANGELA-MATRIX 標註」寫成強制規範，但沒有任何東西
會因此變紅——現況約一半的檔案沒有標註（558／1103）。只要規則不會自己跳出來，下一個
AI 就不會遵循它，於是規範只活在文件裡。

棘輪的語意：未標註檔數只能減不能增。新增一個沒標註的檔案，總數就會超過預算而紅；
把檔案補上標註或刪掉，就能（且應該）把預算下調。
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
    text = (SCRIPTS / "matrix_annotation_budget.txt").read_text(encoding="utf-8")

    assert text.strip().isdigit(), f"預算必須是單一整數，實際是 {text!r}"


def test_budget_is_a_real_measurement_not_an_empty_ratchet():
    # 0 會讓「讀不到預算檔」與「全部都標註好了」無法區分。
    assert int((SCRIPTS / "matrix_annotation_budget.txt").read_text().strip()) > 0


def test_the_gate_reads_the_budget_file(gate, tmp_path, monkeypatch):
    budget = tmp_path / "matrix_annotation_budget.txt"
    budget.write_text("42\n", encoding="utf-8")
    monkeypatch.setattr(gate, "MATRIX_BUDGET", budget)

    assert gate._matrix_annotation_budget() == 42


def test_a_missing_budget_fails_closed(gate, tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "MATRIX_BUDGET", tmp_path / "nope.txt")

    assert gate._matrix_annotation_budget() == 0


def test_the_scopes_are_production_and_tooling(gate):
    # 只掃這兩棵：測試與前端不屬於「新程式碼要標註」的守備範圍。
    assert set(gate.MATRIX_SCOPES) == {"apps/backend/src", "scripts"}
