# Measurement Map — 什麼該在哪，以及在哪裡量

> 為什麼需要這張表：專案曾用「答案含正解」給智能打分，結果 49 個正確答案裡有 32 個是計算器算的、7 個是知識庫查的、10 個是分類器標的、**0 個是模型產生的**，而總分仍寫 5.49/10。問題不是分數高低，是**每一層的東西被拿到別層去計分**。

## 一、五層（與 `LAYER_SEPARATION.md` 同一份定義）

| 層             | 擁有什麼         | 在哪裡量（唯一的儀器）                                                 | 指標                                   | 可以貢獻給             |
| -------------- | ---------------- | ---------------------------------------------------------------------- | -------------------------------------- | ---------------------- |
| 記憶 memory    | 使用者說過的話   | `probe_dialogue_teaching.py`                                           | 回想／更正／保留（%）                  | 只有記憶分             |
| 知識 knowledge | 精選庫＋離線百科 | `run_benchmarks.py`（knowledge, strict）＋`census_reply_provenance.py` | correct / wrong / abstain；lookup 佔比 | 只有知識分             |
| 思考 reasoning | 計算、符號、分類 | `run_benchmarks.py`（math, routing）＋census                           | correct ∧ computed                     | 只有思考分             |
| 學習 learning  | 參數改變         | `probe_neural_learning.py`                                             | 刪掉文字來源後仍答對（%）              | 只有學習分             |
| 表層 surface   | 措辭、模板、語氣 | `trace_reply.py`＋census                                               | echo／template 佔比                    | **不得貢獻任何能力分** |

「產生 generation」不是第六層，而是每層的**來源標記**：同一層可以是查表、計算或模型產生。**只有「該層產生＋正確」才算該層的能力**；查表在知識層是知識，在思考層是零。

## 二、五條判準（違反就是 placement violation，不是扣分）

1. **一物一層**：每個回答的內容只有一個生產者，記錄在
   `source`／`backend`；宣告必須與 trace 到的生產者一致。
2. **不得借光**：表層（模板、回聲）不得出現在知識／思考／學習的分數裡；查表不得出現在「產生」的統計裡。
3. **直接回傳要標記**：echo、lookup、classifier 都是合法的層，但必須在回覆上看得出來（`backend`／`route`），不能一律寫
   `llm`。
4. **總分是表，不是數**：任何「智能 X/10」都必須同時印出上面五層的量測；沒有層表的總分視為無效。
5. **只有核心產生才算智能**：模板／路由／查表／規則可以讓系統有用，但拿它們算智能等於「拿錯木片說桶不漏水」。`report_intelligence.py`
   因此印三欄——系統分（5.75）、核心分（只算 SNN/LLM 產生且正確，**0.00**）、表現層（系統−核心）；對外只認核心分。

## 三、核心 vs 表現層（唯一的邊界）

**純智能不能直接量。**
SNN 的權重裡沒有一句可讀的宣稱；唯一能知道核心會不會「想」的方法，是讓它產生內容、再看結果。這個量測必然**穿過**表現層（呈現、路由、記憶），所以兩層必須分開——表現層可以在零思考的情況下答對，一旦讓它先答，模板分就會被讀成智能（本專案發生過多次）。

|                    | 誰                                           | 算不算智能            |
| ------------------ | -------------------------------------------- | --------------------- |
| 核心 core          | SNN／ED3N／GARDEN／LLM                       | 只有它產生且正確才算  |
| 表現層 performance | 路由、模板、記憶、檢索、規則、encoder 相似度 | **0**（正確也不加分） |

判定只有一個地方：`ai/meta/intelligence.py` 的 `is_core_backend()`。`neural`
這個字**不**等於核心：`semantic-qa`／`neural-bridge`／`unified`
是 encoder 或統計檢索，屬表現層（舊的 `neural_share`
是歷史欄名，意思是「非模板」，不是核心）。

**對照組（LLM）**：`probe_core_control.py`
用同一批凍結題目、同一條評分跑五個生產者（表現層／GARDEN／ED3N／TOK-SNN／LLM），回答「哪些是智能問題」：

| 現象               | 意義                                        |
| ------------------ | ------------------------------------------- |
| LLM 也不會         | 能力或量測／正解本身的問題（不是 SNN 的錯） |
| LLM 會、SNN 不會   | SNN 專屬缺口（任務可解）                    |
| 表現層會、LLM 不會 | 正確答案沒有思考（表層假象）                |

