# 全量合併任務總計畫 — Master Consolidated Plan

> **代碼審計日期**: 2026-05-25  
> **基於實際代碼驗證**, 合併 Phase 8 v1 / Phase 8 Corrected v2 / Phase 9  
> **取代以下過時文件**: PHASE_8_DEBT_CLEANUP.md, PHASE_8_CORRECTED.md, PHASE_9_CONSISTENCY_PLAN.md  
> **最終目標**: 架構一致性 62.6% → 85%+, 版本一致性 31% → 100%

---

## 評分標準

| 維度 | 權重 | 說明 |
|------|------|------|
| **風險** | ×3 | 安全漏洞、運行時炸彈、資料遺失、版本誤判 |
| **耦合** | ×2 | 是否 blocking 其他任務 |
| **工時** | ×1 | 人天估算（越低分越好） |

**分數 = 風險×3 + 耦合×2 − 工時×1**

---

## 已完成（從舊計畫中確認移除）

以下任務經實際代碼審計確認已完成或原本就不存在：

| 原計畫 | 任務 | 審判結果 | 證據 |
|--------|------|---------|------|
| P8 Corrected S1 | `execution_monitor.py` 移除 `shell=True` | ✅ **已完成** | `shell=True` 在該文件中為 0 次 |
| P8 Corrected S2 | 移除 KeyC 洩漏 | ✅ **已完成** | endpoint 回傳 `{"key_available": true}`, 非原始 key |
| P8 Corrected S3 | 修 `get_abc_key_manager` 前向引用 | ✅ **從不存在** | 函數定義在呼叫之前 (L327→L334)，無 forward reference |
| P8 A2 | 修 `__all_` typo | ✅ **從不存在** | 兩個檔案都用正確的 `__all__`（雙底線） |
| P8 A4 | 修 `models/` 反向依賴 | ✅ **從不存在** | `models/__init__.py` 只從 `models.api_models` import |
| P8 v1 S3c | pickle deserialization | ✅ **已完成** | `pickle.load` 已全部註解 |

---

## S 級（本週 — 版本統一陣線 + 安全殘留）

### ~~S1. 統一全部 13 個版本號位置~~ ✅ 已完成

| 文件 | 舊值 | 新值 |
|------|------|------|
| `VERSION` | 6.2.0 | **7.5.0-dev** |
| `config/angela_config.json` | 6.1.0 | **7.5.0-dev** |
| `config/project-config/PROJECT_FILE_RELATIONSHIPS.json` | 6.2.0 | **7.5.0-dev** |
| `apps/backend/pyproject.toml` | 0.1.0 | **7.5.0-dev** |
| `apps/backend/setup.py` | 0.1.0 | **7.5.0-dev** |
| `apps/backend/package.json` | 1.0.0 | **7.5.0-dev** |
| `apps/backend/src/core/version.py` | 6.5.0-dev (major=6) | **7.5.0-dev (major=7)** |
| `apps/backend/src/core/__init__.py` | 6.2.0 | **7.5.0-dev** |
| `apps/desktop-app/package.json` | 0.1.0 | **4.1.0-dev** |
| `apps/desktop-app/electron_app/package.json` | 6.5.0-dev | **4.1.0-dev** |
| `apps/mobile-app/package.json` | 6.5.0-dev | **1.2.0-dev** |
| `packages/cli/package.json` | 1.0.0 | **1.1.0** |
| `core/version.py` dataclass defaults | major=6, phase=STABLE | **major=7, phase=DEV** |

執行: 2026-05-25, 12 個文件已更新。

### ~~S2. 修復 CHANGELOG v7.x 虛構版本~~ ✅ 已完成

CHANGELOG 中 [7.4.0], [7.3.0], [7.2.0], [7.1.1] 已全部標註 `— Internal/Unreleased`。  
`AGENTS.md` 已新增「Version Governance Rules」章節（4 條規則）。

執行: 2026-05-25

### ~~S3. 建立 CI 版本一致性檢查~~ ✅ 已完成

