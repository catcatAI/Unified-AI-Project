# Phase 2 Development Plan: "Spark of Life"

## 1. 核心目標 (Core Objectives)
基於 `PROJECT_MASTER_OVERVIEW.md` 的分析與用戶日誌 (Activity Logs) 的攝入，第二階段的核心目標是讓系統從 "靜態架構" 走向 "動態生命"。
重點在於 MVP 的可視化 (Desktop Pet) 與價值循環 (Economy)。

## 2. 現狀分析 (Current Status)
*   **Infrastructure**: 🟢 95% (Stable).
*   **Memory/Ingestion**: 🟢 攝入 25,000+ 片段 (Background Running).
*   **Desktop Pet**: 🟡 Logic Exists (`desktop_pet.py`), Visuals Missing.
*   **Economy**: 🟡 Logic Exists (`economy_manager.py`), Game Loop Missing.
*   **Meta-Formulas**: 🔴 Static Only, Dynamic Generation Missing.

## 3. 開發路線圖 (Execution Roadmap)

### [Step 1] 深度認知分析 (Cognitive Analysis)
*   **任務**: 執行 `analyze_roadmap_from_logs.py`。
*   **目的**: 從攝入的活動日誌中提取 "用戶潛意識裡的具體需求" (如對 "物理世界"、"預測" 的具體看法)，並將其轉化為 `Desktop Pet` 的性格參數 (Personality Parameters)。
*   **Deliverable**: `docs/01-summaries-and-reports/ROADMAP_FROM_LOGS.md`

### [Step 2] 電子寵物視覺化 (Desktop Pet Visualization)
*   **任務**: 實現 `Frontend` 與 `Desktop App` 的視覺對接。
*   **技術**:
    *   使用 `Three.js` 或 `Live2D` (集成於 Next.js/Electron)。
    *   **Frontend**: 於 `apps/frontend-dashboard/src/components/DesktopPet` 建立可視化組件。
    *   **Desktop App**: 更新 `apps/desktop-app/electron_app/renderer.js` 以支持透明窗口覆蓋與點擊穿透。
    *   **[Insight] Sandbox Mode**: 實現一個 2D 網格視圖 (`2D Grid`)，支持 D-pad 控制與挖掘 (`Digging`)。
    *   **[Insight] Inventory**: 實現拖拽式背包 (`Drag-and-Drop`) 與合成系統 (`Crafting`)。
    *   綁定 `desktop_pet.py` 的狀態 (`idle`, `interacting`) 到 UI。

### [Step 3] 經濟系統閉環 (Economy Loop Integration)
*   **任務**: 將 `EconomyManager` 連接到 `HybridBrain` 與 `DesktopPet`。
*   **功能**:
    *   **Earn**: 用戶與 AI 高質量對話 -> 增加 `Favorability` -> 觸發 `Meta-Formula` -> 獎勵 `Coins`。
    *   **Burn**: 用戶消耗 `Coins` 購買 "寵物裝飾" 或 "高級模型思考時間" (Gemini Pro Access)。
*   **Deliverable**: 一個完整的 "對話挖礦" (Chat-to-Earn) 原型。

### [Step 4] 自我學習自動化 (Automated Self-Evolution - ICE Model)
*   **任務**: 激活 `ExperienceReplay`。
*   **機制**:
    *   採用 **ICE 策略** (Investigate -> Consolidate -> Exploit)，如日誌中所述。
    *   **Investigate**: 每日對話嘗試不同風格 (`Orchestrator` 隨機突變)。
    *   **Consolidate**: 夜間歸納有效策略 (`Auto-Fix` 日誌分析)。
    *   **Exploit**: 更新 `VectorStore` 中的 "Best Practices" 供次日使用 (Gödel Agent 概念)。

## 4. 立即行動 (Immediate Actions)
1.  等待 **Ingestion Script** 完成 (預計還需 5-10 分鐘)。
2.  重啟後端服務 (`Restart Backend`) 以加載新數據庫。
3.  執行 **Step 1 (Analysis)**。

---
*Created: 2026-01-14*
