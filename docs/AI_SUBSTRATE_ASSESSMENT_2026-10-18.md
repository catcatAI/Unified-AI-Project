# AI 底層評估報告（訓練/運行前確認）

日期：2026-10-18 ｜ 範圍：Unified-AI-Project 文字 AI 底層（unified_engine / ED3N
/ GARDEN /
LLM 服務層 / 部署配置）性質：**先確認、後訓練/運行**——本報告為只讀勘察結論，未修改任何生產碼。證據基準：全部結論附
`檔案:行號` 或本機實測（log/網路埠/檔案系統）。

---

## 一、底層盤點：專案的「AI 底層」實際是五層混合

```
┌─────────────────────────────────────────────────────────────────┐
│ L5 路由/融合層  chat_routes → AngelaLLMService(router.py)        │
│    RoutingEngine 連接器序：pipeline_math→…→memory→knowledge→     │
│    neural_bridge→main_llm→fallback；honest-gate/cloud-fusion     │
├─────────────────────────────────────────────────────────────────┤
│ L4 LLM 後端層   unified(本專案核心) / google(Gemini, 有真key) /   │
│    llamacpp×2 / ollama / openai / anthropic（後三者本機不健康）   │
├─────────────────────────────────────────────────────────────────┤
│ L3 兜底/模板層  _ed3n_fallback_text → composed-template →        │
│    _fb_pure_template（7 級 fallback 鏈，router.py:3171-3191）    │
├─────────────────────────────────────────────────────────────────┤
│ L2 自研神經層   ED3N(真 LIF SNN+Hebbian+詞典) / GARDEN(真 LIF     │
│    TensorSNN+Hebbian+錨點解碼) — ModelBus 直出門檻 ≥0.8          │
├─────────────────────────────────────────────────────────────────┤
│ L1 統計內核     UnifiedEngine = FixedSizeCore（雜湊 n-gram 共現    │
│    計數表, 323MiB 固定）+ SemanticQA(真對比學習) + 確定性層       │
│    (math/logic Python ast) + REFLEX 罐頭                          │
└─────────────────────────────────────────────────────────────────┘
```

### L1 UnifiedEngine（本專案的「一號底層」）

- **本質：雜湊 n-gram 共現統計，不是神經網路**——無矩陣乘、無梯度、無損失函式；訓練＝向量化計數遞增（`core_model.py:172-416`）。
- 固定大小 ≈ **323.5 MiB / 8,480 萬 float32 格**（slots=65536 的 5 張 64MiB 表 +
  pos/trans/uni/bool）；詞表＝**256 UTF-8 byte**，無 BPE。
- `process()` 路由為 first-match-wins 五路：reflex 罐頭 →
  deterministic-math/logic（Python ast，docstring 自認 "not AI"）→
  SemanticQA（**唯一真梯度**：對比 SGD + ONNX MiniLM 嵌入）→ 統計投票層 →
  **miss 即原樣 echo**（`unified_engine.py:516-548`）。
- **對話路徑不生成 token**：全部是挑選/拼裝；byte 生成器僅存在於評估（`core_model.py:684-716`）。開放問答
  `answer_votes` 退化為 `chr(peak)`
  單字元（`core_model.py:381-398`，docstring 自認 intractable）。
- 能力實測（`docs/03-technical-architecture/UNIFIED_AI_RESULTS.md`）：enwik9 留出 bpc
  2.403（優於 gzip 2.951、近 bz2
  2.333）；數學留出 1.000、邏輯 0.626；**縮放負結果**（193→2057 MiB
  bpc 平線）；生成 300-byte 最長逐字匹配僅 10-13 bytes。

### L2 ED3N / GARDEN（自研神經層）

- 兩者 SNN 均為**真 LIF**（膜電位/閾值/不應期：`ed3n/snn/lif_neuron.py:14-53`；`garden/snn_core.py:673-710`），非 mock。
- 但 ED3N
  **預設 auto 路徑不經 SNN**（`snn_mode=False`，`ed3n_engine.py __init__`）；466 詞條/89
  reflex 全來自 config
  JSON 內建先驗，**非訓練產物**（`dictionary_layer.py:550`）。
- 兩層 growth 機制已標
  **DeprecationWarning：應由 UnifiedEngine 取代**（`dictionary_layer.py:28-32`、`garden_engine.py:52-56`）——官方定位即「向 L1 遷移中」。
