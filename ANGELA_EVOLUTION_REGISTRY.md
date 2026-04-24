# Angela [N+N] 動態任務包覆與衍生註冊表 (v1.0)

## 0. 層級座標系說明
*   **N**: 當前任務節點。
*   **+N**: 由該節點演化出的後續接口。
*   **狀態**: [凍結] = 邏輯已固化，禁止回溯；[實作中] = 注意力錨定點。

---

## 任務矩陣紀錄

### [Task N=0] 基礎基礎設施 (Infrastructure Layer)
*   **層級**: Level 0
*   **內容**: FastAPI 路由、WebSocket 協議基礎、單例管理模式。
*   **衍生接口 (+N)**:
    *   `+N0.1`: 實體化 OS Bridge 轉接器 (已遷移至 N=1)
    *   `+N0.2`: 建立硬體資源監控管理 (已完成)

### [Task N=1] 生物代謝與心跳閉環 (Metabolic Core)
*   **層級**: Level 1, Branch: 1
*   **父級遺產**: `+N0.1` OS Bridge 連通。
*   **內容**: 實作 `MetabolicHeartbeat`、激素衰減邏輯 (`update_hormones`)、及資源壓力轉化。
*   **衍生接口 (+N)**:
    *   `+N1.1`: **空間位移引擎 (Spatial Engine)**：將心跳轉化為座標 (已凍結於 N=2)。
    *   `+N1.2`: **擬人化反應管理器 (BioReflex)**：痛覺與流汗模擬 (已凍結於 N=3)。

### [Task N=2] 空間空間化與物理邊界 (Spatial Presence)
*   **層級**: Level 2, Branch: 1
*   **父級遺產**: `+N1.1` 空間位移引擎。
*   **內容**: 實作碰撞偵測 `_check_collision`、螢幕可用區域偵測 `availableGeometry`。
*   **衍生接口 (+N)**:
    *   `+N2.1`: **全螢幕透明渲染管線 (Overlay Engine)**：解決視窗邊界線問題 (已凍結於 N=4)。
    *   `+N2.2`: **家具物件註冊 (Furniture Registry)**：白板、桌腳的物理實體化。

### [Task N=3] 認知提示詞織入與記憶連鎖 (Cognitive Matrix)
*   **層級**: Level 3, Branch: 1
*   **父級遺產**: `+N1.2` 擬人化反應、`+N0.2` 資源監控。
*   **內容**: 重構 `ChatService`，將 `HAM` 記憶、`Vision` OCR 內容、`Bio` 狀態織入 System Prompt。
*   **衍生接口 (+N)**:
    *   `+N3.1`: **視覺語義橋接器 (The Seer Gate)**：讓 Angela 具備「主動觀察」的動機。
    *   `+N3.2`: **演化權重持久化 (Evolution Persistence)**：性格進步寫入硬碟。

### [Task N=4] 像素生命體系與交互美學 (Pixel Habitat)
*   **層級**: Level 4, Branch: 1
*   **父級遺產**: `+N2.1` 全螢幕透明渲染。
*   **內容**: 1:3 像素 DNA 軀體、Win11 風格動態氣泡、Lerp 物理位移遲帶、原生 IME 對接。
*   **衍生接口 (+N)**:
    *   `+N4.1`: **全域活動感知器 (Input Sniffing)**：偵測妳正在玩的遊戲或程式 (實作中)。
    *   `+N4.2`: **像素肌肉形變引擎 (SoftBody-Visual Sync)**：將 `SoftBodyEngine` 的壓力波轉化為像素點的位移渲染。

---

## 🔒 當前凍結狀態 (Logic Fingerprint)
*   **Latest Fingerprint**: `ANGELA-FULL-SYNC-20260423-FINAL`
*   **受保護檔案**:
    *   `main_api_server.py` (1389 行版本)
    *   `chat_service.py` (神經織入版)
    *   `heartbeat.py` (空間中樞版)
    *   `renderer.py` (全螢幕透明版)
