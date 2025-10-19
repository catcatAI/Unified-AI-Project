# Unified AI Project 技術棧系統樹

## 📋 系統概覽

**系統名稱**: Unified AI Project 技術棧系統樹  
**創建日期**: 2025年10月12日  
**基於**: 真實文件系統結構分析  
**目的**: 標識每個技術組件的具體使用位置  
**範圍**: 全域性系統測試和開發指導  

## 🌳 系統架構總覽

```
Unified-AI-Project/
├── 前端層 (Frontend Layer)
│   ├── Web儀表板 (Next.js 15 + React 19 + TypeScript 5)
│   ├── 桌面應用 (Electron 29 + React)
│   └── 共享UI組件 (React 19 TypeScript組件庫)
├── 後端層 (Backend Layer)  
│   ├── FastAPI服務 (Python 3.8+ FastAPI框架)
│   ├── MQTT消息系統 (paho-mqtt + gmqtt)
│   └── 配置管理 (YAML/JSON/環境變量)
├── AI引擎層 (AI Engine Layer)
│   ├── BaseAgent系統 (自定義代理框架)
│   ├── 專門化代理 (11個專業AI代理)
│   ├── 概念模型 (AlphaDeepModel等5個核心模型)
│   └── 記憶系統 (ChromaDB + HAMMemoryManager)
├── 工具層 (Tools Layer)
│   ├── Web工具 (requests + BeautifulSoup4)
│   ├── 數學工具 (NumPy + SciPy)
│   ├── 文件工具 (標準文件系統操作)
│   └── 系統工具 (psutil系統監控)
├── 模型層 (Models Layer)
│   ├── 多LLM服務 (MultiLLMService)
│   ├── 訓練系統 (TensorFlow/PyTorch)
│   └── 模型版本管理 (版本控制和回滾)
└── 基礎設施層 (Infrastructure Layer)
    ├── HSP協議 (自定義高速同步協議)
    ├── 監控系統 (性能監控和錯誤追蹤)
    └── 開發工具鏈 (測試、CI/CD、部署)
```

## 🎯 技術使用位置詳圖

### 1. 前端技術使用位置

#### 1.1 Web儀表板 (Next.js技術棧)
```
apps/frontend-dashboard/
├── package.json                    # Next.js 15 + React 19 + TypeScript 5
├── next.config.js                  # Next.js配置
├── tailwind.config.js              # Tailwind CSS 4配置
├── src/
│   ├── pages/                      # Next.js頁面路由
│   │   ├── dashboard.tsx          # 主儀表板頁面 (Next.js + React 19 + TS5)
│   │   ├── api/                   # API路由 (Next.js API Routes)
│   │   └── settings.tsx           # 設置頁面 (React 19組件)
│   ├── components/                 # React 19組件
│   │   ├── ui/                    # shadcn/ui組件
│   │   ├── charts/                # 圖表組件 (TypeScript 5)
│   │   └── forms/                 # 表單組件 (TypeScript 5)
│   ├── hooks/                      # React Hooks (TypeScript 5)
│   ├── utils/                      # 工具函數 (TypeScript 5)
│   └── styles/                     # Tailwind CSS 4樣式
└── public/                         # 靜態資源
```

#### 1.2 桌面應用 (Electron技術棧)
```
apps/desktop-app/
├── package.json                    # Electron 29 + React + TypeScript
├── electron-builder.yml           # Electron構建配置
├── src/
│   ├── main.ts                    # Electron主進程 (Node.js API)
│   ├── renderer/                  # Electron渲染進程
│   │   ├── App.tsx                # React 19根組件
│   │   ├── components/            # React組件 (TypeScript)
│   │   ├── services/              # API服務調用 (TypeScript)
│   │   └── utils/                 # 工具函數 (TypeScript)
│   └── preload.ts                 # Preload腳本 (Electron API)
└── dist/                          # 構建輸出
```

