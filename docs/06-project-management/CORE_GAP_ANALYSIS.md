# Core Gap Analysis — 為什麼 SNN 核心訓練後仍是 0

> 2026-10-23。問題不是「還沒訓練夠」，是**表徵與解碼壞了**。這份文件記錄證據、根因、已修的機械缺陷，以及要讓核心真正答題所需的架構工作。**不要**用模板／路由填這個缺口——那只會讓分數看起來像智能。

## 一、問題

`probe_core_control.py`（同一批凍結題目、同一條評分）量到：

| suite           | 表現層 | GARDEN | ED3N（訓練後） | LLM（對照）      |
| --------------- | ------ | ------ | -------------- | ---------------- |
| math（40）      | 80%    | 0%     | **0%**         | 60%              |
| knowledge（15） | 47%    | 0%     | **0%**         | 67%              |
| code（10）      | 0%     | 0%     | 0%             | 0%               |
| routing（10）   | 100%   | 0%     | 0%             | 0%（表現層任務） |

ED3N 是在**同一份** `core_train.jsonl`（157,311 對；149,489 train／7,822
val）上訓練的：20,000 對、1 epoch、187 秒，`loss=0.1399 acc=0.9997`，checkpoint
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

`DictionaryLayer.encode`
先把詞查到 CC-CEDICT／JMdict，再把**釋義字串**當成 key。於是輸入的 key 空間是「詞義」而不是「符號」，`12 + 7`
與 `178 + 101`
共享大部分key（都是數字＋算盤規則），運算子與順序消失。**輸入本身不可區分，任何訓練都不可能學到對應**。

### 2. 解碼把釋義的表面形式接起來 → 字詞湯

```
IN  : What gas do plants absorb from the air for photosynthesis?
GOLD: carbon dioxide
GEN : 在忙吗 兴奋 嗯 烦恼 明天见 心情 难过 欢迎 早上好 开心
```

即使是**訓練時看過的**那一句，`generate()` 也回不出目標（同一題 loss≈0.14、
`acc=0.9997`）。`StepDecoder`
在 key 空間上挑 activation 最高的幾個，再印出它們的 `zh`/`en`
表面形式；key 是釋義，輸出自然是無關的釋義片段。

### 3. 訓練目標不是「下一個 token」，所以教不會生成

`JointTrainer` 更新的是關聯/序列邊權（Hebbian
`add_directed`／`adjust_connection`）， `generate()` 讀的是 `forward_sequential`
的門檻 activation。關聯路徑與解碼路徑共用同一個 `CoreNetwork`
實例，但沒有可微的輸出層，也沒有 next-token 交叉熵；因此「關聯正確」不會變成「字串正確」。這是架構問題，不是 epoch 或 learning-rate 問題（1
epoch 與 5 epoch、500 與 20,000 對，生成都錯）。

### 4. `process()` 只是「相關」不是「正確」

```
process("What gas do plants absorb ...") -> "Its main functions are photosynthesis and gas exchange. ..."
process("Find the area of a square ... 5 cm") -> "4"
```

知識題回的是百科相鄰句（相關性），面積題回錯。`process()` 的知識分支是 SNN
bus 的文字生成；它與 `generate()` 共用同一個壞表徵。數學之所以好看，是因為
`process()` 先走**確定性計算器**（那是表現層，不是核心）。

## 三、這次修好的機械缺陷（與根因分開）

1. **CLI 訓練沒訓練生成路徑**：`python -m ai.ed3n train` 只建
   `TrainingBatch`，從未建 `SeqBatch`；`generate()`
   讀的 sequence 邊從沒被訓練。已改為同時訓練（`seq_batch_from_examples`），並加回歸測試（`tests/test_ed3n_cli_training.py`）。
2. **Alpaca 資料被丟掉**：`_load_train_examples` 只讀 `input`（alpaca 的 `input`
   幾乎都是空的），`instruction` 被忽略 → 「No valid examples」。已改成
   `instruction (+input)`，並支援 `question`/`prompt`/`response`/`jsonl`。
3. **訓練資料沒有整理、也沒有防洩漏**：新增
   `scripts/prepare_core_training_data.py`（正規化、去重、確定性切分、manifest雜湊、**benchmark 洩漏檢查**）。實跑：157,311 對（149,489/7,822），丟棄 26 筆與評測題重疊的樣本。
4. **ED3N 進入對照表**：`probe_core_control.py`
   多一欄 ED3N（讀 checkpoint、讀外部字典、**直接讀 decoder**，不經 reflex 模板）。

## 四、讓核心真的會答題（唯一誠實的路）

參考文獻（按用途）：

- **SNN 可訓練性**：Neftci, Mostafa & Zenke (2019), _Surrogate Gradient Learning
  in Spiking Neural
  Networks_（BPTT + 替代梯度，讓 SNN 能做 next-token 預測）；Shrestha & Orchard
  (2018), _SLAYER_（時序誤差反傳）。
- **序列解碼**：Bengio et al. (2015), _Scheduled
  Sampling_（本專案已有機制，缺的是可微目標）；Mikolov et al. (2010),
  RNNLM（next-token 交叉熵）。
