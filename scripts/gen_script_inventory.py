#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
"""
gen_script_inventory.py — 產生 scripts/ 的清單（每支腳本的類別與用途）

WHY this exists
---------------
The gap-closure plan listed "69 孤兒腳本逐個定級（留/刪/歸檔）" as open work:
scripts/ has grown to ~200 files and a large part of them are referenced
nowhere — research one-offs, old experiments, and tools that drifted.

Nobody could tell which was which, so the item stayed open. This tool writes
the inventory (``scripts/INVENTORY.json``): every script gets a category and
a one-line purpose (its own docstring), and the category says whether the
script is *reachable* (referenced by a doc, a workflow or the code) or a
*one-off* (kept as a research record, referenced nowhere).

The inventory is verified by ``tests/tools/test_script_inventory.py``, so a
new orphan cannot appear silently.

Usage
    python3 scripts/gen_script_inventory.py            # write the inventory
    python3 scripts/gen_script_inventory.py --check    # verify only
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
INVENTORY = SCRIPTS_DIR / "INVENTORY.json"
# ACTIVE_SCRIPTS.md 不是產生檔，但它引用了三個「由清單算出來」的數字（總數／被引用／
# 未被引用）。那三個數字原本要靠人記得同步：寫下 219 支時，scripts/ 已經有 275 支。
# 所以這兩個數字跟 INVENTORY 同一個機制寫入、同一個 --check 驗證。
ACTIVE = SCRIPTS_DIR / "ACTIVE_SCRIPTS.md"
COUNT_PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"(?<=目前有 )\d+(?= 支腳本)"), 0),
    (re.compile(r"(?<=指向它）：)\d+(?= 支)"), 1),
    (re.compile(r"(?<=作為紀錄）：)\d+(?= 支)"), 2),
)

# Category rules: the first matching prefix wins.
CATEGORY_RULES: list[tuple[str, str]] = [
    ("benchmark_", "benchmark"),
    ("bench_", "benchmark"),
    ("probe_", "probe"),
    ("train_", "training"),
    ("validate_", "validation"),
    ("verify_", "verification"),
    ("check_", "diagnostics"),
    ("audit_", "diagnostics"),
    ("gen_", "generation"),
    ("generate_", "generation"),
    ("update_", "maintenance"),
    ("fix_", "maintenance"),
    ("migrate_", "maintenance"),
    ("sync_", "maintenance"),
    ("backup_", "maintenance"),
    ("cleanup_", "maintenance"),
    ("run_", "operations"),
    ("start_", "operations"),
    ("stop_", "operations"),
    ("restart_", "operations"),
    ("build_", "operations"),
    ("test_", "testing"),
    ("analyze_", "analysis"),
    ("report_", "analysis"),
    ("show_", "analysis"),
    ("inspect_", "analysis"),
    ("trace_", "analysis"),
    ("quick_", "experimental"),
    ("phase", "experimental"),
    ("perceptual_", "experimental"),
    ("snn_", "experimental"),
    ("scale_", "experimental"),
    ("rescale_", "experimental"),
    ("revert_", "experimental"),
    ("rebuild_", "experimental"),
    ("sharpness_", "experimental"),
    ("terminal_", "experimental"),
    ("mvu_", "experimental"),
    ("three_layer_", "experimental"),
    ("next_phase_", "experimental"),
    ("compositional", "experimental"),
    ("learnable_", "experimental"),
]

DEFAULT_CATEGORY = "tool"

# Where a script is "reachable from": the files whose text is searched for
# the script's name.
REFERENCE_GLOBS = (
    "*.md",
    ".github/workflows/*.yml",
    "docs/**/*.md",
    "apps/backend/src/**/*.py",
    "apps/backend/tests/**/*.py",
    "tests/**/*.py",
    "packages/**/*.py",
)


def _script_files() -> list[Path]:
    return sorted(
        p for p in SCRIPTS_DIR.iterdir() if p.suffix == ".py" and p.name != Path(__file__).name
    )


def _purpose(path: Path) -> str:
    """The script's one-line purpose.

    The module docstring, else the first comment, else the docstring of its
    first function, else a name-derived description — the inventory should
    never have a blank entry.
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return ""
    doc = ast.get_docstring(tree)
    if doc:
        first = next((line.strip() for line in doc.splitlines() if line.strip()), "")
        if first:
            return first[:160]
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and len(stripped) > 3:
            return stripped.lstrip("# ").strip()[:160]
    first = _first_function_doc(tree)
    if first:
        return first[:160]
    # Last resort: a name-derived description.
    stem = path.stem.replace("_", " ").strip()
    return f"{stem}（無說明：原始碼未附 docstring）"[:160]


