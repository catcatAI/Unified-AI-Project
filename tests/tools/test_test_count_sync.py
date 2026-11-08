"""測試數量同步器「找不到目標就必須出聲」的合約測試。

WHY：`scripts/check_test_count.py` 存在的目的，是讓同一組數字不要散落在多份文件裡各自
老化。它先前把 AGENTS.md 那段的**換行**釘死在正則裡，而 `.prettierrc` 把 `*.md` 覆寫成
`proseWrap=always` / 寬 80——prettier 一跑（CI 門禁），正則就再也match不到，`_replace`
回 False，`--update` 照樣印 ✅。於是 AGENTS.md 停在 9,242、`docs/INVOCATION_MATRIX.md`
停在 8,143、`docs/status_matrix.yaml` 停在 8,802，而樹上實際是 9,248 / 10,010。

這裡守三件事：
1. 換行怎麼排都要找得到（換行不屬於語意）。
2. `tests/README.md` 的兩個引述處都要同步。
3. 找不到目標要進 `misses`（讓 `--update` 回 1），不能當成「無變更」。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"

MEASURED = {"tests": 9248, "ci": 9674, "full": 10010, "passed": 9910, "skipped": 100}


def _load(name: str):
    """Import a script by path (see tests/tools/test_native_dialogue_gates.py)."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="sync")
def _sync():
    return _load("check_test_count")


def _tree(root: Path, agents_note: str | None = None) -> Path:
    """A miniature repo holding every file the sync tool is supposed to write."""
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("AGENTS.md").write_text(
        agents_note
        or (
            "> 📌 **NOTE CHAIN IS A HISTORICAL CHANGELOG**\n>\n"
            "> that NOTE. The current authoritative count is **9,242 collected (tests/), 0\n"
            "> errors** (re-verified 2026-11-08; full testpaths\n"
            "> `pytest tests/ apps/backend/tests/ apps/game-rpg/tests/ scripts/`: **10,004\n"
            "> collected**, and `pytest tests/ apps/backend/tests/` = **9,561 passed / 107\n"
            "> skipped / 0 failed**).\n"
        ),
        encoding="utf-8",
    )
    readme = root / "tests" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "# Tests\n\n**9,242 tests collected** (tests/; re-verified 2026-11-08).\n"
        "\n## Current Test State\n\n"
        "**9,242 tests collected** (tests/; re-verified 2026-11-08 — same number).\n",
        encoding="utf-8",
    )
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    docs.joinpath("status_matrix.yaml").write_text(
        "  test_suite:\n"
        "    evidence: 8,802 passed, 112 skipped, 0 failed（2026-10-22 測試數量同步批次）\n"
        '    last_verified: "2026-10-22"\n',
        encoding="utf-8",
    )
    docs.joinpath("INVOCATION_MATRIX.md").write_text(
        "python -m pytest tests/ -q --timeout=120          # → 8,143 collected, 0 failed\n",
        encoding="utf-8",
    )
    return root


def _run(sync, root: Path):
    return sync.sync_docs(
        MEASURED["tests"],
        MEASURED["ci"],
        MEASURED["full"],
        MEASURED["passed"],
        MEASURED["skipped"],
        root=root,
    )


def test_every_quoted_number_is_rewritten(sync, tmp_path):
    root = _tree(tmp_path / "repo")
    changed, misses = _run(sync, root)

    assert misses == []
    assert set(changed) == {
        "AGENTS.md",
        "tests/README.md",
        "docs/status_matrix.yaml",
        "docs/INVOCATION_MATRIX.md",
    }
    agents = root.joinpath("AGENTS.md").read_text(encoding="utf-8")
    assert "9,248 collected (tests/)" in agents
    assert "10,010 collected / 9,910 passed / 100 skipped" in agents
    assert "9,242" not in agents
    assert agents.rstrip().endswith("0 failed).")  # bold closed before the period


def test_a_rewrapped_paragraph_is_still_found(sync, tmp_path):
    """prettier 的換行位置不是語意：任何一種排法都必須同步到。"""
    rewrapped = (
        "> that NOTE. The current authoritative count is\n"
        "> **9,242 collected (tests/), 0 errors**\n"
        "> (re-verified 2026-11-08; full testpaths\n"
        "> `pytest tests/ apps/backend/tests/ apps/game-rpg/tests/ scripts/`:\n"
        "> **10,004 collected / 9,561 passed / 107 skipped / 0 failed**).\n"
    )
    root = _tree(tmp_path / "repo", agents_note=rewrapped)
    _changed, misses = _run(sync, root)

    assert misses == []
    agents = root.joinpath("AGENTS.md").read_text(encoding="utf-8")
    assert "9,248" in agents and "10,004" not in agents


def test_both_readme_copies_are_synced(sync, tmp_path):
    root = _tree(tmp_path / "repo")
    _run(sync, root)

    readme = root.joinpath("tests", "README.md").read_text(encoding="utf-8")
    assert readme.count("9,248 tests collected") == 2
    assert "9,242" not in readme


def test_a_missing_sentence_is_reported_not_swallowed(sync, tmp_path):
    """沒有那段話時不能回「無變更」：那是本工具要消滅的靜默失敗。"""
    root = _tree(tmp_path / "repo", agents_note="> 這段話已經被改寫掉了。\n")
    changed, misses = _run(sync, root)

    assert "AGENTS.md" not in changed
    assert any("AGENTS.md" in miss for miss in misses)


def test_a_second_run_changes_nothing(sync, tmp_path):
    root = _tree(tmp_path / "repo")
    _run(sync, root)
    changed, misses = _run(sync, root)

    assert changed == [] and misses == []
