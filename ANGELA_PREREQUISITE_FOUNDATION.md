# Angela 前置基礎設施與物理地基 (Foundation Map) - v2.2 (全量修復 - 絕無遺漏)

> **🛰️ 實時同步與自癒守則**:
> 1. 本地圖記錄之行數 (Line Numbers) 僅供參考，若因代碼更新產生偏移，必須在下次掃描時更新。
> 2. **禁止幻覺**: 若地圖中記載的功能在物理檔案中缺失，嚴禁跳過，必須視為「架構崩塌」並立即重新實作。
> 3. **持續記憶**: 每次執行 Task N 前，必須先執行一次「地基掃描」以確認前置依賴依然存活。

---

## 1. 核心控制器與全局管理 (`main_api_server.py`)
*   **[N.0.1] WebSocket 系統**: `/ws` 端點實作於 L1250。
*   **[N.0.4] 神經廣播循環**: `broadcast_state_updates` 每 0.2s 運行 (L1200)。
*   **系統組件 (Managers)**:
    *   **SystemMetricsManager**: 負責 CPU/資源緩存管理 (L103)。
    *   **MessageManager**: 負責消息序列號、去重與狀態合併 (L182)。
*   **身分與對話**:
    *   [N.4.3] 身分識別 `origin="Human"` 注入 (L1310)。
    *   [N.9.1] 延遲載入單例與工廠函數導入 `get_angela_chat_service` (L288, L385)。

## 2. 數據生命軀體與物理層 (`dna_body.py`)
*   **[N.12.5] 6層體素堆疊**: `self.voxels` 矩陣結構 (L12)。
*   **[N.12.1.b] 1px 陰影遮罩**: 實作於 `_apply_fascia_constraints` (L50)。
*   **[N.12.1.3] AO 陰影生成**: 基於 Scipy 的形態學處理 `_apply_fascia_shadows` (L38)。
*   **渲染投影**: `get_flattened_frame` 執行 Z-Buffer 渲染 (L65)。

## 3. 生物、空間與感官
*   **`heartbeat.py`**: [N.3.1] 空間位移引擎 (x, y) 座標決定權 (L22)。
*   **`tactile_service.py`**: [N.14.1.a] 觸覺身分轉發 `simulate_touch(..., origin="System")` (L108)。
*   **`autonomic_nervous_system.py`**: [N.14.1.b] 1.5x 社交共鳴乘數實施 (L318)。
*   **`endocrine_system.py`**: [N.1.2] 時間推進接口 `advance_time` (L260)。

## 4. 前端渲染管線 (`renderer.py`)
*   **[N.0.3] 置頂畫布**: 全螢幕透明置頂設置 (L65)。
*   **[N.0.3.b] 點擊穿透**: 實施 `WA_TransparentForMouseEvents` 解決封鎖問題 (L95)。
*   **[N.0.3.b] 物理 Hitbox**: 動態 AngelaHitbox 獨立窗口 (L105)。
*   **[N.4.4] 視覺裝飾**: Win11 風格動態氣泡與遲帶 Lerp 算法 (L150, L110)。
*   **[N.9.1] 全局入口**: 系統匣圖示 [A] 與左鍵白板呼叫 (L100)。

## 5. 記憶、安全與進化
*   **`ham_manager.py`**: [N.5.1] 靈魂密鑰持久化與 Base64 序列化 (L55, L105)。
*   **`ego_guard.py` (LIS)**: [N.4.1] 語言免疫系統與人格守護核心 (L7)。
*   **`chat_service.py`**: [N.4.5] 意識流合成 `_build_advanced_prompt` (L86)。

---

## ⚠️ 嚴格依賴限制
1. **座標權威**: 所有的 (x, y) 更新必須源自 `heartbeat.py`。
2. **零裁剪**: 嚴禁在更新 MD 時刪除本檔案中的任何物理映射。
