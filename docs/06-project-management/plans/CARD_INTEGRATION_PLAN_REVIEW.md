# Card Integration Plan Review

**Date**: 2026-05-30  
**審計目標**: `ANGELA_CARD_INTEGRATION_PLAN.md` v1（原始版本）  
**對應 v2**: `ANGELA_CARD_INTEGRATION_PLAN.md`（重寫版本，基於 ModuleManager）  

---

## v1 審計結果：25 問題

### HIGH — 8 個

| # | Phase | Issue | Severity | v2 解決狀況 |
|---|-------|-------|----------|-----------|
| 0.1 | 0 | IntentRegistry never registered as service; learning loop writes to black hole | HIGH | ✅ ModuleManager singleton |
| 1.1 | 1 | Sync `pipeline.process()` called inside async method blocks event loop | HIGH | ✅ ModuleManager.call() 自動處理 |
| 1.2 | 1 | Fresh `IntentRegistry()` created per message — patterns never persist | HIGH | ✅ ModuleManager 提供 singleton |
| 2.1 | 2 | `asyncio.get_running_loop()` in sync method crashes in CLI mode | HIGH | ✅ Lifecycle.call() 自動判斷 sync/async |
| 2.2 | 2 | Phase 2 makes Stage 3 async but never provides `async process()` | HIGH | ✅ Interface schema 強制一致 |
| 3.1 | 3 | `text[:50]` raw fragment as keyword — learning writes garbage | HIGH | ✅ Event hook 提供結構化 keyword |
| 4.1 | 4 | `pipeline.process()` blocks event loop inside async TaskManager | HIGH | ✅ ModuleManager 處理 thread safety |
| 4.2 | 4 | `datetime.utcnow()` deprecated in Python 3.12+ | HIGH | ✅ 已在設計中修正 |

### MEDIUM — 12 個

| # | Phase | Issue | Severity | v2 解決狀況 |
|---|-------|-------|----------|-----------|
| 0.2 | 0 | CardRegistry registration fragmented across lifecycle stages | MEDIUM | ✅ ModuleManager 統一管理 |
| 0.3 | 0 | CLI cards never registered with ServiceRegistry | MEDIUM | ✅ ModuleManager 可 CLI/API 共用 |
| 1.3 | 1 | Race: local CardRegistry lost if pipeline fails | MEDIUM | ✅ ModuleManager 管理 registry state |
| 1.4 | 1 | `HAMMemoryManager()` created without config context | MEDIUM | ✅ ModuleManager 提供已初始化的依賴 |
| 1.5 | 1 | Keyword-dependent detection misses variant phrasing | MEDIUM | ✅ IntentRegistry.detect() YAML-based |
| 2.3 | 2 | LLMBridge redundantly calls `get_llm_service()` per conflict | MEDIUM | ✅ ModuleManager 提供 singleton |
| 2.4 | 2 | `generate_text("")` indistinguishable from LLM failure | MEDIUM | ⚠️ 待 ModuleManager 的 error event 補 sentinel 機制 |
| 3.2 | 3 | Learned patterns never feed back into IntentRegistry | MEDIUM | ✅ Event hook 雙向同步 |
| 3.3 | 3 | Hardcoded `latency_ms: 0` corrupts route learning stats | MEDIUM | ✅ Event hook 提供真實 elapsed |
| 4.3 | 4 | Contradiction: lifespan.py vs wiring.py init location | MEDIUM | ✅ 只有一個入口：ModuleManager.start() |
| 4.4 | 4 | `/cards/import` has no auth, rate limiting, or size validation | MEDIUM | ⚠️ 待 Phase 4 實作時補上 |
| 4.5 | 4 | TaskProgress stuck "running" on early exceptions | MEDIUM | ✅ ModuleManager events 處理錯誤狀態 |
| X.1 | All | Bare `except Exception: pass` silences errors; false success | MEDIUM | ✅ ModuleManager events 追蹤每個失敗 |

### LOW — 7 個

| # | Issue | v2 解決狀況 |
|---|-------|-----------|
| 1.6 | YAML handler `"DocumentBuilder"` misleads maintainers | ✅ 改用 IntentRegistry.detect()，不再依賴 handler 字串 |
| 2.5 | HAM query timeout (5s) too short for cold starts | ✅ config 可覆蓋（angela_core.yaml） |
| 2.6 | Two PersonalityManager instances may conflict | ✅ ModuleManager singleton |
| 3.4 | `get_learned_stats()` written but never read | ⚠️ 留待 Phase 4 API endpoint |
| 4.6 | API uses raw `Dict` instead of Pydantic model | ⚠️ 待 Phase 4 實作時補上 |
| 0.4 | No explicit Phase 0 in plan structure | ✅ v2 已加 Phase 0 |
| X.2 | All line references verified accurate | ✅ |

---

## 根因分析

v1 的 8/8 HIGH 問題追溯到同一個架構缺陷：**沒有中央接線基礎設施**。

v2 透過 ModuleManager 解決：不再手動猜 singleton、手動改 router/lifespan/wiring、手動管 lifecycle。

---

## 殘留注意事項（v2 計劃尚未完全覆蓋）

即使 v2 解決了大部分問題，以下 3 項需要在實作階段特別注意：

| # | 項目 | 說明 |
|---|------|------|
| R1 | `asyncio.to_thread()` pickle 限制 | `CardImportPipeline` 可能不可 pickle。ModuleManager 需用 `thread_safe: false` 標記或在 event loop 直接執行 |
| R2 | Modules 目錄定位 | module 的 `from modules.xxx import init` 需要 `modules/` 在 `sys.path` 中。需確認 `apps/backend/src/` 已在 path 中 |
| R3 | Circular dep 動態偵測 | llm_module ↔ card_pipeline 的循環依賴已在設計中避免，但 hotplug 時需重新檢查 |
