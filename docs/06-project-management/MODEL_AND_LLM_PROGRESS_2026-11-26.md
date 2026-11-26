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

**在生產聊天路徑上，目前沒有會說話的模型**（ollama 空、llamacpp
slots 停用、unified 是確定性＋統計核心）；但
**llama.cpp 這條路徑不是空的**——本機有 3 個 GGUF、`llama_cpp`
套件與 provider 都在， `probe_core_control.py` 直接用 in-process
llama.cpp 載入 1.5B GGUF，得到 math 67.5%／knowledge 73.3%／code
90% 的正解。**差的是接線，不是載體**。

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

| 里程碑                                                   | 狀態                       | 證據                                                                                                     |
| -------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------- |
| M0 四臂 A/B（LIF-1L / GRU-2L / Transformer-6L / hybrid） | **部分完成（2/4 臂）**     | §36 已做 LIF vs GRU（`compare_snn_gru.py`）；無 Transformer-6L / hybrid 腳本                             |
| M1 BPE 32k 中文 + session 切分 + 洩漏守門                | **未開始**                 | 無 BPE 相關腳本／資料                                                                                    |
| M2 30M/80M、ctx 1024 預訓練                              | **未開始**                 | 無對應 checkpoint／報告                                                                                  |
| M3 SFT + 工具呼叫軌跡                                    | **未開始**                 | 無 SFT 語料／訓練產物                                                                                    |
| M4 併入單一核心契約                                      | **只有契約、沒有可用模型** | `AI_AL_SINGLE_CORE_CONTRACT.md` §14（R1：一份權重＋一個 state）；ollama 空、SNN 0/40、llamacpp slot 停用 |

算力估算（記錄用，未實測新訓練）：108M × 千萬 token / 6,677 s → 實效不到 1
TFLOPS；30M × 1B token 粗估 ~50 小時，batch 加大 +
bf16 後有機會 10–15 小時。**瓶頸是資料**：1B
token 中文對話語料本地沒有，149k 答案式配對只會養出模板機。

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

## 6. 尚未開始的 MD P0

`DATA_LIFE_AND_PROJECT_STATUS_REPORT_2026-11-26.md`
§8 的 P0（統一 manifest、lineage、quarantine gate、retention
trace）**尚未實作**——只完成了方向決定。它仍是下一階段的基礎設施缺口。

## 7. 下一步（二選一，需人為決定）

1. **產品線（便宜、當週可為）**：起 llama.cpp server（用既有 1.5B/7B GGUF）、把
   `llm.user.yaml` 的 llamacpp slot 打開，讓 `generation_available()`
   看見；核心仍當「腦」（狀態／記憶／路由／驗證），語言交給 llama.cpp。
   **代價**：核心分契約要改——目前只算神經產生且正確，會永遠 0。
2. **研究線（M0）**：做四臂 A/B（補 Transformer-6L /
   hybrid 兩臂），同一份 149k 語料、等參數等步數，用 val loss +
   100 列 free-running exact 裁決。 **否證條件**：Transformer-6L 的 val
   loss 仍 >3.5 → 問題在分詞／資料，不在架構。

不建議：續訓 108M、把確定性/模板算進核心分、拿 `logs/deviation`
的 mock 當品質證據、用「單一模型」當理由拔掉 LLM（R1 只要求一份權重＋一個 state，沒要求必須是 SNN）。
