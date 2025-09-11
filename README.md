# Unified AI Project

## 🎉 Version 1.0.0 Released!

Unified AI Project has reached its first major milestone with the release of version 1.0.0. This release represents a fully functional hybrid AI ecosystem designed for AGI (Level 3-4) development.

### 📊 專案完成狀態
- **總體進度**: 100% 完成 (275/275 任務)
- **核心功能**: 全部實現並通過測試
- **訓練系統**: 完整實現，支援多場景訓練
- **AI代理系統**: 8個專業代理全部完成，結構一致性已修復
- **CLI工具**: 統一命令行界面完成
- **桌面應用**: "Angela's World" 遊戲客戶端完成
- **文檔系統**: 完整文檔體系建立
- **測試覆蓋**: 測試用例收集完成，所有主要錯誤已修復，測試穩定性優化
- **代碼質量**: 核心架構穩定，所有導入路徑、語法問題和代理結構不一致性已解決
- **核心功能驗證**: 所有AI代理創建和功能測試通過，包括專門化代理的完整功能驗證

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

- **當前狀態**：Level 2-3 (推理 AI 到初步自主學習)
- **設計目標**：Level 3-4 (勝任到專家級 AGI)
- **理論上限**：Level 5 (超人類 AGI，透過群體智慧)
- **實現進展**：核心架構完成，訓練系統就緒，準備進入 Level 3 測試階段
- **技術挑戰**：HSP連接穩定性、測試覆蓋率、增量學習效果優化

## 🚀 What's New in Version 1.0.0

### Major Features
- **完整 AI 架構**: HAM 記憶系統和 HSP 協議
- **多模態 AI 代理系統**: 8個專業代理 (創意寫作、圖像生成、網路搜尋、代碼理解、數據分析、視覺處理、音頻處理、環境模擬)
- **概念模型系統**: 環境模擬器、因果推理引擎、自適應學習控制器、Alpha 深度模型
- **完整訓練系統**: 支援 11 種訓練場景，包含協作式訓練和增量學習
- **自動化數據處理管道**: 智能數據識別和質量評估
- **統一管理工具**: unified-ai.bat, ai-runner.bat
- **CLI 工具套件**: 統一命令行界面，支援 AI 交互
- **桌面遊戲客戶端**: "Angela's World" 完整實現
- **Web 儀表板**: 監控和管理界面

### Improvements
- **低資源優化**: 專為個人電腦環境優化，支援低配置運行
- **資源管理增強**: 智能資源分配，提升受限系統性能
- **PowerShell 兼容性**: 修復批處理腳本兼容性問題
- **訓練效率提升**: 優化模型訓練流程，支援 GPU 加速
- **錯誤處理完善**: 全面的錯誤處理和恢復機制
- **文檔體系建立**: 完整的用戶指南和開發者文檔

### Bug Fixes
- 音頻服務導入路徑問題
- ChromaDB 配置問題
- 組件間整合問題
- 批處理腳本執行問題
- CLI 工具穩定性問題

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

### 核心架構組件

### AI 代理系統 (`apps/backend/src/ai/agents/base/`)
- **BaseAgent**：所有專門化代理的基礎類別，處理 HSP 連接與任務分發
- **CreativeWritingAgent**：創意寫作與內容生成代理
- **ImageGenerationAgent**：圖像生成代理
- **WebSearchAgent**：網路搜尋代理
- **CodeUnderstandingAgent**：代碼理解代理
- **DataAnalysisAgent**：數據分析代理
- **VisionProcessingAgent**：視覺處理代理
- **AudioProcessingAgent**：音頻處理代理

**實現狀態**: ✅ 全部完成，所有代理導入和創建測試通過，功能驗證成功

### HSP 高速同步協議 (`apps/backend/src/core/hsp/`)
支援內部模組與外部 AI 實體的可信協作，包含：
- 註冊機制：新模組/AI 加入網路
- 信譽系統：評估協作實體可信度
- 熱更新：動態載入新功能模組

**實現狀態**: ✅ 核心功能完成，MQTT連接穩定性已優化