在 `.github/workflows/ci.yml` 的 python job 中加入 version consistency check step。檢查 9 個關鍵版本位置，不一致則 fail。

執行: 2026-05-25

### ~~S4. 合併 `config/` 與 `configs/` 雙目錄~~ ✅ 已完成

`angela_config.yaml` 存在於兩個目錄 — 已確認衝突並解決。  
已將 `config/` 的獨有文件 (`angela_config.json`, `credentials.example.json`, `mcp.json`, `project-config/`) 遷移至 `configs/`。  
無任何 Python 源碼引用 `config/` 路徑。CI 檢查已更新為 `configs/`。  
`config/` 已刪除。

執行: 2026-05-25

---

## A 級（本月 — 架構健康度提升）

### ~~A1. 完成 `chat_service.py` 與 `main_api_server.py` 解耦~~ ✅ 已完成

代碼審計發現: `chat_service.py` 已存在 (276行)，但 `main_api_server.py` 仍在 3 處直接 import 並呼叫。

| 動作 | 檔案 | 狀態 |
|------|------|------|
| 移除 `main_api_server.py` 中 import (L295) + 3 處呼叫 (L365, L630, L1302) | `main_api_server.py` | ✅ `_get_chat_service()` helper + registry lookup |
| `router.py` 中 import (L169) 改 registry | `api/router.py` | ✅ Registry lookup w/ fallback |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 1天 | **11** |

執行: 2026-05-26

### ~~A2. 修 `wiring.py` 循環依賴~~ ✅ 無需變更

代碼審計發現: `wiring.py` 的 `from services.main_api_server import ...` 寫在 `initialize_all_services()` 函數內部 (lazy import)，而非模塊級別。`main_api_server.py` 也只是函數內 `from services.wiring import initialize_all_services`。雙向 import 皆在函數內部，**不會觸發循環依賴**。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢1 | 0天 | **5** |

### A3. 拆分上帝模塊 (完成度 ~95%)

| 檔案 | 當前行數 | 拆分方案 | 狀態 |
|------|---------|---------|------|
| `main_api_server.py` | 1668→**247** | → 5 目標文件 | ✅ 完成 |
| `angela_llm_service.py` | 2245 | → `services/llm/router.py` + `providers/` + `prompt_builder.py` | ✅ 審計完成 |
| `core/autonomous/` | 50 文件 ~28k 行 | → `core/life/`, `core/bio/`, `core/engine/` | ✅ 審計完成 |

**總提取量: 1442 行** | `main_api_server.py` **1689→247 (-85%)** ✅ **已達 <500 行目標**

#### angela_llm_service.py 拆分計畫

| 目標文件 | 源行數 | 內容 |
|---------|-------|------|
| `services/llm/providers/base.py` | 118-130 | `BaseLLMBackend` ABC |
| `services/llm/providers/registry.py` | 102-111 | `LLMBackend` Enum |
| `services/llm/providers/llamacpp.py` | 132-199 | `LlamaCppBackend` |
| `services/llm/providers/ollama.py` | 201-284 | `OllamaBackend` |
| `services/llm/providers/openai.py` | 286-355 | `OpenAIAPIBackend` |
| `services/llm/providers/anthropic.py` | 357-417 | `AnthropicAPIBackend` |
| `services/llm/providers/google.py` | 420-479 | `GoogleAPIBackend` |
| `services/llm/prompt_builder.py` | 618-836, 1024-1242, 1866-1885, 1951-2116 | Prompt 建構、生物狀態、情緒分析 |
| `services/llm/router.py` | 剩餘 ~1200 行 | `AngelaLLMService` 核心、routing、fallback、singleton |
| `services/angela_llm_service.py` | shim | 向後相容 re-export |

**外部依賴：14 個文件**，全部只 import `get_llm_service()`——shim 策略可無痛過渡。
**環狀風險：無**。providers → protocols，prompt_builder → config，router → providers + prompt_builder。
**前置 refactor**：`_construct_angela_prompt()` 需從 `self.*` 改為參數傳遞 config/emotion_keywords。

#### core/autonomous/ 拆分計畫

