# 全專案稽核報告 — 2026-11-04

> 主題：**表層不得代替核心**。模板、記憶、檢索、路由可以讓系統有用，但它們產生的句子不是「這一刻生成的回答」。這份報告記錄本輪檢查了什麼、修掉什麼、還有什麼**故意不修**（附理由），以及哪些地方**查過但沒有問題**。
>
> 量測口徑見 `docs/06-project-management/MEASUREMENT_MAP.md`；層的定義見
> `docs/06-project-management/LAYER_SEPARATION.md`；唯一的分數定義在
> `apps/backend/src/ai/meta/intelligence.py`。

## 一、判準（先寫清楚，否則修完會漂走）

1. **有可生成後端時，記憶／模板只發布證據，不說話。** 判定只有一份：
   `services/llm/generation_gate.py`（`GENERATIVE_BACKENDS`＝雲端五家＋ llama.cpp 三個 slot；`unified`／ED3N／GARDEN
   **不算**，它們不能吃提示改寫）。
2. **沒有生成後端（native）時**，抽取式回答是誠實的降級模式，但必須標
   `source=memory`／`backend=dialogue-memory`，不能冒充模型輸出。
3. **核心分與系統分分開陳述。** 核心＝SNN／LLM 產生且正確（本輪仍
   **0.00/10**）；系統分＝分層聚合（含查表／計算／分類器／模板），只是對照。
4. **量測不得寫進被量測的環境**：探針單一實例、任務寫入走沙盒。
5. 不調門檻、不背題、不在 held-out 上調參、不把罐頭句回教回去。

## 二、已修（附證據）

### 1. 記憶層的四條「直接回答」路徑（本輪主要缺陷）

| 路徑                                                          | 修正前                  | 修正後                                                   |
| ------------------------------------------------------------- | ----------------------- | -------------------------------------------------------- |
| `MemoryIntegration.try_memory_retrieval` 的 `memory-template` | 有 LLM 時仍送出罐頭句   | 有生成後端→`None`（前面的回憶已發布證據）                |
| `MemoryIntegration.try_conversation_recall`                   | 抽取式回答先於模型      | 有生成後端→把使用者原句寫進 `memory_evidence`、回 `None` |
| `router._recall_user_fact`                                    | 「我記得：…」直接回答   | 有生成後端→證據、回 `None`                               |
| `chat_routes._taught_fact_turn`                               | 「你教過我：…」直接回答 | 回 `(native_reply, evidence)` 恰一；有生成後端只給證據   |

新增 `services/llm/memory_evidence.py`（`remember`／`collect` 契約）與
`prompt_builder._append_memory_evidence`（中英 locale／`prompt_manager`
預設鍵），證據以「使用者自己說過的話，不是查證過的知識」的身分進提示。

**單一判定**：`memory_integration._has_generative_backend`、
`router._llm_backend_available`、`gate_execution._llm_generation_available`
全部委派 `generation_gate`。這順手修掉一個真 bug：舊名單寫 `llama_cpp`，provider
enum 是 `llamacpp`（還有 `llamacpp-qwen`／
`llamacpp-gemma`）——llama.cpp 後端對記憶層**完全隱形**，罐頭句會蓋掉它。

### 2. 教過的對話對（語意檢索）也會搶在模型前面

`router._try_neural_retrieval` 把 `_taught_pairs`
用編碼器相似度找回來後**原句重播**，還標
`hit_source="neural"`。相似度是神經的，內容是**記憶**：

- 有生成後端→發布 `taught_facts` 證據、回 `None`（模型自己說）。
- native→照舊回答（量測路徑不變）。
- 這一類答案**不再進回應快取**（`_is_cacheable_response` 排除
  `hit_source="neural"`）：教過的東西會增長，快取重播會讓「更正」在 TTL 內失效。

### 3. 知識層的因果問句讓位