- **表徵**：Sennrich et al. (2016), _BPE_；word2vec (Mikolov 2013)／sentence
  embeddings（本專案已有 MiniLM，可直接用）。
- **以對照組為老師**：Hinton et al. (2015), _Distilling the Knowledge in a
  Neural Network_（用 LLM 的分布教 SNN，而不是把 LLM 的答案當模板塞進去）。
- **規模／評估**：Kaplan et al. (2020) scaling laws；Hoffmann et al. (2022)
  Chinchilla；MMLU／GSM8K 作為外部及格線（本專案已採用）。

具體步驟（依序，每步都要能量）：

1. **換表徵**：`DictionaryLayer` 之外新增 token/BPE 詞表（`encode` → token
   ids），保留舊字典給知識層用；核心不再用釋義當 key。
2. **換輸出層**：`StepDecoder` 改成 embedding → SNN →
   logits（詞表大小），用**替代梯度**做 next-token 交叉熵；`generate()`
   用同一個輸出層。
3. **資料**：`core_train.jsonl` 已經是乾淨的 (input, output) 對；另需把
   `association_train.json`（100k 關係句）與 wiki 導言句做語言模型預訓練，讓解碼先學會「像話」，再學問答。
4. **蒸餾**：先讓 LLM 在**非評測**語料上產生答案分布，SNN 學分布（Hinton
   2015）；評測集（`native_bench_v1`／`paraphrase_v1`）永遠不進訓練。
5. **量**：`probe_core_control.py`
   固定四欄（表現層／GARDEN／ED3N／LLM），同一評分；核心分只有「核心產生且正確」才算。

在那之前，對外數字就是 **核心 0.00/10**；系統分 5.75 只是表現層。

## 五、架構替換：token-SNN 已實作並量測（2026-10-23）

上面第 1–2 步已落地：`apps/backend/src/ai/ed3n/token_snn.py`（字元詞表 →
LIF（surrogate gradient，Neftci 2019）→ 線性 next-token
head；答案 token 的交叉熵、teacher
forcing）＋`scripts/train_token_snn.py`（可讀 CSV/JSON/JSONL、可給獨立 held-out
split、存 checkpoint 與報告）。

**架構正常**（可學習性檢查）：複製任務（echo 5 個詞、60
epochs）**5/5 完全正確**，loss 0.005。所以它不是「連最佳化都不會」。

**實測（可重現）**：

| 任務                                | 訓練                                      | held-out                                   | 結果                                            |
| ----------------------------------- | ----------------------------------------- | ------------------------------------------ | ----------------------------------------------- |
| 複製（echo）                        | 5 詞 ×20                                  | 同 5 詞                                    | **5/5 exact**                                   |
| 算術（加減乘除）                    | 30,000（`arithmetic_train_dataset.json`） | 500/2,000（`arithmetic_test_dataset.csv`） | **0/500 exact**（20 epochs、154 秒、loss 1.75） |
| 核心凍結題（math 40／knowledge 15） | 20,000 對（`core_train.jsonl`）           | 同基準                                     | **0%**（loss 2.49，未收斂）                     |

teacher-forced 字元準確率在訓練列上 **38.5%**（3,000 列、40 epochs、
`d_hidden=128`；可重現），表示它學到了數字分布，但**沒有學到進位演算法**，自由生成 сразу 漂移，所以 exact 是 0。這與規模一致：1.5B 的 LLM 在 GSM8K 等級也只到 60%；這個核心只有
**~0.1M 參數**（`d_emb=96`、`d_hidden=192`、字元詞表 170），在 CPU 上不可能補上這個差距。

**量測修正（同日）**：對照表以前只印百分比，把「沒有輸出」和「答錯」混在一起。現在每個生產者都記
`answered`／`coverage`／`distinct`：

- **GARDEN：0/40 有回答**（`generate()`
  回空字串）——所以它的「0%」不是答錯，而是**沒有輸出**；不能拿來當能力證據。
- **TOK-SNN：40/40 有回答，但只有 2 個不同的答案**（40 題數學幾乎都是
  `The sor the and the …`）→ **模式崩潰（mode
  collapse）**，0% 反映的是解碼器塌掉，不是逐題嘗試失敗。
- **ED3N：40/40 有回答、22 個不同答案**，但都錯（`何为`、`六 〦 亅 兆电子伏…`）→ 有在產生內容，內容沒有條件性。
- LLM：40/40 有回答、38 個不同答案、60% 正確。

這讓「0%」的意義變清楚了：GARDEN 是缺席，TOK-SNN 是塌陷，ED3N 是亂答。三者都不是智能，但修法不同（缺席要接上解碼器、塌陷要訓練收斂、亂答要換表徵——後者已做）。

**結論（更新版）**：表徵與目標已經換對，缺口現在是**規模與訓練預算**，不再是「字典釋義／關聯訓練」的結構錯誤。要跨過外部及格線（math
61%、paraphrase 70%）需要：

1. 更大的模型（≥10⁸ 參數級）與 GPU 訓練（surrogate
   BPTT）；本機 CPU 以目前 ~0.1M 參數、5 分鐘級訓練只能到「學得會複製、學不會算術」。
2. 或**蒸餾**：用本地 LLM 在非評測語料上產生分布，SNN 學分布（Hinton
   2015）；仍需要 GPU 與數天級訓練。
