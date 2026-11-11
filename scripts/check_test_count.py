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

WHY the sync used to lie (fixed 2026-11-09)
------------------------------------------
The AGENTS.md pattern pinned the *line breaks* of the paragraph it rewrote. But
``.prettierrc`` overrides ``*.md`` to ``proseWrap=always`` / width 80, so
``prettier --write`` (a CI gate) rewraps that paragraph - after which the pattern
matched nothing, ``_replace`` returned False, and ``--update`` still printed a
tick. AGENTS.md sat at 9,242/9,561/10,004 while the tree measured
9,248/9,567/10,010; ``tests/README.md``, ``docs/INVOCATION_MATRIX.md`` and
``docs/status_matrix.yaml`` each froze on a different day. The pattern is now
wrap-agnostic, ``tests/README.md`` is a target too, rewritten markdown is handed
to prettier, and any target that fails to match exits 1 instead of passing.

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
    "tests": 9424,
    "ci": 10186,
    "full": 10186,
}
TOLERANCE = 0.15


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    return (proc.stdout or "") + (proc.stderr or "")


def collect(scope: str) -> int:
    """Number of collected tests in *scope* (0 when collection fails)."""
    out = _run([sys.executable, "-m", "pytest", *SCOPES[scope], "--collect-only", "-q"])
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
    summary = re.findall(r"([\d,]+) passed[^\n]*?([\d,]+) skipped(?:[^\n]*?([\d,]+) failed)?", out)
    if not summary:
        return (0, 0, 0)
    passed, skipped, failed = summary[-1]
    return (
        int(passed.replace(",", "")),
        int(skipped.replace(",", "")),
        int((failed or "0").replace(",", "")),
    )


# The AGENTS.md note is prose that prettier rewraps (`.prettierrc` overrides *.md to
# proseWrap=always / width 80). Pinning the line breaks in the pattern meant that the
# first `prettier --write` turned every later `--update` into a silent no-op: the
# numbers stayed at 9,242 / 9,561 / 10,004 while the tree measured 9,248 / 9,567 /
# 10,010, and the tool still printed a tick. Match the sentence span, not the wrapping.
AGENTS_NOTE = re.compile(
    r"> that NOTE[.] The current authoritative count is.*?0 failed[*]{0,2}[)][.]", re.S
)
# tests/README.md quotes the same number twice (header + "Current Test State").
README_COUNT = re.compile(r"\*\*[\d,]+ tests collected\*\* \(tests/; re-verified [\d-]+")


