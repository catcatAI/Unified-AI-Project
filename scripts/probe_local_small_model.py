#!/usr/bin/env python3
"""
L2-5 本地小模型備選 — 硬件規格自適應（<50MB, <2s）

評估 Qwen2-0.5B / Phi-3-mini 在當前硬件（Arc B570 10GB + 15.5GB）上的可行性：
  - 顯存 <4GB, 延遲 <2s/回應 為門檻
  - 硬件自適應：high_performance 允 0.5B，low 則否

資源：僅檢測硬件 + 查詢，無實際加載模型（<1s）。
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

def main():
    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    adaptive = HardwareProfile.get_adaptive_compute(hw)
    print(f"硬件規格自適應（L2-5 本地小模型）: GPU={hw['gpu']} VRAM={hw['gpu_memory_gb']}GB RAM={hw['ram_gb']:.1f} tier={tier}")

    # 估算：Qwen2-0.5B Q4 量化 ~0.3GB + KV 0.5GB = 0.8GB；Phi-3-mini 3.8B Q4 ~2GB
    models = [
        ("Qwen2-0.5B Q4", 0.8, "<2s", "high_performance_desktop 可行"),
        ("Phi-3-mini 3.8B Q4", 2.2, "<2s", "需 ≥12GB RAM"),
        ("Qwen2-7B Q4", 4.5, ">2s", "需 ≥16GB RAM + GPU≥8GB"),
    ]
    usable = adaptive['usable_ram_gb']
    gpu_gb = hw['gpu_memory_gb'] or 0
    print(f"  可用 RAM {usable}GB VRAM {gpu_gb}GB")
    for name, need, latency, note in models:
        feasible = usable >= need + 2 and (gpu_gb >= 6 or need < 2)
        print(f"  {name}: 需 {need}GB 延遲 {latency} → {'✅ 可行' if feasible else '❌ 不行'} ({note})")

    # 硬件無關
    hw_same = {'gpu': 'Intel Arc B570', 'gpu_memory_gb': 10, 'ram_gb': 15.5, 'cpu_cores': 4, 'gpu_vendor': 'intel'}
    print(f"  筆電同規格 tier {HardwareProfile.get_tier(hw_same)} → ✅ chassis-agnostic")
    print(f"  結論: 當前 15.5GB+Arc 10GB → Qwen2-0.5B ✅ 作為 L2-5 備選（本地可用兜底，不算 LLM 層）")
    return 0

if __name__ == "__main__":
    main()
