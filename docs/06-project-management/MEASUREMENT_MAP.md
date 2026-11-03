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

## 四、目前量到的（2026-11-02）

| 層                 | 量測                                           | 結果                                                                                                                                                                                |
| ------------------ | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 記憶               | `probe_dialogue_teaching`                      | 回想／泛化／更正 100%、保留正確（10 回合後）；冷啟 7/7 棄權（僅記憶，非學習）                                                                                                       |
| 知識               | knowledge 15 題（strict）                      | **8 對、5 錯、2 棄權**；正確的 8 題**全部是 lookup**；ablation：全開 8 / 只精選庫 5 / 知識層關掉 0 → 知識層加持 **+3**（wiki 評分修復 2026-10-24，見 `CORE_GAP_ANALYSIS` 同日記錄） |
| 思考               | math 40／routing 10                            | math 32 對（全 computed）、routing 10 對（全分類器標籤）                                                                                                                            |
| 學習               | `probe_neural_learning`                        | 教後 0%、刪來源後 0% → **FAIL**                                                                                                                                                     |
| 學習（改述中間層） | `probe_paraphrase`（`heldout_final` 才是分數） | 盲測 75%（4 個沒教過、機制凍結後才寫的說法；42/56，過 70% 及格線）；教過的詞＋新句子 100% 只算回想；開發診斷 87.5%                                                                  |
| 表層               | `trace_reply` 7 句                             | 5 句模板或回聲、1 句查表＋外殼、1 句計算；**0 句產生**                                                                                                                              |
| 對話（純本地）     | `probe_native_dialogue`（1096 題標準集）       | 人話標準通過 **64.9%**（711/1096）：問答 468/492、斷言 96/108、對話 94/100、多重事實 53/72、**邊界題 0/324**；學習效應 **+0.4818**、神經層 22.45%、**核心 0.00**                    |
| 防洩漏             | `census_reply_provenance --check`              | 答對裡**預存命中 0**（serve-time 包了 template／rule-store／memory／dictionary 四類生產者＋按題靜態掃描）→ **VERDICT: 分數不是答案洩漏**                                            |

推論（照實寫）：以「模型產生的正確答案」計，基準上是
**0/49**；以「系統任何層產生的正確答案」計是 **32/50**（全是確定性計算；其余 8
lookup + 10 classifier 是層的成績）。這不是智能分數，是層的成績單。

**對話那一列怎麼讀**：它是**混合層**的量測（回答來源：確定性 469、模板 352、神經 246、檢索 23、其他 6），所以 64.9% 不是「模型智能」——核心仍
**0.00/10**。它的用途是量**表現層的說話品質**（鸚鵡／罐頭／雞同鴨講）。臨時門禁（`scripts/open_gates.json`）的拆除條件是 pass_rate
≥ 0.90、state ≥ 0.50、multi ≥ 0.80、progress ≥ +0.60；`state`
是 0/324，因此 pass_rate 的**上限** ＝772/1096 ≈
0.704——邊界題真的會答之前，這道門禁不可能拆。

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

