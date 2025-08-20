# Unified AI Project

## 專案概覽

Unified AI Project 是一個面向 AGI (Level 3-4) 的混合式 AI 生態系統，採用 monorepo 架構。專案的核心設計理念是**「數據生命」(Data Life)**，透過持續認知迴圈實現真正的 AI 自主學習與進化。

### 核心特色

- **組合式架構**：大型語言模型 + 專門化子模型的分層設計
- **持續學習**：時間分割訓練取代一次性大規模訓練
- **熱更新/熱遷移**：支援不中斷系統的動態升級與遷移
- **HSP 協議**：高速同步協議支援內部模組與外部 AI 協作
- **語義級安全**：基於 UID/Key 機制的深度資料保護

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

## 快速開始

To set up and run the entire monorepo, follow these steps:

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
    The backend API will typically run on `http://localhost:8000`, and the frontend dashboard on `http://localhost:3000`.

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
- **VectorStore**：向量資料庫介面（支援 ChromaDB）

## Running Tests

### Export OpenAPI spec
```bash
python Unified-AI-Project/scripts/export_openapi.py
# output: Unified-AI-Project/docs/api/openapi.json
```


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

## Audio Service Demo Mode

AudioService supports a demo mode for quick end-to-end testing without external STT/Sentiment services.

Enable demo mode by adding the following to the backend config YAML:

```yaml
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

## Individual Package Readmes

For more specific information about each package, refer to their respective README files:

- [Backend README](apps/backend/README.md)
- [Frontend Dashboard README](apps/frontend-dashboard/README.md)
- [Desktop App README](apps/desktop-app/README.md)
- [CLI README](packages/cli/README.md)

## AGI 發展策略

### 階段化推進（基於 112-115.txt 要點）

1. **MVP 優先**：4週穩定除錯 → 封閉測試 → 開放測試 → 正式上線
2. **成本分攤**：避免一次性巨大投資，分階段擴展能力
3. **社群驅動**：經濟 AI + 遊戲化入口促進使用者參與
4. **漸進式 AGI**：分層演化取代直接燒錢堆算力

### 技術實施重點

- **向量化記憶**：整合 ChromaDB 實現高效語義檢索
- **持續學習框架**：支援模型增量更新與知識保持
- **多模態整合**：文本、圖像、音訊的統一處理
- **自主學習能力**：擺脫對外部 LLM 的完全依賴

## 測試與驗證

### 執行測試套件
```bash
# 後端測試
cd apps/backend
pytest tests/ -v

# 近期修復的測試（如 rovo_dev_connector）
pytest tests/integrations/test_rovo_dev_connector.py -v

# 執行測試覆蓋率
pytest tests/ --cov=src --cov-report=html
```

### 匯出 OpenAPI 規格
```bash
python scripts/export_openapi.py
# 輸出：docs/api/openapi.json
```

## 文檔系統

詳細文檔請參考：
- **[核心架構](docs/architecture/README.md)**：系統設計與技術細節
- **[AGI 發展計畫](../planning/core-development/agi-development-plan.md)**：邁向 Level 3-4 AGI 的策略
- **[技術實施路線圖](../planning/core-development/technical-implementation-roadmap.md)**：具體開發任務清單
- **[API 文檔](docs/API_ENDPOINTS.md)**：後端 API 使用指南

## 個別套件說明

各套件的詳細資訊請參考：
- [後端 README](apps/backend/README.md)
- [前端儀表板 README](apps/frontend-dashboard/README.md)
- [桌面應用 README](apps/desktop-app/README.md)
- [CLI 工具 README](packages/cli/README.md)

---

**最後更新**：2025年1月  
**專案狀態**：積極開發中  
**目標里程碑**：Level 3 AGI 實現
