# Angela AI 接線地圖 (Wiring Map)

## 目標

記錄整個專案中元件之間的呼叫、註冊、初始化關係，特別是隱晦的接線（模組層級代碼、間接依賴、背景執行緒）。

---

## 1. 伺服器生命週期接線

### 1.1 `main_api_server.py` (`services/`) — 主要 AI 伺服器

```
lifespan (lines 341-395, @asynccontextmanager)
├── Startup:
│   ├── 讀取 config lifecycle.services_to_preinit
│   ├── 預初始化 AngelaChatService (config-driven)
│   ├── 預初始化 AngelaLLMService (config-driven)
│   ├── 預初始化 BiologicalIntegrator (config-driven)
│   ├── _initialize_all_services() (lines 530-596)
│   │   ├── get_desktop_interaction()
│   │   ├── get_action_executor()
│   │   ├── get_vision_service()
│   │   ├── get_audio_service()
│   │   ├── get_tactile_service()
│   │   ├── get_abc_key_manager()
│   │   ├── get_digital_life()
│   │   ├── get_economy_manager()
│   │   ├── pet.get_pet_manager()
│   │   ├── digital_life.broadcast_callback = manager.broadcast  ← WebSocket hook
│   │   ├── pet.set_biological_integrator(digital_life.biological_integrator)
│   │   ├── pet.set_economy_manager(economy_manager)
│   │   ├── economy.set_economy_manager(economy_manager)
│   │   ├── pet_manager.broadcast_callback = pet_broadcast_wrapper
│   │   └── bio_integrator.register_event_callback(bio_event_callback)
│   ├── get_metabolic_heartbeat().start()
│   │   ├── bio_integrator.initialize()
│   │   ├── create_task(_run_loop())       ← 代謝循環
│   │   └── create_task(_integration_loop()) ← 小腦循環
│   └── (done)
├── yield  ← 伺服器運行
└── Shutdown:
    ├── get_metabolic_heartbeat().stop()
    │   ├── cancel(_task)
    │   └── bio_integrator.shutdown()
    └── (done)

Router registrations:
├── app.include_router(api_v1_router)     ← 共用路由 (api/router.py)
│   ├── drive, pet, vision, audio, tactile
│   ├── mobile, economy, trace, ops
├── app.include_router(atlassian_router)  ← Jira/Confluence
└── app.include_router(state_matrix_router, prefix="/api/v1")

Middleware:
├── CORSMiddleware (config-driven origins)
└── EncryptedCommunicationMiddleware (KeyB, HMAC-SHA256)
    └── Protects: /api/v1/mobile/, /api/v1/system/status/detailed, /api/v1/system/module-control
```

### 1.2 `main.py` (`apps/backend/`) — 系統管理伺服器

```
lifespan (lines 82-178, @asynccontextmanager)
├── Startup:
│   ├── SystemManager.initialize()
│   ├── BootstrapManager.run_full_bootstrap()
│   │   ├── scaffold_directories()        ← EnvResolver
│   │   ├── 硬體探測 (HardwareProbe)
│   │   └── persist_state(system_status.json)
│   ├── ClusterManager (MASTER node)
│   ├── SyncManager
│   │   └── register_callback(broadcast_to_clients)  ← WebSocket hook
│   ├── UnifiedKnowledgeGraph.initialize()
│   ├── EnterpriseMonitor.start()
│   └── PetManager.broadcast_callback = broadcast_to_clients
├── yield
└── Shutdown:
    ├── EnterpriseMonitor.stop()
    └── SystemManager.shutdown()

Router registrations (inside create_app()):
└── app.include_router(router)  ← 與 main_api_server.py 相同的共用路由

Middleware:
├── EncryptedCommunicationMiddleware (KeyB)
└── CORSMiddleware (硬編碼 ["*"])
```

### 1.3 關鍵差異

| 項目 | main_api_server.py | main.py |
|------|-------------------|---------|
| 用途 | AI 推理、聊天、生物模擬 | 系統管理、硬體、叢集 |
| 預初始化服務 | chat, LLM, bio (config-driven) | bootstrap, cluster, sync, KG, monitor |
| 跨服務接線 | `_initialize_all_services()` 完整接線 | 只有 PetManager broadcast hook |
| 生物心跳 | ✅ 啟動 + 關閉 | ❌ 不存在 |
| shutdown timeout | 可配置 (default 10s) | 硬編碼 |
| lifespan 註冊方式 | `app.router.lifespan_context = lifespan` | `FastAPI(lifespan=lifespan)` |

---

## 2. Factory Singleton 接線圖

### 2.1 核心依賴鏈

```
get_angela_config()  [17+ callers]
  ← get_llm_service()
  ← get_angela_chat_service()
  ← get_reflex_system()
  ← get_digital_life() (indirect)
  ← get_template_library() (indirect)
  ← +12 others

get_llm_service()  [async singleton]
  ← get_angela_config()
  ← get_template_library()
  ← get_config_loader() (fallback)
  [Called by: lifespan, chat_service, math_verifier, reflex, UCC,
   creative_agent, project_coordinator, router /llm/reload, REPL]

get_angela_chat_service()  [function-attribute singleton]
  ← get_angela_config()
  ← get_bootstrap_manager()
  ← get_llm_service()
  ← get_template_library()
  ← get_model_core()
  ← get_value_system()
  ← get_formula_config("dynamic")
  [Called by: lifespan, REPL, HTTP /angela/chat]
```