| 項目     | 值                                                                                                                                                                                                                                                                                                 |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 儀器     | `scripts/probe_emergence_boundary.py`（v1.1.0，round-4 schema）；題組 `apps/backend/data/processed/mve1_emergence_boundary.json`（`--check` 逐位重建）                                                                                                                                             |
| 題組     | 200 列 compositional holdout（5 個 `(intent × mode)` cell，宣告在 `generate_al_dataset.MVE1_HOLDOUT_CELLS`，每列新抽狀態）＋ 120 列 seen-composition reference                                                                                                                                     |
| 區段     | `core_train` accepted rows [10000, 50000)（`<50000` 才有稀有 intent，`≥80000` 全是 unknown）；與現有 4 份 `ai_al_*train*/val*` 檔重疊 0 列，每次 probe 重查並回報 `instrument_text_overlap`                                                                                                        |
| 任務     | prompt 給到 gold response 為止，free-running 產生 `<al_out>` 狀態塊（合約 §5 的 F 不消費回應文本；設計裁決見 `CORE_GAP_ANALYSIS` §十二）                                                                                                                                                           |
| 評分     | **exact（single gold）**：`dt` 進輸入行（round-4 schema，`generate_al_dataset.py --expose-dt`），gold 只有對應 rung 一個；4 個 rung 的 family 仍逐列計為 `wrong_rung` 診斷（命中＝模型拿到 dt 卻忽略）。v1.0.0 的 family-exact 已歸檔——rounds 1-3 的 baseline 是在該判準下讀的，與新判準不可直接比 |
| 對照     | **rotation**：同集合內 i→i+1 輪轉錯配（derangement，零 fixed point，同一份生成物重評分）                                                                                                                                                                                                           |
| **門檻** | **holdout exact ≥5/200 且 rotation ≤1/200**（兩條件同時；gate 鍵名沿用 family-exact 時代以保持報告 schema 可比；只有 holdout 列入 gate，reference 不入）                                                                                                                                           |     | 報告 | `data/intelligence_reports/mve1_emergence_boundary.json`：gate、holdout/reference 分組、per_cell、format_ok/marker_ok、field_hits、rows_by_rung/hits_by_rung、dt_conditioning（exact_rung/wrong_rung/no_match）、carved、text_overlap（v1.1.0 鍵名；v1.0.0 時代為 rung_dist） |
| 層       | 學習 learning（參數改變後在未見組合上的泛化）；**不改變核心分**（官方核心分維持 0.00/10）                                                                                                                                                                                                          |

讀法（先看對照，再看四格）：

| exact  | rotation | reference            | 讀法                                                                                                      |
| ------ | -------- | -------------------- | --------------------------------------------------------------------------------------------------------- |
| ≥5/200 | ≤1/200   | 任意                 | 過門檻：`carved=True` 時是組合泛化第一個可測證據；`carved=False` 時只是 seen-cell baseline（未裁切 cell） |
| <5/200 | ≤1/200   | 高（reference 能過） | **組合缺口**：單一組合會、未見組合不會——真正的 compositional 測量對象，也是 `--holdout-cells` 的驗收依據  |
| <5/200 | ≤1/200   | 低                   | **任務/格式缺口**：連 seen 組合都不會，先跨格式與逐 token，門檻不在此格討論                               |
| 任意   | >1/200   | —                    | **讀數無效**：錯配仍能命中 → 格式或機率假象，不算任何結論                                                 |

> **判準版本說明**：下面的首讀是儀器 **v1.0.0 family-exact** 下讀的（round-3
> checkpoint，`dt` 尚未進輸入）；v1.1.0 起改 single-gold（`dt` 進輸入），
> **舊數字不可與新判準直接比**。新判準首讀已補（2026-11-01，round-4，見下）。

**首讀（2026-10-31，`ai_al_round3.pt`，XPU
563.4s，`--set all`，v1.0.0 判準）**：holdout **0/200**、rotation
**0/200**、reference **0/120** → gate FAIL（預期 baseline）。format_ok
106/320、`<al_out>` 出現 248/320、欄位值命中（任一 rung）v 10／a 4／d
14／fatigue 17／stress 17／health
8（共 320）、rung 分佈全 none；`carved=False`（rounds
1-3 訓練含全部 cell）、`text_overlap=0`。解讀：對照乾淨（0）＋格式在動（33% 全欄位，與 tail
76% 一致）＋**逐字 2dp 狀態列一個都沒寫出來**——同一個 0 從此分層可讀。

**single-gold 首讀（2026-11-01，`ai_al_round4.pt`，XPU
558.5s，`--set all`，v1.1.0 判準）**：holdout **0/200**、rotation
**0/200**、reference **0/120** → gate
FAIL。`dt_conditioning`：`exact_rung 0`／`wrong_rung 0`／**`no_match 320`**——模型連一個合法狀態塊都沒寫出來，還沒走到「拿到 dt 卻忽略」（wrong_rung）那格可判讀的位置，按上表讀法在**任務/格式缺口**格。format_ok
31/320、`<al_out>` 192/320、欄位值命中（single-gold）a 13／d 3／fatigue
6（v、stress、health 0）、每 rung 80 列平衡且 hits 全 0；`training_cell_rows`
只剩 round-1 遺留檔（751／233 列），**round-4/5 檔 0 列＝carve 生效**、`text_overlap=0`（6 份 train/val 檔）。與 v1.0.0 首讀不可直接比（判準與 prompt 均已換）；讀數與解讀全文見
`CORE_GAP_ANALYSIS` §十三。

