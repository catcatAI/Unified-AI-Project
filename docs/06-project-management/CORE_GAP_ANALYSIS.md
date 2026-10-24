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

## 五、架構替換：token-SNN 已實作並量測（2026-10-23）

上面第 1–2 步已落地：`apps/backend/src/ai/ed3n/token_snn.py`（字元詞表 → LIF
（surrogate gradient，Neftci 2019）→ 線性 next-token head；答案 token 的交叉熵、
teacher forcing）＋`scripts/train_token_snn.py`（可讀 CSV/JSON/JSONL、可給獨立
held-out split、存 checkpoint 與報告）。

**架構正常**（可學習性檢查）：複製任務（echo 5 個詞、60 epochs）**5/5 完全
正確**，loss 0.005。所以它不是「連最佳化都不會」。

**實測（可重現）**：

| 任務 | 訓練 | held-out | 結果 |
| --- | --- | --- | --- |
| 複製（echo） | 5 詞 ×20 | 同 5 詞 | **5/5 exact** |
| 算術（加減乘除） | 30,000（`arithmetic_train_dataset.json`） | 500/2,000（`arithmetic_test_dataset.csv`） | **0/500 exact**（20 epochs、154 秒、loss 1.75） |
| 核心凍結題（math 40／knowledge 15） | 20,000 對（`core_train.jsonl`） | 同基準 | **0%**（loss 2.49，未收斂） |

teacher-forced 字元準確率在訓練列上 **38.5%**（3,000 列、40 epochs、
`d_hidden=128`；可重現），表示它學到了數字分布，但**沒有學到進位演算法**，
自由生成 сразу 漂移，所以 exact 是 0。這與規模一致：1.5B 的 LLM 在 GSM8K
等級也只到 60%；這個核心只有 **~0.1M 參數**（`d_emb=96`、`d_hidden=192`、
字元詞表 170），在 CPU 上不可能補上這個差距。

**量測修正（同日）**：對照表以前只印百分比，把「沒有輸出」和「答錯」混在一起。
現在每個生產者都記 `answered`／`coverage`／`distinct`：

* **GARDEN：0/40 有回答**（`generate()` 回空字串）——所以它的「0%」不是答錯，
  而是**沒有輸出**；不能拿來當能力證據。
* **TOK-SNN：40/40 有回答，但只有 2 個不同的答案**（40 題數學幾乎都是
  `The sor the and the …`）→ **模式崩潰（mode collapse）**，0% 反映的是解碼器
  塌掉，不是逐題嘗試失敗。
* **ED3N：40/40 有回答、22 個不同答案**，但都錯（`何为`、`六 〦 亅 兆电子伏…`）
  → 有在產生內容，內容沒有條件性。
* LLM：40/40 有回答、38 個不同答案、60% 正確。

這讓「0%」的意義變清楚了：GARDEN 是缺席，TOK-SNN 是塌陷，ED3N 是亂答。三者都
不是智能，但修法不同（缺席要接上解碼器、塌陷要訓練收斂、亂答要換表徵——後者
已做）。

**結論（更新版）**：表徵與目標已經換對，缺口現在是**規模與訓練預算**，不再是
「字典釋義／關聯訓練」的結構錯誤。要跨過外部及格線（math 61%、paraphrase 70%）
需要：

1. 更大的模型（≥10⁸ 參數級）與 GPU 訓練（surrogate BPTT）；本機 CPU 以目前
   ~0.1M 參數、5 分鐘級訓練只能到「學得會複製、學不會算術」。
2. 或**蒸餾**：用本地 LLM 在非評測語料上產生分布，SNN 學分布（Hinton 2015）；
   仍需要 GPU 與數天級訓練。
3. 在達成之前，對外核心分維持 **0.00/10**；TOK-SNN 與 GARDEN／ED3N 並列在
   對照表中，不因「有模型」而加分。

**不要做的事**（已寫進門禁與文件）：把模板／路由／查表塞進核心來「補分」；
把評測題放進訓練；把 `neural` 這個字當成核心。

## 六、學習曲線：不是「再訓練久一點」的問題（2026-10-23）

`--eval-every` 讓 `train_token_snn.py` 在訓練途中量 held-out（同一條
`exact_match`），避免只看最後一點。算術（30,000 訓練／官方 `arithmetic_test.csv`，
抽 200 題、greedy）：

| epoch | loss | exact |
| --- | --- | --- |
| 10 | 1.748 | 0/200 |
| 20 | 1.706 | 0/200 |
| 30 | 1.698 | 2/200 |
| 40 | 1.700 | 0/200 |

loss 在 1.70 附近**平台化**，exact 在 0–1% 之間震盪。多訓練 20 epochs 沒有
改變結論（40 epochs、293 秒）。

