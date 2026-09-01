#!/usr/bin/env python3
"""
L2-6 500 題評測框架 — 硬件規格自適應（<50MB, <1s, 生成框架不重跑）

benchmark_ed3n_garden.py 僅 20 題 hand-picked, L2-6 需 500 題（各 100）
但重跑 500 題確定性引擎仍 <1s，SNN 500 題需分批 + 硬件自適應。

本腳本僅生成框架（不重跑 500 重評），展示硬件如何自適應批次與超時。
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

def main():
    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    adaptive = HardwareProfile.get_adaptive_compute(hw)
    # 500 題分域
    domains = ["math","knowledge","reasoning","chain","dialogue"]
    per_domain = 100
    total = 500
    # 硬件自適應批次
    batch_map = {"high_performance_desktop": 50, "laptop_normal": 20, "laptop_power_saver": 10, "low_power_device": 5, "server_cloud": 100}
    batch = batch_map.get(tier, 20)
    # 依 adaptive 的 batch_mult 調整
    batch = int(batch * adaptive['ed3n_batch_multiplier'])
    batches = (total + batch - 1)//batch
    print(f"硬件規格自適應（L2-6 500 題框架）:")
    print(f"  GPU={hw['gpu']} VRAM={hw['gpu_memory_gb']}GB RAM={hw['ram_gb']:.1f} tier={tier}")
    print(f"  adaptive batch×{adaptive['ed3n_batch_multiplier']} → batch {batch} × {batches} 批 = 500 題")
    print(f"  域: {', '.join([f'{d} 100' for d in domains])}")
    # 驗證 chassis-agnostic
    hw_same = {'gpu': 'Intel Arc B570', 'gpu_memory_gb': 10, 'ram_gb': 15.5, 'cpu_cores': 4, 'gpu_vendor': 'intel'}
    tier_same = HardwareProfile.get_tier(hw_same)
    print(f"  驗證同規格筆電 tier {tier_same} → {'✅ chassis-agnostic' if tier_same==tier else '❌'}")
    # 現狀 20 題輕量驗證
    import subprocess, time
    t0=time.time()
    out = subprocess.check_output([sys.executable, "scripts/benchmark_ed3n_garden.py", "--engine", "ed3n"], stderr=subprocess.DEVNULL, timeout=10)
    elapsed = time.time()-t0
    print(f"  現狀 20 題: {elapsed:.2f}s 輕量通過（確定性引擎）")
    print(f"  預估 500 題: {elapsed*25:.1f}s 確定性 / 需分批 SNN 則 {batches} 批×sleep 0.05s = +{batches*0.05:.1f}s")
    print(f"  目標: HYBRID ≥60% SNN-ONLY ≥30% (L2-6 出階)")
    return 0

if __name__ == "__main__":
    main()
