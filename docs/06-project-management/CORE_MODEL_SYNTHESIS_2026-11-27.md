<!--
  FILE_PATH: docs/06-project-management/CORE_MODEL_SYNTHESIS_2026-11-27.md
  FILE_TYPE: documentation
  PURPOSE: 核心模型的定義、缺口、已完成研究、連貫判斷（整理用，不是新實驗）
  VERSION: 1.0.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-11-27
  AUDIENCE: developers, agents
-->

# 核心模型綜合整理（2026-11-27）

> 這份文件回答三件事：**核心模型應該是什麼**、**現在缺什麼**、**做過哪些研究**。目的在於停止重複實驗，不在於宣傳成果。所有數字都能回到既有報告重算。

## 1. 核心模型該是什麼（定義，不是願望）

依 `AI_AL_SINGLE_CORE_CONTRACT.md`
§2 的 R1：**一份權重（`weights_hash`）＋一個 state 物件＋兩個 step 函式（`ai_step`／`al_step`）**。由此推出：

| 要求       | 含義                                                                   | 不能混淆的東西                          |
| ---------- | ---------------------------------------------------------------------- | --------------------------------------- |
| 一份權重   | 只有一個模型在產生答案                                                 | 不是「SNN 腦＋LLM 嘴」兩份權重          |
| 一個 state | 固定大小、跨回合、模型自己擁有的張量                                   | 不是 prompt 裡的歷史文字，不是 KV cache |
| 會生成語言 | 核心自己輸出答案                                                       | 不是模板／查表／路由／確定性計算        |
| 能力分層   | 語言在權重；事實在記憶／檢索；算術邏輯在工具；人格在 state；不會就棄權 | 不要把工具正確算進核心分                |

一句話：**一個能自己說話、用內部 state 記住的模型的模型**。它不是最小模型——0.5B 級模型需 10¹¹–10¹²
token 才勉強能講話；低於這個規模做不到，這是本地實驗反覆確認的事實。

## 2. 目前缺什麼（用實驗結果背書）

| 缺口                     | 實測證據                                                                                                                    | 量級判斷                                               |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **資料量／型態**         | 本地只有 149k 答案式配對（~5M token）＋百科 199MB（~50M token），且沒有大規模多輪 instruction 語料                          | 離 10¹¹–10¹² token 差 3–4 個數量級                     |
| **state 真的被模型使用** | 投影注入（raw→破壞分布；30 步→重複）、4-memory-token（450 步→5/30 ≈ 猜測）、from-scratch（5M token→生成為空、三臂消融全 0） | 不是單一超參錯，是沒有足夠訓練讓模型讀 state           |
| **結果可對話**           | 唯一會連貫對話的是合併的 Qwen3-0.6B／本地 Qwen1.5B；前者 exact 0，後者是對照組而非核心                                      | 核心分仍 0.00/10，`census` produced=0                  |
| **評測口徑**             | exact string 比對開放式長答案永遠 0；79%/87.6% 對話分數由 verifier／表層產生                                                | 需要 strict benchmark scoring + state 消融，不是改門檻 |
| **生產接線**             | llama.cpp server 兩次被時限 SIGTERM；chat 路徑表層先答、LLM 只在 fallback                                                   | 可比數字只存在 `core_control.json` 的對照臂            |

## 3. 做過哪些研究（`CORE_GAP_ANALYSIS.md` 95 節＋本輪）

以下按「問題類型」整理，不按時間；每類都有 negative result，避免重複：

| 類別           | 代表章節／實驗                                                                  | 已知結論                                                                                                                |
| -------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 表徵與解碼     | §二、§35、§45–47                                                                | 字典釋義當 token 表徵不可區分；byte/char 階段只拿到格式，不是語言                                                       |
| 規模           | §34（108.6M）、scaleup_phase1/2、KD 40k                                         | 108M 的 84% 是輸出投影；大 SNN train exact 0.5–2.5%；KD loss 3.9；核心仍 0                                              |
| 架構對照       | §36 SNN vs GRU、MVE-1 SNN vs Transformer、M0 149k 四臂                          | GRU 0.680 vs SNN 0.349（0.1M）；兩個架構在 MVE-1 都 gate FAIL；149k 上 GRU CE 1.145／transformer 2.198，free exact 全 0 |
| 單一核心 state | §37–§44（T1–T6、state 內容、兩組綁定）、本輪 value-token／memory-token          | state 可攜帶內容（0.995）但一次只能一組；可定址槽尚未成立；新機制 recall ≈ 猜測                                         |
| 記憶定址       | §59–§84（pantry 系列）                                                          | 名字可讀（0.935）、值弱（0.620）、query 沒用 state 選（0.500）→ 狀態裡的內容沒被讀出端使用                              |
| 泛化與反事實   | §90–§95                                                                         | 換數字答案不跟著算；界線是「是否離開訓練支撐」，不是位數                                                                |
| 評測與治理     | intelligence_report、provenance_census、probe_native_dialogue、check_fact_gates | 分數與來源可追溯；核心 0、系統 6.41；門禁全綠                                                                           |

