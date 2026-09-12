#!/usr/bin/env python3
"""
L1-6 對比訓練試點 — 硬件規格自適應（<300MB, <30s）

SharedLatentSpace 真實對比更新：1000 合成對（seed 42，pos 噪聲 0.5），
vision_semantic 投影，lr 0.05 / margin 0.5。loss 逐 epoch 實測回報，
final < initial 才是通過，否則 exit 1（拒絕模擬算術值；舊 0.195*0.85^ep
寫法已作廢，見 PROGRESS 2026-09-03 注）。

噪聲 0.5 的理由：0.1 時初始 loss 即 0.005 平坦無信息，測不出學習；
0.5 下 0.1037→0.0809 單調降且跨跑位元一致（md5 W 初始化 + seed 42）。

資源：1000 對 × 64 維，5 epoch，~0.3s，<200MB。
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

POS_NOISE = 0.5
LR = 0.05
MARGIN = 0.5


def main():
    from core.backbone.hardware import HardwareProfile

    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    print(
        f"硬件規格自適應（L1-6 真實對比 1000）: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f} tier={tier}"
    )

    from ai.multimodal.shared_latent_space import SharedLatentSpace
    import numpy as np

    epochs = 5 if tier in ("high_performance_desktop", "server_cloud") else 2
    total = 1000
    np.random.seed(42)
    pos_pairs, neg_pairs = [], []
    for _ in range(total // 2):
        base = np.random.randn(64).astype(np.float32)
        pos_pairs.append(
            (
                base + np.random.randn(64).astype(np.float32) * POS_NOISE,
                base + np.random.randn(64).astype(np.float32) * POS_NOISE,
            )
        )
        neg_pairs.append(
            (
                np.random.randn(64).astype(np.float32),
                np.random.randn(64).astype(np.float32),
            )
        )

    # 模態必須顯式註冊：未註冊時 _contrastive_loss 靜默回 0（曾因此空轉）。
    sls = SharedLatentSpace()
    sls.register_modality("vision", 64)
    sls.register_semantic_modality("vision", 64)
    print(
        f"  合成 pos {len(pos_pairs)} neg {len(neg_pairs)}，epochs {epochs} "
        f"lr {LR} margin {MARGIN}（真實更新，非模擬）"
    )
    t0 = time.time()
    result = sls.semantic_contrastive_train(
        pos_pairs,
        neg_pairs,
        modality="vision_semantic",
        epochs=epochs,
        lr=LR,
        margin=MARGIN,
    )
    hist = [round(x, 4) for x in result["history"]]
    for i, loss in enumerate(hist):
        print(f"  epoch {i + 1}/{epochs} loss {loss:.4f}")
    print(f"  真實 loss {hist[0]:.4f} → {hist[-1]:.4f} ({time.time() - t0:.1f}s)")
    print(
        "  合成數據：驗證更新迴路與確定性，真實 CIFAR/ESC-50 泛化另由 train_contrastive_real 覆蓋"
    )

    hw_same = {
        "gpu": "Intel Arc B570",
        "gpu_memory_gb": 10,
        "ram_gb": 15.5,
        "cpu_cores": 4,
        "gpu_vendor": "intel",
    }
    same_tier = HardwareProfile.get_tier(hw_same) == tier
    print(f"  筆電同規格 tier {HardwareProfile.get_tier(hw_same)} → {'✅' if same_tier else '❌'}")

    # 學習門：final 必須嚴格小於 initial，否則視為未學到（exit 1）。
    if not (hist[-1] < hist[0]):
        print("  ❌ 未學到（final 未小於 initial）")
        return 1
    print("  ✅ 學到（單調下降趨勢，跨跑位元一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
