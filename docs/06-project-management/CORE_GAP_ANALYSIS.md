# Core Gap Analysis — 為什麼 SNN 核心訓練後仍是 0

> 2026-10-23。問題不是「還沒訓練夠」，是**表徵與解碼壞了**。這份文件記錄證據、
> 根因、已修的機械缺陷，以及要讓核心真正答題所需的架構工作。**不要**用模板／路由
> 填這個缺口——那只會讓分數看起來像智能。

## 一、問題

`probe_core_control.py`（同一批凍結題目、同一條評分）量到：

| suite | 表現層 | GARDEN | ED3N（訓練後） | LLM（對照） |
| --- | --- | --- | --- | --- |
| math（40） | 80% | 0% | **0%** | 60% |
| knowledge（15） | 47% | 0% | **0%** | 67% |
| code（10） | 0% | 0% | 0% | 0% |
| routing（10） | 100% | 0% | 0% | 0%（表現層任務） |

ED3N 是在**同一份** `core_train.jsonl`（157,311 對；149,489 train／7,822 val）上
訓練的：20,000 對、1 epoch、187 秒，`loss=0.1399 acc=0.9997`，checkpoint
`apps/backend/data/models/ed3n_core.json`。**訓練準確率 99.97%，生成正確率 0%。**

## 二、根因（逐項可重現）

### 1. `encode()` 把詞變成「字典釋義」，不是 token

```
encode("12 + 7")
  -> ['m2',
      'cedict_numeral_1_in_the_suzhou_numeral_system_...',
      'cedict_1_divided_by_16_is_0_0625_abacus_rule',
      'cedict_the_seven_apertures_of_the_human_head_...']
```

`DictionaryLayer.encode` 先把詞查到 CC-CEDICT／JMdict，再把**釋義字串**當成 key。
於是輸入的 key 空間是「詞義」而不是「符號」，`12 + 7` 與 `178 + 101` 共享大部分
key（都是數字＋算盤規則），運算子與順序消失。**輸入本身不可區分，任何訓練都不可能
學到對應**。

### 2. 解碼把釋義的表面形式接起來 → 字詞湯

```
IN  : What gas do plants absorb from the air for photosynthesis?
GOLD: carbon dioxide
GEN : 在忙吗 兴奋 嗯 烦恼 明天见 心情 难过 欢迎 早上好 开心
```

即使是**訓練時看過的**那一句，`generate()` 也回不出目標（同一題 loss≈0.14、
`acc=0.9997`）。`StepDecoder` 在 key 空間上挑 activation 最高的幾個，再印出它們的
`zh`/`en` 表面形式；key 是釋義，輸出自然是無關的釋義片段。

### 3. 訓練目標不是「下一個 token」，所以教不會生成

`JointTrainer` 更新的是關聯/序列邊權（Hebbian `add_directed`／`adjust_connection`），
`generate()` 讀的是 `forward_sequential` 的門檻 activation。關聯路徑與解碼路徑共用
同一個 `CoreNetwork` 實例，但沒有可微的輸出層，也沒有 next-token 交叉熵；因此
「關聯正確」不會變成「字串正確」。這是架構問題，不是 epoch 或 learning-rate 問題
（1 epoch 與 5 epoch、500 與 20,000 對，生成都錯）。

### 4. `process()` 只是「相關」不是「正確」

```
process("What gas do plants absorb ...") -> "Its main functions are photosynthesis and gas exchange. ..."
process("Find the area of a square ... 5 cm") -> "4"
```

知識題回的是百科相鄰句（相關性），面積題回錯。`process()` 的知識分支是 SNN bus 的
文字生成；它與 `generate()` 共用同一個壞表徵。數學之所以好看，是因為 `process()`
先走**確定性計算器**（那是表現層，不是核心）。

## 三、這次修好的機械缺陷（與根因分開）

1. **CLI 訓練沒訓練生成路徑**：`python -m ai.ed3n train` 只建 `TrainingBatch`，
   從未建 `SeqBatch`；`generate()` 讀的 sequence 邊從沒被訓練。已改為同時訓練
   （`seq_batch_from_examples`），並加回歸測試（`tests/test_ed3n_cli_training.py`）。
2. **Alpaca 資料被丟掉**：`_load_train_examples` 只讀 `input`（alpaca 的 `input`
   幾乎都是空的），`instruction` 被忽略 → 「No valid examples」。已改成
   `instruction (+input)`，並支援 `question`/`prompt`/`response`/`jsonl`。
3. **訓練資料沒有整理、也沒有防洩漏**：新增
   `scripts/prepare_core_training_data.py`（正規化、去重、確定性切分、manifest
   雜湊、**benchmark 洩漏檢查**）。實跑：157,311 對（149,489/7,822），丟棄
   26 筆與評測題重疊的樣本。
4. **ED3N 進入對照表**：`probe_core_control.py` 多一欄 ED3N（讀 checkpoint、
   讀外部字典、**直接讀 decoder**，不經 reflex 模板）。

## 四、讓核心真的會答題（唯一誠實的路）

參考文獻（按用途）：

- **SNN 可訓練性**：Neftci, Mostafa & Zenke (2019), *Surrogate Gradient Learning in
  Spiking Neural Networks*（BPTT + 替代梯度，讓 SNN 能做 next-token 預測）；
  Shrestha & Orchard (2018), *SLAYER*（時序誤差反傳）。
- **序列解碼**：Bengio et al. (2015), *Scheduled Sampling*（本專案已有機制，
  缺的是可微目標）；Mikolov et al. (2010), RNNLM（next-token 交叉熵）。
- **表徵**：Sennrich et al. (2016), *BPE*；word2vec (Mikolov 2013)／
  sentence embeddings（本專案已有 MiniLM，可直接用）。
- **以對照組為老師**：Hinton et al. (2015), *Distilling the Knowledge in a Neural
  Network*（用 LLM 的分布教 SNN，而不是把 LLM 的答案當模板塞進去）。
- **規模／評估**：Kaplan et al. (2020) scaling laws；Hoffmann et al. (2022)
  Chinchilla；MMLU／GSM8K 作為外部及格線（本專案已採用）。

具體步驟（依序，每步都要能量）：

1. **換表徵**：`DictionaryLayer` 之外新增 token/BPE 詞表（`encode` → token ids），
   保留舊字典給知識層用；核心不再用釋義當 key。
2. **換輸出層**：`StepDecoder` 改成 embedding → SNN → logits（詞表大小），
   用**替代梯度**做 next-token 交叉熵；`generate()` 用同一個輸出層。
3. **資料**：`core_train.jsonl` 已經是乾淨的 (input, output) 對；另需把
   `association_train.json`（100k 關係句）與 wiki 導言句做語言模型預訓練，
   讓解碼先學會「像話」，再學問答。
4. **蒸餾**：先讓 LLM 在**非評測**語料上產生答案分布，SNN 學分布（Hinton 2015）；
   評測集（`native_bench_v1`／`paraphrase_v1`）永遠不進訓練。
5. **量**：`probe_core_control.py` 固定四欄（表現層／GARDEN／ED3N／LLM），
   同一評分；核心分只有「核心產生且正確」才算。

在那之前，對外數字就是 **核心 0.00/10**；系統分 5.75 只是表現層。
