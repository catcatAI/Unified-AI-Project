"""生成檔新鮮度門的合約測試。

WHY：`docs/STATUS_MATRIX.md`、`docs/PROJECT_MAP_GENERATED.md`、`scripts/INVENTORY.json`
都寫著「手不改，重跑覆蓋」，但不是每個都真的擋得住手改——專案地圖先前只被量行數，
手動補一句話完全看不出來。這裡守兩件事：

1. 登記的生成物與產生器沒漏（漏登記＝規則不存在）。
2. 正規化只吃掉「不是內容」的部分（日期、檔案大小、輪轉次數），手改的內容必定浮現。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_every_generated_artifact_is_registered():
    gate = _load("check_generated_docs")
    outputs = {t.output for t in gate.TARGETS}

    assert outputs == {
        "docs/STATUS_MATRIX.md",
        "docs/PROJECT_MAP_GENERATED.md",
        "scripts/INVENTORY.json",
    }
    for target in gate.TARGETS:
        assert target.generator.startswith("scripts/")
        assert target.source
        assert target.regenerate, f"{target.output} 沒有重算指令，就無法判斷是否被手改"


def test_dates_sizes_and_run_counts_are_not_content():
    gate = _load("check_generated_docs")
    a = "# 專案地圖（生成於 2026-11-08，9882 檔）\n- `AGENTS.md`（114KB，2026-11-09）\n"
    b = "# 專案地圖（生成於 2026-11-09，9884 檔）\n- `AGENTS.md`（115KB，2026-11-10）\n"

    assert gate._normalise(a, True) == gate._normalise(b, True)


def test_the_trend_section_is_runtime_bookkeeping():
    gate = _load("check_generated_docs")
    a = "## TREND\n\nruns: 20\nverdict: insufficient history\n"
    b = "## TREND\n\nruns: 0\nverdict: history disabled\n"

    assert gate._normalise(a, True) == gate._normalise(b, True)


def test_a_hand_written_line_still_shows_up():
    gate = _load("check_generated_docs")
    committed = "- `scripts/foo.py`\n- 手動補一句：這個檔案不該出現這行\n"
    produced = "- `scripts/foo.py`\n"

    assert gate._normalise(committed, True) != gate._normalise(produced, True)
    detail = gate._first_difference(committed, produced)
    assert "行數不同" in detail or "手動補一句" in detail


def test_first_difference_names_the_line():
    gate = _load("check_generated_docs")
    detail = gate._first_difference("a\nb\nc\n", "a\nB\nc\n")

    assert "第 2 行不同" in detail
    assert "b" in detail and "B" in detail
