# Angela AI — 全面審計報告與重構計畫

**審計日期**: 2026-06-16
**審計範圍**: 全專案 `apps/backend/src/ai/`, `services/`, `api/`, `tests/`, `docs/`

---

## 一、模組合併分析

### 應該合併

| 模組 | 原因 | 合併方案 |
|------|------|----------|
| `query_classifier.py` + `dictionary_classifier.py` | 兩個分類層重複，`CONTEXT_TO_QUERY_TYPE` 是 `QueryType` enum 的硬編鏡像 | 合併為 `UnifiedClassifier`：ED3N-first，regex-fallback |
| `response/composer.py` + `response/template_matcher.py` | 兩個response生成系統完全斷裂，`TemplateMatcher` 從未被 `ResponseComposer` 調用 | 統一為 `ResponseGenerator` |
| `lifecycle/llm_decision_loop.py` + `lifecycle/proactive_interaction_system.py` | 兩個主動決策循環，邏輯重疊 | 合併為 `ProactiveDecisionEngine` |
| `learning/` 5個學習系統 | `LearningManager` + `ContinuousLearning` + `ED3NLearningIntegration` + `LearningOrchestrator` + `AdaptiveLearningController` 各自獨立 | 整合為 2 個：`OnlineLearner`（字典+權重）+ `MetaLearner`（策略適應） |
| `ed3n/reflex_layer` + `garden/_ReflexTable` | 完全相同的預設數據和匹配邏輯 | 提取為共用 `ReflexTable` 類 |
| `context/dialogue_context.py` + `model_context.py` + `tool_context.py` | 三個上下文子系統都是死代碼（`get_*_context()` 返回 `None`） | 要嘛合併進 `manager_fixed.py`，要嘛移除 |

### 不應該合併

| 模組 | 原因 |
|------|------|
| ED3N + GARDEN | 不同模型層級：ED3N=反射，GARDEN=推理 |
| ED3N SNN + GARDEN SNN | 不同輸入空間、不同架構 |
| `ai/ops/` 各模組 | 真實不同的運維關注點 |
| `ai/reasoning/` | 獨立認知能力 |

---

## 二、功能過於簡單/狭窄

### 嚴重不足

| 組件 | 現狀 | 缺失 | 建議 |
|------|------|------|------|
| `dialogue_context.py` | 情緒分析只看 13 個英文詞；`get_conversation_context()` 永遠返回 `None` | 無中文處理、無跨輪次意圖追蹤、無對話狀態機 | 移除或重建 |
| `model_context.py` | `get_model_context()` 永遠返回 `None` | `create_context` 全部被註解掉 | 移除或實現 |
| `tool_context.py` | `get_tool_context()` 永遠返回 `None` | 同上 | 移除或實現 |
| `manager_fixed.py` search | `str(content).lower() in query` | 無分詞、無排序、無優先級淘汰 | 至少加 TF-IDF |
| `causal_reasoning_engine.py` | 唯一推理引擎 | 無鏈式推理、無類比推理 | 至少加 2-3 種推理策略 |
| `personality_manager.py` | 載入人格JSON但不影響回應生成 | 人格不注入 `NeuroBlender` | 人格應調製 8D 權重 |

### 部分實現（有結構缺核心邏輯）

| 組件 | 狀態 |
|------|------|
| `multimodal_processor.py` | ED3N 多模態編碼器只產生字典 key，無真正圖像理解 |
| `simultaneous_translation.py` | stub，無整合 |
| `ai/security/` | 存在但無可見安全執行 |
| `ai/code_inspection/` + `code_understanding/` | 存在但無整合到 CODE query type handler |

---

## 三、輸入到 ED3N 流程缺口

### 完整流程圖

