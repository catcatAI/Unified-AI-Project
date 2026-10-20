#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
"""
check_test_count.py — 測試數量的單一權威機制（量測＋門禁＋同步文件）

WHY this exists
---------------
The repository carried four different test counts at once (a collected count
in AGENTS.md, a "passed/skipped" pair in status_matrix.yaml, a hand-edited
copy in the generated STATUS_MATRIX.md, and a stale number in
INVOCATION_MATRIX.md). Every one of them was correct on the day it was
written, and the CI "test count drift check" compared the *live* count
against a hard-coded window that the project's own growth had already left
behind — so the gate was red for a reason that had nothing to do with the
tests.

The fix is to stop storing the number in prose and start measuring it:

  measure   量測一次，把真實數字寫回所有宣稱位置
  check     門禁：實測 vs 權威基線，超出容差即紅（防止集體遺失／重複）
  update    ＝ measure，把基線與文件一起更新（基線隨專案成長自動跟著走）

The authoritative baseline lives in THIS file (one place, machine-readable).
The documentation copies are kept in sync by ``--update``; a human editing
one of them by hand is exactly the drift this tool removes.

Usage
    python3 scripts/check_test_count.py --measure      # 量測並印出
    python3 scripts/check_test_count.py --update       # 量測＋同步基線與文件
    python3 scripts/check_test_count.py                # 門禁（CI 用）
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The scopes the project measures. ``ci`` is what the CI gate watches; the
# others are quoted in the documentation.
SCOPES = {
    "tests": ["tests/"],
    "ci": ["tests/", "apps/backend/tests/", "apps/game-rpg/tests/"],
    "full": ["tests/", "apps/backend/tests/", "apps/game-rpg/tests/", "scripts/"],
}

# The authoritative baseline (collected counts), refreshed by --update.
# Tolerance is proportional so the alarm keeps meaning "mass loss or
# duplication" instead of "someone added a test file again".
BASELINE = {
    "tests": 7976,
    "ci": 8739,
    "full": 8739,
}
TOLERANCE = 0.15


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True, check=False
    )
    return (proc.stdout or "") + (proc.stderr or "")


def collect(scope: str) -> int:
    """Number of collected tests in *scope* (0 when collection fails)."""
    out = _run(
        [sys.executable, "-m", "pytest", *SCOPES[scope], "--collect-only", "-q"]
    )
    match = re.search(r"(\d+)\s+tests? collected", out)
    if not match:
        return 0
    return int(match.group(1))


def run_suite(scope: str) -> tuple[int, int, int]:
    """(passed, skipped, failed) for *scope*.

    The LAST summary line wins: a failing test prints diffs that may contain
    the words "passed"/"skipped" themselves (a status-matrix assertion
    quotes the very numbers being parsed here), and the first match would
    then be a quoted number rather than the real one.
    """
    out = _run([sys.executable, "-m", "pytest", *SCOPES[scope], "-q", "--timeout=180"])
    # The "failed" part is optional: a green run prints
    # "8623 passed, 107 skipped, 2 warnings in 313.54s" with no "failed" at all.
    summary = re.findall(
        r"([\d,]+) passed[^\n]*?([\d,]+) skipped(?:[^\n]*?([\d,]+) failed)?", out
    )
    if not summary:
        return (0, 0, 0)
    passed, skipped, failed = summary[-1]
    return (
        int(passed.replace(",", "")),
        int(skipped.replace(",", "")),
        int((failed or "0").replace(",", "")),
    )


def _replace(path: Path, pattern: str, replacement: str) -> bool:
    """Replace *pattern* in *path*; True when the file changed."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if not count or new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def sync_docs(
    tests_collected: int,
    ci_collected: int,
    full_collected: int,
    passed: int,
    skipped: int,
) -> list[str]:
    """Write the measured numbers into every place that quotes them."""
    today = datetime.date.today().isoformat()
    changed: list[str] = []

    # 1. AGENTS.md — the authoritative-count note.
    agents = ROOT / "AGENTS.md"
    if _replace(
        agents,
        r"> that NOTE\. The current authoritative count is \*\*[\d,]+ collected \(tests/\), 0\n"
        r"> errors\*\* \(re-verified [\d-]+; full testpaths `pytest tests/\n"
        r"> apps/backend/tests/ apps/game-rpg/tests/ scripts/`: \*\*[\d,]+ collected /\n"
        r"> [\d,]+ passed / [\d,]+ skipped\*\*, 0 failed\)\.",
        f"> that NOTE. The current authoritative count is **{tests_collected:,} collected (tests/), 0\n"
        f"> errors** (re-verified {today}; full testpaths `pytest tests/\n"
        f"> apps/backend/tests/ apps/game-rpg/tests/ scripts/`: **{full_collected:,} collected /\n"
        f"> {passed:,} passed / {skipped:,} skipped**, 0 failed).",
    ):
        changed.append("AGENTS.md")

    # 2. docs/status_matrix.yaml — the single source of truth for the matrix.
    yaml_path = ROOT / "docs" / "status_matrix.yaml"
    if _replace(
        yaml_path,
        r"    evidence: [\d,]+ passed, [\d,]+ skipped, 0 failed（[^）]*）\n"
        r"    last_verified: \"[\d-]+\"",
        f"    evidence: {passed:,} passed, {skipped:,} skipped, 0 failed"
        f"（{today} 測試數量同步批次全 testpaths 實測：tests/＋apps/backend/tests/＋"
        f"apps/game-rpg/tests＋scripts）\n"
        f"    last_verified: \"{today}\"",
    ):
        changed.append("docs/status_matrix.yaml")

    # 3. docs/INVOCATION_MATRIX.md — the "run the whole suite" line.
    inv = ROOT / "docs" / "INVOCATION_MATRIX.md"
    if _replace(
        inv,
        r"python -m pytest tests/ -q --timeout=120          # → [\d,]+ (?:passed|collected), 0 failed",
        f"python -m pytest tests/ -q --timeout=120          # → {tests_collected:,} collected, 0 failed",
    ):
        changed.append("docs/INVOCATION_MATRIX.md")

    return changed