**single-gold 第二發（2026-11-02，`ai_al_round5.pt`，XPU
596.3s，`--set all`，v1.1.0 判準）**：與 R4 **同一份 frozen 320 列儀器**
→ 可直接比：gate 三項同值 **0/200／0/200／0/120**（pass=False）、`no_match 320`
續航（exact／wrong 皆 0）、format_ok **31→58**、marker 192→118、field_hits
**22→31（六欄全出現）**、hits_by_rung 全 0、`text_overlap=0`、`training_cell_rows`
仍只剩 round-1 遺留檔（carve 在效）。解讀：換新不相交切片後
**0 複現**；格式行為變動但未過格式關，dt 判讀格仍不可用；全文見
`CORE_GAP_ANALYSIS` §十四。
**single-gold 第三發（2026-11-02，`ai_al_round6.pt`，XPU
545.1s，`--set all`，v1.1.0 判準）**：gate 三項
**0/200／0/200／0/120**（pass=False）、`no_match 320`、hits_by_rung 全 0、`text_overlap=0`（8 檔）。表面指標看起來是跳躍：format_ok
**58→316**、marker 118→314、field_hits
31→**142**。**實際生成是塌縮**：320 列輸入只產生
**23 種狀態塊**（最大一種佔 29%），值無論輸入狀態從 `v=-0.97` 到
`v=0.90`、dt 從 0.25 到 4.0、cell 從 greeting 到 humor，都擠在
`v≈0.10–0.12 a 0.42–0.49 d=0.42 fatigue=0.34 stress=0.39 health=0.86 mode=exploratory intent=unknown`（貼近 pilot
baseline 目標，而 gold 的 `d`
跨 0.06–0.77），且每條前面多吐一個數字前綴（`614\n`…）再接 `<al_out>`。整段
`distinct` 180 幾乎全是前綴在變。根因在資料層：該切片 100% 是裸算式而
`_intent_of()` 不認得裸算式 → 3,408 列全 `intent=unknown` → 沒有 per-intent
target、只剩 baseline。全文見 `CORE_GAP_ANALYSIS` §十五。

> **讀法補充（R6 之後）**：`format_ok`／`marker_ok`／`field_hits`
> 三個格式指標**必須與 `output_diversity` 一起讀，而且要看 `body_*`
> 那三個**。一個只會重複極少數塊的模型可以在這三欄拿高分，而 gate 仍是 0——R6 就是這個形狀（format_ok
> 316/320、`body_distinct` 23/320、`body_modal_share`
> 0.29；那 142 個 field_hits 有 136 個能用單一固定塊回算，是壞鐘而非「差一點」）。儀器已把
> `output_diversity`（`distinct`／`modal_share`／`modal`／`body_distinct`／`body_modal_share`／`body_modal`）寫進報告；只讀
> `distinct` 會高估多樣性（R6：180 vs
> 23），因為答案段／數字前綴的抖動不算 conditioning。

**single-gold 第四發（2026-11-02，`ai_al_round7.pt`，XPU
494.0s，`--set all`）**：這批是修好 `_intent_of()`
之後重產的 round-7（3,286 列、math／kq／unknown 三 intent，6
cells），argv 與 R6 逐字相同（仍 `--tail-weight 0.25`）。gate 三項仍
**0/200／0/200／0/120**（pass=False，且這批 0
greeting／humor，結構上不可能通過）。但表面數字全滿：format_ok
**320/320**、marker **320/320**、field_hits
**155**。儀器新增的三欄把它拆開了：`body_distinct` **23 → 128**（塌縮解除、
`body_modal_share` 29.1% → 7.5%），可是 `input_output_correlation` **六欄 \|r\|
≤ 0.083**、 `copy_accuracy` **mode 29.7%／intent 26.9%**——`mode`／`intent`
依契約是照抄輸入，抄中率卻與亂猜（33%／20%）同級。擾動測試（只改 `v` 或 `dt`
再生成）顯示 12/24、14/24 的輸出塊會變：模型有讀
`<al_in>`，但依賴是 ragged 的。解讀：**格式學會了、映射沒學會**；訓練端疑點是
`--tail-weight 0.25` 把狀態塊（正好是 MVE-1 要量的東西）壓到有效梯度 9.9%，R8 以
`--tail-weight 1.0` 單一變因複驗。全文見 `CORE_GAP_ANALYSIS` §十六。

