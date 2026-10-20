# 專案AI自主研究報告：後續研究與升級路徑（自動生成）

> 本文件由 `ai/research/upgrade_research.py`
> 自動生成：事實=專案自測/外部查證，推導=規則與透明公式，撰寫=資料填充模板；**LLM 僅潤色行文（數字指紋守護，失配回退）**。

## 一、摘要

本報告由專案自身AI自主生成（自己查/自己想/自己寫，LLM 僅潤色行文），生成時間 2026-10-18T22:13:09。本輪量測：測試收集 8589（pytest
--collect-only）；fact gates 全部 PASS；status_matrix 25 項（verified
15）；pre-flight 清單 5/18 已完成。自有模型體檢 11/11 通過；外部查證 3/3 組取得。native 基準：math=80%,
knowledge=26.67%, knowledge_mc=97.5%,
routing=100%。由量測推導升級候選 28 條，擇優前 3 條列為 Wave 1（見第七節）。

## 二、研究方法與自我驗證

資料鏈：以下採集器逐一執行（失敗僅記錄、報告照常生成，屬已解釋缺口而非靜默空缺）。

| 採集器                | 狀態 | 耗時   | 說明 |
| --------------------- | ---- | ------ | ---- |
| repo_stats            | ✅   | 37ms   | ok   |
| test_count            | ✅   | 7019ms | ok   |
| status_matrix         | ✅   | 28ms   | ok   |
| verification_register | ✅   | 0ms    | ok   |
| benchmarks            | ✅   | 5ms    | ok   |
| fact_gates            | ✅   | 3335ms | ok   |
| validation_reports    | ✅   | 0ms    | ok   |
| assessment_checklist  | ✅   | 0ms    | ok   |
| docs_index            | ✅   | 2ms    | ok   |
| rule_store            | ✅   | 2ms    | ok   |

自有模型體檢（每項實跑，非引用文件分數）：