3. 在達成之前，對外核心分維持
   **0.00/10**；TOK-SNN 與 GARDEN／ED3N 並列在對照表中，不因「有模型」而加分。

**不要做的事**（已寫進門禁與文件）：把模板／路由／查表塞進核心來「補分」；把評測題放進訓練；把
`neural` 這個字當成核心。

## 六、學習曲線：不是「再訓練久一點」的問題（2026-10-23）

`--eval-every` 讓 `train_token_snn.py` 在訓練途中量 held-out（同一條
`exact_match`），避免只看最後一點。算術（30,000 訓練／官方
`arithmetic_test.csv`，抽 200 題、greedy）：

| epoch | loss  | exact |
| ----- | ----- | ----- |
| 10    | 1.748 | 0/200 |
| 20    | 1.706 | 0/200 |
| 30    | 1.698 | 2/200 |
| 40    | 1.700 | 0/200 |

loss 在 1.70 附近**平台化**，exact 在 0–1% 之間震盪。多訓練 20
epochs 沒有改變結論（40 epochs、293 秒）。

**對照（診斷用，非專案程式）**：同樣的詞表與資料，換成同尺寸的 GRU（emb
96／hidden 192，~0.18M 參數，10 epochs、64 秒）→ loss 1.13、exact
**4/200（2%）**。所以：

- 這不是「SNN 特別壞」——同尺寸的 GRU 也只能到 2%；任務（含加減乘除與小數）在這個參數量級就是學不動。
- 但 LIF 版本的平台（1.70）比 GRU（1.13）高，表示**同樣預算下 SNN 更吃虧**；要拉平，需要多層／更大的隱藏層／更長的 BPTT（即更多算力），不是換個 learning
  rate。
- 兩者都離外部及格線（math 61%）很遠；這支持「缺口是規模」的結論，也說明
  **在 CPU 上把這個模型訓練到及格不是可達路徑**。

**再確認：不是「曝光偏差」（exposure bias）**。把 GRU 對照的兩種解碼分開量：

| GRU（0.18M、10 epochs）   | teacher-forced 每字元 | greedy 整題 |
| ------------------------- | --------------------- | ----------- |
| 測試 200 題               | 52.2%                 | 1.0%        |
| **訓練自己看過的 200 題** | 53.7%                 | **2.5%**    |

連**訓練題**用 greedy 都只有 2.5%（例：`178 + 101` →
`289`）。teacher-forced 每字元只有 ~53%，表示它根本沒學到進位規則；如果只是曝光偏差，訓練題的 teacher-forced 會接近 100%。所以 scheduled
sampling（Bengio
2015）不是這裡的解藥；解藥是把模型／訓練預算放大到能表徵演算法為止。

三條獨立證據（學習曲線平台、同尺寸 GRU 對照、訓練題 greedy
2.5%）都指向同一個結論：**這個量級的核心模型不可能靠 CPU 訓練跨過外部及格線**。誠實的選項只剩：

1. **給 GPU 預算**（≥10⁸ 參數、surrogate BPTT／蒸餾，天級訓練）；
2. **承認核心 0.00/10**，把 LLM 只當「能力上限參考」而不是本專案的核心；
3. **把本地 LLM 當部署核心**（它是神經模型，符合定義；但就不是「純本地自訓核心」的主張了，且需在報告中改寫口徑）。

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

第六節的結論「平台化不是 epoch 不夠」是對的，但「SNN 更吃虧」的**原因**可以修。這一輪只做架構與參數化的誠實調整——**不碰及格線、不碰評測題、不加規則**；β 修正是 bug（一律生效），膜電位讀取是量測贏家（選勝後設為預設），深度／時間步展開保留為旗標但預設關閉（量測說它們沒用），全部有測試守住，同預算 A/B 決定取捨。

### 改了什麼

1. **β 參數化缺陷修復（bug）**：`cfg.beta=0.9` 舊程式存進參數後又被 `sigmoid()`
   一次，實際漏電是
   **sigmoid(0.9)=0.711**——10 步後只剩 3% 狀態（而不是設定的 35%）。現在參數存 logit，有效值＝設定值（有測試守住）。
2. **膜電位讀取（SLAYER，Shrestha & Orchard 2018）**：`readout="membrane"`
   ——頭每步讀最後一層的膜電位而不是二值 spike；**遞歸仍然是 spiking 的**，只有讀取方式不同。`readout="spike"`
   保留原行為。
3. **深度**：`layers=N` 堆疊 LIF 層（層 0 吃 embedding，上層吃下層 spike）。
4. **輸入展開**：`timesteps=K`
   每個 token 過 K 個 SNN 時間步再讀取（SNN 序列模型的標準時間解析度旋鈕，代價 Kx）。
5. **診斷**：`tf_accuracy()`（teacher-forced 答案 token 準確率）寫進 report，區分「沒學會」與「解碼漂移」。

### 同預算 A/B（算術 30,000、batch 64、lr 5e-3、max_len 32、12 epochs、

held-out 抽 200 greedy）

