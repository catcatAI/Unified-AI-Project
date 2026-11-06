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
