#!/usr/bin/env python3
"""C901 複雜度棘輪門（R86）：鎖定超複雜函式上限，只能降不能升。

機制：
- flake8 主執行仍忽略 C901（維持 flake8=0 不紅），複雜度由本門獨立把關
- 讀 scripts/complexity_budget.txt 的預算（允許的 C901 > max-complexity 函式數）
- 以 repo 的 .flake8 排除項為基，額外強制 max-complexity=10 且不禁用 C901
- C901 數 > 預算 → exit 1（禁止新增）；< 預算 → exit 1（要求下調，棘輪轉緊）
  可用 --allow-lower 允許下降通過
- 用法：python scripts/complexity_budget_gate.py [--allow-lower] [--top N]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUDGET_FILE = Path(__file__).resolve().parent / "complexity_budget.txt"
DOT_FLAKE8 = REPO_ROOT / ".flake8"


def _load_flake8_excludes() -> list[str]:
    excludes: list[str] = []
    in_excludes = False
    for line in DOT_FLAKE8.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("exclude"):
            in_excludes = True
            _, _, val = s.partition("=")
            for part in val.split(","):
                part = part.strip()
                if part:
                    excludes.append(part)
            continue
        if in_excludes:
            if s and not s.startswith("#") and ("=" in s or s.startswith("[")):
                in_excludes = False
                continue
            part = s.rstrip(",").strip()
            if part and not part.startswith("#"):
                excludes.append(part)
    return excludes


def count_c901() -> tuple[int, str]:
    excludes = _load_flake8_excludes()
    # 建臨時設定：沿用 .flake8 的 exclude，但強制 max-complexity=10 且不禁用 C901
    with tempfile.NamedTemporaryFile("w", suffix=".flake8", delete=False) as f:
        f.write("[flake8]\n")
        f.write("max-line-length = 100\n")
        f.write("max-complexity = 10\n")
        f.write("exclude = " + ",".join(excludes) + "\n")
        # 其餘 ignore 全沿用，唯獨不放 C901
        f.write(
            "ignore = E203,W503,E501,F401,E402,F811,F841,E226,E228,W291,W292,W293,"
            "W391,E111,E117,E122,E123,E127,E128,E221,E231,E241,E261,E265,E301,E302,"
            "E303,E305,E306,E741,F405,E121,E126,E131,E731,W504,E701,E704\n"
        )
        cfg = f.name
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "flake8",
            "--config",
            cfg,
            "apps/backend/src",
            "tests/",
            "--select=C901",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    Path(cfg).unlink(missing_ok=True)
    out = proc.stdout
    lines = [ln for ln in out.splitlines() if "C901" in ln]
    return len(lines), out


def top_offenders(out: str, n: int) -> list[tuple[str, int, int]]:
    pat = re.compile(r"^(.*?):(\d+):\d+: C901 '(.+?)' is too complex \((\d+)\)")
    rows = []
    for ln in out.splitlines():
        m = pat.match(ln)
        if m:
            rows.append((m.group(1), int(m.group(2)), int(m.group(4))))
    rows.sort(key=lambda r: -r[2])
    return rows[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-lower", action="store_true")
    ap.add_argument("--top", type=int, default=0)
    args = ap.parse_args()

    count, out = count_c901()
    budget = int(BUDGET_FILE.read_text(encoding="utf-8").strip().split()[0])

    if count > budget:
        print(f"❌ C901 超複雜函式 {count} > 預算 {budget}：禁止新增複雜度。")
        if args.top:
            for path, line, cx in top_offenders(out, args.top):
                print(f"  {path}:{line}  complexity={cx}")
        return 1
    if count < budget:
        if args.allow_lower:
            print(f"⚠️  C901 {count} < 預算 {budget}（允許下降）— 建議下調預算至 {count}")
            return 0
        print(
            f"❌ C901 {count} < 預算 {budget}：棘輪只能轉緊，請下調 "
            f"scripts/complexity_budget.txt 至 {count}"
        )
        return 1
    print(f"✅ C901 複雜度預算鎖定（{count} = {budget}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