- ModelBus 直出門檻 ≥0.8（MetaController 可調）才成為最終回答；否則 draft 進 LLM 精煉（`router.py:2946-3029`）。

### L4/L5 服務與路由層

- 本機實測
  `available=['unified','google']`，active=**unified**；`preferred_backend='llamacpp'`
  被 prune 後落空。
- **雲端融合是活的**：deployment.mode=**local+llm**（`llm.user.yaml:21`
  覆寫 default 的 local）→ 開放域問題實走
  `[fusion] open-domain → google`（真 Gemini）。
- 主聊天回答是**三通道混合**：社交寒暄→`composed-template` 模板；開放域→google
  fusion；確定性形狀→unified
  ast/QA；全部失敗→7 級模板 fallback。**不存在單一「純 LLM 通道」**。
- 本機閒置資源：`data/models/qwen2.5-1.5b-instruct-q4_k_m.gguf`（1.1GB）與
  `ollama`(qwen2.5) 均在，但 8080/8081/11434
  **全未監聽**——離線本地 LLM 路徑未啟用。

---

## 二、訓練/權重現場核驗（最重要事實）

| 項目                        | 宣稱                                                                        | 本機實測                                                                                                                                     | 結論                                         |
| --------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| unified checkpoint          | wiki 500MB/128k npz、full_train bpc 2.711（`UNIFIED_AI_RESULTS.md:16-101`） | `data/checkpoints/unified/` **不存在**；全 repo 無 `unified*.npz`；log `checkpoint resolved to (none)`                                       | **缺**——統計核心未載入，unified 只剩確定性層 |
| 產物可重現性                | `train_exact_bytes`/`heldout_bpc` 量測                                      | 兩函式**全 repo 零呼叫者**（`trainer.py:120-155`）；產物應落 `/media/covo/ZX`（另一機器）                                                    | **不可重現**（生產腳本未入庫）               |
| ED3N acc=0.914              | 訓練 84,726 math + 11,180 knowledge                                         | 評估為**訓練集 in-loop**，且 `_grow_missing_keys` miss 即 grow 進字典（`ed3n_trainer.py:109-135`）；raw_datasets 缺 knowledge 檔             | **背自己，非泛化**                           |
| GARDEN acc=0.700            | 訓練收斂                                                                    | **硬編碼常數** `confidence_value("train.garden.record_accuracy", 0.7)`（`train_pipeline.py:1535`），`learn_batch` 不回傳 accuracy            | **假數字**                                   |
| JointTrainer 0.939          | 訓練指標                                                                    | 訓練集 in-loop（`ed3n_trainer.py:587`）                                                                                                      | 指標有效但非留出                             |
| 多模態 p29 權重             | 已訓練                                                                      | `data/multimodal/weights/` **為空**                                                                                                          | 缺                                           |
| ed3n_full/garden_checkpoint | train_pipeline 產物                                                         | `data/checkpoints/` 全無                                                                                                                     | 缺                                           |
| 評估污染                    | —                                                                           | `UNIFIED_AI_RESULTS.md:5-18` 自記舊 2.33x 因 4MB chunk 溢位**污染撤回**；`UNIFIED_AI_ENGINE.md:34` 「評估用訓練集當測試集 → 分數全是背自己」 | 歷史污染已自認，現行 0.914/0.700 仍屬此類    |
| 專案自評                    | —                                                                           | `UNIFIED_AI_ENGINE.md:5`：「**hash n-gram 架構無法匹配 LLM**」；`STATUS_MATRIX.md:25`：神經開放域泛化「硬指標 symbolic 100 / neural 0」      | 官方結論已誠實                               |

**P0 級發現（會直接讓下一次訓練白跑）**：

1. **npz key 前綴斷鏈**：`engine.save()` 寫
   `core_pos/trans/gram…`（`unified_engine.py:571-580`），provider 載入要無前綴
   `pos/trans/gram…`（`providers/unified.py:107`）且不回退 `engine.load()` →
   **訓練→存檔→載入鏈在最後一米斷裂**，即使把 checkpoint 拷回本機也讀不到。
2. 訓練數據集缺
   `knowledge_extra/reasoning_train/tooluse_train`（`train_pipeline.py:140-148`
   會 skip）。
