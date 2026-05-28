# Angela AI 代碼統計分析

## 總覽

| 項目 | 數量 |
|------|------|
| 後端 Python 檔案 (`apps/backend/src/`) | 515 |
| 後端 Python 行數 | ~116,265 |
| 測試檔案 (`tests/`) | 327 |
| 桌面端 JS 檔案 (`apps/desktop-app/`) | 63 |
| 活代碼（有接線、有呼叫者） | ~98K (84%) |
| 死代碼（無呼叫者、孤立模組、demo） | ~10K (9%) |
| 半成品（類別完整但 flow 斷鏈） | ~8K (7%) |

---

## 1. 後端目錄結構（依檔案數排序）

### 核心系統 — `core/`（~150 檔案）

| 子目錄 | 檔案數 | 活/死 | 說明 |
|--------|--------|-------|------|
| `core/autonomous/` | 50 | ✅ 活 | 生物模擬核心：心跳、情緒、荷爾蒙、觸覺、動作執行 |
| `core/` (根目錄) | 28 | ✅ 活 | 主要管理器、橋接層、反饋迴路 |
| `core/tools/` | 14 | ✅ 活 | 邏輯模型、數學工具、參數提取器 |
| `core/managers/` | 10 | ✅ 活 | 對話管理器、記憶管理器 |
| `core/hsp/` | 10 | ✅ 活 | 高速同步協議、內外橋接 |
| `core/state/` | 10 | ✅ 活 | 狀態管理、維度計算 |
| `core/security/` | 7 | ✅ 活 | 安全控制、審計 |
| `core/hardware/` | 7 | ✅ 活 | 硬體偵測 |
| `core/perception/` | 8 | ✅ 活 | 感知系統 |
| `core/sync/` | 3 | ✅ 活 | 狀態同步 |
| `core/system/` | 10 | ✅ 活 | Phase 6+7：bootstrap、config、evolution、state_store |
| `core/tracing/` | 4 | ✅ 活 | 追蹤介面 |
| `core/art/` | 5 | ✅ 活 | 創造引擎 |
| `core/evolution/` | 1 | 🟡 孤立 | 存在但無串接 |
| `core/hsp/fallback/` | 1 | 🟡 孤立 | 備援斷路器 |

### AI 系統 — `ai/`（~112 檔案）

| 子目錄 | 檔案數 | 活/死 | 說明 |
|--------|--------|-------|------|
| `ai/memory/` | 16 | 🟡 斷鏈 | HAM/LU/CDM 類別已定義但查詢/存儲 flow 未接 |
| `ai/context/` | 12 | ✅ 活 | 上下文管理 |
| `ai/agents/specialized/` | 12 | ✅ 活 | 專業代理（創意寫作、搜尋、分析等） |
| `ai/alignment/` | 9 | ✅ 活 | 推理、情感系統 |
| `ai/learning/` | 8 | ✅ 活 | 學習管理器、內容分析器 |
| `ai/ops/` | 6 | ✅ 活 | 容量規劃、監控 |
| `ai/response/` | 6 | ✅ 活 | NGR 神經生成回應、NeuroAutoSelector |
| `ai/lifecycle/` | 6 | ✅ 活 | 生命週期元件 |
| `ai/code_inspection/` | 5 | 🟡 斷鏈 | CodeInspector 存在但未串入 P8 閉環 |
| `ai/code_understanding/` | 5 | ✅ 活 | 程式碼理解 |
| `ai/lis/` | 5 | ✅ 活 | 語言免疫系統 |
| `ai/dialogue/` | 3 | ✅ 活 | 對話管理器 |
| `ai/integration/` | 2 | 🟡 斷鏈 | UCC 存在但部分功能未接 |

### 服務層 — `services/`（19 檔案）

| 檔案 | 行數 | 活/死 | 說明 |
|------|------|-------|------|
| `angela_llm_service.py` | 1,981 | ✅ 活 | LLM 服務 + 熱重載 |
| `main_api_server.py` | 1,452 | ✅ 活 | App B 伺服器入口 |
| `chat_service.py` | 1,281 | ✅ 活 | 聊天服務 + 演化確認閘門 |
| `math_verifier.py` | ~400 | 🟡 斷鏈 | 類別完整但未串入 P8 閉環 |
| `hot_reload_service.py` | ~300 | ❌ 死 | 定義了但無生產呼叫者 |
| `brain_bridge_service.py` | ~200 | ❌ 死 | 孤立服務 |

### 死亡/實驗區

