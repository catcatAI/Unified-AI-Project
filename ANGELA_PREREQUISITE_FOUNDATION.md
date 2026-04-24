# Angela 前置基礎設施與物理地基 (Foundation Map) - v2.0 (全量修復版)

> **🛰️ 實時同步與自癒守則**:
> 1. 本地圖記錄之行數僅供參考，偏移即更新。
> 2. **禁止幻覺**: 缺失即架構崩塌，立即重新實作。
> 3. **持續記憶**: 每次執行前必掃描地基。

## 1. 核心控制器與通訊 (`main_api_server.py`)
*   [N.0.1] WebSocket /ws 端點 (L1250)
*   [N.0.4] 0.2s 高頻廣播循環 `broadcast_state_updates` (L1200)
*   [N.4.3] 身分識別 `origin="Human"` 注入 (L1310)
*   [N.9.1] 單例對話服務獲取 `get_angela_chat_service` (L385)
*   [N.14.1.a] 觸覺身分轉發 `simulate_touch(..., origin="Human")` (L1308)

## 2. 數據生命軀體 (`dna_body.py`)
*   [N.12.5] 6層體素堆疊 `self.voxels` (L12)
*   [N.12.1] 肌膜防粘黏 `_apply_fascia_constraints` (L45)
*   [N.12.1.b] 1px 陰影遮罩邏輯 (L50-L60)

## 3. 生物與感官
*   **`tactile_service.py`**: [N.14.1.a] 簽名修正 (L108)
*   **`autonomic_nervous_system.py`**: [N.14.1.b] 社交權重 1.5x (L318)
*   **`heartbeat.py`**: [N.3.1] 空間位移引擎 (L22)

## 4. 前端渲染管線 (`renderer.py`)
*   [N.0.3] 全螢幕透明置頂畫布 (L65)
*   [N.0.3.b] 點擊穿透與 AngelaHitbox 獨立窗口 (L85)
*   [N.4.4] Win11 風格動態氣泡 (L150)
*   [N.2.3] 視覺生物反饋 (痛覺泛紅、流汗像素) (L135)
*   [N.9.1] 系統匣圖示 [A] 與左鍵白板呼叫 (L100)

## 5. 記憶與安全
*   **`ham_manager.py`**: [N.5.1] 密鑰持久化 `.soul.key` (L55)
*   **`ego_guard.py`**: [N.4.1] 語言免疫系統 (L1)
