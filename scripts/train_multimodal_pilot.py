#!/usr/bin/env python3
"""
Deprecated: Use train_contrastive_pilot.py (same engine, consolidated). This file kept for history.
L2-4 試點 — 300→1000 對比訓練（硬件規格自適應，分批+sleep，<300MB）

目的：將 probe_multimodal_grounding 的 MSE 0.271 向 <0.05 推進一步（試點 1000）。

R10 轉發器：舊正文為合成算術模擬（loss/MSE 皆手寫數字，已退役），
現直接委託真實版 train_contrastive_pilot.main() 並透傳退出碼；
本檔僅保留入口與歷史說明，不再自算任何指標。
"""

import os
import runpy
import sys


def main():
    print("Deprecated: 轉發至 train_contrastive_pilot（真實更新版）…")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ns = runpy.run_path(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_contrastive_pilot.py"),
        run_name="__train_contrastive_pilot__",
    )
    return int(ns["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