| 探針                     | 結果 | 耗時   | 輸出/錯誤                                                                                                                                    |
| ------------------------ | ---- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| deterministic.math+logic | ✅   | 4ms    | math 重算 7006652 ✓；logic false                                                                                                             |
| knowledge.route          | ✅   | 0ms    | blue                                                                                                                                         |
| symbolic.route           | ✅   | 7ms    | yes                                                                                                                                          |
| rules.verify             | ✅   | 0ms    | verified kind=math reason=arithmetic_verified                                                                                                |
| formula.solve            | ✅   | 64ms   | value=12.0 formula=velocity                                                                                                                  |
| ed3n.warm_up             | ✅   | 7033ms | warm_up=461270                                                                                                                               |
| ed3n.process             | ✅   | 4ms    | 2+2 = 4                                                                                                                                      |
| garden.process           | ✅   | 6903ms | Hello! Nice to meet you! (network_output dims=0)                                                                                             |
| causal.predict           | ✅   | 0ms    | predict(user_input) → 3 條                                                                                                                   |
| knowledge_pipeline.query | ✅   | 40ms   | {'answer': 'Paris', 'confidence': 0.95, 'source': 'knowledge'}                                                                               |
| ham.query_core_memory    | ✅   | 2ms    | 2 條：{'user': 'DuckDuckGo vs Brave Search API 免費額度差異', 'assistant；{'user': 'DuckDuckGo vs Brave Search API 免費額度差異', 'assistant |

擇優公式（寫死於 ai/research/upgrade_research.py，可審計）：`score = 4×impact + 2×(4−effort) + 2×(4−risk) + source_bonus`；impact/bonus 依來源（pre-flight/benchmark/gates=3 權重），effort 依動作關鍵字（重訓/數據=3、驗證/門檻=2、註解/清理=1），risk 依來源類別（文件/採集器=1，其餘=2）。LLM 潤色僅作用於純敘述段落（表格/標題逐字保留），每段以數字指紋比對，失配即回退原稿。

## 三、累積研究資產盤點

**程式資產**：apps/backend/src 共 747 個 Python 檔、209632 行；測試收集 8589 項。unified
checkpoint：❌ 未入庫（見 A2/CKPT 路徑）。

**功能狀態（docs/status_matrix.yaml — 專案自有的機器可讀真相源）：**

| status      | 數量 |
| ----------- | ---- |
| implemented | 3    |
| verified    | 15   |
| wired       | 7    |

未達 verified 的功能（升級候選來源，共 10 項，前 12 項）：

| id                  | status      | claim                                                                  |
| ------------------- | ----------- | ---------------------------------------------------------------------- |
| llm-providers       | wired       | OpenAI/Anthropic/Gemini/Ollama/llama.cpp 可接入                        |
| model-routing       | wired       | 依任務/硬體/模式自動選後端                                             |
| continuous-learning | implemented | 對話中成長詞彙與權重                                                   |
| neural-open-domain  | implemented | 誠實標示：低                                                           |
| dashboard-panels    | wired       | Config/Model/Context/Health 可用                                       |
| offline-capability  | wired       | 無 key 可運作（部分）                                                  |
| multimodal          | implemented | 圖片/音訊/生成                                                         |
| live2d              | wired       | 桌面互動                                                               |
| luanti-agent        | wired       | 能識別環境、記住去過哪、自主探索、行為可訓練                           |
| msba-pipeline       | wired       | 全輸入經 7 層語意區塊處理，融合表示以 NeuroBlender 9D 注入 LLM context |

**規則沉澱層（本專案新增的可重用資產）**：rules=0、serves=0、feedback=0、by_kind={}（命中 0
tokens、confidence 公式 (2+successes)/(3+feedback)）。

**訓練/驗證報告工件**：{"ed3n": {"ok": true, "engines": {"ed3n": {"domains":
{"reasoning": {"hybrid": 33.33, "deterministic": 33.33, "snn_only": 1.33,
"det_carry": 32.0, "n": 150}, "math": {"hybrid": 74.0, "deterministic": 74.0,
"snn_only": 0.0, "det_carry": 74.0, "n": 150}, "logic": {"hybrid": 22.0,
"deterministic": 22.0, "snn_only": 22.0, "det_carry": 0.0, "n": 150}},
"aggregate": {"hybrid": 43.11, "deterministic": 43

**基準工件**：bench_20260922-091107.json（generated_at=2026-09-22T09:11:07）

**專案文檔索引**（行數實測）：

| 文檔                                  | 行數 | 路徑                                                  |
| ------------------------------------- | ---- | ----------------------------------------------------- |
| FRAMEWORK_OVERVIEW.md                 | 839  | docs/FRAMEWORK_OVERVIEW.md                            |
| INTELLIGENCE_ASSESSMENT.md            | 610  | docs/06-project-management/INTELLIGENCE_ASSESSMENT.md |
| MASTER_TASK_MAP.md                    | 4140 | docs/06-project-management/MASTER_TASK_MAP.md         |
| STATUS_MATRIX.md                      | 135  | docs/STATUS_MATRIX.md                                 |
| AI_SUBSTRATE_ASSESSMENT_2026-10-18.md | 189  | docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md            |
| VERIFICATION_REGISTER.json            | 142  | docs/VERIFICATION_REGISTER.json                       |
| status_matrix.yaml                    | 528  | docs/status_matrix.yaml                               |

## 四、資產 vs 替代方案：優缺點對照

對照口徑：**優缺點只由本輪實測生成**（探針/工件/規則庫），不引文件宣稱；替代方案欄為外部查證事實（來源見附錄）。LLM-only
/ 純雲端 / 大模型堆疊 等替代組合的事實依據落在「相對替代方案」欄。

| 資產類別                           | 專案實測（本輪）                                                                                                                                                                                                    | 優點（由實測生成）                           | 缺點 / 風險（由實測生成）              | 相對替代方案（外部查證）                                                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 確定性求解與驗算                   | 探針 3/3 通過；deterministic.math+logic=math 重算 7006652 ✓；logic false、formula.solve=value=12.0 formula=velocity、rules.verify=verified kind=math reason=arithmetic_ver                                          | 本輪探針 3/3；離線可用、可重算可驗錯         | （無實測缺點）                         | （對應查詢未取得事實）                                                                                                              |
| 規則沉澱重放（0-token 重用）       | rules=0 serves=0 avg_conf=0.0                                                                                                                                                                                       | 本輪探針 1/1；命中 0 tokens（實測 serves=0） | 身份保守（異數字/異措辭不命中）        | We introduce a step-granular caching abstraction for LLM serving: retrieve a single best-matching prior reques（arxiv.org）         |
| 統計語言核心（n-gram unified）     | native 基準 accuracy=80.0%（math suite）；checkpoint=缺                                                                                                                                                             | （無實測優點）                               | wiki 權重未入庫 → 統計層本輪僅確定性層 | Local AI vs Cloud AI in 2026: Key Tradeoffs / local-llm.net local-llm .net Solutions By buying situation Priva（www.local-llm.net） |
| SNN 神經核心（ED3N / GARDEN）      | 探針 3/3 通過；ed3n.warm_up=warm_up=461270、ed3n.process=2+2 = 4、garden.process=Hello! Nice to meet you! (network_output                                                                                           | 本輪探針 3/3                                 | （無實測缺點）                         | Joined Sep 3, 2026 More from turingrtss Same Model, 4 Tokenizers. 30 Percentage Points of Difference. # machin（dev.to）            |
| 知識 / 記憶 / 因果檢索             | 探針 4/4 通過；knowledge.route=blue、knowledge_pipeline.query={'answer': 'Paris', 'confidence': 0.95, 、ham.query_core_memory=2 條：{'user': 'DuckDuckGo vs Brave Search、causal.predict=predict(user_input) → 3 條 | 本輪探針 4/4                                 | （無實測缺點）                         | Local AI vs Cloud AI in 2026: Key Tradeoffs / local-llm.net local-llm .net Solutions By buying situation Priva（www.local-llm.net） |
| 雲端融合路由（unified→LLM）        | chat_pipeline 狀態：dict {'description': 'WebSocket 訊息進入後的主處理序。各階段對應真實模組； 本區段由 gen_status_matrix check 核對                                                                                | （無實測優點）                               | 依雲端可用性與 key 治理（C3）          | Local AI vs Cloud AI in 2026: Key Tradeoffs / local-llm.net local-llm .net Solutions By buying situation Priva（www.local-llm.net） |
| 外部研究管線（搜尋→事實→矛盾偵測） | 探針 0/0 通過                                                                                                                                                                                                       | 外部查證 3/3 組                              | （無實測缺點）                         | We introduce a step-granular caching abstraction for LLM serving: retrieve a single best-matching prior reques（arxiv.org）         |

## 五、實測現狀

- 測試收集：**8589**（method: pytest --collect-only）
- status_matrix：total=25，分佈={'verified': 15, 'wired': 7, 'implemented': 3}
- pre-flight：5/18 完成，待辦 13 項
- 驗證登錄：10 項 open
- fact gates：ALL PASS（exit=0）

基準明細（benchmarks/results 工件，逐套件）：

| suite                   | passed/total | accuracy | floor | 狀態   |
| ----------------------- | ------------ | -------- | ----- | ------ |
| native/math             | 32/40        | 80%      | 75    | margin |
| native/knowledge        | 4/15         | 26.67%   | 25    | margin |
| native/knowledge_mc     | 39/40        | 97.5%    | 90    | pass   |
| native/routing          | 10/10        | 100%     | 95    | margin |
| native-max/math         | 32/40        | 80%      | 75    | margin |
| native-max/knowledge    | 4/15         | 26.67%   | 25    | margin |
| native-max/knowledge_mc | 40/40        | 100%     | 90    | pass   |
| native-max/routing      | 10/10        | 100%     | 95    | margin |
| echo/math               | 1/40         | 2.5%     | 75    | below  |
| echo/knowledge          | 0/15         | 0%       | 25    | below  |
| echo/knowledge_mc       | 0/40         | 0%       | 90    | below  |
| echo/routing            | 0/10         | 0%       | 95    | below  |
| naive/math              | 14/40        | 35%      | 75    | below  |
| naive/knowledge         | 0/15         | 0%       | 25    | below  |
| naive/knowledge_mc      | 0/40         | 0%       | 90    | below  |
| naive/routing           | 0/10         | 0%       | 95    | below  |

fact gates 項：

- ✅ edge.envelope_vs_8gb
- ✅ edge.decode_bound_vs_15
- ✅ edge.load_vs_5s
- ✅ revised_design_no_blocking_corrections
- ✅ chain.chat_response_overlap
- ✅ chain.cluster_leaves_covered
- ✅ defs.und_slots
- ✅ defs.und_prompt_keys
- ✅ defs.und_influence_types
- ✅ defs.glossary_claims_mismatch
- ✅ defs.yaml_slot_divergence
- ✅ defs.js_slot_divergence
- ✅ defs.test_axis_misplacements
- ✅ defs.dead_prompt_keys
- ✅ defs.wrong_receiver_pairs
- ✅ defs.prompt_locale_parity
- ✅ defs.orphan_events_ratchet
- ✅ defs.get_parameter_keys_resolve
- ✅ defs.template_categories_resolve
- ✅ defs.magic_runtime_resolve
- ✅ config.x143_keys_resolve_in_yaml
- ✅ config.x143_values_match_code_defaults
- ✅ config.inline_default_accessor_ratchet
- ✅ version.package_json_matches_core_version
- ✅ docs.unresolved_path_refs
- ✅ docs.resolved_refs_nonvacuous
- ✅ modules.scanner_safe_on_missing_path

## 六、升級候選路徑

候選由規則從量測推導（共 28 條，來源：pre-flight
checklist 未完成項、VERIFICATION_REGISTER、status_matrix 未 verified、benchmark 地板/餘量/缺地板、fact
gates 失敗、採集器失敗、checkpoint 缺失）。每條附證據，全文如下：

| id                                            | 來源                  | 候選（title）                                                                                                                                                                                                        | I/E/R | score | wave |
| --------------------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ----- | ---- |
| D2                                            | assessment-pre-flight | 清死檔（`src/configs/system/llm.evolved.yaml`）、`routing.policy` 死碼、stats 初始化                                                                                                                                 | 3/1/2 | 24    | W1   |
| E3                                            | assessment-pre-flight | 分數類型標注嚴格遵循 INTELLIGENCE_ASSESSMENT 六型表（架構/框架/預期/訓練/驗證/實際——禁止再混用）                                                                                                                     | 3/1/2 | 24    | W1   |
| A5                                            | assessment-pre-flight | GARDEN accuracy 改實測回傳；ED3N 評估改 hold-out（`_grow_missing_keys` 不得計入評估）                                                                                                                                | 3/2/2 | 22    | W1   |
| B4                                            | assessment-pre-flight | 分通道定義「主 ai」：測評分開計 COMPOSED / fusion-google / unified / fallback                                                                                                                                        | 3/2/2 | 22    | W1   |
| BENCH-margin-knowledge                        | benchmark             | native knowledge 26.67% 雖過門但餘量 ≤5pt（地板 25.0%）                                                                                                                                                              | 3/2/2 | 22    | W1   |
| BENCH-margin-math                             | benchmark             | native math 80.0% 雖過門但餘量 ≤5pt（地板 75.0%）                                                                                                                                                                    | 3/2/2 | 22    | W1   |
| BENCH-margin-routing                          | benchmark             | native routing 100.0% 雖過門但餘量 ≤5pt（地板 95.0%）                                                                                                                                                                | 3/2/2 | 22    | W1   |
| C1                                            | assessment-pre-flight | 離線策略三選一：起 llama-server(8080, 用 data/models gguf) / 起 ollama(qwen2.5) / 純雲端——現況三者皆未接，離線開放域＝0                                                                                              | 3/2/2 | 22    | W1   |
| C3                                            | assessment-pre-flight | key 治理：`keys.*.yaml` 接載或刪除；避免單 `.env` 隱性依賴                                                                                                                                                           | 3/2/2 | 22    | W1   |
| D1                                            | assessment-pre-flight | 收斂 `llm_mode`/`deployment.mode` 雙變數分叉；修 `_allowed_types` 讀取層級                                                                                                                                           | 3/2/2 | 22    | W1   |
| E1                                            | assessment-pre-flight | 未見泛化探針：`probe_reasoning_unseen.py`（symbolic vs neural 分列）                                                                                                                                                 | 3/2/2 | 22    | W2   |
| E2                                            | assessment-pre-flight | angela_bench gate（math≥75/knowledge_mc≥90/routing≥95）作回歸地板                                                                                                                                                    | 3/2/2 | 22    | W2   |
| A2                                            | assessment-pre-flight | 決定 checkpoint 來源：從 `/media/covo/ZX` 機器取回，或本機重訓（`scripts/train_unified.py` 入庫路線）                                                                                                                | 3/3/2 | 20    | W2   |
| A3                                            | assessment-pre-flight | `train_exact_bytes`/`heldout_bpc` 接上呼叫者（訓練報表必須由留出集產生）                                                                                                                                             | 3/3/2 | 20    | W2   |
| A4                                            | assessment-pre-flight | 補齊 3 個缺數據檔或明確從 pipeline 移除（禁止靜默 skip）                                                                                                                                                             | 3/3/2 | 20    | W2   |
| A6                                            | assessment-pre-flight | 統一評測入口：`benchmark_ed3n_garden --gate`＋留出集數字入 JSON 工件（停止以 MD 散佈分數）                                                                                                                           | 3/3/2 | 20    | W2   |
| CKPT-unified                                  | assessment-pre-flight | data/checkpoints/ 無 unified 權重（統計核心未載入，log checkpoint resolved to (none)）                                                                                                                               | 3/3/2 | 20    | W2   |
| VR-config-unhonoured-sections                 | verification-register | 設定檔中宣告但無任何程式消費的項目，已逐條記錄於 tests/test_config_coverage.py::UNHONOURED_SECTIONS（含原因），並在對應 YAML 宣告處加上註解。其中 system/llm 的整個 routing.policy map 是死的：router.py:355 把 self | 2/1/2 | 19    | W2   |
| SM-promote                                    | status-matrix         | 將未 verified 的 10 項功能推進至 verified（附各自 verify_command）                                                                                                                                                   | 2/2/2 | 17    | W2   |
| VR-ai-name-config-mismatch                    | verification-register | ai_name 設為 Angela，並成為單一來源：core/system/config/identity.get_ai_name() 供 SelfModel 與 create_soul_core 使用（後者原本接受 name 參數卻忽略它）                                                               | 2/2/2 | 17    | W2   |
| VR-cli-hsp-sync-init                          | verification-register | HSP CLI 可在真實（同步）core_services 路徑下啟動，--help 不再因 await None 而死                                                                                                                                      | 2/2/2 | 17    | W3   |
| VR-environment-limits-what-cannot-be-verified | verification-register | 本環境的硬體/軟體限制決定了哪些項目無法驗證或無法實作，分三類：(A) 已處理；(B) 需先有功能/子系統，無法只靠接線完成；(C) 環境硬體限制，無論程式碼為何都無法在此驗證                                                   | 2/2/2 | 17    | W3   |
| VR-frontend-angela-app-loads                  | verification-register | 桌面版與 web viewer 現在都會載入 app.js，AngelaApp 可被 new 出來（先前完全沒有任何 script 引用它）                                                                                                                   | 2/2/2 | 17    | W3   |
| VR-frontend-proactive-bubbles                 | verification-register | Angela 主動發話（greet/comfort/remind/share/question）會把氣泡渲染進設定頁既有的 #dialogue-messages 面板                                                                                                             | 2/2/2 | 17    | W3   |
| VR-settings-autostart                         | verification-register | 設定頁的「開機自動啟動」會經 preload 的 autostart 橋接真正呼叫 main.js 的 setAutoStartup()（win32/darwin/linux）                                                                                                     | 2/2/2 | 17    | W3   |
| VR-settings-batch-a-b-c-d-wired               | verification-register | 設定頁已接上 20 項：haptics、modelScale、frameRate+renderQuality、wallpaperMode、backendIp/backendPort、speechRate/speechPitch/ttsVoice/speechLanguage、clickIntensity/touchIn                                       | 2/2/2 | 17    | W3   |
| VR-settings-remaining-need-product-decision   | verification-register | 7 個設定仍只存檔不套用，且都不是「接線」問題：enableCluster/clusterRole/clusterMemoization/clusterIntegerOnly/nodeName（後端只有 /api/v1/system/cluster/status，接上等於要建 cluster 子系統）、ttsEngin              | 2/2/2 | 17    | W3   |
| VR-webviewer-hardware-enhancement             | verification-register | hardware-enhancement-patch.js 在偵測器缺少 detect()/_assessCapabilities() 時會如實跳過並記錄警告，而不是丟出未處理異常                                                                                               | 2/2/2 | 17    | W3   |

證據摘要（逐條）：

- **D2**（score=24）：清死檔（`src/configs/system/llm.evolved.yaml`）、`routing.policy`
  死碼、stats 初始化　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] D2

- **E3**（score=24）：分數類型標注嚴格遵循 INTELLIGENCE_ASSESSMENT 六型表（架構/框架/預期/訓練/驗證/實際——禁止再混用）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] E3

- **A5**（score=22）：GARDEN
  accuracy 改實測回傳；ED3N 評估改 hold-out（`_grow_missing_keys`
  不得計入評估）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] A5

- **B4**（score=22）：分通道定義「主 ai」：測評分開計 COMPOSED / fusion-google /
  unified / fallback　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] B4

- **BENCH-margin-knowledge**（score=22）：固定失敗樣本為回歸集，防止跌破门檻　證據：margin=1.67pt

- **BENCH-margin-math**（score=22）：固定失敗樣本為回歸集，防止跌破门檻　證據：margin=5.0pt

- **BENCH-margin-routing**（score=22）：固定失敗樣本為回歸集，防止跌破门檻　證據：margin=5.0pt

- **C1**（score=22）：離線策略三選一：起 llama-server(8080, 用 data/models gguf)
  / 起 ollama(qwen2.5)
  / 純雲端——現況三者皆未接，離線開放域＝0　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] C1

- **C3**（score=22）：key 治理：`keys.*.yaml` 接載或刪除；避免單 `.env`
  隱性依賴　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] C3

- **D1**（score=22）：收斂 `llm_mode`/`deployment.mode` 雙變數分叉；修
  `_allowed_types` 讀取層級　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] D1

- **E1**（score=22）：未見泛化探針：`probe_reasoning_unseen.py`（symbolic vs
  neural 分列）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] E1

- **E2**（score=22）：angela_bench
  gate（math≥75/knowledge_mc≥90/routing≥95）作回歸地板　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] E2

- **A2**（score=20）：決定 checkpoint 來源：從 `/media/covo/ZX`
  機器取回，或本機重訓（`scripts/train_unified.py`
  入庫路線）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] A2

