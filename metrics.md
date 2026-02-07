# Angela AI Performance Metrics (指標)

本文件記錄 Angela AI 在不同硬體集群環境下的性能指標、推算表現及實測數據。

## 1. 統一狀態矩陣 (Unified Status Matrix: V × L × P × M)

Angela 的運行狀態由四維張量共同定義，實現了從「版本能力」到「運算模式」的全面整合。

| 維度 | 代號 | 範圍 (Range) | 說明 |
| :--- | :--- | :--- | :--- |
| **Version Status** | **V** | v6.2.0 - Production | Angela 目前的版本功能狀態與能力邊界 |
| **Maturity Level** | **L** | L0 ~ L11 | 12 個階段的矩陣成熟度，定義認知深度 |
| **Precision Level** | **P** | FP8 ~ FP128 | 5 個等級的浮點精度，定義數值解析度 |
| **Precision Mode** | **M** | INT ~ DEC4 | 5 個模式的精度模式，定義整數/小數傳輸策略 |

**狀態公式**: `Angela_State = V ⊗ L ⊗ P ⊗ M`

## 2. 安全與通訊監控 (Security & Communication Matrix)

為了確保跨裝置（桌面/行動）通訊的安全，Angela 引入了 A/B/C 密鑰體系與常駐監控器，並與外部模型金鑰進行了物理與邏輯上的隔離。

### **2.1 密鑰 vs 金鑰 (Secret Keys vs API Keys)**

| 類別 | 對象 | 存儲位置 | 生命週期 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| **系統密鑰 (Angela Secrets)** | Key A, B, C | `data/security/abc_keys.json` | 系統生成，可重置 | 用於內部通訊、行動端驗證、後端控制 |
| **外部金鑰 (Model API Keys)** | OpenAI, Anthropic, etc. | `.env` 或 `configs/*.yaml` | 外部服務商提供 | 用於調用大模型 API，與系統安全性解耦 |

### **2.2 A/B/C 密鑰體系詳解**

| 密鑰類型 | 代號 | 用途 | 保護範圍 |
| :--- | :--- | :--- | :--- |
| **Key A** | **Backend Control** | 後端服務啟停與核心權限 | 本地系統管理 (System Tray) |
| **Key B** | **Mobile Comm** | 行動端與後端加密通訊 (HMAC-SHA256) | /api/v1/mobile/* |
| **Key C** | **Sync/Desktop** | 桌面端同步與跨裝置二級驗證 | 全域同步數據 |

**監控表現 (推算)**:
- **密鑰隔離效率**: 100% (獨立管理路徑)
- **密鑰生成速度**: < 50ms (Fernet/AES-128)
- **通訊驗證延遲**: < 2ms (HMAC-SHA256)

## 2. 核心性能指標 (Expected Metrics)

| 指標 | 預期目標 (Standard) | 說明 |
| :--- | :--- | :--- |
| 推論延遲 (Inference Latency) | < 100ms | 矩陣單次運算回應時間 |
| 矩陣精度 (Matrix Precision) | > 99.8% | 整數傳輸與小數點記憶化還原後的精度 |
| 集群吞吐量 (Throughput) | > 5000 ops/s | (L0~L11) × (4~8) 每秒處理任務數 |
| 記憶化命中率 (Memoization Rate) | > 85% | 分機本地小數點記憶化命中比率 |
| 動態精度範圍 (Dynamic Range) | FP8 - FP128 | 支援從高效 FP8 到核心級 FP128 的動態切換 |

## 2. 精度圖譜 (Precision Map)

針對不同功能模組，系統採用差異化維度與精度策略，以平衡性能與效能。

| 模組 (Module) | 預設維度 (Shape) | 預設精度 (Precision) | 動態範圍 (Range) | FP 切分支援 |
| :--- | :--- | :--- | :--- | :--- |
| **Vision (視覺)** | (8, 8) | FP16 | FP8 - FP32 | 否 |
| **Audio (音訊)** | (4, 4) | FP8 | FP8 - FP16 | 否 |
| **Logic (邏輯)** | (8, 8, 8, 8) | FP32 | FP16 - FP64 | 是 (FP128->FP8) |
| **Memory (記憶)** | (12, 8) | FP64 | FP32 - FP128 | 是 (FP128->FP8) |
| **Sensory (感官)** | (4, 4) | FP8 | FP8 - FP16 | 否 |

## 3. 全動態範圍性能推算 (Dynamic Range Projections)

| 精度模式 | 典型場景 | 預期延遲 | 預期能效 | 精度權重 |
| :--- | :--- | :--- | :--- | :--- |
| **FP8 (極速)** | 音訊取樣、即時感官反饋 | < 5ms | 100% (基準) | 0.85 |
| **FP16 (標準)** | 物體檢測、場景建模 | < 15ms | 85% | 0.95 |
| **FP32 (高精度)** | 邏輯推理、語言生成 | < 40ms | 60% | 0.999 |
| **FP64 (超高精度)** | 長期記憶檢索、深度模擬 | < 120ms | 30% | 0.99999 |
| **FP128 (核心核心)** | 矩陣核心對齊、多維時空校準 | < 500ms (切分後) | 15% | 0.999999 |

## 4. 硬體集群推算表現 (Performance Projections)

*註：以下為基於標準硬體集群 (1 Master + 4 Workers) 的推算表現。*

### 標準配置 (Standard Cluster Configuration)
- **Master**: Intel Core i9-13900K, 64GB RAM, RTX 4090 (24GB)
- **Workers**: 4x Intel Core i7-13700K, 32GB RAM, RTX 4070 (12GB)
- **Network**: 10Gbps Ethernet (Intra-cluster)

### 推算指標 (Projections)
- **矩陣並行處理能力**: 可同時處理全量 12 層 (L0-L11) 的 8 維矩陣運算。
- **能效比 (Performance/Watt)**: 透過分佈式計算，預計提升 40% 的運算能效。
- **速度提升**: 相較於單機運作，集群模式下的複雜建模任務速度預計提升 3.5x。
- **精度維持**: 由於 (L0~L11) × (4~8) 矩陣的結構化特性，小數點記憶化能維持在 99.95% 以上的數值精度。

## 3. 實測記錄 (Hardware Efficiency & Speed Logs)

*系統將自動更新此區段，記錄最大、最小、平均值/時間單位。*

### 運算速度 (Ops/s)
- **最大值**: --
- **最小值**: --
- **平均值**: --

### 推論精度 (%)
- **最大值**: --
- **最小值**: --
- **平均值**: --

### 資源利用率 (%)
- **GPU 平均負載**: --
- **CPU 平均負載**: --
- **網絡延遲 (Avg)**: --

---
[返回主頁面 (README.md)](./README.md)