本輪（2026-11-27）新增但**未達成**的：M0 149k 四臂、20M
token 平台、subword、answer-only、from-scratch 19M
Transformer、單核心 state、Qwen 合併 + state 投影／memory tokens。全部寫在
`MODEL_AND_LLM_PROGRESS_2026-11-26.md`。

## 4. 連貫判斷（不再把錯誤路徑當選項）

1. 核心必須**自己會說話**；把語言交給另一個模型、核心只管狀態，不是同一個模型，違反 R1。
2. 把 state 當小模組接到已學會語言的模型上，state 會被語言先驗淹沒；本輪三種注入方式都是這個失敗模式。
3. 從 0 訓一個小模型，在 5M–20M
   token 下只學到字符統計，連連貫生成都沒有；不是把 LIF 換成 Transformer 就能補。
4. 要讓 state 在模型內被用，必須**讓模型在足夠規模的訓練中學會讀 state**；不是 30–600 步，也不是只換表徵。
5. 因此目前**沒有一個可用、能對話的核心模型**。唯一會對話的載體是外部預訓練模型，而它目前是對照組／fallback，不是核心。
6. 結論不是「再換一個架構」，而是：在取得 10⁸–10⁹
   token 級多輪語料與相對應訓練前，核心分不會動；任何在這個 session 內宣布「可比」的說法都是假的。

## 5. 唯一接下來該做的事（不是選項清單）

把「語料與訓練規模」當成核心專案的前置條件：先有 10⁸
token 級多輪／指令語料與可重跑的 train→save→ablation 管線，再訓練一個把 state 內建的模型，並用真／零／隨機 state 三臂消融量測影響。在那之前，所有「核心模型可用」的宣稱都不成立。

**2026-11-27 資源與語料（已實際盤點／下載）**：

| 項目       | 實測                                                                                                     |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| 磁碟       | 916 GB 總量、~89 GB 可用（90% 已用）                                                                     |
| RAM / CPU  | 15 GB（可用 ~9 GB）、12 核心                                                                             |
| 加速器     | Intel Arc B570，10.6 GB VRAM，XPU available（曾有 `DEVICE_LOST`，已恢復）                                |
| 已下載語料 | `HuggingFaceH4/ultrachat_200k`（1.6 GB）、`BAAI/COIG`（338 MB）、`YeungNLP/firefly-train-1.1M`（1.2 GB） |
| 正規化語料 | `data/core_corpus`：477,108 sessions、206,396,814 tokens、32k BPE（1.9 GB）                              |

結果寫入 `data/intelligence_reports/core_model_training.json` 與
`data/models/angela_core`。

**2026-11-27 五輪大訓練的完整結果（全部 `not_demonstrated`）**：

| 輪  | 做法                                                      | 規模                | 結果                                          |
| --- | --------------------------------------------------------- | ------------------- | --------------------------------------------- |
| 1   | prefix memory，一般語料                                   | 12k 步 / 44M token  | loss 10.4→6.5，生成「Sure/Yes」，消融全 0     |
| 2   | 加 25% 合成 state（候選只有 6 個）                        | 40k 步 / 150M token | loss ~2–7，模型背答案（loss 0.03），消融全 0  |
| 3   | 隨機 8 字元代號、修正 state 不一致                        | 20k 步              | loss ~1–7，生成僅碎片，消融全 0               |
| 4   | K=32、50% state 任務                                      | 25k 步              | loss ~1–7，生成「你的XJ。」部分格式，消融全 0 |
| 5   | **cross-attention memory**（state 當 K/V，question 當 Q） | 15k 步 / 80k turns  | loss ~2–5，生成只剩「....」，消融全 0         |