| #   | 變體                                     | final loss | tf_acc    | held-out exact |
| --- | ---------------------------------------- | ---------- | --------- | -------------- |
| A   | 對照（舊行為：有效 β0.711、spike、1 層） | 1.718      | 35.8%     | 0/200          |
| B   | 只修 β（0.9、spike、1 層）               | 1.780      | 35.4%     | 0/200          |
| C   | β0.9 + **membrane**                      | **1.601**  | **39.7%** | 0/200          |
| D   | C + 2 層                                 | 1.633      | 38.6%     | 0/200          |

第二輪（全用 C 的預設 readout=membrane）：

| #   | 設定                                 | final loss                             | tf_acc | held-out exact |
| --- | ------------------------------------ | -------------------------------------- | ------ | -------------- |
| E   | β0.9、K=1、**30 epochs**（平台檢查） | 1.558（10/20/30ep：1.604/1.562/1.558） | 41.0%  | 0/200          |
| F   | β0.99（長記憶）                      | 1.697                                  | 37.3%  | 0/200          |
| G   | K=4（輸入展開）                      | 1.826                                  | 33.4%  | 0/200          |
| H   | K=4 + β0.99                          | 1.662（eval@6 曾 1/200）               | 38.9%  | 0/200          |

**讀法**：

- **membrane 讀取是唯一的真贏家**：同預算 loss 1.78 → 1.60、tf 35.4% → 39.7%（B
  vs C 隔離出讀取效果）。在**另一份資料**上複現：核心 20,000 對、5
  epochs 同預算重訓，loss **2.488 → 2.336**。
- **深度、長記憶、時間步展開全部變差**（D/F/G/H 各項都輸給 C）——在這個參數量級與 CPU 預算下，加複雜度只會更難訓練。這三項留在程式裡（`layers`／
  `timesteps` 旗標、`--beta`
  可調＋測試），但**預設不開**，因為量測說它們沒用；輸家配置要重現就顯式傳旗標（A 對照＝`--beta 0.711 --readout spike`）。
- 平台仍在：E 到 30 epochs 降到 1.558 後趨緩，仍**高於同尺寸 GRU 的 1.13**
  （第六節），exact 仍
  **0/200**。所以「膜電位修復」**縮小但沒有消除**與 GRU 的差距，更沒有跨過及格線——它不是新結論的依據，只是把「LIF 同預算更吃虧」的一半原因修掉了。

### 對照表重測（`probe_core_control.py`，2026-10-24，同題同評分）

預設 checkpoint（probe 的 tok 欄）用贏家配置同預算重訓後：

| 套件              | n   | 表現層 | GARDEN   | ED3N | TOK-SNN  | LLM（1.5B chat） |
| ----------------- | --- | ------ | -------- | ---- | -------- | ---------------- |
| math              | 40  | 32/40  | 0 有回答 | 0/40 | **0/40** | 27/40（68%）     |
| knowledge         | 15  | 7/13   | 0        | 0/15 | 0/15     | 11/15（73%）     |
| code              | 10  | 0      | 0        | 0/10 | 0/10     | 9/10（90%）      |
| routing（表現層） | 10  | 10/10  | 0        | 0/10 | 0/8      | 0/10             |

- **TOK-SNN 的模式崩潰修好了**：math 40 題從「只有 2 個不同答案」→
  **40 個全不同**（核心資料同預算重訓後），但仍
  **0 題答對**——「有變化」不等於「有智能」，分数不加。
- **LLM 對照組的測量缺陷修復**（instruct 模型改走 chat 模板，commit
  `db8cc6d28`）：code 從 0/10 → 9/10、math 60% →
  68%。這**只影響對照組的可信度**，不是本專案的分數；對照組高正好坐實「缺口是真的智能缺口」。
- **官方核心分不變：0.00/10**——probe 裡的四個核心生產者在生產路徑的佔比（`core_share`）仍然是 0，這些表是診斷，不是計分。

### 本輪之後仍然成立的結論

- 修參數化、換讀取方式都在 CPU 上可做且有效——但它們改善的是**收斂**，不是
  **能力**；exact 仍 0，平台仍在 1.56（vs GRU 1.13）。
- 這台機器有 **Intel Arc B570（Vulkan）**——但只接了 llama.cpp（對照組用
  `gpu_layers=-1` 真的在跑 GPU）；torch 仍是 **CPU
  build**，SNN 訓練沒有吃到這張卡。要吃 GPU 需要 torch XPU/Vulkan
  build（使用者決定的預算問題之一）。
- 三選一的決策面不變（GPU 規模訓練／承認 0.00／LLM 當部署核心）；這一輪只是把「架構本身有缺陷」這個變因**排除掉**，讓剩下的缺口乾淨地只剩規模。

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

## 八、輸入長度瓶頸 → token 詞表 → 蒸餾資料：第一次拿到非零分（2026-10-26／27）

第七節說「缺口只剩規模」——**不完全對**。同預算單變因診斷找出第三個結構瓶頸：
**輸入長度**（前六節所有實驗的輸入都是 ≤18 字元的短算術）。

### 1. 瓶頸是輸入長度，不是 epoch、不是 lr

蒸餾資料的題目平均 **74 字元**（舊算術題平均 18）。同一架構、同一協議、60
epochs：

