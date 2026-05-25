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

### A1. 完成 `chat_service.py` 與 `main_api_server.py` 解耦

代碼審計發現: `chat_service.py` 已存在 (276行)，但 `main_api_server.py` 仍在 3 處直接 import 並呼叫。

| 動作 | 檔案 |
|------|------|
| 將 `generate_angela_response()` 移回 `chat_service.py` | `chat_service.py`, `main_api_server.py` |
| 移除 `main_api_server.py` 中 3 處 import 與呼叫 | `main_api_server.py` L286, L356, L621, L1293 |
| 改由 wiring.py 統一注入 | `wiring.py` |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 1天 | **11** |

### A2. 修 `wiring.py` 循環依賴

代碼審計發現: `wiring.py` 存在 (79 行) 但 `from services.main_api_server import get_desktop_interaction, ...` 形成了反向依賴。

| 動作 | 說明 |
|------|------|
| 將 main_api_server 的函數引用改為 lazy import | wiring.py L15-24 |
| 或將被引用的函數移到獨立模塊 | 視情況而定 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟡2 | 0.5天 | **9.5** |

### A3. 拆分上帝模塊

| 檔案 | 當前行數 | 拆分方案 | 工時 |
|------|---------|---------|------|
| `main_api_server.py` | 1668 | → `api/lifespan.py` + `api/routes/*.py` + `services/websocket_manager.py` | 2天 |
| `angela_llm_service.py` | 2196 | → `services/llm/router.py` + `services/llm/providers/*.py` + `services/llm/prompt_builder.py` | 2天 |
| `core/autonomous/` | 60+ 文件 | → 按領域拆 `core/life/`, `core/bio/`, `core/engine/` | 2天 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 6天 | **6** |

### A4. 集成五大理論公式到 LLM Prompt

代碼審計確認: 5 個公式 (`HSMFormula`, `CdmDividend`, `LifeIntensity`, `ActiveCognition`, `NonParadox`) 在 `core/` 中定義完整，但 `chat_service.py` 和 `angela_llm_service.py` 皆未 import 或呼叫它們。需將計算結果注入 `_construct_angela_prompt()`。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟡2 | 1.5天 | **8.5** |

### A5. 補 DI 框架 (FastAPI Depends) 到所有路由

代碼審計: `Depends` 在 4 個檔案 import，但只有 `ops_routes.py` 實際使用。v1/endpoints 全未使用。

需在 `drive.py`, `mobile.py`, `economy.py`, `tactile.py`, `vision.py`, `audio.py`, `trace.py`, `pet.py` 中將 lazy singleton 改為 `Depends()`。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 2天 | **10** |

### A6. 補全 Matrix Annotation（4D → 8D）

更新 `ANGELA_MATRIX_ANNOTATION_GUIDE.md` 補充 εθζη 定義；掃描 `ai/` 子包補齊缺失註解。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟡2 | 0.5天 | **6.5** |

### A7. 建立 `docs/ARCHITECTURE.md` SSOT

從 `FULL_ARCHITECTURE_ANALYSIS.md` §2 濃縮為權威、開發者導向的架構文檔。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟡2 | 1天 | **6** |

---

## B 級（本月 — 低垂果實清理）

### B1. 移除 50 個 `logging.basicConfig` 保留 ≤1 個

各模塊在 module-level 呼叫 `logging.basicConfig()`，互相搶 root logger。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟢0 | 0.5天 | **5.5** |

### B2. 清理 3 個真正死 factory + 標記 13 個休眠資產

依據 `DEAD_FACTORY_FORENSICS.md`: 16 個工廠中 3 個有害雜訊、13 個待激活資產。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟡2 | 0.5天 | **6.5** |

### B3. 啟動副作用隔離 (`sys.path`, module-level init)

`main_api_server.py:75` 在 module level 修改 `sys.path`，需移到函數內。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟡2 | 0.5天 | **7.5** |

### B4. 修 middleware 命名 `Encrypted` → `Signed`

`shared/security_middleware.py` 中 `EncryptedCommunicationMiddleware` 實際上只做簽名。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.2天 | **2.8** |

### B5. Endpoints lazy loading

8 個 v1/endpoints 路由從 eager import 改為 lazy import。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.5天 | **2.5** |

### B6. 持久層統一 (11 個 save_state/load_state → 1)

