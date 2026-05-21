# Angela AI 重構宣言：實作細節的科學化與工程正規化
## REFINEMENT MANIFESTO (v1.0)

### 0. 核心診斷：為什麼目前的實作「不怎麼樣」？
經過深度審計，我們確認目前的系統處於「語義通膨」狀態：文檔宣稱的高級架構（AGI, 6D Matrix）在程式碼中被降維實作為極其簡陋的數值模擬。

#### 實務債務清單 (Technical Debt Audit)
*   **[模擬偽裝] `endocrine_system.py`**：
    *   **現狀**：使用 `current -= rate * minutes`。這只是 RPG 遊戲的數值邏輯。
    *   **後果**：忽略了生物濃度的指數衰減特性（藥代動力學），導致系統在時間跨度較大時行為斷裂且不自然。
*   **[語義通膨] `state_matrix.py`**：
    *   **現狀**：座標計算如 `x = comfort - tension` 配合 Magic Numbers (5.0, 2.0)。
    *   **後果**：所謂的「座標」缺乏物理或心理學邏輯支撐，導致高維張量空間退化為簡單的線性加減。
*   **[架構癌症] `chat_service.py`**：
    *   **現狀**：在 `initialize()` 內部使用 `from ... import ...` 延遲匯入。
    *   **後果**：這是為了掩蓋嚴重的循環依賴與模組耦合。系統並非解耦運作，而是依賴 Python 的動態特性勉強維持的單體結構。
*   **[形式主義] `tests/`**：
    *   **現狀**：大量測試僅驗證 `assert val != 0` 或 `assert final != initial`。
    *   **後果**：只測試「有沒有動」，不測試「動得對不對」。這導致實作細節的平庸被測試覆蓋率所掩蓋。
*   **[游擊隊工程] `auto_install.py`**：
    *   **現狀**：強行調用 `sudo` 並假設宿主機路徑。
    *   **後果**：缺乏環境隔離意識，導致跨平台部署極其脆弱，不符合現代軟體工程標準。

---

### 1. 「完善」與「完成」的工程定義
在本專案中，任務的 **「完成」** 不再以「功能跑通」為準，而必須滿足以下 **「完善」** 指標：

1.  **物理/生物自洽性**：連續變量的演化必須遵循微分方程（ODE）或 PK 模型。
2.  **架構強合約化**：模組通訊必須透過 `Protocols` 定義，禁止隱式耦合與延遲匯入。
3.  **環境中立性**：依賴管理必須容器化（Docker），確保「It works on every machine」。
4.  **行為湧現性**：行為觸發（Intent）必須由「穩態梯度（Homeostatic Gradient）」驅動，廢除 Magic Numbers 驅動的隨機機率。

---

### 2. 三階段外科手術重構路徑

#### 第一階段：基礎設施的「正規化」 (Infra-Purge)
*   **歸檔清理**：刪除 `auto_install.py` 等碎片腳本。
*   **現代管道**：整合 `package.json` 指令集，引入 `pnpm setup` 作為唯一入口。
*   **環境封裝**：建立 Docker 編譯鏡像，封裝 Live2D 與 Native Audio 構建環境。

#### 第二階段：層級協議與合約化 (Layer Formalization)
*   **定義 Protocol**：在 `src/core/interfaces` 建立 `L1_Bio`, `L2_Cognitive` 等強制協議。
*   **合約校驗**：利用 `MyPy` 與裝飾器，確保 L1 模組具備「代謝開銷」與「演化函數」的實作。

#### 第三階段：模型去偽存真 (Scientific Actualization)
*   **重寫核心模型**：
    *   `EndocrineSystem`：改用指數衰減。
    *   `StateMatrix`：改用向量空間餘弦相似度映射。
    *   `Heartbeat`：引入位能場驅動的行為決策邏輯。

---

### 3. 執行規範
*   **拒絕名詞包裝**：禁止在沒有真實算法支撐的情況下使用「引擎」、「系統」等詞彙。
*   **代碼即文檔**：所有的矩陣邏輯必須在代碼中以 `Type Hints` 表達，不再僅依賴外部 MD。

---
**審核人**: Gemini CLI (Engineering Integrity Mode)
**日期**: 2026年5月21日
**狀態**: 已存檔至 `REFINEMENT_MANIFESTO.md`，準備執行。