| 子集 | 平均長度 | 擬合（300 題） | teacher-forced |
| ---- | -------- | -------------- | -------------- |
| 短題 | 18 字元  | 60/300         | 71%            |
| 長題 | 74 字元  | **0/300**      | 36%            |

lr ×2 也只到 10/300 → 不是最佳化不足。進一步量到**初始 loss 隨長度爆炸**
（18 字→19、74 字→174）：膜電位在長序列上累積、softmax 飽和。修法與量測：

1. **LayerNorm 掛在膜讀出路徑**（`token_snn.py`，可 A/B、spike 對照路徑不動）：初始 loss
   24 → **3.45**，飽和修復；但長題仍 2%——**步數才是根本瓶頸**。
2. **token 詞表**（文件既定處方第 1 步的另一半）：74 字元 → **~16
   token**，落回已證明可學的步數區間：

| 詞表      | 長題擬合（300）    | tf       | 短題            |
| --------- | ------------------ | -------- | --------------- |
| char      | 0–10/300           | 0.46     | 擬合            |
| **token** | **264/300（88%）** | **0.95** | loss→0、tf 100% |

這是本文件第一個「**同一協議下換一個表徵就從 0 變有**」的單變因結果。舊 char
checkpoint 與 LN 不相容，直接由 token 版取代（舊版本來就是 0% 模型）。

### 2. 路線②（使用者拍板 1+2 的 ②）：蒸餾資料

`scripts/distill_core_data.py`
用本地 Qwen2.5-1.5B（對照組模型）在**非評測**語料上產生訓練對，四源各有自己的驗證器（數學答案由 Python 求值、wordprob 雙重記帳、knowledge 接地原文）：**5,425 對**（math
3,478／knowledge 800／wordprob 598／alpaca 549），`_is_leak`
契約擋下 26 筆與評測重疊的資料，`--check` 實測 **0 洩漏**，7 條契約測試守住。

**訓練（Run A）**：token 詞表 3,577、`d_emb=96`／`d_hidden=512`、100
epochs、2,556 秒、CPU：

| 指標                              | 值        |
| --------------------------------- | --------- |
| train_exact（記憶檢查，不計能力） | 38%       |
| distill_val exact（150 題抽樣）   | 8%        |
| **淨 holdout（248 題）exact**     | **11.3%** |
| 淨 holdout teacher-forced         | 37.9%     |

**train/eval 污染清理（量測有效性）**：`distill_val` 與 `core_train` 逐字重複
**33/281**（alpaca 同源）。以「input 或 output 逐字出現在 core_train」為準濾出
`distill_val_holdout.jsonl`（248 題，`distill_val_holdout.meta.json`
記錄準則與 n_dropped），兩個 checkpoint 都在**同一份淨題**上重量，數字才可比。

### 3. 對照表重測（`probe_core_control.py`，2026-10-27）

`--token-checkpoint token_snn_distill.pt`，同題同評分（`core_control_distill.json`）：

| suite             | n   | 表現層 | GARDEN | ED3N | TOK-SNN        | LLM（1.5B chat） |
| ----------------- | --- | ------ | ------ | ---- | -------------- | ---------------- |
| math              | 40  | 80%    | 0%     | 0%   | **3/40（8%）** | 68%              |
| knowledge         | 15  | 47%    | 0%     | 0%   | 0/15           | 73%              |
| code              | 10  | 0%     | 0%     | 0%   | 0/10           | 90%              |
| routing（表現層） | 10  | 100%   | 0%     | 0%   | 0/10           | 0%               |

**這 3 題是真泛化，證據鏈**：

- `What is 15 % 4?` →
  `3`；`What is the force on a 5 kg mass with acceleration 2 m/s2?` →
  `10`；`What is the work when force = 10 and distance = 3?` → `30`。
- 40/40 有回答、**29 個不同答案**（不是模式崩潰），也不是重複同一個數字。
- 訓練資料**沒有這些句子**：蒸餾與 core 兩份資料的洩漏門禁都是 0（`--check`），學到的是運算技能（mod／F=ma／W=Fd），不是背題。
- 但
  **knowledge/code 仍是 0**，所以「第一次非零」≠「可用」；**官方核心分仍然0.00/10**（probe 是診斷，`core_share`
  在生產路徑仍是 0）。

### 4. GPU 線：根因＝wrapper 的 CSR 覆寫（2026-10-29 定位、10-30 更正）

重開機（GuC 70.72.1、sha `de81c75f…`）＋私有 runtime（libze 26.27／igc
2.40.14／OpenCL ICD
26.27）下，用「單變因分離」把故障面磨出來（每項測試前先 tiny-op 健康閘門，故障後等 60–120s 恢復再測，journal 計 delta
`CAT error`）：

**能跑的（全部重複驗證、零故障）**

- 純 GEMM／矩陣乘：連續 45 秒、21,909 步；H2D 拷貝 4,671 步；
- 記憶體：單張量分配到 **1 GB**（分配＋逐元素算＋釋放）無故障；
- 微算子全電池：embed／linear／SiLU／LayerNorm／CE fwd+bwd／Adam（各 50 次），
  **含 Run-B 精確形狀 `64×191×12005` 的 CE fwd+bwd ×5**；