3. 評估基準若沿用現行 train_pipeline 報表 → 重跑只會複製「背自己」分數，**必須先換留出集**。

---

## 三、與其他 AI 底層的比較

### A. vs 本地 Transformer 小模型（llama.cpp / Ollama / Qwen-1.5B 量化——本機已有資源）

| 維度            | 專案底層（unified+ED3N+GARDEN）                      | 本地小 LLM（qwen2.5-1.5b q4 ≈1.1GB）             |
| --------------- | ---------------------------------------------------- | ------------------------------------------------ |
| 開放域語言生成  | **≈0**（選取/拼裝，echo 兜底；生成保真 10-13 bytes） | **可用**（真正自回歸，中文對話流暢）             |
| 確定性數理/邏輯 | **強**（Python ast，留出 1.000；無幻覺）             | 弱（需外掛工具/RAG 校正，會幻覺）                |
| 資源/啟動       | 323MiB 固定陣列、零外部進程、毫秒級                  | 需常駐 server/數 GB RAM、秒級啟動                |
| 可解釋/可審計   | **強**（查表、計數、路由全透明）                     | 黑盒                                             |
| 長程上下文      | 512 窗口共現，無注意力                               | 標準 KV 上下文                                   |
| 學習/適應       | 單遍計數即時學、零 GPU                               | 需微調（LoRA/全量），門檻高                      |
| 現狀            | checkpoint 缺 + 評估污染                             | **模型已在本機、server 未起**（8080/11434 靜默） |
| 定位            | 確定性內核＋記憶／管線輔助                           | 開放域語言主力                                   |

→
**互補而非競品**：專案的正確組合＝「確定性內核管對錯、小 LLM 管說話、fusion 層管何時用誰」。現行主路徑已這樣設計（`_maybe_cloud_fusion`），但
**`generate_text` 內部元件旁路了 fusion**（見問題 #7）。

### B. vs 雲端 API（Gemini/OpenAI/Claude）

- 雲端優：品質天花板、免本地資源——本專案已實裝融合且 Gemini
  key 真實有效（`.env`，log `[fusion] open-domain → google`）。
- 雲端劣：隱私/費用/斷網即盲、key 治理薄弱（`keys.default.yaml`
  無任何程式碼載入、唯 `.env` 單 key）。
- 專案差異：**honest-gate 融合是有架構價值的**——確定性層先答對錯、LLM 只接開放域，比純 LLM 更省 token 且可審計；劣勢是融合只覆蓋主聊天，不覆蓋
  `generate_text`/研究合成等旁路。

### C. vs 傳統統計語言模型（n-gram/Kneser-Ney、壓縮器）

- unified 即此類：優＝快、透明、bpc 壓過 gzip、固定大小無 OOM；劣＝無語義、開放域零泛化。
- 專案已做的對照實驗：byte 級 KN **無優勢**、hard
  backoff 最優（`unified_engine_principle_experiments.py`）；縮放平線——**此路線天花板已被自己量測封頂**。

### D. vs 神經形態 SNN（脉衝神經網路路線）

- 專案 SNN 為真 LIF，但審計結論「marginal
  benefit（16-23%）」（`MASTER_TASK_MAP.md:3441`、AGENTS §X
  #199），且 ED3N 預設路徑根本不經 SNN。
- 對比主流（Norse/snnTorch 等 surrogate-gradient 生態）：無梯度訓練生態、無規模化證據；價值在低功耗潛力與可解釋性——以現狀屬**研究性資產而非生產依賴**，不應列入「訓練成效」預期。

### E. 綜合定位（本報告核心判斷）

專案底層不是「另一個 LLM」，而是三件真實資產的組合：

1. **確定性正確性內核**（ast 數學/符號推理/知識庫——INTELLIGENCE_ASSESSMENT 實測 9.5-10/10，是相對純 LLM 的**真優勢**）；
2. **離線共現記憶**（unified 統計層＋詞典＋向量庫——壓縮媲美 bz2、零依賴）；
3. **融合路由架構**（honest-gate/fusion/7 級 fallback——決定「誰在何時說話」）。純開放域語言能力**從來不該由自研統計內核承擔**（專案自己已結論「無法匹配 LLM」），應由本地小 LLM＋雲端 fusion 承擔——本機 qwen
   gguf 閒置正是現成短板。

---

## 四、問題清單（勘察過程發現，按嚴重度）