#### 1.3 共享UI組件 (React技術棧)
```
packages/ui/
├── package.json                    # React 19 + TypeScript組件庫
├── src/
│   ├── components/                # 共享React組件 (TypeScript 5)
│   │   ├── Button.tsx             # 按鈕組件
│   │   ├── Card.tsx               # 卡片組件
│   │   └── Modal.tsx              # 模態框組件
│   ├── hooks/                     # 共享React Hooks
│   └── utils/                     # 共享工具函數
└── dist/                          # 編譯輸出
```

### 2. 後端技術使用位置

#### 2.1 FastAPI服務 (Python FastAPI技術棧)
```
apps/backend/
├── requirements.txt               # Python依賴 (FastAPI + 所有後端庫)
├── src/
│   ├── main.py                    # FastAPI主入口
│   ├── api/                       # API路由層 (FastAPI路由)
│   │   ├── routes/               # 具體API路由實現
│   │   ├── middleware/           # FastAPI中間件
│   │   └── dependencies/         # FastAPI依賴注入
│   ├── services/                  # 業務服務層
│   │   ├── multi_llm_service.py  # 多LLM服務 (FastAPI服務)
│   │   └── auth_service.py       # 認證服務 (FastAPI服務)
│   ├── core/                      # 核心功能層
│   │   ├── hsp/                  # HSP協議實現 (自定義協議)
│   │   ├── memory/               # 記憶系統 (ChromaDB)
│   │   └── tools/                # 工具系統 (Python工具)
│   └── ai/                        # AI引擎層
│       ├── agents/               # 代理系統 (自定義AI框架)
│       ├── concept_models/       # 概念模型 (TensorFlow/PyTorch)
│       └── training/             # 訓練系統 (AI訓練框架)
└── tests/                         # 測試代碼
```

#### 2.2 MQTT消息系統 (MQTT技術棧)
```
apps/backend/src/core/hsp/
├── __init__.py
├── types.py                       # HSP協議類型定義 (自定義協議)
├── connector.py                   # MQTT連接器 (paho-mqtt)
├── bridge/                        # 消息橋接 (MQTT橋接)
│   ├── message_bridge.py         # 消息橋接實現
│   └── data_aligner.py           # 數據對齊器
├── internal/                      # 內部總線 (MQTT內部通信)
│   └── internal_bus.py           # 內部消息總線
├── external/                      # 外部連接器 (MQTT外部連接)
│   └── external_connector.py     # 外部連接器實現
└── utils/                         # HSP工具函數
    └── fallback_config_loader.py # 後備配置加載器 (YAML配置)
```

#### 2.3 配置管理 (YAML/JSON技術棧)
```
apps/backend/configs/
├── system_config.yaml             # 系統配置 (YAML格式)
├── ai_config.yaml                 # AI配置 (YAML格式)
├── hsp_config.yaml                # HSP配置 (YAML格式)
└── environment/                   # 環境特定配置
    ├── development.yaml           # 開發環境配置
    ├── production.yaml            # 生產環境配置
    └── test.yaml                  # 測試環境配置
```

### 3. AI引擎技術使用位置

#### 3.1 BaseAgent系統 (自定義AI框架技術棧)
```
apps/backend/src/agents/
├── base_agent.py                  # BaseAgent基類 (自定義AI框架)
├── __init__.py
├── base/                          # BaseAgent基礎實現
│   └── base_agent.py             # 核心BaseAgent類 (HSP集成)
└── specialized/                   # 專門化代理 (11個專業代理)
    ├── __init__.py
    ├── creative_writing_agent.py  # 創意寫作代理 (NLP技術)
    ├── web_search_agent.py        # 網絡搜索代理 (Web技術集成)
    ├── code_understanding_agent.py # 代碼理解代理 (代碼分析技術)
    ├── data_analysis_agent.py     # 數據分析代理 (數據分析技術)
    ├── vision_processing_agent.py # 視覺處理代理 (計算機視覺技術)
    ├── audio_processing_agent.py  # 音頻處理代理 (音頻處理技術)
    ├── knowledge_graph_agent.py   # 知識圖譜代理 (圖譜技術)
    ├── nlp_processing_agent.py    # NLP處理代理 (NLP技術)
    ├── planning_agent.py          # 規劃代理 (規劃算法技術)
    └── image_generation_agent.py  # 圖像生成代理 (圖像生成技術)
```