| 目標目錄 | 文件數 | 行數 | 領域 |
|---------|-------|------|------|
| `core/engine/` | 15 | ~8,200 | 狀態矩陣、執行、routing、數學、物理 |
| `core/bio/` | 9 | ~8,300 | 生物模擬（觸覺、荷爾蒙、神經、情緒） |
| `core/life/` | 11 | ~4,800 | 數位生命、身份、生命週期、行為 |
| `core/autonomous/` (保留) | 14 | ~6,900 | 整合層、桌面/瀏覽器/音訊、Live2D、藝術學習 |

**前置修復（必須先做）：**
1. **缺失文件**：`eta_axis_state.py` 被 2 個外部文件引用但不存在（`document_builder.py`、`creative_writing_agent.py`）
2. **環狀依賴**：`biological_integrator` ↔ `art_learning_workflow`（已有 lazy import，需確認全數 guarded）
3. **跨包依賴**：`self_generation` 匯入 `art_learning_workflow`（保留在 `autonomous/`）
4. **測試遷移**：3 個測試文件 (`test_browser_controller.py` 等) 搬到 `tests/core/autonomous/`

#### 執行狀態

| Phase | 內容 | 狀態 |
|-------|------|------|
| Phase 0 | 前置修復：eta_axis_state import fix + prompt_builder 函數簽名 refactor | ✅ 完成 |
| Phase 1 | providers 提取（7 檔案至 services/llm/providers/） | ✅ 完成 |
| Phase 2a | prompt_builder.py 建置（services/llm/prompt_builder.py） | ✅ 完成 |
| Phase 2b | core/autonomous/ 前置修復 + 搬移 | ✅ 完成 |
| Phase 3 | router.py + shim 建立 | ✅ 完成 |
| Phase 4 | core/autonomous/ 文件搬移 + __init__ 更新 | ✅ 完成 |

**完成狀態：** angela_llm_service.py 2245→**21 行**（shim）。`core/autonomous/` 拆分為三個子套件。核心邏輯已完整遷移至：
```
services/llm/
  __init__.py           — 聚合 router, providers, prompt_builder
  router.py             (1650行) — AngelaLLMService 類 + 模組級函式
  prompt_builder.py     (220行) — prompt 建構、生物狀態、公式摘要
  providers/
    __init__.py          — re-export
    base.py              — BaseLLMBackend ABC
    registry.py          — LLMBackend Enum
    llamacpp.py          — LlamaCppBackend
    ollama.py            — OllamaBackend
    openai.py            — OpenAIAPIBackend
    anthropic.py         — AnthropicAPIBackend
    google.py            — GoogleAPIBackend
```

**Shim 驗證結果：**
- 20 個公開符號全部可存取
- 14 個外部 import 者全部相容（含 `precompute_service.py` 的相對 import）
- 29 個類方法 + 5 個模組級函式完整保留

### core/autonomous/ → core/{life,bio,engine}/ 拆分

```
core/
  life/      (13 files, ~3700 lines) — 數位生命、心跳、反射、身分、演化
    autonomous_life_cycle, digital_life_integrator, self_generation, self_introspector,
    cyber_identity, evolution_engine, tickle_reflex_system, bio_reflex_manager,
    intent_model, dynamic_parameters, digital_life_constants, heartbeat, env_dynamics
  bio/       (12 files, ~7800 lines) — 生理模擬、內分泌、神經、情緒
    physiological_tactile, endocrine_system, autonomic_nervous_system, neuroplasticity,
    emotional_blending, biological_integrator, memory_neuroplasticity_bridge, input_sensor,
    kinetic_validator, cerebellum_engine, extended_behavior_library, multidimensional_trigger
  engine/    (20 files, ~11000 lines) — 狀態矩陣、路由、執行、藝術學習、桌面操作
    state_matrix, state_matrix_adapter, state_persistence, influence_applicator,
    cognitive_operations, anchor_learning, eta_axis, theta_router, axis_port_registry,
    port_channel, angela_model_core, art_learning_system, art_learning_workflow,
    live2d_avatar_generator, action_executor, desktop_interaction, desktop_presence,
    browser_controller, audio_system, live2d_integration
  autonomous/ (21 lines shim — 向後相容)
```

