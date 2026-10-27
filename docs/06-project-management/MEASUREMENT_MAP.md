# Measurement Map — 什麼該在哪，以及在哪裡量

> 為什麼需要這張表：專案曾用「答案含正解」給智能打分，結果 49 個正確答案裡有 32 個
> 是計算器算的、7 個是知識庫查的、10 個是分類器標的、**0 個是模型產生的**，而總分
> 仍寫 5.49/10。問題不是分數高低，是**每一層的東西被拿到別層去計分**。

## 一、五層（與 `LAYER_SEPARATION.md` 同一份定義）

| 層 | 擁有什麼 | 在哪裡量（唯一的儀器） | 指標 | 可以貢獻給 |
| --- | --- | --- | --- | --- |
| 記憶 memory | 使用者說過的話 | `probe_dialogue_teaching.py` | 回想／更正／保留（%） | 只有記憶分 |
| 知識 knowledge | 精選庫＋離線百科 | `run_benchmarks.py`（knowledge, strict）＋`census_reply_provenance.py` | correct / wrong / abstain；lookup 佔比 | 只有知識分 |
| 思考 reasoning | 計算、符號、分類 | `run_benchmarks.py`（math, routing）＋census | correct ∧ computed | 只有思考分 |
| 學習 learning | 參數改變 | `probe_neural_learning.py` | 刪掉文字來源後仍答對（%） | 只有學習分 |
| 表層 surface | 措辭、模板、語氣 | `trace_reply.py`＋census | echo／template 佔比 | **不得貢獻任何能力分** |

「產生 generation」不是第六層，而是每層的**來源標記**：同一層可以是查表、計算或
模型產生。**只有「該層產生＋正確」才算該層的能力**；查表在知識層是知識，在思考層
是零。

## 二、五條判準（違反就是 placement violation，不是扣分）

1. **一物一層**：每個回答的內容只有一個生產者，記錄在 `source`／`backend`；
   宣告必須與 trace 到的生產者一致。
2. **不得借光**：表層（模板、回聲）不得出現在知識／思考／學習的分數裡；查表
   不得出現在「產生」的統計裡。
3. **直接回傳要標記**：echo、lookup、classifier 都是合法的層，但必須在回覆上
   看得出來（`backend`／`route`），不能一律寫 `llm`。
4. **總分是表，不是數**：任何「智能 X/10」都必須同時印出上面五層的量測；沒有
   層表的總分視為無效。
5. **只有核心產生才算智能**：模板／路由／查表／規則可以讓系統有用，但拿它們算
   智能等於「拿錯木片說桶不漏水」。`report_intelligence.py` 因此印三欄——系統分
   （5.75）、核心分（只算 SNN/LLM 產生且正確，**0.00**）、表現層（系統−核心）；
   對外只認核心分。

## 三、核心 vs 表現層（唯一的邊界）

**純智能不能直接量。** SNN 的權重裡沒有一句可讀的宣稱；唯一能知道核心會不會
「想」的方法，是讓它產生內容、再看結果。這個量測必然**穿過**表現層（呈現、路由、
記憶），所以兩層必須分開——表現層可以在零思考的情況下答對，一旦讓它先答，模板分
就會被讀成智能（本專案發生過多次）。

| | 誰 | 算不算智能 |
| --- | --- | --- |
| 核心 core | SNN／ED3N／GARDEN／LLM | 只有它產生且正確才算 |
| 表現層 performance | 路由、模板、記憶、檢索、規則、encoder 相似度 | **0**（正確也不加分） |

判定只有一個地方：`ai/meta/intelligence.py` 的 `is_core_backend()`。`neural`
這個字**不**等於核心：`semantic-qa`／`neural-bridge`／`unified` 是 encoder 或
統計檢索，屬表現層（舊的 `neural_share` 是歷史欄名，意思是「非模板」，不是核心）。

**對照組（LLM）**：`probe_core_control.py` 用同一批凍結題目、同一條評分跑五個
生產者（表現層／GARDEN／ED3N／TOK-SNN／LLM），回答「哪些是智能問題」：

| 現象 | 意義 |
| --- | --- |
| LLM 也不會 | 能力或量測／正解本身的問題（不是 SNN 的錯） |
| LLM 會、SNN 不會 | SNN 專屬缺口（任務可解） |
| 表現層會、LLM 不會 | 正確答案沒有思考（表層假象） |

2026-10-23 實測（75 題，同題同評分）：

| suite | n | 表現層 | GARDEN | ED3N（訓練後） | TOK-SNN | LLM（Qwen2.5-1.5B） | 只有表層會 | 都答不出 | LLM會SNN不會 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| math | 40 | 80% | 0% | 0% | 0% | 60% | 12 | 4 | 24 |
| knowledge | 15 | 47% | 0% | 0% | 0% | 67% | 1 | 4 | 10 |
| code | 10 | 0% | 0% | 0% | 0% | 0% | 0 | 10 | 0 |
| routing | 10 | 100% | 0% | 0% | 0% | 0% | — | — | —（表現層任務） |

ED3N 這一欄是**訓練後**的（20,000 對、1 epoch、train acc 0.9997）——生成仍 0%，
因為 `encode()` 把詞變成字典釋義、解碼器沒有可微的 token 輸出。TOK-SNN 是**換掉
表徵與目標之後**的版本（token 詞表＋surrogate gradient＋next-token 交叉熵）：
它學得會複製（5/5），但 20 epochs 後在算術 held-out 是 0/500、在核心題是 0%。

