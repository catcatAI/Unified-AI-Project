<!--
  =============================================================================
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-06-05
  =============================================================================
-->

# Angela AI v7.5.0-dev — Cross-Platform Digital Life System

[English](#english-version) | [繁體中文](#繁體中文版)

---

## 📑 Index

<details>
<summary><b>English</b></summary>

- [English Version](#english-version)
  - [Current Status](#current-status)
  - [Quick Start](#quick-start)
  - [What Actually Works](#what-actually-works-code-verified)
  - [What's Broken / Never Finished](#whats-broken--never-finished)
  - [Roadmap / Future Extensibility](#roadmap--future-extensibility)
  - [Comprehensive Audit Report](#comprehensive-audit-report)
  - [Documentation Index](#documentation-index)
</details>

<details>
<summary><b>繁體中文</b></summary>

- [繁體中文版](#繁體中文版)
  - [當前進度](#當前進度獨立代理逐項代碼驗證)
  - [快速啟動](#快速啟動)
  - [什麼能跑](#什麼能跑已驗證)
  - [什麼不能用／斷鏈](#什麼不能用斷鏈)
  - [未來路線圖](#未來路線圖)
  - [文件索引](#架構文件)
</details>

---

<a name="english-version"></a>

## English Version

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()

**Angela AI** is a digital life system with biological simulation, self-evolution, and real execution capabilities.

**Quick facts**: 564 Python files, ~69K LOC. Two FastAPI servers, Electron + Live2D desktop companion, mobile stub. **~948 collectable tests, 0 TODO/FIXME/NotImplementedError, 14/14 version consistency.**  
**Component versions (code-verified)**: backend `7.5.0-dev` · desktop `4.1.0-dev` · mobile `1.2.0-dev` · cli `1.1.0` · biology-core `1.0.0` — [full version audit](docs/09-archive/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析).  
**Architecture consistency score**: **62.6%** — [full breakdown](docs/09-archive/FULL_ARCHITECTURE_ANALYSIS.md#6-一致性綜合評分表) (version 31% · shallow 65% · module 66% · algorithm 74%).  
**Total project files**: ~2,950 (1,001 Python · 140 JS/TS · 805 docs · 577 config · 238 test · ~190 other).  
See [AGENTS.md](AGENTS.md) for developer/agent guidelines and [CHANGELOG.md](CHANGELOG.md) for version history.

---

### Current Status (code-verified)

| Area | Status | Key evidence |
|------|--------|-------------|
| **Server starts** | ✅ | `main_api_server.py` 314 lines, imports valid, FastAPI lifespan at `api/lifespan.py:168` |
| **Chat pipeline** | ✅ Core path | `generate_angela_response()` / `get_angela_chat_service()` at `chat_service.py:302-312`, used by `router.py:176` |
| **Self-Evolution** | ✅ 5/6 | ConfigMutator, hot-reload, broadcast, StateStore done; 1 bug (`"User"` key hardcoded) |
| **8D State Matrix** | ✅ | 34 endpoints, drives NGR + LLM context injection |
| **Config system** | ✅ | `config_loader.py:get_config()` returns Config at L869 |
| **Wiring** | ✅ | `services/wiring.py` + `initialize_module_manager()` in lifespan; 6 模組 (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| **Tests** | ✅ | ~1500+, 16.34% coverage, 0 layer violations |
| **P7 Config** | 🟡 | TieredConfigLoader done; core sleeps/intervals/timeouts migrated, ~43 formula/structural values remain |
| **P8 Tech Debt** | ✅ | S1-S4 已完成 — chat_service import 正常, wiring 統一, 安全修復, DI 框架 |

See **[AGENTS.md](AGENTS.md)** (dev guidelines), **[CHANGELOG.md](CHANGELOG.md)** (history), **[MASTER_CONSOLIDATED_PLAN.md](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md)** (tracking), **[PHASE6_NEXT_PLAN.md](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md)** (P6+P7 done), **[MASTER_FINALIZATION_PLAN.md](docs/06-project-management/plans/MASTER_FINALIZATION_PLAN.md)** (P8-P10), **[COMPREHENSIVE_AUDIT_REPORT.md](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md)** (full completion audit), **[PHASE_REVIEW.md](docs/06-project-management/plans/PHASE_REVIEW.md)** (Phase Review 1), **[PHASE_REVIEW2.md](docs/06-project-management/plans/PHASE_REVIEW2.md)** (Phase Review 2), **[PHASE_REVIEW3.md](docs/06-project-management/plans/PHASE_REVIEW3.md)** (Phase Review 3), and **[PHASE_REVIEW4.md](docs/06-project-management/plans/PHASE_REVIEW4.md)** (Phase Review 4 — latest, comprehensive).

### Quick Start

```bash
# Clone
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# Install backend
cd apps/backend
pip install -r requirements.txt
cd ../..

# Start backend (port 8000)
python run_angela.py --api-only

# Desktop app (separate terminal)
cd apps/desktop-app/electron_app
npm install
npm start
```

**Prerequisites**: Python 3.10+, Node.js 16+, Ollama (LLM backend, CPU ~120s/inference).

---

### What Actually Works (Code-Verified)

- **Server starts** (`services/main_api_server.py:314` lines) — FastAPI with lifespan, WebSocket, state matrix, atlassian routes
- **Chat pipeline** — `ChatService` at `services/chat_service.py:313` lines, `generate_angela_response()` at L302, used by `api/router.py:176`
- **Biological simulation** — Heartbeat via `get_metabolic_heartbeat()`, emotions, endocrine, metabolic cycle in `api/lifespan.py`
- **Self-Evolution** — ConfigMutator, hot-reload, broadcast, StateStore independently verified
- **8D State Matrix** — 34 REST endpoints, drives NGR fragment synthesis + LLM context
- **Config system** — `config_loader.py:get_config()` correctly returns Config at L869
- **Wiring module** — `services/wiring.py` + `initialize_module_manager()` in lifespan; 6 ModuleManager 模組 (card_pipeline, intent_registry, vision, audio, tactile, drive) 自動發現/啟動/註冊
- **DI framework** — FastAPI `Depends` in 5 route files (ops_routes, mobile, drive, economy, atlassian)
- **Economy + Pet** — lifecycle managers, WebSocket broadcast wired via lifespan
- **Bootstrap** — hardware detection, directory scaffold, state persistence
- **Test infrastructure** — ~1500+ tests, 16.34% coverage (`tests/` restructured, 0 layer violations, 6 source bugs fixed)

### What's Broken / Never Finished

See detailed breakdowns in linked analysis docs:

| Category | Key Issues | Reference |
|----------|-----------|-----------|
| **Security** | ✅ KeyC leak fixed (`chat_routes.py:184`). `/eval` endpoint removed | `FORENSIC_AUDIT`, `PROBLEM_ANALYSIS` |
| **Functional** | Desktop→Live2D chain incomplete; Mobile stub; Encryption partial | `WIRING_MAP` |
| **God Modules (refactored)** | `main_api_server.py` 314 lines, `angela_llm_service.py` 40 lines (shim), `core/autonomous/` 2 files — **old 1668/2196/60+ sizes were from pre-refactor code** | `MODULARITY_ANALYSIS` (stale analysis) |
| **Governance** | ✅ 版本 13 檔已統一至 7.5.0-dev (S1-S3 完成); CI 含版本檢查; CHANGELOG 同步 | `FULL_ARCHITECTURE_ANALYSIS` |
| **Wiring Gaps** | ✅ 9 agents standard stub format (`stub: True, message: ...`); ✅ 5/5 plugin hooks connected; 50+ stub 實作 | `PHASE6_NEXT_PLAN` |

### Comprehensive Audit Report

> **⚠️ 重要: 本項目目前綜合完成度約 70%，未達到完美完成標準。** 
> 詳細審計覆蓋計畫、文檔、代碼、測試、配置、應用、ASI/AI引擎等所有方面。
> 完整報告: **[COMPREHENSIVE_AUDIT_REPORT.md](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md)**

關鍵發現:
- **測試**: 37.2% 測試文件不充分，~230+ 模組零測試，零性能測試 (25-30%)
- **代碼**: 78 個 `pass`、50+ SKELETON 標記、2 個空文件、8 對影子模組 (55-60%)
- **文檔**: README 過時、計劃間數字矛盾、行動項目無追蹤 (63%)
- **集成**: Atlassian bridge 5% 完成、3 代理純 stub、Level5 ASI 空殼 (30-40%)
- **配置**: 3 獨立系統不協調、13 缺失 key、30 orphaned key (65%)

### Roadmap / Future Extensibility

Systems that are defined/stubbed but not yet implemented — ordered by estimated impact:

> **⚠️ 注意**: 以下清單基於 2026-05-31 全面審計。完整詳細報告請見 **[COMPREHENSIVE_AUDIT_REPORT.md](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md)**。
>
> 綜合完成度約 **70%**。核心服務器/聊天可運行，P0-P2 阻塞已全部清除。

**Tier 1 — Core Infrastructure (foundational gaps)**
- **Plugin System**: 5 hooks defined, **3 handlers registered** (message_logger, metrics_collector, audit_logger). Full CRUD API exists.
- **Intent Dispatch**: ✅ Migrated to ModuleManager→IntentRegistry. ChatService hardcoded fallback still present.

**Tier 2 — Memory & Persistence**
- **HAM Database**: 6 CRUD methods fall back to mock storage
- **State Persistence**: `save_state()`/`load_state()` missing — reboot loses runtime state
- **Importance Scorer**: Returns hardcoded `0.5` (`ai/memory/importance_scorer.py:17`)

**Tier 3 — Specialized Agents (3 persistent stubs)**
- `ImageGenerationAgent`, `AudioProcessingAgent`, `KnowledgeGraphAgent` — return `{"stub": True}` (need external model backends)
- 6 other agents (WebSearch, VisionProcessing, NLPProcessing, CodeUnderstanding, DataAnalysis, FantasyDM) — basic keyword/rule implementations, no ML
- `PlanningAgent` explicitly marked deprecated

**Tier 4 — Reasoning & Causality**
- `real_causal_reasoning_engine.py`: random correlation placeholder, `pass` classes
- **Ripple Axis Applicators**: Only 3/9 implemented (Alpha, Delta, Pi)

**Tier 5 — Alignment & Safety**
- 6 stub classes in `ai/alignment/` — all `pass`
- 5 theoretical formulas (HSM, CDM, Life Intensity, Active Cognition, Non-Paradox) compute but never reach LLM

**Tier 6 — Monitoring & Ops (all placeholder)**
- Predictive maintenance, performance optimizer, AI ops engine — hardcoded values
- Desktop tray: abstract/partial

**Tier 7 — Infrastructure Sketches**
- `Fragmenta` pipeline: stub orchestrator, placeholder element layer
- `ClusterManager`: mock `distribute_task()` sleeps 0.01s
- `AtlassianBridge`: 15/15 methods return empty dicts (5% complete)
- `Level5ASISystem`: 4 inline stub sub-systems — flagship ASI is hollow

**Tier 8 — Code Quality (known gaps)**
- 78 `pass` statements across 50+ files (unimplemented bodies)
- ~233 functions missing return type annotations
- 8 pairs of shadowed/duplicate module paths (`shared/` vs `core/shared/`)
- 2 config systems (TieredConfigLoader + AngelaConfigManager) not unified
- 3 config systems with 30 orphaned YAML keys and 13 missing keys
- `health_check_service.py`: 2/3 import targets don't exist

---

### Documentation Index

See dedicated docs for full diagrams:

| Document | Contents |
|----------|----------|
| [PROJECT_CHARTER](docs/00-overview/PROJECT_CHARTER.md) | Project mission, scope, principles |
| [GLOSSARY](docs/00-overview/GLOSSARY.md) | Full project terminology reference |
| [UNIFIED_DOC_INDEX](docs/00-overview/UNIFIED_DOCUMENTATION_INDEX.md) | Comprehensive doc inventory |
| [WIRING_MAP](docs/03-technical-architecture/analysis/WIRING_MAP_2026-05-21.md) | Server lifecycle, factory chains, subtle wiring, dead code registry |
| [CODE_STATISTICS](docs/03-technical-architecture/analysis/CODE_STATISTICS_2026-05-21.md) | Live vs dead vs semi-finished code by directory |
| [MODULARITY_ANALYSIS](docs/03-technical-architecture/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God modules, central hub coupling, 20+ singletons |
| [PROBLEM_ANALYSIS](docs/03-technical-architecture/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 3-perspective audit, security issues, CTO roadmap |
| [FORENSIC_AUDIT](docs/03-technical-architecture/analysis/FORENSIC_AUDIT_2026-05-22.md) | 3-perspective audit: execution paths, TCS migration, security + dead code |
| [MASTER_CONSOLIDATED_PLAN](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md) | **Active task plan**: 53 items, S/A/B/C tiers, 53/53 complete |
| [CARD_INTEGRATION_PLAN](docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md) | Card pipeline → ChatService wiring: 4 phases, 10 disconnection points |
| [MODULE_MANAGER_DESIGN](docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md) | ✅ **Implemented** — M0-M5 (6 files + 100 tests) + 6 modules (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| [CARD_INTEGRATION_REVIEW](docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md) | Proactive audit: 25 issues found before implementation, 8 HIGH |
| [PHASE6_NEXT_PLAN](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md) | Quality finishing: Plugin deployment, Config handlers, Magic number migration, Stub cleanup |
| [MASTER_FINALIZATION_PLAN](docs/06-project-management/plans/MASTER_FINALIZATION_PLAN.md) | Final push to 0: Remaining handlers, orphaned services, NotImplementedErrors, docs, tests |
| [COMPREHENSIVE_AUDIT_REPORT](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md) | **Full completion audit**: Plans, docs, code, tests, config, apps — completeness judged against "perfect" standard |
| [PHASE_REVIEW2](docs/06-project-management/plans/PHASE_REVIEW2.md) | **Phase Review 2 (06-03)**: 17-session tracking audit, ~96% composite |
| [PHASE_REVIEW3](docs/06-project-management/plans/PHASE_REVIEW3.md) | **Phase Review 3 (06-04)**: 3-agent comprehensive audit, 10-dimension assessment |

---

<a name="繁體中文版"></a>

## 繁體中文版

**Angela AI** 是一個數位生命系統，具備生物模擬、自演化與真實執行能力。

**Quick facts**：562 個 Python 檔案、~127K 行。兩台 FastAPI 伺服器、Electron + Live2D 桌面端、手機 stub。  
**架構一致性評分**: **62.6%** (版本 31% · 結構 65% · 模塊 66% · 算法 74%) — [評分明細](docs/09-archive/FULL_ARCHITECTURE_ANALYSIS.md#6-一致性綜合評分表)  
**專案總文件**: ~2,950 (Python 1,001 · JS/TS 140 · 文檔 805 · 配置 577 · 測試 238 · 其他 ~190)

---

### 當前進度（代碼驗證）

| 領域 | 狀態 | 關鍵證據 |
|------|------|---------|
| **伺服器啟動** | ✅ | `services/main_api_server.py` 314 行，FastAPI lifespan 在 `api/lifespan.py:168` |
| **聊天管線** | ✅ 核心路徑 | `generate_angela_response()` / `get_angela_chat_service()` 在 `chat_service.py:302-312`，由 `router.py:176` 調用 |
| **自演化** | ✅ 5/6 | ConfigMutator、熱重載、廣播、StateStore 正常；1 bug（`"User"` key 硬編碼） |
| **8D 狀態矩陣** | ✅ | 34 REST 端點，驅動 NGR + LLM 上下文注入 |
| **配置系統** | ✅ | `config_loader.py:get_config()` 正確回傳 Config（L869） |
| **Wiring** | ✅ | `services/wiring.py` + `initialize_module_manager()` in lifespan; 6 模組 (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| **測試** | ✅ | ~1500+ tests, 16.34% 覆蓋率, 0 層級違規 |
| **P7 配置** | 🟡 | TieredConfigLoader 完成；核心 sleeps/intervals/timeouts 已遷移，~43 公式/結構值殘留 |
| **P8 技術債** | ✅ | S1-S4 已完成 — chat_service import 正常, wiring 統一, 安全修復, DI 框架 |

詳見 **[MASTER_CONSOLIDATED_PLAN.md](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md)** (53/53 完成)、**[PHASE6_NEXT_PLAN.md](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md)** (P6+P7 完成)、**[MASTER_FINALIZATION_PLAN.md](docs/06-project-management/plans/MASTER_FINALIZATION_PLAN.md)** (P8-P10，0 剩餘任務目標)、與 **[COMPREHENSIVE_AUDIT_REPORT.md](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md)** (全面審計報告)。

---

### 快速啟動

```bash
cd apps/backend
pip install -r requirements.txt
cd ../..
python run_angela.py --api-only

# 桌面端（另開 terminal）
cd apps/desktop-app/electron_app
npm install
npm start
```

**環境需求**：Python 3.10+、Node.js 16+、Ollama（LLM 後端，CPU 約 120 秒/次）

> ⚠️ 後端有兩台 FastAPI 伺服器，均預設 port 8000。同一時間只能一台綁定 8000，另一台需用 `--port`。詳見 [ARCHITECTURE_MAP](docs/03-technical-architecture/analysis/ARCHITECTURE_MAP_2026-05-20.md)（Server topology, port conflict）。

---

### 什麼能跑（代碼驗證）

- **伺服器啟動**（`services/main_api_server.py` 314 行）— FastAPI + lifespan + WebSocket + 34 state matrix endpoints
- **聊天管線** — `ChatService`（313 行），`generate_angela_response()` 在 L302，由 `api/router.py:176` 調用
- **生物模擬** — Heartbeat 透過 `get_metabolic_heartbeat()`，情緒、荷爾蒙、代謝循環在 `api/lifespan.py`
- **自演化核心** — ConfigMutator、熱重載、廣播、StateStore 獨立驗證
- **8D 狀態矩陣** — 34 REST 端點，驅動 NGR + LLM 上下文注入
- **配置系統** — `config_loader.py:get_config()` 正確回傳 Config（L869）
- **Wiring** — `services/wiring.py` + `initialize_module_manager()` in lifespan; 6 模組自動發現/啟動/註冊至 ServiceRegistry
- **DI 框架** — FastAPI `Depends` 用於 5 路由（ops_routes, mobile, drive, economy, atlassian）
- **經濟 + 寵物** — WebSocket 廣播已接線，lifecycle managers 正常
- **測試基礎設施** — ~1500+ tests, 16.34% 覆蓋率, 0 層級違規, 6 源碼 bug 已修復

### 什麼不能用／斷鏈

| 類別 | 主要問題 | 參考文件 |
|------|---------|---------|
| **功能斷鏈** | 桌面→Live2D 未完成；手機 stub | `WIRING_MAP` |
| **Plugin 空接** | 5 hooks 已定義，3 handler 註冊 | `PHASE6_NEXT_PLAN` |
| **Agent stub** | ~5 agents 仍為 stub 回傳 mock 資料 | `AGENT_DESIGN` |
| **Ripple Axis** | 僅 3/9 applicators 存在 (Alpha/Delta/Pi) | `RIPPLE_AXIS_DESIGN` |

### 未來路線圖

已定義但未實作／未接線的系統 — 依影響力排序：

**Tier 1 — 核心基礎設施**
- **Plugin 系統**：5 hooks 已定義（`on_message`, `on_response`, `on_bio_event`, `on_state_change`, `on_tick`），**3 handler 註冊**（message_logger, metrics_collector, audit_logger）。CRUD API 完整
- **Config Handler**：5 個 YAML handler 無對應代碼：`FileOperationHandler`, `GoogleDriveHandler`, `WebSearchHandler`, `LearningHandler`（`angela_core.yaml:131-257`）
- **意圖分發**：🟡 已部分修復 — `IntentRegistry` 已存在並由 ModuleManager 管理，但 ChatService 仍使用硬編碼 fallback

**Tier 2 — 記憶與持久層**
- **HAM 資料庫**：✅ 已實作 — `HAMCoreStorage` 具備真實檔案 I/O、Fernet 加密、查詢引擎（`ham_core_storage.py` + `ham_query_engine.py`）
- **記憶鏈**：🟡 HAM query/storage 已接線，LU/CDM 仍待完整接線
- **狀態持久化**：🟡 已部分修復 — `save_state()`/`load_state()` 介面已定義，`JSONStore` 已實作（`core/interfaces/persistence.py`）
- **重要性評分**：回傳硬編碼 `0.5`

**Tier 3 — 專業代理（部分 stub）**
- ~5 agents 仍為 stub（影像生成、語音、知識圖譜、網路搜尋、程式碼理解等僅有 header comments，無實作）
- ✅ `agent_manager.py` 健康檢查已實作（結構化狀態報告/代理註冊驗證）
- 其餘 agents（視覺、資料分析、NLP、Fantasy DM、創意寫作）有基本 keyword/rule 實作，無 ML
- Planning agent 已標記為可棄用

**Tier 4 — 推理與因果**
- ✅ 因果推理引擎已修復 — 使用基於字元重疊的確定性函數取代隨機相關係數
- ✅ `RealInterventionPlanner` 已實作（計畫追蹤/執行/評估）
- ✅ `RealCounterfactualReasoner` 已實作（反事實分析/依賴評估/歷史追蹤）
- Ripple Axis Applicators：僅 3/9 存在（Alpha, Delta, Pi），缺 Beta/Theta/Epsilon/Zeta/Eta/Kappa

**Tier 5 — 對齊與安全性**
- ✅ 6 類別已實作：`EmotionSystem`（情緒狀態 VAD）、`OntologySystem`（概念註冊）、`AlignmentManager`（約束匹配）、`DecisionTheorySystem`（期望效用）、`AdversarialGenerationSystem`（對抗提示）、`ASIAutonomousAlignment`（自主檢查）
- 5 大理論公式（HSM/CDM/Life Intensity/Active Cognition/Non-Paradox）計算結果從未注入 LLM Prompt

**Tier 6 — 監控與維運**
- ✅ `AI Ops Engine` 已實作（異常檢測/回應路由/歷史追蹤）
- ✅ `PredictiveMaintenance` 已實作（異常頻率分析/故障預測）
- ✅ `performance_optimizer.py` 已完整實作（psutil 即時指標/閾值檢查/報告）
- Desktop tray：`BaseTrayManager` 抽象，`WindowsTrayManager` 部分實作

**Tier 7 — 基礎設施草稿**
- ✅ `cluster_manager.py` 已實作（節點註冊/任務分發/狀態查詢）
- ✅ Fragmenta 處理管線已實作（orchestrator 片段路由 + vision tone inversion + element layer 轉換）
- ✅ `AtlassianBridge` 已實作（真實 Jira/Confluence/Bitbucket API 整合）
- `ClusterManager`：mock 實作，`distribute_task()` 只 sleep 0.01s
- `AtlassianBridge`：✅ 已實作 — 288 行真實程式碼，支援 Confluence/Jira/Bitbucket API
- `core_services.py`：仍為 CLI standalone stub（36 行，回傳 None）
- `code_understanding_tool.py`：空檔案（0 行），仍無法使用

---

### 架構文件

| 文件 | 內容 |
|------|------|
| [專案憲章](docs/00-overview/PROJECT_CHARTER.md) | 專案使命、範圍、原則 |
| [詞彙表](docs/00-overview/GLOSSARY.md) | 完整名詞解釋 |
| [統一文件索引](docs/00-overview/UNIFIED_DOCUMENTATION_INDEX.md) | 所有文件導覽 |
| [技術架構概覽](docs/03-technical-architecture/README.md) | HSP、HAM、NGR、8D Matrix、多模態代理、通訊層、安全性 |
| [ARCHITECTURE_MAP](docs/03-technical-architecture/analysis/ARCHITECTURE_MAP_2026-05-20.md) | 伺服器拓撲、port 衝突、路由對照 |
| [全量架構分析](docs/09-archive/FULL_ARCHITECTURE_ANALYSIS.md) | 完整架構圖譜、版本溯源、六層一致性評分 |
| [AGENTS.md](AGENTS.md) | 代理開發指南 — 構建/測試/代碼規範 |
| [CHANGELOG.md](CHANGELOG.md) | 版本歷史與變更記錄 |

### 分析與計畫文件

| 文件 | 內容 |
|------|------|
| [WIRING_MAP](docs/03-technical-architecture/analysis/WIRING_MAP_2026-05-21.md) | 接線圖、工廠鏈、死代碼 |
| [CODE_STATISTICS](docs/03-technical-architecture/analysis/CODE_STATISTICS_2026-05-21.md) | 代碼統計、活/死/半成品 |
| [MODULARITY_ANALYSIS](docs/03-technical-architecture/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God module、耦合、singleton |
| [PROBLEM_ANALYSIS](docs/03-technical-architecture/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 三重視角審計、安全問題、優先級 |
| [FORENSIC_AUDIT](docs/03-technical-architecture/analysis/FORENSIC_AUDIT_2026-05-22.md) | 三輪獨立審計：執行路徑、TCS 遷移、安全性 + 死代碼 |
| [MASTER_CONSOLIDATED_PLAN](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md) | **進行中任務總計畫**：53 項、S/A/B/C 分級、53/53 完成 |
| [CARD_INTEGRATION_PLAN](docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md) | 卡片管道 → ChatService 接線 v2：ModuleManager 驅動 |
| [MODULE_MANAGER_DESIGN](docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md) | ✅ **已實作** — M0-M5 (6 files + 100 tests) + 6 模組 (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| [CARD_INTEGRATION_REVIEW](docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md) | 事前審計：執行前發現 25 問題（8 HIGH） |
| [PHASE6_NEXT_PLAN](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md) | Quality finishing: Plugin 部署, Config handler, Magic number 遷移, Stub 清理 |
| [MASTER_FINALIZATION_PLAN](docs/06-project-management/plans/MASTER_FINALIZATION_PLAN.md) | Final push to 0: 殘留 handler, 孤立服務, NotImplementedError, docs, tests |
| [COMPREHENSIVE_AUDIT_REPORT](docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md) | **全面審計報告**: 計畫、文檔、代碼、測試、配置、應用的完美完成度判定 |
| [PHASE_REVIEW](docs/06-project-management/plans/PHASE_REVIEW.md) | **階段審查 1 (06-02)**: 首次3代理並行審計，10維度評分 |
| [PHASE_REVIEW2](docs/06-project-management/plans/PHASE_REVIEW2.md) | **階段審查 2 (06-03)**: 17會話後追蹤審計，~96% 綜合分數 |
| [PHASE_REVIEW3](docs/06-project-management/plans/PHASE_REVIEW3.md) | **階段審查 3 (06-04)**: 3代理綜合審計，10維度判定，23+殘留問題 |
| [REMAINING_ISSUES_PLAN](docs/06-project-management/plans/REMAINING_ISSUES_PLAN.md) | placeholder 清除、unittest→pytest 遷移 |
| [TEST_RESTRUCTURE_PLAN](docs/06-project-management/plans/TEST_RESTRUCTURE_PLAN.md) | 測試層級架構、conftest 分層、CI 整合 |

---

**Version**: 7.5.0-dev | **Code Stats**: 562 Python files, ~127K lines | [Version Audit](docs/09-archive/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析) | [Phase Review 2](docs/06-project-management/plans/PHASE_REVIEW2.md) | [Phase Review 3](docs/06-project-management/plans/PHASE_REVIEW3.md)
