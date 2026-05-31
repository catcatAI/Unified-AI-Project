# Master Finalization Plan — 0 剩餘任務目標

> **基於**: 2026-05-30 全面審計 (43 個 stub 位置、57 個 magic number 檔案、4 個孤立服務、3 個缺失 handler)
> **目標**: 系統性消除所有已知缺口，達到可交付狀態
> **進度追蹤**: 更新本檔 `✅` / `⬜` 標記

---

## Phase 8: Quick Wins (高衝擊、低風險)

### P8-1: 缺失 Handler 實作 🔴 HIGH

#### P8-1a: GoogleDriveHandler ✅
- **檔案**: `services/handlers/google_drive_handler.py`
- **模式**: 同 P6-2 FileOperationHandler → 委派 `integrations.google_drive_service.GoogleDriveService`
- **驗收**: ChatService 可呼叫 handler.handle("列出雲端", "google_drive") 並收到回應

#### P8-1b: WebSearchHandler ✅
- **檔案**: `services/handlers/web_search_handler.py`
- **模式**: 同 FileOperationHandler → 委派 `core.tools.web_search_tool` 或現有搜尋工具
- **驗收**: Handler 可接收搜尋意圖並回覆

#### P8-1c: LearningHandler ✅
- **檔案**: `services/handlers/learning_handler.py`
- **模式**: 接收 "教你/學習" 意圖 → 觸發 `ai.learning` 或 anchor learning 流程
- **驗收**: 學習意圖觸發對應流程

#### P8-1d: llm_manage handler 欄位修復 ✅
- **檔案**: `config/angela_core.yaml` — 為 `llm_manage` 加上 `handler: "LLMManageHandler"`
- **檔案**: `services/handlers/llm_manage_handler.py` — 包裝 ChatService._handle_llm_manage_intent
- **驗收**: YAML 所有 intent 都有 handler 欄位

### P8-2: 孤立服務連線 🟡 MEDIUM

#### P8-2a: 決定 4 個 FULLY ORPHANED SERVICE 命運
- `AIEditorService` (services/ai_editor.py)
- `BrainBridgeService` (services/brain_bridge_service.py)
- `OSContextService` (services/os_context_service.py)
- `AtlassianCLIBridge` (services/atlassian_api.py)

**策略**: 每個服務評估：
  1. 有實際價值？→ 加入 lifespan.py 啟動
  2. 沒價值？→ 標註 `@deprecated` + 加入清理排程

**驗收**: 所有 orphaned service 有明確狀態（wired / deprecated）

#### P8-2b: 清理 deprecated `agents/` 套件
- 目錄: `agents/` (legacy 4 檔 + examples 1 檔)
- **策略**: 確認真無引用後，加 `DEPRECATED` header + 排入移除計畫

### P8-3: NotImplementedError 清理 🟡 MEDIUM

| 位置 | 方法 | 策略 |
|------|------|------|
| `core/desktop/tray_manager.py` (4 方法) | `raise NotImplementedError` | 改為 stub return `{"stub": True}` |
| `core/allocation/policy.py` (2 方法) | `raise NotImplementedError` | 改為 stub return 或 log warning |
| `core/ripple/node.py` (1 方法) | `raise NotImplementedError` | 同上 |
| `core/error/error_handler.py` (1 方法) | `raise NotImplementedError` | 同上 |
| `ai/meta_formulas/meta_formula.py` | `raise NotImplementedError` | 同上 |

**驗收**: 0 個 `raise NotImplementedError` 留在非抽象類別的 hot path

---

## Phase 9: Structural 改善

### P9-1: ModuleManager 擴展 🟡 MEDIUM

**新模組候選 (需 migration + tests)**:

| 優先 | 服務 | 現狀 | Migration 策略 |
|------|------|------|---------------|
| P1 | `ChatService` | lifespan lazy init | 建立 `modules/chat_service/` + `module.yaml` |
| P2 | `AngelaLLMService` | lifespan lazy init | 建立 `modules/llm_service/` + `module.yaml` |
| P3 | `HotReloadService` | wiring.py 建立 | 建立 `modules/hot_reload/` + `module.yaml` |
| P4 | `MathVerifier` | 手動 import | 建立 `modules/math_verifier/` |
| P5 | `ResourceAwarenessService` | 手動 import | 建立 `modules/resource_awareness/` |

**驗收**: 每個新 module 有 `module.yaml` + `__init__.py` (init/start/stop) + tests

### P9-2: Stub 代理大量實作 🟢 LOW (43 位置)

依難度分級：
- **EASY** (改為 return `{"stub": True}`): ~15 位置 (已標準化)
- **MEDIUM** (加入基本邏輯): ~20 位置 (如 truncation summarization → 基本 LLM 摘要)
- **HARD** (需要新整合): ~8 位置 (如 ImageGen → 需 Stable Diffusion API)

**策略**: 非 hot path 的 stub 維持標準化格式，hot path 的優先實作

### P9-3: Magic Number 續遷 🟢 LOW (~57 檔案)

採用批量策略：
1. 已建立 `magic_numbers.py` + config YAML skeleton (P6-3)
2. 分批遷移 (依檔案重要性排序)
3. 優先遷移 hot path 檔案：`heartbeat.py`, `action_executor.py`, `feedback_processor.py`
4. 每批 10 個檔案，目標合計遷移 200+ 數字

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
Week 1-2: Phase 8 (Quick Wins)
  P8-1: 4 handlers (GoogleDrive, WebSearch, Learning, LLMManage)
  P8-2: Orphaned service 評估 + deprecated 清理
  P8-3: NotImplementedError → stub return

Week 3-4: Phase 9 (Structural)
  P9-1: 2 new ModuleManager modules (ChatService, LLMService)
  P9-2: Stub 批量實作 (top 20 EASY items)
  P9-3: Magic number 續遷 (top 10 files, ~100 numbers)

Week 5: Phase 10 (Docs + Tests)
  P10-1: Core smoke tests
  P10-2: Architecture overview + service catalog
```

---

## 進度

```
⬜ Phase 8: Quick Wins
  ├── ⬜ P8-1a: GoogleDriveHandler
  ├── ⬜ P8-1b: WebSearchHandler
  ├── ⬜ P8-1c: LearningHandler
  ├── ⬜ P8-1d: llm_manage handler 修復
  ├── ⬜ P8-2a: Orphaned service 評估
  ├── ⬜ P8-2b: Deprecated agents 清理
  └── ⬜ P8-3: NotImplementedError 清理

⬜ Phase 9: Structural 改善
  ├── ⬜ P9-1: ModuleManager 擴展 (ChatService + LLMService)
  ├── ⬜ P9-2: Stub 大量實作
  └── ⬜ P9-3: Magic number 續遷

⬜ Phase 10: Docs & Tests
  ├── ⬜ P10-1: 基礎測試覆蓋
  └── ⬜ P10-2: 文件補全
```
