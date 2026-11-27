<!--
  FILE_PATH: docs/06-project-management/MODEL_AND_LLM_PROGRESS_2026-11-26.md
  FILE_TYPE: documentation
  PURPOSE: 模型與 LLM 載體進度快照（每個數字附量測來源）
  VERSION: 1.0.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-11-26
  AUDIENCE: developers, agents
-->

# 模型與 LLM 載體進度（2026-11-26）

> **量測基準**：HEAD `4cb815ce6`。所有 `data/`、`apps/backend/data/`
> 下的產物都在
> `.gitignore`（本機訓練/推論產出），**clone 後不會自帶**；要重跑請用本文列出的指令。
>
> **原則**：只記「量到的」與「查到的」，分數與模型能力分開；快照值不改寫，漂移另記。

## 1. 一句話現況

**2026-11-27 更新：llama.cpp 已接線，生產聊天路徑現在有會說話的模型。** 做法：起
`python -m llama_cpp.server --model data/models/qwen2.5-1.5b-instruct-q4_k_m.gguf --model_alias qwen2.5-1.5b-instruct --port 8081 --n_gpu_layers -1 --n_ctx 2048`；把 gitignored 的
`apps/backend/configs/system/llm.user.yaml` 的 `llamacpp-qwen` slot 設為
`enabled: true`、`preferred_backend: llamacpp-qwen`。驗證：`/v1/models`
回 alias；`generation_available()` True 且兩個後端 health OK；真實
`ChatService.generate_response("天空為什麼是藍色的?")` 回傳
`backend=llama.cpp, model=qwen2.5-1.5b-instruct` 的中文解釋。

**非持久警告**：第一次啟動被外層 1 小時時限 SIGTERM 停掉，LLM 路徑隨之失效（slot 仍 enabled，但 health
probe 失敗會被 prune → fallback）。2026-11-27 已用 12 小時時限重啟（PID
637290，`/v1/models` 再驗證 OK）。要長期使用請手動起 server 或做成 service；
**不要把「config 開了」當成「模型一直在」。**

**核心分仍 0.00/10**：凍結題由表層（knowledge_pipeline／deterministic-math）先答，
`census_reply_provenance`
仍記 lookup=8／computed=32／classifier=10／produced=0——
LLM 只在表層放棄時接手；核心分契約也把 LLM 對照臂排除在計分外。
**所以「可比」現在成立於模型層（同題 LLM 臂 67.5/73.3/90%），不成立於核心分層。**

ollama 仍是空的；llama.cpp 是本機 3 個 GGUF、`llama_cpp 0.3.35`、provider 與 generation
gate 都在。

## 2. 核心模型（token-SNN / 108M）現況

| 項目              | 實測值                                                                                              | 來源                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 最大核心          | 108,583,431 參數（d_emb 512 / d_hidden 2560 / layers 1 / timesteps 1 / vocab 32,773 / max_len 192） | `data/intelligence_reports/token_snn_108m.json` 的 `config`      |
| 輸出投影          | 2560 × 32,773 = 83,898,880（約 77% 參數）；真正主體是一層 2560 維 LIF 遞歸                          | 同上，`d_hidden × max_vocab`                                     |
| 語料              | 149,489 列 / 31 MB（`core_train.jsonl`）                                                            | `wc -l` / `du -h apps/backend/data/processed/core_train.jsonl`   |
| 訓練預算          | batch 4、lr 1e-3、1 epoch、6,677 秒、XPU（Arc B570）                                                | `token_snn_108m.json` + `CORE_GAP_ANALYSIS.md` §34               |
| 記憶視野          | beta **0.5407**（約 2 token）、threshold **1.9995**（θ_max 2.0，已飽和）                            | `token_snn_108m.json` 的 `dynamics`                              |
| 梯度帶            | near_threshold **0.0018**（`CORE_GAP` §35.5 的 0.0014 是舊快照；結論同：幾乎關閉）                  | 同上                                                             |
| 凍結題            | math 0/40、knowledge 0/15、code 0/10                                                                | `core_control_108m.json` 的 `tok` 欄                             |
| 有回答 / 不同答案 | math 37/40、19 distinct；knowledge 15/15、9 distinct；code 6/10、5 distinct                         | 同上 `coverage` / `distinct`                                     |
| 自由生成          | val 100 列 **8/100**，命中的是比較句格式與 `False`                                                  | `token_snn_108m.json` 的 `eval` + `CORE_GAP` §34.1               |
| teacher-forced    | 0.4215                                                                                              | `token_snn_108m.json`                                            |
| 等參數等步數對照  | small：SNN 0.3486 vs GRU 0.6798；large：SNN 0.0111 vs GRU 0.8058                                    | `data/intelligence_reports/snn_vs_gru.json`（§36.5，5 種子配對） |