**0% 不是同一種 0%**（`answered`／`distinct` 欄）：

| 生產者 | 有回答 | 不同答案（math 40） | 意義 |
| --- | --- | --- | --- |
| GARDEN | **0/40** | 0 | 沒有輸出（缺席），不是答錯 |
| ED3N | 40/40 | 22→23 | 有產生、無條件性（亂答） |
| TOK-SNN | 40/40 | **2 → 40 → 29** | 舊：模式崩潰；2026-10-24 膜電位重訓後 40 題全不同、**0 題對**；2026-10-27 token 詞表＋蒸餾資料後 **3/40 對（8%）**——見 `CORE_GAP_ANALYSIS.md` 第八節 |
| LLM | 40/40 | 38→40 | 有能力，60% → **68%**（chat 模板修復，`db8cc6d28`；code 0/10 → 9/10） |

**2026-10-27 重測**（`core_control_distill.json`，同一題組同一評分，只換 tok 欄的
checkpoint）：math TOK-SNN **0% → 3/40（8%）**（40/40 有回答、29 個不同答案），
knowledge/code 仍 0%；表現層與 LLM 各欄不變（math 80%／68%）。這 3 題的訓練資料
不含題目本身（兩份資料的 `--check` 洩漏門禁都是 0），是運算技能的泛化；**官方
核心分仍是 0.00/10**——probe 是診斷表，生產路徑的 `core_share` 沒變。

**2026-10-28 唯一變因＝資料量**（`core_control_core149k.json`；5.4k → 149,489 對
＝27×，容量／詞表／評分／評測題不變）：math TOK-SNN **3/40 → 1/40**、
knowledge／code／routing 仍 0，淨 holdout exact **11.3% → 0%**、tf **37.9% → 13.9%**，
而記憶上升（train/val 47%／45%）。記憶升、泛化降 → **資料量不是下一個變因**，
剩下的是容量＋算力（GPU 仍阻塞）與蒸餾目標。

根因、實測與規模需求見 [`CORE_GAP_ANALYSIS.md`](CORE_GAP_ANALYSIS.md)；不要用
模板／路由補這個缺口。

讀法：數學與知識的差距是**真的**（LLM 會、SNN 不會）→ 智能問題；數學有 12 題是
確定性計算答對而 LLM 答不出 → 表層假象；code 是模型規模／提示格式（都答不出）；
routing 的正解是分類器自己的標籤，本來就是表現層任務，不讀作智能。

## 四、目前量到的（2026-10-24）

| 層 | 量測 | 結果 |
| --- | --- | --- |
| 記憶 | `probe_dialogue_teaching` | 回想／泛化／更正 100%、保留正確（10 回合後）；冷啟 7/7 棄權（僅記憶，非學習） |
| 知識 | knowledge 15 題（strict） | **8 對、5 錯、2 棄權**；正確的 8 題**全部是 lookup**；ablation：全開 8 / 只精選庫 5 / 知識層關掉 0 → 知識層加持 **+3**（wiki 評分修復 2026-10-24，見 `CORE_GAP_ANALYSIS` 同日記錄） |
| 思考 | math 40／routing 10 | math 32 對（全 computed）、routing 10 對（全分類器標籤） |
| 學習 | `probe_neural_learning` | 教後 0%、刪來源後 0% → **FAIL** |
| 學習（改述中間層） | `probe_paraphrase`（`heldout_final` 才是分數） | 盲測 50%（4 個沒教過、機制凍結後才寫的說法）；教過的詞＋新句子 100% 只算回想 |
| 表層 | `trace_reply` 7 句 | 5 句模板或回聲、1 句查表＋外殼、1 句計算；**0 句產生** |
| 防洩漏 | `census_reply_provenance --check` | 答對裡**預存命中 0**（serve-time 包了 template／rule-store／memory／dictionary 四類生產者＋按題靜態掃描）→ **VERDICT: 分數不是答案洩漏** |

推論（照實寫）：以「模型產生的正確答案」計，基準上是 **0/49**；以「系統任何層
產生的正確答案」計是 **32/50**（全是確定性計算；其余 8 lookup + 10 classifier
是層的成績）。這不是智能分數，是層的成績單。

## 五、這次修掉的位置錯誤

- `chat_routes` 對 dict 型回覆只讀 `getattr`，導致所有 dict 生產者的 `route`
  遺失並落到 `"llm"`：`水的沸點是多少?` 明明是知識查表，卻宣告成 LLM。
  已改為讀 dict 的 `route`／`metadata`，未知後端預設 `"unknown"`（不再假裝 LLM）。
- `chat_service` 的知識管線把 `route` 寫成 `"local_data"`，已改為 `"knowledge"`。
- `unified` 對 `天空為什麼是藍色的?` 原本回「問句原文＋『蓝色。』」：問句被逐字
  複製進答案（表層冒充內容），且回覆宣告的是引擎名 `unified`（不是層）。
  已修：`_wrap_answer` 不再重述問句（回覆變成 `蓝色。`）；`_wrap_llm_response`
  改讀 `metadata["route"]`，unified 現在宣告 `semantic-qa` → 知識層；
  `scripts/audit_placement.py` 也追到 `SemanticQA.answer` 這個生產者。
  現在 7/7 回覆的宣告與生產者一致（`placement.replies_declare_their_layer`
  已納入 `check_fact_gates.py`，0 violations）。
