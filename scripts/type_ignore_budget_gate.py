#!/usr/bin/env python3
"""type:ignore 壓制棘輪門（R87）：鎖定 # type: ignore 數量上限，只能降不能升。

mypy budget 門已鎖定「未壓制錯誤=0」；本門鎖定「壓制注解總數」——每修一個真實
型別錯誤並移除對應 ignore，預算即下調。新增 ignore 必須同步上調預算並附理由。

機制：
- 掃 apps/backend/src/**/*.py 中含 `# type: ignore` 的行數
- 數 > 預算 → exit 1（禁新增）；< 預算 → exit 1（要求下調，棘輪轉緊）
  可用 --allow-lower 允許下降通過
- 用法：python scripts/type_ignore_budget_gate.py [--allow-lower] [--top N]
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUDGET_FILE = Path(__file__).resolve().parent / "type_ignore_budget.txt"
SRC = REPO_ROOT / "apps" / "backend" / "src"


def scan() -> tuple[int, list[str], Counter]:
    hits: list[str] = []
    codes: Counter = Counter()
    for p in SRC.rglob("*.py"):
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if "# type: ignore" in line:
                rel = p.relative_to(REPO_ROOT)
                hits.append(f"{rel}:{i}")
                m = re.search(r"# type: ignore\[([a-z-]+)\]", line)
                codes[m.group(1) if m else "(bare)"] += 1
    return len(hits), hits, codes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-lower", action="store_true")
    ap.add_argument("--top", action="store_true", help="按錯誤碼分佈")
    args = ap.parse_args()

    count, hits, codes = scan()
    budget = int(BUDGET_FILE.read_text(encoding="utf-8").strip().split()[0])

    if count > budget:
        print(f"❌ type:ignore {count} > 預算 {budget}：禁止新增壓制。")
        print("   若確需新增，請修好對應 mypy 錯誤後再評估，並上調預算附理由。")
        return 1
    if count < budget:
        if args.allow_lower:
            print(f"⚠️  type:ignore {count} < 預算 {budget}（允許下降）— 建議下調至 {count}")
            if args.top:
                for code, n in codes.most_common():
                    print(f"  [{code}] {n}")
            return 0
        print(
            f"❌ type:ignore {count} < 預算 {budget}：請下調 "
            f"scripts/type_ignore_budget.txt 至 {count}"
        )
        return 1
    print(f"✅ type:ignore 壓制預算鎖定（{count} = {budget}）")
    if args.top:
        for code, n in codes.most_common():
            print(f"  [{code}] {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
