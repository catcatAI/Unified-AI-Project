<!--
  =============================================================================
  VERSION: 7.5.0-dev
  STATUS: active
  TITLE: Phase Audit Report v3 — 完整階段性審查
  AUDIENCE: developers, agents
  LAST_MODIFIED: 2026-06-07
  =============================================================================
-->

# Comprehensive Phase Audit v3 — 完整階段性審查

## 審查範圍與判定標準

根據指令，每項需以**滿分為基準**判定。**只要有一個「不」——不完整、不完美、不全面、不細緻、不穩定、不快速——就不算完成。**

審查涵蓋：
1. 全倉庫 MD 文件 vs 實際代碼一致性
2. ED3N 代碼正確性、邊界條件、運行時安全
3. Model Bus + Router 管線正確性
4. GARDEN + 訓練管線 + 檢查點完整性
5. 測試覆蓋率與邊界案例
6. 執行緒安全、數值溢出、記憶體洩漏
7. 文件與計畫的準確性

---

## 1. MD 文件審查結果

| 文件 | 準確度 | 問題 |
|------|--------|------|
| `README.md` | ⚠️ 中 | EN/ZH 矛盾：EN roadmap 顯示 H7.1 ⬜ 未完成，ZH 顯示 ✅ 完成；EN 說 ~69K LOC，ZH 說 ~87K（差 18K）；modules 列 6 個但實際 src/services/ 有 12 個 |
| `docs/06-project-management/README.md` | ❌ 嚴重過時 | 仍是原始模板，版本號 1.0.0（實際 7.5.0-dev），使用 Phase 1-4 結構（實際用 H1-H9），完全未提及 ED3N/GARDEN/Model Bus |
| `GARDEN_MODEL_PLAN.md` | ⚠️ 過時 | Line counts 全部不匹配（doc vs actual 差 10-80 行）；參數規模誇大（doc: 100M-150M params, actual: MiniLM 22M-33M）；宣稱「全部已完成」但多項未實現 |
| `ED3N_MATURITY_PLAN.md` | ✅ 大致準確 | 核心 claims 驗證通過；小問題：說 22 rules 但實際 6 patterns；`ContinuousLearningPipeline` 未在 `__init__.py` 匯出 |
| `SERVICE_CATALOG.md` | ⚠️ 50% 準確 | 列 6 個 modules 但實際 12 個；未提及 `connection_session.py`、`math_verifier.py`、`resource_awareness_service.py`、`adapters/` |
| `docs/INDEX.md` | ✅ 結構正確 | 未列出新計劃文件（ED3N_MATURITY_PLAN.md、GARDEN_MODEL_PLAN.md） |

---

## 2. ED3N 代碼審查 — 16 HIGH/MEDIUM 問題

### 🔴 HIGH — 必須在生產前修復

| # | 問題 | 檔案:行 | 說明 |
|---|------|---------|------|
| H1 | **建構子強制啟用多模態** | `ed3n_engine.py:141` | `enable_multimodal()` 在 `__init__` 無條件呼叫；若 PIL/speech_recognition 等相依缺失，`ED3NEngine()` 完全無法初始化 |
| H2 | **load() 無錯誤處理** | `ed3n_engine.py:497-498` | `json.load(open(...))` 無 try/except — 損毀或遺失檔案直接崩潰 |
| H3 | **CL 執行緒不安全** | `continuous_learning.py:111-113` | `asyncio.to_thread` 執行無鎖狀態變更（`_interaction_count`、`_stats`、`_training_buffer`） |
| H4 | **ReflexLayer 執行緒不安全** | `ed3n_engine.py:37-40` | `process()` 變更 `lru_cache`（OrderedDict）無鎖，並發呼叫會損毀 |
| H5 | **snn_mode race condition** | `ed3n_engine.py:239,244` | `process_snn()` 暫時翻轉 `self.snn_mode`，其他執行緒可見髒狀態 |
| H6 | **_rebuild_index() 執行緒不安全** | `dictionary_layer.py:419-437` | 重建索引時另一執行緒可能正在讀取 |

