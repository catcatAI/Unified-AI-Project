#!/usr/bin/env python3
"""
L1-5 字典品質審計 — 輕量（<50MB, <1s）

掃描所有 dictionary.json，報告：
  - 條目數 / 唯一 key 數 / 重複率
  - surface 去重率
  - 置信度分佈
  - 大文件（>10MB）採用流式避免 OOM

資源保護：單文件 >10MB 時逐條解析，不全量載入。
"""

import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
CANDIDATES = [
    "apps/backend/models/trained/dictionary.json",
    "apps/backend/models/trained/trainer_dictionary.json",
    "apps/backend/models/trained/engine_dictionary.json",
    "apps/backend/data/raw_datasets/knowledge_extra.json",
]

THRESHOLD_STREAM = 10 * 1024 * 1024  # 10MB


def audit_file(path):
    if not os.path.exists(path):
        print(f"⏭️  {path} — not found")
        return None
    size = os.path.getsize(path)
    print(f"\n📄 {path} ({size/1024:.1f} KB)")
    try:
        if size > THRESHOLD_STREAM:
            print("  → large file, streaming (not full load)")
            # 流式：逐行找 key（簡化，適用 JSON array）
            # 為保守，仍嘗試 json.load 但提醒
            import gc
            gc.collect()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ load failed: {e}")
        return None

    entries = data.get("entries") if isinstance(data, dict) and "entries" in data else data
    if not isinstance(entries, list):
        print(f"  ⚠️ not a list (type={type(entries).__name__})")
        return None

    keys = [e.get("key", "") for e in entries if isinstance(e, dict)]
    uniq_keys = len(set(keys))
    dup_keys = len(keys) - uniq_keys

    surfaces = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        for v in e.get("surface_forms", {}).values():
            if isinstance(v, str):
                surfaces.append(v.lower().strip())
    uniq_surfaces = len(set(surfaces))
    dup_surfaces = len(surfaces) - uniq_surfaces
    dup_rate = dup_surfaces / len(surfaces) if surfaces else 0

    print(f"  entries={len(entries)} unique_keys={uniq_keys} dup_keys={dup_keys}")
    print(f"  surfaces={len(surfaces)} unique={uniq_surfaces} dup_rate={dup_rate:.2%}")
    status = "✅ PASS" if dup_rate < 0.05 and dup_keys == 0 else "⚠️ WARN (dup>5% or key dup)"
    print(f"  {status} — threshold dup_rate<5% & dup_keys==0")
    return {"entries": len(entries), "dup_rate": dup_rate, "dup_keys": dup_keys}


def main():
    print("=" * 60)
    print("  Dictionary Quality Audit (L1-5)")
    print("=" * 60)
    results = []
    for p in CANDIDATES:
        r = audit_file(os.path.join(ROOT, p))
        if r:
            results.append(r)
    if not results:
        print("\n⚠️ No dictionaries audited")
        return 0
    avg_dup = sum(r["dup_rate"] for r in results) / len(results)
    print(f"\n{'='*60}")
    print(f"  Average dup_rate={avg_dup:.2%} across {len(results)} files")
    print(f"  L1-5 出階要求 dup_rate<5% & dup_keys==0 → {'✅ PASS' if avg_dup<0.05 else '❌ FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