「為什麼天空是藍的？」原本由精選庫回屬性值
`blue`——那是回答「什麼顏色」，不是回答「為什麼」。`_CAUSAL_QUESTION_RE` ＋
`_try_knowledge` 守衛：有生成後端時回 `None`
讓模型解釋；native 保留原行為（offline-speak 契約已釘在
`tests/services/test_knowledge_handoff.py`，3 tests）。

### 4. 首回合的判定盲點

`chat_routes` Step 1c 在取得 chat service **之前**就問「有沒有生成後端」；那時
`router._llm_service` 可能還沒指派。`generation_gate.generation_available()`
現在會退回讀 service registry（`angela_llm_service`，由同一個
`get_llm_service()` 在 `initialize()` 之後寫入）。測試：
`tests/services/test_memory_handoff.py::test_a_service_registered_before_the_module_global_is_still_seen`。

### 5. 回覆欄位在 dict 生產者上遺失

`_format_chat_response` 用 `getattr` 讀 `llm_response`，但知識層／記憶層的早退是
**dict**——`model`／`confidence`／`hit_score`／`hit_source` 全部變成
`None`／`0.0`／`"none"`，畫面上看起來像「未知來源的 LLM 回覆」。改為 `_read()`
同時讀 dict 與物件；契約測試在 `tests/services/test_llm_force_route.py`。

### 6. 觀測工具跟不上新的交棒形狀

- `scripts/trace_reply.py` 認得 `(reply_dict|None, evidence|None)`
  這種 tuple，並追蹤 `_taught_fact_turn` 階段。
- `scripts/audit_placement.py`
  因此能把「記憶層回答」歸給 memory，而不是 unknown／surface。

### 7. 跨檔測試污染（不是產品 bug，但會讓別人的綠燈說謊）

`tests/api/test_dashboard_real_data.py::TestPetPanel::test_an_interaction_changes_the_real_matrix`
先把 matrix 釘在 0.5、結束沒還原，後續測試讀到被改過的全域狀態。改為 fixture 存檔／還原。

### 8. `docs/STATUS_MATRIX.md` 被手改

上一輪直接改生成的 MD，`tests/test_gen_status_matrix.py`
的 freshness 檢查抓到。現在 2026-11-02 段落寫進
`docs/status_matrix.yaml`、`last_verified` 更新，重跑
`scripts/gen_status_matrix.py generate`（12 tests 綠）。

### 9. 同回合重複掃描

`try_conversation_recall`
會被 template 與 memory-retrieval 兩個 connector 各問一次；`context["_conversation_recall_done"]`
讓第二個直接跳過（也避免證據重複）。

## 三、需注意（未修，附理由）

1. **`state` 類 0/324（帶邊界條件的題）**
   — 這是知識缺口，不是本輪的層問題。**刻意不**把標準集主題種進斷言庫（那是自己教自己）。因此
   `pass_rate` 的上限是 772/1096 ≈ **0.704**，`human_speech_pass_rate ≥ 0.90`
   的臨時門禁在邊界題真的會答之前不可能拆，也不該拆。
2. **`semantic-qa` 仍被 `classify_source` 算成 neural**
   — 這一桶包含教過的對話對（記憶）與 unified 的統計檢索。文件已明說「neural 這裡＝不是模板，不是核心」，且核心分只認
   `ai.meta.intelligence.is_core_backend()`。改標籤會改變 `neural_share`
   的定義與臨時門禁（只許往上），需要單獨一輪重跑全部量測，不宜順手改。
3. **`generation_available()` 的範圍** — 它看 module global 或 service
   registry；若某處自己 `AngelaLLMService()`
   建一個沒註冊的實例，那個實例的後端不會被看到。目前生產路徑都走
   `get_llm_service()`，但這是契約邊界，文件化優於再加一層猜測。
4. **native 的因果問句仍回屬性值** — `天空為什麼是藍色的?` →
   `蓝色。`。這是 offline 的已知降級（沒有模型可以解釋），已列在
   `MEASUREMENT_MAP`／`PROGRESS` 的既有缺陷，不在本輪假裝修好。