| 目錄/檔案 | 行數 | 死因 |
|-----------|------|------|
| `agents/` (5 檔案) | ~1,092 | demo agents，非正式系統 |
| `fragmenta/` (4 檔案) | ~140 | 實驗性專案，import 時副作用不明 |
| `core_services.py` | ~300 | CLI stub，只有「not available」 |
| `test_config.py` | ~100 | 測試檔不該在 src 裡 |
| `test_audio.py` | ~100 | 同上 |
| 16 個死 factory 的檔案 | ~2,500 | 定義了 factory 但無任何呼叫者 |
| 2 個損壞的 `__init__.py` | 2行 | `__all_` typo，import 即炸 |

---

## 2. 死代碼詳細分類

### 2.1 死 Factory（定義了但無生產呼叫者）

以下 factory 存在於 `services/` 或其他位置，但 `grep` 掃描結果顯示從未被任何正式程式碼呼叫：

```
get_hot_reload_service()      → hot_reload_service.py
get_learning_loop()           → services/learning_loop.py
get_art_workflow()            → services/art_workflow.py
get_auth_middleware()         → services/auth_middleware.py
get_security_audit()          → services/security_audit.py
get_waiting_scheduler()       → services/waiting_scheduler.py
get_service_monitor()         → services/service_monitor.py
get_execution_monitor()       → core/execution_monitor.py
get_execution_monitor()       → ai/execution_monitor.py  (同名不同路徑)
get_core_service_manager()    → core_services.py
get_resource_manager()        → core/resource_manager.py
get_sync_manager()            → core/sync_manager.py
get_context_manager()         → core/context_manager.py
get_registry()                → services/registry.py
get_profile()                 → services/profile.py
get_services()                → core_services.py
```

### 2.2 死 config 區段

`angela_core.yaml` 中有 12 個區段標記為 `# DEAD`，約 300 行內容僅供參考：

```
request_routing, model_selection, service_assign, expert_activation_context,
memory_config, learning_policy, security_protocol, crisis_protocol,
optimization_policy, resource_policy, trace_policy, emergency_config
```

### 2.3 死 async 任務

```python
# main_api_server.py:1064
async def broadcast_state_updates():
    """定義了完整邏輯但從未被 create_task"""
```

---

## 3. 半成品（類別完整但 flow 斷鏈）

| 系統 | 行數 | 問題 |
|------|------|------|
| **記憶系統** (HAM/LU/CDM) | ~4,000 | 類別定義完整，但 `save/load/query` flow 從未接入實際對話流程 |
| **P8 LLM 閉環** | ~2,000 | MathVerifier → CodeInspector → StateMatrixAdapter 三個類別獨立存在但從未串成鏈 |
| **記憶查詢路由** | ~1,000 | IntentRouter 定義了記憶查詢意圖但 handler 指向空函數 |
| **RAGManager** | ~500 | 評估未完成，未接入生產 flow |

---

## 4. 隱晦代碼質量問題

| 問題 | 影響 |
|------|------|
| 58 個 `logging.basicConfig()` 在模組層級 | 每個 import 都重設 root logger，最後 import 的檔案決定最終配置 |
| `endpoints/__init__.py` 級聯 import | import 任一個 endpoint → 全部 8 個都被載入 |
| `transformers_compat.py:58` import 時副作用 | 在 import 時修改 os.environ，影響 TensorFlow |
| 2 個 `__init__.py` `__all_` typo | `ai/trust/` 和 `ai/service_discovery/` import 即 NameError |
| `cross-package import` | `core/models/__init__.py` 從 `services` 反向引用 |

---

## 5. 總結：真實有效率

```
後端 Python 源碼          : 116,265 行 (100%)
├── 活代碼（有接線、可運行）: ~98,000 行 (84%)
├── 半成品（類別完整但斷鏈）: ~8,000 行 (7%)
└── 死代碼（無呼叫者/demo） : ~10,000 行 (9%)

非後端代碼：
├── 測試 (tests/)          : 327 檔案
├── 桌面 JS (desktop-app)  : 63 檔案
└── 其他前端               : ~10 檔案
```

**開發效率診斷**：84% 活代碼率不算差，但 9% 的死代碼全是 AI 典型的「寫了沒串、串了沒測」痕跡。半成品的 7% 是最大的機會成本 — 記憶系統和 P8 閉環只差最後一哩就能從「有類別」變成「有功能」。

**建議優先順序**：
1. 🔴 P8 閉環（MathVerifier → CodeInspector → StateMatrixAdapter）— ~2 天能把三個類別串起來
2. 🔴 記憶查詢 chain（HAM → IntentRouter → ChatService）— ~3 天
3. 🟡 刪除/封存死代碼 — ~1 天能清掉 10K 行垃圾