### P0 — 阻斷「訓練有效」或「AI 路徑真實」的確認項

| #   | 問題                                                                                                                   | 證據                                                                             |
| --- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | unified checkpoint 缺失 → 統計核心未載入                                                                               | log `checkpoint resolved to (none)`；`data/checkpoints/unified/` 不存在          |
| 2   | **save→load npz key 前綴不一致**（`core_*` vs 無前綴）→ 訓練產物載不進 provider                                        | `unified_engine.py:571-580` vs `providers/unified.py:107`                        |
| 3   | 訓練/評估生產腳本未入庫（`train_exact_bytes`/`heldout_bpc` 零呼叫者）→ 指標不可重現                                    | `trainer.py:120-155`                                                             |
| 4   | GARDEN acc=0.700 為硬編碼常數；ED3N acc 為訓練集 in-loop＋miss 即存字典 → 0.914/0.700 不可作成效                       | `train_pipeline.py:1535`、`ed3n_trainer.py:109-135`                              |
| 5   | 歷史評估污染已自認（chunk 溢位撤回、訓練集當測試集），現行報表未換留出集                                               | `UNIFIED_AI_RESULTS.md:5-18`、`UNIFIED_AI_ENGINE.md:34,122-123`                  |
| 6   | ed3n/garden 無 LLM 後端工廠，config 註解與現實不符；`Model Bus initialized with 0 models`                              | `router.py:280-288`、`llm.default.yaml:17`                                       |
| 7   | **`generate_text` 無 fusion**（僅主路徑有）→ 研究合成等內部元件只能吃 unified 18 字輸出（實測觸發降級）                | `router.py:4427-4466` 無 `_maybe_cloud_fusion`；log `[Research-Synth] …18 chars` |
| 8   | llm_routes decorator 錯位 regression：`GET /llm/status`、`POST /llm/config` 回 422（桌面設定頁壞，測試直呼函式未察覺） | `llm_routes.py:26-27,140-141` vs `:50,:205`                                      |
| 9   | 訓練數據集缺 3 檔（knowledge/reasoning/tooluse）→ pipeline 靜默 skip                                                   | `train_pipeline.py:140-148`；raw_datasets 實查                                   |

### P1 — 品質/一致性

| #   | 問題                                                                                                             | 證據                                                 |
| --- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 10  | `self.llm_mode`（deployment.mode 優先）遮蔽 `settings.llm_mode`；auto 模式永不觸發                               | `router.py:481-486`                                  |
| 11  | `_allowed_types` fallback 讀錯層級（頂層 `llm_mode` 不存在 → 靜默降 local）                                      | `router.py:933-937`                                  |
| 12  | unified 後端只吃 `prompt`，丟 system_prompt＋歷史 → 同輸入對 unified/google 語義不對等                           | `unified.py:172-181`                                 |
| 13  | 開放問答 `answer_votes` 退化 `chr(peak)` 單字元                                                                  | `core_model.py:381-398`                              |
| 14  | SemanticQA 權重不持久化（load 即 10 epochs 重訓＋`register_modality` 重初始化）                                  | `semantic_qa.py:18,272-273,327`                      |
| 15  | `_frozen` 標誌無強制力（freeze 後仍可 learn）                                                                    | `unified_engine.py:244-248` 不檢查                   |
| 16  | SNN marginal（16-23%）、ED3N 預設路徑不經 SNN                                                                    | `MASTER_TASK_MAP.md:3441`、`ed3n_engine.py __init__` |
| 17  | 466 詞條/89 reflex 係 config 內建先驗，非訓練成果（易誤讀）                                                      | `dictionary_layer.py:550`                            |
| 18  | 本機 qwen gguf＋ollama 均在但 server 全未起（8080/8081/11434 靜默）→ 離線 LLM 底層閒置                           | 實測                                                 |
| 19  | `preferred_backend=llamacpp` 但後端必被 prune → 每次啟動白付 3×5s health timeout                                 | `llm.user.yaml:20`＋log                              |
| 20  | 死檔/死碼：`src/configs/system/llm.evolved.yaml`(gpt-4)、`keys.default.yaml` 無消費者、`routing.policy` 賦值不讀 | `router.py:529`、tiered_loader 選根實測              |
| 21  | `stats.cache_hits` 未初始化即 `+=` 混用 `.get`                                                                   | `router.py:740` vs `:504-514`                        |
| 22  | 主回答三通道混合（模板/google/unified）——「主ai＝什麼」無單一定義，測評需分通道                                  | log COMPOSED/LLM_FULL/fusion 各自計數                |

