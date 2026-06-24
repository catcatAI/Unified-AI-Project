# Angela AI — 全面審計報告（2026-06-25）

**審計日期**: 2026-06-25  
**審計範圍**: 全專案 — 代碼、配置、路由、管線、文檔、測試  
**基準**: 前次審計 `COMPREHENSIVE_AUDIT_2026-06-16.md` + `COMPREHENSIVE_PROJECT_AUDIT.md`  
**方法**: 逐文件驗證、內容檢查、新舊審計比對

---

## 目錄

1. [自前次審計以來的新變化](#1-自前次審計以來的新變化)
2. [文檔陳舊/不正確](#2-文檔陳舊不正確)
3. [路由問題](#3-路由問題)
4. [配置不一致](#4-配置不一致)
5. [Stub / 未完成代碼](#5-stub--未完成代碼)
6. [CHANGELOG 問題](#6-changelog-問題)
7. [版本一致性](#7-版本一致性)
8. [測試狀態](#8-測試狀態)
9. [重複實作](#9-重複實作)
10. [管線流程缺口](#10-管線流程缺口)
11. [修復建議優先級](#11-修復建議優先級)
12. [總結](#12-總結)

---

## 1. 自前次審計以來的新變化

### 1.1 新增: Compositional Image Generation (GVV + ThreeLayerVisual)

Git history 顯示以下新增（自 6/16 審計後）:

| Commit | 內容 |
|--------|------|
| `feat: Three-Layer Visual Architecture` | PCA encoder + nonlinear decoder |
| `fix: GVV API bugs, add ThreeLayerVisual endpoints` | API 路由、Bug 修復 |
| `feat: Concept space improved` | PCA projection 87% accuracy |
| `feat: Concept space mapping` | CLIP → shared concept space |
| `GVV fully wired` | CLIP text encoding, API route, 24 tests |

#### 實際檔案 vs 文檔宣稱不符

| 檔案 | 文檔宣稱數量 | 實際數量 | 差異 |
|------|-------------|---------|------|
| `ai/multimodal/primitives/*.py` | **6** (primitive_types, renderer, library, encoder, __init__, README) | **14** (+ concept_mapper, concept_space, geometric_vocabulary, instance_optimizer, vocabulary_expander, decomposer, differentiable_renderer, learnable_decomposer, pixel_refiner) | +8 |
| `tests/ai/multimodal/primitives/*.py` | **5** (test_types, renderer, library, encoder, integration) | **8** (+ test_concept_mapper, test_geometric_vocabulary, test_instance_optimizer) | +3 |

**問題**: `COMPOSITIONAL_IMAGE_GENERATION_COMPLETE.md` 和 `docs/COMPOSITIONAL_IMAGE_GENERATION_IMPLEMENTATION_SUMMARY.md` 都只記錄了 Phase 1（5 個基礎檔案），完全未提及後續新增的 GVV 架構（geometric_vocabulary, concept_mapper, instance_optimizer 等 9 個檔案）。

### 1.2 新增: image_generation_routes.py

新的 API 路由檔案 `apps/backend/src/api/routes/image_generation_routes.py`，包含 6 個端點:

- `POST /api/v1/generate-image` — 從文字產生圖像
- `POST /api/v1/recognize-image` — 圖像辨識
- `POST /api/v1/reconstruct-image` — 圖像重建
- `POST /api/v1/interpolate-classes` — 類別插值
- `GET /api/v1/generate-image/status` — 健康檢查

**問題**: 路由路徑不一致 — `generate-image` 而非 `/image/generate` 或 `/image-generation/generate`。

### 1.3 新增: 訓練腳本

| 腳本 | 路徑 |
|------|------|
| `train_learned_repr.py` | `scripts/train_learned_repr.py` |
| `train_learned_repr_v2.py` | `scripts/train_learned_repr_v2.py` |
| `train_learned_repr_v3.py` | `scripts/train_learned_repr_v3.py` |
| `train_learned_repr_v4.py` | `scripts/train_learned_repr_v4.py` |
| `train_learned_repr_v5.py` | `scripts/train_learned_repr_v5.py` |

**問題**: 5 個版本代表迭代開發，但 `/scripts/ACTIVE_SCRIPTS.md` 可能未更新這些新腳本。

---

## 2. 文檔陳舊/不正確

### 2.1 前次審計已指出的問題（仍未解決）

| 文件 | 前次審計指出問題 | 當前狀態 |
|------|-----------------|---------|
| `docs/ARCHITECTURE.md` | 缺少 ED3N、GARDEN、ModelBus | ❌ 仍未更新 GVV pipeline |
| `docs/INDEX.md` | 文件索引需更新 | ❌ 仍未包含 image generation |
| `AGENTS.md` | 項目結構不完整 | ⚠️ 有修改（git status 顯示已修改但未提交），但尚未反映完整結構 |
| `docs/development/SERVICE_CATALOG.md` | 可能過時 | ❌ 未驗證是否更新 |
| `docs/development/STUB_TRACKING.md` | 應追蹤所有 stub | ❌ 可能未反映當前 stub 列表 |
| `README.md` | 文件統計數字不正確 | ❌ 仍引用過時數據 |

### 2.2 新增的文檔問題

| 文件 | 問題 | 嚴重度 |
|------|------|--------|
| `COMPOSITIONAL_IMAGE_GENERATION_COMPLETE.md` | 聲稱 6 個檔案，實際 14 個檔案；完全未提及 GVV 架構 | 🔴 HIGH |
| `docs/COMPOSITIONAL_IMAGE_GENERATION_IMPLEMENTATION_SUMMARY.md` | 同上 — 只記錄 Phase 1 | 🔴 HIGH |
| `PHASE1_IMPLEMENTATION_COMPLETE.txt` | 空內容/未知 | 🟡 MEDIUM |
| `docs/ARCHITECTURE.md` | 未提及 GVV 管線、image_generation_routes | 🔴 HIGH |
| `docs/INDEX.md` | 無 image generation 引用 | 🟡 MEDIUM |

### 2.3 前次審計後已修復的

| 文件 | 修復 | 來源 |
|------|------|------|
| `.pre-commit-config.yaml` | Python 版本已修正為 3.10（前次審計指出是 3.8） | ✅ 已修復 |
| Phantom imports | 36 個幻影匯入已修復（Rounds 1-3） | ✅ 已修復 |
| 孤兒目錄 | 12 個 stub 目錄已移除 | ✅ 已修復 |

---

## 3. 路由問題

### 3.1 三重聊天端點

`chat_routes.py` 中有 **3 個幾乎完全相同的 POST 端點**:

| 路由 | 行為 | 差異 |
|------|------|------|
| `POST /api/v1/angela/chat` | 調用 `_handle_chat_request()` | session_id = "angela-{uuid}"，user_name = "朋友" |
| `POST /api/v1/dialogue` | 調用 `_handle_chat_request()` | session_id = "angela-{uuid}"，user_name = "朋友" |
| `POST /api/v1/chat/unified` | 調用 `_handle_chat_request()` | 多 persona 隔離，tenant_id, persona_id, client_id |

`/angela/chat` 和 `/dialogue` **完全等價** — 只是 URL 不同。

### 3.2 路由前綴不一致

| 路由檔案 | 自帶前綴 | router.py 加入前綴 | 最終路徑 |
|----------|---------|-------------------|---------|
| `ops_routes.py` | `/ops` | `/api/v1` | `/api/v1/ops/status` |
| `image_generation_routes.py` | 無 (直接 `/generate-image`) | `/api/v1` | `/api/v1/generate-image` |
| `chat_routes.py` | 無 | `/api/v1` | `/api/v1/angela/chat` |
| `desktop_routes.py` | 無 | `/api/v1` | `/api/v1/desktop/state` |
| `multimodal_routes.py` | 無 (直接 `/multimodal/...`) | `/api/v1` | `/api/v1/multimodal/encode` |

**問題**: 不一致的命名風格 — 有些用名詞 (`desktop`)、有些用領域 (`multimodal`)、有些直接功能 (`generate-image`)。建議統一卷式如 `/api/v1/{domain}/{action}`。

### 3.3 main_api_server.py 死匯入（dead imports）

`apps/backend/src/services/main_api_server.py` 中:
```python
from api.routes.chat_routes import router as chat_router
from api.routes.desktop_routes import router as desktop_router
```
這兩個路由被 **import 但從未被 `app.include_router()` 調用** — 它們已經是透過 `api_v1_router` 間接引入。

**問題**: 死匯入（dead imports）— 變數 `chat_router` 和 `desktop_router` 被賦值但從未使用。這不是 bug，但是不乾淨的程式碼。

### 3.4 ops_routes.py 極簡實作

`ops_routes.py` 只有 3 個端點，所有返回硬編碼 dict:
```python
@router.get("/status")     → return {"status": "ok", "service": "ops"}
@router.get("/health")     → return {"status": "healthy", "service": "ops"}
@router.post("/maintenance") → return {"status": "started", "task": "maintenance"}
```

**問題**: 無真正的運維功能 — 無 Prometheus metrics 整合、無真正維護邏輯。

### 3.5 缺少的常見端點

| 端點 | 狀態 | 說明 |
|------|------|------|
| `GET /health` | 僅在 `ops/health` 可用（需 `/api/v1` 前綴） | 無根級別健康檢查 |
| `GET /metrics` | ❌ 不存在 | Prometheus metrics 端點 |
| `GET /docs` | FastAPI 自動生成 | ✅ 應可用 |
| `GET /openapi.json` | FastAPI 自動生成 | ✅ 應可用 |

---

## 4. 配置不一致

### 4.1 Python 版本衝突

| 文件 | Python 版本 | 
|------|------------|
| `pyproject.toml` | `>=3.10` |
| `.pre-commit-config.yaml` | ✅ 已修復為 `python3.10`（前次審計指出問題） |
| `configs/pyrightconfig.json` | **`pythonVersion: "3.8"`** ⚠️ |

**問題**: `pyrightconfig.json` 仍設定 Python 3.8，與 `pyproject.toml` 的 `>=3.10` 衝突。這會導致 Pyright 型別檢查使用錯誤的 Python 版本規則。

### 4.2 預設值問題

| 配置 | 值 | 問題 |
|------|-----|------|
| `configs/angela_config.yaml` | `test_mode: true` | 🟡 預設為測試模式 |
| `configs/angela_config.yaml` | `debug_mode: true` | 🟡 預設為除錯模式 |
| `configs/angela_config.yaml` | `mobile_bridge: true` | ❌ 手機端是 skeleton，不存在真正 bridge |
| `configs/angela_config.yaml` | `mock_apis: false` | 🟢 合理 |

### 4.3 外部服務配置

`configs/angela_config.yaml` 和 `configs/angela_config.json` 都參考了外部服務（OpenAI、Google）但：
- API keys 顯示為空 (`"google_api_key": ""`)
- 無證據顯示這些服務已配置可用

### 4.4 Docker/Infrastructure 配置

`configs/prometheus.yml` 和 `docker-compose.yml` 參考了 `backend:8000`、`redis:6379`、`postgres:5432` 等服務，但：
- 無證據 Redis 或 PostgreSQL 實際配置
- Nginx SSL 配置參考 `/etc/nginx/ssl/cert.pem` — 無提供證書

---

## 5. Stub / 未完成代碼

### 5.1 已知殘留 Stub（來自前次審計）

| 檔案 | 前次審計狀態 | 當前狀態 |
|------|------------|---------|
| `services/handlers/google_drive_handler.py` | ❌ STUB | ❌ 仍是 stub（28 行，回傳 `"handled by GoogleDriveHandler (stub)"`） |
| `core/security/key_generator.py` | ❌ STUB | ❌ 仍是 stub（自標 "Stub"） |
| `core/security/secure_eval.py` | ❌ STUB | ❌ 仍是 stub（17 行空類） |
| `ai/multimodal/multimodal_processor.py` | ❌ STUB | ⚠️ 部分實作（有 process_text/process_image 方法但有實作，非完全空 stub） |
| `ai/trust/trust_manager_module.py` | ✅ 已重寫 (Phase 3) | ❓ 檔案不存在（`glob` 查無結果 — 可能被刪除） |
| `ai/world_model/environment_simulator.py` | ✅ 已擴充 (Phase 3) | ❓ 檔案不存在 |
| `core/search/search_engine.py` | ❌ STUB | ⚠️ 待確認 |

### 5.2 新發現的未完成代碼

| 檔案 | 問題 |
|------|------|
| `services/math_verifier.py:25-55` | 類別 docstring 自標 `"stub — not yet implemented"` |
| `services/math_verifier.py:25` | `MathExtractor` docstring: `"stub — not yet implemented"` |
| `services/math_verifier.py:32` | `GeometrySolver` docstring: `"stub — not yet implemented"` |
| `services/math_verifier.py:39` | `MathVerifier` docstring: `"stub — not yet implemented"` |
| `core/waiting_scheduler.py:36` | `"Stub — generated by agent, not yet implemented"` |
| `core/state/axis_field.py:87` | `return NotImplemented` |
| `services/cross_modal_router.py:283-293` | 多個 `pass` 區塊 |
| `services/cross_modal_quality.py:209-213` | 多個 `pass` 區塊 |

### 5.3 極簡實作（非完全 stub 但功能有限）

| 檔案 | 行數 | 功能 |
|------|------|------|
| `services/ops_routes.py` | 22 | 3 個端點都回傳硬編碼 dict |
| `services/node_services/server.js` | 36 | Express placeholder server，回傳 "placeholder" |
| `core/tools/js_tool_dispatcher/index.js` | 49 | 回傳 "Placeholder tools loaded" |

---

## 6. CHANGELOG 問題

### 6.1 自報版本與未來日期

| 版本 | 日期 | 標記 | 問題 |
|------|------|------|------|
| 7.5.0-dev | 2026-06-16 | Phase 7 i18n | ✅ 合理（當前開發版本） |
| 7.3.0 | 2026-05-09 | Internal/Unreleased | ⚠️ 自報版本，無對應 git tag |
| 7.2.0 | 2026-05-09 | Internal/Unreleased | ⚠️ 自報版本 |
| 7.1.1 | 2026-02-13 | Internal/Unreleased | ⚠️ 自報版本 |

### 6.2 不一致的完成度聲稱

| 位置 | 聲稱 | 問題 |
|------|------|------|
| CHANGELOG 7.5.0-dev | Server imports OK, Tests 511, ~85-90% complete | 未經獨立驗證的聲稱 |
| CHANGELOG 7.1.1 | "Phase 14 Complete, 99.2% completion" | 明顯誇大 |
| CHANGELOG v6.2.0 | "Phase 14 Complete, Production Ready" | 與當前 7.5.0-dev 狀態矛盾 |

### 6.3 缺失的 CHANGELOG 條目

| 功能 | 出現時間 | CHANGELOG 是否記錄 |
|------|---------|------------------|
| GVV pipeline | 6/16-6/25 之間 | ❌ 無 |
| ThreeLayerVisual | 同上 | ❌ 無 |
| image_generation_routes | 同上 | ❌ 無 |
| Compositional Image Generation | 同上 | ❌ 無 |

---

## 7. 版本一致性

AGENTS.md 聲稱「所有 14 個版本位置必須保持同步」。檢查結果:

| 位置 | 版本 | 狀態 |
|------|------|------|
| `VERSION` | 7.5.0-dev | ✅ |
| `package.json` | 7.5.0-dev | ✅ |
| `apps/backend/pyproject.toml` | 7.5.0-dev | ✅ |
| `configs/angela_config.json` | 7.5.0-dev | ✅ |
| `apps/backend/src/services/main_api_server.py` | 7.5.0-dev (docstring + FastAPI version) | ✅ |

**結論**: 已檢查的版本位置一致。但 AGENTS.md 提到 14 個位置 — 需要完整驗證所有 14 個。

---

## 8. 測試狀態

### 8.1 前次審計的測試數量

前次審計（6/16）報告:
- Phase 6 E2E: 24/24 ✅
- Phase 5 Integration: 13/13 ✅
- Phase 5 Infrastructure: 24/24 ✅  
- Phase 6 Documentation: 15/15 ✅
- Phase 1 Core Activation: 10/10 ✅
- Phase 2 Intelligence: 7/7 ✅
- Phase 3 Safety: 18/18 ✅
- **Total: 111/111 ✅**

### 8.2 新測試

| 測試集 | 文件 | 預估數量 |
|--------|------|---------|
| Primitives Phase 1 | 5 個測試檔案 | ~38 tests (文檔聲稱) |
| GVV pipeline | 3 個測試檔案 (test_concept_mapper, test_geometric_vocabulary, test_instance_optimizer) | ~24 tests (git commit 聲稱) |
| 總計新增 | | ~62 tests |

### 8.3 測試覆蓋缺口（持續存在）

前次審計指出的未測試模組:
- ✅ `services/handlers/*.py` — 全部無專屬測試（7/8 handlers）
- ✅ `services/llm/providers/ed3n.py` — 無測試
- ✅ `services/llm/providers/garden.py` — 無測試
- ✅ `core/security/auth_middleware.py` — 無測試
- ✅ `core/security/encryption.py` — 無測試
- ✅ `image_generation_routes.py` — 新檔案，無測試

### 8.4 跳過測試（stub modules）

大量測試因 stub modules 跳過（來自 code-search 結果）:

| 被跳過的 stub module | 測試檔案數 |
|---------------------|-----------|
| StateMatrixAdapter | 6 |
| ResonanceEngine | 5 |
| AllocationPolicy | 4 |
| RippleNode / InfluenceSpace | 2 |
| ConfigValidator | 1 |
| KeyGenerator | 1 |
| SecureEval | 1 |
| MergeEngine | 1 |
| 其他 | 10+ |

---

## 9. 重複實作

### 9.1 聊天端點三重複

`/angela/chat`、`/dialogue`、`/chat/unified` — 如前所述，三個端點功能等價。

### 9.2 Vision 分析端點

| 路由 | 檔案 | 功能 |
|------|------|------|
| `POST /api/v1/vision/analyze` | `chat_routes.py` | 上傳圖片 + 問題 → VisionService |
| `POST /api/v1/chat/with-image` | `chat_routes.py` | 上傳圖片 + 訊息 → CLIP → VisionService |

**問題**: 這兩個端點都在 `chat_routes.py` 中，且都有圖像分析功能。`/chat/with-image` 有額外的 CLIP 分類步驟，但 `/vision/analyze` 更簡單直接。功能重疊。

### 9.3 Reflex Tables 重複

| 位置 | 類型 |
|------|------|
| `ai/ed3n/reflex_layer` | ED3N 反射層（含 LRU cache） |
| `ai/garden/_ReflexTable` | GARDEN 反射表（無 cache） |

前次審計指出 GARDEN 的 `_ReflexTable.PRESETS` 與 ED3N 的反射層有 18 個相同的反射對。建議提取為共用 `ReflexTable` 類。

### 9.4 分類器重複

| 位置 | 功能 |
|------|------|
| `ai/core/query_classifier.py` | QueryClassifier v2（ED3N-first） |
| `ai/core/dictionary_classifier.py` | DictionaryClassifier（老的基於字典的分類器） |

這兩個分類器在 `_handle_chat_request()` 中僅 `QueryClassifier` 被使用。`DictionaryClassifier` 可能是舊版殘留。

---

## 10. 管線流程缺口

### 10.1 image_generation_routes.py 管線問題

`_get_gvv()` 函數做了:
1. `sys.path.insert(0, ...)` — 破壞性的全域路徑修改
2. `GeometricVocabulary.load()` — 從檔案載入
3. `ConceptMapper.load()` — 從檔案載入
4. 若 concepts space 存在則載入
5. `InstanceOptimizer(vocabulary, mapper, (128, 128))` — canvas 硬編碼

**問題**:
- `sys.path` 修改應避免 — 使用相對匯入
- Canvas size 硬編碼為 128x128
- 無錯誤恢復機制（如某個模型檔案損壞）
- 模組級快取無清理機制
- 兩個 lazy initializer（`_get_gvv()` 和 `_get_three_layer()`）各自獨立

### 10.2 _handle_chat_request 的巨型 try/except

約 330 行的 `_handle_chat_request` 函數中，幾乎每個區塊都用:
```python
try:
    ...
except Exception as e:
    logger.warning(f"...: {e}")
```

**問題**: 過度使用寬泛的 `except Exception` 捕獲，隱藏了真正的錯誤，使除錯困難。

### 10.3 無跨輪次上下文傳播

`QueryClassifier.classify()` 只接收文字，不接收對話上下文，無法消歧（如「另一個呢？」）。

### 10.4 學習管線未完全整合

ED3N `ContinuousLearningPipeline` 在 `_handle_chat_request` 中被 fire-and-forget 調用，但分類器改進、字典增長、用戶偏好學習等尚未整合到統一迴路中。

---

## 11. 修復建議優先級

### P0 — 緊急

| # | 問題 | 修復 |
|---|------|------|
| 1 | `pyrightconfig.json` 版本 3.8 | 改為 `"pythonVersion": "3.10"` |
| 2 | `main_api_server.py` 重複路由匯入 | 移除 chat_router/desktop_router 的直接 `include_router` |
| 3 | 文件與實際 primitives 數量不一致 | 更新 `COMPOSITIONAL_IMAGE_GENERATION_COMPLETE.md` 和 `docs/COMPOSITIONAL_IMAGE_GENERATION_IMPLEMENTATION_SUMMARY.md` |

### P1 — 高優先

| # | 問題 | 修復 |
|---|------|------|
| 4 | `/angela/chat` 和 `/dialogue` 重複 | 棄用 `/dialogue`，統一使用 `/angela/chat` 或 `/chat/unified` |
| 5 | `configs/angela_config.yaml` 預設 test_mode/debug_mode | 改為 `false` |
| 6 | `image_generation_routes.py` 的 `sys.path` 修改 | 改用相對匯入 |
| 7 | CHANGELOG 缺少 GVV pipeline 條目 | 新增 CHANGELOG 記錄 |

### P2 — 中優先

| # | 問題 | 修復 |
|---|------|------|
| 8 | `services/math_verifier.py` stub | 實作或加載階段跳過 |
| 9 | `core/waiting_scheduler.py` stub | 實作或移除 |
| 10 | 路由路徑命名不一致 | 統一路徑命名規範 |
| 11 | `docs/ARCHITECTURE.md` 更新 | 加入 GVV 管線、image_generation_routes |
| 12 | `docs/INDEX.md` 更新 | 加入 image generation 相關文件 |

### P3 — 低優先

| # | 問題 | 修復 |
|---|------|------|
| 13 | 殘留 stub 實現或移除 | google_drive_handler, secure_eval, key_generator |
| 14 | 版本一致性完整驗證 | 檢查所有 14 個版本位置 |
| 15 | `ops_routes.py` 擴展 | 加入真正的運維功能 |
| 16 | `_handle_chat_request` 重構 | 拆分為更小的函數 |

---

## 12. 總結

### 前次審計（6/12-6/16）已修復 ✅

| 類別 | 數量 |
|------|------|
| Phantom imports 修復 | 36 |
| 孤兒 stub 目錄移除 | 12 |
| BOM 字元移除 | 6 |
| 循環依賴修復 | 1 |
| Python 版本修正 (pre-commit) | 1 |

### 前次審計問題仍存在 ❌

| 類別 | 數量 | 說明 |
|------|------|------|
| 殘留 stub | 3+ | google_drive_handler, secure_eval, key_generator |
| 文檔陳舊 | 5+ | ARCHITECTURE.md, INDEX.md, COMPOSITIONAL_IMAGE_GENERATION docs |
| 重複程式碼 | 3+ | 聊天端點、ReflexTables、分類器 |
| 配置不一致 | 2+ | pyrightconfig.json pythonVersion, test_mode 預設 |

### 新發現的問題（6 月 16 日後）🆕

| 類別 | 數量 | 說明 |
|------|------|------|
| 文檔與實際不符 | 2 | Compositional Image Generation docs 未反映 GVV |
| CHANGELOG 缺失條目 | 3 | GVV, ThreeLayerVisual, image_generation_routes |
| 路由路徑不一致 | 3 | generate-image vs domain-based |
| 重複路由匯入 | 1 | main_api_server.py 重複 include_router |
| 未測試的新代碼 | 1 | image_generation_routes.py |

### 總體健康度評分

| 維度 | 評分 | 備註 |
|------|------|------|
| 核心後端 (core/) | 80-90% | 大部份 module 有真實實作 |
| AI 子系統 (ai/) | 60-70% | 部分 stub，部分極簡 |
| LLM 整合 | 95% | 所有 8 個 provider 完整 |
| API 路由 | 70% | 功能完整但有小問題 |
| 文檔 | 50-60% | 多個文件過時，新功能未記錄 |
| 測試 | 75% | 大量測試但覆蓋有缺口 |
| 配置 | 65% | 版本衝突、預設值問題 |
| **總體** | **~65-70%** | 比 6/16 審計略有下降因新功能未記錄 |

---

*本報告基於 2026-06-25 的代碼審計。前次審計參考: `COMPREHENSIVE_AUDIT_2026-06-16.md` and `COMPREHENSIVE_PROJECT_AUDIT.md`。*

---

## 13. 重大發現：遺失的 AI 子模組 🔴

### 13.1 先前審計聲稱存在但實際已消失的目錄

**`COMPREHENSIVE_AUDIT_2026-06-16.md`** 和 **`AGENTS.md`** 都記錄了以下 `ai/` 子目錄有真實實作，但本次審計發現它們**完全不存在**（glob 返回 0 個檔案）：

| 目錄 | 6/16 審計聲稱 | 實際狀態 | 差異 |
|------|-------------|---------|------|
| `ai/learning/` | 「5 個學習系統：LearningManager, ContinuousLearning 等」 | ❌ **不存在** | 目錄完全消失 |
| `ai/ops/` | 「ai_ops_engine.py 9.9KB ✅ REAL」 | ❌ **不存在** | 目錄完全消失 |
| `ai/lis/` | 「lis_manager.py 生命強度系統，未審計」 | ❌ **不存在** | 目錄完全消失 |
| `ai/compression/` | 「alpha_deep_model.py 16.9KB ✅ REAL」 | ❌ **不存在** | 目錄完全消失 |
| `ai/evaluation/` | 「evaluation/task_evaluator.py 6.5KB ✅ REAL」 | ❌ **不存在** | 目錄完全消失 |
| `ai/symbolic_space/` | 「unified_symbolic_space.py 11.1KB ✅ REAL」 | ❌ **不存在** | 目錄完全消失 |
| `ai/trust/` | 「trust_manager_module.py 已重寫（Phase 3）」 | ❌ **不存在** | 目錄完全消失 |
| `ai/world_model/` | 「environment_simulator.py 已擴充（Phase 3）」 | ❌ **不存在** | 目錄完全消失 |
| `ai/security/` | － | ❌ **不存在** | 目錄完全消失 |
| `ai/token/` | － | ❌ **不存在** | 目錄完全消失 |
| `ai/distributed/` | 空目錄 | ❌ **不存在** | 先前已空，現在消失 |

### 13.2 影響分析

| 影響 | 說明 |
|------|------|
| **測試跳過** | 這些模組的測試現在全部以 `pytest.skip` 跳過 |
| **文檔引用** | AGENTS.md、ARCHITECTURE.md、INDEX.md 都引用這些目錄 |
| **匯入斷裂** | 任何匯入這些模組的代碼都會失敗（`ModuleNotFoundError`） |
| **聲稱的可信度** | 6/16 審計對這些模組的 "REAL" 判定是錯誤的 |

**可能原因**: 這些目錄可能在一次重大重構中被刪除或移動，而文檔未更新。

---

## 14. Desktop App (Electron) 問題

### 14.1 死匯入與未使用變數

`apps/desktop-app/electron_app/main.js`:
- `chat_routes` 和 `desktop_routes` 被 import 但從未使用

### 14.2 WebSocket 衝突

```javascript
// Auto-connect to backend WebSocket - DISABLED to avoid conflicts
// Renderer process uses IPC bridge for WebSocket communication
// const wsUrl = `ws://${backendIP}:8000/ws`
```
Main process 的 WebSocket 自動連線被**註解掉**但保留，而 renderer process 透過 IPC bridge 另有一套 WebSocket 連線。兩者可能衝突。

### 14.3 Placeholder 系統

| 功能 | 狀態 | 代碼 |
|------|------|------|
| 音頻 | ❌ Placeholder | `ipcMain.handle('audio-get-devices', async () => { return { inputDevices: [], outputDevices: [] } })` |
| 觸覺 | ❌ Placeholder | `ipcMain.handle('haptic-get-devices', async () => { return { devices: [] } })` |
| 音頻註解 | ❌ 未實作 | `// Will use node-core-audio or similar` |

### 14.4 空的 catch 區塊

```javascript
ipcMain.handle('plugins-list', () => {
  try { ... } catch { return [] }  // 空 catch 隱藏錯誤
})

function restoreWindowPosition() {
  try { ... } catch { return null }  // 空 catch
}
```

### 14.5 38 個 JS 檔案 — 大量功能重疊

`electron_app/js/` 目錄有 38 個 JS 檔案，與 `web-live2d-viewer/js/`（41 個檔案）有許多重複：

| 共同檔案（兩處都有） |
|------|
| app.js, audio-handler.js, availability-manager.js, backend-websocket.js,
character-touch-detector.js, dialogue-ui.js, error-handler.js, frontend-utils.js,
haptic-handler.js, i18n.js, input-handler.js, layer-renderer.js,
live2d-cubism-wrapper.js, live2d-manager.js, logger.js, maturity-tracker.js,
performance-manager.js, plugin-manager.js, precision-manager.js,
security-manager.js, security-utils.js, settings.js,
simple-live2d-loader.js, state-matrix.js, theme-manager.js, tray-manager.js,
unified-display-matrix.js, user-manager.js, wallpaper-handler.js,
z-index-manager.js |

**問題**: ~30 個 JS 檔案在 desktop 和 web-live2d-viewer 之間重複，維護兩個副本增加不一致風險。

---

## 15. modules/ 目錄 — 包裝器模式（Wrapper-Only）

### 15.1 11 個模組包裝器

`apps/backend/src/modules/` 目錄包含 11 個子目錄，每個只有一個 `__init__.py`：

| 模組 | 內容 | 狀態 |
|------|------|------|
| `audio_service/` | 匯入真正的 AudioService | 🟡 僅包裝 |
| `card_pipeline/` | 最小實作 | 🟡 僅包裝 |
| `chat_service/` | 匯入真正的 ChatService | 🟡 僅包裝 |
| `google_drive_service/` | 匯入真正的 GoogleDriveHandler | 🟡 僅包裝 |
| `hot_reload_service/` | 匯入真正的 HotReloadService | 🟡 僅包裝 |
| `intent_registry/` | 最小實作 | 🟡 僅包裝 |
| `llm_service/` | 匯入真正的 LLM Service | 🟡 僅包裝 |
| `math_verifier/` | **自標 stubbed, not yet implemented** | ❌ STUB |
| `resource_awareness_service/` | 匯入真正的 ResourceAwarenessService | 🟡 僅包裝 |
| `tactile_service/` | **DEPRECATED: TactileService removed** | ❌ 棄用 |
| `vision_service/` | 匯入真正的 VisionService | 🟡 僅包裝 |

**問題**: 11 個模組中 9 個只是包裝器（wrapper），1 個是 stub，1 個是 deprecation notice。這些包裝器增加複雜度但沒有提供增值功能。

---

## 16. 其他重大代碼問題

### 16.1 resource_awareness_service.py 引用不存在的方法

在 `if __name__ == "__main__"` 測試區塊中，程式碼呼叫了 `service_default.get_simulated_disk_config()`，但該方法**從未在類別中定義**。這會在執行時引發 `AttributeError`。

### 16.2 ai/core/__init__.py 不存在

`apps/backend/src/ai/core/__init__.py` 不存在（[FILE_DOES_NOT_EXIST]）。雖然這不一定是錯誤（`__init__.py` 在 Python 3.3+ 對 namespace package 非必要），但與專案中其他 162 個 `__init__.py` 不一致。

### 16.3 state_matrix_api.py 多個端點回傳 "not_implemented"

| 端點 | 行為 |
|------|------|
| `POST /navigate` | `# Placeholder for navigation logic` — 回傳硬編碼 dict |
| `POST /port/register` | `if hasattr(matrix, "register_port"):` — fallback 回 "not_implemented" |
| `POST /ripple` | 同上 |
| `POST /allocation` | 同上 |
| `GET /temporal/trend` | `Temporal tracking not available` — **所有功能都回傳 None** |

**問題**: 多個端點使用 `hasattr` 檢查方法是否存在，而非假設它們存在。建議在 StateMatrix4D 中直接實作這些方法或移除端點。

### 16.4 brain_bridge_service.py 引用可能不存在的屬性

```python
bio_state = self.digital_life.biological_integrator.get_biological_state()
```
`DigitalLifeIntegrator` 可能沒有 `biological_integrator` 屬性 — 至少在 `lifespan.py` 中的初始化流程中 `_bio_integrator_instance` 是獨立初始化的，而非作為 `DigitalLifeIntegrator` 的一部分。

### 16.5 connection_session.py 完整但獨立

`SessionManager` 類別（~250 行）有**完整的 session 管理實作**，但從未被 `websocket_manager.py` 或 `lifespan.py` 引用。這是一個孤立的完整實作。

### 16.6 context_storage/ 在專案根目錄

`context_storage/` 目錄包含 **數百個 JSON 檔案**（runtime state data），儲存在專案根目錄中。這些應存放在 `data/` 或 `var/` 目錄下。

---

## 17. 過時的根目錄計畫文件

| 文件 | 問題 |
|------|------|
| `PLAN_chat_pipeline_fix.md` | 根目錄中的過時計畫 |
| `PLAN_full_pipeline_architecture.md` | 根目錄中的過時計畫 |
| `PLAN_pixel_angela_and_live2d.md` | ✅ 已在 CHANGELOG 6/13 記錄完成 |
| `PLAN_REVIEW.md` | 根目錄中的過時計畫 |

建議：將已完成/過時的 PLAN 文件移至 `docs/09-archive/`。

---

## 18. 二次審計新發現總結

### 🆕 新增至總問題清單

| # | 問題 | 嚴重度 | 類型 |
|---|------|--------|------|
| 17 | 11 個 ai/ 子模組消失（learning/, ops/, lis/ 等） | 🔴 **CRITICAL** | 代碼缺失 |
| 18 | Desktop app 音頻/觸覺 placeholder | 🟡 MEDIUM | 未完成 |
| 19 | Desktop/web-live2d-viewer JS 重複 ~30 個檔案 | 🟡 MEDIUM | 重複 |
| 20 | modules/ 目錄 11 個包裝器無增值 | 🟢 LOW | 設計問題 |
| 21 | resource_awareness_service 引用不存在方法 | 🟡 MEDIUM | Bug |
| 22 | state_matrix_api 多端點 "not_implemented" | 🟡 MEDIUM | 未完成 |
| 23 | brain_bridge_service 可能引用不存在屬性 | 🟡 MEDIUM | 潛在 Bug |
| 24 | connection_session.py 完整但孤立未使用 | 🟢 LOW | 死代碼 |
| 25 | context_storage/ 在根目錄（數百 JSON） | 🟢 LOW | 組織問題 |
| 26 | 4 個過時根目錄 PLAN 文件 | 🟢 LOW | 清理 |

### 總體健康度（更新）

| 維度 | 評分（更新） | 變化 | 原因 |
|------|------------|------|------|
| 核心後端 (core/) | 80-90% | — | 無變化 |
| AI 子系統 (ai/) | **40-50%** | ⬇️ -20% | 11 個子目錄消失 |
| LLM 整合 | 95% | — | 無變化 |
| API 路由 | 70% | — | 無變化 |
| Desktop App | 70% | 🆕 | 38 JS 檔案，placeholder 功能 |
| web-live2d-viewer | 60% | 🆕 | 與 desktop 大量重複 |
| 文檔 | **40-50%** | ⬇️ -10% | 更嚴重過時（遺失模組） |
| 測試 | 75% | — | 無變化 |
| 配置 | 60% | ⬇️ -5% | 發現更多不一致 |
| **總體** | **~55-60%** | ⬇️ -10% | AI 子系統大幅降級 |

### 更新 P0 — 緊急（新增）

| # | 問題 | 修復 |
|---|------|------|
| 17 | 11 個 ai/ 子模組消失 | 確認移除是否預期，更新文檔，或從 git history 恢復 |
| 18 | resource_awareness_service 不存在方法 | 移除 `__main__` 中的錯誤方法調用或實作該方法 |

### 更新 P1 — 高優先（新增）

| # | 問題 | 修復 |
|---|------|------|
| 19 | Desktop/web-l2d JS 重複 | 建立共用 JS 套件 |
| 20 | state_matrix_api "not_implemented" 端點 | 實作方法或移除端點 |
| 21 | modules/ 包裝器 | 評估是否可移除包裝層 |
| 22 | context_storage/ 放入 data/ 目錄 | 移動 runtime 資料 |
| 23 | 過時 PLAN 文件 | 移至 09-archive/ |

---

*報告完整。審計方法：逐文件驗證、glob 搜索、code search、檔案內容檢查。前次審計參考: `COMPREHENSIVE_AUDIT_2026-06-16.md`、`COMPREHENSIVE_PROJECT_AUDIT.md`。*