2026-10-23 實測（75 題，同題同評分）：

| suite     | n   | 表現層 | GARDEN | ED3N（訓練後） | TOK-SNN | LLM（Qwen2.5-1.5B） | 只有表層會 | 都答不出 | LLM會SNN不會    |
| --------- | --- | ------ | ------ | -------------- | ------- | ------------------- | ---------- | -------- | --------------- |
| math      | 40  | 80%    | 0%     | 0%             | 0%      | 60%                 | 12         | 4        | 24              |
| knowledge | 15  | 47%    | 0%     | 0%             | 0%      | 67%                 | 1          | 4        | 10              |
| code      | 10  | 0%     | 0%     | 0%             | 0%      | 0%                  | 0          | 10       | 0               |
| routing   | 10  | 100%   | 0%     | 0%             | 0%      | 0%                  | —          | —        | —（表現層任務） |

ED3N 這一欄是**訓練後**的（20,000 對、1 epoch、train acc
0.9997）——生成仍 0%，因為 `encode()`
把詞變成字典釋義、解碼器沒有可微的 token 輸出。TOK-SNN 是**換掉表徵與目標之後**的版本（token 詞表＋surrogate
gradient＋next-token 交叉熵）：它學得會複製（5/5），但 20
epochs 後在算術 held-out 是 0/500、在核心題是 0%。

**0% 不是同一種 0%**（`answered`／`distinct` 欄）：

| 生產者  | 有回答   | 不同答案（math 40） | 意義                                                                                                                                                 |
| ------- | -------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| GARDEN  | **0/40** | 0                   | 沒有輸出（缺席），不是答錯                                                                                                                           |
| ED3N    | 40/40    | 22→23               | 有產生、無條件性（亂答）                                                                                                                             |
| TOK-SNN | 40/40    | **2 → 40 → 29**     | 舊：模式崩潰；2026-10-24 膜電位重訓後 40 題全不同、**0 題對**；2026-10-27 token 詞表＋蒸餾資料後 **3/40 對（8%）**——見 `CORE_GAP_ANALYSIS.md` 第八節 |
| LLM     | 40/40    | 38→40               | 有能力，60% → **68%**（chat 模板修復，`db8cc6d28`；code 0/10 → 9/10）                                                                                |

**2026-10-27 重測**（`core_control_distill.json`，同一題組同一評分，只換 tok 欄的 checkpoint）：math
TOK-SNN **0% →
3/40（8%）**（40/40 有回答、29 個不同答案），knowledge/code 仍 0%；表現層與 LLM 各欄不變（math
80%／68%）。這 3 題的訓練資料不含題目本身（兩份資料的 `--check`
洩漏門禁都是 0），是運算技能的泛化；**官方核心分仍是 0.00/10**——probe 是診斷表，生產路徑的
`core_share` 沒變。

**2026-10-28 唯一變因＝資料量**（`core_control_core149k.json`；5.4k →
149,489 對＝27×，容量／詞表／評分／評測題不變）：math TOK-SNN **3/40 →
1/40**、knowledge／code／routing 仍 0，淨 holdout exact **11.3% → 0%**、tf
**37.9% → 13.9%**，而記憶上升（train/val 47%／45%）。記憶升、泛化降 →
**資料量不是下一個變因**，剩下的是容量＋算力（GPU 仍阻塞）與蒸餾目標。

**2026-10-30 換 checkpoint＝AI+AL 第一輪**（`core_control_ai_al_round1.json`，同題同評分，只換 tok 欄）：math
TOK-SNN **1/40 → 0/40**，knowledge／code／routing 仍 0。該模型練的是
`(狀態, 文字) → (回應, 狀態′)`（3,180 對、XPU 30
epochs），不是核心問答，**不能拿來說核心分上升**；它的成績單在
[`CORE_GAP_ANALYSIS.md`](CORE_GAP_ANALYSIS.md) 第九節（holdout teacher-forced
61.76%、free-running exact
0/100）。同一次實測的對照欄：knowledge 表現層 53%／LLM
73%（15 題小樣本，較 10-23 的 47%／67% 差一題）、code LLM
90%（與「chat 模板修復後 0/10 →
9/10」一致）。**GPU 線已解除阻塞**（同日，根因＝wrapper 的 CSR 覆寫，見
`CORE_GAP_ANALYSIS.md` §4）。

