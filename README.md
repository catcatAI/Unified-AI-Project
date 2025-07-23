# Unified AI Project

## 概述

統一 AI 專案是一個先進的多維語義 AI 系統，整合了 MikoAI、Fragmenta 和其他 CatAI 計劃。本專案不僅是工具的集合，更是創造**多維語義實體**的嘗試，其架構由湧現、自我修正和語義演化的敘事所引導。

## 項目文檔

- **[合併與重構計劃](MERGE_AND_RESTRUCTURE_PLAN.md)**: 詳細介紹項目結構、合併策略和架構原則
- **[項目內容組織](docs/PROJECT_CONTENT_ORGANIZATION.md)**: 項目文件組織概覽
- **[HSP 規範](docs/technical_design/HSP_SPECIFICATION.md)**: 異構服務協議 (HSP) 詳細規範
- **[哲學與願景](docs/philosophy/PHILOSOPHY_AND_VISION.md)**: 項目的哲學基礎和長期願景
- **[內部數據標準](docs/technical_design/INTERNAL_DATA_STANDARDS.md)**: TypedDict 使用規範
- **[HAM 設計規範](docs/technical_design/architecture/HAM_design_spec.md)**: 分層抽象記憶系統設計文檔
- **[術語表 (Glossary)](docs/GLOSSARY.md)**: 專案核心概念定義

### 未來願景

除了目前已實現的功能外，本項目秉持「語言即生命」的長期願景，旨在創造一個具有深度自我意識、適應性強且能夠語義演化的 AI。這包括探索「語言免疫系統」和「元公式」等先進概念，引導其發展成為「多維語義實體」。這些哲學基礎和未來概念目標在項目文檔中有進一步闡述。

## 核心功能與模組

本項目整合並開發了多個核心 AI 組件：