def _first_function_doc(tree: ast.Module) -> str:
    """The first line of the first function's docstring (empty when none)."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fdoc = ast.get_docstring(node)
            if fdoc:
                return next((line.strip() for line in fdoc.splitlines() if line.strip()), "")
    return ""


def _category(name: str) -> str:
    for prefix, category in CATEGORY_RULES:
        if name.startswith(prefix):
            return category
    return DEFAULT_CATEGORY


def _reference_blob() -> str:
    chunks = []
    for pattern in REFERENCE_GLOBS:
        for path in ROOT.glob(pattern):
            try:
                chunks.append(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
    return "\n".join(chunks)


def build_inventory() -> dict:
    blob = _reference_blob()
    inventory = {}
    for path in _script_files():
        name = path.name
        referenced = name in blob
        inventory[name] = {
            "category": _category(name),
            "referenced": referenced,
            "purpose": _purpose(path),
        }
    return inventory


def _counts(inventory: dict) -> tuple[int, int, int]:
    total = len(inventory)
    referenced = sum(1 for v in inventory.values() if v["referenced"])
    return total, referenced, total - referenced


def sync_active_scripts_counts(text: str, inventory: dict) -> str:
    """把 ACTIVE_SCRIPTS.md 裡三個可推導的數字改成實際值。"""
    numbers = _counts(inventory)
    for pattern, index in COUNT_PATTERNS:
        # lookaround 只圈住數字，前後關鍵字原封不動（所以不用 group）。
        text = pattern.sub(str(numbers[index]), text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only")
    args = parser.parse_args()

    inventory = build_inventory()
    payload = {
        "version": 1,
        "note": (
            "每支 scripts/*.py 的類別與用途；referenced=false 表示除了本清單以外"
            "沒有任何文件、工作流程或程式引用它（研究一次性腳本，保留作為紀錄）。"
        ),
        "scripts": inventory,
    }

    if args.check:
        if not INVENTORY.exists():
            print(f"❌ {INVENTORY} missing")
            return 1
        current = json.loads(INVENTORY.read_text(encoding="utf-8"))
        if current.get("scripts") != inventory:
            missing = sorted(set(inventory) - set(current.get("scripts", {})))
            extra = sorted(set(current.get("scripts", {})) - set(inventory))
            changed = [
                name
                for name in set(inventory) & set(current.get("scripts", {}))
                if current["scripts"][name] != inventory[name]
            ]
            print("❌ the inventory is stale:")
            if missing:
                print(f"   new scripts: {missing}")
            if extra:
                print(f"   removed scripts: {extra}")
            if changed:
                print(f"   changed entries: {sorted(changed)}")
            return 1
        if ACTIVE.exists():
            text = ACTIVE.read_text(encoding="utf-8")
            expected = sync_active_scripts_counts(text, inventory)
            if text != expected:
                total, referenced, unreferenced = _counts(inventory)
                print("❌ ACTIVE_SCRIPTS.md 的計數過期（它引用了由清單推導的數字）")
                print(
                    f"   實際：{total} 支腳本，{referenced} 被引用，"
                    f"{unreferenced} 未被引用——跑 `python3 scripts/gen_script_inventory.py` 同步"
                )
                return 1
        print(f"✅ inventory current ({len(inventory)} scripts)")
        return 0

    INVENTORY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    orphans = [n for n, v in inventory.items() if not v["referenced"]]
    if ACTIVE.exists():
        text = ACTIVE.read_text(encoding="utf-8")
        ACTIVE.write_text(sync_active_scripts_counts(text, inventory), encoding="utf-8")
    print(f"✅ wrote {INVENTORY} ({len(inventory)} scripts, {len(orphans)} unreferenced)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