#### 3.2 概念模型 (深度學習技術棧)
```
apps/backend/src/ai/concept_models/
├── __init__.py
├── alpha_deep_model.py            # Alpha深度模型 (TensorFlow/PyTorch)
├── unified_symbolic_space.py      # 統一符號空間 (符號處理技術)
├── environment_simulator.py       # 環境模擬器 (模擬技術)
├── causal_reasoning_engine.py     # 因果推理引擎 (因果推理技術)
├── adaptive_learning_controller.py # 自適應學習控制器 (自適應技術)
└── tests/                         # 概念模型測試
```

#### 3.3 記憶系統 (向量數據庫技術棧)
```
apps/backend/src/ai/memory/
├── __init__.py
├── ham_memory_manager.py          # HAM記憶管理器 (ChromaDB + 自定義)
├── deep_mapper.py                 # 深度映射器 (嵌入技術)
├── vector_store.py                # 向量存儲 (ChromaDB向量數據庫)
└── tests/                         # 記憶系統測試
```

### 4. 工具層技術使用位置

#### 4.1 Web工具 (Web技術棧)
```
apps/backend/src/core/tools/
├── web_search_tool.py             # Web搜索工具 (requests + BeautifulSoup4)
├── __init__.py
├── math_tool.py                   # 數學工具 (NumPy數學計算)
├── calculator_tool.py             # 計算器工具 (基礎數學運算)
├── file_system_tool.py            # 文件系統工具 (Python文件系統API)
├── system_monitor_tool.py         # 系統監控工具 (psutil系統監控)
├── csv_tool.py                    # CSV工具 (CSV文件處理)
├── dependency_checker.py          # 依賴檢查器 (依賴分析)
└── tests/                         # 工具測試
```

#### 4.2 高級工具 (專業技術棧)
```
apps/backend/src/core/tools/
├── js_tool_dispatcher/            # JS工具調度器 (JavaScript執行)
├── logic_model/                   # 邏輯模型 (邏輯推理技術)
├── math_model/                    # 數學模型 (高級數學模型)
├── parameter_extractor/           # 參數提取器 (參數提取技術)
├── translation_model/             # 翻譯模型 (機器翻譯技術)
├── natural_language_generation_tool.py # NLG工具 (自然語言生成)
├── speech_to_text_tool.py         # 語音轉文本工具 (語音識別技術)
├── image_generation_tool.py       # 圖像生成工具 (圖像生成技術)
├── image_recognition_tool.py      # 圖像識別工具 (圖像識別技術)
└── tool_dispatcher.py             # 工具調度器 (工具統一調度)
```

### 5. 模型層技術使用位置

#### 5.1 多LLM服務 (多模型技術棧)
```
apps/backend/src/core/services/
├── multi_llm_service.py           # 多LLM服務 (多模型管理技術)
├── __init__.py
├── llm_config_loader.py           # LLM配置加載器 (配置管理技術)
└── model_registry.py              # 模型註冊表 (模型註冊技術)
```

#### 5.2 訓練系統 (AI訓練技術棧)
```
training/
├── train_model.py                 # 主訓練腳本 (TensorFlow/PyTorch)
├── auto_training_manager.py       # 自動訓練管理器 (自動化訓練技術)
├── collaborative_training_manager.py # 協作訓練管理器 (分佈式訓練技術)
├── incremental_learning_manager.py # 增量學習管理器 (增量學習技術)
├── enhanced_checkpoint_manager.py # 增強檢查點管理器 (檢查點技術)
├── fault_detector.py              # 故障檢測器 (故障檢測技術)
├── gpu_optimizer.py               # GPU優化器 (GPU優化技術)
├── distributed_optimizer.py       # 分佈式優化器 (分佈式優化技術)
└── examples/                      # 訓練示例和配置
```

### 6. 基礎設施層技術使用位置