```
用戶輸入
    │
    ▼
[1] chat_routes.py: _handle_chat_request()
    ├── MathVerifier.is_math_message()
    ├── EmotionAnalyzer.analyze_emotion()
    ├── CrisisSystem.assess_input_for_crisis()
    └── BiologicalIntegrator.process_auditory_stimulus()
    │
    ▼
[2] QueryClassifier.classify(text)
    ├── DictionaryClassifier.classify() ← ED3N字典
    ├── Regex pattern matching ← 備用
    └── 返回 QueryResult(primary_type, confidence, action_type)
    │
    ▼
[3] ExecutionGate.decide()
    ├── 計算 exec_score = reversibility × impact × clarity
    └── 決定 auto_execute / confirm / reject
    │
    ▼
[4] ModelBus.route() 或 LLM generate_response()
    │
    ▼
[5] 學習系統觸發
    ├── ContinuousLearning.process_interaction_async()
    ├── GARDEN.learn_from_interaction()
    └── MemoryManager.store_experience()
```

### 關鍵缺口

| 缺口 | 嚴重度 | 說明 |
|------|--------|------|
| **無語義橋接** | 🔴 HIGH | `DictionaryLayer.encode()` 用關鍵字/二元組子串匹配，不是語義相似度。"太高兴了" 不會匹配 "开心" |
| **分類信心與ED3N信心斷裂** | 🟡 MEDIUM | 字典條目的 `confidence` 欄位（預設1.0）從未用於分類計算 |
| **缺少上下文傳播** | 🔴 HIGH | `QueryClassifier.classify()` 只接收文字，不接收對話上下文，無法消歧 |
| **訓練數據靜態** | 🔴 HIGH | `classifier_training.json` 啟動時載入一次，`DictionaryLayer.grow()` 的新模式永遠不會回饋到分類器 |
| **無多輪分類** | 🟡 MEDIUM | 每條訊息獨立分類，無意圖延續。"另一個呢？" 會被分為 UNKNOWN |
| **動作類型映射脆弱** | 🟢 LOW | `CONTEXT_TYPE_TO_ACTION` 是靜態 dict，新 context_id 需手動加 |

---

## 四、上下文管理

### 實際上下文限制

| 組件 | 上下文限制 | 工作方式 |
|------|-----------|----------|
| **ED3N** | **無上下文窗口** | 每次查詢獨立處理，context dict 只用於關係分類 |
| **GARDEN** | **無上下文窗口** | 同上，每查詢獨立 |
| **雲端 LLM** | 由供應商管理：OpenAI 4K-128K, Anthropic 200K, Google 1M | 系統提示中的完整對話歷史 |
| **NeuroAutoSelector** | 預設 4096 tokens（一般），8192（高需求） | 模型預算，非實際累積上下文 |
| **ContextManager** | `memory_max_size=1000` contexts | 上下文存儲限制，非 token 級 |

### 「有效上下文」評估

```
ED3N/GARDEN 的有效上下文：零（每次查詢獨立）
雲端 LLM 的有效上下文：僅系統提示中的內容
HAM 記憶的有效上下文：語義搜索（非對話上下文）
```

**關鍵缺失**：無跨輪次對話歷史累積機制，每輪實質上是無狀態的。

---

## 五、ED3N 循環能力

### 現狀：**無循環能力**

ED3N 是嚴格的**單遍線性管線**：

```
輸入 → 反射 → 數學 → 編碼 → 網路前向 → 解碼 → 驗證 → 輸出
```

- `ed3n_engine.py::_process_unlocked()` — 無 while、無 loop
- `core_network.py::forward()` — 單次前向傳播
- `core_network.py::compute_spike_propagation()` — BFS 廣播，max_hops=3，非迭代精煉

### GARDEN 的有限循環

`_process_multi_step()` 依序號標記（"然後"、"and then"）分割文字，逐步處理。這是**序列分解**，非迭代精煉。

### 唯一迭代組件

`step_decoder.py::generate_text()` 做 token-by-token 生成，但這是文字生成，非推理迭代。

---

## 六、循環輸出 vs 直接輸出

### 直接輸出（現狀）

```
輸入 → 單次管線 → 輸出
```

- 確定性：相同輸入 → 相同輸出
- 延遲：ED3N 1-50ms，GARDEN 50-200ms
- 無自我修正
- 無信心閾值重試

