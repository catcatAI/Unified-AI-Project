#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
"""MD ↔ 主幹線對照審查工具。

使用時機：主幹線能打印（`python -m core.backbone dump`）後，用它對照非歸檔的
MD，找出「MD 內容對不上主幹線實際註冊」的候選。

方法（保守、只產候選，不刪檔）：
1. 掃描目標 MD 中出現的類別名/模組名（CamelCase 或 snake_case token）。
2. 對照 backbone 實際結構（structure()）、apps/backend/src 存在檔案、既有
   註冊名（module/dictionary/memory/matrix）。
3. 完全查無任何 token 的 MD → 標記為「空洞/與代碼無關」候選。

用法：
    python scripts/utils/md_consistency_check.py [path/to/md...]
    python scripts/utils/md_consistency_check.py               # 全 docs/
出口：印出候選清單 + 統計。
"""

import re
import sys
from pathlib import Path

SRC_ROOT = Path("apps/backend/src")
BACKBONE_KEYS = {
    "matrix",
    "module",
    "dictionary",
    "memory",
    "external",
    "learning",
    "training",
    "axes_registry",
}


def _split_tokens(text: str) -> set:
    """抓 CamelCase / snake_case / 大寫縮寫 token。"""
    tokens = set()
    for m in re.finditer(r"[A-Z][A-Za-z0-9_]*(?:[A-Z][a-z0-9]+)+", text):
        tokens.add(m.group(0))
    for m in re.finditer(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", text):
        tokens.add(m.group(0))
    for m in re.finditer(r"\b[A-Z]{2,}\b", text):
        tokens.add(m.group(0))
    return tokens


def _src_symbols() -> set:
    """收集 apps/backend/src 下的檔案 stem 與原始碼內類別名。"""
    symbols = set()
    for path in SRC_ROOT.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        symbols.add(path.stem)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\b", text):
            symbols.add(m.group(1))
    return symbols


def _backbone_known(bb) -> dict:
    structure = bb.structure() if hasattr(bb, "structure") else {}
    known = set()
    for key in ("modules", "dictionaries", "memory", "training", "external", "learning"):
        for item in structure.get(key, []) or []:
            known.add(str(item.get("name") or item.get("key") or ""))
    known.update(BACKBONE_KEYS)
    return {"known": known, "structure_keys": set(structure.keys())}


def check_md(path: Path, src_symbols: set, bb_info: dict) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    tokens = _split_tokens(text)
    # 過濾通用詞
    generic = {
        "Backbone",
        "StateMatrix",
        "SharedLatentSpace",
        "MultimodalDictionary",
        "DictionaryRegistry",
        "DatasetRegistry",
        "AxesRegistry",
        "TokenStream",
        "Envelope",
        "IOPair",
        "PairScheduler",
        "Mountable",
    }
    meaningful = tokens - generic
    hits = meaningful.intersection(src_symbols)
    bb_hits = meaningful.intersection(bb_info["known"])
    coverage = len(hits | bb_hits) / max(1, len(meaningful))
    return {
        "file": str(path),
        "tokens": len(meaningful),
        "src_hits": sorted(hits)[:8],
        "bb_hits": sorted(bb_hits)[:8],
        "coverage": round(coverage, 2),
    }


def main(argv: list) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="MD 路徑或目錄；預設全 docs/")
    parser.add_argument("--min-tokens", type=int, default=3, help="token 少於此數視為空洞（略過）")
    parser.add_argument("--threshold", type=float, default=0.15, help="coverage 低於此值列為候選")
    args = parser.parse_args(argv)

    root = Path(".")
    if args.paths:
        md_paths = []
        for p in args.paths:
            path = Path(p)
            if path.is_dir():
                md_paths.extend(path.rglob("*.md"))
            else:
                md_paths.append(path)
    else:
        md_paths = list(Path("docs").rglob("*.md"))

    # 排除已歸檔目錄
    md_paths = [p for p in md_paths if "09-archive" not in p.parts]

    sys.path.insert(0, "apps/backend/src")
    import core.backbone as cb
    from core.backbone.structure import inventory

    bb = cb.get_backbone()
    bb_info = {
        "known": _backbone_known(bb)["known"],
        "structure_keys": _backbone_known(bb)["structure_keys"],
    }
    src_symbols = _src_symbols()

    results = []
    for path in sorted(md_paths):
        res = check_md(path, src_symbols, bb_info)
        if res["tokens"] < args.min_tokens:
            res["note"] = "low-token (空洞/極簡)"
        elif res["coverage"] < args.threshold:
            res["note"] = "LOW COVERAGE — 候選審查"
        else:
            res["note"] = "ok"
        results.append(res)

    # 印出候選
    candidates = [
        r
        for r in results
        if r["note"].startswith("LOW") or r.get("note") == "low-token (空洞/極簡)"
    ]
    print(f"掃描 {len(results)} 份 MD，候選 {len(candidates)} 份")
    print("=" * 78)
    for r in candidates:
        print(f"[{r['note']}] {r['file']}")
        print(f"    tokens={r['tokens']} coverage={r['coverage']} src_hits={r['src_hits']}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