#### 6.1 HSP協議 (自定義協議技術棧)
```
apps/backend/src/core/hsp/
├── types.py                       # HSP協議類型 (自定義協議定義)
├── connector.py                   # HSP連接器 (MQTT集成技術)
├── bridge/                        # 消息橋接 (協議轉換技術)
├── internal/                      # 內部通信 (內部總線技術)
├── external/                      # 外部連接 (外部集成技術)
├── security.py                    # 安全模組 (安全協議技術)
├── versioning.py                  # 版本管理 (版本控制技術)
└── utils/                         # 工具函數 (協議工具技術)
```

#### 6.2 監控系統 (監控技術棧)
```
apps/backend/src/core/
├── monitoring/                    # 監控系統
│   ├── performance_monitor.py     # 性能監控 (psutil技術)
│   ├── error_tracker.py           # 錯誤追蹤 (錯誤追蹤技術)
│   └── health_checker.py          # 健康檢查 (健康檢查技術)
└── shared/                        # 共享組件
    ├── logger.py                  # 日誌系統 (Python logging技術)
    └── utils.py                   # 工具函數 (通用工具技術)
```

#### 6.3 開發工具鏈 (開發技術棧)
```
# 測試系統
tests/
├── backend/                       # 後端測試 (pytest測試框架)
├── frontend/                      # 前端測試 (Jest測試框架)
├── hsp/                          # HSP協議測試 (MQTT測試技術)
└── integration/                   # 集成測試 (端到端測試技術)

# 腳本和工具
scripts/
├── deploy.sh                      # 部署腳本 (Shell腳本技術)
├── test.sh                        # 測試腳本 (Shell腳本技術)
└── setup.py                       # 設置腳本 (Python腳本技術)

# CI/CD配置
.github/workflows/                 # GitHub Actions工作流
├── test.yml                       # 測試工作流 (GitHub Actions技術)
├── deploy.yml                     # 部署工作流 (GitHub Actions技術)
└── code-quality.yml               # 代碼質量工作流
```

## 🔗 技術依賴關係圖

### 核心依賴鏈
```
前端應用 (Next.js/Electron)
    ↓ (API調用)
FastAPI服務 (Python/FastAPI)
    ↓ (業務邏輯)
AI引擎 (自定義AI框架)
    ↓ (AI處理)
概念模型 (TensorFlow/PyTorch)
    ↓ (數據存儲)
ChromaDB (向量數據庫)
    ↓ (通信協議)
MQTT/HSP (消息隊列)
```

### 工具依賴鏈
```
代理系統 (BaseAgent)
    ↓ (調用工具)
工具系統 (Python工具)
    ↓ (具體實現)
Web工具 (requests + BeautifulSoup4)
數學工具 (NumPy + SciPy)
系統工具 (psutil)
```

### 模型依賴鏈
```
多LLM服務 (MultiLLMService)
    ↓ (模型管理)
概念模型 (TensorFlow/PyTorch)
    ↓ (訓練優化)
訓練系統 (分佈式訓練框架)
    ↓ (版本控制)
模型版本管理 (版本控制系統)
```

## 📊 技術使用統計

### 按文件類型分佈
- **Python文件**: ~30,819個 (主要實現)
- **TypeScript文件**: ~89個 (前端界面)
- **YAML文件**: ~578個 (配置文件)
- **JSON文件**: ~100+個 (數據和配置)

### 按技術複雜度分佈
- **專家級**: HSP協議、概念模型、分佈式訓練 (5%)
- **高級**: AI代理、多LLM、向量數據庫 (15%)
- **中級**: FastAPI、工具集成、MQTT (30%)
- **基礎**: 標準庫、簡單封裝 (50%)

### 按依賴層級分佈
- **核心依賴**: Python解釋器、FastAPI、ChromaDB (必須)
- **重要依賴**: TensorFlow/PyTorch、MQTT代理 (關鍵功能)
- **輔助依賴**: requests、BeautifulSoup4、psutil (增強功能)
- **開發依賴**: 測試框架、格式化工具 (開發支持)

## 🎯 關鍵技術使用位置

### 高優先級技術位置

#### 1. BaseAgent系統核心位置
```
apps/backend/src/agents/base_agent.py  # BaseAgent核心 (必須修復)
apps/backend/src/agents/specialized/   # 11個專業代理 (必須驗證)
```