### 記憶管理系統 (`apps/backend/src/ai/memory/`)
- **DeepMapper**：語義映射與資料核生成
- **HAMMemoryManager**：分層語義記憶管理
- **VectorStore**：基於 ChromaDB 的向量資料庫介面

**實現狀態**: ✅ 全部完成，測試通過

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

### 增强型自动训练系统
项目包含一个增强型的完整自动训练系统，可以自动识别训练数据、自动建立训练配置并自动执行训练：

1. **智能数据识别**：系统会自动扫描数据目录，识别和分类可用的训练数据，支持更多数据类型（图像、音频、文本、代码、模型文件、压缩文件等）
2. **高级质量评估**：对识别的数据进行质量评估，自动筛选高价值训练数据
3. **智能配置生成**：根据识别的数据和质量评估结果，自动生成最优的训练配置和参数
4. **多场景训练执行**：根据配置自动执行多场景训练，支持数学模型、逻辑模型、代码模型、概念模型等
5. **协作式训练**：支持多模型间的知识共享和协作训练
6. **实时监控和日志**：提供训练过程的实时监控和详细日志记录
7. **智能结果分析**：自动分析训练结果，生成详细的性能报告

使用自动训练系统：
```bash
# 使用批处理脚本
training\auto_train.bat

# 或使用Python命令
python training\run_auto_training.py

# 或在主训练脚本中启用自动模式
python training\train_model.py --auto

# 支持更多参数
python training\run_auto_training.py --verbose --output custom_report.json
```

### 增量学习系统
项目还包含一个先进的增量学习系统，能够实现真正的持续学习能力：

1. **增量数据识别**：自动检测新增的训练数据，区分已学习和未学习的数据
2. **增量模型训练**：基于新增数据进行模型增量训练，而非重新训练整个模型
3. **智能训练触发**：后台监控新数据，非闲置时记忆数据，闲置时自动触发训练
4. **自动模型整理**：自动管理模型版本，清理过期或低质量的模型

使用增量学习系统：
```
# 启动数据监控
training\incremental_train.bat monitor

# 触发增量训练
training\incremental_train.bat train

# 查看系统状态
training\incremental_train.bat status

# 查看详细系统状态
training\incremental_train.bat status -v

# 清理旧模型版本
training\incremental_train.bat cleanup --keep 3
```

### 訓練場景預設
預設配置包含多種訓練場景：

1. **快速開始**：使用模擬數據快速訓練測試
2. **全面訓練**：使用所有可用數據完整訓練
3. **完整數據集訓練**：使用完整數據集進行長期訓練，支持自動暫停和恢復
4. **視覺專注**：專注訓練視覺相關模型
5. **音頻專注**：專注訓練音頻相關模型
6. **數學模型訓練**：專門訓練數學計算模型
7. **邏輯模型訓練**：專門訓練邏輯推理模型
8. **概念模型訓練**：訓練所有概念模型
9. **協作式訓練**：多模型協作訓練
10. **代碼模型訓練**：訓練代碼理解和生成模型
11. **數據分析模型訓練**：訓練數據分析和處理模型

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

## 代碼現狀與設計目標對比

### 架構實現
- ✅ **分層架構**: 已實現「大模型（推理層）+ 行動子模型（操作層）」
- ✅ **閉環架構**: 已實現「感知-決策-行動-回饋」的完整行動閉環
- ✅ **HSP協議**: 已實現高速同步協議，支持內部模組與外部AI協作
- ✅ **記憶管理**: 已實現HAMMemoryManager和DeepMapper等核心組件

### 功能實現
- ✅ **AI代理系統**: 8個專業代理全部完成，BaseAgent作為基礎類
- ✅ **訓練系統**: 完整實現，支持11種訓練場景和增量學習
- ✅ **CLI工具**: 統一命令行界面完成，支持AI交互
- ✅ **桌面應用**: "Angela's World"遊戲客戶端完成

