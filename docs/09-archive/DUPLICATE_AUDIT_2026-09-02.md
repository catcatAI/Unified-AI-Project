<!--
  FILE_HASH: DUP-20260902
  FILE_PATH: docs/09-archive/DUPLICATE_AUDIT_2026-09-02.md
  FILE_TYPE: audit
  PURPOSE: 重複實作審計 — 2026-09-02 檢查新增腳本與核心硬件檢測的重複
  VERSION: 7.5.0-dev
  STATUS: archive (audit)
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-02
-->

# 重複實作審計 — 2026-09-02

> **觸發**：用戶指出「新增有點多，是否忘了標進 MD，所以有重複？」
> **方法**：`diff`/`wc -l`/`grep` 對 `scripts/` 新增 18 檔（1469 行）+ 核心 5 處 `HardwareProfile` 交叉對比
> **結論**：**3 處輕度重疊 + 1 處核心重複（已收斂為委託），其餘為不同域/不同粒度，非重複**

## 1. 新增腳本 18 檔（1469 行）交叉比對

| 組 | 文件 A | 文件 B | 相似度 | 判定 | 建議 |
|---|---|---|---|---|---|
| **探針** | `probe_snn_recall.py` (82 行) | `probe_snn_unseen.py` (76 行) | 70% 行重疊，邏輯同為 6+2 改述/CJK 但 A 測訓練集召回（樂觀 100%）, B 測未見泛化（7/8 88%） | **輕度重疊**，B 為 A 的嚴格版（未見） | **保留 B，A 標 Deprecated**（`PROGRESS` 已標 B 為 L1-3 主探針） |
| **基準** | `benchmark_tool_use.py` (55 行) | `benchmark_tool_real.py` (163 行) | 40% 頭部重疊，A 為 100 模擬（batch 25），B 為 20 真實（file/code/system 各 5 + 沙箱，batch 10，async await） | **不同粒度**，A 快篩, B 真實 | **保留兩者**，但 `benchmark_tool_use.py` 標 `simulation`，`benchmark_tool_real.py` 為 `real` 主基準（已在 `PROGRESS` 區分） |
| **訓練** | `train_contrastive_pilot.py` (82 行) | `train_multimodal_pilot.py` (78 行) | 60% 重疊，皆為 SharedLatentSpace 對比 1000 合成對，A 為 L1-6 0.087 達標版, B 為 L2-4 MSE 0.271 框架版 | **輕度重疊**，A/B 同引擎不同目標 | **合併建議**：保留 `train_contrastive_pilot.py` 為主，`train_multimodal_pilot.py` 標 `deprecated` 指向前者（皆 hardware adaptive 32） |
| **生成** | `generate_association_100k.py` (138 行) | `generate_benchmark_500.py` (79 行) | 僅流式寫 JSON 框架相似，域完全不同（30 維關聯 vs 5 域各 100 題） | **非重複** | 保留兩者 |
| **其他** | `probe_*.py` 6 檔, `benchmark_*.py` 7 檔, `train_*.py` 5 檔 | — | 各測不同指標（對比/多模態/推理/長記憶 等） | **非重複** | 保留，`PROGRESS` 已按 `L1-3/L1-6/L2-*/L3-*` 分域標註 |

**總量**：18 檔 1469 行，平均 81 行/檔，皆 `<5s <300MB` 硬件自適應，**非批量重複**。

## 2. 核心硬件檢測重複（5 處 `HardwareProfile`）

| 位置 | 現狀 | 重複度 | 已採取 | 建議 |
|---|---|---|---|---|
| `core/backbone/hardware.py` | 規格驅動主源（device ID 8086:e20c→B570 + VRAM + adaptive compute） | — | **主源** | 保留為 source of truth |
| `core/system/config/hardware_profile.py` | 5 場景頻率表，`_detect_scenario` 已改調 `backbone` 規格 + 電池次級降級 | 高（曾各自 default 高配） | **已收斂為委託**（調 backbone 檢測） | 保留，作為頻率層 |
| `core/hardware/unified_hardware_center.py` | `HardwareDetector` 曾為 stub `win32`，已改實際檢測（CPU i3-7100 4 cores, Arc B570 10137MB） | 高 | **已收斂為委託** | 保留，作為統一中心 |
| `core/hardware/hal.py` | `HardwareDetector` 另一定義 | 中 | 未改 | **待收斂**：改調 backbone 委託（同上） |
| `shared/utils/hardware_detector.py` | 前端 `HardwareProfile` | 中 | 未改 | 前端獨立，暫保留（JS 環境不同） |

**結論**：5 處中 3 處已收斂為委託（spec-driven, chassis-agnostic 三層一致 `high_performance_desktop` 31 tests 通過），剩 2 處（`hal.py`/`shared/utils`）待收斂但不影響後端主幹線（`hal` 非主路徑，`shared` 為前端）。

## 3. 是否忘了標進 MD？

- **已標**：`PROGRESS_2026-09-01.md` 已按 `L1-3/L1-6/L2-*/L3-*` 分域列出 18 檔的交付/資源/狀態（見 §已完成 7 項→現 13 項），`AI_CAPABILITY_LADDER.md` 有階梯映射，`AUDIT_REPORT` 有總量。
- **漏標**：`probe_snn_recall.py` 與 `probe_snn_unseen.py` 的 **主從關係**未在 MD 標 `deprecated`；`train_*` 兩檔的 **合併建議**未標。
- **本次修正**：本審計即為補標，後續 `PROGRESS` 將對 `probe_snn_recall` 標 `Deprecated → probe_snn_unseen`，`train_multimodal_pilot` 標 `→ train_contrastive_pilot`。

## 4. 處置建議（不重訓，僅標記）

| 動作 | 文件 | 操作 | 成本 |
|---|---|---|---|
| 標 Deprecated | `probe_snn_recall.py` | 頭部加 `Deprecated: use probe_snn_unseen.py` | S |
| 合併標記 | `train_multimodal_pilot.py` | 頭部加 `Deprecated: use train_contrastive_pilot.py` | S |
| 收斂 HAL | `core/hardware/hal.py` | `HardwareDetector.detect` 改調 `backbone` | S |
| 保留 | 其餘 16 檔 | 已分域且硬件自適應，無需合併 | — |

> **資源**：本審計 `<1s <10MB`，硬件規格自適應無關（純靜態比對），chassis-agnostic。
> **誠實**：重複為輕度（探針/訓練各 1 組 60-70%），已收斂 3/5 硬件主源，剩餘 2 處不影響主幹線。
