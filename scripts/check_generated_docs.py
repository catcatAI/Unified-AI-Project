#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [γ] [C] [L0]
# =============================================================================
"""生成檔新鮮度門：手改生成物 → 紅燈，指名該跑哪個產生器。

WHY this exists
---------------
倉庫有三個由程式產生的檔案，AGENTS.md 也寫了「生成檔不要手改」，但規則從來
沒有自己跳出來過：

- ``docs/STATUS_MATRIX.md``：CI 有 check＋freshness，這一個是守著的。
- ``docs/PROJECT_MAP_GENERATED.md``：CI 只檢查**行數預算**（≤10000）。手改一行
  完全看不出來，而且它是最容易被「順手補一句」的那種檔。
- ``scripts/INVENTORY.json``：``--check`` 模式早就寫好了，但沒有接進 CI／
  pre-commit，等於不存在。

「規則不會自己跳出來，就沒有 AI 會遵循」——所以把三者收成單一入口：任何一個
生成物與產生器的輸出不一致，就 exit 1，並把「改來源」與「跑哪個指令」寫在同一
行。手改不是風格問題：手改的內容下一次重跑就消失，等於把事實寫進會被沖掉的地方。

Usage
    python scripts/check_generated_docs.py           # 門禁（CI／pre-commit）
    python scripts/check_generated_docs.py --fix     # 就地重跑三個產生器
    python scripts/check_generated_docs.py --list    # 印出登記的生成物

Notes
- 專案地圖的標題行帶當天日期（``生成於 2026-11-08``），所以比對前先把
  YYYY-MM-DD 一律換成 ``<date>``：日期不是內容，內容才是。
- 產生器一律寫到暫存檔再比對，門禁本身不改動工作區。
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass
class Generated:
    """一個生成物：它由誰生成、來源是什麼、不一致時該怎麼修。"""

    output: str
    generator: str
    source: str
    args: list[str] = field(default_factory=list)
    # 產生器輸出到 stdout／指定路徑；None 代表「檔案本身就是輸入，無法重算」
    regenerate: list[str] | None = None
    check_command: list[str] | None = None
    normalise_dates: bool = True


TARGETS: list[Generated] = [
    # 比對的是「產生出來的 MD」與「提交的 MD」，不是 ``check``（那只驗 YAML 宣稱）。
    # 先前這道門寫著「與產生器輸出一致」，實際上跑的是 check——訊息在說謊，正是本門禁
    # 要消滅的那種。
    Generated(
        output="docs/STATUS_MATRIX.md",
        generator="scripts/gen_status_matrix.py",
        source="docs/status_matrix.yaml",
        regenerate=[f"{PY}", "scripts/gen_status_matrix.py"],
        check_command=[
            f"{PY}",
            "scripts/gen_status_matrix.py",
            "generate",
            "--output",
            "<tmp>",
        ],
    ),
    Generated(
        output="docs/PROJECT_MAP_GENERATED.md",
        generator="scripts/gen_project_map.py",
        source="整棵樹（檔案與 import 掃描結果）",
        regenerate=[f"{PY}", "scripts/gen_project_map.py", "--budget", "10000"],
        check_command=[
            f"{PY}",
            "scripts/gen_project_map.py",
            "--output",
            "<tmp>",
            "--no-history",
            "--budget",
            "10000",
        ],
    ),
    Generated(
        output="scripts/INVENTORY.json",
        generator="scripts/gen_script_inventory.py",
        source="scripts/*.py 的 docstring 與呼叫關係",
        regenerate=[f"{PY}", "scripts/gen_script_inventory.py"],
        check_command=[f"{PY}", "scripts/gen_script_inventory.py", "--check"],
        normalise_dates=True,
    ),
    # ACTIVE_SCRIPTS.md 本體是手寫的，但裡面三個「由清單推導」的數字（總數／被引用／
    # 未被引用）由同一支產生器寫入——它寫下 219 支時 scripts/ 已經有 274 支了。
    Generated(
        output="scripts/ACTIVE_SCRIPTS.md",
        generator="scripts/gen_script_inventory.py",
        source="scripts/*.py 的實際數量（計數由清單推導）",
        regenerate=[f"{PY}", "scripts/gen_script_inventory.py"],
        check_command=[f"{PY}", "scripts/gen_script_inventory.py", "--check"],
    ),
]


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


TREND_RE = re.compile(r"^## TREND\s*$.*?(?=^## |\Z)", re.M | re.S)
# 專案地圖把「每一個檔案的位元組數與修改日期」也寫進去了，任何一次編輯都會讓它
# 變。這些是快照刻度，不是內容：比對它們等於要求每次改檔都重跑地圖。
VOLATILE_RES = [
    (re.compile(r"\d+KB"), "<size>KB"),
    (re.compile(r"\d+\s*檔"), "<n> 檔"),
    (re.compile(r"\d+/\d+\s*行"), "<n>/<budget> 行"),
    (re.compile(r"import 邊：\d+"), "import 邊：<n>"),
    (re.compile(r"引用檔數"), "引用檔數"),
]


def _normalise(text: str, with_dates: bool) -> str:
    """去掉「不是內容」的部分再比對。

    - 日期：專案地圖標題是 ``生成於 <今天>``，每天重跑都不同。
    - 檔案位元組數與檔數（``114KB``、``9884 檔``）：任何一次編輯都會變。
    - ``## TREND`` 段：印的是 ``docs/.project_map_history.jsonl`` 的輪轉次數，
      每跑一次產生器就 +1（而且門禁用 ``--no-history`` 跑是 0）。它記錄的是
      「產生器被跑過幾次」，不是專案內容，比對它只會讓門禁每天閃紅。
    """
    text = text.replace("\r\n", "\n")
    if with_dates:
        text = DATE_RE.sub("<date>", text)
    text = TREND_RE.sub("## TREND\n（略）\n\n", text)
    for pattern, repl in VOLATILE_RES:
        text = pattern.sub(repl, text)
    return text.rstrip("\n")


def _tracked(rel: str) -> bool:
    """這個生成物是否在版本控制裡。

    這一條是給「生成檔」看的：`docs/PROJECT_MAP_GENERATED.md` 是 gitignore 的（每次
    產生都含日期與檔案大小，進版控只會制造噪音）。未追蹤的文件在乾淨 clone 的 CI 上
    不存在，如果把它當成「手改」，門禁在 CI 上就永遠紅——那是門禁自己在說謔。
    """
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        # git 不可用（或不在 repo 裡）：不確定就當作有追蹤，寧可嚴格。
        return True
    return proc.returncode == 0


def _fresh(target: Generated) -> tuple[bool, str]:
    """(is_fresh, detail) for one generated artifact."""
    if not _tracked(target.output):
        return True, "（未納入版本控制：不在版控的生成物無從手改，跳過）"
    out_path = REPO_ROOT / target.output
    if not out_path.exists():
        return False, f"{target.output} 不存在（已追蹤、但檔案不見了——先跑 `{target.generator}`）"
    committed = out_path.read_text(encoding="utf-8", errors="replace")

    if target.check_command is None:
        return True, "（無重算指令，僅登記）"

    cmd = list(target.check_command)
    tmp_name = ""
    if "<tmp>" in cmd:
        fd, tmp_name = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        cmd = [tmp_name if c == "<tmp>" else c for c in cmd]

    try:
        rc, log = _run(cmd)
        if tmp_name:
            produced = Path(tmp_name).read_text(encoding="utf-8", errors="replace")
            old_text = _normalise(committed, target.normalise_dates)
            new_text = _normalise(produced, target.normalise_dates)
            if old_text != new_text:
                # 報告用「正規化後」的內容：否則第一個不同點會是日期／runs 這種不是內容的東西。
                return False, _first_difference(old_text, new_text)
            return True, "（與產生器輸出一致）"
        if rc != 0:
            return False, log.strip() or f"{target.generator} 回報不一致（exit {rc}）"
        return True, "（與產生器輸出一致）"
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)


def _first_difference(committed: str, produced: str) -> str:
    """指出第一行不同的地方——「哪裡被手改了」比「不一致」有用。"""
    old = committed.splitlines()
    new = produced.splitlines()
    for i, (a, b) in enumerate(zip(old, new), 1):
        if DATE_RE.sub("<date>", a) != DATE_RE.sub("<date>", b):
            return f"第 {i} 行不同：\n      檔案：{a[:120]}\n      產生：{b[:120]}"
    return f"行數不同：檔案 {len(old)} 行、產生器 {len(new)} 行（多／少的段落被手改或過期）"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix", action="store_true", help="就地重跑產生器覆蓋生成物")
    ap.add_argument("--list", action="store_true", help="列出登記的生成物")
    args = ap.parse_args()

    if args.list:
        for t in TARGETS:
            print(f"{t.output:38s} ← {t.generator}（來源：{t.source}）")
        return 0

    if args.fix:
        failed = 0
        for t in TARGETS:
            if t.regenerate is None:
                continue
            rc, log = _run(t.regenerate)
            status = "✅" if rc == 0 else "❌"
            print(f"{status} {t.output} ← {' '.join(t.regenerate[1:])}")
            if rc != 0:
                failed += 1
                print(log.strip()[-800:])
        return 0 if failed == 0 else 1

    stale: list[Generated] = []
    for t in TARGETS:
        ok, detail = _fresh(t)
        mark = "✅" if ok else "❌"
        print(f"{mark} {t.output:38s} {detail}")
        if not ok:
            stale.append(t)

    if not stale:
        print("✅ 生成物都與產生器一致（沒有手改殘留）")
        return 0

    print("\n❌ 生成檔與產生器不一致。生成檔不准手改：手改的內容下一次重跑就消失。")
    for t in stale:
        print(f"   {t.output}：改來源「{t.source}」，或跑 `{' '.join(t.regenerate or [])}`")
    print("   一次修完：python scripts/check_generated_docs.py --fix")
    return 1


if __name__ == "__main__":
    sys.exit(main())