### 🟡 MEDIUM

| # | 問題 | 檔案:行 | 說明 |
|---|------|---------|------|
| M1 | **>10K 輸入靜默截斷** | `dictionary_layer.py:83-84` | 截斷到 10K 但不記錄 warning |
| M2 | **快取全部清除** | `dictionary_layer.py:109-111` | overflow 時清除整個 cache 而非 LRU eviction |
| M3 | **_growth_history 無限增長** | `dictionary_layer.py:49` | 無上限，隨時間無限膨脹 |
| M4 | **_stage_times 無限增長** | `telemetry.py:29,70-73` | 每個 stage 的 latency list 無上限 |
| M5 | **CL _history 無上限** | `continuous_learning.py:57` | 記憶體中無限增長（save 只存最後 100） |
| M6 | **learning_integration 使用過時 API** | `learning_integration.py:95-102` | `asyncio.get_event_loop()` 在 Python 3.10+ deprecated |
| M7 | **__init__.py 未匯出 CL** | `__init__.py` | `ContinuousLearningPipeline` 未在 `__all__` 中 |

---

## 3. Model Bus + Router 審查 — 6 HIGH 問題

### 🔴 HIGH

| # | 問題 | 檔案:行 | 說明 |
|---|------|---------|------|
| H7 | **同步 process() 阻塞 event loop** | `model_bus.py:304-307` | `_try_model` 直接呼叫 `engine.process()`（同步）在 async context 中，無 `to_thread` |
| H8 | **無 timeout** | `model_bus.py:303-311` | `engine.process()` 若 hang，整個 request 永遠阻塞 |
| H9 | **「多少」分類錯誤** | `query_classifier.py:52-57` | MATH pattern 包含「多少」——「中國有多少人口」被分類為 MATH 而非 KNOWLEDGE |
| H10 | **Cloud backend 不兼容** | `router.py:522-523` | `register_cloud(self.active_backend)` — active_backend 是 Ollama/OpenAI，它們用 `.generate()` 而非 `.process()` |
| H11 | **Parallel fan-out 無取消機制** | `model_bus.py:156-162` | `as_completed` 無 timeout/cancellation，慢 model 拖慢全部 |
| H12 | **全部 engine 回空值時不回退** | `model_bus.py:315-318,329-351` | 所有 model 回空時 `_pick_best` 仍選一個，產生空 text 的 LLMResponse |

### 🟡 MEDIUM

| # | 問題 | 檔案:行 | 說明 |
|---|------|---------|------|
| M8 | `多少` 分類衝突 | `query_classifier.py:52-57,71-78` | KNOWLEDGE pattern 無「多少」——事實查詢被歸為 MATH |
| M9 | >200 chars 強制 KNOWLEDGE | `query_classifier.py:108-109` | 長詩或複雜數學也被歸為 KNOWLEDGE |
| M10 | deconflict_samples 不做去重 | `training_coordinator.py:157-165` | 名為去重但只分組，不呼叫 `should_skip` |
| M11 | CL state 路徑脆弱 | `chat_service.py:23-24` | `os.path.dirname(__file__)` 相對路徑在 symlink/mount 下失效 |

---

## 4. GARDEN + 訓練審查 — 4 HIGH 問題

### 🔴 HIGH

| # | 問題 | 檔案:行 | 說明 |
|---|------|---------|------|
| H13 | **pickle 安全風險** | `snn_core.py:312` | `torch.load(..., weights_only=False)` — 允許任意 pickle 代碼執行，應為 `weights_only=True` |
| H14 | **hash(bigram) 非確定性** | `dictionary.py:79` | Python `hash()` 受 `PYTHONHASHSEED` 影響，同 input 每次跑 vector 不同 |
| H15 | **GARDENBackend 無 compatibility_mode** | `garden.py:36` | `GARDENEngine()` 無傳 `compatibility_mode=True`，強制載入 sentence-transformers |
| H16 | **_lazy_torch() 無錯誤處理** | `dictionary.py:36` | `import torch` 失敗時無 try/except，傳播到所有呼叫者崩潰 |