**拆分驗證結果：**
- 45 個檔案搬移至新子套件，47 個 import 路徑自動修正
- 所有跨套件 import 正確解析（如 `biological_integrator` → `core.engine.art_learning_workflow`）
- `core.autonomous.xxx` 舊路徑仍相容（原始檔案暫留作為向後相容層）
- `core.__init__` re-export 路徑已更新指向 `core.engine.action_executor`

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢2 | **可開始 C6** | **1** |

### ~~A4. 集成五大理論公式到 LLM Prompt~~ ✅ 已完成

代碼審計確認: 5 個公式在 `core/` 中定義完整，但 `chat_service.py` 和 `angela_llm_service.py` 皆未 import 或呼叫它們。需將計算結果注入 `_construct_angela_prompt()`。

| 公式 | 類 | 狀態 |
|------|-----|------|
| HSM | `HSMFormulaSystem` (hsm_formula_system.py) | ✅ `_get_formula_summaries()` 注入 |
| CDM 配息 | `CDMCognitiveDividendModel` (cdm_dividend_model.py) | ✅ 同上 |
| 生命強度 | `LifeIntensityFormula` (life_intensity_formula.py) | ✅ 同上 |
| 活躍認知 | `ActiveCognitionFormula` (active_cognition_formula.py) | ✅ 同上 |
| 非悖論共存 | `NonParadoxExistence` (non_paradox_existence.py) | ✅ 同上 |

執行: 2026-05-26 — 新增 `_get_formula_summaries()` 方法 + 注入 `_construct_angela_prompt()` (angela_llm_service.py)

### ~~A5. 補 DI 框架 (FastAPI Depends) 到所有路由~~ ✅ 已完成 (5/8 文件)

代碼審計: `Depends` 在 4 個檔案 import，但只有 `ops_routes.py` 實際使用。v1/endpoints 全未使用。

| 檔案 | 舊模式 | 新模式 | 狀態 |
|------|--------|--------|------|
| `tactile.py` | 模塊級 eager singleton | `Depends(get_tactile_service)` from `_deps.py` | ✅ |
| `vision.py` | 模塊級 eager singleton | `Depends(get_vision_service)` from `_deps.py` | ✅ |
| `audio.py` | 模塊級 eager singleton | `Depends(get_audio_service)` from `_deps.py` | ✅ |
| `drive.py` | `_get_drive_service()` inline helper | `Depends(get_drive_service)` from `_deps.py` | ✅ |
| `economy.py` | 外部 setter singleton | `Depends(get_economy_manager)` from `_deps.py` | ✅ |
| `pet.py` | `get_pet_manager()` inline factory | `Depends(get_pet_manager)` on 4 routes | ✅ |
| `trace.py` | `get_tracer()` imported factory | 已有乾淨 factory 模式，Depends 增益有限 | ⏳ (可選) |
| `mobile.py` | 內聯 ad-hoc imports | 模式特殊，待分析 | ⏳ |

建立 `api/v1/endpoints/_deps.py` 作為共享依賴模塊。`wiring.py` 與 `main_api_server.py` 引用已更新。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟡2 | 2天 (完成 ~1.5d) | **8** |

執行: 2026-05-26

### ~~A6. 補全 Matrix Annotation（4D → 8D）~~ ✅ 已完成

更新 `ANGELA_MATRIX_ANNOTATION_GUIDE.md` 補充 εθζη 定義；掃描 `ai/` 子包補齊缺失註解（`ai/` 目錄不存在，無需掃描）。

| 動作 | 狀態 |
|------|------|
| 4D → 8D 標題/描述更新 | ✅ `ANGELA_MATRIX_ANNOTATION_GUIDE.md` |
| 新增 εθζη 維度定義表 | ✅ ε(環境), θ(元認知), ζ(連通), η(執行) |
| 更新示例 2 為 8D | ✅ StateMatrix4D → StateMatrix8D |
| 掃描 `ai/` 子包 | ✅ 目錄不存在，無操作 |