### 循環輸出（未實現）

```
輸入 → Pass 1 → Output1 → 品質檢查 →
  如果信心 < 閾值：
    Pass 2（含 Output1 上下文）→ Output2 → 品質檢查 →
    ... 重複直到信心或最大迭代次數
  否則：Output1
```

### 已有類循環組件

| 組件 | 類型 | 差異 |
|------|------|------|
| `ContinuousLearningPipeline` | 離線學習 | 非線上迭代處理 |
| `LLMDecisionLoop` | 主動行為循環 | 非迭代回應精煉 |
| `LearningLoop` | 事後學習 | 非迭代處理 |
| `ModelBus hybrid routing` | 草稿概念 | 有 draft→refine 概念但未實現 |

---

## 七、學習能力分析

### Angela 能學會什麼

| 機制 | 學習內容 | 狀態 |
|------|---------|------|
| 字典增長 | 從對話中新增詞彙條目 | ✅ 可用 |
| 持續學習管線 | 新概念 + Hebbian 權重更新 | ✅ 可用 |
| GARDEN Hebbian | 輸入-輸出對的 SNN 權重更新 | ✅ 可用 |
| 經驗回放 | 存儲互動元組用於批次訓練 | ✅ 可用 |
| 學習循環 | 從 LLM 回應提取新短語 | ✅ 可用 |
| ED3N 訓練器 | Hebbian delta 關係連接更新 | ✅ 可用 |
| 神經詞彙映射 | 8D 狀態軸的值-描述映射 | ✅ 可用 |
| 元學習 | 基於評估指標的策略適應 | ⚠️ 部分 |

### Angela 學不會什麼

| 限制 | 說明 |
|------|------|
| **無法學習新查詢類型** | `QueryType` enum 固定，新領域（如"醫療"）會一直返回 UNKNOWN |
| **無法學習新反射模式** | `ReflexLayer.add_pattern()` 存在但正常運行時從未調用 |
| **無法學習回應品質** | `DeviationTracker` 記錄指標但無反饋迴路調整管線 |
| **無法學習用戶偏好** | 無用戶偏好模型，`PersonalityManager` 不從互動學習 |
| **無法學習對話流程** | 無狀態機或對話模式學習，每輪獨立 |
| **無法從失敗中學習** | 當 ED3N 返回 fallback 時，無機制學習用戶真正意圖 |
| **無法跨 Session 學習** | HAM 存儲經驗但無 Session 級學習整合 |

### 學習架構總結

**寬但淺** — 6+ 個學習機制獨立運作，無統一學習迴路。`LearningOrchestrator` 嘗試成為中央協調器但只連接了 `TaskExecutionEvaluator` 和 `AdaptiveLearningController`，未協調字典增長、Hebbian 更新、詞彙映射、反射模式更新、分類器改進。

---

## 八、需要更新的 MD 文件

| 文件 | 問題 | 優先級 |
|------|------|--------|
| `AGENTS.md` | 項目結構缺少 `ai/learning/`, `ai/meta/`, `ai/reasoning/`, `ai/ops/`, `ai/alignment/` 等 | 🔴 HIGH |
| `docs/ARCHITECTURE.md` | 模組依賴圖缺少 ED3N、GARDEN、ModelBus、上下文子系統 | 🔴 HIGH |
| `docs/development/STUB_TRACKING.md` | 應追蹤所有 stub 和死代碼 | 🔴 HIGH |
| `docs/architecture/ANGELA_FULL_ARCHITECTURE.md` | 需對照當前代碼驗證 | 🟡 MEDIUM |
| `docs/development/SERVICE_CATALOG.md` | 可能未反映當前服務實現 | 🟡 MEDIUM |
| `CHANGELOG.md` | 可能包含虛構版本條目 | 🟡 MEDIUM |
| `README.md` | 可能引用過時模組結構 | 🟡 MEDIUM |

### 應該新建的 MD

