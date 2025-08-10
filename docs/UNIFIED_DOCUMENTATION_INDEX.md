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
| 協作指南 | (中) | `Unified-AI-Project/PROJECTS_COLLABORATION_GUIDE_Version2.md` | 統一協作與技術指南 | ✅ 完整 |

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
| 🔴 必讀 | 專案概述 | (英) | `Unified-AI-Project/README.md` | 專案簡介與快速開始 | ✅ 完整 |
| 🔴 必讀 | 專案章程 | (中) | `Unified-AI-Project/docs/00-overview/PROJECT_CHARTER.md` | 完整架構說明與技術規範 | ✅ 完整 |
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
| 美術資源規範 | (英) | `docs/02-game-design/art-asset-specification.md` | 遊戲美術資源規格 | ✅ 完整 | 🟢 低 |

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

#### 📖 哲學與願景文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 性質 | 價值 |
|---|---|---|---|---|---|
| 哲學與願景 | (中) | `docs/00-overview/PHILOSOPHY_AND_VISION.md` | 專案哲學理念 | 🔮 概念 | 🟢 高 |

#### 📚 歷史與歸檔文檔
| 文檔名稱 | 語言 | 路徑 | 描述 | 狀態 | 保存價值 |
|---|---|---|---|---|---|
| 歷史專案摘要 | (中) | `docs/09-archive/legacy-project-summary.md` | 歷史專案記錄 | 🗂️ 歸檔 | 🟡 中 |
| 歸檔說明 | (中) | `docs/09-archive/README.md` | 歸檔文檔說明 | 🗂️ 歸檔 | 🟢 高 |
| 舊版文檔 | (混合) | `docs/09-archive/old_docs/` | 2025年7月前未重組的舊文檔 | 🗂️ 歸檔 | 🟡 中 |



---

## 🎯 按使用場景的文檔導航

### 🚀 新用戶入門路徑 (推薦順序)
1. **專案概述 (英)** → `Unified-AI-Project/README.md`
2. **協作指南 (中)** → `Unified-AI-Project/PROJECTS_COLLABORATION_GUIDE_Version2.md`
3. **術語表 (中)** → `docs/00-overview/GLOSSARY.md`
4. **專案章程 (中)** → `docs/00-overview/PROJECT_CHARTER.md`
5. **文檔索引 (中)** → `docs/00-overview/README.md`

### 👨‍💻 開發者技術路徑
1. **架構概述 (英)** → `docs/03-technical-architecture/README.md`
2. **核心服務 (英)** → `docs/03-technical-architecture/core-services/overview.md`
3. **API 文檔 (英)** → `docs/08-api-reference/README.md`
4. **HSP 快速開始 (英)** → `docs/03-technical-architecture/communication/hsp-quick-start.md`
5. **故障排除 (英)** → `docs/05-development/debugging/troubleshooting.md`

---

*本索引最後更新：2025年8月10日*
*維護者：Gemini*