<!--
  =============================================================================
  FILE_PATH: docs/user_guide/hardware.md
  FILE_TYPE: documentation
  PURPOSE: 硬體需求與推理限制
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-17
  AUDIENCE: users
  =============================================================================
-->

# 硬體指南（Hardware Guide）

## 需求

| 項目   | 最低             | 建議                             |
| ------ | ---------------- | -------------------------------- |
| Python | 3.10             | 3.10+                            |
| RAM    | 4GB              | 8GB+（GARDEN/SNN 訓練建議 16GB） |
| 磁碟   | 2GB              | 10GB+（模型、字典、資料集）      |
| GPU    | 無（可全程 CPU） | 非必要——Intel XPU 為實驗性，見下 |

## 推理裝置：預設 CPU，XPU 為實驗性

> **正式版不承諾硬體加速推理**：硬體加速推理（CUDA/ROCm/Metal）未驗證、列為不支援項；
> Intel XPU 是**實驗性**路徑，實測可用但不在支援範圍內。預設設定可在純 CPU 上完整執行。

- 裝置由 `core/system/config/compute_device.py` 的 `resolve_torch_device()` 解析
  （明確可用的裝置 → `xpu` > `cuda` > `cpu`），每個功能再由
  `compute.<feature>.mode`（`auto`／`on`／`off`）決定是否使用加速器；`off` 一律回 CPU，
  不會因為偵測到加速器就擅自使用。
- 2026-11-05 實測（Intel Arc B570，torch 2.14.1+xpu）：token-SNN 訓練以 `device=xpu` 可跑；
  CLIP 文字編碼 64 條 0.013s（CPU 0.125s）、影像 0.028s（CPU 0.165s），輸出 cosine
  1.000000；GARDEN 的稀疏 Hebbian 更新在 XPU 上反而慢約 7 倍，因此預設仍為 CPU。
- 本地 LLM（Ollama/llama.cpp）本身的 GPU
  offload 由該服務自行管理，不受本專案控制；本專案對其僅做 HTTP 呼叫。
- 專案內的 SNN／多模態訓練依「硬體規格自適應」自動調整 batch
  size、詞彙量與背景循環頻率（`backbone/hardware.py`＋`hardware/unified_hardware_center.py`，純規格驅動：RAM/VRAM/CPU 核心數）。
- 訓練類腳本有 RAM 門檻保護（預設 85%），避免 OOM。

## 省電與低階裝置

- 硬體 profile 會在低 RAM／低功耗規格自動降載（例如關聯生成 100K→50K）。
- 啟動時的硬體偵測結果寫入 `system_status.json`，Tier 判定見 bootstrap log。