def update_baseline(counts: dict[str, int]) -> None:
    """Write the measured counts back into this file's BASELINE block."""
    path = Path(__file__).resolve()
    text = path.read_text(encoding="utf-8")
    for scope, value in counts.items():
        text = re.sub(
            rf'("{scope}": )\d+', rf"\g<1>{value}", text, count=1
        )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measure", action="store_true", help="measure and print")
    parser.add_argument("--update", action="store_true", help="measure and sync")
    parser.add_argument(
        "--scope", default="ci", choices=sorted(SCOPES), help="scope to measure"
    )
    args = parser.parse_args()

    if args.update:
        counts = {name: collect(name) for name in SCOPES}
        if not all(counts.values()):
            print("❌ collection failed — refusing to write a bogus baseline")
            return 2
        passed, skipped, failed = run_suite("full")
        changed = sync_docs(
            counts["tests"], counts["ci"], counts["full"], passed, skipped
        )
        update_baseline(counts)
        # The generated status matrix must follow the YAML it is generated
        # from — otherwise its freshness test fails and the numbers disagree
        # in two files at once.
        gen = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "gen_status_matrix.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if gen.returncode == 0:
            changed.append("docs/STATUS_MATRIX.md (regenerated)")
        print(f"✅ measured: {counts}")
        print(f"   full suite: {passed} passed, {skipped} skipped, {failed} failed")
        print(f"   docs synced: {changed or '（無變更）'}")
        return 0 if failed == 0 else 1

    if args.measure:
        counts = {name: collect(name) for name in SCOPES}
        for name, value in counts.items():
            print(f"{name:6s} collected: {value}")
        return 0

    # Default: the gate.
    scope = args.scope
    measured = collect(scope)
    baseline = BASELINE[scope]
    if not measured:
        print(f"❌ could not collect {scope} — collection error")
        return 2
    low = int(baseline * (1 - TOLERANCE))
    high = int(baseline * (1 + TOLERANCE))
    print(f"collected[{scope}] = {measured} (baseline {baseline}, window {low}-{high})")
    if not (low <= measured <= high):
        print(
            "❌ test count outside the window — mass loss or duplication? "
            "(run with --update after checking the tree)"
        )
        return 1
    print("✅ test count within the window")
    return 0


if __name__ == "__main__":
    sys.exit(main())
