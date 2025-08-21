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
- **VectorStore**：基於 ChromaDB 的向量資料庫介面

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
