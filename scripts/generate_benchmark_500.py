#!/usr/bin/env python3
"""
L2-6 500 題評測集實現 — 硬件規格自適應（流式，分批，<10MB）

5 域各 100 題（math/knowledge/reasoning/chain/dialogue），流式寫 JSON array，
批間 sleep 0.02s，同硬件無論桌機/筆電同結果。

資源：500 題 × ~100B = 50KB，<1s。
"""

import json, os, sys, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))
random.seed(42)

def gen_math(n):
    for i in range(n):
        a, b = random.randint(1, 20), random.randint(1, 20)
        op = random.choice(["+", "-", "*"])
        q = f"{a} {op} {b} = ?"
        ans = str(eval(f"{a}{op}{b}"))
        yield {"domain": "math", "question": q, "expected": ans, "id": f"math_{i}"}

def gen_knowledge(n):
    kb = [("sky color?", "blue"), ("opposite of hot?", "cold"), ("days in week?", "7"), ("meow animal?", "cat"), ("Red Planet?", "Mars")]
    for i in range(n):
        q, a = random.choice(kb)
        yield {"domain": "knowledge", "question": q, "expected": a, "id": f"know_{i}"}

def gen_reasoning(n):
    for i in range(n):
        yield {"domain": "reasoning", "question": "A taller than B. B taller than C. Who tallest?", "expected": "A", "id": f"reason_{i}"}

def gen_chain(n):
    for i in range(n):
        yield {"domain": "chain", "question": "A->B->C->D chain, who reaches D?", "expected": "A", "id": f"chain_{i}"}

def gen_dialogue(n):
    for i in range(n):
        yield {"domain": "dialogue", "question": f"Turn {i%5+1}: 你好，我是小明", "expected": "記憶人設", "id": f"dial_{i}"}

def main():
    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    adaptive = HardwareProfile.get_adaptive_compute(hw)
    print(f"硬件規格自適應（500 題生成）: {hw['gpu']} {hw['ram_gb']:.1f}GB tier={tier} batch×{adaptive['ed3n_batch_multiplier']}")

    out_path = os.path.join(os.path.dirname(__file__), "..", "apps/backend/data/benchmark_500.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    total = 500
    batch = int(50 * adaptive['ed3n_batch_multiplier'])  # 50*1.5=75
    # 流式寫
    gens = [gen_math(100), gen_knowledge(100), gen_reasoning(100), gen_chain(100), gen_dialogue(100)]
    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("[\n")
        for gi, gen in enumerate(gens):
            for j, item in enumerate(gen):
                is_last = (gi == len(gens)-1 and j == 99)
                json.dump(item, f, ensure_ascii=False)
                if not is_last:
                    f.write(",\n")
                else:
                    f.write("\n")
                count += 1
                if count % batch == 0:
                    print(f"  {count}/{total} ({count/total:.0%})")
                    time.sleep(0.02)
        f.write("]\n")
    size = os.path.getsize(out_path)/1024
    print(f"✅ 生成 {count} 題 → {out_path} ({size:.1f} KB) 硬件自適應 batch {batch}×{count//batch} 批")
    # 驗證 chassis-agnostic
    hw_same = {'gpu': 'Intel Arc B570', 'gpu_memory_gb': 10, 'ram_gb': 15.5, 'cpu_cores': 4, 'gpu_vendor': 'intel'}
    print(f"  筆電同規格 tier {HardwareProfile.get_tier(hw_same)} → {'✅' if HardwareProfile.get_tier(hw_same)==tier else '❌'}")
    return 0

if __name__ == "__main__":
    main()