**對照（診斷用，非專案程式）**：同樣的詞表與資料，換成同尺寸的 GRU
（emb 96／hidden 192，~0.18M 參數，10 epochs、64 秒）→ loss 1.13、exact
**4/200（2%）**。所以：

* 這不是「SNN 特別壞」——同尺寸的 GRU 也只能到 2%；任務（含加減乘除與小數）
  在這個參數量級就是學不動。
* 但 LIF 版本的平台（1.70）比 GRU（1.13）高，表示**同樣預算下 SNN 更吃虧**；
  要拉平，需要多層／更大的隱藏層／更長的 BPTT（即更多算力），不是換個
  learning rate。
* 兩者都離外部及格線（math 61%）很遠；這支持「缺口是規模」的結論，也說明
  **在 CPU 上把這個模型訓練到及格不是可達路徑**。

**再確認：不是「曝光偏差」（exposure bias）**。把 GRU 對照的兩種解碼分開量：

| GRU（0.18M、10 epochs） | teacher-forced 每字元 | greedy 整題 |
| --- | --- | --- |
| 測試 200 題 | 52.2% | 1.0% |
| **訓練自己看過的 200 題** | 53.7% | **2.5%** |

連**訓練題**用 greedy 都只有 2.5%（例：`178 + 101` → `289`）。teacher-forced
每字元只有 ~53%，表示它根本沒學到進位規則；如果只是曝光偏差，訓練題的
teacher-forced 會接近 100%。所以 scheduled sampling（Bengio 2015）不是這裡的
解藥；解藥是把模型／訓練預算放大到能表徵演算法為止。

三條獨立證據（學習曲線平台、同尺寸 GRU 對照、訓練題 greedy 2.5%）都指向同一個
結論：**這個量級的核心模型不可能靠 CPU 訓練跨過外部及格線**。誠實的選項只剩：

1. **給 GPU 預算**（≥10⁸ 參數、surrogate BPTT／蒸餾，天級訓練）；
2. **承認核心 0.00/10**，把 LLM 只當「能力上限參考」而不是本專案的核心；
3. **把本地 LLM 當部署核心**（它是神經模型，符合定義；但就不是「純本地自訓
   核心」的主張了，且需在報告中改寫口徑）。

在這三者之間選定之前，不應該再往 0.1M 的模型塞 epoch 或規則。

重跑：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_token_snn.py \
  --train apps/backend/data/raw_datasets/arithmetic_train_dataset.json \
  --val "" --eval-data apps/backend/data/raw_datasets/arithmetic_test_dataset.csv \
  --eval-sample 200 --eval-every 10 --epochs 40 \
  --out apps/backend/data/models/token_snn_arith.pt
