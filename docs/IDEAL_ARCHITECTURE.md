# Angela AI — 理想架構規範（Target Architecture）

**版本**: 1.0.0  
**最後更新**: 2026-06-25 (v2 — §2.2/§4.4 實際狀態同步; creation/optimization/tools 已移除)  
**狀態**: Target / Blueprint  
**目的**: 定義 Unified AI Project 應有的理想狀態 — 完整、全面、細節、細緻的架構規範

---

## 目錄

1. [核心原則](#1-核心原則)
2. [目錄結構](#2-目錄結構)
3. [架構層次](#3-架構層次)
4. [路由設計標準](#4-路由設計標準)
5. [AI 子系統設計](#5-ai-子系統設計)
6. [核心子系統設計](#6-核心子系統設計)
7. [服務層設計](#7-服務層設計)
8. [前端架構](#8-前端架構)
9. [配置標準](#9-配置標準)
10. [測試標準](#10-測試標準)
11. [文檔標準](#11-文檔標準)
12. [版本治理](#12-版本治理)
13. [管線設計](#13-管線設計)
14. [Stub 管理政策](#14-stub-管理政策)
15. [程式碼品質標準](#15-程式碼品質標準)
16. [CI/CD 標準](#16-cicd-標準)

---

## 1. 核心原則

### 1.1 架構原則

| 原則 | 說明 | 強制程度 |
|------|------|---------|
| **單一職責** | 每個模組/類別/函數只做一件事 | 🔴 強制 |
| **依賴反轉** | 高層模組不依賴低層模組，都依賴抽象 | 🔴 強制 |
| **明確優於隱含** | 顯式 import、顯式錯誤處理、顯式配置 | 🔴 強制 |
| **一致命名** | 相同概念使用相同命名規則 | 🔴 強制 |
| **最小依賴** | 避免不必要的依賴和包裝層 | 🟡 建議 |
| **文檔即真實** | 文檔必須與程式碼相符 | 🔴 強制 |
| **測試即規範** | 測試應作為行為規範文件 | 🔴 強制 |
| **無死代碼** | 沒有被使用的程式碼應被刪除 | 🔴 強制 |

### 1.2 命名規範

| 類別 | 規則 | 範例 |
|------|------|------|
| Python 套件 | `snake_case` | `ai/memory/ham_memory/` |
| Python 模組 | `snake_case.py` | `query_classifier.py` |
| Python 類別 | `PascalCase` | `QueryClassifier` |
| Python 函數 | `snake_case` | `classify_query()` |
| API 路由 | `/api/v1/{domain}/{action}` | `/api/v1/chat/send` |
| 配置鍵 | `snake_case` | `max_message_length` |
| JS 檔案 | `kebab-case.js` | `live2d-manager.js` |
| JS 類別 | `PascalCase` | `Live2DManager` |
| JS 函數 | `camelCase` | `loadModel()` |
| 目錄 | `kebab-case` | `ham-memory/` |

### 1.3 設計模式偏好

| 情境 | 模式 | 說明 |
|------|------|------|
| 服務建立 | Singleton + Factory | 由 lifespan 統一管理 |
| 路由依賴 | FastAPI Depends | 透過 lifespan 的 lazy factories |
| AI 引擎 | Strategy | 統一介面，多種實作 |
| 事件處理 | Pub/Sub | Plugin 系統、WebSocket 推送 |
| 錯誤處理 | 自訂 Exception Hierarchy | 繼承自 `AngelaError` |
| 配置載入 | Adapter + Overlay | YAML 3-tier merge |

---

## 2. 目錄結構

### 2.1 理想目錄樹

```
unified-ai-project/
├── apps/
│   ├── backend/                 # Python FastAPI 後端
│   │   ├── src/
│   │   │   ├── main.py          # FastAPI 應用入口（薄層）
│   │   │   ├── api/
│   │   │   │   ├── lifespan.py  # 生命週期管理
│   │   │   │   ├── router.py    # 統一路由註冊
│   │   │   │   ├── middleware.py# 中介軟體
│   │   │   │   ├── routes/
│   │   │   │   │   ├── chat.py          # 聊天端點
│   │   │   │   │   ├── desktop.py       # 桌面互動
│   │   │   │   │   ├── multimodal.py    # 多模態
│   │   │   │   │   ├── image_gen.py     # 圖像生成
│   │   │   │   │   ├── meta.py          # 元認知
│   │   │   │   │   ├── ops.py           # 運維
│   │   │   │   │   └── state.py         # 狀態矩陣
│   │   │   │   └── v1/endpoints/        # (v1 保留相容)
│   │   │   ├── core/
│   │   │   │   ├── engine/       # 核心引擎
│   │   │   │   │   ├── state_matrix.py
│   │   │   │   │   ├── action_executor.py
│   │   │   │   │   └── desktop_interaction.py
│   │   │   │   ├── life/         # 生命系統
│   │   │   │   │   ├── digital_life_integrator.py
│   │   │   │   │   ├── tickle_reflex_system.py
│   │   │   │   │   └── heartbeat.py
│   │   │   │   ├── bio/          # 生物系統
│   │   │   │   │   ├── biological_integrator.py
│   │   │   │   │   ├── emotional_blending.py
│   │   │   │   │   └── neuroplasticity_core.py
│   │   │   │   ├── hsp/          # HSP 協定
│   │   │   │   ├── security/     # 安全（真實實作）
│   │   │   │   ├── config/       # 配置管理
│   │   │   │   ├── plugin/       # 插件系統
│   │   │   │   └── i18n/         # 國際化
│   │   │   ├── ai/               # AI 系統
│   │   │   │   ├── core/         # 核心分類/路由
│   │   │   │   │   ├── query_classifier.py
│   │   │   │   │   ├── execution_gate.py
│   │   │   │   │   ├── model_bus.py
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── ed3n/         # ED3N 引擎
│   │   │   │   ├── garden/       # GARDEN 引擎
│   │   │   │   ├── memory/       # 記憶系統
│   │   │   │   │   ├── ham_memory/ # HAM 記憶
│   │   │   │   │   └── vector_store/ # 向量存儲
│   │   │   │   ├── agents/       # 代理系統
│   │   │   │   ├── multimodal/   # 多模態
│   │   │   │   │   ├── primitives/ # 圖像生成原語
│   │   │   │   │   └── three_layer_visual.py
│   │   │   │   ├── reasoning/    # 推理引擎
│   │   │   │   ├── response/     # 響應組合
│   │   │   │   └── alignment/    # 對齊系統
│   │   │   ├── services/         # 應用服務
│   │   │   │   ├── chat_service.py
│   │   │   │   ├── llm/          # LLM 供應商
│   │   │   │   ├── handlers/     # 意圖處理器
│   │   │   │   ├── multimodal_service.py
│   │   │   │   ├── vision_service.py
│   │   │   │   ├── audio_service.py
│   │   │   │   └── weather_service.py
│   │   │   └── shared/          # 共用工具
│   │   ├── configs/              # 後端配置
│   │   ├── models/               # 訓練模型
│   │   └── tests/                # 後端測試
│   ├── desktop-app/              # Electron 桌面應用
│   │   ├── electron_app/
│   │   │   ├── main.js           # 主程序（薄層）
│   │   │   ├── preload.js        # 預加載
│   │   │   ├── index.html
│   │   │   └── js/
│   │   │       ├── app.js        # 應用邏輯
│   │   │       ├── live2d/       # Live2D 專用
│   │   │       ├── ui/           # UI 元件
│   │   │       ├── services/     # 服務通訊
│   │   │       └── utils/        # 工具函數
│   │   ├── shared/               # 與 web-viewer 共用
│   │   └── package.json
│   ├── web-live2d-viewer/        # Web Live2D 預覽（輕量）
│   │   ├── index.html
│   │   ├── js/
│   │   └── assets/
│   ├── pixel-angela/             # PyQt6 像素引擎
│   └── gemini-os-bridge/         # 作業系統橋接
├── packages/                     # 共用套件
│   ├── shared-js/                # JS 共用程式庫
│   │   ├── src/
│   │   │   ├── live2d/           # Live2D 包裝
│   │   │   ├── state-matrix/     # 狀態矩陣
│   │   │   ├── i18n/             # 國際化
│   │   │   └── websocket/        # WebSocket 客戶端
│   │   └── package.json
│   ├── cli/                      # CLI 工具
│   └── biology-core/             # 生物核心
├── configs/                      # 全專案配置
├── docs/                         # 文檔
│   ├── 00-overview/
│   ├── 03-technical-architecture/
│   ├── 05-development/
│   ├── 06-project-management/
│   └── 09-archive/
├── scripts/                      # 腳本
├── tests/                        # 測試
└── data/                         # Runtime 資料（非版本控制）
    ├── vector_store/
    ├── context_storage/
    └── logs/
```

### 2.2 應該存在的目錄 vs 不該存在的目錄

| 目錄 | 理想狀態 | 實際狀態 | 說明 |
|------|---------|:--------:|------|
| `apps/backend/src/ai/core/__init__.py` | ✅ **應存在** | ✅ 存在 | 讓 `ai.core` 成為 namespace package |
| `apps/backend/src/modules/` | ❌ **不應存在** | ✅ 已移除 (Phase 1) | 包裝器層無增值 |
| `apps/backend/src/monitoring/` | ❌ **不應存在** | ⚠️ 仍存在 | `system_monitor.py` (252行) 監控系統資源（CPU/GPU/記憶體/磁碟/網路），與 `core/monitoring/enterprise_monitor.py` (指標告警框架) 不同職責。有測試依賴，待合併至 `core/monitoring/` |
| `apps/backend/src/optimization/` | ❌ **不應存在** | ✅ 已移除 (2026-06-25) | `performance_optimizer.py` (300行)，0 生產代碼/測試引用。測試引用已刪除的 `ai.ops.performance_optimizer` |
| `apps/backend/src/creation/` | ❌ **不應存在** | ✅ 已移除 (2026-06-25) | `creation_engine.py` (95行)，0 引用，完全死代碼 |
| `apps/backend/src/search/` | ❌ **不應存在** | ✅ 已移除 (2026-06-25) | 16 行 stub，無生產代碼引用 |
| `apps/backend/src/tools/` | ❌ **不應存在** | ✅ 已移除 (2026-06-25) | `file_system_tool.py` (57行)，0 引用，完全死代碼 |
| `apps/mobile-app/` | ❌ **已不存在** | skeleton 已被刪除 |
| `context_storage/` (根目錄) | ❌ **不應在根目錄** | 應在 `data/context_storage/` |
| `packages/shared-js/` | ✅ **應新增** | 共用 JS 程式庫 |

### 2.3 已刪除的 AI 子模組 — 最終決定

| 目錄 | 審計發現 | 理想決定 | 理由 |
|------|---------|---------|------|
| `ai/learning/` | Phase 11 刪除 | ❌ **不恢復** — 功能已移至 ED3N | ED3N ContinuousLearningPipeline 已涵蓋 |
| `ai/ops/` | Phase 11 刪除 | ❌ **不恢復** — 功能已分散 | `core/managers/`、`core/monitoring/` |
| `ai/lis/` | Phase 11 刪除 | ❌ **不恢復** — 冗餘 | 被 `core/life/` 取代 |
| `ai/compression/` | Phase 11 刪除 | ❌ **不恢復** — alpha_deep_model 應重建於 `core/` | `ai/` 不合適 |
| `ai/evaluation/` | Phase 11 刪除 | ❌ **不恢復** — 功能在 `core/managers/` |
| `ai/symbolic_space/` | Phase 11 刪除 | ❌ **不恢復** — 功能冗餘 |
| `ai/trust/` | Phase 12b 刪除 | ❌ **不恢復** — 功能在 `security/` |
| `ai/world_model/` | Phase 9 刪除 | ❌ **不恢復** — 原本就是 stub |
| `ai/security/` | chore 刪除 | ❌ **不恢復** — 功能在 `core/security/` |
| `ai/token/` | Phase 9 刪除 | ❌ **不恢復** — 原本就是 stub |
| `ai/distributed/` | 移除 | ❌ **不恢復** — 無需求 |
| `ai/dialogue/` | Phase 11 刪除 | ❌ **不恢復** | 功能已移至 `services/chat_service.py` |
| `ai/execution/` | Phase 11 刪除 | ❌ **不恢復** | 功能在 `core/engine/action_executor.py` |
| `ai/code_inspection/` | Phase 11 刪除 | ❌ **不恢復** | 功能在 `core/tools/` |
| `ai/language_models/` | Phase 11 刪除 | ❌ **不恢復** | 功能在 `services/llm/` |
| `ai/integration/` | Phase 11 刪除 | ❌ **不恢復** | 功能分散在各處 |
| `ai/formula_engine/` | Phase 9 刪除 | ❌ **不恢復** | 原本就是 stub |
| `ai/rag/` | Phase 9 刪除 | ❌ **不恢復** | 無需求 |
| `ai/service_discovery/` | Phase 9 刪除 | ❌ **不恢復** | 原本就是 stub |
| `ai/deep_mapper/` | Fix 刪除 | ❌ **不恢復** | 無需求 |

---

## 3. 架構層次

### 3.1 6 層架構（更新版）

```
┌──────────────────────────────────────────────────────────────────┐
│  L6 — PRESENTATION LAYER                                         │
│  Desktop App (Electron) │ Web Viewer │ Pixel Angela │ CLI        │
│  透過 HTTP/REST + WebSocket 與 L5 通訊                           │
├──────────────────────────────────────────────────────────────────┤
│  L5 — API / TRANSPORT LAYER                                      │
│  FastAPI (main.py → lifespan.py → router.py)                     │
│  Routes: /api/v1/{domain}/{action}                               │
│  WebSocket: /ws (session-managed)                                │
│  Middleware: CORS → Auth → Logging                                │
│  Session: SessionManager (全局 singleton，from connection_session)│
├──────────────────────────────────────────────────────────────────┤
│  L4 — APPLICATION SERVICE LAYER                                  │
│  ChatService │ LLMService │ VisionService │ AudioService          │
│  MultimodalService │ WeatherService │ BrainBridgeService          │
│  Handlers (file_operation, task_manager, system_command, ...)     │
│  Lifecycle: 由 lifespan.py 統一初始化/關閉                       │
├──────────────────────────────────────────────────────────────────┤
│  L3 — CORE INFRASTRUCTURE LAYER                                  │
│  StateMatrix4D │ ActionExecutor │ DesktopInteraction              │
│  HAM Memory │ DigitalLifeIntegrator │ HSP Protocol                │
│  Security (auth, encryption, audit) │ ConfigLoader                │
│  Plugin System │ i18n Manager │ Bio Systems                       │
├──────────────────────────────────────────────────────────────────┤
│  L2 — AI ENGINE LAYER                                            │
│  ED3N (reflex → encode → SNN → decode → verify → cycle)         │
│  GARDEN (vector dict → SNN core → inference → multistep)         │
│  QueryClassifier │ ExecutionGate │ ModelBus                       │
│  Multimodal (GVV pipeline, ThreeLayerVisual)                     │
│  ResponseComposer │ TemplateMatcher │ DeviationTracker            │
│  Agents (AgentManager, BaseAgent, specialized agents)             │
├──────────────────────────────────────────────────────────────────┤
│  L1 — THEORETICAL FOUNDATION                                     │
│  HSM Formula │ CDM Dividend │ Life Intensity                     │
│  Active Cognition │ Non-Paradox Existence                         │
│  Maturity L0-L11 │ Angela DNA (voxel skeleton)                   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 依賴方向

```
L6 (Presentation) → L5 (API) → L4 (Services) → L3 (Core) → L2 (AI) → L1 (Theory)
                                                      │              │
                                                      └── 不可反向依賴 ──┘
```

**強制規則**:
- L6 只能依賴 L5
- L5 只能依賴 L4
- L4 只能依賴 L3 + L2
- L3 不能依賴 L4/L5/L6
- L2 不能依賴 L4/L5/L6
- 禁止循環依賴（如 A→B→A）

### 3.3 模組間通訊規則

| 通訊方式 | 使用場景 | 範例 |
|---------|---------|------|
| **直接函數調用** | 同層級模組 | `StateMatrix4D.update_dimension()` |
| **依賴注入** | 跨層級工廠 | `lifespan.py` 提供 `get_digital_life()` |
| **事件/Plugin** | 橫切關注點 | `plugin_manager.emit("on_message", msg)` |
| **WebSocket Pub/Sub** | 即時推送 | `websocket_manager.broadcast(state_update)` |
| **HSP 協定** | 外部系統整合 | `HSPConnector.send()` |

---

## 4. 路由設計標準

### 4.1 路由命名規範

**格式**: `/{version}/{domain}/{resource}[/{action}]`

| 域 (Domain) | 路由前綴 | 範例 |
|------------|---------|------|
| Chat | `/api/v1/chat` | `POST /api/v1/chat/send` |
| Desktop | `/api/v1/desktop` | `GET /api/v1/desktop/state` |
| Multimodal | `/api/v1/multimodal` | `POST /api/v1/multimodal/encode` |
| Image Gen | `/api/v1/image` | `POST /api/v1/image/generate` |
| Meta | `/api/v1/meta` | `GET /api/v1/meta/confidence/summary` |
| Ops | `/api/v1/ops` | `GET /api/v1/ops/health` |
| State | `/api/v1/state` | `GET /api/v1/state/summary` |

### 4.2 端點命名規則

| HTTP 方法 | 動作 | 範例 |
|----------|------|------|
| `GET` | 讀取資源 | `GET /api/v1/chat/sessions/{id}` |
| `POST` | 建立資源/動作 | `POST /api/v1/chat/send` |
| `PUT` | 完整更新 | `PUT /api/v1/state/axis/{name}` |
| `PATCH` | 部分更新 | `PATCH /api/v1/chat/sessions/{id}` |
| `DELETE` | 刪除 | `DELETE /api/v1/chat/sessions/{id}` |

### 4.3 理想路由清單

| 方法 | 路徑 | 功能 | 所屬檔案 |
|------|------|------|---------|
| `GET` | `/health` | 根級健康檢查 | `routes/ops.py` |
| `GET` | `/metrics` | Prometheus metrics | `routes/ops.py` |
| `POST` | `/api/v1/chat/send` | 發送訊息（統一入口） | `routes/chat.py` |
| `POST` | `/api/v1/chat/session/start` | 建立 Session | `routes/chat.py` |
| `POST` | `/api/v1/chat/with-image` | 圖片對話 | `routes/chat.py` |
| `POST` | `/api/v1/chat/with-audio` | 語音對話 | `routes/chat.py` |
| `GET` | `/api/v1/desktop/state` | 桌面狀態 | `routes/desktop.py` |
| `POST` | `/api/v1/desktop/organize` | 整理桌面 | `routes/desktop.py` |
| `POST` | `/api/v1/desktop/cleanup` | 清理桌面 | `routes/desktop.py` |
| `GET` | `/api/v1/image/status` | 圖像生成狀態 | `routes/image_gen.py` |
| `POST` | `/api/v1/image/generate` | 從文字產生圖像 | `routes/image_gen.py` |
| `POST` | `/api/v1/image/recognize` | 圖像辨識 | `routes/image_gen.py` |
| `POST` | `/api/v1/image/reconstruct` | 圖像重建 | `routes/image_gen.py` |
| `POST` | `/api/v1/image/interpolate` | 類別插值 | `routes/image_gen.py` |
| `POST` | `/api/v1/multimodal/encode` | 編碼 | `routes/multimodal.py` |
| `POST` | `/api/v1/multimodal/decode` | 解碼 | `routes/multimodal.py` |
| `POST` | `/api/v1/multimodal/compare` | 比較 | `routes/multimodal.py` |
| `POST` | `/api/v1/multimodal/train` | 訓練 | `routes/multimodal.py` |
| `GET` | `/api/v1/multimodal/health` | 多模態健康 | `routes/multimodal.py` |
| `GET` | `/api/v1/meta/confidence/summary` | 信心摘要 | `routes/meta.py` |
| `GET` | `/api/v1/ops/health` | 運維健康 | `routes/ops.py` |
| `GET` | `/api/v1/ops/status` | 運維狀態 | `routes/ops.py` |
| `POST` | `/api/v1/ops/maintenance` | 維護觸發 | `routes/ops.py` |
| `GET` | `/api/v1/state/summary` | 狀態矩陣摘要 | `routes/state.py` |
| `GET` | `/api/v1/state/axis/{name}` | 單軸狀態 | `routes/state.py` |
| `POST` | `/api/v1/state/axis/{name}/update` | 更新軸值 | `routes/state.py` |

### 4.4 棄用路由（不應存在 — 但仍有實際代碼）

以下路由存在於實際代碼中，但已加上 `DeprecationWarning`。最終目標是移除。

| 當前路由 | 實際狀態 | 應改為 | 理由 |
|---------|:--------:|-------|------|
| `POST /api/v1/angela/chat` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/chat/send` | 與 `/dialogue` 重複 |
| `POST /api/v1/dialogue` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/chat/send` | 與 `/angela/chat` 重複 |
| `POST /api/v1/generate-image` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/image/generate` | 命名不一致 |
| `POST /api/v1/reconstruct-image` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/image/reconstruct` | 同上 |
| `POST /api/v1/recognize-image` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/image/recognize` | 同上 |
| `POST /api/v1/interpolate-classes` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/image/interpolate` | 同上 |
| `POST /api/v1/vision/analyze` | ⚠️ 存在 (有 DeprecationWarning) | `POST /api/v1/multimodal/encode` | 與 `/chat/with-image` 重疊 |
| `GET /generate-image/status` | ⚠️ 存在 (有 DeprecationWarning) | `GET /api/v1/image/status` | 命名不一致 |

---

## 5. AI 子系統設計

### 5.1 理想 AI 目錄結構

```
apps/backend/src/ai/
├── __init__.py              # 套件匯出
├── types.py                 # 共用型別 (AgentStatus, RegisteredAgent...)
├── core/                    # 核心分類/路由/執行
│   ├── __init__.py          # ✅ 必須存在
│   ├── query_classifier.py  # QueryClassifier v2
│   ├── execution_gate.py    # ExecutionGate
│   ├── model_bus.py         # ModelBus
│   └── unicode_utils.py     # 工具
├── ed3n/                    # ED3N 引擎
│   ├── ed3n_engine.py       # 主引擎
│   ├── continuous_learning.py # 持續學習
│   ├── dictionary_layer.py  # 字典層
│   ├── reflex_layer.py      # 反射層
│   ├── core_network.py      # SNN 核心網路
│   ├── step_decoder.py      # 逐步解碼器
│   └── multimodal/          # 多模態編碼
├── garden/                  # GARDEN 引擎
│   ├── garden_engine.py     # 主引擎
│   ├── vector_dictionary.py # 向量字典
│   ├── snn_core.py          # SNN 核心
│   └── config/
├── memory/                  # 記憶系統
│   ├── ham_memory/          # HAM 記憶
│   └── vector_store/        # 向量存儲
├── agents/                  # 代理系統
│   ├── agent_manager.py     # 代理管理器
│   ├── base/base_agent.py   # 基礎代理
│   └── agent_adapter.py     # 代理註冊
├── multimodal/              # 多模態 AI
│   ├── primitives/          # 圖像生成原語 (GVV)
│   ├── three_layer_visual.py # ThreeLayerVisual
│   ├── semantic_visual.py   # CLIP 編碼器
│   └── concept_library.py   # 概念庫
├── reasoning/               # 推理引擎
│   ├── causal_reasoning_engine.py # 因果推理
│   └── planning_engine.py   # 規劃引擎
├── response/                # 響應組合
│   ├── composer.py          # ResponseComposer
│   ├── template_matcher.py  # 模板匹配
│   ├── deviation_tracker.py # 偏差追蹤
│   └── learning_loop.py     # 學習循環
├── alignment/               # 對齊系統
│   ├── emotion_system.py    # 情緒系統
│   ├── ontology_system.py   # 本體系統
│   ├── reasoning_system.py  # 推理對齊
│   └── alignment_manager.py # 對齊管理器
├── crisis/                  # 危機處理
│   └── crisis_system.py
├── lifecycle/               # 生命週期
├── context/                 # 上下文管理
├── meta/                    # 元學習
├── audio/                   # 音頻處理
├── vision/                  # 視覺處理
└── ensemble.py              # ResponseFusionEngine
```

### 5.2 AI 引擎選擇邏輯（理想）

```
用戶輸入
    │
    ▼
QueryClassifier.classify(text, context)
    ├── ED3N-first: 字典關鍵字匹配
    ├── Regex fallback: 模式匹配
    └── CRISIS check: 安全篩查
    │
    ▼
ExecutionGate.decide(query_type, confidence, context)
    ├── auto_execute: 90%+ 信心
    ├── confirm: 70-90%
    └── reject: <70%
    │
    ▼
ModelBus.route(query_type, context)
    ├── ED3N (reflex): 簡單問候、反射
    ├── GARDEN (fast): 輕量推理
    ├── LLM (cloud): 複雜對話
    └── Hybrid (local→cloud refine): 高質量需求
    │
    ▼
Cycling Processing (信心迭代)
    ├── Output → Quality Check → < threshold → Refine
    └── max 3 iterations
    │
    ▼
ResponseComposer.compose(llm_output, state, context)
    │
    ▼
Fire-and-forget 學習
    ├── ED3N.continuous_learning.learn()
    ├── MemoryManager.store()
    └── CausalReasoning.learn()
```

---

## 6. 核心子系統設計

### 6.1 Core 目錄（理想）

```
apps/backend/src/core/
├── engine/           # ✅ 保留 — 核心引擎
│   ├── state_matrix.py
│   ├── action_executor.py
│   └── desktop_interaction.py
├── bio/              # ✅ 保留 — 生物系統
├── life/             # ✅ 保留 — 生命系統
├── hsp/              # ✅ 保留 — HSP 協定
├── security/         # ✅ 保留 — 安全（需移除 stub）
│   ├── auth_middleware.py
│   ├── encryption.py
│   ├── key_generator.py  # ❌ 需實作
│   ├── key_validator.py
│   ├── secure_eval.py    # ❌ 需實作或移除
│   └── security_audit.py
├── config/           # ✅ 保留 — 配置
├── plugin/           # ✅ 保留 — 插件
├── i18n/             # ✅ 保留 — 國際化
├── managers/         # ✅ 保留 — 管理器
├── monitoring/       # ✅ 保留 — 監控
├── system/           # ✅ 保留 — 系統
├── state/            # ✅ 保留 — 狀態管理
├── perception/       # ✅ 保留 — 感知
├── tools/            # ✅ 保留 — 工具
├── card/             # ✅ 保留 — 卡片系統
│   └── resolver/pipeline_orchestrator.py # 管線
├── economy/          # ✅ 保留 — 經濟
├── art/              # ✅ 保留 — 藝術
├── autonomous/       # ✅ 保留 — 自主別名（7 shims）
├── tracing/          # ✅ 保留 — 追蹤
├── error/            # ✅ 保留 — 錯誤處理
├── api/              # ✅ 保留 — API 版本化
├── knowledge/        # ✅ 保留 — 知識圖譜
├── interfaces/       # ✅ 保留 — 介面定義
├── maturity/         # ✅ 保留 — 成熟度
├── metamorphosis/    # ✅ 保留 — 蛻變
├── precision/        # ✅ 保留 — 精度
├── ripple/           # ✅ 保留 — 漣漪效應
├── sync/             # ✅ 保留 — 同步
├── identity/         # ✅ 保留 — 身份
├── influence/        # ✅ 保留 — 影響力
├── services/         # ✅ 保留 — 服務
├── allocation/       # ✅ 保留 — 資源分配
├── logging/          # ✅ 保留 — 日誌
├── hardware/         # ✅ 保留 — 硬體
├── evolution/        # ✅ 保留 — 演化
└── tests/            # ✅ 保留 — 測試
```

### 6.2 StateMatrix4D 理想實作

```python
# 所有方法應直接實作，不依賴 hasattr fallback
class StateMatrix4D:
    # 已實作 ✅
    def update_alpha(self, **values)
    def update_beta(self, **values)
    def update_gamma(self, **values)
    def update_delta(self, **values)
    def update_epsilon(self, **values)
    def update_theta(self, **values)
    def compute_influences()
    def apply_epsilon_influence()
    
    # 需實作 ❌ (目前回傳 "not_implemented")
    def register_port(self, name: str, config: dict)
    def unregister_port(self, name: str)
    def apply_ripple(self, source_axis, source_value, target_axes, strength)
    def allocation_decide(self, candidates, dimension)
    
    # 需確認是否存在
    def save_state(self, filepath)
    def load_state(self, filepath)
    temporal.trend(axis, key, window)
    temporal.anomalies(axis, key, threshold)
```

---

## 7. 服務層設計

### 7.1 服務架構（理想）

```
apps/backend/src/services/
├── __init__.py
├── chat_service.py              # 聊天服務（統一）
├── llm/                         # LLM 供應商
│   ├── router.py                # 路由選擇
│   ├── prompt_builder.py        # 提示建構
│   └── providers/               # 8 個供應商
├── handlers/                    # 意圖處理器
│   ├── file_operation_handler.py    # ✅ 保留
│   ├── task_manager_handler.py      # ✅ 保留
│   ├── system_command_handler.py    # ✅ 保留
│   ├── code_execution_handler.py    # ✅ 保留
│   ├── vision_handler.py            # ✅ 保留
│   ├── web_search_handler.py        # ✅ 保留
│   ├── learning_handler.py          # ✅ 保留
│   └── google_drive_handler.py      # ❌ 需實作（目前 stub）
├── multimodal_service.py        # 多模態服務
├── vision_service.py            # 視覺服務
├── audio_service.py             # 音頻服務
├── weather_service.py           # 天氣服務
├── websocket_manager.py         # WebSocket 管理
├── connection_session.py        # Session 管理（✅ 完整，需整合）
├── brain_bridge_service.py      # 大腦橋接
├── cross_modal_router.py        # 跨模態路由
├── cross_modal_quality.py       # 跨模態品質
├── math_verifier.py             # ❌ 需實作（目前 stub）
├── hot_reload_service.py        # 熱重載
├── resource_awareness_service.py # ✅ 保留（修復 __main__ bug）
├── api/                         # API 路由
│   └── state_matrix_api.py      # 狀態矩陣 API（❌ 需實作 not_implemented）
├── node_services/               # Node.js 服務
│   └── server.js                # ❌ 目前 placeholder
└── adapters/                    # 空目錄
    └── ❌ 不存在，無增值則不移除
```

### 7.2 處理器（Handlers）理想標準

```python
class BaseHandler(ABC):
    """所有處理器的基礎類別"""
    
    @abstractmethod
    async def handle(self, intent: str, params: dict) -> dict:
        """處理意圖並返回結果"""
        ...

# 每個 Handler 必須:
# 1. 有對應的單元測試
# 2. 使用 i18n 處理用戶面向文字
# 3. 有完整的錯誤處理
# 4. 回傳一致的 response 格式
```

---

## 8. 前端架構

### 8.1 JS 程式庫共用化

當前問題：desktop-app 和 web-live2d-viewer 有 ~30 個重複 JS 檔案。

**理想方案**：

```
packages/shared-js/
├── src/
│   ├── live2d/
│   │   ├── live2d-cubism-wrapper.js    # Live2D 包裝
│   │   ├── live2d-manager.js           # Live2D 管理器
│   │   └── simple-live2d-loader.js     # 簡易載入器
│   ├── state/
│   │   ├── state-matrix.js             # 狀態矩陣
│   │   └── unified-display-matrix.js   # 顯示矩陣
│   ├── i18n/
│   │   └── i18n.js                     # 國際化
│   ├── services/
│   │   ├── backend-websocket.js        # WebSocket 客戶端
│   │   └── api-client.js               # API 客戶端
│   └── ui/
│       ├── dialogue-ui.js              # 對話 UI
│       └── character-touch-detector.js # 觸碰偵測
├── package.json
└── dist/
```

### 8.2 Desktop App 應保留

- 38 個 JS 檔案太多 → 應簡化為使用共用套件
- 音頻/觸覺 placeholder → 實現或移除
- WebSocket 衝突 → 統一管理方式
- 空 catch 區塊 → 加載日誌

### 8.3 web-live2d-viewer 應輕量化

- 使用 `packages/shared-js` 取代重複 JS
- 只保留 web-specific 的 UI 邏輯

---

## 9. 配置標準

### 9.1 配置層級

```
Layer 1: configs/angela_config.json     # 預設配置（版本控制）
Layer 2: configs/angela_config.yaml     # 用戶配置（版本控制）
Layer 3: .env                           # 敏感配置（非版本控制）
Layer 4: 環境變數                        # Runtime 覆蓋
```

### 9.2 配置欄位標準

| 欄位 | 類型 | 預設值 | 必填 | 說明 |
|------|------|--------|------|------|
| `app.name` | string | "Angela AI" | ✅ | 應用名稱 |
| `app.version` | string | "7.5.0-dev" | ✅ | 版本（與 VERSION 同步） |
| `backend.host` | string | "127.0.0.1" | ✅ | 後端主機 |
| `backend.port` | int | 8000 | ✅ | 後端埠號 |
| `features.voice_recognition` | bool | false | ✅ | 語音辨識（預設關閉） |
| `features.text_to_speech` | bool | false | ✅ | 文字轉語音（預設關閉） |
| `features.mobile_bridge` | bool | false | ✅ | 手機橋接（預設關閉—實際不存在） |
| `security.session_timeout` | int | 3600 | ✅ | Session 逾時 |
| `logging.level` | string | "INFO" | ✅ | 日誌級別 |
| `testing.test_mode` | bool | false | ✅ | 測試模式（**必須預設關閉**） |
| `development.debug_mode` | bool | false | ✅ | 除錯模式（**必須預設關閉**） |

### 9.3 禁止的預設值

| 配置 | 當前值 | 理想值 | 理由 |
|------|--------|--------|------|
| `test_mode` | `true` | `false` | 生產環境不應預設測試模式 |
| `debug_mode` | `true` | `false` | 生產環境不應預設施錯模式 |
| `mobile_bridge` | `true` | `false` | 實際不存在此功能 |

---

## 10. 測試標準

### 10.1 測試層級

```
Level 1 — Unit Tests (tests/unit/)
  ├── 測試單一類別/函數
  ├── 無外部依賴（mock）
  └── 執行時間 < 100ms/測試

Level 2 — Integration Tests (tests/ai/, tests/core/, tests/services/)
  ├── 測試多個模組互動
  ├── 可使用真實依賴或輕量 mock
  └── 執行時間 < 1s/測試

Level 3 — API Tests (tests/api/)
  ├── 測試 HTTP 端點
  ├── 使用 TestClient
  └── 執行時間 < 3s/測試

Level 4 — E2E Tests (tests/e2e/)
  ├── 測試完整使用者流程
  ├── 使用真實後端實例
  └── 執行時間 < 30s/測試
```

### 10.2 測試覆蓋目標

| 模組類別 | 覆蓋率目標 | 當前估計 |
|---------|-----------|---------|
| Core 引擎 | >90% | ~80% |
| AI 引擎 (ED3N, GARDEN) | >85% | ~70% |
| Services | >80% | ~50% |
| API Routes | >90% | ~60% |
| Handlers | >80% | ~10% (幾乎無測試) |
| LLM Providers | >90% | ~80% |

### 10.3 測試禁令

| 禁止 | 替代方案 | 理由 |
|------|---------|------|
| `pytest.skip()` 因 stub module | 實作 module 或移除測試 | 測試不應永久跳過 |
| `except ImportError: pytest.skip()` | 修復 import 路徑 | 掩蓋真實問題 |
| `assert True` 佔位符 | 移除測試 | 無意義 |
| `pass` 測試方法 | 移除測試 | 無意義 |
| Mock 整個外部服務 | 使用真實服務或 lightweight fake | 過度 mock 降低信心 |

---

## 11. 文檔標準

### 11.1 文件分類

| 類別 | 位置 | 維護頻率 |
|------|------|---------|
| 開發指南 | `AGENTS.md` | 每次結構變更 |
| 架構概覽 | `docs/ARCHITECTURE.md` | 每次架構變更 |
| 文件索引 | `docs/INDEX.md` | 每新增/刪除文件 |
| 模組文檔 | `*/README.md` | 每次模組變更 |
| 審計報告 | `docs/COMPREHENSIVE_AUDIT_*.md` | 每月或重大變更後 |
| 計畫 | `docs/06-project-management/` | 執行期間持續更新 |
| CHANGELOG | `CHANGELOG.md` | 每次提交功能變更 |
| 用戶指南 | `README.md`, `QUICK_START.md` | 每次釋出版本 |

### 11.2 文檔必須反映現實

| 檢查項 | 頻率 | 方法 |
|--------|------|------|
| 目錄結構 | 每次提交 | glob 比對文檔宣稱的檔案 |
| 檔案數量 | 每次提交 | `find . -name "*.py" | wc -l` |
| 版本號 | CI 檢查 | 14 個位置比對 |
| API 路由 | 每次路由變更 | OpenAPI schema 與文檔比對 |
| 模組狀態 | 每月 | 重新執行審計腳本 |

### 11.3 過時文檔處理

1. **標記過時**: 在文件頂部加入 `> ⚠️ OUTDATED: Last verified {date}`
2. **更新**: 修改程式碼後立即更新相關文檔
3. **封存**: 完全過時無需保留的文件移至 `docs/09-archive/`
4. **刪除**: 確定永遠不需要的刪除（如 `PHASE1_IMPLEMENTATION_COMPLETE.txt`）

---

## 12. 版本治理

### 12.1 16 個版本位置（已驗證）

| # | 位置 | 當前版本 | 檢查方法 |
|---|------|---------|---------|
| 1 | `VERSION` | 7.5.0-dev | `cat VERSION` |
| 2 | `package.json` | 7.5.0-dev | `jq .version` |
| 3 | `apps/backend/pyproject.toml` | 7.5.0-dev | `grep 'version ='` |
| 4 | `configs/angela_config.json` | 7.5.0-dev | `jq .version` |
| 5 | `apps/backend/package.json` | 7.5.0-dev | `jq .version` |
| 6 | `apps/desktop-app/package.json` | 7.5.0-dev | `jq .version` |
| 7 | `apps/desktop-app/electron_app/package.json` | 7.5.0-dev | `jq .version` |
| 8 | `packages/cli/package.json` | 7.5.0-dev | `jq .version` |
| 9 | `packages/biology-core/package.json` | 7.5.0-dev | `jq .version` |
| 10 | `apps/web-dashboard/package.json` | 7.5.0-dev | `jq .version` |
| 11 | `apps/backend/src/core/version.py` | major=7, minor=5, patch=0 | 檢查版本類別 |
| 12 | `apps/backend/src/services/main_api_server.py` | 7.5.0-dev | docstring 與 FastAPI |
| 13 | `configs/angela_config.yaml` | 7.5.0-dev | `grep 'version'` |
| 14 | `AGENTS.md` | 7.5.0-dev | 檔案元資料 |
| 15 | `README.md` | 7.5.0-dev | 版本參考 |
| 16 | `.github/workflows/ci.yml` | 7.5.0-dev | EXPECTED 變數 |

### 12.2 CI 版本檢查修復（已完成）

**已修復 (2026-06-25)**:
- ✅ `scripts/create-release.sh` 不存在檔案檢查已移除
- ✅ `packages/cli/package.json` 版本比對已從 `1.1.0` 改為 `$EXPECTED`

**剩餘問題**: Python 3.14 仍在測試矩陣（建議改為 3.10 / 3.11 / 3.12）

---

## 13. 管線設計

### 13.1 聊天管線（理想）

```
用戶輸入
    │
    ▼
[1] Input Validation
    ├── 長度檢查 (< 4000 chars)
    ├── 格式檢查 (非空)
    └── 安全檢查 (內容過濾)
    │
    ▼
[2] Context Assembly
    ├── Session Context (來自 SessionManager)
    ├── Dialogue Context (跨輪次歷史)
    ├── Memory Context (來自 HAM)
    └── State Context (StateMatrix4D)
    │
    ▼
[3] Classification
    ├── MathVerifier (數學檢測)
    ├── EmotionAnalyzer (情緒分析)
    ├── CrisisSystem (安全評估)
    └── QueryClassifier (意圖分類 + 上下文感知)
    │
    ▼
[4] Execution Gate
    ├── auto_execute (高度確定)
    ├── confirm (中等確定)
    └── reject (低確定)
    │
    ▼
[5] Model Routing
    ├── ED3N (反射級: 問候、簡單關鍵字)
    ├── GARDEN (推理級: 模式匹配、分類)
    ├── LLM Cloud (複雜級: 對話、創作)
    └── Hybrid (高品質級: draft + refine)
    │
    ▼
[6] Cycling (信心迭代)
    ├── Pass 1: 初始輸出
    ├── Quality Check: 信心 > 0.7?
    ├── Pass 2: 使用 Pass 1 作為上下文重試
    └── Pass 3: 最終輸出 (max 3)
    │
    ▼
[7] Response Composition
    ├── LLM Output + State Injection
    ├── Fragment Merging (ResponseComposer)
    └── i18n Post-processing
    │
    ▼
[8] Learning (Fire-and-forget)
    ├── ED3N ContinuousLearning
    ├── GARDEN Hebbian Learning
    ├── HAM Memory Store
    ├── CausalReasoning.learn()
    └── DeviationTracker.update()
    │
    ▼
[9] Output
    ├── HTTP Response (JSON)
    └── WebSocket Push (即時)
```

### 13.2 圖像生成管線（理想）

```
文字輸入
    │
    ▼
[1] CLIP Encoding
    └── SemanticVisualEncoder.encode_text(text) → 512-dim vector
    │
    ▼
[2] Concept Mapping
    ├── ConceptSpaceMapper.encode(clip_vec) → 概念座標
    └── ConceptMapper.map_text_to_primitives(clip_vec) → 初始向量
    │
    ▼
[3] Instance Optimization
    └── InstanceOptimizer.optimize_from_text(clip_vec) → 優化參數
    │
    ▼
[4] Rendering
    ├── PrimitiveRenderer.render(instructions) → PIL Image
    └── ThreeLayerVisual (可選增強)
    │
    ▼
[5] Output
    ├── image_base64
    ├── metrics (概念、相似度、損失)
    └── metadata
```

### 13.3 多模態管線（理想）

```
輸入 (圖片/音頻)
    │
    ▼
[1] Encode
    ├── Feature Extraction → feature_vector
    └── Latent Encoding → latent_vector (item_id 關聯)
    │
    ▼
[2] Store
    ├── Register item (item_id → {latent, modality, metadata})
    └── Optional: Memory Store (HAM)
    │
    ▼
[3] Process
    ├── Decode (latent → base64)
    ├── Compare (item_a vs item_b → similarity)
    ├── Retrieve (latent query → top-k similar)
    └── Generate (cross-modal: vision→audio, audio→vision)
    │
    ▼
[4] Continuous Learning
    └── CML (Continuous Multimodal Learning) micro-training
```

---

## 14. Stub 管理政策

### 14.1 Stub 分類與處理

| 類別 | 定義 | 處理方式 |
|------|------|---------|
| **Intentional Stub** | 有明確的 TODO 計畫未來實作 | 保留，加 TODO 註解，但不得超過 1 個 release |
| **Accidental Stub** | 應實作但未實作 | 🔴 必須在 1 週內實作或移除 |
| **Deprecated Stub** | 功能已移除但包裝保留 | 🟡 應在下一版本移除 |
| **Testing Stub** | 為測試建立的 mock/fake | ✅ 可保留，但需明確標記 |
| **Dead Code** | 無任何 import 的程式碼 | 🔴 應立即刪除 |

### 14.2 當前 Stub 處理計畫

| Stub | 類別 | 處理 |
|------|------|------|
| `google_drive_handler.py` | Accidental | 實作真正的 Google Drive 操作 |
| `core/security/key_generator.py` | ✅ 已完成 (已有真實實作，移除 stub 標記) |
| `core/security/secure_eval.py` | ✅ 已確認 (AST 安全求值器，完整實作，非 stub) |
| `services/math_verifier.py` | Intentional | 保留但加明確時間表 |
| `core/waiting_scheduler.py` | ✅ 已完成 (slot-based 排程器實作) |
| `modules/tactile_service/` | ✅ 已移除（包含在 modules/ 刪除中） |
| `modules/math_verifier/` | ✅ 已移除（包含在 modules/ 刪除中） |
| `modules/` (全部 11 個) | ✅ 已移除 (Phase 1) |
| `services/node_services/server.js` | Accidental | 實作或移除 |
| `core/tools/js_tool_dispatcher/index.js` | Accidental | 實作或移除 |

---

## 15. 程式碼品質標準

### 15.1 Python 品質閘門

| 檢查項 | 工具 | 通過標準 |
|--------|------|---------|
| 語法正確性 | Python compile | 0 錯誤 |
| 格式化 | black | 無差異 |
| Import 排序 | isort | 無差異 |
| Lint | flake8 | 0 錯誤 (允許 F401 在 `__init__.py`) |
| 型別檢查 | mypy | 0 錯誤 (strict mode) |
| 測試通過率 | pytest | 100% |
| 測試覆蓋率 | pytest-cov | >80% |
| 安全掃描 | bandit | 0 HIGH 漏洞 |
| Secret 掃描 | gitleaks | 0 洩漏 |

### 15.2 JavaScript 品質閘門

| 檢查項 | 工具 | 通過標準 |
|--------|------|---------|
| Lint | ESLint | 0 錯誤 |
| 格式化 | Prettier | 無差異 |

### 15.3 禁止模式

| 模式 | 禁止原因 | 替代方案 |
|------|---------|---------|
| `except: pass` | 隱藏所有錯誤 | `except SpecificError: logger.warning(...)` |
| `except Exception: pass` | 隱藏意外錯誤 | 同上 |
| `return NotImplemented` | 執行時崩潰 | 實作方法或 `raise NotImplementedError` |
| `if __name__ == "__main__":` 中的錯誤測試 | 生產代碼混淆 | 使用 pytest |
| `sys.path.insert()` 在執行時 | 破壞匯入順序 | 使用正確的套件結構 |
| `hasattr(obj, "method")` fallback | 隱藏缺失方法 | 直接在類別中實作方法 |
| 無 `__init__.py` 的目錄 | Python <3.3 不相容 | 加入空 `__init__.py` |

---

## 16. CI/CD 標準

### 16.1 CI 工作流（理想）

```yaml
jobs:
  version_check:
    runs-on: ubuntu-latest
    steps:
      - 檢查所有 14+ 版本位置一致
      - 使用 `jq` 檢查 package.json 版本
      - 使用 `grep` 檢查 pyproject.toml 版本
      - 失敗時列出所有不一致的位置

  lint_python:
    runs-on: ubuntu-latest
    steps:
      - black --check
      - isort --check-only
      - flake8
      - mypy

  lint_js:
    runs-on: ubuntu-latest
    steps:
      - ESLint
      - Prettier --check

  test_python:
    strategy:
      matrix:
        python-version: [ '3.10', '3.11', '3.12' ]  # ✅ 不需要 3.14
    steps:
      - pytest tests/unit/ tests/core/
      - pytest tests/ai/ --ignore=tests/ai/test_phase*.py
      - pytest tests/services/ tests/api/
      - 不應有大片 pytest.skip

  security_scan:
    steps:
      - bandit
      - gitleaks

  docs_check:
    steps:
      - 驗證 AGENTS.md 的目錄結構 vs glob
      - 驗證 docs/INDEX.md 的文件清單 vs glob
      - 驗證 CHANGELOG.md 有當前版本的條目
```

### 16.2 CI 當前實際狀態

| 組件 | 實際狀態 | 說明 |
|------|:--------:|------|
| **版本一致性檢查** | ✅ 14 位置已同步 | ci.yml 內嵌檢查所有 14+ 版本位置，皆為 7.5.0-dev |
| **Deploy pipeline** | ✅ `deploy.yml` 存在 | Docker build → ghcr.io → SSH 部署至 staging/production（含通知） |
| **Python 3.14 測試矩陣** | ⚠️ 仍存在 | 3.14 為 alpha 版，建議改為 3.10 / 3.11 / 3.12 |
| **JS 測試** | ⚠️ 佔位符 | `echo "No JS unit tests configured yet"` — 需加入真實 JS 測試 |
| **編譯檢查腳本** | ✅ 不存在亦不檢查 | `scripts/create-release.sh` 不存在，但 CI 也未引用（§16.1 的疑慮已確認消除） |

---

## 附錄 A：配置檔案清單（理想）

```
configs/
├── angela_config.json       # Angela 配置
├── angela_config.yaml       # Angela 配置 (YAML)
├── alert_rules.yml          # Prometheus 告警規則
├── nginx.conf               # Nginx 反向代理
├── prometheus.yml           # Prometheus 配置
└── pyrightconfig.json       # Pyright 配置
```

## 附錄 B：版本位置清單（已驗證 16 個）

見 [12.1 版本位置](#121-14-個版本位置已驗證) 章節。

## 附錄 C：已刪除檔案確認

以下檔案已被確認不再存在且**不應恢復**：

| 檔案/目錄 | 刪除時間 | 最終決定 |
|-----------|---------|---------|
| `apps/mobile-app/` | 2026-06 chore | ❌ 不恢復 |
| `apps/backend/src/modules/` | — | ❌ 應刪除 |
| `apps/backend/src/ai/learning/` | Phase 11 | ❌ 不恢復 |
| `apps/backend/src/ai/ops/` | Phase 11 | ❌ 不恢復 |
| `apps/backend/src/ai/lis/` | Phase 11 | ❌ 不恢復 |
| `apps/backend/src/ai/compression/` | Phase 11 | ❌ 不恢復 |
| `apps/backend/src/ai/evaluation/` | Phase 11 | ❌ 不恢復 |
| `apps/backend/src/ai/symbolic_space/` | Phase 11 | ❌ 不恢復 |
| `apps/backend/src/ai/trust/` | Phase 12b | ❌ 不恢復 |
| `apps/backend/src/ai/security/` | chore | ❌ 不恢復 |
| `apps/backend/src/ai/world_model/` | Phase 9 | ❌ 不恢復 |
| `apps/backend/src/ai/token/` | Phase 9 | ❌ 不恢復 |
| `apps/backend/src/ai/distributed/` | 移除 | ❌ 不恢復 |
| `apps/backend/context_storage/` | — | ❌ 應移至 `data/` |

---

*本文檔定義了 Unified AI Project 的理想目標架構。任何偏離此架構的實作都應被視為需要修復的技術債。*