### P2 — 記錄性

- `qa_fallback.json`
  12 條＋單條硬編 sky→blue 最後手段（`unified_engine.py:175-194`）。
- `llm_decision_loop` 曾 600s 降級 rule fallback（log 2026-10-18 14:58）。
- black 全庫 71 檔既有漂移；`llm.evolved.yaml` 位置歧義（src/configs vs
  configs）。

---

## 五、訓練/運行前檢查清單（Pre-flight Checklist）

**A. 權重與可重現性（先修再練）**

- [x] A1 修 npz key 前綴斷鏈（provider 讀 `core_*`
      或 save 寫無前綴＋互相回退），並加 round-trip 測試 ← **不修則訓練白跑** —
      ✅ 2026-10-18：`_load_checkpoint_weights` 改 `engine.load()`
      全狀態優先＋容錯移植雙鍵（`core_*`/裸鍵+feat/feat_bool），round-trip 測試
      `test_unified_engine.py::TestProviderNpzChain` 通過（commit 7a11c9c22）
- [ ] A2 決定 checkpoint 來源：從 `/media/covo/ZX`
      機器取回，或本機重訓（`scripts/train_unified.py` 入庫路線）
- [ ] A3 `train_exact_bytes`/`heldout_bpc`
      接上呼叫者（訓練報表必須由留出集產生）
- [ ] A4 補齊 3 個缺數據檔或明確從 pipeline 移除（禁止靜默 skip）
- [x] A5 GARDEN accuracy 改實測回傳；ED3N 評估改 hold-out（`_grow_missing_keys`
      不得計入評估）— ✅ 2026-10-19：GARDEN `_eval_garden_holdout`（`process`
      實測 contains-match，替掉 `train.garden.record_accuracy`
      0.7 假常數）；ED3N
      `ED3NTrainer.evaluate_holdout`（純推論，不 grow/不調權重）＋`_holdout_split`
      每 10th 切分（cap 500/200）；16 新測試
      `tests/ai/ed3n/test_holdout_eval.py`，全套 8504 passed 0 failed
- [ ] A6 統一評測入口：`benchmark_ed3n_garden --gate`＋留出集數字入 JSON 工件（停止以 MD 散佈分數）

**B. AI 路徑真實性（先確認「走 AI」再談「AI 好不好」）**

- [x] B1 `generate_text`
      接 fusion 或明式指定後端（研究合成/內部元件不該旁路 google）— ✅
      2026-10-18：`generate_text` 內建 `_maybe_cloud_fusion`
      嘗試（開域→unified→google 同主路徑），`test_generate_text_fusion.py`
      4 測試通過
- [x] B2 修 llm_routes decorator 錯位（/llm/status、/llm/config 422）— ✅
      2026-10-18：decorator 歸位 `llm_status`/`llm_config_set`，另新增
      `GET /llm/solution-rules` 統計端點，`TestRouteBinding` 5 測試通過
- [x] B3 更正 `llm.default.yaml:17` 註解（ed3n/garden 不可註冊）；決定 ModelBus
      0 models 是終態還是待接 — ✅ 2026-10-18：註解已更正；**決定：ModelBus 0
      models 為終態**（註冊制已由 LLM bus + PriorityNegotiator 取代，不再接）
- [ ] B4 分通道定義「主 ai」：測評分開計 COMPOSED / fusion-google / unified /
      fallback

**C. 環境選擇（運行前定案）**

- [ ] C1 離線策略三選一：起 llama-server(8080, 用 data/models gguf)
      / 起 ollama(qwen2.5) / 純雲端——現況三者皆未接，離線開放域＝0
- [x] C2 `preferred_backend` 對齊可用後端（否則每啟動 15s health 白付）— ✅
      2026-10-18：`preferred_backend: llamacpp→unified`（主路徑），llamacpp-local/qwen
      `enabled:false`（8080/8081 curl 實測未聽，停啟動白付 3×5s health 探測）
- [ ] C3 key 治理：`keys.*.yaml` 接載或刪除；避免單 `.env` 隱性依賴

**D. 配置一致性**

