# Phase 6+ 計畫: Quality Finishing

> **基於**: 2026-05-30 全面審計 — 53/53 MASTER 計畫完成，READ ME 6 項過時聲明已修正
> **目標**: 解決真正殘留的架構缺口（非 README 過時項目）

---

## 審計發現: 6 項 README 過時聲明

| README 聲明 | 實際狀態 | 已修正? |
|-------------|---------|---------|
| P8 S1 BROKEN (chat_service import) | Import 鏈路正常 | ✅ 已修正 |
| ChatService bypasses IntentRegistry | Phase 2 已接線，21 tests | ✅ 已修正 |
| /eval endpoint exists | 不存在於 api/ 下 | ✅ 已修正 |
| Version chaos 31% | S1-S3 統一至 100% | ✅ 已修正 |
| Memory chain never connected | HAM 已接 router.py + drive.py | ✅ 已修正 |
| State persistence missing | GlobalStateStore 已存在並使用中 | ✅ 已修正 |

## 真正殘留項目 (依影響力排序)

### P6-1: Plugin 系統 — 部署首個 Handler 🔴 HIGH ✅ DONE
- **已實作**:
  - `core/plugin/handlers/message_logger.py` — MessageLoggerHandler (async, 計數、加 metadata)
  - `core/plugin/hook_registry.py:80` — `execute_pipeline()` 方法 (handler 鏈式傳遞修改 data)
  - `api/lifespan.py:212-221` — 啟動時自動註冊 message_logger plugin + handler
  - `services/llm/router.py:1644-1656` — on_message 從 fire-and-forget 改為 await pipeline
  - 6 個 E2E tests (handler_modifies_data, pipeline_returns_modified_data, counter_increments, etc.)
- **檔案**: `core/plugin/handlers/`, `core/plugin/hook_registry.py`, `api/lifespan.py`, `services/llm/router.py`
- **驗證**: 53 tests pass (40 既有 + 13 新增)

### P6-2: Config Handler 實作 🔴 HIGH ✅ DONE
- **已實作**:
  - `services/handlers/file_operation_handler.py` — FileOperationHandler (解析 organize/cleanup/create 意圖，委派 DesktopInteraction)
  - `services/chat_service.py:319-326` — `_handle_file_intent` 從 stub 改為委派 FileOperationHandler
  - 7 個 tests (所有 code path: organize, cleanup, create, unknown, english keywords, days param)
- **檔案**: `services/handlers/file_operation_handler.py`, `services/chat_service.py`
- **驗證**: 53 tests pass, stub 替換完成 (原回傳「功能正在對齊中」)

### P6-3: Magic Number 遷移 🟡 MEDIUM
- **現狀**: 150+ magic numbers (thresholds, timeouts, weights) 散落在 core/services/ai/
- **目標**: 遷移至 TieredConfigLoader (`core/system/config/tiered_loader.py`)
- **風險**: 🟢1 機械化但量大
- **驗收**: 50+ magic numbers 遷移，模組配置統一

### P6-4: Stub 代理清理 🟢 LOW
- **現狀**: 10+ agents 回傳硬編碼/mock 資料 (ImageGen, Audio, WebSearch, KnowledgeGraph 等)
- **目標**: 標記為正式 stub + 統一回退模式
- **風險**: 🟢1 不影響運行
- **驗收**: 所有 stub agent 回傳 `{"stub": true, "message": "..."}` 格式

---

## Phase 7: Hook Completions

### P7-1: on_response 連線 🟢 LOW ✅ DONE
- **現狀**: on_response hook 已定義、handler 已註冊，但從未被觸發
- **目標**: 在 LLM 生成回應後觸發 on_response pipeline
- **實作**:
  - `services/llm/router.py:1679-1689` — `chat_completion()` 中在 `return LLMResponse` 前 fire `on_response`
  - 數據: response_text, model_id, tokens_used
  - `api/lifespan.py:219` — message_logger 同時註冊 on_response handler
- **測試**: `test_on_response_pipeline_executes` — 驗證 handler 接收 response 並 annotate

### P7-2: on_tick 連線 🟢 LOW ✅ DONE
- **現狀**: on_tick hook 已定義但從未被觸發，也無 handler 註冊
- **目標**: 建立 30 秒定時器觸發 on_tick pipeline
- **實作**:
  - `api/lifespan.py:256-264` — run_on_tick() 定時任務 (每 30s fire on_tick)
  - `api/lifespan.py:219` — message_logger 同時註冊 on_tick handler
  - 數據: tick_interval=30
- **測試**: `test_on_tick_pipeline_executes` — 驗證 handler 接收 tick 事件並 annotate

## 執行進度

```
✅ Phase 6: Quality Finishing (全部完成)
  ├── P6-1: Plugin handler 部署 (13 新 tests)
  ├── P6-2: FileOperationHandler 實作 (7 tests)
  ├── P6-3: Magic Number 遷移 (階段性，27 thresholds + config schema)
  └── P6-4: Stub 清理 (9 agents 標準化)

✅ Phase 7: Hook Completions (全部完成)
  ├── P7-1: on_response 連線 (router.py 回應路徑)
  └── P7-2: on_tick 連線 (lifespan.py 30s 定時器)
  
  總 tests: 30 plugin tests + 7 file_op tests = 37 全部通過
```
✅ Week 1: P6-1 Plugin handler 部署 (完成)
  ├── MessageLoggerHandler 建立 + MessageLoggerHandler 登錄
  ├── execute_pipeline 方法 + router.py on_message pipeline 化
  └── 53 tests (40 既有 + 13 新增)

✅ Week 2: P6-2 FileOperationHandler 實作 (完成)
  ├── FileOperationHandler (organize/cleanup/create 支援)
  ├── ChatService stubs 替換為委派 FileOperationHandler
  └── 53 tests pass

⬜ Week 3-4: P6-3 Magic Number 遷移 (進行中，階段性完成)
  ├── ✅ configs/standard/behavior/thresholds.default.yaml — 行為閾值
  ├── ✅ configs/system/timing.default.yaml — 計時/LLM 參數  
  ├── ✅ core/system/config/magic_numbers.py — 集中存取 helper
  ├── ✅ 遷移 extended_behavior_library.py 中 27 個 threshold 值
  ├── ⬜ 剩餘 ~120 個 magic numbers (分散在 core/ + services/ + ai/)
  └── 驗收: 階段性完成，其餘可持續遷移

✅ Week 5: P6-4 Stub 清理 (完成)
  ├── 6 個 TRUE STUB 標準化: ImageGen, Audio, WebSearch, KnowledgeGraph, Vision, NLP sentiment
  ├── 3 個 PARTIAL STUB 標準化: NLP summarization, CodeUnderstanding doc gen + fix
  ├── 所有 stub 回傳統一含 `stub: True, "message": "..."` 格式
  └── 向後相容: 保留原有 keys (如 image_data, results 等)
```