### 🟡 MEDIUM

| # | 問題 | 檔案:行 | 說明 |
|---|------|---------|------|
| M12 | `torch.load()` 無錯誤處理 | `snn_core.py:310-322` | 無 `FileNotFoundError`/`KeyError`/corrupted file 處理 |
| M13 | `learn_from_interaction()` 無例外保護 | `garden_engine.py:267-312` | 獨立使用時無人 wrap |
| M14 | Save path 脆弱 | `snn_core.py:293-314` | `os.path.dirname(path) or "."` pattern |
| M15 | checkpoint 無 checksum | 所有 load path | 損毀無檢測直到 runtime exception |
| M16 | `load_all_data()` 空數據無 warning | `train_pipeline.py:113-162` | 全部檔案缺失時回傳空 list，訓練繼續但 misleading stats |

---

## 5. 測試覆蓋率分析

### ED3N 測試: 45 tests, 全部通過

| 邊界案例 | 已測試? | 說明 |
|---------|---------|------|
| 空字串 encode | ✅ | `test_empty_string` |
| 超長輸入 | ✅ | `test_very_long_input` (slow marker) |
| None input to `process()` | ❌ | 缺失 |
| None input to `encode()` | ❌ | 缺失 |
| 損毀 save 檔案 | ❌ | 缺失 |
| 並發存取 | ❌ | 缺失 — 0 tests for thread safety |
| `prune()` 邊界 | ❌ | 缺失 — 空/近空 entries |
| 多模態失敗 | ❌ | 缺失 |
| Telemetry 邊界 | ❌ | 缺失 — 0 records, percentiles, histogram |
| IOAnalyzer 空狀態 | ❌ | 缺失 |
| learning_integration | ❌ | 完全無測試 |

**結論：~30% 關鍵邊界案例未測試**

### 其他模組測試覆蓋率 (從 pytest 報告)

```
core/                   → 0% (model_bus.py, query_classifier.py, training_coordinator.py 完全無測試)
garden/                 → 0% (179 tests exist but all env-limited, 127 pass in right env)
router.py               → 0%
chat_service.py         → 0%
services/llm/providers/ → 0% (ed3n.py, garden.py)
scripts/                → 0% (train_pipeline.py)
```

---

## 6. 完整度判定總表

### 判定標準
- ❌ **不完整** — 功能缺失或半實作
- ❌ **不完美** — 有已知 HIGH 問題
- ❌ **不全面** — ∼30% edge cases 無測試覆蓋
- ❌ **不細緻** — 6 處 unbounded growth, 0 處 thread safety
- ❌ **不穩定** — 6 個 HIGH 問題可能導致崩潰/數據損毀
- ❌ **不快速** — 同步 process() 阻塞 event loop, 無 timeout
- ✅ 若全部「不」都不成立才算完成

| 模組 | 完整 | 完美 | 全面 | 細緻 | 穩定 | 快速 | 總判定 |
|------|------|------|------|------|------|------|--------|
| ED3N Engine | ✅ | ❌ (H1) | ❌ (~30% 缺測) | ❌ (M3,M4,M5) | ❌ (H2-H6) | ❌ (H4 sync) | **❌ 不通過** |
| Model Bus | ✅ | ❌ (H7,H8) | ❌ (0% 測試) | ❌ (H10,H11) | ❌ (H8) | ❌ (H7,H11) | **❌ 不通過** |
| Query Classifier | ✅ | ❌ (H9) | ❌ (M8) | ❌ (M9) | ✅ | ✅ | **❌ 不通過** |
| Training Coordinator | ✅ | ✅ | ❌ (0% 測試) | ❌ (M10) | ✅ | ✅ | **❌ 不通過** |
| GARDEN | ✅ | ❌ (H13,H14) | ❌ (M15) | ❌ (M12) | ❌ (H15,H16) | ✅ | **❌ 不通過** |
| Router pipeline | ✅ | ❌ (H10) | ❌ (0% 測試) | ✅ | ❌ (H7,H8) | ❌ (H7) | **❌ 不通過** |
| ChatService | ✅ | ✅ | ❌ (0% 測試) | ✅ | ❌ (H3) | ✅ | **❌ 不通過** |
| Training Pipeline | ✅ | ✅ | ❌ (M16) | ❌ (M14) | ✅ | ✅ | **❌ 不通過** |
| MD 文件 | ✅ | ❌ (README矛盾) | ❌ (6 docs 4 個有問題) | ✅ | N/A | N/A | **❌ 不通過** |