- **A3**（score=20）：`train_exact_bytes`/`heldout_bpc`
  接上呼叫者（訓練報表必須由留出集產生）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] A3

- **A4**（score=20）：補齊 3 個缺數據檔或明確從 pipeline 移除（禁止靜默 skip）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] A4

- **A6**（score=20）：統一評測入口：`benchmark_ed3n_garden --gate`＋留出集數字入 JSON 工件（停止以 MD 散佈分數）　證據：docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: -
  [ ] A6

- **CKPT-unified**（score=20）：本機重訓入庫或自外置機器復原（併同 A2 決策）　證據：checkpoints 現況：['msba/v0001/cross_attention.npy',
  'msba/v0001/history.json', 'msba/v0001/meta.json', 'msba/v0001/trainin

- **VR-config-unhonoured-sections**（score=19）：實作 complexity 路由後，移除對應註解與清單條目，test_routing_policy_map_is_either_used_or_documented 會要求同步　證據：why_unverified: 本項為靜態分析結論，非執行期行為：無法在此環境示範缺少的路由策略或指令觸發功能;
  area: other

- **SM-promote**（score=17）：逐項執行 verify_command 並回填 evidence：llm-providers,
  model-routing, continuous-learning, neural-open-domain, dashboard-panels,
  offline-capability, multimodal,
  live2d（等 10 項）　證據：status 分佈：{'verified': 15, 'wired': 7,
  'implemented': 3}

- **VR-ai-name-config-mismatch**（score=17）：決定後：若採單一來源，讓程式讀 ai_name（預設維持 Angela），並更新 YAML；若維持 Angela，將 YAML 改為 Angela 使設定與實作一致　證據：why_unverified: 這是產品命名決策：套用設定會把對外名稱從 Angela 改成 Miko，需使用者決定;
  area: other

- **VR-cli-hsp-sync-init**（score=17）：cd packages/cli && python3 cli/main.py
  --help　證據：why_unverified: 已於本機以 python3 cli/main.py
  --help 實測通過；此條保留作為迴歸錨點; area: other

- **VR-environment-limits-what-cannot-be-verified**（score=17）：C 類需在有 GPU 的機器或安裝 Electron 後驗證：python3
  scripts/gen_project_map.py 會顯示本條；安裝 Electron 後可依各條 how_to_verify 逐項改為 verified　證據：why_unverified: 分類本身是本機偵測結果，非執行期行為。A=已修復並測試；B=需產品決策（cluster 子系統、command
  triggers、複雜度路由、後端 TTS 端點）；C=本機無 GPU（無 /dev/nvidi; area:
  other

- **VR-frontend-angela-app-loads**（score=17）：開啟桌面版，開發者工具主控台不應出現 ReferenceError:
  AngelaApp is not
  defined，且視窗狀態列應由載入流程更新　證據：why_unverified: 需要 Electron
  / 瀏覽器載入頁面；本機無 GUI，僅能靜態驗證 script src 與順序; area: other

- **VR-frontend-proactive-bubbles**（score=17）：讓後端觸發任一 proactive
  action（例：情緒路由到 comfort），確認對話面板出現該則訊息而非只有 Live2D 動作　證據：why_unverified: 需要後端推播 proactive
  action 且前端可見；本機無 GUI 可觀察畫面; area: other

- **VR-settings-autostart**（score=17）：啟動桌面版 → 設定 → 勾選「開機自動啟動」→ 確認作業系統登入項出現/消失（Linux:
  ~/.config/autostart/angela-ai.desktop；macOS: 系統設定「登入項」；Windows: 登錄檔 Run）　證據：why_unverified: 需要啟動 Electron 桌面程式並檢查 OS 登入項；本機無顯示器，無法點擊設定頁;
  area: settings

- **VR-settings-batch-a-b-c-d-wired**（score=17）：啟動桌面版 → 設定 → 逐項修改並儲存 → 確認：haptics、模型縮放、FPS/品質、桌布模式與效果、後端 IP/埠重新連線、語速/音高/語音、情緒強度、主視窗透明度、系統音訊（Linux 應顯示不支援）、除錯模式日誌層級、關閉自動切換後低幀率不再降級（開啟時會降級）、閒置 60 秒後 Angela 播放 idle 動作、任何操作後恢復　證據：why_unverified:
  applySettingsToApplication 的呼叫鏈可用靜態與 node 行為測試驗證，但「設定視窗勾選後桌面版實際反應」需要啟動 Electron，本機無顯示器;
  area: settings

- **VR-settings-remaining-need-product-decision**（score=17）：決策後逐項處理。註：autoSwitchFallback 與 idleMode 原先也被列為需決策，後來確認 setAutoAdjust() 與 idle
  motion 早已存在、缺的只是呼叫路徑，已完成接線　證據：why_unverified: 這些需要產品決策（要建什麼、語意是什麼），不是機械式接線；在決策前維持現狀並記錄在此，避免再被當成已完成;
  area: settings

- **VR-webviewer-hardware-enhancement**（score=17）：開啟 web viewer →
  console 應出現 [HW-Patch] ...
  skipped 警告，且後續初始化不中斷　證據：why_unverified: 需要 web
  viewer 實際載入並觀察 console；本機無 GUI; area: other

## 七、擇優排序與路線圖

**擇優（公式排序前 3，建議先做）**：

1. **D2** — 清死檔（`src/configs/system/llm.evolved.yaml`）、`routing.policy`
   死碼、stats 初始化（score=24，來源 assessment-pre-flight）
2. **E3**
   — 分數類型標注嚴格遵循 INTELLIGENCE_ASSESSMENT 六型表（架構/框架/預期/訓練/驗證/實際——禁止再混用）（score=24，來源 assessment-pre-flight）
3. **A5** — GARDEN
   accuracy 改實測回傳；ED3N 評估改 hold-out（`_grow_missing_keys`
   不得計入評估）（score=22，來源 assessment-pre-flight）

**Wave
1**（最高分 1/3，含上述擇優項）：D2(24)、E3(24)、A5(22)、B4(22)、BENCH-margin-knowledge(22)、BENCH-margin-math(22)、BENCH-margin-routing(22)、C1(22)、C3(22)、D1(22)

**Wave
2**：E1(22)、E2(22)、A2(20)、A3(20)、A4(20)、A6(20)、CKPT-unified(20)、VR-config-unhonoured-sections(19)、SM-promote(17)、VR-ai-name-config-mismatch(17)

**Wave
3**（其餘，含文件/採集器修復）：VR-cli-hsp-sync-init(17)、VR-environment-limits-what-cannot-be-verified(17)、VR-frontend-angela-app-loads(17)、VR-frontend-proactive-bubbles(17)、VR-settings-autostart(17)、VR-settings-batch-a-b-c-d-wired(17)、VR-settings-remaining-need-product-decision(17)、VR-webviewer-hardware-enhancement(17)

排序完全由公式決定（公式與規則表見第二節），本節無人工覆寫。

## 八、後續研究議題

**源自 pre-flight 的研究型待辦**：

- [E1] 未見泛化探針：`probe_reasoning_unseen.py`（symbolic vs neural 分列）
- [E2] angela_bench gate（math≥75/knowledge_mc≥90/routing≥95）作回歸地板
- [E3] 分數類型標注嚴格遵循 INTELLIGENCE_ASSESSMENT 六型表（架構/框架/預期/訓練/驗證/實際——禁止再混用）

**外部查證矛盾偵測**：本輪未取得矛盾（或外部查證未成功，見附錄採集表）。

**基準面開放問題**：

- native knowledge 26.67% 雖過門但餘量 ≤5pt（地板 25.0%）
- native math 80.0% 雖過門但餘量 ≤5pt（地板 75.0%）
- native routing 100.0% 雖過門但餘量 ≤5pt（地板 95.0%）

**開放研究問題（由量測缺口推導，非人工列點）**：

- native math 餘量僅 5.0pt，跌破前該固定哪些失敗樣本為回歸集？
- native knowledge 餘量僅 1.7pt，跌破前該固定哪些失敗樣本為回歸集？
- native routing 餘量僅 5.0pt，跌破前該固定哪些失敗樣本為回歸集？
- unified 權重復原（A2）後，bpc 是否與歷史 UNIFIED_AI_RESULTS.md 的 2.711 一致（重現性驗證）？
- status_matrix
  10 項未 verified 中，哪些能用自動 verify_command 直接推進、哪些需先補實作？

## 九、附錄：資料源與重現命令

**資料源（全部可重現）**：

- docs/status_matrix.yaml、docs/VERIFICATION_REGISTER.json、docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md（pre-flight）、benchmarks/results/、scripts/validation_report_*.json、data/rules/solution_rules.json

**重現命令**：

```bash
.venv/bin/pytest --collect-only -q -o addopts=
python3 scripts/check_fact_gates.py
python3 scripts/run_benchmarks.py --backend native --gate-native
python3 scripts/generate_upgrade_report.py --no-polish   # 重生成（不含 LLM 潤色）
```

**外部查證來源**：

- [small local LLM versus cloud LLM tradeoffs latency privacy q…] Local AI vs
  Cloud AI in 2026: Key Tradeoffs - local-llm.net —
  https://www.local-llm.net/learn/local-vs-cloud-ai/
- [small local LLM versus cloud LLM tradeoffs latency privacy q…] Local LLM vs
  Cloud LLM: Differences & Gap [2026] —
  https://arte.itlibra.com/en/articles/local-llm-vs-cloud-llm-comparison
- [small local LLM versus cloud LLM tradeoffs latency privacy q…] Local LLM
  Trade-Offs 2026: Privacy vs Speed vs Quality —
  https://www.promptquorum.com/local-llms/local-llm-limitations
- [spiking neural network advantages limitations compared with …] Spiking Neural
  Networks vs Transformers: I Tested Both. Here is What ... —
  https://dev.to/turingrtss/spiking-neural-networks-vs-transformers-i-tested-both-here-is-what-matters-427e
- [spiking neural network advantages limitations compared with …] Why Spiking
  Neural Networks May Outpace Transformers —
  https://ersinyildiz.com/en/blog/spiking-neural-networks-vs-transformers-i-tested-both-here-is-what-matters-en-2026
- [spiking neural network advantages limitations compared with …] Why Spiking
  Neural Networks Lag Behind Transformers in 2026 —
  https://logicnest.cc/why-spiking-neural-networks-lag-behind-transformers-in-2026/
- [serving cached verified answers instead of regenerating LLM …] StepCache:
  Step-Level Reuse with Lightweight Verification and Selective ... —
  https://arxiv.org/pdf/2603.28795
- [serving cached verified answers instead of regenerating LLM …] KV Cache
  Optimization Strategies for Scalableand Efficient LLM Inference —
  https://arxiv.org/html/2603.20397v1
- [serving cached verified answers instead of regenerating LLM …] Optimize LLM
  response costs and latency with effective caching —
  https://aws.amazon.com/blogs/database/optimize-llm-response-costs-and-latency-with-effective-caching/

**LLM 潤色記錄**（只潤色、數字指紋守護）：

| 區塊                                                                        | 潤色結果              |
| --------------------------------------------------------------------------- | --------------------- |
| p3:本報告由專案自身AI自主生成（自己查/自己想/自己寫，LLM 僅潤色行文），生成 | polished              |
| p8:擇優公式（寫死於 ai/research/upgrade_research.py                         | polished              |
| p9:**程式資產**：apps/backend/src 共 747 個 Python                          | fallback:數字指紋失配 |
| p14:**規則沉澱層（本專案新增的可重用資產）**：rules=0、serves=0、           | polished              |
| p15:**訓練/驗證報告工件**：{"ed3n": {"ok": true, "eng                       | polished              |
| p16:**基準工件**：bench_20260922-091107.json（gene                          | polished              |
| p21:- 測試收集：**8589**（method: pytest --collect                          | polished              |
| p25:- ✅ edge.envelope_vs_8gb - ✅ edge.decode                              | polished              |
| p26:候選由規則從量測推導（共 28 條，來源：pre-flight checklis               | polished              |
| p29:- **D2**（score=24）：清死檔（`src/configs/syst                         | polished              |
| p30:- **E3**（score=24）：分數類型標注嚴格遵循 INTELLIGEN                   | polished              |
| p31:- **A5**（score=22）：GARDEN accuracy 改實測回傳                        | polished              |
| p32:- **B4**（score=22）：分通道定義「主 ai」：測評分開計 COM               | polished              |
| p33:- **BENCH-margin-knowledge**（score=22）：固                            | polished              |

生成耗時：52.3s；生成時間：2026-10-18T22:13:09。