**推論**：108M 是誤導的規模感；LIF-1L 不是缺預算，是序列學習機制在此配置下不成立（§36 在等參數、等步數、同資料、同目標下 GRU 大幅勝出，大 SNN 連訓練集都沒擬合）。
**不要續訓 `token_snn_108m.pt`**（beta
0.54、threshold 釘死、梯度帶關閉，§35.5 已判不作基底）。

## 3. LLM 載體現況（ollama 之外）

| 項目                  | 現況                                                                                                                                                          | 來源                                                                                                                  |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| ollama                | 已安裝（`command -v ollama`）但 `ollama list` **空**                                                                                                          | 本機執行                                                                                                              |
| llama.cpp Python 套件 | `llama_cpp 0.3.35`                                                                                                                                            | `./.venv/bin/python -c "import llama_cpp; print(llama_cpp.__version__)"`                                              |
| 本機 GGUF             | `qwen2.5-1.5b-instruct-q4_k_m.gguf`(1,117,320,736 B)、`qwen2.5-7b-instruct-q4_k_m.gguf`(4,683,074,240 B)、`qwen2.5-14b-instruct-q4_k_m.gguf`(8,988,110,976 B) | `ls -la data/models/*.gguf`                                                                                           |
| llama.cpp provider    | `apps/backend/src/services/llm/providers/llamacpp.py`                                                                                                         | 檔案存在                                                                                                              |
| generation gate       | `llamacpp` / `llamacpp-qwen` / `llamacpp-gemma` 被列為 **GENERATIVE_BACKENDS**（可吃提示改寫）                                                                | `apps/backend/src/services/llm/generation_gate.py`                                                                    |
| 預設設定              | `llm.default.yaml` 三個 llamacpp slot 全部 `enabled: false`（需手動起 server）                                                                                | `apps/backend/configs/system/llm.default.yaml`                                                                        |
| 本機 user 覆寫        | `llm.user.yaml`（**gitignored**）也全部 `enabled: false`，原因：8080/8081 的 llama-server 未運行；`preferred_backend: unified`                                | `apps/backend/configs/system/llm.user.yaml`                                                                           |
| llama-server 可執行檔 | 不在 PATH；但 `llama_cpp.server` Python module 可 import → 可起 server                                                                                        | `command -v` / `import llama_cpp.server`                                                                              |
| **in-process 實測**   | `probe_core_control.py` 以 `llama_cpp.Llama` 直接載入 1.5B GGUF：math **67.5%**、knowledge **73.3%**、code **90%**（Qwen 角色 slot 另有 0.6 coverage 等診斷） | `data/intelligence_reports/core_control_108m.json`（`llm` 欄，provenance `qwen…gguf (ok; mode=chat, gpu_layers=-1)`） |
| role 設定             | `role_b` → `llamacpp-gemma`、`role_c` → `llamacpp-qwen`（slot 目前停用，會走 fallback）                                                                       | `apps/backend/configs/system/roles.default.yaml`                                                                      |
| 舊 mock 殘跡          | `logs/deviation/metrics_20261026_192612.json` 的 `llm_full` 回「蓝色。」——那是**沒有真模型時的輸出**，不是對話品質證據                                        | 檔案內容                                                                                                              |