> **讀法（R7 之後，三欄成組）**：`format_ok` 高 + `body_distinct`
> 低 = 塌縮（R6）；`body_distinct` 高但 `input_output_correlation` ≈ 0 且
> `copy_accuracy`
> ≈ 隨機 = 格式對而映射沒學到（R7）。只看前兩欄會把 R7 誤讀成「終於學會了」——這也是 gate 仍為 0 的原因。

**single-gold 第五發（2026-11-03，`ai_al_round8.pt`，XPU，`--set all`）**：R8 是 R7 的
**單一變因**——資料、切片、argparse 逐字相同，只把 `--tail-weight 0.25` 改成
`1.0`。gate 仍
**0/200／0/200／0/120**，但這一發不是複驗 0，而是換掉了 0 的解讀：
`body_distinct` **128 → 241**、`body_modal_share` 7.5% → 4.1%、`field_hits`
**155 → 98**、train loss 0.633 → **0.571**（min @95，100 epochs 終於夠），代價是
`format_ok` **320 → 223**、marker **320 → 203**（最常見破法是吞掉 `a=` 欄位）。
`input_output_correlation` 仍 ≤ 0.14、`copy_accuracy` mode 37.2%／intent
25.0%（隨機水位 33%／20%）——連照抄都做不到。結論：`--tail-weight` 不是主因。

同時這一發補上兩個**判讀用的上界**，讓 0 不再只能與 0 相比：-
`gold_input_correlation`（gold 對 `state_in`，**0.743–0.839**）：`r ≈ 0`
的意思是「與上界的差距」，不是「與零的距離」。契約本身高度依賴輸入，所以 0.0–0.14 是模型的讀數。

- `learnability`（把契約形式 `t + (s−t)·exp(−dt/τ)` 用 5-fold
  out-of-fold 擬合）：逐 `dt` 一組係數 → row_exact **0.503**、R²
  0.9996–0.9999；`dt` 當一般特徵（無交互項）→ row_exact
  **0.000**。gate 只需 2.5%，所以**門檻可達**；而 `dt_blind`
  的 0.000 標出這道題的全部內容就是 `dt` 交互項。

> **讀法（R8 之後，五欄成組）**：`format_ok` + `body_distinct` 判塌縮，
> `input_output_correlation`／`copy_accuracy` **要和 `gold_input_correlation`
> 一起讀** （上界 ≈
> 0.8、抄中上界 100%），`learnability.dt_conditioned.row_exact`
> 則是**門檻的可達性證明**。三欄時代的 R7 讀數（映射沒學到）成立，但當時無法排除「資料不可學」；現在可以：上界 50.3%
> ≫ 門檻 2.5%，權重與位置都已排除，剩下的是容量／表徵。全文見
> `CORE_GAP_ANALYSIS` §十七。

**架構對照（2026-11-03，`baseline_transformer.pt`，同一批資料／同一評分程式）**：把 R8 的 SNN 與一個參數相當的 causal
transformer（1,196,112 vs 1,239,634，100
epochs、同詞表、同加權、同排程取樣 0.5、同 greedy）放在一起讀同一份
`probe_emergence_boundary`：**兩者 gate 都是 0/200**。差別只在破法—— transformer
`tail_tf` **0.848**、`copy_accuracy` mode **59.1%**、改 `v` 敏感度
**21/24**（擬合與條件化更好），但自由生成 `format_ok` 只有 **8/320**；SNN
`tail_tf` 0.794、抄中 37.2%、`format_ok`
**223**（骨架更穩、內容不準）。兩者的 \|r\| 都在 0.14–0.16，而上界是 0.74–0.84。

