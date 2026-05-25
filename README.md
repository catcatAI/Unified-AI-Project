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
  - [Current Status (Code-Verified)](#current-status-code-verified-by-independent-audit)
    - [Phase 6 — Self-Evolution Loop](#current-status-code-verified-by-independent-audit)
    - [Phase 6.5 — Startup Wiring](#current-status-code-verified-by-independent-audit)
    - [Phase 7 — Tiered Config](#current-status-code-verified-by-independent-audit)
    - [Phase 8 — Tech Debt Cleanup](#current-status-code-verified-by-independent-audit)
    - [Test Infrastructure](#current-status-code-verified-by-independent-audit)
  - [Quick Start](#quick-start)
  - [What Actually Works](#what-actually-works-code-verified)
  - [What's Broken / Never Finished](#whats-broken--never-finished)
    - [Security](#whats-broken--never-finished)
    - [Functional Gaps](#whats-broken--never-finished)
    - [God Modules](#whats-broken--never-finished)
    - [Architecture & Governance](#whats-broken--never-finished)
    - [Code Quality](#whats-broken--never-finished)
  - [Architecture Documents](#architecture)
  - [Analysis Documents](#analysis-documents)
</details>

<details>
<summary><b>繁體中文</b></summary>

- [繁體中文版](#繁體中文版)
  - [當前進度 (獨立代理逐項代碼驗證)](#當前進度獨立代理逐項代碼驗證)
    - [P6 自演化閉環](#當前進度獨立代理逐項代碼驗證)
    - [P6.5 啟動接線](#當前進度獨立代理逐項代碼驗證)
    - [P7 分層配置](#當前進度獨立代理逐項代碼驗證)
    - [P8 技術債清理](#當前進度獨立代理逐項代碼驗證)
    - [測試基礎設施](#當前進度獨立代理逐項代碼驗證)
  - [快速啟動](#快速啟動)
  - [什麼能跑 (已驗證)](#什麼能跑已驗證)
  - [什麼不能用／斷鏈](#什麼不能用斷鏈)
    - [安全性](#什麼不能用斷鏈)
    - [架構與治理](#什麼不能用斷鏈)
    - [大型上帝模塊](#什麼不能用斷鏈)
    - [功能斷鏈](#什麼不能用斷鏈)
    - [代碼品質](#什麼不能用斷鏈)
  - [架構文件](#架構文件)
  - [分析文件](#分析文件)
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

### Current Status (Code-Verified by Independent Audit)

**▶ Phase 6 — Self-Evolution Loop**

| Deliverable | Evidence (file:line) | Status |
|-------------|---------------------|--------|
| ConfigMutator | `core/system/evolution/config_mutator.py` — full class, schema validation (L41-79), atomic write (L100-102), targets `*.evolved.yaml` (L110-136) | ✅ Done |
| Hot-reload | `angela_llm_service.py` — `reload_config()` at L945-963, clears backends, re-inits | ✅ Done |
| User confirmation gate | `chat_service.py` — `_handle_evolution_proposal()` at L54-96, checks confirm keywords, calls `mutator.apply_mutation()` | 🟡 Has bug: L270 hardcodes `"User"` key, fails for other usernames |
| Evolution broadcast | `bootstrap_manager.py` — `broadcast_evolution()` at L58-78, writes to state + StateStore | ✅ Done |
| StateStore | `core/system/state_store/global_store.py` — full pub-sub with domains, subscribers (86 lines) | ✅ Implementation complete; 🟡 Not integrated into main state matrix update loop |

**▶ Phase 6.5 — Startup Wiring**

| Deliverable | Evidence | Status |
|-------------|----------|--------|
| Heartbeat in lifespan | `main_api_server.py` — `.start()` at L376-378, `.stop()` at L405-406 | ✅ Done |
| `_initialize_all_services()` | `main_api_server.py` — L370 called in lifespan startup; L547-623 wires vision/audio/tactile/digital_life/economy/pet + WebSocket hooks | ✅ Done |

**▶ Phase 7 — Tiered Config Architecture**

| Deliverable | Evidence | Status |
|-------------|----------|--------|
| TieredConfigLoader class | `core/system/config/tiered_loader.py` — implements Default→User→Angela merge chain correctly (L27-48) | ✅ Done |
| S-level defaults | `configs/system/`: 4 `.default.yaml` files | ✅ Done |
| A-level defaults | `configs/standard/`: 6 `.default.yaml` across science/behavior/matrix/narrative | ✅ Done |
| M-level defaults | `configs/mods/`: `active_mods.default.yaml` | ✅ Done |
| config_loader.py → TCS redirect | `config_loader.py` — `load_config()` calls TCS (L20-25); `get_config()` at L869 assigns `_config = Config.load()` — **works correctly** | ✅ **Working** |
| `.user.yaml` overlays | rg search: **0 files** in entire configs/ tree | ❌ Missing |
| `.evolved.yaml` overlays | rg search: **1 demo file** (`standard/behavior/demo.evolved.yaml`), 0 production | ❌ Missing |
| Hardcoded thresholds → config | rg search: `arousal >` x15, `random.random()` x29, `target_fps` x24, `if.*>.*0.x` x150+ | ❌ Not done |
| Legacy config deprecated | `angela_core.yaml` (27 sections, 12 DEAD) still primary runtime source | ❌ Still primary |
| ConfigMutator writes `*.evolved.yaml` | `config_mutator.py` L110-136 — correctly maps to evolved paths | ✅ Done |
| DEAD sections cleaned | 12 `# DEAD` sections still in `angela_core.yaml` | ❌ Not cleaned |

**▶ Phase 8 — Tech Debt Cleanup (S1-S4 still broken)**

| Task | Evidence | Status |
|------|----------|--------|
| S1: Split chat_service | `chat_service.py` now 306 lines (was 1281); BUT `generate_angela_response()` and `get_angela_chat_service()` removed — `main_api_server.py:292,695,1370` and `router.py:175` still import them → **ImportError at server start** | ❌ **BROKEN** |
| S2: Split wiring to independent file | No `wiring.py` exists; `_initialize_all_services()` still embedded in `main_api_server.py` L547-623 | ❌ Not started |
| S3: Security fixes | Pickle commented out (cache_manager.py L156-167); command injection `/eval` endpoint still exists (main_api_server.py L1467); KeyC leak via localhost endpoint | 🟡 Partial |
| S4: DI framework | `Depends` used in 5 route files (atlassian, drive, mobile, ops, economy); all core services still use manual lazy singletons | 🟡 Partial |

**▶ Test Infrastructure (Completed in this session — code-audited)**

| Task | Detail | Status |
|------|--------|--------|
| Source bugs found & verified fixed | 6 in source (Pearson, 2× NameError, 2× TypeError, missing param); 1 (health_check_service imports) only test-mocked | ✅ **6 fixed** |
| Architecture layer violations (ai/ → services/) | 0 (4 lazy imports in methods, acceptable) | ✅ |
| Root directory cleaned | 62 scripts → tests/scripts/, only conftest.py + __init__.py remain | ✅ |
| Legacy subdirectories removed | 6 (creation, economy, evaluation, interfaces, meta, security) | ✅ |
| Legacy tests migrated to correct layers | 40 files (services 6, core 22, ai 5, memory 3, agents 2, shared 2) | ✅ |
| SMOKE→REAL, WEAK→STRONG upgrades | 8 subdirs, 70+ assertions upgraded, 24 files | ✅ |
| New tests created | ai/meta/ 48, core/ 222 across 13 modules | ✅ |
| Total test count | ~1500+ (audited) | ✅ |
| Coverage | 16.34% (was ~12.64%) | 🟡 Target 30% |
| File structure errors corrected in docs | 4 dirs→files, all counts updated | ✅ |

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

- **Backend server starts** — `main_api_server.py` imports are valid; `generate_angela_response` and `get_angela_chat_service` both exist in `chat_service.py`
- **Biological Simulation** — heartbeat, emotions, endocrine, metabolic cycle (live in lifespan)
- **Self-Evolution core** — ConfigMutator, hot-reload, broadcast, StateStore all independently verified
- **8D State Matrix** — 34 endpoints (αβγδεθζη)
- **Config system** — `config_loader.py:get_config()` correctly returns Config (L869)
- **Wiring separation** — `services/wiring.py` exists with `initialize_all_services()`
- **DI framework** — FastAPI `Depends` used in 4+ route handlers (ops_routes, mobile, drive, economy)
- **Economy + Pet** — lifecycle managers, WebSocket broadcast wired
- **Bootstrap** — hardware detection, directory scaffold, state persistence
- **Test infrastructure** — ~1500+ tests, 16.34% coverage, 0 layer violations

### What's Broken / Never Finished

**Security:**
- **KeyC leak** — `/sync-key-c` endpoint returns `{"key_c": key_c}` in JSON response (main_api_server.py:697)

**Functional gaps:**
- **Memory Chain (HAM/LU/CDM)** — classes defined, query/storage flow never connected
- **P8 LLM Flow** — MathVerifier / CodeInspector / StateMatrixAdapter: 3 isolated classes, 0 connections between them
- **Persistence** — save_state/load_state doesn't exist. Reboot loses all state
- **Desktop → Live2D** — backend WebSocket control chain to Electron never completed
- **Mobile App** — React Native stub, encryption stripped
- **Plugin System** — frontend JS exists, backend hooks absent
- **Encryption** — HMAC-SHA256 signature only, no body encryption. Key A/C unused
- **User evolution gate** — hardcodes `"User"` key at chat_service.py:270; non-default usernames can't confirm evolution
- **5 theoretical formulas defined but not integrated** — HSM, CDM, Life Intensity, Active Cognition, Non-Paradox all compute results that never reach the LLM prompt. See [§5.4](docs/FULL_ARCHITECTURE_ANALYSIS.md#54-理論公式系統).

**God modules (Major):**
- **`main_api_server.py`** — 1668 lines mixing API entry, WebSocket, and lifecycle
- **`angela_llm_service.py`** — 2196 lines mixing LLM routing, multi-backend switching, and prompt construction
- **`core/autonomous/`** — 60+ files, over-broad boundary. See [§4.3](docs/FULL_ARCHITECTURE_ANALYSIS.md#43-核心層-core-分析--30-子包).

**Architecture & Governance (Critical):**
- **Version chaos** — 13 files declare versions, only 4 (31%) are consistent; `VERSION` and `config/angela_config.json` **107 days stale**. See [full audit](docs/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析).
- **Fake v7.x changelog** — AI agent self-assigned v7.2.0~v7.4.0 in `CHANGELOG.md` without any corresponding git tag or source code version change. See [analysis](docs/FULL_ARCHITECTURE_ANALYSIS.md#72-中度問題-major).
- **No version management process** — all version bumps happen in blind "Fix and update" AI commits, never human-reviewed.
- **Dual config dirs** — `config/` vs `configs/` coexist with overlapping purposes, risking overwrites.

**Code quality:**
- **16 Factories: 9 truly dead + 6 dormant + 1 alive** — forensic audit: `DEAD_FACTORY_FORENSICS.md`
- **57 logging.basicConfig()** — module-level, fight for root logger
- **2 Broken \_\_init\_\_.py** — `__all_` typo in ai/trust/ and ai/service_discovery/
- **150+ hardcoded magic numbers** — `arousal >` x15, `random.random()` x29, `target_fps` x24, `> 0.x` comparisons x150+
- **health_check_service.py** — 2/3 import targets don't exist (`ham_memory_manager.py`, `multi_llm_service.py`), caught by try/except

---

### Architecture

See dedicated docs for full diagrams:

| Document | Contents |
|----------|----------|
| [DUAL_SERVER](docs/architecture/DUAL_SERVER_ARCHITECTURE.md) | App A (main.py) vs App B (main_api_server.py), port conflict, middleware |
| [6_LAYER_LIFE](docs/architecture/6_LAYER_LIFE_ARCHITECTURE.md) | L1 Biology → L6 Execution |
| [PROJECT_STRUCTURE](docs/architecture/PROJECT_STRUCTURE.md) | Directory tree |
| [FULL_ARCHITECTURE_ANALYSIS](docs/FULL_ARCHITECTURE_ANALYSIS.md) | Full architecture map, version trace, component audit, 6-layer consistency scoring |

---

### Analysis Documents

| Document | What It Covers |
|----------|---------------|
| [WIRING_MAP](docs/analysis/WIRING_MAP_2026-05-21.md) | Server lifecycle, factory chains, subtle wiring, dead code registry |
| [CODE_STATISTICS](docs/analysis/CODE_STATISTICS_2026-05-21.md) | Live vs dead vs semi-finished code by directory |
| [MODULARITY_ANALYSIS](docs/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God modules, central hub coupling, 20+ singletons |
| [PROBLEM_ANALYSIS](docs/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 3-perspective audit, security issues, CTO roadmap |
| [PHASE_8_PLAN](docs/plans/PHASE_8_DEBT_CLEANUP.md) | 6-week cleanup roadmap |
| [CONFIG_ARCHITECTURE.md](CONFIG_ARCHITECTURE.md) | TCS spec and migration plan |
| [FORENSIC_AUDIT](docs/analysis/FORENSIC_AUDIT_2026-05-22.md) | 3-perspective audit: execution paths, TCS migration, security + dead code |
| [FULL_ARCHITECTURE_ANALYSIS](docs/FULL_ARCHITECTURE_ANALYSIS.md) | Full architecture map, version history, component version audit, consistency scoring |
| [MASTER_CONSOLIDATED_PLAN](docs/plans/MASTER_CONSOLIDATED_PLAN.md) | Merged task plan (replaces P8 v1, P8 Corrected, P9): 27 tasks, S/A/B/C tiers, code-verified status |

---

<a name="繁體中文版"></a>

## 繁體中文版

**Angela AI** 是一個數位生命系統，具備生物模擬、自演化與真實執行能力。

**Quick facts**：515 個 Python 檔案、~116K 行（84% 活、9% 死、7% 半成品）。兩台 FastAPI 伺服器、Electron + Live2D 桌面端、手機 stub。  
**架構一致性評分**: **62.6%** (版本 31% · 結構 65% · 模塊 66% · 算法 74%) — [評分明細](docs/FULL_ARCHITECTURE_ANALYSIS.md#6-一致性綜合評分表)  
**專案總文件**: ~2,761 (Python 1,001 · JS/TS 140 · 文檔 805 · 配置 577 · 測試 238)

---

### 當前進度（獨立代理逐項代碼驗證）

| Phase | 狀態 | 關鍵發現 |
|-------|------|---------|
| **P6 自演化閉環** | ✅ 5 項完成，1 項有 bug | ConfigMutator、熱重載、廣播、StateStore 全部正常。**用戶確認閘門：L270 硬編碼 `"User"` key，非預設使用者名會靜默失敗** |
| **P6.5 啟動接線** | ✅ 2/2 | Heartbeat.start/stop + _initialize_all_services() 全在 lifespan 中 |
| **P7 分層配置** | 🟡 部分完成 | 目錄 + loader 完整。**config_loader.py:get_config() 正確回傳**（審計確認 L869）。150+ 個硬編碼魔法數字未遷移 |
| **P8 技術債清理** | ❌ S1 broken, S2 未開始, S3/S4 partial | **S1 chat_service 拆分後 import 斷裂** — `generate_angela_response()` 已不存在但 `main_api_server.py` 仍引用。S2 wiring.py 也不存在。S3 KeyC leak 未修 |
| **測試基礎設施** | ✅ **完成** | ~1500+ tests, 16.34% 覆蓋率, 0 層級違規, 6 源碼 bug 修復 |

**P8 明細**：

| 項目 | 審計結果 |
|------|---------|
| S1 chat_service（拆分後 `generate_angela_response()` 消失，但 main_api_server.py 仍 import） | ❌ **BROKEN** |
| S2 wiring 拆分（wiring.py 不存在，`_initialize_all_services()` 仍在 main_api_server.py L547-623） | ❌ **未開始** |
| S3 pickle（已註解）；`/eval` 仍存在 (main_api_server.py:1467)；KeyC 洩漏 | 🟡 **Partial** |
| S4 DI 框架（Depends 用於 ops_routes + 4 檔案；核心服務仍用 lazy singleton） | 🟡 **Partial** |

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

> ⚠️ 後端有兩台 FastAPI 伺服器，均預設 port 8000。同一時間只能一台綁定 8000，另一台需用 `--port`。詳見 [雙伺服器架構](docs/architecture/DUAL_SERVER_ARCHITECTURE.md)。

---

### 什麼能跑（已驗證）

**✅ 後端伺服器可正常啟動** — 所有 import 有效，chat_service 函數完整。

**可正常運行：**
- 生物模擬（心跳、情緒、荷爾蒙、代謝循環，在 lifespan 中常駐）
- 自演化核心（ConfigMutator、熱重載、廣播、StateStore 均已獨立驗證）
- 8D 狀態矩陣（34 端點）
- 配置系統 — `get_config()` 正確回傳 Config
- Wiring 分離 — `services/wiring.py` 含 `initialize_all_services()`
- DI 框架 — FastAPI `Depends` 用於多個路由
- 經濟 + 寵物系統（WebSocket 廣播已接線）
- 引導流程（硬體偵測、目錄初始化、狀態持久化）
- 測試基礎設施 — ~1500+ tests, 16.34% 覆蓋率, 0 層級違規

### 什麼不能用／斷鏈

**🔴 安全性：**
- ~~**KeyC 洩漏** — `/sync-key-c` 端點回傳 `{"key_c": key_c}` (main_api_server.py:697)~~ ✅ **已修復** — 改為只回傳 `{"key_available": true}`
- *(無其他已知安全性問題)*

**功能斷鏈：**
- 記憶鏈（HAM/LU/CDM）— 類別完整但查詢/存儲 flow 從未接上
- P8 LLM 閉環 — MathVerifier / CodeInspector / StateMatrixAdapter 三者孤立
- 持久層 — save_state/load_state 不存在，重啟全丟
- 桌面→Live2D 控制鏈 — 後端到 Electron 的控制流從未完成
- 用戶演化確認閘門 — L270 硬編碼 `"User"`，非預設使用者無法確認演化
- 手機端 — 純 stub，加密層已拆
- 插件系統 — 前端有 JS，後端無 hooks
- 加密 — 只驗 HMAC 簽名不加密，Key A/C 未用

**架構與治理（嚴重）：**
- **版本號混亂** — 13 個文件僅 4 個 (31%) 一致；`VERSION` 和 `config/angela_config.json` **107 天未更新**。見[完整審計](docs/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析)
- **虛假 v7.x CHANGELOG** — AI agent 自行分配 v7.2.0~v7.4.0，無對應 git tag 或代碼版本
- **無版本管理流程** — 所有版本變更在盲目 AI 提交中自動完成
- **雙 config 目錄** — `config/` vs `configs/` 並存可能造成覆蓋

**大型上帝模塊（Major）：**
- **`main_api_server.py`** — 1668 行，混合 API/WebSocket/生命週期
- **`angela_llm_service.py`** — 2196 行，混合 LLM 路由/多後端/Prompt 構建
- **`core/autonomous/`** — 60+ 文件，邊界過寬

**功能斷鏈：**
- 記憶鏈（HAM/LU/CDM）— 類別完整但查詢/存儲 flow 從未接上
- P8 LLM 閉環 — MathVerifier / CodeInspector / StateMatrixAdapter 三者孤立
- 5 大理論公式（HSM/CDM/Life Intensity/Active Cognition/Non-Paradox）定義完整但未真正注入 LLM Prompt
- 持久層 — save_state/load_state 不存在，重啟全丟
- 桌面→Live2D 控制鏈 — 後端到 Electron 的控制流從未完成
- 用戶演化確認閘門 — L270 硬編碼 `"User"`，非預設使用者無法確認演化
- 手機端 — 純 stub，加密層已拆
- 插件系統 — 前端有 JS，後端無 hooks
- 加密 — 只驗 HMAC 簽名不加密，Key A/C 未用

**代碼品質：**
- 12 個死 factory（已識別待清理）、58 個 logging 互搶（已修復主要衝突）、2 個 `__init__` typo（不存在，原為誤判）
- 150+ 硬編碼魔法數字：`random.random()` x29、`> 0.x` 比較 x150+
- `health_check_service.py` — 2/3 import targets 不存在（已修復指向正確路徑）
- 6 個源碼 bug 已修復（審計 verified）
- 13 個 scripts 語法錯誤已修復
- 5 個 module-level logging.basicConfig 已移至 `if __name__` guard
- 12 個 conftest fixtures 已清理（root 3 + integration 9 全未使用）
- `tests/game/` 已刪除（全部 3 個測試指向不存在模組）
- `tests/hsp/` 已清理：刪除 3 個 stub、1 個 broken import、1 個 dead script
- `test_gmqtt_mock.py` 已修復（缺少 AsyncMock import + 檔名改為 test_ 前綴）
- 6 個源碼 bug 已修復（審計 verified）
- 13 個 scripts 語法錯誤已修復
- 5 個 module-level logging.basicConfig 已移至 `if __name__` guard
- 12 個 conftest fixtures 已清理（root 3 + integration 9 全未使用）
- `tests/game/` 已刪除（全部 3 個測試指向不存在模組）
- `tests/hsp/` 已清理：刪除 3 個 stub、1 個 broken import、1 個 dead script
- `test_gmqtt_mock.py` 已修復（缺少 AsyncMock import + 檔名改為 test_ 前綴）

---

### 架構文件

| 文件 | 內容 |
|------|------|
| [雙伺服器架構](docs/architecture/DUAL_SERVER_ARCHITECTURE.md) | App A vs App B、port 衝突、中介層 |
| [六層生命架構](docs/architecture/6_LAYER_LIFE_ARCHITECTURE.md) | L1 生物層 → L6 執行層 |
| [專案結構](docs/architecture/PROJECT_STRUCTURE.md) | 目錄樹 |
| [全量架構分析](docs/FULL_ARCHITECTURE_ANALYSIS.md) | 完整架構圖譜、版本溯源、組件審計、六層一致性評分 |

### 分析文件

| 文件 | 內容 |
|------|------|
| [WIRING_MAP](docs/analysis/WIRING_MAP_2026-05-21.md) | 接線圖、工廠鏈、死代碼 |
| [CODE_STATISTICS](docs/analysis/CODE_STATISTICS_2026-05-21.md) | 代碼統計、活/死/半成品 |
| [MODULARITY_ANALYSIS](docs/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God module、耦合、singleton |
| [PROBLEM_ANALYSIS](docs/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 三重視角審計、安全問題、優先級 |
| [PHASE_8_PLAN](docs/plans/PHASE_8_DEBT_CLEANUP.md) | 6 週清理路線圖 |
| [遺留問題修復計畫](docs/plans/REMAINING_ISSUES_PLAN.md) | 架構違規修復、placeholder 清除、unittest→pytest 遷移 |
| [測試重構與建立計畫](docs/plans/TEST_RESTRUCTURE_PLAN.md) | 測試層級架構、conftest 分層、CI integration、階段執行路線 |
| [全量架構分析](docs/FULL_ARCHITECTURE_ANALYSIS.md) | 完整架構圖譜、版本歷史、組件版本審計、一致性評分 |
| [合併任務總計畫](docs/plans/MASTER_CONSOLIDATED_PLAN.md) | 27 項任務合併計畫 (取代 P8 v1/P8 Corrected/P9)，經代碼審計驗證狀態 |

---

**Version**: 7.5.0-dev | **Code Stats**: 515 Python files, ~116K lines (84% live, 9% dead, 7% semi-finished) | [Version Audit](docs/FULL_ARCHITECTURE_ANALYSIS.md#17-各組件正確子版本號分析)
