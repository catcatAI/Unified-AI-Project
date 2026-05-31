<!--
  =============================================================================
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-05-25
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
  - [Documentation Index](#architecture)
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

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()

**Angela AI** is a digital life system with biological simulation, self-evolution, and real execution capabilities.

**Quick facts**: 515 Python files, ~116K lines (84% live, 9% dead, 7% semi-finished). Two FastAPI servers, Electron + Live2D desktop companion, mobile stub. **~1500+ tests, 16.34% coverage, 0 layer violations.**  
**Component versions (code-verified)**: backend `7.5.0-dev` · desktop `4.1.0-dev` · mobile `1.2.0-dev` · cli `1.1.0` · biology-core `1.0.0` — [full audit](docs/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析).  
**Architecture consistency score**: **62.6%** — [full breakdown](docs/FULL_ARCHITECTURE_ANALYSIS.md#6-一致性綜合評分表) (version 31% · shallow 65% · module 66% · algorithm 74%).  
**Total project files**: ~2,761 (1,001 Python · 140 JS/TS · 805 docs · 577 config · 238 test).

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
| **P7 Config** | 🟡 | TieredConfigLoader done; 150+ magic numbers not migrated |
| **P8 Tech Debt** | ✅ | S1-S4 已完成 — chat_service import 正常, wiring 統一, 安全修復, DI 框架 |

See **[MASTER_CONSOLIDATED_PLAN.md](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md)** (53/53 complete) and **[PHASE6_NEXT_PLAN.md](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md)** (quality finishing).

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

**Prerequisites**: Python 3.9+, Node.js 16+, Ollama (LLM backend, CPU ~120s/inference).

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
| **Wiring Gaps** | ✅ 9 agents standard stub format (`stub: True, message: ...`); 50+ stub 實作 | `PHASE6_NEXT_PLAN` |

### Roadmap / Future Extensibility

Systems that are defined/stubbed but not yet implemented — ordered by estimated impact:

**Tier 1 — Core Infrastructure (foundational gaps)**
- **Plugin System**: 5 hooks defined (`on_message`, `on_response`, `on_bio_event`, `on_state_change`, `on_tick`), **0 handlers registered**. Full CRUD API exists (`api/v1/endpoints/plugins.py`) but no plugins deployed.
- **Config Handlers**: 5 YAML-defined handlers have **no code**: `FileOperationHandler`, `GoogleDriveHandler`, `WebSearchHandler`, `LearningHandler` (`angela_core.yaml:131-257`)
- **Intent Dispatch**: ✅ ChatService 現已優先經 ModulerManager→IntentRegistry 偵測意圖 (Phase 2 完成)。回退至硬編碼 keyword match (`chat_service.py:162-198`, 21 tests)

**Tier 2 — Memory & Persistence**
- **HAM Database**: All 6 CRUD methods transparently fall back to mock storage (`database.py:33-165`)
- **Memory Chain**: HAM/LU/CDM classes defined but query/storage flow never wired
- **State Persistence**: `save_state()`/`load_state()` do not exist — reboot loses all runtime state
- **Importance Scorer**: Returns hardcoded `0.5` placeholder (`importance_scorer.py:10`)

**Tier 3 — Specialized Agents (all stub)**
- ImageGeneration, AudioProcessing, WebSearch, KnowledgeGraph, VisionProcessing, DataAnalysis, NLPProcessing, CodeUnderstanding, FantasyDM, CreativeWriting agents — all return hardcoded/placeholder data
- **Planning agent** explicitly marked deprecated (`planning_agent.py:35-36`)

**Tier 4 — Reasoning & Causality**
- Causal reasoning engine: `_analyze_observation_causality()` uses random correlation placeholder (`real_causal_reasoning_engine.py:26`)
- `RealInterventionPlanner` and `RealCounterfactualReasoner` are empty `pass` classes
- **Ripple Axis Applicators**: Only 3/9 exist (Alpha, Delta, Pi). Missing: Beta, Theta, Epsilon, Zeta, Eta, Kappa (`ripple/node.py:290-292`)

**Tier 5 — Alignment & Safety**
- 6 stub classes in `ai/alignment/`: `EmotionSystem`, `OntologySystem`, `AlignmentManager`, `DecisionTheorySystem`, `AdversarialGenerationSystem`, `ASIAutonomousAlignment` — all `pass`
- 5 theoretical formulas (HSM, CDM, Life Intensity, Active Cognition, Non-Paradox) compute but never reach LLM prompt

**Tier 6 — Monitoring & Ops (all placeholder)**
- Predictive maintenance, performance optimizer, AI ops engine — all return hardcoded values
- Desktop tray: `BaseTrayManager` abstract, `WindowsTrayManager` partial

**Tier 7 — Infrastructure Sketches**
- `Fragmenta` processing pipeline: stub orchestrator, placeholder element layer, stub vision tone inverter
- `ClusterManager`: mock implementation, `distribute_task()` sleeps 0.01s
- `AtlassianBridge`: skeleton, all 15+ methods return empty dicts
- `core_services.py`: CLI standalone stub
- `code_understanding_tool.py`: all methods return "temporarily unavailable"

**Tier 8 — Code Quality (known but not prioritized)**
- 16 Factories: 9 dead + 6 dormant + 1 alive (see `DEAD_FACTORY_FORENSICS.md`)
- 57 `logging.basicConfig()` module-level calls fighting for root logger
- 2 broken `__init__.py` with `__all_` typo (`ai/trust/`, `ai/service_discovery/`)
- 150+ hardcoded magic numbers (`arousal >` x15, `random.random()` x29, `> 0.x` x150+)
- `health_check_service.py`: 2/3 import targets don't exist (caught by try/except)

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
| [MASTER_CONSOLIDATED_PLAN](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md) | **Active task plan**: 27 items, S/A/B/C tiers, code-verified status |
| [CARD_INTEGRATION_PLAN](docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md) | Card pipeline → ChatService wiring: 4 phases, 10 disconnection points |
| [MODULE_MANAGER_DESIGN](docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md) | ✅ **Implemented** — M0-M5 (6 files + 100 tests) + 6 modules (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| [CARD_INTEGRATION_REVIEW](docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md) | Proactive audit: 25 issues found before implementation, 8 HIGH |
| [PHASE6_NEXT_PLAN](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md) | Quality finishing: Plugin deployment, Config handlers, Magic number migration, Stub cleanup |

---

<a name="繁體中文版"></a>

## 繁體中文版

**Angela AI** 是一個數位生命系統，具備生物模擬、自演化與真實執行能力。

**Quick facts**：515 個 Python 檔案、~116K 行（84% 活、9% 死、7% 半成品）。兩台 FastAPI 伺服器、Electron + Live2D 桌面端、手機 stub。  
**架構一致性評分**: **62.6%** (版本 31% · 結構 65% · 模塊 66% · 算法 74%) — [評分明細](docs/FULL_ARCHITECTURE_ANALYSIS.md#6-一致性綜合評分表)  
**專案總文件**: ~2,761 (Python 1,001 · JS/TS 140 · 文檔 805 · 配置 577 · 測試 238)

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
| **P7 配置** | 🟡 | TieredConfigLoader 完成；150+ magic number 未遷移 |
| **P8 技術債** | ✅ | S1-S4 已完成 — chat_service import 正常, wiring 統一, 安全修復, DI 框架 |

詳見 **[MASTER_CONSOLIDATED_PLAN.md](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md)** (53/53 完成) 與 **[PHASE6_NEXT_PLAN.md](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md)** (quality finishing)。

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

**環境需求**：Python 3.9+、Node.js 16+、Ollama（LLM 後端，CPU 約 120 秒/次）

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
| **安全性** | ✅ KeyC 洩漏已修復。`/eval` 端點已移除 | `FORENSIC_AUDIT` |
| **功能斷鏈** | 桌面→Live2D 未完成；手機 stub；加密不完整 | `WIRING_MAP` |
| **上帝模塊（已重構）** | `main_api_server.py` 314 行、`angela_llm_service.py` 40 行 (shim)、`core/autonomous/` 2 檔 | `MODULARITY_ANALYSIS` |
| **治理** | ✅ 版本 13 檔已統一至 7.5.0-dev (S1-S3 完成); CI 含版本檢查; CHANGELOG 同步 | `FULL_ARCHITECTURE_ANALYSIS` |
| **接線缺口** | ✅ 9 agents 標準化 stub 格式 (`stub: True, message: ...`); 50+ stub 實作 | `PHASE6_NEXT_PLAN` |

### 未來路線圖

已定義但未實作／未接線的系統 — 依影響力排序：

**Tier 1 — 核心基礎設施**
- **Plugin 系統**：5 hooks 已定義（`on_message`, `on_response`, `on_bio_event`, `on_state_change`, `on_tick`），**0 handler 註冊**。CRUD API 完整但無任何 plugin 部署
- **Config Handler**：5 個 YAML handler 無對應代碼：`FileOperationHandler`, `GoogleDriveHandler`, `WebSearchHandler`, `LearningHandler`（`angela_core.yaml:131-257`）
- **意圖分發**：ChatService 硬編碼 3 種 intent 的 keyword match，繞過可辨識 12+ intents 的 `IntentRegistry`（`modules/intent_registry/` 模組已存在但未接線）

**Tier 2 — 記憶與持久層**
- **HAM 資料庫**：6 個 CRUD 方法全部透明降級到 mock 儲存
- **記憶鏈**：HAM/LU/CDM 類別完整但查詢/儲存流程從未接線
- **狀態持久化**：`save_state()`/`load_state()` 不存在，重啟丟失所有狀態
- **重要性評分**：回傳硬編碼 `0.5`

**Tier 3 — 專業代理（全部 stub）**
- 10+ agents（影像生成、語音、網路搜尋、知識圖譜、視覺、資料分析、NLP、程式碼理解、Fantasy DM、創意寫作）— 全部回傳硬編碼或 mock 資料
- Planning agent 已標記為可棄用

**Tier 4 — 推理與因果**
- 因果推理引擎使用隨機相關性 placeholder
- `RealInterventionPlanner` 和 `RealCounterfactualReasoner` 是空的 `pass` 類別
- Ripple Axis Applicators：僅 3/9 存在（Alpha, Delta, Pi），缺 Beta/Theta/Epsilon/Zeta/Eta/Kappa

**Tier 5 — 對齊與安全性**
- `ai/alignment/` 中 6 個 stub 類別：`EmotionSystem`, `OntologySystem`, `AlignmentManager` 等 — 全是 `pass`
- 5 大理論公式（HSM/CDM/Life Intensity/Active Cognition/Non-Paradox）計算結果從未注入 LLM Prompt

**Tier 6 — 監控與維運（全部 placeholder）**
- 預測維護、效能優化器、AI Ops Engine — 全部回傳硬編碼值
- Desktop tray：`BaseTrayManager` 抽象，`WindowsTrayManager` 部分實作

**Tier 7 — 基礎設施草稿**
- Fragmenta 處理管線：stub orchestrator + placeholder element layer + stub vision inverter
- `ClusterManager`：mock 實作，`distribute_task()` 只 sleep 0.01s
- `AtlassianBridge`：skeleton，15+ 方法全部回傳空 dict
- `core_services.py`：CLI standalone stub
- `code_understanding_tool.py`：全部回傳 "temporarily unavailable"

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

### 分析與計畫文件

| 文件 | 內容 |
|------|------|
| [WIRING_MAP](docs/03-technical-architecture/analysis/WIRING_MAP_2026-05-21.md) | 接線圖、工廠鏈、死代碼 |
| [CODE_STATISTICS](docs/03-technical-architecture/analysis/CODE_STATISTICS_2026-05-21.md) | 代碼統計、活/死/半成品 |
| [MODULARITY_ANALYSIS](docs/03-technical-architecture/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God module、耦合、singleton |
| [PROBLEM_ANALYSIS](docs/03-technical-architecture/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 三重視角審計、安全問題、優先級 |
| [FORENSIC_AUDIT](docs/03-technical-architecture/analysis/FORENSIC_AUDIT_2026-05-22.md) | 三輪獨立審計：執行路徑、TCS 遷移、安全性 + 死代碼 |
| [MASTER_CONSOLIDATED_PLAN](docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md) | **進行中任務總計畫**：27 項、S/A/B/C 分級、代碼審計驗證 |
| [CARD_INTEGRATION_PLAN](docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md) | 卡片管道 → ChatService 接線 v2：ModuleManager 驅動 |
| [MODULE_MANAGER_DESIGN](docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md) | ✅ **已實作** — M0-M5 (6 files + 100 tests) + 6 模組 (card_pipeline, intent_registry, vision, audio, tactile, drive) |
| [CARD_INTEGRATION_REVIEW](docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md) | 事前審計：執行前發現 25 問題（8 HIGH） |
| [PHASE6_NEXT_PLAN](docs/06-project-management/plans/PHASE6_NEXT_PLAN.md) | Quality finishing: Plugin 部署, Config handler, Magic number 遷移, Stub 清理 |
| [REMAINING_ISSUES_PLAN](docs/06-project-management/plans/REMAINING_ISSUES_PLAN.md) | placeholder 清除、unittest→pytest 遷移 |
| [TEST_RESTRUCTURE_PLAN](docs/06-project-management/plans/TEST_RESTRUCTURE_PLAN.md) | 測試層級架構、conftest 分層、CI 整合 |

---

**Version**: 7.5.0-dev | **Code Stats**: 515 Python files, ~116K lines (84% live, 9% dead, 7% semi-finished) | [Version Audit](docs/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析)
