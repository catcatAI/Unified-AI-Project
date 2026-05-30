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

### P6-1: Plugin 系統 — 部署首個 Handler 🔴 HIGH
- **現狀**: C3 Phase 1-4 已完成基礎設施 (HookRegistry, PluginManager, CRUD API, hot-reload, sandbox)，但 0 個 handler 註冊
- **目標**: 註冊 `on_message` handler，實現 plugin 可攔截/修改訊息
- **檔案**: `core/plugin/plugin_manager.py`, `api/v1/endpoints/plugins.py`
- **風險**: 🟡2 耦合度低，獨立模組
- **驗收**: 1 plugin handler 部署，E2E 測試通過

### P6-2: Config Handler 實作 🔴 HIGH
- **現狀**: `angela_core.yaml:131-257` 定義 5 個 handler (FileOperation, GoogleDrive, WebSearch, Learning) 但 0 個有對應代碼
- **目標**: 實作 FileOperationHandler (最高優先，ChatService 已 reference)
- **檔案**: (新建) `services/handlers/file_operation_handler.py`
- **風險**: 🟡2
- **驗收**: FileOperationHandler init + process 方法可被 ChatService 呼叫

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

## 執行路線

```
Week 1: P6-1 Plugin handler 部署
  ├── 註冊首個 on_message handler
  ├── E2E test (plugin 攔截 → 修改 response)
  └── 驗收: plugin 流程完整可測

Week 2: P6-2 FileOperationHandler 實作
  ├── 實作 init/process 方法
  ├── ChatService 接線
  └── 驗收: 可執行檔案操作

Week 3-4: P6-3 Magic Number 遷移
  ├── 掃描 core/ + services/ 高頻 magic numbers
  ├── 建立配置 schema
  └── 驗收: 50+ numbers 中央化

Week 5: P6-4 Stub 清理 (可選)
  ├── 10+ agents 標準化 stub 格式
  └── 驗收: 統一回傳格式
```