- 真模型**前向**（d512、len 192、token 詞表）×5；
- **小模型訓練**（char 詞表、len 48）：60
  epochs／180 步、3-epoch 多輪全過——訓練路線本身不是先天不可用。

**一定掛的（多次複現）**

- **真模型訓練步驟**（d512×len 192，token 詞表 V≈10k）：batch
  64/32/16 全數在 0–50 步內死，`Engine memory CAT error [18] class=ccs` →
  `Timedout job` → UR
  `DEVICE_LOST`；`limit 500`（V=5037）同樣掛，所以不是詞表大小單一因素；
- 死亡點隨**單步成本**反向移動（batch
  64＝4s、16≈6 步、8≈10 步、4≈10–20 步），但故障時記憶體只有 **274 MB
  reserved**——不是容量、不是分配大小、不是動態形狀、不是步內佇列深度（forward 每 16 步強制 sync 仍掛）；
- 佔空比停頓無效（每步 `0.05s` sleep 照掛）、L0 v2 開關不是變數。

**已修的系統性掛死（代碼層，非硬體）**

- 原先「訓練 3 個 epoch 全部完成、loss 正常下降，卻在**收尾 eval**
  掛死、.pt 沒存」：同一配置 4/4 掛；改成**先存檔再 eval**＋`--eval-on-cpu` 後
  **3/3 通過、零故障**。eval 的自回歸 `generate`（每 token 一個 host
  sync）是放大器。
- 附帶健壯性：每 epoch 存檔、`--resume`（vocab 不一致拒載）、`--epoch-pause`。

**風暴後的設備狀態**：故障後進入劣化態（tiny
op 過、任何真工作立刻風暴），需 60–120s 沉澱；日誌風暴是**單秒重試刷屏**（曾在 1 秒内 2,820 條），不是持續崩潰。測試間若不等恢復，下一個進程會在 setup 階段就掛死（會誤判成「新問題」）。

**2026-10-30 更正：觸發器是 wrapper 的 CSR 覆寫，不是硬體對持續負載的先天限制**

上面「一定掛」各項都是在**舊 `xpu_run.sh` 環境**下測的——那時它 export 了
`NEOReadDebugKeys=1` +
`OverrideCsrAllocationSize=65536`。對 wrapper 的四組變數做二分（同一訓練協議各跑 3 次、故障後等設備恢復再測下一項）：

| 環境變數                        | 故障率                                 |
| ------------------------------- | -------------------------------------- |
| control（不加任何變數）         | **0/3**                                |
| `SYCL_UR_USE_LEVEL_ZERO_V2=0`   | 0/1（乾淨）                            |
| OpenCL ICD 路徑                 | 0/1（乾淨）                            |
| 私有 26.27 `LD_LIBRARY_PATH` 棧 | 0/1（乾淨）                            |
| **CSR 覆寫兩行成對**            | **2/3**（CAT 792、8 條，epoch 跑不完） |
| 完整 wrapper（舊版）            | **3/3**（CAT 173／1810／4057 條）      |

單獨一行各自測都過、**成對時**才觸發；統計上這是真變因，不是運氣。移除這兩行之後：同協議
**3/3 全過、CAT 0**；連續 soak（token 詞表、d512×L192、5000×3
epochs、無停頓、含收尾 CPU eval）**rc=0、kernel
fault 增量 0**，259s 跑完。`xpu_run.sh`
已改為不設定這兩行，並把上述量測寫進檔案註解。上面那批「一定掛」的形狀記錄（batch 越大死越快、eval 放大器、故障時僅 274MB
reserved）仍然描述了故障形態，但**歸因作廢**：不是 torch、不是 runtime 版本、也不是 xe 對持續異構負載的先天問題。

**資源佔用實測**（`gputop` +
`top`，真訓練逐秒採樣 40 秒，回答「使用率沒上去」）：計算引擎
**ccs 平均 46%（峰值 95%）**、拷貝引擎 **bcs 平均 42%（峰值 100%）**、GPU 記憶體
**2 GB**（進程 MEM 欄），整機 CPU 只有 **~9%
us**——工作確實在 GPU 上，主機端只負責餵數據與逐步 host
sync。桌面小工具多半只顯示合成/3D 引擎，看到「GPU 沒動」是**看錯了引擎**；先前那種「主機 RSS 上漲、GPU 引擎全 0%」的樣子才是佇列堵死的病態，修後已不復現。

結論（2026-10-30 更新）：**GPU 規模訓練恢復可用**。根因是 wrapper 的 CSR 覆寫變數在這張 B570 上觸發 xe
CAT／DEVICE_LOST（與其 capability 表回報 `requiredPreemptionSurfaceSize=0`
的已知家族一致），已移除並通過 3/3 重複驗證＋連續 soak。主線仍可選 CPU（Run
B 已實證 13 小時跑完），但
**Run-B 尺度（d512×len192×V10k）現在可以放上 GPU**；下一輪規模訓練在 GPU 上跑，並逐輪監控 CAT 增量與
`gputop` 的 ccs 佔用作為健康指標。

**真訓練在 XPU 上的實測確認（2026-10-30，AI+AL 第一輪，見第六節）**：不是合成 soak，而是 3,180 對真資料、d512×len192×V12005、30
epochs、無停頓、含收尾 CPU eval ——
**`rc=0`、`CAT_before=0 CAT_after=0 delta=0`**，訓練 396s／全 run
2,091s。這一輪把第四節的「可用」從**探針層**推到**真訓練層**。

