# 🌟 catcatAI 統一文檔索引與分類系統 (中英雙語版)

## 📋 文檔概覽

根據 `PROJECTS_COLLABORATION_GUIDE_Version2.md` 的指導原則，本索引將所有 MD 文檔按照功能、重要性、使用場景及語言進行分類整理。

---

## 🎯 專案架構總覽

### 主要專案結構
```
catcatAI 組織
├── github-connect-quest/          # GitHub 集成與自動化工具
│   ├── 前端界面 (React + TypeScript)
│   └── GitHub API 集成後端
└── Unified-AI-Project/           # AI 平台與後端服務集成
    ├── 核心 AI 服務
    ├── 遊戲系統 (Angela's World)
    ├── 技術架構與文檔
    └── packages/
        └── ui/                     # 共享 UI 組件庫
```

---

## 📚 按專案分類的文檔結構

### 🔗 GitHub Connect Quest 專案文檔

#### 核心文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 狀態 |
|---|---|---|---|---|
| 專案概述 | (英) | `github-connect-quest/README.md` | Lovable 專案基本信息 | ✅ 基礎 |
| 協作指南 | (中) | `Unified-AI-Project/docs/PROJECTS_COLLABORATION_GUIDE_Version2.md` | 統一協作與技術指南 | ✅ 完整 |