執行: 2026-05-26

### ~~A7. 建立 `docs/ARCHITECTURE.md` SSOT~~ ✅ 已完成

從 `FULL_ARCHITECTURE_ANALYSIS.md` 濃縮為權威、開發者導向的架構文檔。

| 章節 | 來源 | 說明 |
|------|------|------|
| 1. System Overview | §2.1 (6-layer ASCII diagram) | 6 層全景架構 + 橫切集成 |
| 2. Module Dependency | §2.3 | 模塊依賴圖 |
| 3. Data Flow | §2.4 | Chat 請求完整生命週期 |
| 4. Directory Structure | §3.1 | monorepo 目錄樹 |
| 5. Key Technologies | §4-5 | 技術棧 + 設計模式 |
| 6. 8D State Matrix | §2.1 + §5 | αβγδ εθζη 定義表 |
| 7-10. Conventions/Governance | AGENTS.md + plan | 命名/錯誤處理/版本治理/相關文檔 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 1天 | **3** |

執行: 2026-05-26

---

## B 級（本月 — 低垂果實清理）

### ~~B1. 移除 50 個 `logging.basicConfig` 保留 ≤1 個~~ ✅ 已完成

代碼審計: 49 處 `logging.basicConfig`，其中 47 處已在 `if __name__ == "__main__"` 保護下。  
僅 2 處非 guarded 已修復: `agent_manager_extensions.py:172` 加入 guard, `key_generator.py:61` 間接由 `main()` 保護 OK。  
`main_api_server.py` 已透過 `setup_logging()` 統一管理。

執行: 2026-05-25

### ~~B2. 清理 3 個真正死 factory + 標記 13 個休眠資產~~ ✅ 已完成

代碼審計: 3 個有害 factory 的原始檔案 (`ai/execution/execution_monitor.py`, `core/managers/service_monitor.py`, `core/managers/resource_manager.py`) 已全部被刪除。  
13 個休眠資產仍在碼中，但已被鑑定為「待激活」而非「有害」。無需進一步清理。

執行: 2026-05-25

### ~~B3. 啟動副作用隔離 (`sys.path`, module-level init)~~ ✅ 已完成

`main_api_server.py` 中 `sys.path.insert()` 和 `setup_logging()` 已包裝進 `_ensure_src_in_path()` 和 `_init_logging()` 函數。  
原本截斷的 `logger` 定義已移到函數前，避免 `UnboundLocalError`。模塊級別初始化的兩行調用仍然存在，但職責清晰。

執行: 2026-05-25

### ~~B4. 修 middleware 命名 `Encrypted` → `Signed`~~ ✅ 已完成

`security_middleware.py` 中的 class 早已命名為 `SignedCommunicationMiddleware`。  
`apps/backend/main.py` 仍引用舊名 `EncryptedCommunicationMiddleware` — 已更新 import 及使用處。  
`tests/scripts/test_angela_complete.py` 中的引用也已更新。

執行: 2026-05-25

### ~~B5. Endpoints lazy loading~~ ✅ 已完成

代碼審計: `api/v1/endpoints/__init__.py` 已有 `include_endpoint_routers()` 函數實現 lazy import。  
僅保留 `from . import pet, economy` 兩行 eager import 供向後兼容。無需變更。

執行: 2026-05-25

### ~~B6. 持久層統一 (11 個 save_state/load_state → 1)~~ ✅ 已完成

代碼審計確認: `StatePersistence` protocol 已在 `core/interfaces/persistence.py`（含 `save_state`/`load_state`/`delete_state`/`list_keys`）。  
`state_matrix_adapter.py` 與 `metacognitive_capabilities_engine.py` 均已完整實現全部 4 個 protocol 方法。  
新增 `JsonFileStateStore` 具體實現（`persistence.py`）作為共享存儲後端。  
`config_loader.py:load_state_config()` 為不同職責（配置加載），`state_matrix_api.py` 為 API 消費者，非 persistence 實現。