| 文件 | 用途 |
|------|------|
| `docs/LEARNING_ARCHITECTURE.md` | 說明 5+ 個學習系統如何互動 |
| `docs/ED3N_INTERNALS.md` | 說明 encode → network → decode 管線 |
| `docs/CONTEXT_MANAGEMENT.md` | 說明哪些上下文管理有效，哪些是 stub |
| `docs/MODEL_BUS_ROUTING.md` | 說明路由決策樹和模型選擇 |
| `docs/KNOWN_GAPS.md` | 記錄所有 stub、死代碼、缺失整合 |

---

## 九、硬編值審計

| 文件 | 行 | 硬編值 | 應改為 |
|------|-----|--------|--------|
| `ed3n_engine.py` | 93 | 反射預設 24 個中英文問候對 | 從 config JSON 載入 |
| `garden_engine.py` | 48-68 | `_ReflexTable.PRESETS` 18 個反射對 | 引用共用配置 |
| `dictionary_classifier.py` | 64 | `NEGATION_KEYWORDS` 3 個詞 | 從配置載入 |
| `query_classifier.py` | 88-90 | `_reflex_words` 硬編 set | 可配置 |
| `query_classifier.py` | 54-59 | 動詞集（`_CREATE_VERBS` 等） | 從 ED3N 字典載入 |
| `composer.py` | 107-163 | 7 個預設片段 | 從配置載入 |
| `llm_decision_loop.py` | 324-370 | ~50 行決策提示模板 | 可配置模板 |

---

## 十、重構優先級計畫

### Phase 1: 緊急修復（1-2 週）

1. **合併分類器** — `query_classifier.py` + `dictionary_classifier.py` → `UnifiedClassifier`
2. **提取共用 ReflexTable** — ED3N + GARDEN 的反射表合併
3. **清理死代碼** — `dialogue_context.py`, `model_context.py`, `tool_context.py` 要嘛實現要嘛移除
4. **更新 AGENTS.md** — 項目結構、測試數量

### Phase 2: 核心補強（2-4 週）

5. **上下文傳播** — `QueryClassifier.classify()` 接收對話上下文
6. **動態分類器** — `DictionaryLayer.grow()` 的新模式回饋到分類器
7. **語義橋接** — 加入簡單 embedding 匹配（非純關鍵字）
8. **循環處理** — 實現信心閾值驅動的迭代精煉

### Phase 3: 學習整合（4-6 週）

9. **統一學習迴路** — 6+ 個學習系統整合為 `OnlineLearner` + `MetaLearner`
10. **學習新查詢類型** — 分類器動態擴展 QueryType
11. **學習反射模式** — 從用戶互動中學習新的反射-回應對
12. **跨 Session 學習** — HAM 經驗整合到 Session 級學習

### Phase 4: 能力擴展（6-8 週）

13. **多步推理** — 連結式推理、類比推理
14. **人格注入** — PersonalityManager 注入 NeuroBlender
15. **混合路由實現** — local→cloud refinement 真正執行
16. **文檔補齊** — 所有缺失的 MD 文件

---

## 十一、架構總覽（現狀 vs 目標）

```
現狀：
┌─────────────────────────────────────────────────┐
│ 用戶輸入                                         │
│   ├── QueryClassifier (硬編 regex + ED3N字典)     │
│   ├── ExecutionGate                              │
│   ├── LLM (獨立生成)                             │
│   └── 6+ 個獨立學習系統                          │
└─────────────────────────────────────────────────┘

目標：
┌─────────────────────────────────────────────────┐
│ 用戶輸入                                         │
│   ├── UnifiedClassifier (ED3N-first + 動態擴展)   │
│   ├── ExecutionGate (配置驅動)                    │
│   ├── ContextManager (跨輪次上下文)               │
│   ├── MathRippleEngine (統一數學)                 │
│   ├── ResponseGenerator (統一回應)                │
│   ├── 循環處理 (信心閾值驅動)                     │
│   └── OnlineLearner + MetaLearner (統一學習)      │
└─────────────────────────────────────────────────┘
```

---

*本報告由全面審計產生，基於代碼實際狀態而非文檔聲稱。*