> **讀法（對照之後）**：`0/200`
> 只有在**兩個**架構、同一份評分程式下都讀 0 時，才可以說「這是題目的問題」而不是「這個架構的問題」。三個可引用的錨點：
> `gold_input_correlation`（上界 0.74–0.84）、affine 逐 `dt`
> 擬合（非神經參考解 0.503）、同預算的兩個神經架構（0／0）。比較 SNN 與其他方案時，這三個數必須一起出現；只報
> `format_ok` 會把「骨架穩」誤讀成「能力高」（R8：223 vs baseline
> 8，但 gate 相同）。全文見 `CORE_GAP_ANALYSIS` §十八。

**數值原子化（2026-11-03，R9，`mve1_emergence_boundary_atoms.json`）**：同一個
`probe_emergence_boundary`，唯一差別是 tokenizer 把契約值（`-1.00 … 1.00`，加
`dt` 的 `2.00`）當成單一原子（201+1 個，閉集、`max_vocab` 不可截斷）。合法塊
`format_ok` **223 → 301/320**、`marker_ok` 203 → 265、改 `v` 的敏感度 8/24 →
**23/24**；但 gate 仍 **0/200**，`|r|` 0.137 → 0.097，`val_exact` 仍 0。

> **讀法（精確度的算術）**：`tail_tf`（val、gold 前綴）0.829 對一個約 40 原子的塊意味著
> `0.829^40 ≈ 5e-4` 的行級命中率——320 列期望 0.16 列。所以 **exact 0 與
> `tail_tf 0.83`
> 是同一件事**，不是兩個壞消息。gate 要 5/200（2.5%），逐 token 準確率需要 ~0.99。看到「模型在 gold 前綴下寫得出來」時，必須同時換算成行級期望，否則會把結構改善（223→301）誤讀成能力改善。同一份原子詞表下 transformer 仍 0/200 且
> `format_ok` 只有 8（訓練 loss 0.054 = 記憶），見 `CORE_GAP_ANALYSIS` §十九。

**契約形式上界（2026-11-03，`--ceiling`）**：`generate_al_dataset` 的 gold 是
`c[intent] + (state − c[intent])·exp(−dt/1.0)`——每個 intent 一組 6 個常數、一個指數。`probe_emergence_boundary.py --ceiling`
只用訓練檔反推常數（`c` 的中位數）並在 τ 格子上挑 τ（選到
**1.0**），再把算子套到評分列：逐位 **0.854–0.913**、逐列
**0.508**（122/240，只看訓練看得到的 intent；以整個 200 列 gate 為分母是
**0.381**）。這與 affine 上界 0.503 幾乎相同，因為兩者都被**狀態以 2dp 印刷**卡住：算子完全正確也只能到這裡。

> **讀法（三個數字一起看）**：`0/200` 要跟 **0.508（可達）**
> 比，不是跟 1 比，也不是跟 0.503 的「模型天花板」比——0.5 是資料精度。另外 200 列裡有
> **80 列（greeting／humor）的 intent 從未在訓練出現**，其常數無從觀測，這 40% 是
> **不可知**而非難；報告必須把 120 列（可達）與 80 列（不可達）分開，否則兩個相反的結論會被平均掉。見
> `CORE_GAP_ANALYSIS` §二十。

**值介面 vs 文字介面（2026-11-03，`--value-head` /
`--operator-head`）**：兩個成因量到了。(1) 訓練後 `beta = 0.832`，有效記憶 ≈ **6
atoms**，而 block 起點在 ~120 atoms 之後（`0.83^120 ≈ 2e-10`）：從 hidden
state 線性回歸 gold 的 R² 在 `values_end` 是 0.08–0.28，6 個 atom 之後就 ≤
0。(2) 把契約欄位直接給閉式 ridge（繞過循環）R² 0.69–0.83、MAE
0.055–0.145，但 grading 容差 ±0.005 需要 MAE ≈ 0.002 → **逐列 exact
0/316**：連續估計不可能通過 exact gate。

> **讀法**：`--operator-head`（19 參數：18 常數 +
> τ）在**值介面**上讓 gate 首次通過：τ 學到 **1.0001**、seen
> 52.5%、全 200 列 63 列 exact、gate
> pass=true。這是介面改變的結果，不是同一個任務的分數提升；文字介面（~40
> atoms 自由生成）的 0/200 現在有兩個確定的成因。見 `CORE_GAP_ANALYSIS`
> §二十一。