```

## 七、架構升級輪：同預算 A/B（2026-10-24）

第六節的結論「平台化不是 epoch 不夠」是對的，但「SNN 更吃虧」的**原因**可以
修。這一輪只做架構與參數化的誠實調整——**不碰及格線、不碰評測題、不加規則**；
β 修正是 bug（一律生效），膜電位讀取是量測贏家（選勝後設為預設），深度／時間步
展開保留為旗標但預設關閉（量測說它們沒用），全部有測試守住，同預算 A/B 決定取捨。

### 改了什麼

1. **β 參數化缺陷修復（bug）**：`cfg.beta=0.9` 舊程式存進參數後又被
   `sigmoid()` 一次，實際漏電是 **sigmoid(0.9)=0.711**——10 步後只剩 3% 狀態
   （而不是設定的 35%）。現在參數存 logit，有效值＝設定值（有測試守住）。
2. **膜電位讀取（SLAYER，Shrestha & Orchard 2018）**：`readout="membrane"`
   ——頭每步讀最後一層的膜電位而不是二值 spike；**遞歸仍然是 spiking 的**，
   只有讀取方式不同。`readout="spike"` 保留原行為。
3. **深度**：`layers=N` 堆疊 LIF 層（層 0 吃 embedding，上層吃下層 spike）。
4. **輸入展開**：`timesteps=K` 每個 token 過 K 個 SNN 時間步再讀取（SNN 序列
   模型的標準時間解析度旋鈕，代價 Kx）。
5. **診斷**：`tf_accuracy()`（teacher-forced 答案 token 準確率）寫進 report，
   區分「沒學會」與「解碼漂移」。

### 同預算 A/B（算術 30,000、batch 64、lr 5e-3、max_len 32、12 epochs、
held-out 抽 200 greedy）

| # | 變體 | final loss | tf_acc | held-out exact |
| --- | --- | --- | --- | --- |
| A | 對照（舊行為：有效 β0.711、spike、1 層） | 1.718 | 35.8% | 0/200 |
| B | 只修 β（0.9、spike、1 層） | 1.780 | 35.4% | 0/200 |
| C | β0.9 + **membrane** | **1.601** | **39.7%** | 0/200 |
| D | C + 2 層 | 1.633 | 38.6% | 0/200 |

第二輪（全用 C 的預設 readout=membrane）：

| # | 設定 | final loss | tf_acc | held-out exact |
| --- | --- | --- | --- | --- |
| E | β0.9、K=1、**30 epochs**（平台檢查） | 1.558（10/20/30ep：1.604/1.562/1.558） | 41.0% | 0/200 |
| F | β0.99（長記憶） | 1.697 | 37.3% | 0/200 |
| G | K=4（輸入展開） | 1.826 | 33.4% | 0/200 |
| H | K=4 + β0.99 | 1.662（eval@6 曾 1/200） | 38.9% | 0/200 |

**讀法**：

* **membrane 讀取是唯一的真贏家**：同預算 loss 1.78 → 1.60、tf 35.4% → 39.7%
  （B vs C 隔離出讀取效果）。在**另一份資料**上複現：核心 20,000 對、5 epochs
  同預算重訓，loss **2.488 → 2.336**。
* **深度、長記憶、時間步展開全部變差**（D/F/G/H 各項都輸給 C）——在這個
  參數量級與 CPU 預算下，加複雜度只會更難訓練。這三項留在程式裡（`layers`／
  `timesteps` 旗標、`--beta` 可調＋測試），但**預設不開**，因為量測說它們沒用；
  輸家配置要重現就顯式傳旗標（A 對照＝`--beta 0.711 --readout spike`）。
* 平台仍在：E 到 30 epochs 降到 1.558 後趨緩，仍**高於同尺寸 GRU 的 1.13**
  （第六節），exact 仍 **0/200**。所以「膜電位修復」**縮小但沒有消除**與 GRU 的
  差距，更沒有跨過及格線——它不是新結論的依據，只是把「LIF 同預算更吃虧」的
  一半原因修掉了。

### 對照表重測（`probe_core_control.py`，2026-10-24，同題同評分）

預設 checkpoint（probe 的 tok 欄）用贏家配置同預算重訓後：

| 套件 | n | 表現層 | GARDEN | ED3N | TOK-SNN | LLM（1.5B chat） |
| --- | --- | --- | --- | --- | --- | --- |
| math | 40 | 32/40 | 0 有回答 | 0/40 | **0/40** | 27/40（68%） |
| knowledge | 15 | 7/13 | 0 | 0/15 | 0/15 | 11/15（73%） |
| code | 10 | 0 | 0 | 0/10 | 0/10 | 9/10（90%） |
| routing（表現層） | 10 | 10/10 | 0 | 0/10 | 0/8 | 0/10 |

* **TOK-SNN 的模式崩潰修好了**：math 40 題從「只有 2 個不同答案」→ **40 個
  全不同**（核心資料同預算重訓後），但仍 **0 題答對**——「有變化」不等於「有
  智能」，分数不加。
* **LLM 對照組的測量缺陷修復**（instruct 模型改走 chat 模板，commit
  `db8cc6d28`）：code 從 0/10 → 9/10、math 60% → 68%。這**只影響對照組的
  可信度**，不是本專案的分數；對照組高正好坐實「缺口是真的智能缺口」。
* **官方核心分不變：0.00/10**——probe 裡的四個核心生產者在生產路徑的佔比
  （`core_share`）仍然是 0，這些表是診斷，不是計分。

### 本輪之後仍然成立的結論

* 修參數化、換讀取方式都在 CPU 上可做且有效——但它們改善的是**收斂**，不是
  **能力**；exact 仍 0，平台仍在 1.56（vs GRU 1.13）。
* 這台機器有 **Intel Arc B570（Vulkan）**——但只接了 llama.cpp（對照組用
  `gpu_layers=-1` 真的在跑 GPU）；torch 仍是 **CPU build**，SNN 訓練沒有吃到
  這張卡。要吃 GPU 需要 torch XPU/Vulkan build（使用者決定的預算問題之一）。
* 三選一的決策面不變（GPU 規模訓練／承認 0.00／LLM 當部署核心）；這一輪只是
  把「架構本身有缺陷」這個變因**排除掉**，讓剩下的缺口乾淨地只剩規模。

重跑（A/B 全套，約 10 分鐘）：

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=6 ./.venv/bin/python \
  scripts/train_token_snn.py \
  --train apps/backend/data/raw_datasets/arithmetic_train_dataset.json \
  --val "" --eval-data apps/backend/data/raw_datasets/arithmetic_test_dataset.csv \
  --epochs 12 --batch 64 --lr 5e-3 --max-len 32 --eval-every 6 --eval-sample 200 \
  --beta 0.9 --readout membrane --layers 1 --timesteps 1 \
  --out /tmp/tok_winner.pt --report /tmp/tok_winner.json
```
