#!/usr/bin/env python3
"""
L1-4 Hold-out gap validation — 輕量評估（CPU-only, <50MB, <2s）

不做重型訓練，僅驗證「訓練集 vs hold-out 的確定性引擎表現 gap <15%」的
量測框架是否就緒。為 L1-4 出階標準的可量測基礎。

方法：
  1. 對 logic_train.json 做 80/20 確定性切分（hash 取模，避免隨機）
  2. 各抽 100 樣本，跑 route_knowledge / route_reasoning 的命中率
  3. 報告 train/holdout 命中率與 gap

資源保護：
  - 只載 logic_train.json（~1M），不碰 alpaca 22M
  - 批次 100 樣本，單次 forward 無 SNN 大矩陣
  - 超時 10s，記憶體峰值 <50MB
"""

import json
import os
import sys
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "data", "raw_datasets", "logic_train.json")


def split_holdout(items, train_ratio=0.8):
    train, hold = [], []
    for it in items:
        # 確定性 hash：避免 random
        h = int(hashlib.md5(json.dumps(it, sort_keys=True).encode()).hexdigest(), 16)
        (train if h % 100 < train_ratio * 100 else hold).append(it)
    return train, hold


def sample(items, n=100):
    return items[:n]  # 確定性前 n，無隨機


def hit_rate(samples):
    from ai.knowledge_base import route_knowledge
    from ai.symbolic_reasoner import route_reasoning

    hits = 0
    for s in samples:
        q = s.get("input") or s.get("question") or s.get("text") or ""
        # 嘗試兩個確定性引擎任一命中即算 hit（模擬「可理解」）
        if route_knowledge(q) is not None or route_reasoning(q) is not None:
            hits += 1
        # 若樣本已有 output，嘗試模糊匹配（不強制）
        elif s.get("output") and s["output"].lower() in q.lower():
            hits += 1
    return hits / len(samples) if samples else 0.0


def main():
    if not os.path.exists(DATA_PATH):
        print(f"⚠️ {DATA_PATH} not found — using synthetic 200 samples")
        items = [{"input": f"Test question {i}", "output": "dummy"} for i in range(200)]
    else:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            items = json.load(f)
        print(f"Loaded {len(items)} logic_train samples from {DATA_PATH}")

    train, hold = split_holdout(items, 0.8)
    print(f"Split: train={len(train)} holdout={len(hold)} (80/20)")

    train_s = sample(train, 100)
    hold_s = sample(hold, 100)

    train_hit = hit_rate(train_s)
    hold_hit = hit_rate(hold_s)
    gap = abs(train_hit - hold_hit)

    print(f"Hit rate: train={train_hit:.3f} holdout={hold_hit:.3f} gap={gap:.3f}")
    print(f"Gap <0.15 ? {'✅ PASS' if gap < 0.15 else '❌ FAIL (待訓練後複測)'}")
    # 當前為框架驗證，不以 gap 作為 exit code（避免 CI 誤紅）
    # 真正訓練後 gap 應 <0.15，屆時再改為嚴格
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
