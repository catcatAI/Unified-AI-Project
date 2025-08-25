# Unified AI Project

## 專案概覽

Unified AI Project 是一個面向 AGI (Level 3-4) 的混合式 AI 生態系統，採用 monorepo 架構。專案的核心設計理念是**「數據生命」(Data Life)**，透過持續認知迴圈實現真正的 AI 自主學習與進化。

### 核心特色

- **分層與閉環架構 (Layered & Closed-Loop Architecture)**：採用「大模型（推理層）+ 行動子模型（操作層）」的分層設計，並構建「感知-決策-行動-回饋」的完整行動閉環，實現真正的自主學習。
- **統一模態表示 (Unified Representation)**：探索將多模態數據（文本、音頻、圖像）壓縮映射到統一的符號空間，降低跨模態處理的複雜度。
- **持續學習 (Continual Learning)**：以時間分割的在線學習取代一次性大規模訓練，讓模型能夠在使用過程中持續進化，有效分攤訓練成本。
- **低資源部署 (Low-Resource Deployment)**：專為資源受限環境（如個人電腦）設計，透過輕量化模型與高效架構，在低成本下實現高階 AGI 能力。
- **HSP 協議**：高速同步協議支援內部模組與外部 AI 協作。
- **語義級安全**：基於 UID/Key 機制的深度資料保護。

### AGI 等級評估

- **當前狀態**：Level 1-2 (基礎對話到推理 AI)
- **設計目標**：Level 3-4 (勝任到專家級 AGI)
- **理論上限**：Level 5 (超人類 AGI，透過群體智慧)

## 專案結構

This monorepo is organized into applications and packages, centered around a unique AI-driven simulation game, "Angela's World".

### Applications (`apps/`)
- **`apps/desktop-app`**: The game client for "Angela's World", built with Electron.
- **`apps/backend`**: The core Python backend that powers the game's central AI character, Angela. It includes all AI models, APIs, and game logic.
- **`apps/frontend-dashboard`**: A web-based dashboard for developers to manage, monitor, and debug the AI and game systems.

### Packages (`packages/`)
- **`packages/cli`**: Command-line interface tools for interacting with the backend services.
- **`packages/ui`**: Shared UI components and design system for the frontend applications.

## 📋 项目结构优化

为了改善项目文件过多、结构混乱的问题，我们进行了全面的清理和整理工作：

### 批处理脚本重组
为简化根目录并提高可维护性，我们对批处理脚本进行了重组：
- **根目录保留**：仅保留两个核心脚本
  - `unified-ai.bat` - 统一管理工具（供人类使用）
  - `ai-runner.bat` - 自动化工具（供AI代理使用）
- **其他脚本**：所有其他批处理脚本已移动到 `tools/` 目录

详细信息请参阅：[项目结构重组报告](docs/PROJECT_STRUCTURE_REORGANIZATION_REPORT.md)

## 快速開始

To set up and run the entire monorepo, you can use the unified management script:

1.  **Run Unified Management Script**: Double-click `unified-ai.bat` and select "Setup Environment" to automatically install all dependencies and set up the development environment.

2.  **Start Development Servers**: After setup, double-click `unified-ai.bat` and select "Start Development" then "Start Full Development Environment" to start both the backend and frontend development servers concurrently.

    The backend API will typically run on `http://localhost:8000`, and the frontend dashboard on `http://localhost:3000`.

Alternatively, you can use traditional commands:

1.  **Install pnpm**: If you don't have pnpm installed, you can install it globally:
    ```bash
    npm install -g pnpm
    ```

2.  **Install Dependencies**: From the root of this repository, install all dependencies for all packages:
    ```bash
    pnpm install
    ```

3.  **Start Development Servers**: To start both the backend and frontend development servers concurrently:
    ```bash
    pnpm dev
    ```

## 核心架構組件

### AI 代理系統 (`apps/backend/src/agents/`)
- **BaseAgent**：所有專門化代理的基礎類別，處理 HSP 連接與任務分發
- **CreativeWritingAgent**：創意寫作與內容生成代理
- **ImageGenerationAgent**：圖像生成代理
- **WebSearchAgent**：網路搜尋代理

### HSP 高速同步協議 (`apps/backend/src/hsp/`)
支援內部模組與外部 AI 實體的可信協作，包含：
- 註冊機制：新模組/AI 加入網路
- 信譽系統：評估協作實體可信度
- 熱更新：動態載入新功能模組