#### 2. HSP協議核心位置  
```
apps/backend/src/core/hsp/types.py     # HSP協議類型 (通信基礎)
apps/backend/src/core/hsp/connector.py # MQTT連接器 (消息基礎)
```

#### 3. 工具系統核心位置
```
apps/backend/src/core/tools/web_search_tool.py  # Web搜索 (已修復)
apps/backend/src/core/tools/math_tool.py        # 數學工具 (待驗證)
apps/backend/src/core/tools/file_system_tool.py # 文件工具 (待驗證)
```

#### 4. 多LLM服務核心位置
```
apps/backend/src/core/services/multi_llm_service.py  # 多模型服務 (待驗證)
```

### 中優先級技術位置

#### 概念模型位置
```
apps/backend/src/ai/concept_models/alpha_deep_model.py           # Alpha深度模型
apps/backend/src/ai/concept_models/unified_symbolic_space.py    # 統一符號空間
apps/backend/src/ai/concept_models/environment_simulator.py     # 環境模擬器
```

#### 記憶系統位置
```
apps/backend/src/ai/memory/ham_memory_manager.py  # HAM記憶管理器
apps/backend/src/ai/memory/vector_store.py       # 向量存儲 (ChromaDB)
```

#### 訓練系統位置
```
training/train_model.py                           # 主訓練腳本
training/auto_training_manager.py                # 自動訓練管理器
training/collaborative_training_manager.py       # 協作訓練管理器
```

## 🔧 開發建議和注意事項

### 1. 技術一致性原則
- **Python版本**: 統一使用Python 3.8+標準
- **異步處理**: 統一使用asyncio和async/await
- **類型註解**: 全面使用Python類型註解
- **錯誤處理**: 統一的異常處理模式

### 2. 依賴管理原則
- **版本鎖定**: 鎖定關鍵依賴版本避免兼容性問題
- **分層依賴**: 按層次管理依賴關係
- **依賴最小化**: 避免不必要的依賴引入
- **依賴文檔**: 每個依賴都要有明確用途文檔

### 3. 配置管理原則
- **集中配置**: 統一的配置管理中心
- **環境隔離**: 開發/測試/生產環境配置隔離
- **配置驗證**: 配置加載時的完整性驗證
- **熱加載**: 支持配置的動態更新

### 4. 測試策略原則
- **分層測試**: 單元測試 → 集成測試 → 系統測試
- **真實測試**: 基於真實組件而非模擬
- **並發測試**: 多代理、多工具、多模型同時測試
- **性能測試**: 真實負載下的性能基準測試

## 📋 技術使用檢查清單

### 必須驗證的核心技術
- [ ] BaseAgent系統 - `apps/backend/src/agents/base_agent.py`
- [ ] HSP協議 - `apps/backend/src/core/hsp/types.py`
- [ ] WebSearchTool - `apps/backend/src/core/tools/web_search_tool.py`
- [ ] MultiLLMService - `apps/backend/src/core/services/multi_llm_service.py`
- [ ] ChromaDB集成 - 向量數據庫功能
- [ ] MQTT連接 - 消息隊列通信

### 需要驗證的重要技術
- [ ] 11個專門化代理 - `apps/backend/src/ai/agents/specialized/`
- [ ] 5個概念模型 - `apps/backend/src/ai/concept_models/`
- [ ] 記憶管理系統 - `apps/backend/src/ai/memory/`
- [ ] 訓練系統 - `training/`目錄下所有組件
- [ ] 監控系統 - `apps/backend/src/core/monitoring/`

### 需要驗證的輔助技術
- [ ] 數學工具 - `apps/backend/src/core/tools/math_tool.py`
- [ ] 文件工具 - `apps/backend/src/core/tools/file_system_tool.py`
- [ ] 系統工具 - `apps/backend/src/core/tools/system_monitor_tool.py`
- [ ] 配置管理 - 所有YAML配置文件
- [ ] 開發工具鏈 - 測試框架和CI/CD

---

**系統樹完成**: 2025年10月12日  
**分析深度**: 技術組件到文件級別的定位  
**用途**: 指導全域性系統測試的具體實施路徑