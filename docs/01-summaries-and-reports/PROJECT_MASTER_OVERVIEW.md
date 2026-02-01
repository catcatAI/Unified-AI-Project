# Unified AI Project Master Overview (總攬與詳情)

## 1. 項目總結 (Project Summary)

Unified AI Project 是一個**架構優先 (Architecture-First)** 的低資源 AGI/ASI 探索項目。其核心理念是通過複雜的認知架構（而非單純堆砌模型參數）來實現通用人工智能。
目前的 MVP (最小可行性產品) 目標是構建一個具備**桌面寵物 (Desktop Pet)** 形態和內置**經濟系統 (Economic System)** 的自我演化 AI。

*   **核心目標**: 在消費級硬件上運行具備自我修正、持續學習能力的 AGI 原型。
*   **當前狀態**: 基礎設施 (Infrastructure) 與核心認知架構 (Cognitive Architecture) 已基本完成。MVP 應用層 (Gameplay) 尚處於早期開發階段。
*   **關鍵成就**: 實現了基於行為樹 (Behavior Tree) 的認知編排器、混合大腦 (Hybrid Brain) 接口、以及本地向量記憶系統 (HAM)。

---

## 2. 項目總攬 (Project Overview)

### 系統架構 (System Architecture)
項目採用 Monorepo 結構，包含三個主要端點：
*   **Backend (大腦)**: 基於 Python FastAPI，承載所有 AI 邏輯、記憶與決策。
*   **Frontend (儀表板)**: 基於 Next.js，提供開發者調試、監控與交互界面。
*   **Desktop App (軀體)**: 基於 Electron，作為用戶桌面的具現化 AI 形象 (Desktop Pet)。

### 進度概覽 (Progress Overview)
| 領域 (Domain) | 完成度 (Completion) | 狀態 (Status) |
| :--- | :--- | :--- |
| **基礎設施 (Infrastructure)** | **95%** | 🟢 成熟 (Stable) - Docker, CI/CD, Testing Ready |
| **核心 AI (Core AI)** | **75%** | 🟡 完善中 (Refining) - 記憶與感知已上線 |
| **工具系統 (Tooling)** | **90%** | 🟢 成熟 (Stable) - 搜索、計算、記憶檢索可用 |
| **MVP 應用 (Desktop Pet)** | **20%** | 🔴 早期 (Early) - 僅基礎通信，無圖形/物理引擎 |
| **經濟系統 (Economy)** | **10%** | 🔴 規劃中 (Planning) - 僅數據模型 |

---

## 3. 細節與子系統 (Details & Subsystems)

本項目遵循 **M1-M6 認知架構** 標準：

### M1: 感知 (Perception) - VDAF System
*   **功能**: 將多模態輸入 (文本、圖像、音頻) 轉化為統一的張量或語義表達。
*   **組件**: `VDAFManager`, `VisionService`, `AudioService`
*   **狀態**: ✅ 文本與基礎音頻/視覺流已打通。

### M2: 記憶 (Memory) - HAM (Hierarchical Associative Memory)
*   **功能**: 存儲短期交互與長期經驗，支持語義檢索。
*   **組件**: `HAMMemoryManager`, `VectorStore` (Local JSON/ChromaDB), `ExperienceReplay`
*   **狀態**: ✅ 向量存儲與 RAG (檢索增強生成) 已上線。**Activity Log Ingestion** (活動日誌攝入) 已驗證支持 700MB+ 數據集。

### M3: 邏輯與公式 (Logic & Formulas)
*   **功能**: 處理確定性邏輯、數學運算與符號推理。
*   **組件**:
    *   **Formula Engine**: 動態公式評估引擎 (Python AST based)。
    *   **Symbolic Core**: 符號邏輯推導核心。
    *   **Meta-Formulas (元公式)**: 定義邏輯之間關係的高階規則 (位於 `apps/backend/src/ai/formula_engine`)。
*   **狀態**: 🟡 基礎引擎可用，但在對話中的深度集成仍需加強。