### 記憶管理系統 (`apps/backend/src/core/memory/`)
- **DeepMapper**：語義映射與資料核生成
- **HAMMemoryManager**：分層語義記憶管理
- **VectorStore**：基於 ChromaDB 的向量資料庫介面

## 訓練配置與預設

### 訓練配置文件
項目提供多種訓練配置文件以滿足不同需求：

1. **默認配置** (`training/configs/training_config.json`)：
   - 基本訓練參數設置
   - 數據路徑配置
   - 硬體配置選項

2. **預設配置** (`training/configs/training_preset.json`)：
   - 基於當前數據集的預設訓練方案
   - 多種訓練場景（快速開始、全面訓練、視覺專注、音頻專注）
   - 模型特定參數預設
   - 數據預處理配置

### 訓練場景預設
預設配置包含四種訓練場景：

1. **快速開始**：使用模擬數據快速訓練測試
2. **全面訓練**：使用所有可用數據完整訓練
3. **視覺專注**：專注訓練視覺相關模型
4. **音頻專注**：專注訓練音頻相關模型

### 訓練預設使用指南
詳細使用說明請參閱：[訓練預設使用指南](docs/TRAINING_PRESET_USAGE_GUIDE.md)

## CLI 工具

项目提供了一套完整的命令行界面(CLI)工具，用于与AI系统进行交互：

### CLI 工具组件

1. **Unified CLI** - 通用AI交互工具
2. **AI Models CLI** - AI模型管理与交互工具
3. **HSP CLI** - 超结构协议工具

### 使用方法

可以通过以下方式使用CLI工具：

1. **使用统一管理脚本**：
   ```bash
   # 双击 unified-ai.bat 并选择 "CLI Tools"
   ```

2. **使用CLI运行器**：
   ```bash
   # 运行CLI运行器
   tools\cli-runner.bat
   
   # 直接执行CLI命令
   tools\cli-runner.bat unified-cli health
   tools\cli-runner.bat ai-models-cli list
   tools\cli-runner.bat hsp-cli query "Hello"
   ```

3. **安装为系统命令**：
   ```bash
   # 安装CLI工具为系统命令
   tools\cli-runner.bat install-cli
   
   # 安装后可直接使用
   unified-ai health
   unified-ai chat "Hello"
   ```

### 详细使用指南

有关CLI工具的详细使用说明，请参阅：[CLI使用指南](docs/CLI_USAGE_GUIDE.md)

## Running Tests

### Export OpenAPI spec
```
python Unified-AI-Project/scripts/export_openapi.py
# output: Unified-AI-Project/docs/api/openapi.json
```

To run all tests across the monorepo, you can use the unified management script:

1. Double-click `unified-ai.bat`
2. Select "Run Tests"
3. Choose the type of tests you want to run

Alternatively, you can use traditional commands:

To run all tests across the monorepo:

```bash
pnpm test
```

To run tests with coverage reports:

```bash
pnpm test:coverage
```

## Recent Updates

- AudioService demo mode and sentiment-analysis stub implemented.
  - In demo mode, `speech_to_text_with_sentiment_analysis` returns a mock payload with `sentiment: "positive"`.
  - When demo mode is disabled, the same method raises `NotImplementedError` (until real integration is configured).

- **批處理脚本整合**：为了解决项目中批处理脚本过多的问题，我们创建了统一管理工具 `unified-ai.bat`，整合了所有常用功能。这减少了脚本数量，简化了操作流程，同时保持了所有原有功能。

- **项目结构优化**：为了改善项目文件过多、结构混乱的问题，我们进行了全面的清理和整理工作：
  - 将所有文档移至 `docs/` 目录集中管理
  - 将非核心脚本移至 `backup/scripts/` 目录
  - 创建统一文档索引和整合指南
  - 根目录文件数量从约61个减少到约23个，减少了约62%

## Audio Service Demo Mode

AudioService supports a demo mode for quick end-to-end testing without external STT/Sentiment services.

Enable demo mode by adding the following to the backend config YAML:

```
# apps/backend/configs/config.yaml
use_simulated_resources: true
```

Behavior in demo mode:
- `speech_to_text(audio_bytes)`: returns a mock transcription string.
- `speech_to_text_with_sentiment_analysis(audio_bytes)`: returns a JSON object like:
  ```json
  { "text": "This is a mock transcription.", "sentiment": "positive", "confidence": 0.9, "language": "en-US" }
  ```