### 總體判定：❌ 全部不通過

**所有 9 個模組/文件類別至少有一個「不」。每個模組都至少帶 2-6 個未修復問題。**

---

## 7. 修復優先級計畫

### P0 — 立即修復（安全 + 崩潰風險）

| ID | 問題 | 預計工時 | 相依性 |
|----|------|---------|--------|
| P0.1 | `ed3n_engine.py:141` — 多模態改為 lazy init | 0.5h | 無 |
| P0.2 | `ed3n_engine.py:497-498` — load() 加 try/except | 0.5h | 無 |
| P0.3 | `model_bus.py:304-307` — 同步 process 改為 to_thread | 0.5h | 無 |
| P0.4 | `model_bus.py:303-311` — 加 timeout | 0.5h | 無 |
| P0.5 | `snn_core.py:312` — weights_only=True | 0.2h | 無 |
| P0.6 | `dictionary.py:79` — hash → zlib.adler32 | 0.2h | 無 |
| P0.7 | `garden.py:36` — 加 compatibility_mode=True | 0.2h | 無 |
| P0.8 | `query_classifier.py:52-57` — 修復「多少」分類 | 0.2h | 無 |
| P0.9 | `router.py:522-523` — cloud backend adapter | 0.5h | 無 |
| P0.10 | `dictionary.py:36` — lazy_torch 加 try/except | 0.3h | 無 |

### P1 — 執行緒安全

| ID | 問題 | 預計工時 |
|----|------|---------|
| P1.1 | ReflexLayer + threading.Lock | 0.5h |
| P1.2 | ContinuousLearningPipeline + threading.Lock | 1h |
| P1.3 | snn_mode atomic flag | 0.3h |
| P1.4 | _rebuild_index() + threading.Lock | 1h |

### P2 — 記憶體管理

| ID | 問題 | 預計工時 |
|----|------|---------|
| P2.1 | _growth_history 加 maxlen | 0.3h |
| P2.2 | _stage_times 加 maxlen | 0.3h |
| P2.3 | CL _history 加 maxlen | 0.3h |
| P2.4 | encode cache eviction 改為 LRU | 0.5h |

### P3 — 測試補充

| ID | 問題 | 預計工時 |
|----|------|---------|
| P3.1 | None input tests (process + encode) | 0.5h |
| P3.2 | Corrupted load tests | 0.5h |
| P3.3 | Thread safety tests | 1h |
| P3.4 | prune boundary tests | 0.5h |
| P3.5 | Telemetry boundary tests | 0.5h |
| P3.6 | IOAnalyzer empty state test | 0.3h |

### P4 — MD 文件修復

| ID | 問題 | 預計工時 |
|----|------|---------|
| P4.1 | README EN/ZH 同步 | 1h |
| P4.2 | docs/06-project-management/README.md 重寫 | 1h |
| P4.3 | GARDEN_MODEL_PLAN.md 更新 | 1h |
| P4.4 | SERVICE_CATALOG.md 更新 | 0.5h |
| P4.5 | docs/INDEX.md 加新計劃連結 | 0.3h |

### 總工時估計：~12h

---

## 8. 即時可修復的 P0 項目

以下項目無相依性，可直接在當前 session 修復：

