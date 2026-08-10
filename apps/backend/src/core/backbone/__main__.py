# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""主幹線 CLI 入口 — `python -m core.backbone`。

用法：
    python -m core.backbone              # 打印主幹線全覽（dump）
    python -m core.backbone dump         # 同上（詳細）
    python -m core.backbone summary      # 簡潔數量摘要
    python -m core.backbone json         # 結構化 JSON（供工具/審查）
    python -m core.backbone dump --brief # 只列數量
"""

from __future__ import annotations

import json
import sys
from typing import Any


def _get_backbone() -> Any:
    from core.backbone import get_backbone

    return get_backbone()


def _print_dump(backbone: Any, brief: bool) -> None:
    from core.backbone.structure import dump

    print(dump(backbone, title="UNIFIED BACKBONE", detailed=not brief))


def _print_summary(backbone: Any) -> None:
    print(json.dumps(backbone.summary(), ensure_ascii=False, indent=2))


def _print_json(backbone: Any) -> None:
    print(json.dumps(backbone.structure(), ensure_ascii=False, indent=2, default=str))


def main(argv: list) -> int:
    args = list(argv)
    command = args[0] if args else "dump"

    if command in ("dump", "status"):
        backbone = _get_backbone()
        _print_dump(backbone, brief="--brief" in args or "-b" in args)
        return 0
    if command == "summary":
        _print_summary(_get_backbone())
        return 0
    if command in ("json", "tree"):
        _print_json(_get_backbone())
        return 0
    if command in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    print(f"unknown command: {command}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