- [ ] D1 收斂 `llm_mode`/`deployment.mode` 雙變數分叉；修 `_allowed_types`
      讀取層級
- [x] D2 清死檔（`src/configs/system/llm.evolved.yaml`）、`routing.policy`
      死碼、stats 初始化— ✅ 2026-10-19：刪 `src/configs` 死檔（canonical
      `configs/system/llm.evolved.yaml` 保留）；移除 `router._angela_routing`
      死屬性＋更新 `test_routing_policy_map_is_either_used_or_documented`
      契約；`stats["cache_hits"]=0` 初始化＋2 新測試，75 passed

**E. 評估基準（重訓前先立）**

- [ ] E1 未見泛化探針：`probe_reasoning_unseen.py`（symbolic vs neural 分列）
- [ ] E2 angela_bench gate（math≥75/knowledge_mc≥90/routing≥95）作回歸地板
- [x] E3 分數類型標注嚴格遵循 INTELLIGENCE_ASSESSMENT 六型表（架構/框架/預期/訓練/驗證/實際——禁止再混用）—
      ✅
      2026-10-19：§1.1 分數總表加「分數類型」欄（11 維度全標注）；§1.2「訓練+驗證 3.0」行標「已廢混合記法」；§2.2 隨機權重行標 ED3N 汙染/GARDEN 硬編碼假常數；§3.2 訓練基線加 E3 警示框；「知識+推理 8.6」行標「訓練（污染）⚠️」

---

## 五-b、升級前基準計分（六型口徑，2026-10-19）

依 `docs/RESEARCH_UPGRADE_REPORT_2026-10-18.md`
§五既有量測計分；**不新測**。六型定義見
`docs/06-project-management/INTELLIGENCE_ASSESSMENT.md`：架構/框架/預期/訓練/驗證/實際。「訓練分」＝訓練集 in-loop，**不得當驗證分**；缺數據＝0，不用推估值填。

| 維度           | 分                        | 型                 | 證據（報告既有量測）                                                                            |
| -------------- | ------------------------- | ------------------ | ----------------------------------------------------------------------------------------------- |
| 確定性引擎     | 9.5/10                    | 驗證               | math 5/5、knowledge 5/5、reasoning 5/5（符號/KB 擋下）；native math 32/40=80%                   |
| 知識/推理混合  | 8.6/10                    | 驗證(部分)+訓練    | native knowledge 4/15=26.67%、knowledge_mc 39/40=97.5%；其引用的 ED3N 0.914 屬訓練分            |
| 架構接通       | 9.5/10                    | 架構               | 19/20 子系統、606 py、88 routes、0 STUB                                                         |
| 查詢+學習閉環  | 9.0/10                    | 框架               | 6 個閉環運作、CN→EN probe 8/8                                                                   |
| 自主閉環       | 9.0/10                    | 框架               | 生命週期+心跳+DLI+因果 warm-start                                                               |
| 路由正確性     | 100%（10/10）             | 驗證               | native routing（餘量僅 5pt）                                                                    |
| **神經訓練分** | ED3N 0.914 / GARDEN 0.700 | 訓練（**不採信**） | ED3N 訓練集 in-loop 且 grow 計入；GARDEN 為硬編碼常數（train_pipeline.py:1535）→ 誠實計 **N/A** |
| **神經驗證分** | **0/10**                  | 驗證               | 無任何 hold-out 評估（A5 未做）                                                                 |
| 離線開放域     | 0/10                      | 實際               | 8080/8081/11434 全未監聽（C1 未接）                                                             |
| 雲端開放域     | 6.0/10                    | 實際               | google fusion 活、本地無推理                                                                    |
| 多模態         | 5.1/10                    | 架構+框架          | 接通 1.0＋生成 0.02（MSE 0.271）                                                                |
| 統計內核開放域 | ≈0/10                     | 實際               | 專案自評「hash n-gram 無法匹配 LLM」；生成保真 10-13 bytes                                      |

**綜合口徑分（升級前）＝ 4.3/10**（明示權重，步驟④後同式重算）

| 成分                           | 權重 | 升級前值                    |
| ------------------------------ | ---- | --------------------------- |
| 神經**驗證**分（hold-out，A5） | 0.25 | **0**（無 hold-out）        |
| 確定性 native 四件套均值       | 0.25 | (80+26.67+97.5+100)/4 = 7.6 |
| 雲端開放域（實際）             | 0.20 | 6.0                         |
| 離線開放域（實際）             | 0.15 | 0（C1 未接）                |
| 架構/框架均值                  | 0.10 | (9.5+9.0)/2 = 9.25          |
| 多模態                         | 0.05 | 5.1                         |