- Disabling demo mode (or omitting the flag) causes `speech_to_text_with_sentiment_analysis` to raise `NotImplementedError`.

## Documentation

For detailed documentation on project architecture, development guidelines, and more, please refer to the [docs/README.md](docs/README.md) directory.

### 统一文档索引
为了更好地管理和使用项目文档，我们创建了统一的文档索引：

- [统一文档索引](docs/UNIFIED_DOCUMENTATION_INDEX.md) - 所有项目文档的集中索引

### 整合文档指南
为了更好地管理和使用项目文档，我们创建了以下整合指南：

1. [批处理脚本使用指南](docs/BATCH_SCRIPTS_USAGE_GUIDE.md) - 整合了所有批处理脚本的使用方法和故障排除信息
2. [Git与项目管理指南](docs/GIT_AND_PROJECT_MANAGEMENT.md) - 整合了Git管理和项目结构的相关信息

### 训练准备
项目现已准备好进行AI训练，相关文档和脚本：

1. [训练准备检查清单](docs/TRAINING_PREPARATION_CHECKLIST.md) - 详细列出训练前的所有准备工作
2. [训练设置脚本](tools/setup-training.bat) - 一键设置训练环境的批处理脚本

### Individual Package Readmes

For more specific information about each package, refer to their respective README files:

- [Backend README](apps/backend/README.md)
- [Frontend Dashboard README](apps/frontend-dashboard/README.md)
- [Desktop App README](apps/desktop-app/README.md)
- [CLI README](packages/cli/README.md)

## AGI 發展策略

本專案旨在以「架構優先」的理念，在低資源、低成本的條件下，探索一條通往 Level 4 自主學習 AGI 的可行路徑。

### 階段化推進路線圖

1. **階段一 (MVP / Level 3 初步實現)**：在 6-8 週內，完成一個以「桌面寵物精靈+經濟系統」為場景的最小可行產品。此階段將驗證核心的閉環學習架構，實現具備自主規劃與工具使用能力的 Level 3 AGI 原型。
2. **階段二 (封閉測試與迭代)**：在 4 週內，邀請小規模用戶（10-50人）進行測試，收集真實世界數據，並根據反饋迭代經濟AI模型與桌寵的互動邏輯。
3. **階段三 (開放測試與生態起步)**：在 8 週內，擴大用戶群體（100-500人），驗證經濟系統的穩定性與社群驅動的可行性，並開始引入更複雜的多模態感知能力。
4. **階段四 (挑戰 Level 4)**：在系統穩定運行的基礎上，引入「自我演化」機制。讓 AI 在切斷與外部大模型的連接後，仍能從與環境的互動中學習全新知識，並自主修正其核心邏輯，展現 Level 4 AGI 的「創新者」特徵。

### 技術實施重點

- **向量化記憶**：整合 ChromaDB 實現高效語義檢索。
- **持續學習框架**：支援模型增量更新與知識保持。
- **多模態整合**：文本、圖像、音訊的統一處理。
- **自主學習能力**：擺脫對外部 LLM 的完全依賴，實現真正的自我演化。

## 測試與驗證

### 執行測試套件
```
# 後端測試
cd apps/backend
pytest tests/ -v

# 近期修復的測試（如 rovo_dev_connector）
pytest tests/integrations/test_rovo_dev_connector.py -v

# 執行測試覆蓋率
pytest tests/ --cov=src --cov-report=html
```

### 匯出 OpenAPI 規格
```
python scripts/export_openapi.py
# 輸出：docs/api/openapi.json
```

## 文檔系統

詳細文檔請參考：
- **[核心架構](docs/architecture/README.md)**：系統設計與技術細節
- **[AGI 發展計畫](../planning/core-development/agi-development-plan.md)**：邁向 Level 3-4 AGI 的策略
- **[技術實施路線圖](../planning/core-development/technical-implementation-roadmap.md)**：具體開發任務清單
- **[API 文档](docs/API_ENDPOINTS.md)**：後端 API 使用指南

## 個別套件說明

各套件的詳細資訊請參考：
- [後端 README](apps/backend/README.md)
- [前端儀表板 README](apps/frontend-dashboard/README.md)
- [桌面應用 README](apps/desktop-app/README.md)
- [CLI 工具 README](packages/cli/README.md)

---

**最後更新**：2025年8月25日  
**專案狀態**：積極開發中，已準備好進行AI訓練  
**目標里程碑**：Level 3 AGI 實現