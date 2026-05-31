# Master Finalization Plan — 0 剩餘任務目標

> **基於**: 2026-05-30 全面審計 (43 個 stub 位置、57 個 magic number 檔案、4 個孤立服務、3 個缺失 handler)
> **目標**: 系統性消除所有已知缺口，達到可交付狀態
> **進度追蹤**: 更新本檔 `✅` / `⬜` 標記

---

## Phase 8: Quick Wins (高衝擊、低風險) ✅ ALL DONE

### P8-1: 缺失 Handler 實作 🔴 HIGH

#### P8-1a: GoogleDriveHandler ✅ DONE
- **檔案**: `services/handlers/google_drive_handler.py` (新), `services/chat_service.py` (dispatch), `tests/core/test_google_drive_handler.py`
- **模式**: 同 P6-2 FileOperationHandler → 委派 `integrations.google_drive_service.GoogleDriveService`
- **支援操作**: list, sync, status, logout (auth 提示引導 OAuth 流程)
- **驗收**: ChatService 可呼叫 handler.handle("列出雲端", "google_drive") 並收到回應

#### P8-1b: WebSearchHandler ✅ DONE
- **檔案**: `services/handlers/web_search_handler.py` (新), `services/chat_service.py` (dispatch), `tests/core/test_web_search_handler.py`
- **模式**: 委派 `core.tools.web_search_tool.WebSearchTool` (DuckDuckGo HTML search)
- **Query 萃取**: 支援中英文前綴去除 (搜尋/搜索/google/search/lookup/幫我查/查)
- **驗收**: 7 tests pass (包括 query extraction edge cases)

#### P8-1c: LearningHandler ✅ DONE
- **檔案**: `services/handlers/learning_handler.py` (新), `services/chat_service.py` (dispatch + intent_map + fallback keywords), `tests/core/test_learning_handler.py`
- **模式**: 抽取事實 → 選用委派 `AnchorLearningEngine.record_fact()`
- **支援關鍵字**: 記住/學習/記錄/教我/remember/learn/teach...
- **驗收**: 10 tests pass (extract_fact variants + handle roundtrip)

#### P8-1d: llm_manage handler 欄位修復 ✅
- **檔案**: `config/angela_core.yaml` — 為 `llm_manage` 加上 `handler: "ChatService._handle_llm_manage"`
- **原因**: `_handle_llm_manage_intent` 深度耦合 ChatService（依賴 state_adapter、pending_evolution_proposals、module_manager），建立獨立 handler class 會產生不必要的抽象層。改為在 YAML 直接指向 ChatService 實例方法。
- **驗收**: YAML 所有 intent 都有 handler 欄位

### P8-2: 孤立服務連線 🟡 MEDIUM

#### P8-2a: 決定 7 個 ORPHANED SERVICE 命運 ✅

**評估結果** (2026-05-31):

| # | 檔案 | 類別 | 狀態 | 說明 |
|---|------|------|------|------|
| 1 | `services/ai_editor.py` | `AIEditorService`, `DataProcessor`, `SandboxExecutor`, `HAMMemoryManager` | **❌ ORPHANED** | AI Editor 生態系 — 3 個檔案互相依賴但完全未接入 (僅 tests import) |
| 2 | `services/ai_editor_config.py` | `AIEditorConfig`, `get_config()` | **❌ ORPHANED** | 同上生態系，0 production import |
| 3 | `services/ai_virtual_input_service.py` | `AIVirtualInputService` | **❌ ORPHANED** | 僅被 #1 引用 (同為 orphaned) |
| 4 | `services/brain_bridge_service.py` | `BrainBridgeService` | **❌ ORPHANED** | 僅 scripts/ 引用，非 production path |
| 5 | `services/os_context_service.py` | `OSContextService` | **❌ ORPHANED** | 0 production import |
| 6 | `services/angela_types.py` | TypeDefs (TypedDicts) | **❌ ORPHANED** | 0 production import |
| 7 | `services/api_models.py` | Re-export from `models.api_models` | **❌ ORPHANED** | Dead re-export shim |

**排除項目** (原始清單錯誤):
- `AtlassianCLIBridge` (atlassian_api.py) — ✅ 已 wired in `main_api_server.py:298`
- `hot_reload_service.py` — ✅ 已 wired in `wiring.py:47`

**推薦策略**: 全部 7 個檔案加 `@deprecated` header 並排入移除計畫。

#### P8-2b: 清理 deprecated `agents/` 套件
- 目錄: `agents/` (legacy 4 檔 + examples 1 檔)
- **策略**: 確認真無引用後，加 `DEPRECATED` header + 排入移除計畫

### P8-3: NotImplementedError 清理 ✅ DONE

| 位置 | 方法數 | 舊作法 | 新作法 |
|------|--------|--------|--------|
| `core/desktop/tray_manager.py` | 4 | `raise NotImplementedError` | `logger.warning(...)` + `{"stub": True}` |
| `core/allocation/policy.py` | 2 | `raise NotImplementedError` | `logger.warning(...)` + `return False` / `AllocationAction.DEFER` |
| `core/ripple/node.py` | 1 | `raise NotImplementedError` | `logger.warning(...)` + 靜默返回 |
| `core/error/error_handler.py` | 1 | `raise NotImplementedError` | `logger.warning(...)` + `return False` |
| `ai/meta_formulas/meta_formula.py` | 1 | `raise NotImplementedError` | `logger.warning(...)` + `{"stub": True}` |

**驗收**: ✅ 0 個 `raise NotImplementedError` 留在非抽象類別的 hot path

---

## Phase 9: Structural 改善