5. **`tools` 維度 0.0** — 原生後端沒有代碼生成，`run_benchmarks.py`
   對 code 直接回空字串（設計上的誠實失敗），非回歸。

## 四、未發現問題（查過）

- **所有聊天入口走同一條管線**：`/chat/unified`、`/session/{id}/send`、
  `/chat/stream`、`/chat/group`、`/chat/with-image`、`/chat/with-audio` 都呼叫
  `_handle_chat_request` → `_run_chat_pipeline`；沒有繞過 gate 的旁路。
- **沒有其他模板直出**：`backend="template"` 只出現在
  `composed-template`（native 降級）與 terminal fallback；有生成後端時
  `_serve_template_selection` 只把模板放進 `template_example` 並回 `None`。
- **沒有新的未定義名稱／語法錯誤**：pyflakes 掃過本輪改動的 9 個檔案，只剩既有的 unused-import 噪音（`router.py`
  的延遲匯入、`chat_routes.py` 的
  `time`／`timedelta`），不是本輪引入的執行路徑缺陷。
- **層分離門禁全綠**：`scripts/check_layer_separation.py` → ALL
  PASS（記憶不得走知識、學習宣稱需刪除來源、標記與登記一致）。
- **答案不是洩漏**：`census_reply_provenance.py --check` → 預存命中 0、verdict =
  not answer-leakage。
- **placement 7/7**：每一句回覆宣告的層＝實際生產者（含
  `memory-teaching`、`Zorblax` 記憶題）。

## 五、本輪量測（重跑，不是引用舊值）

| 項目                                | 結果                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| pytest `tests/ apps/backend/tests/` | **9,207 passed / 107 skipped / 0 failed**（8 分 11 秒，`-p no:randomly`）                                     |
| census（正確答案來源）              | knowledge 8（lookup 8）、math 32（computed 32）、routing 10（classifier 10）、code 0；**產生 32／50**，預存 0 |
| placement                           | **7/7**                                                                                                       |
| 層分離                              | **ALL PASS**                                                                                                  |
| 核心分                              | **0.00/10**（不變；本輪沒有任何核心產生的正確答案）                                                           |

### 純本地對話（1096 題標準集，`probe_native_dialogue.py`，2026-11-04）

| 指標                            | 結果                                                                           |
| ------------------------------- | ------------------------------------------------------------------------------ |
| 人話標準通過                    | **711/1096（64.9%）** — 問答 468/492、斷言 96/108、對話 94/100、多重事實 53/72 |
| 邊界題（`state`）               | **0/324**（知識缺口；刻意不自己教自己）                                        |
| 學習效應（冷→熱）               | **+0.4818**（穩定度 0.1028）                                                   |
| 回答來源                        | deterministic 469／template 352／neural 246／retrieval 23／other 6             |
| 核心佔比                        | **0.00**（`semantic-qa` 的相似度檢索仍算「neural」，不是核心）                 |
| 樣本有效性／一致性              | ✅（1,168 回合、381 種不同輸出、94 組教→問；少量 vs 標準量一致）               |
| 與上一輪（2026-11-02, nd9）比較 | **逐項相同**：本輪交棒與因果讓位只在有生成後端時生效，native 不受影響          |

系統分 **6.41/10**（facts 5.3／math 8.0／paraphrase 7.5／dialogue 8.8／boundary
8.9／tools
0.0），只是對照；**核心 0.00/10、核心階梯 L0、系統階梯 L2**。分數只認核心分。

## 六、後續（依序）

1. `state`
   類：要真的回答帶邊界條件的題，需要知識覆蓋＋例外推理，不是模板能補的；在做到之前門禁保持關閉。
2. `semantic-qa` 標籤與 `neural_share` 的定義校正（會改量測，單獨一輪）。
3. 核心 SNN 的規模缺口見 `CORE_GAP_ANALYSIS.md`（架構已排除，剩規模）。
