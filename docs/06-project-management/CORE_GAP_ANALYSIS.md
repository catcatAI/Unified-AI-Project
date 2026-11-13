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

在那之前，對外數字就是 **核心 0.00/10**；系統分 6.41 只是表現層。

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
  **2026-11-05 更正**：上面描述的是**當時的 venv**。現在 venv 是
  `torch 2.14.1+xpu`、`torch.xpu.is_available()=True`（Arc B570），
  `resolve_device()` 選 `xpu`，`scripts/train_token_snn.py` 實跑 `device=xpu`
  成功。GARDEN 的 `TensorSNNCore`
  例外地**預設 CPU**：它的稀疏每樣本 Hebbian 更新在 XPU 上實測慢约 7x（forward 則快約 10x），顯式
  `device="xpu"` 才走加速器（AGENTS §X #281）。
- 三選一的決策面不變（GPU 規模訓練／承認 0.00／LLM 當部署核心）；這一輪只是把「架構本身有缺陷」這個變因**排除掉**，讓剩下的缺口乾淨地只剩規模。

重跑（A/B 全套，約 10 分鐘）：

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=6 ./.venv/bin/python \
  scripts/train_token_snn.py \
  --train apps/backend/data/raw_datasets/arithmetic_train_dataset.json \
  --val "" --eval-data apps/backend/data/raw_datasets/arithmetic_test_dataset.csv \
  --epochs 12 --batch 64 --lr 5e-3 --max-len 32 --eval-every 6 --eval-sample 200 \
  --beta 0.9 --readout membrane --layers 1 --timesteps 1 \
  --out data/checkpoints/tok_winner.pt \
  --report data/intelligence_reports/tok_winner.json
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

**真訓練在 XPU 上的實測確認（2026-10-30，AI+AL 第一輪，見第九節）**：不是合成 soak，而是 3,180 對真資料、d512×len192×V12005、30
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

## 九、AI+AL 第一輪：10 筆 → 3,180 筆、XPU 全程無故障，但 free-running exact 仍是 0（2026-10-30）

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

---

## 十、AI+AL 第二輪：第一輪的四個變因一次修掉，答案段確實動了、凍結對照表仍是 0（2026-10-30）

第一輪（§九）留下四個**已定位**的問題。第二輪一次修掉它們，其餘（資料、容量、及格線、評測題、規則）**全不變**：

| 第一輪的問題                                              | 第二輪的處置                                      | 實測效果                                            |
| --------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------- |
| `max_len=192` 擋掉 52% 列                                 | `--max-len 384`                                   | train **1,528 → 3,003**（48% → 94%）；val 400 → 767 |
| 聚合 tf 把答案與狀態塊混在一起（61.76% 被低熵狀態塊墊高） | `split_tf_accuracy()` 拆 `response_tf`／`tail_tf` | 分離指標成為正式輸出，可跨輪比較                    |
| loss 被長狀態塊主導                                       | `--tail-weight 0.25`（答案段 4×，weighted mean）  | 答案段的梯度不再被狀態塊淹沒                        |
| 30 epochs／約 1,440 步                                    | 100 epochs／約 9,300 步                           | 步數不再是藉口                                      |

### 1. 訓練（同協議、同資料、同容量，只動上表四項）

```bash
scripts/xpu_run.sh env PYTHONPATH=apps/backend/src OMP_NUM_THREADS=4 \
  ./.venv/bin/python scripts/train_token_snn.py --vocab token \
  --train apps/backend/data/processed/ai_al_train.jsonl \
  --val apps/backend/data/processed/ai_al_val.jsonl \
  --epochs 100 --batch 32 --lr 3e-3 --d-emb 96 --d-hidden 512 \
  --max-len 384 --tail-weight 0.25 --device xpu --eval-on-cpu \
  --out data/checkpoints/ai_al_round2.pt \
  --report data/intelligence_reports/ai_al_round2.json
```

| 指標                  | 第一輪（30 ep、len192、無加權）   | **第二輪（100 ep、len384、tail 0.25）**            |
| --------------------- | --------------------------------- | -------------------------------------------------- |
| loss                  | 3.7085 → 0.4565（持續下降未收斂） | 5.1933 → **0.9108（ep60 觸底）** → 1.0093（ep100） |
| 進得去的列            | 1,528/3,180（48%）                | **3,003/3,180（94%）**                             |
| 訓練／全 run          | 396s／2,091s                      | 4,839s／**7,642s**                                 |
| **GPU 穩定性**        | `rc=0`、CAT delta 0               | **`rc=0`、CAT delta 0（100 epochs）**              |
| train exact（200 題） | 0/200                             | **0/200**                                          |
| val exact（200 題）   | 0/200                             | **0/200**                                          |

報告：`data/intelligence_reports/ai_al_round2.json`（本機）。

### 2. 分離指標：狀態塊飽和、答案段微升、記憶讓位給泛化

第一輪記的 `14–26%`
是在**不同列集合**上量的，而且當時還沒有分離指標。為了能跨輪比較，把兩個 checkpoint 用**同一支程式、同一個列集合**重測（teacher-forced，無自由生成）：

| 列集合（同碼同列）            | R1 `resp_tf` | **R2 `resp_tf`** | R1 `tail_tf` | **R2 `tail_tf`** |
| ----------------------------- | ------------ | ---------------- | ------------ | ---------------- |
| val 進得去 ≤192（400 列）     | 19.51%       | **22.71%**       | 78.35%       | 78.30%           |
| val 進得去 ≤384（767 列）     | 14.73%       | **23.47%**       | 78.23%       | 78.11%           |
| train 前 600 列（≤192，記憶） | **90.16%**   | 72.33%           | 81.52%       | 78.35%           |

三件事照實寫：

1. **狀態塊（AL 側）飽和在 78%**：四種條件（兩模型 × 兩列集合）全部落在 78±0.4%，連第一輪都已經到頂。`<al_out>`
   是低熵的固定結構——**一學就會，也馬上到天花板**；它既不區分模型也不區分資料，所以第一輪那個 61.76% 的聚合數字**主要是在量它**。
2. **答案段（AI 側）在同列上只動 3.2 個百分點**（19.51% →
   22.71%），同時 train 端從
   **90.16% 掉到 72.33%**——R2 用「少記一點」換來「多泛化一點」，這是 `max_len`
   放開讓序列長度翻倍的直接後果（同容量、進得去的列數也翻倍）。方向對，但
   **22.7% 的逐 token 命中率離 exact 還差整個量級**：exact 要求**每一發 token 都對**，不是每五發對一發。
3. **loss 在 ep60 觸底後回升**（0.9108 →
   1.0093）：train 與 val 的差距拉開，這不是「還沒練夠」，是**這個容量配這個目標在 3,000 對上到頂了**。再加 epoch 只會更過擬合。

### 3. 對照表重測（`probe_core_control.py`，2026-10-30，同題同評分）

只換 `--token-checkpoint data/checkpoints/ai_al_round2.pt`，其餘四個對照欄不變：

| suite     | n   | 表現層 | GARDEN | ED3N | **TOK-SNN（ai_al_round2）** | LLM（Qwen2.5-1.5B） |
| --------- | --- | ------ | ------ | ---- | --------------------------- | ------------------- |
| math      | 40  | 80%    | 0%     | 0%   | **0%**                      | 68%                 |
| knowledge | 15  | 53%    | 0%     | 0%   | **0%**                      | 73%                 |
| code      | 10  | 0%     | 0%     | 0%   | **0%**                      | 90%                 |
| routing   | 10  | 100%   | 0%     | 0%   | 0%                          | 0%                  |

**照實寫：0/75，與第一輪（0/40）同為 0。**

生成樣本把「**格式學會了、綁定沒學會**」寫得很直白：

```
Q: What is 3 + 5 * 2?
tok: The number π is 37.
     <al_out> v=0.07 a=0.38 d=0.33 fatigue=0.33 stress=0.30 health=...
```

`<al_out>` 狀態塊**欄位、順序、數值範圍全對**（tail_tf
78% 的實體），答案句是字詞湯（response_tf
23.5% 的實體）——**同一個模型，兩種能力差 3.3 倍**。

同時排除一個假說：probe 問的是**裸問題**，而訓練資料一律 `<al_in>…|question`
前綴，一度懷疑是前綴分佈不匹配把分數打成 0。在第一輪 checkpoint 上直接對照量測，**裸問題與加前綴生成都是字詞湯**——前綴不是主因，模型本來就還沒學會問題→答案的綁定。

### 4. 第二輪回答了什麼

1. **資料格式不是瓶頸**（§九 第 5 點的假說被否證）：列數 48% →
   94%、loss 更低、同列答案段 19.51% →
   22.71%，凍結對照表仍 0——把格式修掉**不改變結論**。
2. **GPU 再拿一次乾淨紀錄**：真資料 3,180 對 × 100 epochs ×
   d512×len384×V12005，`rc=0`、CAT 增量 0。§四 的「GPU 規模訓練可用」在更大配置上仍成立。
3. **瓶頸回到 §5（架構替換）／§6（學習曲線）／§7（架構升級輪）早就寫下的那一條：容量＋目標。**
   資料量（Run
   B：27× 資料無效）、資料格式（本節：94% 列無效）、GPU（§四：已解決）——**三個候選都已單變因排除**，剩下的是模型容量與訓練目標（teacher 分佈／scheduled
   sampling）本身，不是再餵一批資料能解的。
4. **分離指標必須留在正式輸出**：聚合 tf 跨輪不可比（被狀態塊墊高），以後一律看
   `response_tf`。
5. **及格線、評測題、規則沒動**，洩漏門未被觸碰，**官方核心分維持 0.00/10**。

## 十一、AI+AL 第三輪：容量＋目標單變因——teacher-forced 答案段再升、free-running 與凍結對照表仍是 0（2026-10-31）

§十 第 4 點把三個候選（資料量、資料格式、GPU）排除後，只剩**容量＋目標**。第三輪就是這一格的單變因實驗：只動下表兩項，其餘含資料全不變：

| 變因     | 第二輪            | **第三輪**                                           |
| -------- | ----------------- | ---------------------------------------------------- |
| 容量     | `d_hidden 512`    | **1024**                                             |
| 訓練目標 | 純 teacher-forced | **`--ss-final 0.5`**（scheduled sampling 線性 ramp） |

不變項：`ai_al_train/val.jsonl` 同一批 3,180 對、epochs 100、lr 3e-3、batch
32、d-emb 96、max_len 384、tail-weight 0.25、評測題、及格線。Ramp 直接打 §十 的
`response_tf` 23% 對 free-running exact
0 的**曝光偏差**：早期 epoch 從 gold 語境學映射，後期在模型自己的語境上練（p 從 0 線性升到 0.5）。

### 1. 訓練（含一次驅動層故障與加固重啟）

```bash
scripts/xpu_run.sh env PYTHONPATH=apps/backend/src OMP_NUM_THREADS=4 \
  ./.venv/bin/python scripts/ai_al_round_loop.py --round 3 -- \
  ./.venv/bin/python scripts/train_token_snn.py --vocab token \
  --train apps/backend/data/processed/ai_al_train.jsonl \
  --val apps/backend/data/processed/ai_al_val.jsonl \
  --epochs 100 --batch 32 --lr 3e-3 --d-emb 96 --d-hidden 1024 \
  --max-len 384 --tail-weight 0.25 --ss-final 0.5 --device xpu \
  --eval-on-cpu --out data/checkpoints/ai_al_round3.pt \
  --report data/intelligence_reports/ai_al_round3.json
```

兩次嘗試，照實寫：

- **attempt1（02:09 開跑）死在驅動層**：epoch 19（loss 1.6480）後停滯， `dmesg`
  對上時間戳的是
  `xe ... Engine reset: engine_class=bcs`（02:34，全 boot 單次事件）——非 OOM、非 pipe 塞死。證據保留
  `data/intelligence_reports/ai_al_round3_loop.attempt1-killed.log`。評估過
  `--resume` 但**不用**：它只還原權重，Adam 狀態重建、ramp 從頭數 100（總 119
  epochs＋ramp 重啟），會污染單變因——寧可損失 20 分鐘重跑。
- **attempt2（02:57 重啟）**：改用 `setsid` 讓訓練成為獨立 session（驗證
  `SID=PID`、`PPID=1`）——runner 再重啟也帶不走它；全程**零新增 Engine
  reset**，`rc=0` 收官（07:09）。

| 指標            | 第二輪                               | **第三輪**                                                   |
| --------------- | ------------------------------------ | ------------------------------------------------------------ |
| loss            | 5.1933 → 0.9108（ep60 觸底）→ 1.0093 | 5.6157 → **1.5832（ep25 谷）** → 3.1115（ep99）              |
| 訓練／全 run    | 4,839s／7,642s                       | 7,264s／**15,124s**                                          |
| GPU 穩定性      | `rc=0`、CAT delta 0                  | **`rc=0`、attempt1 一次 bcs reset（見上）、attempt2 零事件** |
| train exact 200 | 0/200                                | **0/200**                                                    |
| val exact 200   | 0/200                                | **0/200**                                                    |

Loss 曲線後段回升**跨輪不可比**：R3 的 loss 定義在 SS 混合語境上（p 越大任務越難），ep50 後的爬升是 ramp 讓模型在自產語境上重練的直接效應，不是「練壞了」。

### 2. 分離指標：答案段繼續升、記憶腰斬、狀態段首次鬆動

同支程式（`split_tf_accuracy`）、同列集合重測；重測先在 R1/R2 上逐位重現了 §十.2 的已發布值（19.51／22.71／90.16…）才讀 R3，跨輪比較有效：

| 列集合（同碼同列）            | R1 `resp_tf` | R2 `resp_tf` | **R3 `resp_tf`** | R1→R3 tail（R3）        |
| ----------------------------- | ------------ | ------------ | ---------------- | ----------------------- |
| val 進得去 ≤192（400 列）     | 19.51%       | 22.71%       | **24.52%**       | 78.35 → 76.42（76.42%） |
| val 進得去 ≤384（767 列）     | 14.73%       | 23.47%       | **25.86%**       | 78.23 → 76.31（76.31%） |
| train 前 600 列（≤192，記憶） | 90.16%       | 72.33%       | **48.61%**       | 81.52 → 76.39（76.39%） |

三件事照實寫：

1. **答案段（AI 側）在同列上再動 1.8～2.4 個百分點**（23.47 →
   25.86），兩個 val 列集合方向一致——SS 更換訓練目標在 teacher-forced 答案段**確實持續起作用**（R1→R3 累計 +5～+11pp）。但 25.86% 離 exact 仍是同一個量級的差：**exact 要每發全中，26% 的逐 token 命中率抽不出整串全對**——即使 free-running 與 teacher 分佈完全對齊也做不到。
2. **記憶端大幅讓位**（train600 90.16 → 72.33 →
   **48.61%**）：SS 把近半訓練訊號移到自產語境，gold-context 的訓練列擬合直線下降；val 升 train 降，泛化/記憶缺口收窄，但代價是記憶腰斬。
3. **狀態段 78% 首次鬆動**（四種條件七個測點全在 78±0.4
   → 全部跌到 76.3-76.4）：d1024+SS 讓狀態塊終於開始**區分模型**，不再完全飽和。但它與答案段仍差 2.9 倍（76%
   vs 26%），聚合數字照樣主要在量它。

### 3. 對照表重測（`probe_core_control.py`，2026-10-31，同題同評分）

只換 `--token-checkpoint data/checkpoints/ai_al_round3.pt`，其餘四欄不變：

| suite     | n   | 表現層 | GARDEN | ED3N | **TOK-SNN（ai_al_round3）** | LLM（Qwen2.5-1.5B） |
| --------- | --- | ------ | ------ | ---- | --------------------------- | ------------------- |
| math      | 40  | 80%    | 0%     | 0%   | **0%**                      | 68%                 |
| knowledge | 15  | 53%    | 0%     | 0%   | **0%**                      | 73%                 |
| code      | 10  | 0%     | 0%     | 0%   | **0%**                      | 90%                 |
| routing   | 10  | 100%   | 0%     | 0%   | 0%                          | 0%                  |

**照實寫：0/75——R1 0/40、R2 0/75、R3 0/75，三輪同一個 0。** 生成樣本（`math-001`
`What is 3 + 5 * 2?`）與第二輪同構：

```
Q: What is 3 + 5 * 2?
tok: The 1verage 5]
     <al_out> v=0.21 a=0.4 d=0.37 fatigue=0.33 stress=0.37 health=0.86
```

`<al_out>` 狀態塊仍是欄位、順序、數值範圍全對（tail
76% 的實體），答案句仍是字詞湯（response
26% 的實體）——**格式與綁定的 2.9 倍差距跨三輪未變**。

### 4. MVE 判讀（湧現界線的門檻：compositional holdout exact ≥5/200、亂配對照 ≤1/200）

- **儀器已建（§十二）**：compositional
  holdout 題組與亂配對照組原不存在——本輪（第三輪）無法做完整判讀；儀器與首讀數見 §十二，門檻已註冊進
  `MEASUREMENT_MAP.md` §六。
- **現有最接近的代理指標全部不達標**：val free-running exact **0/200 <
  5/200**（與 R1/R2 持平）；凍結對照表 **0/75**（同上）。
- **結論照實寫**：容量＋目標這一格**只動了 teacher-forced 分佈**（§十.2 的三個列集合全部印證），free-running 與對照表一個數字都沒動。曝光偏差被 ramp 緩解了 2.4pp，但當前主要矛盾不是它——**答案段 teacher-forced 本身只有 26%**，每發四中一，先跨過這個才輪得到 exact。

### 5. 循環（第二半）第一次完整實跑

`scripts/ai_al_round_loop.py` 第三輪全程
`train_rc=0 → generate_rc=0 → prepare_rc=0 → check_rc=0`：`--skip 4000`
取 core_train **沒用過的新切片** （不是重複同一批問題），寫進獨立的
`ai_al_round4_{dataset,train,val,manifest}` 四個檔案（sha256 記錄在
`data/intelligence_reports/ai_al_round3_loop.json`），`--check`
roundtrip 通過。**第四輪批次就緒但不自動啟動**——下輪換什麼變因仍是人的決定（且狀態行 schema≠生產快照 v2 的開放項排在第四輪，見 ISSUES
§十.6）。

### 6. 這一輪回答了什麼

1. **「容量＋目標是瓶頸」只對了一半**：它在 teacher-forced 答案段持續有效（23.47
   →
   25.86，兩個 val 列集合一致），但**沒有兌現成任何一個 free-running 數字**（exact
   0/200、對照表 0/75 三輪持平）。
2. **資料側三重確認不再是變因**：資料量 27×（Run
   B）、資料格式（§十94% 列）、本輪資料原封不動——三種走法同一個 0。
3. **下一個要動的不是訓練輪**：resp_tf
   26% 意味著就算零曝光偏差也抽不出 exact；在動第四輪的變因之前，要先建**能測的湧現界線儀器**（compositional
   holdout＋亂配對照），否則下一個 0 與這三個無法區分。**（已建：§十二。）**
4. **循環閉環可用**：訓練→自動產下一批資料→校驗→manifest 一條龍通過，數據始終取自專案語料（`core_train.jsonl`
   新切片），不脫離專案所需。
5. **及格線、評測題、規則照舊沒動**，洩漏門未觸碰，**官方核心分維持0.00/10**。

## 十二、湧現界線儀器（MVE-1）：設計裁決與首讀（2026-10-31）

§十一.6.3 說「在動第四輪的變因之前，先建能測的湧現界線儀器」——本節就是它。門檻與讀法註冊在
`MEASUREMENT_MAP.md` §六；此處記**為什麼這樣設計**
與首讀數。儀器：`scripts/probe_emergence_boundary.py`（14 契約測試
`tests/test_probe_emergence_boundary.py`），題組
`apps/backend/data/processed/mve1_emergence_boundary.json`（`--check`
逐位重建），報告 `data/intelligence_reports/mve1_emergence_boundary.json`。

### 1. 現有 exact 在結構上就測不到湧現

- **`dt` 不在輸入行**：`ai_al_train.jsonl`、`ai_al_round4_train.jsonl` 對 `dt=`
  均為 **0 命中**，輸入行只有
  `v a d fatigue stress health mode intent`。而合約 §5 是
  `S(t+1) = F(S(t), events, dt)`——dt 有 4 種可能（0.25/0.5/1.0/2.0），**同一輸入有 4 個合法輸出**，單一 gold 的 exact 永遠是 0，與模型好壞無關。
- **exact 還要求逐字重現語料回應**（resp_tf
  25.86%）——即使 dt 看得見，這個 0 也會把狀態側的任何進步蓋掉。

所以三輪的 0/200 分不出「沒有湧現」與「儀器不可能響」。MVE-1 兩處解開：

### 2. 四個設計裁決

| 裁決                                        | 出處與理由                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **family-exact**：gold ＝ 4 個 dt rung 任一 | dt 不在輸入（見上）；rung 分佈另計為診斷；單一 gold 的升級路徑＝dt 進輸入，那是**資料 schema 變因**，留給下一輪決定。**2026-10-31 續**：round-4 schema 已把 dt 放進輸入（`--expose-dt`，預設關），gold 改單一 rung、family 降為 `wrong_rung` 診斷，見 §十二.5                                                             |
| **回應給進 prompt**，只生成 `<al_out>` 塊   | 合約 §5 的 F 不消費回應文本；`token_snn._encode` 顯示訓練時狀態塊本來就以 gold 回應為條件（teacher-forcing），所以「prompt 到 response 為止」是訓練分布的同一個續寫任務，不是新格式；逐字回應重現是另一個 0（resp 26%），不綁進核心門檻                                                                                   |
| **組合軸＝(intent × mode)，裁切在生成端**   | dt 看不見 → (intent×dt) holdout 在舊格式上不可良好定義（模型無法知道自己「不該」見過哪些格）；(intent×mode) 每個 primitive 都還在訓練裡（每 intent 留 2 個 mode、每 mode 留其他 intent），過關＝把 intent-target 分支與 mode-carry 分支**組合到未見配對**；裁切用 `--holdout-cells`（預設關閉，`--check` 逐位一致已驗證） |
| **對照＝同集合內輪轉（derangement）**       | 隨機亂配可能有 fixed point（期望 ~1 個真命中）吃掉 ≤1/200 的門檻；輪轉保證零 fixed point，且同一份生成物重評分，不重跑模型                                                                                                                                                                                                |

題組細節：5 個 cell 各 40 列（`unknown:conservative`、`knowledge_query:neutral`、
`math_query:exploratory`、`humor:conservative`、`greeting:neutral`；**farewell刻意不在**——全語料 16 列填不滿 cell）；reference
120 列取三個語料充足 intent 的非 holdout mode；每列狀態新抽、與訓練列零重疊；192
token 視窗判準用 `tokenize == vocab.encode`
的原子計數在建置期精確檢查（不需 checkpoint）。

### 3. 首讀（round-3 checkpoint，baseline）

`--set all`（200 holdout ＋ 120 reference）、XPU、563.4s、2026-10-31：

| 量                                            | 值                                                                           |
| --------------------------------------------- | ---------------------------------------------------------------------------- |
| **gate：holdout family-exact**（v1.0.0 判準） | **0/200**（≥5 才過；v1.1.0 起改 single-gold，見 §十二.5）                    |
| **gate：rotation 對照**                       | **0/200**（≤1 才過）→ 對照乾淨                                               |
| reference（seen cell）                        | 0/120                                                                        |
| format_ok（6 欄位＋mode＋intent）             | 106/320（33%）                                                               |
| `<al_out>` 出現                               | 248/320（77.5%）                                                             |
| 欄位值命中（任一 rung，/320）                 | v 10、a 4、d 14、fatigue 17、stress 17、health 8                             |
| rung 分佈                                     | 全 none（320/320）                                                           |
| carved / text_overlap                         | **False**（rounds 1-3 訓練含全部 cell）／**0**（與 4 份 train/val 檔零重疊） |

照實寫三點：

1. **門檻現在是可測的，首讀 0 是真 0 的一部分**：對照 0 → 不是格式假象；format
   33% → 結構在動（與 tail
   76% 一致）；但逐字 2dp 狀態列一個都沒寫出來（欄位命中 ~3-5% 是數字層亂槍）。樣本可見模型大多已輸出完整
   `<al_out>`
   骨架，值不對、且部分列會先多補一句回應再進狀態塊（暴露偏差的殘跡）。
2. **carved=False**：rounds 1-3 訓練含全部 cell，所以 0/200 是 **seen-cell
   baseline**，不是組合泛化成績。組合意義在某輪用
   `generate_al_dataset.py --holdout-cells` 裁切後才啟用。
3. **與 §十一 的 0 不矛盾，且更細**：同一個 0 現在分層成「格式 33%／marker
   77.5%／欄位 ~5%／全串 0」＋乾淨對照——下一個 0 或第一個 ≥5 都能被讀成確定的東西，這正是 §十一.4 要的「可區分」。

### 4. 留給人的決定（儀器不自動做）

1. **dt 進輸入嗎**（資料 schema 變因）：**已進儀器**（`generate_al_dataset.py --expose-dt`，預設關；`ai_al_round_loop.py --next-expose-dt`
   讓下一批沿用同一 schema）。做了，單一 gold
   exact 才可能，(intent×dt) 組合軸才可良好定義；不做，family 是唯一可判讀的門檻。**第四輪是否採用仍是人的決定**——儀器提供能力，不替人選變因。
2. **第四輪裁切 cell 嗎**（資料變因）：做了，holdout
   0/200 才變成分組明確的組合泛化讀數；不做，門檻測的只是 seen-cell 重現（首讀即此狀態）。
3. **儀器區段 [10000, 50000) 已標記**：後續輪次 `--skip` 若走進該區，probe會在
   `instrument_text_overlap` 報出（首讀 0）；要加硬門可在循環裡加反向洩漏檢查。

### 5. 2026-10-31 續：round-4 schema 進儀器（v1.1.0）

`--expose-dt`
把 dt 放進輸入行（`<al_in> ... intent=x dt=1.00 | text`），gold 從「4 個 rung 任一」收成「對應 rung 一個」，family 逐列保留為
`wrong_rung` 診斷。三個設計限制照實記：

- **預設關**：不帶 `--expose-dt` 的 build 仍逐位等於 rounds
  1-3 的 schema（`--check` 已驗），既有資料／報告不會被悄悄換掉。
- **rung 由位置決定**（`slot % 4`），不是新抽一顆 rng：加 dt 不動隨機流，每個 cell 的 rung 分佈仍平衡。
- **gate 鍵名不變**（`exact` 仍叫
  `exact`，報告 schema 可比），但判準嚴格了一層：舊 family 命中在新判準下是
  `wrong_rung`，不算過。

題組已用新 schema 重建並 `--check` 通過（200 holdout ＋ 120
reference）。**新 baseline 已於 2026-11-01 用 round-4 checkpoint 重跑**（v1.1.0
single-gold 首讀：holdout 0/200、rotation
0/200，見 §十三.3）——舊的 0/200 是 v1.0.0 family 判準的讀數，兩者不可直接比。

## 十三、AI+AL 第四輪：MVE schema 單變因——single-gold 首讀 0/200，瓶頸定位到格式層（2026-11-01）

§十二.4 留給人的兩個決定（dt 進輸入、裁切 cell）**都做了**——第四輪的單一變因就是這個
**MVE schema 包**，本輪是它的驗收輪：

| 變因        | 第三輪                                             | **第四輪**                                                                                                                                                                                                              |
| ----------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 輸入 schema | `v a d fatigue stress health mode intent`（無 dt） | **＋`dt=`**（`generate_al_dataset.py --expose-dt`）                                                                                                                                                                     |
| 組合軸裁切  | 無（seen-cell baseline）                           | **裁 5 個 `(intent × mode)` cell**（`--holdout-cells`：`unknown:conservative`、`knowledge_query:neutral`、`math_query:exploratory`、`humor:conservative`、`greeting:neutral`；farewell 仍刻意不在——全語料 16 列填不滿） |

不變項：同起點重生成（`--skip 4000`、seed 7、`id_prefix r4_`）、epochs 100、lr
3e-3、batch 32、d-emb 96、d-hidden 1024、max_len 384、tail-weight
0.25、`--ss-final 0.5`、XPU＋`--eval-on-cpu`、評測題、及格線。

### 1. 資料（雙 `--check` 全過）

`ai_al_round4_{dataset,train,val,manifest}` 重生成：**3,952 列**（train
3,095／val 857），dt 在輸入行 **3,952/3,952**、輸出側 **0 洩漏**、5 個 carved
cell 在 dataset 與 train/val 全 **0 列**（本輪復驗同數）；儀器題組 v1.1.0 重建
`--check`
逐位一致（`apps/backend/data/processed/mve1_emergence_boundary.json`）。dataset
provenance 記錄
`skip=4000`、`holdout_cells`、`holdout_carved`、`expose_dt=true`。

### 2. 訓練（一次 XPU 故障、一次重開機中斷，attempt2 收官）

兩次中斷照實寫：

- **attempt1 死於遊戲佔卡**：使用者遊戲（Arc B570）佔用期間 XPU
  `UR_RESULT_ERROR_DEVICE_LOST`——不動遊戲、不擅自切 CPU；證據歸檔
  `data/intelligence_reports/ai_al_round4_loop.attempt1-xpu-lost.log`。另機器 15:37 重開機把自動重啟 watcher 一併殺掉（log 只剩啟動行），改手動重啟。
- **attempt2（16:57:50 起，`setsid`
  獨立 session）**：全程零事件，21:53:42 收官，`train_rc=0`。

| 指標            | 第三輪                                     | **第四輪**                                                                 |
| --------------- | ------------------------------------------ | -------------------------------------------------------------------------- |
| loss            | 5.6157 → 1.5832（ep25 谷）→ 3.1115（ep99） | 5.6830 → **1.5970（ep26 谷）** → 3.1249（ep99）                            |
| 訓練／全 run    | 7,264s／15,124s                            | **5,935s／17,748s**（eval ~2.5h 在 CPU；pre-eval save 防 B570 評估期掛掉） |
| GPU 穩定性      | `rc=0`、attempt1 一次 bcs Engine reset     | `rc=0`、attempt1 XPU DEVICE_LOST（遊戲佔卡，見上）                         |
| train exact 200 | 0/200                                      | **0/200**                                                                  |
| val exact 200   | 0/200                                      | **0/200**                                                                  |

Loss 曲線形狀與主輪幾乎重疊（同超參、同 SS
ramp）——跨輪差異不在訓練動力學。teacher-forced 分離指標：`response_tf`
23.72%、`tail_tf` 76.02%——**列集合已變**（新切片＋carve，val_fit 790 vs
R3 的 767），R3 §十一.2 的「同列重測」面板不可延用，此處只作方向參考。

### 3. 讀數：MVE-1 single-gold 首讀（v1.1.0 判準）

`--probe --checkpoint data/checkpoints/ai_al_round4.pt`、`--set all`（200
holdout ＋ 120 reference）、XPU、558.5s、2026-11-01：

| 量                                     | 值                                                                                                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **gate：holdout exact（single gold）** | **0/200**（≥5 才過）                                                                                                        |
| **gate：rotation 對照**                | **0/200**（≤1 才過）→ 對照乾淨                                                                                              |
| reference（seen cell）                 | 0/120                                                                                                                       |
| **dt 條件化**                          | `exact_rung 0`／`wrong_rung 0`／**`no_match 320`**                                                                          |
| format_ok（6 欄位＋mode＋intent）      | 31/320（R3 v1.0.0 為 106/320）                                                                                              |
| `<al_out>` 出現                        | 192/320（R3 為 248/320）                                                                                                    |
| 欄位值命中（single-gold，/320）        | a 13、d 3、fatigue 6（v／stress／health 0）                                                                                 |
| rung 分佈                              | 每 rung 80 列平衡；hits 全 0                                                                                                |
| carved / text_overlap                  | `training_cell_rows` 只剩 round-1 遺留檔（751／233 列）——**round-4/5 檔 0 列＝carve 生效**；重疊 **0**（6 份 train/val 檔） |

判準版本與題組 prompt 都已換（v1.0.0 family → v1.1.0
single-gold、輸入加 dt），數字只作方向參考，不與 §十二.3 直接比。照實寫兩點：

1. **0 是真 0，但分層位置變了**：`no_match 320`＝模型連一個合法狀態塊都沒寫出來——還沒走到「拿到 dt 卻忽略」（`wrong_rung`）那格可判讀的位置；按 §十二 讀法表，現在在**任務/格式缺口**格，不在組合缺口格。dt 進輸入把門檻變得可測了，但格式層先擋在前面。
2. **格式層比 R3 還退**：format_ok 106→31、marker
   248→192（跨版本僅方向性）——carve＋新切片改了訓練分佈，格式穩定性沒跟上；這是本輪單變因的**副作用**，下輪動變因前要先解釋它。

### 4. 循環：四個 rc 全 0，round-5 批次就緒（已於 2026-11-01 23:34 啟動，見 §十四）

`ai_al_round_loop.py` round
4：`generate_rc=0 → prepare_rc=0 → check_rc=0 → train_rc=0`（loop record
`data/intelligence_reports/ai_al_round4_loop.json`，總 17,751.9s）。下一批**同 schema**（carve＋`--expose-dt`）已產出**未啟動**：`ai_al_round5_dataset.json`、`--skip 50000`（core_train
`<50000` 才有稀有 intent 的已知取捨）、rows 5,200、seed
7、四個 sha256 記錄在 loop record——launch 仍是人的決定（2026-11-01
23:34 已啟動，見 §十四）。狀態行 schema≠生產快照 v2（ISSUES
§五.6）**未動**：本輪單變因是 MVE
schema，快照接線照舊排後、與 AL 側工作對齊後一起切。

### 5. 這一輪回答了什麼

1. **dt 進輸入＋裁 cell 沒有立刻打開湧現門**：single-gold
   0/200、對照 0/200、reference
   0/120——門檻現在可測且對照乾淨，這是一個確定的 0。
2. **瓶頸明確移到格式層**：`no_match 320`＋format
   31/320——先讓模型穩定寫出合法狀態塊，才輪得到「dt 有沒有被用」的判讀；組合泛化讀數要等格式層跨過去才有效。
3. **凍結對照表（`probe_core_control`）本輪未重測**：判讀儀器換成 MVE-1
   single-gold（§十二.5）；及格線、評測題、規則照舊沒動，**官方核心分維持 0.00/10**。
4. **循環繼續一條龍**：訓練→自動產下一批（同 schema、新切片、sha 記錄）→校驗通過，數據始終取自專案語料（`core_train.jsonl`），不脫離專案所需。

## 十四、第五輪（2026-11-01 23:34 → 11-02 01:43；probe 11-02 10:44）：同 schema 換切片複驗——0 複現，格式指標微改善

### 1. 變因不變，只換切片

MVE schema 包原樣（carve 5
cell＋`--expose-dt`、超參照抄第四輪），唯一變的是新切片：`--skip 50000`、rows
5,200、seed 7、id_prefix `r5_`（provenance 實測）。四個 sha256 與
`ai_al_round4_loop.json` 記錄逐一複核吻合（dataset `fe920a96…`／train
`653fd3ea…`／val `d76089b8…`／manifest
`92faa639…`）；generate/prepare/check 已在第四輪循環內 rc=0，本輪只跑 train（23:34:11 起，log
`ai_al_round5_train.log`）。

### 2. 訓練讀數（`data/intelligence_reports/ai_al_round5.json`）

同一 train argv（epochs 100／batch 32／lr 3e-3／d-emb 96／d-hidden 1024／max-len
384／tail-weight 0.25／ss-final 0.5／xpu／eval-on-cpu）。**seconds
7,771.4**（train_seconds 4,365.7）、pairs train 3,310／fit 3,008／val_fit
750、loss 4.359 → **min 0.914 @ep31** → 1.678
@ep100（同第四輪先降後升的過擬合型）、`train_exact_200=0.0`／`val_exact_200=0.0`、eval_tf_split
**response 0.2766**／**tail 0.7871**（12,742／39,630
tok）——雙雙高於第四輪（0.2372／0.7602）。輪詢中斷一夜，進程 01:43:24 自行完成（report／log／checkpoint 三檔同一時間戳，無 crash 痕跡），11-02 晨確認收官。

### 3. MVE-1 v1.1.0 讀數（probe 10:33–10:44，XPU 596.3s，`--set all`）

R4 canonical 已歸檔
`mve1_emergence_boundary_round4.json`；R5 寫入 canonical。**同一份 frozen
320 列儀器、同判準 → 與 R4 可直接比**：

| 指標（v1.1.0，320 列）               | R4                                 | R5                                                         |
| ------------------------------------ | ---------------------------------- | ---------------------------------------------------------- |
| gate holdout / rotation              | 0/200 / 0/200                      | **0/200 / 0/200**（pass=False，≥5/≤1）                     |
| reference                            | 0/120                              | **0/120**                                                  |
| `dt_conditioning`                    | exact 0／wrong 0／**no_match 320** | exact 0／wrong 0／**no_match 320**                         |
| format_ok                            | 31/320                             | **58/320**                                                 |
| marker_ok                            | 192/320                            | 118/320                                                    |
| field_hits（總）                     | 22（a13／d3／fatigue6）            | **31，六欄全有**（v3／a4／d3／fatigue7／stress8／health6） |
| hits_by_rung                         | 全 0                               | 全 0                                                       |
| `text_overlap`／`training_cell_rows` | 0／round-1 遺留 751+233            | 0／round-1 遺留 751+233（carve 在效）                      |
| elapsed                              | 558.5s                             | 596.3s                                                     |

### 4. 循環：round-6 批次已補產（`--generate-only`）

第五輪 train 未走 loop 腳本（手動直跑：train 讀數在
`ai_al_round5_train.log`／`ai_al_round5.json`，故 `ai_al_round5_loop.json` 的
`train_rc=null` 只涵蓋批次補產）。補產用
`ai_al_round_loop.py --round 5 --generate-only`：skip
**55200**（接續 round-5 的 [50000, 55200)，不重疊）、rows 5,200、seed
7、`r6_`、同 carve＋`--next-expose-dt`，check ok **3,408 train／792
val**，四 sha 錄 manifest（dataset `9e6490fc…`／train `90da6ee8…`／val
`deb98afe…`／manifest
`e4b0c51a…`）。launch 仍是人的決定；§五.6 狀態行 schema≠生產快照**仍未動**。

> 此批次已於 2026-11-02
> 11:51 開跑並收官（2,003.6s）。**那份切片 100% 是裸算式、標註全成了
> `unknown`**，訓練與 probe 讀數都是退化的——見 §十五。

### 5. 這一輪回答了什麼

1. **0 是複現的，不是切片巧合**：全新不相交切片下 gate 三項全 0（0/200＋0/200＋0/120）、對照仍乾淨——第四輪的讀數在同 schema 下穩定重現。
2. **瓶頸仍在格式層**：`no_match 320` 續航，`wrong_rung`
   依然一格都讀不到；format_ok 31→58、field_hits 六欄全出現（22→31）但 marker
   192→118、hits_by_rung 全 0——格式行為在變動、離 gate
   ≥5 還遠，「先過格式關」的判斷不變。
   > **R6 之後修正**：這條只對 R5 成立。R6 的 format_ok
   > 316/320 是輸出塌成常數的產物，不是格式學習； `format_ok` 必須與
   > `output_diversity` 一起讀（見 §十五.4）。
3. **訓練側同型改善**：response/tail
   TF 雙升（0.2766／0.7871）而 exact 仍 0——teacher-forced 分佈改善照舊不轉化為 free-running 精確輸出（第三輪以來同型）。
4. **單純換切片已不再提供新資訊**：兩輪 0 之後，下一發要動格式層本身（prompt／格式訓練占比／輸出後處理）或換變因；round-6 批次就緒，**launch 仍是人的決定**（§10.4）。

## 十五、第六輪（2026-11-02 11:51 → 12:28；probe 12:31–12:40）：同一發第三次複驗——格式指標跳到 316/320，實際輸出卻塌成 23 種塊

### 1. 變因不變，第三次複驗（訓練走手動直跑）

train argv 逐字照抄第四／五輪 loop
record（`--vocab token --epochs 100 --batch 32 --lr 3e-3 --d-emb 96 --d-hidden 1024 --max-len 384 --tail-weight 0.25 --ss-final 0.5 --device xpu --eval-on-cpu`），只換 checkpoint／report 路徑；切片為 round-6 批次
`[55200, 60400)`（skip 55200、rows 5,200、seed
7、`r6_`、同 carve＋`--expose-dt`）。

### 2. 訓練讀數（`data/intelligence_reports/ai_al_round6.json`）

**seconds 2,003.6**（train_seconds 1,806.1，是第五輪 7,771 的四分之一）、pairs
train 3,408／fit 3,408／val 792、loss 2.264 → **min 0.747 @ep90** →
0.772（無回彈）、`train/val_exact_200=0`、eval_tf_split **response
0.4311**（4,419 tok）／**tail 0.7883**（41,812 tok）、**vocab_size 68**。

有兩件事在訓練階段就已經很可疑，只是當時當成「切片剛好簡單」：

- **vocab
  68**（第四輪 12,005、第五輪 7,568）——語料字元集縮到只剩數字與運算符，這是切片退化的第一個免費警報；
- **訓練時間砍到四分之一**——同時 loss 曲線漂亮得不像是同一個任務。

### 3. MVE-1 v1.1.0 讀數（probe 12:31–12:40，XPU 545.1s，`--set all`）

R5 canonical 先歸檔為
`mve1_emergence_boundary_round5.json`，R6 寫入 canonical。同一份 frozen
320 列儀器、同判準：

| 指標（v1.1.0，320 列）               | R4            | R5            | R6                                                 |
| ------------------------------------ | ------------- | ------------- | -------------------------------------------------- |
| gate holdout / rotation              | 0/200 / 0/200 | 0/200 / 0/200 | **0/200 / 0/200**                                  |
| reference                            | 0/120         | 0/120         | **0/120**                                          |
| `dt_conditioning`                    | 0／0／320     | 0／0／320     | **exact 0／wrong 0／no_match 320**                 |
| format_ok                            | 31            | 58            | **316**                                            |
| marker_ok                            | 192           | 118           | **314**                                            |
| field_hits（總）                     | 22            | 31            | **142**（v16 a18 d12 fatigue39 stress23 health34） |
| hits_by_rung                         | 全 0          | 全 0          | 全 0                                               |
| `text_overlap`／`training_cell_rows` | 0／751+233    | 0／751+233    | 0／8 檔／751+233                                   |
| elapsed                              | 558.5s        | 596.3s        | 545.1s                                             |

單看這張表，R6 像是**格式層的大躍進**：format_ok 31 → 58 →
**316/320**、marker 到 314、field_hits
142。這是我在 §十四.5 判「瓶頸在格式層」之後最想看到的形狀——所以更要看實際生成。

### 4. 實測：format_ok 316 是「塌成極少數塊」的另一面，不是格式學會了

逐列看生成物（`samples`
與人工抽看 13 列，涵蓋不同 cell、不同 rung、不同輸入狀態）：

```
614
<al_out> v=0.11 a=0.42 d=0.42 fatigue=0.34 stress=0.39 health=0.86 mode=exploratory intent=unknown
```

儀器新增 `output_diversity`
後（同 checkpoint 重跑一次，數字與原 R6 逐項相同：gate 0/200＋0/200、format_ok
316、marker 314、elapsed 521.7s）量到的是：

| 層級                   | distinct | modal_share | modal                                                                                       |
| ---------------------- | -------- | ----------- | ------------------------------------------------------------------------------------------- |
| 整段生成               | 180      | 8.4%        | `61\n<al_out> v=0.12 a=0.42 …`                                                              |
| **狀態塊本身（body）** | **23**   | **29.1%**   | `v=0.12 a=0.42 d=0.42 fatigue=0.34 stress=0.39 health=0.86 mode=exploratory intent=unknown` |

也就是說：**320 列輸入只產生 23 種狀態塊**，其中一個佔 29%（93 列）。整段看起來「有 180 種」幾乎全是前面那串數字在變——`distinct`
不拆 body 會高估多樣性一倍以上。

- **值貼著 baseline 不動**：輸入狀態從 `v=-0.97` 到
  `v=0.90`、dt 從 0.25 到 4.0、cell 從 greeting 到 humor，輸出都在
  `v≈0.10–0.12`、`a 0.42–0.49`、`d=0.42`、`fatigue=0.34`、`stress=0.39`、`health=0.86`，`mode`／`intent`
  恆為 `exploratory`／`unknown`。這組數字貼近 pilot 的 baseline 目標
  `{0.14, 0.47, 0.46, 0.355, 0.30, 0.867}`，而 gold 的實際跨度是
  `d 0.06–0.77`、`stress 0.08–0.54`、`health 0.56–0.86`。模型學到的是**邊際平均狀態**，不是「state＋dt
  → target」的鬆弛。
- **每條生成都多吐一個數字前綴**（`614\n`、`619\n`、`696\n`、`916\n`、`993\n`），然後才接
  `<al_out>`。前綴來自這份切片 100% 是算式問答（gold 是 `162174`
  這種裸數字），回覆段的分布整個被數字佔滿。
- 因此 exact 結構上必 0：`grade()`
  要求整段文字逐字等於某個 rung 的 gold，而生成物既多了前綴、值也不對應任何 rung。

**壞鐘驗證**：142 個 `field_hits`
不是「差一點就對」。若模型輸出一個固定塊，某欄位的命中數就等於「該列 4 個 rung
gold 裡剛好出現這個常數」的列數——用 modal 塊的數值回算：

| 欄位     | v    | a    | d    | fatigue | stress | health |
| -------- | ---- | ---- | ---- | ------- | ------ | ------ |
| 常數     | 0.12 | 0.42 | 0.42 | 0.34    | 0.39   | 0.86   |
| 回算命中 | 11   | 19   | 12   | 39      | 21     | 34     |
| 實測命中 | 16   | 18   | 12   | 39      | 23     | 34     |

六欄回算 136／實測 142——**這些「命中」幾乎全部是壞鐘也會準兩次**，不含任何 conditioning 資訊（其餘 6 個來自另外 22 種塊的少數變體）。

**自我修正**：§十四.5 第 2 點「格式行為在變動」只對 R5 成立。R6 的 316/320 不是格式學習的證據，而是
**輸出塌縮到 23 種塊**。`format_ok` 高與 `body_distinct`
低必須一起讀——這條讀法已寫進 `MEASUREMENT_MAP`
§六，並補進儀器報告（`output_diversity.distinct／modal_share／modal／body_distinct／body_modal_share／body_modal`）。

### 5. 資料層根因：這份切片 100% 是裸算式，`_intent_of` 不認得

`round6_train` 的 `(intent, mode)`
只有兩格：`('exploratory','unknown') 1,718`、`('neutral','unknown') 1,690`——**3,408 列全部 intent=unknown**。原因不是 carve，是標註：

- 語料 `[55200, 60400)` 全是 `211 + 561` 這種裸算式；
- `_intent_of()` 只認動詞關鍵詞（`calculate` 在 `_INTENT_KEYWORDS['math_query']`
  裡，但裸算式沒有動詞）→ 一律 unknown；
- carve 掉的正是 `unknown:conservative` → conservative mode 直接歸零；
- `gen.transition()` 對 unknown 沒有 per-intent target，一律落 baseline
  → 模型的最佳解就是輸出 baseline。

語料 intent 帶地圖（`core_train` 149,489 列，實測）：

| 區段              | intent 分佈                                                   | 用途                                                        |
| ----------------- | ------------------------------------------------------------- | ----------------------------------------------------------- |
| `[0, 50000)`      | 多樣（每 5,000 列 greeting 15–26、humor 14–28、math 140–170） | r1 `[0,4000)`、r4 `[4000,7952)`、probe 儀器 `[10000,50000)` |
| `[7952, 10000)`   | **未用**：unknown 1620／kq 356／math 55／humor 10／greeting 7 | 目前唯一還答得出 gate 的未用切片                            |
| `[50000, 55000)`  | unknown 4,678／kq 261／math 55／humor 4／greeting 2           | r5                                                          |
| `[55200, 60400)`  | **100% 裸算式**                                               | r6（本輪）                                                  |
| `[60400, 65600)`  | unknown／math／knowledge 混合，**無 greeting/humor**          | r7（已產，見 §十五.6）                                      |
| `[80000, 149489)` | 全 unknown                                                    | 不可用                                                      |

### 6. 三個修正（本輪一起落地）

1. **`_intent_of()` 認得裸算式**（`scripts/generate_al_dataset.py`）：新增
   `_ARITH_EXPR` 正則，命中即 `math_query`（關鍵詞優先，故 `what is 2+2?` 仍是
   `knowledge_query`）。這一條同時修正了 r5/r6/r7 三份批次把 math 當 unknown 的標註錯誤。
2. **carve 覆蓋審計**（同檔
   `_carve_coverage()`）：把「批次還剩哪些 cell、丟了哪些 intent／mode、是否 ok」寫進 dataset
   provenance；`ai_al_round_loop.py` 生成後讀回、寫進
   `next_batch.carve_coverage`，不 ok 時印 WARNING 並改寫
   `next_step`（不再讓退化批次頂著「ready」字樣）。以修正後的生成器重跑 round-6 切片：`ok=False`，只剩
   `math_query:conservative 1000`＋`math_query:neutral 2092`，缺 greeting／humor／knowledge_query／unknown 與 exploratory——**這就是當初訓練前看不到的那張圖**。
3. **`output_diversity`**（`scripts/probe_emergence_boundary.py`）：報告新增 distinct／modal_share／modal，讓「塌成常數」在讀數層就看得見，不必等人工抽看。

round-7 批次已用修正後的生成器重產（skip 60400、rows 5,200、seed
7）：math_query 正確出現，但
`ok=False`、缺 greeting／humor——**這塊語料帶本來就沒有這兩個 intent**，不是標註問題。

### 7. 這一輪回答了什麼

1. **R6 的 gate 0 不是新的資訊**：它是資料退化的必然結果（100% unknown →
   baseline 目標），不能拿來當「第三次複現」的證據。2. **`format_ok`
   是會被塌縮騙的指標**：31 → 58 →
   316 的曲線看起來像格式學習，實際是 320 列只輸出 23 種塊、`field_hits`
   142 個裡 136 個能用一個固定塊回算出來。之後讀 gate 必須同時看
   `output_diversity`（`body_distinct`／`body_modal_share`，本次補進儀器）。
2. **切片前進已走到語料邊界**：`[0,10000)` 用完、`[10000,50000)`
   被儀器保留、`≥50000` 幾乎只剩unknown／math／knowledge。`[7952,10000)`
   是唯一還能回答 gate 的未用切片（2,000 列 → carve 後 1,509，greeting 5／humor
   8，很薄）。
3. **下一步仍是人的決定**（§10.4）：要嘛用 `[7952,10000)`
   這塊薄切片，要嘛擴充語料，要嘛改儀器（例如把 compositional 變因從
   `intent×mode` 換成
   `intent×dt`，只留 intent 多樣性）。在資料層修好之前，再跑幾輪都會讀到同一個 0。

## 十六、第七輪（2026-11-02 17:0x → 17:2x）：修好標註後塌縮解除，但狀態塊仍不是輸入的函數

### 1. 變因：只換資料標註，argv 不動

批次為 §十五.5 修好 `_intent_of()` 之後重產的 round-7（skip 60400、rows
5,200、seed 7、`r7_`、同 carve ＋
`--expose-dt`）：3,286 列、**3 個 intent**（math 1,832／kq 615／unknown
839）、6 個 cell。train argv 與第六輪逐字相同（含
`--tail-weight 0.25`），只換檔案與 checkpoint 路徑，因此與 R6 可直接比。

為什麼是這一批：`[60000,70000)` 修好標註後是 math 6,169 ＋ kq 1,889 ＋ unknown
1,942，是「多 intent 且量夠」的唯一現成切片。代價是 0 greeting／humor →
`carve_coverage.ok=false`（缺這兩個 intent），**gate 結構上不可能通過**；這一輪的用途是診斷，不是通關。

### 2. 訓練讀數（`ai_al_round7.json`）

seconds **1,573.8**（train 1,377.2）、pairs 2,633／2,633／653、vocab_size
**80**（R6 是 68）、loss 2.685 → **0.633**，而且
**min 落在最後一個 epoch（99）**、沒有回彈——還在下降，100
epochs 對這批資料不夠。`train/val_exact_200=0`、eval_tf_split **response
0.3915**（2,991 tok）／**tail 0.7872**（35,362
tok）——尾段 teacher-forced 與 R6 的 0.7883 幾乎一樣。

### 3. probe 讀數（XPU 494.0s，`--set all`）

| 指標                            | R6            | R7                                 |
| ------------------------------- | ------------- | ---------------------------------- |
| gate holdout / rotation         | 0/200 / 0/200 | **0/200 / 0/200**（仍 pass=False） |
| reference                       | 0/120         | 0/120                              |
| format_ok / marker_ok           | 316 / 314     | **320 / 320**                      |
| field_hits（總）                | 142           | 155                                |
| `body_distinct`（320 列）       | **23**        | **128**                            |
| `body_modal_share`              | 29.1%         | **7.5%**                           |
| `input_output_correlation`      | 未量          | **六欄全部 \|r\| ≤ 0.083**         |
| `copy_accuracy`（mode／intent） | 未量          | **29.7%／26.9%**                   |
| `dt_conditioning`               | 0／0／320     | 0／0／320                          |

### 4. 讀數的意思：塌縮解除，但依賴是 ragged 的

- **128 種 body（原 23）**：標註修正確實解除了「一律回 baseline」的塌縮。
- **格式 320/320**：每個欄位都吐得出來，連 marker 都對。
- **但 correlation 全部 ≈ 0**：生成值與輸入狀態之間沒有單調關係。
- **copy 指標更狠**：`mode`／`intent`
  依契約本來就是照抄輸入（`mode_out = mode_in`、`intent_out = intent_in`），抄中率 29.7%／26.9%；mode 三選一隨機是 33%、intent 五選一 20%——**抄中率不比亂猜好多少**。R7 對 greeting 的列還會吐
  `intent=math_query`。
- **擾動測試（24 列，只改一個欄位再生成）**：改 `v` 有 12/24 列輸出塊改變、改
  `dt` 有 14/24。所以模型**有**在讀
  `<al_in>`，只是依賴不穩定、方向不對——準確說法是「ragged 依賴」，不是「完全無視」。

### 5. 訓練端的疑點：被測量的東西被壓到 1/4 權重

`train_token_snn.py --tail-weight` 的 help 自己寫著：`<al_out>`
狀態塊的 loss 權重，「lower it to spend the gradient on the response」，而
**R4–R7 全部用 0.25**。一份樣本裡狀態塊約 34%
tokens、response 約 66%，0.25 權重下狀態塊只佔有效梯度約
**9.9%**（`0.34×0.25 / (0.66 + 0.34×0.25)`）。

MVE-1 量的正是狀態塊——也就是**唯一被降權的對象**；`resp_tf 0.39` 對
`tail_tf 0.79`
的落差正好對應這個權重差。這不是新 bug，是**既有實驗設定與目標不一致**：前四輪為了讓 response 學起來調的參數，正好壓低了要驗的那個轉移。

### 6. 下一步（已啟動）

R8：同一批資料、同一 argparse，唯一改動
`--tail-weight 1.0`（狀態塊梯度佔比 34%）。若 correlation／copy 仍 ≈
0，就不是權重問題，下一個變因才是容量與表徵（例如把數字回歸改成 copy-with-scale 解碼）。

### 7. 本輪新增的三個儀器欄位

`output_diversity.body_*`（只看 `<al_out>` 之後的塊）、
`input_output_correlation`（輸入↔生成逐欄 Pearson，常數輸出記 `null`）、
`copy_accuracy`（照抄欄位的抄中率）。三者要一起讀：`format_ok` 滿分 +
`body_distinct` 低 = 塌縮；`body_distinct` 高但 correlation／copy ≈ 0
= 格式對而映射沒學到（R7）。

## 十七、第八輪（2026-11-03 00:5x → 01:2x；probe 01:3x–01:5x）：tail-weight 不是主因，先把「這題能不能學」量出來

§十六 留下的疑點是：R4–R7 全部用
`--tail-weight 0.25`，而 MVE-1 量的正是被降權的狀態塊（有效梯度約 9.9%）。§十六.6 於是排定 R8 為**單一變因**：資料、切片、argparse 全部與 R7 逐字相同，只把
`--tail-weight 0.25` 改成
`1.0`。本節記三件事——權重換到了什麼、位置是不是瓶頸、以及「0/200 到底是不是儀器的問題」。

### 1. 換掉權重買到多樣性、賣掉表面正確性，映射仍然沒動

`data/intelligence_reports/ai_al_round8.json`（train 1,329s，`vocab 80`，pairs
2,633/2,633/653）：

| 讀數                                     | R7（tail 0.25）                           | R8（tail 1.0）                     |
| ---------------------------------------- | ----------------------------------------- | ---------------------------------- |
| train loss                               | 2.685 → 0.633（min 在 epoch 99）          | 2.262 → **0.571**（min 0.563 @95） |
| `resp_tf` / `tail_tf`                    | 0.3915（2,991 tok）/ 0.7872（35,362 tok） | 0.3858 / 0.7943（同分割）          |
| `body_distinct`                          | 128                                       | **241**                            |
| `body_modal_share`                       | 7.5%                                      | **4.1%**                           |
| `field_hits`（單一固定塊可解釋的欄位數） | 155                                       | **98**                             |
| `input_output_correlation` 最大 \|r\|    | 0.083                                     | 0.137（`d`）                       |
| `copy_accuracy` mode / intent            | 29.7% / 26.9%                             | 37.2% / 25.0%                      |
| `format_ok` / `marker_ok`                | **320 / 320**                             | **223 / 203**                      |
| `input_sensitivity` 改 `v` / 改 `dt`     | 12/24 · 14/24                             | 8/24 · 18/24                       |

loss 更低、min 落到 epoch 95（100
epochs 這次夠了）、塊更分散、單一固定塊能解釋的欄位從 155 掉到 98——權重確實把梯度花了在狀態塊上。但**surface 正確性被賣掉了**：97 列連一個合法塊都吐不出來，最常見的破法是吞掉
`a=` 欄位或整個 `<al_out>`：

```
> v=-0.15 d=0.58 fatigue=0.41 stress=0.24 health=0.85 mode=neutral intent=math_query
```

而映射本身沒有變好：correlation 仍 ≤ 0.14，`copy_accuracy` mode
37.2% 對照隨機水位 33%（三選一）、intent
25.0% 對照 20%（五選一）——模型連**照抄**它眼前那行的 `mode`／`intent`
都做不到。所以 §十六.5 的疑點結案：`--tail-weight` **不是**主因。

### 2. 位置不是瓶頸（一次 OOD 對照）

若資訊是在單層遞歸膜裡衰減掉的，把 `<al_in>`
行搬到生成點旁邊就會改善。實測（24 列，`data/checkpoints/ai_al_round8.pt`）：把
`<al_in>` 行移到 prompt 末端後 `copy_mode` 10/24 →
**5/24**、correlation 沒有系統性上升（`d` 0.24 → 0.24、 `stress` 0.30 →
−0.05）。搬近反而更差，且不是「讀不到」——把整行換成 `<al_in> v=0.00`
會讓 24/24 列的輸出塊改變。模型在讀，只是讀到的資訊不足以回復那個映射。

### 3. 先量「這題能不能學」：新增 `gold_input_correlation` 與 `learnability`

`0/200`
只有在兩種情況下有意義：門檻在構造上可達，而模型沒達到。R8 把這兩個前提做成儀器欄位（`scripts/probe_emergence_boundary.py`）：

- `gold_input_correlation`——gold 對 `state_in` 的逐欄 Pearson，是
  `input_output_correlation` 的**上界**。沒有它，`r ≈ 0`
  分不出「模型沒學到」與 「契約本來就不怎麼依賴輸入」。實測（`--set all`，320 列）**0.743–0.839**（`v`
  0.810、 `a` 0.839、`d` 0.826、`fatigue` 0.801、`stress` 0.743、`health`
  0.755；只看 200 列 holdout 是 0.758–0.829）：正確模型應該重現 0.8 左右，模型讀到的是 0.0–0.14。
- `learnability`——把契約自己的形式（`out = t + (s−t)·exp(−dt/τ)`，對 `(s,t)`
  線性但係數依 `dt` 而變）用 5-fold out-of-fold 最小平方擬合，逐 `dt`
  一組係數，跟「`dt`
  只當一般特徵（無交互項）」對照。邊界集的讀數（`--set all`，320 列；括號為只取 200 列 holdout 時的值）：

  | 擬合                              | row_exact（六欄全在 ±0.005） | 逐欄 R²       |
  | --------------------------------- | ---------------------------- | ------------- |
  | 逐 `dt` 一組係數（模型看得到 dt） | **0.503**（0.385）           | 0.9996–0.9999 |
  | `dt` 當一般特徵（無交互項）       | **0.000**（0.000）           | 0.80–0.84     |

gate 需要 5/200 = **2.5%**，上界是 **50.3%**（holdout
38.5%）：門檻可達，而且離模型很遠。用 R7 自己的 2,633 列 train／653 列 val 對同一形式擬合，row_exact
**0.524**、逐欄R² 0.9996–0.9999，與邊界集一致。`dt_blind`
的 0.000 另外標出一件事：這道題的全部內容就是 `dt` 交互項——一個訓練時不把 `dt`
乘進狀態的模型，逐位幾乎不可能對。

### 4. 結論：0/200 是模型的讀數

資料可學（上界 50.3%）、儀器可達（門檻 2.5%）、權重已排除、位置已排除、輸入確實被讀到。剩下的是容量與表徵：1
layer、1 timestep、token-level、`vocab 80`、單層膜 readout 的模型在 loss
0.56 附近停住，連 3 選 1 的 `mode`
都只抄到 37%。下一個變因因此是**容量／表徵**（`--layers 2` 或
`--timesteps > 1`；或把六欄數字改成 copy-with-scale 解碼），而不是再調 loss 權重。

### 5. 儀器變更

`probe` 報告新增 `gold_input_correlation` 與 `learnability`（`folds`／`rows`／
`rungs_fitted`／`rungs_unfitted_rows`／`dt_conditioned`／`dt_blind`，各含
`row_exact`、`field_within`、`r2`）；`_affine_ceiling()`
對列數不足的 rung 不硬擬合，該 rung 的列改用 `dt_blind` 預測並計入
`rungs_unfitted_rows`，避免出現捏造的負 R²。
`tests/test_probe_emergence_boundary.py` 由 20 增至 **24
passed**（新增：gold 相關必須是上界、可學性上界 > 10× 門檻、`dt_blind`
逐位更低、列數不足回 `None`）。

## 十八、架構對照（2026-11-03）：同資料、同表徵、同目標、同評分下的第二個架構也讀 0

§十七 的結論是「剩下容量／表徵」。但那裡只有**一個**架構的 0。一個 0 在還沒有第二個架構讀過同一題之前，只證明「這個模型沒學到」，不證明「這題在這個 representation 下不可學」。本節把一個**標準 transformer**放進完全相同的條件，並且先修掉一個我自己引入的不對稱。

### 1. 先修對照中的不對稱（這一項是 bug，不是發現）

第一版 baseline 只有 teacher forcing，而 R8 的 SNN 帶 `--ss-final 0.5`
（排程取樣）。同一批資料在**不同訓練制度**下比較，量到的是制度的差，不是架構的差。修正後 baseline 走同一條 ramp（線性到 0.5、one-step 變體、loss 仍對 gold 計分）。修正前後 baseline 自己的 loss 由 0.19 升到 0.33——正好就是「學生開始看自己的預測」的代價，若不修，這個差會被誤記成架構優勢。

### 2. 對照條件（`scripts/compare_al_baselines.py`）

| 項目                                                                   | 設定                                                                |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 資料                                                                   | `ai_al_round7_train.jsonl`：train 2,633／val 653（與 R8 同一批）    |
| 分詞                                                                   | **直接從 SNN checkpoint 取詞表**（`vocab 80`）；batch／mask／加權由 |
| 同一份 `make_batch_weighted` 產生，不重寫資料格式                      |
| 目標                                                                   | answer 位置 CE、加權平均、clip 1.0、Adam lr 3e-3                    |
| 制度                                                                   | 教師強制＋排程取樣到 0.5、100 epochs、batch 32、greedy 解碼         |
| 容量                                                                   | transformer 1,196,112 參數（d_model 256／2 層／ff 512）vs SNN       |
| 1,239,634（d_emb 96／d_hidden 1024，其中 1.05M 是 1024×1024 遞歸矩陣） |
| 評分                                                                   | `probe_emergence_boundary.probe(model=...)`——**同一份評分程式**，   |
| 包含 gate、format、copy、correlation、可學性上界                       |

### 3. 讀數

| 讀數                                  | SNN（R8）     | Transformer                                 | 差值說的是什麼                               |
| ------------------------------------- | ------------- | ------------------------------------------- | -------------------------------------------- |
| gate（holdout／rotation）             | 0/200 · 0/200 | **0/200 · 0/200**                           | 兩個架構同樣沒過                             |
| 訓練 loss 最低                        | 0.563         | **0.334**                                   | baseline 擬合得更好                          |
| 訓練時間                              | 1,168s        | **159s**                                    | 同 epoch 下 baseline 快 7.3×                 |
| `response_tf`／`tail_tf`              | 0.386／0.794  | 0.318／**0.848**                            | 兩者都**能**在 gold 前綴下寫出狀態塊         |
| `format_ok`／`marker_ok`              | **223／203**  | 8／22                                       | 自由生成時 SNN 守得住骨架，baseline 崩成亂碼 |
| `copy_accuracy` mode／intent          | 37.2%／25.0%  | **59.1%／32.2%**                            | baseline 更會照抄                            |
| `input_output_correlation` 最大 \|r\| | 0.137         | 0.156                                       | 兩者都與上界 0.74–0.84 差一個量級            |
| `input_sensitivity` 改 `v`／改 `dt`   | 8/24 · 18/24  | **21/24** · 15/24                           | baseline 更依賴輸入，但依賴的方式不是契約    |
| 生成的合法塊樣本                      | 常缺 `a=`     | `3775\n<al_outealth=0.57 a=0.473 a=0.5257…` | 兩者的破法不同，都不到「一個正確塊」         |

### 4. 結論

1. **在相同表徵與預算下，0/200 不是 SNN 的判決。**
   一個參數相當、擬合更好、快 7 倍的 transformer 讀同一個 0，而且連骨架都更差（`format_ok`
   8 vs
   223）。所以 §十七 的「剩下容量」需要修正：**容量不是區分點**，我先前建議的
   `--layers 2` 不該當下一步（見 §十七.5 的修正註）。
2. **blocking factor 是介面，不是深度。**
   兩個模型都能在 gold 前綴下達到 0.79–0.85 的逐 token 準確率（`tail_tf`），卻只能在自由生成裡拿到 0 個合法塊。這道題要求把
   `v=0.26 → v=0.28` 這種值**精確重寫**，而要算出來必須先 (a) 把 `0.26`
   從 token 還原成數、(b) 對 `dt`
   做指數衰減、(c) 把結果印回兩位小數。token 序列上這是三次算術，不是一次查表——兩個架構都停在「學到形狀、學不到算術」。
3. **可比的條件現在成立，而且可被引用的比較是這張表**：`gold_input_correlation`
   給上界（0.74–0.84），affine 逐 `dt` 擬合給**非神經的參考解**（row_exact
   0.503），SNN 與 transformer 給兩個同預算的實測（0／0）。任何「SNN 不如／勝過其他方案」的說法，在此之前都沒有這三個數。
4. 下一個變因因此改成**介面**：狀態值以單一原子表示（`v=+0.28`
   一個 token）＋ copy-with-scale 解碼，讓「照抄並乘一個學到的係數」成為可學習的操作；容量留到介面修好之後再談，否則量到的仍是算術能力。

> **修正註（對 §十七.5）**：§十七 把下一步定為
> `--layers 2`／`--timesteps > 1`。本節的對照顯示容量不是區分點（transformer 容量相當仍 0/200），故該項降級為「介面修好後再驗」；介面（representation）先行。

## 十九、第九輪（2026-11-03）：修介面——結構修好了，精確度沒有

§十八 把阻塞點定位在**介面**：`v=0.26`
這種值在 token 空間要 4 個 id（`v`、`=`、`0`、`.`、`2`、`6`），要算出新值必須先做逐位進位算術。R9 把介面換掉，其餘全部不動。

### 1. 改了什麼（單一變因：representation）

`ai/ed3n/token_snn.py` 新增 `numeric_atoms` 模式（`--numeric-atoms`）：

- 契約值的閉集字母表：`-1.00 … 1.00` 共 201 個原子，加上 `dt` 的 `2.00`
  （四個 rung 中唯一落在 `[-1,1]`
  外的值，否則只有那一個 rung 會被拆成數字，量到的會是介面不一致而不是 `dt`
  條件化），被 seed 在詞表最前面， `max_vocab`
  **不得截斷**（缺一個值原子＝該值不可學；缺一個詞只是變 `<unk>`）。
- 其他所有數字（response 的
  `665`、`7.1944`）維持逐位切分，所以未見的 response 值仍可組合，`"".join(tokenize(x)) == x`
  仍成立。
- 詞表存進 checkpoint（`numeric_atoms`），`from_dict`/`load`
  會還原——否則同一份權重會被解成別的表示。

R9 的訓練指令與 R8 逐字相同（`--vocab token --d-emb 96 --d-hidden 1024 --max-len 384 --layers 1 --timesteps 1 --epochs 100 --batch 32 --lr 3e-3 --tail-weight 1.0 --ss-final 0.5`），唯一差別
`--numeric-atoms`。詞表 282（201 值原子 + 80 詞/符號 +
specials），2,633 列全部進得去 `max_len 384`。

### 2. 讀數：結構大幅改善，映射與精確度沒有

| 讀數                                        | R8（字元數字） | **R9（值原子）**   |
| ------------------------------------------- | -------------- | ------------------ |
| gate                                        | 0/200 · 0/200  | 0/200 · 0/200      |
| `format_ok`                                 | 223/320        | **301/320（94%）** |
| `marker_ok`                                 | 203            | **265**            |
| `body_distinct`                             | 241            | **306**            |
| `copy_accuracy` mode                        | 37.2%          | 36.6%              |
| `input_sensitivity` 改 `v`                  | 8/24           | **23/24（96%）**   |
| `tail_tf`（val，gold 前綴）                 | 0.794          | **0.829**          |
| `input_output_correlation` 最大 \|r\|       | 0.137          | 0.097              |
| `train_exact_200`／`val_exact_200`          | 0.000／0.000   | 0.015／0.000       |
| `field_hits`（v/a/d/fatigue/stress/health） | 98 合計        | 68 合計            |

**介面修對了它該修的東西**：合法塊 70% → 94%，骨架（`<al_out>`
標記）幾乎全中，輸入敏感度從 8/24 升到 23/24（模型確實讀 `v`
了）。**但 exact 仍是 0**，而且 `input_output_correlation`
反而略降到 0.097——值被讀進去，卻沒有依契約映射。

### 3. 為什麼「逐 token 0.83」等於「整塊 0」

把 `tail_tf = 0.829` 當成獨立事件乘一次就知道：狀態塊約 40 個原子，
`0.829^40 ≈ 5e-4`，在 320 列裡期望命中
**0.16 列**。也就是說 R9 的 0 不是新的壞消息，而是 `tail_tf`
的算術後果——**要通過 gate（5/200 =
2.5%），逐 token 準確率必須到 ~0.99**，而不是 0.83。

自由生成還多一層：`copy_accuracy` 只有 36.6%，但 `mode`
是**照抄輸入**的欄位（三選一隨機 33%）——所以「抄」這件事本身也沒學會，儘管
`tail_tf`
說它在 gold 前綴下寫得出。兩者不矛盾：gold 前綴裡已經有答案的前幾個原子，模型只要接龍；自由生成要它**自己決定第一個原子**，錯誤立刻複合。這個落差是 exposure
bias 的量，不是容量的量。

### 4. 架構對照（同一份原子詞表）

把 transformer 放進 R9 的詞表（`--checkpoint ai_al_round9.pt`，詞表與
`make_batch_weighted` 直接取用，其餘條件同 §十八）：

| 讀數                                  | SNN（R9）     | Transformer（R9 詞表） |
| ------------------------------------- | ------------- | ---------------------- |
| gate                                  | 0/200 · 0/200 | **0/200 · 0/200**      |
| `format_ok`                           | **301**       | 8                      |
| `marker_ok`                           | **265**       | 71                     |
| `tail_tf`                             | 0.829         | 0.840                  |
| 訓練 loss 最低                        | 0.385         | **0.054**              |
| `input_output_correlation` 最大 \|r\| | 0.097         | 0.143                  |

transformer 把訓練集擬合到 0.054（1.3M 參數對 2,633 列，記憶），`tail_tf`
略高，但自由生成只吐出 8 個合法塊——**守不住結構**。SNN 相反：結構 94%、內容不準。兩個架構在同一個介面下仍然都是 0，所以「0」不是介面的殘留，也不是架構的判決，而是**逐欄位精確度**的問題。

### 5. 下一步（依此輪量到的數字排序）

1. **copy-with-scale 解碼／值頭**：不要讓模型用下一個 token 決定一個連續值，而是每個欄位一個 201 頭的 softmax／回歸，解碼時取最近原子。理由：契約是
   `t + (s−t)·exp(−dt/τ)`，這是「照抄某欄 + 對 `dt`
   縮放」，用分類頭表達它需要的歸納偏置遠比 40 個 token 的自迴歸精確度容易；而
   `tail_tf 0.83 → 需要 0.99` 這條算術說明，光靠加層／加 epoch 沒有機會。
2. **把 response 從梯度裡拿掉**（或降權）：response 是另一件事（`653 + 12`），但佔 answer
   token 的三分之一；gate 只量狀態塊。R4–R8 一直用 0.25 權重壓狀態塊、R8/R9 用 1.0 平權，兩者都不是「只訓被量的那一塊」。
3. 容量（`--layers 2`）仍排在最後：§十八 已證容量不是區分點。

> **本輪的三個新事實（可直接引用）**：數值原子化讓合法塊 223→301/320；
> `tail_tf 0.83`
> 對 40 個原子的塊期望命中 0.16 列，所以 exact 必然是 0；同一份原子詞表下 transformer 仍是 0/200 且
> `format_ok` 只有 8。

## 二十、儀器的第四個錯（2026-11-03）：可學性上界低估了一半，而且 40% 的題目沒有答案

§十九 之後我仍有一個說不通的數字：兩個架構都 0，但
`learnability.dt_conditioned.row_exact`
是 0.503。若 0.5 的列真的可達，320 列裡就該有人偶爾命中。於是我把
`generate_al_dataset.build` 的 gold 公式拿出來對：

```
out[f] = c[intent][f] + (state[f] − c[intent][f]) · exp(−dt / 1.0)
```

`c` 是「10 列 pilot 的
`al_state_out`」——每個 intent 一組 6 個常數。所有輸入都在 prompt 裡（`<al_in>`
的六個值、`intent`、`dt`），只有 `c` 不在。也就是說這題是
**18 個常數的查表 + 一個 exp**，不是我以為的「token 空間算術」。

### 1. 新儀器欄位：`--ceiling` / `contract_form_ceiling`

`probe_emergence_boundary.py` 新增 `_contract_form_ceiling()`，只做三件事：

1. 從**訓練檔**反推常數：`c = (gold − state·k) / (1 − k)`，取中位數（`1/(1−k)`
   會放大 2dp 印刷誤差，短 `dt` 尤其嚴重，所以用中位數不用平均）；
2. 用**只含訓練檔**的資訊在 τ ∈ {0.25 … 2.0} 的格子上挑一個（結果選到 **τ =
   1.0**，與契約 §3.1 一致——這是獨立驗證，不是把常數寫死）；
3. 把算子套到評分列，用**跟 grader 同一個單位**（±0.005）算逐位與逐列。

實測（`data/intelligence_reports/mve1_contract_form_ceiling.json`）：

| 讀數                              | 值                                                                  |
| --------------------------------- | ------------------------------------------------------------------- |
| τ（由訓練檔挑出）                 | **1.0**                                                             |
| 學到的常數（math_query）          | v 0.30 / a 0.40 / d 0.70 / fatigue 0.22 / stress 0.18 / health 0.90 |
| 逐位命中                          | v .904 · a .879 · d .913 · fatigue .854 · stress .875 · health .892 |
| 逐列命中（看得到的 intent）       | **0.508**（122/240）                                                |
| 同上，但以整個 200 列 gate 為分母 | **0.381**                                                           |

### 2. 這翻轉了三個讀數

1. **「上界 0.503」其實是對的，只是理由錯了。**
   affine 上界 0.503 與契約形式上界 0.508 幾乎相同——不是巧合，而是**兩者都被 2dp 印刷卡住**：狀態以 2dp 印出，即使算子完全正確，`c + (s−c)k`
   也只能到逐位 0.85–0.91、逐列 ~0.51。所以 0.5 不是「模型的天花板」，是**資料精度**的天花板。
2. **gate 是 100% 可通過的。**
   2.5% 的門檻遠低於 51% 的上界；之前「0/200 且上界只有 0.5，所以也許是題目太難」的推論，現在可以換成「0/200 是能力的 0，不是題目的 0」。
3. **gate 有 40% 的題目在構造上沒有答案。** holdout 200 列是 5 個 intent ×
   40 列，其中 `greeting`、`humor` 兩個 intent
   **在訓練檔裡完全沒出現**（訓練只有
   `math_query`／`unknown`／`knowledge_query`）。新 intent 的 6 個常數沒有任何觀測，模型不可能猜中 6 個 2dp 值。這 80 列（40%）不是「難」，是**不可知**；剩下 120 列才是真正的考題。`contract_form_ceiling`
   因此同時報 `seen_intent_rows` / `unseen_intent_rows` 與兩個分母。

### 3. 對「繼續修」的影響

- 值頭／copy-with-scale 的目標從「逐 token
  0.99」換成**逐位 0.85–0.91、逐列 ~0.5**，這是可以量、可以驗的；值頭直接輸出每欄一個 201 元分布，正好落在這個目標上。
- 任何後續比較都必須**分開報**
  120 列（可達）與 80 列（不可達），否則「0/200」與「61/200」會被平均成一團無法解釋的數字。
- 儀器現在有四個互相印證的錨點：`gold_input_correlation`（線性上界 0.74–0.84）、affine 上界（0.503）、**契約形式上界（0.508，τ 由資料挑出）**、以及模型實測（0）。

## 二十一、0/200 的兩個成因（都量到了），以及 gate 第一次通過（2026-11-03）

§二十 把「輸入不可見」排除之後，還有兩個候選：狀態留不住輸入、或狀態留住了但解碼不到exact。我加了三種讀數把它們分開，結論是**兩個成因同時存在，而且都可量**。

### 1. 成因一：漏電遺忘 —— 狀態的有效記憶是 6 個 atom

訓練後的 `beta`（膜電位保留率）是 **0.832**，所以有效記憶 `1/(1−β) ≈ 6.0`
個 atom。block 起點距離 `<al_in>` 的六個數值約 **120** 個 atom，衰減
`0.83^120 ≈ 2×10⁻¹⁰`。

用「從 hidden state 線性回歸六個 gold 值」在三個位置量 R²（ridge，λ=10/100）：

| 讀點                               | 距讀到數值 | R² (v/a/d) | R² (fatigue/stress/health) |
| ---------------------------------- | ---------- | ---------- | -------------------------- |
| `values_end`（`\|` 之前）          | 0 atom     | 0.08–0.19  | 0.15–0.28                  |
| `input_line_end`（讀完題目文字）   | ~6 atoms   | ≤ 0        | ≤ 0                        |
| `block_start`（要吐 block 的位置） | ~120 atoms | ≤ 0        | ≤ 0                        |

也就是說：**在讀到的那一刻，狀態只線性編碼了 8–28% 的輸出變異；6 個 atom 之後歸零。**
任何解碼器在 block 起點都拿不到輸入——這不是容量問題，是 $\beta$ 的算術。

### 2. 成因二：±0.005 的閘門要求「精確計算」，統計估計不可能達到

把契約欄位（六個 in 值 + dt + intent
one-hot）**直接**交給閉式 ridge，完全繞過循環：

| 讀數                     | 值            |
| ------------------------ | ------------- |
| 逐欄 R²                  | **0.69–0.83** |
| 逐欄 MAE                 | 0.055–0.145   |
| 逐欄 ±0.02 內            | 8%–23%        |
| **逐列 exact（±0.005）** | **0 / 316**   |

R² 0.8 已經很好，但 grading 的容差是 ±0.005，等於要求 MAE ≈ 0.002
—— 比量到的 MAE 小 30–70 倍。**任何連續估計都不可能通過 exact
gate；只有精確算子可以。** 這也解釋了 §二十 的 0.508 上界為何是「算子正確 +
2dp 印刷」而不是「模型不夠好」。

> 同時修掉兩個我自己引入的儀器 bug：(a) 值頭的標籤 gather 寫成
> `y_flat[idx.repeat_interleave(6)]`，把**列索引**當扁平位置用，head 學到的是「我是第幾列」（train
> 0.05 nats、準確率 0），已改為 `y[idx].reshape(-1)`；(b) 40 epochs × 2611 列 =
> **240 次更新**，對 1206 個 logits 根本沒動，改為 3000
> steps。修正後 head 在 train 0.80–0.99、eval 0.000
> —— 也就是**記住了 2611 列**，這是資料量與參數量的問題（1.24M 參數 /
> 2611 列），不是表示問題。

### 3. 修法：值介面 + 精確算子（19 個參數），gate 首次通過

契約 §5 的算子形式是已知的：`out = c[intent][f] + (in[f] − c[intent][f])·e^(−dt/τ)`。資料只需要提供
**18 個常數 + 1 個 τ**。新增
`--operator-head`：用梯度下降（不是閉式反推）在這 19 個參數上擬合訓練列，其餘交給精確算術。

實測（`data/intelligence_reports/mve1_operator_head.json`，checkpoint R9）：

| 讀數                   | 值                                              |
| ---------------------- | ----------------------------------------------- |
| 學到的 τ               | **1.0001**（資料自己回到契約的 1.0）            |
| 參數                   | **19**                                          |
| seen-intent 逐列 exact | **0.525**（120 列中 63 列）                     |
| 全 200 列逐列 exact    | **0.315**（63/200）                             |
| 逐欄命中               | 0.867–0.933                                     |
| **gate**               | family 63 ≥ 5、rotation 0 ≤ 1 → **pass = true** |

**這是 MVE-1 第一次通過**，而且必須誠實標籤：通過的是**值介面**（block 是六個數字），不是文字介面（block 是 ~40 個 atom）。文字介面的 0/200 現在有兩個確定的成因（記憶 6
atoms、精確度 30–70 倍的差距），而不是「容量不夠」或「題目太難」。

剩下 80/200（greeting、humor）仍然無解：它們的常數從未在訓練出現，任何模型都無法從 prompt 推出，這一半必須由資料或契約補上，不能由模型補。

## 二十二、有界元胞機對照：兩個真實缺陷，以及「可區分 ≠ 可解碼 ≠ 可泛化」（2026-11-03）

§二十一 把成因指向漏電，那就需要一個**不是漏電積分器**的對照。新增
`scripts/compare_cellular_baseline.py`：有限晶格、只有局部疲勞、**沒有
`tick % N`
全局清空**。容器大小不抄外部玩具，直接綁專案自己的界：`TokenConfig.max_len` =
**384 格（20×20）**，一格對一個 token 槽；每格三個狀態（活化／疲勞／閾值），可選加一個慢積分器（latch）；動力學參數 0 個（固定隨機耦合），只有讀出層是學的。同 tokenizer、同窗口、同訓練檔、同 316 列評分列、同 ±0.005 評分程式。

### 1. 機器自己先壞了兩次，都是量出來的

| 症狀                 | 量到的證據                               | 成因                                                         | 修法                                                          |
| -------------------- | ---------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------- |
| 容器幾乎不隨輸入變   | 跨列 std **0.004**、行內 std 0.18        | **全正耦合 → 晶格同步成均勻場**（384 格活化 std 只有 0.012） | 混合正負耦合 + 每格偏壓 → idle std **0.382**                  |
| token 幾乎不影響狀態 | 一次注入只把活化推 ~0.01，遞歸驅動 ~0.18 | 輸入耦合 `1/√N` 相對遞歸太弱                                 | 加 `--in-gain`（預設 4.0）→ 跨列 std 0.013，兩個 token 可區分 |

這正是設計筆記警告的「全局飽和」，只是成因不是清空而是**同步**：沒有抑制性連結，整個容器只裝一個數。修完之後，測試把它釘住（`tests/test_compare_cellular_baseline.py`）：沒有全局重置、不均勻、token 進得去。

### 2. 記憶：CA 贏了，但只贏一點

同一組六個值、同一組位置、同一種線性讀出（in-sample，只看「容器裡有沒有」）：

| 讀點                       | SNN hidden（§二十一） | 有界 CA（無 latch） | 有界 CA（latch τ=64） |
| -------------------------- | --------------------- | ------------------- | --------------------- |
| 剛讀到數值                 | 0.08–0.28             | **0.188**           | **0.225**             |
| 走一半到 block             | ≤ 0                   | 0.239               | 0.274                 |
| block 起點（~12 atoms 後） | **≤ 0**               | **0.144**           | **0.181**             |

結論：**沒有全局清空、只有疲勞的有限晶格，確實比漏電 SNN 留得住**（0.14–0.18 對 ≤0）。但絕對值仍然只有 14–18%——離「可解碼」還很遠，而且加上慢積分器只多 25% 相對值。

### 3. 任務：0 exact，而且泛化是負的

| 讀數                          | 值                  |
| ----------------------------- | ------------------- |
| 同分布驗證 R²（訓練列 80/20） | **0.19–0.23**       |
| 316 列評分列 R²               | **−19 ~ −21**       |
| 逐列 exact（±0.005）          | **0 / 197 holdout** |

同分布只有 0.23、跨分布直接崩到 −19：讀出層學到的是**prompt 的文字樣式**，不是契約關係。這與 §二十一 的值頭（train
0.80–0.99、eval 0.000）是同一個病，只是換了載體。

### 4. 對「找問題、修問題」的結論

1. **「不會卡死」不是 gate 的瓶頸。**
   這台機器確實不卡死、不靠計時器、容器有限、不同輸入留下不同狀態——設計筆記的四個測試都會過——**但 gate 仍然是 0**。「可區分」（test
   D）不等於「可解碼」（R²），也不等於「可泛化」（−19）。
2. **latch 是必要條件，但不是充分條件。** 慢積分器把 12
   atoms 的記憶從 0.144 提到 0.181，方向對、量級不夠；要真的留住六個 2dp 值，需要的是**暫存器**（把值寫進去、不解碼前不清），而不是更慢的衰減。
3. **專案該修的**：MVE-1 的通過路徑就是 §二十一 的算子頭（63/200）——把數值當**值**、用精確算術；任何「靠狀態記憶 + 統計讀出」的路線（SNN、transformer、CA）都在§二十一的 0/316 與這裡的 0/197 上撞同一堵牆。新腳本與 5 個回歸測試把兩個缺陷（同步、輸入太弱）釘住，以後要主張「這台機器有記憶」就必須同時報 contrast 與 retention。

## 二十三、80 列「沒看過的 intent」與 ±0.005 的天花板（2026-11-03）

§二十一 的 63/200 一直被讀成「模型只做到三成」。把它拆開之後，這兩個數字都要改：一個是我自己儀器的漏洞，一個是**評分格子本身的上限**。

### 1. 沒看過的 intent 不是「學不會」，是「查不到」

holdout 200 列裡：`math_query` 40、`knowledge_query` 40、`unknown` 40
—— 這三個在訓練檔裡； `greeting` 40、`humor` 40 ——
**訓練檔完全沒有**。實測（用正確的目標向量、精確算術）：

| intent                       | 正確目標 → exact | 用 baseline 當 fallback → exact |
| ---------------------------- | ---------------- | ------------------------------- |
| greeting                     | **23/40**        | 0/40                            |
| humor                        | **19/40**        | 0/40                            |
| math_query                   | 22/40            | 0/40                            |
| knowledge_query              | 22/40            | 0/40                            |
| unknown（目標就是 baseline） | 21/40            | 21/40                           |

所以「退回去用平均值」是 0 分，不是可行解。可行解只有一個：**契約 §5 的 intent 目標表是執行期查表**
（config，不是學來的權重）。把表接上：

| 讀法                                  | 200 列 exact | holdout 比例 | gate             |
| ------------------------------------- | ------------ | ------------ | ---------------- |
| 原生文字介面（round 9 原狀）          | 0            | 0            | fail             |
| 值介面算子頭（只靠學到的常數）        | **63**       | 0.315        | **pass（首次）** |
| 值介面 + 契約 intent 表（執行期查表） | **105**      | **0.525**    | **pass**         |
| 正確常數 + 精確算術（參考上界）       | **107**      | 0.535        | —                |

**105/107 =
98%**：算子頭已經吃下這個介面給的全部。剩下的 2 列與那 93 列失手，不是模型，是格子。

### 2. 失手 93 列的原因：輸入與 gold 都只印到 2dp

評分是 `|pred − gold| ≤ 0.005`，但算子要吃的 `<al_in>` 本身只印到 2dp，所以
`pred` 繼承 `|Δin|·k ≤ 0.005·exp(−dt/tau)`，再加上 gold 自己的 2dp 四捨五入。
`dt=0.25` 時 k=0.779，兩項相加可到 0.0089 > 0.005 ——
**這一列無論模型多準都不會 exact**。

| dt   | 50 列中 exact（正確常數） |
| ---- | ------------------------- |
| 0.25 | **11**                    |
| 0.50 | 25                        |
| 1.00 | 25                        |
| 2.00 | **46**                    |

逐列最大誤差中位數 0.0049、p90
0.0070——全部貼在容差邊上。這是**儀器**的性質，不是模型的。

### 3. 我自己犯的兩個錯（都靠對帳抓回來）

1. **跳過 unseen**：`_score_contract_rows` 原本遇到 `intent` 不在常數表就
   `continue`，於是 80 列「沒看過的 intent」在分母裡、在分子裡永遠是 0。修：接受
   `targets`（契約表），兩種讀法都輸出（`row_exact_of_all`
   = 只靠學習、`row_exact_all_intents` = 加查表）。
2. **分子分母搞混**：第一版寫
   `graded = seen_n + unseen_exact`，把「已見**列數**」當成「已見**命中數**」，於是報出
   **162/200（81%）**——比 200 列裡 unseen 只有 80 列還多，算術上不可能。修成
   `seen_exact + unseen_exact` →
   105。這條現在有回歸測試（`test_exact_counts_can_never_exceed_rows`）。

### 4. 結論

1. **gate 通過兩次、且不是靠調參**：63/200（純學習）→
   105/200（+ 契約表），後者是這個介面的 98%。
2. **「0/200」的真正成因是介面，不是智力**：把六個數當數值、用精確算術，配上契約的 intent 表，就從 0 走到 105。這與 §二十一/§二十二 的結論一致。
3. **要讓 exact 這個數字有意義，儀器得先修**：把
   `<al_in>`/gold 印到 3dp，或把容差改成
   `0.005 + 0.005·exp(−dt/tau)`。否則「≥5/200」這個 gate 太鬆（實測上限 53.5%），而「exact」在 dt=0.25 那一格幾乎不可能。這是下一步該做的，不是再調模型。

### 5. 第二種讀法：把列印誤差從「模型錯」裡分出來

既然 93 列失手全是容差邊界，就加一個明示的第二讀法：
`row_exact_rounding_aware`，容差放寬到 `0.005·(1 + exp(−dt/τ))`（把 2dp 輸入的
`0.005·k` 加上 gold 自己的 0.005）。同一支模型、同一組常數、同一次執行：

| 讀法                      | 200 列 exact | 上限（正確常數） | 達成率    | reference 120 列 |
| ------------------------- | ------------ | ---------------- | --------- | ---------------- |
| 嚴格格子 ±0.005           | **105**      | 107              | 98%       | 59（0.492）      |
| 列印誤差修正 ±0.005·(1+k) | **197**      | **200**          | **98.5%** | **117（0.975）** |

也就是說：**算子頭的算術誤差只有 3 列**，其餘全部落在 2dp 列印造成的不可判定區。那 3 列逐列查過，不是 clamp、不是截斷，是學到的常數差了約 0.002（例如
`unknown` 的 fatigue 推 0.4570 對 gold 0.450，差 0.0070 > 0.0068 的容差）。

### 6. 最終階梯

```
原生文字介面                0 / 200
值介面（只靠學到的常數）     63 / 200   （嚴格格子；= 已見 intent 的上限 65/120）
值介面 + 契約 intent 表     105 / 200   （嚴格格子；上限 107 → 98%）
                            197 / 200   （列印誤差修正；上限 200 → 98.5%）
```

**判讀**：MVE-1 這個 boundary 不是「模型智力不足」，而是三件可分別修的事——介面（文字 vs 數值）、知識來源（權重 vs 契約表）、度量（2dp 格子）。三者分開量之後，這個任務到此基本達成；剩下該改的是**度量**（印 3dp 或採列印誤差修正的容差），否則「exact」永遠只能到 53%。

## 二十四、修度量：把 2dp 印成 3dp 之後，同一支算子頭 200/200

§二十三 的結論是「該修的是度量」。這輪真的修了，而且修出三個都是**儀器**的缺陷，不是模型的缺陷。

### 1. 修掉的三個儀器缺陷

**(a) 輸入 3dp、gold 2dp。** `family_golds()` 沒接 `decimals`，`<al_out>`
停在 2dp 而 `<al_in>` 已經 3dp。逐列查那 15 列失手，誤差是
`0.00532 / 0.00530 / 0.00520 …`
——正好是「gold 的 2dp 捨入」而不是「模型的算術」。同一批列在正確常數下的最大值就是 0.0053，也就是**上界本身被自己的列印卡住**。這是
`"precision mismatch"` 型缺陷：兩邊精度不一致時，容差被吃掉一半。

**(b) 常數用 GD 擬合，落在收斂地板上。** 固定 τ 時 `out = c + (in − c)·k`
對 c 是
**線性**的，所以常數有閉式解：`c = Σ w·a·b / Σ w·a²`（`a = 1−k`、`b = gold − k·in`、
`w = 1/(1+k²)`
是殘差的反變異數）。GD 的 19 個參數只能逼近到 ~0.002，那正是上一輪剩下 3 列的誤差。改成閉式解後 τ 只剩一維網格搜尋（訓練 MSE 選），不再有學習率與收斂地板。

**(c) 價值介面被文字詞彙的 2dp 格子擋住。** `_operator_head_report` 原本用
`_value_targets(vocab, gold) is not None`
過濾訓練列 —— 那是**文字**介面的條件（atom 只能落在 201 個 2dp 值上）。算子頭直接讀六個浮點數，根本不需要這個閘門。留著它的結果就是：3dp 語料的
`train_ok` 是
**0 列**（`expressible = 0`），3dp 版本「學不了」的原因是閘門，不是資料。現在改成計數後放行。

順手修掉兩個 CLI/檢查的坑：`--check` 沒給 `--src`
時會拿 10 列 pilot 去比對 3180 列的語料（永遠失敗）→ 改讀 manifest 記錄的 source；`--report`
被三個 head 模式忽略（各自寫死檔名）→ 改成 `--report` 給了就用。

### 2. 量測（同一支模型、同一組列、只改上面三件事）

| 設定                         | strict ±0.005 | 列印誤差修正 | 上界    | reference 120 列 |
| ---------------------------- | ------------- | ------------ | ------- | ---------------- |
| 2dp 語料 + GD 常數（上一輪） | 105/200       | 197/200      | 107     | 0.492            |
| 2dp 語料 + 閉式常數          | 108/200       | **199/200**  | 107     | 0.458            |
| **3dp 語料 + 閉式常數**      | **200/200**   | **200/200**  | **200** | **1.000**        |

`by_dt` 全綠：0.25 / 0.5 / 1.0 /
2.0 各 50/50。LS 與 GD 在 3dp 上都是 200（資料乾淨時兩者都到頂；差別只在 2dp 的 108
vs 105）。

### 3. 誠實判讀

- 200/200 是**算子頭**（值介面）的分數，不是 1.24M 參數語言模型的分數。文字介面仍是 0/200（它要輸出 ~40 個 atom，而且 atom 只認 2dp）。
- 上界也是 200，所以這次不是「逼近上界」而是**碰到上界**：契約 §5 的算術 +
  intent 查表 + 可判定的度量，三者齊了就滿分。這個 boundary 已經**沒有剩餘空間**留給「更會算」的模型去賺。
- 反過來說，MVE-1 到這裡證明的東西很窄：它證明「介面與度量決定一切」，不證明「模型有 emergent 能力」。要把 emergent 的部分量出來，得換一個**文字介面不可解、值介面可解**的任務，而不是繼續在同一個 6 數字上調。
- 剩下的真問題：`ai_al_round7`
  之後的語料還是 2dp 生的，checkpoint 也是在 2dp 上訓的。3dp 只驗證了**介面**，沒有重訓 LM。要不要把
  `--decimals 3` 定為下一輪預設，是一個訓練成本決策（舊 round 1–6 的 `--check`
  會全部失敗，因為它們是 2dp 生的）。

## 二十五、收尾：把同一個修法套到剩下的路徑上

§二十四 換掉的三件事只發生在算子頭那條路。其餘還在用舊做法的路徑一併對齊：

1. **`--ceiling`（分析用天花板）**
   原本只有 median 一種估常數的方式。現在兩種都跑、都報（`estimator_comparison`），並按訓練分數取較好者。實測 2dp：median
   `row_exact_seen = 0.5083`、閉式解 `0.5042` ——
   **差 1 列，median 在這裡沒有錯**。這很重要：它證明 §二十四 的 105→108 不是「換估計器」賺來的，而是 §二十四(a)(c) 兩個缺陷修掉之後，閉式解才顯得出來。3dp 上兩者都是
   `seen 1.0`。
2. **round loop 沒有 3dp 出口**：`ai_al_round_loop.py` 的 generate / prepare /
   check 三步都寫死 2dp，所以「下一輪用 3dp」只能手動做。加上
   `--next-decimals`（預設 2，保持既有 round 1–7
   byte-identical），一路傳到 prepare 與 check，並在 batch
   manifest 記錄（非 2dp 才寫）。
3. **舊 round 的 `--check` 全部回歸驗證**：round
   4/5/6/7 的 train/val 分別 3095/857、3310/815、3408/792、2633/653，四輪
   `check ok`。預設 2dp 的 ── 這條路沒被動到。

到這裡，「值介面 + 契約表 + 可判定度量」三件都齊，且在 2dp 與 3dp 上各有一組可重現的數字。**MVE-1 這一輪沒有剩下的模型問題可修**；要再往前，得換任務，而不是繼續在同一個 boundary 上調參數。

## 二十六、規模上限：先量硬體，再談加大模型

「能不能擴大規模」在這個邊界上不是模型問題，是**兩個會被搞混的記憶體**。這台是 Intel
Arc B570（9.9 GiB）、12 核、**實體記憶體 7
GB**。VRAM 看起來很大，但它跟使用者的遊戲共用；主記憶體小，而且**看不見**。

`scripts/probe_scale_envelope.py` 用真實的 `TokenSNN.loss` 跑 1 warmup +
3 步，每個配置**獨立一個行程**（host
high-water 是單調的，同一個行程量多個配置會全部印出第一個的峰值 —— 第一版就是這樣印出 2
TB RSS 的）。

| d_emb   | d_hid    | L     | bs     | len     | params     | dev MiB  | host MiB | s/step    |                |
| ------- | -------- | ----- | ------ | ------- | ---------- | -------- | -------- | --------- | -------------- |
| 96      | 1024     | 1     | 32     | 384     | 1.45M      | 83       | 2162     | 0.094     | round-9 的點   |
| 128     | 1536     | 1     | 32     | 384     | 3.01M      | 142      | 2170     | 0.102     |                |
| 128     | 2048     | 2     | 32     | 384     | 13.44M     | 410      | 2151     | 0.179     |                |
| 192     | 2048     | 2     | 48     | 512     | 13.59M     | 501      | 2166     | 0.207     |                |
| 256     | 3072     | 2     | 48     | 512     | 30.01M     | 919      | 2164     | 0.348     |                |
| **256** | **4096** | **3** | **64** | **512** | **86.13M** | **2450** | **2128** | **0.878** | **預算內最大** |
| 384     | 5120     | 3     | 64     | 768     | 134.56M    | 3515     | 1931     | 1.342     | 超 3 GiB       |

三個結論，最後一個最重要：

1. **可以放大到 59 倍參數**（1.45M →
   86.13M），代價 9.3 倍步時；整個 grid 的 host 峰值只差 **144
   MiB**。也就是說主記憶體**不是**容量的限制 —— 它是**併發**的限制。
2. host 的成本是**固定的每行程 ~2.15 GiB**（torch + oneAPI/L0
   loader + 第一步的 kernel codegen），跟模型大小幾乎無關。7
   GB 只有一條命：**同時只能跑一個 torch 行程**，這也是為什麼長跑不能併行測試。
3. VRAM 才是隨容量線性長的那個。3 GiB 預算下 86.13M 站得住，還留 6.9
   GiB 給遊戲；134.56M 就進不去了。**校準證據**：grid 第一列預測 100 epoch ≈
   13 分鐘，round-9 實測 1037 秒（17 分鐘）—— 探針不是紙上算的。

## 二十七、多合一：混合比例是量出來的，不是配的

`scripts/hybrid_boundary.py` 放四個**失敗方式不同**的元件，用同一組列比：

- `table` — 契約 §5 的 intent→target 查表（不學，是引擎本來就有的知識）
- `operator` — 閉式常數 + 契約算術（參數型，19 個數）
- `knn` — 最近鄰的隱含常數（非參數，假設「每個 intent 一個常數」不成立時才該贏）
- `copy` — 恆等，對照組

路由在**訓練檔**上決定（knn 用 leave-one-out，否則它會找到自己而得 100%），量到儀器集上：

| 精度 | table   | operator | knn   | copy  | 混合        | 混合比例                   |
| ---- | ------- | -------- | ----- | ----- | ----------- | -------------------------- |
| 3dp  | 240/320 | 240/320  | 6/320 | 0/320 | **320/320** | table .749 / operator .251 |
| 2dp  | 128/320 | 121/320  | 1/320 | 0/320 | **164/320** | operator .443 / table .557 |

- **兩個元件都是承重的**：3dp 去掉任一個都掉回 240/320（各缺 80 列，一組是「沒訓練過的 intent」、一組是「表裡沒有的 intent」）。這不是疊加好看，是互相補洞。
- **knn 是死重**：3dp 0.019、2dp
  0.003。非參數反演把 1/(1−k) 的放大直接吃進來，最近鄰的 dt 又不一樣，噪音主導。**已從預設組合移除**，保留
  `--with-knn` 供日後重測。
- 2dp 的混合比例跟 3dp 不同（operator .443 vs
  .251），因為 2dp 下 operator 在 knowledge_query 上略勝 table
  —— 比例是資料決定的，不是寫死的。

### 文本介面為什麼不進這個混合

`_value_targets`
檢查：**2dp 語料 2611/2633 列可以被 atom 表達，3dp 語料 0/2633**。3dp 的文字介面在**構造上**就是 0 分（tokenizer 只有 201 個 2dp
atom），不是訓練不足，加大容量、加長訓練都不會改變。所以文字頭沒有資格進混合 —— 它不是一個會輸的元件，它是一個**表達不了**的元件。

### 判讀

多合一在這裡的價值不是分數（3dp 已經是 320/320 的天花板），是三件事：**成本**
（table 一查表就打掉 75% 的列）、**誠實**（哪個元件承重、哪個是死重，ablation 直接說）、以及**退化**（拿掉任一元件會掉多少，是可預測的 80 列，不是崩掉）。

## 二十八、把模型真的跑到邊界上：兩個真缺陷、一個否證

§二十六 只證明「放得下」，沒證明「放得下就會學」。實跑 86.13M（d_emb 256 /
d_hidden 4096 / layers 3 / batch 64 / max_len
512）暴露三個問題，前兩個是缺陷，第三個是答案。

### 缺陷一：堆疊 LIF 層會塌成無條件分布

第一輪（layers=3）訓練曲線 `11.68 → 4.36 → 3.87`
之後**完全平**：25 個 epoch 動不了 0.03。而同一份資料、同樣 4
epoch，layers=1 掉到 2.50。

- 排除學習率：`lr 3e-3` 與 `lr 3e-4` 停在**同一個** 3.89。
- 排除 DC 飽和：把上層驅動減去平均放電率（`spk − 0.5`）仍是 3.89。
- 定位：3.89 ≈ 語料的**邊際熵 4.10
  nats**。也就是說讀出端只剩「與 token 無關的向量」，模型退化成 unigram，這不是欠擬合而是**資訊在層間丟失**。
- 修法（`token_snn.py`）：每層從 embedding 加一條 skip
  `mem[layer] += w_skip[layer](x)`，深度不必再靠脈衝傳遞「我是哪個 token」。同一配置 4
  epoch 由 3.89 降到 **2.96**。
- 相容性：`w_skip[0]` 是 `nn.Identity()`、`layers=1`
  時 skip 恆為 0 且沒有參數，所以 rounds 1-9 的 checkpoint
  **完全載得進去**（測試鎖住）。

### 缺陷二：最後一個 epoch 發散會把好權重蓋掉

修好之後的第二輪：`epoch 17/18/19 = 1.041/1.043/1.139`，`epoch 20 = 7.02`（同 lr，
`scheduled sampling` 餵自己的預測餵爆）。而舊的 `log_row`
**每個 epoch 無條件存檔**，於是最後一次寫入把 19 個好 epoch 全蓋掉，`--probe`
量到 `format_ok=0`。

修法（`train_token_snn.py`）：非有限 loss 不寫入；另存 `<out>.best`
邊車，訓練結束後若最後一個 epoch 更差就還原最佳。第二輪日誌：
`restored epoch 14 (loss=1.0373) over the final epoch (loss=2.6117)`。報告新增
`best_loss` / `best_epoch`，讓「跑完」與「跑好」分得開。

### 否證：容量不是這裡的瓶頸

同資料、同 `lr 1e-3`、同 20 epoch、同 batch 64，只差容量與深度：

| 模型                      | 參數   | 20 epoch loss | teacher-forced | response | state block | 儀器 0/20     |
| ------------------------- | ------ | ------------- | -------------- | -------- | ----------- | ------------- |
| 1.45M（layers 1）         | 1.45M  | **0.580**     | **0.785**      | 0.458    | **0.829**   | `format_ok=0` |
| 86.13M（layers 3 + skip） | 86.13M | 1.037         | 0.185          | 0.248    | 0.176       | `format_ok=0` |

- 小模型在**相同 epoch 預算**下全面勝出（0.785 vs
  0.185），而且每步只要 1/9.3 的時間。
- 大模型的文字介面仍是 **0/20、`format_ok=0`**；round-9（1.45M、100
  epoch）的 0.786 teacher-forced 也從沒產生過一個可解析的 block。
- 也就是說：§二十六 證明的 59× 容量**買得到**，但**買不到文字介面**。真正的限制仍是 §二十七 尾巴那個數字 ——
  3dp 語料 atom 可表達率 0/2633。在格子改動之前，加大模型只是把同一個 0 變貴。

### 判讀

這輪的真正產出不是分數，是兩個會被反覆踩到的坑：**深層 LIF 需要非脈衝的身分通道**、
**訓練迴圈不能無條件覆寫 checkpoint**。兩者都只用幾行程式修掉，而且不影響既有 checkpoint。至於「能不能擴大規模」——可以，硬體也撐得住；但**沒有理由**在這條路線上擴大，因為它的瓶頸被量在 tokenizer，不在參數。

## 二十九、訓練的規則：不是「小心調參」，而是四條寫進迴圈的機制

§二十八 的結論是「跑得動，但不會學、也不會停」。那是**沒有規則**的結果。這節把規則寫成程式，讓「怎麼訓練」不再是一個需要回答的問題 —— 任何 lr 只會落到「學會 / 震盪 / 自己降速」三種結局之一，而磁碟上的 checkpoint 永遠是有限、而且訓練過的模型。

### 四條規則

1. **不許無限長大**（`train_on(guard=True)`）：某一 epoch 的 loss 超過目前最佳
   `--diverge-factor`（預設 3）倍，或出現非有限值，就**還原最佳有限權重、把 lr 砍半**
   並繼續。震盪是允許的 —— 規則只在「失控」時動手；被砍半的 lr 有 `--min-lr`
   地板。
2. **單一壞 batch 不污染權重**：非有限 loss 的那一步直接跳過（`skipped`
   計數），不讓一次 NaN 傳進參數。
3. **選擇看驗證，不看訓練**（`--patience`）：每 epoch 算一次 teacher-forced 驗證 loss（一次前向、不生成），最好的那個 epoch 才寫進 checkpoint；連續
   `N` 個 epoch 沒進步就早停。這條是「不過擬合」的實際執行者。
4. **形狀固定**（`--lr-schedule cosine --warmup K`）：先線性升溫，再餘弦下坡，最後停在
   `--min-lr`。爆掉的常見成因是「開頭太大、結尾還太大」，這條同時處理兩端。

### 動力學特徵：三種死法，loss 分不出來

spiking
stack 只會用三種方式壞掉，而 loss 曲線對三者一視同仁：**死掉**（沒有層放電）、
**飽和**（每個 unit 每步都放電，速率不帶 token 資訊）、**活著**。判別特徵是**門檻附近的質量**
—— surrogate gradient 是 `sigmoid(5x)`，`|mem−θ|<2`
之外幾乎沒有梯度，所以在那個帶裡的比率（`sensitive`）才是「這層還在學嗎」的證據，放電率不是。

`TokenSNN.dynamics()` 量出來的實況（同一批 8 列驗證資料）：

| checkpoint                             | verdict                     | β     | θ        | 各層 rate / sensitive / \|mem\|                                            |
| -------------------------------------- | --------------------------- | ----- | -------- | -------------------------------------------------------------------------- |
| round-9（1.45M，100ep，lr 3e-3）       | alive                       | 0.832 | **6.75** | L0 0.03 / 0.015 / 24.5                                                     |
| round-10（86M，20ep，lr 1e-3，無規則） | **firing-without-gradient** | 0.820 | 0.57     | L0 0.50 / 0.013 / 46.2；L1 0.51 / **0.002** / 91.0；L2 0.32 / 0.024 / 52.2 |
| small20（1.45M，20ep，lr 1e-3）        | alive                       | 0.890 | 0.72     | L0 0.04 / **0.239** / 3.3                                                  |
| **86M guarded（20ep，cosine+warmup）** | alive（L1 邊緣）            | 0.852 | —        | L0 0.47 / 0.018；L1 0.49 / 0.006；L2 0.04 / 0.028                          |

兩個可以拿去當規則看的數字：

- **θ 會漂**：round-9 把門檻從 0.5 學到
  **6.75**，於是 97% 的放電被關掉、\|mem\| 卻漲到 24.5
  —— 那不是「學會了稀疏表徵」，是把梯度通道關掉的省力解。θ 是自由參數這件事本身就是一個失控源。
- **`sensitive` 才是預測指標**：0.239（TF 0.785）／0.015（TF 0.786，100
  epoch 補回來）／0.002（TF
  0.185）。放電率在三個模型上都介於 0.03–0.51，完全分不開好壞。

### 規則跑起來之後

同一個 86.13M 邊界配置、同樣 20 epoch、同樣 `lr 1e-3`，只加上四條規則：

|                   | loss   | val loss | TF        | state block | 儀器 `format_ok` | 0/20 |
| ----------------- | ------ | -------- | --------- | ----------- | ---------------- | ---- |
| 無規則（§二十八） | 1.037  | —        | 0.185     | 0.176       | 0/20             | 0    |
| **有規則**        | 0.9879 | 0.9678   | **0.765** | **0.805**   | **11/20**        | 0    |

**這是對 §二十八 結論的修正**：那時「大模型不如小模型」不是容量的判決，是**訓練不穩**
的產物。加上規則後，86M 在 20 epoch 追上 1.45M（TF 0.765 vs
0.785），而且第一次能吐出 **可解析的 block（11/20，之前是 0/20）**
—— 邊界模型從「不會說話」變成「說得格式對、數字還不對」。

「不過擬合」也有實測：1.45M 那輪訓練 loss 一路從 0.757 掉到 0.628，驗證 loss 卻從 0.917
**往上**爬到 0.951，第 6 個沒進步的 epoch 早停，還原 epoch 8（val
0.9112）。若照舊規則（存最後一個 epoch），交出去的會是**最過擬合**的那一個。

### 判讀

規則的價值不在「訓練得更好」，在**失敗變成可預期的形狀**：爆掉會降速、壞 batch 會跳過、過擬合會早停、學不動會在
`dynamics` 上顯示成
`firing-without-gradient`。這四件事以前都要人盯著 log 才看得到，現在是 checkpoint 旁邊的一行字。

## 三十、值介面不是「還沒學會」，是**算的**：θ 上界與介面分工

§二十九 的規則讓 86M 在 20 epoch 追上 1.45M，`format_ok` 從 0/20 變成 11/20
—— 但
**exact 仍是 0**。這節把 0 拆開：一部份是被自由參數偷走的，另一部份是介面放錯了地方。

### 3.1 逐類別 TF：0 是一個 token 種類造成的

同一個 guarded 86M checkpoint、160 列驗證資料，teacher-forced 逐 token 準確率：

| token 種類                          | 準確率    | 樣本      |
| ----------------------------------- | --------- | --------- |
| `field`（`v=`、`fatigue=` …）       | **0.998** | 480       |
| `punct`（`=`、`                     | `、換行） | **0.993** | 1605 |
| `word`（`neutral`、`math_query` …） | 0.955     | 2806      |
| `digit`（答案的數字，逐位）         | **0.084** | 403       |
| `value_atom`（`-0.14` 這類狀態值）  | **0.010** | 959       |

非數值全部 ≥0.955，數值全部 ≈ 亂猜（201 個 atom 的亂猜是 0.005）。所以「狀態 block
TF 0.805」是平均值把兩種完全不同的東西混在一起：格式全部學會了，
**數值一個都沒學會**。

### 3.2 那些數字是線性算出來的，不是猜的

把 2633 列訓練資料依 `(intent, dt)` 分格，在單一格內對六個欄位做最小平方：

- **R² = 0.9987 / 0.9987 / 0.9987 / 0.9945 / 0.9944 / 0.9951**
- 最大誤差 **0.006** —— 正好是輸入印成 2dp 的捨入量，模型本身是精確的
- 係數幾乎是對角的 `0.468 / 0.464 / 0.474 / 0.462 / 0.468 / 0.451`，加一個 bias

和 `scripts/generate_al_dataset.py` 的 `transition()` 對上了：
`out = target(intent) + (in − target) · exp(−dt/τ)` —— 對 `in` 是線性、對
`intent` 是查表、對 `dt` 是四段梯度。**這是算子，不是樣式。**

### 3.3 所以 SNN 在記場景，不是在學算子

| 實驗     | 設定                      | 訓練 value_atom                    | 驗證 value_atom |
| -------- | ------------------------- | ---------------------------------- | --------------- |
| 記憶上限 | 200 列、150 epoch         | **1.000**（loss 0.002，block 1.0） | —（同批）       |
| 泛化     | 2633 列、60 epoch、cosine | **0.471**                          | **0.035**       |

架構完全能吐對 atom（200 列時 100%），但一換資料就掉到 3.5%。也就是說它有容量
**背下** 2633 個場景，卻沒有抽出「`0.46·in + bias`」這條規則。

也排除了最直覺的解釋（梯度傳不回來）：把 leak 從 `beta=0.90` 掃到 `0.995`
（40 步前的係數從 0.0015 變成 0.82），驗證 value_atom 是 **0.021 → 0.028 →
0.006**，沒有改善 —— 不是記憶長度，是表徵裡沒有「數字」這個東西可以相加。

### 3.4 介面分工：文字歸 SNN，數值歸算子

兩件事被一個模型同時做，才會出現「格式對、數字全錯」的 0/20。分開之後各自都在行內：

| 部分              | 由誰產生                              | 量測                                                       |
| ----------------- | ------------------------------------- | ---------------------------------------------------------- |
| 回應文字 + 格式   | token SNN（guarded 86M）              | `format_ok` 11/20；欄位/標點/詞 ≥0.955                     |
| `<al_out>` 六個值 | 契約算子（`hybrid_boundary.py`，3dp） | **320/320 逐字**（`instrument.hybrid.exact_of_all = 1.0`） |

`hybrid_boundary.py --predict '<al_in> …' --checkpoint … --response-from <ck>`
會印出 `<response> …` 與 operator 算出的 `<al_out>`
block。實跑（greeting 那列）：

```
<response> -440                                   ← SNN，答案是錯的（真值 35244）
<al_out> v=0.23 a=0.36 d=0.55 … intent=math_query  ← SNN 自己接下去寫的 block（不要用）
<al_out> v=-0.137 a=-0.273 d=-0.186 fatigue=0.275 stress=0.568 health=0.463  ← 算子，與 gold 逐字相同
```

第三行才是要的。第二行是證據：SNN 會把 block 也寫出來，但值全錯 —— 所以
`--response-from` 在 `<al_out>` 處截斷，block 一律由算子寫。

### 3.5 還剩下什麼

0/20 現在只剩一個成因：**答案本身的數字**（`digit`
0.084）。那是 AI 側的算術/理解，不是 AL 的狀態介面；它和「狀態 block 要不要由算子算」是兩個獨立問題，不該再混在同一個 exact 指標裡。3dp
atom 格（0/2633 可表達）也不必修：分工後 block 由算子直接印文字，SNN 不需要吐出 3dp 數值。

### 3.6 θ 上界（順手補的那一刀）

`dynamics()` 早前指出 round-9 的門檻從 0.5 漂到 **6.75**，關掉 97% 的放電 ——
surrogate 是
`sigmoid(5·(mem−θ))`，θ 遠高於膜電位分佈時梯度就沒有了，而 loss 看起來完全正常。θ 是自由參數這件事本身就是失控源，所以給它一個上界：

- `TokenConfig.theta_max`（預設 **2.0**，0 = 關閉），`--theta-max` 對應 CLI
- 實作是**每步之後的投影**（`clamp_(0, theta_max)`），不是重新參數化：forward 路徑與既有 checkpoint 一位元都不變，只有值被關在梯度帶裡
- 驗證：兩顆模型都從 5.0 出發跑一步，`theta_max=0.8` → **0.8**（拉回），
  `theta_max=0` → 維持在帶外；小規模自然訓練 4 epoch，有界 0.79 / 無界 0.865

## 三十一、穩定結構會被訓練自己刷掉（一半對、可量、可擋）

猜想：訓練越多越容易爆，是因為過程裡學到的「穩定結構」（元胞機式的吸引子／週期）被後續的更新洗掉；若能保留，就能跑很多輪而不爆。這節把它拆成三個可量測的問題：結構真的在漂嗎、漂的方向是不是壞的、擋住它有沒有用。

### 31.1 量測方式：`scripts/probe_stability.py`

跑真實資料（200 列、120 epoch、單一 seed、d_emb 48 / d_hidden 96 /
2 層），每個 epoch 記 `beta`（膜電位洩漏）、`sr`（`w_rec`
的譜半徑）、`theta`、以及**自主軌道**：先用真資料列把狀態灌滿，然後把輸入切掉，讓遞迴自己跑，看還剩多少放電。

三個量都是「可以免費換低 loss」的自由度：θ 大→不發電、β 小→忘得快、 `sr`
大→跳過積分直接導線。

### 31.2 結果：漂移是單調的，而且發生在 loss 還在降的時候

|             | epoch 1     | epoch 120       |                             |
| ----------- | ----------- | --------------- | --------------------------- |
| `beta`      | 0.8981      | **0.8027**      | 記憶視窗 9.8 → **5.1 步**   |
| `sr(w_rec)` | 0.55 / 0.65 | **1.36 / 1.81** | 大於 1 = 擾動每步變大       |
| `theta`     | 0.487       | **0.899**       | 往 2.0 的上界爬             |
| train loss  | 3.19        | **0.666**       | 一直在降                    |
| val loss    | 3.20        | **0.9169**      | 最佳 0.8216 @ ep49 之後回升 |

也就是說：**它不是學不動，而是換了一種算法**
—— 把「積分」換成「導線」，把記憶視窗砍半，換取對這 200 列的貼合。val 的回升（末 10 個 epoch 平均 0.9105，比最佳差
**+0.089**）發生在 train 仍持續下降的時候，所以任何只看 train 的曲線都看不見。

### 31.3 擋住它：`leak_floor` + `gain_cap`

兩個都做成**投影**（跟 `theta_max`
一樣，關閉時 forward 與舊 checkpoint 一位元不變）：

- `--leak-floor 0.9`：把 `sigmoid(beta)` 夾在地板以上 → 記憶視窗不得縮短
- `--gain-cap 1.0`：`sr(w_rec)` 超過上限就整體縮放 → 擾動不得每步放大

同一組資料、同一個 seed、120 epoch：

|                       | 無控制                   | 有控制                       |
| --------------------- | ------------------------ | ---------------------------- |
| `beta`                | 0.8981 → 0.8027          | **0.9000 → 0.9000**          |
| `sr` 末期             | 1.36 / 1.81（最高 1.90） | **0.85 / 0.65**（最高 1.20） |
| train loss            | 0.6655                   | 0.7586（**較差**）           |
| val 最佳              | 0.8216 @ ep49            | 0.8253 @ **ep75**            |
| val 末期              | 0.9169                   | **0.8418**                   |
| val 末 10 平均 − 最佳 | **+0.089**               | **+0.020**                   |

**結論**：擋住漂移把「訓練 50 輪後開始變壞」變成「持平」。代價是 train
loss 較高（0.666 →
0.759）—— 那正是它原本換到的東西：對這 200 列的記憶。最佳 val 幾乎相同（0.8216
vs 0.8253），但**有控制的那次最佳出現在更晚（ep75 vs
ep49）而且之後不再崩**，這才是「多輪不爆」要的性質。

### 31.4 哪一半的猜想成立、哪一半不成立

- **「結構被刷掉」——成立，但僅指參數層面**：β 與 `w_rec`
  的增益是單調、系統性、且在 loss 改善時發生的，擋住它們就止住了退化。不是隨機亂走，也不是梯度壞掉。
- **「保留穩定結構就能多輪不爆」——在這個量上成立**（val 退化 +0.089 → +0.020）。
- **「規則沒寫好」——不成立**：guard、best-checkpoint、θ 上界都在正常工作，沒有被違反；漂移不是規則失效，是**一條沒被約束的自由度**。
- **「其他可能」——就是記憶化**：train↓/val↑ 與 §三十 的 value_atom 結論一致（2633 列訓練 0.471、驗證 0.035）；縮短記憶視窗正是最省力的記憶化路徑。

### 31.5 一個誠實的負結果：自主軌道不是判準

原本想用「切掉輸入後還剩多少放電」當作結構是否被保留的證據。實測**不行**，兩個原因：

1. `w_in` 的 bias 是常數驅動，切掉輸入後膜電位收斂到 `b/(1−β)`，即使把 `w_rec`
   完全歸零也照樣放電（測試 `test_orbit_dies_without_recurrence...`
   就是靠把 bias 也歸零才看得到靜默）。所以軌道量到的主要是**自發驅動**，不是記憶。
2. 兩組（有控制／無控制）的軌道活性都從 ~0.5 掉到 ~0.12–0.16
   —— 有控制的那組並沒有保住軌道。學著只在有資訊的 token 上放電，本來就會降低無輸入時的自發率，這是稀疏化，不是侵蝕。

因此 `summarise()` 的判定讀 `beta` 與 `sr`，`orbit`
只作診斷；只有完全靜默（`dead_at`）才算決定性證據。這一點寫進程式的 docstring，避免下一個人拿它去支持結論。

### 31.6 限制

單一 seed、200 列、小模型（48/96/2），兩個投影預設關閉。86M 的規模包絡沒有重跑；
`gain_cap` 每步要做一次收斂的 power
iteration（4096×4096 上是可觀的固定成本），上大模型前要先量。以上都寫成旗標，不改變既有行為。

### 31.7 真實語料上重做一次（800 列 / token 詞表 / 30 epoch）

小模型 probe 的結論要能在真資料上重現才算數。同一份 round7 3dp 語料，
`--vocab token`、800 列、30 epoch、d_emb 96 / d_hidden 192 / 2 層、lr 2e-3：

|                           | 無控制                | `--leak-floor 0.9 --gain-cap 1.0` |
| ------------------------- | --------------------- | --------------------------------- |
| `beta`（視窗）            | 0.8745（**7.97** 步） | **0.9003**（10.03 步）            |
| `sr(w_rec)`               | 1.49 / 1.27           | **0.64 / 1.00**                   |
| `theta`                   | 0.5518                | 0.5445                            |
| 回應 teacher-forced       | 0.340                 | 0.337                             |
| 狀態 block teacher-forced | 0.723                 | 0.728                             |

兩件事：

1. **漂移在真語料上更快**（30 epoch 就 `sr`
   1.49、視窗掉到 8 步），不是小模型假象。
2. **擋住它不傷學習** —— 回應 0.340 vs 0.337、block 0.723 vs
   0.728，在雜訊內；先前 200 列 probe 的 train
   loss 代價（0.666→0.759）正是它換掉的記憶化。

附帶量到的事：`generate()` 每個 token 重跑整段前綴（O(len²)），143
token 的列實測 ~8 s，所以 `exact_match`
的 200 列是**訓練後靜默的 25 分鐘**。現在有進度輸出與 `--match-sample`（0
= 跳過），長跑不會再看起來像卡死。

### 三十二、漂移 ≠ 僵化：把兩件事分開量

§三十一 的結論留了一個沒驗的因果假設：**結構漂移造成「越訓越差」**。同一支
`probe_stability.py`、同一份 val（最後 300 列）、同樣 seed 與超參，只改訓練列數：

| 訓練列 | epoch | `beta`（視窗）                | `sr` 末   | val 最佳     | 末期退化    |
| ------ | ----- | ----------------------------- | --------- | ------------ | ----------- |
| 200    | 120   | 0.898→**0.803**（9.8→5.1 步） | 1.36/1.81 | 0.8216 @ep49 | **+0.089**  |
| 800    | 60    | 0.890→**0.746**（9.1→3.9 步） | 1.88/2.31 | 0.7887 @ep33 | **+0.0025** |

**資料變多，漂移更嚴重，退化幾乎消失。**
兩者因此不是因果，是共現：資料太少時唯一能降 loss 的路是記憶化，漂移是那條路的副產品；資料夠時同一條路照樣走，val 卻繼續（緩慢）下降。

三個補充量測把這件事釘住：

1. **漂移被初始化錨定，不是被語料推向單一吸引子。** 初始 `beta=0.98` 訓練 30
   epoch 後只到 0.972；初始 0.9 到 0.875。回授強度 `sr` 則從 0.55 爬到 1.49+
   ——漂得最兇的是增益，不是衰減。
2. **模型有長依賴的能力，只是語料不要求。**
   合成 recall（8 符號字母表、答案為序列第一個 token、k=4 與 k=24）：`beta`
   0.9805→0.9804 / 0.9806→0.9748，幾乎不漂，val 分別到 **0.0000 /
   0.0069**。同一支模型、同樣 30 epoch。
3. **擋漂移與加記憶對準確率的影響，比對 `beta` 的影響小得多** （真語料 800 列 /
   30 epoch，teacher-forced）：

   | 設定                                           | 回應 TF | 狀態 block TF | 末 `beta` |
   | ---------------------------------------------- | ------- | ------------- | --------- |
   | `beta=0.9` 無控制                              | 0.340   | 0.723         | 0.875     |
   | `beta=0.9` + `--leak-floor 0.9 --gain-cap 1.0` | 0.337   | 0.728         | 0.900     |
   | `beta=0.98` 無控制                             | 0.304   | 0.733         | 0.972     |
   | `beta=0.98` + `--leak-floor 0.95`              | 0.302   | 0.733         | 0.973     |

   逐類別（同 200 列 val）：標點 0.99、詞 0.96（`beta=0.98` 時 **0.999**）、數字
   **0.45**（`beta=0.98`
   0.443）。數字占答案 token 約 54%，所以「回應 0.30-0.34」其實是數字介面的天花板，不是記憶或漂移。

**應用的三個結論**

1. `probe_stability.py`
   當訓練前體檢：它會說漂到哪、val 從哪個 epoch 開始回頭。但**漂移本身不是停手訊號**——800 列那組漂得更多而 val 沒壞。
2. 只有「資料少到 val 不可信」時，兩個投影（`--leak-floor` /
   `--gain-cap`）才值得開；它們的代價是把記憶化那部分的 loss 拿掉（200 列 train
   0.666→0.759）。
3. `beta`
   是**要照任務設的超參**，不是讓優化器挑的旋鈕：詞的長距離複製 0.959→0.999 變好，回應 0.340→0.304 變差；尾端 block
   0.723→0.733 變好。

**下一步該攻的不是漂移，是數字。**
回應的瓶頸在 0.45 的數字準確率，而這在 §三十的值介面已經記錄過同一個洞（`value_atom`）。把算力花在 anti-drift 上，量到的收益是 ±0.003；花在值介面上，上限是 +0.2 以上。

限制：單 seed；≤2633 列；d_emb 96 / d_hidden 192 / 2 層。86M 未在此輪重跑。

### 三十三、把四個槓桿都拉一遍：epoch、資料量、容量、表示

§三十二 說漂移不是瓶頸、數字才是。這輪就照那條線把四個能動的槓桿各拉一次，量的是
**同一份 val（round-7 3dp，前 200 列）**、teacher-forced，並補上 teacher-forced
**逐欄位精確率**（六個 `k=v` 全部字元相符才算對；3 位小數，錯一位就整欄錯）。

| 語料 / 列            | epoch  | 模型 d/layers | 數值表示     | 回應 TF   | block TF  | block 精確 | 回應精確 |
| -------------------- | ------ | ------------- | ------------ | --------- | --------- | ---------- | -------- |
| 3dp 800              | 30     | 96/192/2      | 逐字         | 0.340     | 0.723     | 0.08%      | 0/200    |
| 3dp 800              | **90** | 96/192/2      | 逐字         | 0.337     | 0.726     | —          | —        |
| 3dp 2000             | 30     | 96/192/2      | 逐字         | **0.362** | 0.725     | 0.25%      | 1/200    |
| 3dp 2000             | 30     | **192/384/3** | 逐字         | 0.355     | 0.722     | 0.08%      | 2/200    |
| 3dp 800              | 30     | 96/192/2      | **3dp 原子** | 0.319     | **0.814** | 0.25%      | 0/200    |
| 3dp 2000             | 30     | 96/192/2      | 3dp 原子     | 0.342     | 0.819     | 0.08%      | 0/200    |
| 3dp 2000             | 30     | 192/384/3     | 3dp 原子     | 0.335     | 0.821     | 0.17%      | 0/200    |
| r8 14751（混合長題） | 4      | 96/192/2      | 3dp 原子     | 0.290     | 0.802     | —          | —        |

四個槓桿各自的結論：

1. **epoch 沒用**：30 → 90 輪，回應 0.340 → 0.337、block 0.723 → 0.726。
2. **資料量有一點用，很小**：800 → 2000 列，回應 +0.022（0.340 → 0.362）。
3. **容量沒用**：4 倍參數量（d 96/192/2 → 192/384/3），回應 0.362 →
   0.355，在雜訊內；而且 2000 列上 train 0.33 / val 1.78
   = 開始記憶化而不是變強。
4. **表示有用，但只對 block 的 token 準確率**：`--numeric-atoms --value-decimals 3`
   讓 `0.261` 由 6 個 id 變 1 個原子，block token 準確率 0.723 →
   **0.814**；逐欄位精確率仍是 0.1-0.25%。

**最重要的一條：逐 token 準確率不是可用性指標。**
0.72-0.82 的 token 準確率對應的是 **0.1-0.25% 的逐欄位精確率**與
**0-2/200 的回應精確率**——3 位小數的值要每個字元都對，錯誤高度相關，於是「八成 token 對」等於「幾乎沒有一次全對」。§三十一、三十二 都用 token 數字描述趨勢，那是對的；但任何「能不能用」的判斷都必須讀精確率。

**要真的能用，只有兩條路，而這輪把其中一條排除掉了：**

- ❌ 把模型放大／訓久／餵更多同分布資料：三個都量了，擋住的不是這些。
- ✅ 把算術交給算子（§三十 的 hybrid，3dp
  320/320），網路只負責它能做的部分（格式、block 佈局、路由；block token
  0.81）。

r8 語料是這輪現做的：`generate_al_dataset.py --rows 24000 --skip 8000 --id-prefix r8_ --expose-dt` +
`prepare_ai_al_training_data.py --decimals 3`，19,252 訓練列。它在
`--max-len 256` 下只有 14,751 列可容納，而且 4 epoch 後 train
loss 仍 2.37（窄語料同期是 0.87）——**同一個網路吃不下自然語言題目**，這也解釋了為什麼「像本地 LLM 一樣能用」在這個規模不是訓練次數的問題。

限制：單 seed；teacher-forced（非自由生成）；精確率用 200 列 val；r8 只跑 4
epoch。

#### 33.1 那「能用」了嗎？— 用 653 列 val 直接量生產路徑

上面說該把算術交給算子。這不是建議，是**現況已經如此**，而且路徑就在生產程式碼裡：

| 輸出的一半        | 走的東西                                                   | 準確率（round-7 3dp val, 653 列）                                          |
| ----------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| 回應（算式結果）  | `ai/arithmetic/deterministic_router.try_deterministic`     | **653/653 = 100%**（值是對的；回傳格式是 `267 * 132 = 35244`，不是裸數字） |
| `<al_out>` 六個值 | `scripts/hybrid_boundary.py`（table 0.80 ∪ operator 0.60） | **200/200 = 100%** 逐字                                                    |

所以這個語料任務今天就能「正常用」，而且是**比 LLM 更準**（LLM 算 2531×796 會錯，這裡不會）。SNN 在這兩半的貢獻是 0/200
—— 它現在的價值不在算，而在 SNN 擅長的部分（格式、block 佈局、路由；block token
0.81）。

一句話總結這三節的關係：**漂移不是病（§三十二），token 準確率不是可用性（§三十三），而「能不能用」早就不是模型問題，是哪一半交給誰的問題（33.1）。**

## 三十四、把「規模」這個槓桿真的拉滿：108.6M 參數的 XPU 訓練

§三十三 的結論是「把模型放大、訓久、餵更多同分布資料，三個都量了，擋住的不是這些」。但那時最大只到 86M／3.5M 的 checkpoint，而且沒有一次是「≥10⁸ 參數、完整跑完、再用同一批凍結題目量」。這節把那條做完：

| 項目                | 值                                                                    |
| ------------------- | --------------------------------------------------------------------- |
| 參數                | **108,583,431**（d_emb 512 / d_hidden 2560 / 1 layer / vocab 32,773） |
| 語料                | 149,489 列，`max_len 192` 下可容納 138,671 列                         |
| 設定                | batch 4、lr 1e-3、**1 epoch**、XPU（Arc B570）                        |
| 訓練時間            | 6,677 s（約 1.9 h）；總流程 6,755 s                                   |
| train loss          | **2.3623**（1 epoch；3.5M 版 5 epoch 是 2.05）                        |
| dynamics            | `alive`（spike rate 0.0816、threshold 1.9995、mem_abs_mean 24.99）    |
| 回應 teacher-forced | **0.4215**                                                            |
| 自由生成 exact      | train 6/100、val **8/100**（7197 列 val 的隨機 100 列）               |

### 34.1 那 8% 是什麼？— 不是算術，也不是知識

把 val 的 100 列命中逐一印出來，8 個命中是：

- 5 句比較句（`giraffe is shorter than turtle.`、`Oscar is faster than billionaire.`、
  `train比高铁矮`、`Heidi比故宫小`、`Jerry is poorer than 小红.`）；
- 3 個 `False`。

也就是說，模型學會的是**比較句的格式與兩個實體的次序**，以及分類題最常見的單字答案；它沒有學會算術或事實。拿同一份 val 的**前 200 列**（不是隨機抽樣）量，是 0/200。8% 不是「開始會推理」，是**模板回想的低標**。

### 34.2 凍結題目：仍然是 0，而且不是「沒回答」

`scripts/probe_core_control.py --token-checkpoint token_snn_108m.pt`（115 題、同一條嚴格評分）：

| 套件      | n   | TOK-SNN 正確       | 有回答 | distinct（不同答案數） | LLM 對照 |
| --------- | --- | ------------------ | ------ | ---------------------- | -------- |
| math      | 40  | **0/40**           | 37/40  | 19                     | 27/40    |
| knowledge | 15  | **0/15**           | 15/15  | 9                      | 11/15    |
| code      | 10  | **0/10**           | 6/10   | 5                      | 9/10     |
| routing   | 10  | 0/10（表現層任務） | 9/10   | 6                      | 0/10     |

「有回答」很高、`distinct`
也不低（不是同一個字串重播），所以 0 分不是 coverage 或單一模式崩潰造成的：它真的在生成不同句子，只是句子不對。數學題的典型輸出是
`12`（3+5×2 應為 13）、`120`（2¹⁰ 應為 1024）、
`The sum of 10 is 10.`（不同物理題共用同一個罐頭句）；知識題是
`The common price of the sentence is "".`。這是**語言模型式的模板坍縮**，不是「還沒接上生產路徑」。

### 34.3 判讀（照實）

- **規模槓桿已拉滿並量測**：108.6M 參數、完整 1 epoch、XPU、同一批凍結題目 →
  **核心分仍是 0.00/10**。
- **但這不是「規模無效」的證明**：loss 2.3623 還在 3.5M 版 5
  epoch（2.05）之上，1 epoch 明顯未收斂。可誠實說的只有「**在這個預算（1 epoch ×
  149k 列）下，規模沒有把 0 變成非 0**」。
- **下一個能動的槓桿不再是「更大」**：同樣的錢拿去多跑 2-3 個 epoch 會先看到 loss 下降；但 §三十三 的 3.5M 版在 5
  epoch 後仍是 exact 0，且算術連記憶都做不到（30k 算術 40 epoch train_exact
  0.005）。要跨過外部及格線，剩下的是**蒸餾**（從會做的 LLM 學下一個 token），不是再把同一個目標函式放大。
- **生產路徑不變**：token-SNN 沒有接進聊天路徑（接上去只會讓每個回答變差）。核心「缺席」與「答錯」分開記錄：census
  0/49 由模型產生；探針 0/65 由模型答對。

量測的配套修正：`report_intelligence.py --core-checkpoint` 現在把探針結果寫到
`core_control_<checkpoint>.json`，不再覆蓋生產用的
`core_control.json`——否則下一次 `--from-cache`
會把別顆模型的數字當成上線核心的分數（這正是本節要防的誤判）。

## 三十五、訓練地基的驗證：資料對得上、記得住、學得會（2026-11-12）

在做任何架構／規模比較之前，先確認「地基」不是壞的：訓練資料與凍結測試題是否在**同一件事**上、標籤是否同一條規則、管線是否真能把一個小集合訓練到 100%、以及單一算子是否學得起來。全部重跑、不引用舊值。

### 35.1 資料：標籤、表面形式、洩漏

新增 `scripts/prepare_arithmetic_task.py`（規則單一來源在 `scripts/arithmetic_task.py`），輸出 `apps/backend/data/processed/arithmetic_plain/`＋manifest（來源與輸出 sha256、每個計數、算子與位數覆蓋、洩漏檢查），並可用 `--check` 重驗。

| 項目 | 結果 |
| --- | --- |
| 原始 30,000 列 | 28,790 列（train 27,362 / val 1,428） |
| 裝飾句（`… =`／`equals`／`calculate`／`what is`） | 16,054 列全部**改寫成純算式**（不是丟掉：`2位數 - 1位數` 這個測試形狀只存在於裝飾句） |
| 標籤 | 5,056 列正規化；**全部是除法格式**（`17` → `17.0`），數值不合 0 列 |
| 重複 | 1,190 列 |
| 洩漏 | 16 列精確、4 列可交換（`+`/`*`）等價，全部**只從訓練移除** |
| 凍結測試 2,000 列 | 2,000/2,000 與正規化規則一致（不一致就拒絕執行，不改測試檔） |
| 位數形狀覆蓋 | 四個算子的測試形狀全部被訓練覆蓋（`+`/`*` 以可交換比較） |

先前 curriculum 的洩漏守門只比對**字串完全相同**，因此漏掉 `3 + 4` vs `4 + 3`（0–99 有 4 對、0–999 有 499 對）。現在兩處共用同一條 `problem_key`（`+`/`*` 可交換，`-`/`/` 不行）。

### 35.2 管線：記得住，且可重現

- **記憶檢查**（32 列、token 詞表、160 epoch、`d_hidden=128`）：loss 10.4 → **0.0031**、**train_exact 32/32 = 100%**。這證明分詞／遮罩／解碼不是壞的；它**不是**技能分數。
- **可重現**：同一個 `--seed` 連跑兩次，loss 曲線逐位相同、eval 也相同。先前 curriculum 只固定了 batch 順序，沒有固定初始權重（`TokenSNN()` 吃全域 RNG），所以每次都是不同初始化；已補 `--seed`（建模型前 `torch.manual_seed`）。

### 35.3 單一算子：加法 0–99 學得起來

char 詞表、9,000 訓練 / 1,000 held-out、100 epoch（`scripts/train_token_snn_curriculum.py`）：

| seed | held-out 0–99 exact |
| --- | --- |
| 0 | 0.677 |
| 1 | 0.683 |
| 2 | 0.677 |

**誠實更正**：script 文件裡的 77% 是**單次未固定種子**的結果；未固定種子的另一次重跑是 58.7%。固定種子後三個 seed 是 **67.7–68.3%**，這才是可重現的值。另外，凍結測試的 `+` 列只有 0–0.5%：stage A 從未看過 2–3 位數運算元，這是**位數泛化**（stage B）的缺口，不是同一個問題。

### 35.4 兩種規模的管線煙霧測試（乾淨 4 算子資料、2 epoch）

| 規模 | 參數 | eval_tf | train_exact | 時間 | 動力學 |
| --- | --- | --- | --- | --- | --- |
| `d_hidden=256` | 0.10M | **0.431** | 0.030 | 32 s | beta 0.8425、near 0.0066、sens 0.1667 → 過 |
| `d_hidden=2048` | 4.47M | 0.375 | 0.000 | 40 s | beta 0.8254、near 0.0004、sens 0.0246 → 梯度帶仍冷 |

判讀：管線在兩個規模都能跑完並存檔；但**等 epoch 對大模型不公平**（2 epoch 時大模型還在暖機，梯度帶沒開）。之後的 SNN vs GRU 比較必須先登記「等步數／等算力」或固定暖機，不能拿等 epoch 當公平。

### 35.5 舊 checkpoint 的處置

`token_snn_108m.pt` 的 `beta=0.5407`（記憶視野約 2 token）、`near_threshold=0.0014`（梯度帶幾乎關閉）：**不作為任何續訓或比較的基底**，新實驗一律從頭訓練。readiness probe 的兩個 FAIL 是對這顆舊產物的正確判讀，不是新管線的缺陷——同一條量測下，新的 0.10M 煙霧 checkpoint 是 `beta=0.8425`、`near=0.0066`、`sens=0.1667`。

蒸餾管線本身（teacher 對齊、cache 綁定、可微、loss 下降）在 readiness probe 是 PASS；但「有沒有品質增益」仍未建立，維持獨立第二實驗，不在這輪混入。

## 三十六、SNN vs GRU：預先登記的對照（2026-11-12）

前面的量測回答的是「token-SNN 在這個任務上能不能學」（能，但只限加法 0–99），還沒有回答下一個問題：
**核心 0% 是因為 spiking 架構不適合序列生成，還是因為規模／預算不足？**

在動架構之前，先做一個可裁決的對照：同一個任務、同一份資料、同一種表徵、同一個目標函式、同樣的優化步數下，
把遞歸單元換成同參數量的 GRU。如果 GRU 在這個預算下也學不起來，換架構就不是缺口所在；如果 GRU 明顯更好，
那就必須承認「架構」是一個真變因，而不是用「再大一點」把它蓋過去。

**這一節的設計在執行前寫定。** 結果另列 36.5；量測後只填數字，不改任務、不改切分、不改指標、不改判定規則。

### 36.1 任務與資料（凍結）

- 任務：`a + b`，`a, b ∈ [0, 99]`，純算式表面 → 十進位答案（`37 + 58` → `95`）。
- 池子：列舉全部 10,000 對，用 `scripts/arithmetic_task.py` 的 `problem_key` 對
  `arithmetic_test_dataset.csv` 洩漏守門（`+` 可交換）。凍結測試檔不改。
- 順序與切分：**按 `problem_key` 分組**（`3 + 4` 與 `4 + 3` 是同一個練習，兩者必須留在同一側），
  `Random(0)` 打亂 key 群組，依序把整組放進訓練集直到再加一組會超過 9,000，其餘全部為 held-out。
  兩種順序都留在同一側，所以 held-out 量的是「沒見過的運算元對」，不是「同一對的反向」。
- **初稿修正（執行前、尚未量測時發現）**：初稿寫的是「打亂 10,000 列，前 9,000 列訓練」。
  但 `+` 可交換，列切分會讓約九成的 held-out 配對，其交換孿生落在訓練集裡——
  那不是 held-out，是同一題的反向。改成 key 群組切分後：池子 9,992（8 列對凍結測試洩漏）、
  train 9,000、held-out 992。此修正在任何分數產生之前完成，判定規則不變。
- 詞表：`CharVocab.build` 在整個池子上建一次，四個臂**共用同一個物件**
  （`d_emb=96`、`max_len=24`、`TokenConfig` 預設 `min_count=2`／`max_vocab=12000`）。
  實測 `len(vocab)=17`（數字 10、空白、`+`、換行、四個 special）。報告要記 `len(vocab)` 與 token 清單。
- 為什麼是這個任務：§35.3 是唯一一個 SNN 被量到會學的任務（種子 0/1/2 → 67.7–68.3%）。
  混合 30k 四算子集已知在 loss ~1.70／0% 平台，不能當第一個對照。

### 36.2 四個臂與參數配對規則

| 臂 | 遞歸單元 | 隱藏維度 | 參數量（預估） |
| --- | --- | --- | --- |
| `snn_small` | LIF（`TokenSNN` 現況，`readout=membrane`） | 256 | 96,883 |
| `snn_large` | 同上 | 2048 | 4,433,523 |
| `gru_small` | `nn.GRU` | 134 | 97,191（差 0.32%） |
| `gru_large` | `nn.GRU` | 1165 | 4,435,639（差 0.05%） |

- GRU 臂沿用 `TokenSNN` 的**同一個** `CharVocab`、`make_batch`（同樣的 padding／mask）、
  `loss`（同樣的 shifted CE 與遮罩）、`train_on`（同樣的 shuffle／Adam／grad clip）、
  `generate`（同樣的 greedy 解碼）。只有 `net` 被換掉：同樣的 `nn.Embedding(d_emb=96, padding_idx=PAD)`、
  同樣的 `head`，中間是 `nn.GRU(96, d, batch_first=True)`。
- 參數配對規則（先寫定，後搜尋）：對每個 SNN 臂的實際參數量 `N_snn`，在整數 `d` 上選
  `argmin |N_gru(d) − N_snn|`，其中 `N_gru(d)` 是完整模型（embedding＋GRU＋head）的參數量。
  配對誤差必須 ≤2%，否則該規模不進入判定。**任何臂不得在看到分數後調整大小。**
- 兩邊都不使用 KD、scheduled sampling、tail weight、課程或額外正則。

### 36.3 預算（等步數，不等 epoch）

- 每臂：`16 epochs × 141 batches`（9,000 / 64）＝ **2,256 個優化步**，batch 64。
- 優化器：Adam，`lr=5e-3` 常數，梯度裁剪 1.0，`guard=True`（兩邊相同；rollback 與實際 lr 要記進報告）。
- 為什麼不等 epoch：§35.4 顯示 2 epoch 時 4.47M 的 SNN 還在暖機（梯度帶仍是冷的）。
  等 epoch 會拿「暖機中的大 SNN」去比「已收斂的小 GRU」，比的不是架構。
- 裝置：兩邊都 `auto`（本機解析到 XPU）；同一台機器、同一天、依 seed 交錯執行四個臂，
  避免把機器狀態的漂移算成架構差異。
- 種子：**0–4，共 5 個，配對**（同一個 seed 餵給初始化與 batch 順序）。
  「配對」指同一個種子，不是同一組初始權重（架構不同，權重不可能相同）。

### 36.4 主要指標與判定規則

- **主要指標**：held-out 全部配對的 **greedy exact match**（temperature 0，答案字串完全相等）。
- 次要指標（只描述，不參與判定）：teacher-forced token 準確率、訓練集 200 對的 exact、
  loss 曲線、實際參數量、每步秒數、總秒數。
- 判定（每個規模分開做）：對每個 seed 算 `d_s = exact_snn(s) − exact_gru(s)`；
  取 5 個 `d_s` 的平均與 **95% t 信賴區間（df=4）**。
  - 區間完全 >0 → 此預算下 SNN 較好；
  - 區間完全 <0 → 此預算下 GRU 較好；
  - 區間含 0 → **此預算下測不出差異**（不是「一樣好」，是解析度不夠）。
- **可學性前置條件**：若某規模兩個臂中最好的 held-out exact < 0.10，該規模記為
  **inconclusive（兩邊都沒學會）**，不得解讀成「平手」，也不得因此宣稱架構無關。
- 不做的事：不刪種子、不重跑、不看結果換指標、不把 held-out 併回訓練、不調 `lr`／epoch 追分。

### 36.5 結果（2026-11-12，實跑 680.8 s）

設定照 36.1–36.3，**執行中與執行後都沒有改任何一項**。完整輸出在
`data/intelligence_reports/snn_vs_gru.json`（`data/` 不進版控；同一條指令可重跑）。

**主要指標：held-out 992 對的 greedy exact（5 個種子，配對）**

| 規模 | SNN 平均 | GRU 平均 | 配對差（SNN−GRU） | 95% t 區間（df=4） | 判定 |
| --- | --- | --- | --- | --- | --- |
| small（96,883 / 97,191 參數） | **0.3486** | **0.6798** | −0.3313 | [−0.4330, −0.2295] | **GRU 較好** |
| large（4,433,523 / 4,435,639 參數） | **0.0111** | **0.8058** | −0.7948 | [−0.9376, −0.6519] | **GRU 較好** |

逐種子（small，SNN / GRU）：0.364/0.579、0.299/0.643、0.387/0.795、0.336/0.739、0.357/0.643。
逐種子（large，SNN / GRU）：0.012/0.702、0.006/0.700、0.008/0.963、0.017/0.785、0.012/0.880。

**次要指標（5 個種子的平均）**

| 臂 | held-out exact | held-out tf | train-200 exact | 訓練秒數（2,256 步） |
| --- | --- | --- | --- | --- |
| `snn_small` | 0.3486 | 0.7585 | 0.374 | 34.2 s |
| `gru_small` | 0.6798 | 0.9016 | 0.791 | 18.1 s |
| `snn_large` | 0.0111 | 0.4733 | 0.011 | 39.3 s |
| `gru_large` | 0.8058 | 0.9403 | 0.863 | 30.0 s |

- 守門（`guard=True`）在 20 個 run 中只觸發一次：`gru_large` seed 2 rollback 1 次、lr 5e-3 → 2.5e-3，
  該 run 仍到 0.963。兩邊規則相同，沒有因此改變判定。
- 每臂都跑滿 2,256 步（`skipped=0`）。

### 36.6 判讀與限制

1. **判定照規則**：兩個規模都是 GRU 較好，且區間離 0 很遠——不是「解析度不夠」。
2. **大 SNN 不是泛化差，是根本沒擬合**：`snn_large` 的 train-200 exact 只有 0.5–2.5%，
   held-out 0.6–1.7%，teacher-forced 也只有 47%。反過來，`snn_small` 的 train（37.4%）
   與 held-out（34.9%）幾乎相同：它在擬合訓練集的一個子集，不是在背題。
3. **規模不是瓶頸**：多 45 倍參數的大 SNN 比小 SNN 還差（0.011 vs 0.349）。這與 §35.4
   「2 epoch 時 4.47M 的梯度帶是冷的」是同一個缺陷，且 16 epoch（2,256 步）仍然冷
   （tf 0.47 vs 小模型的 0.76）。
4. **等步數沒有偏袒 GRU 的算力**：SNN 每步更貴（34.2 s／39.3 s vs 18.1 s／30.0 s），
   GRU 用更少的時間做到更多。
5. **不能拿這次的 0.35 去和 §35.3 的 0.68 比**：那次是 14,100 步、`d_hidden=192`、
   列切分（held-out 約九成含交換孿生）。這次是它的 16% 步數、按 key 群組切分。
   0.35 不是退步，是不同問題上的另一個數字。
6. **限制**：只有一個任務（加法 0–99）與一個預算（2,256 步）。而且 SNN 兩臂在 2,256 步內
   都沒有把訓練集擬合好（train-200 exact：37% / 1%），所以這次比的是「固定預算下各自達到什麼」，
   **不是**「同樣擬合度下誰泛化得好」。這不證明 SNN 做不到，只證明「在這個實作、這個預算、
   這個任務」下，換成 GRU 會好很多。要推翻它，得先修好大模型的暖機／梯度帶，再用一份**新的**
   預登記重測——不是把這次的門檻往後挪。
7. **核心分不變（0.00/10）**：這是診斷實驗，不是把 GRU 接進生產。生產聊天路徑仍然沒有
   核心模型；把 GRU 接上去會讓分數好看，但那是換了一個非核心的模型，不是補上核心。


## 三十七、AI+AL 單一核心：T1–T6 的預先登記（2026-11-12，量測前寫定）

> **這一節是在跑任何訓練之前寫的。** 下面的資料、預算、指標與門檻一旦寫下就不再改；
> 結果接在 §37.6（同一天稍後），失敗就照實記，不改門檻、不在 held-out 上調任何東西。
> 契約本身是 `AI_AL_SINGLE_CORE_CONTRACT.md`；這一節只回答一個問題：
> **在一個時間會作用在狀態上的最小任務裡，`ai_step`／`al_step` 共用同一份權重與同一個
> state 時，模型是否真的在用 state。**

### 37.1 要證偽的宣稱

宣稱（可證偽）：`al_step(dt)` 把時間推進到同一個 recurrent state，之後的 `ai_step`
讀到的 state 帶著「距離上一次教導過了多久」的資訊；把 state 歸零，答案就會掉回猜測。

反面（必須能區分）：一個**不靠 state、只靠 context** 的解法（把經過時間當成輸入
token 附在問題上）也會答對，但它對 state ablation **不敏感**——如果我們的測試對它也
「有下降」，那測試就沒有鑑別力，先修測試，不是先慶祝。

### 37.2 任務（合成、控制變因，不是能力考試）

每個 session 是一段多回合對話，答案都是單一 token：

```
回合 1（教導）：  <remember> <key> <value>
回合 2–4（間隔）： al_step(dt) → <talk>
回合 5（時間題）： al_step(dt) → <bucket?> <q_time> → <valid> / <expired>
回合 6（內容題）：               <bucket?> <q_key>  → <value> / <unknown>
```

- 詞表 **26**：`<pad>`、`<remember>`、`<talk>`、`<q_time>`、`<q_key>`、
  `<valid>`、`<expired>`、`<unknown>`、`<bucket_short>`、`<bucket_long>`、
  8 個 `<key>`、8 個 `<value>`。chance：時間題 **1/2**、內容題 **1/9**、兩題都對 **1/18**。
- **為什麼要兩題**：如果只問「剛才教的值是什麼」，歸零 `h` 會同時毀掉內容與時間，
  hand-state 對照組就無法分離。時間題的答案只取決於「過了多久」，內容題只取決於
  「教了什麼」；T1 與 T2 才有鑑別力。
- `<bucket?>` 在**核心臂固定是 `<pad>`**（不提供任何時間資訊），在 hand-state
  對照臂才是 `<bucket_short>`／`<bucket_long>`。兩臂的架構、詞表、序列長度完全相同，
  只差「時間從哪個通道進來」。
- 時間規則：從教導到提問的累積間隔 `T`；`T ≤ 240 s` → `<valid>`，`T > 240 s` →
  `<expired>`（內容題在過期時答 `<unknown>`，不是回舊值）。
- `T` 的抽樣：一半 session 抽 `U(0, 200)`（可回答），一半抽 `U(280, 400)`（過期）；
  再把 `T` 隨機切成 4 段當作 4 個 `dt`（每段都 > 0）。刻意留 200–280 的空隙：這是
  一個**機制測試**，量的是「時間有沒有進 state」，不是邊界泛化。
- 資料量：train **4,000** sessions、held-out **1,000** sessions，**依 session 切分**
  （同一 session 的回合不跨兩邊）；資料種子 `1000 + seed`，模型種子 `seed`。
- `dt` 一律以 `al_step` 進入模型；`ai_step` **不看時間**。

### 37.3 模型與訓練（固定）

| 項目 | 值 |
| --- | --- |
| 遞歸 | 單層 `GRUCell`，`d_hidden = 64`，`d_emb = 32` |
| 時間輸入 | `Linear(1 → 32)` 作用在每個 chunk 的正規化 dt（`chunk/60`） |
| chunk | `al_step` 把**每個樣本**的 dt 切成 `ceil(dt/60)` 段，每段 `dt/n` 秒；同一個 batch 內樣本段數不同時，先用完的樣本**不再更新**（不是補零輸入——補零會無故改 `h`） |
| `dt ≤ 0` | 回傳**同一個 state（逐位恆等）**；`ticks` 不動 |
| 共用 | `ai_step` 與 `al_step` 用**同一個** `GRUCell`（同權重）；時間只是不同的輸入投影 |
| 優化 | Adam，lr **5e-3** 常數，grad clip 1.0 |
| 批次 | **64** sessions；BPTT 貫穿整個 session（不截斷） |
| epochs | **30** |
| loss | 時間題＋內容題的 cross-entropy（等權重相加）；**第一輪不使用 `L_al`** |
| 評估 | 貪婪 argmax，exact match；時間題／內容題分開報，各再分「可回答／過期」兩半 |

**第一輪不用 `L_al`** 是刻意的：如果連「答案要靠 state 才對」的 CE 都無法逼模型用
state，那再加一個自我預測 loss 只會讓結果更難解讀。`L_al` 是 T1 沒過之後的下一步。

### 37.4 六個測試與對照（預先登記）

| # | 變體 | 做法 |
| --- | --- | --- |
| T1 | ablation | 兩題之前把 `h` 歸零，其餘不變 |
| T2 | hand-state | 另一臂：不用 `al_step`，時間改成 `<bucket_short>`／`<bucket_long>` 放在兩題前面 |
| T3 | retention | 主臂的準確率（context 不含前面回合） |
| T4 | restart | 教導＋間隔後把 state 存檔／載回 → 續跑兩題，比對時間題的機率 |
| T5 | cycle switch | (a) 不跑 `al_step`；(b) gaps 跨 session 打亂；(c) 假時鐘（每段固定 30 s → `T=120`） |
| T6 | provenance | 記錄 `weights_hash`、`state_version`、`ticks`、`route`；核心臂的 token 序列不得含任何 bucket token |

### 37.5 通過條件（寫死；5 個種子 0–4 的平均）

| # | 指標 | 通過條件 |
| --- | --- | --- |
| T3 | 主臂 | 時間題 ≥ **0.90**、內容題 ≥ **0.85**；且兩題在「可回答／過期」各自的準確率都 ≥ **0.85** |
| T1 | 歸零 `h` | 時間題 ≤ **0.65**（chance 0.5）、**內容題（可回答半）≤ 0.30**（chance 1/9）、時間題下降 ≥ **0.30**（絕對） |
| T4 | 重啟 | 200 題時間題的最大機率差 ≤ **1e-5** |
| T5 | 不跑 `al_step` | 時間題 ≤ **0.65**，且相對主臂下降 ≥ **0.30** |
| T5 | 打亂 gaps | 整體（兩題都對）≤ **0.70** |
| T5 | 假時鐘（30 s×4 = 120 s） | 過期半的時間題 ≤ **0.30**（方向：它會把過期當成可回答） |
| T2 | hand-state 臂 | 時間題 ≥ **0.90**；歸零 `h` 後時間題變化 ≤ **0.05**；bucket 改成 `<pad>` 後時間題下降 ≥ **0.30** |
| T6 | provenance | `weights_hash` 在評估前後一致；`state_version`／`ticks` 有單調記錄；核心臂 token 序列無 bucket token |
| 附加 | `dt = 0` | 與原 state **逐位相同** |
| 附加 | 半群（量測，不是門檻） | `al_step(30)+al_step(30)` 與 `al_step(60)` 的 `h` 差**照實報**；不列入通過條件（見下） |


**預登記修正（在跑登記 run 之前；只跑過 1 epoch 的煙霧測試）**：T1 原本寫「內容題 ≤0.35」，
但內容題的**常數答案基線是 0.5**（永遠答 `<unknown>` 就對一半的過期 session），所以那個門檻
會把「只會答 `<unknown>`」誤判成失敗。改成量**可回答半**（基線 1/9）≤0.30。這是修正一個
量測缺陷，不是放寬門檻：時間題與下降幅度都沒有動。

**半群為什麼不是門檻**：`al_step` 把時間切成等長段，30+30 是兩個 `0.5` 的輸入，
60 是一個 `1.0` 的輸入；GRU 是非線性遞歸，兩者本來就不會逐位相等。AL ladder r1
的精確半群是**閉式積分器**量到的，不能拿來要求一個學出來的 recurrence。第一輪沒有
訓練 `L_al`，所以這一項只量、不判。

**判定規則**：九項全過＝「這個合成任務上，state 被 `al_step` 使用且可被 T1 偵測」；
任一項不過＝照實記為該項失敗，**不改門檻重跑**。要改設計，必須另寫一份新的預登記。

### 37.6 結果（2026-11-12，登記 run 實測；未改任何門檻）

登記參數：5 個種子（0–4）、4,000／1,000 sessions、30 epochs、batch 64、lr 5e-3、
GRU `d_hidden=64`／`d_emb=32`、**21,402 參數**、chunk 60 s。整輪 **102.9 s**（CPU）。
完整輸出：`data/intelligence_reports/probe_state_cycles.json`（`data/` 不進版控）。

**主臂與對照（5 種子平均 ± 95% t 半寬，df=4）**

| 條件 | 指標 | 結果 | 預登記門檻 | 判定 |
| --- | --- | --- | --- | --- |
| 主臂 | 時間題 | **0.9998 ± 0.0006** | ≥ 0.90 | PASS |
| 主臂 | 內容題 | **0.9998 ± 0.0006** | ≥ 0.85 | PASS |
| 主臂 | 兩題都對 | **0.9998 ± 0.0006** | — | — |
| 主臂 | 可回答／過期（時間題） | 0.9996／1.0000 | 各 ≥ 0.85 | PASS |
| 主臂 | 可回答／過期（內容題） | 0.9996／1.0000 | 各 ≥ 0.85 | PASS |
| T1 歸零 `h` | 時間題 | **0.5092 ± 0.0141** | ≤ 0.65 | PASS |
| T1 歸零 `h` | 內容題（可回答半） | **0.0785 ± 0.0894** | ≤ 0.30 | PASS |
| T1 下降 | 時間題 | **0.4906** | ≥ 0.30 | PASS |
| T5 不跑 `al_step` | 時間題 | **0.5092 ± 0.0141**（下降 0.4906） | ≤ 0.65／下降 ≥ 0.30 | PASS |
| T5 打亂 gaps | 兩題都對 | **0.4934 ± 0.0147** | ≤ 0.70 | PASS |
| T5 假時鐘（30 s×4） | 過期半時間題 | **0.0000 ± 0.0000** | ≤ 0.30 | PASS |
| T2 hand-state | 時間題 | **1.0000** | ≥ 0.90 | PASS |
| T2 hand-state 歸零 `h` | 時間題變化 | **0.0000** | ≤ 0.05 | PASS |
| T2 拿掉 bucket token | 時間題 | **0.5056 ± 0.0217**（下降 0.4944） | 下降 ≥ 0.30 | PASS |
| T4 重啟 | 200 題最大機率差 | **0.00e+00** | ≤ 1e-5 | PASS |
| T6 provenance | `weights_hash`／token | 前後一致；核心 token 只有 `{PAD, Q_TIME}` | 一致／無 bucket | PASS |
| `dt = 0` | `h` 與 ticks | **逐位不變** | 恆等 | PASS |
| 半群（只量） | `al_step(30)+al_step(30)` vs `al_step(60)` | **0.7588 ± 0.3732** | 不判 | 照實記 |

逐種子（主臂 時間題／內容題）：1.000/1.000、1.000/1.000、1.000/1.000、0.999/0.999、
1.000/1.000。歸零後時間題：0.504／0.499／0.504／0.528／0.511（= chance 0.5）。

**判定：17 項預登記檢查全過。** 這是「在這個合成任務上，state 被 `al_step` 使用，
且 T1 偵測得到」——不是能力分數，也不改核心分。

### 37.7 怎麼讀這個結果（含限制）

1. **state 真的被用了**：主臂 0.9998，歸零 `h` 後時間題掉到 0.5092（chance 0.5）、
   內容題（可回答半）掉到 0.0785（chance 1/9）。不是「輸出有變」，是**答案消失**。
2. **時間只從 `al_step` 進來**：完全跳過 `al_step` 的結果與歸零 `h` **逐位同分**
   （0.5092 vs 0.5092，5 個種子都一樣）。這正是 T5 要的方向：沒有 AL 週期，模型就
   不知道過了多久。
3. **對照組有鑑別力**：hand-state 臂把時間放在 token 上，歸零 `h` 對它的時間題
   **完全沒有影響**（1.0000 → 1.0000），拿掉 token 才掉到 0.5056。同一個 T1 對
   「state 在模型裡」與「state 在 context 裡」給出不同結果——測試不是擺設。
4. **假時鐘照預測方向失敗**：每段固定 30 s（T=120）→ 過期半時間題 **0.0000**：
   模型把過期當成可回答。這是「時間作用在狀態上」的正面證據，不是雜訊。
5. **重啟**：同一個 `h` 存成 `.npz`、載回、續跑，200 題時間題最大機率差 **0**。
   但這是**同進程**的 save/load；跨進程版尚未做（§12 的 `probe_state_restart.py`）。

**限制（不可略過）**

- **合成任務、100% 不代表智能**。它只證明機制可用；核心分仍是 **0.00/10**，生產
  聊天路徑沒有接這個模型，`state_for_llm` 仍然存在。
- **chunk 數本身是時間訊號**：gap > 60 s 會切成 2 段、≤ 60 s 只有 1 段，所以模型可以
  用「更新了幾次」代替「積分 dt」。這仍然只透過 `al_step`，但比「等段數、只變 dt 大小」
  容易。下一輪要做**等段數**版本，把這個捷徑拿掉再量一次（新預登記）。
- **半群沒有成立**（差 0.7588）：GRU 不是積分器，第一輪也沒有訓練 `L_al`。要讓它成立，
  得加 `L_al` 或換 SSM（dt 進遞歸）——這是 P3，不是這一輪的失敗。
- **T1 的內容題門檻用「可回答半」**：歸零後模型常常固定答 `<unknown>`，整體內容題
  會拿到 0.4–0.5（因為一半 session 過期），所以整體數字沒有鑑別力；可回答半的基線是
  1/9。這是量測缺陷的修正，已在 §37.5 記錄，不是放寬門檻。
- **只量了一個架構（GRU）、一個預算（30 epochs）、一個任務**。SNN 第二臂還沒接；
  「同一個契約在 SNN 上可行」仍未被證實。
- **T2 的 hand-state 是合成對照**，不是語言模型把狀態寫進 prompt；生產層的
  prompt-leak 檢查（T2 的另一半）要在 P4 接線時做。

**下一步**（依契約 §9 的停損）

1. ✅ 等段數版本（§38）：chunk 總數固定為 8、同一組門檻重跑，**18/18 通過**——
   「數次數」的捷徑已排除，時間從 dt 大小進 state。
2. ✅ 加 `L_al`（§39）：對照組（無 `L_al`）max|Δh| 1.66–1.88，加 `L_al` 後
   0.069–0.140（縮小 12–24 倍），但**未達登記的 1e-2**（三項 FAIL）。照實記為
   「方向對、幅度不夠」；不宣稱「時間連續作用」。下一步是 SSM（dt 進遞歸），不是調 λ。
3. SNN 第二臂：同一份 `ai_step`/`al_step`，先修梯度帶，再用同預算比。
4. 跨進程 restart，然後才是 P4 生產接線（`generation_gate` 加 `stateful`、
   `chat_routes` 傳 state 物件、prompt 只給 fallback）。

## 三十八、等段數的重跑：把「數 chunk」的捷徑拿掉（2026-11-12，量測前寫定）

> **這一節同樣是在跑之前寫的。** §37 通過了，但它的 gap 切法留了一個捷徑：`al_step`
> 把 dt 切成 ≤60 s 的段，而 §37 的 gap 是**不等長**的（總長 0–200／280–400 隨機切成 4 段），
> 所以一段 180 s 會變成 3 個 chunk、一段 20 s 只有 1 個。模型因此可以不去積分「dt 有多大」，
> 只去數「`al_step` 被呼叫了幾次／走了幾步」就判斷有沒有過期。§37 的結果沒有區分這兩者。
> 這一輪只改一件事：**讓每個 session 的 chunk 總數完全相同**，唯一的時間訊號只剩 step 內
> 的 dt 大小。

### 38.1 要回答的問題

在「段數固定」的條件下，主臂是否**仍然**通過 §37.5 的同一組門檻？若通過，表示時間是從
`dt` 的**大小**進 state，而不是從「更新了幾次」；若失敗，則 §37 的通過有一部分是捷徑，
必須照實記下來（不改門檻、不改題目）。

### 38.2 任務（其餘與 §37.2 完全相同）

- 詞表、教導／間隔／時間題／內容題、`T` 的兩個區間（`U(0,200)`、`U(280,400)`）、
  240 s 到期規則、train 4,000／held-out 1,000 依 session 切分、資料種子 `1000+seed`／
  `2000+seed` 全部不變。
- **唯一改動**：每個 session 的 `T` 平均切成 **8 段**（每段 `T/8`）。因為 `T ≤ 400`，
  每段 ≤ 50 s，所以每段恰好 1 個 chunk，**每個 session 的 chunk 總數都是 8**。
- 模型：仍是單層 `GRUCell`、`d_hidden=64`、`d_emb=32`、chunk 60 s、同一個 `al_step`
  切段規則；優化器、lr、batch、epochs、seeds 與 §37.3 相同。
- 假時鐘對照改為 **8 × 15 s（T=120）**：chunk 數與真實 session 一樣是 8，只有 dt 大小
  不同——這是這一輪真正在測的通道。
- 打亂 gaps 仍是跨 session 打亂，段數不變。

### 38.3 通過條件

**完全沿用 §37.5 的門檻，一個數字都不改**（時間題 ≥0.90、內容題 ≥0.85、兩半各 ≥0.85、
歸零後時間題 ≤0.65／內容題可回答半 ≤0.30／下降 ≥0.30、重啟 ≤1e-5、不跑 `al_step`
≤0.65 且下降 ≥0.30、打亂 ≤0.70、假時鐘過期半 ≤0.30、hand-state 三項、provenance、
`dt=0` 恆等），另加一項**機制檢查**：

| 檢查 | 條件 |
| --- | --- |
| `equal_step_counts` | held-out 所有 session 的 chunk 總數集合必須恰好是 `[8]` |

半群仍是**量測、不判**（§37.5 的理由不變；這一輪也沒有 `L_al`）。

**判定**：全部（18 項）通過＝「在段數固定的條件下，時間仍從 dt 大小進 state」；
任一項不過＝照實記該項失敗，**不改門檻重跑**。若只有主臂三項或 T1 失敗，結論必須寫成
「§37 的通過依賴 chunk 數」，不能只報這一輪的失敗。

### 38.4 結果（2026-11-12，登記 run 實測；未改任何門檻）

登記參數與 §37 相同（5 種子、4,000／1,000 sessions、30 epochs、batch 64、lr 5e-3、
21,402 參數），唯一差別是 **8 個等長 gap**。整輪 **107.7 s**（CPU）。完整輸出：
`data/intelligence_reports/probe_state_cycles_round2.json`。
**機制檢查先確認**：held-out 所有 session 的 chunk 總數集合 = **`[8]`**（min=max=8），
所以這一輪不存在「用更新次數數時間」的通道。

| 條件 | 指標 | 結果 | 預登記門檻 | 判定 |
| --- | --- | --- | --- | --- |
| 主臂 | 時間題 | **1.0000 ± 0.0000** | ≥ 0.90 | PASS |
| 主臂 | 內容題 | **1.0000 ± 0.0000** | ≥ 0.85 | PASS |
| 主臂 | 兩題都對 | **1.0000 ± 0.0000** | — | — |
| 主臂 | 可回答／過期（時間題） | 1.0000／1.0000 | 各 ≥ 0.85 | PASS |
| 主臂 | 可回答／過期（內容題） | 1.0000／1.0000 | 各 ≥ 0.85 | PASS |
| T1 歸零 `h` | 時間題 | **0.4986 ± 0.0129** | ≤ 0.65 | PASS |
| T1 歸零 `h` | 內容題（可回答半） | **0.0485 ± 0.0835** | ≤ 0.30 | PASS |
| T1 下降 | 時間題 | **0.5014** | ≥ 0.30 | PASS |
| T5 不跑 `al_step` | 時間題 | **0.4988 ± 0.0130**（下降 0.5012） | ≤ 0.65／下降 ≥ 0.30 | PASS |
| T5 打亂 gaps | 兩題都對 | **0.4948 ± 0.0136** | ≤ 0.70 | PASS |
| T5 假時鐘（8 × 15 s = 120 s） | 過期半時間題 | **0.0000 ± 0.0000** | ≤ 0.30 | PASS |
| T2 hand-state | 時間題 | **1.0000** | ≥ 0.90 | PASS |
| T2 hand-state 歸零 `h` | 時間題變化 | **0.0000** | ≤ 0.05 | PASS |
| T2 拿掉 bucket token | 時間題 | **0.5052 ± 0.0108**（下降 0.4948） | 下降 ≥ 0.30 | PASS |
| T4 重啟 | 200 題最大機率差 | **0.00e+00** | ≤ 1e-5 | PASS |
| T6 provenance | `weights_hash`／token | 前後一致；核心 token 只有 `{PAD, Q_TIME}` | 一致／無 bucket | PASS |
| `dt = 0` | `h` 與 ticks | **逐位不變** | 恆等 | PASS |
| 機制 | `equal_step_counts` | chunk 總數 **`[8]`** | 恰為 `[8]` | PASS |
| 半群（只量） | 30+30 vs 60 | **0.9180 ± 0.3514** | 不判 | 照實記 |

逐種子（歸零後時間題）：0.498／0.497／0.483／0.511／0.504（= chance 0.5）。
**判定：18 項全過。**

### 38.5 怎麼讀這一輪（含與 §37 的差別）

1. **「數 chunk」的捷徑被排除了**：段數固定成 8 之後，主臂仍是 1.0000，歸零 `h` 仍
   掉回 0.4986（chance 0.5）、內容題可回答半掉到 0.0485（常數答錯，低於 chance 1/9）。
   所以 §37 的通過不是靠「更新了幾次」，而是 dt 的**大小**經由 `al_step` 進入同一個
   `GRUCell`。§37.7 列的這個限制，這一輪已經處理掉。
2. **對照組仍分得開**：hand-state 臂歸零 `h` 完全不受影響（1.0000 → 1.0000），
   拿掉 bucket token 才掉到 0.5052。同一個 T1 對「state 在模型裡」與「state 在
   context 裡」給出不同結果。
3. **假時鐘仍照預測方向失敗**：8 × 15 s（T=120）→ 過期半 **0.0000**；段數與真實
   session 完全相同，所以這不是段數造成的。
4. **半群反而更差（0.7588 → 0.9180）**：這一輪的資料全部 ≤ 50 s／段，`al_step(60)`
   是一個 `1.0` 的輸入、`30+30` 是兩個 `0.5`，模型沒有理由把它們視為等價。
   這再次確認「學出來的 recurrence 不保證可加性」——`L_al` 或 SSM 才會處理，這一輪
   沒有訓練 `L_al`，所以只量不判。

**限制（與 §37.7 相同的仍然成立）**

- 合成任務、只有 GRU、同進程 restart、沒有 `L_al`；核心分仍是 **0.00/10**，生產聊天
  路徑沒有接這個模型，`state_for_llm` 仍然存在。
- 段數固定排除了「數次數」，但**沒有**排除「dt 的排序」：打亂 gaps 仍會改變總和，
  所以 shuffled 掉到 0.4948 只證明「跨 session 換掉時間值會壞」，不是「順序重要」。
  要分離順序，需要另一個預登記（同一個多重集合、不同排列）。
- 100% 是這個 26 詞彙、單一答案位置的任務的 100%，不是語言能力。

## 三十九、`L_al`：時間的可加性能不能被訓練出來（2026-11-12，量測前寫定）

> **這一節也是在跑之前寫的。** §37／§38 只用了答案的 cross-entropy（`L_ai`），
> 半群是**量測項**：`al_step(30)+al_step(30)` 與 `al_step(60)` 差 0.7588／0.9180，
> 不相等。這一輪把契約 §5.2 的第二個 loss 真的加上去，並預先登記它要證明什麼、
> 用哪一組「沒教過的切法」驗。

### 39.1 要證偽的宣稱

宣稱：加上 `L_al`（同一個 state 在時間上的一致性）後，模型**不只**在訓練用的
`(25,25)→50` 上可加，在**沒教過的** `(30,30)→60` 與 `(20,40)→60` 上也接近可加，
而且答案能力（§38 的 T1–T3）沒有被破壞。

反面（必須能區分）：只學「複製上一個 state」或把 `h` 壓成常數，會讓半群變好但
T1（歸零）與 T3（答案）失敗——所以 T3／T1 的門檻與半群門檻必須**同時**通過。

### 39.2 `L_al` 的形式（固定，不調）

對一個狀態 `h`：

```
h_A = al_step(dt2, al_step(dt1, h))        # 先走 dt1 再走 dt2
h_B = al_step(dt1 + dt2, h)                # 一次走完
L_al = mean((h_A - h_B)^2)
```

- 訓練只教 **`(dt1, dt2) = (25, 25)`**（和 50）。
- 半群量測用**沒教過的** `(30, 30)`（和 60）與 `(20, 40)`（和 60）；另報訓練對
  `(25, 25)` 當健全性檢查（不當通過條件）。
- `L_al` 的狀態取**每個 training session 最後一個 `al_step` 之後的 `h`**（模型實際
  會停留的分布），不是隨機噪聲；兩個分支共用同一個 `h0`，梯度都回傳。
- 總 loss：`CE(時間題) + CE(內容題) + λ · L_al`，**λ = 0.5**（預先寫定）。
- 其餘與 §38 完全相同：8 個等長 gap（每段 ≤50 s）、4,000／1,000 sessions、30 epochs、
  batch 64、lr 5e-3、GRU 64／32、5 個種子 0–4。
- **對照組就是 §38 的 round 2 結果**（同一批種子、同一份資料、同一個預算，唯一差別是
  `L_al` 權重 0 對 0.5）。不重跑對照組，避免用不同執行污染比較。

### 39.3 通過條件（與 §38 同一組答案門檻，另加半群）

| # | 指標 | 通過條件 |
| --- | --- | --- |
| T3 | 主臂時間題／內容題 | ≥ **0.90**／≥ **0.85**，且四半各 ≥ **0.85** |
| T1 | 歸零 `h` | 時間題 ≤ **0.65**、內容題可回答半 ≤ **0.30**、下降 ≥ **0.30** |
| T5 | 不跑 `al_step` | 時間題 ≤ **0.65** 且下降 ≥ **0.30** |
| T5 | 打亂 gaps／假時鐘 | 整體 ≤ **0.70**；假時鐘過期半 ≤ **0.30** |
| T2 | hand-state 臂 | 三項與 §37.5 相同 |
| T4／T6／`dt=0`／等段數 | 與 §37.5／§38.3 相同 | 同前 |
| `L_al` 訓練對（健全性） | `(25,25)` vs 50 的 max abs Δ | **≤ 1e-2** |
| **`L_al` 留出 1** | `(30,30)` vs 60 | **≤ 1e-2** |
| **`L_al` 留出 2** | `(20,40)` vs 60 | **≤ 1e-2** |

量測方式：取 held-out 1,000 個 session 在提問前的 `h`（`run_sessions` 的
`prefix_state`），對每一組 dt 算兩個分支，回報**所有樣本、所有維度的最大絕對差**。

**判定**：全部通過＝「`L_al` 讓時間在沒教過的切法上也近似可加，且沒有用塌縮換來」；
任一項不過＝照實記該項失敗，不改 λ、不改門檻、不改留出對。若半群過了但 T3 掉了，
結論必須寫成「用可加性換掉能力」，不得只報半群。

### 39.4 結果（2026-11-12，登記 run 實測；未改任何門檻）

登記參數：λ=0.5、訓練對 (25,25)、留出對 (30,30)／(20,40)、其餘同 §38（8 等長 gap、
4,000／1,000 sessions、30 epochs、batch 64、lr 5e-3、21,402 參數、5 種子）。
整輪 **109.5 s**（CPU）。輸出：`data/intelligence_reports/probe_state_cycles_round3.json`。

**對照組**：§38 的 round 2（無 `L_al`）以相同種子／資料／預算重跑一次，數字與 §38.4
**完全重現**（主臂 1.0000、歸零 0.4986、內容題可回答半 0.0485、不跑 `al_step` 0.4988、
打亂 0.4948、restart 0），所以下面兩臂的差別不是執行變異。

| 半群對（max abs Δh，1,000 held-out states） | 對照（`L_al`=0） | `L_al`=0.5 | 縮小 | 登記門檻 | 判定 |
| --- | --- | --- | --- | --- | --- |
| **25+25**（訓練對，健全性） | 1.6989 | **0.0694** | 24.5× | ≤ 1e-2 | **FAIL** |
| **30+30**（留出） | 1.8755 | **0.1397** | 13.4× | ≤ 1e-2 | **FAIL** |
| **20+40**（留出） | 1.6570 | **0.1330** | 12.5× | ≤ 1e-2 | **FAIL** |

平均 Δh（同一個量，供對照）：訓練對 1.5504 → 0.0517；30+30 1.6079 → 0.0868；
20+40 1.4533 → 0.0948。逐種子訓練對 max：0.0694／0.0403／0.0557／0.0425／0.0507。

**答案與機制（與 §38 同組門檻）**：主臂 1.0000、歸零 `h` 時間題 0.4986／內容題可回答半
0.0528、下降 0.5014；不跑 `al_step` 0.4952（下降 0.5048）；打亂 0.4948；假時鐘 0.0000；
restart 0；核心 token `{PAD, Q_TIME}`；`equal_step_counts=[8]`——**18 項全部 PASS**。

**判定：3 項 `L_al` 失敗 → 這一輪沒有證明「時間在沒教過的切法上可加」。**

### 39.5 怎麼讀這個否定結果

1. **方向是真的，幅度不夠**：同一個量在兩臂之間差 12–24 倍，`L_al` 確實作用在同一個
   `GRUCell` 的狀態上（測試也釘住梯度會回到 cell）。但登記的門檻是 **1e-2**，實際最好
   的訓練對仍是 **6.9e-2**，留出對 1.3–1.4e-1。**不改 λ、不改門檻重跑**。
2. **loss 是「狀態局部」的**：最後一個 mini-batch 的 `L_al` 已到 **1.4e-5**，但同一組
   (25,25) 在 held-out 的 session 狀態上仍是 6.9e-2（平均 5.2e-2）。也就是說，它把
   **那一批狀態**壓平了，沒有把可加性變成整個狀態分布上的性質。這是這一輪最有用的一個
   觀察：下一版若還用 `L_al`，必須在**重播的狀態分布**上做，而不是當前 batch。
3. **沒有用塌縮換分數**：T1／T3 全過、歸零仍回到 chance，所以不是「把 `h` 壓成常數」
   造成的假可加。這一輪是單純的「約束不夠強／不夠廣」。
4. **下一步（契約 §9 P3）**：SSM（dt 真的進遞歸，而不是當輸入投影）是下一個預登記
   ——✅ 已完成（§40：21/21 通過，半群 1.9–3.8e-6 且是架構保證）；
   或把 `L_al` 改成狀態重播 + 更長的訓練預算（另一個預登記、另一組門檻）。**不調這一輪
   的 λ**，也不把 30 epochs 改成 60 後重報同一件事。
5. 仍然是合成任務、只有 GRU、同進程 restart；核心分不變（**0.00/10**），生產路徑未接。

## 四十、SSM 臂：時間「在遞歸裡」而不是「當輸入特徵」（2026-11-12，量測前寫定）

> **這一節也是在跑之前寫的。** §37／§38 證明 GRU 的時間是從 `al_step` 進 state 的（歸零、
> 跳過、打亂、假時鐘都照預測方向失敗），§39 證明 `L_al` 只能把半群差縮小 12–24 倍、
> 沒到 1e-2。這一輪換的是**遞歸本身**：對角線性 SSM，時間以 decay 的形式直接乘進狀態。
> 半群因此是**架構保證**，不是訓練出來的——這一節同時寫清楚「所以它不能當能力證據」。

### 40.1 要回答的問題

在同一個合成任務、同一份資料、同一組答案門檻下，SSM 臂是否

1. 通過 §37.5／§38.3 的 **T1–T6 全部答案與機制檢查**（時間題、內容題、歸零、跳過
   `al_step`、打亂、假時鐘、hand-state 對照、restart、provenance、`dt=0`、等段數）；
2. 在**沒有** `L_al` 的情況下，半群差 ≤ **1e-2**（三組：訓練對 (25,25)、留出 (30,30)、
   留出 (20,40)）。

第 2 點若成立，只表示「這個遞歸的數學形式可加」，**不表示模型學會了連續時間**；能力仍只看
T1／T3／T5。這一輪的用途是給 P3 一個可比較的候選，不是加一條能力宣稱。

### 40.2 架構（固定，不調）

`ai/core/stateful_decoder.py::SSMCore`，與 `GRUCore` 共用同一個 `StatefulCore`（state
物件、`weights_hash`、checkpoint 格式）：

- **`al_step(dt)`**：`h ← h · exp(-dt/τ)`，`τ` 是每個 hidden 維度各自的正數（`τ = exp(τ_log)`，
  所以任何梯度步都保持正）。切段仍走同一個 `chunk_dt`（≤60 s），每段乘一次 decay——
  乘積就是 `exp(-dt/τ)`，這是**精確**的，不是近似。
- **`ai_step(tokens)`**：`h ← h + W_in · E[token]`，讀出 `logits = W_out · h + b`（線性頭）。
  時間只從 `al_step` 進來；不呼叫它就沒有時間。
- **`τ` 初始化**：在 `[20 s, 2000 s]` 之間**對數等距**（`hidden=64`），不依賴種子。
  理由（也寫在程式 docstring）：任務的時間尺度是 chunk 60 s → session 400 s，需要同時有
  快通道（比值帶時間）與慢通道（內容撐過 400 s）。這個區間是**跑之前**寫定的；看到結果
  之後不改。
- **可訓練**：`embedding`、`in_proj`、`head`、`τ_log`，一個 Adam 優化器；其餘（lr、batch、
  epochs、grad clip、seeds、8 個等長 gap、4,000／1,000 sessions、chunk 60 s）與 §38 相同。
- **參數量**：SSM **4,634**（26×32 + 32×64 + 64×26+26 + 64）vs GRU **21,402**。
  這一輪**不**用它加分或扣分；P3 的成本比較另外記。

### 40.3 通過條件

答案／機制門檻**完全沿用 §38.3，一個數字都不改**（T3 時間 ≥0.90、內容 ≥0.85、四半各
≥0.85；T1 歸零 ≤0.65／內容可回答半 ≤0.30／下降 ≥0.30；T5 不跑 `al_step` ≤0.65 且下降
≥0.30、打亂 ≤0.70、假時鐘過期半 ≤0.30；T2 三項；T4 ≤1e-5；T6；`dt=0`；等段數 `[8]`），
另加：

| 檢查 | 條件 | 性質 |
| --- | --- | --- |
| `SEMIGROUP_25+25` | max abs Δh ≤ **1e-2** | **架構保證**（乘法指數），不是能力 |
| `SEMIGROUP_30+30` | 同上（留出） | 同上 |
| `SEMIGROUP_20+40` | 同上（留出） | 同上 |

**判定**：

- 21 項全過 → SSM 是 P3 的合格候選；接著才做 P3 比較（T3／T5 **優於或等於** §38 的 GRU，
  GRU 是 1.0000／1.0000，所以實際上是「不得下降」），成本另外記。
- 任一答案／機制項不過 → 照實記該項，**不改 τ 區間、不改門檻重跑**。若只有半群過而
  T3 掉，結論寫成「架構可加、但讀出扛不住兩個任務」，不得只報半群。
- 對照組是 §38 的 round 2（同種子、同資料、同預算）；它是決定性的，重跑會逐位重現
  （§39.4 已驗證一次），所以**不重跑**以避免污染比較。

### 40.4 結果（2026-11-12，登記 run 實測；未改任何門檻）

登記參數：§38 同一份資料與預算（5 種子、4,000／1,000 sessions、30 epochs、batch 64、
lr 5e-3、8 個等長 gap、chunk 60 s、`hidden=64`／`emb=32`），**沒有** `L_al`。SSM **4,634**
參數。輸出：`data/intelligence_reports/probe_state_cycles_round4.json`。
執行時全量測試同時在跑，所以下面的 wall time **不當成本證據**。

| 條件 | 指標 | 結果 | 預登記門檻 | 判定 |
| --- | --- | --- | --- | --- |
| 主臂 | 時間題 | **1.0000 ± 0.0000** | ≥ 0.90 | PASS |
| 主臂 | 內容題 | **1.0000 ± 0.0000** | ≥ 0.85 | PASS |
| 主臂 | 四半 | 1.0000／1.0000／1.0000／1.0000 | 各 ≥ 0.85 | PASS |
| T1 歸零 `h` | 時間題 | **0.0000 ± 0.0000** | ≤ 0.65 | PASS（常數錯答） |
| T1 歸零 `h` | 內容題（可回答半） | **0.0000 ± 0.0000** | ≤ 0.30 | PASS |
| T1 下降 | 時間題 | **1.0000** | ≥ 0.30 | PASS |
| T5 不跑 `al_step` | 時間題 | **0.4970 ± 0.0123**（下降 0.5030） | ≤ 0.65／下降 ≥ 0.30 | PASS |
| T5 不跑 `al_step` | 內容題（可回答半） | **1.0000** | （未登記，供診斷） | — |
| T5 打亂 gaps | 兩題都對 | **0.4948 ± 0.0136** | ≤ 0.70 | PASS |
| T5 假時鐘（8 × 15 s = 120 s） | 過期半時間題 | **0.0000 ± 0.0000** | ≤ 0.30 | PASS |
| T2 hand-state | 時間題／歸零／無 bucket | 1.0000／1.0000／**0.5052** | 同 §37.5 | PASS |
| T4 重啟 | 200 題最大機率差 | **0.00e+00** | ≤ 1e-5 | PASS |
| T6 provenance | `weights_hash`／token | 前後一致；核心 token 只有 `{PAD, Q_TIME}` | 一致／無 bucket | PASS |
| `dt = 0` | `h` 與 ticks | **逐位不變** | 恆等 | PASS |
| 機制 | `equal_step_counts` | **`[8]`** | 恰為 `[8]` | PASS |
| 半群（**架構**） | 25+25 | max abs Δh **3.81e-06** | ≤ 1e-2 | PASS |
| 半群（**架構**） | 30+30（留出） | **3.81e-06** | ≤ 1e-2 | PASS |
| 半群（**架構**） | 20+40（留出） | **1.91e-06** | ≤ 1e-2 | PASS |

逐種子主臂全部 1.0000。半群平均：25+25 2.86e-6、30+30 2.67e-6、20+40 1.91e-6；
對照組 §38 的 GRU 同一個量是 **1.66–1.88**（差 5–6 個數量級）。
`τ` 學到什麼（初始 `[20, 2000]`，逐種子）：最小 **20.5–24.4 s**、中位數 **166.6–243.2 s**、
最大 **2,810.9–3,343.7 s**——快通道留在 chunk 尺度，慢通道**長出了初始上限**。

**判定：21/21 全過。**

### 40.5 怎麼讀這一輪（以及哪一部分不能拿來邀功）

1. **半群過關是架構，不是學習。** `al_step` 是 `exp(-dt/τ)` 的乘積，`exp(-a)exp(-b)=
   exp(-(a+b))` 本來就成立；就算把權重全部隨機初始化、完全不訓練，這個檢查也會過。所以
   它**不能**寫成「SSM 學會了時間可加」，也不能拿它去和 §39 的 `L_al` 比「哪個學得好」——
   一個是數學恆等式，一個是訓練約束。它唯一的用途是：P3 的候選不必再背 `L_al`。
2. **歸零後 0.0000 不是「不知道」，是「固定答錯」。** `h=0` 之後，時間題的輸入只剩
   bucket＋`Q_TIME` 兩個 token 注入，所有樣本得到同一組 logits，模型固定選 `EXPIRED`，
   所以可回答半全錯（0.0000），不是掉回 chance 0.5。這和 §38 的內容題可回答半 0.0485
   同類：門檻（≤0.65）過，但必須照實寫成「常數錯答」。
3. **時間與內容被乾淨分離**：不跑 `al_step` 時，時間題 0.4970（chance）、**內容題仍是
   1.0000**。內容不需要時間，時間只從 `al_step` 進來；這正是 T5 想看到的 dissociation，
   比 GRU 那一輪更清楚（GRU 的 no_al 只有時間題被登記）。
4. **`τ` 的移動是描述，不是調參**：初始上限 2,000 s，訓練後最大 τ 到 2,810–3,344 s，
   中位數落在 167–243 s（正好覆蓋 200／280 s 的判定邊界），最小 τ 貼在 20 s 下限
   （chunk 尺度）。這表示模型自己把通道分配到「段」與「session」兩個尺度；區間是跑之前
   寫定的，沒有因為結果改動。
5. **成本當時沒有結論。** 參數 4,634 vs GRU 21,402（0.22×），但這一輪 wall time（74.0 s）
   是在全量測試同時跑的時候量的，§38 的 99.4 s 是機器閒置時量的，**兩者不可比**。
   乾淨計時後來補做，見 §40.7。
6. **順序偏離要寫出來**：契約 §9 寫 P2（SNN）→ P3（SSM），這一輪先做 P3。原因是 SNN 的
   token 表徵／梯度問題（`CORE_GAP_ANALYSIS` §七、§X #276）是另一條工作，不是這個介面能
   修的。**這不表示 P2 完成**；SNN 臂仍未接，P2 的 gate 未動。
7. **仍然是合成任務、同進程 restart（跨進程版見 §40.8）、單一線性讀出、沒有接生產**；核心分不變
   （**0.00/10**），`state_for_llm` 仍在。這一輪只證明「同一契約下，dt 原生的遞歸可以
   用更少參數達到同樣的 T1／T3／T5，且半群不必訓練」。

### 40.6 下一步

1. ✅ **乾淨的成本量測**（同一台機器、同一時間、交替跑 GRU 與 SSM 各 3 次，量 forward／
   train step／記憶體）——見 §40.7。
2. ✅ **跨進程 restart**（`scripts/probe_state_restart.py`）：新解釋器只靠權重檔＋狀態檔
   重跑，兩臂 Δp = 0；順手抓到並修掉 `attach_state()` 不檢查 `model_kind`／
   `weights_hash` 的真缺陷——見 §40.8。
3. **SNN 臂**（P2）：先解決 token 表徵與梯度帶，再用同一組 T1–T6；不要用 SSM 的結果
   代替它。
4. **P4 接生產**：`generation_gate` 加 `stateful`、`chat_routes` 傳 state 物件、
   `state_for_llm` 只留 fallback；在那之前，核心分仍是 0.00/10。

### 40.7 成本（2026-11-12，`--cost`；三次獨立 run）

§38 的 99.4 s 與 §40.4 的 74.0 s 不可比（其中一次有全量測試同時在跑）。要回答 P3 的
「成本可接受」，量的是**同一條路徑上的同一份工作**，不是兩次訓練的 wall time：

- **工作**：batch 64、8 個等長 gap 的一整回合（teach → 7 次 `al_step`＋8 次 `ai_step`
  → `Q_TIME`／`Q_KEY` 兩個查詢）。訓練步就是 `train_arm` 呼叫的**同一個**
  `_train_step()`——為了讓它可被單獨計時，把它從迴圈裡抽成函式（行為不變：登記 run 重跑
  逐位相同，見下）。
- **計時**：每臂 **warmup 5 + 30 reps**，取中位數；**交替順序**三次（gru→ssm、
  ssm→gru、gru→ssm），這樣機器負載漂移會落在兩臂上而不是只落在其中一臂。
- **環境**：同一進程、CPU、PyTorch 2.14.1+xpu（eager，6 threads／12 cores）；沒有 GPU、
  沒有 inductor。三次獨立 run 各自完整重跑。

| 臂 | 參數 | checkpoint | forward（中位數） | 一個訓練步（中位數） |
| --- | --- | --- | --- | --- |
| GRU | 21,402 | 86.9 KiB | **2.02–2.07 ms** | **6.31–6.42 ms** |
| SSM | 4,634 | 20.8 KiB | **1.14–1.15 ms** | **2.82–3.01 ms** |
| SSM／GRU | **0.217** | **0.239** | **0.552–0.566** | **0.445–0.468** |

可重現性：三次獨立 run 的差 ≤ ~3%（forward 0.55–0.57×、訓練步 0.45–0.47×），中位數的
min–max 區間也窄（例：GRU forward 1.91–3.14 ms，SSM 1.10–1.57 ms）。

**能說什麼、不能說什麼**：

1. 能說：在這個合成任務尺寸上，SSM 的**計算量**約為 GRU 的 **0.55×**（單次 forward）／
   **0.45×**（一個訓練步），參數 0.22×、checkpoint 0.24×。
2. 不能說：「SSM 更快」若指的是生產延遲——這不是端到端量測，模型只有 26 個 token、
   `hidden=64`；生產路徑（P4）根本還沒接。也不能說「成本可接受」：可接受是對某個
   服務目標而言，而系統還沒有那個目標。
3. 不能說：RSS／記憶體佔用。進程 RSS 由 torch 共享，無法按臂歸因；表裡的
   `state_bytes_per_batch` 只算 hidden state（64×64×4 B），不含配置器開銷。
4. **量測機不是專用 benchmark 機**：這是桌面環境，load average 3.6–4.7（12 cores），
   有桌面程式與一個無關的背景程序在跑。所以照實寫成「交替順序＋中位數」，不是
   「絕對毫秒」；三次獨立 run 的一致性就是它的可信度來源。

輸出：`data/intelligence_reports/probe_state_cycles_cost.json`（gitignored）。指令：
`python3 scripts/probe_state_cycles.py --cost`。

### 40.8 跨進程 restart（2026-11-12，新解釋器；T4 的第二半）

§37.5 的 T4 是在**同一個行程**裡量的（`CoreState.save` → `load` → `attach_state`）。生產會
重啟行程，所以真正的問題是：**權重檔＋狀態檔單獨存在時夠不夠**——新解釋器、沒有共享
記憶體、沒有把時間或上下文寫進提示詞。

方法（`scripts/probe_state_restart.py`，判定在跑之前寫定）：

- 兩個獨立的 Python 行程。`--phase capture` 先訓練核心（2,000 sessions、10 epochs、與 §38
  同一個等長 gap 生成器），打一個回合（教 → 8 × 50 s → 查詢），存下**權重檔**、**查詢
  之前**的 state、查詢 token 與參考機率；`--phase resume` 在**新行程**裡**從檔案載入權重**
  （不是靠同一個種子重建），再用 `expected_weights_hash` 載入 state、只重跑查詢。
- 為什麼要訓練：未訓練的 GRU，查詢輸出由輸入 token 主導，**歸零的 state 看起來一樣**，
  那 1e-5 的比較就沒有意義。這一點是實測到的（煙霧預算下敏感度檢查會 FAIL），所以登記
  版本先訓練核心；訓練預算寫在檔案的 `REGISTERED` 裡，不是看到結果才加。

判定與結果（`all_pass = True`）：

| 檢查 | 條件 | GRU | SSM |
| --- | --- | --- | --- |
| max abs Δp（capture vs resume） | ≤ 1e-5 | **0.000e+00** | **0.000e+00** |
| `weights_hash`／`model_kind` | 一致 | PASS | PASS |
| `ticks`（8）／`last_dt_s`／`state_version` | 一致 | PASS | PASS |
| 歸零 state 的 Δp（敏感度） | ≥ 1e-2 | **0.9063** | **0.9904** |
| 另一臂的 state | 拒絕 | PASS | PASS |
| 把 state 接到錯的臂 | 拒絕 | PASS | PASS |
| 位元組被改寫的 state | 拒絕 | PASS | PASS |

**過程中抓到的真缺陷（已修）**：`StatefulCore.attach_state()` 原本只把 numpy 轉回 tensor，
**不檢查 `model_kind`、也不檢查 `weights_hash`**。GRU 與 SSM 的 `hidden` 都是 64，所以把
`gru` 的 state 接上 `ssm` 核心會**安靜地成功**，模型於是用一個對它從不存在的 state 回答。
修法：`attach_state()` 兩項都驗，不符就丟 `CoreStateInvalid`（`CoreState.load(
expected_weights_hash=…)` 守檔案路徑，這個守記憶體路徑），並加 2 條測試。附帶記錄一個分類
細節：權重不符時 `CoreState.load` 拋的是 `CoreStateVersionMismatch`（`CoreStateError` 的
另一支，不是 `CoreStateInvalid`），所以探針的拒絕檢查要接 `CoreStateError`——第一版接
`CoreStateInvalid` 會漏掉。

限制照實記：

1. 同一台機器、同一個 torch build：測的是**行程邊界＋檔案**，不是重開機、不是換機器。
2. 只打**一個回合**；生產是長 session（P4）。
3. 敏感度檢查需要**訓練過**的核心才成立。用 64 sessions × 1 epoch 的煙霧預算跑，它會照實
   FAIL（`tests/ai/test_state_restart.py` 因此只驗機制，不驗這一項），這不是探針壞了，是
   那個預算下的 GRU 本來就幾乎不看 state。
4. 核心分不變（**0.00/10**），生產路徑仍走 prompt／`state_for_llm`。

## 四十一、P4：同一個 state 物件第一次進到真實路徑（2026-11-12）

§37–§40 證明的是「在一個 probe 裡，模型會用 state」。P4 要回答的是另一件事：**在真正的
聊天路徑上，連續性是不是由那個 state 物件承載，而不是由 prompt 文字承載。** 這一節只談
載體，不談能力——核心分不變（**0.00/10**）。

### 41.1 接法（opt-in，預設關）

- `apps/backend/src/ai/core/stateful_runtime.py`：`ChatCoreRuntime`。每回合
  `advance(text)` 做四件事：載入 checkpoint 描述的臂（臂由**檔案**決定，不是環境變數）、
  載入該 session 的 state（`expected_weights_hash` ＋ `attach_state` 兩道檢查）、用
  `last_update` 算 `dt` 後 `al_step(dt)`、把使用者這句話送進 `ai_step`、存檔。
- **每 session 一個狀態目錄**（session id 的 sha256 前 16 碼），共用同一份權重。單一
  process-wide 狀態檔會讓 A 的回合推進 B 的狀態——那正是契約要防的「不屬於任何人的
  state」。
- `chat_routes._handle_chat_request` 在 `try` 之前推進一次，於 `finally`（與 session
  持久化同一個區塊）把 provenance 貼回回覆。所有失敗都吞掉並記 warning：核心是基礎設施，
  不得把回覆一起帶走。
- 開啟時 `_ctx_state_matrix` **直接返回**，不發布 `state_for_llm`；`context["state_source"]
  = "core"`。契約 §3 的規則「狀態不得以文字寫進 prompt」於是在生產路徑上成立。
  「承載連續性」的判定要求**核心真的載入成功**（`_core is not None`），不是「磁碟上有
  checkpoint」：torch 缺失或 checkpoint 壞掉時，把 prompt 載體關掉卻沒有任何東西補上，
  等於讓連續性歸零還宣稱有載體。此時 `state_source="none"`，prompt 走原本的路。
- `generation_gate` 新增 `STATEFUL_BACKENDS = {"stateful-core"}` 與
  `stateful_core_active()`。**`stateful-core` 不在 `GENERATIVE_BACKENDS` 裡**：它能承載
  狀態，不能吃提示改寫；放進去就會讓模板答案被記在模型頭上。有一條測試釘住這件事。

### 41.2 實測（真實路徑，不是 mock）

`ANGELA_STATEFUL_CORE=1` ＋ 一份 26-token、`hidden=64`、`emb=32` 的 SSM checkpoint
（未訓練——這一節量的是載體），連續三個回合呼叫**真正的** `_handle_chat_request`：

| 回合 | 回覆（既有路由產生） | `state_source` | `ticks` | `state_version` | `dt_s` |
| --- | --- | --- | --- | --- | --- |
| 你好 | 你好呀！見到你真開心~ | `core` | 0 | 1 | 0.000 |
| 水的沸點是多少? | 答案是 100。 | `core` | 1 | 3 | 6.304 |
| 再見 | 拜拜！下次見啦~ | `core` | 2 | 5 | 0.625 |

- 狀態真的落在 `state/<session digest>/`（`meta.json` ＋ `tensors.npz`），三回合是同一個
  物件在長大：`state_version` 每回合 +2（`al_step` 一次、`ai_step` 一次），`ticks` 只在
  `dt > 0` 時前進。
- **回覆不是核心產生的**：三句分別來自模板與知識層，與 §40 之前相同。核心只承載狀態。
  `state_source` 就是為了讓這件事在回覆裡可被檢查，而不是靠文件宣稱。
- 關閉時（預設）：回覆**沒有**任何新鍵，狀態目錄**不存在**。預設行為未變。
- prompt 端確實被關掉（同一進程實測）：`_stateful_core_carries_continuity()` 在載入前是
  `False`、`advance()` 之後是 `True`；接著 `_ctx_state_matrix({})` 的結果是
  **只有** `{'state_source': 'core'}`——`state_for_llm` 沒有被發布。

### 41.3 接線時抓到的兩個真缺陷（已修）

1. **`CoreState.load` 交回 numpy，不能直接步進**。第一次煙霧測試就在
   `_hidden()` 拋 `CoreStateInvalid: state 'h' must be a torch tensor`。修法：載入後
   必須 `core.attach_state(state)`——它同時是第二道 `model_kind`／`weights_hash` 檢查
   （§40.8 修的正是那裡）。
2. **`last_update` 是 UTC，卻用 `time.mktime` 解析**。`mktime` 把 struct 當**本地**時間，
   於是每個 gap 都多算主機的 UTC 偏移（此機 +8 小時）：一個 6 秒的停頓會變成 8 小時的
   `al_step`。改成 `calendar.timegm`，並加一條測試釘住 `1970-01-01T00:00:00Z == 0.0`
   （在非 UTC 時區上會失敗的正是 `mktime` 版本）。

### 41.4 這一節**沒有**證明什麼（照實寫）

1. **沒有任何東西把 state 讀回生成**。核心不產生文字；prompt 不讀它；router 不讀它。
   所以 P4 的成果是「載體在真實路徑上正確」，不是「載體被使用」。要走到後者，需要一個
   能生成開放域文字的核心（§七／§X #276：目前 0/200 exact），那是 P2/P5 的工作。
2. **tokenizer 是標記用的佔位實作**：文字被 crc32 雜湊進 26 個桶，provenance 寫
   `tokenizer="hash-bucket"`。所以 state 的**內容**沒有語言意義；被驗證的是「一個物件、
   一個 writer、跨回合存回來」。
3. **沒接過 `/api` 的 HTTP 層**：量的是 `_handle_chat_request`（`trace_reply.py` 用的同一個
   入口），不是 FastAPI 的請求／回應序列化。
4. 核心分仍 **0.00/10**（L0）；系統分不因這條接線變動——它不產生任何被計分的答案。
5. **只有單進程的鎖**：`ChatCoreRuntime` 用 `threading.RLock` 串行化同一進程內的回合，
   多 worker（`uvicorn --workers > 1`）會變成兩個 writer 寫同一個 session 目錄。R3 的
   樂觀鎖（`state_version` 比較）與檔案鎖還沒做，這是 P5 的項目；在那之前只該以單一
   worker 開啟這個旗標。

### 41.5 指令

```bash
# 16 條 runtime 測試（預設關、兩回合、session 隔離、restart、三種拒絕、prompt 抑制、
# provenance、以及「檔案存在 ≠ 已載入」）
./.venv/bin/python -m pytest tests/ai/test_stateful_runtime.py -q

# 能力邊界：核心不是生成後端，且預設關
./.venv/bin/python -m pytest tests/services/test_memory_handoff.py -q

# 真實路徑（需要一份 checkpoint；預設關時同一個指令不會建立任何狀態）
ANGELA_STATEFUL_CORE=1 ANGELA_STATEFUL_CORE_DIR=data/core_state \
    ./.venv/bin/python scripts/trace_reply.py "你好"
```

## 四十二、P5：單一寫入者、所有權、真實回合的量（2026-11-13）

§41 用三個回合證明「接線是對的」。三個回合證明不了兩件事：連續性撐不撐得住一個
session，以及多個 worker 同時跑時會不會互相覆寫。這一節只補這兩件，外加一件在補的時候
發現的：**狀態說不說得出它是誰的**。能力不變——核心分仍 **0.00/10**，本節沒有任何一條
是「模型變強」。

### 42.1 為什麼是這三件

- **R3 的字面要求**就是「per-session 鎖＋版本號」，而 §41.4 第 5 點自己記了「只有單進程
  `threading.RLock`；多 worker 會變成兩個 writer」。旗標若在 `uvicorn --workers > 1`
  下端開，就是一個已知會損壞狀態的設定——那比沒做更糟。
- **所有權**：session id 由呼叫端給（前端可指定），所以「A 的 session」不是秘密。若狀態
  不記主人，A 拿到 B 的 session id 就把 B 的連續性接下去，而檔案本身說不出這件事發生過。
- **量**：三個回合只能說「三個回合是對的」。要說「載體撐得住一個 session」，得跑完整
  標準集、每個 stratum 一個 session、逐回合記版本號。

不是 P2（SNN 臂）的原因：§36 已量過同型比較，預期會 FAIL（T3）；它關的是架構問題，
不會讓載體更正確。這一輪的順序是「先讓已存在的東西不會壞，再談更難的模型」。

### 42.2 R3 的三道鎖，各補別人的盲點

| 機制 | 擋得住 | 擋不住 |
| --- | --- | --- |
| per-session 執行緒**條帶**（固定 64） | 同一個進程裡的其他執行緒 | 其他進程 |
| session 目錄裡的 advisory **檔案鎖**（POSIX `flock`／Windows `msvcrt`） | 其他有拿同一把鎖的進程 | 完全沒拿鎖的寫入者（工具、手改、舊版建置） |
| 存檔前的**版本比對** | 任何改了 `state_version` 的寫入者 | 把版本寫回同一個數字的寫入者（那樣就與自己的續接無法區分） |

- **條帶不是 dict**：以 session id 為鍵的 dict 會無限成長，而淘汰一個「正在被持有」的
  條目會讓同一 session 產生第二把鎖——兩個 writer，而且安靜無聲。條帶永遠不變大小，
  所以一個 session 的鎖物件在進程生命期內固定；碰撞只是讓兩個本來就不競爭的 session
  多等一下。
- **檔案鎖用 `LOCK_NB` 輪詢，不是阻塞式 `flock`**：阻塞式沒有逾時，一個卡住的持有者會
  把一個聊天回合永遠掛住。上限 `LOCK_TIMEOUT_S = 2.0`（**呼叫時讀取**，測試可縮短），
  逾時就拒絕該回合（`state_source="none"`）而不是排隊等。
- **沒有檔案鎖的主機自己說出來**：`availability()["lock"]` 是 `flock`／`msvcrt`／
  `none`，`multi_writer_safe` 隨之為真／假；`none` 時載入 checkpoint 記**一次** warning
  （不是每回合，那只會把噪音埋掉），並要求只開一個 worker。

**實測（測試，不是宣告）**：

| 情境 | 結果 |
| --- | --- |
| 12 個執行緒同時推進同一個 session | 12 個全部落地，版本 `1..12` 不重複、遞增 |
| 2 個**真實進程**各推進 5 回合 | 最終版本 `19`（`1 + 2×9`：建立那回合只 +1，之後每回合 `al_step`＋`ai_step` 各 +1）——一次更新都沒掉 |
| 另一個進程持有 `flock` | 在 0.25 秒後拒絕（`LOCK_TIMEOUT_S` 於呼叫時改成 0.25），釋放後下一回合正常 |
| 一個**合法**存檔（有效 checksum）但沒拿鎖的寫入者 | `version conflict: read 1, disk has 2`，拒絕覆寫，對方狀態留在磁碟上 |
| `meta.json` 在回合中途消失 | 拒絕（`cannot verify the version on disk`），不復活一個看不見歷史的狀態 |

最後兩列是這一輪**修掉的兩個真缺陷**：第三道鎖原本只在「版本不同」時拒絕，檔案讀不出來
（`None`）卻繼續寫——那會把一個失去歷史的狀態寫成一個看起來正常的新版本；同一段
`_disk_version` 的 docstring 原本就寫著「refusal, not overwrite」，是文件與程式不一致，
以程式為準修好並補測試。另外 `_windows_lock` 把 `msvcrt` 的常數用 `getattr` 讀：POSIX
上那個 stub 沒有 `locking`／`LK_NBLCK`，用 `# type: ignore` 會花掉專案零容忍的 ignore
預算去掩蓋一個永遠不會在那裡執行的分支。

### 42.3 所有權：狀態要說得出它是誰的

- 新狀態把 `user_id` 寫進 invariant 欄位；續接時若呼叫端帶了 `user_id` 而檔案裡的是
  另一個非空值，**拒絕**（`state belongs to 'alice', not 'bob'`），檔案不動。
- **空主人的舊狀態接受**：§41 的 run 建立狀態時還沒有這個欄位，把它們回溯作廢等於用
  一個新欄位宣告過去的量測無效。
- 這不是身分驗證：它擋的是「不小心共用」與「檔案說不出主人」，擋不了呼叫端謊報
  `user_id`。要擋那個需要真正的認證，不在這一輪。
- 回覆 provenance 也多了 `user_id`，所以「這回合推進的是誰的狀態」在回覆裡可被檢查。

### 42.4 量測：2,208 回合的真實路徑（2026-11-13，登記 run 實測）

`scripts/probe_core_turns.py` 走**真正的** `_handle_chat_request`（`trace_reply.py` 用的
同一個入口），把凍結標準集整輪整輪地跑（不截斷最後一輪，否則尾端 stratum 會無故缺額），
五個 stratum 各一個 session，逐回合寫 JSONL 到 `data/core_turns/`（gitignored）。
checkpoint 是**未訓練**的 SSM（26 tokens、hidden 64、emb 32）——這一節量的是載體，
不是模型。

| session | 回合 | `state_version` | 最終 `ticks` | 拒絕 | 第一回合建立 |
| --- | --- | --- | --- | --- | --- |
| `core-turns-claim` | 216 | 1→431 | 215 | 0 | 是 |
| `core-turns-dialogue` | 200 | 1→399 | 199 | 0 | 是 |
| `core-turns-multi` | 160 | 1→319 | 159 | 0 | 是 |
| `core-turns-qa` | 984 | 1→1967 | 983 | 0 | 是 |
| `core-turns-state` | 648 | 1→1295 | 647 | 0 | 是 |

- 總計 **2,208 回合／1,545 秒（1.43 回合/秒）**；by stratum：
  `claim 216／dialogue 200／multi 160／qa 984／state 648`（每輪 1,104 題，跑兩輪）。
- **版本嚴格遞增**，而且每一個 session 都恰好是 `2n−1`：`al_step` 一次、`ai_step` 一次，
  建立那回合只 +1。這是「一次更新都沒掉」的可檢查形式，掉一次就紅。
- **拒絕 0 次**：2,208 個回合全部由 state 物件承載（`state_source="core"`），沒有任何
  一回合退回 prompt 載體。
- `dt_s`：2,203 個回合 > 0（每 session 第一回合是 0，因為那是建立、不是續接），中位數
  **2.24 秒**、最大 **42.3 秒**。中位數是**回覆層**的處理時間（回合背靠背跑，中間沒有
  sleep），最大值是載入模型／抓取的時間——兩者都不是核心成本。
- `all_pass = True`（五項檢查：回合數、零拒絕、版本嚴格遞增、五個 stratum 都在、每一回合
  都由核心承載）。
- 狀態落在沙盒 `data/probe_native_dialogue/core_state/state/<digest>/`：探針只寫
  gitignored 的 `data/`，量測不污染被量的環境。

**怎麼讀**：這證明「同一個 state 物件在真實回合迴圈裡連續 2,208 次都是唯一寫入者，沒有
一次更新被覆寫」。它**不**證明狀態有用——回覆仍由表層產生。

### 42.5 這一節**沒有**證明什麼（照實寫）

1. **沒有任何東西把 state 讀回生成**。核心不產生文字，prompt 不讀它，router 不讀它。
   核心分仍 **0.00/10**；這輪的成果是「載體在多回合、多寫入者的情況下不會壞」。
2. **`schema_version` 只有 v1，沒有 migration**。不符就拒絕（寧可拒絕，不可靜默重置），
   但 P5 清單上的「版本遷移」只做了**拒絕那一半**。要真的 migration 需要一個 v2 schema
   與它的測試；這裡沒有先寫一個空殼假裝做過。
3. **tokenizer 仍是 `hash-bucket` 佔位**：2,208 回合的 state 內容沒有語言意義。要讓
   它有，是 P2 的訓練工作。
4. **回合速度不是核心成本**：1.43 回合/秒是**回覆層**的速度（模板／知識／路由），
   核心只佔其中很小一段；§40.7 的 0.55× forward 是合成任務的計算量，兩者不可互相換算。
5. **in-memory 訊息歷史仍是每進程一份**：多 worker 對**核心狀態檔**是安全的（R3），
   對聊天歷史不是（既有問題，本輪未處理）。
6. **不是多使用者並發壓力測試**：2,208 回合是同一台機器、同一個進程、五個 session
   依序跑；併發只出現在測試裡（12 執行緒、2 進程）。

### 42.6 指令

```bash
# 載體：2,208 回合的真實路徑量測（沙盒；約 26 分鐘；gate 不過就 exit 1）
./.venv/bin/python scripts/probe_core_turns.py --turns 2000

# R3：27 條 runtime 測試（12 執行緒、2 進程、flock 持有者、合法卻沒拿鎖的寫入者、
# 中途消失的 meta.json、主人不符、空主人被接受、不可讀的版本）
./.venv/bin/python -m pytest tests/ai/test_stateful_runtime.py -q

# gate 自己的測試（掉一次更新／一次拒絕／少一個 stratum 都必須 all_pass=False）
./.venv/bin/python -m pytest tests/test_probe_core_turns.py -q
```

## 四十三、狀態有沒有內容：把東西記住、再從生成讀回來（2026-11-13，量測前寫定）

§37–§42 證明的是**載體**：一份權重、一個 state 物件、一次更新都沒掉。它們全都
刻意避開同一個問題——**state 裡裝的東西有沒有語言內容，生成會不會讀它**。
P4 的 `state_source="core"` 只說「連續性由 state 承載」，回覆仍由表層產生；
2,208 回合的 tokenizer 是 crc32 的 26 個桶，內容沒有意義。核心分因此一直是
**0.00/10**，而且不是因為量測保守，是因為**沒有任何一條路徑把 state 讀回生成**。

這一節要回答的就是那一條：**模型能不能把一個它剛看到的字串放進 state，跨過一個
回合邊界，再用它生成答案。** 這是核心分要動的**前置條件**；它本身不動分數
（這一輪用的不是任何 benchmark 的題目，也沒有接進生產）。

### 43.1 為什麼不是「直接上 benchmark」

因為現在上 benchmark 只會量到一件事：核心答不出來。那已經知道了，而且它分不出
三種完全不同的原因——(a) 模型沒有把輸入記住的機制；(b) 有記住但生成讀不到；
(c) 有記住、讀得到，但不知道那些知識。三者的修法完全不同，先量那個分不出原因的
數字只是把 0 再寫一次。

所以這一輪把任務縮到**只有 (a)(b) 能解釋成敗**的形狀：答案只存在於 state 裡，
prompt 裡沒有；沒有檢索、沒有模板、沒有字典。成功＝state 真的有內容且生成讀它，
失敗＝這條路在目前規模上不通，而且知道是哪一半不通。

### 43.2 任務族（固定，不調）

**跨回合綁定**（carry the binding）。一個「回合」是契約裡的回合，不是一句話：

| 回合 | 輸入 | 損失 | 說明 |
| --- | --- | --- | --- |
| 1（教） | `remember <name> = <value> .` | **不算** | 只推進 state；模型不需要學「記住了」 |
| 中間 | `al_step(120.0)` | — | 生產路徑每回合都有時間推進；兩個 chunk（`max_chunk_s=60`） |
| 2（問） | `<name> ?` | **只在答案上算** | 模型必須生成 `<value> .` |

> **修訂（在任何量測之前，2026-11-13）**：第二回合原本寫的是單一個 `?`。寫下之後
> 發現那樣**名字與答案無關**——state 只需要記住「最近一個值」，名字只是裝飾，
> 於是「沒見過的名字」那個切分什麼都量不到。改成 `<name> ?`：state 必須記住一組
> **配對**，而且必須用問句裡的名字去選它。這是把任務改成它原本要量的東西，
> 不是看過結果之後放寬；當時**還沒有跑過任何一次訓練或評估**（這一節的 commit
> 在任何 run 之前）。

- `<value>` 是由 **CV 音節**拼出來的字串（子音×母音，2–4 個音節，長度 4–8），
  字元集固定且封閉。它**不在**第二回合的輸入裡，也不在任何檢索表裡。
- 兩個回合是**兩次 `ai_step`**，中間一次 `al_step`——不是把兩句接成一個序列。
  這一點是刻意的：接成一個序列的話，模型可以靠「最近看過的字串」的區域模式過關，
  那量不到跨回合的載體。
- 生成是**貪心解碼**，從 `?` 之後的第一個位置開始，遇 `.` 或長度上限停止；
  和訓練時的 teacher forcing 不同，這裡沒有任何 gold token 餵回去。

### 43.3 為什麼是「沒見過的名字／沒見過的值」

如果測試用的名字和值都在訓練集裡出現過，那通過的可能是一張表，不是一個機制。
所以三個切分的**每一個**都只由「訓練時沒看過的字串」組成：

| 切分 | 名字 | 值 | 用途 |
| --- | --- | --- | --- |
| `train`（20,000 對） | 池 A | 池 A | 訓練 |
| `dev`（3,000） | 池 A 的**新組合** | **沒看過的字串** | G1：機制學起來了嗎 |
| `heldout_names`（3,000） | **沒看過的名字**（新音節組合） | **沒看過的字串** | G2：能不能複製一個全新的字串 |
| `cold`（3,000） | 同 `heldout_names` | 同 `heldout_names` | G4：**沒有**教的那個回合 |

`cold` 是同一批題目但**跳過第一回合**：state 是零。它同時抓兩種假通過——「答案
其實來自 prompt」與「模型只是在吐高頻字串」。

另一條**診斷**（不進 gate，因為它量的是「配對有沒有被使用」而不是「內容有沒有被
攜帶」）：`wrong_name`——教 `<name> = <value>`，問一個**沒教過**的名字，記下模型
仍然吐出 `<value>` 的比率。若這個比率很高而 G2 也高，那答案其實是「把 state 裡
唯一的值端出來」，不是查詢；兩者要分開記錄。

洩漏檢查是機械的：三個切分的值字串集合與訓練集**交集必須為空**，名字集合也一樣；
產生器把切分與檢查碼寫進報告，重跑得到同一份資料（固定種子）。

### 43.4 架構（固定，跑之前寫下）

- 臂：`ai.core.stateful_decoder.GRUCore`——**既有**的 P1 臂，不是新模型。這一輪
  不新增架構，只給它一個有意義的詞表與一個會讀它的任務。
- `token_count` ＝ 字元集（子音＋母音＋數字）＋ `SPECIALS` ＋ `.`／`?`；`hidden=128`、
  `emb=64`、`chunk_seconds=60`、`seed=20261113`。
- 最佳化：Adam，學習率 `3e-3`，batch 128，最多 24 epochs，`dev` 的 exact match
  連續 3 個 epoch 沒進步就停（早停看 dev，不看 held-out）。
- 裝置：`core.system.config.compute_device.resolve_torch_device()`（本機解析到 `xpu`）。
- 這一輪**不調**：hidden/emb/學習率/epoch 上限都在跑之前寫死；跑完不改再跑一次
  挑好看的。要換設定＝新的一輪、新的預註冊。

### 43.5 通過條件（跑之前寫定）

| 代號 | 條件 | 意思 |
| --- | --- | --- |
| **G1** | `dev` exact ≥ **0.60** | 在「看過名字風格、沒看過值」上，機制學得起來 |
| **G2** | `heldout_names` exact ≥ **0.30** | 能複製一個**完全沒見過**的字串（跨回合） |
| **G3** | `heldout_names` 零狀態 ablation exact ≤ **0.05**，且 G2−G3 ≥ **0.25** | 答案真的來自 state，不是別的地方 |
| **G4** | `cold`（沒有教的那回合）exact ≤ **0.02** | 沒有 state 就答不出來（與 G3 互為獨立證據） |
| **G5** | 成本記錄完整（參數量、訓練秒數、每次 forward 秒數、裝置） | 可比較，不是宣稱 |

- **G3 的 ablation**：教完之後、問之前把 `state.tensors["h"]` 歸零（同一個 state
  物件、同一份權重、同一個 prompt）。這不是「換一個模型」，所以差距只能來自 state。
- **`al_step` 的兩半都記**：主數字是**有** `al_step(120)` 的（生產路徑的形狀）；
  另記一個**沒有** `al_step` 的診斷數字，看時間衰減有沒有傷害。診斷不進 gate。

### 43.5a 結果（2026-11-13，登記 run 實測；門檻未改）

`./.venv/bin/python scripts/train_state_content.py --out data/state_content`（登記設定：
hidden 128、emb 64、lr 3e-3、batch 128、上限 24 epochs、dev exact 連續 3 epoch 沒進步
就停）。跑完 9 個 epoch 就停了。

| 代號 | 門檻 | 實測 | |
| --- | --- | --- | --- |
| G1 `dev` exact | ≥ 0.60 | **0.001** | FAIL |
| G2 `heldout_names` exact | ≥ 0.30 | **0.000** | FAIL |
| G3 零狀態 ablation / 差距 | ≤ 0.05 且 ≥ 0.25 | **0.000** / 0.000 | FAIL |
| G4 `cold` exact | ≤ 0.02 | **0.000** | PASS |
| G5 成本 | 完整 | params 81,765／訓練 42.9 s／0.0009 s/回合 | PASS |

`all_pass = False`。字元準確率把形狀講清楚了：`dev` **0.447**、`zero_state` **0.138**、
`cold` **0.138**（後兩者逐位相同）——**state 確實帶了東西**（+0.31 字元準確率），
但不足以指認那 6 個字元；零狀態與冷啟一模一樣，說明 ablation 與「沒有教」是同一個
狀態，量測本身沒有接錯。

### 43.5b 診斷：資訊掉在哪一段（不是門檻，是定位）

| 診斷 | 字元 | 全對 | 讀法 |
| --- | --- | --- | --- |
| teacher-forced `dev` | 0.681 | 0.001 | 給定 gold 前綴時，下一個字元有 68% 對（亂猜約 0.135）→ **資訊在 state 裡，head 也讀得到一部分** |
| teacher-forced `heldout_names` | 0.682 | 0.000 | 同上，且**沒有**因為名字沒見過而變差 |
| 線性 probe `dev`（只讀 `h`） | 0.391 | 0.000 | 只給 `h`、一個線性層：0.391 ≫ 0.135 → 內容**部分**線性可解 |
| 線性 probe `heldout_names` | 0.389 | 0.000 | 同上 |

所以不是「完全沒有記住」，也不是「記住但讀不到」，是**記得不夠**——足夠讓
teacher forcing 猜對三分之二的字元，不夠讓自由生成指認整個字串。自由生成一旦
第一步偏掉就再也回不來，於是 exact 是 0。

**還有一個協定缺陷，這才是真正該修的**：早停看的是 `dev` 的 **exact**，而 exact
在模型幾乎全對之前一直是 0（它是階躍函數，不是連續訊號）。實測曲線：
loss `1.546 → 1.201 → 1.007 → 0.955 → 0.926 → 0.901 → 0.882 → 0.860 → 0.845`，
`dev_char` `0.198 → 0.383 → 0.446 → … → 0.518`——**兩者都還在往下走**，
`dev_exact` 卻卡在 0.000–0.001，於是「連續 3 個 epoch 沒進步」在第 9 個 epoch
成立，訓練在 24 個 epoch 的預算用掉 37% 時被自己的規則停掉。

§43.6 的對照表把「G1 < 0.60」寫成**容量**問題。照實說：這個對照表**錯了**，
證據不支持容量。它是協定問題（用一個階躍訊號當早停條件），而診斷（teacher-forced
0.68、probe 0.39）正好指出了「再多訓練一點可能就跨過去」。這一點寫在這裡，而不是
把表格改成對自己有利的說法。

### 43.5c 開發集上的確認（throwaway seed 777；不是登記的 held-out）

在**另行抽樣的**資料（seed 777，與登記 run 的 seed 20261113 無關）上，只改訓練
長度、其餘不動，量到：

| 臂 | epochs | params | `dev` exact | `heldout_names` | `zero_state` | `cold` |
| --- | --- | --- | --- | --- | --- | --- |
| hidden 128 | 60 | 81,765 | **1.000** | **1.000** | 0.000 | 0.000 |
| hidden 256 | 60 | 310,949 | **1.000** | **1.000** | 0.000 | 0.000 |

- **容量不是瓶頸**：登記的 128 在足夠的訓練下就全對了，不需要放大到 256。
- 這一列是**開發**，不是結果：它用來決定下一輪要改什麼（只改訓練長度），
  而且它用的資料與登記的 held-out 無關。真正的確認在 §44，用**另一個沒用過的
  seed**（20261114）。
- 同一份診斷也確認了零狀態／冷啟仍然是 0.000：不是「剛好猜中」，是真的靠 state。

### 43.6 原本寫的失敗對照表（保留；它錯在哪見 43.7）

| 觀察 | 讀法 | 下一步 |
| --- | --- | --- |
| G1 < 0.60 | 82k 參數在這個任務上學不起來 | 這是**容量**問題，不是載體問題；先加寬再談，不調任務 |
| G1 過、G2 < 0.30 | 記住了訓練看過的名字，新字串複製不出來 | **表化**，不是機制。誠實記為否定 |
| G2 過、G3 > 0.05 | 答案不是來自 state（洩漏或猜中） | 這一輪作廢，先找洩漏 |
| G2 過、G3 過、G4 > 0.02 | 沒有 state 也能答 → 上面兩條的證據都不可信 | 同上，先找洩漏 |
| 全過 | state 有內容、生成讀它、移除就掉 | **這才是核心分可以開始動的前置條件**；下一輪才接 benchmark 的題型 |
| 全過但 `wrong_name` 很高 | 值被攜帶了，配對沒有被使用 | 內容這半成立、查詢那半不成立，照實分開寫 |

**這一輪不管結果如何，都不會改變核心分**：它用的不是 benchmark 題目，也沒有接進
生產回覆。會改的是「核心分 0.00 的原因」——從「不知道是沒有機制還是沒有知識」
變成「知道」。

### 43.7 這一節判定（照實）

- 登記的門檻**全部維持不動**，登記的那個 run **FAIL**。不能因為「多跑幾輪就會過」
  就回頭改登記的次數。要改，是下一輪、另一份預註冊。
- 這一輪真正的產物有三個，而且都不是分數：(1) 一個可裁決的任務族與機械洩漏檢查；
  (2) 「資訊部分在 state 裡」的可量測證據（teacher-forced 0.68／probe 0.39）；
  (3) 一個協定缺陷——用階躍訊號早停——以及它對應的修法。
- 核心分**不變**（**0.00/10**）：這一輪用的不是任何 benchmark 題目，也沒有接進生產。

### 43.8 指令

```bash
# 資料＋訓練＋四種評估，一份 JSON 報告（暫存目錄；不寫入 data/ 以外的東西）
./.venv/bin/python scripts/train_state_content.py --out data/state_content

# 產生器與洩漏檢查的測試（切分交集為空、重跑可重現、cold 與 heldout 同題）
./.venv/bin/python -m pytest tests/test_state_content_task.py -q
```

## 四十四、把訓練長度修好之後：同一個任務、同一組門檻（2026-11-13，量測前寫定）

§43 的登記 run 失敗，但失敗的位置是**協定**，不是模型：早停看 `dev` 的 exact，
而 exact 在模型幾乎全對之前一直是 0，於是訓練在第 9／24 個 epoch 被停掉，當時
loss 與字元準確率都還在下降。開發集（throwaway seed 777）顯示同一個 128-hidden
臂在 60 個 epoch 下 `dev` 與 `heldout_names` 都是 **1.000**、零狀態與冷啟 **0.000**。

這一輪只改**一個**東西：訓練長度與早停規則。任務、資料產生器、臂、大小、學習率、
batch、`al_step` 間隔、五條門檻——**全部不動**。

### 44.1 改了什麼，為什麼只有這個

| 項目 | §43（登記） | §44 |
| --- | --- | --- |
| 上限 epochs | 24 | **60** |
| 早停 | `dev` exact 連續 3 epoch 沒進步 | **關閉**（`--patience 0`） |
| 其餘 | — | 完全相同 |

早停關閉而不是換一個訊號：exact 是階躍函數、loss 會一直被「多數正確」的佔位答案
壓低，兩者都不適合當停止條件；在一個**固定、寫在跑之前**的預算下跑完，然後取
`dev` 最好的 checkpoint，比再發明一個啟發式規則乾淨。60 是開發集上「loss 已經到
`1e-4` 以下、`dev` 早已 1.000」的長度，不是「剛好過線」的長度。

### 44.2 新鮮的 held-out

§43 的 held-out 已經被讀過一次（那是它的工作）。為了不讓「同一個測試集被用兩次」
這件事有任何解釋空間，§44 用**另一個種子**（`--seed 20261114`）重新抽一份資料；
`train`／`dev`／`heldout_names`／`cold`／`wrong_name` 的關係與洩漏檢查完全不變。
seed 777 那一輪是**開發**，不進結果表。

### 44.3 門檻（與 §43 逐字相同，不重訂）

- **G1** `dev` exact ≥ 0.60
- **G2** `heldout_names` exact ≥ 0.30
- **G3** `zero_state` exact ≤ 0.05，且 G2 − G3 ≥ 0.25
- **G4** `cold` exact ≤ 0.02
- **G5** 成本完整（params／訓練秒數／每回合秒數／裝置）

### 44.4 預測與失敗的意思

- **預測**：G1／G2 過，G3／G4 仍然過（零狀態與冷啟在開發集上一直是 0.000）。
- G1 過、G2 不過 → 記住了訓練看過的名字風格，新字串複製不出來（表化）。
- 全過但 `wrong_name` 很高 → 值被攜帶、配對沒被使用（診斷，不進 gate）。
- 全不過 → §43.5c 的開發結果是抽樣運氣或程式缺陷，照實記，並先找缺陷。

### 44.5 指令

```bash
# §44：唯一改動是 --epochs 60 --patience 0，資料用新 seed
./.venv/bin/python scripts/train_state_content.py \
    --seed 20261114 --epochs 60 --patience 0 --out data/state_content
```

### 44.6 結果（2026-11-13，登記 run 實測；門檻未改）

`./.venv/bin/python scripts/train_state_content.py --seed 20261114 --epochs 60 --patience 0`
——與 §43 唯一的差別就是這兩個旗標。資料是**另一個種子**（`20261114`），洩漏檢查
`clean=True`（值交集 0、名字交集 0、`<unk>` 0）。

| 代號 | 門檻 | 實測 | |
| --- | --- | --- | --- |
| G1 `dev` exact | ≥ 0.60 | **0.994** | PASS |
| G2 `heldout_names` exact | ≥ 0.30 | **0.995** | PASS |
| G3 零狀態 / 差距 | ≤ 0.05 且 ≥ 0.25 | **0.000** / **0.995** | PASS |
| G4 `cold` exact | ≤ 0.02 | **0.000** | PASS |
| G5 成本 | 完整 | see below | PASS |

`all_pass = True`。

| 量測 | exact | 字元準確率 |
| --- | --- | --- |
| `dev`（看過的名字風格、沒看過的值） | 0.994 | 0.999 |
| `heldout_names`（沒看過的名字＋沒看過的值） | **0.995** | 0.999 |
| `zero_state`（同題、同權重、同 prompt，`h` 歸零） | **0.000** | 0.135 |
| `cold`（跳過教學回合） | **0.000** | 0.136 |
| `heldout_names_no_al`（不呼叫 `al_step`） | **0.003** | 0.312 |
| `wrong_name`（教 A、問沒教過的 B） | **0.994** | 0.999 |

診斷：teacher-forced `dev` 0.999／`heldout` 0.999（全對 0.994／0.995）；線性 probe
`dev` 0.846／`heldout` 0.851（全對 0.285／0.308）。成本：**81,765 參數**、訓練
**271.6 秒**（60 epochs，XPU）、評估 16,000 回合 2.42 秒（**0.00015 秒/回合**）。
`dev` 的曲線是慢啟動：epoch 1–6 的 exact 是 0.000–0.021，epoch 10 才 0.238，
epoch 20 到 0.877——**這正是 §43 用 exact 早停會誤殺的形狀**。

**重載驗證**：把存下來的 checkpoint 重新載進一個全新的 `GRUCore`（CPU），
`heldout` 前 200 題 exact **0.995**、零狀態 **0.000**，config 與詞表一致。報告裡的
數字不是只在訓練進程裡成立。

### 44.7 這一輪證明了什麼，以及它**沒有**證明什麼

**證明（可重跑、有對照）**：在一個答案只存在於 state 的任務上，一個 81,765 參數的
GRU 把一個**沒見過**的字串放進 state、跨過一個回合邊界（含一次 `al_step(120 s)`），
再從生成把它完整讀回來（`heldout` 0.995，字元 0.999）；把 `h` 歸零（**同一個物件、
同一份權重、同一個 prompt**）或跳過教學回合，都掉到 **0.000**。teacher-forced 與
線性 probe 都接近滿分，說明失敗與成功都不是量測接錯。

**沒有證明（照實，而且其中兩條是這一輪自己量到的）**：

1. **名字沒有被使用**：`wrong_name` **0.994**——教 A、問一個沒教過的 B，模型照樣
   吐出 A 的值。所以這是**單槽攜帶**，不是鍵值查詢。「state 有內容」成立，
   「依查詢選取」不成立。§43 的診斷就是為這件事準備的，它給出的答案是「配對沒有
   被使用」。
2. **不是間隙不變的**：把 `al_step` 拿掉，exact 從 0.995 掉到 **0.003**。模型學到
   的是「經過**一次** 120 秒的 `al_step` 之後可讀」，不是「無論多久都記得」。
   生產路徑本來就每回合推進一次，所以這不是 bug，但它是一條**邊界**：這一輪沒有
   量多個不同的 `dt`。
3. **不是語言**：詞彙是封閉的 CV 音節字母表（19 個字母），句型只有一種。這是
   **機制**的證明，不是「會說話」。
4. **沒有接進生產**：`stateful_runtime` 的 tokenizer 仍是 `hash-bucket`，回覆仍由
   表層產生。核心分**不變**（**0.00/10**）——這一輪用的不是任何 benchmark 題目，
   也沒有任何一條路徑把這個 checkpoint 的輸出當成回覆。把它接進去會是一句只能講
   `remember X = Y` 的模型，那比不接更糟。
5. **`dev` 是開發集，`heldout` 才是分數**：§43.5c 的 seed 777 是開發，`20261114`
   是這一輪才第一次用的。兩者都沒有被用來調門檻。

### 44.8 下一輪的三個候選（照重要性排）

1. **讓名字真的被使用**（`wrong_name` 要掉到 0）：多槽、或教學回合一次給兩三組，
   問其中一組。這是把「攜帶」變成「查詢」的一步，也是唯一能讓這個機制有用的一步。
2. **間隙不變**：訓練時 `dt` 從分佈抽（例如 30／60／120／240 秒），量「同一個
   state 在不同 gap 下的召回率」。現在的 0.003 就是沒有做這件事的代價。
3. **換成自然的詞彙**：把 CV 音節換成真實英文詞／子詞，任務不變。這一步才開始
   接近「狀態有語言內容」，但需要的資料與模型都大一個量級，應該在前兩項站穩之後。

### 44.9 驗證指令

```bash
# 任務本身的契約（13 條：洩漏、可重現、cold 同題、答案不在問句裡、零狀態真的歸零）
./.venv/bin/python -m pytest tests/test_state_content_task.py -q

# checkpoint 重載（數字不是只在訓練進程裡成立）
./.venv/bin/python - <<'EOF'
import torch, importlib.util, sys
spec = importlib.util.spec_from_file_location("tsc", "scripts/train_state_content.py")
m = importlib.util.module_from_spec(spec); sys.modules["tsc"] = m; spec.loader.exec_module(m)
ckpt = sorted(__import__("glob").glob("data/state_content/*.pt"))[-1]
payload = torch.load(ckpt, map_location="cpu", weights_only=True)
table = m.CharTable(); core = m.build_core(table, "cpu")
core.load_state_dict(payload["state_dict"]); core.eval()
print(m.evaluate(core, table, m.build_splits(seed=20261114)["heldout_names"][:200], device="cpu")["exact"])
EOF
```

### 44.10 記錄缺陷與重現性重跑（2026-11-13，重跑之前寫定）

§44.6 的**數字**是那次 run 的數字，但存下來的報告把**設定**記錯了：`config.max_epochs`
寫的是模組預設 `24`、`early_stop_patience` 寫的是 `3`，實際跑的是 CLI 給的 `60`／`0`。
這叫「記錄的 run 不是跑的 run」——與分數無關，但必須修：下一個人照報告重跑會得到不同
的東西，而且從檔案看不出是誰對。

修法：`config` 改記**生效值**（`max_epochs = 2 if --smoke else --epochs`、
`early_stop_patience = --patience`）。修完之後用**完全相同**的指令與 seed 再跑一次，
當作**重現性檢查**，不是第二次嘗試：

- 兩個 run 的數字都會寫出來，**不論新的比較好還是比較差**。
- 若 `heldout_names`／`zero_state` 有變動，照實記差值——那代表 XPU kernel 的非決定性
  要寫進限制，而不是挑一個好看的 run。
- 不因為重跑而改任何門檻、資料、臂或 epoch 數。

### 44.11 重跑結果（2026-11-13，登記的重現性檢查）

同一個指令、同一個 seed（`--seed 20261114 --epochs 60 --patience 0`），程式碼只差
§44.10 的 `config` 記錄修正（`git_head ea19eaedf`）。報告：
`data/state_content/state_content_20261113-014220.json`（gitignored）。

| 量測 | §44.6 | §44.11 | 差 |
| --- | --- | --- | --- |
| `dev` exact／char | 0.994／0.999 | 0.994／0.999 | 0 |
| `heldout_names` exact／char | 0.995／0.999 | 0.995／0.999 | 0 |
| `heldout_names_no_al` | 0.003／0.312 | 0.003／0.312 | 0 |
| `zero_state` | 0.000／0.135 | 0.000／0.135 | 0 |
| `cold` | 0.000／0.136 | 0.000／0.136 | 0 |
| `wrong_name` | 0.994／0.999 | 0.994／0.999 | 0 |
| teacher-forced `dev`／`heldout` | 0.999／0.999 | 0.999／0.999 | 0 |
| 線性 probe `dev`／`heldout` | 0.846／0.851 | 0.846／0.851 | 0 |

不只數字相同：五個切分的 digest、`best_epoch`（51）、`epochs_run`（60）、
`weights_hash`（`sha256:6b5e331d46cdb…`）都逐位相同，訓練 271.6 秒、81,765 參數、
0.00015 秒/回合。`config` 現在記的是 `max_epochs: 60`、`early_stop_patience: 0`，
與實際跑的一致。

讀法：**在這個裝置、這個 seed 上這次訓練是決定性的**，所以 §44.6 的數字不是抽樣運氣；
先前那份報告的錯只在「設定記成模組預設」，不在數字。門檻、資料、臂、epoch 數都沒有
因為重跑而改動。

## 四十五、一次記兩組：state 是「槽」還是「記憶」（2026-11-13，量測前寫定）

§44 讓 state 第一次裝了**有內容**的東西，但它自己量出三條邊界，第一條最致命：
`wrong_name` **0.994**——教 A、問一個沒教過的 B，模型照樣吐 A 的值。所以那是一個
**單槽緩衝區**（「最近一次的值」），不是**鍵值記憶**（「你問哪個，我答哪個」）。
名字是裝飾，查詢沒有被使用。

這一輪問的就是那一句：**同一個 state 能不能同時持有兩組配對，並由查詢選一組？**

### 45.1 任務（兩個教學回合，問其中一組）

一個 episode：

1. 教學回合 1：`remember <name A> = <value A> .` → `ai_step` → `al_step(120 s)`
2. 教學回合 2：`remember <name B> = <value B> .` → `ai_step` → `al_step(120 s)`
3. 查詢回合：`<name A> ?` **或** `<name B> ?`（各半）
4. 生成 `<value> .`

四個回合是**四次 `ai_step`**（教學不計損失），不是把四句接成一個序列；查詢回合的
輸入裡**沒有值**，所以 state 是唯一通道——與 §43／§44 同一條規則。與 §44 的差別只有
「兩組配對」與「查詢要選一組」；字母表、句型、`al_step` 間隔、模型臂、寬度、學習率、
batch 全部相同。

**單槽緩衝區在這個任務上的上限是 0.5**（永遠回同一個值，而答案各半），所以任何
高於 0.5 的 exact 都必須來自「選對」。

### 45.2 唯一的變數：訓練目標（`single` vs `both`）

| 臂 | 教學回合 | 損失涵蓋的查詢 | 為什麼 |
| --- | --- | --- | --- |
| `single` | 兩組 | **只有**被抽中的那一組（與 §44 同形狀） | 對照組：目標從來沒要求「兩組都要答得出來」 |
| `both` | 兩組 | **兩組都算**，各自從同一組教學結果、**全新的 state** 出發 | 目標不能再靠「帶一個值、兩邊都賭它」滿足 |

`both` 的每一題都從**新的 state** 出發（重新跑兩個教學回合），與評估時的形狀逐位
相同——兩臂的差別因此只有「哪些查詢進了損失」，沒有「序列佈局」這個額外變數。
評估一律是**一個查詢、一個全新 state**，所以訓練時若學到位置捷徑，會被 `by_ask`
（兩個位置各自的分數）抓到。

### 45.3 開發證據（seed 777；**這不是結果**，只是選預算與檢查設計）

開發用的資料種子 777 與登記的 20261115 無關，這一節的數字不進結果表，也不當分數。

| 設定（100 epochs、20,000 教學 episode、81,765 參數） | `dev` exact | `heldout_names` exact | `h` 的線性 probe（字元） |
| --- | --- | --- | --- |
| `single`（本輪臂） | 0.0033 | 0.0020 | slot0 0.301／slot1 0.379／asked 0.283 |
| `both`（本輪臂） | 0.0017 | 0.0013 | slot0 0.362／slot1 0.383／asked 0.285 |
| 加寬到 256（另一種佈局，先前診斷） | — | 0.057 | 0.42／0.47／0.34 |

參考點：§44 的**單一組**配對在同一個臂上 probe 是 **0.85**、exact 0.995；這裡三條
probe 全部落在 0.28–0.38（chance ≈ 0.027），**兩個槽都不可讀**。加寬到 256 讓訓練
loss 從 0.68 掉到 0.196，held-out exact 只從 0.010 升到 0.057，probe 仍然不到 0.5。

讀法（開發階段結論，登記 run 要測的是它在新 seed 上成不成立）：**兩組配對不是
「寫進去了但選不出來」，而是根本沒有被寫進去**；而且把它寫進去不是目標的問題——
目標換了，兩個槽一樣不可讀。

### 45.4 預算（跑之前寫定）

| 項目 | 值 |
| --- | --- |
| 臂 | `GRUCore`，`hidden=128`、`emb=64`，**81,765 參數**（與 §44 同一個臂） |
| epochs | **100** |
| 早停 | **關閉**（`--patience 0`） |
| checkpoint 選擇 | **dev 的 teacher-forced 答案損失最低**的那個 epoch（不是 exact） |
| 資料量 | train 20,000／dev 3,000／held-out 3,000／`wrong_name` 1,000 episodes |
| 學習率／batch | 3e-3／128 |
| `al_step` 間隔 | 120 秒，每回合一次 |
| 資料 seed | **20261115**（沒用過；777 是開發，20261114 已被 §44 用掉） |
| 模型初始化 seed | 固定（兩臂**同一組初始權重**，所以差異只能來自目標） |

**為什麼是 100 而不是更多**：開發曲線在 100 個 epoch 時 dev 損失還在緩慢下降
（`single` 0.950、`both` 0.891），但斜率約每 10 個 epoch 下降 0.02；§44 的任務在
exact 跳到 0.994 之前，loss 已經到 **0.008**。從 0.89 到那個量級是兩個數量級以上，
不是把 100 加到 200 能跨過的距離（加寬到 256 已經把訓練 loss 壓到 0.196，exact 仍
只有 0.057）。這一點**寫在跑之前**，這樣 FAIL 就不能被解釋成「預算給太少」。

**checkpoint 用損失選、不用 exact 選**：exact 是階躍函數，在模型接近全對之前一直是
0；以 exact 選，長時間的平手會讓「第一個 0」的那個 epoch 永遠勝出（§43 就是被這個
訊號停掉的，`--patience 0` 只關掉早停、沒修好選擇）。損失是連續的，可以在 exact
還讀 0 的時候說「這個 epoch 比較好」。exact 仍然照記，只是不用來選。

### 45.5 門檻（B1–B6，跑之前寫定，不得事後改）

| 代號 | 條件 | 意思 |
| --- | --- | --- |
| **B1** | `dev` exact ≥ **0.60** | 機制在訓練看過的名字上學得起來 |
| **B2** | `heldout_names` exact ≥ **0.30** | 沒見過的名字＋沒見過的值，仍能選對並複製 |
| **B3** | `heldout_names` 零狀態 ablation exact ≤ **0.05**，且 B2−B3 ≥ **0.25** | 答案來自 state，不是別的地方 |
| **B4** | `cold`（跳過教學回合、**同一批題目**）exact ≤ **0.02** | 沒有 state 就答不出來 |
| **B5** | `dev` 與 `heldout_names` 兩邊的 `by_ask` 全部 ≥ **0.50**，且兩邊 `other_value_rate` ≤ **0.25** | 是**選對**，不是「兩個位置都賭同一個值」 |
| **B6** | 成本記錄完整（參數量、訓練秒數、每次評估秒數、裝置） | 可比較 |

- **B5 是這一輪的核心**：單槽緩衝區的 `by_ask` 會落在 0.5 附近、`other_value_rate`
  ≈ 0.5（另一半答成另一組的值）。所以「exact 高」不夠：兩個位置都要各自選對，而且
  **答成另一組值的比例要低**。
- **B3 的 ablation** 與 §43／§44 相同：教完之後、問之前把 `state.tensors["h"]` 歸零
  （同一個物件、同一份權重、同一個 prompt）。
- **`wrong_name` 不進門檻**（登記為診斷）：教兩組、問第三個沒教過的 key，量
  `taught_value_rate`——單槽會接近 1.0，鍵值記憶應該接近 0。

### 45.6 對照組 C1（不是門檻，但沒有它就沒有結論）

同一個臂、同一個資料 seed（20261115）、**一組**配對的 §44 任務必須仍然過它自己的
門檻（`heldout_names` ≥ 0.30、零狀態 ≤ 0.05）。理由：如果連一組都學不起來，這一輪
的 FAIL 只說明「這個 seed／這個臂當時壞了」，不能說明「兩組很難」。C1 用 §44 的
`scripts/train_state_content.py --seed 20261115 --epochs 60 --patience 0`。

### 45.7 每一個分支要怎麼讀（先寫定，避免事後解釋）

| 觀察 | 讀法 | 下一輪 |
| --- | --- | --- |
| `both` 過 B1–B6、`single` 不過 | **目標是槓桿**：差別只在「哪些查詢進損失」 | 往「間隙不變」或「自然詞彙」推 |
| 兩臂都過 | 目標不是必要條件 | 檢查 `single` 的 `by_ask` 是否靠位置 |
| 兩臂都 < B1，但 **slot0／slot1 都可讀（≥0.5 字元）**、`asked` 不可讀 | **選取**是瓶頸：東西有寫進去，查詢沒有被用來選 | 明確的 key 位址化（查詢決定讀哪一格） |
| 兩臂都 < B1，且**只有一個槽可讀** | **寫入覆蓋**是瓶頸：第二次寫入蓋掉第一次 | 多槽寫入路徑 |
| 兩臂都 < B1，且**兩個槽都不可讀（<0.5 字元）** | **根本沒有寫進去**——不是選取問題，也不是覆蓋問題 | 結構：固定大小的 state 沒有位址；改成 key 位址化的槽，或對教學回合做注意力 |
| `both` 過 B1／B2 但 `by_ask` 有一邊 < 0.50 | **位置捷徑**（記住「第二個問題」而不是「被問的 key」） | 視為 FAIL（B5），下一輪把查詢位置隨機化 |
| `both_sequential`（診斷）高、單題 exact 低 | 目標教的是**序列**不是**綁定** | 記錄為目標設計缺陷，不當分數 |

登記時已知（開發階段看到）這一輪會落在**第五列**（兩臂都不可讀）。把它寫進來不是
事後解釋，而是把「已知會失敗的實驗為什麼還要做」講清楚：seed 777 是開發用的，
登記 run 用的是沒用過的 20261115、沒見過的名字與值——被確認的是**否證**本身，不是
一個能過的實驗。

### 45.8 預測（寫在跑之前）

- `single` 與 `both` 都會 **FAIL B1/B2/B5**；兩臂的差別在雜訊內。
- 零狀態與冷啟會是 0.000（它們在開發階段就是 0，而且任務本身讓「沒有 state 也能猜對」
  幾乎不可能）。
- C1（單一組、同一個 seed）會 **PASS**。
- 若 C1 反而失敗，這一輪作廢，先修 C1 的協定。

### 45.9 診斷（不是門檻）

1. **`h` 的線性 probe**：分別解碼「第一組教的值」「第二組教的值」「被問的值」。
2. **`by_ask`**：ask=0 與 ask=1 各自的分數。
3. **`other_value_rate`**：答成另一組值的比例（單槽的特徵）。
4. **`wrong_name.taught_value_rate`**：問沒教過的 key 卻吐出教過的值。
5. **`both_sequential`**：同一個 state 依序問兩題，分辨「綁定」與「序列」。
6. **每個 epoch 的 dev 損失**：用來判斷「還沒收斂」與「已經到牆」的差別。

### 45.10 指令

```bash
# 兩臂：同一份資料、同一組初始權重，只有 --objective 不同
./.venv/bin/python scripts/train_state_binding.py \
    --objective single --seed 20261115 --width 128 --epochs 100 --patience 0 \
    --out data/state_binding
./.venv/bin/python scripts/train_state_binding.py \
    --objective both   --seed 20261115 --width 128 --epochs 100 --patience 0 \
    --out data/state_binding

# C1：同一個臂、同一個 seed、一組配對的 §44 任務（對照組，不是門檻）
./.venv/bin/python scripts/train_state_content.py \
    --seed 20261115 --epochs 60 --patience 0 --out data/state_content

# 任務自己的契約（24 條：洩漏偵測器被故意餵壞、cold 同題、兩個教學回合是兩個序列、
# ask 兩邊都出現、wrong_name 問的是沒教過的 key、`_teach` 真的是兩次 ai_step、
# checkpoint 用連續訊號選）
./.venv/bin/python -m pytest tests/test_state_binding_task.py -q
```

### 45.11 結果（2026-11-13，登記 run 實測；門檻未改）

`git_head d9aacbc5e`（= 預登記的那個 commit），資料 seed **20261115**，兩臂同一個
81,765 參數的 `GRUCore`、同一組初始權重，唯一差別是 `--objective`。

| 量測 | `single` | `both` | 門檻 |
| --- | --- | --- | --- |
| `dev` exact | 0.0033 | 0.0097 | B1 ≥ 0.60 |
| `heldout_names` exact | **0.0033** | **0.0100** | B2 ≥ 0.30 |
| 零狀態 ablation exact | 0.0000 | 0.0000 | B3 ≤ 0.05 |
| `cold` exact | 0.0000 | 0.0000 | B4 ≤ 0.02 |
| `other_value_rate`（held-out） | 0.0020 | 0.0037 | B5 ≤ 0.25 |
| `by_ask`（held-out） | 0.0019／0.0048 | 0.0110／0.0090 | B5 每個 ≥ 0.50 |
| `wrong_name.taught_value_rate` | 0.004 | 0.010 | 診斷 |
| `both_sequential`（診斷） | 0.0023／0.0007 | 0.0107／0.0010 | 診斷 |
| 訓練秒數／最佳 epoch | 577.6 s／87 | 1,103.9 s／100 | B6 |
| 最佳 dev 答案損失 | 1.007 | 0.741 | — |

`h` 的線性 probe（held-out，字元準確率；chance ≈ 0.027）：

| | slot0（第一組教的值） | slot1（第二組教的值） | asked（被問的值） |
| --- | --- | --- | --- |
| `single` | 0.319 | 0.413 | 0.303 |
| `both` | 0.351 | 0.383 | 0.280 |

**判定：兩臂都 FAIL**（B1／B2／B3／B5 不過，B4／B6 過）。預測成立。

**C1（對照組，同一個 seed、一組配對、同一個臂）**：
`data/state_content/state_content_20261113-033723.json`，60 epochs、237.2 秒，
`dev` **1.000**、`heldout_names` **1.000**、零狀態 **0.000**、`cold` **0.000**、
`wrong_name` **1.000**、probe 0.874、teacher-forced 1.000——**它自己的五條門檻全過**。
所以這個 seed、這個臂、這個裝置沒有壞：**一組配對 1.000，兩組配對 0.003–0.010**。

### 45.12 這一輪證明了什麼，以及它**沒有**證明什麼

**證明（登記 run、C1 對照）**：一個 81,765 參數的 GRU 在**同一個 seed** 上
可以學到「跨回合攜帶一個值」（1.000），**但不能**學到「同時持有兩組、由查詢選一組」
（0.003／0.010，比門檻低一到兩個數量級，也比一組配對低 100–300 倍）。

**照實記的六點**：

1. **不是「寫進去了但選不出來」**：兩個槽的 probe 都在 0.28–0.41 字元，而一組配對
   是 0.87。資訊**根本沒有被寫進去**——這是 §45.7 表格的第五列，登記前就寫下來了。
2. **不是目標的問題**：換了目標，結果類別不變。兩臂的**排序在兩個 seed 上翻轉**
   （開發 seed：0.0020 vs 0.0013；登記 seed：0.0033 vs 0.0100），所以在這些比率上
   「三倍」是雜訊。`both` 一致的差別是**比較好擬合**（dev 損失 0.741 vs 1.007，最佳
   epoch 100 代表還沒收斂），但沒有跨過任何東西。
3. **不是寬度的問題**：加寬到 256 把訓練損失壓到 0.196，held-out exact 只有 0.057
   （§45.3）。寬度讓訓練集更可分，沒有讓 state 多一個位址。
4. **`other_value_rate` 低不是「不賭」**：兩臂的 `other_value_rate` 只有 0.002–0.004，
   但那是因為模型**兩組的值都沒答出來**（吐出第三個字串），不是因為它選對了。所以
   B5 必須同時要求 `by_ask ≥ 0.50`，只看「沒有答成另一組」會把一個壞掉的模型讀成
   很乾淨。這一點登記時就寫進 B5，這一輪剛好是它的反例。
5. **零狀態與冷啟是 0.000**（同一個 state 物件歸零、同一批題目跳過教學）：不是
   「剛好猜中」——但也**不代表**答案來自 state（一個什麼都沒學到的模型在任何輸入下
   都答不出來）。通過 B3／B4 不構成能力證據，B1／B2 才是。
6. **不是語言，也沒有接進生產**：封閉 CV 音節、單一句型；`stateful_runtime` 仍是
   `hash-bucket` tokenizer；核心分**不變**（**0.00/10**）。

**這一輪的結論是一條設計要求，不是一個分數**：可定址性（addressing）不能靠
「同一個 128 維向量連續覆寫兩次」長出來。下一輪要改的是**結構**——key 位址化的槽
（查詢決定寫／讀哪一格），或對教學回合做注意力——不是預算、不是寬度、不是目標。

### 45.13 驗證指令

```bash
# 任務本身的契約（24 條）
./.venv/bin/python -m pytest tests/test_state_binding_task.py -q

# 兩份登記報告與 C1（報告在 gitignored 的 data/；這裡只驗證關鍵欄位與判定）
./.venv/bin/python - <<'EOF'
import json, glob
for path in sorted(glob.glob("data/state_binding/state_binding_*_2026*.json")):
    d = json.load(open(path))
    if d["config"]["seed"] != 20261115:
        continue
    r = d["results"]
    print(d["objective"], "heldout", r["heldout_names"]["exact"],
          "zero", r["zero_state"]["exact"], "cold", r["cold"]["exact"],
          "pass", d["all_pass"])
c1 = json.load(open(sorted(glob.glob("data/state_content/state_content_20261113-033723.json"))[-1]))
print("C1 heldout", c1["results"]["heldout_names"]["exact"], "pass", c1["all_pass"])
EOF
```

## 四十六、換結構：可定址的槽（2026-11-13，量測前寫定）

§45 的結論不是分數，是**設計要求**：addressability（鍵定址的槽，或對教學回合做
attention）不會從「同一個 128 維向量被覆寫兩次」裡長出來。這一輪就改**結構**，
其餘一律不動——任務、字母表、間隔、目標函數、seed、預算、寬度、學習率、batch 全部
沿用 §45，讓「結構」是唯一的變數。

### 46.1 任務：與 §45 完全相同（不是新題目）

兩個教學回合（各自 `ai_step` ＋ `al_step(120 s)`）→ 問其中一組 → 生成該組的值。
單槽的上限仍是 0.5。`build_splits(seed=20261115)` 的切分、digest、`wrong_name`
控制全部重合，所以 §45 的 `both` 臂（held-out **0.0100**）就是這一輪的**同任務、
同資料、同預算**對照。

### 46.2 唯一的變數：state 由「一個向量」變成「向量 ＋ 可定址的槽」

| | §45（`GRUCore`） | §46（`SlotMemoryCore`） |
| --- | --- | --- |
| state 張量 | `h` | `h`、`slot_k [4,64]`、`slot_v [4,64]` |
| 寫入 | 只有遞歸覆寫 `h` | **讀先於寫**；寫入是 `slot ← slot(1-gw) + gw·new` |
| key／value 哪來 | 無 | `W_k h`／`W_v h`，與讀取同一個 `h` |
| 讀取 | 無 | `softmax(scale·W_q h · slot_kᵀ)` 加權 `slot_v` |
| 讀取去哪裡 | — | 輸出頭 **與下一步的控制器輸入**（`cell([x, r_prev])`） |
| 誰決定寫哪格 | 無 | `softmax(scale_w·W_w h)`（學習得來） |
| 參數 | 81,765 | 134,124（+64%） |

**不是外掛的字典**：寫入分布、寫入強度、key、value、查詢向量全部是 `h` 的函數，
共用同一組權重，由 `ai_step` 寫、由 `al_step` 推進同一個狀態物件；沒有任何
`store(key, value)` API 讓訓練器繞過模型。讀取在**寫入之前**發生，所以問題讀到的
是「教過的內容」，不是它自己。

**讀取必須進到下一步的控制器**（第一版沒有，跑之前改掉）：只把讀取接到輸出頭，
store 只能影響**一個**解碼字元；而答案有八個字元、要跨八步生成，值在第二步就
掉了。這是接線的限制，不是 store 的限制——留著會讓 FAIL 讀成「記憶無法定址」，
而真正的理由是「值沒地方放」。改成 `cell([x, r_prev])` 之後，讀到的內容跟著遞歸
往前走，八個字元都還在。

`al_step` 只推進 `h`（與 `GRUCore` 同一條算式、同一個 `dt_proj`），**槽不隨時間
衰減**：位址是內容，時間作用在控制器上。這是先寫定的設計選擇，代價是這一輪**不能**
拿「跳過 `al_step`」（T5）當證據。

### 46.3 開發證據（seed 777；**這不是結果**，只確認管線會動）

3,000 訓練 episodes、12 epochs、`both`、寬度 128；不進任何表格、不改任何門檻。

| | 第一版（讀取只接輸出頭、診斷讀寫入後） | 現行（讀取進控制器、診斷讀寫入前） |
| --- | --- | --- |
| dev loss（ep 1 → 12） | 1.5168 → 1.1038 | 1.5316 → **1.2706** |
| `distinct_read_slot_rate` | 0.000 | **0.152** |
| `read_cosine_between_asks` | 1.000 | **0.9754** |
| 讀取注意力最大機率（平均） | 0.948 | 0.518 |

**兩個接線缺陷，都在跑任何計分 run 之前修掉，並記錄理由**：

1. **診斷量錯了向量**。第一版在 `ai_step` 之後才讀 `attention()`／`read_vector()`，
   那已經是「問題自己寫進去之後」的 store，不是產生答案的那次讀取。於是量到
   `distinct_read_slot_rate` 0.188——看起來像「位址分開了」，其實是問題的字改了
   自己那一格。改成 `ai_step(..., return_trace=True)` 回傳**每個 token 寫入前**的
   讀取與定址權重之後，同一個訓練掉到 **0.004**（第一版接線）／0.152（現行接線）。
   「看起來變好」的數字正是要懷疑的那一種。
2. **讀取只接輸出頭**（見 §46.2）：store 只能影響一個字元，八個字元的答案跨不過去。
   改成讀取餵進下一步的控制器輸入。這不是調分數，是讓這一臂**有辦法**表達任務；
   留著會讓 FAIL 的說法失真。

寫入閘的初始值也先寫明：`slot ← slot(1-s) + s·new` 是移動平均，`sigmoid(0)=0.5`
時記憶視窗約 2 個 token，**記住兩組在結構上不可能**，量到的會是初始值而不是設計。
bias −2（0.12／token，九個 token 的回合留下約 68%）是「記憶控制器先慢慢寫、再學
什麼時候 commit」的先驗；寫什麼、寫哪格、怎麼定址仍然全部要學。

開發曲線兩者都還在下降（12 epochs 只走了登記預算的 1/8 資料量），所以「收斂不夠」
不是這一輪的結論，登記 run 仍用 §45 的 100 epochs。

### 46.4 預算（跑之前寫定）

| 項目 | 值 | 理由 |
| --- | --- | --- |
| seed | 20261115 | 與 §45 登記 run 相同，切分與 digest 重合 |
| 目標函數 | `both` | §45 的兩個目標同類；`both` 的 dev loss 較低且是登記臂 |
| epochs | 100 | 與 §45 相同；不因這一輪較慢而縮短 |
| 選檔 | 最低 dev answer loss，`--patience 0` | 與 §45 相同（exact 是階梯函數） |
| 寬度／嵌入／間隔／lr／batch | 128／64／120 s／3e-3／128 | 全部沿用 §45 |

**參數對照規則（先寫定，構模型即可知，不必等結果）**：若新臂參數超過 §45 的 81,765
的 20%，就必須跑 C3——**同樣參數量的純 GRU**。新臂 134,124（+64%）→ **C3 成立**，
寬度取「≥134,124 的最小 GRU 寬度」＝**hidden 176（136,821 參數）**。

### 46.4b 修訂記錄（在 `36769fb0b` 之後、**任何計分 run 之前**，逐條列出）

§46.2–§46.4 的第一次提交版寫的是 109,548 參數／C3 `--width 154`。在跑任何計分 run
之前，三個**裝置缺陷**被找到並修掉；因為它們改變參數量，這裡不是「偷偷改數字」，是
把修訂寫成修訂。三條都只讓這一臂**有能力**表達任務，沒有一條在調門檻或看結果：

| # | 缺陷 | 為什麼留著會讓結論失真 | 修法 |
| --- | --- | --- | --- |
| A1 | 診斷在 `ai_step` **之後**讀 store | 量到的是「問題自己寫進去之後」的狀態，不是產生答案的那次讀取。第一版因此報 0.188 的 `distinct_read_slot_rate`，看起來像位址分開了 | `ai_step(..., return_trace=True)` 回傳**每個 token 寫入前**的讀取／定址權重；同一訓練掉到 0.004（舊接線） |
| A2 | 讀取只接到輸出頭 | store 只能影響**一個**解碼字元；答案是八個字元、跨八步生成，值在第二步就沒了。留著會把「值沒地方放」讀成「記憶無法定址」 | 讀取餵進下一步的控制器輸入 `cell([x, r_prev])`；`al_step` 期間讀取為 0 |
| A3 | 寫入閘 bias 初始化為 0（`sigmoid(0)=0.5`） | `slot ← slot(1-s)+s·new` 每 token 寫掉 50%，記憶視窗約 2 個 token → 「記住兩組」**結構上不可能**，量到的是初始值 | bias −2.0（0.12／token，九 token 回合留下約 68%） |

**連帶的數字**（構模型即可知，不是結果）：本臂 **109,548 → 134,124** 參數（+64%
於 §45 的 81,765）。§46.4 的規則是「超過 20% 就跑 C3，寬度取 ≥ 本臂的最小 GRU」，
所以 C3 由 `--width 154`（109,871）改為 **`--width 176`（136,821）**。門檻 B1–B8
的**數字一個都沒動**。

### 46.5 門檻（跑之前寫定，不得事後改）

B1–B6 的**數字完全不動**（不是為這一輪重訂的），只把 B3 的「zero」說清楚：

| 門檻 | 條件 |
| --- | --- |
| B1 | `dev` exact ≥ 0.60 |
| B2 | `heldout_names` exact ≥ 0.30 |
| B3 | `zero_state` ≤ 0.05 且 `heldout − zero_state` ≥ 0.25 |
| B4 | `cold` ≤ 0.02 |
| B5 | 兩個切分的 `by_ask` 皆 ≥ 0.50，且 `other_value_rate` ≤ 0.25 |
| B6 | 成本（參數、訓練秒數）已記錄 |
| **B7** | 同結構、**拿掉 store** 的消融（R4）：`heldout − 消融 heldout` ≥ **0.20** |
| **B8** | C3（參數 ≥ 本臂的純 GRU）的 `heldout` < **0.30** |

**B3 的措辭修訂（跑之前，且更嚴）**：§45 的 state 只有一個張量，所以「zero state」
等於「zero `h`」。現在 state 有三個張量，只清 `h` 會把答案留在槽裡——那會讓一個
**正確**的狀態看起來違反 B3。所以 B3 定義為**清空 state 的所有張量**。這不是放寬：
清的比 §45 多。逐張量的結果另外列為**診斷**（`zero_h_only`、`zero_store_only`），
不是門檻。

B7／B8 是門檻而非註記，理由和 §43–§45 一致：沒有消融，「是 store 在做事」是宣稱；
沒有參數對照，「是結構」也可能是「是參數」。**兩個對照報告都必須存在**（缺一個
`B7_control_present`／`B8_control_present` 直接 FAIL），且 digest 必須與本 run 相同
（`*_control_same_splits`），否則對照不算數。

### 46.6 對照組（都需要，且在計分 run 之前跑完）

| | 內容 | 期望 |
| --- | --- | --- |
| **C2** | `--core slots --no-memory`：參數一個不少，讀取恆為 0、不寫入 | 掉回 §45 那一類（B7 差 ≥ 0.20） |
| **C3** | `--core gru --width 176`：136,821 參數 ≥ 本臂 134,124 | 仍不足 B2（< 0.30），否則「是參數」 |
| （參考）| §45 `both`（81,765 參數，held-out 0.0100） | 不重跑：digest 與預算相同 |

### 46.7 每一個分支要怎麼讀（先寫定）

| 結果 | 讀法 |
| --- | --- |
| B1–B8 全過 | 可定址的 state 讓同一個核心持有兩組並依查詢選取；**核心分不因此改變**（這是 state 的結構，不是語言能力），下一步才是把它接到生成 |
| B1/B2 過、B7 不過 | 值是真的，但消融也做得到 → 不是 store 的功勞（多半只是參數變多）→ 這一輪不算證明 |
| B1/B2 過、B8 不過 | 純 GRU 在同等參數下也過 → 是參數量，不是「可定址」 |
| B2 不過、`distinct_read_slot_rate` 明顯 > 0 | 位址分開了但讀到的內容對不上 → 問題在寫入的 key/value，不在定址 |
| B2 不過、`distinct_read_slot_rate` ≈ 0 | 兩個問題仍讀同一格 → 學習沒有把槽分開，下一步是對教學回合做 attention（把整個回合的表示留在 state 裡，由查詢去 attend），不是再調這一臂 |
| B3 不過 | 答案不是從 state 來的 → 整個裝置有問題，先修裝置 |

### 46.8 預測（寫在跑之前）

**B1 過**（同一個任務、單槽 0.5 上限，dev 是訓練過的切分）；**B2 不確定，偏不過**
（現行接線的 dev loss 在 12 epochs 降到 1.2706 且仍在下降，但正確答案是階梯函數，
loss 這一階降完 exact 才會跳；同時 `distinct_read_slot_rate` 只有 **0.152**，位址
只分開了一小部分——若 100 epochs 後仍停在這個量級，B2 會落在 0.10–0.30）；**B5 可能
不過**（讀取不夠果斷時 `by_ask` 會有一邊偏低）；**B7 預期過**（消融就是 §45 的那一類，
0.01 附近）；**B8 預期過**（§45 已量到參數不是瓶頸）。若 B2 落在 0.10–0.30，這一輪
的結論會是「位址需要更強的結構」，而不是「記憶不可能」。

### 46.9 診斷（不是門檻）

* `zero_h_only`／`zero_store_only`：答案住在控制器還是槽裡（B3 只要求「全部清空」）。
* probe 兩個特徵：`h`（控制器）與 `read`（實際定址到的內容），各對第一組、第二組、
  被問的那組做線性讀出。§45 只有 `h`，所以分不出「沒存」與「存了但選不出來」。
* `addressing_*`：`distinct_read_slot_rate`（兩個問題讀到同不同格）、
  `read_cosine_between_asks`、`attention_max_prob_mean`。
* `both_sequential`：同一 state 依序問兩組（訓練形狀），與單問的差距。

### 46.10 指令（順序固定：對照先，計分 run 最後）

```bash
# C3：同樣參數量的純 GRU（136,821 ≥ 134,124）
./.venv/bin/python scripts/train_state_binding.py --core gru --width 176 \
    --objective both --seed 20261115 --epochs 100 --patience 0 --out data/state_binding
# C2：同結構、拿掉 store（參數一個不少）
./.venv/bin/python scripts/train_state_binding.py --core slots --no-memory \
    --objective both --seed 20261115 --epochs 100 --patience 0 --out data/state_binding
# 計分 run（帶兩個對照，B7／B8 才算得出來）
./.venv/bin/python scripts/train_state_binding.py --core slots \
    --objective both --seed 20261115 --epochs 100 --patience 0 --out data/state_binding \
    --control <C2 report>.json --control <C3 report>.json
```

### 46.11 執行記錄（三件儀器事件，先寫，因為它們差一點讓這一輪沒有結果）

1. **C2 第一次（18:37–18:51）死於 GPU 共享**：`RuntimeError: level_zero backend
   failed with error: 20 (UR_RESULT_ERROR_DEVICE_LOST)`，發生在 backward。當時同一張
   Intel Arc 上還有文字階段的 toy run 與 pytest（都以 `xpu` 跑）。不是模型問題，是
   量測衛生問題：**登記 run 進行中，其他 torch/XPU 工作一律不得啟動**；toy run 與測試
   一律 `--device cpu`。
2. **C2 第一次重跑（18:52–19:19）跑完 100 epochs 才死在診斷**：
   `addressing_diagnostics` 對 `--no-memory` 臂取 `trace["attention"]`，得到
   `'NoneType' object is not subscriptable`。消融臂依定義沒有 attention 權重，崩潰是
   **儀器的錯**，而且錯在訓練之後——26 分鐘的對照整個丟掉。修法（`47cbed7d0`）：消融臂
   回 `{"applicable": false, "reason": ...}`，不回 `None`、不丟例外，並加回歸測試，讓
   下一次在**訓練前**就能用 `--smoke` 走完整條診斷路徑。
3. **第一個 driver 在控制失敗後仍啟動計分 run**（`--control` 接到空路徑），B7 註定算不
   出來。第二個 driver 在兩個對照報告都存在之前拒絕啟動計分 run。順帶修掉 `all_pass`：
   `checks` 裡同時放布林門檻與 B7／B8 的數字，`all(value is True ...)` 讓**任何**全過的
   run 也不可能回 `True`（`0.1557 is not True`）；`verdict()` 只數布林，且至少要有
   一個（`722fec7ec`）。這一輪的判定不受影響（B1/B2/B3/B5/B7 用自己的述詞就不過）。

這三件事的共同點：每一件都會讓「看起來有跑」變成「沒有結果」。所以寫在結果前面，而
不是附註。

### 46.12 結果（2026-11-13，xpu，獨佔；順序＝對照先、計分 run 最後）

| 臂 | 參數 | 訓練 | dev exact | held-out exact | best dev loss @ epoch |
| --- | --- | --- | --- | --- | --- |
| C3 純 GRU，`--width 176`（B8 的對照） | 136,821 | 1,293 s | 0.1547 | 0.1557 | 0.4212 @ 91 |
| C2 `slots --no-memory`（B7 的消融） | 134,124 | 1,670 s（100 ep） | 0.1270 | **0.1233** | 0.4316 @ 100 |
| **A `slots`（計分）** | 134,124 | 5,047 s（100 ep），wall 5,070 s | **0.0007** | **0.0000** | 0.1290 @ 59 |

三份報告：`state_binding_gru_both_20261113-181527.json`、
`state_binding_slots-ablate_both_20261113-192129.json`、
`state_binding_slots_both_20261113-194934.json`（都在 `data/state_binding/`）。三者的
split digest 相同（`1bd42bc6c07762b7`／`acefd33d73f3c946`／`4dbf4939a9cb808b`／
`3e30de58992eec76`），所以真的是同一份資料，不是「換了切分剛好變好／變壞」。

**A 的其餘讀數**：

* `zero_state`／`zero_h_only`／`zero_store_only`／`cold` 全部 **0.0000**；
  `wrong_name` 的 `taught_value_rate` **0.001**。
* `both_sequential`（訓練形狀，同一個 state 依序問兩組）：key0 0.0007、key1 0.0000。
  連它自己訓練時看到的形狀都沒有。
* **讀取探針**：`read` 對第一組／第二組教過的值 char **0.589／0.593**、full
  0.008／0.010；`h` 只有 0.202／0.527、asked 0.344。結構化 6 字值（CVCVCV）的 char
  chance 是 **0.1333**、full **2.4e-6**，所以**兩組值都真的在 store 裡，而且是線性可
  讀的**——不是「沒存進去」。
* **定址**：`distinct_read_slot_rate` dev **0.0000**／held-out **0.0003**、
  `read_cosine_between_asks` **0.9998**、`attention_max_prob_mean` **0.97**。兩個問題
  讀到同一格，而且讀得很果斷。
* **生成**：`other_value_rate` **0.0000**——吐出來的字串不是「另一組教過的值」，是
  **兩組都不是**（alphabet 內、值域外的音節串）。所以這不是「hedging 到另一個答案」，
  是解碼本身壞了。

### 46.13 門檻判定（B1–B8，數字一個都沒動）

| 門檻 | 條件 | 量到 | 判定 |
| --- | --- | --- | --- |
| B1 | dev exact ≥ 0.60 | 0.0007 | **FAIL** |
| B2 | held-out exact ≥ 0.30 | 0.0000 | **FAIL** |
| B3 | `zero_state` ≤ 0.05 **且** held-out − zero ≥ 0.25 | 0.0000；gap 0.0000 | **FAIL**（前半過，後半不過） |
| B4 | `cold` ≤ 0.02 | 0.0000 | PASS |
| B5 | 兩個切分 `by_ask` 皆 ≥ 0.50，且 `other_value_rate` ≤ 0.25 | 0.0000／0.0000；0.0000 | **FAIL** |
| B6 | 成本已記錄 | 134,124 參數、5,047 s、xpu | PASS |
| B7 | held-out − 消融 held-out ≥ 0.20 | 0.0000 − 0.1233 = **−0.1233** | **FAIL** |
| B8 | C3（參數 ≥ 本臂）held-out < 0.30 | 0.1557 | PASS |

**B8 的讀法**：它問的是「參數是不是解釋」。matched GRU 只有 0.1557 → 不是。**B7 的
方向跟預期相反**：不是「加了 store 沒有幫助」，是**加了 store 比沒有它更差**
（0.0000 vs 0.1233）。這一條比 B1／B2 更值得記，因為它排除了「只是還沒學會」以外的
另一種解釋——它學會了**用一種會壓壞解碼的方式**去用 store。

### 46.14 這一輪的結論（照實，含預測錯誤的部分）

§46.8 寫的預測是：B1 過、B2 偏不過、B5 可能不過、B7／B8 預期過。實測 B1、B2、B5
不過（方向對，幅度比預測差得多：預測 B2 落在 0.10–0.30，實際 0.0000），**B7 不過且方向
相反**，B8 過。不一致的部分比一致的部分有資訊：

1. **「記不住」不是這一輪的失敗點**。store 讀得到兩組值（線性探針 0.589／0.593，
   chance 0.1333；full 0.008／0.010，chance 2.4e-6），所以問題不在容量、也不在寫入
   閘。§46.4b 的 A3（寫入率）修對了。
2. **失敗點是「選不出來」，而且是飽和式的選不出來**：兩個問題的 attention 幾乎逐位相
   同（cosine 0.9998、distinct 0.0）、`max_prob` 0.97。它學會「每次讀同一格」，而且
   很果斷。單槽的行為原封不動搬進多槽——這正是 §46.1 說「單槽最多 0.5」想排除的形狀，
   只是這次更低：連那一格都答不對。
3. **接線比定址更早壞**：同參數、只是沒有讀寫的 C2 還有 0.1233（`h` 本身就帶得住一部分
   值），接上讀取的 A 掉到 0.0000，且 `other_value_rate` 0.0。也就是說 §46.4b 的 A2
   （讀取餵進 `cell([x, r_prev])`）在這一輪被量到**會壓壞解碼**，不只是「幫助有限」。
   對照之下，`h` 的 asked 探針 0.344 也說明 A 的控制器裡還有資訊，只是輸出頭沒把它變成
   字。
4. 因此下一輪的問題不是「再加一格」「再寬一點」「多訓練」。要換的是**定址訊號的來
   源**：兩個教導回合是兩個時間步，鍵（名字）寫在裡面；現在的 attention 只有一組可學習
   的查詢，沒有「這是哪一個回合」的訊號，所以它只能學到一個常數位置。round 8 要登記的
   是「讀取對齊教導回合（per-turn keys）」**以及**讀取與控制器的接法（A2 已被證明會壓
   壞解碼）——**先登記再跑**，在登記寫下來之前不開計分 run，也不在這一節裡預告它會過。
5. 這一輪**沒有**證明「多綁定記憶不可能」，只證明「用一組全域查詢去讀一個可寫槽，在這
   個預算與接線下不會分工」。核心分不變（**0.00/10**），生產路徑未接。§47 的文字階段仍
   照登記先跑：語言能力會改變 pantry 的量測，而 round 8 只是把同一個合成任務修好。

## 四十七、先給核心語言能力：byte-level 文字階段（2026-11-13，量測前寫定）

### 47.1 為什麼順序要改

§45／§46 量的是「state 能不能記住兩組綁定」，答案是：128 維的單一向量不行，四個可定址的槽也還不確定。但
pantry v2 之後出現一個更前面的問題——**如果核心連「把一段話讀進去」都做不到，pantry 就會被迫用一堆約束去補語言**，
而量到的會是那些約束，不是推理。所以這是最後一次改順序，不是又一次調參：

```
文字階段 L（本節）  →  推理階段 P（另案登記）
byte-level 語言模型      在 L 的權重上做 pantry
```

本節**只**登記 L。P 要另外登記，因為它改的是任務表徵（把 37 個 CV 音節換成 byte），不是同一個任務的變體。
把 L 和 P 寫在同一份登記裡，等於事前允許「P 不過就說 L 過了」。先分開。

### 47.2 登記什麼、不登記什麼

| | 內容 |
| --- | --- |
| **登記** | 一個 byte-level 的 `GRUCore`（同一個類別、同一份 `CoreState`）能不能學會下一個 byte，並且**生成**（不是只會評分） |
| **不登記** | pantry 的轉移。L 過不代表 P 會過；P 的門檻與指令另外寫 |
| **不改** | 核心分、系統分、既有門檻、既有評測題。這一節是設備，不是分數 |

### 47.3 語料（跑之前寫定，不得事後改）

| 來源 | 訓練 | 留出 |
| --- | --- | --- |
| 一般英文 | `apps/backend/data/processed/core_train.jsonl`，前 **3,000,000 bytes**（整行，不切半行） | `apps/backend/data/processed/core_val.jsonl`，前 **300,000 bytes**（整行） |
| 茶水間口供 | `scripts/gen_pantry_ecosystem.py --sessions 1000 --seed 20261113` 的 **train** 切分：800 sessions、**1,014,924 bytes** | 同一份的 **held-out** 切分：200 sessions、**254,050 bytes** |

* 一般英文的每一行 = `input + " " + output + "\n"`；口供的每一行 = `"\n".join(turn["user_input"]) + "\n"`。
* 留出的一般英文是**另一個檔案**（`core_val.jsonl`），不是我從 train 切一段——它是既有的、資料準備腳本已經分好的切分。
* **偏離（照實記）**：口供的**句型**在 train 與 held-out 之間共用。這是刻意的：L 學的是語言，P 才是用沒見過的
  答案 tuple 量推理。L 的留出仍然是**沒見過的 200 個 session**，不是同一段文字。
* 文字流**不得**包含 `ground_truth_oracle` 的任何欄位；L6 會逐 session 掃 `evidence_tag`。

### 47.4 表徵與模型（不新增類別）

| | 值 | 理由 |
| --- | --- | --- |
| 詞表 | byte：`0=<pad>`、`1=<bos>`、`2=<eos>`、`3..258 = byte 0..255` | 可逆（`decode(encode(x)) == x`），沒有未登錄詞，也沒有 tokenizer 的訓練/推論不一致 |
| `token_count` | **259** | 由詞表決定，不是調出來的 |
| 模型 | `ai.core.stateful_decoder.GRUCore(token_count=259, hidden=128, emb=64, chunk_seconds=60.0)` | **同一個類別**、同一份 `CoreState`（schema v1）。L5 檢查這件事 |
| 輸出 | 每個位置對 259 個 byte 的 logits | BPC 直接是 byte 的 BPC，沒有「每 token 幾個 byte」的換算空間 |

### 47.5 預算（跑之前寫定）

| | 值 |
| --- | --- |
| seed | **20261116** |
| 優化器 | Adam，lr **1e-3** |
| batch | **32** 條獨立 stream |
| window | **L = 128 bytes** |
| state 重置 | 每 **4096 bytes** 一次（truncated BPTT；不是每個 window 都重置） |
| epochs | **5**（不做 early stopping） |
| device | `core.system.config.compute_device.resolve_torch_device()` 決定，報告記錄 |

### 47.6 門檻（跑之前寫定，不得事後改）

| 門檻 | 條件 |
| --- | --- |
| **L1** | 留出 BPC **<** 插值 **bigram** 的 BPC（同一批 bytes；λ 在 train 內部最後 5% 上選，留出只用量） |
| **L2** | 留出 BPC **<** 插值 **trigram** 的 BPC（同上） |
| **L3** | 100 個留出 prefix 的 greedy 24-byte 續寫：(a) distinct ≥ **90**；(b) 平均最長共同前綴 **>** trigram 的 |
| **L4** | 帶著 state 的留出 BPC **<** 每個 window 重置 state 的 BPC（同權重、同 bytes） |
| **L5** | checkpoint 的 `model_kind == "gru"`、`state_schema == 1`，且 `GRUCore.load_weights()` 能載入 |
| **L6** | 文字流不含任何 session 的 `evidence_tag`，也不含 oracle 欄位 |
| **L7** | 成本（參數、秒數、device）已記錄 |

L1／L2 的基準是**可計算的**，不是我訂的數字：λ 由 train 決定，留出只拿來量。L3 用 trigram 當對照，不用
「像不像人話」這種沒有儀器的標準；「distinct ≥ 90」防的是 TOK-SNN 那種模式崩潰（40 題只有 2 個不同答案），
不是品質分數。L4 的對照是**同一個權重**在「不給 state」下的分數——這和 §45 的 B3 是同一個邏輯：沒有這個對照，
「state 有用」只是宣稱。

### 47.7 每一個分支要怎麼讀（先寫定）

| 結果 | 讀法 |
| --- | --- |
| L1 過、L2 不過 | 模型用了 1–2 個 byte 的上下文，沒用到更多。讀法是「規模/資料不足」，不是「架構壞了」 |
| L1 不過 | 連 bigram 都沒贏：表徵或訓練有缺陷，**不得**進入 P，先修 L |
| L3(a) 不過 | 模式崩潰（只會吐少數幾種續寫）——這是生成能力缺失，不是分數低 |
| L4 不過 | state 沒有被使用；「跨 window 的記憶」是宣稱，不是事實 |
| L5 不過 | 文字階段與 pantry 不是同一個載體；後續的轉移宣稱一律不成立 |
| 全過 | 只證明「核心能壓縮並生成文字」。**不證明** pantry、不證明推理、不改變核心分 |

### 47.8 預測（寫在跑之前）

* L1：**會過**。byte bigram 在英文上大約 3.2–3.6 BPC；124k 參數的 GRU 在 4 MB 上應該在 2.0–2.6。
* L2：**不確定**。trigram 大約 2.8–3.2；這個規模可能只贏一點，甚至不贏。
* L3(a)：**會過**。L3(b)：**邊緣**。
* L4：**會過**（否則等於沒學到跨 window 的東西）。

### 47.9 診斷（不是門檻）

* `general` 與 `testimony` **分開**的 BPC（英文與中文混在一起報會把兩件事混為一談）。
* BPC 對訓練步數（學習曲線）。
* 前 20 個 greedy 續寫，人工看，記錄但不評分。
* unigram BPC（0 階），只為了畫出三條線。

### 47.10 指令（先跑完 L，才輪到 P）

```bash
./.venv/bin/python scripts/train_text_stage.py --seed 20261116 --epochs 5 \
    --general-bytes 3000000 --general-holdout-bytes 300000 \
    --pantry-sessions 1000 --out data/text_stage
# 之後不重訓也能重驗門檻：
./.venv/bin/python scripts/train_text_stage.py --check data/text_stage/<report>.json
```

### 47.11 這一節**不會**證明什麼

1. 不會證明 pantry（P）會過。文字階段的權重只是起點；P 換表徵、換目標，要另外量。
2. 不會證明「智能」。BPC 是壓縮指標；一個只會續寫的模型仍然可能答不出任何問題。
3. 不會證明中文能力。`general` 是英文、`testimony` 是中文，分開報；加權平均會把兩者混掉。
4. 不會改變核心分 **0.00/10**。這一輪是設備，不是結果。

## 四十八、文字階段 L 的結果（2026-11-13，依 §47 的登記跑）

### 48.1 實際跑的指令與成本

完全照 §47.10：`--seed 20261116 --epochs 5 --general-bytes 3000000
--general-holdout-bytes 300000 --pantry-sessions 1000 --out data/text_stage`。報告
`data/text_stage/text_stage_20261113-212446.json`、checkpoint 同名 `.pt`。

| | 值 |
| --- | --- |
| 參數 | **124,611**（`GRUCore(259, hidden=128, emb=64)`；§47.4 登記的模型，沒有換類別） |
| device | **xpu**（`resolve_torch_device()`） |
| 語料 | general 2,999,463 B 訓練／299,408 B 留出；testimony 訓練 **1,014,924 B**／留出 **254,050 B**（與 §47.3 登記的位元組數**完全相符**，`registered_sizes_match: true`） |
| 訓練 | 5 epochs，**402.65 s**（每個 epoch 約 80 s；視窗數 992／epoch） |
| 評估＋L3 生成 | 28.04 s；wall **430.69 s** |

### 48.2 門檻（L1–L7，一個都沒動）

| 門檻 | 條件 | 量到 | 判定 |
| --- | --- | --- | --- |
| L1 | 留出 BPC < 插值 bigram | 1.3164 < 3.4317 | **PASS** |
| L2 | 留出 BPC < 插值 trigram | 1.3164 < 2.1547 | **PASS** |
| L3 | 100 個 prefix：(a) distinct ≥ 90；(b) 平均 LCP > trigram | 98/100；8.14 > 1.71 | **PASS** |
| L4 | 帶 state 的 BPC < 每窗重置 | 1.3164 < 1.4219（好 **7.4%**） | **PASS** |
| L5 | checkpoint 載得回同一個類別／schema | `model_kind="gru"`、`state_schema=1`、`token_count=259`；`--check` 也重載一次 | **PASS** |
| L6 | 文字流無 oracle 欄位／camera tag | `clean: true` | **PASS** |
| L7 | 成本已記錄 | 參數／秒數／device 都在 `cost` | **PASS** |

`--check` 重驗：**OK**（重算 L1–L4／L6／L7，並把 checkpoint 真的載回新的 `GRUCore`）。

**先講清楚這一節最重要的一件事**：`all_pass=True` 是照登記算出來的，但**合併的
BPC 把兩半混在一起**，而兩半的難度差一個數量級。§47.9 要求分開報，所以下面分開。

### 48.3 分解（診斷，不是新門檻）

| 切分 | unigram | bigram | trigram | **模型** | 模型相對 trigram |
| --- | --- | --- | --- | --- | --- |
| general（英文，299,408 B） | 4.9036 | 3.6747 | 2.9739 | **2.2201** | −25.3% |
| testimony（中文證詞，254,050 B） | 7.7041 | 3.1452 | 1.1892 | **0.2480** | **−79.1%** |
| 合併 | 6.1891 | 3.4317 | 2.1547 | **1.3164** | −38.9% |

兩半各自都贏過自己的 trigram floor（§47.6 只要求合併，這裡照 §47.9 分開報）。

**L3 也分開看**（同一份 checkpoint、同一批留出 prefix、同一個貪心解碼；這是 §47.9 的診斷，
不是改門檻）：把 100 個 prefix 按落在哪一半拆開——

| 領域 | n | 模型平均 LCP | trigram 平均 LCP | distinct |
| --- | --- | --- | --- | --- |
| general | 55 | **1.64** | 0.55 | 53/55 |
| testimony | 45 | **16.09** | 3.13 | 45/45 |

也就是說：**L3(b) 的「8.14 > 1.71」幾乎全部來自證詞那一半**。英文續寫只比 trigram 多對
1.1 個 byte，而且內容是固定的填充詞——20 個樣本裡反覆出現 `and sentence`／
`the following sentence`／`and sentences and`，整批英文輸出只用到 **20 個不同字元**。
它學會的是「英文的下一個 byte 長什麼樣」，不是「這段話在講什麼」。

**證詞那一半的 0.248 BPC 要怎麼讀**：pantry v2 的證詞是模板生成的（固定句式、封閉人名與
物品集），所以大部分 byte 在給定格式後就是可預測的；unigram 7.70 → trigram 1.19 → 模型
0.248，這個跌落量的是**格式規律**，不是中文能力，也不是推理。這正是 §47.11 第 3 點先寫下
來的限制。

### 48.4 與 §47.8 的預測對照

| 預測 | 實際 | 對不對 |
| --- | --- | --- |
| L1 會過（估 2.0–2.6 BPC） | 1.3164（合併）／2.2201（general） | 對（general 落在估計帶內） |
| L2 不確定 | 過，但**兩半的margin 差很多**（general 只贏 25%，testimony 贏 79%） | 對「不確定」，錯在「合併看不出來」 |
| L3(a) 會過 | 98/100 | 對 |
| L3(b) 邊緣 | 合併看很寬（8.14 vs 1.71），**general 只有 1.64 vs 0.55** | 對英文那半是「邊緣」，合併數字把它掩蓋了 |

### 48.5 這一輪的結論（照實）

1. **核心現在有一個能讀、能寫 byte 的載體**：同一個 `GRUCore`／`CoreState` v1、124,611
   參數、430 秒訓練，在沒見過的英文上贏過最強的 3-gram floor 25%，而且會生成**不是模板
   拷貝**的 byte 序列（98/100 不同）。L4 說「跨視窗的 state 真的被用到」（7.4%），不是
   宣稱。
2. **它不是語言理解**。英文續寫是局部 n-gram 加上一組填充詞；證詞的低 BPC 是格式規律。
   任何「核心會說英文／中文」的讀法都超出這一輪的量測。§47.11 的四條限制原封不動成立。
3. **它給了 P 一個可量的起點，也給了 P 一個警告**：證詞的 BPC 0.248 表示 pantry 的
   **格式**幾乎是免費的；P 的難度必須落在**選誰／選哪一項**（entity binding），不能落在
   句子上。所以 P 的預登記要含一個**格式對照**：一個只會學模板、不綁定實體的模型，在 P
   的選取門檻上必須失敗。沒有這個對照，P 的高分會再一次是「格式預測」而不是推理。
4. **分數不變**：核心分仍 **0.00/10**（它還沒在任何凍結題目上產生正確答案），系統分
   6.41 也不動。這一輪是設備，現在設備有了，而且是被量過的設備。

### 48.6 下一步

* **P（pantry 推理）先預登記再跑**：以 L 的權重為**起點**（§47.11 已寫「P 換表徵、換
  目標，要另外量」，所以 P 的表徵與目標必須在登記裡寫清楚，不能沿用 L 的 byte 目標假裝
  同一件事）、同一組 `CoreState`、pantry v2 的留出答案 tuple；門檻要含「格式對照失敗」
  「必要性／撤回由求解器驗證」「選取要對人」。§47.3 已把 L→P 的順序寫定，這一節不改它。
* **round 8（定址）排在 P 之後**：§46 的結論是「選取與接線」，但 P 是更前面的問題（核心
  能不能用語言做推理），而且 P 的結果會決定多綁定到底是不是必要條件。先跑能改變後續量測的
  那一階。

### 48.7 更正（2026-11-13，發現於 P 的接線，未改任何 L 的數字）

L 的報告把 **初始化的權重 hash** 記在 `weights_hash` 這個名字底下。`train_text_stage.py`
在 `train()` **之前**就寫了 `report["weights_hash"] = core.weights_hash()`（第 972 行），
訓練後直接存 checkpoint，於是：

| | 值 | 這是什麼 |
| --- | --- | --- |
| 報告的 `weights_hash` | `sha256:a7843b34…6c4b` | `seed=20261116` 的**初始化**（可重現：同一顆種子建 `GRUCore(259,128,64)` 就得到它） |
| checkpoint 載入後 | `sha256:77cb6af3…ea825` | **訓練後**的權重 |
| checkpoint 檔 | `e2a6580ec06b1a8afe886adc5b955d9e7a10bba8996b782383f86b16370efdd4` | 檔案本身 |

**為什麼沒被發現**：L5 只檢查 `model_kind`、`state_schema`、`token_count`；`--check`
只重算 L1–L4／L6／L7 的數字（那些門檻不讀 `weights_hash`）。所以一個標錯的欄位靜靜地
跟著報告走了。P 要拿它鎖起點時才撞上：載入檔案得到的 hash 與登記不符，而**錯的是報告的
欄位，不是檔案**。

**修法**（`train_text_stage.py`）：`init_weights_hash` 記訓練前，`weights_hash` 記訓練後
（存檔前），另記 `checkpoint_sha256`；`--check` 現在會把載回的 hash 與報告比對。
**代價照實記**：舊的 L 報告因此**不再通過** `--check`（它會回報 hash 不符）——這是正確
的，因為那個欄位就是錯的。L1–L7 的分數與判定不受影響（沒有任何一條讀這個欄位），但
「報告本體可以鎖住起點」這個用法作廢；P 的 G1 改成鎖**檔案**與**訓練後 hash**（§49.12）。

## 四十九、在 L 的載體上做 pantry 推理：階段 P（2026-11-13，量測前寫定）

### 49.1 為什麼是 P、它與 L 的關係

L 量的是**載體**：同一個 `GRUCore` 能不能讀 byte、能不能產生 byte。那不等於任何任務。
P 問的是下一個問題，而且是一個可以被否證的問題：

> 讀完 11 個 turn 的口供（沒有人名出現在證據句裡、值與人分在不同 turn），模型能不能產生
> **窗內那個值對應的那個人**？

三件事先講清楚，因為它們是這一節存在的理由：

1. **L 過了不代表 P 會過**，反之亦然。L 的證據只支持「會接 byte」，P 的證據要另外造。
   §47.1 拒絕的是把 L 與 P 寫成同一份登記（那會讓「P 不過就說 L 過了」成立），不是拒絕
   讓 P 沿用 L 的表徵。
2. **相對 §45 的 37 個 CV 音節，P 換了表徵**（byte）；**相對 L，P 不改表徵、只改目標與
   輸入結構**。兩句話不衝突：P 不重跑、也不改 L 的 L1–L7 門檻，L 的報告仍是它自己的
   證據。
3. **起點是 L 的 checkpoint，不是重訓**。順序的重點就是「先有語言載體」；起點用
   **檔案 sha256 與訓練後權重 hash** 兩層鎖住（G1），所以「從哪裡開始」不是我可以事後
   改的變數。**L 報告裡的 `weights_hash` 不能用來鎖起點**：那個值是初始化的 hash
   （§48.7 的更正），不是檔案裡訓練後的權重。

### 49.2 登記什麼、不登記什麼

| | 內容 |
| --- | --- |
| **登記** | 同一個 `GRUCore`／`CoreState` v1，在 800 段口供上微調，能不能對**沒見過的** 200 段產生正確的兇手；而且四個控制（格式對照、state 重置、撤回、名冊移除）都照登記的方向 |
| **不登記** | 自然語言理解、一般推理、多綁定 memory（那是 round 8）、任何核心分 |
| **不改** | 核心分 0.00／系統分 6.41、六維的及格線、既有評測題、L 的報告與門檻 |

**這不是六維智能的及格線。** P 是合成任務（12 個英文名字、4 條模板鏈），它的分數不可與
MMLU／GSM8K 比較；`INTELLIGENCE_PASS_CRITERIA.md` 的外部錨在這裡不適用，原因見 §49.6。

### 49.3 語料（跑之前寫定，不得事後改）

| | 值 |
| --- | --- |
| 來源 | `scripts/gen_pantry_ecosystem.py`，`seed=20261113`、`sessions=1000`、`heldout_fraction=0.2`——**與 L 完全同一份** |
| 訓練 | **800** sessions、**1,014,924 bytes**、`sha256:cbbe5265b2f065b15c170116d277c20eb508d822929e6f8865e59c19997d0179` |
| 留出 | **200** sessions、**254,050 bytes**、`sha256:2ef82f705aedbf957be04ad375021e383520e52d141d3c4e335393137871ba6a` |
| 渲染 | `"\n".join(turn["user_input"] for turn in turns) + "\n"`（與 L 的證詞渲染逐字相同） |
| 結構 | 每個 session **11 個 turn**（1000/1000）；長度 train 1,157–1,445 B、留出 1,169–1,420 B |
| 答案 tuple | `chain|culprit|target_item|window|evidence_tag`，產生器用同一個 `used` 集合跨兩切分去重，所以訓練與留出的 tuple **不重複** |

* 兩個 digest 與 L 報告的 `corpus.digests.testimony_train`／`testimony_holdout` **相同**
  （`18fb92bc1`）。這不是巧合，是同一次產生器呼叫；它也意味著 L 的留出文字 P 同樣沒訓練過。
* 產生器的四道資料門檻（`_validate_necessity`、`_validate_retraction`、
  `_validate_name_balance`、`_validate_shortcuts`）在**跑之前**重跑一次，0 violations，
  否則中止。必要性／撤回是**求解器**驗的，不是我用眼睛看的：`derive()` 是唯一的裁判，
  P 的正解、前綴解、消融解都從它算出來。
* 文字流不得包含 `ground_truth_oracle` 的任何欄位；最後一輪的 `expected_final_deduction`
  不是 `user_input` 的一部分（渲染只看 `user_input`），報告會逐 session 再掃一次。

### 49.4 任務與表徵

| | 值 |
| --- | --- |
| 輸入 | turn 0–10 的文字（含最後的問句），逐 turn 餵 `ai_step`；turn 之間 `al_step(turn["dt_s"])` |
| 目標 | 兇手的名字（**4–5 bytes**）＋ `"\n"`；損失**只**在這些 byte 上 |
| 不餵 | `asserts`（結構化欄位）。那是評分器用的；模型只看得到文字 |
| 不加 | 新問句、新前綴、新 head、新類別。答案直接接在 session 自己的最後一個問句後面 |
| state | 同一份 `CoreState` v1、同一個 `GRUCore(259, hidden=128, emb=64)`（124,611 參數） |

**為什麼不加「答：」之類的前綴**：那會是 L 沒見過的新字串，等於把「格式」再教一次；而
§48.3 已經說格式幾乎免費。P 要量的是選誰，所以答案直接接在既有的問句後面。

### 49.5 預算（跑之前寫定）

| | 值 |
| --- | --- |
| seed | **20261118** |
| 優化器 | Adam，lr **5e-4**（微調，比 L 的 1e-3 低） |
| batch | **8** 個 session |
| epochs | **20**，固定；**沒有** early stopping、**沒有** checkpoint 選擇（選 checkpoint 就會選到留出） |
| 步數 | **2,000**（100 步／epoch） |
| BPTT | 全序列，**不 detach**（最長 1,445 bytes；答案的梯度要能回到名冊那個 turn） |
| `al_step` | session 自己的 `dt_s`，chunk 60 s；留出的平均 **319.1** chunks／session、最大 dt 14,375.8 s |
| device | `core.system.config.compute_device.resolve_torch_device()`；報告記錄實際值 |
| 生成 | greedy，最多 **8 bytes**，遇 `"\n"` 停 |
| 時間 | 登記前的 CPU smoke：一個 **batch 8、含 `al_step`、forward+backward+step** 是 **1.44 s**（三次 1.45／1.38／1.47），tick 1,630／batch → 100 batch／epoch ≈ **2.4 分鐘／epoch**、CPU 上限約 **48 分鐘／臂**；xpu 應更快。這是估計，不是門檻 |

**量測衛生**：登記 run 進行中，不得有其他 torch／XPU 工作（§46.11 第一件事）。兩臂依序
跑，對照先（§49.10）。

### 49.6 門檻（跑之前寫定，不得事後改）

| 門檻 | 條件 | 這個數字從哪來 |
| --- | --- | --- |
| G1 | 起點檔案 sha256 = `e2a6580ec06b1a8afe886adc5b955d9e7a10bba8996b782383f86b16370efdd4`，載入後 `weights_hash` = `sha256:77cb6af3cf2a9df9d3e26142ab2092720d99e8b74423f73d250ff942945ea825`，參數 **124,611** | L 的那個 checkpoint 檔（訓練後）；不符就中止。舊登記寫的 `a784…` 是初始化的 hash，見 §48.7／§49.12 |
| G2 | 語料的兩個 digest 等於 §49.3、800／200、`registered_sizes_match` | 同上；不符就中止 |
| G3 | **儀器**：train 切分前 200 個 session 的 free exact **> 0.25** | 與 G4 同一條線；這一條問的是「通道能不能把答案說出來」，不是能力 |
| G4 | 留出 free exact 的 **Wilson 95% 下界 > 0.25** | 0.25 = 語料自己算出的**最強 surface baseline 上界**（見下） |
| G5 | 留出 ranking（12 個名字的 sequence log-likelihood，argmax）的 Wilson 下界 **> 0.25** | 同上；ranking 把「選誰」與「能不能拼出 byte」分開 |
| G6 | 撤回：98 題（求解器說**前綴唯一解是陷阱那個人**）上，`full`→真兇、`no_correction`→陷阱的 **flip rate ≥ 0.50**，且 `full` 在這 98 題 ≥ 0.25 | 0.50 是慣例（多數）；求解器說前綴的解是唯一的，所以「有在讀」應該接近 1.0 |
| G7 | state：`full` − `reset` **≥ 0.25**，且 `reset` **≤ 0.2591** | 0.25 沿用 §46.5 B3；0.2591 = chance + 0.10 |
| G8 | 格式對照 F-rand：free exact **≤ 0.2591** 且 ranking **≤ 0.2591** | 產生器接受語料用的同一條線（`CHANCE_MARGIN`） |
| G9 | 最常見預測名字的 share **≤ 0.35** | 2× 最大均勻 share（1/5 = 0.20）；常數答案直接出局 |
| G10 | 成本已記錄（參數、秒數、device、每 epoch loss） | — |

**0.25 是怎麼來的（不是外接、也不是我挑的）**：留出的 chance 是 **0.1591**
（每個 session 的 1/|actors| 平均；|actors| = 5–8，計數 49／54／50／47）。五個 surface
baseline 在同 200 題上的 95% Wilson 上界是：

| baseline | accuracy | upper95 |
| --- | --- | --- |
| `last_named` | 0.180 | 0.2391 |
| `first_named` | 0.185 | 0.2446 |
| `most_mentioned` | 0.190 | 0.2500 |
| `turn_with:主管`／`值班表`／`卡號`／`登記簿`／`更正` | 0.190 | 0.2500 |

最大值是 **0.2500**。所以 G4／G5 的意思很精確：**模型的 95% 下界要高過最強捷徑的 95%
上界**——兩個區間不重疊，才叫「不是捷徑」。觀測值要 ≥ 0.31 才會過，這是刻意的。

**98 題是怎麼來的**：把 `correction_turn` 拿掉後重跑 `derive()`，前綴只剩一個候選的
session 有 **98/200**（apron **52/52**、badge **46/46**、ledger **0/54**、window
**0/48**——後兩條鏈在更正前，兇手自己那一列也落在窗內，所以前綴是兩個候選）。所以撤回
的門檻只在 98 題上判，其餘 102 題只報分布。

### 49.7 每一個分支要怎麼讀（先寫定）

| 量到什麼 | 讀法 |
| --- | --- |
| G3 不過 | **儀器封頂**：800 段（其中抽 200 段）都記不住，後面所有數字都是上限，不是「推理失敗」 |
| G3 過、G4／G5 不過 | **通道會、推理不會**（最可能的分支）。這時 G5 比 G4 有資訊：ranking 不需要拼 byte |
| G4 過、G6 不過 | 答對了但**不是靠撤回**（記憶、位置線索或某個還沒找到的 cue）→ 記成「未解釋」，不記成推理 |
| G4 過、G7 不過 | 答案**不在 state**（在最後一輪的局部文字）→ 不符合「stateful core」的宣稱，即使分數好看 |
| G8 不過（F-rand > 0.2591） | **儀器量到的是格式**，這一輪作廢（void），重新登記；**不改門檻** |
| G9 不過 | 常數答案；即使 G4 過了也不算「選取」 |

### 49.8 預測（寫在跑之前）

| 門檻 | 預測 | 理由 |
| --- | --- | --- |
| G1／G2 | 過 | 機械檢查 |
| G3 | **不確定**，0.30–0.60 | 124k 參數、800 段、2,000 步；可能直接過擬合，也可能連記都記不住 |
| G4 | **不過**，0.10–0.22 | 答案要三個 hop（窗→值→名冊→人），而且要跨 11 個 turn 保存在 128 維 state |
| G5 | **不過**，0.12–0.25 | ranking 只要相對次序，通常比自由生成好一點 |
| G6 | **不過**，flip 0.0–0.20 | 更正 turn 是第 8 個，離答案最遠 |
| G7 | gap 小（兩邊都接近 chance） | 若 G4 本來就沒過，這條不會有訊號 |
| G8 | **過**（F-rand ≤ chance） | 隨機答案學不到關係 |
| G9 | 過 | 分布應該接近均勻 |

一句話：**預期 P 不過，而且失敗點會在「選取」而不是「格式」**。如果 G3 也不過，那這一輪
的結論會變成「載體在 2,000 步內連訓練集都記不起來」，那比「推理不會」更前面。

### 49.9 診斷（不是門檻）

* **V4 名冊移除**：拿掉 `roster_turn`，`derive()` 回全部人（沒有唯一解）。若 exact 沒掉，
  它用的不是名冊。
* **V5 時間界線移除**：拿掉兩個 `window` turn，同上。
* **V6 不呼叫 `al_step`**（dt=0）：這個號誌有**兩個方向**，兩個都要照實讀，不預設哪一個
  ——(a) 掉下去 → 它把時鐘當位置線索（`dt_s` 與 turn 序號相關，而序號與答案無關，所以那
  是捷徑）；(b) 升上去 → 真實的時間間隔把 state 洗掉（§43 只在 120 s／2 chunks 上量過
  內容攜帶，留出的平均是 **319.1** chunks／session，最大 240 chunks／turn）。這一條是
  診斷，不是門檻；哪個方向出現就照哪個方向記。
* **每條鏈分開報**：n≈50，Wilson 區間約 ±13pp，**不作門檻**（理由與產生器對 underpowered
  shortcut 的處理相同：在那個樣本量上把 0.30 與 chance 分開是不可能的）。
* **F-0**：L 的 checkpoint 直接上同一個儀器（不訓練、不微調）——純格式對照，免費。
* train 曲線：每 epoch 的 loss、train exact。
* 每條鏈 3 個生成樣本（原始 bytes，不只分數）。

### 49.10 指令（對照先，計分 run 最後）

```bash
PY=./.venv/bin/python   # 同一個直譯器；寫成變數是為了讓這份登記可以先於腳本存在
# 訓練前的 smoke（CPU；走完整條路徑，含診斷與 --check）
$PY scripts/train_pantry_deduction.py --smoke --device cpu
# F-rand（格式對照；必須先完成）
$PY scripts/train_pantry_deduction.py --control rand --seed 20261118 --out data/pantry_stage
# A（計分）
$PY scripts/train_pantry_deduction.py --seed 20261118 --out data/pantry_stage
# 不重訓的重驗
$PY scripts/train_pantry_deduction.py --check data/pantry_stage/<report>.json
```

* driver 在 F-rand 報告不存在時**拒絕**啟動 A（§46.11 第三件事）。
* `--check` 由報告裡的數字重算 G1–G10，並把 checkpoint 載回**同一個類別**；竄改任何一個
  門檻數字都會讓它失敗。

### 49.11 這一節**不會**證明什麼

1. **不會證明核心會推理。** 200 段合成口供、12 個英文名字、4 條模板鏈；過了只說這個任務
   在這個預算下成立。
2. **不會證明中文能力。** 文字是模板產生的；§48.3 的證詞 BPC 0.248 已經說明格式幾乎免費，
   所以 G8 是這一輪不可省的那一條。
3. **不會改變核心分（0.00/10）或系統分（6.41）。** P 是學習層的宣稱**候選**；結果出來才進
   `LAYER_REGISTRY.json`（預期是 `fail`，跟 `neural_fact_learning` 一樣照實記，而不是
   從缺）。
4. **不證明多綁定 memory 是必要條件。** round 8 另外登記。
5. **一個「不過」不代表核心不能推理**，只代表這個載體＋這個預算＋這個任務沒有做到。

### 49.12 修訂記錄（**在任何計分 run 之前**）

* **2026-11-13，V6 的讀法（§49.9）**：原本只寫「掉下去＝用時鐘不是時間戳」。這句話把
  「`al_step` 幫了忙」與「`al_step` 洗掉內容」混成一個方向。改成兩個方向都照實讀，並把
  `319.1` chunks／session 寫進來——這不是看到結果才改的，改的時候一趟 P 都還沒跑。
* **2026-11-13，G1 的鎖（§49.1、§49.6）**：舊登記把起點鎖在 `sha256:a784…`，那是**初始化**
  的 hash（§48.7），不是 checkpoint 裡的權重。發現時正在把 P 接上 L，一趟 P 都還沒跑；
  改成同時鎖**檔案 sha256** 與**訓練後 weights_hash**。這不是把門檻放寬：舊值連「檔案裡
  的權重」都不是，依它判會讓每個 run 在第一步就中止。G1 的其他條件（124,611 參數、同一個
  `GRUCore` 設定）不變。
* **2026-11-13，G6 的讀法（§49.6）**：程式把 `flip_rate` 寫成「兩邊都對」（前綴答陷阱、
  完整答兇手），不是「答案有變」。任何改變都算 flip 會讓「錯兩次」看起來像撤回，所以同時
  另記 `changed_rate` 當診斷。這一條在第一次 P 執行前就定在程式裡。

### 49.13 兩臂與十條門檻（2026-11-13，照 §49.10 跑；一個門檻都沒動）

指令完全照 §49.10，順序也照（對照先）。兩個 `--check` 都回 `OK`。

| | F-rand（格式對照） | A（計分） |
| --- | --- | --- |
| 報告 | `data/pantry_stage/pantry_deduction_20261113-220852.json` | `data/pantry_stage/pantry_deduction_20261113-230140.json` |
| 答案 | 隨機的**另一個** actor | 兇手 |
| device／參數 | xpu／**124,611** | xpu／**124,611** |
| 訓練 | 800 段、20 epochs、**3,139.3 s** | 800 段、20 epochs、**3,200.6 s** |
| train 前 200 段 exact | 0.0850 | **0.1150** |
| 留出 free exact | 0.0650 | **0.0850（17/200）** |
| 留出 ranking | 0.1550 | **0.1650** |
| 最常見預測 | `Chris`，share **1.0** | `Kevin`，share **1.0** |

留出 chance **0.1591**；最強 surface baseline 的 95% 上界 **0.2500**（§49.6 已算）。

| variant | n | exact | ranking | chance |
| --- | --- | --- | --- | --- |
| `full` | 200 | **0.0850** | **0.1650** | 0.1591 |
| `reset`（問之前把 state 歸零） | 200 | 0.0850 | 0.1650 | 0.1591 |
| `skip_al`（不呼叫 `al_step`） | 200 | 0.0850 | 0.1650 | 0.1591 |
| `no_correction`（拿掉更正那一輪） | 98 | 0.1224 | 0.2041 | 0.1584 |
| `no_bounds`（拿掉兩個時間界線） | 52 | 0.0962 | 0.2308 | 0.1561 |
| `no_roster`（拿掉名冊） | 0 | — | — | — |
| `train_fit`（前 200 段訓練資料） | 200 | 0.1150 | 0.1750 | 0.1595 |

`full` 的 Wilson 95% 區間：exact **0.0537–0.1319**、ranking **0.1200–0.2227**——兩者的
上界都低於 0.2500。

| 門檻 | 量到 | 判定 |
| --- | --- | --- |
| G1 起點是 L 的成品 | 檔案 `e2a6580e…`、載入後 `77cb6af3…`、124,611 參數 | **PASS** |
| G2 語料是登記的那份 | 兩個 digest 相符、800／200、位元組數相符 | **PASS** |
| G3 儀器：train exact > 0.25 | **0.1150** | **FAIL** |
| G4 留出 exact 下界 > 0.25 | 0.0537 | **FAIL** |
| G5 留出 ranking 下界 > 0.25 | 0.1200 | **FAIL** |
| G6 撤回 flip ≥ 0.50 | 98 題上 flip **0.0**（changed 也 **0.0**） | **FAIL** |
| G7 `full` − `reset` ≥ 0.25 | 差 **0.0000** | **FAIL** |
| G8 格式對照 ≤ 0.2591 | 0.0650／0.1550 | **PASS** |
| G9 最常見名字 share ≤ 0.35 | **1.0** | **FAIL** |
| G10 成本已記錄 | 參數／秒數／device／每 epoch loss | **PASS** |

`all_pass = False`。`LAYER_REGISTRY.json` 的 `stateful_core_pantry_deduction` 記為
`learning`／**`fail`**，與 `neural_fact_learning` 同一個處理方式（記下來，不從缺）。

### 49.14 三個讀數（這一輪的重點不是 0.0850）

1. **17/200 不是「選對 17 次」，是 Kevin 在留出的比例**。模型 200 題全部答 `Kevin`；
   Kevin 在**訓練**集是邊際眾數（84/800），在留出只有 **17/200**（第 6 名）。所以
   exact 0.0850 的分子就是「留出剛好是 Kevin 的題數」，逐鏈也一樣：ledger 4/54、
   apron 5/52、badge 4/46、window 4/48——正好是 Kevin 在該鏈出現的次數。換一個名字當
   常數，分數就會跟著換成那個名字的邊際比例。
2. **答案的損失就是「12 個名字哪一個」的熵**。最後一個 epoch 的 per-token loss
   **0.4499**；留出答案平均 **5.615** 個 token（名字 4–5 bytes ＋ `\n`），所以每個
   session 約 **2.526 nats**。留出兇手的熵是 **2.4641**、訓練集 **2.4757**、
   `ln 12 = 2.4849`。也就是說：模型學到的是名字的**邊際分布**，對「這一段口供」沒有
   任何條件資訊。這比「推理失敗」更前面——連「這一題是誰」都沒有進入預測。
3. **三個臂的預測逐位元組相同**。`full`、`reset`（把前 10 輪的 state 歸零）、`skip_al`
   （完全不呼叫 `al_step`）都是 0.0850／0.1650，200 題的預測完全一樣；`no_correction`
   也一樣，`changed_rate = 0.0`。所以第 1–10 輪建立的 state、以及第 8 輪的更正，對輸出
   **沒有作用**。

**與 §49.8 的預測對照**：

| 預測 | 實際 | 對不對 |
| --- | --- | --- |
| G3 不確定，0.30–0.60 | **0.1150** | 錯在「低估了有多難」——連訓練集都記不住 |
| G4 不過，0.10–0.22 | 0.0850 | 對「不過」，低於估計帶 |
| G5 不過，0.12–0.25 | 0.1650 | 對（帶內） |
| G6 不過，flip 0.0–0.20 | 0.0（changed 也 0.0） | 對 |
| G7 gap 小 | 0.0000 | 對，但比預期更徹底 |
| G8 過 | PASS | 對 |
| G9 過（分布近均勻） | share 1.0 | **錯**：崩成一個常數 |

**成本**：**3,200.6 s／臂**（53 分鐘），不是登記時估的 15–25 分鐘；loss 從第 5 個 epoch
起停在 0.4429–0.4523，20 epochs 沒有改變結論。**F-0（L 的 checkpoint 不訓練直接上儀器）
沒有跑**：它是診斷不是門檻，而且這一輪的常數答案會把它掩蓋（未訓練的載體同樣只會吐眾數）；
照實記為「未量」，不補跑（在看到結果之後才加臂，就是事後選資料）。

### 49.15 讀法（§49.7 的第一條分支）與下一個變數

1. **走的是「儀器封頂」分支**：G3 不過（0.1150 ≤ 0.25）。依 §49.7，後面所有數字都是
   **上限**，不能讀成「推理失敗」，更不能讀成「核心不會推理」。這一輪沒有任何一條推理
   宣稱成立，也沒有一條被否證。
2. **G8 過，所以「格式」不是解釋，但「推理」也不是結論**。對照臂 0.0650／0.1550，
   計分臂 0.0850／0.1650——兩者差 0.02，而且是同一個機制（換一個常數名字）。所以
   「它只是學了模板」和「它學會了推理」都不成立：兩臂都停在「輸出邊際眾數」。
3. **G7／G9 不過是同一件事的兩種說法**：state 歸零不改變答案、答案是一個常數。
4. **失敗點往前移了一格**：不是 round 7 的「存了但選不出來」，也不是 round 6 的
   「讀不懂時間」，而是**答案點沒有條件於輸入**。loss ＝邊際熵這件事同時說明：
   同一個登記換 seed／加 epochs 會再收斂到同一個邊際，再跑一次沒有資訊。
5. **因此下一步不是無條件接 round 8 的「選取」**。原訂的 per-turn keys ＋讀取→控制器
   解的是「存了兩組、選不出來」；P 顯示連**一組**都沒被讀。下一個登記若要動這條線，
   必須先有**過擬合校準臂**：固定 32（或 64）段訓練 session，要求 train exact 接近
   1.0；過了才有資格談泛化與選取。這是儀器校準，不是能力宣稱，門檻與資料在跑之前寫定。
6. **分數不動**：核心 **0.00/10**、系統 **6.41**。P 是學習層的宣稱，判定 `fail`。
7. **兩個照實記的限制**：(a) `no_roster` 的 n=0 是求解器在拿掉名冊後回**多個**候選，
   所以沒有單一正解可判——不是崩潰，也不是 0 分；(b) 語料是模板產生的中英口供、
   12 個名字、4 條鏈，任何讀法都只在這個任務上。

### 49.16 事後診斷（不是門檻）：答案的梯度只到得了最後一輪

P 的 loss 停在邊際熵，下一步該往哪裡走取決於一個機械問題：答案的 cross-entropy 反傳時，
**對每一輪的 state 還剩多少梯度**。新增 `scripts/probe_credit_assignment.py`（6 條測試）：
用同一支 driver 的 `turn_tokens`／`turn_gaps`／`_answer_loss`，逐輪保留 `h`
（`retain_grad`）、一次 backward，報每一輪的 `|dL/dh|`、越過 `1e-6` 的最早一輪、以及往回
的每輪縮小倍率。這是**訓練資料上的儀器診斷**，不是能力量測，沒有門檻，也沒有用留出集。

實測（CPU、batch 8、11 輪、floor `1e-6`；`data/pantry_stage/credit_assignment.json`）：

| 輪 | L 的載體（未受任務訓練） | P 的 checkpoint |
| --- | --- | --- |
| 0–3 | **0**（float32 下溢） | **0** |
| 4 | 7.57e-22 | 1.02e-19 |
| 6 | 1.56e-16 | 1.36e-16 |
| 8 | 1.83e-09 | 3.55e-11 |
| 9 | 1.21e-04 | 1.13e-07 |
| **10（答案那一輪）** | **8.75e-01** | **4.95e-02** |
| 越過 floor 的輪數 | 2 | 1 |
| 往回每輪縮小 | **3.09e-04×** | **1.13e-03×** |

`loss` 分別是 5.8238（未訓練）與 0.4241（訓練後）；`head` 的梯度是 2.83 與 0.485，所以
這不是「整條路都沒有梯度」，而是**梯度在迴歸裡衰減**。

**讀法**（這一節只把原因縮小，不宣稱修好）：

1. 答案的梯度**只到得了第 8–10 輪**；第 7 輪以前在 1e-13 以下，第 0–3 輪是 0。
2. 要跟 optimizer 一起讀：訓練用 `Adam(lr=5e-4)`，`eps=1e-8`。`|g| ≪ eps` 時
   `m/(sqrt(v)+eps)` 退化成 `m/eps`，**步長隨梯度一起消失**。第 8 輪的 3.6e-11 比 eps
   小 2–3 個數量級，所以口供那幾輪實際上收不到這個 loss 的更新。
3. 這解釋了為什麼 train exact 0.1150 剛好是常數的邊際（前 200 段裡 Kevin 23/200），
   也解釋了 `reset`／`skip_al` 為什麼逐位元組相同：答案沒有條件在第 1–8 輪，因為那些輪
   從來沒有為答案的 loss 收過一個有效的更新。
4. **不是「再訓練就會好」的證明**：它只把「為什麼沒有條件於輸入」縮小到一個可改的機制
   ——**路徑長度**（11 輪 × 約 140 bytes ≈ 1,500 步 BPTT），不是寬度，也不是 epoch 數
   （更多的 epoch 只會把同一個邊際擬得更準）。

## 五十、階段 Q：短路徑監督（每個 turn 一次讀出；2026-11-14，量測前寫定）

### 50.1 為什麼是 Q，而不是先接 round 8

§49.16 量到的是機制，不是猜測：答案的 cross-entropy 往回傳，每經過一個 turn 就**縮小約 3
個數量級**（P 的 checkpoint 是 **1.13e-03×／turn**），所以只有第 8–10 輪拿得到
有效梯度；第 0–7 輪在 `Adam(eps=1e-8)` 下**收不到這個 loss 的更新**。P 的 train exact
**0.1150** 剛好是常數 `Kevin` 在前 200 段的邊際（23/200），這與「只有 head 的邊際被學到」
一致。

round 8 的 per-turn keys ＋讀取→控制器，解的是「**存了兩組、選不出來**」（§46）。P 顯示
的是更前面的一件事：**連一組都沒有被讀，因為口供那幾輪沒有為答案的 loss 收過更新**。
在路徑長度沒修好之前先加結構，會量到同一個邊際——那不是新資訊。

所以 Q 只改一件與 P 不同的事：**答案的監督路徑長度**。

### 50.2 唯一變數：每個 turn 邊界都讀出一次（auxiliary readout）

同一個 `GRUCore`（124,611 參數）、同一個 `CoreState` v1、同一份語料與切分、同一個起點
（L 的 checkpoint）、同一個 seed、同樣的 20 epochs、同樣的 lr／batch。**沒有新參數**
（讀出用的就是同一個 `head`），state 格式不變，eval 協定不變（仍然只在最後一輪問一次）。

訓練損失（`--aux-loss` 預設 **0.0**＝P 的行為；Q 用 **1.0**）：

```
L = CE(head(h_10) → 答案)  +  λ · (1/10) · Σ_{k=0..9} CE(head(h_k) → 答案)
```

* `h_k` 是第 k 輪跑完之後的 state；答案的 teacher-forced 解碼與 P 完全相同（4–5 bytes
  ＋ `\n`，`MAX_ANSWER_BYTES=8`）。
* 輔助項只到第 0–9 輪；第 10 輪已經在主要項裡，不重複計。
* **eval 時完全不用輔助項**：推論仍然只有最後一輪的問題與那個 state。輔助項是訓練訊號，
  不是推理時多問幾次。
* 每一輪的 CE 都是從**那一個邊界**出發、只經過答案的 5–6 個 token——所以口供的第 k 輪到
  損失的路徑是「1 個 turn」，不是「11−k 個 turn」。

這不是「把答案放進 context」：輔助項沒有改變任何輸入文字，也沒有把答案餵進 state；它只是
讓每個邊界都對同一個目標負責。

### 50.3 不變的東西（避免一次改兩個變數）

| | 維持 §49 的登記 |
| --- | --- |
| 模型／state | 同一個 `GRUCore`、124,611 參數、`CoreState` v1，不新增任何參數 |
| 語料 | 同一次產生器呼叫，兩個 digest 與 §49.3 相同（1,014,924／254,050 B） |
| 切分 | train 800／held-out 200，同一個交錯切分 |
| 起點 | L 的 checkpoint，G1 鎖**檔案 sha256** 與訓練後 hash |
| optimizer | `Adam(lr=5e-4)`、batch 8、20 epochs、seed **20261118** |
| eval | 每段只問最後一輪；greedy 8 bytes；12 個名字的 ranking 另計 |
| 門檻 | Q3–Q8 與 P 的 G4–G9 **完全相同**，一個數字都不改 |
| 對照 | F-rand 格式對照**重跑一次**，並套用同一條輔助損失 |

### 50.4 門檻（跑之前寫定，不得事後改）

| 門檻 | 條件 | 為什麼是這個數字 |
| --- | --- | --- |
| **Q1** | 過擬合校準：**32 段訓練 session**、100 epochs、輔助損失 1.0，train exact **≥ 0.90** | 這是儀器校準，不是能力。若 32 段都背不起來，Q 的完整臂不用跑（先記 `fail`，不浪費約 55 分鐘） |
| **Q2** | 完整臂的 **train** 前 200 段 exact **> 0.25**（＝P 的 G3） | 沿用 §49.6 的同一條儀器線；不通過就代表路徑之外還有別的東西擋著 |
| Q3 | 留出 free exact 的 Wilson 95% **下界 > 0.2500** | 與 P 的 G4 相同：0.25＝最強 surface baseline 的上界 |
| Q4 | 留出 ranking 的 Wilson 95% **下界 > 0.2500** | 與 P 的 G5 相同 |
| Q5 | 撤回：98 題上 flip（兩邊都對）**≥ 0.50**，且 `full` 在該子集 **≥ 0.25** | 與 P 的 G6 相同 |
| Q6 | `full` − `reset` **≥ 0.25**，且 `reset` **≤ 0.2591** | 與 P 的 G7 相同 |
| Q7 | 格式對照（含輔助損失）free exact 與 ranking **都 ≤ 0.2591** | 與 P 的 G8 相同；輔助項會強化格式學習，所以這一條是 Q 最關鍵的對照 |
| Q8 | 最常見預測名字的 share **≤ 0.35** | 與 P 的 G9 相同 |
| Q9 | 成本已記錄：參數、秒數、device、**每個 epoch 的總損失與輔助損失**、每輪邊界的讀出準確率 | 沒有分開記輔助項，就分不出「擬合」與「主要項變好」 |
| Q10 | `--check` 由報告重算 Q1–Q9 並重載 checkpoint | 與 P 相同 |

**Q1 的資料衛生**：32 段取自 **train 切分的前 32 段**（不是留出）；報告記 `overfit: true`，
control 查找與 `--check` 都必須忽略它。Q1 的 0.90 不得被引用為泛化或能力。

### 50.5 預測（寫在跑之前）

| 門檻 | 預測 | 理由 |
| --- | --- | --- |
| Q1 | **過**（0.80–1.00） | 32 段、400 步、每個邊界都有梯度；若這也不過，代表「路徑」不是唯一的原因 |
| Q2 | **不確定**，0.25–0.60 | 路徑修好後主要項才有機會；但 800 段仍可能不夠 |
| Q3 | **不過**，0.10–0.24 | 多跳推理（窗→值→名冊→人）對 124k GRU 仍是難的；這一輪修的是「能不能學」，不是「會不會推理」 |
| Q4 | **不過**，0.12–0.28 | ranking 通常比自由生成好一點，但同樣未達 0.25 的下界 |
| Q5 | 不確定，0.0–0.40 | 若 Q3 沒過，這條不會有訊號 |
| Q6 | 不確定；若 Q3 沒過，gap ≈ 0 | state 有沒有被用，要 Q3 先有訊號才讀得出來 |
| Q7 | **過**（≤ 0.2591） | 輔助損失對隨機答案同樣只是擬合格式，不該超過 chance |
| Q8 | **不確定** | 有了條件訊號之後，常數答案才可能鬆動；若 Q3 沒過，大概仍是常數 |

一句話：**Q 預期會把「學不學得起來」修好（Q1／Q2），但預期不會讓「推理」過線
（Q3／Q4）**。若結果是這樣，下一個變數才是 round 8 的選取／定址；若 Q1 就不過，則是路徑
以外的原因，照實記，不進完整臂。

### 50.6 診斷（不是門檻）

* **每輪讀出準確率**（held-out）：第 k 輪的 `head(h_k)` 直接解碼答案，對「求解器在該前綴
  上已有唯一解」的 session 計分。這條會說出「它多早就能答」，也是防止「輔助項讓模型靠
  roll-call 猜」的守門。
* **輔助損失曲線**與主要損失分開記。
* **梯度剖面重跑**（`scripts/probe_credit_assignment.py`）：Q 之後，第 0–8 輪的
  `|dL/dh|` 應該離開 float32 下溢；這是「路徑真的變短」的機械證據，不是分數。
* 每條鏈分開報（n≈50，不作門檻）。
* 三個生成樣本／鏈（原始 bytes）。

### 50.7 這一節**不會**證明什麼

1. **不會證明核心會推理。** 就算 Q3／Q4 過線，那也只是這個任務、這個預算、這 200 段
   合成口供。§49.11 的五條限制原封不動。
2. **不會證明輔助讀出是「智慧」。** 它是訓練訊號；eval 時不多問一次。
3. **不會改變核心分（0.00/10）或系統分（6.41）。** Q 若過線，仍然只是學習層的一條
   任務宣稱，要另外登記；分數只在模型於凍結題目上產生正確答案時才動。
4. **不會證明 round 8 不必要。** Q 修的是「答案是怎麼被學到的」；選取與定址是另一個問題。
5. **不會用 Q 的結果去改 P 的門檻。** P 的記錄照 §49.13 留著。

### 50.8 指令（Q1 先，對照次之，完整臂最後）

```bash
PY=./.venv/bin/python
# Q1：過擬合校準（32 段、100 epochs；不過就不跑完整臂）
$PY scripts/train_pantry_deduction.py --overfit 32 --epochs 100 --aux-loss 1.0 \
    --device cpu --out data/pantry_stage/q_overfit
# 格式對照（含同一條輔助損失；必須先完成）
$PY scripts/train_pantry_deduction.py --control rand --aux-loss 1.0 --seed 20261118 \
    --out data/pantry_stage/q
# Q：完整臂
$PY scripts/train_pantry_deduction.py --aux-loss 1.0 --seed 20261118 \
    --out data/pantry_stage/q
# 不重訓的重驗
$PY scripts/train_pantry_deduction.py --check data/pantry_stage/q/<report>.json
```

* 完整臂在對照報告不存在時**拒絕**啟動（沿用 §49 的 driver 行為）。
* Q1 的報告在 `q_overfit/`，`--overfit` 會記 `overfit: true`；control 查找與 `--check`
  都忽略它。

### 50.9 這一節的地位

這是**第六輪之後第一次改訓練訊號**（前幾輪改的是結構或任務）。依 §49.16 的診斷，它只改
一個可指名的東西：**口供的每一輪到答案損失的路徑長度**。門檻、語料、切分、模型、起點、
eval 協定全部沿用 §49；沒有任何一條在看到 Q 的結果之後才寫。

### 50.10 Q1（登記的過擬合校準）：**FAIL**

指令完全照 §50.8 的第一條，順序也照（Q1 先，完整臂不跑）：

```
./.venv/bin/python scripts/train_pantry_deduction.py --overfit 32 --epochs 100 \
    --aux-loss 1.0 --device cpu --out data/pantry_stage/q_overfit
```

報告 `data/pantry_stage/q_overfit/pantry_deduction_20261114-000928.json`（`.pt` 同名）。
`--overfit` 記為 `true`，`control_arm = answer`（校準臂不是對照）。

| | 值 |
| --- | --- |
| 參數 | **124,611**（同一個 `GRUCore`，沒有換模型） |
| device | **cpu**（Q1 是儀器校準，不需要加速器） |
| 訓練 | 32 段、100 epochs、batch 8 → **400 步**、**278.2 s** |
| train_fit（**就是那 32 段**） | **5/32 = 0.1562**（門檻 **0.90**） |
| 最常見預測 | `David`，share **0.6562**（21/32）；distinct **3** |
| 留出（只記，不判） | exact 0.1050、ranking 0.1800 |
| 每個 epoch 的損失 | 第 1 個 9.4933（main 4.8377／aux 4.6556）→ 第 100 個 **0.7682**（main **0.3991**／aux 0.3691） |

| 門檻 | 量到 | 判定 |
| --- | --- | --- |
| **Q1** 32 段 train exact ≥ 0.90 | **0.1562** | **FAIL** |
| Q2–Q8（完整臂的儀器／留出／撤回／state／對照／常數） | — | **n/a**（校準臂不是分數，見 §50.4） |
| Q9 成本＋輔助損失＋每輪讀出已記錄 | 參數／秒數／device／100 個 epoch 的 main 與 aux／11 輪讀出 | **PASS** |
| Q10 `--check` 重算並重載 checkpoint | `OK` | **PASS** |

**5/32 不是「答對 5 次」**：`David` 在這 32 段裡剛好出現 **5** 次（訓練集前 32 段的邊際
第 2 名），而模型的 21/32 都答 `David`——也就是這 5 題正好是常數命中的那 5 題。逐 token 的
main loss **0.3991** × 平均 **5.615** token ≈ **2.241 nats／session**，與這 32 段的兇手熵
**2.3691** 同量級（`ln 12` = 2.4849）。所以它連**訓練集**都沒有條件於輸入，也沒有背起來。

**每輪讀出（§50.6，留出，診斷）**：第 0–5 輪 n=0（每個人都被點名，不可判）；第 6 輪
0.1122（n=98）、第 7 輪 0.1050、第 8 輪 0.0850、第 9 輪 0.0750、第 10 輪 0.1050（各
n=200）。**沒有任何一輪高過 base rate**——不是「早點問會答錯、最後會答對」，而是每個邊界
都只吐邊際。

**與 §50.5 的預測對照**：Q1 預測「**過**（0.80–1.00）」，實際 **0.1562**——**預測被否證**。
依 §50.4／§50.5 的停損：Q1 不過 → **完整臂不跑**（也不跑它需要的 F-rand 對照，因為 Q7
沒有東西可對照），**不改 epochs、lr、寬度或 lambda 重跑**。這一輪停在這裡。

### 50.11 事後配對診斷：同樣的 32 段、λ=0（**不是門檻、不是新臂**）

Q1 失敗有兩個完全不同的解釋：① 輔助讀出把模型拉向邊際（每個早期邊界都只能猜邊際，而它們
共用同一組遞歸權重）；② 這個預算本來就背不起 32 段。分辨的方法只有一個：把 Q 唯一改掉的
東西**拿掉**，其餘完全相同。這是診斷，不是新登記的臂，也不是把 Q1 改成 λ=0：

```
./.venv/bin/python scripts/train_pantry_deduction.py --overfit 32 --epochs 100 \
    --aux-loss 0.0 --device cpu --out data/pantry_stage/q_overfit_lambda0
```

報告 `data/pantry_stage/q_overfit_lambda0/pantry_deduction_20261114-001433.json`。

| | λ=1（Q1，登記的臂） | λ=0（配對診斷） |
| --- | --- | --- |
| train_fit（同 32 段） | 5/32 = **0.1562** | 7/32 = **0.2188** |
| 最常見預測／share | `David` 0.6562 | `Kevin` 0.7500 |
| distinct | 3 | 2 |
| 最後一個 epoch 的 main loss | 0.3991 | **0.3832** |
| ≈ 每 session nats | 2.241 | **2.152** |
| 32 段的兇手熵 | — | **2.3691** |
| 留出 exact／ranking（只記） | 0.1050／0.1800 | 0.0850／0.1750 |
| 秒數 | 278.2 s | 485.7 s |

兩臂都**沒有**接近 0.90。λ=0 的 7 題比 `Kevin` 的 6/32 多一題（唯一一題不是常數），λ=1 的
5 題正好等於 `David` 的 5/32（完全是常數）。**秒數不可比**：兩臂步數相同，λ=0 反而慢 1.7 倍，
而且從第 1 個 epoch 就是 5.2 s vs 2.8 s——這是同一台機器上的負載差異，不是計算量。

### 50.12 讀法（照實，不補跑）

1. **Q 唯一改的那件事不是 Q1 的瓶頸**：把輔助讀出拿掉（λ=0），同樣 32 段、同樣 100 epochs，
   一樣停在邊際（0.2188 vs 0.90）。所以 Q1 的失敗不是「輔助項把模型拉壞」。
2. **但它也沒有證明路徑長度不重要**：失敗的兩臂裡，λ=1 那一臂的梯度**確實到達每一輪**
   （`tests/test_pantry_deduction.py` 用玩具模型釘住：λ=0 時第 0–1 輪的 `|dL/dh|` 恰好是 0，
   λ=1 時每一輪都 > 0）。所以 Q1 的失敗在**信用分配之後**——訊號到了，模型仍然背不起 32 段。
   這和 P 的失敗（訊號只到第 8–10 輪）不是同一個位置，也不該互相代替。
3. **§49.16 的讀法要收窄**：它把「為什麼沒有條件於輸入」縮小到路徑長度，這一輪顯示「路徑
   長度」不是唯一的阻礙。原本那句話（「更多的 epoch 只會把同一個邊際擬得更準」）在 P 的
   預算上成立，但**不能**推廣成「修好路徑就會背起來」。
4. **預算本身是下一個候選，但沒有量**：Q1 是 400 步，P 是 2,000 步（800 段 × 20 epochs /
   batch 8）。「步數不夠」與「這個寬度背不起這個任務」在這一輪**沒有分開**，而且現在去調
   epochs／lr／寬度就是事後調參——登記寫的是「Q1 不過就記 fail、不進完整臂」，所以不調。
   下一個登記若要動這條線，必須先寫下這兩者的分辨方式（例如固定 32 段、把 epochs 做成
   階梯並在跑之前寫定門檻，或先把任務縮到「有任何條件訊號」為止），而不是直接加預算再宣稱。
5. **沒有分數變動**：核心 **0.00/10**、系統 **6.41**。Q 沒有過線，所以**沒有新的層級宣稱**
   （§50.7 已寫：Q 若過線才需要另外登記）；`LAYER_REGISTRY.json` 的
   `stateful_core_pantry_deduction` 仍舊是 `learning`／`fail`，只是證據多了一條「連儀器
   校準都沒過」。
6. **照實記的兩個限制**：(a) Q1 的 32 段取自 **train 切分的前 32 段**，它的 0.1562 不可
   引用為泛化、能力或「推理」；(b) λ=0 的配對診斷是**看到 Q1 結果之後**才跑的，它只用來
   分辨原因，沒有改任何門檻，也沒有被用來讓 Q1 變成 pass。

### 50.13 之後的便宜診斷：答案到底有沒有進到 state？（2026-11-14，不是新臂、不計分）

Q1 與它的 λ=0 配對都停在邊際。在花另一輪訓練之前，先用兩分鐘回答一個更前面的問題：**問句那一步
的 state 裡，有沒有「誰是兇手」這個資訊？** 如果沒有，那麼加 epochs、加寬度、換讀出都不會有效，
因為 head 沒有東西可讀。

工具是既有的 §49.16 探針（`scripts/probe_credit_assignment.py`）新增的 `--state-probe`：對每個
turn 邊界的 `h`，用**訓練切分 800 段**擬合一個線性讀出（ridge 1.0、特徵只用訓練統計標準化），
再在**沒見過的留出 200 段**上評分。這不是能力的分數，是一條「資訊在不在」的線性判定。三個
載體：`stage_l`（沒碰過這個任務）、`q1 λ=1`、`q1 λ=0`。

| 邊界 | stage_l | q1 λ=1 | q1 λ=0 | null（打亂標籤） | chance |
| --- | --- | --- | --- | --- | --- |
| 6（名冊） | 0.1350 | 0.1400 | 0.1150 | 0.070–0.095 | 0.0833 |
| 7（更正） | 0.1100 | 0.0950 | 0.0550 | 0.040–0.075 | 0.0833 |
| 8 | 0.0850 | 0.0700 | 0.1100 | 0.065–0.105 | 0.0833 |
| 9 | 0.0850 | 0.1200 | 0.0900 | 0.080–0.085 | 0.0833 |
| 10（問句） | 0.1050 | 0.0950 | 0.1100 | 0.070 | 0.0833 |

**每一個邊界、每一個載體都在 chance**，而且落在打亂標籤的 null 範圍內——包含名冊已經出現的
第 6 輪、更正之後的第 7 輪、以及答案已完全確定的第 10 輪。所以 Q1 的失敗不是「讀不出來」，
是**沒有東西被讀**。

**這個陰性結果需要自己的對照，否則可能只是探針壞了**。同一支探針換一個一定會在 state 裡的
標籤（`--probe-target chain`，四條線索鏈各用不同詞彙，chance 0.25）：

| 邊界 | 0 | 3 | 5（取用登記簿） | 6（名冊） | 7（更正） | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage_l | 0.225 | 0.205 | **1.000** | 0.585 | **1.000** | 0.820 | 0.230 | 0.230 |
| q1 λ=1 | 0.210 | 0.275 | **1.000** | 0.550 | **1.000** | 0.620 | 0.220 | 0.230 |

探針**有效**：第 5、7 輪的線索鏈是 **1.000**（null 0.19–0.25）。也因為它有效，第 9–10 輪的
0.22–0.23 才是壞消息：**兩輪前還明確可讀的內容，到了問句那一步已經讀不出來**——不是只有
「結論沒進去」，是「連案情主題都被後面的文字蓋掉」。這與 state 的幾何一致：問句邊界上跨
session 的平均成對 cosine 是 **0.9999**（stage_l）／0.9213（λ=1），殘餘變異的 participation
ratio 只有 **1.06**／1.64（滿秩 64）——state 幾乎只剩一個方向，而那個方向不編碼兇手。

**讀法**（照實）：
1. **瓶頸在表徵，不在讀出、也不在信用分配**：訊號到了每一輪（§50.12.2），但到的那個 `h` 沒有
   答案。修讀出、修梯度路徑都不會讓 Q1 過。
2. **Q1 的兩個臂都合理化了**：λ=1 要求模型在每個邊界都答一次，而那些邊界上什麼都沒有 →
   梯度把 head 推向邊際；這正好是「`David` 佔 0.6562、5/32 剛好是它的次數」與「λ=1 第 50 個
   epoch 就平掉、λ=0 還在降」的成因。
3. **下一個變數因此改名**：不是步數、不是寬度、也不是再校準一次過擬合，而是**「問句那一步的
   state 能不能留住第 5–7 輪的名冊與更正」**——這一輪量到的是「留不住」。round 8 的 per-turn
   keys／讀取→控制器現在有了與 §46 不同的理由（不是選不出來，是存進去的東西在問句前就沒了），
   但那是**另一個登記**，不是這一輪的結論。
4. **不宣稱**：(a) 線性 probe 讀不到不等於「非線性也讀不到」；(b) 這是三個特定 checkpoint 的
   state，不是「GRU 做不到」的一般結論；(c) 它不改變任何分數（核心 **0.00/10**、系統 **6.41**），
   也不是能力分數。