### 2.2 所有 Factory 及其呼叫者

詳見原始碼與以下摘要：

**有實際生產呼叫者的 factory：**
`get_metabolic_heartbeat`, `get_desktop_interaction`, `get_action_executor`,
`get_tactile_service`, `get_abc_key_manager`, `get_digital_life`,
`get_economy_manager`, `get_llm_service`, `get_angela_chat_service`,
`get_session_manager`, `get_angela_config`, `get_bootstrap_manager`,
`get_formula_config`, `get_bootstrap_config`, `get_reflex_system`,
`get_tracer`, `get_template_library`, `get_value_system`, `get_model_core`,
`get_pet_manager`, `get_drive_service`

**定義了但無生產呼叫者的 factory（死代碼）：**
`get_hot_reload_service`, `get_learning_loop`, `get_art_workflow`,
`get_auth_middleware`, `get_security_audit`, `get_waiting_scheduler`,
`get_service_monitor`, `get_execution_monitor` (core version),
`get_execution_monitor` (ai version), `get_core_service_manager`,
`get_resource_manager`, `get_sync_manager` (core),
`get_context_manager`, `get_registry`, `get_profile`,
`get_services` (core_services.py)

---

## 3. 隱晦接線 (Subtle Wiring)

### 3.1 模組層級代碼（import 時執行）

| 檔案 | 行 | 影響 |
|------|----|------|
| `compat/transformers_compat.py:58` | `ensure_transformers_compatibility()` 在 import 時立即執行 | 修改 os.environ、影響 TensorFlow 行為 |
| `main.py:31` | `sys.path.insert(0, ...)` | 修改全域 import 路徑 |
| `main.py:45,78` | `ABCKeyManager()` + `SystemManager()` | 在模組層級建立 singleton |

### 3.2 背景執行緒

| 檔案 | 行 | 模式 | 說明 |
|------|----|------|------|
| `resource_pool.py:300` | `Thread(target=cleanup_loop, daemon=True)` | 每次 ResourcePool 實例化時啟動 |
| `resource_pool.py:375` | `Thread(target=self._worker_loop, daemon=True)` | 在 ThreadPool.start() 時啟動 |
| `waiting_scheduler.py:89` | `Thread(target=self._worker_loop, daemon=True)` | 在 _start_worker() 時啟動 |
| `tray_manager.py:189,297,412` | `Thread(target=lambda: asyncio.run(...)).start()` | 功能表回呼中啟動 async 任務 |

### 3.3 58 個 `logging.basicConfig()` 在模組層級

每個都在 import 時重新設定 root logger。最後 import 的檔案決定最終配置。

### 3.4 損壞的 `__init__.py`

| 檔案 | 問題 |
|------|------|
| `ai/trust/__init__.py:3` | `__all_["TrustManager"]` — 應為 `__all__ =`，import 時會 `NameError` |
| `ai/service_discovery/__init__.py:3` | 同上 |

### 3.5 在 `__init__.py` 中定義類別

| 檔案 | 內容 |
|------|------|
| `ai/formula_engine/__init__.py` | 整個 `FormulaEngine` 類別 + 測試區塊 |
| `ai/alignment/__init__.py` | 6 個 stub 類別（靜默替代真實實作） |

### 3.6 跨套件 import

| 檔案 | import | 問題 |
|------|--------|------|
| `core/models/__init__.py` | `from services.api_models import ...` | 從 services 跨套件引用 |
| `core/services/__init__.py` | `from core.hardware import HardwareDetector` | 非相對路徑 |

### 3.7 `endpoints/__init__.py` 級聯 import

`api/v1/endpoints/__init__.py` 用 `from . import drive, pet, vision, ...`
導入所有 8 個 endpoint 模組。任何一個 endpoint 被 import 時，全部 8 個都會被載入。

---

## 4. 死代碼 (Defined But Never Called)

### 4.1 Factory 無呼叫者
`get_hot_reload_service`, `get_learning_loop`, `get_art_workflow`,
`get_auth_middleware`, `get_security_audit`, `get_waiting_scheduler`,
`get_service_monitor`, `get_execution_monitor` (×2), `get_core_service_manager`,
`get_resource_manager`, `get_sync_manager` (core), `get_context_manager`,
`get_registry`, `get_profile`, `get_services`

### 4.2 背景任務無註冊
```python
async def broadcast_state_updates():  # main_api_server.py:1064
    """定義了但從未被 create_task"""
```

---

## 5. 兩台伺服器比較

| 面向 | main_api_server.py (App B) | main.py (App A) |
|------|---------------------------|------------------|
| Routes | ~104 (含共用、state-matrix、atlassian) | 8 + 共用路由 |
| 啟動時接線 | chat + LLM + bio + 跨服務 wiring + heartbeat | bootstrap + cluster + sync + KG + monitor |
| Heartbeat | ✅ `.start()` + `.stop()` 在 lifespan | ❌ 無 |
| 共用路由 | `include_router(api_v1_router)` | `include_router(router)` (同一個) |
| 中介層 | CORS + EncryptedComm | EncryptedComm + CORS |
| 死代碼 | `broadcast_state_updates()` | 較少，但沒有生物模擬 |
| 配置驅動 | 是 (lifecycle.services_to_preinit) | 部分硬編碼 |