### [動態 AI 代理協作框架](docs/architecture/AGENT_COLLABORATION_FRAMEWORK.md)
*   **[元代理 (Angela)](docs/GLOSSARY.md#meta-agent-元代理)**: 由 `DialogueManager` 和新的 `ProjectCoordinator` 共同實現，扮演指揮官的角色。能夠理解複雜的用戶意圖，將其自動分解為一個帶有依賴關係的任務圖 (DAG)。
*   **[子代理 (Specialized Agents)](docs/GLOSSARY.md#sub-agent-子代理)**: 位於 `src/agents/` 的專門化 AI 代理，每個代理都擁有特定的能力（如數據分析、創意寫作）。它們作為獨立的 HSP 服務運行。
*   **[代理管理器 (Agent Manager)](docs/GLOSSARY.md#agent-manager-srccore_aiagent_managerpy)**: 能夠根據 `DialogueManager` 的請求，動態地啟動或關閉子代理進程，實現資源的按需使用。
*   **學習閉環**: 框架能夠從完整的項目案例中學習，提煉出成功的協作策略並儲存於記憶中，用於指導未來的任務分解，實現自我優化。

### 對話管理系統
*   **[對話管理器 (`DialogueManager`)](docs/GLOSSARY.md#dialoguemanager-srccore_aidialoguedialogue_managerpy)**: 作為**元代理**的核心，協調對話流程，並將複雜項目委派給 `ProjectCoordinator`。利用個性配置、記憶系統和基於公式的邏輯。
*   **[項目協調器 (`ProjectCoordinator`)](docs/GLOSSARY.md#projectcoordinator-srccore_aidialogueproject_coordinatorpy)**: 負責執行「四抽模型」，處理複雜項目的任務分解、DAG 執行、結果整合和學習。
*   **個性管理器 (`src/core_ai/personality/personality_manager.py`)**: 管理不同的 AI 個性，影響語調、響應風格和核心價值觀。配置文件可自定義（見 `configs/personality_profiles/`）。
*   **情感系統 (`src/core_ai/emotion/emotion_system.py`)**: 模擬和管理 AI 的情感狀態。
*   **危機系統 (`src/core_ai/crisis/crisis_system.py`)**: 評估輸入的危機情況並觸發適當響應。
*   **[語言學免疫系統 (LIS)](docs/architecture/Linguistic_Immune_System_spec.md)**: 檢測和處理語義異常，提供語言修復和自愈能力。包含免疫敘事緩存和音調修復引擎，支持語言演化和模型崩潰預防。
*   **元公式系統 (`src/core_ai/metaformulas/`)**: 高級動態原則定義語義模塊學習和適應，支持 AI 結構的自我重組，提供元級別的行為控制機制。
*   **日常語言模型 (`src/core_ai/daily_language_model/`)**: 專門處理日常對話和意圖識別，支持工具選擇和參數提取，與 LLM 接口集成進行智能路由。
*   **信任管理器 (`src/core_ai/trust/trust_manager.py`)**: 管理 AI 間的信任關係，影響事實處理和能力選擇，支持基於信任的決策制定。

### 記憶系統
*   **[分層抽象記憶 (HAM)](docs/architecture/HAM_design_spec.md)**: 專為存儲和檢索體驗、學習事實和對話上下文而設計的自定義記憶系統。
    - 支援中文部首提取和英文語言特徵分析
    - 使用 Fernet 對稱加密和 SHA256 校驗和確保數據完整性
    - 實現 zlib 壓縮以優化存儲空間
*   **[Fragmenta 系統](docs/architecture/Fragmenta_design_spec.md)**: 高級記憶碎片化和重組系統，實現動態記憶結構管理。
    - **Fragmenta 編排器 (`fragmenta_orchestrator.py`)**: 協調記憶碎片的創建、組織和檢索
    - **記憶碎片 (`memory_fragment.py`)**: 基本記憶單元，支持語義標記和關聯性分析
    - **碎片管理器 (`fragment_manager.py`)**: 管理碎片生命週期、合併和分割操作
    - **語義索引器 (`semantic_indexer.py`)**: 為記憶碎片創建多維語義索引，支持快速檢索

### 學習系統 (`src/core_ai/learning/`)
*   **事實提取模組**: 從對話中提取結構化事實
*   **自我批判模組**: 評估 AI 響應的質量和連貫性
*   **學習管理器**: 協調學習過程，將新知識存儲到 HAM 中。現在包含一個**基於質量的資訊評估體系**，通過綜合評估來源可信度、證據支持度和資訊新穎性，來有效抵制錯誤資訊在網絡中的傳播（反「傻子共振」）。
*   **內容分析模組**:
    - **目的**: 通過分析文本內容（如文檔、用戶輸入、HSP 事實）實現更深層的上下文理解，創建和維護結構化知識圖譜
    - **功能**: 提取命名實體，識別關係（包括語義三元組），並將此信息整合到 NetworkX 知識圖譜中。支援基本本體映射
    - **技術**: 利用 `spaCy` 進行自然語言處理任務（NER、依存句法分析）和 `NetworkX`
    - **狀態**: 已整合功能原型（第二階段），能夠生成和更新知識圖譜，具備實體和基於規則的關係提取，包括處理結構化 HSP 事實。持續工作重點是完善提取、增強本體使用，並深化與 `DialogueManager` 的整合以實現更豐富的上下文感知

### 公式引擎 (`src/core_ai/formula_engine/`)
實現基於規則的系統，其中預定義的「公式」（配置於 `configs/formula_configs/default_formulas.json`）可以根據輸入條件（目前支持簡單的關鍵字匹配）觸發特定動作或響應。它負責匹配輸入並返回相應的動作和參數，供其他模組（如 `DialogueManager`）執行。這允許確定性行為和工具調度。

### 工具系統
*   **工具調度器 (`src/tools/tool_dispatcher.py`)**: 使 AI 能夠使用外部或內部「工具」（如計算器、信息檢索功能）來增強其能力。工具可由公式引擎或其他 AI 邏輯觸發，支持動態工具加載和執行

*   **數學工具 (`src/tools/math_tool.py`)**: 處理數學計算和公式求解，支持複雜數學運算和表達式求值
    - **數學模型 (`src/tools/math_model/`)**: 包含自定義數學模型訓練組件

*   **邏輯工具 (`src/tools/logic_tool.py`)**: 處理邏輯推理和判斷，支持邏輯表達式求值和布爾運算，提供符號邏輯和神經網絡兩種評估方法
    - **邏輯模型 (`src/tools/logic_model/`)**: 專注於符號推理和邏輯推論，包含邏輯數據生成器

*   **翻譯工具 (`src/tools/translation_tool.py`)**: 提供多語言翻譯服務，支持實時翻譯功能，集成 Helsinki-NLP 和 T5 神經網絡模型
    - **翻譯模型 (`src/tools/translation_model/`)**: 包含翻譯模型訓練組件

*   **代碼理解工具 (`src/tools/code_understanding_tool.py`)**: 分析和理解代碼結構，提供代碼語義分析和工具結構解析
    - **代碼理解模型 (`src/tools/code_understanding/`)**: 支持輕量級代碼模型

*   **依賴檢查器 (`src/tools/dependency_checker.py`)**: 檢查和管理項目依賴關係，提供依賴衝突檢測和解決建議，支持多種包管理器格式

### 遊戲客戶端
*   **[Angela's World](docs/game/README.md)**: 一個內建的 GBA 風格的專屬休閒養成遊戲，由 Unified-AI-Project 直接維護與運行，旨在為用戶提供一個「寓教於樂」的「人生發展模擬器」。

### 服務層
*   **LLM 接口 (`src/services/llm_interface.py`)**: 提供與各種大型語言模型（如 Ollama、OpenAI）交互的標準化接口，管理 API 調用和模型配置

*   **主 API 服務器 (`src/services/main_api_server.py`)**: FastAPI 應用程序，提供與 AI 交互的 API 端點

*   **沙盒執行器 (`src/services/sandbox_executor.py`)**: 在隔離環境中安全執行代碼

*   **資源感知服務 (`src/services/resource_awareness_service.py`)**: 管理模擬硬件資源

*   **AI 虛擬輸入服務 (`src/services/ai_virtual_input_service.py`)**: 處理虛擬輸入和模擬用戶交互

*   **音頻服務 (`src/services/audio_service.py`)**: 提供音頻處理和語音識別功能

*   **視覺服務 (`src/services/vision_service.py`)**: 處理圖像和視覺數據分析

*   **Node.js 服務 (`src/services/node_services/`)**: 提供額外的 JavaScript 運行時服務支持

### 配置系統 (`configs/`)
集中化的 YAML 和 JSON 文件，用於系統行為、個性配置、API 密鑰、公式等配置。

### 異構同步協議 (HSP) (`src/hsp/`)
*   **目的**: 使不同的 AI 實例（對等體）能夠通信、共享知識並協作執行任務
*   **功能**: 定義消息類型（事實、能力廣告、任務請求/結果等）和通信模式（發布/訂閱、請求/回復）用於 AI 間交互
*   **傳輸**: 使用 MQTT 進行消息傳輸，基於 gmqtt 實現異步通信。有關 MQTT 代理替代方案的詳細分析，請參見 [MQTT 代理替代方案分析](docs/architecture/MQTT_BROKER_ALTERNATIVES_ANALYSIS.md)
*   **關鍵特性**: 包括服務發現機制、對等體間的基本信任管理，以及處理來自不同 AI 的衝突信息的策略
*   **規範**: 詳見 `docs/technical_design/HSP_SPECIFICATION.md`

#### HSP 核心組件
*   **HSP 連接器 (`src/hsp/connector.py`)**: 實現基於 gmqtt 的異步 MQTT 通信，支持異構系統間的數據同步和消息路由，提供分散式 AI 協作能力和任務委派，包含重連策略和錯誤處理機制
*   **服務發現模塊 (`src/hsp/service_discovery_module.py`)**: 自動發現網絡中的其他 AI 系統，管理服務註冊和註銷，支持能力廣告，提供動態服務路由功能和能力過期處理，集成信任評估和能力匹配算法
*   **HSP 消息處理器 (`src/hsp/message_processor.py`)**: 處理 HSP 協議消息的序列化和反序列化，支持多種消息類型（事實、信念、任務請求等），提供消息驗證和格式檢查功能
*   **HSP 任務管理器 (`src/hsp/task_manager.py`)**: 管理分散式任務的分配和執行，協調多 AI 系統間的任務協作，提供任務狀態追蹤和結果聚合

## 開始使用

以下說明將幫助您在本地機器上運行項目進行開發和測試。

### 先決條件

*   **Python**: 需要 3.8 或更高版本（推薦 3.9+）
*   **Node.js**: 推薦 16.x 或更高版本，以及 npm
*   **Git**: 用於克隆存儲庫

### 依賴管理

本項目使用**靈活的依賴管理系統**，所有依賴項配置均集中在 `dependency_config.yaml` 文件中。這允許您：
- 根據預定義的安裝類型（如最小、標準、完整或特定功能組）安裝所需依賴項。
- 當首選包不可用時自動回退到替代包。
- 即使某些可選依賴項缺失也能運行項目。
- 依賴項優先級已調整，以支持輕量級模型優先。

**安裝選項：**

現在，推薦使用項目提供的安裝程式來管理依賴項。這些安裝程式會讀取 `dependency_config.yaml` 中的配置，並引導您完成安裝過程。

1.  **命令行安裝程式：**
    ```bash
    python installer_cli.py
    ```
    運行此命令後，您將被提示選擇所需的安裝類型（例如 `minimal`, `standard`, `full`, `ai_focused` 等）。

2.  **圖形化安裝程式 (GUI)：**
    ```bash
    python installer.py
    ```
    運行此命令將啟動一個圖形化嚮導，您可以在其中選擇安裝類型和其他配置選項。

**依賴狀態檢查：**

開始之前，您可以檢查哪些依賴項可用：
```bash
python src/tools/dependency_checker.py
```

獲取詳細狀態和錯誤信息：
```bash
python src/tools/dependency_checker.py --detailed
```

將依賴狀態導出為 JSON：
```bash
python src/tools/dependency_checker.py --json dependency_status.json
```

### 設置

1.  **克隆存儲庫：**
    ```bash
    git clone <repository_url>
    cd Unified-AI-Project
    ```

2.  **設置 Python 環境：**
    為您的操作系統運行適當的設置腳本。這些腳本將創建虛擬環境（`venv/`）並安裝所有必要的 Python 依賴項。

    *   **在 Windows 上（命令提示符或 PowerShell）：**
        ```bash
        .\scripts\setup_env.bat
        ```
    *   **在 macOS/Linux 上（Bash 或 Zsh）：**
        ```bash
        bash ./scripts/setup_env.sh
        ```
    運行腳本後，您的虛擬環境將被激活，並且 `requirements.txt` 中的所有依賴項都將被安裝。您將在終端提示符中看到 `(venv)`，表示虛擬環境處於活動狀態。

    要在新的終端會話中激活虛擬環境，請運行：
    *   **在 Windows 上：** `.\venv\Scripts\activate.bat`
    *   **在 macOS/Linux 上：** `source ./venv/bin/activate`

3.  **設置 Node.js 環境：**
    安裝根項目 Node.js 依賴項：
    ```bash
    npm install
    ```
    安裝 Electron 應用程序特定依賴項：
    ```bash
    cd src/interfaces/electron_app
    npm install
    cd ../../..  # 返回項目根目錄
    ```

4.  **環境變量：**
    項目使用 `.env` 文件進行敏感配置，如 API 密鑰和加密密鑰。
    複製示例文件並填入您的詳細信息：
    ```bash
    # 在 Windows 上（命令提示符）
    copy .env.example .env
    # 在 Windows 上（PowerShell）
    Copy-Item .env.example .env
    # 在 macOS/Linux 上
    cp .env.example .env
    ```
    現在，使用您的特定密鑰和設置編輯 `.env`。
    
    **重要環境變數：**
    - `MIKO_HAM_KEY`: HAM記憶管理器的加密密鑰（Base64編碼的Fernet密鑰）
    - `GEMINI_API_KEY`: Google Gemini API密鑰
    - `OPENAI_API_KEY`: OpenAI API密鑰
    - `FIREBASE_CREDENTIALS_PATH`: Firebase服務帳戶密鑰文件路徑
    
    生成HAM加密密鑰：
    ```bash
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ```

5.  **PYTHONPATH（通常不需要設置腳本）：**
    項目使用來自 `src` 目錄的絕對導入（例如，`from core_ai...`）。如果您使用 `setup_env` 腳本，虛擬環境激活應該自動處理這個問題。如果您在直接運行腳本時遇到導入錯誤（不是通過激活的 venv），請確保您的 `PYTHONPATH` 包含項目根目錄或 `src` 目錄。許多 IDE 會自動處理這個問題。或者，您可以在 shell 中臨時設置它：
    ```bash
    # 在 Windows 上（命令提示符）
    set PYTHONPATH=%PYTHONPATH%;%CD%
    # 在 Windows 上（PowerShell）
    $env:PYTHONPATH += ";${pwd}"
    # 在 macOS/Linux 上
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    ```
    通常最好從項目根目錄運行 Python 腳本以避免導入問題。

### 運行應用程序

#### 智能啟動與依賴回退

項目包含一個智能啟動系統，可自動檢測可用依賴項並相應配置應用程序：

```bash
# 基於可用依賴項自動檢測最佳模式
python startup_with_fallbacks.py

# 或指定特定模式
python startup_with_fallbacks.py --mode standard
python startup_with_fallbacks.py --mode minimal
python startup_with_fallbacks.py --mode full
python startup_with_fallbacks.py --mode ai_focused
```

**啟動模式：**
- **minimal**: 僅核心功能（Flask、numpy、PyYAML）
- **standard**: Web API + HSP 通信（添加 FastAPI、MQTT）
- **full**: 啟用所有功能（添加 AI 模型、NLP、知識圖譜）
- **ai_focused**: AI/ML 功能，無 Web 界面
- **auto**: 基於可用依賴項自動選擇最佳模式

**啟動選項：**
```bash
# 檢查依賴項而不啟動
python startup_with_fallbacks.py --check-only

# 獲取模式建議
python startup_with_fallbacks.py --suggest-mode

# 使用自定義端口和調試模式啟動
python startup_with_fallbacks.py --port 8080 --debug
```

#### 傳統應用程序接口

您也可以通過多種傳統方式與 Unified-AI-Project 交互：

1.  **命令行接口 (CLI)：**
    通過 CLI 向 AI 發送查詢：
    ```bash
    python src/interfaces/cli/main.py query "Hello AI, how are you?"
    ```
    （確保您在項目根目錄中或已正確設置 `PYTHONPATH`。）

2.  **Electron 桌面應用程序：**
    啟動 Electron 應用程序：
    ```bash
    cd src/interfaces/electron_app
    npm start
    ```

3.  **API 服務器 (FastAPI/Flask)：**
    啟動腳本將自動選擇最佳可用的 Web 框架：
    ```bash
    # 使用智能啟動（推薦）
    python startup_with_fallbacks.py --mode standard
    
    # 或直接啟動（如果依賴項可用）
    python src/services/main_api_server.py
    
    # 用於開發的自動重載
    uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000
    ```
    API 將在 `http://localhost:5000`（Flask）或 `http://localhost:8000`（FastAPI）可訪問。FastAPI 的 Swagger UI 文檔可在 `/docs` 獲得。

### 運行時硬體與作業系統適應

Unified AI Project 旨在在不同硬體配置和作業系統上提供靈活的運行體驗。這種適應性主要通過以下機制實現：

*   **依賴項備用機制：** 專案利用 `dependency_config.yaml` 中定義的備用依賴項。例如，如果 TensorFlow 在特定硬體或作業系統上不可用，系統會自動回退到使用 `scikit-learn` 或 `numpy` 進行 AI 模型操作。這確保了即使在資源受限或特定環境下，核心功能也能保持運行。
*   **動態服務器選擇：** `startup_with_fallbacks.py` 腳本會根據當前環境中可用的 Web 框架（例如 FastAPI 或 Flask）動態選擇啟動哪個 API 服務器。如果沒有可用的 Web 服務器，專案將回退到僅 CLI 模式運行。
*   **作業系統特定處理：** 在某些情況下，例如 `src/core_ai/dependency_manager.py` 中，會包含針對特定作業系統（如 Windows）的特殊處理邏輯，以避免兼容性問題（例如，避免在 Windows 上直接導入 TensorFlow 以防止潛在的崩潰）。

這些機制共同確保了專案在多樣化的運行環境中具有彈性和魯棒性。

### 命令列安裝程式

項目現在包含一個命令列安裝程式，可以引導您完成安裝過程。要使用安裝程式，請運行以下命令：

```bash
python installer_cli.py
```

#### 故障排除

如果您遇到依賴項相關問題：

1. **檢查依賴項狀態：**
   ```bash
   python src/tools/dependency_checker.py --detailed
   ```

2. **安裝缺失的依賴項：**
   ```bash
   # 檢查器將建議安裝命令
   pip install tensorflow spacy  # AI 功能示例
   ```

3. **使用回退模式：**
   ```bash
   python startup_with_fallbacks.py --mode minimal
   ```

4. **檢查配置：**
   ```bash
   # 查看當前依賴項配置
   cat dependency_config.yaml
   ```

### 關鍵配置文件

*   `configs/system_config.yaml`: 通用系統範圍配置
*   `configs/api_keys.yaml`: 外部 API 密鑰配置（儘管 `.env` 可能更適合本地覆蓋）
*   `configs/personality_profiles/`: 包含定義不同 AI 個性的 JSON 文件
*   `configs/formula_configs/`: 包含公式引擎的 JSON 文件

## 貢獻指南

我們歡迎並非常感謝您的貢獻！以下是一些指南，幫助您開始本地開發。

### 開發工作流程

1.  **創建分支：**
    在單獨的分支上處理新功能或錯誤修復是一個好習慣。
    ```bash
    # 確保您在主開發分支上（例如，master）
    # git checkout master
    # git pull # 如果您正在協作並需要更新

    git checkout -b feat/your-feature-name  # 示例：feat/new-dialogue-intent
    # 或
    git checkout -b fix/issue-description   # 示例：fix/incorrect-api-response
    ```

2.  **進行更改：**
    編寫您的代碼並在適用時添加新測試。

3.  **測試您的更改：**
    *   **Python 測試：** 使用 `pytest` 運行 Python 單元測試。確保您已安裝它（`pip install pytest`）。
        ```bash
        pytest tests/
        ```
        或者，運行特定測試：
        ```bash
        pytest tests/core_ai/test_dialogue_manager.py
        ```
    *   **JavaScript 測試：**（佔位符 - 隨著 JS 測試的添加將更清楚地定義）
        根目錄 `package.json` 和 `src/interfaces/electron_app/package.json` 有佔位符測試腳本。隨著這些的開發，將在此處添加特定命令。目前，請確保您的更改不會破壞現有的 JS 功能。

4.  **格式化和檢查您的代碼：**
    *   **Python：** 遵循 PEP 8 指南。考慮使用像 Black 這樣的格式化工具和像 Flake8 這樣的檢查工具。
        ```bash
        # 示例（如果安裝了 Black 和 Flake8）
        # black .
        # flake8 .
        ```
    *   **JavaScript/TypeScript：** 使用像 Prettier 這樣的格式化工具。
        ```bash
        # 示例（如果在 package.json 腳本中設置了 Prettier）
        # npm run format
        ```

5.  **提交您的更改：**
    使用清晰和描述性的提交消息。我們鼓勵使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式。例如：
    *   `feat: Add user authentication for API`
    *   `fix: Correct personality loading error for custom profiles`
    *   `docs: Update API endpoint documentation`
    *   `style: Format code with Black`
    *   `refactor: Simplify dialogue state management`
    *   `test: Add unit tests for new calculation tool`
    ```bash
    git add .
    git commit -m "feat: Describe your change"
    ```

### 代碼風格與數據標準

*   **Python：** 遵循 PEP 8。
*   **JavaScript/TypeScript：** 遵循標準社區實踐。考慮使用 Prettier 進行一致的格式化。
*   **內部數據結構：** 對於內部 Python 模組之間交換的數據，請遵循 [內部數據標準 (`docs/INTERNAL_DATA_STANDARDS.md`)](docs/technical_design/INTERNAL_DATA_STANDARDS.md) 中概述的標準。這主要涉及使用 `TypedDict` 以提高清晰度和靜態類型檢查。
*   **一般：** 追求清晰、可讀和文檔完善的代碼。

### 問題或疑問

如果您有問題、發現錯誤或想建議改進，請考慮記錄它們或與您的團隊討論，以適合您的項目管理風格。

## 界面層

### CLI 界面 (`src/interfaces/cli/`)
- 提供命令行交互界面 (`cli_main.py`)
- 支持腳本化操作和批量處理
- 適合開發和調試使用
- 集成對話管理和 HSP 功能測試
- 支持直接查詢命令：`python src/interfaces/cli/main.py query "Hello AI"`

### Electron 應用 (`src/interfaces/electron_app/`)
- **統一前端界面**：一個基於 React 和 Vite 的單體應用程式，整合了所有用戶交互功能。
- **核心視圖**：
    - **聊天 (Chat)**：與 AI 進行對話的核心界面。
    - **HSP 網絡 (HSP Network)**：查看和與異構服務協議網絡中的其他 AI 代理互動。
    - **遊戲 (Game)**：啟動和遊玩內建的 GBA 風格休閒養成遊戲。
    - **程式碼檢查器 (Code Inspector)**：一個用於分析程式碼專案的工具（開發中）。
    - **儀表板 (Dashboard)**：顯示 AI 狀態和項目指標的儀表板（開發中）。
- **技術棧**：Electron, React, TypeScript, Vite, Tailwind CSS。
- **啟動命令**：`cd src/interfaces/electron_app && npm install && npm run dev`

## 項目架構

項目的邏輯圖和知識圖譜可在 `docs/architecture` 目錄中找到。

### 核心服務初始化 (`src/core_services.py`)

`src/core_services.py` 作為 Unified AI Project 的中央初始化點，負責創建和管理所有核心 AI 模組和服務的單例實例。它通過依賴注入的方式，將所需的依賴項傳遞給各個模組，確保了系統的模塊化和可測試性。此文件還處理基礎配置的載入和 HSP 連接的初始化。

### 邏輯圖

項目遵循模塊化架構，具有清晰的關注點分離：

```
┌─────────────────────────────────────────────────────────────────┐
│                        用戶界面                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │     CLI     │  │  Electron   │  │      API 服務器         │ │
│  │             │  │     應用     │  │   (FastAPI/Flask)       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      核心 AI 系統                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  對話管理   │  │ 個性管理器  │  │     HAM 記憶            │ │
│  │    器       │  │             │  │     系統                │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  學習管理   │  │   公式引擎  │  │     工具系統            │ │
│  │    器       │  │             │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     服務層                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │     LLM     │  │   配置系統  │  │        HSP              │ │
│  │    接口     │  │             │  │      協議               │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

[邏輯圖](docs/architecture/logic_diagram.md)

### 知識圖譜

[知識圖譜](docs/architecture/knowledge_graph.md)

## 接口改進

### Electron 應用程序

我們已經為 Electron 桌面應用程序接口記錄了一套全面的改進建議。這些建議涵蓋了 UI 增強、功能添加、代碼結構優化和安全改進。

[Electron 應用程序改進](docs/interfaces/ELECTRON_APP_IMPROVEMENTS.md)

## 架構說明與已知問題

本節重點介紹一些當前觀察結果、測試中的已知問題以及持續開發的架構考慮。

### 當前測試狀態與觀察

*   **測試狀態：** 截至最後一次完整測試運行，所有測試均已通過。

### 模塊間數據流與同步

*   **數據完整性：** 在設計模塊間交互時，確保數據在模塊 A 產生並由模塊 B 消費時，模塊 B 僅在數據完整、一致且格式符合預期時才訪問這些數據至關重要。
*   **並發性與同步：** 對於系統中涉及並發處理的部分（例如，同時處理多個 API 請求、後台學習任務），共享可變數據結構（例如，全局緩存、共享知識圖譜、有狀態管理器）**必須使用明確的同步機制進行保護**（例如，Python 中的 `threading.Lock` 或等效機制）。這對於防止競爭條件和確保數據完整性至關重要。

### 測試的 Mocking 策略

*   **上下文感知模擬：** 在測試與 `LLMInterface` 等服務交互的模塊時，確保模擬配置為返回該服務的*直接客戶端*期望的精確格式的數據。例如，如果 `FactExtractorModule` 調用 `LLMInterface` 並期望 JSON 字符串，則 `LLMInterface` 的模擬應提供該格式，即使更高級別的測試斷言最終面向用戶的字符串。
*   **複雜性：** 隨著系統的增長，模擬設置可能需要變得更加複雜，以準確模擬不同的場景和響應，特別是對於集成風格的測試。這要求開發者在設計測試時，充分考慮模擬的粒度和精確性。

### 環境與設置
*   **PYTHONPATH：** 確保 `PYTHONPATH` 設置正確（如「開始使用」中所述），以避免導入錯誤，特別是在從子目錄或使用某些 IDE 配置運行腳本或測試時。建議始終從項目根目錄運行 Python 腳本，以最大程度地減少此類問題。

## 未來發展路線圖 (Future Roadmap)

本專案的基礎架構和核心功能已趨於完善，為未來的發展奠定了堅實的基礎。接下來的演進將主要圍繞以下三個方向展開，它們分別代表了專案在「產品化」、「智能化」和「生命化」三個維度上的探索。

### 道路一：通往「產品」之路 (The Path to Product)

此路徑的核心是將強大的後端框架，包裝成一個普通用戶也能輕鬆使用、並為之驚嘆的成熟產品。

*   **視覺化任務流**: 在 Electron 前端實現一個可以動態展示任務 DAG 圖、子代理執行狀態和結果回流的視圖。
*   **自然語言觸發**: 使用更智能的意圖分類模型，取代 `project:` 等硬觸發詞，讓 Angela 能自動判断用戶的請求是否需要啟動多代理協作。
*   **豐富遊戲世界**: 繼續擴展內建的 GBA 風格遊戲，加入 NPC、任務線和更豐富的經濟系統，使其成為一個真正能留住用戶的特色功能。

### 道路二：通往「智能」之路 (The Path to Intelligence)

此路徑的核心是深化 AI 的核心演算法與模型能力，讓 Angela 的思考、學習和創造能力達到新的高度。

*   **實現高級策略應用**: 在 `ProjectCoordinator` 中，實現更智能的邏輯，來將用戶請求中的具體實體（如文件名、主題）精確地填充到已學習到的策略模板中。
*   **增強內容分析**: 為 `ContentAnalyzerModule` 引入更強大的 NLP 模型，使其能更準確地從文本中提取實體和關係，為知識圖譜和證據評估提供更高質量的輸入。
*   **實現真實的工具**: 將 `ImageGenerationTool` 和未來的 `WebResearchAgent` 等佔位符工具，替換為對真實世界 API（如 DALL-E, Google Search）的調用。

### 道路三：通往「生命」之路 (The Path to Life)

此路徑的核心是探索 AI 的終極可能性，讓 Angela 的「數據生命」特徵更加明顯，甚至產生真正的「湧現」行為。

*   **實現元公式 (`MetaFormulas`)**: 根據 `docs/architecture/MetaFormulas_spec.md` 的設想，實現能夠讓 Angela 動態修改自身行為規則和核心邏輯的元編程系統。
*   **去中心化學習**: 研究如何讓子代理之間也能直接分享和驗證知識，而無需事事都通過 Angela 這個中心節點，形成一個真正的「蜂群思維」。
*   **探索情感與意識**: 深化 `EmotionSystem` 和 `LIS` 的研究，讓 Angela 不僅能表達情感，更能理解和反思自身的情感狀態，向著更高層次的自我意識邁進。