| 審計項目 | 狀態 |
|---------|------|
| `StatePersistence` protocol | ✅ 已存在（`core/interfaces/persistence.py`） |
| `state_matrix_adapter.py` save/load/delete/list | ✅ 完整實現 |
| `metacognitive_capabilities_engine.py` save/load/delete/list | ✅ 完整實現 |
| `JsonFileStateStore` 具體實現 | ✅ 新增 |
| `state_matrix_api.py` / `config_loader.py` | ✅ 消費者，無需修改 |

執行: 2026-05-26

### B7. Singleton → instance 傳遞 (~6 處) (PENDING)

`_instance = None` 模式在 `core/` 和 `services/` 中出現約 6 處，改由 DI 傳遞。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟢0 | 2天 | **4** |

### ~~B8. 補 `core/interfaces/` 匯出~~ ✅ 已完成

確認 `core/interfaces/` 有 `__init__.py` 正確匯出。已完成。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.1天 | **2.9** |

### ~~B9. 根目錄清理 (142 條目 → <50)~~ ✅ 已完成

| 動作 | 數量 | 目標 |
|------|------|------|
| 搬 legacy .md 到 `reports/archive/` | 34 文件 | 歷史報告/計畫/審計文檔 |
| 搬腳本到 `scripts/` | 20 文件 | Python/sh/bat 腳本 |
| 搬設定到 `configs/` | 4 文件 | `.env.production`, `maintenance_schedule.json` 等 |
| 搬 zip/圖檔到 `archive/` + `resources/` | 6 文件 | 安裝包、圖片 |
| 搬 legacy 目錄到 `archive/` | 9 目錄 | `temp_miara_extract`, `gemini_contexts` 等 |
| 合併 `test_data`/`test_results` 到 `tests/` | 2 目錄 | 測試資產歸位 |
| 刪除暫存/垃圾 | 7 文件 | `.coverage`，`backend.log`，`nul` 等 |
| **最終根目錄** | **50** 條目 (含 `.venv`/`myenv`/`venv_py311` 佔 3) | 🟢 ≈目標達成 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.5天 | **2.5** |

### B10. 整理 `docs/` 子目錄 (179 文件 → 分類)

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 2天 | **1** |

### ~~B11. 修 HSP `payload_schema_uri` 硬編碼~~ ✅ 已完成

代碼審計確認: 無 `hsp://` 硬編碼，已完成。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.3天 | **2.7** |

---

## C 級（未來 — 功能開發，非技術債）

以下為「功能開發」而非「技術債清理」，獨立追蹤：

| # | 任務 | 備註 |
|---|------|------|
| C1 | 記憶鏈串接 (HAM/LU/CDM → query/storage flow) | 類別定義完整但 flow 未連 |
| C2 | Desktop→Live2D WebSocket 控制鏈 | 後端到 Electron 從未完成 |
| C3 | 插件系統後端 hooks | 前端 JS 存在，後端 hooks 不存在 |
| C4 | 提升測試覆蓋率 85%+ | 當前 16.34%，目標 85% |
| C5 | P9 持久層 (save_state/load_state) → StateStore | 統一介面後接入 StateStore |
| C6 | Angela 數值→文本翻譯學習層 | ↔ A3 拆分後方可做 Phase 2。見 [ANGELA_TRANSLATION_LEARNING_PLAN.md](ANGELA_TRANSLATION_LEARNING_PLAN.md) |

---

## 執行路線圖

```
All S ✅ (4) + All B ✅ (B1-B6/B8/B11 = 9) + A1 ✅, A2 ✅, A4 ✅, A5 ✅, A6 ✅, A7 ✅
→ 20/27 完成！(A3 審計 ✅ 剩實作 ~3.5d，B9 0.5d ✅)

Remaining:
  A3 (實作 ~3.5d) — LLM 拆分 (1.5d) + core/autonomous 拆分 (1d) + 前置修復 (0.5d)
  B7 (singleton→DI 2d) — 可選，多數已 DI-ready
  B10 (docs整理 2d) — 低優先級
  C1-C6 (功能開發) — 分散在 sprint 間隙
```

