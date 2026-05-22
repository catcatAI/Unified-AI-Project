# Angela AI 分層配置架構與自演化規範 (v1.0)
## Tiered Configuration Architecture (TCS)

### 0. 核心設計理念：異質隔離與優先級覆蓋
為了終結代碼中的「硬編碼」病灶，並確保 Angela 的自演化不會破壞系統地基，我們將配置分為三個等級，每個等級均遵循 **[Default -> User -> Angela]** 的覆蓋鏈條。

---

### 1. 配置等級定義 (Configuration Tiers)

#### **S級：系統級 (System/Core Tier)**
*   **職責**：核心基礎設施、安全性金鑰、權限邊界。
*   **包含內容**：API Keys、Database 連接、ABC 安全權限、環境路徑。
*   **儲存路徑**：`configs/system/` 與 `.env`。
*   **演化權限**：低 (僅在用戶明確授權下修改環境變量名)。

#### **A級：標準級 (Standard/Runtime Tier)**
*   **職責**：Angela 正常運行所需的核心邏輯參數、科學模型、文本資產。
*   **包含內容**：
    *   **科學域**：內分泌 PK 參數、位能場權重、座標投影矩陣。
    *   **文本域**：Prompt 模板、對話風格、Live2D 動畫觸發路徑。
    *   **行為域**：喚醒度閾值、移動速度、決策係數。
*   **儲存路徑**：`configs/standard/`。
*   **演化權限**：高 (Angela 可根據對話反饋微調這些參數)。

#### **M級：擴展級 (MOD/External Tier)**
*   **職責**：非標準功能、第三方插件、實驗性能力。
*   **包含內容**：用戶自定義 MOD、外部 API 擴展包。
*   **儲存路徑**：`configs/mods/`。
*   **演化權限**：中。

---

### 2. 覆蓋優先級鏈 (Priority Chain)

在讀取任何配置時，系統會自動按以下順序進行「深度合併」：
1.  **Default (`*.default.yaml`)**：由開發者提供，保證系統能跑起來。
2.  **User (`*.user.yaml`)**：由用戶手動修改，具有中優先級。
3.  **Angela (`*.evolved.yaml`)**：由 Angela 在自演化循環中生成，具有最高優先級。

> **公式**：`FinalConfig = Default + User + Angela`

---

### 3. 重構任務與路徑 (Refinement Roadmap)

#### **Step 1: 物理路徑正規化**
*   搬遷 `configs/formula_configs/` 至 `configs/standard/science/`。
*   搬遷 `api_keys.yaml` 至 `configs/system/keys.yaml`。

#### **Step 2: 實作 `TieredConfigLoader`**
*   支持「三層合併」邏輯。
*   建立緩存機制，確保熱加載 (Hot Reload) 的性能。

#### **Step 3: 徹底清除硬編碼 (The Final Purge)**
*   **Heartbeat**：將 `arousal > 0.7` 與 `random < 0.1` 搬遷至 `standard/behavior.yaml`。
*   **StateMatrix**：將預設座標、初始值、軸名稱全數從代碼中抽離至 `standard/matrix_meta.yaml`。

#### **Step 4: 更新自演化寫入器 (`ConfigMutator`)**
*   **規則**：Angela 的自演化寫入器 **禁止** 修改 `*.default.yaml` 與 `*.user.yaml`。
*   **動作**：所有的學習結果必須寫入對應類別的 `*.evolved.yaml`。

---
**完善聲明**：配置不只是「變量存儲」，它是數位生命的「表觀遺傳學 (Epigenetics)」。分層架構確保了核心基因 (Default) 的穩定，同時允許後天學習 (Angela) 的靈活性。
**起草人**: Gemini CLI (System Architect Mode)
**日期**: 2026年5月21日