- [ ] P0.5: `snn_core.py:312` — `weights_only=True` (1 line change)
- [ ] P0.6: `dictionary.py:79` — `hash(bigram)` → `zlib.adler32(bigram.encode()) & 0x7FFFFFFF`
- [ ] P0.7: `garden.py:36` — `GARDENEngine(compatibility_mode=True)`
- [ ] P0.8: `query_classifier.py:52-57` — 從 MATH 移除「多少」
- [ ] P0.10: `dictionary.py:36` — `_lazy_torch()` 加 try/except

---

## 9. 動態分析：Runtime 行為與異常情境

### 9.1 路由流程
```
User Input → QueryClassifer.classify() → ModelBus.route() → engine.process() → response
                                                                    ↑
                                                             若所有 model 回空:
                                                             _pick_best 選 confidence -1
                                                             → 回空字串 LLMResponse
                                                             → Router 不自覺 → 用戶看到 ""
```

### 9.2 分類判定條件影響
- 「多少」包含在 MATH pattern → 事實查詢被誤導至 ED3N（只能做 reflex/math）
- >200 chars 強制 KNOWLEDGE → 300 char 數學題走 GARDEN（vector 編碼而非計算）
- GREETING 包含「謝謝」→ 感謝語境被歸為 GREETING，跳過 GARDEN/Cloud

### 9.3 數值安全分析
| 風險 | 位置 | 結果 |
|------|------|------|
| integer overflow | `_next_key_id` 無上限 | ✅ Python big ints |
| division by zero | `core_network.py:225-228` | ✅ `max(n, 1)` guard |
| NaN propagation | 全檔案 | ✅ 無 trig/log/sqrt 負數 |
| Hebbian delta | `core_network.py:304` | ✅ pre_act/post_act ∈ [0,1] |
| torch.tensor overflow | `snn_core.py:238` `decay ** t` | ❌ 若 decay > 1 可能 overflow |
| hash collision | `_CharBagEncoder` | ✅ 256-dim 稀疏向量，碰撞無害 |
| `hash(bigram)` 非確定性 | `dictionary.py:79` | ❌ 同 input 不同次執行結果不同 |

### 9.4 檢查點損毀場景
```
損毀類型                   影響
JSONDecodeError            ed3n_engine.load() 崩潰 (H2)
FileNotFoundError          ed3n_engine.load() 崩潰 (H2)
corrupted .pt file         snn_core.load() 崩潰 (M12)
missing engine_meta.json   garden_engine.load() 崩潰 (M12)
checkpoint 遺失            pipeline 跳過載入，用 presets（不報錯也不提示）
```

### 9.5 並發 crash 場景
```
場景 1: 兩個 request 同時進 ReflexLayer.process()
  Thread A: 檢查 cache → miss → 開始掃 patterns → B 修改 patterns → A 讀到髒資料
  結果: KeyError 或回傳錯誤 response

場景 2: request 進 process_snn()，snn_mode=True，另一個 request 進 process_deep()
  Thread B 看到 snn_mode=True → 走 SNN path，但 SNN 可能未初始化
  結果: AttributeError 或錯誤結果

場景 3: 一個 request 觸發 _rebuild_index()，另一個正在 encode() 讀取 index
  Thread A 正在清空/重建 keyword_index → Thread B 讀到不完整索引
  結果: encode() 回傳部份/空結果
```

---

## 10. 結論

**專案當前狀態：功能完整但不可用於生產。**

所有模組都有完整的基礎功能（架構到位、管線已接、訓練可跑），但在執行緒安全、邊界處理、測試覆蓋、文件準確度上均有顯著 gap。總計 **16 個 HIGH 問題 + 16 個 MEDIUM 問題**，需約 **12 小時**修復才能達到生產就緒標準。

### 關鍵數字
- 45 tests, all passing (ED3N)
- 179 tests, 127 pass in right env (GARDEN)
- 0 tests: core/, router.py, chat_service.py, providers/
- 16 HIGH issues (生產阻塞)
- 16 MEDIUM issues
- 6 docs with accuracy issues
- ~30% critical edge cases untested
- 0 thread safety tests