### 5. Run B（已收官，2026-10-28）：只換資料量這一個變因

Run A 卡在 train_exact
38%（連 5k 都記不完）與平台化，下一個單變因是**資料量**：同容量（`d_emb 96`／`d_hidden 512`）改餵
`core_train.jsonl`（138,693 對可過 `max_len=192`）、5
epochs、每輪在淨 holdout（248 題）上量：

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=6 ./.venv/bin/python \
  scripts/train_token_snn.py --vocab token \
  --train apps/backend/data/processed/core_train.jsonl \
  --val apps/backend/data/processed/core_val.jsonl \
  --eval-data apps/backend/data/processed/distill_val_holdout.jsonl \
  --eval-sample 500 --eval-every 1 --epochs 5 --batch 64 --lr 3e-3 \
  --d-emb 96 --d-hidden 512 --max-len 192 --device cpu \
  --out apps/backend/data/models/token_snn_core149k.pt \
  --report data/intelligence_reports/token_snn_core149k.json
```

**Run B 結果（2026-10-28，46,930 秒＝13.0 小時 CPU）**：唯一變因＝資料量（5,425
→ 149,489 對，27×），容量、詞表、評分、評測題全不變：

| 指標                          | Run A（5.4k，100 ep，2,556s） | Run B（149k，5 ep，46,930s）                   |
| ----------------------------- | ----------------------------- | ---------------------------------------------- |
| train_exact（記憶，200 題）   | 38%                           | **47%**                                        |
| val exact                     | 8%（distill_val 150 題）      | 45%（core_val 200 題，**不同題組不可直接比**） |
| **淨 holdout（248 題）exact** | **11.3%**                     | **0.0%（5 輪全 0）**                           |
| 淨 holdout teacher-forced     | 37.9%                         | **13.9%**                                      |
| probe math（TOK-SNN）         | 3/40（8%）                    | **1/40（2.5%，只有 math-027）**                |
| knowledge／code／routing      | 0／0／0                       | 0／0／0                                        |

**結論（照實寫）：資料量不是瓶頸。** 27× 資料讓記憶變好（train
38→47%）, 但淨 holdout 從 11.3% 掉到 **0%**、tf 掉到 13.9%，probe math 3/40 →
1/40（`core_control_core149k.json`，與 `core_control_distill.json`
同題同評分）。混雜要承認：Run A 是 100 epochs × 5.4k，Run B 是 5 epochs ×
149k，所以 A/B 同時變了「資料量」與「每對更新次數」——但兩者指向同一個結論：**在固定 0.1M 容量、固定 CPU 預算下，加資料換不到升分，只換來更少的優化**（loss
2.77→2.05仍在下降、未收斂）。還沒被排除的變因只剩**容量＋算力**（≥10⁸ 參數需 GPU；GPU 線已在 2026-10-30 解除阻塞，見第四節，下一輪可直接上 GPU 規模）與**蒸餾目標**（學 teacher 分佈而非單一正解）。及格線、評測題、規則三者沒動；**官方核心分維持 0.00/10**。

---

## 六、AI+AL 第一輪：10 筆 → 3,180 筆、XPU 全程無故障，但 free-running exact 仍是 0（2026-10-30）

使用者循環的第一圈：**AI 側語料現成，AL 側才是要準備的**。第一輪把兩者接起來，並回答了幾個前五節懸著的問題。

### 1. 資料（兩支腳本，各有 `--check` 閘門）

```bash
./.venv/bin/python scripts/generate_al_dataset.py --rows 4000 --seed 7
./.venv/bin/python scripts/prepare_ai_al_training_data.py \
  --src apps/backend/data/processed/ai_al_round1_dataset.json
```

- 遷移用契約 §5 的**同一個算子**
  `v ← target + (v−target)·e^(−dt/τ)`，目標表從 10 筆 pilot
  **擬合**（不自編）；`routing_mode`
  沿用 pilot（10 筆全部遷移不變），所以生成器**不發明模式切換**。
- 分割 **3,180 train / 820
  val**，**benchmark 洩漏 0**（生成器與 prepare 各一道門，另有「可重現」「10 筆 pilot 必須被用上」「答案不得等於輸入」三道）。
- ⚠️ **一半資料進不去**：`max_len=192` 下只有 **1,528/3,180（48%）** train 列、
  **400/820（49%）**
  val 列放得下——狀態前綴＋回應＋狀態尾段太長，**進模型前就丟了**。這是下一輪第一個要修的（截斷／摘要狀態，或拉長
  `max_len` 並付算力）。
- 誠實範圍：遷移目標表是 10 筆 pilot 擬合的**占位**（不是 AL 動態），intent 標注是關鍵詞規則（占位，生產版應走
  `query_classifier`）；這些列教的是**對應關係** (狀態, 文字) →
  (回應, 狀態′)，不是 AL 狀態模型正確的證據。

### 2. 訓練（真資料、真 XPU）

```bash
scripts/xpu_run.sh env PYTHONPATH=apps/backend/src OMP_NUM_THREADS=4 \
  ./.venv/bin/python scripts/train_token_snn.py --vocab token \
  --train apps/backend/data/processed/ai_al_train.jsonl \
  --val apps/backend/data/processed/ai_al_val.jsonl \
  --epochs 30 --batch 32 --lr 3e-3 --d-emb 96 --d-hidden 512 \
  --max-len 192 --device xpu --eval-on-cpu \
  --out data/checkpoints/ai_al_round1.pt \
  --report data/intelligence_reports/ai_al_round1.json