結論：在 89M 參數、2 億 token 語料、單機 Arc B570 的規模下，從 0 訓練的 single
model 始終無法在 prompt 只有問題時從 state 取值回答。問題不是單一超參、不是注入方式、也不是合成任務設計——是模型規模與訓練量不足以同時學會語言與 state 讀取。
`data/models/angela_core*`
的 checkpoint 已保存，但**不可作為可用核心模型宣稱**。

**按資源訂出的上限（2026-11-27）**：VRAM 10.6 GB 在 fp32 +
AdamW 下，3 億參數約需 3.6 GB（權重+優化器）＋ 3–4
GB 激活，是單機安全上限。smoke 實測：`d=1280 / layers=16 / heads=16 / memory=32`
= **304,683,008 參數**，10 步 9.4 秒（~0.94
s/步），無 OOM。因此正在跑最大可行規模： **25,000 步 × batch
2、~6.5 小時、cross-attention state、50% 不可背誦合成任務**。結果寫入
`data/intelligence_reports/core_model_large.json` 與
`data/models/angela_core_large`；gate 仍為 `real>=8/30` 且 `delta>=3`。

**實際結果（2026-11-27
23:21）**：25,000 步跑完、7,212 秒（2 小時，比預估快），88,488 turns、loss
1.0–7.9 震盪，但消融仍是
`real=0 / zero=0 / random=0`，生成只剩句點（`....`），`not_demonstrated`。**這是在可用資源上限內能跑的最大規模，仍不足以做出可對話、可用 state 的 single
core model。**
六輪從 0 訓練（12k／40k／20k／25k／15k／25k 步）一致失敗，已排除超參、注入方式、合成任務、模型規模（89M→305M）與訓練量（44M→200M
tokens）的單一因素；剩餘瓶頸是 **state 的寫入沒有被訓練**（`new_state`
被 detach，只訓練「讀」、沒訓練「寫」），以及整體規模仍低於語言模型形成對話能力所需。這兩個都需要新的訓練設計／更多資源，不能在原 session 內偷渡。

**2026-11-28 state 寫入 bug 的完整追蹤（不是規模問題）**：

1. 文獻（`hf papers search`：RMT 2207.06881、Titans 2501.00663、LiveMem
   2608.02515）一致指出：memory 必須被明確訓練**寫入**，不能只把向量接到輸入。
2. Linear probe 量舊 checkpoint：state 解出代號首字只有 **0.09**（chance
   0.028）→ state 裡幾乎沒有要記的內容。
3. 第一個 write objective 加了 aux loss，但 probe 只升到 **0.18**——因為
   `new_state = tail.detach()` 把梯度切斷，aux loss 只訓練 `mem_readout`，
   **產生 state 的模型本體完全沒被訓練寫入**。
4. 已修：forward 不再 detach；目前回合的 state 保留計算圖給 write
   loss，backward 後才 detach 傳給下一回合（避免重複 backprop）。state 也改成固定 K 向量（短回合從前面補）。15k 步重訓正在跑。
5. 潘多拉的結論：**前面六輪失敗不是不夠大，是 state 的寫入路徑被 detach 切斷**。Gate 不改：仍需
   `real>=8/30` 且 `delta>=3`。

**2026-11-28 後續除錯（全部修好但問題仍未解決）**：

- 均勻 state 錨點（MARCH/ATLAS 式）：state 從整句取樣而非只取尾端。
- **雙重 special tokens**：`tok.encode()` 預設加 BOS/EOS，程式又手動加
  `[1]/[2]`，訓練格式與 eval 不一致。已全面改 `add_special_tokens=False`，eval
  teaching 格式也對齊。
- 純化任務（答案只有代號本身、無模板稀釋）、aux WRITE loss 收到 ~0。
- **結果**：真／零／隨機 state 消融仍全 0；生成是重複字串（`ZNJNJN…`）。代表 state 確實被寫入（aux≈0），但模型在 prompt 只有問題時**讀不出精確值**，或語言解碼本身尚未成形。
- 誠實結論：今天修掉的是四個真 bug（detach 梯度、state 形狀、token 格式、評測錯位），它們都**確認已修**；但「核心模型可用、能對話、state 影響可測」這個目標**尚未解決**。剩下的不是再調一個本地開關，而是需要真正的 content-addressed
  write/read 架構與足夠的語言訓練規模；不可把 checkpoint 宣傳成成果。