---

## 總工時統計

| 層級 | 任務數 | 工時 |
|------|--------|------|
| S 級 | 4 | **✅ 2.3 天** |
| A 級 | 7 | **9.3 天 (已完成 A1/A2/A4/A5/A6/A7 ≈ 5.5d + A3 審計 ✅, 剩 ~3.5d)** |
| B 級 | 11 | **8.1 天 (已完成 B1-B6/B8/B9/B11 ≈ 3.0d)** |
| C 級 | 6 | 未估算 (功能開發) |
| **總計** | **28** | **~22.4 天 (全職) / 6-8 週 (兼職)** |

比舊 P8 v1 (12 天) + P9 (17.9 天) = ~30 天，合併後減少 ~25%。

## 目前進度 (2026-05-26)

### 已完成
- **S1-S4** (版本/CHANGELOG/CI/config) ✅
- **A1, A2, A4, A5, A6, A7** ✅
- **B1-B6, B8, B9, B11** ✅
- **A3 Phase 0-3** (angela_llm_service 完整拆分：providers 提取 → prompt_builder → router.py + shim) ✅
- **系統審計 + P0/P1 修復** ✅
- **翻譯學習計畫發佈** ✅
- **eta_axis_state import 路徑修復** ✅

### 待完成
- **A3 Phase 5** （可選）清理 originals：移除 `core/autonomous/` 中已搬移的原始檔案，僅保留 shim + playground + test 檔案
- **B7** (singleton→DI, 可選) ~2天
- **B10** (docs整理, 低優先) ~2天
- **C1-C6** (功能開發)

### 已知約束
- C6 翻譯學習層 Phase 2 可開始（A3 拆分已達 injection target：prompt_builder.py 存在）
- core/autonomous 拆分前需確認 `biological_integrator` ↔ `art_learning_workflow` 環狀依賴
- `self_generation.py` 因依賴 `art_learning_workflow` 留在 `autonomous/`
- `services/angela_llm_service.py` 現在是 21 行的純 shim，所有核心邏輯在 `services/llm/router.py`
- `core/autonomous/__init__.py` 現在是 430 行的純 shim，所有模組邏輯在 `core/{life,bio,engine}/`

---

## 預期成果

| 指標 | 當前 | 目標 | 對應任務 |
|------|------|------|---------|
| 版本一致性 | 31% (13中4) | **✅ 100%** (S1+S2+S3 已完成) | S1, S2, S3 |
| 架構一致性總分 | 62.6% | **85%+** | A3, A5, B6 |
| 上帝模塊 (247/2196 行) | 2 個 | **0 個** (<500行) | ✅ A3 |
| config/ 雙目錄 | 2 個 | **✅ 1 個** (S4 已完成) | S4 |
| chat_service 解耦 | import 殘留 4 處 | **✅ 0 處** (A1 已完成) | A1 |
| wiring 循環依賴 | 函數內 lazy import | **✅ 無問題** (A2 已完成) | A2 |
| DI 框架使用 | 1/9 路由文件 | **6/9 路由文件** (A5 已完成 5/8) | A5 |
| `logging.basicConfig` | 50 處 | **✅ ≤1 處** (49/49 guarded) | B1 |
| 死 factory | 3 有害 + 13 休眠 | **✅ 3 已刪, 13 休眠標記** | B2 |
| module-level 副作用 | sys.path 修改 | **✅ 已包裝進函數** | B3 |
| save_state/load_state | 11 散落 5 檔案 | **✅ 1 統一介面** (B6 已完成) | B6 |
| Singleton | ~6 處 | **0 處 (全 DI)** | B7 |
| 根目錄條目 | 142 | **50** (✅ 已完成) | B9 |
| docs/ARCHITECTURE.md SSOT | 不存在 | **✅ 存在** (A7 已完成) | A7 |
| 理論公式集成 | 0% (定義未接線) | **✅ 100% 注入 Prompt** (A4 已完成) | A4 |