**結論**：「沒有會說話的模型」只在**生產聊天路徑**成立；llama.cpp 的載體（GGUF + 套件 +
provider + 可起 server 的 module）與能力（probe 的 67.5/73.3/90%）都已存在，差的是把 slot 接上並讓
`generation_available()` 看見。

## 4. 研究計畫 M0–M4 進度

| 里程碑                                                   | 狀態                               | 證據                                                                                                                                                                                                                                                         |
| -------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| M0 四臂 A/B（LIF-1L / GRU-2L / Transformer-6L / hybrid） | **部分完成；不可照抄**             | §36 已做 LIF vs GRU（`compare_snn_gru.py`／`snn_vs_gru.json`）；`mve1_architecture_comparison.json` 已做 SNN vs causal Transformer，但題目是 **MVE-1 AI+AL atoms 對**（不是 149k 語言任務）。**不要重跑 MVE-1**；若要 M0，必須另立 149k 語言任務的預登記協定 |
| M1 BPE 32k 中文 + session 切分 + 洩漏守門                | **部分完成／未開始**               | `scripts/prepare_core_training_data.py` 已有正規化、去重、95/5 切分、**manifest + source sha256 + benchmark 洩漏檢查**（`ai_al_manifest.json` 可證）；但 **BPE 分詞尚未做**（仍為字元/整句 token）                                                           |
| M2 30M/80M、ctx 1024 預訓練                              | **已有不同規模的訓練，但非此配置** | `scaleup_phase1*.json`／`scaleup_phase2_*.json`／`kd_scaleup_*.json`／`width_ab_*.json`／`token_snn_core149k.json` 已跑；皆為 LIF 系列、max_len 192，不是 Transformer-6L／ctx 1024                                                                           |
| M3 SFT + 工具呼叫軌跡                                    | **未開始**                         | 無 SFT 語料／訓練產物；`chat_qwen.py` 只是用既有微調 adapter 對話，不是 SFT 訓練                                                                                                                                                                             |
| M4 併入單一核心契約                                      | **只有契約、沒有可用模型**         | `AI_AL_SINGLE_CORE_CONTRACT.md` §14（R1：一份權重＋一個 state）；ollama 空、SNN 0/40、llamacpp slot 停用                                                                                                                                                     |

算力估算（記錄用，未實測新訓練）：108M × 千萬 token / 6,677 s → 實效不到 1
TFLOPS；30M × 1B token 粗估 ~50 小時，batch 加大 +
bf16 後有機會 10–15 小時。**瓶頸是資料**：1B
token 中文對話語料本地沒有，149k 答案式配對只會養出模板機。

## 4.0 M0 語言任務實測（2026-11-27，新協定，非 §36/MVE-1）

`scripts/probe_core_lm_ab.py`：149k 自然語言答案配對、同 next-token 目標、同 token 預算，char-level 詞表 229、XPU。跑前登記：**Transformer
val CE > 3.5 → 資料/分詞瓶頸，終止架構線。**

| 預算               | 臂                               | val CE                            | free exact/30 |
| ------------------ | -------------------------------- | --------------------------------- | ------------- |
| 200k tokens / d256 | LIF / GRU / Transformer / hybrid | 2.557 / **1.863** / 2.198 / 2.062 | 0 / 0 / 0 / 0 |
| 2M tokens / d512   | GRU / Transformer                | **1.158** / 2.356                 | 0 / 0         |

否證未觸發（Transformer 2.198/2.356 ≤
3.5），所以不是分詞/資料死路。但 GRU 生成「The states of the store is a string
of the story…」——語法-like、語意不對；模型在學 char 分佈，還沒學到「答案」。

**跑前登記的下一個否證（20M tokens / GRU d768，已在跑）**：若 free
exact 仍為 0，
**結論是不可再靠「加資料/加預算」**，必須改表徵（subword/BPE）或改訓練目標（指令/SFT、蒸餾），並把這條寫成研究結論，不是再加大一次。

