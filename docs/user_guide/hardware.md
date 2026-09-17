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

| 項目 | 最低 | 建議 |
|------|------|------|
| Python | 3.10 | 3.10+ |
| RAM | 4GB | 8GB+（GARDEN/SNN 訓練建議 16GB） |
| 磁碟 | 2GB | 10GB+（模型、字典、資料集） |
| GPU | 無（可全程 CPU） | 非必要——見下方「僅 CPU 推理」 |

## 推理限制：僅 CPU

> **正式版明確不支援硬體加速推理（CUDA/ROCm/Metal）**。所有模型推理（ED3N、GARDEN、本地 LLM 的 Python 端編碼、多模態管線）皆在 CPU 執行。

- 本地 LLM（Ollama/llama.cpp）本身的 GPU offload 由該服務自行管理，不受本專案控制；本專案對其僅做 HTTP 呼叫。
- 專案內的 SNN／多模態訓練依「硬體規格自適應」自動調整 batch size、詞彙量與背景循環頻率（`backbone/hardware.py`＋`hardware/unified_hardware_center.py`，純規格驅動：RAM/VRAM/CPU 核心數）。
- 訓練類腳本有 RAM 門檻保護（預設 85%），避免 OOM。

## 省電與低階裝置

- 硬體 profile 會在低 RAM／低功耗規格自動降載（例如關聯生成 100K→50K）。
- 啟動時的硬體偵測結果寫入 `system_status.json`，Tier 判定見 bootstrap log。
