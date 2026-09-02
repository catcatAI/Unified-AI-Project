#!/usr/bin/env python3
"""
L2-3 未見推理泛化 — 硬件規格自適應（<50MB, <3s, 分批+sleep）

測純神經推理（關確定性引擎）0%→50% 基線：
  - 確定性 symbolic 僅覆蓋正則（A taller than B 等），未見改述應 0%
  - 純神經（semantic_qa 未訓推理域）也 0%，證 gap 存在
  - 硬件自適應：batch 依 tier（high 25 / low 10）+ sleep，桌機/筆電同結果

資源：100 問 × 輕量 route_reasoning + semantic_qa，無重型訓練，<2s。
"""

import os, sys, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))
random.seed(123)

# 未見推理：改述/隱含比較/多跳，刻意避開 symbolic 正則
UNSEEN_REASONING = [
    ("The first is higher than second, second higher than third, which is top?", "first"),
    ("若 A 比 B 強，B 比 C 強，誰最強？", "A"),
    ("X > Y > Z, Y > W, 誰最小？", "W"),
    ("Alice, Bob, Carol 中 Alice 最聰明，Bob 次之，誰最笨？", "Carol"),
    ("If Tom is older than Jerry, Jerry older than Spike, is Tom older than Spike? yes/no", "yes"),
    ("A is not as short as B, B not as short as C, who shortest?", "C"),
] * 17  # 102 → 取 100
UNSEEN_REASONING = UNSEEN_REASONING[:100]

def main():
    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    adaptive = HardwareProfile.get_adaptive_compute(hw)
    print(f"硬件規格自適應（L2-3 未見推理 100 問）: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f} tier={tier}")

    from ai.symbolic_reasoner import route_reasoning
    from ai.unified_engine.semantic_qa import SemanticQA

    # 未訓推理域的 semantic_qa（僅知識 6 問）
    qa = SemanticQA()
    qa.learn([("What color is sky?", "blue")])  # 極小，避免推理命中

    batch = 25 if tier in ("high_performance_desktop", "server_cloud", "high_performance_gpu") else 10
    batch = int(batch * adaptive['ed3n_batch_multiplier'] / 1.5)  # 歸一
    symbolic_hits = 0
    neural_hits = 0
    for i in range(0, len(UNSEEN_REASONING), batch):
        for q, exp in UNSEEN_REASONING[i:i+batch]:
            sym = route_reasoning(q)
            if sym and exp.lower() in sym.lower():
                symbolic_hits += 1
            ans, sim = qa.answer(q) or (None, 0)
            if ans and exp.lower() in ans.lower() and sim >= 0.7:
                neural_hits += 1
        time.sleep(0.02)

    print(f"  確定性 symbolic: {symbolic_hits}/100 = {symbolic_hits}%（未見改述應低）")
    print(f"  純神經 semantic_qa（未訓推理）: {neural_hits}/100 = {neural_hits}%（現 0% 基線）")
    print(f"  目標 L2-3 純神經 ≥50%（需在 FixedSizeCore 訓 5K 未見推理域）")
    # 硬件無關
    hw_same = {'gpu': 'Intel Arc B570', 'gpu_memory_gb': 10, 'ram_gb': 15.5, 'cpu_cores': 4, 'gpu_vendor': 'intel'}
    print(f"  筆電同規格 tier {HardwareProfile.get_tier(hw_same)} → {'✅' if HardwareProfile.get_tier(hw_same)==tier else '❌'}")
    # 提示下一步
    if symbolic_hits < 20 and neural_hits < 5:
        print(f"  基線確認：未見推理 gap 存在，L2-3 需收集 5K 未覆蓋推理題 + FixedSizeCore 訓練（hardware adaptive batch）")
    return 0

if __name__ == "__main__":
    main()