## 4.1 已執行研究清單（**不要重複執行**）

下列研究都已有產物（報告在 `data/intelligence_reports/`，多數在
`.gitignore`，可重跑但不要當新問題再問一次）：

| 類別                          | 已跑過的 experiment / 報告                                                                                                                                                                                                               |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SNN 規模與資料                | `token_snn.json`、`token_snn_arithmetic*.json`、`token_snn_core149k.json`、`token_snn_curriculum.json`、`token_snn_distill.json`、`token_snn_108m.json`、`token_snn_xpu_soak.json`                                                       |
| Scale-up / KD                 | `scaleup_phase1*.json`、`scaleup_phase2_*.json`、`kd_scaleup_*.json`、`scale_envelope.json`                                                                                                                                              |
| 架構對照（已做！）            | `snn_vs_gru.json`（LIF vs GRU）、`width_ab_*.json`、`mve1_architecture_comparison*.json` 與 `mve1_emergence_boundary_transformer*.json`（SNN vs causal Transformer，MVE-1 題目）、`mve1_cellular_baseline.json`                          |
| TLN 自研架構                  | `tln_phase0..13*.json`（含 `_b1`、`_tok` 對照）；`CUSTOM_ARCHITECTURE_PLAN.md`                                                                                                                                                           |
| AI+AL / 下游                  | `ai_al_round1..10*.json`（含 guarded）、`al_downstream_v7..v22*.json`、`al_c_*.json`、`al_phase_effect.json`、`al_ladder.json`                                                                                                           |
| 状态/記憶研究                 | `data/pantry_stage/*`（§49–§84 的 fit/composition/address/readrule/…）、`probe_state_cycles*.json`、`probe_state_restart.json`                                                                                                           |
| 對話/改述/歸因                | `native_dialogue.json`、`paraphrase.json`、`dialogue_teaching`、`neural_learning`、`intelligence_sources.json`、`reasoning_unseen.json`、`provenance_census.json`                                                                        |
| Core control（多 checkpoint） | `core_control.json`、`core_control_108m.json`、`core_control_core149k.json`、`core_control_distill.json`、`core_control_ai_al_round1.json`                                                                                               |
| LLM 基線                      | `exp_gemma_baseline.py`（Gemma E2B Q4_0 的 18 事實探針）、`chat_qwen.py`（Qwen3-0.6B 微調 adapter 對話）、`probe_local_small_model.py`（僅硬體可行性估計，未實際載模型）、`core_control_108m.json` 的 llama.cpp 1.5B 臂（67.5/73.3/90%） |

**禁止重複的具體例子**：不要在 149k 語言任務上「重新發現 Transformer 比 LIF 好」——這在 MVE-1 題目上已經量過；新的 M0 必須換題目／換協定並先登記，不是把舊報告Copy 一份。

## 5. 今天已完成的證據鏈基礎

- 六維智能分數的分子/分母可追溯（facts 8/15、math 32/40、paraphrase
  42/56、dialogue 468/492+94/100+53/72、boundary 96/108、tools 0/10
  → 系統 6.41/10）。
- 報告工具防呆：過期快取／對照臂失敗／缺 `torch`·`llama_cpp` 都直接拒絕。
- 改述量測如實記錄編碼器為
  `onnx-fallback`（sentence-transformers 與 transformers 的 huggingface_hub 版本衝突），不再冒充 MiniLM。
- 文件舊數字糾正：pass-criteria dialogue 78→87.6%、strict
  scoring 描述、assessment 來源分布（1127→1096）、今日狀態報告的測試數快照註記。
- 門禁全綠：`check_fact_gates`／`audit_repo_facts` ALL
  PASS、`check_generated_docs` 0、mypy debt 0、定義有誤 0；`tests/` 10,868
  collected / 全 testpaths 11,526 passed / 112 skipped / 0 failed。

## 6. MD P0：部分已有，尚未完整

`DATA_LIFE_AND_PROJECT_STATUS_REPORT_2026-11-26.md`
§8 的 P0（統一 manifest、lineage、quarantine gate、retention
trace）**部分已有**：