**2026-10-30 換 checkpoint＝AI+AL 第二輪**（同題同評分，只換 tok 欄）：TOK-SNN
**0/75**（math 0/40、knowledge 0/15、code 0/10、routing
0/10），與第一輪同為 0。第二輪修掉了第一輪的四個變因（`max_len`
192→384 讓進得去的列 48% → 94%、分離指標、`--tail-weight 0.25`、100
epochs），同列重測答案段 teacher-forced **19.51% →
22.71%**、狀態塊持平 78%——**改進是真的但量級遠不夠**（exact 要每一發都對）。生成樣本顯示**格式學會了、綁定沒學會**：`<al_out>`
狀態塊欄位順序全對，答案句是字詞湯。詳見
[`CORE_GAP_ANALYSIS.md`](CORE_GAP_ANALYSIS.md) §十；**官方核心分維持 0.00/10**。

根因、實測與規模需求見
[`CORE_GAP_ANALYSIS.md`](CORE_GAP_ANALYSIS.md)；不要用模板／路由補這個缺口。

讀法：數學與知識的差距是**真的**（LLM 會、SNN 不會）→ 智能問題；數學有 12 題是確定性計算答對而 LLM 答不出 → 表層假象；code 是模型規模／提示格式（都答不出）；routing 的正解是分類器自己的標籤，本來就是表現層任務，不讀作智能。

## 四、目前量到的（2026-10-24）

| 層                 | 量測                                           | 結果                                                                                                                                                                                |
| ------------------ | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 記憶               | `probe_dialogue_teaching`                      | 回想／泛化／更正 100%、保留正確（10 回合後）；冷啟 7/7 棄權（僅記憶，非學習）                                                                                                       |
| 知識               | knowledge 15 題（strict）                      | **8 對、5 錯、2 棄權**；正確的 8 題**全部是 lookup**；ablation：全開 8 / 只精選庫 5 / 知識層關掉 0 → 知識層加持 **+3**（wiki 評分修復 2026-10-24，見 `CORE_GAP_ANALYSIS` 同日記錄） |
| 思考               | math 40／routing 10                            | math 32 對（全 computed）、routing 10 對（全分類器標籤）                                                                                                                            |
| 學習               | `probe_neural_learning`                        | 教後 0%、刪來源後 0% → **FAIL**                                                                                                                                                     |
| 學習（改述中間層） | `probe_paraphrase`（`heldout_final` 才是分數） | 盲測 50%（4 個沒教過、機制凍結後才寫的說法）；教過的詞＋新句子 100% 只算回想                                                                                                        |
| 表層               | `trace_reply` 7 句                             | 5 句模板或回聲、1 句查表＋外殼、1 句計算；**0 句產生**                                                                                                                              |
| 防洩漏             | `census_reply_provenance --check`              | 答對裡**預存命中 0**（serve-time 包了 template／rule-store／memory／dictionary 四類生產者＋按題靜態掃描）→ **VERDICT: 分數不是答案洩漏**                                            |

推論（照實寫）：以「模型產生的正確答案」計，基準上是
**0/49**；以「系統任何層產生的正確答案」計是 **32/50**（全是確定性計算；其余 8
lookup + 10 classifier 是層的成績）。這不是智能分數，是層的成績單。

## 五、這次修掉的位置錯誤

- `chat_routes` 對 dict 型回覆只讀 `getattr`，導致所有 dict 生產者的 `route`
  遺失並落到 `"llm"`：`水的沸點是多少?`
  明明是知識查表，卻宣告成 LLM。已改為讀 dict 的
  `route`／`metadata`，未知後端預設 `"unknown"`（不再假裝 LLM）。
- `chat_service` 的知識管線把 `route` 寫成 `"local_data"`，已改為
  `"knowledge"`。
