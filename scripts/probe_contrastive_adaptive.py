#!/usr/bin/env python3
"""
L1-6 對比訓練硬件自適應 — 規格驅動批處理（<50MB, <1s）

不實際跑 3000 重訓，僅展示硬件規格如何自適應 batch/slots/vocab，
證明 同硬件無論桌機/筆電皆同 compute。

300 現狀 loss 0.195 → 3000 目標 loss <0.1 需：
  - batch 32 (high_performance) vs 16 (low) 自適應
  - slots/vocab 自適應
  - 批間 sleep + checkpoint 避免 OOM/佔滿
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

def main():
    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    adaptive = HardwareProfile.get_adaptive_compute(hw)
    print(f"硬件規格自適應（L1-6 對比訓練）:")
    print(f"  GPU={hw['gpu']} VRAM={hw['gpu_memory_gb']}GB RAM={hw['ram_gb']:.1f}GB tier={tier}")
    print(f"  adaptive: vocab={adaptive['garden_max_vocab']} batch×{adaptive['ed3n_batch_multiplier']} slots={adaptive['unified_slots']} tl_batch={adaptive['three_layer_batch']}")

    # 模擬對比訓練批處理
    total = 3000
    batch_map = {"high_performance_desktop": 64, "high_performance_gpu": 64, "desktop_igpu": 32, "laptop_normal": 32, "laptop_power_saver": 16, "low_power_device": 16, "server_cloud": 64}
    batch = batch_map.get(tier, 32)
    # 覆蓋為 adaptive 的 tl_batch
    batch = adaptive['three_layer_batch']
    batches = (total + batch - 1) // batch
    vram_est = adaptive['garden_max_vocab']**2 * 4 / 1024**3
    print(f"  300→3000 需 {batches} 批 × {batch} (spec-driven tl_batch={batch})")
    print(f"  估算 vocab 矩陣 {adaptive['garden_max_vocab']}²×4B = {vram_est:.2f}GB (usable {adaptive['usable_ram_gb']}GB)")
    print(f"  策略: 每 100 樣本 checkpoint + sleep 0.1s，批間 check RAM>85% 暫停，確保不 OOM/不佔滿")
    # 驗證 chassis-agnostic
    hw_laptop_same = {'gpu': 'Intel Arc B570', 'gpu_memory_gb': 10, 'ram_gb': 15.5, 'cpu_cores': 4, 'gpu_vendor': 'intel', 'disk_free_gb': 500}
    adaptive_laptop = HardwareProfile.get_adaptive_compute(hw_laptop_same)
    print(f"  驗證筆電同規格: vocab {adaptive_laptop['garden_max_vocab']} batch {adaptive_laptop['three_layer_batch']} → {'✅ chassis-agnostic' if adaptive_laptop['garden_max_vocab']==adaptive['garden_max_vocab'] else '❌'}")
    print(f"\n  現狀 loss 0.195 (300) → 目標 <0.1 (3000) 需 {batches} 批，硬件自適應已就緒")
    return 0

if __name__ == "__main__":
    main()