#### 技術特性
- **前端技術棧**: React + TypeScript + Vite + shadcn-ui + Tailwind CSS
- **專案類型**: GitHub 集成與自動化工具前端界面
- **部署平台**: Lovable (https://lovable.dev)
- **開發模式**: 支援本地開發和雲端編輯

---

### 🤖 Unified AI Project 文檔分類

#### 🏠 核心入門文檔
| 優先級 | 文檔名稱 | 語言 | 路徑 | 描述 | 完整度 |
|---|---|---|---|---|---|
| 🔴 必讀 | 專案概述 | (英) | `Unified-AI-Project/docs/README.md` | 專案簡介與快速開始 | ✅ 完整 |
| 🟡 重要 | 術語表 | (中) | `Unified-AI-Project/docs/00-overview/GLOSSARY.md` | 關鍵概念定義 | ✅ 完整 |
| 🟡 重要 | 貢獻指南 | (英) | `Unified-AI-Project/CONTRIBUTING.md` | 參與專案指南 | ✅ 完整 |
| 🟢 參考 | 文檔索引 | (中) | `Unified-AI-Project/docs/00-overview/README.md` | 完整文檔導航 | ✅ 完整 |

#### 🎮 遊戲設計文檔 (Angela's World)
| 文檔名稱 | 語言 | 路徑 | 描述 | 完整度 | 技術複雜度 |
|---|---|---|---|---|---|
| 遊戲總覽 | (中) | `docs/02-game-design/README.md` | Angela's World 概述 | ✅ 完整 | 🟢 低 |
| 主設計文檔 | (中) | `docs/02-game-design/main-design.md` | 核心遊戲設計理念 | ✅ 完整 | 🟡 中 |
| 角色設計 | (中) | `docs/02-game-design/character-design/general-characters.md` | 遊戲角色設定 | ✅ 完整 | 🟡 中 |
| Angela 設計 | (中) | `docs/02-game-design/character-design/angela-design.md` | AI 角色詳細設計 | ✅ 完整 | 🔴 高 |
| 遊戲系統 | (中) | `docs/02-game-design/game-systems.md` | 遊戲機制設計 | ✅ 完整 | 🟡 中 |
| 地圖設計 | (中) | `docs/02-game-design/map-design.md` | 遊戲世界設計 | ✅ 完整 | 🟡 中 |
| 玩家角色 | (英) | `docs/02-game-design/player.md` | 遊戲玩家角色管理 | ✅ 完整 | 🟢 低 |
| 成功標準 | (中) | `docs/02-game-design/success-criteria.md` | 遊戲成功指標 | ✅ 完整 | 🟢 低 |
| 場景與遊戲狀態管理 | (英) | `docs/02-game-design/scenes.md` | 遊戲場景和狀態管理 | ✅ 完整 | 🟢 低 |
| 庫存系統 | (英) | `docs/02-game-design/inventory.md` | 遊戲內物品管理 | ✅ 完整 | 🟢 低 |
| 物品定義 | (英) | `docs/02-game-design/items.md` | 遊戲物品定義和管理 | ✅ 完整 | 🟢 低 |
| 遊戲主模組 | (英) | `docs/02-game-design/game-main.md` | 遊戲核心循環和初始化 | ✅ 完整 | 🟢 低 |
| 遊戲小遊戲 | (英) | `docs/02-game-design/minigames.md` | 遊戲內互動小遊戲 | ✅ 完整 | 🟢 低 |
| NPC 系統 | (英) | `docs/02-game-design/npcs.md` | 遊戲非玩家角色管理 | ✅ 完整 | 🟢 低 |
| 美術資源規範 | (英) | `docs/02-game-design/art-asset-specification.md` | 遊戲美術資源規格 | ✅ 完整 | 🟢 低 |
| 地圖瓦片設計 | (英) | `docs/02-game-design/tiles.md` | 遊戲地圖瓦片設計 | ✅ 完整 | 🟢 低 |
| 遊戲工具 | (英) | `docs/02-game-design/game-utils.md` | 遊戲通用實用函數 | ✅ 完整 | 🟢 低 |
| 主設計文檔 | (中) | `docs/02-game-design/main-design.md` | 核心遊戲設計理念 | ✅ 完整 | 🟡 中 |
| 角色設計 | (中) | `docs/02-game-design/character-design/general-characters.md` | 遊戲角色設定 | ✅ 完整 | 🟡 中 |
| Angela 設計 | (中) | `docs/02-game-design/character-design/angela-design.md` | AI 角色詳細設計 | ✅ 完整 | 🔴 高 |
| 遊戲系統 | (中) | `docs/02-game-design/game-systems.md` | 遊戲機制設計 | ✅ 完整 | 🟡 中 |
| 地圖設計 | (中) | `docs/02-game-design/map-design.md` | 遊戲世界設計 | ✅ 完整 | 🟡 中 |
| 玩家角色 | (英) | `docs/02-game-design/player.md` | 遊戲玩家角色管理 | ✅ 完整 | 🟢 低 |
| 成功標準 | (中) | `docs/02-game-design/success-criteria.md` | 遊戲成功指標 | ✅ 完整 | 🟢 低 |
| 場景與遊戲狀態管理 | (英) | `docs/02-game-design/scenes.md` | 遊戲場景和狀態管理 | ✅ 完整 | 🟢 低 |
| 庫存系統 | (英) | `docs/02-game-design/inventory.md` | 遊戲內物品管理 | ✅ 完整 | 🟢 低 |
| 物品定義 | (英) | `docs/02-game-design/items.md` | 遊戲物品定義和管理 | ✅ 完整 | 🟢 低 |
| 遊戲主模組 | (英) | `docs/02-game-design/game-main.md` | 遊戲核心循環和初始化 | ✅ 完整 | 🟢 低 |
| 遊戲小遊戲 | (英) | `docs/02-game-design/minigames.md` | 遊戲內互動小遊戲 | ✅ 完整 | 🟢 低 |
| UI 系統 | (英) | `docs/02-game-design/ui.md` | 遊戲對話框和 UI 元素 | ✅ 完整 | 🟢 低 |
| NPC 系統 | (英) | `docs/02-game-design/npcs.md` | 遊戲非玩家角色管理 | ✅ 完整 | 🟢 低 |

#### 🏗️ 核心技術架構文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| 架構概述 | (英) | `docs/03-technical-architecture/README.md` | 系統整體架構 | 🔴 高 | 🟢 高 |
| 核心服務概述 | (英) | `docs/03-technical-architecture/core-services/overview.md` | 核心服務初始化與管理 | 🟡 中 | 🟢 高 |
| HSP 規範 | (英) | `docs/03-technical-architecture/communication/hsp-specification/01-overview-and-concepts.md` | 異構服務協議詳細規範 (已分解) | 🔴 極高 | 🟡 中 |
| HSP 快速開始 | (英) | `docs/03-technical-architecture/communication/hsp-quick-start.md` | HSP 快速入門指南 | 🟡 中 | 🟢 高 |
| HAM 設計規範 | (英) | `docs/03-technical-architecture/memory-systems/ham-design.md` | 分層抽象記憶系統 | 🔴 極高 | 🔴 高 |
| 多模型 LLM 服务 | (中) | `docs/03-technical-architecture/ai-components/multi-llm-service.md` | 统一 AI 模型接口 | 🟡 中 | 🟢 高 |
| Fragmenta 設計 | (英) | `docs/04-advanced-concepts/fragmenta-design.md` | Fragmenta 架構規範 | 🔴 極高 | 🟡 中 |
| Project Coordinator | (英) | `docs/03-technical-architecture/core-services/project-coordinator.md` | 複雜任務協調器 | 🔴 高 | 🟢 高 |
| HSP Connector | (英) | `docs/03-technical-architecture/communication/hsp-connector.md` | HSP 通訊連接器 | 🔴 高 | 🟢 高 |
| 外部代理整合 | (英) | `docs/03-technical-architecture/integrations/external-agent-integration.md` | 外部 AI 工具整合架構 | 🔴 高 | 🟢 高 |

##### AI 組件詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| Alpha Deep Model | (英) | `docs/03-technical-architecture/ai-components/alpha-deep-model.md` | AI 內部狀態高壓縮模型 | 🔴 極高 | 🟡 中 |
| 音頻處理 | (英) | `docs/03-technical-architecture/ai-components/audio-processing.md` | 音頻處理模組佔位符 | 🟢 低 | 🟡 中 |
| 音頻服務 | (英) | `docs/03-technical-architecture/ai-components/audio-service.md` | 語音轉文本與文本轉語音 | 🟡 中 | 🟢 高 |
| 計算器工具 | (英) | `docs/03-technical-architecture/ai-components/calculator-tool.md` | 數學表達式計算工具 | 🟢 低 | 🟢 高 |
| 代碼理解工具 | (英) | `docs/03-technical-architecture/ai-components/code-understanding-tool.md` | Python 工具代碼理解 | 🟡 中 | 🟢 高 |
| 代碼理解模組 | (英) | `docs/03-technical-architecture/ai-components/code-understanding.md` | 輕量級代碼靜態分析 | 🟡 中 | 🟢 高 |
| 創造引擎 | (英) | `docs/03-technical-architecture/ai-components/creation-engine.md` | 動態生成 AI 模型與工具代碼 | 🔴 高 | 🟡 中 |
| 危機系統 | (英) | `docs/03-technical-architecture/ai-components/crisis-system.md` | AI 危機檢測與管理 | 🟡 中 | 🟢 高 |
| 內容分析模組 | (英) | `docs/03-technical-architecture/ai-components/content-analyzer-module.md` | 知識圖譜構建與文本分析 | 🔴 高 | 🟢 高 |
| CSV 工具 | (英) | `docs/03-technical-architecture/ai-components/csv-tool.md` | CSV 數據分析工具 | 🟢 低 | 🟢 高 |
| 日常語言模型 | (英) | `docs/03-technical-architecture/ai-components/daily-language-model.md` | 用戶意圖識別與工具調度 | 🟡 中 | 🟢 高 |
| 深度映射器 | (英) | `docs/03-technical-architecture/ai-components/deep-mapper.md` | 數據轉換引擎 | 🔴 高 | 🟡 中 |
| 演示學習管理器 | (英) | `docs/03-technical-architecture/ai-components/demo-learning-manager.md` | 演示環境自動學習與清理 | 🟢 低 | 🟢 高 |
| 依賴管理器 | (英) | `docs/03-technical-architecture/ai-components/dependency-manager.md` | 集中式依賴管理系統 | 🟡 中 | 🟢 高 |
| 情感系統 | (英) | `docs/03-technical-architecture/ai-components/emotion-system.md` | AI 情感狀態管理 | 🟡 中 | 🟢 高 |
| 環境模擬器 | (英) | `docs/03-technical-architecture/ai-components/environment-simulator.md` | AI 世界模型與動作後果模擬 | 🔴 高 | 🟢 高 |
| 經驗重放緩衝區 | (英) | `docs/03-technical-architecture/ai-components/experience-replay.md` | 強化學習核心組件 | 🟡 中 | 🟢 高 |
| 事實提取模組 | (英) | `docs/03-technical-architecture/ai-components/fact-extractor-module.md` | LLM 驅動的事實與偏好提取 | 🔴 高 | 🟢 高 |
| 評估器 | (英) | `docs/03-technical-architecture/ai-components/evaluator.md` | AI 模型與工具性能評估 | 🟡 中 | 🟢 高 |
| 執行管理器 | (英) | `docs/03-technical-architecture/ai-components/execution-manager.md` | 統一執行管理系統 | 🔴 高 | 🟢 高 |
| 執行監控模組 | (英) | `docs/03-technical-architecture/ai-components/execution-monitor-module.md` | 智能執行監控功能 | 🟡 中 | 🟢 高 |
| 任務執行評估器 | (英) | `docs/03-technical-architecture/ai-components/task-evaluator.md` | AI 任務執行評估系統 | 🟡 中 | 🟢 高 |
| 公式引擎 | (英) | `docs/03-technical-architecture/ai-components/formula-engine.md` | 預定義規則執行 | 🟡 中 | 🟢 高 |
| 公式引擎類型 | (英) | `docs/03-technical-architecture/ai-components/formula-engine-types.md` | 公式配置類型定義 | 🟢 低 | 🟢 高 |
| Fragmenta 元素層 | (英) | `docs/03-technical-architecture/ai-components/fragmenta-element-layer.md` | Fragmenta 元素數據處理 | 🟡 中 | 🟢 高 |
| Fragmenta 視覺語氣反轉器 | (英) | `docs/03-technical-architecture/ai-components/fragmenta-vision-tone-inverter.md` | 動態視覺語氣調整 | 🟡 中 | 🟢 高 |
| 創世紀管理器 | (英) | `docs/03-technical-architecture/ai-components/genesis-manager.md` | AI 身份與記憶恢復 | 🔴 高 | 🟢 高 |
| JS 工具調度器 | (英) | `docs/03-technical-architecture/ai-components/js-tool-dispatcher.md` | JavaScript 工具集成與執行 | 🟡 中 | 🟢 高 |
| 知識蒸餾管理器 | (英) | `docs/03-technical-architecture/ai-components/knowledge-distillation.md` | 知識從教師模型到學生模型轉移 | 🔴 高 | 🟢 高 |
| 知識圖譜類型 | (英) | `docs/03-technical-architecture/ai-components/knowledge-graph-types.md` | 知識圖譜數據結構定義 | 🟢 低 | 🟢 高 |
| 知識蒸餾管理器 | (英) | `docs/03-technical-architecture/ai-components/knowledge-distillation.md` | 知識從教師模型到學生模型轉移 | 🔴 高 | 🟢 高 |
| 語言模型註冊表 | (英) | `docs/03-technical-architecture/ai-components/language-model-registry.md` | 集中式 LLM 模型註冊表 | 🟡 中 | 🟢 高 |
| 語言模型路由器 | (英) | `docs/03-technical-architecture/ai-components/language-model-router.md` | 基於啟發式的 LLM 模型路由器 | 🟡 中 | 🟢 高 |
| LIS 緩存接口 | (英) | `docs/03-technical-architecture/ai-components/lis-cache-interface.md` | 語言免疫系統緩存接口 | 🔴 高 | 🟢 高 |
| LIS 語氣修復引擎 | (英) | `docs/03-technical-architecture/ai-components/lis-tonal-repair-engine.md` | 語言免疫系統語氣修復 | 🟢 低 | 🟡 中 |
| LIS 類型 | (英) | `docs/03-technical-architecture/ai-components/lis-types.md` | 語言免疫系統數據結構 | 🟢 低 | 🟢 高 |
| 知識圖譜 | (英) | `docs/03-technical-architecture/ai-components/knowledge-graph.md` | 知識表示與存儲 | 🔴 高 | 🟡 中 |
| 輕量級代碼模型 | (英) | `docs/03-technical-architecture/ai-components/lightweight-code-model.md` | Python 代碼輕量級靜態分析 | 🟡 中 | 🟢 高 |
| 學習管理器 | (英) | `docs/03-technical-architecture/ai-components/learning-manager.md` | AI 知識獲取與整合 | 🔴 高 | 🟢 高 |
| 學習類型 | (英) | `docs/03-technical-architecture/ai-components/learning-types.md` | AI 學習系統數據結構 | 🟢 低 | 🟢 高 |
| 邏輯模型 | (英) | `docs/03-technical-architecture/ai-components/logic-model.md` | 布爾表達式評估 | 🟡 中 | 🟢 高 |
| 數學模型 | (英) | `docs/03-technical-architecture/ai-components/math-model.md` | 輕量級算術計算 | 🟡 中 | 🟢 高 |
| 自然語言生成工具 | (英) | `docs/03-technical-architecture/ai-components/natural-language-generation-tool.md` | 文本生成工具 | 🟡 中 | 🟢 高 |
| 參數提取器 | (英) | `docs/03-technical-architecture/ai-components/parameter-extractor.md` | 模型配置管理 | 🟡 中 | 🟢 高 |
| 個性管理器 | (英) | `docs/03-technical-architecture/ai-components/personality-manager.md` | AI 個性定義與調整 | 🟡 中 | 🟢 高 |
| RAG 管理器 | (英) | `docs/03-technical-architecture/ai-components/rag-manager.md` | 檢索增強生成 | 🔴 高 | 🟢 高 |
| 因果推理引擎 | (英) | `docs/03-technical-architecture/ai-components/causal-reasoning-engine.md` | 因果理解、反事實與干預 | 🔴 高 | 🟢 高 |
| 資源感知服務 | (英) | `docs/03-technical-architecture/ai-components/resource-awareness-service.md` | 模擬硬件資源感知 | 🟡 中 | 🟢 高 |
| 即時翻譯 | (英) | `docs/03-technical-architecture/ai-components/simultaneous-translation.md` | 輕量級模擬即時翻譯 | 🟢 低 | 🟡 中 |
| 自我批評模組 | (英) | `docs/03-technical-architecture/ai-components/self-critique-module.md` | LLM 驅動的 AI 響應評估 | 🔴 高 | 🟢 高 |
| 服務發現模組 | (英) | `docs/03-technical-architecture/ai-components/service-discovery.md` | 動態服務發現與註冊 | 🟡 中 | 🟢 高 |
| 自我批評模組 | (英) | `docs/03-technical-architecture/ai-components/self-critique-module.md` | LLM 驅動的 AI 響應評估 | 🔴 高 | 🟢 高 |
| 服務發現模組 | (英) | `docs/03-technical-architecture/ai-components/service-discovery-module.md` | 動態服務發現與註冊 | 🟡 中 | 🟢 高 |
| 語音轉文本工具 | (英) | `docs/03-technical-architecture/ai-components/speech-to-text-tool.md` | 語音識別工具 | 🟡 中 | 🟢 高 |
| 時間系統 | (英) | `docs/03-technical-architecture/ai-components/time-system.md` | 時間感知與管理 | 🟢 低 | 🟢 高 |
| 工具調度器 | (英) | `docs/03-technical-architecture/ai-components/tool-dispatcher.md` | 智能工具路由 | 🔴 高 | 🟢 高 |
| 翻譯模型 | (英) | `docs/03-technical-architecture/ai-components/translation-model.md` | 輕量級詞典翻譯 | 🟢 低 | 🟡 中 |
| 翻譯工具 | (英) | `docs/03-technical-architecture/ai-components/translation-tool.md` | 詞典翻譯工具 | 🟢 低 | 🟡 中 |
| 信任管理器 | (英) | `docs/03-technical-architecture/ai-components/trust-manager-module.md` | AI 實體信任評分管理 | 🔴 高 | 🟢 高 |
| 信任管理器 | (英) | `docs/03-technical-architecture/ai-components/trust-manager.md` | AI 實體信任評估 | 🔴 高 | 🟢 高 |
| 統一模型加載器 | (英) | `docs/03-technical-architecture/ai-components/unified-model-loader.md` | 統一模型加載與管理 | 🟡 中 | 🟢 高 |
| 統一控制中心 | (英) | `docs/03-technical-architecture/ai-components/unified-control-center.md` | 統一 AI 系統控制中心 | 🔴 極高 | 🟡 中 |
| 統一模型加載器 | (英) | `docs/03-technical-architecture/ai-components/unified-model-loader.md` | 統一模型加載與管理 | 🟡 中 | 🟢 高 |
| 向量記憶存儲 | (英) | `docs/03-technical-architecture/ai-components/vector-store.md` | 向量化記憶存儲 | 🔴 高 | 🟢 高 |
| 視覺服務 | (英) | `docs/03-technical-architecture/ai-components/vision-service.md` | 圖像理解與分析 | 🟡 中 | 🟢 高 |
| 網絡搜索工具 | (英) | `docs/03-technical-architecture/ai-components/web-search-tool.md` | 網絡信息檢索 | 🟢 低 | 🟢 高 |

##### 工具詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| 工具分派器 | (英) | `docs/03-technical-architecture/tools/tool-dispatcher.md` | 集中式工具路由與執行 | 🔴 高 | 🟢 高 |
| 圖像生成工具 | (英) | `docs/03-technical-architecture/tools/image-generation-tool.md` | 從文本提示生成圖像 | 🟡 中 | 🟢 高 |
| 代碼理解工具 | (英) | `docs/03-technical-architecture/tools/code-understanding-tool.md` | Python 工具代碼理解 | 🟡 中 | 🟢 高 |
| CSV 工具 | (英) | `docs/03-technical-architecture/tools/csv-tool.md` | CSV 數據分析工具 | 🟢 低 | 🟢 高 |
| 邏輯工具 | (英) | `docs/03-technical-architecture/tools/logic-tool.md` | 評估邏輯表達式 | 🟡 中 | 🟢 高 |
| 數學工具 | (英) | `docs/03-technical-architecture/tools/math-tool.md` | 從自然語言進行算術計算 | 🟡 中 | 🟢 高 |
| 自然語言生成工具 | (英) | `docs/03-technical-architecture/tools/natural-language-generation-tool.md` | 生成類人文本 | 🟡 中 | 🟢 高 |
| 語音轉文本工具 | (英) | `docs/03-technical-architecture/tools/speech-to-text-tool.md` | 從音頻識別語音 | 🟡 中 | 🟢 高 |
| 翻譯工具 | (英) | `docs/03-technical-architecture/tools/translation-tool.md` | 基於詞典的文本翻譯 | 🟢 低 | 🟢 高 |
| 網絡搜索工具 | (英) | `docs/03-technical-architecture/tools/web-search-tool.md` | 網絡信息檢索 | 🟢 低 | 🟢 高 |

##### API 詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| 主 API 服務器 | (英) | `docs/03-technical-architecture/api/main-api-server.md` | 外部接口與服務生命週期管理 | 🔴 高 | 🟢 高 |
| API 模型 | (英) | `docs/03-technical-architecture/api/api-models.md` | 後端服務數據結構 | 🟢 高 | 🟢 高 |
| 多模型 LLM 服務 | (英) | `docs/03-technical-architecture/api/multi-llm-service.md` | 統一 LLM 接口 | 🔴 高 | 🟢 高 |
| 多模型 LLM API | (中) | `docs/03-technical-architecture/api/multi-llm-api.md` | 多模型 LLM 服務 API 參考 | 🟡 中 | 🟢 高 |
| Node.js 服務 | (英) | `docs/03-technical-architecture/api/node-services.md` | 未來微服務佔位符 | 🟢 低 | 🟡 中 |
| 服務類型 | (英) | `docs/03-technical-architecture/api/service-types.md` | 服務層數據結構定義 | 🟢 低 | 🟢 高 |
| 服務類型 | (英) | `docs/03-technical-architecture/api/service-types.md` | 服務層數據結構定義 | 🟢 低 | 🟢 高 |

##### 通訊協議詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| HSP 消息信封與模式 | (英) | `docs/03-technical-architecture/communication/hsp-specification/02-message-envelope-and-patterns.md` | HSP 消息結構與通訊模式 | 🔴 高 | 🟢 高 |
| HSP 交互邏輯與網絡服務 | (英) | `docs/03-technical-architecture/communication/hsp-specification/03-interaction-logic-and-services.md` | HSP 高層交互與服務 | 🔴 高 | 🟢 高 |
| HSP 傳輸與未來考量 | (英) | `docs/03-technical-architecture/communication/hsp-specification/04-transport-and-future.md` | HSP 傳輸層與未來發展 | 🟡 中 | 🟢 高 |
| HSP 能力與任務載荷 | (英) | `docs/03-technical-architecture/communication/hsp-specification/message-payloads/capability-and-task.md` | HSP 能力與任務消息載荷 | 🟡 中 | 🟢 高 |
| HSP 上下文與狀態載荷 | (英) | `docs/03-technical-architecture/communication/hsp-specification/message-payloads/context-and-state.md` | HSP 環境與 AI 狀態同步載荷 | 🟡 中 | 🟢 高 |
| HSP 事實與信念載荷 | (英) | `docs/03-technical-architecture/communication/hsp-specification/message-payloads/fact-and-belief.md` | HSP 知識表示與共享載荷 | 🟡 中 | 🟢 高 |
| HSP 消息載荷 README | (英) | `docs/03-technical-architecture/communication/hsp-specification/message-payloads/README.md` | HSP 消息載荷概述 | 🟢 低 | 🟢 高 |
| HSP 規範 README | (英) | `docs/03-technical-architecture/communication/hsp-specification/README.md` | HSP 協議規範總覽 | 🟢 低 | 🟢 高 |
| HSP 類型定義 | (英) | `docs/03-technical-architecture/communication/hsp-types.md` | HSP 數據結構與消息格式 | 🟢 低 | 🟢 高 |
| 數據對齊器 | (英) | `docs/03-technical-architecture/communication/data-aligner.md` | HSP 消息對齊與驗證 | 🟡 中 | 🟢 高 |
| 消息橋接器 | (英) | `docs/03-technical-architecture/communication/message-bridge.md` | 外部 HSP 與內部消息橋接 | 🔴 高 | 🟢 高 |
| MCP 連接器 | (英) | `docs/03-technical-architecture/communication/mcp-connector.md` | 管理控制協議通訊 | 🟡 中 | 🟢 高 |
| MCP Context7 連接器 | (英) | `docs/03-technical-architecture/communication/mcp-context7-connector.md` | Context7 MCP 增強集成 | 🔴 高 | 🟢 高 |
| 外部連接器 | (英) | `docs/03-technical-architecture/communication/external-connector.md` | MQTT 外部通訊橋接 | 🔴 高 | 🟢 高 |
| HSP 備用協議 | (英) | `docs/03-technical-architecture/communication/hsp-fallback-protocols.md` | 彈性通訊系統 | 🔴 高 | 🟢 高 |
| 備用配置加載器 | (英) | `docs/03-technical-architecture/communication/fallback-config-loader.md` | HSP 備用協議配置加載器 | 🟡 中 | 🟢 高 |
| 內部總線 | (英) | `docs/03-technical-architecture/communication/internal-bus.md` | 進程內發布-訂閱消息系統 | 🟡 中 | 🟢 高 |
| HSP 類型定義 | (英) | `docs/03-technical-architecture/communication/hsp-types.md` | HSP 消息定義 | 🔴 高 | 🟢 高 |
| MCP 連接器 | (英) | `docs/03-technical-architecture/communication/mcp-connector.md` | 管理控制協議通訊 | 🟡 中 | 🟢 高 |
| MCP Context7 連接器 | (英) | `docs/03-technical-architecture/communication/mcp-context7-connector.md` | Context7 MCP 增強集成 | 🔴 高 | 🟢 高 |
| MCP 類型定義 | (英) | `docs/03-technical-architecture/communication/mcp-types.md` | MCP 數據結構與消息格式 | 🟢 低 | 🟢 高 |
| MCP 類型定義 | (英) | `docs/03-technical-architecture/communication/mcp-types.md` | MCP 數據結構與消息格式 | 🟢 低 | 🟢 高 |

##### 核心服務詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| 代理管理器 | (英) | `docs/03-technical-architecture/core-services/agent-manager.md` | 專門化子代理生命週期管理 | 🔴 高 | 🟢 高 |
| 對話管理器 | (英) | `docs/03-technical-architecture/core-services/dialogue-manager.md` | 用戶交互與 AI 服務協調 | 🔴 高 | 🟢 高 |
| 核心服務模組 | (英) | `docs/03-technical-architecture/core-services/core-services-module.md` | 集中式服務初始化與管理 | 🔴 高 | 🟢 高 |
| 配置加載器 | (英) | `docs/03-technical-architecture/core-services/config-loader.md` | 集中式應用配置管理 | 🟢 低 | 🟢 高 |
| AI 虛擬輸入服務 | (英) | `docs/03-technical-architecture/core-services/ai-virtual-input-service.md` | 模擬 GUI 交互 | 🔴 高 | 🟢 高 |
| 代理管理器 | (英) | `docs/03-technical-architecture/core-services/agent-manager.md` | 專門化子代理生命週期管理 | 🔴 高 | 🟢 高 |
| 搜索引擎 | (英) | `docs/03-technical-architecture/core-services/search-engine.md` | 統一 AI 模型與工具發現 | 🟡 中 | 🟢 高 |
| 資源感知服務 | (英) | `docs/03-technical-architecture/core-services/resource-awareness-service.md` | 模擬硬件資源感知 | 🟡 中 | 🟢 高 |
| 沙盒執行器 | (英) | `docs/03-technical-architecture/core-services/sandbox-executor.md` | 安全隔離代碼執行 | 🔴 高 | 🟢 高 |
| 視覺服務 | (英) | `docs/03-technical-architecture/core-services/vision-service.md` | 圖像理解與分析 | 🟡 中 | 🟢 高 |
| 熱重載服務 | (英) | `docs/03-technical-architecture/core-services/hot-reload-service.md` | 核心 AI 服務動態熱重載 | 🔴 高 | 🟢 高 |
| 項目協調器 | (英) | `docs/03-technical-architecture/core-services/project-coordinator.md` | 複雜任務協調器 | 🔴 高 | 🟢 高 |
| 執行管理器 | (英) | `docs/03-technical-architecture/core-services/execution-manager.md` | 統一執行管理系統 | 🔴 高 | 🟢 高 |
| 項目協調器 | (英) | `docs/03-technical-architecture/core-services/project-coordinator.md` | 複雜任務協調器 | 🔴 高 | 🟢 高 |

##### 數據結構詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| 共享類型 | (英) | `docs/03-technical-architecture/data-structures/common-types.md` | 共享數據結構定義 | 🟢 低 | 🟢 高 |
| 可映射數據對象 | (英) | `docs/03-technical-architecture/data-structures/mappable-data-object.md` | 靈活數據容器 | 🟡 中 | 🟢 高 |
| HAM 配置 | (英) | `docs/03-technical-architecture/memory-systems/ham-config.md` | HAM 配置佔位符 | 🟢 低 | 🟢 高 |
| HAM 數據庫接口 | (英) | `docs/03-technical-architecture/memory-systems/ham-db-interface.md` | HAM 數據庫接口佔位符 | 🟢 低 | 🟢 高 |
| HAM 錯誤定義 | (英) | `docs/03-technical-architecture/memory-systems/ham-errors.md` | HAM 異常定義 | 🟢 低 | 🟢 高 |
| HAM 類型定義 | (英) | `docs/03-technical-architecture/memory-systems/ham-types.md` | HAM 數據結構定義 | 🟢 低 | 🟢 高 |
| HAM 記憶體管理器 | (英) | `docs/03-technical-architecture/memory-systems/ham-memory-manager.md` | 分層抽象記憶體管理器 | 🔴 高 | 🟢 高 |
| HAM 實用工具 | (英) | `docs/03-technical-architecture/memory-systems/ham-utils.md` | HAM 記憶體實用函數 | 🟢 低 | 🟢 高 |
| 重要性評分器 | (英) | `docs/03-technical-architecture/memory-systems/importance-scorer.md` | 記憶體重要性評分佔位符 | 🟢 低 | 🟢 高 |
| 記憶體類型 | (英) | `docs/03-technical-architecture/memory-systems/memory-types.md` | HAM 內部數據結構定義 | 🟢 低 | 🟢 高 |
| 自適應學習控制器 | (英) | `docs/03-technical-architecture/ai-components/adaptive-learning-controller.md` | 動態學習策略適應 | 🔴 高 | 🟢 高 |
| 元公式錯誤變數 | (英) | `docs/03-technical-architecture/ai-components/meta-formulas-errx.md` | 元公式語義錯誤變數 | 🟢 低 | 🟢 高 |
| 元公式基類 | (英) | `docs/03-technical-architecture/ai-components/meta-formula-base.md` | AI 元公式基類 | 🟡 中 | 🟢 高 |
| 元公式未定義字段 | (英) | `docs/03-technical-architecture/ai-components/meta-formulas-undefined-field.md` | 元公式未定義語義空間 | 🟢 低 | 🟢 高 |
| 分佈式處理框架 | (英) | `docs/03-technical-architecture/ai-components/distributed-processing.md` | 分佈式 AI 計算概念框架 | 🔴 高 | 🟢 高 |
| 向量記憶存儲 | (英) | `docs/03-technical-architecture/memory-systems/vector-memory-store.md` | 向量化記憶存儲 | 🔴 高 | 🟢 高 |

##### 整合詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| Atlassian 橋接 | (英) | `docs/03-technical-architecture/integrations/atlassian-bridge.md` | 與 Atlassian 服務無縫集成 | 🔴 高 | 🟢 高 |
| Rovo Dev 代理 | (英) | `docs/03-technical-architecture/integrations/rovo-dev-agent.md` | 智能開發助手代理 | 🔴 高 | 🟢 高 |

##### 代理詳情
| 文檔名稱 | 語言 | 路徑 | 描述 | 複雜度 | 實用性 |
|---|---|---|---|---|---|
| 基礎代理 | (英) | `docs/03-technical-architecture/agents/base-agent.md` | 專門化子代理基類 | 🟡 中 | 🟢 高 |
| 創意寫作代理 | (英) | `docs/03-technical-architecture/agents/creative-writing-agent.md` | 專門化創意寫作任務代理 | 🟡 中 | 🟢 高 |
| 數據分析代理 | (英) | `docs/03-technical-architecture/agents/data-analysis-agent.md` | 專門化數據分析任務代理 | 🟡 中 | 🟢 高 |
| 死鎖檢測器 | (英) | `docs/03-technical-architecture/ai-components/deadlock-detector.md` | 並發與資源洩漏檢測工具 | 🟡 中 | 🟢 高 |
| 圖像生成代理 | (英) | `docs/03-technical-architecture/agents/image-generation-agent.md` | 專門化圖像生成任務代理 | 🟡 中 | 🟢 高 |
| 網絡搜索代理 | (英) | `docs/03-technical-architecture/agents/web-search-agent.md` | 專門化網絡搜索任務代理 | 🟡 中 | 🟢 高 |

#### 🔧 專業技術規範文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 實用性 | 維護狀態 |
|---|---|---|---|---|---|
| API 端點摘要 | (英) | `docs/08-api-reference/README.md` | API 接口總覽 | 🟢 高 | ✅ 最新 |
| API 模型 | (英) | `docs/03-technical-architecture/api/api-models.md` | API 請求和響應的數據結構 | 🟢 高 | ✅ 最新 |
| 消息傳輸 | (英) | `docs/03-technical-architecture/communication/message-transport.md` | 消息傳輸機制 | 🟢 高 | ✅ 最新 |
| 模型和工具 | (英) | `docs/03-technical-architecture/ai-components/models-and-tools.md` | AI 模型工具集 | 🟢 高 | ✅ 最新 |
| 內部數據標準 | (英) | `docs/03-technical-architecture/memory-systems/data-standards.md` | 內部數據格式規範 | 🟡 中 | ✅ 最新 |
| 故障排除 | (英) | `docs/05-development/debugging/troubleshooting.md` | 問題解決指南 | 🟢 高 | ✅ 最新 |
| 執行監控 | (英) | `docs/05-development/debugging/execution-monitor.md` | 執行監控系統 | 🟡 中 | ✅ 最新 |
| API 端點 | (英) | `docs/API_ENDPOINTS.md` | 專案 API 端點列表 | 🟢 高 | ✅ 最新 |
| 值類型定義 | (英) | `docs/VALUE_TYPES.md` | 專案中使用的值類型定義 | 🟡 中 | ✅ 最新 |

#### 🧠 高級架構概念文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 研究性質 | 實現狀態 |
|---|---|---|---|---|---|
| 代理協作框架 | (英) | `docs/04-advanced-concepts/agent-collaboration.md` | 多代理協作機制 | 🔴 高 | 🟡 部分 |
| AI 虛擬輸入系統 | (英) | `docs/04-advanced-concepts/ai-virtual-input.md` | AVIS 系統規範 | 🔴 高 | 🟡 部分 |
| 語言免疫系統 | (英) | `docs/04-advanced-concepts/linguistic-immune-system.md` | LIS 系統規範 | 🔴 極高 | 🔴 概念 |
| 深度映射與個性模擬 | (英) | `docs/04-advanced-concepts/deep-mapping-personality.md` | 高級個性模擬 | 🔴 極高 | 🔴 概念 |
| 增強解耦策略 | (英) | `docs/04-advanced-concepts/enhanced-decoupling.md` | 模組解耦策略 | 🟡 中 | 🟢 實用 |
| 知識圖譜 | (英) | `docs/04-advanced-concepts/knowledge-graph.md` | 知識圖譜設計 | 🔴 高 | 🟡 部分 |
| 記憶系統 | (英) | `docs/03-technical-architecture/memory-systems/memory-overview.md` | 記憶系統概述 | 🔴 高 | 🟢 實現 |
| 元公式規範 | (英) | `docs/04-advanced-concepts/meta-formulas.md` | 元公式系統 | 🔴 極高 | 🔴 概念 |
| AI 虛擬輸入服務 | (英) | `docs/04-advanced-concepts/ai-virtual-input-service.md` | 模擬 UI 交互 | 🔴 高 | 🟡 部分 |
| Alpha Deep 模型設計 | (英) | `docs/04-advanced-concepts/alpha-deep-model-design.md` | AI 內部狀態高壓縮模型設計 | 🔴 極高 | 🟡 部分 |
| Fragmenta 編排器 | (英) | `docs/04-advanced-concepts/fragmenta-orchestrator.md` | 複雜任務記憶檢索與合成 | 🔴 高 | 🟡 部分 |

#### 🧪 測試與品質保證文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 狀態 | 實用性 |
|---|---|---|---|---|---|
| 測試總結 | (英) | `docs/05-development/testing/test-summary.md` | 測試修復記錄 | ✅ 最新 | 🟢 高 |
| 測試修復摘要 | (英) | `docs/05-development/testing/test-fixes.md` | 詳細修復歷史 | ✅ 最新 | 🟢 高 |
| 測試超時策略 | (英) | `docs/05-development/testing/timeout-strategy.md` | 測試超時處理 | ✅ 最新 | 🟡 中 |

#### 🛠️ 開發工具與腳本
| 腳本名稱 | 語言 | 路徑 | 描述 | 功能 | 實用性 |
|---|---|---|---|---|---|
| pytest 超時工具 | (中) | `scripts/add_pytest_timeouts.py` | 為 pytest 測試添加超時裝飾器 | 測試優化 | 🟢 高 |
| 通用測試超時工具 | (中) | `scripts/add_test_timeouts.py` | 支援 unittest 和 pytest 的超時設置 | 測試優化 | 🟢 高 |
| 測試超時裝飾器 | (中) | `scripts/add_timeout_to_tests.py` | 簡化版測試超時添加工具 | 測試優化 | 🟡 中 |
| API 健康檢查 | (英) | `scripts/health_check.py` | API 服務健康狀態檢查 | 監控工具 | 🟢 高 |
| 導入掃描工具 | (英) | `scripts/scan_imports.py` | 掃描專案中所有 Python 導入模塊 | 依賴分析 | 🟡 中 |

#### 📑 總結與報告
| 文檔名稱 | 語言 | 路徑 | 描述 | 狀態 | 實用性 |
|---|---|---|---|---|---|
| Rovo Dev AI 集成摘要 | (中) | `docs/01-summaries-and-reports/ROVO_DEV_AI_INTEGRATION_SUMMARY.md` | Rovo Dev AI 集成摘要 | ✅ 最新 | 🟢 高 |
| AI 模型總結 | (英) | `docs/01-summaries-and-reports/README_AI_MODELS.md` | AI 模型總結 | ✅ 最新 | 🟢 高 |
| HSP 備用機制總結 | (英) | `docs/01-summaries-and-reports/README_HSP_FALLBACK.md` | HSP 備用機制總結 | ✅ 最新 | 🟢 高 |
| 除錯總結 | (英) | `docs/01-summaries-and-reports/debugging_summary.md` | 除錯總結 | ✅ 最新 | 🟢 高 |
| 測試計畫 | (英) | `docs/01-summaries-and-reports/test_plan.md` | 測試計畫 | ✅ 最新 | 🟢 高 |
| 工作區組織完成報告 | (英) | `docs/01-summaries-and-reports/WORKSPACE_ORGANIZATION_COMPLETE.md` | 工作區組織完成報告 | ✅ 最新 | 🟢 高 |
| 未實作/部分實作核心功能摘要 | (英) | `docs/01-summaries-and-reports/UNIMPLEMENTED_FEATURES_SUMMARY.md` | 專案中未實作或部分實作的核心功能列表 | ✅ 最新 | 🟢 高 |

#### 🛡️ 備用機制與容錯文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 狀態 | 實用性 |
|---|---|---|---|---|---|
| Rovo Dev 實施最終報告 | (中) | `docs/06-project-management/reports/rovo-dev-implementation-final-report.md` | 備用機制完整實施報告 | ✅ 最新 | 🟢 高 |
| HSP 備用協議 | (英) | `docs/03-technical-architecture/communication/hsp-fallback-protocols.md` | HSP 備用協議規範 | ✅ 最新 | 🟢 高 |
| HSP 備用實施摘要 | (英) | `docs/03-technical-architecture/communication/hsp-fallback-implementation-summary.md` | HSP 備用實施細節 | ✅ 最新 | 🟡 中 |
| MCP 備用協議 | (英) | `docs/03-technical-architecture/communication/mcp-fallback-protocols.md` | MCP 備用協議系統 | ✅ 最新 | 🟢 高 |

#### 📊 專案管理與狀態文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 重要性 | 時效性 |
|---|---|---|---|---|---|
| 專案狀態摘要 | (中) | `docs/06-project-management/planning/project-status-summary.md` | 專案狀態總結 | 🟢 高 | ✅ 活躍 |
| 專案組織狀態 | (中) | `docs/06-project-management/status/organization-status.md` | 當前組織狀態 | 🟢 高 | ✅ 活躍 |
| 內容組織 | (中) | `docs/06-project-management/planning/content-organization.md` | 內容組織方式 | 🟡 中 | ✅ 穩定 |
| 成功標準 | (中) | `docs/06-project-management/status/success-criteria.md` | 專案成功指標 | 🟢 高 | ✅ 穩定 |
| 進度追蹤 | (中) | `docs/06-project-management/status/progress-tracker.md` | 進度追蹤記錄 | 🟡 中 | ✅ 活躍 |
| 今日成就 | (中) | `docs/06-project-management/status/achievements.md` | 每日成就記錄 | 🟡 中 | ✅ 活躍 |
| 每日勝利摘要 | (中) | `docs/06-project-management/status/daily-wins.md` | 每日勝利記錄 | 🟡 中 | ✅ 活躍 |

#### 🚧 開發與維護文檔
- Observability Guide — `docs/05-development/observability-guide.md`
- Hot Reload & Drain — `docs/05-development/hot-reload-and-drain.md` (endpoints & examples)

| 文檔名稱 | 語言 | 路徑 | 描述 | 時效性 | 維護狀態 |
|---|---|---|---|---|---|
| **舊版專案摘要** | (中) | `docs/06-project-management/reports/legacy-project-summary.md` | **描述專案早期狀態的歷史摘要** | 🟡 **歷史** | 🟢 **高** |
| **合併與重構計畫** | (中) | `docs/06-project-management/reports/merge-restructure-plan.md` | **記錄了將專案遷移到 monorepo 的計畫** | 🟡 **歷史** | 🟢 **高** |
| 待辦事項 | (中) | `docs/06-project-management/planning/todo-placeholders.md` | 開發待辦列表 | 🟢 活躍 | ✅ 維護中 |
| **重構週期1總結** | (中) | `docs/06-project-management/reports/refactoring_sprint_1_summary.md` | **第一次文件-程式碼-測試同步週期的總結報告** | ✅ **最新** | 🟢 **高** |
| 清理摘要 | (中) | `docs/06-project-management/reports/cleanup-summary.md` | 專案清理記錄 | 🟡 歷史 | ✅ 完成 |
| 工作目錄整理總結 | (中) | `docs/06-project-management/reports/workspace-cleanup-summary.md` | 目錄整理與清理記錄 | ✅ 最新 | 🟢 高 |
| 文檔連結審查報告 | (中) | `docs/06-project-management/reports/documentation-link-audit-report.md` | 文檔連結檢查與修復記錄 | ✅ 最新 | 🟢 高 |
| 文檔連結審查更新 | (中) | `docs/06-project-management/reports/documentation-link-audit-update.md` | 連結修復進度更新報告 | ✅ 最新 | 🟢 高 |
| 項目繼續任務總結 | (中) | `docs/06-project-management/reports/project-continuation-summary.md` | 繼續中斷任務完成總結 | ✅ 最新 | 🟢 高 |
| 路線圖 | (中) | `planning/core-development/technical-implementation-roadmap.md` | 未來發展路線圖 | 🟢 重要 | ✅ 活躍 |
| Electron 主進程 | (英) | `docs/05-development/electron-main-process.md` | Electron 應用程式主進程 | ✅ 完整 | 🟢 高 |
| Electron 預載入腳本 | (英) | `docs/05-development/electron-preload-script.md` | Electron 應用程式預載入腳本 | ✅ 完整 | 🟢 高 |
| Electron 渲染器進程 | (英) | `docs/05-development/electron-renderer-process.md` | Electron 應用程式渲染器進程 | ✅ 完整 | 🟢 高 |
| 清理工具 | (英) | `docs/05-development/cleanup-utils.md` | 開發清理實用工具 | ✅ 完整 | 🟢 高 |
| 依賴檢查器 | (英) | `docs/05-development/dependency-checker.md` | 檢查專案依賴關係 | ✅ 完整 | 🟢 高 |
| 環境設置 | (英) | `docs/05-development/environment-setup.md` | 開發環境設置指南 | ✅ 完整 | 🟢 高 |
| 密鑰管理 | (英) | `docs/05-development/key-management.md` | 密鑰管理策略 | ✅ 完整 | 🟢 高 |
| 熱重載與排空 | (英) | `docs/05-development/hot-reload-and-drain.md` | 熱重載與連接排空機制 | ✅ 完整 | 🟢 高 |

##### 調試與故障排除文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 時效性 | 維護狀態 |
|---|---|---|---|---|---|
| 錯誤處理 | (英) | `docs/05-development/debugging/error-handling.md` | 錯誤處理指南 | ✅ 完整 | 🟢 高 |
| 錯誤處理模組 | (英) | `docs/05-development/utilities/error-handling-module.md` | 集中式錯誤管理 | 🟢 低 | 🟢 高 |
| 網絡彈性 | (英) | `docs/05-development/utilities/network-resilience.md` | 網絡彈性工具 | 🟡 中 | 🟢 高 |
| 沙盒執行器 | (英) | `docs/05-development/debugging/sandbox-executor.md` | 沙盒執行環境 | ✅ 完整 | 🟢 高 |

#### 📖 哲學與願景文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 性質 | 價值 |
|---|---|---|---|---|---|
| 哲學與願景 | (中) | `docs/00-overview/PHILOSOPHY_AND_VISION.md` | 專案哲學理念 | 🔮 概念 | 🟢 高 |

#### 📚 歷史與歸檔文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 狀態 | 保存價值 |
|---|---|---|---|---|---|
| 歷史專案摘要 | (中) | `docs/09-archive/legacy-project-summary.md` | 歷史專案記錄 | 🗂️ 歸檔 | 🟡 中 |
| 歸檔說明 | (中) | `docs/09-archive/README.md` | 歸檔文檔說明 | 🗂️ 歸檔 | 🟢 高 |
| 文檔重組計畫 | (中) | `docs/DOCUMENTATION_REORGANIZATION_PLAN.md` | 記錄文檔重組的歷史計畫 | 🗂️ 歸檔 | 🟡 中 |
| 舊版文檔 | (混合) | `docs/09-archive/old_docs/` | 2025年7月前未重組的舊文檔 | 🗂️ 歸檔 | 🟡 中 |


---

## 🎯 按使用場景的文檔導航

### 🚀 新用戶入門路徑 (推薦順序)
1. **專案概述 (英)** → `Unified-AI-Project/docs/README.md`
2. **協作指南 (中)** → `Unified-AI-Project/docs/PROJECTS_COLLABORATION_GUIDE_Version2.md`
3. **術語表 (中)** → `docs/00-overview/GLOSSARY.md`
4. **文檔索引 (中)** → `docs/00-overview/README.md`

### 👨‍💻 開發者技術路徑
1. **架構概述 (英)** → `docs/03-technical-architecture/README.md`
2. **核心服務 (英)** → `docs/03-technical-architecture/core-services/overview.md`
3. **API 文檔 (英)** → `docs/08-api-reference/README.md`
4. **HSP 快速開始 (英)** → `docs/03-technical-architecture/communication/hsp-quick-start.md`
5. **故障排除 (英)** → `docs/05-development/debugging/troubleshooting.md`

---

*本索引最後更新：2025年8月10日*
*維護者：Gemini*