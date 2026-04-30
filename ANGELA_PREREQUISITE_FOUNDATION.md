# Angela 前置基礎設施與物理地基 (Foundation Map) - v2.4 (絕對修復版)

> **🛰️ 實時同步與自癒守則**:
> 1. 本地圖記錄之行數僅供參考，偏移即更新。
> 2. **動態錨定 (Dynamic Anchoring)**: 執行 `replace` 前，必須先使用關鍵字 `grep_search` 校準。
> 3. **禁止幻覺**: 缺失即架構崩塌，立即重新實作。

---

## 🔍 核心功能動態錨點 (Grep Keywords)

| 功能模組 | 文件 | 核心關鍵字 (用於定位) |
|---------|------|--------------------|
| WebSocket 端點 | `main_api_server.py` | `@app.websocket("/ws")` |
| 狀態廣播循環 | `main_api_server.py` | `async def broadcast_state_updates` |
| 體素渲染引擎 | `dna_body.py` | `def get_flattened_frame` |
| 觸覺身分轉發 | `tactile_service.py` | `def forward_tactile_identity` |
| 小腦神經初始化 | `cerebellum_engine.py` | `class CerebellumEngine` |
| 語言免疫系統 | `ego_guard.py` | `class EgoGuard` |
| 藝術學習工作流 | `art_learning_workflow.py` | `class ArtLearningWorkflow` |
| 異步標準化工具 | `async_utils.py` | `def safe_create_task` |

---

## 1. 核心控制器與全局管理 (`main_api_server.py`)
*   **[N.0.1] WebSocket 系統**: `/ws` 端點實作於 L1250。
*   **[N.0.4] 神經廣播循環**: `broadcast_state_updates` 每 0.2s 運行 (L1200)。
*   **系統組件 (Managers)**:
    *   **SystemMetricsManager**: 負責 CPU/資源緩存管理 (L103)。
    *   **MessageManager**: 負責消息序列號、去重與狀態合併 (L182)。
*   **身分與對話**:
    *   [N.4.3] 身分識別 `origin="Human"` 注入 (L1310)。
    *   [N.9.1] 單例工廠函數 `get_angela_chat_service` (L288, L385)。

## 2. 數據生命軀體與物理層 (`apps/backend/src/core/dna_body.py`)
*   **[N.12.5] 6層體素堆疊**: `self.voxels` 矩陣結構 (L12)。
*   **[N.12.1.b] 1px 陰影遮罩**: `_apply_fascia_constraints` (L45)。
*   **[N.12.1.3] AO 陰影生成**: `_apply_fascia_shadows` (L158)。
*   **[N.12.Full] 全器官解剖**: 髮、脊、手、腳 IDs (L34-L75)。
*   **渲染投影**: `get_flattened_frame` 執行 Z-Buffer 渲染 (L190)。

## 3. 生物、空間與感官
*   **`tactile_service.py`**: [N.14.1.a] 觸覺身分轉發 (L108)。
*   **`autonomic_nervous_system.py`**: [N.14.1.b] 社交權重 1.5x (L318)。
*   **`endocrine_system.py`**: [N.1.2] 時間推進接口 `advance_time` (L260)。
*   **`heartbeat.py`**: [N.3.1] 空間位移引擎 (L22)。
*   **`kinetic_validator.py`**: [N.12.2] 物理極限驗證 (L20)。

## 4. 前端渲染管線 (`renderer.py`)
*   **[N.0.3] 置頂畫布**: 透明設置與 Win32 API 穿透 (L65, L95)。
*   **[N.0.3.b] 物理 Hitbox**: 獨立透明點擊窗口 (L105)。
*   **[N.4.4] 視覺裝飾**: Win11 氣泡與 Lerp 延遲 (L150, L110)。
*   **[N.9.1] 全局入口**: 系統匣藍色 [A] 圖示 (L100)。

## 5. 記憶、安全與大腦
*   **`ham_manager.py`**: [N.5.1] 靈魂密鑰持久化 (L55, L105)。
*   **`apps/backend/src/ai/security/ego_guard.py` (LIS)**: [N.4.1] 語言免疫系統與人格守護核心 (L7)。
*   **`chat_service.py`**: [N.4.5] 意識流合成與多維環境感知 (L86, L45)。

---

## 6. 小腦與自律演化
*   **`apps/backend/src/core/autonomous/cerebellum_engine.py`**: [N.16.1] 小腦單例、脊椎控制矩陣與誤差日誌實作於 L15-L60。
*   **`evolution_engine.py`**: [N.5.4] 性格演化與持久化 (待進一步映射)。