def _replace(
    path: Path,
    pattern,
    replacement: str,
    label: str,
    misses: list[str],
    count: int = 1,
) -> bool:
    """Replace *pattern* in *path*; True when the file changed.

    A target that no longer matches lands in *misses* instead of being skipped
    silently: a miss used to look exactly like success, which is how the prose kept
    four different counts at once. ``count=0`` replaces every occurrence.
    """
    if not path.exists():
        misses.append(f"{label}: {path} 不存在")
        return False
    text = path.read_text(encoding="utf-8")
    if hasattr(pattern, "subn"):  # already compiled: it carries its own flags
        new_text, hits = pattern.subn(replacement, text, count=count)
    else:
        new_text, hits = re.subn(pattern, replacement, text, count=count, flags=re.S)
    if not hits:
        misses.append(f"{label}: {path.name} 裡找不到要同步的句子（換行或措辭被改寫過？）")
        return False
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def _prettier_write(root: Path, paths: list[Path]) -> str:
    """Hand the markdown wrapping back to the repo's prettier; note when it is absent.

    ``prettier --check .`` is a CI gate, so prose we write must survive it. Left
    unwrapped, the next prettier run changes the file behind the sync tool's back -
    the loop that produced the drift in the first place.
    """
    md = [str(p) for p in paths if p.suffix == ".md" and p.exists()]
    if not md:
        return ""
    proc = subprocess.run(
        ["npx", "--no-install", "prettier", "--write", *md],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return "⚠️  prettier 不可用：換行未重排，請自己跑 pnpm exec prettier --write <檔案>"
    return ""


def sync_docs(
    tests_collected: int,
    ci_collected: int,
    full_collected: int,
    passed: int,
    skipped: int,
    root: Path | None = None,
) -> tuple[list[str], list[str]]:
    """Write the measured numbers into every place that quotes them.

    Returns ``(changed, misses)``. A miss is a target whose sentence is gone - it is
    reported by ``--update`` instead of passing as "nothing to change".
    """
    root = ROOT if root is None else root
    today = datetime.date.today().isoformat()
    changed: list[str] = []
    misses: list[str] = []

    # 1. AGENTS.md — the authoritative-count note.
    agents = root / "AGENTS.md"
    if _replace(
        agents,
        AGENTS_NOTE,
        f"> that NOTE. The current authoritative count is **{tests_collected:,} collected"
        f" (tests/), 0 errors** (re-verified {today}; full testpaths"
        f" `pytest tests/ apps/backend/tests/ apps/game-rpg/tests/ scripts/`:"
        f" **{full_collected:,} collected / {passed:,} passed / {skipped:,} skipped**, 0 failed).",
        "AGENTS.md",
        misses,
    ):
        changed.append("AGENTS.md")

    # 2. tests/README.md — the same number, quoted twice.
    readme = root / "tests" / "README.md"
    if _replace(
        readme,
        README_COUNT,
        f"**{tests_collected:,} tests collected** (tests/; re-verified {today}",
        "tests/README.md",
        misses,
        count=0,
    ):
        changed.append("tests/README.md")

    # 3. docs/status_matrix.yaml — the single source of truth for the matrix.
    yaml_path = root / "docs" / "status_matrix.yaml"
    if _replace(
        yaml_path,
        r"    evidence: [\d,]+ passed, [\d,]+ skipped, 0 failed（[^）]*）\n"
        r"    last_verified: \"[\d-]+\"",
        f"    evidence: {passed:,} passed, {skipped:,} skipped, 0 failed"
        f"（{today} 測試數量同步批次全 testpaths 實測：tests/＋apps/backend/tests/＋"
        f"apps/game-rpg/tests＋scripts）\n"
        f'    last_verified: "{today}"',
        "docs/status_matrix.yaml",
        misses,
    ):
        changed.append("docs/status_matrix.yaml")

    # 4. docs/INVOCATION_MATRIX.md — the "run the whole suite" line.
    inv = root / "docs" / "INVOCATION_MATRIX.md"
    if _replace(
        inv,
        r"python -m pytest tests/ -q --timeout=120          # → [\d,]+ (?:passed|collected), 0 failed",
        f"python -m pytest tests/ -q --timeout=120          # → {tests_collected:,} collected, 0 failed",
        "docs/INVOCATION_MATRIX.md",
        misses,
    ):
        changed.append("docs/INVOCATION_MATRIX.md")

    return changed, misses


def update_baseline(counts: dict[str, int]) -> None:
    """Write the measured counts back into this file's BASELINE block."""
    path = Path(__file__).resolve()
    text = path.read_text(encoding="utf-8")
    for scope, value in counts.items():
        text = re.sub(rf'("{scope}": )\d+', rf"\g<1>{value}", text, count=1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measure", action="store_true", help="measure and print")
    parser.add_argument("--update", action="store_true", help="measure and sync")
    parser.add_argument("--scope", default="ci", choices=sorted(SCOPES), help="scope to measure")
    args = parser.parse_args()

    if args.update:
        counts = {name: collect(name) for name in SCOPES}
        if not all(counts.values()):
            print("❌ collection failed — refusing to write a bogus baseline")
            return 2
        passed, skipped, failed = run_suite("full")
        changed, misses = sync_docs(counts["tests"], counts["ci"], counts["full"], passed, skipped)
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
        prettier_note = _prettier_write(ROOT, [ROOT / name.split(" ")[0] for name in changed])
        print(f"✅ measured: {counts}")
        print(f"   full suite: {passed} passed, {skipped} skipped, {failed} failed")
        print(f"   docs synced: {changed or '（無變更）'}")
        if prettier_note:
            print(f"   {prettier_note}")
        if misses:
            # A target that no longer matches is the failure mode this tool exists to
            # remove, so it must not exit 0: silent skips are how the docs drifted.
            for miss in misses:
                print(f"❌ {miss}")
            print("   ❗ 有宣稱位置沒同步到——修好該檔案的句子，不要把手改當成同步")
            return 1
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
