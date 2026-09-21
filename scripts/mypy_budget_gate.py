#!/usr/bin/env python3
"""mypy 棘輪門（R74）：鎖定型別債上限，只能下降不能上升。

機制：
- 讀 scripts/mypy_budget.txt 的預算數字
- 跑 `mypy apps/backend/src` 統計 errors
- errors > 預算 → exit 1（CI 紅燈，禁止新增型別債）
- errors < 預算 → exit 1（要求把預算下調到實際值，棘輪只能轉緊）
  可用 --allow-lower 允許下降通過（本地收斂時用）
- errors == 預算 → exit 0

用法：
  python scripts/mypy_budget_gate.py                  # CI 嚴格門
  python scripts/mypy_budget_gate.py --allow-lower    # 本地收斂後檢查
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUDGET_FILE = Path(__file__).resolve().parent / "mypy_budget.txt"


def count_mypy_errors() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "mypy", "apps/backend/src"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Found ") and " errors " in line:
            # "Found 680 errors in 218 files (checked 684 source files)"
            try:
                return int(line.split()[1]), output
            except (IndexError, ValueError):
                break
    # 沒有 "Found N errors" 摘要行 → 可能全綠或被擋
    if "error" in output.lower():
        # errors prevented further checking 之類：視為失控，門檻直接紅
        return -1, output
    return 0, output


def main() -> int:
    parser = argparse.ArgumentParser(description="mypy ratchet budget gate")
    parser.add_argument("--allow-lower", action="store_true", help="允許 errors 低於預算時通過")
    args = parser.parse_args()

    budget = int(BUDGET_FILE.read_text().strip())
    actual, output = count_mypy_errors()

    if actual < 0:
        print("❌ mypy 全量檢查被擋（errors prevented further checking）——先修阻擋錯誤")
        print("\n".join(output.splitlines()[:10]))
        return 1

    print(f"mypy errors: {actual} ｜ budget: {budget}")
    if actual > budget:
        print(
            f"❌ 型別債上升（{budget} → {actual}）：禁止。修掉新增錯誤，或（僅限有充分理由時）人工上調 {BUDGET_FILE}"
        )
        return 1
    if actual < budget:
        if args.allow_lower:
            print(
                f"✅ 型別債下降（{budget} → {actual}）。請把 {BUDGET_FILE} 更新為 {actual} 以鎖定成果"
            )
            return 0
        print(
            f"⚠️ 型別債下降（{budget} → {actual}）：棘輪應轉緊——把 {BUDGET_FILE} 更新為 {actual} 後重新提交"
        )
        return 1
    print("✅ mypy budget gate passed（棘輪鎖定）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