**有界元胞機對照（2026-11-03，`compare_cellular_baseline.py`）**：容器 = 專案自己的
`TokenConfig.max_len`（384 格 20×20），每格 3 個狀態，動力學 0 參數，無全局清空。先量到兩個真缺陷並修掉：全正耦合使晶格**同步成均勻場**（跨列 std
0.004）、輸入耦合 `1/√N` 相對遞歸太弱（改
`--in-gain 4`）。修好後 retention（六個 in 值，in-sample）：讀到當下 0.19、block 起點
**0.144**（加 latch
τ=64 為 0.181）——比 SNN 的 ≤0 好，但絕對值仍不足。任務：**0/197
exact**，同分布驗證 R² 0.23、跨分布 **−19**。

> **讀法**：「不卡死／狀態可區分」不是 gate 的證據。這台機器四個定性測試全過、仍然 0
> exact；可區分 ≠ 可解碼 ≠ 可泛化。只有 §二十一的算子頭（63/200）能過，因為它把數值當值、用精確算術。見
> `CORE_GAP_ANALYSIS` §二十二。

**MVE-1 介面階梯（2026-11-03）**：原生文字 0/200
→ 值介面算子頭（只靠學習）**63/200**
→ 加上契約 intent 目標表（執行期查表，非權重）**105/200**；「正確常數＋精確算術」的參考上界是
**107/200**，即算子頭吃到 98%。剩下 93 列失手是 2dp 列印 × ±0.005 的結果（誤差 ≤
0.005·exp(−dt)，dt=0.25 那格 50 列只有 11 列可能 exact、dt=2.0 有 46 列）。

> **讀法**：holdout 的 80 列 unseen intent（greeting/humor）用 baseline
> fallback 是 0/40，只有查契約表才有 23/40、19/40。要讓 exact 這個讀數有意義，先把輸入/gold 印到 3dp 或把容差放寬到
> `0.005 + 0.005·exp(−dt/τ)`；在那之前 53.5% 就是上限。見 `CORE_GAP_ANALYSIS`
> §二十三。

**列印誤差修正讀法（2026-11-03）**：容差改 `0.005·(1+exp(−dt/τ))`
後，同一支算子頭從 105/200 升到 **197/200**（上限 200 →
98.5%），reference 從 0.492 升到
**0.975**。剩下 3 列是學到的常數差約 0.002（不是 clamp、不是截斷）。
**同一支模型、同一組常數**，差別只在「要不要把 2dp 列印誤差算成模型錯」。最終階梯：0
→ 63 → 105（嚴格）→ 197（修正）。

**3dp 語料（2026-11-03，§二十四）**：修掉「輸入 3dp / gold
2dp」的精度不一致、把常數從 GD 換成閉式解、解開價值介面被文字 2dp 格子擋住的閘門之後，**同一支算子頭 strict
200/200**（上界也是 200），reference 1.000，`by_dt`
四個 rung 各 50/50。2dp 語料同條件是 108/200（修正讀法 199/200）。**判讀**：MVE-1 在值介面上已碰到上界，剩下能證明「emergent」的空間不在這六個數字上。

**規模上限（2026-11-03，§二十六／二十七）**：`probe_scale_envelope.py` 用真實
`TokenSNN.loss` 每配置獨立行程量到 —— 容量可放大 **59 倍**（1.45M →
86.13M 參數，device 2450 MiB / 3
GiB 預算，步時 9.3×），而 host 峰值在整個 grid 只差 **144 MiB**
（固定每行程 ~2.15
GiB，torch+XPU 載入）：**主記憶體限制的是併發，不是容量**。多合一（table／operator／knn／copy）：3dp
**320/320**（比例 table .749／operator .251，兩者各承重 80 列，knn
0.019 已移除）、2dp
**164/320**（.443／.557，最佳單一元件 128）。3dp 語料 atom 可表達率
**0/2633**（2dp 為 2611/2633）→ 文字介面在 3dp 是構造性零分。
