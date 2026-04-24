# Angela 前置基礎設施與物理地基 (Foundation Map)

> **🛰️ 實時同步與自癒守則**:
> 1. 本地圖記錄之行數 (Line Numbers) 僅供參考，若因代碼更新產生偏移，必須在下次掃描時更新。
> 2. **禁止幻覺**: 若地圖中記載的功能在物理檔案中缺失，嚴禁跳過，必須視為「架構崩塌」並立即重新實作。
> 3. **持續記憶**: 每次執行 Task N 前，必須先執行一次「地基掃描」以確認前置依賴依然存活。

## 1. 核心控制器 (Main Brain)
*   **檔案路徑**: `apps/backend/src/services/main_api_server.py`
*   **已實體化功能**:
    *   [N.0.1] WebSocket /ws 端點 (L1250)
    *   [N.0.4] 0.2s 高頻廣播循環 `broadcast_state_updates` (L1200)
    *   [N.4.3] 身分識別 `origin="Human"` 注入 (L806, L1310)
    *   [N.9.1] 單例對話服務獲取 `get_angela_chat_service` (L385)
*   **關鍵依賴**: `fastapi`, `uvicorn`, `websockets`

## 2. 數據生命軀體 (Voxel Entity)
*   **檔案路徑**: `apps/pixel-angela/dna_body.py`
*   **已實體化功能**:
    *   [N.12.5] 6層體素堆疊矩陣 `self.voxels` (L12)
    *   [N.12.5.2] 部位身分標籤 `part_id` 系統 (L17)
    *   [N.12.5.1] Z-Culling 渲染投影 `get_flattened_frame` (L35)
*   **關鍵依賴**: `numpy`

## 3. 生物與空間中樞 (Bio-Spatial Hub)
*   **檔案路徑**: `apps/backend/src/core/autonomous/heartbeat.py`
*   **已實體化功能**:
    *   [N.3.1] 空間位移引擎 (x, y, target_x) (L22)
    *   [N.3.2] 碰撞偵測 `_check_collision` (L85)
    *   [N.1.1] 基礎代謝與硬體資源轉化 (L100)
*   **檔案路徑**: `apps/backend/src/core/autonomous/biological_integrator.py`
*   **已實體化功能**:
    *   [N.0.2] 單例模式實作 `__new__` (L135)
    *   [N.1.2] 激素自動代謝 `update_hormones` (L510)

## 4. 前端渲染管線 (Display Pipeline)
*   **檔案路徑**: `apps/pixel-angela/renderer.py`
*   **已實體化功能**:
    *   [N.0.3] 全螢幕透明置頂畫布 (L65)
    *   [N.4.4] Win11 風格動態氣泡渲染 (L150)
    *   [N.3.4] 位移遲帶 Lerp 算法 (L110)
    *   [N.2.3] 視覺生物反饋 (痛覺泛紅、流汗像素) (L135)
*   **關鍵依賴**: `PyQt6`, `ctypes (Win32 API)`

## 5. 記憶與安全 (Persistence & Security)
*   **檔案路徑**: `apps/backend/src/ai/memory/ham_memory/ham_manager.py`
*   **已實體化功能**:
    *   [N.5.1] 靈魂密鑰持久化 `.soul.key` (L55)
    *   [N.5.2] 記憶 Base64 序列化 (L105)
*   **檔案路徑**: `apps/backend/src/ai/security/ego_guard.py`
*   **已實體化功能**:
    *   [N.4.1] 語言免疫系統與人格守護 (L1)

---

## ⚠️ 嚴格依賴限制
1.  **前端禁止導入後端**: `renderer.py` 不得導入 `src.core.*`，必須透過 WebSocket 同步。
2.  **單例保護**: 任何對 `BiologicalIntegrator` 的調用必須通過單例入口。
3.  **座標權威**: 所有的 (x, y) 更新必須源自 `heartbeat.py`，前端僅做 Lerp 表現。