算式＝0.25×0＋0.25×7.6＋0.20×6.0＋0.15×0＋0.10×9.25＋0.05×5.1 = **4.28 → 4.3**。
**不計入**：ED3N 0.914／GARDEN
0.700（訓練分且評估污染——GARDEN 為硬編碼假常數）。誠實扣分項（不入式，另表記錄）：假分、缺 hold-out、checkpoint 缺、pre-flight
5/18、28 條升級候選。

> 本分為「報告量測口徑」總分，步驟④後以同權重式重算比對。變動主要來自**假分清除/補實測**，非能力增長——如實陳述。

---

## 五-c、升級後重算（同式，2026-10-19）

D2/E3/A5 三項已執行；以**同一權重式**重算比對。原則：本批改的是**量測誠實度與死碼**，未新增任何能力量測——故各輸入分**不動**，總分不動。

| 成分                       | 權重 | 升級前 | 升級後            | 變動原因                                                                                                                   |
| -------------------------- | ---- | ------ | ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 神經**驗證**分（hold-out） | 0.25 | 0      | **0（可測未測）** | A5 已接 `evaluate_holdout`/`_eval_garden_holdout` 並移除 GARDEN 假常數，但**未重跑訓練**——尚無 hold-out 數字，缺數據仍計 0 |
| 確定性 native 四件套均值   | 0.25 | 7.6    | 7.6               | 未重跑 benchmark                                                                                                           |
| 雲端開放域（實際）         | 0.20 | 6.0    | 6.0               | 未動                                                                                                                       |
| 離線開放域（實際）         | 0.15 | 0      | 0                 | C1 未做                                                                                                                    |
| 架構/框架均值              | 0.10 | 9.25   | 9.25              | D2 清死碼不改子系統量測                                                                                                    |
| 多模態                     | 0.05 | 5.1    | 5.1               | 未動                                                                                                                       |

算式＝0.25×0＋0.25×7.6＋0.20×6.0＋0.15×0＋0.10×9.25＋0.05×5.1 = **4.28 →
4.3（不變）**。

**結論（如實）**：綜合口徑分 **4.3 → 4.3，零變化**。本批價值不在分數，而在——

1. **假分清除**：GARDEN
   0.700 硬編碼常數已移除，訓練管線不再產出假 accuracy（A5）。
2. **hold-out 可測**：下次重跑 `train_pipeline`
   即產出真實神經驗證分，該 0.25 權重項首次可被真數填入。
3. **量測口徑強制**：E3 六型標注入 assessment，訓練分冒充驗證分的記法被標「已廢」。
4. **死碼清零**：D2 死配置檔/死屬性/stats 缺鍵移除（75 passed）。
5. **checklist 5/18 → 8/18；候選 28 → 25**（新報告
   `RESEARCH_UPGRADE_REPORT_2026-10-19.md`，top-3 換為 B4/BENCH-margin-*）。

> 分數能動的唯一路徑：重跑訓練（填入 hold-out 真分）或重跑 benchmark——皆屬 A6/C1/E 範圍，本批不執行。

---

## 六、結論

1. **專案 AI 底層是誠實的混合體**：確定性內核與融合架構是真優勢（數理 9.5-10/10、離線零依賴、可審計）；開放域語言從設計上就不由自研統計內核承擔，且專案已有自我結論（「hash
   n-gram 無法匹配 LLM」）。
2. **當前最大缺口不是模型，是「鏈」**：checkpoint 缺＋save/load 斷鏈＋評估污染＋生產腳本未入庫——四者任一未解，任何新訓練都無法被證明有效。
3. **第二缺口是「路徑」**：主路徑融合活著（google 真實可用），但 `generate_text`
   旁路、llm_routes 壞、本地 LLM 閒置——「走 AI」的宣稱需要按通道逐一驗證。
4. 建議順序（本報告不執行）：**先修 A1/B1/B2（一天級）→ 接本地 qwen 或確認雲端（C1）→ 換留出集（A5/A6/E）→ 才談重訓（A2/A3）**。