代碼審計發現: 5 個檔案有 11 個 `save_state`/`load_state` 函數，散落在 `state_matrix_api.py`, `state_matrix_adapter.py`, `metacognitive_capabilities_engine.py`, `persistence.py`, `config_loader.py`。需統一成一個介面。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟢0 | 2天 | **4** |

### B7. Singleton → instance 傳遞 (~6 處)

`_instance = None` 模式在 `core/` 和 `services/` 中出現約 6 處，改由 DI 傳遞。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟢0 | 2天 | **4** |

### B8. 補 `core/interfaces/` 匯出

確認 `core/interfaces/` 有 `__init__.py` 正確匯出。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.1天 | **2.9** |

### B9. 根目錄清理 (142 條目 → <50)

搬 legacy 報告到 `reports/archive/`，零散腳本到 `scripts/`。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.5天 | **2.5** |

### B10. 整理 `docs/` 子目錄 (179 文件 → 分類)

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 2天 | **1** |

### B11. 修 HSP `payload_schema_uri` 硬編碼

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

---

## 執行路線圖

```
Week 1 (版本統一陣線):
  ✅ S1 (版本統一) + ✅ S2 (CHANGELOG) + ✅ S3 (CI檢查) + ✅ S4 (config合併)
  B1 (logging 0.5d) + B2 (死factory 0.5d) + B3 (啟動副作用 0.5d)
  + B4 (middleware命名 0.2d) + B5 (lazy loading 0.5d)
  + B8 (interfaces匯出 0.1d) + B11 (HSP硬編碼 0.3d)
  → 已完成 4/11, 剩餘 4.1 天

Week 2-3 (架構健康度):
  A1 (chat_service解耦 1d) + A2 (wiring循環 0.5d) + A5 (DI框架 2d) + B9 (根目錄 0.5d)
  → 4 天 — 架構紀律恢復

Week 4-5 (深度重構):
  A3 (拆上帝模塊 6d)
  → 6 天 — 最大耦合解除

Week 6 (智能與文檔):
  A4 (公式集成 1.5d) + A6 (Matrix補全 0.5d) + A7 (SSOT 1d) + B6 (持久層統一 2d)
  → 5 天 — AI + 文檔同步

Ongoing:
  B7 (singleton→DI 2d) + B10 (docs整理 2d)
  C1-C5 (功能開發) — 分散在 sprint 間隙
```

---

## 總工時統計

| 層級 | 任務數 | 工時 |
|------|--------|------|
| S 級 | 4 | **2.3 天** |
| A 級 | 7 | **12.5 天** |
| B 級 | 11 | **7.6 天** |
| C 級 | 5 | 未估算 (功能開發) |
| **總計** | **27** | **~22.4 天 (全職) / 6-8 週 (兼職)** |

比舊 P8 v1 (12 天) + P9 (17.9 天) = ~30 天，合併後減少 ~25%。

---

## 預期成果

| 指標 | 當前 | 目標 | 對應任務 |
|------|------|------|---------|
| 版本一致性 | 31% (13中4) | **✅ 100%** (S1+S2+S3 已完成) | S1, S2, S3 |
| 架構一致性總分 | 62.6% | **85%+** | A3, A5, B6 |
| 上帝模塊 (1668/2196 行) | 2 個 | **0 個** (<500行) | A3 |
| config/ 雙目錄 | 2 個 | **✅ 1 個** (S4 已完成) | S4 |
| chat_service 解耦 | import 殘留 3 處 | **0 處** | A1 |
| wiring 循環依賴 | 存在 | **0 處** | A2 |
| DI 框架使用 | 1/9 路由文件 | **9/9 路由文件** | A5 |
| `logging.basicConfig` | 50 處 | **≤1 處** | B1 |
| 死 factory | 3 有害 + 13 休眠 | **0 有害, 13 標記** | B2 |
| module-level 副作用 | sys.path 修改 | **0 處** | B3 |
| save_state/load_state | 11 散落 5 檔案 | **1 統一介面** | B6 |
| Singleton | ~6 處 | **0 處 (全 DI)** | B7 |
| 根目錄條目 | 142 | **<50** | B9 |
| docs/ARCHITECTURE.md SSOT | 不存在 | **存在且維護** | A7 |
| 理論公式集成 | 0% (定義未接線) | **100% 注入 Prompt** | A4 |