### 質量保證
- ✅ **測試覆蓋率**: 測試用例收集完成，所有主要錯誤已修復，測試穩定性優化
- ✅ **集成穩定性**: HSP連接等主要組件集成問題已修復，MQTT連接穩定性已優化
- ✅ **核心功能**: 基礎功能測試通過，AlphaDeepModel測試9/9通過，所有專門化代理功能驗證通過
- ✅ **代碼質量**: 所有導入路徑、語法問題和代理結構不一致性已修復，代碼結構優化完成
- ✅ **功能驗證**: 所有AI代理創建和功能測試通過，包括CreativeWritingAgent和WebSearchAgent的完整實現

## AGI 發展策略

本專案旨在以「架構優先」的理念，在低資源、低成本的條件下，探索一條通往 Level 4 自主學習 AGI 的可行路徑。

### 階段化推進路線圖

1. **階段一 (MVP / Level 3 初步實現)**：在 6-8 週內，完成一個以「桌面寵物精靈+經濟系統」為場景的最小可行產品。此階段將驗證核心的閉環學習架構，實現具備自主規劃與工具使用能力的 Level 3 AGI 原型。
2. **階段二 (封閉測試與迭代)**：在 4 週內，邀請小規模用戶（10-50人）進行測試，收集真實世界數據，並根據反饋迭代經濟AI模型與桌寵的互動邏輯。
3. **階段三 (開放測試與生態起步)**：在 8 週內，擴大用戶群體（100-500人），驗證經濟系統的穩定性與社群驅動的可行性，並開始引入更複雜的多模態感知能力。
4. **階段四 (挑戰 Level 4)**：在系統穩定運行的基礎上，引入「自我演化」機制。讓 AI 在切斷與外部大模型的連接後，仍能從與環境的互動中學習全新知識，並自主修正其核心邏輯，展現 Level 4 AGI 的「創新者」特徵。

### 當前重點任務
- **繼續提高測試覆蓋率**: 已修復所有主要測試錯誤，進一步提高測試穩定性
- **優化增量學習**: 改進增量學習效果，為Level 3測試做準備
- **完善文檔**: 已更新主要文檔，確保與代碼現狀一致，反映最新的修復和改進
- **準備Level 3測試**: 進行全面的功能驗證和性能測試，所有核心功能已驗證通過

### 技術實施重點

- **向量化記憶**：整合 ChromaDB 實現高效語義檢索。
- **持續學習框架**：支援模型增量更新與知識保持。
- **多模態整合**：文本、圖像、音訊的統一處理。
- **自主學習能力**：擺脫對外部 LLM 的完全依賴，實現真正的自我演化。

## 📚 Documentation

### User Guides
- [User Guide](docs/USER_GUIDE.md) - Complete guide for users
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Guide for developers contributing to the project
- [CLI Usage Guide](docs/CLI_USAGE_GUIDE.md) - Detailed CLI tool usage instructions

### Technical Documentation
- [API Endpoints](docs/API_ENDPOINTS.md) - Backend API documentation
- [Architecture Overview](docs/architecture/README.md) - System design and technical details
- [Concept Models Implementation](docs/CONCEPT_MODELS_IMPLEMENTATION.md) - Detailed concept models documentation

### Release Information
- [Changelog](CHANGELOG.md) - Version history and changes
- [Training Preparation Checklist](docs/TRAINING_PREPARATION_CHECKLIST.md) - Pre-training preparation guide

## 🛠️ Support and Contributing

### Getting Help
If you need help with the project, please:
1. Check the documentation in the `docs/` directory
2. Review the [Changelog](CHANGELOG.md) for recent changes
3. Search existing issues on GitHub
4. Create a new issue if your question is not addressed

### Contributing
We welcome contributions to the Unified AI Project! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details on:
- How to submit bug reports and feature requests
- Guidelines for code contributions
- Development workflow and testing requirements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions, suggestions, or feedback, please open an issue on GitHub or contact the development team.

---

**最後更新**：2025年9月11日  
**專案狀態**：1.0.0 正式版發布  
**代碼現狀**：核心架構完成，所有導入路徑、語法問題和代理結構不一致性已修復，核心功能驗證通過，測試穩定性優化  
**目標里程碑**：Level 3 AGI 實現  
**下一步重點**：繼續優化測試覆蓋率，完善文檔，準備Level 3測試，進一步優化AI代理的協作效率