- **已有**：`scripts/prepare_core_training_data.py`
  對**訓練資料**已寫 manifest（來源 sha256、筆數、去重、95/5 切分、benchmark 洩漏檢查），見
  `ai_al_manifest.json`。
- **缺口**：HAM 記憶、checkpoint、benchmark 結果、**訓練入口 quarantine gate**
  仍未納入同一 manifest；retention decision trace 未暴露。
- **因此 P0 的正確做法是擴充既有 manifest，不是重造一份。**

## 7.1 與其他 AI 模型的對比：到底有什麼能比？

**同題四臂對照**（`core_control.json`，Qwen2.5-1.5B 由 llama.cpp
in-process 載入）：

| 題組           | 專案表現層 | GARDEN | ED3N | token-SNN | **本地 LLM**   |
| -------------- | ---------- | ------ | ---- | --------- | -------------- |
| math (40)      | 80%        | 0%     | 0%   | 0%        | **67.5%**      |
| knowledge (15) | 53.3%      | 0%     | 0%   | 0%        | **73.3%**      |
| code (10)      | 0%         | 0%     | 0%   | 0%        | **90%**        |
| routing (10)   | 100%       | 0%     | 0%   | 0%        | 0%（錶面任務） |

**與外部錨點對比**（協定只是 analogous，不是同一份題目——及格線是可比性下限，不是「在 MMLU 上拿 45%」）：

| 維度       | 專案                 | 外部錨點                           | 讀法                                                                   |
| ---------- | -------------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| facts      | 53.3%（8/15 strict） | MMLU：隨機 25%、專家 89.8%         | 低於本地 LLM 73.3%，離專家很遠                                         |
| math       | 80%（32/40）         | GSM8K 已發表基線 87.3%             | 數字看似接近，但由確定性計算器產生，**不是模型**                       |
| paraphrase | 75%（42/56）         | PAWS：訓練後模型 85%、人類 92%     | 落後，且量測用 ONNX 備援編碼器                                         |
| dialogue   | 87.6%                | LoCoMo：人類 87.9%、最佳 LLM 51.6% | **不能宣稱打平人類**：分數用專案自己的 verifier 與確定性路徑，協定不同 |
| boundary   | 88.9%（96/108）      | FOLIO：專家 96%、GPT-4 64.2%       | 由 claim 規則＋retrieval 產生，不是模型推理                            |
| tools      | 0%（0/10）           | BFCL V4 SOTA 77.5%                 | 真實且嚴重的缺口                                                       |
| **核心**   | **0.00/10**          | 任何模型基線                       | 沒有任何由專案神經核心產生且正確的答案可比                             |

**MVE-1 架構對照**（`mve1_architecture_comparison.json`，同資料／同表徵／同目標）：SNN(1.24M) 與 causal
Transformer(1.20M, 2 layers) **兩個臂的 gate 都 FAIL** （family_hits
0、rotation_hits 0）；input→output 相關係數兩邊都接近 0（SNN
v=-0.003、Transformer v=-0.056）。Transformer 的 copy 較高（0.591 vs
0.372），但**沒有任何一個學到映射**。

### 結論：問題不只是架構

1. **在那個 task/protocol 上，架構不是瓶頸**——SNN 與 Transformer 都讀 0，問題在題目／表徵／資料，不在「用 LIF 還是用 attention」。
2. **在語言任務上，架構尚未被乾淨檢驗**——149k 是答案式配對，Transformer-6L／ctx
   1024 從未在這份資料上跑過。不能把 MVE-1 的結論搬到語言。
3. **真正落後的維度是資料型態與規模**：149k 答案配對 vs 業界 0.5B 級模型吃 10¹¹–10¹²
   token 的多輪／指令／工具軌跡；本地沒有 1B token 中文對話語料。
4. **分數歸因是另一個問題**：87.6% dialogue、80%
   math 由 verifier／計算器產生，不是模型能力；把它們當「模型很強」會得到完全錯誤的方向。