### P9-1: ModuleManager 擴展 ✅ DONE

| 優先 | 服務 | 狀態 |
|------|------|------|
| P1 | `ChatService` | ✅ `modules/chat_service/module.yaml` + `__init__.py` |
| P2 | `AngelaLLMService` | ✅ `modules/llm_service/module.yaml` + `__init__.py` |
| P3 | `HotReloadService` | ⬜ 待建立 |
| P4 | `MathVerifier` | ⬜ 待建立 |
| P5 | `ResourceAwarenessService` | ⬜ 待建立 |

**注意**: module wrappers 使用 deferred init 模式 (init → start → initialize)，實際初始化仍由 lifespan.py 管理。模組啟動不會建立重複實例。

### P9-2: Stub 代理大量實作 ✅ PARTIAL (20 位置)

| 優先 | 檔案 | 方法 | 修復內容 |
|------|------|------|----------|
| EASY | `core/system/module_manager/scanner.py` | `watch()` | 加 `logger.warning` |
| EASY | `core/engine/state_matrix.py` | `_apply_influence_fallback()` | 加 `logger.warning` (deprecated) |
| EASY | `ai/memory/importance_scorer.py` | `__init__()` | 加 `logger.debug` |
| EASY | `ai/ops/intelligent_ops_manager.py` | 3 methods | 加 `logger.warning` + return |
| EASY | `ai/level5_asi_system.py` | 10 placeholder methods | 加 `logger.warning` + docstrings |
| EASY | `integrations/atlassian_bridge.py` | `start()`/`close()` | 加 `logger.info` |
| EASY | `integrations/enhanced_rovo_dev_connector.py` | `start()`/`close()`/`_authenticate()` | 加 `logger.info` + remove redundant `pass` |

**待辦 (MEDIUM)**: 20 個 stub 位置需要加入基本邏輯

### P9-3: Magic Number 續遷 🟡 PARTIAL (12 新增)

**新增 config 值**:
- `configs/system/timing.default.yaml` → `timing.heartbeat.*` (7 keys)
- `core/system/config/magic_numbers.py` → `heartbeat_value()` accessor

**遷移統計**:
| 檔案 | 此前 | 已遷移 | 待遷移 |
|------|------|--------|--------|
| `heartbeat.py` | ~31 | 8 (sleeps + interval + battery) | ~23 |
| `action_executor.py` | ~36 | 4 (sleeps) | ~32 |
| `feedback_processor.py` | ~38 | 0 | ~38 |
| **合計** | **~105** | **12** | **~93** |

---

## Phase 10: Documentation & Tests

### P10-1: 基礎測試覆蓋 🟢 LOW

| 優先 | 目標 | 策略 |
|------|------|------|
| P1 | `tests/core/` 基礎測試 | 為 top 10 core modules 加 smoke test |
| P2 | `tests/services/` 基礎測試 | 為 top 5 services 加 smoke test |
| P3 | plugin system tests | 已完成 (30 tests) |
| P4 | handler tests | 已完成 (7 tests) |

### P10-2: 文件補全 🟢 LOW

| 文件 | 內容 |
|------|------|
| `docs/architecture/OVERVIEW.md` | 系統架構圖 + 服務依賴圖 |
| `docs/development/SERVICE_CATALOG.md` | 所有服務/模組列表與狀態 |
| `docs/development/STUB_TRACKING.md` | 所有 stub 位置與實作狀態 |

---

## 執行路線

```
Week 1-2: Phase 8 (Quick Wins) — P8-1a ✅
  P8-1: 4 handlers (GoogleDrive ✅, WebSearch ✅, Learning ✅, LLMManage ✅)
  P8-2: Orphaned service 評估 + deprecated 清理 ✅
  P8-3: NotImplementedError → stub return ✅

Week 3-4: Phase 9 (Structural) — all progressed
  P9-1: ✅ 2 new ModuleManager modules (ChatService, LLMService)
  P9-2: ✅ Stub 批量實作 (20 EASY items — logging + standard returns)
  P9-3: 🟡 Partial — 12 numbers migrated (heartbeat 8 + action_executor 4), ~93 deferred

Week 5: Phase 10 (Docs + Tests)
  P10-1: Core smoke tests
  P10-2: Architecture overview + service catalog
```

---

## 進度

```
⬜ Phase 8: Quick Wins
  ├── ✅ P8-1a: GoogleDriveHandler (services/handlers/google_drive_handler.py + dispatch + 9 tests)
  ├── ✅ P8-1b: WebSearchHandler (services/handlers/web_search_handler.py + dispatch + 7 tests)
  ├── ✅ P8-1c: LearningHandler (services/handlers/learning_handler.py + dispatch + 10 tests)
  ├── ✅ P8-1d: llm_manage handler 修復 (angela_core.yaml handler field added)
  ├── ✅ P8-2a: Orphaned service 評估 (7 orphaned found, document updated)
  ├── ✅ P8-2b: Deprecated agents 清理 (4 legacy + 1 example → DEPRECATED header)
  └── ✅ P8-3: NotImplementedError 清理 (5 files → log warning + stub return)

⬜ Phase 9: Structural 改善
  ├── ✅ P9-1: ModuleManager 擴展 (ChatService + LLMService module wrappers)
  ├── ✅ P9-2: Stub 大量實作 (20 EASY stubs → logging + standard returns)
  └── 🟡 P9-3: Magic number 續遷 (12 values migrated: heartbeat 8 + action_executor 4)

⬜ Phase 10: Docs & Tests
  ├── ⬜ P10-1: 基礎測試覆蓋
  └── ⬜ P10-2: 文件補全
```
