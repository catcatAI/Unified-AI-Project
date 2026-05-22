<!--
  =============================================================================
  VERSION: 6.5.0-dev
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-05-21
  =============================================================================
-->

# Angela AI v6.5.0-dev — Cross-Platform Digital Life System

[English](#english-version) | [繁體中文](#繁體中文版)

---

<a name="english-version"></a>

## English Version

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()

**Angela AI** is a digital life system with biological simulation, self-evolution, and real execution capabilities.

**Quick facts**: 515 Python files, ~116K lines (84% live, 9% dead, 7% semi-finished). Two FastAPI servers, Electron + Live2D desktop companion, mobile stub.

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
| config_loader.py → TCS redirect | `config_loader.py` — `load_config()` calls TCS (L20-25); **`get_config()` at L52-58 ignores return value → always returns `{}`** | ❌ **BROKEN** |
| `.user.yaml` overlays | rg search: **0 files** in entire configs/ tree | ❌ Missing |
| `.evolved.yaml` overlays | rg search: **1 demo file** (`standard/behavior/demo.evolved.yaml`), 0 production | ❌ Missing |
| Hardcoded thresholds → config | rg search: `arousal >` x15, `random.random()` x29, `target_fps` x24, `if.*>.*0.x` x150+ | ❌ Not done |
| Legacy config deprecated | `angela_core.yaml` (27 sections, 12 DEAD) still primary runtime source | ❌ Still primary |
| ConfigMutator writes `*.evolved.yaml` | `config_mutator.py` L110-136 — correctly maps to evolved paths | ✅ Done |
| DEAD sections cleaned | 12 `# DEAD` sections still in `angela_core.yaml` | ❌ Not cleaned |

**▶ Phase 8 — Tech Debt Cleanup**

| Task | Evidence | Status |
|------|----------|--------|
| S1: Split chat_service | `chat_service.py` now 306 lines (was 1281); BUT `generate_angela_response()` and `get_angela_chat_service()` removed — `main_api_server.py:292,695,1370` and `router.py:175` still import them → **ImportError at server start** | ❌ **BROKEN** |
| S2: Split wiring to independent file | No `wiring.py` exists; `_initialize_all_services()` still embedded in `main_api_server.py` L547-623 | ❌ Not started |
| S3: Security fixes | Pickle commented out (cache_manager.py L156-167); command injection `/eval` endpoint still exists (main_api_server.py L1467); KeyC leak via localhost endpoint | 🟡 Partial |
| S4: DI framework | `Depends` used in 5 route files (atlassian, drive, mobile, ops, economy); all core services still use manual lazy singletons | 🟡 Partial | |

---

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

### What Actually Works (Verified)

**⚠️ Server won't start due to import error** — `main_api_server.py:292` does `from services.chat_service import generate_angela_response, get_angela_chat_service` at module level, but these functions no longer exist in the 306-line rewrite. This is a **top-level import** — the server crashes at import time, before any route is served.

**Code that would work IF the import bug were fixed:**
- **Biological Simulation** — heartbeat, emotions, endocrine, metabolic cycle (live in lifespan)
- **Self-Evolution core** — ConfigMutator, hot-reload, broadcast, StateStore all independently verified
- **8D State Matrix** — 34 endpoints (αβγδεθζη)
- **Economy + Pet** — lifecycle managers, WebSocket broadcast wired
- **Bootstrap** — hardware detection, directory scaffold, state persistence

### What's Broken / Never Finished

**Critical (server won't start):**
- **chat_service.py rewrite broke callers** — `generate_angela_response()` and `get_angela_chat_service()` removed from chat_service.py (306-line rewrite), but still imported by `main_api_server.py:292,695,1370` and `api/router.py:175`. Causes **ImportError on server start**.
- **config_loader.py:get_config() returns {}** — L52-58 ignores `load_config()` return value, always returns empty dict. Every caller of `get_config()` gets no config silently.

**Functional gaps:**
- **Memory Chain (HAM/LU/CDM)** — classes defined, query/storage flow never connected
- **P8 LLM Flow** — MathVerifier / CodeInspector / StateMatrixAdapter: 3 isolated classes, 0 connections between them
- **Persistence** — save_state/load_state doesn't exist. Reboot loses all state
- **Desktop → Live2D** — backend WebSocket control chain to Electron never completed
- **Mobile App** — React Native stub, encryption stripped
- **Plugin System** — frontend JS exists, backend hooks absent
- **Encryption** — HMAC-SHA256 signature only, no body encryption. Key A/C unused
- **User evolution gate** — hardcodes `"User"` key at chat_service.py:270; non-default usernames can't confirm evolution

**Code quality:**
- **16 Factories: 9 truly dead + 6 dormant + 1 alive** — forensic audit: `DEAD_FACTORY_FORENSICS.md`
- **57 logging.basicConfig()** — module-level, fight for root logger
- **2 Broken \_\_init\_\_.py** — `__all_` typo in ai/trust/ and ai/service_discovery/
- **150+ hardcoded magic numbers** — `arousal >` x15, `random.random()` x29, `target_fps` x24, `> 0.x` comparisons x150+

---

### Architecture

See dedicated docs for full diagrams:

| Document | Contents |
|----------|----------|
| [DUAL_SERVER](docs/architecture/DUAL_SERVER_ARCHITECTURE.md) | App A (main.py) vs App B (main_api_server.py), port conflict, middleware |
| [6_LAYER_LIFE](docs/architecture/6_LAYER_LIFE_ARCHITECTURE.md) | L1 Biology → L6 Execution |
| [PROJECT_STRUCTURE](docs/architecture/PROJECT_STRUCTURE.md) | Directory tree |

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

---

<a name="繁體中文版"></a>

## 繁體中文版

**Angela AI** 是一個數位生命系統，具備生物模擬、自演化與真實執行能力。

**Quick facts**：515 個 Python 檔案、~116K 行（84% 活、9% 死、7% 半成品）。兩台 FastAPI 伺服器、Electron + Live2D 桌面端、手機 stub。

---

### 當前進度（獨立代理逐項代碼驗證）

| Phase | 狀態 | 關鍵發現 |
|-------|------|---------|
| **P6 自演化閉環** | ✅ 5 項完成，1 項有 bug | ConfigMutator、熱重載、廣播、StateStore 全部正常。**用戶確認閘門：L270 硬編碼 `"User"` key，非預設使用者名會靜默失敗** |
| **P6.5 啟動接線** | ✅ 2/2 | Heartbeat.start/stop + _initialize_all_services() 全在 lifespan 中 |
| **P7 分層配置** | 🟡 6/11 完成，2 項 BROKEN | 目錄 + loader 完整。**config_loader.py:get_config() 永遠回傳 `{}`**。150+ 個硬編碼魔法數字未遷移 |
| **P8 技術債清理** | 🆕 0 項完成，1 項 BROKEN（使伺服器無法啟動） | 僅計畫，無執行。**chat_service.py 被改寫為 306 行 class 版本，但舊 standalone function 被刪後 caller 未更新 → ImportError** |

**P7 明細**：

| 項目 | 完成 |
|------|------|
| TieredConfigLoader 類別 | ✅ |
| S 層 4 個 .default.yaml | ✅ |
| A 層 6 個 .default.yaml | ✅ |
| M 層 active_mods.default.yaml | ✅ |
| config_loader.py `load_config()` 轉導 TCS | ✅ |
| config_loader.py `get_config()` 正確回傳 | ❌ **BROKEN：忽略回傳值，永遠回傳 `{}`** |
| .user.yaml 覆蓋層（0 檔案） | ❌ |
| .evolved.yaml 覆蓋層（1 demo，0 production） | ❌ |
| 硬編碼遷移：`random.random()` x29、`if>0.x` x150+ | ❌ |
| Legacy config 淘汰：`angela_core.yaml` 仍為主要來源 | ❌ |
| ConfigMutator 寫入 `*.evolved.yaml` | ✅ |
| 12 個 DEAD sections 清理 | ❌ |

**P8 明細**：

| 項目 | 完成 |
|------|------|
| S1 拆分 chat_service（306 行已拆，但舊函數被刪 → ImportError） | ❌ **BROKEN** |
| S2 拆分 wiring 到獨立檔案 | ❌ 未開始 |
| S3 安全修復（pickle 註解掉；/eval 注入端點仍在；KeyC 洩漏） | 🟡 部分 |
| S4 DI 框架（Depends 在 5 個路由檔案，核心服務仍用手動 singleton） | 🟡 部分 | |

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

**⚠️ 伺服器無法啟動** — `main_api_server.py:292` 在 module 層級 import 已不存在的 `generate_angela_response`，伺服器在 import 階段就會 crash。

**如果修好 import bug，以下可正常運行：**
- 生物模擬（心跳、情緒、荷爾蒙、代謝循環，在 lifespan 中常駐）
- 自演化核心（ConfigMutator、熱重載、廣播、StateStore 均已獨立驗證）
- 8D 狀態矩陣（34 端點）
- 經濟 + 寵物系統（WebSocket 廣播已接線）
- 引導流程（硬體偵測、目錄初始化、狀態持久化）

### 什麼不能用／斷鏈

**🔴 伺服器無法啟動（立即要修）：**
- **chat_service.py 改寫後舊函數被刪** — `generate_angela_response()` 和 `get_angela_chat_service()` 已移除，但 `main_api_server.py:292,695,1370` 和 `router.py:175` 還在 import → **ImportError**
- **config_loader.py:get_config() 永遠回傳空 dict** — L52-58 忽略回傳值

**功能斷鏈：**
- 記憶鏈（HAM/LU/CDM）— 類別完整但查詢/存儲 flow 從未接上
- P8 LLM 閉環 — MathVerifier / CodeInspector / StateMatrixAdapter 三者孤立
- 持久層 — save_state/load_state 不存在，重啟全丟
- 桌面→Live2D 控制鏈 — 後端到 Electron 的控制流從未完成
- 用戶演化確認閘門 — L270 硬編碼 `"User"`，非預設使用者無法確認演化
- 手機端 — 純 stub，加密層已拆
- 插件系統 — 前端有 JS，後端無 hooks
- 加密 — 只驗 HMAC 簽名不加密，Key A/C 未用

**代碼品質：**
- 16 個死 factory、58 個 logging 互搶、2 個 `__init__` typo
- 150+ 硬編碼魔法數字：`random.random()` x29、`> 0.x` 比較 x150+

---

### 架構文件

| 文件 | 內容 |
|------|------|
| [雙伺服器架構](docs/architecture/DUAL_SERVER_ARCHITECTURE.md) | App A vs App B、port 衝突、中介層 |
| [六層生命架構](docs/architecture/6_LAYER_LIFE_ARCHITECTURE.md) | L1 生物層 → L6 執行層 |
| [專案結構](docs/architecture/PROJECT_STRUCTURE.md) | 目錄樹 |

### 分析文件

| 文件 | 內容 |
|------|------|
| [WIRING_MAP](docs/analysis/WIRING_MAP_2026-05-21.md) | 接線圖、工廠鏈、死代碼 |
| [CODE_STATISTICS](docs/analysis/CODE_STATISTICS_2026-05-21.md) | 代碼統計、活/死/半成品 |
| [MODULARITY_ANALYSIS](docs/analysis/MODULARITY_ANALYSIS_2026-05-21.md) | God module、耦合、singleton |
| [PROBLEM_ANALYSIS](docs/analysis/PROBLEM_ANALYSIS_2026-05-21.md) | 三重視角審計、安全問題、優先級 |
| [PHASE_8_PLAN](docs/plans/PHASE_8_DEBT_CLEANUP.md) | 6 週清理路線圖 |

---

**Version**: 6.5.0-dev | **Code Stats**: 515 Python files, ~116K lines (84% live, 9% dead, 7% semi-finished)