### M4: 決策 (Decision) - Cognitive Orchestrator
*   **功能**: 根據感知與記憶，規劃並執行行動。
*   **組件**: `CognitiveOrchestrator`, `BT Engine` (Behavior Tree), `PlanningManager`
*   **狀態**: ✅ 行為樹引擎已作為核心調度器運行，支持動態工具調用。

### M5: 行動 (Action) - Tools & Agents
*   **功能**: 執行具體任務或調用外部 API。
*   **組件**: `ToolRegistry`, `AgentManager`
*   **工具箱 (Tools)**:
    *   `SearchTool`: 網絡搜索 (模擬/真實)。
    *   `CalculatorTool`: 數學運算。
    *   `MemoryRetrievalTool`: 歷史回溯。
    *   `CodeAnalysisTool`, `DataAnalysisTool`: 代碼與數據處理 (基礎封裝)。

### M6: 安全與自我 (Security & Self) - Immune System
*   **功能**: 監控系統健康，防止有害輸出或指令注入。
*   **組件**: `LinguisticImmuneSystem` (LIS), `SandBoxExecutor`
*   **狀態**: ✅ 基礎輸入過濾與沙盒執行已實裝。

---

## 4. 模型與大模型 (Models & LLMs)

### 大語言模型 (Large Models)
*   **Ollama (Local)**:
    *   `tinyllama:latest`: 當前主力模型，用於快速響應與對話。已優化 Prompt Engineering 以避免幻覺。
*   **Gemini (Cloud)**:
    *   `gemini-pro`: 備用/高智商模式 (需 API Key)。
*   **OpenAI (Cloud)**:
    *   `gpt-4o`: 兼容接口支持。

### 小模型 (Small Models)
*   **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (用於向量記憶)。
*   **Audio**: `YAMNet` (計劃中，用於環境音識別)。
*   **Vision**: `EfficientNet` (計劃中，用於物體識別)。

---

## 5. 查缺補漏 (Gap Analysis)

### 🔴 未完成 (Critical Missing)
1.  **Desktop Pet Visuals**: 電子寵物的視覺呈現 (Live2D 或 3D模型) 尚未集成。
2.  **Physics Engine**: 簡單的物理反饋系統 (如寵物碰撞、重力) 缺失。
3.  **Economic System Logic**: 代幣賺取、消費循環的具體數值邏輯尚未實現代碼。

### 🟡 需完善 (Needs Improvement)
1.  **Learning Loops (學習迴路)**: `ExperienceReplay` 和 `KnowledgeDistillation` 文件已建立，但自動化觸發機制 (如每晚自動總結學習) 尚未完全串接。
2.  **Meta-Formula Integration**: 元公式目前更多是靜態規則，缺乏動態生成的 "新公式" 能力 (即 AI 自己寫邏輯)。
3.  **HSP Protocol Refinement**: `hsp_protocol.py` (高速通信協議) 仍為早期版本，需優化以支持實時遊戲數據傳輸。

### ✅ 已完成 (Completed & Verified)
1.  **Core Loop**: 用戶輸入 -> 感知 -> 決策 -> 行動 -> 反饋 閉環已打通。
2.  **Memory RAG**: 支持導入外部巨量日誌並精準檢索。
3.  **System Stability**: 經由 Fuzz Testing 驗證，系統魯棒性強，處理 `Timeout` 和 `Error` 機制完善。

---

## 6. 下一步行動建議 (Next Steps)

1.  **MVP Focus**: 優先開發 `Desktop Pet` 的視覺交互與 `Economic System` 的基礎循環，讓系統 "活" 起來。
2.  **Automation**: 部署 `Cron Job` 或後台任務，激活 `Experience Replay` 的夜間自我學習流程。
3.  **Expansion**: 擴展 `Symbolic Core`，嘗試讓 AI 通過 `ToolUse` 寫出簡單的 Python 腳本並存為新的 `Skill` (技能)。