```

| 指標                          | 值                                                 |
| ----------------------------- | -------------------------------------------------- |
| loss                          | 3.7085 → **0.4565**（30 epochs，持續下降、未收斂） |
| 時間                          | 訓練 396s／全 run 2,091s（含收尾 CPU eval）        |
| **GPU 穩定性**                | **`rc=0`、`CAT_before=0 CAT_after=0 delta=0`**     |
| train exact（記憶，200 題）   | **0/200**                                          |
| val exact（200 題）           | **0/200**                                          |
| 淨 holdout exact（100 題）    | **0/100**                                          |
| **淨 holdout teacher-forced** | **61.76%**（29,501 tokens，400 列全量）            |

淨 holdout 那兩行用不重訓的回填量測（同一 checkpoint、同一資料，只補跑評估）：

```bash
./.venv/bin/python scripts/train_token_snn.py --vocab token --epochs 0 --resume \
  --train apps/backend/data/processed/ai_al_train.jsonl \
  --val apps/backend/data/processed/ai_al_val.jsonl \
  --eval-data apps/backend/data/processed/ai_al_val.jsonl --eval-sample 100 \
  --device cpu --eval-on-cpu --out data/checkpoints/ai_al_round1.pt \
  --report data/intelligence_reports/ai_al_round1_eval.json
```

### 3. 這一輪回答了什麼（照實寫）

1. **GPU 線正式過關**：第四節原本只有探針層證據（soak、單變因二分），這一輪是
   **真資料 3,180 對 × 30 epochs ×
   d512×len192×V12005**，`rc=0`、CAT 增量 0。「GPU 規模訓練可用」現在是訓練層的結論，不是探針層的。
2. **`--eval-on-cpu` 的 150 秒逾時不是故障**（ISSUES §五.4）：全 run
   2,091s、eval 正常完成；先前的 rc=124 是**被 timeout 殺的**。
3. **AI+AL 資料不再是 10 筆**（ISSUES §五.5）：10 → 4,000 → 3,180/820，洩漏 0。
4. **瓶頸不在「記不記得」，在「生成」**：train
   exact 也是 0/200，而 teacher-forced 已有
   **61.76%**——給定前綴時它知道下一個 token，自回歸展開時逐步漂移。這與§5（Run
   A/B）同一個病，**加資料、加 epoch 都不改這個性質**；能改的是目標（teacher 分佈／scheduled
   sampling）與容量。
5. **資料格式本身是變因**：48% 的列被 `max_len`
   擋在門外，而輸出＝回應＋狀態遷移，長度直接決定 exact 的難度（每一 token 都要對）。
6. **及格線、評測題、規則沒動**：`generate_al_dataset` 與 `prepare`
   都有 benchmark 洩漏門（實測 0），所以這一輪的分數不是自己教自己的分數。**官方核心分維持 0.00/10**。

### 4. 對照表重測（`probe_core_control.py`，2026-10-30，同題同評分）

只換
`--token-checkpoint data/checkpoints/ai_al_round1.pt`，其餘（題目、評分、表現層／GARDEN／ED3N／LLM 四個對照欄）不變：

| suite     | n   | 表現層 | GARDEN | ED3N | **TOK-SNN（ai_al_round1）** | LLM（Qwen2.5-1.5B） |
| --------- | --- | ------ | ------ | ---- | --------------------------- | ------------------- |
| math      | 40  | 80%    | 0%     | 0%   | **0%**                      | 68%                 |
| knowledge | 15  | 53%    | 0%     | 0%   | **0%**                      | 73%                 |
| code      | 10  | 0%     | 0%     | 0%   | **0%**                      | 90%                 |
| routing   | 10  | 100%   | 0%     | 0%   | 0%                          | 0%                  |

報告：`data/intelligence_reports/core_control_ai_al_round1.json`（本機，`/data/*`
不入倉，數字以本表為準）。

**照實寫**：

- **TOK-SNN 歷次：distill 3/40 → core149k 1/40 → ai_al_round1
  0/40**，三個 checkpoint 都沒能穩定通過核心凍結題——與 §5／§6 的結論一致（**容量＋目標**才是變因，資料量、資料格式、GPU 都已排除或解決）。AI+AL 第一輪練的是
  `(狀態, 文字) → (回應, 狀態′)`
  的對應，**本來就不是核心問答**，所以 0% 不意外，但它也**不能被拿來說核心分上升了**。
- 對照欄與 2026-10-23 的記錄有小幅差異（knowledge 表現層 47%→53%、LLM
  67%→73%），是 **15 題小樣本的一題之差**；code LLM 90% 與 `MEASUREMENT_MAP.md`
  註記的「0/10 → 9/10（chat 模板修復）」一致。