5. **接線缺口**：唯一能與外部模型公平比較的載體是 llama.cpp 的 1.5B（67.5/73.3/90%），但它在生產路徑被停用；核心契約要求的「一份權重＋一個 state」載體並不存在。

**一句話**：如果只看專案自己的神經核心，的確「沒有什麼能與其他 AI 模型比」——但這不代表問題只在模型架構；資料規模／型態、評測歸因、與生產接線都是更靠近瓶頸的位置。

## 7.2 接線後量測（2026-11-27）

| 量測                           | 結果                                                                                                                                | 來源                                            |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| 模型本身（直接 chat endpoint） | 「天空為什麼是藍色的?」答出散射和解釋                                                                                               | `curl /v1/chat/completions`                     |
| 真實 ChatService               | `backend=llama.cpp`、`model=qwen2.5-1.5b-instruct`、中文解釋                                                                        | 直接呼叫 `ChatService.generate_response`        |
| 同題 4 臂（可比）              | 表現層 80/53.3/0/100；**本地 LLM 67.5/73.3/90/0**；TOK-SNN 全 0                                                                     | `core_control.json`（venv）                     |
| 凍結題走 ChatService           | math 5/5 正確，但 4 題由 `knowledge_pipeline`、1 題 `deterministic-math`——**LLM 沒被用**，因為表層先答                              | `/tmp/opencode/prod_llm_measure.json`（小樣本） |
| 對話探針（接線後）             | 人味 0.695（輪1）/0.892（輪2）、學習效應 +0.482、有效性 ✅、一致性 ✅；與接線前 0.691/0.897/+0.554 相比**無退化**（隨機波動範圍內） | `/tmp/opencode/dialogue_after_llamacpp.json`    |
| 門禁                           | `check_default_config`（gitignored user 層 0）、`check_fact_gates` ALL PASS                                                         | 指令輸出                                        |

**結論**：現在有「能與其他 AI 模型比」的載體與分數（本地 Qwen1.5B 在同題 67.5/73.3/90%），且已接進聊天；但**核心分契約仍把 LLM 對照臂排除**，而凍結題由表層先答，所以
`census`
仍記 produced=0。要讓核心分動起來，得改契約或改量測路徑——那是人為決定，不是接線 bug。

操作註記：量測若改寫 `data/intelligence_reports/`
的 cache，manifest 的 hash 會失效——請重跑
`scripts/gen_artifact_manifest.py`。`lifecycle/` 與 `msba/`
是 runtime 會自己變的目錄，已標 `verified=false` 不進 hash gate。

## 8. 下一步（二選一，需人為決定）

1. **產品線（便宜、當週可為）**：起 llama.cpp server（用既有 1.5B/7B GGUF）、把
   `llm.user.yaml` 的 llamacpp slot 打開，讓 `generation_available()`
   看見；核心仍當「腦」（狀態／記憶／路由／驗證），語言交給 llama.cpp。
   **代價**：核心分契約要改——目前只算神經產生且正確，會永遠 0。
2. **研究線（新 M0，不可重複舊 MVE-1/§36）**：先查 §4.1 的清單—— LIF vs
   GRU（§36）、SNN vs Transformer（MVE-1 atoms）、width A/B、scale-up、KD、TLN
   phase
   0–13 都已跑過。新的四臂 A/B 必須換**題目／協定**（149k 語言任務、free-running
   exact），跑前先登記門檻與否證條件，不是在舊題目上再比一次架構。
   **否證條件**：Transformer-6L 的 val loss 仍 >3.5
   → 問題在分詞／資料，不在架構。

**不重複規則**：任何新實驗必須先能在 §4.1 找到「沒做過的那一格」；找不到就不要跑。不建議：續訓 108M、把確定性/模板算進核心分、拿
`logs/deviation`
的 mock 當品質證據、用「單一模型」當理由拔掉 LLM（R1 只要求一份權重＋一個 state，沒要求必須是 SNN）。
