#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [α] [A] [L7]
# =============================================================================
"""專案AI自主研究報告 CLI — 生成《後續研究與升級路徑完整報告》。

自己查（可重現量測 + 外部查證）→ 自己想（自有模型體檢 + 規則推導候選 +
透明公式擇優）→ 自己寫（資料填充模板 + LLM 僅逐段潤色/數字指紋守護）→
validate_report 零容忍驗證。problems 非空 → exit 1（有問題繼續修）。

用法：
    python3 scripts/generate_upgrade_report.py                # 全管線（web+polish）
    python3 scripts/generate_upgrade_report.py --no-web       # 離線
    python3 scripts/generate_upgrade_report.py --no-polish    # 不做 LLM 潤色
    python3 scripts/generate_upgrade_report.py --out /tmp/x.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# 與 main_api_server 同口徑載入根目錄 .env（雲端後端金鑰），否則 CLI 模式下
# google 等雲端後端不會註冊 → fusion 無候選 → 潤色靜默降級為空回應。
try:
    from dotenv import load_dotenv as _load_dotenv

    _env_path = REPO_ROOT / ".env"
    if _env_path.exists():
        _load_dotenv(_env_path, override=False)
except ImportError:
    # python-dotenv 未安裝：沿用現行環境（雲端潤色可能降級，附錄會記錄）
    pass

from ai.research.upgrade_research import run_upgrade_research  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="生成專案AI自主研究報告")
    parser.add_argument("--no-web", action="store_true", help="跳過外部查證（離線模式）")
    parser.add_argument("--no-polish", action="store_true", help="跳過 LLM 潤色（資料填充原稿）")
    parser.add_argument(
        "--out", default=None, help="輸出路徑（預設 docs/RESEARCH_UPGRADE_REPORT_<date>.md）"
    )
    parser.add_argument("--json", action="store_true", help="stdout 輸出機器可讀摘要")
    args = parser.parse_args()

    result = asyncio.run(
        run_upgrade_research(web=not args.no_web, polish=not args.no_polish, out_path=args.out)
    )
    stats = result.get("stats", {})
    problems = result.get("problems") or []

    if args.json:
        print(
            json.dumps(
                {"path": result["path"], "ok": result["ok"], "problems": problems, "stats": stats},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"報告：{result['path']}")
        print(
            f"stats: candidates={stats.get('candidates')} picked={stats.get('picked')} "
            f"probes={stats.get('probes_ok')}/{stats.get('probes_total')} "
            f"web_ok={stats.get('web_ok')} "
            f"collectors={stats.get('collectors_ok')}/{stats.get('collectors_total')} "
            f"polish={stats.get('polish')} chars={stats.get('report_chars')} "
            f"elapsed={stats.get('elapsed_s')}s"
        )
        if problems:
            print(f"problems（{len(problems)}）:")
            for p in problems:
                print(f"  - {p}")
        else:
            print("validate_report: 無問題（PASS）")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
