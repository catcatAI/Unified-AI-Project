#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L5] [βδεθζη] [A] [L3+]
# =============================================================================
#
# Angela Review CLI — 命令列審查工具
#
# 用法:
#     python scripts/angela_review.py                       # 全維度審查
#     python scripts/angela_review.py --dimension code      # 單維度
#     python scripts/angela_review.py --json                # JSON 輸出
#     python scripts/angela_review.py --output report.txt   # 輸出到檔案
#     python scripts/angela_review.py --files path/to/file.py  # 指定文件
#
# =============================================================================

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_ROOT = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(SRC_ROOT))


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="Angela Project Review Engine — 多維度項目審查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
審查維度:
  design      基於 Angela Matrix 權威的設計審查
  code        代碼質量與 ANGELA-MATRIX 标注合規
  markdown    文檔完整性與一致性
  consistency 設計↔代碼↔MD 交叉對比
  training    訓練管线與成果质量

範例:
  python scripts/angela_review.py
  python scripts/angela_review.py --dimension code
  python scripts/angela_review.py --dimension consistency --json
  python scripts/angela_review.py --files ai/core/execution_gate.py
        """,
    )
    parser.add_argument(
        "--dimension",
        "-d",
        choices=["design", "code", "markdown", "consistency", "training"],
        help="指定審查維度（預設全部）",
    )
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    parser.add_argument("--output", "-o", help="輸出檔案路徑")
    parser.add_argument("--files", nargs="+", help="指定審查檔案（僅 code 維度）")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    args = parser.parse_args(argv)

    from ai.meta.angela_review_engine import AngelaReviewEngine, get_review_engine

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    engine = AngelaReviewEngine()

    if args.files:
        reviewer = AngelaReviewEngine()._reviewers.get("code")
        if reviewer:
            from ai.meta.angela_review_engine import CodeReviewer
            report = CodeReviewer(SRC_ROOT).review(target_files=args.files)
            reports = {"code": report}
        else:
            print("Error: code reviewer not available", file=sys.stderr)
            return 1
    elif args.dimension:
        report = engine.run_review(args.dimension)
        reports = {args.dimension: report}
    else:
        reports = engine.run_full_review()

    if args.json:
        output = json.dumps(
            {k: v.to_dict() for k, v in reports.items()},
            indent=2,
            ensure_ascii=False,
        )
        if not args.files:
            output = json.dumps(
                {
                    "reports": {k: v.to_dict() for k, v in reports.items()},
                    "composite_score": engine.get_composite_score(reports),
                },
                indent=2,
                ensure_ascii=False,
            )
    else:
        output = engine.generate_summary(reports)
        composite = engine.get_composite_score(reports)
        if args.dimension:
            output += f"\nScore: {reports[args.dimension].score:.1f}/10"
        else:
            output += f"\nCOMPOSITE: {composite:.2f}/10"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved to {args.output}")
    else:
        print(output)

    max_severity = 0
    for r in reports.values():
        for f in r.findings:
            if f.severity.value == "critical":
                max_severity = 4
            elif f.severity.value == "high" and max_severity < 3:
                max_severity = 3
    return min(max_severity, 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
