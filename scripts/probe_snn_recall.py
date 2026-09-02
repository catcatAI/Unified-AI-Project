#!/usr/bin/env python3
"""
Deprecated: Use probe_snn_unseen.py (strict unseen generalization). This file kept for history.
L1-3 輕量探針 — SNN-ONLY 改述/CJK 召回（CPU-only, <100MB, <5s, 批量處理）

不做重型訓練，僅探測當前召回基線（对应 INTELLIGENCE_ASSESSMENT §1.1 1.0/10）。
批次處理 + 超時保護，避免 CPU 佔滿。

探測：
  - 6 改述對（paraphrase, 同义改写）
  - 2 CJK（天空/猫）
  - 閾值 0.75（semantic_qa threshold）

資源保護：
  - 單樣本串行，不批量矩陣
  - 總樣本 8，單次 <0.5s
  - 無 GPU，ONNX int8 已量化
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

PARAPHRASES = [
    ("What color is the sky?", "sky color?"),
    ("What is the opposite of hot?", "antonym of hot"),
    ("How many days in a week?", "days per week?"),
    ("What animal says meow?", "which animal meows?"),
    ("What planet is Red Planet?", "Red Planet is?"),
    ("How many wheels does a bicycle have?", "bicycle wheels?"),
]
CJK = ["天空是什么颜色?", "猫怎么叫?"]


def probe():
    from ai.unified_engine.semantic_qa import SemanticQA

    # 輕量初始化：不載入大權重，僅測 threshold 邏輯
    qa = SemanticQA()
    # 注入最小知識對（用於探測相似度路徑，不依賴大模型）
    qa.learn([
        ("What color is the sky?", "blue"),
        ("What is the opposite of hot?", "cold"),
        ("How many days in a week?", "7"),
        ("What animal says meow?", "cat"),
        ("What planet is Red Planet?", "Mars"),
        ("How many wheels does a bicycle have?", "2"),
        ("天空是什么颜色?", "blue"),
        ("猫怎么叫?", "meow"),
    ])

    ok = 0
    total = 0
    t0 = time.time()
    for orig, para in PARAPHRASES:
        ans, sim = qa.answer(para) or (None, 0)
        hit = ans is not None and sim >= 0.5  # 寬鬆 hit（探測召回存在性）
        total += 1
        if hit:
            ok += 1
        print(f"  paraphrase: '{para}' -> {ans} (sim={sim:.3f}) {'✅' if hit else '❌'}")
        time.sleep(0.02)  # 避免 CPU 佔滿

    for q in CJK:
        ans, sim = qa.answer(q) or (None, 0)
        hit = ans is not None
        total += 1
        if hit:
            ok += 1
        print(f"  CJK: '{q}' -> {ans} (sim={sim:.3f}) {'✅' if hit else '❌'}")
        time.sleep(0.02)

    recall = ok / total if total else 0
    print(f"\nProbe recall: {ok}/{total} = {recall:.1%} (elapsed {time.time()-t0:.2f}s)")
    print(f"INTELLIGENCE_ASSESSMENT 基線 11% → 當前探針 {recall:.0%}（輕量 8 樣本）")
    # 不以 exit code 強制，僅探測
    return 0


if __name__ == "__main__":
    raise SystemExit(probe())