- `unified` 對 `天空為什麼是藍色的?`
  原本回「問句原文＋『蓝色。』」：問句被逐字複製進答案（表層冒充內容），且回覆宣告的是引擎名
  `unified`（不是層）。已修：`_wrap_answer` 不再重述問句（回覆變成
  `蓝色。`）；`_wrap_llm_response` 改讀 `metadata["route"]`，unified 現在宣告
  `semantic-qa` → 知識層； `scripts/audit_placement.py` 也追到
  `SemanticQA.answer`
  這個生產者。現在 7/7 回覆的宣告與生產者一致（`placement.replies_declare_their_layer`
  已納入 `check_fact_gates.py`，0 violations）。

## 六、湧現界線 MVE-1（AI+AL 訓練主線的門檻，2026-10-31 註冊）

第三輪收官時（`CORE_GAP_ANALYSIS`
§十一.4）**只定了門檻、沒儀器**——「下一個 0」與「儀器不可能響」不可區分。現在門檻與儀器同時註冊：

| 項目     | 值                                                                                                                                                                                                |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 儀器     | `scripts/probe_emergence_boundary.py`；題組 `apps/backend/data/processed/mve1_emergence_boundary.json`（`--check` 逐位重建）                                                                      |
| 題組     | 200 列 compositional holdout（5 個 `(intent × mode)` cell，宣告在 `generate_al_dataset.MVE1_HOLDOUT_CELLS`，每列新抽狀態）＋ 120 列 seen-composition reference                                    |
| 區段     | `core_train` accepted rows [10000, 50000)（`<50000` 才有稀有 intent，`≥80000` 全是 unknown）；與現有 4 份 `ai_al_*train*/val*` 檔重疊 0 列，每次 probe 重查並回報 `instrument_text_overlap`       |
| 任務     | prompt 給到 gold response 為止，free-running 產生 `<al_out>` 狀態塊（合約 §5 的 F 不消費回應文本；設計裁決見 `CORE_GAP_ANALYSIS` §十二）                                                          |
| 評分     | **family-exact**：輸出須逐字等於 4 個 dt rung（0.25/0.5/1.0/2.0）之一的 gold——`dt` 不在輸入行（訓練資料 0 命中），單一 gold 結構上不可得；升級路徑＝dt 進輸入（資料 schema 變因，留給下一輪決定） |
| 對照     | **rotation**：同集合內 i→i+1 輪轉錯配（derangement，零 fixed point，同一份生成物重評分）                                                                                                          |
| **門檻** | **holdout family-exact ≥5/200 且 rotation ≤1/200**（兩條件同時；只有 holdout 列入 gate，reference 不入）                                                                                          |
| 報告     | `data/intelligence_reports/mve1_emergence_boundary.json`：gate、holdout/reference 分組、per_cell、format_ok/marker_ok、field_hits、rung_dist、carved、text_overlap                                |
| 層       | 學習 learning（參數改變後在未見組合上的泛化）；**不改變核心分**（官方核心分維持 0.00/10）                                                                                                         |

讀法（先看對照，再看四格）：

| family | rotation | reference            | 讀法                                                                                                      |
| ------ | -------- | -------------------- | --------------------------------------------------------------------------------------------------------- |
| ≥5/200 | ≤1/200   | 任意                 | 過門檻：`carved=True` 時是組合泛化第一個可測證據；`carved=False` 時只是 seen-cell baseline（未裁切 cell） |
| <5/200 | ≤1/200   | 高（reference 能過） | **組合缺口**：單一組合會、未見組合不會——真正的 compositional 測量對象，也是 `--holdout-cells` 的驗收依據  |
| <5/200 | ≤1/200   | 低                   | **任務/格式缺口**：連 seen 組合都不會，先跨格式與逐 token，門檻不在此格討論                               |
| 任意   | >1/200   | —                    | **讀數無效**：錯配仍能命中 → 格式或機率假象，不算任何結論                                                 |

**首讀（2026-10-31，`ai_al_round3.pt`，XPU 563.4s，`--set all`）**：holdout
**0/200**、rotation **0/200**、reference **0/120** → gate
FAIL（預期 baseline）。format_ok 106/320、`<al_out>`
出現 248/320、欄位值命中（任一 rung）v 10／a 4／d 14／fatigue 17／stress
17／health 8（共 320）、rung 分佈全 none；`carved=False`（rounds
1-3 訓練含全部 cell）、`text_overlap=0`。解讀：對照乾淨（0）＋格式在動（33% 全欄位，與 tail
76% 一致）＋**逐字 2dp 狀態列一個都沒寫出來**——同一個 0 從此分層可讀。
