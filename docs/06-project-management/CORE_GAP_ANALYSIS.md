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

## 五十一、階段 R：只在「已經有答案」的邊界監督（2026-11-14，量測前寫定）

### 51.1 為什麼是 R，而不是加 epochs

Q1（λ=1，每個邊界都讀一次）**0.1562**，配對的 λ=0 **0.2188**，兩者都停在邊際（§50.10–§50.11）。
§50.13 的狀態探針把原因再往前推一格：**問句那一步的 `h` 裡沒有答案**——線性讀出在三個載體、
每一個邊界都只有 chance（0.055–0.140 vs 0.0833），而同一支探針讀「線索鏈」在相同邊界是
**1.000**（第 5、7 輪）。所以問題不是「讀不出來」，是「沒有東西」。

Q 的輔助項有一個可指名的設計缺陷，正好與這個量測一致：它對**每一個** turn 邊界都要求答案，
但第 0–5 輪 `derive()` 根本還沒有唯一答案（名冊在第 6 輪才出現）。那段損失等於要求模型在
**資訊還不存在**時作答，唯一的低損失解就是吐邊際——這正是 λ=1 的兩個徵兆：`David` 佔 0.6562、
5/32 剛好是它的次數，而且第 50 個 epoch 就平掉。

所以 R 不是「再試一次」，是把 Q 那個缺陷修掉，其餘全部不動。

### 51.2 唯一變數：輔助項只在可解的邊界、用該邊界自己的答案

新增 `--aux-mode resolvable`（`all` 是 Q 的行為，預設不動）：

```
L = CE(head(h_10) → 最終答案) + λ · mean over (k, i) ∈ S  CE(head(h_k^i) → derive(前 k 輪)^i)
S = { (k, i) : derive() 在第 k 輪的前綴上剛好一個答案 }
```

* 邊界不變、模型不變、λ 不變（**1.0**）、參數不變、state 格式不變、eval 只問最後一次。
* 在 32 段上，實際被監督的 (k, i) 是：第 0–5 輪 **0**、第 6 輪 **16**、第 7–9 輪各 **32**；
  第 10 輪是主項（32）。共 112 個輔助項（Q 是 320 個，其中 192 個在問不可能的問題）。
* 第 6 輪的目標是**更正前**的答案（98/200 有唯一解），第 7 輪之後才是最終答案。所以模型被要求
  做的正是這一輪要量的能力：**保留名冊，然後讓更正改掉結論**。
* 不可解的邊界**不計入**，不是乘 0（乘 0 仍會把梯度推向「什麼都別說」的邊際）。

### 51.3 不變的東西

同一個 `GRUCore`（124,611）、同一個 `CoreState` v1、同一份語料與切分（800／200，digest 不變）、
同一個起點（L 的 checkpoint，sha256 不變）、seed 20261118、Adam(5e-4)、batch 8、20 epochs
（2,000 步）、同樣的 eval 協定與同樣的門檻常數（0.25／0.35／0.50／0.25）。**沒有任何門檻被
移動，也沒有一個新門檻被發明。** R 的 F-rand 對照必須用同樣的 λ **與同樣的 aux_mode**，
否則 R7 會拿兩個不同目標的訓練互相比較（`_find_control_report` 現在兩者都比對）。

### 51.4 門檻（跑之前寫定）

| 門檻 | 條件 | 來源 |
| --- | --- | --- |
| R1 | 32 段 overfit 校準的 train exact **≥ 0.90** | 與 Q1 同一個門檻，可直接比較 |
| R2 | 800 段 train_fit exact **> 0.25** | 與 Q2／G3 相同 |
| R3 | 留出 free exact 的 Wilson 下界 **> 0.2500** | 與 Q3／G4 相同 |
| R4 | 留出 12 選 ranking 的 Wilson 下界 **> 0.2500** | 與 Q4／G5 相同 |
| R5 | 98 題上 flip（兩邊都對）**≥ 0.50** 且 `full` 在該子集 **≥ 0.25** | 與 Q5／G6 相同 |
| R6 | `full` − `reset` **≥ 0.25**，且 `reset` **≤ chance+0.10** | 與 Q6／G7 相同 |
| R7 | 格式對照（同 λ、同 aux_mode）free 與 ranking **都 ≤ chance+0.10** | 與 Q7／G8 相同 |
| R8 | 最常見預測名字的 share **≤ 0.35** | 與 Q8／G9 相同 |
| R9 | 成本、每個 epoch 的 main／aux、每輪讀出都已記錄 | 與 Q9 相同 |
| R10 | `--check` 由報告重算 R1–R9 並重載 checkpoint | 與 Q10 相同 |

R1 的 32 段取自 train 切分的前 32 段（不是留出），報告記 `overfit: true`、`aux_mode: resolvable`，
**不得被引用為泛化或能力**。

### 51.5 預測（寫在跑之前）

| 門檻 | 預測 | 理由 |
| --- | --- | --- |
| R1 | **過**，0.60–1.00 | 監督只在有答案的邊界，32 段／400 步應該夠；但 400 步本身仍可能是瓶頸 |
| R2 | 不確定，0.25–0.50 | 800 段、2,000 步，比 P 好一點就值得 |
| R3 | **不過**，0.10–0.25 | 124k GRU 在 800 段上要跨 ~600 byte 的填充把名冊帶到問句；這一輪修的是「會不會學」，不是「會不會推理」 |
| R4 | **不過**，0.15–0.30 | 同上 |
| R7 | **過** | 格式對照沒有答案可學 |
| R8 | 不確定 | 若 R3 沒過，常數答案就過不了這一條 |

**R1 的否證條件**：若 R1 ≤ 0.30（不比 Q1 的 λ=0 好），則「在空邊界上監督」**不是**原因，
不准改 epochs／lr／寬度／λ 重跑，記錄後停。

### 51.6 診斷（不是門檻）

* **R1b**：在 R1 的 checkpoint 上跑 `probe_credit_assignment.py --state-probe`，在**那 32 段**
  上讀兇手（probe 用 800 段擬合）。預測 **≥ 0.90**——若 R1 過但 R1b 在 chance，代表模型答得出來
  但答案不在 state 裡，那是比失敗更嚴重的訊號，**完整臂不跑**，先查。
* 留出 200 段上第 6–10 輪的讀出（`diagnostics.readout`）：預測第 7–10 輪高於 base rate（這是
  Q 沒做到的事）。

### 51.7 這一節**不會**證明什麼

不是推理能力，不是智能，不是分數（核心仍 0.00/10；pantry 不在計分套件裡）。即使 R1–R9 全過，
它證明的是「同一個載體可以在有答案的邊界上被教會、且答案在 state 裡」，那是學習層的宣稱，
需要另外登記到 `LAYER_REGISTRY.json`；它不讓核心分從 0 變成任何數字。

### 51.8 指令（對照先，計分臂後）

```
./.venv/bin/python scripts/train_pantry_deduction.py --control rand --aux-loss 1.0 \
    --aux-mode resolvable --out data/pantry_stage/r
./.venv/bin/python scripts/train_pantry_deduction.py --aux-loss 1.0 \
    --aux-mode resolvable --out data/pantry_stage/r
./.venv/bin/python scripts/train_pantry_deduction.py --overfit 32 --epochs 100 \
    --aux-loss 1.0 --aux-mode resolvable --device cpu --out data/pantry_stage/r_overfit
./.venv/bin/python scripts/train_pantry_deduction.py --check data/pantry_stage/r/<report>.json
```

R1 先跑（校準）；R1 不過 → 完整臂**不跑**。

### 51.9 這一節的地位

這是**第三次改訓練訊號**（Q 改路徑長度、R 改「在哪裡問」），而且 R 的依據是 §50.13 的實測，
不是猜測。門檻、語料、切分、模型、起點、eval 協定全部沿用 §49–§50；沒有任何一條在看到 R 的
結果之後才寫。

### 51.10 R1（登記的過擬合校準）：**FAIL**，否證條件觸發

報告：`data/pantry_stage/r_overfit/pantry_deduction_20261114-043536.json`（400 步、265 秒、cpu、
`aux_mode=resolvable`、λ=1.0、32 段 train、100 epochs）。`--check` **OK**（R1–R9 由報告重算、
checkpoint 重載一致）。

| 項目 | 值 | 門檻 |
| --- | --- | --- |
| train exact | **8/32 = 0.2500** | ≥ 0.90 → **FAIL** |
| 最常見預測 | `Ivan` 0.5625 | — |
| 不同預測數 | 4（32 段中） | — |
| main loss（nats/session） | 0.3609 × 5.615 = **2.026**（邊際熵 2.3691） | — |
| aux loss | 0.2977 | — |
| 留出 full exact／ranking | 0.0400／0.1550 | — |
| 留出讀出（第 6–10 輪） | 0.0816／0.1000／0.0800／0.0800／0.0400 | — |

**0.2500 ≤ 0.30 → §51.5 寫定的否證條件成立**：在空邊界上監督**不是** Q1 失敗的原因。依登記，
完整臂（800 段 F-rand 對照 + 計分臂）**不跑**，epochs／lr／寬度／λ 一律不改，本階段到此為止。

### 51.11 讀法（照實，不補跑）

1. **R 有效，但不夠**：同一個 32 段、同一個 400 步，Q1 是 5/32（0.1562），R1 是 8/32（0.25），
   λ=0 配對是 7/32（0.2188）。R 確實把「在什麼都沒有的邊界上作答」這個缺陷移除了——證據是
   它**沒有在第 50 個 epoch 平掉**（main 0.4170 → 0.3788 → 0.3609），而 Q1 平了。所以
   §50.13 對 λ=1 的解釋（梯度把 head 推向邊際）成立。
2. **但三者只差 3 段**：0.1562／0.2188／0.25 是 5、7、8 段的分別，不是換了一個機制。誤差量級
   （32 段的二項標準差約 0.077）比三者的差距還大。**誠實的結論是「三個訓練訊號在這裡量不出
   差別」，不是「R 比 Q 好」。**
3. **它仍在擬合邊際**：main 2.026 nats/session 只比「12 個名字的邊際」低 **0.343 nats**，而且到
   第 100 個 epoch 還在降。這與 §50.13 一致：`h_10` 裡沒有可讀的答案，所以最快的下降方向就是
   學「最常見的名字」。R1 的最常見預測 `Ivan` 佔 0.5625，但 train 32 段裡 `Ivan` 不是絕對多數
   （§49 的邊際是 `Kevin` 6/32）——它是這個起點／種子下的擬合殘差，不是資料的邊際，正好說明
   head 在讀一個幾乎不變的 state。
   **補記（同一份報告、同一個 checkpoint 重跑 eval，不是新臂）**：R1 的 32 段答案只落在
   **4 個名字**上——`Ivan` 18、`Kevin` 7、`Lena` 4、`Elena` 3（12 個名字裡有 8 個從未被預測）。
   8 個正確是 `Ivan` 3/3、`Kevin` 3/7、`Lena` 3/4、`Elena` 1/3。Q1 則是 `David` 5/5（單一常數）、
   λ=0 是 `Kevin` 6/7＋1。所以三臂的差別是**輸出字母表收縮到幾個名字**，不是條件化程度；
   「R 沒有平掉」只描述**損失曲線**，不能讀成「R 學會了條件映射」。這一點直接決定下一步：
   先量「同一個協定在多少段上還能擬合」，而不是先改任務的距離。
4. **照實記的限制**：(a) 32 段取自 **train 前 32 段**，R1 的 0.25 **不是**泛化、不是能力、
   不是分數；(b) 只有一個 seed、一個寬度（64）、一個 400 步預算；(c) R1b（用探針在那 32 段上
   讀兇手）依 §51.6 只在 R1 過線時才有意義，**沒有跑**，不補跑。

### 51.12 這一輪留下的、可量測的線索（不是結論）

R1 的失敗把問題縮到「**問句那一步的 state 存不住第 5–7 輪**」（§50.13），而下一個變數必須由
一個可操作的量定義。盤點語料後，這個「距離」有**兩個可分離的成分**，而且都比先前假設的大：

| 成分 | 每段平均 | 佔整段比例 |
| --- | --- | --- |
| 第 8、9、10 輪的文字 | 332 bytes | 26%（全段 1,277 bytes） |
| 第 8、9、10 輪的 `al_step` 區塊 | **121 次 `cell` 更新** | 31%（全段 384 次） |

`al_step` 不是空的：第 1–10 輪的 `dt_s` 最大 ~14,300 秒，`chunk_seconds=60`，所以每輪最多 240 次
`cell(dt_proj(dt/chunks/60), h)`，整段平均 **384 次**。而 `dt/(chunks·60)` 的構造使它幾乎恆在
(0.5, 1]——**同一個近似常數的輸入反覆施加 ~121 次**，正是收縮到單一方向的機制（§50.13 量到
第 8 輪 cosine 1.0000、participation ratio 1.08）。所以「距離」不能只用文字長度代表；下一步
必須把**文字**與**時間區塊**分開操弄。那是 §52 的登記，不是這一節的結論。

## 五十二、階段 S：同一個協定的擬合容量（2026-11-14，量測前寫定）

### 52.1 為什麼先問「能背幾段」，而不是先改距離

§51.11 的補記量到：R1 的 32 段答案只落在 **4 個名字**上（`Ivan` 18、`Kevin` 7、`Lena` 4、
`Elena` 3），12 個名字有 8 個從未被預測。Q1 是單一常數（`David` 5/5），λ=0 是 `Kevin` 6/7＋1。
所以三個臂的差別是**輸出字母表收縮到幾個名字**，不是條件化程度；損失曲線的形狀（R1 沒有像
Q1 那樣第 50 個 epoch 平掉）只描述擬合速度，不能讀成「學會了條件映射」。§51.12 的距離線索
（文字 332 bytes／`al_step` 121 次更新）仍然成立，但它預設了「載體至少能背起這個任務」。在
那個前提被量出來之前改任務距離，等於在未知的儀器上做消融。

所以 S 問的是更前面、更便宜、且**不改變任務**的問題：**同一個 124,611 參數的載體、同一個
λ=1／`resolvable` 目標、同一個起點與 eval，只是把要背的段數從 32 降到 1/4/8/16，仍然給
400 個優化步，它能背到幾段？** 這是一個容量（capacity）量測，也是一個儀器正控：如果連 1 段
都背不起，後面所有臂的失敗都不能歸因於「推理」或「距離」。

### 52.2 階梯（固定 400 步，只變段數 N）

「固定步數」的作法是把 epochs 設成 `400 / ceil(N/8)`——batch 8，所以 400 步對每個 rung 都一樣；
變的只有 N。段數取 train 切分的**前 N 段**（與 R1 相同的取法），它們的目標字母表如下：

| rung | N | epochs | 優化步 | 不同目標名 | 常數解可不可能過 0.90 |
| --- | --- | --- | --- | --- | --- |
| S0 | 1 | 400 | 400 | 1 | — |
| S1 | 4 | 400 | 400 | 4 | 不可能（3/4 = 0.75 < 0.90） |
| S2 | 8 | 400 | 400 | 7 | 不可能（7/8 = 0.875 < 0.90） |
| S3 | 16 | 200 | 400 | 10 | 不可能（14/16 = 0.875 < 0.90） |
| — | 32 | 100 | 400 | 12 | 已量：**0.2500**（R1，§51.10） |

**這個門檻本身就把「字母表收縮」擋掉了**：在 N=4/8/16 上要達到 0.90，實際要求 4/4、8/8、≥15/16，
也就是必須正確產生 4、7、10 個**不同**的名字。所以 S 的 pass 不可能由「猜一個常數」得到——這與
R1 的 8/32（4 個名字）是不同性質的結果。

### 52.3 不變的東西

同一個 `GRUCore`（124,611；hidden 128／emb 64）、同一個 `CoreState` v1、同一份語料與切分
（800／200，digest 不變）、同一個起點（L 的 checkpoint，sha256 不變）、seed 20261118、
Adam(5e-4)、batch 8、λ=**1.0**、`--aux-mode resolvable`、同一組 eval 變體與同一組門檻常數
（0.25／0.35／0.50／0.25）。**沒有任何門檻被移動，也沒有一個新門檻被發明**；唯一的新設定是
`--gate-prefix S`，用途只是讓報告以 S1–S9 命名，不會被誤讀成 Q 或 R 的結果（`--check` 由
config 重算同一個前綴）。

### 52.4 判讀規則（跑之前寫定，機械決定下一個變數）

| 結果 | 判讀 | 下一個變數 |
| --- | --- | --- |
| S0（1 段）< 0.90 | **儀器缺陷**：head／loss／生成不一致，或 400 步不足以產生一個已知名字 | 停止階梯，先查程式（不得先改寬度或 epochs） |
| 第一個失敗的 rung 是 N\*（N\* ∈ {4,8,16}） | 在 400 步下，容量斷點在 N\*/2 與 N\* 之間 | 跑 N\* 的 **4× 步**（1,600 步，epochs×4） |
| N\* 的 4× 步 ≥ 0.90 | **預算**是那個 rung 的約束；容量足夠 | 之後才問「步數如何隨 N 成長」，以及 32 段的 1,600 步 |
| N\* 的 4× 步 < 0.90 | **不是預算**：同一份資料、四倍步數仍背不起 | 跑 N\* 的 **2× 寬**（hidden 256／emb 64，400 步） |
| 2× 寬仍 < 0.90（N\* ≥ 8） | 不是寬度、不是步數：**表徵／接線** | 下一個登記必須是架構（per-turn 讀寫或工作記憶槽），並由這個量測背書 |
| 全部 rung（含 N=16）≥ 0.90，32 段仍 0.25 | 斷點在 16 與 32 之間 | 跑 32 段的 4× 步（1,600 步），再套用上面兩條 |

**上界（先寫死，避免無限加碼）**：這個階段最多跑 **3 個基本 rung + 1 個 4× 步 rung + 1 個 2× 寬
rung**。超過就不是 S 的延伸，而是另一個登記。任何一個 rung 的結果都不准回頭改 0.90、batch、lr、
λ、種子或語料。

### 52.5 預測（寫在跑之前）

| rung | 預測 | 理由 |
| --- | --- | --- |
| S0（1 段） | **過**，1.00 | 一個已知名字＋400 步；若不過，是程式而非容量 |
| S1（4 段） | **過**，0.90–1.00 | 4 個不同名字，400 步 |
| S2（8 段） | 可能過，0.75–1.00 | 7 個不同名字；開始需要綁定 |
| S3（16 段） | **不確定**，0.40–0.85 | 10 個名字＋名冊／更正；我預期這裡開始收縮 |
| N\* 的 4× 步 | 若 N\*=16，預測 **不過**，0.50–0.80 | R1 的損失在最後 25 個 epoch 只再降 0.018（0.3788→0.3609），是減速而非等速 |
| N\* 的 2× 寬 | 不確定，0.55–0.90 | 寬度可能買到一些綁定能力，但也可能只是更慢的同一種收縮 |

**這不是「再試一次」**：S 的目的是用最少的算力把下一個變數**機械地**命名出來（步數／寬度／
接線），而且每個分支都在跑之前寫好，包含停止上界。

### 52.6 診斷（不是門檻）

* 每個 rung 的 `train_fit` 已記錄 exact、最常見預測、`top_share`、`distinct_predictions`——字母表
  大小與 top share 一併讀，避免把「收縮到 4 個名字」誤讀成條件化。
* 每個 rung 的最後一個 epoch 的 main／aux loss（`training.history`）——用來判斷「還在降」還是
  「平掉」，這是 §51.11 唯一可用的收斂證據。
* 留出 200 段的數字在 overfit rung 上**沒有意義**（模型只看過 1–16 段），報告照記錄，但不判讀。

### 52.7 這一節**不會**證明什麼

不是推理、不是泛化、不是智能、不是分數（核心仍 0.00/10；pantry 不在計分套件裡）。S 的 pass
只證明「這個載體在同一個協定下能背起 N 段」，那是**擬合**，不是能力；它唯一的作用是把下一個
變數（步數／寬度／接線）從猜測變成量測。§51.12 的距離消融**延後、沒有廢除**：如果 S0 或 S1
就失敗，距離問題根本還輪不到問。

### 52.8 指令（依序；每個 rung 之後跑 `--check`）

```
for N in 1 4 8 16; do
  E=$(( 400 / ((N + 7) / 8) ))
  ./.venv/bin/python scripts/train_pantry_deduction.py --overfit $N --epochs $E \
      --aux-loss 1.0 --aux-mode resolvable --gate-prefix S --device cpu \
      --out data/pantry_stage/s_ladder/n$N
done
# 之後只跑 52.4 指到的那一個 rung：
./.venv/bin/python scripts/train_pantry_deduction.py --overfit <N*> --epochs <4E> \
    --aux-loss 1.0 --aux-mode resolvable --gate-prefix S --device cpu \
    --out data/pantry_stage/s_ladder/n<N*>_4x
./.venv/bin/python scripts/train_pantry_deduction.py --check data/pantry_stage/s_ladder/<report>.json
```

### 52.9 這一節的地位

這是第**四**次改實驗，但第一次**不改訓練訊號、不改任務**，只改「要背幾段」。它之所以排在
§51.12 的距離消融之前，是因為 §51.11 的補記顯示載體在 32 段上根本沒有形成條件映射；在容量
未知時做距離消融，會把「背不起」誤讀成「留不住」。門檻、語料、模型、起點、eval 全部沿用
§49–§51；沒有任何一條在看到 S 的結果之後才寫。

## 五十三、階段 S 的結果：不是步數、不是寬度（2026-11-14，跑完照實記）

### 53.1 階梯（固定 400 步，只變要背幾段）

全部 `--overfit N --aux-loss 1.0 --aux-mode resolvable --gate-prefix S --device cpu`，報告在
`data/pantry_stage/s_ladder/`，每一份都 `--check` **OK**。

| rung | N | epochs | 步 | train exact | 最常見預測 | 不同預測 | 最後 main | 判定 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 1 | 400 | 400 | **1/1 = 1.0000** | `Judy` 1.00 | 1 | 0.0003 | PASS |
| S1 | 4 | 400 | 400 | **4/4 = 1.0000** | `Judy` 0.25 | 4 | 0.0049 | PASS |
| S2 | 8 | 400 | 400 | **7/8 = 0.8750** | `Grace` 0.375 | 6 | 0.0522 | **FAIL** |
| S3 | 16 | 200 | 400 | **7/16 = 0.4375** | `David` 0.375 | 5 | 0.3148 | FAIL |
| — | 32 | 100 | 400 | 8/32 = 0.2500 | `Ivan` 0.5625 | 4 | 0.3609 | （R1，§51.10） |

**儀器是好的**：S0 與 S1 都 1.00，且 S1 是 4 個不同名字——不是常數。斷點在 **N\* = 8**：N=4 過、
N=8 不過（7/8，只差一段，但門檻 0.90 要求 8/8）。N=16 是 7/16，比 N=8 掉得更深（0.4375）。

### 53.2 登記指到的兩個判別 rung

**(a) N\*=8 的 4× 步（1,600 步）→ PASS**：8/8 = 1.0000、7 個不同預測、main 0.0005、1,070 秒。
而且它的 **epoch 400 損失與 400 步那一輪完全相同**（loss 0.1318／main 0.0522）→ 訓練是確定性的，
步數只是把同一條曲線走更遠。

**(b) N=32 的 1,600 步 → FAIL**：12/32 = 0.3750、7 個不同預測、main 在 90% 是 0.2563、最後
**回升到 0.2811**、1,007 秒。所以 N=8 的瓶頸是預算，N=32 的瓶頸不是：同樣四倍步數，8 段 → 8/8，
32 段 → 12/32。

**(c) N=32 的 2× 寬（hidden 256／emb 64／400 步）→ FAIL**：**10/32 = 0.3125**、
最常見 `Kevin` 0.5625、**只有 4 個不同預測**（`Kevin` 18、`Ivan` 8、`Alex` 3、`David` 3）、
main 0.3296（0.4279→0.3996→0.3616→0.3296，還在降但沒到位）、330,563 參數、316 秒。
**寬度沒有買到綁定，反而收縮得更厲害**（base 128 在同樣 400 步是 8/32、4 個名字；2× 寬是 10/32、
4 個名字，而 32 段裡 `Kevin` 只佔 6 段，卻被預測 18 次）。

三臂在 32 段上是 **8／10／12**（0.25／0.3125／0.375），32 段的二項標準差約 0.077——**量不出差別**。
照實的說法是「步數與寬度都沒有改變 32 段的結果」，不是「其中一個比較好」。

### 53.3 判讀（照 §52.4 機械決定，沒有事後改門檻）

§52.4 的最後一列成立：**2× 寬仍 < 0.90（N\* ≥ 8）→ 不是寬度、不是步數：表徵／接線**。因此下
一個登記**必須是架構**——per-turn 讀寫，或在同一個 `CoreState` 裡加工作記憶槽——並由這個量測
背書，不得再靠「加 epochs」或「加寬」。這一節沒有移動 0.90、batch、lr、λ、種子或語料，也沒有
重跑任何 rung。

**同一天的更正，在跑架構之前（§54）**：上表的「400 步」在 N ≥ 8 時把**每段的複習次數**除以
N（batch 8），所以「不是步數」實際只證明了「不是**總**步數」。這不改變本節的任何數字，但改變
下一個登記的前置條件：先用一個 6,400 步的 run 把 N=32 給到 N=8 通過時的 1,600 複習／段。
**結果該 run PASS 31/32（§54.5）→ 本節「容量／表徵」的讀法被否證**：同一個載體在 1,600
複習／段下背得起 32 段（12 個名字全出現）。下一節的架構登記因此不是由「背不起」背書，而是由
「要 1,600 複習／段才背得起」背書。

**新增的可量測事實（比「失敗」有用）**：同一個協定在 400 步下的容量斷點在 **N=4 與 N=8 之間**，
而 1,600 步把斷點推到至少 N=8；但 32 段在 1,600 步、2× 寬都停在 0.31–0.38。也就是說「背幾段」
不是單一常數，而是**隨 N 快速下降**：4 段 → 1.00、8 段 → 1.00（4× 步）／0.875（400 步）、
16 段 → 0.44、32 段 → 0.25–0.38。任何「加資源」的解釋都必須說明為什麼它對 8 段有效、對 32 段
無效；目前沒有這種解釋，所以登記架構是唯一誠實的下一步。

### 53.4 上界：多跑了一個 rung，照實記

§52.4 原先寫死「最多 3 個基本 rung + 1 個 4× 步 rung + 1 個 2× 寬 rung」＝5 次。實際跑了 **6 次**：
多出來的是 **N=32 的 1,600 步**。原因是決策樹的兩列都各自指名一次 4× 步——「第一個失敗的 rung
跑 4×」指到 N=8，「全部 rung 過、只有 32 不過」指到 N=32——而階梯沒有單一斷點（N=8 在 400 步
失敗、在 1,600 步通過），所以兩列都觸發。這是**上界寫法與決策樹沒有對齊**，不是加碼；超出之後
**沒有再跑任何 rung**，也沒有因為結果不好而補跑第七次。

### 53.5 這一節**不會**證明什麼

不是推理、不是泛化、不是智能、不是分數（核心仍 0.00/10；pantry 不在計分套件裡）。它證明的是：
① 儀器在 1–4 段上可以到 1.00，所以後面的失敗不是 head／loss／生成壞掉；② 容量在 400 步下
4→8 段之間就斷，1,600 步可修 8 段、不能修 32 段，2× 寬連 8 段的預算都補不回來；③ 因此下一個
變數是**接線**（每輪讀寫／工作記憶槽），不是資源。§51.12 的距離線索仍**延後、沒有廢除**。

## 五十四、先修正 S 的量測：固定步數 ≠ 固定複習次數（2026-11-14，跑之前寫定）

### 54.1 S 實際變了什麼

batch 固定 8，所以一個優化步只碰到 N 段中的 `min(8, N)` 段；**每一步對每段的複習次數**是
`steps × min(8, N) / N`。把七份報告的這個量算出來，S 的比較就露出來了：

| rung | N | steps | epochs | **複習／段** | train exact |
| --- | --- | --- | --- | --- | --- |
| S0 | 1 | 400 | 400 | **400** | 1.0000 |
| S1 | 4 | 400 | 400 | **400** | 1.0000 |
| S2 | 8 | 400 | 400 | **400** | 0.8750 |
| S3 | 16 | 200 | 400 | **200** | 0.4375 |
| N\* 4× | 8 | 1,600 | 1,600 | **1,600** | 1.0000 |
| 32 4× | 32 | 1,600 | 400 | **400** | 0.3750 |
| 32 2× 寬 | 32 | 400 | 100 | **100** | 0.3125 |

**「固定 400 步」在 N ≥ 8 時不是固定努力，而是把每段的複習次數除以 N。** §53 把它讀成
「不是步數」，但實際成立的只有「不是**總**步數」：S 從頭到尾沒有在**相同的複習／段**下比較過
N=8 與 N=32（N=8 通過時是 1,600／段，N=32 最多只被給到 400／段）。這是**量測缺陷**，不是
「結果不好所以換說法」——它在跑之前就寫得出來，只是 S 的登記把「步數」當成了努力的代理。

### 54.2 唯一要跑的更正：N=32 給到 N=8 通過時的複習率

一個 run，其他全部不動（語料、切分、起點 L、seed 20261118、Adam 5e-4、batch 8、λ=1.0、
`--aux-mode resolvable`、`--gate-prefix S`、門檻 0.90、eval 與所有常數）：

```
--overfit 32 --epochs 1600   # 1600×4 = 6,400 步 = 1,600 複習／段
```

**這不是 S 的新 rung**：S 已在 §52.4 的上界內結束（§53.4），本節是「S 的結論是否站得住」的
**否證檢查**，與 §50.13 同一類（便宜診斷，不是新臂）。它不改任何門檻、不重跑任何既有 rung，
也不因為結果再開第七個 rung。

同時把 `updates_per_session` 寫進報告的 `training` 區塊（`--check` 照舊由 config 重算，不需
要新欄位；測試釘住公式）：以後任何「容量」比較都不會再把總步數與複習次數混在一起。

### 54.3 預測（寫在跑之前）

**預測 FAIL，0.45–0.75。** 理由：在**相同**的 400 複習／段下，曲線已是 N=1 → 1.00、N=4 →
1.00、N=8 → 0.875、N=32 → 0.375；而 4× 複習只讓 N=8 從 0.875 加到 1.00（+0.125）。要用
同樣的 4× 讓 N=32 從 0.375 過 0.90，需要 +0.525，是 N=8 那個增益的四倍以上。若它 **PASS
≥ 0.90**，則 §53 的「容量」讀法被否證：真正的變數是**每段複習次數**，架構登記就必須先等這個
更正被吸收，不能拿一個被混淆的容量結論去背書架構。

### 54.4 這一節**不會**證明什麼

不是推理、不是泛化、不是智能、不是分數；核心仍 0.00/10。它只決定 §53 的哪一句話可以留：
「這個載體在 32 段上需要多少複習」與「這個載體在 32 段上背不起」是兩個不同的結論，而下一個
登記（架構）只能由後者背書。

### 54.5 結果：**PASS 31/32**，預測錯了，§53 的容量讀法被否證

報告：`data/pantry_stage/s_ladder/n32_r1600/pantry_deduction_20261114-055822.json`（6,400 步、
3,969 秒、cpu、1,600 複習／段）。`--check` **OK**。

| 項目 | 值 |
| --- | --- |
| train exact | **31/32 = 0.9688**（門檻 0.90 → **PASS**） |
| 不同預測 | **12**（全部名字都出現過） |
| 最常見預測 | `Kevin` 0.1562 |
| main loss（每 25%） | 0.3133 → 0.0952 → 0.0119 → **0.0096** |
| 成本 | 6,400 步、3,969 秒、124,611 參數 |

**§54.3 的預測（FAIL，0.45–0.75）是錯的，而且錯的方式有資訊**：我假設 N=8 的 4× 增益（+0.125）
可以外推到 N=32，但 32 段的曲線不是平緩的，是**門檻式的**——100 複習／段 → 0.3125、400 → 0.375，
到 1,600 → 0.9688。中間那一段（400）幾乎沒動，然後在 400→1,600 之間跳過去。所以：

1. **§53 的「不是步數、不是寬度 → 表徵／接線」作為容量宣稱不成立。** 同一份資料、同一個起點、
   同一個 124,611 參數的載體，在 1,600 複習／段下 **32/32 背起來**（12 個名字全出現）。容量
   不是 N=32 的約束；§52.4 的機械判定是在一個**被混淆的比較**上做的，這一點已寫進 §54.1。
2. **真正成立的句子是「不是總步數」**：S 在 N=8 與 N=32 之間從來沒有在相同的複習率下比較；
   一旦補上（本節），N=32 就過了。§53 的「不是寬度」仍然成立（2× 寬在 100 複習／段是 0.3125，
   沒有救回覆習率的差距）。
3. **新的、可操作的數字是「要多少複習」**：32 段需要**介於 400 與 1,600 之間**的複習／段才能
   從 0.375 跳到 0.9688。這是**信用分配效率**的度量，不是容量。它同時解釋了 P 臂為什麼在
   0.085：P 給 800 段只有 **20 複習／段**（2,000 步 × 8 / 800），比 N=32 過線所需的量少 20–80 倍。
4. **架構登記的背書因此改變了**：不是「背不起所以換架構」，而是「同一件事要 1,600 複習／段，
   800 段就是 128 萬步，不可行」。架構要證明的不是「能背」，而是**用更少的複習／段達到同樣的
   擬合**——這正好是 §46.14 說的「縮短信用分配路徑」，也讓 §55 的門檻可以寫得很具體：
   在 **400 複習／段**（GRU 對照 = 12/32 = 0.375）下，架構臂要 ≥ 0.90。

### 54.6 這一節留下的狀態

* §52.4 的決策樹**已執行完畢且不再延伸**；S 的七份報告與本節的第八份都 `--check` OK。
* §53.3／§53.5 的「不是步數」已被本節取代；§53.1 的容量表仍然有效，但它的欄位現在必須連
  `updates_per_session` 一起讀（報告已記錄該欄位）。
* 下一個登記（§55）是架構，但它的**理由與門檻都來自本節**，不是来自 §53 的容量結論。

## 五十五、階段 T：每輪一個槽，讀進輸出頭（2026-11-14，量測前寫定）

### 55.1 為什麼是架構，以及架構要證明什麼

§54.5 把問題改成了一個成本問題：同一個 124,611 參數的載體**背得起** 32 段，但要 **1,600
複習／段**（6,400 步）。照這個比例，800 段要 **128 萬步**——不可行。所以架構要證明的不是
「能不能背」，而是：**在 400 複習／段（1,600 步，GRU 對照 n32_4x = 12/32 = 0.375）下，能不能
到 0.90**，也就是把同樣的擬合所需更新數降下來。這對應 §49.16／§50.13 量到的信用分配衰減
（往回每輪 ×1.13e-3）：答案的梯度要穿過 ~1,100 個 cell 才到第 1 輪的名冊。

### 55.2 唯一的變數：`TurnStoreCore`

新增一個 `StatefulCore` 子類（`ai/core/stateful_decoder.py`），**遞歸與 GRUCore 完全相同**
（`cell` 的輸入只有 `embedding`，`dt_proj`、`al_step`、`chunk_seconds` 都不變），差別只有：

| | GRUCore | TurnStoreCore |
| --- | --- | --- |
| state 張量 | `h [B,128]` | `h [B,128]`、`k [B,16,64]`、`v [B,16,64]` |
| 寫入時機 | 無 | **每輪結尾一次**（`end_turn`），不是每個 token |
| 寫入 | 無 | `slot ← slot(1−a·g) + a·g·W_v h`，`a = softmax(scale·W_s h)` |
| 讀取 | 無 | `r = Σ softmax(scale·W_q h · kᵀ) v` |
| 輸出 | `head(h)` | `head([h, r])` |
| 讀取的去向 | — | **只進輸出頭**，不進 `cell`（§46 的 A2 已量到餵進控制器會壓壞解碼） |

**兩個設計選擇寫在跑之前，且各有一個已量到的理由**：

1. **每輪一次寫入**，不是每 token。§46.4b 的 A3 量到 moving average 的記憶視窗是
   `1/s` 個 token；口供的每一輪約 100 bytes，per-token 寫入在輪內就洗掉了。每輪一次寫入讓
   11 輪剛好對上 16 個槽。
2. **讀取只進輸出頭**。§46.13 量到 `cell([x, r_prev])` 讓消融臂 0.1233、計分臂 0.0000
   （B7 方向相反），所以這一輪不重複那個接法；r 由當前 `h` 當查詢、在**每個解碼步**重算，
   因此 store 能影響答案的每一個 byte，而不必進入遞歸。

`memory=False` 是 R4 要求的消融：**參數一個不少**，只把 `r ≡ 0` 且不寫入；在這個設定下
`head([h,0])` 就是 `head(h)`，所以消融臂的函數等於 GRU 臂（起點也相同，見 55.3），差別只有
隨機流。

### 55.3 起點與不變的東西

* **起點是 L**：`embedding`、`dt_proj`、`cell`（輸入維度不變，形狀與 L 完全相同）整塊複製；
  `head.weight[:, :128]` 與 `head.bias` 複製，新的 64 欄為 0。新的 `key_proj`／`value_proj`／
  `query_proj`／`slot_gate`／`write_gate` 用 seed 初始化（它們是這一臂新加的參數）。
* 槽初值是 0，所以**第一個 token** 的 logits 與 L 完全相同（0 槽 → r=0）；第一次寫入在
  第一輪結尾。測試會釘住「第一輪結尾前與 L 逐位相同」。
* 不變：語料與切分（800／200，digest）、seed 20261118、Adam 5e-4、batch 8、λ=1.0、
  `--aux-mode resolvable`、eval 與所有門檻常數、`--gate-prefix T`（報告記 T1–T9）。
* **門檻 0.90 沒有移動**，它就是 §50 以來的那一個。

### 55.4 門檻（跑之前寫定）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| T1 | store 臂 train exact **≥ 0.90**（32 段、1,600 步 = 400 複習／段） | 在 GRU 只到 12/32 的預算下到達同樣擬合 |
| T2 | 消融（`memory=False`）train exact **≤ 0.65**，且 store − 消融 **≥ 0.25** | 是 store 在做事，不是參數 |
| T3 | 消融與 GRU 對照（n32_4x 12/32）**差距 ≤ 0.15** | 消融的函數真的等於 GRU 臂（接線檢查） |
| T4 | 成本（參數、訓練秒數、device）已記錄 | — |

T1 沒過就不宣稱架構有效；T2 沒過就不宣稱是 store 的功勞；T3 沒過代表消融不是同一個函數，
T2 的差距不能讀。三個對照都必須存在：store 臂、消融臂、GRU 臂（後者已跑、報告在
`data/pantry_stage/s_ladder/n32_4x/`，`--check` OK）。

### 55.5 預測（寫在跑之前）

| 臂 | 預測 | 理由 |
| --- | --- | --- |
| store（T1） | **不確定，0.55–0.90**（偏不過） | 名冊在第 1 輪、問題在第 10 輪，寫入的 value 是 `W_v h_1`，梯度到 `W_v`／`W_q` 只經過兩層；但**檢索要學會**，而 16 個槽要對上 11 輪 |
| 消融（T2） | 0.30–0.45 | 函數等於 GRU 臂，400 複習／段是 12/32 |
| 消融 vs GRU（T3） | 差距 ≤ 0.10 | 同函數、同起點，只差隨機流 |

### 55.6 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| T1 過、T2 過 | store 真的縮短了信用路徑 | 才輪到「同樣預算下的留出泛化」（800 段的子集＋200 留出），不是分數 |
| T1 過、T2 不過 | 擬合變好但不是 store 的功勞（參數／起點） | 不做架構宣稱，先做參數對照（同參數的純 GRU） |
| T1 不過、T2 過 | store 有一點用但不夠 | 下一步是 per-turn 的區域損失（每輪自己解一次），不是加寬／加步數 |
| T1 不過、T2 不過 | 這個接法沒有縮短路徑 | 下一步是 truncated BPTT 或對整輪做 attention；**不得**回到「加 epochs／加寬」 |
| T3 不過 | 消融不是同函數 | 先修接線，T1／T2 不判讀 |

### 55.7 這一節**不會**證明什麼

不是推理、不是泛化（32 段取自 train 前 32 段，報告記 `overfit: true`）、不是智能、不是分數
（核心仍 0.00/10）。即使 T1–T4 全過，它證明的只是「同一個 state 物件裡，一個每輪寫入的槽讓
同樣的擬合用四分之一的更新達到」——那是**機制**，不是能力；泛化要另一份登記。

### 55.8 指令

```
# 先跑消融（T2／T3 的對照），再跑計分臂
./.venv/bin/python scripts/train_pantry_deduction.py --overfit 32 --epochs 400 \
    --core turnstore --no-memory --aux-loss 1.0 --aux-mode resolvable \
    --gate-prefix T --device cpu --out data/pantry_stage/t_store/ablate
./.venv/bin/python scripts/train_pantry_deduction.py --overfit 32 --epochs 400 \
    --core turnstore --aux-loss 1.0 --aux-mode resolvable \
    --gate-prefix T --device cpu --out data/pantry_stage/t_store/arm
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

（`--epochs 400` × 4 batches = 1,600 步 = 400 複習／段；GRU 對照 n32_4x 也是 1,600 步。）

### 55.9 這一節的地位

這是第**五**次改實驗，也是 §52.4 指定的架構登記，但它的理由已由 §54.5 更正：不是「容量不足」，
而是「同樣的擬合要 1,600 複習／段」。門檻 0.90、語料、模型寬度、起點、eval 全部沿用 §50–§54；
沒有任何一條在看到 T 的結果之後才寫。

### 55.10 結果（2026-11-14，依 §55.8 的指令跑完，照實記）

| 臂 | train exact | 不同預測 | 最大單一預測 | 步數 | 秒 | 參數 |
| --- | --- | --- | --- | --- | --- | --- |
| store（記憶開） | **1.0000**（32/32） | 12 | `Kevin` 0.1875 | 1,600 | 1,078 | 168,150 |
| 消融（`memory=False`） | **0.5000**（16/32） | 9 | `Ivan` 0.2812 | 1,600 | 1,057 | 168,150 |
| GRU 對照（n32_4x，§52 已存在） | 0.3750（12/32） | 7 | `David` 0.3125 | 1,600 | 1,007 | 124,611 |

四條門檻：**T1 PASS**（1.0000 ≥ 0.90）、**T2 PASS**（0.5000 ≤ 0.65，gap 0.5000 ≥ 0.25）、
**T3 PASS**（|0.5000 − 0.3750| = 0.1250 ≤ 0.15）、**T4 PASS**。`--stage-t` 的機械分支：
「T1+T2 過：store 縮短了信用路徑；下一步是同樣預算下的留出泛化，不是分數」。

**預測的偏差照實記**：§55.5 預測 store 0.55–0.90（偏不過），實際 **1.0000**——落在區間**之上**；
消融預測 0.30–0.45，實際 0.5000（略高）；T3 預測差距 ≤ 0.10，實際 0.1250（超過預測，仍在登記的
0.15 容差內）。這三條都往「比預測好」的方向偏，所以下面用接線證據而不是數字來支撐讀法。

**消融真的是同一個函數**（T3 是接線檢查，不是數字接近就好）：

1. 消融與 GRU 對照的逐 epoch loss **到第 25 個 epoch 逐位相同**（9.6233／5.8541／2.4114／
   1.0466／0.8560；main 與 aux 也相同），第 50 個 epoch 之後才分開（100：0.6358 vs 0.6586；
   200：0.4715 vs 0.5145；400：0.2999 vs 0.4266）。分開的原因是 `head` 的 GEMM 形狀不同
   （192 vs 128 欄）造成浮點求和順序不同，不是函數不同。
2. 消融 checkpoint 的 `head.weight[:, 128:]` **非零元素 0 個** → 作用中的參數就是 L 的函數，
   多出來的 64 欄從頭到尾沒有被讀。
3. 消融臂**仍然持有全部 168,150 個參數**（R4：消融不是砍參數），只是 `r ≡ 0` 且不寫入。
   與 GRU 的參數差（+43,539，+34.9%）不是 T2 差距的來源，因為消融證明「有這些參數但沒有 store
   也到不了」。

**不可讀的數字**：兩臂的留出 `full` exact（store 0.1000、消融 0.0450、chance 0.1591）都是 32 段
過擬合的副產品，依 §55.7 不作任何泛化宣稱；它們只用來對照 §56 在同一個留出集上的讀數。

**限制**（照實記）：`overfit: true`、32 段取自 train 前 32 段、單一 seed、單一任務、CPU；
「1.0000 vs 0.5000」證明的是**同一個 state 物件裡，擬合所需的更新數下降**（1,600 步 vs 6,400 步），
不是推理、不是泛化、不是智能。核心分不變（0.00/10）。

## 五十六、階段 G：同樣的複習預算、200 段不同的口供（2026-11-14，量測前寫定）

### 56.1 為什麼是這一問

§55.6 的分支在 T1+T2 通過時只允許一個下一步：**同樣預算下的留出泛化**（「800 段的子集＋200
留出」，不是分數）。§55 證明的是「32 段、同一個 state 物件、400 複習／段，store 到 1.0000 而 GRU
只到 0.3750」——那是**擬合**。若 store 只是讓模型更快記住 32 段，它對核心沒有意義；這一節問的是
**換成沒背過的答案組合，它還答不答得出來**。

### 56.2 唯一的變數

兩臂都從 L 出發、同一個 seed／lr／batch／aux loss／aux mode，唯一差別是核心：

| | GRU 臂 | store 臂 |
| --- | --- | --- |
| `--core` | `gru`（§49–§54 的載體） | `turnstore`（§55） |
| 參數 | 124,611 | 168,150 |
| 寫入 | 無 | 每輪結尾一次 |
| 讀取 | 無 | 只進輸出頭 |

**消融不進這一輪**：§56 問的是「store 在留出上是否比同預算的 GRU 好」，不是「store 的哪一部分
有用」；若 G3 不過，登記的下一步才是消融（§56.6）。

### 56.3 訓練集子集與留出（為什麼是 200 段）

* **訓練**：**前 200 段**（frozen 的 800 段 train 順序的前綴；`--train-sessions 200`，報告記
  `config.train_subset = 200`、`corpus.train_sessions_used = 200`）。**不是** `--overfit`
  （那是 32 段的校準臂、`overfit: true`、依 §50.4 不判讀泛化）。
* **留出**：原本的 200 段（答案元組與訓練不重疊，generator 的 gate 已驗），**在這一輪之前從未
  參與訓練**，也不是本輪挑的。
* **預算**：`--epochs 400`、batch 8 → 每 epoch 25 步 → **10,000 步 = 400 複習／段**，與 §55 的
  複習預算**逐字相同**（§54 的更正：固定步數 ≠ 固定複習；這一輪固定的是複習）。200 段不同口供
  × 400 複習 = 200 萬次 session 檢視。
* 成本：同一台機器、CPU、~0.64 s/步 → 每臂約 1.8 小時，兩臂約 3.6 小時（預先記錄，不是事後解釋）。

### 56.4 門檻（跑之前寫定）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| G1 | store 臂 train exact（200 段全部）**≥ 0.90** | 擬合先活下來，留出才可讀（用 §55 的 STORE_FLOOR，不新訂） |
| G2 | 留出 `full.exact` 的 **95% Wilson 下界 > chance（0.1591）** | 在沒背過的答案元組上高於「按該段名冊亂猜」 |
| G3 | 同一批 200 段留出上，store 贏／輸的**不一致對**做單尾精確符號檢定，**p < 0.05** 且 wins > losses | 泛化是 store 的功勞，不是兩臂共有的東西 |
| G4 | 成本（參數、秒數、device）已記錄 | — |

**chance 是算出來的，不是挑的**：每一段的裁決集合是 5–8 個名字（200 段留出：5 人 49 段、6 人 54、
7 人 50、8 人 47），所以依 session 平均的 chance 是 **0.1591**（不是 1/12 = 0.0833；§49 那個
0.0833 是另一種讀法）。用 Wilson 下界而不是點估計，是因為 n = 200 時 0.21 的點估計可以來自
0.16 的下界。換算成題數：**42/200（21.0%，下界 0.1593）剛好過，41/200（20.5%，下界 0.1548）不過**
——門檻很近，這是算術結果，不是我們挑的；判定一律用記在報告裡的 `wilson_lower`，不事後重數。

**G3 為什麼是不一致對**：兩臂看同一段文字、回答同一批 200 段；兩臂都答對或都答錯的段，對「誰
比較好」沒有資訊。只有「store 對、GRU 錯」與「store 錯、GRU 對」進入檢定（精確二項，不是常態
近似），所以基率偏移不能製造 G3。**這也讓 G3 對格式免疫**：同一個格式兩臂都看到。

### 56.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| store train exact | **0.55–0.95**（**偏不過 G1**） | §55 的 32 段是 1.0000，但 6.25 倍的**不同**口供要在同一個 400 複習／段裡拉進來；擬合與背誦的比例未知 |
| store 留出 exact | **0.10–0.20**（**預測 G2 不過**，門檻 0.21） | 200 段、124k–168k 參數、byte-level 解碼；§49 的 800 段臂在 20 複習／段只有 0.0850 |
| GRU train exact | 0.15–0.45 | 同預算、同資料，沒有短路徑 |
| GRU 留出 exact | 0.06–0.13 | 與 §49／§52 一致 |
| G3 | **不確定（偏不過）** | 若兩臂都在 chance 附近，不一致對會很少 |

### 56.6 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| G1 不過 | 400 複習／段背不起 200 段不同口供 | per-turn 的區域損失（§55.6 T1-fail 的同一條），**不得**加 epochs／加寬 |
| G1 過、G2 不過 | 擬合活下來，泛化沒有 | 記憶診斷：預測從哪來（逐鏈、與名冊的關係、是否常數），不是加 epochs |
| G1+G2 過、G3 不過 | 會泛化，但不是 store 的功勞 | store 消融（`memory=False`）在**同一個子集**上跑一次，看寫入對留出有沒有貢獻；不是分數 |
| 三條都過 | store 在同樣複習預算下泛化 | 同一協定跑剩下的訓練段（資料規模），登記，不是分數 |

判定由 `--stage-g` 從兩份報告重算（重新載入 checkpoint、重跑留出、檢查 weights hash），不讀
記在報告裡的 G3（單臂報告的 G3 一律 `None`，`verdict` 忽略 `None`，所以一份報告不能宣稱配對結果）。

### 56.7 這一節**不會**證明什麼，以及它自己的弱點

* 不是能力分數：核心分不變（0.00/10），系統分不變；200 段是 800 段的**子集**，不是全部訓練集。
* **沒有格式對照（Q7）**：G4 不含它，而在同一個子集上再訓一個 F-rand 臂要多 1.8 小時，換到的閘門
  不在 §56.4 裡。代價寫在這裡：**G2 單獨通過不足以排除格式**；G3 不受影響（兩臂同格式），所以
  只有 G1+G2+G3 全過才讀成「store 泛化」。若 G2 過而 G3 不過，讀法本來就是「不是 store 的功勞」。
* 單一 seed、單一任務、單一語料；留出與訓練**共用文字模板**（generator 的 deviation 2：答案元組
  與證據值不重疊，句子模板重疊），所以「高於 chance」代表**推理規則**而不是「見過這句話」——但
  它仍然只在這一個合成任務上成立。
* 200 段 × 400 複習是一個人為預算；它與 §55 相同，不是「訓練到收斂」。

### 56.8 指令

```
# store 臂（§55 的 turn store）
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 200 --epochs 400 --core turnstore \
    --aux-loss 1.0 --aux-mode resolvable \
    --gate-prefix G --device cpu --out data/pantry_stage/g_store
# GRU 對照（同樣的子集、步數、seed、λ）
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 200 --epochs 400 \
    --aux-loss 1.0 --aux-mode resolvable \
    --gate-prefix G --device cpu --out data/pantry_stage/g_gru
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
./.venv/bin/python scripts/train_pantry_deduction.py --stage-g <store>.json <gru>.json
```

### 56.9 這一節的地位

這是 §55.6 分支指名的下一問，也是「同一個 state 物件」第一次在**沒背過的答案組合**上被量。
它不改任何門檻、不改語料、不改寬度；G1 沿用 §55 的 0.90，G2 的 chance 由語料算，G3 的 α 是
0.05（跑之前寫定）。若 G1 或 G2 不過，這一輪的產物是**限制**（這條路在什麼預算下只會擬合），
不是「核心不能推理」的證據。

### 56.10 結果（2026-11-14，依 §56.8 的指令跑完，照實記）

| 臂 | train exact（200 段） | 不同預測 | 留出 exact（200 段） | Wilson 下界 | 排名 exact | 參數 | 步數 | 秒 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| store | **1.0000**（200/200） | 12 | **0.0850**（17/200） | 0.0537 | 0.1600 | 168,150 | 10,000 | 6,234 |
| GRU | 0.2100（42/200） | 11 | 0.0950（19/200） | 0.0617 | 0.1850 | 124,611 | 10,000 | 6,495 |

chance（依 session 的名冊大小平均）**0.1591**。

四條門檻：**G1 PASS**（store 1.0000 ≥ 0.90；GRU 0.2100 不過——同一個預算下 GRU 連 200 段都背不
起來）、**G2 FAIL**（0.0850 的 Wilson 下界 0.0537 遠低於 0.1591）、**G3 FAIL**（store 獨贏 17 段、
GRU 獨贏 19 段，p = 0.6911）、**G4 PASS**。`--stage-g` 的機械分支：

> 「G1 passes but G2 fails: fitting survives more sessions, generalisation does not; next is
> the memorisation diagnosis (where the prediction comes from), not more epochs」

**預測的偏差照實記**：store 的 fit 預測 0.55–0.95、實際 **1.0000**（在區間之上）；store 的留出
預測 0.10–0.20、實際 **0.0850**（在區間**之下**，而且是**低於 chance**）；GRU 的 fit 預測
0.15–0.45、實際 0.2100（區間內）；GRU 的留出預測 0.06–0.13、實際 0.0950（區間內）；G3 預測
「不確定、偏不過」、實際不過。也就是說：**擬合比預期好，泛化比預期差**。

**記憶診斷（§56.6 指名的那一步；只讀 checkpoint，不再訓練）**

用兩份 checkpoint 在 200 段留出上各重跑一次 `evaluate(..., "full")`，再對照每段自己的名冊
（`session["environment"]["actors"]`）與 `solver_candidates(..., "no_correction")`：

| 讀數 | store | GRU | 「完全不管這段話」的期望 |
| --- | --- | --- | --- |
| 正確 | 17/200（0.0850） | 19/200（0.0950） | 0.1591（名冊內均勻猜） |
| 預測落在**本段名冊內** | 122/200（0.6100） | 109/200（0.5450） | 0.5457（12 個名字 × 名冊 5–8 人） |
| 預測＝名冊第一個 | 15/200 | 15/200 | — |
| 預測＝名冊最後一個 | 19/200 | 15/200 | — |
| 預測＝撤回前的答案（98 段） | 13/98 | 6/98 | 0.1591 |
| 前三個名字佔比 | `David` 31、`Kevin` 25、`Elena` 25（40.5%） | `Alex` 64、`David` 39、`Kevin` 30（66.5%） | — |

三個讀數合起來的結論很窄，也很清楚：**它背下了 200 段，但沒有學到「答案在這份名冊裡、由證據值
選出來」**。① 訓練段 200/200、12 個名字全出現、最大單一名冊佔比只有 0.115 → 擬合時它真的逐段
選對，不是常數；② 換到沒背過的段，預測落在本段名冊內只有 0.6100（不管內容的期望是 0.5457，
只高 6.4 個百分點），正確率 0.0850 **低於**在名冊內均勻猜的 0.1591——它比亂猜還差，因為它把
機率押在 `David`／`Kevin`／`Elena` 這三個全域常見名上，而這三個名字不一定在該段的名冊裡；
③ 排名（把輸出限縮到本段名冊）0.1600 vs chance 0.1591 → **即使給它名冊，它也選不出來**。

這與 §50.13 對 GRU 的線性探針一致（每個邊界的 `h` 都讀不出答案）；差別是這一輪的 store 在
**它背過的段**上完全正確——所以 store 改變的是「能不能把一段背起來」，不是「會不會用名冊」。

**其他照實記的讀數**：`reset` 0.0700、`skip_al` 0.0850、`no_bounds` 0.0769、`no_correction`
0.0918——全都在 chance 附近，和 stage P 一樣，這些消融在這個階段沒有資訊（因為主臂本來就
是 chance）。`flip` 的 `both_right` 0.0、`changed_rate` 0.5612：拿掉撤回那一輪，答案有一半會
變——**文字有被讀進去**，只是讀進去的東西不足以選人。

**限制**：200 段是 800 段的子集；沒有格式對照（§56.7）；單一 seed；CPU；`--epochs 400` 是
人為預算（400 複習／段）。「G1 過、G2 不過」的讀法只有一個：**在這個預算與這個任務上，
store 讓擬合變便宜，但沒有讓規則變得可學**；它不證明「store 對泛化沒用」（200×400 這個配置
本身就在鼓勵背誦），也不證明「核心不能推理」。

## 五十七、階段 H：同一個算力，換成「更多不同的口供、更少複習」（2026-11-14，量測前寫定）

### 57.1 為什麼是這一問

§56.10 的診斷把失敗定位成「背下了 200 段、沒學到規則」。最直接、且**不增加算力**的另一種配置
是：把同一個 10,000 步的預算從「200 段 × 400 複習」換成「400 段 × 200 複習」。這正好檢驗
「複習太多、口供太少」這個解釋——若泛化仍不出現，就不能再拿「資料不夠多」當理由（在這個算力下）；
若泛化出現了，下一個登記才是「同樣的 rung 加 GRU 對照」。

### 57.2 唯一的變數

| | §56 的 rung（已跑） | §57 的 rung |
| --- | --- | --- |
| 訓練段數 | 200 | **400** |
| epochs | 400 | **200** |
| 步數（batch 8） | 25 × 400 = 10,000 | 50 × 200 = **10,000** |
| 複習／段 | 400 | **200** |
| 其他 | store、L 起點、seed 20261118、lr 5e-4、batch 8、λ=1、`--aux-mode resolvable`、`--device cpu` | **完全相同** |

**算力沒有增加**：步數、batch、模型、語料都一樣，只有「同樣的步數花在多少段不同的口供上」變了。
這不是「加 epochs」（每段的複習反而減半），也不是「加寬」。

### 57.3 門檻（跑之前寫定）

沿用 §56 的同一個評分函式（`--gate-prefix G`；報告記 G1／G2／G4），不新訂數字：

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| H1 ＝ G1 | store 臂 train exact（400 段全部）**≥ 0.90** | 200 複習／段還背得起 400 段，留出才可讀 |
| H2 ＝ G2 | 留出 `full.exact` 的 **95% Wilson 下界 > 0.1591** | 在沒背過的答案元組上高於名冊內均勻猜 |
| H3 ＝ G4 | 成本已記錄 | — |

### 57.4 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| H1（fit 400 段、200 複習／段） | **0.55–0.90**（偏不過） | §56 的 200 段在 400 複習／段是 1.0000，且到第 200 個 epoch 損失已 0.0114；複習減半、段數加倍，兩邊同時變緊 |
| H2（留出過 chance） | **0.08–0.16**（預測不過） | §56 是 0.0850；診斷說失敗不是「段數不夠」而是「沒學到用名冊」 |
| H3 | 已記錄 | — |

### 57.5 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| H1 不過 | 在同樣算力下，200 複習／段背不起 400 段 | 擬合優勢是「複習」的函數，不是「資料」的函數；下一個變數是**目標**（per-turn 區域損失：每一輪都要從當時的前綴解一次），**不得**加步數或加寬 |
| H1 過、H2 不過 | 更多不同的口供、同樣算力，仍然不泛化 | 失敗不在資料量（在這個尺度），在表徵／目標；下一輪登記「讀取端的選擇」（把輸出限縮到名冊的選擇頭，或每輪的區域損失），不是更多段 |
| H1 過、H2 過 | 泛化出現，且來自「更多不同的口供」 | 下一個登記是**同一個 rung 加 GRU 對照**（成對，同 §56 的 G3），確認是不是 store 的功勞 |

### 57.6 這一節**不會**證明什麼

不是能力分數（核心分不變）；單一 seed、單一任務、沒有格式對照；400 段仍是 800 段的子集；
「200 複習／段」是相對於 §56 的配置，不是收斂點。若 H1 不過，這一輪的產物是**擬合預算的比例**
（400 段需要多少複習），不是「核心不能泛化」。

### 57.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore \
    --aux-loss 1.0 --aux-mode resolvable \
    --gate-prefix G --device cpu --out data/pantry_stage/h_store
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

### 57.8 這一節的地位

§56.6 只允許「記憶診斷」作為下一步；診斷（§56.10）已經做完，且它指名的是「擬合變便宜、規則沒
學到」。這一節是對那個診斷的**第一個可否證的檢驗**：同樣算力下改變曝露多樣性。它不改任何門檻、
不改語料、不加算力。

### 57.9 結果（2026-11-14，依 §57.7 的指令跑完，照實記）

| 讀數 | 值 |
| --- | --- |
| train exact（**宣告的 400 段全部**） | **0.9125**（365/400） |
| train exact（報告的 `train_fit`，§49.6 的上限 200 段） | 0.9000（180/200） |
| 留出 exact（200 段） | **0.0950**（19/200） |
| 留出 Wilson 下界／上界 | **0.0617** ／ 0.1436 |
| chance（名冊 5–8 人） | **0.1591** |
| 留出 ranking（限縮到名冊） | 0.1650（下界 0.1200） |
| 參數／步數／複習／秒 | 168,150 ／ 10,000 ／ 200 ／ 6,648 |

三條門檻：**H1 PASS**（0.9125 ≥ 0.90）、**H2 FAIL**（下界 0.0617 遠低於 0.1591）、
**H3 PASS**。`--gate-prefix G` 的機械分支：

> 「G1 passes but G2 fails: fitting survives more sessions, generalisation does not; next is
> the memorisation diagnosis (where the prediction comes from), not more epochs」

依 §57.5 的對應列：**「H1 過、H2 不過：更多不同的口供、同樣算力，仍然不泛化 → 失敗不在資料量
（在這個尺度），在表徵／目標」**。

**量測缺陷（跑完才發現，照實修）**：報告的 `train_fit` 只算 `train_sessions[:200]`（§49.6 為了
stage-P 的成本把擬合讀數上限設在 200 段）。§57.3 寫的是「400 段全部」，所以 H1 是**另外**從同一份
checkpoint、用同一條 `evaluate` 路徑量的（不再訓練）：365/400 = **0.9125**；報告裡那個 0.9000 是
前 200 段的讀數。這不是調門檻（0.90 沒動），是原本的讀數只覆蓋了宣告子集的一半。已改：
`--train-sessions N`（N > 200）現在會多記一個 `results.train_fit_subset`（整個宣告子集），
`G1`／`H1` 優先讀它；§56 的兩份報告沒有這個欄位，重算後判定**完全不變**（store PASS／GRU FAIL，
已用新舊兩條路徑對照確認），測試 +1（64 條）。

**預測的偏差照實記**：H1 預測 0.55–0.90（「偏不過」），實際 **0.9125**（在區間之上，但報告上限那
一欄剛好是 0.9000）；H2 預測 0.08–0.16、預測不過，實際 **0.0950**（區間內）——這一條是對的。
另外，訓練損失到最後一個 epoch 還在降（第 150→200 個 epoch：0.3337 → 0.1052），所以 0.9125 **不是
這個預算的擬合上限**，只是「200 複習／段走到這裡」。

**記憶診斷（同一份 checkpoint，不訓練）**：把 200 段留出逐段跑完，對照本段名冊與撤回前的答案：

| 讀數 | §57（400 段 × 200 複習） | §56（200 段 × 400 複習） | 「完全不管這段話」的期望 |
| --- | --- | --- | --- |
| 正確 | 19/200（0.0950） | 17/200（0.0850） | 0.1591 |
| 預測落在**本段名冊內** | 107/200（0.5350） | 122/200（0.6100） | 0.5457 |
| 預測＝名冊第一個 | 21/200 | 15/200 | — |
| 預測＝名冊最後一個 | 15/200 | 19/200 | — |
| 預測＝撤回前的答案（98 段） | 6/98 | 13/98 | 0.1591 |
| 前三個名字佔比 | `Alex` 33、`Elena` 29、`David` 26（44%） | `David` 31、`Kevin` 25、`Elena` 25（40.5%） | — |

把複習減半、口供加倍之後，**形狀完全沒變**：擬合還在（0.9125），預測落在本段名冊內 **0.5350**，
比「完全不管內容」的 0.5457 還**低**，ranking 0.1650 ≈ chance 0.1591。所以「複習太多、口供太少」
這個解釋被否證了——至少在這 10,000 步的尺度上，換曝露多樣性不改變失敗的形狀。

**其他照實記的讀數**：`reset` 0.0850（≈ `full` 0.0950）、`skip_al` 0.1000、`no_bounds` 0.0769、
`no_correction` 0.0612——和 §56 一樣，這些消融在 chance 附近沒有資訊，因為主臂本來就是 chance。
逐鏈：ledger 5/54、apron 4/52、badge 7/46、window 3/48。

**限制**：400 段仍是 800 段的子集；單一 seed；CPU；沒有格式對照（§56.7）；`0.9125` 是「跑完 200
個 epoch」的讀數，不是收斂值（損失還在降）。「H1 過、H2 不過」只證明一件事：**在這個算力下，把
預算從複習移到資料多樣性，沒有讓規則變得可學**；它不證明「加資料永遠沒用」，也不證明「核心不能
推理」。

## 五十八、階段 K：答案在 state 裡嗎（2026-11-14，量測前寫定）

### 58.1 為什麼是這一問

§56.10 與 §57.9 的診斷是同一個形狀：**擬合得到（200/200、365/400），但留出上「預測落在本段名冊
內」只有 0.61／0.535（不管內容的期望 0.5457），ranking ≈ chance**。這留下兩個互斥的解釋，而它們
指向完全不同的下一步：

1. **表徵有、讀出沒有**：名冊與「證據值→人」的綁定已在 state（`h` 或 store 的 `r`）裡，失敗在
   解碼／評分端；
2. **表徵根本沒有**：state 從來沒有把「這份名冊＋這個證據值」綁起來，所以再怎麼換讀出都一樣。

§50.13 對 GRU 的線性探針已經問過一次（每個邊界的 `h` 都只有 chance），但那一輪的模型在訓練段上
也背不起來；這一輪的 store 在訓練段上是 **0.9125**，所以「背得起來但用不出來」第一次可以被單獨
量。這一節不訓練新模型，只讀 checkpoint。

### 58.2 儀器

新增 `scripts/probe_pantry_state.py`：

* 從一份報告重建同一個核心、載入 checkpoint、**核對 `weights_hash`**（報告與權重不能混）。
* 逐段跑完 11 輪（與 `evaluate` 同一條 `run_session` 路徑），取**問句之後**的 state：
  `h`（128 維）、`r = read_vector(state)`（64 維，store 的讀取）、以及兩者串接（192 維）。
  這正是解碼器回答時看到的那個 state，不是別的邊界。
* 在**前 400 段訓練段**上配适一個多項式邏輯迴歸（12 個名字；`StandardScaler` 只在訓練段上 fit，
  `C=1.0`、`lbfgs`、`max_iter=2000`、`random_state` 固定），在**200 段留出**上評分。
* 三個特徵組各跑一次（`h`／`r`／`h+r`），並印出訓練段 in-sample、留出 exact、Wilson 下界、
  chance 與混淆矩陣的前幾列。

**這不是模型在回答**：探針是一個額外配适的線性分類器，它測的是「state 裡有沒有**線性可解碼**的
答案」，不是「解碼器會不會用」。

### 58.3 門檻（跑之前寫定）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| K1 | 訓練段 in-sample exact **≥ 0.90** | 儀器檢查：探針連訓練段都配不起來，後面的數字不讀 |
| K2 | 留出 exact 的 **95% Wilson 下界 > 0.1591**（chance，與 §56 的 G2 同一條線） | state 裡有線性可解碼的答案 |
| K3 | `h`／`r` 兩組分開的讀數已記錄（診斷，不是門檻） | 是哪一半帶著資訊 |
| K4 | 成本（秒、特徵維度、樣本數）已記錄 | — |

### 58.4 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| K1 | **過**（≈1.0） | 192 維、400 段、12 類，線性分類器在 in-sample 上幾乎一定配得起來 |
| K2（`h+r`） | **不過**（0.08–0.18） | §56／§57 的 ranking 都在 chance；若 state 線性帶著答案，ranking 不該是 chance |
| K2（`r` 單獨） | **不過**（0.08–0.18） | store 寫的是「每輪的摘要」，不是「名冊的鍵值」；§46 的 A2 也量到讀取只進頭 |
| K2（`h` 單獨） | **不過**（0.08–0.18） | §50.13 對 GRU 的 `h` 已經是 chance |

### 58.5 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| K1 不過 | 探針壞了（配不起訓練段） | 先修探針，**不得**用這一輪的 K2 下任何結論 |
| K1 過、K2 不過（含三組都不過） | 答案是**非線性可解碼或不存在**；綁定沒有被學進 state | 表徵端：一個顯式的綁定運算（把名冊每人寫成一槽、以**證據值**為鍵，回答時以證據值讀取），登記後再跑；**不得**加段數／步數／寬度 |
| K1 過、K2 過（至少一組） | 答案在 state 裡，失敗在讀出 | 讀出端：以 state 為輸入的名冊選擇頭（在名冊上歸一化），登記後再跑；**不得**加段數／步數／寬度 |

**為什麼「K2 不過」不是「核心不能推理」**：線性探針不過只否定「線性可解碼」，非線性可解碼仍可能
存在；但它是**最便宜**的讀法，而且與 ranking（也是線性評分）一致。若它不過，下一步就必須動表徵，
不是再換讀出。

### 58.6 這一節**不會**證明什麼

不是能力分數（核心分不變 0.00/10）；不是「模型會不會用 state」（探針不是解碼器）；單一 seed、單一
任務、單一 checkpoint；線性探針的非線性版本沒有量。K2 過也**不代表**解碼器一定學得會用——那只證明
資訊在那裡，下一個登記仍然是訓練一個讀出端並用同一條留出線量。

### 58.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_state.py \
    --report data/pantry_stage/h_store/pantry_deduction_20261114-140311.json \
    --train-sessions 400
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_state.py \
    --report data/pantry_stage/g_store/pantry_deduction_20261114-102725.json \
    --train-sessions 200
```

### 58.8 這一節的地位

§57.5 只允許「表徵／目標」這條線作為下一步。這一節先把「表徵 vs 讀出」分開，而且用的是已經存在
的 checkpoint，不再燒 1.8 小時。它不改門檻、不改語料、不改模型；K2 的線與 §56 的 G2 同一條
（0.1591），K1 只檢查儀器。

## 五十九、階段 B：把名冊寫成可定址的槽（token 級 key-value cache；2026-11-14，量測前寫定）

### 59.1 為什麼是這一問

§58 的 K2 判決（K1 過 0.9725、K2 不過）把問題指到**表徵**：最終 state 在訓練段上線性帶著答案
（探針 in-sample 0.9725），在留出上只到 0.11（chance 0.1591）。所以不是解碼器不會讀，是 state 裡
**沒有可泛化的綁定**。

再看任務要求的那個運算：名冊那一輪同時列出 8 組「證據值 → 人名」（例如「藍色 David、紅色 Elena…」），
證據輪只給一個值、不給人名，答案是「名冊[值]」。這是一個**鍵值綁定**，而 §55 的 store **每輪只寫
一格**（`end_turn` 把整輪平均成一個向量）——8 組配對在寫入時就被壓成一個向量，讀取端再怎麼讀也
分不開。§56／§57 的「預測落在本段名冊內只有 0.61／0.535」正是這個形狀。

所以這一節的單一變數是**寫入的粒度**：從「每輪一格」改成「每個 token 一格」（key/value 都由該
token 的遞歸狀態投影而來），讀取仍是內容定址，且**只進輸出頭**（§55.2 的同一條規則）。這不是把
語料裡的名冊用規則解析出來（那會是表層），是把「哪個名字跟哪個值相鄰」交給模型自己的狀態去記。

### 59.2 唯一的變數：`TokenCacheCore`

新增一個 `StatefulCore` 子類（`ai/core/stateful_decoder.py`），遞歸、`dt_proj`、`al_step`、
`chunk_seconds`、`emb`、`hidden` 與 `GRUCore`／`TurnStoreCore` **完全相同**，差別只在 state 與寫入：

| | GRUCore | TurnStoreCore（§55） | TokenCacheCore（§59） |
| --- | --- | --- | --- |
| state | `h [B,128]` | `h`、`k [B,16,64]`、`v [B,16,64]` | `h`、`ck [B,S,64]`、`cv [B,S,64]`、`mask [B,S]` |
| 寫入時機 | 無 | 每輪結尾一次 | **每個 token 一次** |
| 寫入 | 無 | `slot ← slot(1−ag) + ag·W_v h` | `ck_t = W_k h_t`、`cv_t = W_v h_t`（位置=t） |
| 讀取 | 無 | `softmax(scale·W_q h·kᵀ)·v` | `softmax(scale·W_q h·ckᵀ，mask 外的槽為 −inf)·cv` |
| 輸出 | `head(h)` | `head([h, r])` | `head([h, r])` |
| 讀取去向 | — | 只進輸出頭 | 只進輸出頭 |
| `memory=False` | — | `r ≡ 0`、不寫入（參數全留） | `r ≡ 0`、不寫入（參數全留） |

* **槽數 `S = 1024`，只保留**會議最前面的 1024 個 token（不是環狀覆寫）。理由：名冊在第 2–3 輪、
  證據輪在 4–9 輪，都在前段；保留前段讓「值與名字相鄰」的那些 token 一定還在，避免後面的填充把
  名冊擠掉。超出 `S` 的 token 不進 cache（記錄在報告裡）。
* **寫入是函數式堆疊，不是原地改寫**：一個 turn 的 key/value 由該 turn 的 `stacked` 狀態一次投影、
  再 `cat` 進 `ck`／`cv`（避免 in-place 破壞 autograd）。
* **padding 不進 cache**：`mask` 由每個樣本的真實長度決定（`position < length`），右側 padding 的
  key 被遮掉、value 不參與讀取。這與 §49 的「pad 從不進 state」是同一條要求。
* 讀取只在 `token_logits` 裡發生（主損失與 §50 的輔助讀出都用同一個入口），生成時不寫入。

### 59.3 起點與不變的東西

從 L 的 checkpoint 出發（`L_WEIGHTS_HASH` 逐位核對，§49.1），seed 20261118、lr 5e-4、batch 8、
λ=1.0、`--aux-mode resolvable`、`--device cpu`、`--train-sessions 400 --epochs 200`
（50 batches × 200 = **10,000 步 = 200 複習／段**，與 §57 完全相同）。語料、切分、chance 都不動。

### 59.4 門檻（跑之前寫定，沿用既有數字，不新訂）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| B1 | 宣告子集（400 段全部）train exact **≥ 0.90** | 擬合先活下來，留出才可讀（§55 的 `STORE_FLOOR`） |
| B2 | 留出 exact 的 **95% Wilson 下界 > 0.1591** | 在沒背過的答案元組上高於名冊內均勻猜（§56 的 G2 線） |
| B3 | 留出「預測落在本段名冊內」的比率**已記錄** | 機制診斷（§56.10 的 0.6100、§57.9 的 0.5350 是這一欄） |
| B4 | 成本（參數、秒、cache 槽數、被截斷的 token 數）已記錄 | — |

### 59.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| B1 | **0.85–0.95**（偏過） | §57 的 per-turn store 在同一預算下是 0.9125；token cache 多一層讀取，擬合更便宜，但參數與計算也更多 |
| B2 | **0.20–0.45**（**偏過**） | 這是第一次讓「值→名字」的配對以原樣留在 state 裡；若 §58 的診斷正確（資訊不在 state），這一改應該把留出從 0.095 拉起來 |
| B3 | **0.85–1.00** | 有了 token 級 cache，輸出至少應該是本段名冊裡的一個人（不是全域常見名） |
| 排名 | 0.30–0.60 | 若 B2 過，限縮到名冊的排名應同步上升 |

**這是本節唯一一次「偏過」的預測**：§55／§56／§57 我預測得偏保守（實際都比預測好或持平），這一節
相反——如果 token cache 不能把留出拉過 chance，那麼「綁定粒度」這個解釋就被否證，剩下的是資料量
或目標函數。

### 59.6 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| B1 不過 | token cache 破壞了擬合（讀取端把梯度帶歪） | 回到 §55 的 per-turn store；下一步是目標函數（per-turn 區域損失的**加權**版本），不是再加架構 |
| B1 過、B2 不過 | 綁定粒度不是原因；「以相似度定址」不足以學會「值→人」 | 顯式監督名冊映射：在名冊輪的邊界加一個輔助損失（值→名字的 96 維分類），登記後再跑；**不得**加段數／步數／寬度 |
| B1+B2 過 | 綁定粒度是原因，且泛化出現 | 登記同一個 rung 的**配對對照**（§57 的 per-turn store 臂作為控制，`--stage-g` 的 G3 流程），確認是 cache 的功勞；不是分數 |

### 59.7 這一節**不會**證明什麼，以及它自己的弱點

* 不是能力分數：核心分不變（0.00/10）；400 段仍是 800 段的子集；單一 seed；CPU；單一任務。
* **cache 是「只保留前 1024 個 token」**：更長的 session 尾段不進 cache（報告記錄被截斷的比率）。
  這是為了「名冊不被擠掉」的設計選擇，不是量測。
* **它仍然只是「把相鄰的值與名字放進可定址的位置」**：時間窗、撤回、多輪證據的過濾仍由遞歸
  state 負責；這一節只改寫入粒度，不改推理規則。
* 若 B2 過，也不能直接說「核心會推理」——它只說在這個任務上，答案元組的留出高於 chance；格式
  對照（Q7）沒有跑（§56.7 的同一條限制）。

### 59.8 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core tokencache \
    --aux-loss 1.0 --aux-mode resolvable \
    --gate-prefix G --device cpu --out data/pantry_stage/b_cache
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_state.py \
    --report <report>.json --train-sessions 400
```

### 59.9 這一節的地位

§58.5 的分支只允許「表徵端」作為下一步，且明文列出「把名冊每人寫成一槽、以證據值為鍵」。這一節
就是那個運算，但**鍵值由模型自己的狀態投影**（不是用規則解析語料），寫入粒度是唯一變數；門檻全部
沿用 §55／§56 已經登記過的線，沒有新數字。

### 59.10 結果（2026-11-14，依 §59.8 的指令跑完，照實記）

| 讀數 | 值 |
| --- | --- |
| train exact（**宣告的 400 段全部**） | **0.5000**（200/400） |
| train exact（報告的 `train_fit`，前 200 段） | 0.4950（99/200） |
| 留出 exact（200 段） | **0.0750**（15/200） |
| 留出 Wilson 下界／上界 | **0.0460** ／ 0.1200 |
| chance | **0.1591** |
| 留出 ranking（限縮到名冊） | 0.1450（下界 0.1029） |
| 留出「預測落在本段名冊內」 | 106/200 = **0.5300**（不管內容的期望 0.5457） |
| 參數／步數／複習／秒 | 165,956 ／ 10,000 ／ 200 ／ 7,363.7 |
| cache 槽數／被丟掉的 token | 1024 ／ 49,250 of 254,050 = **19.39%**（留出）；19.35%（訓練子集） |

四條門檻：**B1 FAIL**（0.5000 < 0.90）、**B2 FAIL**（下界 0.0460 < 0.1591）、
**B3 已記錄**（0.5300）、**B4 PASS**（參數、秒、槽數、截斷量都已記）。`--gate-prefix G`
的機械分支：

> 「G1 fails: ... the fit is capped by underfitting and is not read」

依 §59.6 的對應列：**「B1 不過：token cache 破壞了擬合（讀取端把梯度帶歪）→ 回到 §55 的
per-turn store；下一步是目標函數（per-turn 區域損失的加權版本），不是再加架構」**。

**四個預測全部落空，而且都在同一個方向（比預測差）**：

| 讀數 | 預測（§59.5，跑之前寫的） | 實際 | 方向 |
| --- | --- | --- | --- |
| B1 | 0.85–0.95（偏過） | **0.5000** | 低於區間 |
| B2 | 0.20–0.45（**刻意偏過**） | **0.0750** | 低於區間 |
| B3 | 0.85–1.00 | **0.5300** | 低於區間 |
| ranking | 0.30–0.60 | **0.1450** | 低於區間 |

這是 §55 以來第一次**每一個**預測都錯、且方向一致。§59.5 的預測是刻意樂觀的（它說「若 token
cache 不能把留出拉過 chance，綁定粒度這個解釋就被否證」），所以這個結果**否證了「寫入粒度」**：
把名冊每人寫成一格、以內容定址讀取，不但沒有讓留出變好，**連擬合都掉了**（0.9125 → 0.5000）。

**擬合掉在哪裡，照實記**：訓練損失到第 200 個 epoch 還在降（第 150 個 epoch 0.5698 → 第 200 個
0.4590，main 0.2854、aux 0.1737），而 §57 同一預算結束在 0.1052。所以 0.5000 **不是收斂值**，
是「1024 槽的 softmax 讀取讓每個邊界的梯度被攤平」——讀取端在訓練中沒有把 `h` 的資訊集中到
正確的槽上。這與分支寫的「讀取端把梯度帶歪」一致，但**不能**被讀成「更多 epoch 就會好」：§59.6
明文禁止把加步數當下一步。

**逐邊界讀數（`diagnostics.readout`，同一份 checkpoint，不訓練）**：第 6 輪 n=98 exact 0.102、
第 7 輪 13/200 = 0.065、第 8 輪 15/200 = 0.075、第 9 輪 21/200 = 0.105、第 10 輪 15/200 = 0.075。
**每一個邊界都在 chance 附近**，所以不是「答案只在最後一輪才出現」，是整條路徑都沒有綁定。

**其他照實記的讀數**：`reset` 0.0600、`no_correction` 0.0510、`no_bounds` 0.0769、`skip_al` 0.0750
——和 §56／§57 一樣，消融在 chance 附近沒有資訊；`flip` 98 段的 `changed` 是 0.0（撤回不改變答案，
再次顯示沒有用到證詞）。逐鏈：ledger 2/54、apron 4/52、badge 5/46、window 4/48。預測分佈：
11 個不同名字，`Alex` 51、`David` 33、`Kevin` 32（前三名 58%）。

**截斷的量測（§59.4 B4 要求，也是註冊時我主張「名冊不會被擠掉」的檢驗）**：一個 session 平均
1,270 個 token（最大 1,421），**每一段都被截斷**、丟掉約 19% 的 token。逐輪位移：第 1–7 輪在
**200/200** 段都結束於 1024 之前、第 8 輪 189/200、第 9 輪 75/200、第 10–11 輪 0/200。所以名冊
（第 2–3 輪）**一定在 cache 裡**，被丟掉的是後段證詞；那個主張成立，但它成立的方式與我寫的不完全
一樣（我寫「後面填充擠不掉名冊」，實際是「名冊在很前面，但後段證詞會被丟掉」）。

**限制**：400 段仍是 800 段的子集；單一 seed；CPU；單一任務；`0.5000` 是「跑完 200 個 epoch」的
讀數而非收斂值；沒有格式對照（§56.7 的同一條限制）；B2 的失敗只說「這個寫入粒度加這個讀取端
在這個預算下不泛化」，不證明「核心不能推理」，也不證明「token 級定址在別的讀取端下一定無效」。

## 六十、階段 W：每個邊界只問「這份名冊裡是誰」（加權區域損失；2026-11-14，量測前寫定）

### 60.1 為什麼是這一問

§59.6 對「B1 不過」的判決是：**回到 §55 的 per-turn store，下一步是目標函數（per-turn 區域損失
的加權版本），不是再加架構**。§59 的結果（擬合 0.5000、留出 0.0750、每個邊界都 ≈ chance）讓這條
判決更明確：問題不在「資料放在哪一格」，而在**損失函數從來沒有要求模型在名冊裡做選擇**。

現行的輔助目標（§51.2 `--aux-mode resolvable`）在每個邊界問的是同一個答案字串，CE 攤在**全部
259 個 byte token** 上。於是模型有一條很便宜的退路：把「這一段口供 → 某個名字」直接背起來，全域
常見名（`Alex` 51 次、`David` 33、`Kevin` 32）就足以吃下大半的機率質量——§56.10、§57.9、§59.10
三次量到的「預測落在名冊內只有 0.61／0.535／0.530，低於不管內容的 0.5457」正是這條退路。

這一節把那個退路關掉：每個邊界的損失**只在該邊界仍然一致的名字（也就是名冊）上做 softmax**，
並且**依名冊的寬度加權**（越窄的邊界訊號越確定）。這是指標的改變，不是架構的改變：載體回到 §57
的 `TurnStoreCore`，語料、切分、步數、seed、lr 全部不動。

### 60.2 唯一的變數：`--aux-mode weighted-region`

對每個樣本 `s`、每個早段邊界 `k`（`k = 0 … 9`，最後一輪仍是主損失）：

* `C = prefix_candidates(module, session, k)`——該邊界仍與證詞一致的名字。**這是輸入裡就有的名冊**，
  不是答案：正解仍由證詞決定，`C` 只界定「可以回答的區域」。（`resolvable` 用同一個函數，只是
  只取 `len(C) == 1` 的那些邊界。）
* `|C| < 2` → 不計（只有一個候選時 CE 的梯度是 0，算了也沒有資訊）。
* 對每個 `name ∈ C`，從該邊界的 view 做 teacher-forced 解碼，取 `log p(name + "\n")`；在 `C` 上
  做 softmax，CE 對正解（正解一定在 `C` 裡，語料的 `derive()` 保證）。
* 權重 `w = 1 / |C|`：名冊越窄，該邊界的答案越確定，權重越大。
* `aux = Σ_{(s,k)} w·CE / Σ w`，`λ = 1` 與主損失相加（與 §57 同一個 λ）。

實作上把 `(樣本, 候選)` 攤平成一個 batch（8 個樣本 × 5–8 個名字），名字最長 6 個 byte，所以每個
邊界多花 6 步、batch ≈ 48 的計算；估計成本 +10–20%，遠小於重跑一次架構的代價。

**不變的東西**：`--core turnstore`（§55 的 per-turn store）、400 段 × 200 複習 = 10,000 步、
seed 20261118、lr 5e-4、batch 8、`--device cpu`、從 L 的 checkpoint 出發（逐位核對）。

### 60.3 門檻（跑之前寫定，沿用 §59 的 B1–B4，不新訂數字）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| W1 | 宣告子集（400 段全部）train exact **≥ 0.90** | 擬合先活下來（§55 的 `STORE_FLOOR`，同 §59 的 B1） |
| W2 | 留出 exact 的 **95% Wilson 下界 > 0.1591** | 高於名冊內均勻猜（同 §56 G2／§59 B2） |
| W3 | 留出「預測落在本段名冊內」的比率**已記錄** | 這個目標的機制診斷：它應該接近 1.0，否則「關掉退路」沒有發生 |
| W4 | 成本（參數、秒、每個邊界的候選評分次數、被跳過的邊界數）已記錄 | — |

### 60.4 預測（寫在跑之前，這次不刻意樂觀）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| W1 | **0.85–0.95（偏過）** | 限制在 5–8 個候選上比 259 個 byte 容易擬合；但候選解碼的梯度要穿過 `consume`，可能不穩 |
| W2 | **不過，0.10–0.25** | 這個目標強迫輸出落在名冊裡，但**沒有**強迫「用證據值去選」——模型仍可用「這一段口供的身分」直接對映到答案。§58 的探針（訓練段 in-sample 0.9725、留出 0.11）指向的是表徵，不是決策邊界 |
| W3 | **0.90–1.00** | 損失只在名冊上做 softmax，訓練後自由解碼應該幾乎不再吐全域常見名 |
| ranking | 0.25–0.55 | 若 W3 接近 1.0，ranking 會跟著上升；上限受 W2 限制 |

W2 預測不過是刻意的：如果這個目標就能讓留出過線，那 §58 的「表徵沒有綁定」診斷就是錯的。把這個
衝突寫在跑之前，結果出來才有資訊。

### 60.5 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| W1 不過 | 候選解碼的梯度不穩、把擬合帶歪 | 回 `--aux-mode resolvable`；下一步是**反事實語料**（同一份名冊、換掉證據值，答案跟著換），登記後再跑；**不得**加段數／步數／寬度 |
| W1 過、W2 不過 | 目標仍允許「背身分、不用值」 | **反事實語料臂**：每一段口供生成一個配對版本（同一名冊、不同證據值 → 不同兇手），讓「session 身分」不再是答案的充分統計量。這是唯一能直接把「背誦」與「綁定」分開的介入，登記後再跑；**不得**加段數／步數／寬度 |
| W1+W2 過 | 「在名冊裡做選擇」是缺的那一步 | 登記同一個 rung 的配對對照（`resolvable`，`--stage-g` 的 G3 流程）確認是目標的功勞；仍不是能力分數 |

### 60.6 這一節**不會**證明什麼

* 不是能力分數（核心分不變 0.00/10）；400 段仍是子集；單一 seed；CPU；單一任務。
* **候選集合來自語料生成器的 `derive()`**：訓練時用它界定區域是合法的監督（它等於「你只能從名冊
  裡挑」），但**推論時不能用它**——解碼仍是自由詞表。若 W3 沒有接近 1.0，就代表訓練時的限制沒有
  轉移到自由解碼，這一點會在結果裡照實寫，不會用「推論時也套候選」的方式補救（那是用解答回答）。
* W2 過也只說「在這個任務、這個預算下留出高於 chance」；格式對照（Q7）仍然沒有跑。

### 60.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore \
    --aux-loss 1.0 --aux-mode weighted-region \
    --gate-prefix G --device cpu --out data/pantry_stage/w_region
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

### 60.8 這一節的地位

§59.6 對 B1 失敗只允許「目標函數（per-turn 區域損失的加權版本）」這一條線。這一節就是那個損失：
不新架構、不加步數、不改語料，只把「可以回答的區域」從 259 個 byte 縮到這份名冊，並依確定性加權。
W2 的預測是**不過**——如果它過了，§58 的表徵診斷就要重寫；如果它不過，下一步（反事實語料）已經
寫在上面的分支裡，不是事後才想。

### 60.9 結果（2026-11-14，依 §60.7 的指令跑完，照實記）

| 讀數 | 值 |
| --- | --- |
| train exact（**宣告的 400 段全部**） | **0.9000**（360/400，剛好壓在 0.90 地板） |
| train exact（報告的 `train_fit`，前 200 段） | 0.8850（177/200） |
| 留出 exact（200 段） | **0.1050**（21/200） |
| 留出 Wilson 下界／上界 | **0.0697** ／ 0.1552 |
| chance | **0.1591** |
| 留出 ranking（限縮到名冊） | 0.1700（下界 0.1243） |
| 留出「預測落在本段名冊內」 | 114/200 = **0.5700**（不管內容的期望 0.5396） |
| 訓練「預測落在本段名冊內」 | 376/400 = **0.9400**（前 200 段 186/200 = 0.9300） |
| 參數／步數／複習／秒 | 168,150 ／ 10,000 ／ 200 ／ **12,471.8** |
| `training.aux_region` | 2,607 個邊界計分／1,393 跳過／每 epoch 15,852 個候選對／平均寬度 6.08（最大 8） |

四條門檻：**W1 PASS**（0.9000 ≥ 0.90）、**W2 FAIL**（下界 0.0697 < 0.1591）、
**W3 已記錄**（0.5700）、**W4 已記錄**（參數、秒、`aux_region` 都在報告裡）。`--gate-prefix G`
的機械分支：

> 「G1 passes but G2 fails: fitting survives more sessions, generalisation does not; next is the
> memorisation diagnosis (where the prediction comes from), not more epochs」

依 §60.5 的對應列：

> **「W1 過、W2 不過｜目標仍允許「背身分、不用值」｜反事實語料臂：每一段口供生成一個配對版本
> （同一名冊、不同證據值 → 不同兇手），讓「session 身分」不再是答案的充分統計量。這是唯一能
> 直接把「背誦」與「綁定」分開的介入，登記後再跑；不得加段數／步數／寬度」**

**預測對照（§60.4 寫在跑之前）**：

| 讀數 | 預測 | 實際 | 方向 |
| --- | --- | --- | --- |
| W1 | 0.85–0.95（偏過） | **0.9000** | **命中**（貼地板） |
| W2 | 不過，0.10–0.25 | **0.1050** | **命中** |
| W3 | 0.90–1.00 | **0.5700** | 低於區間 |
| ranking | 0.25–0.55 | **0.1700** | 低於區間 |

W1／W2 命中，W3／ranking 落空。W3 的落空是這一節最重要的讀數。

**區域損失把 token cache 弄掉的擬合救回來了，但沒有把綁定帶出去**：同一個載體、同一個起點、
同一個 10,000 步，§59 的 0.5000 → **0.9000**（main 0.0808、aux 0.5143 在最後一個 epoch）。
所以「損失函數從來沒有要求模型在名冊裡做選擇」是一個真缺陷——把它補上，擬合就回來了。但留出
**0.1050**、Wilson 下界 0.0697，仍在 chance 之下；這個目標不是瓶頸。

**W3 才是機制讀數**：訓練時 94.0% 的預測落在本段名冊內，留出只有 57.0%（不管內容的期望
53.96%）。也就是說，模型在訓練段學會了「這一段口供的答案在這份名冊裡」，但到了沒見過的段，
它又退回全域常見名。這個差距和 §56／§57／§59 量到的是同一條退路，只是換了一個觀測點：
**名冊的成員資格是跟著 session 身分背下來的，不是從名冊文字算出來的**。損失只在名冊上做
softmax，主損失仍在自由詞表上，所以推論時沒有任何東西強迫它留在名冊裡——§60.6 已把這一點
寫在跑之前，結果照實顯示限制沒有轉移。

**留出在統計上與 chance 不可分**：21/200，期望 31.8；Wilson 下界 0.0697。逐鏈：ledger **0/54**、
apron 7/52（0.1346）、badge 7/46（0.1522）、window 7/48（0.1458），四條鏈都在 chance 附近或
之下，沒有哪一條把機制扛起來。12 個不同預測，留出最多的是 `Kevin`（12.5%），訓練段最多的是
`Alex`（11.5%）。

**逐邊界讀數（`diagnostics.readout`，同一份 checkpoint，不訓練）**：第 6 輪 n=98 exact
**0.0102**（1/98）、第 7 輪 4/200 = 0.0200、第 8 輪 2/200 = 0.0100、第 9 輪 2/200 = 0.0100、
第 10 輪 21/200 = **0.1050**。答案是到最後一個邊界才出現，而且出現的比率就是留出比率；整條
路徑沒有提早綁定。

**`flip`：`changed` 第一次不是 0，但 `flipped` 仍是 0**。98 段裡 `changed` = 21
（0.2143），`flipped` = 0（上界 0.0377）；撤回前答對 8/98、撤回後答對 14/98、兩次都對 0。
§59.10 已把這兩個讀數分開：`changed` 是「換了一個名字」（診斷用），`flipped` 是「撤回前答對
陷阱、撤回後答對兇手」（強讀法）。所以這次的「有在動」不是撤回，是噪聲；不能寫成為「學到更新」。

**成本**：12,471.8 秒，比 §57 的 7,363.7 秒多 **69.4%**。§60.2 估的是 +10–20%，估錯了：實際
每個 epoch 有 15,852 個候選對（不是估計的「8 個樣本 × 5–8 個名字」那個量級），每個名字最多
6 個 byte、要 teacher-forced 解碼。照實記，不藏；停損規則不允許用「多跑幾個 epoch」把成本
差補回來。

**擬合不是收斂值**：第 150 個 epoch total 0.8788（main 0.1445、aux 0.7343），第 200 個
0.5952（main 0.0808、aux 0.5143），aux 還在降。所以 0.9000 是「跑完 200 個 epoch」的讀數，
不是收斂值；而且它剛好等於門檻（`>=` 才算過），一點擾動就會掉到線下，這個 PASS 是脆的。

**消融照實記**：`reset` 0.0850、`no_correction` 0.0816、`no_bounds` 0.1154、`skip_al` 0.1000；
in-roster 分別是 0.5900／0.5714／0.5962／0.5600，和完整的 0.5700 幾乎一樣。`no_roster` 不能
評分（沒有名冊就沒有可回答的區域）。和 §56／§57／§59 一樣，消融在 chance 附近沒有資訊；
in-roster 也不隨消融改變，再一次顯示那個行為不是從 state 來的。

**限制**：400 段仍是 800 段的子集；單一 seed；CPU；單一任務；單一讀出；沒有格式對照（Q7
仍未跑）；候選集合在訓練時來自 `derive()`（合法的監督，但推論時不能用，W3 量的正是這個轉移）。
W2 的失敗只說「這個目標、這個預算、這份語料不泛化」，不證明核心不能綁定，也不證明
「把身分退路拿掉」一定有效——那正是 §61 要量的。核心分不變 **0.00/10**。

## 六十一、階段 CF：把「身分」從答案的充分統計量裡拿掉（反事實語料；2026-11-14，量測前寫定）

### 61.1 為什麼是這一問

§60 的機械分支（W1 過、W2 不過）只允許一個介入：**反事實語料**。理由在 §60.9 的 W3 讀數裡：
訓練段 94.0% 的預測落在本段名冊內，留出只有 57.0%（不管內容的期望 53.96%）。模型學會的是
「這**段**口供的答案在這份名冊裡」，而「這一段」是用 session 身分認出來的。所以留出不是沒學會
名冊，而是**沒有需要用名冊**：每一段口供在訓練集裡只有一個版本，身分本身就是答案的充分統計量。

§60 的損失只在名冊上做 softmax，主損失仍在自由詞表；推論時沒有任何東西強迫模型留在名冊裡。
把損失再收緊一次是「在同一個退路上加壓」，不是把退路拆掉。這一節改的是**語料**：每一段口供多一個
配對版本，名冊的成員集合、證詞、時間、物品全部逐位元組相同，**只有名冊裡「哪個值對到誰」的兩格
互換**——證據值不變、證詞不變，兇手因此不同。

結果是：同一段非名冊文字，對應兩個不同答案。「背下這一段 → 那個名字」不再是充分策略，因為
這一段有兩個答案；模型若還要答對，只能去讀名冊那一行。

### 61.2 唯一的變數：`--counterfactual`（語料），其餘逐項固定

* **配對的建法**（`scripts/gen_pantry_ecosystem.py` 的 `counterfactual_twin`）：取該段口供的
  名冊對照 `value → name`，把「兇手實際使用的證據值」與一名**非兇手且在名冊上**的人的值互換。
  名冊文字因此只差兩格；證詞（誰看到什麼顏色、哪張卡在哪裡進出）、時間線、物品、`actors` 全部
  `deepcopy` 後不動；`session_id` 加 `_cf`、`session_meta.index` 加 10,000、
  `session_meta.counterfactual_of` 指向原段、`ground_truth_oracle.culprit` 與最後一輪的
  `expected_final_deduction` 改成新兇手。
* **只接受真的換了答案的配對**：`derive()` 必須只回新兇手；撤回前的候選集合必須與原段**完全相同**
  （陷阱不能跟著換）；該段的資料閘門（`_validate_necessity`／`_validate_retraction`／
  `_validate_name_balance`／`_validate_session`）必須全過；答案五元組不得與留出集、也不得與其他
  配對重複。任一條件不過就換下一個人；全部不行就**拋錯**，不靜默跳過（跳過會悄悄改掉登記的語料）。
* **配對的人選**由 `session_id` 決定性洗牌，不用位置順序：位置順序會讓「第一個演員」過度常成為
  配對兇手，而語料的 `most_mentioned` 捷徑基準正好在同一個位置破平手——那會是一個原本被閘門擋掉
  的表面線索。（實作時真的踩到：位置掃描讓 `_validate_shortcuts` 在 0.237 失敗，改成洗牌後 PASS。）
* **語料形狀**：原始 800 段不動，前 200 段各插入一個配對版本，所以訓練 split 的前 400 項是
  `[o0, t0, o1, t1, …]`、後面接著原本第 201–800 段；**留出集逐位元組不動**（同一個 digest），
  §60 的 200 題就是這一節的 200 題。
* **不變的東西**：`--core turnstore`、§60 的 `--aux-loss 1.0 --aux-mode weighted-region`、
  10,000 步、seed 20261118、lr 5e-4、batch 8、`--device cpu`、從 L 的 checkpoint 出發
  （逐位核對）、`--gate-prefix G`。

**已登記的混淆（照實寫在跑之前）**：`--train-sessions 400` 在這裡是 **200 個不同的結構 + 200 個
配對版本**，不是 400 個不同的結構。所以 C1 的擬合率不能與 §57／§60 的「400 段不同口供」直接
比較；它的用途只有一個——確認這條臂不是被語料改壞了（擬合活著），不是新的能力讀數。

### 61.3 不變量（程式與測試都守著）

1. 配對除名冊那一輪外，**每一輪 `user_input` 與原段逐位元組相同**；`environment`、`timeline`、
   `chain`、輪數也相同。
2. 名冊的值集合與名字集合不變，只有恰好兩格互換，且互換的方向是「兇手的 live 值 ↔ 配對者的值」。
3. `derive(全部證詞) == [新兇手]`；`derive(撤回前) == derive(原段撤回前)`。
4. 新兇手 ≠ 原兇手；新答案五元組與留出集、其他配對都不重複。
5. 留出集的 digest 等於登記值；前 400 項必須是 200 組 `(原段, 配對)` 的交錯。
6. 1200 段（1000 訓練 + 200 留出）通過 §49.3 的捷徑稽核。

以上六條寫成 `validate_counterfactual()` 的閘門，並有 `tests/test_pantry_deduction.py` 的
8 條測試（含一條「把配對兇手改回去，閘門必須紅」的突變測試）。

### 61.4 門檻（跑之前寫定；C1／C2 沿用 §60 的數字，不新訂）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| C1 | 宣告的 400 項（200 結構 + 200 配對）train exact **≥ 0.90** | 擬合先活下來；否則這條臂的留出不可讀（同 §55 `STORE_FLOOR`、§60 W1） |
| C2 | 留出 exact 的 **95% Wilson 下界 > 0.1591** | 同一個 200 題、同一個 chance；高於名冊內均勻猜（同 §56 G2／§59 B2／§60 W2） |
| C3 | 配對診斷**已記錄**：`same_prediction`、`both_correct`、`structure_correct`、`twin_correct`、`targets_differ` | 機制讀數，不是分數（見下） |
| C4 | 成本（參數、秒、`aux_region`：計分／跳過邊界、每 epoch 候選對、平均寬度）已記錄 | — |

**C3 的算術必須先講清楚**：一組配對的兩個答案不同，若模型對兩項給同一個名字，這一組最多只能對
一題。因此 400 項裡若答對 ≥ 360（C1 過），`same_prediction` 必然 **≤ 40/200 = 0.20**。也就是說
「配對被答成不同名字」不是獨立證據，是 C1 的算術後果；C3 唯一真正有資訊的部分是
`both_correct` 是否 ≈ C1/2（模型沒有靠「一組固定答案」把擬合撐起來）。這一點寫在跑之前，避免
結果出來後把必然的事當成發現。

### 61.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| C1 | **0.80–0.95（偏過）** | 同樣的 10,000 步、同樣的目標；配對讓每個結構有兩個答案，但兩者的非名冊文字完全相同，等於把「這一組的答案」從 1 個變成 2 個，容量壓力上升 |
| C2 | **不過，0.10–0.25** | 語料拆掉了「身分 → 答案」的充分性，但沒有拆掉「自由詞表解碼不需要看名冊」這件事；而且留出集本來就沒有配對版本，訓練分佈的改變不一定轉移到留出 |
| C3 | `same_prediction` 0.00–0.20（被 C1 算術限制）；`both_correct` **0.30–0.48** | 若擬合 0.80–0.95 且同組答案不同，兩題都對的比率上限是 C1/2 ≈ 0.475 |
| ranking | **0.20–0.45** | 比 §60 的 0.1700 高一些（配對至少讓「這一段的答案」不再是單一名字），但仍受 C2 限制 |

C2 預測不過是刻意的，理由與 §60.4 同一個：如果只換語料就能讓留出過線，那 §58 的「表徵沒有綁定」
就要重寫。把衝突寫在跑之前，結果才有資訊。

### 61.6 這一節**不會**證明什麼

* 不是能力分數（核心分不變 0.00/10）；不是「學會了綁定」的證明，只是一個**必要條件**的測試。
* 400 項是 **200 個不同結構**（見 §61.2 的混淆）；單一 seed；CPU；單一任務；單一讀出。
* 配對由生成器用已知規則造出來；C2 過也只說「在這個任務、這個預算、這份語料下留出高於 chance」，
  不證明核心能在別的分佈上綁定。格式對照（Q7）仍然沒有跑。
* 留出集**沒有配對版本**：這一節量的是「訓練時拆掉捷徑，留出會不會跟著變好」，不是「留出也拆掉
  捷徑」的另一個實驗。

### 61.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore \
    --aux-loss 1.0 --aux-mode weighted-region --counterfactual \
    --gate-prefix G --device cpu --out data/pantry_stage/cf_arm
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

### 61.8 這一節的地位

§60.5 對「W1 過、W2 不過」只給了一條路，而且明文禁止加段數／步數／寬度。這一節就是那條路：
不改載體、不改目標、不改步數，只把「身分」從答案的充分統計量裡拿掉。C2 的預測是**不過**；
如果它過了，§58 的表徵診斷要重寫；如果它不過，下一步（留出名冊的排列／配對目標控制）已經寫在
下面的分支裡，不是事後才想。

### 61.9 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| C1 不過 | 配對讓擬合崩掉，這條臂的留出不可讀 | **最小綁定診斷**：一份只有 2 人的名冊、一個 live 值，逐步看它能不能在單一邊界上選對；**不得**加 epoch、加寬度、加段數 |
| C1 過、C2 不過 | 「每段一組答案」仍然可以逐段背下來（現在是兩個名字），沒有形成「讀名冊算答案」 | **留出名冊排列／配對目標控制**：同一份留出文字、換掉名冊的對應（或成對地要求兩個答案），量「答案有沒有跟著名冊走」；仍不得加步數／寬度 |
| C1+C2 過 | 拆掉身分捷徑後留出過線 | 登記同一個 rung 的配對 `resolvable` 對照（§55.6／§56.6 的 G3 流程）確認是語料的功勞；**仍不是能力分數** |

### 61.10 結果（2026-11-15，依 §61.7 的指令跑完，照實記）

| 讀數 | 值 |
| --- | --- |
| train exact（**宣告的 400 項全部**） | **0.5000**（200/400） |
| train exact（報告的 `train_fit`，前 200 項） | 0.5150（103/200） |
| train ranking（400 項，限縮到名冊） | 0.6050（Wilson 0.5563–0.6517） |
| train「預測落在本段名冊內」 | 325/400 = **0.8125**（不管內容的期望 0.5396） |
| 留出 exact（200 段） | **0.0900**（18/200） |
| 留出 Wilson 下界／上界 | **0.0577** ／ 0.1378 |
| chance | **0.1591** |
| 留出 ranking（限縮到名冊） | 0.1550（下界 0.1114） |
| 留出「預測落在本段名冊內」 | 111/200 = **0.5550**（不管內容的期望 0.5396） |
| 參數／步數／複習／秒 | 168,150 ／ 10,000 ／ 200 ／ **6,633.0** |
| `training.aux_region` | 2,604 個邊界計分／1,396 跳過／每 epoch 15,948 個候選對／平均寬度 6.12（最大 8） |
| 留出 digest | `2ef82f70…`＝登記值（`heldout_digest_registered: true`） |

四條門檻：**C1 FAIL**（0.5000 < 0.90）、**C2 FAIL**（下界 0.0577 < 0.1591）、
**C3 已記錄**（見下）、**C4 PASS**（參數、秒、`aux_region` 都在報告裡）。`--gate-prefix G` 的
機械輸出是：

> 「G1 fails: at 400 reviews/session the store does not fit 200 distinct sessions, so held-out is
> not read; next is per-turn regional losses (§55.6's T1-fail rule), never more epochs or width」

依 §61.9 的對應列（C1 不過）：

> **「最小綁定診斷：一份只有 2 人的名冊、一個 live 值，逐步看它能不能在單一邊界上選對；不得加
> epoch、加寬度、加段數」**

**預測對照（§61.5 寫在跑之前）**：

| 讀數 | 預測 | 實際 | 方向 |
| --- | --- | --- | --- |
| C1 | 0.80–0.95（偏過） | **0.5000** | 大幅低於區間 |
| C2 | 不過，0.10–0.25 | **0.0900** | 命中「不過」，但比區間更低 |
| C3 `same_prediction` | 0.00–0.20 | **0.56** | 落空（條件是 C1 過；C1 沒過，算術不適用） |
| C3 `both_correct` | 0.30–0.48 | **0.24** | 低於區間 |
| ranking | 0.20–0.45 | **0.1550** | 低於區間 |

**最重要的讀數不是 0.5000，而是「0.5000 是怎麼來的」**。C3 記下的配對表是：200 組配對、
`structure_correct` 103、`twin_correct` 97、`both_correct` **48**、`same_prediction` **112**。
由此可推（算術，不是新量測）：`exactly_one` = 104、`neither` = **48**。所以這條臂不是「模型完全
不看名冊」——完全不看時，同一組的兩項非名冊文字逐位元組相同，預測會**200/200 相同**；實際是
112/200 相同、88 組給了不同答案，而那 88 組裡有 **48 組兩題都對**（0.545，遠高於在 5–8 人名冊裡
亂猜兩個不同名字的 ~0.03）。也就是說：**能分辨配對的那一小部分是真的在讀名冊；其餘一半以上塌成
同一個答案，一組最多對一題，於是整體擬合剛好停在 0.5000。** 這是「綁定只在部分樣本上發生、
其餘退回身分」的混合物，不是「完全沒有綁定」。

逐鏈的擬合把這件事說得更清楚：**apron 34/90 = 0.3778**，其餘 ledger 0.5455、badge 0.5283、
window 0.5319——apron 的難度把整體拉到 0.5000；它不是四條鏈一起均勻地 0.5。

**留出仍在 chance 之下**（18/200，期望 31.8，Wilson 下界 0.0577）：逐鏈 ledger 6/54、apron 6/52、
badge 3/46、window 3/48。訓練段 in-roster 0.8125、留出 0.5550（不管內容的期望 0.5396）——和
§60 的 W3（0.94 → 0.57）是同一個形狀：在訓練段「知道答案在這份名冊裡」，到留出就退回全域常見名
（留出最多 `Elena` 20.5%、訓練段最多 `Elena` 17.75%，12 個不同預測）。

**逐邊界讀數**（同一份 checkpoint）第 6 輪 4/98 = 0.041、第 7 輪 0/200、第 8 輪 9/200 = 0.045、
第 9 輪 2/200 = 0.010、第 10 輪 18/200 = 0.090：答案仍然只在最後一個邊界出現，且比率就是留出比率。

**`flip` 第一次在統計上離開 0**：`changed` 39/98 = 0.398、**`flipped` 2/98 = 0.0204**
（Wilson 0.0056–0.0714，下界 > 0）、撤回前答對 8/98、撤回後答對 9/98。這是系列裡第一個非零的
強讀法，但只有 **2 個事件**，不能當成「學會更新」；照實記它的下界，不升級成結論。

**擬合不是收斂值**：第 150 個 epoch total 1.6377（main 0.3542、aux 1.2835）、第 200 個 1.4182
（main 0.2735、aux 1.1446），還在降。所以 0.5000 是「跑完 200 個 epoch」的讀數，不是收斂值；
§61.9 的 C1 失敗分支**不允許**用「多跑幾個 epoch」補，這一點在跑之前就寫定了。

**成本**：6,633.0 秒，比 §60 的 12,471.8 秒**少 46.8%**。兩個數字不能互相比較：§60 跑的時候
機器上有其他負載（§60.2 的成本估計也因此失準），這一輪是乾淨的單一 CPU 行程。照實記「不可控的
差異」，不用它宣稱任何效率。

**消融照實記**：`reset` 0.0850（ranking 0.1650）、`no_correction` 0.0816（0.1837）、
`no_bounds` 0.1346（0.1346）、`skip_al` 0.0850（0.1600）；in-roster 分別 0.5350／0.6224／
0.7692／0.5550。和 §56／§57／§59／§60 一樣，消融在 chance 附近沒有資訊。

**限制（照實寫）**：400 項是 **200 個不同結構**（§61.2 的混淆），所以 0.5000 不能與 §57／§60 的
「400 段不同口供」相比；單一 seed；CPU；單一任務；單一讀出；留出集沒有配對版本；格式對照（Q7）
仍未跑。C1／C2 的失敗只說「這份語料、這個目標、這個預算不擬合也不泛化」，不證明核心不能綁定——
配對表反而顯示它**部分**在綁定。核心分不變 **0.00/10**。

**下一步（依 §61.9 機械決定）**：最小綁定診斷（2 人名冊、1 個 live 值、單一邊界），不再加
epoch／寬度／段數。§61.9 沒寫到、但這一輪量到的是：那個診斷必須能分辨「負載下塌掉」與
「從未綁定」——配對表的 48/88 兩題都對說明是前者，這一條會寫進 §62 的登記。

## 六十二、階段 MB：最小綁定診斷（2 人名冊、1 個 live 值；2026-11-15，量測前寫定）

### 62.1 為什麼是這一問

§61.9 對「C1 不過」只給了一條路，而且明文禁止加 epoch／寬度／段數：

> **最小綁定診斷**：一份只有 2 人的名冊、一個 live 值，逐步看它能不能在單一邊界上選對。

§61.10 的配對表讓這條路多了一個必須回答的問題：200 組配對裡 `same_prediction` 112、`both_correct`
48，而 88 組給了不同答案的配對中有 48 組**兩題都對**。所以上一輪的 0.5000 **不是**「完全不看名冊」，
而是「一部分在看、一半以上塌成同一個答案」。§62 要分辨的就是這兩種讀法：

* **負載下塌掉**：名冊只有 2 人、證據只有 1 個值、口供只有 4 輪時，它會綁定；上一輪是容量／干擾
  把它壓垮的。
* **從未綁定**：連這個最小情況都不綁定；那 §61 的 48 組只是「兩個答案剛好都猜中」的殘餘，不是
  機制。

這兩種讀法的下一步完全不同（見 §62.8），所以必須先量，不能從 0.5000 推論。

### 62.2 儀器：一份**獨立**的最小語料，不是把 800/200 改造

登記的產生器做不出 2 人名冊：四條鏈都要 3–4 個演員（`sample(actors, 3)`、時間窗要留兩側誘餌、
撤回要指向另一個人）。硬把名冊縮到 2 人會同時拆掉陷阱、時間濾網與撤回，等於換了一個任務卻還掛著
同一個 digest。所以 §62 用**另一份語料**，並在報告裡用 `corpus.minimal_binding` 標記；登記的
800/200 語料與 §61 的配對語料都不動。

每一段 4 輪（`scripts/gen_pantry_ecosystem.py` 的 `_minimal_session`）：

1. 案件：茶水間少了 N 份某物，旁邊冰了另一個誘餌物（**沒有任何 asserts**）。
2. 名冊：`今天值班表上寫著：紅色是 A、白色是 B。`（`roster` assert，值是**顏色**，兩個值對兩個人）。
3. 證據：目擊者看到一個人穿著**其中一個顏色**的圍裙出來（`seen` assert，帶時間戳）。
4. 提問：誰吃了它？（`expected_final_deduction` ＝ 兇手）。

沒有陷阱、沒有撤回、沒有時間濾網；**證據只有一個值**，那個值在名冊上。另一個顏色（dead value）
只出現在名冊，從不出現在證詞裡——它讓名冊是真的「二選一」，不是單筆查表。

**配對版本**（`minimal_twin`）：把名冊的兩個名字互換，其餘每一個 byte 不動（證據的顏色不變，所以
換完之後它指到另一個人）。這就是最小可能的反事實：一行名冊、兩個名字對調、答案不同。

**形狀**：訓練 `[o0, t0, o1, t1, …]` ＝ 200 段 + 200 個配對版本 ＝ **400 項**；留出 **200 段**，
另加 **200 個留出配對**（`heldout_twins`，只做診斷，不計分）。chance ＝ **0.5**（2 個演員）。

**不變的東西**：`--core turnstore`（168,150 參數）、10,000 步、seed 20261118、lr 5e-4、batch 8、
`--device cpu`、從 L 的 checkpoint 出發（逐位核對）、`--gate-prefix G`、`--aux-loss 1.0`。

**唯一的變數是語料**，但**目標函數必須改**，這點寫在跑之前：§60／§61 的 `weighted-region` 會把
每個早段邊界都當成 2 選 1（寬度 2 → 權重 0.5）。在第 0 輪（只有案件、沒有任何 assert）與第 1 輪
（只有名冊）的邊界上，**沒有任何資訊能區分兩個人**，那裡等於要求模型從噪音預測兇手。§62 要問的
是「單一邊界能不能綁定」，所以用 `--aux-mode resolvable`：只有 `derive()` 已經唯一的那個邊界
（第 2 輪之後）被訓練。**照實記這個混淆**：語料與目標函數都和 §61 不同，所以 M1／M2 不能歸因給
其中任何一項；§62 是診斷，不是歸因臂。

### 62.3 不變量（程式與測試都守著）

`validate_minimal_binding()`（訓練前跑，任一違反就 `SystemExit`）：

1. 訓練 400 項、留出 200 段 + 200 個留出配對；訓練的前 400 項是 200 組 `(原段, 配對)` 的交錯。
2. 每一段 4 輪、**2 個演員**；名冊剛好 2 格，兩格的名字集合等於演員集合。
3. **證據只有 1 個值**，而且是 `seen`；它在名冊上；dead value 從不以任何形式出現在證據裡。
4. `derive(全部證詞) == [兇手]`；**只看名冊（第 0–1 輪）仍是兩個人**（名冊本身不能回答）。
5. 每個名字在整段文字裡只出現 1 次，且**不出現在提問那一輪**；oracle tag 不在文字裡。
6. 配對除名冊那一輪外**逐位元組相同**；配對的兇手 ≠ 原段兇手；`derive(配對) == [配對兇手]`。
7. 留出配對與留出段一一對應（`counterfactual_of`），且答案互換。
8. 答案五元組（`_answer_key`）在訓練 + 留出之間不重複。

另外 `tests/test_pantry_deduction.py` 有 9 條 §62 測試（形狀、決定性、閘門、2 人／1 值／無陷阱、
dead value 不出現、配對逐位元組相同且換答案、留出配對連結、配對報告算術、CLI 拒絕 7 種會改動
這條臂的組合）。

**這份語料沒有可預先釘住的 digest**（它今天才存在，不像 §49 的 800/200）。取而代之：`--check`
會重新產生整份語料並比對報告裡的 `train_digest`／`heldout_digest`，另有一條測試斷言兩次建構
逐位元組相同。

### 62.4 門檻（跑之前寫定；M1／M2 沿用 §56 的數字，不新訂）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| M1 | 宣告的 **400 項**（200 結構 + 200 配對）train exact **≥ 0.90** | 擬合先活下來；不過就是「連最小負載都不綁定」，留出不可讀（同 §55 `STORE_FLOOR`、§60 W1、§61 C1） |
| M2 | 留出 exact 的 **95% Wilson 下界 > 0.5** | 高於 2 人名冊的均勻猜；用下界而不是點估計（同 §56 G2／§60 W2／§61 C2） |
| M3 | 配對診斷**已記錄**：擬合的 `same_prediction`、`both_correct`、`structure_correct`、`twin_correct`、`targets_differ`，以及**留出配對**的同一組數字 | 機制讀數，不是分數 |
| M4 | 成本（參數、秒、步數、`updates_per_session`）已記錄 | — |

**M3 的算術先講清楚**（同 §61.4）：每組配對的兩個答案不同，若模型對兩項給同一個名字，這一組最多
對一題。所以若 M1 過（≥ 360/400），`same_prediction` 必然 **≤ 40/200 = 0.20**；「配對被答成不同
名字」不是獨立證據。M3 真正有資訊的是 `both_correct` 是否 ≈ M1/2，以及**留出配對**的
`same_prediction`（留出沒有擬合壓力，那邊的同答率才是「看不看名冊」的乾淨讀數）。

### 62.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| M1 | **0.90–1.00（偏過）** | 這裡要學的只是一個 2 格查表：名冊那一行寫著「顏色→人」，證據那一輪說出顏色。§61 的 0.5000 是在 5–8 人名冊、8 輪證詞、時間濾網與陷阱之下得到的；把這些全部拿掉後，擬合要活下來只需要學這一個函數 |
| M2 | **不過，0.50–0.55（Wilson 下界 ≤ 0.5）** | §57 的 in-roster 0.5350、§58 的線性探針（in-sample 0.9725、留出 0.1100）與 §61 的 0.5550 都指向「答案在訓練段、不在留出」。2 人只把 chance 抬到 0.5，門檻變鬆，但同一個過擬合形狀預測仍是 0.5 附近 |
| M3 | `same_prediction` ≤ 0.20（M1 過的算術後果）；`both_correct` **0.40–0.50**；留出配對 `same_prediction` **0.60–0.90** | 若 M1 過，擬合段的配對必須分開（否則最多 0.5）；留出段若仍是每段一個名字，就會大量同答 |
| M4 | 記錄 | — |

M1 過而 M2 不過是**預期**的組合；這正是「綁定只在訓練段」的讀法，不是失敗。反過來，M1 不過是
這一節**真正想抓**的結果：那表示連 2 人 1 值都綁不起來，§61 的 48/88 就不能讀成「部分綁定」。

### 62.6 這一節**不會**證明什麼

* 不是能力分數（核心分不變 0.00/10）；不是「學會了綁定」的證明。
* 400 項是 **200 個不同結構**（每組一對），不能與 §57／§60 的「400 段不同口供」相比。
* 單一 seed；CPU；單一任務；單一讀出；2 人名冊的 chance 是 0.5，M2 的門檻比 §56–§61 鬆。
* 語料與目標函數同時偏離 §61（§62.2 的混淆），所以 M1／M2 不是歸因。
* 留出配對是**診斷**，不是第二個分數；它不進門檻。

### 62.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding \
    --gate-prefix G --device cpu --out data/pantry_stage/min_arm
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

### 62.8 這一節的地位

§61.9 的機械分支只允許這一個介入，並且明文禁止加 epoch／寬度／段數。§62 把它縮到不能再縮：
2 個人、1 個值、4 輪、單一邊界。結果只回答一個問題——**這個載體在最小負載下會不會綁定**。

### 62.9 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| M1 不過 | 連 2 人 1 值都不擬合：不是「負載下塌掉」，是**從未綁定**（在這個載體／目標／預算下） | **單段梯度檢查**：只拿一組 `(原段, 配對)` 做同樣的損失與步數，看 loss 是否下降、兩個答案是否分開；若連一組都分不開，問題在讀出／梯度路徑，不在容量。**不得**加 epoch、加寬度、加段數 |
| M1 過、M2 不過 | 綁定是**逐段查表**（在訓練段會、到留出就退回常見名） | **容量曲線**（2／3／4／5 人，同一個預算）或**留出名冊排列控制**（同一份留出文字、只換名冊對應，看答案跟不跟著名冊走）；選一個，登記後再跑；仍不得加步數／寬度 |
| M1 + M2 過 | 最小負載下綁定且轉移到留出 | **容量曲線往上**（2→3→4→5 人，同一個預算），確認是哪一格開始掉；**仍不是能力分數** |

### 62.10 結果（2026-11-15，依 §62.7 的指令跑完）——還有跑完之後才發現的語料缺陷

| 讀數 | 值 |
| --- | --- |
| M1 train exact（**宣告的 400 項全部**） | **1.0000**（400/400，Wilson 0.9905–1.0000） |
| M1 train exact（報告的 `train_fit`，前 200 項） | 1.0000（200/200） |
| M2 留出 exact（200 段） | **1.0000**（200/200，Wilson 下界 **0.9812** > 0.5） |
| chance | **0.5**（2 個演員） |
| 留出 ranking | 1.0000 |
| 留出「預測落在本段名冊內」 | 200/200 = 1.0000（不管內容的期望 0.1667） |
| `reset`（T2 式消融） | **0.0900**（18/200，ranking 0.4500） |
| `no_bounds`（此語料沒有時間濾網） | 1.0000（與 `full` 相同，照實記） |
| `skip_al` | 1.0000 |
| 留出配對（診斷） | 200 組、`same_prediction` **0**、`both_correct` **200** |
| 參數／步數／秒 | 168,150 ／ 10,000 ／ **1,845.2** |
| 逐邊界讀數 | 第 0、1 輪 n=0（名冊本身仍無法回答）；第 2 輪 200/200；第 3 輪 200/200 |
| 語料 digest | train `6e99f629…`、heldout `6e19fd05…`（`--check` OK） |

四條門檻：**M1 PASS**、**M2 PASS**、**M3 已記錄**、**M4 PASS**；`--gate-prefix G` 的機械輸出是
`all_pass: True`。依 §62.9 的對應列（M1 + M2 過）：

> **「容量曲線往上（2→3→4→5 人，同一個預算），確認是哪一格開始掉；仍不是能力分數」**

**但是這一列不能套用。** 跑完之後的稽核找到一個語料缺陷，它讓這一輪的 M1／M2 無法區分「綁定」與
「讀位置」：

`_minimal_session()` 用 `mapping = {dead_value: other, live_value: culprit}` 建名冊，
Python 的 dict 保留插入順序，所以**名冊的第二格永遠是兇手**。四組都一樣：

| 組別 | 「名冊第二格」等於兇手 |
| --- | --- |
| 訓練結構（200） | **200/200** |
| 訓練配對（200） | **200/200** |
| 留出結構（200） | **200/200** |
| 留出配對（200） | **200/200** |

證據值在名冊上的位置分布（留出 200 段）：**`{1: 200}`**——永遠在第二格。

**配對診斷抓不到它**：位置策略對結構答第二格（正確）、對配對也答第二格（配對的第二格在換名後
剛好是新的兇手），所以 `same_prediction` 是 0、`both_correct` 是 200——和真正的綁定完全一樣。
§62.4 的算術只排除了「兩題同答」，排除不了「兩題都答第二格」。

**對已完成 checkpoint 的位置對照（跑完之後才做的診斷，不是登記的臂）**：把留出段的**名冊順序反過來**
（`value → name` 的對應不動，所以正解完全不變），用同一個 checkpoint 重評：

| 讀數 | 原順序 | 名冊順序反轉（正解不變） |
| --- | --- | --- |
| exact | 200/200 = **1.0000** | **0/200 = 0.0000** |
| 預測 == **新**名冊第二格 | — | **200/200** |
| 預測 == **舊**名冊第二格 | — | **0/200** |

例：`David -> David`（原順序）；反轉後 `David -> Frank`，而新的第二格正是 `Frank`。**模型答的是
第二格，不是名冊的對應。** 所以 §62 的 1.0000 是位置捷徑，不是綁定；§62.2 說「§62 要分辨
『負載下塌掉』與『從未綁定』」——這一輪兩個都沒有分辨到。

**預測對照（§62.5 寫在跑之前）**：

| 讀數 | 預測 | 實際 | 判讀 |
| --- | --- | --- | --- |
| M1 | 0.90–1.00（偏過） | **1.0000** | 命中，但事後看是捷徑給的 |
| M2 | 不過，0.50–0.55 | **1.0000** | **大幅落空**——這個落空本身就是缺陷的訊號：2 人查表不該比 8 人名冊（§60 0.1050）好這麼多 |
| M3 `same_prediction` | ≤ 0.20 | **0.0** | 命中 |
| M3 `both_correct` | 0.40–0.50 | **1.0000** | 落空 |
| M3 留出配對 `same_prediction` | 0.60–0.90 | **0.0** | 落空 |

**照實記的三件事**：

1. **這一輪的 M1／M2 不作數**（不是「不過」，是**無效**）：它量到的是「模型會答名冊第二格」。
   核心分不變 **0.00/10**。
2. **缺陷在語料，不在模型**：`validate_minimal_binding()` 的八條不變量裡沒有一條檢查「兇手在名冊
   的位置」，而 §62.3 的第 5 條（每個名字只出現一次）反而讓位置線索更乾淨。
3. **位置對照是可重用的儀器**：把名冊順序反轉、對應不動，正解不變——任何「讀位置」的模型在這裡
   會整批翻掉。它應該**登記成門檻**，而不是跑完之後才想起來。

**下一步（依 §62.9 的機械分支 + 這一輪的缺陷）**：§62.9 的「容量曲線往上」**暫緩**，因為在位置
線索存在時，容量曲線每一格都會量到同一個捷徑。先做兩件事，並在跑之前登記為 §63：

* **語料修正**：名冊順序由 `index` 的奇偶決定（偶數兇手在第一格、奇數在第二格），讓兇手位置在
  200 段裡剛好 100/100，且與名字無關；配對保持「只換名字、不動順序」，所以配對的兇手位置正好與
  原段相反。§62 的舊語料**保留可重現**（報告記 `corpus.minimal_roster_order`，`--check` 用同一個
  順序重建；舊報告沒有這個欄位，預設回舊順序），新臂用 `balanced`。
* **位置對照升級為門檻 M5**：同一批留出段、名冊順序反轉、對應不動，`exact` 必須 ≥ **0.80**；
  若 M1 不過則 M5 記為不可讀（`None`，不進 verdict），因為模型連任務都不會時，反轉掉分不能證明
  什麼。

## 六十三、階段 CF2：位置對照與平衡名冊（2026-11-15，量測前寫定）

### 63.1 為什麼 §62 的 1.0000 不作數

§62 跑完、稽核之後才發現：`_minimal_session()` 用
`mapping = {dead_value: other, live_value: culprit}` 建名冊，dict 保留插入順序，所以**名冊的第二格永遠
是兇手**（訓練結構、訓練配對、留出、留出配對四組都是 200/200；留出的 live 值位置分布是 `{1: 200}`）。
一個只答「第二格」的模型在結構與配對上都會答對，所以配對診斷的 `same_prediction` 是 0、
`both_correct` 是 200——和真正的綁定一模一樣。用完成的 checkpoint 做位置對照（名冊順序反轉、對應不動、
正解不變）：原順序 200/200、反轉後 **0/200**，預測 200/200 跟著**新的**第二格走。§62 量到的是位置捷徑，
不是綁定。

**所以 §62 的 M1／M2 是無效，不是「不過」。** §62.9 的「M1 + M2 過 → 容量曲線往上」暫緩：在位置線索
還在的時候，容量曲線每一格都會量到同一個捷徑。§63 先修語料，並把那個位置對照**升級成門檻**，而不是
跑完之後才想起來的診斷。

### 63.2 語料修正：名冊順序由 index 的奇偶決定

`_minimal_session(..., roster_order=)`：

* `balanced`（新臂的預設）：`index` 偶數 → `{live: culprit, dead: other}`（兇手在第一格）；`index` 奇數
  → `{dead: other, live: culprit}`（兇手在第二格）。**兩個位置各半**，且與名字無關。
* `culprit_second`：§62 的舊順序，保留是為了讓那份報告仍可 `--check`（報告記
  `corpus.minimal_roster_order`；舊報告沒有這個欄位，重載時預設回舊順序）。

**配對仍然只換名字、不動順序。** 這一點要先講清楚，否則會誤以為配對也會把位置翻過來：配對保留 live 值
的**鍵**，只把兩個名字對調，所以配對的兇手（另一個名字）**坐在同一個格子**。因此「第二格讀者」在奇數
段對結構與配對都對、在偶數段對兩者都錯——一對配對剛好贏一半，**整體等於 2 人 chance（0.5）**，沒有
免費的分數。驗證器因此對**四組**（訓練結構、訓練配對、留出、留出配對）都要求兇手位置 100/100：

```python
for label, rows in (("train structures", ...), ("train twins", ...),
                    ("heldout", ...), ("heldout twins", ...)):
    positions = [culprit_position(s) for s in rows]
    first, second = positions.count(0), positions.count(1)
    if first + second != len(positions) or first != second:
        problems.append(... "a positional shortcut would be free")
```

`validate_minimal_binding()` 的其餘八條不變量不動；`roster_order="culprit_second"` 時跳過這一條（舊語料
本來就不平衡，而它的用途是可重現，不是再被評分）。

### 63.3 新門檻 M5：名冊順序反轉，正解不動

`reorder_roster()`：把名冊的兩個條目**順序對調**，`value → name` 的對應完全不動，並用產生器自己的
`_roster_text()` 重畫那一輪（插入順序與分隔符與產生器一致，所以只有兩格的前後改變）。`derive()` 仍然
指到同一個兇手——**正解不變**。只有「讀位置」的模型會被擾動。

`roster_permutation_report(core, heldout, module=)` 對同一批留出段重評，記下：

* `exact`：反轉後的正確率；M5 要求 **≥ 0.80**（`ROSTER_PERMUTATION_FLOOR`）。
* `follows_second_entry`：反轉後預測等於**新**第二格名字的次數。§62 的 checkpoint 在這一欄是
  **200/200**，`exact` 是 **0.0**——儀器讀得出來那個缺陷。
* `note`：寫明這個對照的語意。

**M5 在 M1 不過時記為 `None`**（不可讀、不進 verdict）：模型連任務都不會時，反轉掉分不能證明它讀位置。
這與 §56 G3「需要兩條臂」的處理相同：單一報告不能宣稱它。

### 63.4 門檻（跑之前寫定；M1／M2 與 §62 完全相同，不因結果放寬）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| M1 | 宣告的 400 項（200 結構 + 200 配對）train exact **≥ 0.90** | 擬合先活下來（同 §55 `STORE_FLOOR`、§60 W1、§61 C1、§62 M1） |
| M2 | 留出 exact 的 **95% Wilson 下界 > 0.5** | 高於 2 人名冊的均勻猜（同 §56 G2／§60 W2／§61 C2） |
| M3 | 擬合與留出配對的 `same_prediction`／`both_correct`／`structure_correct`／`twin_correct`／`targets_differ` **已記錄** | 機制讀數，不是分數 |
| M4 | 成本（參數、秒、步數、`updates_per_session`）已記錄 | — |
| **M5** | 留出名冊順序反轉、正解不動，exact **≥ 0.80**；M1 不過時為 `None` | **位置對照**：答的是對應，不是格子 |

### 63.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| M1 | **0.90–1.00（偏過）** | 要學的仍是一個 2 格查表；§62 的擬合也是 1.0000。拿掉位置捷徑不會讓「擬合」變難，只會讓它必須真的讀名冊 |
| M2 | **不過，0.50–0.60（Wilson 下界 ≤ 0.5）** | §57 的 in-roster 0.5350、§58 的線性探針（in-sample 0.9725、留出 0.1100）、§60 的 0.1050、§61 的 0.5550 都指向「答案在訓練段、不在留出」。2 人只把 chance 抬到 0.5，門檻變鬆，但同一個形狀預測仍是 0.5 附近 |
| M3 | 擬合 `same_prediction` ≤ 0.20（M1 過的算術後果）；`both_correct` 0.40–0.50；留出配對 `same_prediction` 0.50–0.90 | 若 M1 過，擬合段配對必須分開；留出段若仍每段一個名字，就會大量同答 |
| M4 | 記錄 | — |
| M5 | **0.90–1.00（偏過）** | 若 M1 過，模型必須是「證據值 → 名字」的對應才可能在平衡語料上擬合；反轉順序不應該動它。**若 M5 不過而 M1 過，代表它找到了別的位置線索**——那是語料層的缺陷，下一步是語料稽核，不是容量 |

M1 過、M2 不過仍是**預期**組合：綁定只在訓練段。§63 真正要抓的是 **M1 不過**與 **M5 不過**：前者說
§62 的 1.0000 全部來自位置，後者說平衡語料之外還有別的位置線索。

### 63.6 這一節**不會**證明什麼

* 不是能力分數（核心分不變 0.00/10）；不是「學會了綁定」的證明。
* 400 項是 200 個不同結構（每組一對），不能與 §57／§60 的「400 段不同口供」相比。
* 單一 seed；CPU；單一任務；單一讀出；2 人名冊的 chance 是 0.5，M2 的門檻比 §56–§61 鬆。
* **語料與目標函數仍同時偏離 §61**（`--aux-mode resolvable`，理由同 §62.2 的混淆）：§63 是診斷，不是
  歸因臂。
* 留出配對仍是**診斷**，不是第二個分數；它不進門檻。

### 63.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding \
    --gate-prefix M --device cpu --out data/pantry_stage/min2_arm
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

**啟動時的實作修正（在看到任何結果之前）**：`--gate-prefix` 為 `G` 或 `M` 時不要求 F-rand 對照報告。
§62 以 G 跑，因此原本就沒要求；§63 改用 M，而 M1–M5 沒有任何「格式對照」條款，且 §62 的配對來自真兇、
做不出格式對照。這只改「先決條件」，不改門檻、語料、評分或任何預測。

### 63.8 這一節的地位

§62 的結果不作數，因為它的語料讓「答第二格」與「讀名冊」在四組資料上都無法區分。§63 只做兩件事：
把兇手的位置在語料裡對半（並且驗證器守住），把位置對照升成 M5 門檻。除此之外**沒有**加 epoch、寬度、
段數、載體或新目標——那些是 §62.9 明文禁止的。

### 63.9 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| M1 不過 | 拿掉位置捷徑後連擬合都沒有：§62 的 1.0000 全部是位置，這個載體／目標／預算下**從未綁定** | **單段梯度檢查**：只拿一組 `(原段, 配對)`，同樣的損失與步數，看 loss 是否下降、兩個答案是否分開；若連一組都分不開，問題在讀出／梯度路徑。**不得**加 epoch、寬度、段數 |
| M1 過、M5 不過 | 擬合了，但換名冊順序就掉：**還有位置線索沒清掉**（語料缺陷，不是模型） | **語料稽核**（逐輪找還有什麼在預測答案：名字長度、顏色、時序、token 位置），修完重新登記；**不得**把 M5 的地板調低，也不得改 M1／M2 |
| M1 + M5 過、M2 不過 | 綁定是**逐段查表**（訓練段會、留出退回常見名），位置已排除 | **容量曲線**（2／3／4／5 人，同一個預算），確認從哪一格開始掉；仍不得加步數／寬度 |
| M1 + M2 + M5 過 | 最小負載下綁定、位置已排除、且轉移到留出 | **容量曲線往上**（2→3→4→5 人，同一個預算）；**仍不是能力分數** |

### 63.10 結果（2026-11-15，依 §63.7 的指令跑完）

| 讀數 | 值 |
| --- | --- |
| M1 train exact（**宣告的 400 項全部**） | **0.9775**（391/400，Wilson 0.9578–0.9881） |
| M1 train exact（`train_fit`，前 200 項） | 0.9700（194/200） |
| M2 留出 exact（200 段） | **0.4250**（85/200，Wilson **0.3585–0.4943**） |
| chance | **0.5**（2 個演員） |
| 留出 ranking | 0.5600（112/200） |
| 留出「預測落在本段名冊內」 | 147/200 = 0.7350（不管內容的期望 0.1667） |
| `reset` | **0.0950**（19/200，ranking 0.4650，單一預測 `Lena`） |
| `no_bounds` | 0.4250（此語料沒有時間濾網，與 `full` 相同） |
| `skip_al` | 0.4300（86/200） |
| 留出配對（診斷） | 200 組、`same_prediction` **26**、`both_correct` **55**、structure 85、twin 83 |
| 擬合配對（診斷） | 200 組、`same_prediction` **6**、`both_correct` **192**、structure 195、twin 196 |
| **M5** 名冊順序反轉（正解不動） | **0.3100**（62/200）；`follows_second_entry` 80/200 = 0.40 |
| 參數／步數／秒 | 168,150 ／ 10,000 ／ **1,826.7** |
| 逐邊界讀數 | 第 0、1 輪 n=0；第 2 輪 200/200；第 3 輪 200/200 |
| 語料 digest | train `ad5cb3bf…`、heldout `69c730e1…`（`--check` OK） |

四條門檻：**M1 PASS**、**M2 FAIL**、**M3 已記錄**、**M4 PASS**、**M5 FAIL**。依 §63.9 的對應列：

> **「M1 過、M5 不過 → 還有位置線索沒清掉（語料缺陷，不是模型）→ 語料稽核」**

稽核做完了，**它否證了這一列的前提**：平衡語料沒有留下位置線索，M5 的掉分來自模型自己的順序偏好。

**稽核（跑完之後，診斷；不是登記的臂）**。對四組資料逐一測試「不讀名冊對應、只看某個表面特徵」的規則
（每條規則都是「這一段該答哪個名字」，chance 0.5）：

| 規則 | 訓練結構 | 訓練配對 | 留出結構 | 留出配對 |
| --- | --- | --- | --- | --- |
| 答名冊第二格 | 0.50 | 0.50 | 0.50 | 0.50 |
| 答名冊第一格 | 0.50 | 0.50 | 0.50 | 0.50 |
| 名字較長 | 0.55 | 0.51 | 0.49 | 0.56 |
| 名字較短 | 0.51 | 0.55 | 0.56 | 0.49 |
| ACTORS 較前 | 0.56 | 0.45 | 0.48 | 0.52 |
| ACTORS 較後 | 0.45 | 0.56 | 0.52 | 0.48 |
| 顏色在 COLOURS 較前 | 0.52 | 0.52 | 0.50 | 0.50 |
| 顏色在 COLOURS 較後 | 0.48 | 0.48 | 0.50 | 0.50 |
| 字母序較前／較後 | 0.56／0.45 | 0.45／0.56 | 0.48／0.52 | 0.52／0.48 |

最高 0.56，全部落在 200 題的噪音範圍內（SE ≈ 0.035）。位置分布是 **100/100**（四組都一樣），
live 值在名冊的哪一格與顏色、名字、index 都沒有系統關係；訓練與留出的 `(live 顏色, 兇手)` 組合
85 與 83 種、重疊 74 種，沒有「留出用沒見過的名字」這回事（名字對 57 與 66 種，留出只有 9 種沒在訓練
出現）。**沒有一條語料規則能把答案從表面特徵讀出來。**

**M5 的掉分是什麼**（同一 checkpoint，把留出段按「正解在第幾格」切開）：

| 資料 | 正解在第 0 格 | 正解在第 1 格 |
| --- | --- | --- |
| 留出（原順序） | 28/100 = **0.28** | 57/100 = **0.57** |
| 留出配對 | 31/100 = 0.31 | 52/100 = 0.52 |
| 留出（名冊順序反轉後） | 24/100 = 0.24 | 38/100 = 0.38 |

不論名冊有沒有反轉，**正解在第 1 格時的正確率都比第 0 格高約 0.2**；反轉只是把「哪一半是第 1 格」
換過來。所以這是一個**順序偏好**（模型的讀出偏向名冊較後的名字），不是語料把答案放在固定格子。

**誠實的讀法**：

1. **M1 的 0.9775 是真的綁定，但只到擬合**：擬合段的配對 194/200 給不同答案、192/200 兩題都對，
   所以它確實在讀名冊（§61 的 112/200 同答已不復見）。這是這一輪相對 §61 唯一明確的進步。
2. **M2 的 0.4250 不是「剛好在 chance」，是低於 chance**（Wilson 上界 0.4943）。留出配對仍只有
   26/200 同答（13%），所以它也不是「完全不看名冊」；它是「看得懂，但常常選錯那一格」。
3. **M5 的 0.3100 不是語料缺陷**：稽核找不到任何表面規則（最高 0.56），位置分布 100/100。
   它是模型的順序偏好，登記的 M5-fail 分支（「語料缺陷」）**不成立**，因此**沒有做任何語料修補**，
   也沒有調低 M5 的地板或改 M1／M2。
4. **M5 的設計限制要照實記**：它的地板是絕對的 0.80，而留出正確率只有 0.425 時，反轉後不可能
   達到 0.80（除非反轉恰好把錯的變對的）。所以 **M5 只在 M2 接近 1 時有資訊量**；M2 在 chance
   附近時，M5 的 FAIL 不能單獨讀成「讀位置」。§64 會把這一點寫進登記，並改讀「順序保留率」這個
   診斷（反轉後 / 原順序），而不是把 M5 的地板改掉。
5. **§63.9 的分支被走了，但它的診斷被否證**：沒有語料可修。下一步必須針對量到的原因（順序偏好），
   而不是再改一次語料或加 epoch。核心分不變 **0.00/10**。

**下一步（登記為 §64）**：**順序擴增**（order augmentation）——同樣 200 個結構，每個結構在訓練裡
各出現兩次：一次原順序、一次名冊順序反轉（兇手不變，其餘文字逐位元組相同），仍然是 **400 項、
10,000 步、同一個目標**。這不是「加段數」：段數（不同口供）不變，改的是每個結構看到兩種順序。
它直接測試「順序偏好是不是可以被訓練消掉」，並用**順序保留率**（反轉後 exact ÷ 原順序 exact）讀，
M5 仍照登記記錄、不當地板使用。


## 六十四、階段 ORD：順序擴增（2026-11-15，量測前寫定）

### 64.1 為什麼要改訓練的呈現方式

§63 的稽核否證了「語料還有位置線索」：四組資料上沒有任何表面規則超過 0.56，兇手位置在名冊裡是
100/100 對半，訓練與留出的 `(live 顏色, 兇手)` 組合重疊 74/85。掉分的是**模型的順序偏好**——正解在
名冊第 1 格時正確率比第 0 格高約 0.2，名冊反轉只是把「哪一半是第 1 格」換過來（§63.10）。

因此 §64 不動語料、不動步數、不動目標函數，只改**每個結構在訓練裡看到幾種順序**：同一個結構出現兩次，
一次原順序、一次名冊反轉（對應與兇手都不動，其餘文字逐位元組相同）。仍然 400 項、10,000 步。

這一點很重要：**在順序擴增的語料上，「答第 N 格」不可能擬合。** 一個結構的兩份拷貝把兇手放在相反的
格子裡，任何固定位置規則在其中一份必錯，擬合上限是 0.5。所以 M1 不再是「§63 那種可以靠位置過關的
擬合」，而是「必須讀名冊對應才可能過」的擬合。

### 64.2 語料（`minimal_order_twin()`、`build_minimal_binding(order_augmented=True)`）

* 同樣 200 個結構（`minimal_pantry_000`…`199`），每個結構的配對不是換名字，而是**換名冊順序**：
  `session_id` 加 `_ro`、`session_meta.index + 20_000`、`session_meta.order_augmented_of = 原 id`，
  `value → person` 的對應完全不動，`derive()` 仍指同一個兇手。
* 訓練 400 項（200 結構 + 200 順序配對），留出仍是 200 結構 + 200 換名配對（`_cf`），**chance 0.5**。
* 驗證器（`validate_minimal_binding(..., order_augmented=True)`）額外要求：
  1. 沒有 `_cf` 配對、`_ro` 配對剛好 200 個；
  2. 訓練陣列是 `[原, 順序配對, ...]`，配對的 `order_augmented_of` 指向它的結構；
  3. 配對的兇手與對應不變、`derive()` 仍得到同一個兇手；
  4. 名冊條目**確實反轉**（`list(old_map) != list(new_map)`）；
  5. 非名冊輪的文字逐位元組相同；名冊輪的文字等於產生器自己的 `_roster_text()`；
  6. 兩個半邊的兇手位置各 100/100。
* §63 的語料（`balanced` 或 `culprit_second`）不受影響；新的「名冊文字必須等於 mapping 的渲染」檢查對
  兩者都成立（產生器本來就用 `_roster_text()` 畫那一輪），所以舊報告仍可 `--check`。

### 64.3 讀數：M5 仍然記錄，但這一節讀「順序保留率」

`roster_permutation_report()` 現在同時算原順序與反轉後：

* `original_exact`：原順序的正確率（等於 M2 的重評，用來對照）。
* `exact`：反轉後的正確率（M5 讀的那一個）。
* `retention = exact / original_exact`（原順序為 0 時 `None`）：**順序保留率**。

另外，擬合段的配對讀數改成 `minimal_order_pairs`（`counterfactual_pair_report(..., suffix="_ro")`）：
兩份拷貝的正解相同，所以 `targets_differ` **依設計是 0**，而 `same_prediction` 是**想要的不變量**
（同一個結構、兩種順序 → 應該給同一個答案）。它與 §61/§62 的 `_cf` 配對語意相反，因此分開記、分開讀。
M3 接受 `minimal_pairs` 或 `minimal_order_pairs` 任一。

**M5 的門檻仍照 §63 登記（反轉後 exact ≥ 0.80，M1 不過時 `None`）**，但 §64 的分支**不**用它的絕對地板
當觸發條件：M2 在 chance 附近時，反轉後不可能達到 0.80（除非反轉恰好把錯的變對）。這一節的分支讀
**M1**（在順序擴增下是否擬合）、**M2**（留出是否高於 chance）與 **retention**（擬合是不是真的順序不變）。

### 64.4 門檻（跑之前寫定；M1／M2 與 §62／§63 完全相同，不因結果放寬）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| M1 | 宣告的 400 項 train exact **≥ 0.90** | 擬合先活下來；在順序擴增下位置規則上限 0.5，所以這是真的綁定門檻 |
| M2 | 留出 exact 的 **95% Wilson 下界 > 0.5** | 高於 2 人名冊的均勻猜 |
| M3 | 擬合配對（`minimal_order_pairs`）與留出配對的讀數**已記錄** | 機制讀數，不是分數 |
| M4 | 成本（參數、秒、步數、`updates_per_session`）已記錄 | — |
| M5 | 留出名冊順序反轉、正解不動，exact **≥ 0.80**；M1 不過時 `None` | 位置對照（沿 §63 登記） |

### 64.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| M1 | **0.90–1.00（偏過）** | §63 的擬合段已經是 391/400，且配對 194/200 給不同答案（它在訓練段確實讀名冊）；§64 只剩 200 個不同的 `(對應, 兇手)`，每個看兩次，記憶量更小 |
| M2 | **不過，0.40–0.50** | 順序擴增不增加任何「沒見過的結構」的資訊；而且 §63 的 400 項是 400 個不同的名字對，§64 只有 200 個不同對各看兩次，**多樣性反而減半**，留出更可能停在 chance 或以下 |
| `original_exact` | 0.35–0.50 | 與 §63 的 0.4250 同一個形狀（同一個留出集、同一個 checkpoint 大小） |
| `retention` | **0.85–1.00**（若 M1 過） | 若 M1 過，模型必須對同一個結構的兩種順序給同一個答案，反轉後自然不會掉；若 M1 不過，retention 才是診斷主角 |
| M3 | `targets_differ` **0**（依設計）；`same_prediction` 0.90–1.00（若 M1 過） | 兩份拷貝的正解相同；擬合若成立就該同答 |
| M4 | 記錄 | — |

**關鍵的不對稱**：若 M1 不過而 `original_exact` 高、反轉後低（retention 低），那是**順序偏好連訓練都
消不掉**；若 M1 不過而兩邊都 ~0.5，那是**這個載體在 200 對 × 2 順序下根本沒擬合**（不是位置問題）。
這兩種結果的下一步不同，所以 retention 必須與 M1 一起讀。

### 64.6 這一節**不會**證明什麼

* 不是能力分數（核心分不變 0.00/10）；不是「學會了綁定」的證明。
* 只有 200 個不同的 `(對應, 兇手)` 對（各看兩次），比 §63 的 400 個不同對更少；留出仍是 200 段。
* 單一 seed；CPU；單一任務；單一讀出；2 人名冊的 chance 是 0.5。
* **語料與目標函數仍同時偏離 §61**（`--aux-mode resolvable`，§62.2 已登記的混淆）→ 診斷，不是歸因臂。
* M5 的 `exact` 仍記錄，但它在 M2 ≈ chance 時沒有資訊量；這一節的結論**不**建立在它的地板上。

### 64.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --gate-prefix M --device cpu --out data/pantry_stage/ord_arm
./.venv/bin/python scripts/train_pantry_deduction.py --check <report>.json
```

### 64.8 這一節的地位

§63 證明了語料沒有殘留的位置線索，但也暴露了一件事：**「擬合得到綁定」與「答案不隨順序改變」是兩個
不同的性質**。§64 只改訓練的呈現方式（每個結構看兩種順序），把「位置規則」從擬合的可能性裡移除，
藉此分辨「模型學到的是對應」與「模型學到的是某種順序習慣」。沒有加 epoch、寬度、段數或新目標。

### 64.9 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| M1 不過、`original_exact` 明顯高於反轉後（retention < 0.5） | 順序偏好**連在訓練集裡被兩種順序直接矛盾都消不掉**：讀出層把位置當成答案 | **讀出／狀態探針**：在名冊那一輪抓 state，只換名冊文字、不改其他輸入，看輸出頭是否真的看到名冊；**不得**加 epoch／寬度／段數 |
| M1 不過、兩邊都 ~0.5 | 不是位置問題：這個載體在 200 對 × 2 順序下沒擬合 | **單段梯度檢查**（§63.9 的第一列）：一組 `(結構, 順序配對)`，同樣損失與步數，看 loss 是否下降、兩個答案是否分開 |
| M1 過、M2 不過 | 擬合是真的綁定（位置已在語料層被中和），但不轉移到留出 | **容量曲線**（2／3／4／5 人，同一個預算）；這是 §63.9 那一列現在才可達的原因 |
| M1 + M2 過 | 最小負載下綁定、順序不變、且轉移到留出 | **容量曲線往上**（2→3→4→5 人，同一個預算）；**仍不是能力分數** |


### 64.10 結果（2026-11-15，依 §64.7 的指令跑完）

| 讀數 | 值 |
| --- | --- |
| M1 train exact（**宣告的 400 項全部**） | **1.0000**（400/400，Wilson 0.9905–1.0000） |
| M1 train exact（`train_fit`，前 200 項＝原順序） | 1.0000（200/200） |
| **擬合順序配對**（`minimal_order_pairs`） | 200 組、`same_prediction` **200/200**、`both_correct` **200/200**、`targets_differ` 0（依設計） |
| M2 留出 exact（200 段） | **0.2650**（53/200，Wilson **0.2087–0.3302**） |
| chance | 0.5（2 個演員） |
| 留出 ranking | 0.4950（99/200） |
| 留出「預測落在本段名冊內」 | 111/200 = **0.5550**（不管內容的期望 0.1667）；**89/200（44.5%）答了名冊外的名字** |
| `reset` | 0.0600（12/200，單一預測 `Ivan`） |
| `no_bounds` | 0.2650（此語料沒有時間濾網，與 `full` 相同） |
| `skip_al` | 0.2600（52/200） |
| 留出配對（`_cf`，診斷） | 200 組、`same_prediction` **70**（35%）、`both_correct` **15**、structure 53、twin 65 |
| 留出配對（換名，`minimal_heldout_twins`） | 65/200 = 0.3250（Wilson 0.2639–0.3927） |
| **M5** 名冊順序反轉 | exact **0.2850**（57/200）；`original_exact` **0.2650**、**`retention` 1.0755**；`follows_second_entry` 64/200 |
| 參數／步數／秒 | 168,150 ／ 10,000 ／ **1,784.4** |
| 語料 digest | train `416a8a68…`（順序擴增）、heldout `69c730e1…`（與 §63 相同，留出未動） |

四條門檻：**M1 PASS**、**M2 FAIL**、**M3 已記錄**、**M4 PASS**、**M5 FAIL**。依 §64.9 的對應列：

> **「M1 過、M2 不過 → 容量曲線（2／3／4／5 人，同一個預算）」**

**這一節得到的是本輪最乾淨的一個正面讀數，和一個更差的留出。**

1. **擬合是真的綁定，而且順序不變。** §64 的語料讓「答第 N 格」的擬合上限變成 0.5：同一個結構的
   兩份拷貝把兇手放在相反的格子裡。模型拿到 **400/400**，而且 200 組順序配對**全部同答、全部兩份
   都對**。這是 §62（位置捷徑）、§63（擬合靠名冊但留出有順序偏好）之後第一次有「擬合段不可能靠
   位置過關、而它仍然過關」的證據。§64.5 預測 M1 0.90–1.00，**命中**。
2. **順序偏好在擬合段被消掉了。** §63 的 checkpoint 在留出上的 retention 是 **0.7294**（原 0.4250、
   反轉 0.3100）；§64 是 **1.0755**（原 0.2650、反轉 0.2850）。§64.5 預測 retention 0.85–1.00，
   **命中**（略高於 1 是 200 題的噪音）。
3. **但留出更差，而且低於 chance。** M2 **0.2650**（Wilson 上界 0.3302）比 §63 的 0.4250 低，
   §64.5 預測 0.40–0.50，**在低側落空**。原因是可分解的：**89/200（44.5%）的答案根本不在這兩人的
   名冊裡**（12 個名字的詞表），另外 58 次答了名冊裡的另一個名字、53 次答對；名冊內答對率
   53/111 = 0.477，與 2 選 1 的 0.5 沒有差別。也就是說，它不是「把對應學反了」，而是**沒見過的
   結構上，輸出頭不再被名冊約束**：它仍然偏好名冊內的名字（0.5550 ≫ 0.1667），但在兩人之間不區分，
   其餘時間吐訓練集的常見名字。
4. **M5 的 `retention ≈ 1` 不能單獨讀成「順序不變」**：在平衡語料上，一個純位置規則的整體正確率
   在反轉前後也一樣（只是把「哪一半是第 1 格」換過去）。真正排除位置的是**擬合的 `both_correct`
   200/200**——純位置規則在每組配對只能對一份（上限 0.5）。所以這一節的「順序不變」是**擬合段**
   的性質，不是留出段的性質。留出段的 `follows_second_entry` 64/200 也顯示它仍偏後面的格子
   （正解在第 0 格 0.16 vs 第 1 格 0.37），只是在平衡語料上整體正確率不隨反轉改變。

**照實記的三個限制**：（a）§64 的訓練集只有 **200 個不同的 `(對應, 兇手)` 對**（各看兩次），
§63 有 400 個不同對（換名配對）——多樣性減半，這正是留出可能更差的原因之一，因此**不能**把
0.2650 讀成「順序擴增讓模型變差」；（b）留出仍是 200 段、單一 seed、CPU、單一讀出；（c）核心分
不變 **0.00/10**，這一節是診斷。

**機械分支**：M1 過、M2 不過 → **容量曲線**（2／3／4／5 人，同一個預算）。§63.9 當時把這一列
列為「M1 + M5 過、M2 不過」的下一步；§64 把位置從擬合裡移除之後，這個條件以更強的形式成立
（擬合段 200/200 兩份都對），所以照登記走。**注意**：k=2 已經不過，容量曲線的用途是**界定**
失敗（每一個 k 都不轉移），不是去找一個會過的格子；若某個 k 反而過，那才是意外，必須先查語料。


## 六十五、階段 CAP：容量曲線（2026-11-15，量測前寫定）

### 65.1 為什麼要掃名冊大小

§64 把「擬合」這一關清乾淨了：順序擴增讓「答第 N 格」的擬合上限變成 0.5，而模型仍然拿到 400/400，
200 組順序配對全部同答且兩份都對。但留出 **0.2650**、**44.5% 的答案不在名冊裡**、名冊內答對率 0.477
＝ 2 選 1。於是問題只剩一個形狀：**這是「2 人名冊太小／太擠」，還是「不管幾個人都不會轉移」？**

§64.9 的機械分支因此登記為**容量曲線**：同一個語料家族（§64 的順序擴增）、同 400 項、同 10,000 步、
同一個目標函數、同一個讀出，只把名冊的人數從 2 換成 3／4／5（chance 1/k）。

**這不是「找一個會過的格子」**：k=2 已經不過，而且低於 chance。曲線的用途是**界定**失敗——如果每一格
都不轉移，「名冊太小」就被排除；如果某格反而過，那是意外，必須先稽核語料（見 65.9）。

### 65.2 語料（`MINIMAL_ROSTER_SIZES`、`_minimal_session(..., roster_size=)`）

* 產生器新增 `roster_size`：`rng.sample(ACTORS, k)` 取 k 人（同一個順序、同一個取法），
  `rng.sample(sorted(COLOURS), k)` 取 k 個值，`values[0]` 是 live 值，其餘是 dead 值。
* 兇手（live 值的主人）**輪流放在 `index % k` 格**，所以每一格約 `n / k` 次；驗證器要求
  「各格次數 max−min ≤ 1」，固定格子規則的上限是 **1/k**（k=2 時與 §63 的對半相同）。
* 配對仍是 `_ro`（順序反轉）而不是 `_cf`（換名字），所以訓練集仍是 200 個結構 × 2 順序＝400 項，
  留出仍是 200 結構 + 200 換名配對。**名冊有 k 個條目時整份反轉**（`dict(reversed(...))`）。
* `minimal_twin()`（留出用）原本寫死「交換 names[0] 與 names[1]」，在 k>2 時**不一定改變答案**
  （兇手可能在第三格）。改成「把兇手換成名冊中第一個不是兇手的人」，k=2 的輸出與原本逐位元組相同。
* **k=2 必須逐位元組不變**：`_minimal_session` 的 RNG 呼叫順序、`mapping` 的插入順序在 k=2 時
  與 §63／§64 完全相同，`train_digest` 仍是 `416a8a68…`（順序擴增）、`heldout_digest` 仍是
  `69c730e1…`；§63 的 `ad5cb3bf…` 也仍然重現（測試守住，見 65.6）。

### 65.3 讀數

與 §62–§64 完全相同（M1–M5、`full`／`reset`／`no_bounds`／`skip_al`、`in_roster_exact`、
`ranking`、`top_share`、配對讀數、順序保留率），另外每份報告記 `corpus.minimal_roster_size` 與
`corpus.minimal_binding_chance = 1/k`，`minimal_roster_permutation` 記 `roster_size` 與
`follows_last_entry`（k=2 時 `follows_second_entry` 是同一個數字，舊鍵保留給 §62–§64 的報告）。

**M2 的門檻不需要改一個字**：`_stage_m_gate_values` 讀的是 `results.full.chance`，而 `summarise()`
用 `1/row["actors"]` 算 chance——k 由語料自己決定，所以 0.5 → 1/k 是自動的（測試守住）。

### 65.4 門檻（跑之前寫定）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| M1 | 每一格的 400 項 train exact **≥ 0.90** | 擬合先活下來；順序擴增下固定格子規則上限 0.5 |
| M2 | 每一格留出 exact 的 **95% Wilson 下界 > 1/k** | 高於該格自己的均勻猜 |
| M3 | 擬合順序配對 `minimal_order_pairs` 與留出配對**已記錄** | 機制讀數，不是分數 |
| M4 | 成本（參數、秒、步數、`updates_per_session`）已記錄 | — |
| M5 | 留出名冊順序反轉、正解不動，exact **≥ 0.80**；M1 不過時 `None` | 沿 §63／§64 登記；**不是本節的分支觸發條件** |

### 65.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| M1（k=3／4／5） | **每格都過，0.95–1.00** | §64 在同一個預算下 400/400；k 只把輸出頭的候選從 2 個換成 k 個，而名冊是文字裡的逐字對應，擬合段記得住 |
| M2（k=3） | **不過，0.15–0.30**（chance 0.3333） | §64 在 k=2 是 0.2650（chance 0.5），而且 44.5% 答名冊外；沒有理由 k=3 會轉移 |
| M2（k=4） | **不過，0.10–0.22**（chance 0.25） | 同上，候選變多、名冊內的 1/k 更小 |
| M2（k=5） | **不過，0.08–0.18**（chance 0.2） | 同上 |
| `in_roster_exact` | 每格 **0.35–0.55**，且**不隨 k 上升到 1** | §64 的 0.477；若它隨 k 上升，代表模型學會「從名冊裡挑」但仍不挑對的人 |
| `retention` | **0.90–1.10**（M1 過的格） | 平衡語料上，順序不變是擬合的性質（§64 是 1.0755） |
| `follows_last_entry` | **低於 1/k** | 它偏好後面的格子，但在平衡語料上不是固定格子規則 |
| M3 | `targets_differ` **0**（依設計）；`same_prediction` 0.90–1.00 | 兩份拷貝正解相同 |
| M4 | 記錄 | 每格約 1,800 s（與 §64 同一個預算） |

**關鍵的形狀**：如果三格的 exact 大致是 chance 的固定比例（例如 0.5×chance），那是「輸出頭合法但
內容自由」；如果 exact 隨 k **上升**、而 `in_roster_exact` 不動，那是「候選變多反而更容易猜中名冊內
的名字」（1/k 的算術，不是能力）。兩種讀法都要寫出來，不能只報最高那格。

### 65.6 這一節**不會**證明什麼

* 不是能力分數（核心分不變 0.00/10）；不是「學會了綁定」的證明。
* **k=2 不重跑**：§64 的語料 digest 與這一節的 k=2 逐位元組相同（測試守住），重跑只會再花 ~1,800 s
  重現 0.2650。這是**跳過已知結果**，不是跳過難看的一格——那一格已經登記在 §64.10，而且比 chance 差。
* 單一 seed；CPU；單一任務；單一讀出；每格只有 200 個留出結構。
* 語料與目標函數仍同時偏離 §61（`--aux-mode resolvable`，§62.2 已登記的混淆）→ 診斷，不是歸因臂。
* 曲線**不能**分辨「容量不足」與「這個載體根本沒有把名冊放進 state」；那是 65.9 的下一列。

### 65.7 指令（每一格一次；k=2 不重跑）

```
for k in 3 4 5; do
  PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
      --train-sessions 400 --epochs 200 --core turnstore \
      --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
      --roster-size $k --gate-prefix M --device cpu --out data/pantry_stage/k${k}_arm
  ./.venv/bin/python scripts/train_pantry_deduction.py --check \
      $(ls -t data/pantry_stage/k${k}_arm/*.json | head -1)
done
```

### 65.8 這一節的地位

§64 把「擬合是綁定、而且順序不變」釘住了，但留出比 chance 差。§65 只問一件事：**那是 2 個人太小，
還是不管幾個人都不轉移？** 它不改語料家族、不改步數、不改目標、不改讀法，只改名冊長度（以及由它
決定的 chance）。所以它得到的不是新能力，而是**失敗的邊界**：在哪一個 k 上，擬合還在、轉移仍不在。

### 65.9 分支（跑之前寫定，機械決定下一步）

| 結果 | 讀法 | 下一步 |
| --- | --- | --- |
| 某一格 **M1 不過**（其他格過） | 擬合本身在該 k 上就撐不住：這是**擬合容量**的上限，不是轉移 | 回報曲線並**停止加格子**；**不得**用加 epoch／加大寬度去「補回」那一格 |
| M1 全過、**M2 全不過** | 綁定在每一種名冊大小上都只是**擬合**，不轉移 → 「名冊太小」被排除 | **讀出／狀態探針**：在已訓練的 k=2 與 k=5 checkpoint 的名冊輪抓 state，只換名冊文字（換順序、換名字、換人數），看輸出頭是否真的讀到 mapping；**不新增訓練預算** |
| M1 全過、**M2 某一格過**（Wilson 下界 > 1/k） | 先**稽核語料**（每格 slot 次數、名字分布、`(live 值, 兇手)` 重疊、答案元組唯一性），並確認該格沒有被別的機制解釋（例如 k 大時 1/k 門檻下降） | 稽核乾淨才回報「第一個有轉移的 rung」；再把曲線往上（6／8 人），**仍不是能力分數** |
| M1 全過、M2 全過 | 同上，但先查是否只是 **chance 變小**：比較 exact 與 1/k 的比值是否與 k=2 的 0.53 同一個數量級 | 若比值不變 → 「低於 chance 的比例常數」被證實，回報為**負結果**；若比值上升 → 稽核語料後再往上掃 |


### 65.10 結果（2026-11-15，依 §65.7 跑完 k=3／4／5；k=2 不重跑）

每一格都是同樣的 400 項、10,000 步、同一個目標與讀法，只差名冊人數（chance 1/k）：

| 讀數 | k=2（§64，不重跑） | k=3 | k=4 | k=5 |
| --- | --- | --- | --- | --- |
| M1 擬合（400 項） | 1.0000 | **0.9750**（390/400，Wilson 0.9546–0.9895） | **0.9725**（389/400，0.9514–0.9872） | **0.9750**（390/400，0.9546–0.9895） |
| chance | 0.5000 | 0.3333 | 0.2500 | 0.2000 |
| **M2 留出 exact** | 0.2650 | **0.1900**（38/200） | **0.0950**（19/200） | **0.1300**（26/200） |
| M2 Wilson 區間 | 0.2087–0.3302 | 0.1417–0.2500 | 0.0617–0.1436 | 0.0903–0.1837 |
| **exact / chance** | 0.530 | 0.570 | 0.380 | 0.650 |
| 留出 ranking | 0.4950 | 0.3550 | 0.2050 | 0.2650 |
| 預測落在名冊內 | 111/200 = 0.555 | 110/200 = 0.550 | 100/200 = 0.500 | 90/200 = 0.450 |
| 不管內容的期望（k/12） | 0.167 | 0.250 | 0.333 | 0.417 |
| **名冊內正確率** | 53/111 = 0.477 | 38/110 = 0.345 | 19/100 = 0.190 | 26/90 = 0.289 |
| 名冊外答案 | 89 | 90 | 100 | 110 |
| 擬合順序配對 `same_prediction` | 200/200 | 192/200 | 197/200 | 190/200 |
| 擬合順序配對 `both_correct` | 200/200 | 191/200 | 193/200 | 190/200 |
| `targets_differ` | 0 | 0 | 0 | 0 |
| 留出換名配對（`_cf`）同答 | 70/200 | 63/200 | 105/200 | 142/200 |
| 留出換名配對 `both_correct` | 15 | 9 | 2 | 2 |
| 留出 twins exact | 0.3250 | 0.2050 | 0.1400 | 0.0950 |
| 順序反轉後 exact | 0.2850 | 0.2050 | 0.0800 | 0.1250 |
| `retention` | 1.0755 | 1.0789 | 0.8421 | 0.9615 |
| `follows_last_entry` | 64/200 | 66/200 = 0.330 | 27/200 = 0.135 | 38/200 = 0.190 |
| `reset` | 0.0600 | 0.1050 | 0.0550 | 0.0750 |
| 參數／步數／秒 | 168,150／10,000／1,784.4 | 168,150／10,000／1,748.4 | 168,150／10,000／1,672.9 | 168,150／10,000／1,764.4 |
| 語料 train digest | `416a8a68…` | `838a1a35…` | `0dd8ed32…` | `d6ca78a8…` |

四條門檻的結果在**每一格都一樣**：**M1 PASS、M2 FAIL、M3 已記錄、M4 PASS、M5 FAIL**。
依 §65.9 的對應列：

> **「M1 全過、M2 全不過 → 綁定在每一種名冊大小上都只是擬合，不轉移 → 讀出／狀態探針」**

#### 一、預測對照（跑之前寫在 §65.5）

| 預測 | 實際 | 判定 |
| --- | --- | --- |
| M1 每格都過，0.95–1.00 | 0.9750／0.9725／0.9750 | **命中** |
| M2 k=3 在 0.15–0.30 | 0.1900 | **命中** |
| M2 k=4 在 0.10–0.22 | 0.0950 | **落空（低側，差 0.005）** |
| M2 k=5 在 0.08–0.18 | 0.1300 | **命中** |
| `in_roster_exact` 0.35–0.55 且**不隨 k 上升** | 0.550 → 0.500 → 0.450 | **命中**（而且是下降） |
| `retention` 0.90–1.10 | 1.0789／0.8421／0.9615 | k=3、k=5 命中；**k=4 落空（0.8421）** |
| `follows_last_entry` 低於 1/k | 0.330（1/3=0.333）、0.135（0.25）、0.190（0.2） | **命中**（三格都低於或等於） |
| M3 `targets_differ` 0、`same_prediction` 0.90–1.00 | 0；0.96／0.985／0.95 | **命中** |

#### 二、這一節的答案：**「名冊太小」被排除**

1. **擬合在每一格都成立，而且擬合段仍然順序不變。** 400 項的擬合是 0.9750／0.9725／0.9750，
   順序配對 190–197/200 同答、190–193/200 兩份都對，`targets_differ` 依設計是 0。所以每一格都是
   「讀名冊對應」的擬合，不是位置規則（位置規則在平衡語料上上限 1/k）。
2. **留出在每一格都低於該格自己的 chance**，而且 `exact / chance` 沒有趨勢：0.530（k=2）→ 0.570 →
   0.380 → 0.650。曲線**沒有**隨名冊變大而改善，也沒有系統性地變差；它是同一個比例的噪音。
   0.0950 是四格最低，但 200 題的 Wilson 區間（0.0617–0.1436）與 k=5 的（0.0903–0.1837）重疊，
   所以**不能**說「4 個人最難」。
3. **真正隨 k 變化的是「答案落在名冊裡的比例」。** 0.555 → 0.550 → 0.500 → 0.450，而不管內容的
   期望是 0.167 → 0.250 → 0.333 → 0.417：**領先幅度 0.388 → 0.300 → 0.167 → 0.033**。
   也就是說，名冊越大，模型越不去看名冊——到 k=5 時它的答案落在名冊裡的比例幾乎等於從 12 個名字裡
   亂抽。這是本節最乾淨的讀數：**不是「容量不夠」，是「名冊對輸出的約束隨候選變多而消失」**。
4. **名冊內正確率從來沒有超過 chance**：0.477（1/2）→ 0.345（1/3）→ 0.190（1/4）→ 0.289（1/5）。
   在名冊內的 90–111 次猜測裡，它選對人的比例等於或低於亂猜。所以「有讀名冊、只是挑錯人」這個
   較溫和的解釋也不成立。
5. **留出換名配對的同答率隨 k 上升**（70/200 → 63 → 105 → 142）：名冊越大，它越常對「只差名冊
   兩格」的兩題給同一個答案——與第 3 點同一個機制的另一面（忽略名冊，答案就只由其餘文字決定）。
6. **位置偏好不穩定**：k=3 偏好最後一格（24/67）、k=4 也是最後（8/50）、k=5 卻偏好第一格（8/40）。
   沒有跨格一致的格子規則，所以「換一個 k 就換一個位置捷徑」不成立。

#### 三、照實記的限制

* k=2 **不重跑**：語料與 §64 逐位元組相同（測試守住），重跑只會重現 0.2650。§64 的數字直接列進
  上表，並註明來源。
* 單一 seed、CPU、單一讀出、單一任務；每格 200 個留出結構，Wilson 區間寬約 ±0.05（k=4 時 ±0.04）。
* `exact/chance` 的 0.380（k=4）與 0.650（k=5）相差很大，但兩者的區間重疊，**不足以**支撐任何
  「k 越大越好」或「k 越大越差」的單調敘述。
* 語料與目標函數仍同時偏離 §61（`--aux-mode resolvable`），所以這仍是**診斷**，不是歸因臂。
* 這一節**不能**分辨「名冊沒有進 state」與「名冊進了 state 但讀出頭不用它」——那正是 §65.9 下一列
  的探針要量的事。
* 核心分不變 **0.00/10**；這一節不是能力分數。

#### 四、機械分支

**M1 全過、M2 全不過** → 下一步是**讀出／狀態探針**：在已訓練的 k=2 與 k=5 checkpoint 上，於名冊
那一輪抓 state，只換名冊文字（換順序、換名字、換人數），看輸出頭是否真的讀到 mapping；
**不新增訓練預算**（不加 epoch、不加寬度、不加段數）。



## 六十六、階段 ORD-2：讀出／狀態探針（2026-11-15，量測前寫定）

### 66.1 為什麼是這一支

§65.10 的機械輸出是：k=3／4／5 每一格 **M1 過、M2 不過**，而且 `exact/chance` 沒有趨勢
（0.570／0.380／0.650，k=2 是 0.530）。真正隨 k 變化的是**名冊對輸出的約束**：答案落在名冊裡的比例
0.555→0.550→0.500→0.450，而不管內容的期望是 0.167→0.250→0.333→0.417，領先幅度從 0.388 掉到
0.033；名冊內正確率也從未超過 chance（0.477／0.345／0.190／0.289）。

§65.9 對這一格登記的下一步是**讀出／狀態探針**：在已訓練的 k=2 與 k=5 checkpoint 上，只換名冊文字，
看輸出頭是否真的讀到 mapping；**不新增訓練預算**。這一節就是那支探針，而且它要在跑之前把「讀到哪裡」
與「在哪一層丟掉」寫清楚，否則量完只會得到另一組可以任意解釋的餘弦。

### 66.2 量什麼（三層 × 三種編輯 + 一個參考分布）

對每一個留出 session，只改名冊那一輪（`roster_turn`，§62 起固定是第 2 輪），重跑整段，然後在**答案邊界**
讀三層：

| 層 | 量 | 為什麼 |
| --- | --- | --- |
| 控制器 | `h` 的餘弦／相對 L2 | 名冊的影響有沒有傳到答題時的迴路狀態 |
| 讀出 | `core.read_vector` 的餘弦／相對 L2 | 輸出頭**實際被餵到**的內容（`token_logits = head([h, read])`） |
| 存放 | 答案邊界上 `k`／`v` 槽的相對 L2 | 「從來沒寫進去」與「寫了但答題時不讀」是兩件事 |

以及**行為層**：對 12 個語料名字逐一算「名字＋換行」的序列對數似然（與 `rank_actor` 同一條路徑），
取該 session 名冊內的 argmax，量它有沒有跟著 mapping 走。

三種編輯（同一批留出 session）：

* `identity`：不改，重跑。R1 必須逐欄重現報告的 `results.full`。
* `twin`（§62 的換名配對）：正解翻成另一個人，證據值不動。
* `reorder`（§64 的順序配對）：mapping 不動，名冊條目反序，正解不動。
* `mismatch`（**參考分布，不是編輯**）：第 *i* 題的答案邊界對第 *i+1* 題的。它給「兩題完全無關」時的
  餘弦，讓「名冊只是小擾動」有一把量出來的尺，而不是靠 0.99 這個數字自己說。

### 66.3 程式與重用

* 新檔 `scripts/probe_pantry_readout.py`（`--report` 讀已訓練報告、`--check` 機械重驗）。
* 重用 `train_pantry_deduction.py` 的 `run_session`（`boundaries` 鉤子）、`evaluate`（R1 的生產路徑）、
  `summarise`、`generate_bytes`、`_slice`／`_decode_view`、`candidates_tokens`、`_chunks`，以及
  `gen_pantry_ecosystem.py` 的 `minimal_twin`、`minimal_order_twin`、`derive`、`_all_asserts`。
* 名字分數的迴圈與 `rank_actor` 逐字相同（只多回傳每個名字的分數），並有一條測試要求兩者的 argmax
  在同樣的 boundary 上一致——否則探針量的不是生產路徑的讀出。
* 只讀 checkpoint（`weights_hash` 與檔案 sha256 前後比對），不寫入任何被量的環境；輸出只寫 `--out`。

### 66.4 門檻（跑之前寫定）

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| **R1** | `identity` 重跑的 `summarise(evaluate(..., "full"))` 與報告 `results.full` 的 14 個欄位**逐欄相等** | 儀器檢查：語料／checkpoint 配對正確，否則後面全部不讀 |
| **R2** | 每一組編輯只改 `roster_turn` 這一輪、輪數不變；`twin` 的 `derive()` 等於 twin 正解且不等於原正解、名冊成員不變；`reorder` 的 `derive()` 等於原正解。違規數 **0** | 編輯是外科手術，不是換了一題 |
| **R3** | 見 66.9 的分叉（`READ_COS_STATIC = 0.99`、`STORE_WRITTEN = 0.01`、`FOLLOWS_MAPPING = 0.50`） | 這是**發現**，不是通過／不通過 |
| **R4** | 成本（session 數、變體數、秒、參數）已記錄；`weights_hash` 與 checkpoint sha256 前後相同 | 探針沒有改動模型 |

0.99 是一個**先寫定的診斷切點**，不是自然常數。所以報告同時給出 `min/p25/median/p75/max` 與
「低於 0.90／0.95／0.99／0.999 各有幾題」的敏感度表，讀者可以自己換切點重讀；分叉的結論必須在
同一組數字下可重算（`--check` 會用儲存的數字重跑 `branch()`）。

### 66.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| R1 | **逐欄相符** | 同一份語料、同一個 checkpoint、CPU 決定性 |
| R2 | **0 違規** | 兩種配對都是既有的產生器函式，§63／§64 已用過 |
| `read_cos_roster` 中位數 | **< 0.99**（兩個變體、兩個 k） | 名冊文字真的變了，名冊那一輪的讀出一定不同 |
| **`read_cos_final` 中位數** | **≥ 0.99**（兩個變體、兩個 k）→ **R3a** | 答案邊界還隔著證據輪與提問輪；§65 的名冊約束随 k 衰減，預期答題時的讀出幾乎不變 |
| `store_v_rel_final` 中位數 | **≥ 0.01** → **R3a-stored-not-read** | 名冊那一輪的寫入應該有進去，只是答題時不讀它 |
| `moved_to_twin_target` | 與 identity 的名冊內正確率相差 **±0.05 以內**（k=2 ≈ 0.265、k=5 ≈ 0.130） | 若答題時的讀出沒變，換名與否對頭來說是同一題 |
| `same_prediction`（twin vs identity） | k=2 **0.30–0.45**、k=5 **0.60–0.80** | §65 的留出換名配對同答率是 70/200＝0.35、142/200＝0.71 |
| `mismatch` 的 `read_cos_final` 中位數 | **低於 twin 的** | 兩題完全無關時狀態應該差更多；若反而更高，代表狀態根本沒有 session 特異性 |
| `reorder` 的 `follows_last_entry` | **0.10–0.60** | §65 已量到沒有跨 k 一致的位置規則，這裡不應該冒出 1.0 |

**最可能落到的分支**：R3a-stored-not-read（讀出在答題時不看名冊槽）。這不是「名冊太小」，也不是
「沒寫進去」，而是**答題那一輪的 query 沒有去要名冊那一輪的內容**——對應的修法是讀／query 路徑，
不是加 epoch、加寬度或加段數。

### 66.6 這一節**不會**證明什麼

* 不是能力分數；核心分不變 **0.00/10**。
* 只探 k=2 與 k=5 兩個已訓練 checkpoint（§64 與 §65），k=3／k=4 不重跑：分叉只需要「最小」與
  「最大」兩個名冊，重跑其餘兩格是重複。
* 餘弦是**診斷**，不是因果：`read_cos` 高不代表名冊一定不在別處，只代表**答題時餵給頭的向量**沒變。
  `store_v_rel` 就是為了把這個區別量出來。
* 單一 seed、單一讀出、單一任務；200 題；`--aux-mode resolvable` 的混淆仍在（§62.2）→ 診斷，不是
  歸因臂。
* `mismatch` 是循環位移（第 *i* 題對第 *i+1* 題），不是獨立抽樣的配對；它只給一個量級，不是檢定。
* 探針不改任何門檻、不改評測題、不在留出上調參。

### 66.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_readout.py \
    --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \
    --out data/pantry_stage/probe66/k2.json
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_readout.py \
    --report data/pantry_stage/k5_arm/pantry_deduction_20261115-033310.json \
    --out data/pantry_stage/probe66/k5.json
./.venv/bin/python scripts/probe_pantry_readout.py --check data/pantry_stage/probe66/k2.json
./.venv/bin/python scripts/probe_pantry_readout.py --check data/pantry_stage/probe66/k5.json
```

### 66.8 這一節的地位

§64 證明擬合是順序不變的綁定；§65 排除「名冊太小」。§66 只問一件事：**那份綁定在答題的時候，
有沒有被端到輸出頭面前？** 三個層次（控制器／讀出／存放）與一個無關配對的參考分布，是為了讓
「沒有」可以再分成三種不同的「沒有」，各自指向不同的修法。它不改語料、不改步數、不改模型。

### 66.9 分叉（跑之前寫定，機械決定下一步）

先看儀器，再看發現：

| 條件 | 編號 | 讀法 | 下一步 |
| --- | --- | --- | --- |
| **R1 不符** | — | 語料／checkpoint 配對錯了，或生產路徑改了 | 修探針；**不得**讀任何 R3 數字 |
| **R2 有違規** | — | 編輯不是只動名冊那一輪 | 修編輯；**不得**讀任何 R3 數字 |
| `read_cos_final` 中位數 **≥ 0.99**（兩個變體）且 `store_v_rel_final` **≥ 0.01** | **R3a-stored-not-read** | 名冊寫進去了，答題時的讀出幾乎不變：**寫了但沒被讀** | 讀／query 路徑（讓答題那一輪去要名冊那一輪的內容），**不是**加訓練預算 |
| `read_cos_final` 中位數 **≥ 0.99** 且 `store_v_rel_final` **< 0.01** | **R3a-not-stored** | 連槽內容都沒怎麼變：名冊那一輪沒有進入載體 | 寫入路徑（write gate／slot 分配），**不是**加訓練預算 |
| `read_cos_final` 中位數 **< 0.99** 且 `moved_to_twin_target` **< 0.50** | **R3b-head-ignores** | 內容在 state 裡，輸出頭不用它 | 讀出（名冊限定的選擇頭），**不是**加訓練預算 |
| `read_cos_final` 中位數 **< 0.99** 且 `moved_to_twin_target` **≥ 0.50** | **R3c-follows-but-wrong** | 頭跟著換名走，但準確率仍在 chance 以下：方向或正規化錯了（位置／順序假象） | 先稽核選擇的方向與名冊順序的正規化，再談訓練 |

不論落到哪一格，**都不得**用「加 epoch／加大寬度／加段數」當下一步：這一節量的就是「再訓練也不會
改變的那一層」。



### 66.10 結果（2026-11-15，k=2 與 k=5 已訓練 checkpoint，CPU，不新增訓練）

#### 〇、先記一個實作 bug（跑完、記錄前修掉）

第一次跑出來的 `accuracy`／`moved_to_twin_target` 全是 **0.0**，原因不是模型，是探針自己的
`pick_all()` 把候選的**索引**轉成字串回傳（`str(index[position])`），於是每個「名字 == 名字」的比較
都恆假。R1／R2 不會抓到它，因為它們走的是 `summarise(evaluate(...))` 與語料，不經過 `pick_all`。

修法與**新增的儀器檢查**（都在寫下任何數字之前）：

1. `pick_all()` 回傳 `names[index[position]]`；
2. R1 增加第二半：探針自己的名冊 argmax 準確率必須等於報告的 `results.full.ranking_exact`
   （也就是生產路徑 `rank_actor` 的準確率）。第一次的 0.0 對 0.4950 就會在這裡被抓到；
3. `--check` 也驗這一條。

**門檻、語料、fork 規則都沒有改**；修正後兩個 checkpoint 都重跑，`--check` 都是 OK。上面那個
0.0 沒有被採用，也不放進任何表。

#### 一、讀數

| 讀數 | k=2（§64 checkpoint） | k=5（§65 checkpoint） |
| --- | --- | --- |
| R1（14 欄重現報告 + 名冊 argmax = `ranking_exact`） | **OK**（0.4950 = 0.4950） | **OK**（0.2650 = 0.2650） |
| R2（只改名冊輪） | **0 違規 / 200** | **0 違規 / 200** |
| 成本 | 2.56 s，168,150 參數，200 題 × 3 變體 | 2.86 s，168,150 參數，200 題 × 3 變體 |
| checkpoint 前後 | `weights_hash` 與 sha256 不變 | 同左 |
| `identity` 名冊 argmax 準確率 | 0.4950 | 0.2650 |
| `h_cos_final` 中位數（twin／reorder） | 1.0000／1.0000（min 1.0000） | 1.0000／1.0000（min 0.9991） |
| `h_rel_final` 中位數（twin） | 0.0000（max 0.0006） | 0.0000（max 0.0431） |
| **`read_cos_final` 中位數（twin）** | **0.8405** | **0.9938** |
| **`read_cos_final` 中位數（reorder）** | **0.8553** | **0.8105** |
| `read_rel_final` 中位數（twin／reorder） | 0.6004／0.5560 | 0.1198／0.6968 |
| **`store_v_rel_final` 中位數（twin／reorder）** | **0.6004／0.5560** | **0.1203／0.6968** |
| `store_k_rel_final` 中位數（twin） | 0.1818 | 0.0440 |
| `h_cos_roster` 中位數（twin） | 0.8051 | 0.9742 |
| `read_cos_roster` 中位數（twin） | 0.8390 | 0.9939 |
| `same_prediction`（twin vs identity） | 0.3500 | 0.7100 |
| `same_roster_argmax`（twin） | 0.5700 | 0.7700 |
| `argmax_flip_rate`（twin） | 0.4300 | 0.2300 |
| **`moved_to_twin_target`** | **0.4950**（chance 1/2） | **0.2300**（chance 1/5） |
| `stayed_on_original`（twin） | 0.5050 | 0.2150 |
| twin 的名冊 argmax 準確率 | 0.5050 | 0.2150 |
| reorder 的準確率／`kept_original_target` | 0.5300 | 0.2550 |
| reorder 的 `argmax_flip_rate` | 0.3750 | 0.5400 |
| reorder 的 `follows_last_entry` | 0.4700 | 0.1550 |
| `mean_abs_delta_roster`（twin） | 10.78 nats | 4.86 nats |
| `mismatch`：`read_cos_final`／`h_cos_final` | 0.4442／0.9870 | 0.5501／0.9999 |
| 敏感度：twin `read_cos < 0.99` 的題數 | 183/200 | 86/200 |

#### 二、預測對照（§66.5 寫在跑之前）

| 預測 | 實際 | 判定 |
| --- | --- | --- |
| R1 逐欄相符、名冊 argmax = `ranking_exact` | 0.4950/0.4950、0.2650/0.2650 | **命中**（第二半是修正後新增的儀器檢查） |
| R2 0 違規 | 0 / 200（兩個 k） | **命中** |
| `read_cos_roster` < 0.99 | 0.839／0.855（k=2）、0.8096（k=5 reorder） | 命中，**但 k=5 twin 是 0.9939（未 < 0.99）** |
| `read_cos_final` ≥ 0.99 → R3a | 0.8405／0.8553（k=2）、0.8105（k=5 reorder） | **落空** → 落到 R3b，不是 R3a |
| `store_v_rel` ≥ 0.01 | 0.60／0.56、0.12／0.70 | 量級命中，但前提（靜態讀出）不成立 |
| `moved_to_twin` 與 identity 準確率差 ±0.05 | 0.4950 vs 0.2650（+0.2300）、0.2300 vs 0.1300（+0.1000） | **落空**；但落到的正是 chance（0.5、0.2） |
| `same_prediction` k=2 0.30–0.45、k=5 0.60–0.80 | 0.35、0.71 | **命中** |
| `mismatch` 的 `read_cos` 低於 twin | 0.4442 < 0.8405、0.5501 < 0.8105 | **命中** |
| reorder 的 `follows_last_entry` 0.10–0.60 | 0.47、0.155 | **命中** |

兩個落空都要寫清楚：

1. **讀出不是靜態的。** 我預期答案邊界的 `read` 幾乎不變（≥ 0.99），實際是 0.84（k=2）與
   0.81（k=5 reorder）。名冊的內容**有**被端到輸出頭面前，而且差得不少（`read_rel` 0.56–0.70、
   `mean_abs_delta_roster` 4.86–12.08 nats）。
2. **`moved_to_twin` 不是「停在原答案」，是「在名冊裡換硬幣」。** k=2 是 0.4950、k=5 是 0.2300，
   正好是 1/k（0.5、0.2）；`stayed_on_original` 是 0.505／0.215。也就是說，換名之後頭會換答案
   （`argmax_flip_rate` 0.43／0.23），但換到誰**與 mapping 無關**——落在正解上的比例就是亂猜。
   我原本預期它會「不理編輯、停在原答案」，實際是「被編輯推動，但推的方向不是名冊說的方向」。
   這是 R3b 的更精確版本，不是另一個分支。

#### 三、這一節的答案：**內容在 state 裡，輸出頭不用它**（R3b）

三個層次分得很乾淨：

1. **`h` 從來不是載體。** `h_cos_final` 的中位數是 **1.0000**（k=2 最小值也是 1.0000；k=5 最小
   0.9991），`h_rel_final` 中位數 0.0000。更關鍵的是 `mismatch`：**兩題完全無關**時 `h_cos_final`
   仍是 0.9870（k=2）／0.9999（k=5）。答題那一輪的文字對每個 session 都一樣，處理完之後 `h` 幾乎
   只由那一輪決定，不帶 session 資訊。所以「`h_cos ≈ 1`」不能讀成「名冊不重要」——它讀成
   「`h` 本來就不裝這一題」。
2. **store 才是載體，而且確實被讀。** `store_v_rel` 是 0.60／0.56（k=2）、0.12／0.70（k=5），
   `read_cos_final` 是 0.84／0.86、0.99／0.81，而 `read_cos_roster` 幾乎一樣——名冊那一輪寫進去的
   內容差多少，答題時讀出來的就差多少。`read` 是 `token_logits = head([h, read])` 的另一半，
   所以**輸出頭真的看到不同的內容**。
3. **頭看到了，卻不照 mapping 選。** 名冊限定的 argmax 跟著換名走的比例是 0.4950／0.2300，
   正好是 1/k；identity 的準確率是 0.4950／0.2650，也在 chance 附近。同一個 `h`、不同的 `read`、
   分數確實移動了（`mean_abs_delta_roster` 10.78／4.86 nats），但贏家換成誰與「值是誰的」無關。

**k=5 的一個非對稱，照實記**：twin 的 `read_cos` 是 0.9938（86/200 題 ≥ 0.99），reorder 是 0.8105
（只有 22/200 ≥ 0.99）。若只拿 twin 判，k=5 會落到 R3a（讀出靜態）；登記的規則要求**兩個編輯都**
靜態才算，而 reorder 明顯在動，所以不是 R3a。這個差距本身有意義：k=5 的答題讀出對「哪個名字在
哪一格」幾乎不敏感，對「格子順序」敏感——位置痕跡，與 §65 的「名冊約束隨 k 衰減、沒有穩定格子規則」
同一個方向。但 reorder 改动的字元比 twin 多，這個非對稱有一部分是改動量，不能全讀成位置編碼。

#### 四、照實記的限制

* **餘弦是診斷，不是因果。** `read_cos` 高只代表「答題時餵給頭的向量相近」；`store_v_rel` 是為了把
  「沒寫進去」與「寫了沒讀」分開才量的。這一節沒有做任何介入（沒有改寫 store、沒有換 query），
  所以「把 read 修好就會對」是**下一個實驗的假設**，不是本節的結論。
* **`h` 在無關 session 之間也幾乎一樣（0.987／0.9999）**，所以這一節不能說「模型忽略了名冊」；
  它說的是「`h` 不含這一題，`read` 含，頭不用」。
* `mismatch` 是循環位移（第 *i* 題對第 *i+1* 題），只給量級，不是獨立抽樣的檢定。
* 只探 k=2 與 k=5；k=3／k=4 不重跑（分叉只需要最小與最大名冊）。
* 單一 seed、CPU、單一讀出、單一任務、200 題；`--aux-mode resolvable` 的混淆仍在（§62.2）→
  診斷，不是歸因臂。
* **核心分不變 0.00/10**；這一節不是能力分數。
* 探針沒有改任何門檻、評測題、語料或 checkpoint；`--check` 從儲存的數字重算 fork，兩份都是 OK。

#### 五、機械分支

依 §66.9：`read_cos_final` 中位數 < 0.99（不是兩個編輯都靜態）且 `moved_to_twin_target` < 0.50
→ **R3b-head-ignores**。

> 讀法：綁定在 state 裡（store 的 value 槽），答題時也被讀出來餵給頭，但頭的選擇沒有用它；
> 換名之後贏家會動，動到誰與 mapping 無關（正好 1/k）。
>
> 下一步：**讀出**——一個以 `read` 為輸入、在名冊候選上做選擇的頭（例如對每個候選算
> `[h, read, candidate embedding]` 的分數），訓練它讀 state，而不是加 session、步數或寬度。
> 這一節已經把「再加訓練不會改變的那一層」量出來了：`h` 不含這一題、store 含、頭不用。



## 六十七、階段 RD：名冊限定的選擇頭（2026-11-15，量測前寫定）

### 67.1 為什麼是這一支

§66.10 的機械輸出是 **R3b-head-ignores**，兩個 checkpoint 都一樣：`h` 的餘弦中位數 1.0000（連兩題完全
無關時也只有 0.9870／0.9999）→ `h` 不裝這一題；`read` 會動（0.8405／0.8553、0.9938／0.8105）、store 的
value 也在動（0.6004／0.5560、0.1203／0.6968）→ 綁定有寫進去、答題時也讀給頭看；但名冊限定的 argmax
跟著換名走的比例只有 0.4950（chance 1/2）與 0.2300（chance 1/5），正好是 1/k。

**§66 有一個必須先說清楚的限制**：它量的是「換了名冊文字，`read` 會不會變」，**不是**「`read` 裡有沒有
足夠的資訊指出兇手」。所以 R3b 其實留下**兩種**讀法，而只有第一種是讀出問題：

1. state 裡有 value → person 的綁定，自迴歸頭不用它 → 換一個選擇頭就應該拿得到，**而且應該轉移**；
2. `read` 只是**隨著名冊文字變動**（session 記憶），並不以可轉移的方式指出兇手 → 任何讀出都無法把它
   變成留出正確率。

§66 分不開這兩種，因為它沒有做任何**介入**（沒有換掉 `read`、沒有換 query）。這一節只換讀出，並且加上
一個不需要訓練的介入，把「頭有沒有在用 `read`」變成可裁決的問題。

### 67.2 量什麼（三個臂 + 一個介入）

載體**凍結**：訓練前後記錄 `weights_hash` 與 checkpoint sha256，只有一個新的小頭被訓練，訓練資料是
**同一個 400 項已宣告訓練集**（§64 的順序擴增語料／§65 的 k=5 語料）：

```
score(c) = v · tanh(W_h h + W_r read + W_e e_c + b)
```

`e_c` 是候選名字在載體 `embedding` 表上的**凍結平均 byte 向量**（沒有逐名字參數表），softmax **只在該
session 的名冊候選上**取，所以「答名冊外的人」在構造上不可能（記為建構檢查，不是分數）。

| 臂 | 輸入 | 用途 |
| --- | --- | --- |
| `read` | `[h, read, e_c]` | 登記的讀出 |
| `h` | `read` 在訓練與評估都歸零 | 只有控制器（消融） |
| `cand` | `h` 與 `read` 都歸零 | 只有候選名字（無內容對照） |

三個臂**同一個架構、同一個參數量、同一個初始化**（同一個 seed 先建構），所以差異只能來自輸入。

**介入（不訓練）**：把留出集每一列的 `read` 換成**下一列**的（循環位移），再問同一個 `read` 頭。若它
照樣答對，就表示它根本沒在用 `read`。位移的有效性本身就是建構檢查（`read_permutation_share` 必須是
1.0，即每一列都真的被換掉）。

### 67.3 程式與重用

* 新檔 `scripts/train_pantry_selection.py`（`--report` 讀已訓練報告、`--check` 機械重驗）。
* 直接重用 §66 探針的 `rebuild_core`／`checkpoint_sha256`／`turn_payload`（import 同一個檔案，
  兩階段的編碼不可能漂移），以及 `train_pantry_deduction.py` 的 `load_corpus`／`run_session`／
  `_chunks`／`BYTE_OFFSET`，和 `gen_pantry_ecosystem.py` 的 `minimal_twin`／`minimal_order_twin`。
* 特徵只讀一次（載體凍結、`torch.no_grad`）：訓練 400 列、留出 200 列、留出換名 200 列、留出反序
  200 列；頭的訓練只在這些固定特徵上跑，**不會**回寫載體。
* 輸出只寫 `--out`；`--check` 從儲存的數字重算五道門與分支。

### 67.4 門檻（跑之前寫定）

頭的表面參數：`hidden=64`、`steps=6000`、`batch=8`、`AdamW(lr=1e-3, weight_decay=1e-4)`、
`seed=20261118`、每 500 步記錄一次 fit／留出曲線；**報告的是最後一步，沒有 early stopping、沒有挑
checkpoint**。

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| **R1** | 語料 digest 與項數已記錄（`train_digest`／`heldout_digest`／400／200） | 語料是登記的那一份 |
| **R2** | 載體 `weights_hash` 與 checkpoint sha256 前後相同 | 只訓練了頭 |
| **R3** | 三個臂的留出預測 **0 個**在名冊外；`read_permutation_share == 1.0` | 建構檢查：softmax 在名冊上、介入是真的 |
| **S1** | `read` 臂 **fit exact ≥ 0.90**（與 §62–§65 的 M1 同一個地板） | 頭至少能擬合已宣告的 400 項 |
| **S2** | `read` 臂 **留出 Wilson 下界 > 1/k**（與 M2 同一個形狀） | 轉移：比亂猜好，且不是靠浮動 |
| **S3** | `read` 臂留出**反序後同人率 ≥ 0.80**（與 M5 同一個地板） | 選擇跟著 mapping，不跟著格子 |
| **S4** | `read` 臂留出 Wilson 下界 **> max(`h`、`cand`、`permuted` 的 Wilson 上界)** | 增益可歸因於 `read`，不是先驗或位置 |

S1／S2／S3 的地板與 §62–§65 完全相同（0.90／chance 的 Wilson 下界／0.80），沒有為這一節調整。S4 是
**分離**而不是另訂地板：它要求登記臂的下界高過三個對照的上界，等於要求「不是重疊」。

### 67.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| R1／R2／R3 | 全過 | 語料由同一支產生器、載體只讀、softmax 在名冊上 |
| S1（fit） | **PASS**，兩個 k 都 ≥ 0.99 | 400 項上載體本來就擬合 1.0000；固定特徵上一個 17k 參數的頭要背 400 列不難 |
| `h` 臂的 fit | **也會很高**（≥ 0.80） | 證據值本身在 `h` 裡，擬合段可以背「這個值 → 這個人」；這正是它必須當消融的原因 |
| `cand` 臂的 fit | 接近 1/k | 只有名字、沒有這一題的資訊 |
| **S2（transfer）** | **FAIL**，兩個 k 都是 | §58 的線性探針已是同一個形狀（in-sample 0.9725、留出 0.1100）；§65 的 k=3／4／5 也一樣。若讀出真的是缺口，S1 與 S2 會**同時**過——那會是對 §66 R3b 讀法的重要修正 |
| S3（order） | 大約 chance | 留出反序是沒見過的；S2 若不過，S3 不會被讀 |
| S4（attribution） | **FAIL**（因為 S2 先不過） | 分離需要先有轉移 |
| 最可能的分支 | **R4b-fits-not-transfers** | 「讀出不是缺口」與 §58／§64／§65 的既有形狀一致 |

**這一段是這一節最重要的預測**：我預期 S1 過、S2 不過。若真的如此，§66 的「內容在 state 裡、頭不用它」
必須收窄成「`read` 隨名冊變動，但不含可轉移的答案識別」——那不是把 §66 讀得更寬，是讀得更窄。

### 67.6 這一節**不會**證明什麼

* 不是能力分數；核心分不變 **0.00/10**，不論四道門結果如何。
* 不是產品：名冊是 session 給的，所以這是**選擇題**讀出，不是開放式作答；它只回答「state 裡有沒有
  可轉移的綁定」。
* 只探 k=2 與 k=5 兩個 checkpoint（§64／§65），不重跑 k=3／k=4。
* 單一 seed、單一頭架構、單一任務、200 題；`--aux-mode resolvable` 的混淆仍在（§62.2）→ 診斷，
  不是歸因臂。
* 頭的 6,000 步是**事先寫定**的預算；若 S1 不過，**不得**用「加步數／加寬度」當下一步（§59 的教訓：
  先分開「架構不對」與「訓練不夠」）。
* `read` 只取一個向量（value_dim 聚合），沒有做 per-slot 讀取；所以 S2 不過**不能**推論「任何讀出都
  不行」，只推論「這一個讀出不行、而它已經拿到同樣的 state」。

### 67.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_selection.py \
    --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \
    --out data/pantry_stage/sel67/k2.json
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_selection.py \
    --report data/pantry_stage/k5_arm/pantry_deduction_20261115-033310.json \
    --out data/pantry_stage/sel67/k5.json
./.venv/bin/python scripts/train_pantry_selection.py --check data/pantry_stage/sel67/k2.json
./.venv/bin/python scripts/train_pantry_selection.py --check data/pantry_stage/sel67/k5.json
```

### 67.8 這一節的地位

§66 把「綁定在哪一層丟掉」問到剩一個問題：**換一個會用 `read` 的讀出，能不能把 state 裡的東西變成
留出正確率？** 三個臂（`read`／`h`／`cand`）與一個介入（permuted read）是為了讓「可以」與「不行」都
有對照：不行的时候，必須能說出「不是因為沒擬合、不是因為先驗、不是因為介入沒生效」。

### 67.9 分叉（跑之前寫定，機械決定下一步）

先看儀器，再看發現：

| 條件 | 編號 | 讀法 | 下一步 |
| --- | --- | --- | --- |
| **R1／R2／R3 任一不過** | — | 語料、載體或介入錯了 | 修儀器；**不得**讀任何 S 數字 |
| S1 **FAIL**（fit < 0.90） | **R4a-head-cannot-fit** | 凍結的 state 連擬合段都撐不起選擇頭：§66 的「內容」只是「`read` 隨名冊變動」，不是「指出兇手」 | 用線性讀出量 `read` 到底編碼了什麼（兇手 vs 格子），**不是**加訓練、**不是**換另一個頭 |
| S1 PASS、S2 **FAIL** | **R4b-fits-not-transfers** | 頭能擬合已宣告的 400 項，留出仍在 chance 以下：**讀出不是缺口**，state 裡是 per-session 記憶，不是可轉移的 value → person 綁定 | 量「擬合段與留出段的 state 差在哪」（§58 的形狀），因為任何讀出都無法從同一個 state 產生它沒有的轉移 |
| S1／S2 PASS、S4 **FAIL** | **R4c-uses-a-prior** | 頭有轉移，但沒有高過 `h`／`cand`／permuted 的上界：學到的東西不需要 `read` | 先稽核頭在用哪個輸入，再談 state 的綁定 |
| S1／S2／S4 PASS、S3 **FAIL** | **R4d-unstable-under-order** | 能轉移、也高過對照，但換名冊順序就換答案：選擇仍靠格子位置 | 在頭裡做順序正規化（排序或 set-pool），再談放大 |
| 四道全 PASS | **R4e-readout-was-missing** | 凍結的 state 裡有可轉移的綁定，名冊限定的選擇頭拿得到、且高過所有對照、也撐過反序：**讀出就是缺口** | 把同一個頭接到 §49 的 11 輪語料；能力宣告仍只在凍結基準說話時才移動 |

不論落到哪一格，**都不得**用「加 epoch／加大寬度／加段數」當下一步：這一節量的就是「在同一個 state
上換讀出」。


### 67.10 結果（2026-11-15，k=2 與 k=5 已訓練 checkpoint，CPU，只訓練選擇頭）

#### 〇、先記一個實作 bug 與三個儀器檢查

第一次跑（20 步的煙霧測試）就在 `gates()` 掛掉：`ceiling = max(block["heldout"]["wilson_upper"] for block
in [arms["h"], arms["cand"], permuted])`，但 `permuted` 已經是 `summarise()` 的摘要（沒有 `heldout`
這一層），只有 `arms[...]` 才需要往下一層。修法是把三個對照都先降到 `["heldout"]` 再取上界。**門檻、
語料、三個臂、介入都沒有改**；20 步的數字（fit 0.9175、留出 0.4850 等）只當煙霧測試，不採用、不進表。

跑正式數字之前先做了三個儀器檢查：

1. **決定性**：同一條指令重跑 k=2，除了 `seconds` 以外**每一個記錄欄位都相同**（`weights_hash`、
   12 個曲線點、每個臂的預測分布都一樣）→ 這一節的數字可以由第三人用同一條指令重現。
2. **`--check` 重算**：五道門與分支都從儲存的數字重算（不是讀回 `pass` 欄位），兩份都是 OK。
3. **語料捷徑**（在寫下任何數字之前查的）：兇手在名冊**文字**裡的位置，k=2 是 200/200 對半、k=5 是
   每格 80/80，完全平衡；`culprit` 在 `environment["actors"]` 裡**永遠是第 0 個**（產生器
   `culprit = actors[0]`），但這個頭的 `proj_e` 對所有候選**共用權重**、分數逐候選獨立算，**沒有位置
   輸入**，所以那個排序無法被利用。這兩點讓 `cand` 臂是真正的「只有名字」對照，也讓下面的名冊內數字
   不會是位置捷徑。

#### 一、讀數

| 讀數 | k=2（§64 checkpoint） | k=5（§65 checkpoint） |
| --- | --- | --- |
| R1 語料（digest／400／200） | `416a8a68…`／`69c730e1…`／400／200 | `d6ca78a8…`／`948b08cc…`／400／200 |
| R2 載體（`weights_hash`、checkpoint sha256） | 前後相同（`de17ed7d…`／`cc173f9d…`） | 前後相同（`05c3b103…`／`e4d13e56…`） |
| R3 建構（名冊外答案／介入有效） | 0／0／0；`read_permutation_share` **1.0** | 同左 |
| 成本 | 12.1 s，16,641 參數，6,000 步 | 12.08 s，同一個頭 |
| **`read` 臂 fit** | **1.0000**（400/400） | **1.0000**（400/400） |
| `read` 臂留出 | **0.4850**（97/200），Wilson 0.4167–0.5539 | **0.2300**（46/200），Wilson 0.1771–0.2931 |
| `read` 臂留出反序同人率 | 0.5200 | 0.2450 |
| `read` 臂換名（twin）準確率 | 0.5200 | 0.2300 |
| `h` 臂 fit／留出 | 0.7250（290/400）／0.4500（90/200，0.3826–0.5192） | 0.3000（120/400）／0.2150（43/200，0.1637–0.2770） |
| `cand` 臂 fit／留出 | 0.5850（234/400）／**0.5050**（101/200，0.4363–0.5735） | 0.2850（114/400）／**0.2150**（43/200，0.1637–0.2770） |
| `permuted`（換鄰居的 read） | 0.4200（84/200），0.3537–0.4893 | 0.1550（31/200），0.1114–0.2116 |
| `read` 曲線（每 500 步的 fit／留出） | 1.0000 起，留出在 0.465–0.495 之間來回 12 點 | 0.995 後 1.0000，留出 0.21–0.235 |
| **S1**（fit ≥ 0.90） | **PASS**（1.0000） | **PASS**（1.0000） |
| **S2**（留出 Wilson 下界 > 1/k） | **FAIL**（0.4167 ≤ 0.5） | **FAIL**（0.1771 ≤ 0.2） |
| **S3**（反序同人 ≥ 0.80） | **FAIL**（0.5200） | **FAIL**（0.2450） |
| **S4**（`read` 下界 > 三個對照的上界） | **FAIL**（0.4167 ≤ 0.5735） | **FAIL**（0.1771 ≤ 0.2770） |
| 對照的上界（`h`／`cand`／`permuted`） | 0.5192／0.5735／0.4893 | 0.2770／0.2770／0.2116 |

#### 二、預測對照（§67.5 寫在跑之前）

| 預測 | 實際 | 判定 |
| --- | --- | --- |
| R1／R2／R3 全過 | 兩個 k 都過 | **命中** |
| S1 PASS（≥ 0.99） | 1.0000／1.0000，而且第 500 步就已經 1.0000 | **命中** |
| **`h` 臂 fit 也會很高（≥ 0.80）** | **0.7250（k=2）／0.3000（k=5）** | **落空** |
| `cand` 臂 fit 接近 1/k | 0.5850／0.2850（留出 0.5050／0.2150） | **落空（略高）**，下面解釋 |
| S2 FAIL，兩個 k 都是 | 0.4167／0.1771，都低於 chance | **命中** |
| S3 大約 chance | 0.5200／0.2450 | **命中** |
| S4 FAIL | 兩個 k 都 FAIL | **命中** |
| 最可能分支 R4b | 兩個 k 都是 R4b | **命中** |

兩個落空都要寫清楚：

1. **`h` 臂在 k=5 連擬合都做不到（0.3000 vs chance 0.2）。** 我預期 `h` 可以背「這個值 → 這個人」，
   所以 fit 會很高。實際 k=2 是 0.7250、k=5 只有 0.3000，而且 k=5 的預測**塌成一個名字**
   （`Chris` 佔 0.405，只有 9 個不同答案）——那不是背起來，是把訓練集的邊際分布端出來。這與 §66
   的 `h_cos_final` 1.0000（`h` 不裝這一題）一致：`h` 臂的高 fit 若出現，也只能來自「這一題的身分」，
   不是「值屬於誰」的規則；k=5 有 12 個可能的人、400 列，這一點微弱訊號撐不起來。
2. **`cand` 比 1/k 高，因為訓練集的兇手邊際是斜的。** 訓練段 400 項的兇手次數是
   `Chris 56／Betty 52／Kevin 38／Frank 36／Hana 34／David 34…`（均勻期望 33.3），留出段卻是平的
   （`Alex 21／Betty 20／Lena 19／Chris 18…`）。用一條純機械規則「在名冊裡挑訓練段出現最多的名字」
   在留出上得 **0.5400**（k=2）／**0.2100**（k=5），與 `cand` 的 0.5050／0.2150 同一個量級 →
   `cand` 學到的是**名字先驗**，不是這一題的內容。這也是為什麼 S4 在 k=2 的上界是 0.5735（由
   `cand` 決定）：那個對照看起來「有訊號」，其實是語料邊際。

#### 三、這一節的答案：**讀出不是缺口**（R4b）

1. **擬合是真的，而且是 `read` 單獨做到的。** `read` 臂的 fit 是 1.0000，`h` 被歸零；同一批特徵
   拿掉 `read`（`h` 臂）只剩 0.7250／0.3000。所以 `read` 單獨就能把 400 個已宣告項目分開——**state
   裡有這一題的資訊**，這與 §66 的 `read_cos` 0.84／0.99 是同一個事實。但那是**這一題的身分**，
   不是「值屬於誰」的規則。
2. **同一個 `read` 換到 200 個沒見過的結構上，就在 chance。** 0.4850／0.2300，Wilson 下界
   0.4167／0.1771 **低於** 0.5／0.2。S2 不過。曲線從第 500 步起 fit 就是 1.0000，留出在 12 個量測
   點之間只動了 0.03（k=2）／0.025（k=5）——**沒有一次接近 chance 以上**，所以不是「訓練不夠」，
   也不是「最後一步剛好壞掉」。
3. **它沒有比「只有名字」的對照好。** `cand`（`h` 與 `read` 都歸零）是 0.5050／0.2150，k=2 時
   **比 `read` 高**；`h` 是 0.4500／0.2150；`permuted` 是 0.4200／0.1550。三個對照的上界都比
   `read` 的下界高，S4 不過。
4. **與 §64 的擬合不衝突，而且是同一個數字的兩面。** §64 的 M1 是 1.0000（自迴歸解碼器在
   in-distribution 上把名冊讀對），§67 凍結載體後用 `[h, read]` 餵一個選擇頭也得到 1.0000 →
   兩個讀出在**已宣告的 400 項**上強度相同。差別只在留出：§64 的 M2 是 0.2650，但其中
   0.5550 的答案落在名冊裡，名冊內正確率是 **53/111 = 0.4775**；§67 的選擇頭**構造上只能在名冊裡
   選**，得到 **0.4850**。兩者幾乎相同 → **把答案限制在名冊裡並沒有帶來轉移**，它只是拿掉了
   §64 那些「答名冊外」的猜測。k=5 同方向但沒那麼貼（§65 名冊內 26/90 = 0.289 vs §67 的 0.2300），
   兩者都貼著 1/5。

**所以 §66 的 R3b 要收窄，不是放寬**：`read` 隨名冊文字變動、也足以辨認「這是哪一題」，但**不含**
可轉移的「值 → 人」對應。§66 說「內容在 state 裡」時，那個「內容」是**這一題的身分**；它不是答案，
任何讀出都無法從同一個 state 產出它沒有的轉移。

#### 四、照實記的限制

* **S1 這道門很弱。** 400 列、16,641 參數，第 500 步（等於看過 4,000 個樣本、10 個 epoch）就
  1.0000。它通過只證明「頭能背」，真正的判別全在 S2／S4；把它讀成「架構有容量」是過度解讀。
* **`permuted` 的區間與 `read` 重疊**（k=2：0.3537–0.4893 vs 0.4167–0.5539；k=5 也是）。
  所以這一節**不能**說「頭完全沒在用 `read`」——只能說「用了也沒有變成轉移」。點估計在兩個 k 都
  下降（0.4850→0.4200、0.2300→0.1550），但這不是檢定。
* **只有一種讀出。** `read` 是 `read_vector()` 聚合成的一個向量（value 維度），沒有 per-slot 讀取、
  沒有 attention。所以 S2 不過**不能**推論「任何讀出都不行」，只推論「這一個拿到完整 state 的讀出
  不行」。
* **名冊是 session 給的**，所以這是選擇題讀出，不是開放式作答；它量的是「state 裡有沒有可轉移的
  綁定」，不是「模型會不會推理」。
* 只探 k=2 與 k=5 兩個 checkpoint（§64／§65），不重跑 k=3／k=4；單一 seed、單一頭架構、200 題；
  `--aux-mode resolvable` 的混淆仍在（§62.2）→ 診斷，不是歸因臂。
* 頭的 6,000 步是登記的預算，沒有 early stopping、沒有挑 checkpoint；也沒有事後改門檻、語料或臂。
  S1 已經過了，所以「加步數／加寬度」本來就不在分叉裡。
* **核心分不變 0.00/10**；這一節是診斷，不是能力分數。

#### 五、機械分支

依 §67.9：R1／R2／R3 全過、S1 PASS、S2 FAIL（兩個 k）→ **R4b-fits-not-transfers**。

> 讀法：頭能擬合已宣告的 400 項，留出的 Wilson 下界仍在 chance 以下——**讀出不是缺口**；state 裡
> 是 per-session 記憶，不是可轉移的 value → person 綁定。
>
> 下一步（登記的）：量「擬合段與留出段的 state 差在哪」（§58 的形狀：in-sample 0.9725、留出
> 0.1100），因為任何讀出都無法從同一個 state 產生它沒有的轉移。**不得**以「加 epoch／加寬度／加段數」
> 當下一步。

## 六十八、階段 CT：state 裡裝的是什麼（2026-11-15，量測前寫定）

### 68.1 為什麼是這一支

§67.10 的機械輸出是 **R4b-fits-not-transfers**，兩個 checkpoint 都一樣：同一個凍結載體、同一個
`read` 向量，選擇頭能把 **400 個已宣告項目擬合到 1.0000**（`h` 歸零也做得到），換到 **200 個沒見過
的結構**就回到 chance（0.4850／0.2300，名冊限定的 chance 是 1/2、1/5），而且沒有比「只有名字」的
對照好。**讀出不是缺口**——這是 §67 的結論。

§67.9 已經點名下一個問題：**擬合段與留出段的 state 差在哪？** 這一節把它變成一個可裁決的量測，而
不是再問一次推理題。留下的兩種讀法並不相同：

1. state 裡有這一題的**事實**（看到的顏色、名冊上的名字），但沒有事實之間的**配對**（哪個名字穿那個
   顏色）。若是這樣，一個「報告事實」的讀出會成功，而一個「查答案」的讀出會失敗——**缺口在組合**。
2. state 裡只有一個**session key**（足以分辨 A 題與 B 題、沒有可轉移的內容）。若是這樣，任何讀出都
   不會比 §67 好——**缺口在狀態本身**。

這一節不換載體、不訓練新的載體、也不再要求任何讀出回答「誰是兇手」。

### 68.2 量什麼（三個讀出 + 一個 shift 對照）

全部在**答題邊界**（最後的 `read` 向量，也就是 §66／§67 看的那一個），同一份凍結特徵，同一個協定：
在 **400 個已宣告項目**上擬合、在 **200 個沒見過的結構**上計分；參考值是**訓練段內**按結構分 5 折
（同一結構的兩個名冊順序永遠在同一折，所以沒有一折看過測試結構的姊妹列）。

| 讀出 | 答案空間 | 判分 | chance |
| --- | --- | --- | --- |
| `colour` | 8 色（`COLOURS`） | argmax | 1/8 |
| `roster` | 12 個名字裡的那 k 個 | **top-k 集合**，整組必須完全相同 | `1 / C(12, k)`＝1/66（k=2）、1/792（k=5） |
| `culprit` | 12 個名字 | argmax（§58／§67 的對照） | 1/12 |
| `shift` | — | §67 的 `read` 頭，同一批 400 項、標籤**全部**移到名冊的下一個位置 | — |

`roster` 用 top-k 而不是 12 個獨立的 0.5 門檻，是因為名冊**就是** k 個名字的集合：門檻是任意的，
集合才是那個事實的形狀。

三個讀出都是**單一個 `nn.Linear`**（沒有非線性、沒有隱藏層），刻意比 §67 的 16,641 參數 MLP 弱：
問題是向量**裝了什麼**，不是頭能背多少。

**`shift` 對照**回答的是另一個問題：「§67 的擬合是不是只是容量？」把每一列的標籤移到名冊的**下一個
位置**（迴圈位移）：k=2 時每一列的答案都變成另一個人，仍然是**這一列名冊裡的人**。若 §67 的頭照樣
擬合到 1.0000，那麼它的 in-sample 1.0000 是容量，不是「state 裝了真對應」。

用迴圈位移而**不是**固定 seed 的隨機排列，是跑前就改掉的設計，理由照實記：k=2 只有兩個位置，隨機
排列會讓**大約一半的列保留原標籤**（等同原標籤的機率 1/2），那樣「能擬合打亂的標籤」就與「能擬合
真標籤」分不開；迴圈位移讓 **100%** 的列換標籤，而且換到的仍是自己名冊裡的人。

### 68.3 程式與重用

* 新檔 `scripts/probe_pantry_contents.py`（`--report` 讀已訓練報告、`--out` 寫判決、`--check` 從
  儲存的數字機械重驗）。
* 直接重用 §67 的 `train_pantry_selection.py`：`load_trainer`／`load_probe`／`session_features`／
  `name_vectors`／`build_head`／`fit_head`／`predict`／`summarise`／`HEAD_*`；以及 §66 探針的
  `rebuild_core`／`checkpoint_sha256`。特徵與 `shift` 對照因此不可能與 §66／§67 漂移。
* 載體凍結：訓練前後記錄 `weights_hash` 與 checkpoint sha256，只擬合探針。
* 輸出只寫 `--out`（`data/` 已被 gitignore）；`--check` 重算五道門與分支，並要求
  `labels_changed == 1.0`、`labels_in_row_roster == 1.0`、容量對照是**真的排列**。
* 契約測試 `tests/test_pantry_contents.py`（40 條）：目標抽取、結構分組、chance 與多數基線、
  標準化只用訓練段統計、迴圈位移是雙射且留在名冊、容量對照是真排列、集合判分、7 個分支都可達、
  `--check` 對每個壞掉的欄位都會拒收。

### 68.4 門檻（跑之前寫定，含兩個跑前就修掉的儀器缺陷）

探針預算（寫定，不因結果調整）：`steps=2000`、`batch=64`、`AdamW(lr=1e-3, weight_decay=1e-4)`、
`seed=20261119`；參考折 5 折；容量對照用同一支探針、同一預算、同一 seed，把**標籤在列之間置換**
（`CAPACITY_SEED=20261119`）。輸出是**最後一步**，沒有 early stopping、沒有挑 checkpoint。

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| **G1** | `culprit` **in-sample ≥ 0.95** 且載體 `weights_hash` 前後相同 | 讀出與載體都沒有壞；低分才值得讀 |
| **G2** | `shift` 擬合 **≥ 0.90**，且 `labels_changed == 1.0`、`labels_in_row_roster == 1.0` | §67 的 in-sample 1.0000 是容量，不是「裝了真對應」 |
| **G3** | `colour`：**留出 exact ≥ 0.50** 且 Wilson 下界 > max(1/8, 多數基線) | 顏色事實**有轉移** |
| **G4** | `roster`：**留出 exact ≥ 0.50** 且 Wilson 下界 > max(1/C(12,k), 多數基線) | 名冊事實**有轉移** |
| **G5** | `culprit`：Wilson 下界 **> 1/k**（名冊推論的上限，不是 1/12） | 對照：若成立，與 §67 矛盾，必須先稽核 |

G3／G4 用 **0.50 的效果量**，不是「比 chance 高就好」：§68 問的是這兩個事實**能不能被組合**，而
留出只有 5% 的集合命中不可能拿去組合，把它記成「有轉移」是灌水。G5 的地板是 **1/k** 而不是 1/12，
因為「知道名冊是哪幾個人、不知道配對」的策略在 12 選 1 上本來就會明顯高過 1/12；拿 1/12 當地板會
把「只知道名冊」誤判成「與 §67 矛盾」。

`readable`（in-sample ≥ 0.95）與 `capacity`（同一支探針在置換標籤上的 in-sample）**不是門檻，是讀法
的座標**：一個事實如果在樣本內都擬合不起來，它的留出 null 不能讀成「state 沒有這個事實」，只能讀成
「在這個邊界、這個線性讀出看不到它」。分支表就是為此寫的。

#### 跑前儀器檢查（**只用訓練段**，留出段在前置階段從未被計分）

這三件事在寫下任何正式數字之前就量了，因此照實記進門檻，而不是事後改門檻：

1. **原始 `read` 的尺度讓新 `nn.Linear` 起點飽和。** 400 列的 `read` 平均範數 **36.93**，而
   `nn.Linear` 的預設初始化讓 logits 一開始就到十幾的量級，softmax 飽和、梯度極小：同一支線性探針
   在**隨機 8 類標籤**上 2,000 步只有 **0.2025**、8,000 步 0.2500。這不是「沒有資訊」，是
   **儀器壞了**。修法：探針吃**標準化**特徵（訓練段 per-dimension 平均／標準差，**同一組統計**套到
   留出列，沒有洩漏）。
2. **這個向量活在一個 ~8 維的子空間裡。** `read` 的奇異值前 8 個就佔 **99.89%** 的能量（第 9 個
   之後加起來不到 0.11%）。所以在這裡「任意 8 類標籤」本來就擬合不起來——8 維的線性切分無法實現
   400 個點的任意劃分。這正是為什麼每個目標都帶一個 **`capacity`** 對照：低分只有在**高過**自己的
   容量天花板時才是證據。
3. **修正後的跑前實測（k=2 語料、400 列、2,000 步）**：
   `colour` in-sample **0.2550**／capacity **0.2175**；`roster`（top-2）in-sample **0.2875**／
   capacity **0.0500**；`culprit` in-sample **1.0000**／capacity **0.1600**。也就是說：兇手是**線性
   可讀**的（1.0000 對比 0.16 的天花板），顏色幾乎貼著天花板（0.255 對 0.2175），名冊有訊號（0.2875
   對 0.05）但遠不到「讀得出來」。

**跑前也修掉兩個實作 bug**（都是 30 步煙霧測試抓到的，數字全部丟棄、不採用）：(a) 「位移後的標籤是否
留在名冊裡」原本拿**位置索引**去比**名字索引**的清單，得到 0.19 的假失敗——改成比**推導出的名字**，
現在是 1.0；(b) 容量對照原本要求 `labels_changed == 1.0`，但**隨機排列**本來就會留下一部分列在原
標籤（8 類約 12%、12 類約 8%），改成「必須是雙射」＋`labels_changed ≥ 0.5`。

**照實記的丟棄量測**：前置階段有兩次 30 步煙霧測試跑過**一次**留出段（第一次是舊設計，得到
`colour` 0.125／`roster` 0.01／`culprit` 0.285；第二次是新設計，0.115／0.07／0.195）。那些數字**不
是證據**：30 步等於 1.9 秒的未收斂探針（`culprit` in-sample 只有 0.675，連 G1 都不過），而且登記的
設定是 2,000 步。它們只用來確認 shape、簽名與 `--check`，沒有用來選門檻——門檻是上面的 0.95／
0.50／1/k，與那兩次讀數無關。

### 68.5 預測（寫在跑之前）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| G1 | **PASS** | 跑前實測 `culprit` in-sample 1.0000；載體只讀 |
| G2 | **PASS** | 跑前煙霧裡 §67 的頭只花 200 步就把位移後的標籤擬合到 1.0000，而同一批列對真標籤是 0.0000 |
| G3 `colour` | readable **FAIL**（0.255）、transfers **FAIL** | in-sample 貼著 0.2175 的天花板：在這個邊界看不到顏色 |
| G4 `roster` | readable **FAIL**（0.288）、transfers **FAIL** | 高過 0.05 的天花板 5.7 倍，但遠不到 0.95；留出不可能超過 in-sample |
| G5 `culprit` | **不成立**（不矛盾） | 跑前 30 步的留出是 0.195，離 1/k＝0.5 很遠；§67 的名冊限定讀出是 0.4850，同一件事 |
| 最可能的分支 | **N3-facts-not-linearly-readable** | 「答題邊界看不到事實」比「state 沒有事實」更貼近手上的數字 |

**預測改了，照實記**：在寫這一節之前，我的預測是 **N1-facts-without-pairing**（兩個事實都在、缺的是
組合）。跑前只用**訓練段**的儀器校準就把這個預測推翻了：顏色與名冊在這個邊界連樣本內都擬合不起來，
所以「事實都在」不是手上數字支持的讀法。這不是把門檻往對自己有利的方向調——門檻（0.95／0.50／1/k）
與協定（2,000 步、5 折、400／200）都是在校準**之前**就定的，校準只影響**預測**與**分支表**的分類。

### 68.6 這一節**不會**證明什麼

* 不是能力分數；核心分不變 **0.00/10**。
* **N3 不等於「state 沒有事實」。** 它只說「在答題邊界，這個**線性**讀出看不到顏色與名冊」。事實
  可能裝在別的邊界（名冊那一回合、證據那一回合）、或以非線性的方式編碼——那需要下一個階段去量。
* 只探 k=2 與 k=5 兩個 checkpoint（§64／§65），不重跑 k=3／k=4；單一 seed、單一探針架構、單一
  邊界、200 題。
* 訓練段 400 列包含 200 個結構的兩個名冊順序，所以 `colour`／`culprit` 在樣本內是**重複的** 200 個
  答案；5 折參考值按結構分，正是為了不讓同一個答案出現在兩折。
* 容量天花板本身是一個**下界**（同一支探針、同一預算），不是「可分性的上限」；它只用來拒絕「低分
  就是沒有資訊」這種讀法。
* 名冊是 session 給的，所以這仍是**多選**讀出，不是開放式作答。
* `shift` 只測 §67 的那一個頭、那一組預算；它回答「擬合是不是容量」，不回答「有沒有別種擬合方式」。

### 68.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_contents.py \
    --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \
    --out data/pantry_stage/contents68/k2.json
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_contents.py \
    --report data/pantry_stage/k5_arm/pantry_deduction_20261115-033310.json \
    --out data/pantry_stage/contents68/k5.json
./.venv/bin/python scripts/probe_pantry_contents.py --check data/pantry_stage/contents68/k2.json
./.venv/bin/python scripts/probe_pantry_contents.py --check data/pantry_stage/contents68/k5.json
```

兩份都用 `--device cpu`（預設）。跑完後同一條指令重跑 k=2 一次，確認決定性（除 `seconds` 外每個
欄位相同）。

### 68.8 這一節的地位

§66 問「綁定在哪一層丟掉」，§67 問「換一個會用 `read` 的讀出能不能救」，兩者都回到「不行」。§68
問的是**剩下的那一半**：如果讀出不是缺口，那 state 裡到底有什麼？它把答案拆成「事實」與「配對」兩個
可分別量測的東西，並且為每一種結果準備了一個**具名的**下一步——包含「看不到」這一種，因為把
「看不到」讀成「不存在」正是這個專案一路在犯的錯（§X #275 的核心分、§X #272 的記憶冒充學習）。

### 68.9 分叉（跑之前寫定，機械決定下一步）

先看儀器，再看發現：

| 條件 | 編號 | 讀法 | 下一步 |
| --- | --- | --- | --- |
| **G1 FAIL**（或載體動了） | **N0-instrument** | 讀出或載體壞了，留出數字不能讀 | 修讀出；**不得**從這份結果讀任何事實 |
| G1 PASS、**G5 成立** | **N5-contradiction** | 不受限的線性探針在 `read` 上**單獨**轉移了兇手（Wilson 下界 > 1/k），而 §67 的名冊限定 MLP 沒有 → 兩個讀出不同（線性 vs MLP、自由 vs 限定），必須先稽核差異 | 稽核 §67 的頭與這支探針的差，不是語料 |
| G1 PASS、G5 不成立、**G2 FAIL** | **N4-fit-needs-true-labels** | §67 的頭**不能**擬合位移後的同批標籤 → 它的 in-sample 1.0000 依賴真標籤：state 裝了「關於真對應的某種東西」，只是不轉移 | 在名冊邊界與答題邊界直接探「顏色 → 名字」這個關係本身 |
| G3 與 G4 **都轉移** | **N1-facts-without-pairing** | 兩個事實都在沒見過的結構上轉移、兇手仍在 chance → 缺的是**組合**，不是事實 | 登記一個在沒見過的結構上獎勵組合的目標（先問配對會不會出現），不是在同一目標上加步數 |
| G3／G4 **恰好一個轉移** | **N2-partial-facts** | 半個 session 在 state 裡、半個不在：失敗有具名的位置 | 到**那個事實被說出來的那一回合**去探它，先於任何新目標 |
| 都不轉移，且**至少一個在樣本內讀不出** | **N3-facts-not-linearly-readable** | 在答題邊界，線性讀出看不到至少一個事實（in-sample 貼著自己的容量天花板）→ 「state 沒有事實」**尚未**成立；失敗可能在**邊界**，不在 state | 到名冊那一回合與證據那一回合探同樣的事實，再談 state 裝了什麼 |
| 都不轉移，但**兩個在樣本內都讀得出** | **N6-session-key-only** | 兩個事實都線性可讀、卻都不轉移，兇手也不轉移 → state 是 session key：足以分辨這一題與那一題，沒有可轉移的內容 | 探每一回合的 store 寫入（有沒有任何 slot 真的裝了顏色），不是在同一批向量上再換讀出 |

不論落到哪一格，**都不得**把「加步數／加寬度／加資料」當下一步：這一節量的是「同一個凍結 state 的
內容」，不是訓練量。

### 68.10 結果（2026-11-15，k=2 與 k=5 已訓練 checkpoint，CPU，不新增訓練）

#### 〇、登記與執行的順序（可查）

登記（§68.1–§68.9、腳本、40 條契約測試）先 commit 為 `f7987bc18`，時間戳
`2026-11-15T10:37:45+08:00`；正式跑的第一行 log 是 `2026-11-15T10:37:56+08:00`。也就是說**跑之前**
門檻、協定、分支表就已經在版控裡，不是跑完才寫。兩支探針各 12.25 s／12.35 s（CPU），
`--check` 兩份都 **OK**；k=2 用同一條指令重跑一次（`k2_rerun.json`），除 `instrument.seconds`
以外**每一個欄位相同**。

載體沒動：`weights_hash` 前後都是 `de17ed7d…`（k=2）／`05c3b103…`（k=5），checkpoint sha256 前後
都是 `cc173f9d…`／`e4d13e56…`。這一節只擬合四個小讀出，沒有任何權重被寫回。

#### 一、讀數

| 讀數 | k=2（§64 checkpoint） | k=5（§65 checkpoint） |
| --- | --- | --- |
| 語料（digest／400／200） | `416a8a68…`／`69c730e1…`／400／200 | `d6ca78a8…`／`948b08cc…`／400／200 |
| 探針預算 | 2,000 步／batch 64／AdamW(1e-3, wd 1e-4)／seed 20261119／5 折 | 同左 |
| **`colour` in-sample／capacity** | **0.2550**／0.2200（+0.035） | **0.2550**／0.2375（+0.0175） |
| `colour` 5 折參考 | 0.1600（0.175／0.175／0.2125／0.1375／0.10） | 0.1550（0.175／0.1625／0.1875／0.2125／0.0375） |
| `colour` 留出 | **0.1450**（29/200），Wilson 0.1029–0.2005，chance 0.1250 | **0.0850**（17/200），0.0537–0.1319，chance 0.1250 |
| **`roster` in-sample／capacity** | **0.2875**／0.0500（5.75×） | **0.0175**／0.0000 |
| `roster` 5 折參考 | 0.2275（0.225／0.30／0.2625／0.15／0.20） | 0.0025（0.0／0.0／0.0125／0.0／0.0） |
| `roster` 留出 | **0.1300**（26/200），0.0903–0.1837，chance 0.0152（1/66） | **0.0100**（2/200），0.0027–0.0357，chance 0.0013（1/792） |
| **`culprit` in-sample／capacity** | **1.0000**／0.1600 | **0.9925**／0.1900 |
| `culprit` 5 折參考 | 1.0000（五折全 1.0） | 0.9500（0.9875／0.9625／0.9375／0.925／0.9375） |
| `culprit` 留出 | **0.2650**（53/200），0.2087–0.3302，chance 0.0833 | **0.1100**（22/200），0.0738–0.1609，chance 0.0833 |
| 多數基線（colour／roster／culprit） | 0.1000／0.0150／0.0900 | 0.0700／0.0050／0.0900 |
| **`shift` 對照** | fit **1.0000**（400/400），同批列對**真**標籤 **0.0000**，留出 0.5150 | fit **0.9625**（385/400），同批真標籤 **0.0000**，留出 0.2100 |
| `shift` 建構檢查 | `labels_changed` **1.00**、`labels_in_row_roster` **1.00** | 同左 |
| 容量對照建構檢查 | 8 類 **0.865**、12 旗標 **0.9825**、12 類 **0.895** 的列被換標籤；排列皆為雙射 | 0.870／0.995／0.895 |
| **G1**（culprit in-sample ≥ 0.95 且載體不變） | **PASS**（1.0000） | **PASS**（0.9925） |
| **G2**（shift ≥ 0.90 且兩個建構檢查 = 1.0） | **PASS**（1.0000） | **PASS**（0.9625） |
| **G3 `colour`** | readable **False**（0.2550 < 0.95）／transfers **False** | readable **False**／transfers **False** |
| **G4 `roster`** | readable **False**（0.2875 < 0.95）／transfers **False** | readable **False**（0.0175）／transfers **False** |
| **G5 `culprit`**（Wilson 下界 > 1/k） | **不成立**（0.2087 ≤ 0.5） | **不成立**（0.0738 ≤ 0.2） |

#### 二、三個必須照實記的細節

1. **`roster` 在 k=2 的 Wilson 下界確實高過 chance，是登記的 0.50 效果量把它擋下來的。**
   0.1300 對 chance 0.0152 是 8.6 倍，Wilson 下界 0.0903 也遠高於 0.0152——如果門檻只寫「比 chance
   高」，這一格就會被記成「名冊事實有轉移」。但它離「能被組合」還很遠（0.13 的集合命中），所以
   登記的 0.50 效果量判它 **transfers=False**。這是這一節唯一一個「門檻真的在做事」的地方，寫出來
   以免讀者以為它只是形式。
2. **`culprit` 的留出也不是純粹的 chance，但沒有到 1/k。** k=2 是 0.2650（Wilson 下界 0.2087），
   高於 1/12＝0.0833、低於名冊上限 1/k＝0.5。這正是把 G5 的地板設成 **1/k** 的理由：一個「知道名冊是
   哪兩個人、不知道配對」的讀出在這題上本來就會落在 1/12 與 1/2 之間，用 1/12 當地板會把它誤判成
   「與 §67 矛盾」。它沒有矛盾。
3. **k=5 的名冊在這個邊界幾乎完全看不到。** in-sample 0.0175、capacity 0.0000、留出 2/200——比 k=2
   的 0.2875 差一個量級。所以「名冊事實」不是穩定地「有一點訊號」，而是**隨 k 崩塌**；把 k=2 的 0.2875
   當成「有一半讀得出來」會高估。

#### 三、這一節的答案：**N3-facts-not-linearly-readable**

機械分支（§68.9，先看儀器再看發現）依序判定：G1 PASS → 不是 N0；G5 不成立 → 不是 N5；G2 PASS →
不是 N4；G3 與 G4 都不轉移；至少一個（兩個都）在樣本內讀不出 → **N3**。

讀法照登記的寫法：**在答題邊界，這個線性讀出看不到至少一個事實**（`colour` 的 in-sample 只比自己的
容量天花板高 0.035／0.0175；`roster` 在 k=5 幾乎是零）。所以 **「state 沒有事實」尚未成立**——失敗
可能在**邊界**，不在 state。這與 §67 的 R4b 不衝突，而是把它**收窄**：§67 說「換一個會用 `read` 的
讀出也救不了答案」；§68 說「連讀出事實都在這個邊界做不到」，所以下一步不是再換讀出，而是**換邊界**。

#### 四、預測對帳

| 讀數 | 預測（§68.5） | 實際 | 對帳 |
| --- | --- | --- | --- |
| G1 | PASS | PASS（1.0000／0.9925） | ✅ |
| G2 | PASS | PASS（1.0000／0.9625） | ✅ |
| G3 `colour` readable | FAIL（預測 0.255） | FAIL（**0.2550**，兩個 k 都是） | ✅（數值也對上） |
| G3 `colour` transfers | FAIL | FAIL（0.1450／0.0850） | ✅ |
| G4 `roster` readable | FAIL（預測 0.288） | FAIL（0.2875／0.0175） | ✅（k=2 數值對上；k=5 比預測更差） |
| G4 `roster` transfers | FAIL | FAIL（0.1300／0.0100） | ✅ |
| G5 `culprit` | 不成立 | 不成立（0.2087／0.0738 ≤ 1/k） | ✅ |
| 分支 | **N3** | **N3** | ✅ |

**兩個沒預期到的細節，照實記**：(a) `colour` 的 in-sample 在兩個 k 上**都是 0.2550**——不同 checkpoint、
不同語料（k=5 的名冊更長），同一個線性探針卻給出同一個小數四位。合理的解釋是它讀到的是**與 k 無關的
某個 3 類劃分**（0.255 ≈ 2/8 附近），不是「顏色」本身；這正好說明為什麼要跟 capacity 比，而不是看
絕對值。(b) `roster` 在 k=2 的 Wilson 下界過 chance（見上一節第 1 點），這是登記的**效果量**擋下來的，
不是我事後改判。

**預測在登記前就改過一次**（§68.5 已記）：原本預測 **N1-facts-without-pairing**，跑前只用訓練段的
儀器校準就改成 **N3**。校準只動預測與分支分類，門檻（0.95／0.50／1/k）與協定（2,000 步、5 折、
400／200）都在校準之前就定好。

#### 五、這一節的限制（照實寫）

* **N3 ≠「state 沒有事實」。** 只說「在答題邊界、用一個 `nn.Linear`、在標準化後的 `read` 上」看不到
  顏色與名冊。事實可能在別的邊界（名冊那一回合、證據那一回合），或以非線性方式編碼。
* 只探 **k=2／k=5** 兩個 checkpoint（§64／§65），不重跑 k=3／k=4；單一 seed、單一探針架構、單一
  邊界、200 題。
* `capacity` 是**下界**（同一支探針、同一預算），不是可分性上限；它只能拒絕「低分就是沒有資訊」。
* `colour` 的 8 類包含 `grey`／`black`／`white` 這種在中文裡只差一個字的色名，語料本身的標記是否
  乾淨沒有另外稽核——不過留出是 200 個沒見過的結構，標記雜訊會同時壓低 in-sample 與留出，不會製造
  假轉移。
* `shift` 只測 §67 那一個頭、那一組預算；它回答「擬合是不是容量」，不回答「有沒有別種擬合方式」。
* **不是能力分數**；核心分不變 **0.00/10**。

#### 六、下一步（§68.9 的機械輸出）

N3 指名的是**邊界**，不是讀出、不是語料、不是訓練量：

> 到名冊那一回合與證據那一回合探同樣的事實，再談 state 裝了什麼。

所以下一個階段要登記的是**同一組事實、同一個線性讀出、換邊界**（名冊回合之後、證據回合之後），
並且要能回答一個 N3 沒有回答的問題：**若事實在那兩個邊界讀得出來、在答題邊界讀不出來，那它們是在
哪一步被丟掉的？** 這仍然**不得**以「加步數／加寬度／加資料」當下一步——這一節量的是同一個凍結
state 的內容。

---

## §69 事實住在哪一回合？（同一個凍結 state，三個邊界）

### 69.1 為什麼是這一支

§68 的機械輸出是 **N3-facts-not-linearly-readable**：在**答題邊界**、用一個 `nn.Linear`、在標準化後
的 `read` 上，看不到顏色與名冊。N3 刻意**沒有**說「state 沒有事實」——它只說「在這個邊界、這個讀出
看不到」。§68.9 因此把下一步指名為：

> 到名冊那一回合與證據那一回合探同樣的事實，再談 state 裝了什麼。

這一節就是那一步。它把「事實在哪裡丟掉」變成一個可裁決的問題：**同一個事實、同一支讀出、同一批
400／200 個結構，只換邊界。** 三種結果互斥且都有具名的下一步：

1. 事實**在自己的回合轉移**、在答題邊界不轉移 → **保留（retention）**出問題，不是表徵；
2. 事實**在自己的回合也不轉移** → 線性讀出看不到它，問題在寫入或編碼，不在「後面丟掉」；
3. 事實**在答題邊界也轉移**（與 §68 相反）→ 差異是**特徵視角**（見 §69.4），不是邊界。

這一節**不**換載體、**不**訓練、**不**加步數／寬度／資料。它只讀同一個凍結 state 的三個切面。

### 69.2 量什麼（三個邊界 × 四個目標）

語料與 checkpoint 與 §68 **完全相同**（§64 的 k=2、§65 的 k=5）：400 個已宣告結構（含兩個名冊順序）、
200 個沒見過的結構、同一份 `minimal_binding` 產生器、同一組 digest。**沒有重新生成語料**，所以任何
差異都只能來自邊界或讀出。

三個邊界都是「那一回合跑完之後」的 state（含該回合的寫入）：

| 邊界 | 回合 | 內容 |
| --- | --- | --- |
| `roster` | 名冊回合（index 1）之後 | 名冊那一句話（顏色 → 名字） |
| `evidence` | 證據回合（index 2）之後 | 證人說看到誰穿什麼顏色 |
| `answer` | 最後一回合（index 3）之後 | 最終問題（§68 的邊界，這裡重算以共用同一支儀器） |

四個目標，各自只探**它能存在的邊界**：

| 事實 | 在哪裡被說出來 | 在哪裡被探 | 判分 | chance |
| --- | --- | --- | --- | --- |
| `roster`（k 個名字的集合） | 名冊回合 | 名冊、證據、答題 | 12 個名字的 **top-k 集合**，整組相同 | `1 / C(12,k)`＝1/66、1/792 |
| `colour`（8 色之一） | 證據回合 | 證據、答題 | argmax | 1/8 |
| `pairing`（每個名冊位置的颜色） | 名冊回合 | 名冊、證據、答題 | **per-slot 正確率**（嚴格 tuple 另存） | 1/8（slot）、`1/8**k`（tuple） |
| `culprit`（12 人之一） | 無（必須推論） | 答題 | argmax，**只當陽性對照** | 1/12 |

`colour` **不**在名冊邊界被探：那時證人還沒說話，顏色在輸入裡不存在；給一個「不可知」的事實打分只會
多一列 chance，卻可能被讀成「state 沒有顏色」。

`pairing` 的 target 以 `environment.actors` 的順序定義 slot（不是那一句話的呈現順序）。§64 的順序
孿生只反轉**呈現**、不動對應，所以兩個孿生列的 pairing target 相同——這一欄量的是**關聯**，不是
「誰先被講到」。嚴格 tuple（每個 slot 都對）另存為次級讀數：k=5 時它的 chance 是 1/32768，會把
「大部分 slot 解對」誤讀成「完全沒有」，所以**閘門用 per-slot 正確率**，tuple 率只寫進 JSON。

`roster` 的集合判分沿用 §68（同一個事實形狀、同一個 chance），不改成 12 個獨立門檻。

### 69.3 程式與重用

* 新檔 `scripts/probe_pantry_boundaries.py`（`--report`、`--out`、`--check`、`--device`）。
* 重用 §68 的 `probe_pantry_contents.py`：`load_selection`（＝§67 的 trainer／probe）、
  `standardise`、`live_value`、`structure_of`、`load_probe`、`checkpoint_sha256`；重用 §66 的
  `rebuild_core`；重用 §64 的 `run_session(..., boundaries=...)`——它每回合附加一份 **dict**
  快照（`h` ＋ store 張量），`core.read_vector(dict)` 就是模型自己的讀取。
* 每個邊界只跑一次前向（`torch.no_grad()`、`core.eval()`），特徵不回流、不寫入語料。
* 載體凍結：`weights_hash` 與 checkpoint sha256 在擬合前後各記一次；`--check` 會拒收任何一項改變。
* 輸出只寫 `--out`（`data/` 已 gitignore）。`--check` 從存下來的數字**重算**八道門與分支，並要求
  pairing 的 per-slot 欄位、容量對照是**真排列**、`labels_changed ≥ 0.5`、read-only 對照列存在。
* 契約測試 `tests/test_pantry_boundaries.py`（47 條）：三個邊界的索引與拒絕、名冊順序、名冊回合
  自己的 assert、三個 target 的形狀（multi-hot／顏色索引／slot 順序）、兩個孿生列共用結構鍵、
  chance（含 `1/8**k` 與 per-slot 1/8）、多數基線（列與 slot）、單標籤／集合／tuple 兩種判分、
  容量限制的讀法、7 個分支都可達且都有 next、`--check` 對每個壞掉的欄位都會拒收、常數被釘住。

### 69.4 門檻、特徵視角與跑前就修掉的儀器缺陷（照實記）

探針預算（寫定，不因結果調整）：`steps=2000`、`batch=64`、`AdamW(lr=1e-3, weight_decay=1e-4)`、
`seed=20261121`；參考折 5 折（按結構分，同一結構的兩個呈現順序永遠同折）；容量對照用同一支探針、
同一預算、同一 seed 把**列之間的標籤置換**（`CAPACITY_SEED=20261121`）。輸出是最後一步，沒有 early
stopping、沒有挑 checkpoint。

**特徵視角（本節唯一的儀器變更）**：每個邊界擬合**兩次**——

* `state` ＝ `[h, read]`，也就是載體自己的輸出頭（`token_logits`）**實際吃到的向量**；
* `read` ＝ 只有 `read_vector`，§68 的那一欄，保留為**可比性對照**。

理由是 §68 的 N3 只讀了 `read`，而模型的答案頭讀的是 `[h, read]`；如果事實裝在 `h` 裡卻沒有被
`read` 的 query 取到，§68 的「看不到」就是**讀出位址**的問題，不是 state 的問題。兩欄都存進 JSON，
閘門用 `state` 欄，`read` 欄只用來和 §68 逐格對照。**這不是把門檻調鬆**：所有門檻的數值
（0.95／0.50／0.50）不變，變的是「用哪一個向量去問」。

| 門檻 | 條件 | 意思 |
| --- | --- | --- |
| **G0**（陽性對照） | `culprit` 在答題邊界 **in-sample ≥ 0.95**、capacity **≤ 0.50**、載體前後不變 | 讀出與最佳化真的能擬合「模型被訓練要輸出的那個標籤」；否則不得讀任何事實 |
| **G1** | `colour` 在**證據邊界**：留出 **≥ 0.50** 且 Wilson 下界 > max(1/8, 多數基線) | 顏色事實從它被說出來的回合**轉移** |
| **G2** | `colour` 在**答題邊界**（同一支儀器重算 §68） | 若成立，與 §68 矛盾 |
| **G3** | `roster` 在**名冊邊界**：留出 ≥ 0.50 且 Wilson 下界 > max(1/C(12,k), 多數基線) | 名冊事實從它被說出來的回合**轉移** |
| **G4** | `roster` 在**答題邊界** | 與 §68 對照 |
| **G5** | `pairing` 在**名冊邊界**：**per-slot** 留出 ≥ 0.50 且 Wilson 下界 > max(1/8, 多數基線) | 顏色→名字的關聯從它被說出來的回合**轉移** |
| **G6** | `pairing` 在**答題邊界**（per-slot；嚴格 tuple 另存） | 關聯有沒有被保留 |
| **G7** | `culprit`（自由線性、非名冊限定）Wilson 下界 **> 1/k** | 若成立，與 §67／§68 矛盾，先稽核 |

`CAPACITY_MAX = 0.50` 是新增的**儀器條件**，不是效果量：`readable` 只在「同一支探針在置換標籤上
擬合不到 0.50」時才有意義。若 capacity 自己就 ≥ 0.50，該格記為 `capacity_limited`，分支會照實說
「這一格分不出『沒有編碼』與『不是線性可解』」。**G0 是唯一會讓整份結果作廢的門**（B0）。

#### 跑前就修掉的儀器缺陷（數字全部丟棄）

1. **40 步煙霧測試：探針整體塌成常數。** 三個邊界的 in-sample、capacity、5 折全部一模一樣（例如
   roster 0.1425），因為 40 步內 `nn.Linear` 還沒離開初始的常數預測。**這不是發現**，是儀器還沒熱
   起來；它暴露的是「同一組數字重複出現在不同邊界」這個症狀，讓我回頭檢查特徵是否真的不同（`read`
   逐回合的 hash 不同）。整份丟棄。
2. **400 步煙霧測試：`read` 欄與 `state` 欄差距很大。** `read` 欄的 roster in-sample 0.2400、
   colour 0.1925；`state` 欄同一預算是 roster **0.5775**、colour **0.8950**（證據邊界）。這確認了
   特徵視角的差異是真的，也暴露 §68 只看 `read` 的天花板。**留出數字也在那次煙霧裡被印出來**（見
   下一段的照實記），整份仍然丟棄、不當證據。
3. **2,000 步、只用訓練段的校準：in-sample 閘門會誤判。** 在**訓練段 400 列**上跑登記的預算：
   roster in-sample **0.7700**、pairing（嚴格 tuple）**0.4575**、colour **0.9125**。也就是說，原先
   設計的「在自己回合 in-sample ≥ 0.95」會讓 **G1／G2 以『讀出擬合不足』為理由 FAIL**，機械分支
   會落到 **B0-instrument**，而 B0 的下一步（「修邊界抽取」）是**錯的**——邊界抽取沒有壞。因此在
   登記前把事實閘門改成「**在自己的回合轉移**」，並加上 G0 陽性對照；`0.95`／`0.50`／`0.50` 三個
   數值本身不變。這是**登記前的設計修正**，不是看到留出結果後調門檻。
4. **跑前修掉的實作 bug**（煙霧測試抓到，數字丟棄）：(a) tuple 讀出的 reshape 用 `labels.shape[1]`
   當寬度，`[B, 8k]` 被切成 `[B*8, k]`，`cross_entropy` 直接報 `Expected input batch_size (512) to
   match target batch_size (128)`；改成用 slot 數切 `[B*k, 8]`。(b) 多數基線的鍵原本寫成
   `roster.roster`，而閘門讀 `roster_boundary.roster`，`KeyError`；改成含 `_boundary` 的鍵。
   (c) `folds` 這個名字同時是迴圈變數與函式參數，第二次呼叫把 dict 當成 int 傳進去（`TypeError:
   'dict' object cannot be interpreted as an integer`）；改名 `fold_block`。(d) `score_predictions`
   用了模組層不存在的 `torch`（`logits.argmax` 即可），flake8 的 F821 抓到。

**照實記的丟棄量測**：第 2 項的 400 步煙霧**印過一次留出段**（roster 0.2200、colour 0.8650、
pairing per-slot 0.2025／0.5325／0.1400、culprit 0.2900）。那些數字**不是證據**：預算不是登記的
2,000 步、折數是 2 不是 5，而且它只用來確認 shape、簽名與 `--check`。但它確實讓我**看過**留出段，
所以 §69.5 的預測要標成「**看過 400 步儀器檢查之後寫的**」，不能假裝是盲的。**閘門與門檻在正式跑
之前就已固定在版控裡，跑完不會再改。**

### 69.5 預測（寫在跑之前；已看過 400 步儀器檢查，照實標註）

| 讀數 | 預測 | 理由 |
| --- | --- | --- |
| **G0** | **PASS** | `culprit` 在答題邊界的 in-sample 在 400 步煙霧已是 1.0000，capacity 0.1575；2,000 步只會更穩 |
| **G1** `colour` @ evidence | **PASS** | 400 步的留出 0.8650；顏色就寫在**當前這一回合**的句子裡 |
| **G2** `colour` @ answer | **FAIL** | 400 步 0.1250；與 §68 的 0.1450／0.0850 同向 |
| **G3** `roster` @ roster | **FAIL** | 400 步留出 0.2200；2,000 步 in-sample 0.7700，留出要同時 ≥0.50 且 Wilson 下界 > 0.0152——機會不大 |
| **G4** `roster` @ answer | **FAIL** | 400 步 0.1200；§68 的 0.1300／0.0100 同向 |
| **G5** `pairing` @ roster（per-slot） | **FAIL** | 400 步 per-slot 0.2025；in-sample（嚴格 tuple）2,000 步只有 0.4575；要 per-slot 留出 ≥0.50 機會不大 |
| **G6** `pairing` @ answer | **FAIL** | 400 步 per-slot 0.1400 |
| **G7** `culprit` > 1/k | **不成立**（不矛盾） | 400 步 0.2900（k=2）；§67 的名冊限定讀出 0.4850 也遠低於 1/2 |
| **最可能的分支** | **B5-partial-facts-held** | 顏色從自己的回合轉移、名冊不轉移：失敗有**具名的位置**，不是單一判決 |

**會讓我意外、而且必須照實寫的結果**：(a) 若 G3 在 2,000 步過線 → 分支至少是 **B4**（事實都在、
缺的是關聯）或 **B3**（三者在自己的回合都轉移）；(b) 若 G2／G4 在答題邊界過線 → **B2**，那表示
§68 的 N3 是**特徵視角**的產物（只讀 `read`），不是邊界，必須先重跑 §68 的 `read` 欄對照再談。

### 69.6 這一節**不會**證明什麼

* **不是能力分數**；核心分不變 **0.00/10**。這一節只讀一個凍結 state 的三個切面。
* **只測線性讀出**。`[h, read]` 是模型答案頭的輸入，但仍然是**一個特定的 192 維向量**；非線性可解
  不等於線性可解。`capacity_limited` 的格子會明說「分不出沒有編碼與不是線性可解」。
* **只測 k=2／k=5 兩個 checkpoint**（§64／§65），不重跑 k=3／k=4；單一 seed、單一讀出架構。
* **`roster` 的集合判分很嚴**：2-of-12 的 exact 要整組相同，0.50 的轉移門檻很高。失敗**不等於**
  零資訊——JSON 與結果表都會附上「相對 chance 的倍數」，讀者可以自己看訊號強度。
* **`pairing` 的 slot 定義是 `environment.actors` 的順序**，不是句子的呈現順序；順序孿生只改呈現，
  所以這一欄量的是關聯、不是語序。嚴格 tuple 率另存，不當閘門。
* **capacity 是下界**（同一支探針、同一預算），不是可分性上限。
* **400 步煙霧看過留出段**（§69.4），預測因此不是盲的；但閘門、門檻、協定在正式跑之前就已固定，
  跑完不改。
* 名冊、顏色都是**多選**（題目給了候選集合），不是開放式作答；`culprit` 也只在 12 人裡選。

### 69.7 指令

```
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_boundaries.py \
    --report data/pantry_stage/ord_arm/pantry_deduction_20261115-015751.json \
    --out data/pantry_stage/bounds69/k2.json
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_boundaries.py \
    --report data/pantry_stage/k5_arm/pantry_deduction_20261115-033310.json \
    --out data/pantry_stage/bounds69/k5.json
./.venv/bin/python scripts/probe_pantry_boundaries.py --check data/pantry_stage/bounds69/k2.json
./.venv/bin/python scripts/probe_pantry_boundaries.py --check data/pantry_stage/bounds69/k5.json
```

兩份都用 `--device cpu`（預設；登記的裝置）。跑完後同一條 k=2 指令重跑一次（`k2_rerun.json`），
確認決定性：除 `instrument.seconds` 外每個欄位相同。

### 69.8 分叉（跑之前寫定，機械決定下一步）

先看儀器（G0），再看矛盾（G7／G2／G4），最後才讀事實。**固定優先序**：

| 條件（依序） | 編號 | 讀法 | 下一步 |
| --- | --- | --- | --- |
| **G0 FAIL** | **B0-instrument** | 讀出／最佳化／載體有問題，任何事實都不能讀 | 修讀出預算或特徵視角後重跑；**不得**從這份結果讀任何事實 |
| G0 過、**G7 成立** | **B1-contradiction-with-§67** | 自由線性讀出在答題邊界轉移了兇手（Wilson 下界 > 1/k），與 §67／§68 相反 | 稽核這支探針與 §67 的頭、§68 的 `read` 欄，不是語料 |
| **G2 或 G4 成立** | **B2-answer-boundary-contradicts-§68** | 答題邊界**轉移**了 §68 記為缺席的事實 → 差異是**特徵視角**（`[h, read]` vs `read`），不是邊界 | 同一份 JSON 裡逐格對照 `read` 欄；必要時重跑 §68 的協定 |
| G1、G3、G5 **都成立** | **B3-held-at-their-turn-lost-by-the-answer** | 事實與關聯在**被說出來的回合**都轉移，在答題邊界都不轉移 → 這是**保留**，不是表徵 | 在證據邊界與答題邊界**之間**逐回合二分（問題回合、`al_step` 間隔），不是再探答題邊界 |
| G1、G3 成立、G5 不成立 | **B4-facts-held-mapping-missing** | 兩個事實都在自己的回合轉移，關聯在兩個邊界都不轉移 → state 裝了**零件**，不是**關係** | 直接探該回合的 store 寫入（有沒有任何 slot 以顏色文字為鍵），或登記一個關係型目標 |
| **只有一個**事實成立 | **B5-partial-facts-held** | 一個事實從自己的回合轉移、一個不轉移：失敗有**具名位置** | 對失敗的那一個事實，在**它自己的回合**換讀出家族（非線性、或直接讀 store 值），先於任何新目標 |
| 兩個事實**都不**成立 | **B6-facts-not-transferable-anywhere** | 在事實被寫下的回合也轉移不了，而陽性對照通過 → 線性讀出在**寫入處**就看不到它 | 直接探那一回合的 store 寫入（值本身，不是 read），先於新目標或更多訓練 |

不論落到哪一格，**都不得**把「加步數／加寬度／加資料」當下一步：這一節量的是同一個凍結 state 的
內容。

### 69.9 執行順序（登記在前，計分在後）

登記（§69.1–§69.8、`scripts/probe_pantry_boundaries.py`、`tests/test_pantry_boundaries.py`
47 條、產生的 `scripts/INVENTORY.json`／`ACTIVE_SCRIPTS.md`）先 commit 為 **`d3167de91`**，時間戳
**2026-11-15T11:15:36+08:00**；三個計分產出檔的寫入時間是 **11:16:42（k2）／11:17:50（k5）／
11:18:59（k2 重跑）**，全部在登記之後。指令就是 §69.7 那四行，`--device cpu`（登記的裝置），
**沒有新增訓練、沒有改語料、沒有改 checkpoint**。

| 執行 | 產出 | 裝置／成本 | `--check` |
| --- | --- | --- | --- |
| k=2（§64 `de17ed7d…`） | `data/pantry_stage/bounds69/k2.json` | cpu，**60.34 s** | **OK** |
| k=5（§65 `05c3b103…`） | `data/pantry_stage/bounds69/k5.json` | cpu，**61.41 s** | **OK** |
| k=2 重跑 | `k2_rerun.json` | cpu，59.00 s | 與 `k2.json` **除 `instrument.seconds` 外逐欄位相同** |

載體在擬合前後都沒有動：`weights_hash_before == weights_hash_after`
（k=2 `sha256:de17ed7d…`、k=5 `sha256:05c3b103…`）、checkpoint sha256 前後相同
（`cc173f9d…`／`e4d13e56…`），`carrier_unchanged`／`checkpoint_unchanged` 兩份都是 `true`，
`instrument_ok` 兩份都是 `true`。語料 digest 與 §64／§65 逐位元組相同
（k=2 `416a8a68…`／`69c730e1…`、k=5 `d6ca78a8…`／`948b08cc…`）。

### 69.10 結果（k=2 與 k=5，兩個特徵視角）

`state` 欄＝`[h, read]`（模型答案頭真正吃的向量，閘門用這一欄）；`(read)` 列＝只有 `read`
（§68 的那一欄，只用於對照）。`in-dist`＝訓練段內按結構分 5 折，`留出`＝200 個沒見過的結構。

**k=2（§64 checkpoint）**

| 邊界 | 事實 | in-sample | capacity | in-dist | 留出 | Wilson | chance | 倍數 | 閘門 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 名冊 | `roster`（top-2 集合） | 0.7700 | 0.2500 | 0.4725 | **0.2850** | 0.2269–0.3512 | 0.0152 | 18.7× | **G3 FAIL** |
| 名冊 | `pairing`（per-slot） | 0.6550 | **0.5713** | 0.1650 | 0.2250 | 0.1868–0.2684 | 0.1250 | 1.8× | **G5 FAIL**（`capacity_limited`） |
| 證據 | `colour` | 0.9125 | 0.2400 | 0.8650 | **0.8900** | 0.8391–0.9262 | 0.1250 | 7.1× | **G1 PASS** |
| 證據 | `roster` | 0.3375 | 0.0650 | 0.2350 | 0.1450 | 0.1029–0.2005 | 0.0152 | 9.5× | （未設閘門） |
| 證據 | `pairing`（per-slot） | 0.6238 | 0.2462 | 0.5150 | 0.5300 | 0.4810–0.5784 | 0.1250 | 4.2× | （未設閘門） |
| 答題 | `colour` | 0.3150 | 0.1925 | 0.1775 | **0.1400** | 0.0987–0.1949 | 0.1250 | 1.1× | **G2 FAIL** |
| 答題 | `roster` | 0.3525 | 0.0325 | 0.1800 | 0.1500 | 0.1071–0.2061 | 0.0152 | 9.9× | **G4 FAIL** |
| 答題 | `pairing`（per-slot） | 0.2925 | 0.2100 | 0.1412 | 0.1575 | 0.1251–0.1964 | 0.1250 | 1.3× | **G6 FAIL** |
| 答題 | `culprit`（陽性對照） | **1.0000** | 0.1700 | 0.9975 | 0.2850 | 0.2269–0.3512 | 0.0833 | — | **G0 PASS**；G7 不成立（0.2269 < 1/2） |

`read` 對照（同一個協定、只有向量不同）：證據邊界 `colour` in-sample 0.2350／留出 **0.1500**、
名冊邊界 `roster` 0.2925／**0.1350**、答題邊界 `culprit` 1.0000／**0.2700**——與 §68 的
0.1450／0.1300／0.2650 同向且同量級，確認**這一欄重現了 §68**。

**k=5（§65 checkpoint）**

| 邊界 | 事實 | in-sample | capacity | in-dist | 留出 | Wilson | chance | 倍數 | 閘門 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 名冊 | `roster`（top-5 集合） | 0.1525 | 0.0700 | 0.0025 | **0.0050** | 0.0009–0.0278 | 0.0013 | 4.0× | **G3 FAIL** |
| 名冊 | `pairing`（per-slot） | 0.6460 | **0.5905** | 0.1370 | 0.1500 | 0.1292–0.1735 | 0.1250 | 1.2× | **G5 FAIL**（`capacity_limited`） |
| 證據 | `colour` | **1.0000** | 0.2400 | 0.9725 | **0.9950** | 0.9722–0.9991 | 0.1250 | 8.0× | **G1 PASS** |
| 證據 | `roster` | 0.0250 | 0.0100 | 0.0000 | 0.0000 | 0.0000–0.0188 | 0.0013 | 0.0× | （未設閘門） |
| 證據 | `pairing`（per-slot） | 0.4670 | 0.2605 | 0.3060 | 0.3280 | 0.2996–0.3577 | 0.1250 | 2.6× | （未設閘門） |
| 答題 | `colour` | 0.3150 | 0.2025 | 0.1375 | **0.1100** | 0.0738–0.1609 | 0.1250 | 0.9× | **G2 FAIL** |
| 答題 | `roster` | 0.0400 | 0.0050 | 0.0025 | 0.0000 | 0.0000–0.0188 | 0.0013 | 0.0× | **G4 FAIL** |
| 答題 | `pairing`（per-slot） | 0.3205 | 0.2595 | 0.1205 | 0.1200 | 0.1013–0.1416 | 0.1250 | 1.0× | **G6 FAIL** |
| 答題 | `culprit`（陽性對照） | **0.9975** | 0.2425 | 0.9150 | 0.1150 | 0.0779–0.1666 | 0.0833 | — | **G0 PASS**；G7 不成立（0.0779 < 1/5） |

`read` 對照：證據 `colour` 0.2375／**0.1000**、名冊 `roster` 0.0225／**0.0100**、答題 `culprit`
0.9925／**0.1100**——同樣重現 §68（0.0850／0.0100／0.1100）。

兩份的機械分支都是 **B5-partial-facts-held**（`--check` 重算同一結果）。

### 69.11 三個照實記的細節（不影響分支，但影響怎麼讀）

1. **`pairing` 的閘門在兩個 k 都是 `capacity_limited`**（cap 0.5713／0.5905 > `CAPACITY_MAX` 0.50）。
   也就是說，per-slot 讀出在同一個邊界、同一預算下，**連列之間亂置換的標籤都擬合到 0.57 以上**，
   所以 G5 的 FAIL **不能**讀成「這個對應沒有被編碼」——它只能讀成「這一支讀出在這個邊界分不出
   『沒有』與『不是線性可解』」。B5 的 `next` 因此仍然指向「直接看 store 的寫入」，不是換更大的讀出。
   k=2 的嚴格 tuple 率是 in-sample 0.4575／留出 0.0400、k=5 是 0.1925／0.0000（chance 分別
   1/64、1/32768），照登記只當次級讀數。
2. **顏色在自己那一回合轉移、在答題邊界塌掉**：證據邊界 0.8900（k=2）／0.9950（k=5），答題邊界
   0.1400／0.1100，chance 0.1250。這是**保留**（retention），不是表徵——顏色曾經在 state 裡、
   頭也吃得到，到了最後一回合就不見了。**但「不見了」不是「完全沒有」**：答題邊界的 in-sample 在
   兩個 k **都剛好是 0.3150**（63/200），而同一格自己的置換容量是 0.1925／0.2025——比容量高，
   所以還有一點可分離的東西，只是它不轉移到沒見過的結構（in-dist 0.1775／0.1375、留出
   0.1400／0.1100）。照實記這個巧合（兩個不同 checkpoint、不同語料 digest、不同 k，in-sample 都是
   0.3150），沒有另外追；它不影響閘門（0.3150 < 0.95），也不影響分支。
3. **`roster` 在自己那一回合「不過線，但在 k=2 不是零」**：0.2850 是 chance（0.0152）的 **18.7 倍**，
   Wilson 下界 0.2269 遠高過 chance 與多數基線（0.0150），只是低於登記的 **0.50 效果量**，所以
   `transfers=False`。k=5 則是 0.0050 對 chance 0.0013（4.0×）、in-dist 0.0025——幾乎沒有訊號。
   所以 B5 的機械讀法（「一個事實轉移、一個不轉移」）是對的，但更精確的說法是：**顏色完全轉移；
   名冊在 k=2 有明顯但不到登記效果量的訊號，在 k=5 幾乎為零**。這也解釋了為什麼 in-dist 與留出
   在 k=2 差這麼多（0.4725 vs 0.2850）：訓練段內換結構還撐得住，換到沒見過的結構就掉一半以上。
   登記的 0.50 是**設計時**就寫下的（§69.4），不是看到 0.2850 之後改的。
4. **兩個邊界的 `read` 欄逐格重現 §68**（顏色 0.1500／0.1000、名冊 0.1350／0.0100、兇手
   0.2700／0.1100 對 §68 的 0.1450／0.0850、0.1300／0.0100、0.2650／0.1100）。所以 §68 與 §69
   **不矛盾**：§69 只是多問了 `h` 那一半，而 `h` 那一半在證據邊界確實裝了顏色
   （`read` 0.15 → `state` 0.89），在答題邊界兩半都沒有可轉移的內容。§68 的 N3 因此要收窄成
   「`read` 這個位址看不到」，不是「state 沒有」——但答題邊界的 `state` 也沒有，所以 N3 的
   **結論**站得住，理由要換。
5. **一個沒有閘門的觀察**：`pairing` 在**證據邊界**（k=2）per-slot 留出 **0.5300**
   （Wilson 0.4810–0.5784，chance 0.1250），在 k=5 只有 0.3280。§69.2 只把 pairing 閘在名冊與
   答題兩個邊界，所以這一格**不是**判定的一部分。它與「證人那一句只重新講到**一個** slot 的顏色
   （兇手那一格），其餘 slot 沒有被重新寫入」在 k=2 上剛好吻合（只解出 2 個 slot 中的 1 個 →
   0.50，實測 0.5300），但 k=5 的 0.3280 **高於**這個假設給的 0.20，所以那個解釋**不完整**。
   這是**假設，沒有量**——要驗它得把 per-slot 正確率拆開存，而登記的輸出沒有存。

### 69.12 預測對帳（8 項 + 分支，全部命中；但預測不是盲的）

| 讀數 | 預測（§69.5） | 實際 k=2／k=5 | 對帳 |
| --- | --- | --- | --- |
| G0 陽性對照 | PASS | 1.0000／0.9975，cap 0.1700／0.2425 | ✅ |
| G1 `colour` @ 證據 | PASS | 0.8900／0.9950（Wilson 下界 0.8391／0.9722） | ✅ |
| G2 `colour` @ 答題 | FAIL | 0.1400／0.1100 | ✅ |
| G3 `roster` @ 名冊 | FAIL | 0.2850／0.0050 | ✅ |
| G4 `roster` @ 答題 | FAIL | 0.1500／0.0000 | ✅ |
| G5 `pairing` @ 名冊 | FAIL | per-slot 0.2250／0.1500 | ✅ |
| G6 `pairing` @ 答題 | FAIL | per-slot 0.1575／0.1200 | ✅ |
| G7 兇手 > 1/k | 不成立 | Wilson 下界 0.2269／0.0779 | ✅ |
| 分支 | B5-partial-facts-held | B5-partial-facts-held（兩個 k） | ✅ |

**8／8 與分支都命中，但這不是盲預測**：§69.4 已照實記下 400 步儀器檢查印過一次留出段，§69.5 的
預測是在看過那一次之後寫的。真正有訊息量的是**兩件沒有預測到的事**：(a) `pairing` 的閘門在兩個 k
都 `capacity_limited`（預測只說會 FAIL，沒說會因為讀出容量而無法判讀）；(b) 顏色在答題邊界的
in-sample 在兩個 k 都是 0.3150，比自己的容量高——「塌掉」不是「歸零」。

### 69.13 這一節證明與不證明的

**證明（在登記的協定下）**：

* 顏色事實**在它被說出來的那一回合**就線性可讀、且轉移到沒見過的結構（0.89／0.995）；
  同一份 state 在**答題邊界**只剩 0.14／0.11（chance 0.125）。所以顏色是被**後面的回合弄丟的**，
  不是從沒寫進去。
* 名冊事實**沒有**達到登記的轉移效果量（k=2 0.2850 < 0.50；k=5 0.0050），所以「兩個事實都在、
  只缺組合」不成立。
* 陽性對照在同一支讀出、同一預算下 **1.0000／0.9975**，所以「讀不出來」不是讀出壞了。
* `read` 欄逐格重現 §68 → §68 的 N3 是**位址**問題，不是 state 沒有內容；但答題邊界的 `state`
  也沒有可轉移內容，所以「答題時 state 不提供這兩個事實」成立。

**不證明**：

* **只測線性讀出**（一個 `nn.Linear`、2,000 步）。非線性可解 ≠ 線性可解；`capacity_limited` 的格子
  已經明說分不出「沒有編碼」與「不是線性可解」。
* **只測 k=2／k=5 兩個 checkpoint**、單一 seed、200 個留出結構；`roster` 用整組相同的 top-k 判分，
  0.50 的效果量很高（k=2 的 0.2850 已是 chance 的 18.7 倍）。
* **證據邊界的 `pairing` 沒有閘門**（§69.11 第 5 點），它只是一個觀察，不是判定。
* **`colour` 的 8 類**包含 `grey`／`black`／`white` 這種只差一個字的色名；留出是沒見過的結構，
  標記雜訊會同時壓低 in-sample 與留出，不會製造假轉移。
* **不是能力分數**；核心分不變 **0.00/10**。這一節讀的是一個凍結 state 的三個切面。

### 69.14 下一步（B5 的機械輸出）

B5 指名的是**失敗的那一個事實，在它自己的回合，換一個讀出家族**——不是加步數、加寬度、加資料：

> 對失敗的那一個事實，在**它自己的回合**換讀出家族（非線性、或直接讀 store 值），先於任何新目標。

所以下一個階段要登記的是 `roster` 在**名冊邊界**的兩種讀法，兩者都不訓練載體：

1. **直接讀 store 的值**（那一回合寫進去的 value 向量，不是 `read` 的加權和）——如果名冊的名字
   根本沒有以可分辨的方式寫進去，換任何讀出都沒用；這一項先做，因為它排除的是「寫入」而不是
   「讀出」。
2. **非線性讀出**（同一個 2,000 步預算、同樣的置換容量對照）——如果 store 裡有、只是不在一個
   線性可切的子空間裡，這一項才會過。

另外一個**獨立**的目標（不是 B5 的下一步，但這一節把它變成可量測的）：顏色從證據邊界 0.89 掉到
答題邊界 0.14，中間只隔一個回合（問題回合）與一次 `al_step`。要問的不是「答題邊界有什麼」，而是
**那一個回合做了什麼**——逐欄位比對「證據邊界 → 問題回合之後 → 答題邊界」的 `read` 與 store，
而不是再探一次答題邊界。這一項要另外登記，不能順手塞進 B5 的階段裡。

## §70 哪一種讀出家族碰得到名冊（B5 的下一步）

### 70.1 為什麼是這一支

§69 的機械分支是 **B5-partial-facts-held**：顏色在它被說出來的回合轉移（0.8900／0.9950），名冊在
它自己的回合**沒有**達到登記的 0.50 效果量（0.2850／0.0050）。B5 指定的下一步不是加步數、寬度或
資料，而是：

> 對失敗的那一個事實，在**它自己的回合**換讀出家族（先直接讀 store 的值，再試非線性）。

所以 §70 只問一件事：**名冊到底在不在名冊邊界的 state 裡，而 §69 的線性讀出只是沒把它取出來？**
這一節把「在」與「取不出來」拆成兩個可分別裁決的量：一個**有參數**的讀出（換家族），與一個
**沒有參數**的結構檢定（同一個名冊的兩個 state 是否比不同名冊更近）。

### 70.2 量什麼（同一個載體、同一個回合、四個臂）

* 載體：§64 的 k=2 checkpoint（`de17ed7d…`）與 §65 的 k=5 checkpoint（`05c3b103…`），
  `weights_hash` 與 checkpoint sha256 在跑前跑後都要相同。
* 語料：同一份 400 段宣告／200 段留出（digest 與 §64／§65／§69 逐位元組相同），同一個名冊邊界
  （最小語料每個 session 都是 4 回合：crime 0／roster 1／evidence 2／question 3）。
* 讀出預算：2,000 步、batch 64、lr 1e-3、weight decay 1e-4、seed 20261121、訓練段統計標準化——
  **與 §69 完全相同**，只換家族。
* 四個臂：
  1. `linear_state`：§69 的那一格（`[h, read]` 上的線性讀出），**原地重算**，用來確認兩個階段
     共用同一個儀器；
  2. `linear_values`：store 的 **values** `v` 攤平後（16 × 64）上的線性讀出——這是「寫入本身」，
     不是 `read` 的加權和；
  3. `nonlinear_quad`：`[x, x*x]` 之後接線性頭（固定特徵、沒有隨機投影、沒有額外種子）；
  4. `structure`：**無參數**檢定——留出段任兩列，同一名冊組的餘弦距離是否小於不同名冊組。
     統計量是 AUC ＝ `P(same pair 較近)`，虛無假設是「名冊不留在 state 裡」，用 1,000 次
     列置換（固定距離矩陣、只換列上的名冊標籤）取 p 值。

名冊以**集合**比較（`roster_keys` 排序），所以 order twins（同一名冊、文字順序相反）算同一組。

程式：`scripts/probe_pantry_families.py`（`--report` 讀已訓練報告、`--reference` 指向 §69 的名冊格、`--check` 機械重驗）；契約測試 `tests/test_pantry_families.py` **19 條**。（§66 的 `scripts/probe_pantry_readout.py` 不動——它是 `train_pantry_selection.PROBE` 載入的模組。）

### 70.3 先量到的機制：store 不可能裝「每個名字」（訓練段，無留出）

在寫這一節的登記之前，先在**訓練段**上讀了 store 的實際內容（k=2 checkpoint，400 列，沒有碰留出）：

| 讀數 | 值 | 意思 |
| --- | --- | --- |
| 每個 run 的 `v` 有效秩（參與率） | **1.000**（最大 1.000） | 一個回合的 16 個槽共用同一個方向 |
| 槽與槽之間的平均 \|cos\| | **0.8316** | 不是 16 個獨立的記憶單位 |
| 寫入強度（`sigmoid(write_gate)`）名冊回合 | **0.716** | 寫得進去 |
| 寫入強度，證據／答題回合 | **0.004 / 0.004** | 後兩個回合幾乎不寫 |
| 寫入位址（`slot_gate` 的 argmax）名冊回合 | **16 個槽全部都是 slot 10**，最大權重 0.999997 | 位址是常數，不是內容 |
| `‖v‖` 平均 | 39.0 | — |
| `v`(證據) 與 `v`(答題) 的槽平均 cos | **0.8575**（最小 0.2817） | 後面的寫入稀釋，不是覆蓋 |

機制因此是：`end_turn` 每次只寫**一個** `value_proj(h)`，`share = strength * weights` 對所有槽相同
（`unsqueeze(-1)`），所以 `v` 的秩上限是「寫過幾個回合」，而不是「講過幾個名字」；而位址
（哪個槽）在這個 checkpoint 上是**常數**。**store 是一個回合摘要緩衝區，不是逐實體記憶**。
這使「名冊住在 store 的某個槽」在結構上不可能，也解釋了 §69 的 `pairing` 為何 `capacity_limited`。

這一段是**機制**，不是判決：它預測第 2 臂會失敗，但第 2 臂仍然要跑，因為預測必須被否證。

### 70.4 儀器校準（訓練段；跑前就修掉的兩個設計缺陷）

**缺陷一：非線性家族在 400 段上不可裁決。** 先試了一個 192→256→128→12 的 MLP（GELU，同樣
2,000 步）：名冊 in-sample **0.9975**、留出 0.3150，但**置換標籤的容量也是 0.9875**——它連亂數
標籤都擬合得起來，所以它的留出分數不能讀成「沒有編碼」。改成寬度階梯（同樣 2,000 步、同樣
optimizer），在**訓練段**上量（名冊 in-sample／名冊容量；括號是陽性對照 culprit 的 in-sample／容量）：

| 家族 | 名冊 in-sample | 名冊容量 | culprit in-sample | culprit 容量 | 可裁決？ |
| --- | --- | --- | --- | --- | --- |
| 線性 `[h, read]`（§69） | 0.7700 | 0.2500 | 1.0000 | 0.2350 | 是（但擬合不足） |
| MLP 192→256→128→12 | 0.9975 | **0.9875** | 1.0000 | 0.6350 | 否 |
| MLP 192→128→12 | 0.9825 | **0.9250** | 1.0000 | 0.6350 | 否 |
| MLP 192→64→12 | 0.9700 | **0.8550** | 1.0000 | 0.4875 | 否 |
| MLP 192→32→12 | 0.9475 | **0.6925** | 1.0000 | 0.4150 | 否 |
| MLP 192→16→12 | 0.8650 | 0.3725 | 1.0000 | 0.2975 | 容量合格，但 in-sample < 0.95（擬合不足） |
| `[x, x*x]` 線性頭 | 0.9375 | **0.5650** | 1.0000 | 0.3475 | 否（in-sample 0.9375、容量 0.5650） |
| 固定 `tanh(·32)` 特徵＋線性頭 | 0.8025 | 0.2950 | 1.0000 | 0.2650 | 容量合格，但 in-sample 0.8025（擬合不足） |
| 固定 `tanh(·64)` 特徵＋線性頭 | 0.7975 | 0.3250 | 1.0000 | 0.2700 | 同上 |

也就是說：在 400 段上，**「容得下真標籤」與「容不下置換標籤」的窗口是空的**。這是取樣數的
性質，不是家族選錯；MLP-256-128 那組數字**作廢**（它證明了容量問題，不是名冊的問題）。

選定家族的規則（寫在這裡、跑之前）：**在通過陽性對照（culprit in-sample ≥ 0.95、容量 ≤ 0.50）
的家族中，取名冊 in-sample 最高者** → `[x, x*x]`（0.9375／0.5650）。這條規則只用訓練段
in-sample，沒有碰留出，也不因為留出數字而改。

**缺陷二：兩個有參數的臂註定讀不出結論。** 既然非線性臂的容量 > 0.50、值臂的 in-sample < 0.95，
只跑 B5 指名的兩臂會以「無法裁決」收尾。因此這一節多登記一個**沒有參數**的臂（`structure`）：
它不擬合任何東西，所以容量問題不存在，而它問的正是「名冊有沒有留在 state 裡」。它不是把別的
題目塞進來——它量的是同一個事實、同一個邊界、同一批列。它的門檻（AUC ≥ 0.65、p ≤ 0.001、
1,000 次置換）也在跑之前固定。

訓練段上的結構檢定讀數（校準，不是判決）：AUC **0.8287**、置換虛無均值 0.5014、200 次置換下
p 已到下限（0.005）。79,800 對中有 1,520 對同名冊、57 個不同名冊——統計量可用。留出段沒有
order twins（每個結構唯一），同名冊對只來自名冊碰撞，所以留出比訓練段**更難**，這一點照實記。

### 70.5 閘門（跑之前寫定；門檻沿用 §69，只有結構檢定是新數字）

| 閘門 | 條件 | 讀什麼 |
| --- | --- | --- |
| **H0 儀器** | 三個有參數家族**各自**的 culprit in-sample ≥ 0.95 且容量 ≤ 0.50，且載體未動 | 任何一個家族不能擬合載體自己的標籤，這一輪就沒有讀數 |
| **H1 重現** | `linear_state` 的 in-sample／容量／in-dist／留出**逐格等於** `bounds69/k2.json` 的名冊格 | 兩節共用同一個儀器 |
| **H2 值臂可讀** | `linear_values` in-sample ≥ 0.95 | 讀不出來 vs 沒編碼的分界 |
| **H3 非線性可裁決** | `nonlinear_quad` in-sample ≥ 0.95 **且** 容量 ≤ 0.50 | 同上；容量 > 0.50 就叫 `capacity_limited` |
| **H4 幾何分得開** | 留出 AUC ≥ 0.65 **且** p ≤ 0.001 **且** 同／不同名冊對都 > 0 | 無參數，容量買不到 |
| **H5 值臂轉移** | 留出 ≥ 0.50 且 Wilson 下界 > max(chance, 多數基線) | §69 的 `fact_gate`，同一支 |
| **H6 非線性轉移** | 同上，套在 `nonlinear_quad` | 只有在 H3 過時才可讀 |

`chance` 仍是 `1/C(12, k)`（k=2 為 1/66 = 0.0152、k=5 為 1/792 = 0.0013）。

### 70.6 分叉（跑之前寫定，機械決定下一步；固定優先序）

| 分支 | 條件 | 下一步 |
| --- | --- | --- |
| **B0-instrument** | H0 不過或載體移動 | 修家族／預算，不從這一輪讀任何名冊結論 |
| **B1-store-values-hold-the-roster** | H2 且 H5 | 名冊在**寫入**裡；問 `read_vector` 為何取不出 store 已有的值 |
| **B2-nonlinear-readout-holds-the-roster** | H3（可讀且容量合格）且 H6 | 名冊以非線性形式在 state 裡；找出那個特徵再測答題邊界 |
| **B3-roster-present-but-not-fittable** | H4 過，但 B1／B2 都不成立 | **停止在 400 段上換有參數的讀出**；改成**干預**名冊那一句（只換一個名字），問 state 是否移到編輯後名冊的鄰域 |
| **B4-roster-absent-at-its-own-turn** | H4 也不過 | 名冊在**它自己的回合**就沒有留下痕跡；問那個回合的寫入與 token state，不是再加讀出家族 |

### 70.7 預測與否證（寫在跑之前）

| 讀數 | 預測 | 否證條件 |
| --- | --- | --- |
| H0 | PASS（三個家族都能擬合 culprit、容量 ≤ 0.50；§69 的線性與訓練段校準都如此） | 任一家族 in-sample < 0.95 或容量 > 0.50，或載體移動 |
| H1 | PASS（同一支程式、同一 seed，應逐格相等） | 任何一格不等 → 特徵抽取與 §69 不同，兩節不可比 |
| H2 | **FAIL（可讀＝否）**，in-sample ≈ 0.4975（訓練段校準） | in-sample ≥ 0.95 |
| H3 | **FAIL（可裁決＝否）**，in-sample ≈ 0.9375、容量 ≈ 0.5650 → `capacity_limited` | in-sample ≥ 0.95 **且** 容量 ≤ 0.50 |
| H4 | **PASS**（訓練段 AUC 0.8287、p 已到下限；留出更難，可能低一些） | 留出 AUC < 0.65 或 p > 0.001 |
| H5 | FAIL | 留出 ≥ 0.50 且 Wilson 下界過地板 |
| H6 | FAIL | 同上 |
| 分支 | **B3-roster-present-but-not-fittable** | 任何更高優先序的分支成立 |

**這一輪的預測不是盲的**：§70.3／§70.4 的機制與校準都在訓練段上做過，而我已經看過 §69 的留出
數字（那正是這一節的起點）。但四個新臂的**留出**數字一個都沒看過；H1 是重現檢查，不是預測。

### 70.8 什麼會讓這一節作廢

1. H1 不過（`linear_state` 與 §69 的名冊格不逐格相同）——代表特徵抽取、標準化或邊界選錯，整份
   輸出的比較無效；
2. 載體 `weights_hash` 或 checkpoint sha256 前後不同（探針不得訓練載體）；
3. 結構檢定的同／不同名冊對有一邊為 0（問題未定義），或置換全為退化分割；
4. 任何人為改動門檻、語料、seed、家族清單或分支表——改動必須以 amendment 另記，不能就地改。

**這一節不是能力分數**；核心分不變 **0.00/10**。

### 70.9 執行順序（登記在前，計分在後）

登記 commit `f630d795d`（`2026-11-15T11:44:37+08:00`）。之後的每一次執行都照時間記下來，包含**作廢**
的那一次：

| 時間 | 產物 | 狀態 |
| --- | --- | --- |
| 11:45:04 | `data/pantry_stage/readout70/k2_void_unstandardised.{json,log}` | **作廢**（見下） |
| 11:47:15 | `data/pantry_stage/readout70/k2.json` | 計分（k=2） |
| 11:47:35 | `data/pantry_stage/readout70/k5.json` | 計分（k=5） |
| 11:48:04 | `data/pantry_stage/readout70/k2_rerun.json` | 重現檢查 |

**作廢的那一次**：結構檢定被套在**未標準化**的 `[h, read]` 上。餘弦距離對每一維的尺度敏感，而
`h`（128 維）與 `read`（64 維）的尺度不同，逐維標準化正是 §70.2 登記的視角——登記檔本身在
`probe.structure.distance` 欄寫的是 `"cosine on the standardised [h, read]"`，那一欄在 commit
`f630d795d` 裡，跑之前就固定了。所以第一次跑的是**另一個度量**，不能拿來當這一節的讀數：

* 作廢的讀數（照實記，不採用）：train AUC **0.7875**、held-out **0.6939**（p 0.001、270 對）；
* 修正後（登記的度量）：train **0.8287**、held-out **0.7699**。

作廢那一次的**分支**剛好也是 B3，但這不構成「可以留著」的理由：這一節的門檻是 AUC ≥ 0.65，
兩組都過，可是**數字**是這一節的產物，換度量就是換題目。整個檔案留在 `data/` 並在這一節標明作廢，
不刪除、不覆蓋、不混進計分表。

修正只動**實作**（把 `structure_test` 的輸入換成 `standardised("linear_state")`），沒有動門檻、語料、
seed、家族清單或分支表。

三次計分執行的 `--check` 都是 `OK`；`instrument_ok=True`；兩份 checkpoint 的 `weights_hash` 與 sha256
在跑前跑後相同（k=2 `de17ed7d…`／`cc173f9d…`，k=5 `05c3b103…`／`e4d13e56…`）；語料 digest 與
§64／§65／§69 逐位元組相同（k=2 `416a8a68…`／`69c730e1…`，k=5 `d6ca78a8…`／`948b08cc…`）。
`k2_rerun` 與 `k2` 除 `instrument.seconds`（14.85 s／14.72 s）與時間戳外**逐欄位相同**，置換虛無
陣列也逐位元相同。

### 70.10 結果（k=2 與 k=5）

名冊邊界、同一批 400 段宣告／200 段留出、同一個 2,000 步預算。chance 是 `1/C(12, k)`
（k=2 0.0152、k=5 0.0013）；多數基線在 k=2 是 0.0150、k=5 是 0.0050（k=5 時**多數基線比 chance
更難過**，所以地板是 0.0050，不是 0.0013）。

**k=2（§64 的載體）**

| 臂 | in-sample | 置換容量 | in-distribution | 留出 |
| --- | --- | --- | --- | --- |
| `linear_state`（§69 那一格） | 0.7700（308/400） | 0.2500 | 0.4725 | **0.2850**（57/200） |
| `linear_values` | 0.4975（199/400） | 0.1650 | 0.2625 | **0.1400**（28/200） |
| `nonlinear_quad` | 0.9375（375/400） | **0.5650** | 0.4600 | **0.3000**（60/200） |

陽性對照（答題邊界的 culprit，載體被訓練要吐出的那一個標籤）：`linear_state` 1.0000／容量 0.1700、
`linear_values` 1.0000／0.3600、`nonlinear_quad` 1.0000／0.2675 → 三個家族都讀得到載體自己的標籤，
且都容不下置換標籤。**讀出沒有壞**。

| 結構檢定 | AUC | p | 同／不同名冊對 | 不同名冊 | 虛無均值／上界 |
| --- | --- | --- | --- | --- | --- |
| train | 0.8287 | 0.0010 | 1,520／78,280 | 57 | 0.5002／0.5326 |
| held-out | **0.7699** | **0.0010** | 270／19,630 | 66 | 0.5006／0.5633 |

→ H0 PASS、H1 PASS、H2 FAIL、H3 FAIL（`capacity_limited`）、H4 PASS、H5 FAIL、H6 FAIL
→ **B3-roster-present-but-not-fittable**。

**k=5（§65 的載體）**

| 臂 | in-sample | 置換容量 | in-distribution | 留出 |
| --- | --- | --- | --- | --- |
| `linear_state` | 0.1525（61/400） | 0.0700 | 0.0025 | **0.0050**（1/200） |
| `linear_values` | 0.0850（34/400） | 0.0300 | 0.0025 | **0.0050**（1/200） |
| `nonlinear_quad` | 0.4575（183/400） | 0.2550 | 0.0075 | **0.0150**（3/200） |

陽性對照：`linear_state` 0.9975／0.2425、`linear_values` 0.9975／0.2175、`nonlinear_quad`
1.0000／0.3125。

| 結構檢定 | AUC | p | 同／不同名冊對 | 不同名冊 | 虛無均值／上界 |
| --- | --- | --- | --- | --- | --- |
| train | 0.8034 | 0.0010 | 296／79,504 | 177 | 0.5008／0.5494 |
| held-out | **0.5498** | **0.1918** | **24**／19,876 | 176 | 0.4989／0.6936 |

→ H0 PASS、H1 PASS、H2 FAIL、H3 FAIL（但**不是** `capacity_limited`）、H4 FAIL、H5 FAIL、H6 FAIL
→ **B4-roster-absent-at-its-own-turn**。

H5／H6 的 Wilson 區間（同一個 `fact_gate`）：k=2 值臂 [0.0987, 0.1949]、非線性 [0.2407, 0.3668]；
k=5 值臂 [0.0009, 0.0278]、非線性 [0.0051, 0.0432]。k=5 的兩者的下界都低於 0.0050 的多數基線地板。

### 70.11 照實記的限制（哪些讀數不能那樣讀）

1. **k=5 的 H4 是「量不到」，不是「證明沒有」。** 200 段留出、`C(12,5)=792` 個名冊，同名冊對只由
   碰撞產生，實測只有 **24 對**（不同名冊 19,876 對）。在 1,000 次置換下，虛無上界可以到 **0.6936**
   ——也就是說單次置換就能靠運氣拿到 0.69。這個樣本量下 p ≤ 0.001 幾乎不可達（最小可達 p 是
   1/1001），所以 0.5498／p 0.1918 只能讀成「在這個檢定力下沒有看到」。同一個 k 的**訓練段**
   （296 對）是 0.8034／p 0.001，所以 carrier 本身在 k=5 也留了痕跡；留出看不到是**對數太少**。
   這一點沒有用「加資料」在事後補救——那會是看過結果之後改設計。
2. **非線性臂在兩個 k 失敗的理由不同。** k=2 是 `capacity_limited`（0.5650 > 0.50）：它容得下真標籤，
   也容得下亂數標籤，所以它的 0.3000 不能讀成「沒有編碼」。k=5 是**擬合不足**（0.4575 < 0.95、
   容量 0.2550 合格）：它在訓練段就吃不下來，所以它的 0.0150 也不能讀成「沒有編碼」。兩邊都不是
   「證明不在」，而是「這個儀器在 400 段上不能裁決」。§70.4 的寬度階梯已經說明這個窗口在 400 段上
   是空的；這一輪只是把它在留出上重現一次。
3. **值臂連 in-sample 都吃不下（0.4975／0.0850）**，與 §70.3 的機制預測一致：`end_turn` 每回合只寫
   一個 `value_proj(h)`、16 個槽共用同一個 share、位址是常數 slot 10。這是**機制被確認**，不是
   「名冊不在 store 裡」的獨立量測——它本來就不可能在那裡。
4. **結構檢定是粗訊號。** 它只說「同名冊的 state 在餘弦上比較近」，沒有說 (a) 名字讀得出來、
   (b) 順序保留、(c) 那個痕跡**就是名字**。同一個名冊的兩個 session 在名冊那一回合的文字也比較像
   （同一批 token），所以「同字面 → 近 state」與「同名冊 → 近 state」在這個設計下分不開。這是
   無參數的代價：它換來「容量買不到」，代價是「語意不保證」。
5. **0.7699 是真訊號但很弱**（地板 0.65）：它足以推翻「那個回合什麼都沒留下」，不足以說「名冊被
   編碼成可用的綁定」。
6. **兩個 k 都是診斷，不是能力分數。** 核心分不變 **0.00/10**；這一節沒有任何一格可以拿去當
   「模型會了」。

### 70.12 預測對帳（登記的八項 × 兩個 k）

| 讀數 | 登記的預測 | k=2 實際 | k=5 實際 | 對帳 |
| --- | --- | --- | --- | --- |
| H0 儀器 | PASS | PASS | PASS | 兩個 k 都中 |
| H1 重現 | PASS（逐格等於 `bounds69`） | PASS | PASS | 兩個 k 都中 |
| H2 值臂可讀 | FAIL（≈0.4975） | 0.4975 FAIL | 0.0850 FAIL | 方向兩個 k 都中；數字只對 k=2（預測寫的是 k=2 校準） |
| H3 非線性可裁決 | FAIL，`capacity_limited`（0.9375／0.5650） | 0.9375／0.5650 FAIL | 0.4575／0.2550 FAIL，**不是** `capacity_limited` | k=2 中（含理由）；k=5 方向中、**理由不中** |
| H4 幾何分得開 | PASS | 0.7699／0.001 PASS | 0.5498／0.1918 FAIL | k=2 中；k=5 **不中** |
| H5 值臂轉移 | FAIL | 0.1400 FAIL | 0.0050 FAIL | 兩個 k 都中 |
| H6 非線性轉移 | FAIL | 0.3000 FAIL | 0.0150 FAIL | 兩個 k 都中 |
| 分支 | B3 | B3 | **B4** | k=2 中；k=5 **不中** |

k=2：**8/8**。k=5：**方向 6/8**（H4 與分支不中），把 H3 的理由也算進去是 **5/8**。

**miss 的是哪一種 miss**：不是「名冊在 k=5 被證明不在」，而是「k=5 的留出只有 24 對同名冊，這個
檢定在那裡量不到」（§70.11 第 1 點）。登記時把 H4 寫成「留出更難，可能低一些」——低到 0.5498 是
**超過**「低一些」的，照實記為預測失準，不改寫成「本來就知道」。

### 70.13 這一節證明什麼、不證明什麼

**證明**（k=2）：

* 名冊那一回合的 state **有**與名冊集合相關的幾何：留出 AUC 0.7699、p 0.001、270／19,630 對、
  虛無上界 0.5633，而且**沒有擬合任何參數**（容量不可能製造它）；
* 因此 §68／§69 的線性失敗**不是**「那個回合什麼都沒寫」——失敗發生在**讀出**，不在**寫入的有無**；
* 值臂的失敗與 §70.3 的機制（秩 1、常數位址、每回合一個 value）一致；
* 兩個階段共用同一個儀器（H1 逐格重現），所以 §69 與 §70 的數字可以直接並排。

**不證明**：

* 不證明「換更大的讀出就一定拿得到」——只證明在這個 400 段預算、這三個家族下，可讀與容量乾淨的
  窗口是空的；
* 不證明那個痕跡**是名字**（見 §70.11 第 4 點）；
* 不證明 k=5 也一樣（檢定力不足）；
* 不改變 §68 對**答題邊界**的結論：答題邊界仍然沒有可轉移的名冊內容。

### 70.14 下一步（B3 與 B4 的機械輸出）

B3 指名的是**干預**，不是再加讀出家族；B4 指名的是**看那個回合本身**。兩者在同一個實驗裡可以
同時回答，所以下一個階段（§71）登記**一個**干預檢定，同時覆蓋 B3 與 B4：

> 只改**名冊那一句**的文字（把一個名字換成不在該 session 裡的名字），其餘每一個位元組不動，
> 重算名冊邊界的 state，然後問兩件事：
> (a) state **有沒有動**（與原 state 的距離 > 0，且大於一個無操作編輯的距離）；
> (b) 動的方向**是不是朝向編輯後名冊的鄰域**（在未編輯的留出 state 裡做最近鄰，不擬合任何參數）。
> 同時跑兩個對照：**order twin**（同一個名冊、順序顛倒）與**no-op**（只改空白）。

判讀是機械的：若 (a) 不動 → 那個回合的 state 與名冊文字無關（B4 的形狀）；若 (a) 動了但 order twin
動得一樣多、最近鄰也沒有偏向編輯後名冊 → 痕跡是**字面**而不是**名冊**（§70.11 第 4 點被證實）；
若 (b) 成立 → 名冊在 state 裡是可尋址的，下一步才問「為什麼讀不出來」。

這一項要**另外登記**（門檻、對照、名冊編輯規則、留出切割都寫在跑之前），不能順手接在這一節後面跑。
**不加步數、不加寬度、不加資料**——這是 B3／B4 的條件。

## §71 名冊那一句有沒有造成 state 裡的名冊（干預，不擬合）

### 71.1 為什麼是這一支

§70 的機械輸出是 **B3-roster-present-but-not-fittable**（k=2：同名冊的 state 在幾何上比較近，AUC
0.7699、p 0.001；但值臂 in-sample 0.4975、非線性容量 0.5650，沒有可裁決的讀出家族）與
**B4-roster-absent-at-its-own-turn**（k=5：留出只有 24 對同名冊，這個檢定在那裡沒有檢定力）。
B3 指定的下一步是**干預名冊那一句**；B4 指定的是**看那個回合本身**。兩者是同一個實驗。

§70.11 第 4 點已經記下這個實驗為什麼不能只換一個名字：**同名冊的兩個 session，名冊那一回合的文字
也比較像**（同一批 token）。所以「改了名字之後 state 落在編輯後名冊的鄰域」與「state 追蹤那一行
的字面」在只做一次編輯時分不開——因為編輯後的那一行**就是**那個名冊的某一種真實寫法。要分開，
就需要**兩個受控編輯**當對照。

### 71.2 量什麼（同一句、三個等長編輯、三個無參數量）

對 200 段留出 session，各自產生三個編輯，**只改名冊那一回合的 `user_input`**，其餘位元組不動：

| 編輯 | 改什麼 | 名冊集合 | 字面 |
| --- | --- | --- | --- |
| `swap` | 一個名字換成**同 byte 長度**、不在名冊裡的名字 | **變** | 變成另一個名冊的真實寫法 |
| `reverse` | 子句順序顛倒（同名字、同顏色） | 不變 | 變（語料自己的 order twin） |
| `colour` | 一個顏色詞換成這一行沒用過的顏色（同寬度） | 不變 | 變 |

名字依長度分兩群（4 byte 與 5 byte），每一群都比一個名冊大，所以**同長度替代永遠存在**；顏色詞
都是 2 個字。因此三個編輯都**保持名冊那一回合的 token 數不變**——這一點在跑之前就固定，並在
`instrument.token_counts_matched` 裡機械檢查。

三個讀數（都**不擬合**任何參數）：

1. `movement` ＝ `1 − cos(state_edited, state_original)`：那一行改了，state 有沒有動？
2. `lift`（只對 `swap`）＝ 每一列「與**編輯後**名冊的未編輯 state 的平均 cos」減「與**原本**名冊的
   平均 cos」。虛無假設是「state 不帶名冊身分」，所以這兩個平均在列上交換無關，檢定用**逐列符號
   翻轉**（1,000 次、固定 seed），不需要任何擬合。
3. `retention`（對 `reverse` 與 `colour`）＝ 編輯後「與**自己**名冊的未編輯 state 平均 cos」減
   未編輯 state 的同一個平均。名冊集合沒變，所以「state 追蹤的是集合」預測這個差 ≈ 0；
   「state 追蹤的是字面」預測它**變負**（改過的行不再像任何真實的那個名冊的寫法）。

**判讀的關鍵是 `swap` 與兩個對照的組合**：`swap` 一定會把 state 帶到「編輯後名冊的真實寫法」
附近，無論 state 追蹤的是集合還是字面。真正分開兩者的是 `reverse`／`colour` 的 retention。

參考池是 400 段訓練＋200 段留出的**未編輯** state（600 列），比較時排除該列自己的 session。

### 71.3 程式

* 探針：`scripts/probe_pantry_intervene.py`（`--report` 讀已訓練報告、`--check` 機械重驗）；
* 契約測試：`tests/test_pantry_intervene.py` **23 條**（三個編輯的等長／單一子句／順序不變、
  符號翻轉的虛無、鄰域與 retention 的方向、分支優先序、`--check` 會拒絕被改過的 p 值）。

探針重用 §70 的邊界抽取（`scripts/probe_pantry_families.py`）與 §66 的載體重建
（`scripts/probe_pantry_readout.py`），所以三個階段的特徵視角是同一個。

### 71.4 登記的門檻，與 k=5 為什麼只報 movement

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `EDIT_MOVEMENT_FLOOR` | **1e-3** | 重跑的 state 逐位相同（`determinism_min_cosine ≥ 1 − 1e-6`），所以任何 > 1e-3 的移動都不是雜訊 |
| `LIFT_ALPHA` | **0.001** | 與 §70 的結構檢定同一個 alpha |
| `LIFT_PERMUTATIONS` | **1,000** | 同上 |
| `LIFT_SEED` | **20261124** | 跑前固定；`retention` 的兩個檢定用 +1／+2 |
| `RETENTION_FLOOR` | **−0.01** | 「沒有把 state 推離自己的名冊」的容許量；比 0 稍負是給有限樣本的抖动 |
| `MIN_LIFT_ROWS` | **50** | 少於 50 列有參考，就不宣稱 neighborhood 的結論 |

**k=5 只報 movement／retention**：600 列參考、`C(12,5)=792` 個名冊，多數編輯後的名冊在參考池裡
**一列都沒有**，所以「編輯後的名冊鄰域」在那個 k 上多半無定義。這一點寫在跑之前，不是事後解釋；
k=5 的 `lift` 會照實報 `rows_compared`／`rows_missing_reference`，但分支會落到
**J4-neighbourhood-underpowered**，不會被讀成「沒有名冊」。

### 71.5 閘門（跑之前寫定）

| 閘門 | 條件 |
| --- | --- |
| **J0 儀器** | 未編輯重跑逐位相同（`determinism_min_cosine ≥ 1−1e-6`）、三個編輯都改變位元組、三個編輯都保持名冊回合的 token 數、載體 `weights_hash` 與 checkpoint sha256 前後相同 |
| **J1 編輯移動 state** | `swap` 的平均 movement > **1e-3** |
| **J2 swap 落在編輯後名冊** | 有定義的列 ≥ **50**、`lift` 平均 > 0、符號翻轉 p ≤ **0.001** |
| **J3 順序與顏色不移動名冊** | `reverse` 與 `colour` 的 retention 平均皆 ≥ **−0.01** |
| **J4 鄰域檢定力** | 有定義的列 ≥ 50（否則這一輪不裁決鄰域問題） |

`top1_rate`（編輯後 state 的最近參考是否落在編輯後名冊）**只描述、不設門檻**，chance 是
`1/不同參考名冊數`（k=2 約 1/66）。

### 71.6 分叉（跑之前寫定，機械決定；固定優先序）

| 分支 | 條件 | 下一步 |
| --- | --- | --- |
| **J0-instrument** | J0 不過 | 修編輯管路（決定性／位元組／token 數），不從這一輪讀任何東西 |
| **J3-state-ignores-the-turn-text** | J1 不過 | 那個邊界的 state 不是那一行的函數——這會**反過來質疑 §70 的結構結果**，必須先解釋同名冊的鄰近從哪裡來 |
| **J4-neighbourhood-underpowered** | J1 過，但有定義的列 < 50 | 保留 movement 的結果；名冊問題只在名冊空間夠小的 k 上問 |
| **J1-roster-line-sets-the-roster** | J2 過 **且** J3 過 | 名冊在 state 裡是可尋址的，而且追蹤的是**集合**；下一步問讀出為什麼取不出來（位址碰撞 vs 疊加），用逐槽探針 |
| **J2-the-trace-is-the-line-not-the-roster** | J1 過，J2/J3 其餘情況 | §70.11 第 4 點成立：state 追蹤的是**那一行**，不是名字的集合；停止把名冊邊界當成名冊表徵，改看回合內名字的 token state 與 `end_turn` 寫了什麼 |

### 71.7 預測與否證（寫在跑之前）

| 讀數 | 預測 | 否證條件 |
| --- | --- | --- |
| J0 | PASS | 任一項（決定性、位元組、token 數、載體）不過 |
| J1 | PASS（改一個 token，那一回合的 state 應該會動） | movement ≤ 1e-3 |
| J2（k=2） | **PASS**（§70 已量到同名冊鄰近，而編輯後的行是編輯後名冊的真實寫法） | 有定義的列 < 50，或平均 ≤ 0，或 p > 0.001 |
| J3（k=2） | **FAIL**（預測 state 追蹤那一行：反轉順序與換顏色都會把它推離自己的名冊） | 兩個 retention 都 ≥ −0.01 |
| 分支（k=2） | **J2-the-trace-is-the-line-not-the-roster** | J1（兩個 retention 都過）或 J3／J4 |
| 分支（k=5） | **J4-neighbourhood-underpowered** | 有定義的列 ≥ 50 且 J2 有結論 |

**這一輪的預測不是盲的**：§70 的留出結構數字已經看過，§70.3 的機制（每回合一個 value、常數位址）
也已量過。但三個編輯的留出讀數（movement／lift／retention）**一個都沒看過**；J1 的預測來自「輸入
變了、state 應該跟著變」，與名冊無關。

### 71.8 什麼會讓這一節作廢

1. J0 不過（重跑不逐位相同、編輯沒改位元組、或編輯改變了 token 數）——代表編輯管路有問題，
   整份輸出的比較無效；
2. 載體 `weights_hash` 或 checkpoint sha256 前後不同（探針不得訓練載體）；
3. 有定義的列 < 50：k=2 這一輪不裁決鄰域問題（k=5 本來就登記為不裁決）；
4. 任何人為改動門檻、編輯規則、參考池、seed 或分支表——改動必須以 amendment 另記。

**這一節不是能力分數**；核心分不變 **0.00/10**。

### 71.9 修正：登記裡有一句是錯的（跑之前就發現）

§71.2 寫著「名字依長度分兩群（4 byte 與 5 byte），每一群都比一個名冊大，所以**同長度替代永遠
存在**」。**這句話在 k=5 不成立**：4 byte 的名字只有五個（Alex／Hana／Ivan／Judy／Lena），一個
五人名冊可以剛好把它們用完，此時那一類沒有 outsider。k=2 不受影響（兩人的名冊最多佔一類的兩個
名額，而兩類各有 5 與 7 個 outsider），所以 k=2 的登記沒有錯，錯的是把它當成一般敘述。

**發現的時機**：k=5 第一次執行時，`minimal_pantry_214`（`['Ivan','Alex','Hana','Judy','Lena']`，
五個都是 4 byte）讓探針以 `SystemExit` 中止——**當時沒有任何 k=5 的計分數字存在**，所以這個錯誤
沒有被用來調整任何讀數。

**修正（跑之前套用）**：`edit_swap` 不再假設替代存在，而是先找出**還有 outsider 的長度類**；若一類
都沒有，回傳 `None`，該 session 的 `swap` 臂**跳過並計數**（`edits.swap_skipped`），**不**改成不同
長度的名字（那會改變 token 數，破壞登記的「等 token 數」不變量）。`reverse`／`colour` 不受影響，
任何名冊都做得到。k=5 實測跳過 **2** 段（`minimal_pantry_214`、`minimal_pantry_324`，兩者的名冊都
剛好是那五個 4 byte 名字），所以 198 列；k=2 跳過 **0** 段。

**修正沒有改變 k=2 的任何分數**：修正後重跑 k=2 得到 `k2_amended.json`，與修正前的計分檔 `k2.json`
逐欄位比對，**所有數字欄位相同**（movement 0.333621／0.233220／0.166692、lift 0.130641／p 0.001／
199 列、top1 45/199、retention +0.007788／−0.001729，以及兩個分支的判定），`--check OK`。不同的只有
`instrument.seconds`（2.63 s → 2.34 s）、新增的欄位（`n_rows`、`swap_rows`、`swap_skipped`）與
`gates.J0_instrument.reading` 的說明文字。這正是「修正不可能動到 k=2 的分數」的機械證據，而不是
一句宣稱。

**另記一個管路瑕疵**（同樣沒有動到數字）：第一次 k=2 計分執行時，`J4_neighbourhood_power` 沒有
`pass` 旗標，所以顯示 FAIL，但分支仍然是 J1——J4 在那一輪是「有定義（199 ≥ 50）」，顯示與判定
不一致。修法是依登記條件補上 `"pass": bool(lift_defined)`；該次輸出留在
`k2_preflag.{json,log}`（2.41 s），與計分檔 `k2.json` 數字完全相同。

**執行順序**（登記 commit `a6ad25c97`，之後每一次執行都記下來）：

| 時間（+08:00） | 產物 | 狀態 |
| --- | --- | --- |
| 12:06:52 | `intervene71/k2_preflag.{json,log}` | 計分（J4 顯示瑕疵，數字與下一列相同） |
| 12:07:15 | `intervene71/k2.json` | 計分（k=2，修正前程式） |
| 12:10:36 | `intervene71/k2_amended.{json,log}` | 修正後重跑（不變性證據） |
| 12:10:50 | `intervene71/k5.{json,log}` | 計分（k=5，修正後程式） |

三份 `--check` 都是 `OK`（k=2 修正前的檔案也重驗得同一個分支：`check()` 對「沒有 `n_rows` 欄」的
舊檔以 `per_row` 長度回推，這是相容讀法，不是重評分）。`instrument_ok=True`；載體前後相同
（k=2 `de17ed7d…`／`cc173f9d…`，k=5 `05c3b103…`／`e4d13e56…`）；`determinism_min_cosine` 兩份都是
**1.0**；語料 digest 與 §69／§70 逐位元組相同（k=2 `416a8a68…`／`69c730e1…`，k=5 `d6ca78a8…`／
`948b08cc…`）。

### 71.10 結果（k=2）

400 段訓練＋200 段留出；參考池 600 段未編輯 state（66 個不同名冊＝`C(12,2)` 的全部）。

| 編輯 | 列數 | movement（1 − cos） |
| --- | --- | --- |
| `swap` | 200（跳過 0） | **0.333621** |
| `reverse` | 200 | 0.233220 |
| `colour` | 200 | 0.166692 |

| 讀數 | 值 |
| --- | --- |
| `lift`（`swap`，199 列；1 列參考池裡沒有編輯後名冊） | **0.130641**，符號翻轉 **p 0.001** |
| `top1`（描述性） | 45/199 ＝ **0.2261**，chance 0.0152（1/66）→ 14.9× |
| `retention` `reverse` | 0.677183 vs 未編輯 0.669394 → **+0.007788**（p 0.2927） |
| `retention` `colour` | 0.667665 vs 0.669394 → **−0.001729**（p 0.5704） |
| `retention` `swap`（描述性，不同列集） | 0.668335（200 列） |

→ J0 PASS、J1 PASS、J2 PASS、J3 PASS、J4 PASS → **J1-roster-line-sets-the-roster**。

### 71.11 結果（k=5）

| 編輯 | 列數 | movement |
| --- | --- | --- |
| `swap` | **198**（跳過 2） | 0.110628 |
| `reverse` | 200 | 0.311620 |
| `colour` | 200 | 0.077265 |

| 讀數 | 值 |
| --- | --- |
| `lift` | 0.002037，p 0.4805，**只有 34 列**有參考（164 列沒有；302 個不同參考名冊，792 個可能名冊） |
| `top1`（描述性） | 0/34 ＝ 0.0，chance 0.0033（1/302） |
| `retention` `reverse` | **+0.013823**（p 0.3357，**90 列**） |
| `retention` `colour` | **+0.012219**（p 0.2817，**90 列**） |

→ J0 PASS、J1 PASS、J2 FAIL（`defined` FALSE：34 < 50）、J3 PASS、J4 FAIL
→ **J4-neighbourhood-underpowered**。

`retention` 在 k=5 只有 90 列，是因為 200 段留出裡有 110 段的名冊在參考池裡**沒有第二段**；J3 是在
這 90 列上算的，照實記在下面。

### 71.12 預測對帳

| 讀數 | 登記的預測 | 實際 | 對帳 |
| --- | --- | --- | --- |
| J0 | PASS | PASS | 中 |
| J1 | PASS | 0.333621 > 1e-3 | 中 |
| J2（k=2） | PASS | 0.130641／p 0.001，199 列 | 中 |
| J3（k=2） | **FAIL**（兩個 retention 都負） | reverse **+0.007788**、colour **−0.001729** | **不中** |
| 分支（k=2） | **J2-the-trace-is-the-line-not-the-roster** | **J1-roster-line-sets-the-roster** | **不中** |
| 分支（k=5） | J4-neighbourhood-underpowered | J4（34 列 < 50） | 中 |

k=2：**4/5**（J3 與分支不中）；k=5：**1/1**。

**這是一個有用的 miss，照實寫**：登記時我預測 state 追蹤的是**那一行字面**（§70.11 第 4 點），所以
把子句順序顛倒、把一個顏色詞換掉，都應該把 state 推離自己的名冊。實際是：換一個名字（`swap`）移動
最多（0.3336）、**反轉順序移動 0.2332**、換顏色移動 0.1667——三個都動了，但**兩個對照都沒有把
state 推離自己的名冊**（+0.0078、−0.0017，都在 0 附近，p 0.29／0.57）。也就是說那一回合的 state 對
**順序**與**未使用的顏色**是不變的，改變它的是**名字的集合**。

我原本的理由是「同一名冊的兩段 session，文字也比較像」，所以結構檢定分不開字面與集合——那個
理由本身沒錯（§70.11 第 4 點仍然成立），但它預測錯了一件事：**逆序的寫法在語料裡也是同一名冊的
真實寫法**。語料的 order twin 讓「逆序」與「原序」同屬一個名冊的文字集合，所以逆序不會離開自己的
鄰域。這一點在登記時寫的預測裡漏掉了，不是事後才發現的細節——它就是我預測錯的地方。

### 71.13 照實記的限制（哪些讀數不能那樣讀）

1. **movement 不是判別量，只是「有沒有動」。** k=2 的排序是 swap > reverse > colour，k=5 是
   reverse (0.3116) > swap (0.1106) > colour (0.0773)——兩個 k 的排序不一致，所以 movement 只能讀
   成「> 1e-3，那一行確實影響了 state」，不能讀成「swap 動得最多＝它最相關」。登記的門檻本來就
   只有 1e-3。
2. **k=2 的 lift 很響，但它證明的是「可尋址」，不是「可讀出」。** 199/200 列都有編輯後名冊的參考，
   是因為 `C(12,2)=66` 個名冊在 600 段參考裡**全部出現**；k=5 只有 302/792，所以只有 34 列。
   這個差別是**語料覆蓋**，不是機制差別。k=2 的 0.130641／p 0.001 因此不能拿去說 k=5 也有。
3. **`top1` 只描述、不設門檻。** k=2 的 0.2261（chance 0.0152，14.9×）看起來很強，但它是
   「最近的那一列剛好同名冊」的比例，鄰域半徑由語料決定；k=5 是 0/34。兩者都不進分支判定。
4. **J3 在 k=5 只有 90 列**（110 段留出沒有同名冊的第二段），所以 k=5 的「兩個對照都不推離」是
   在 90 列上成立；k=2 是 199 列。兩個 k 都沒有達不到 50 列的問題（J3 沒有登記最小列數，這是一
   個應該在下次登記時補上的缺口，照實記下來）。
5. **這一輪沒有回答「讀出為什麼取不到」。** 它只把 §70 的 B3 往前推一格：那個痕跡**是名字的集合**，
   而且**在 state 裡是可尋址的**；讀出仍取不出來（§70：值臂 in-sample 0.4975、非線性容量 0.5650）。
   「可尋址」與「可讀出」是兩件事，這一節只證明前者。
6. **k=2 的預測錯了，而它錯得有用**：它把 §70.11 第 4 點從「無法區分」改成「可以區分，而且區分的
   結果偏向集合」——但代價是我在登記裡寫了一個錯的預測，這個 miss 不能用「本來就接近」含混過去。
7. **兩個 k 都是診斷，不是能力分數。** 核心分不變 **0.00/10**。

### 71.14 這一節證明什麼、不證明什麼

**證明**（k=2，199 列有定義）：

* 名冊那一行的**文字**確實是那個邊界 state 的函數：三個等 token 數的編輯都讓 state 移動
  （0.3336／0.2332／0.1667，皆遠大於 1e-3，而重跑自己的 state 是逐位相同、cos 1.0）；
* 換掉一個名字之後，state 落在**編輯後名冊**的鄰域（lift 0.130641、p 0.001、199 列、無擬合），
  這排除了「那個回合什麼都沒寫」；
* **順序與未使用顏色不是內容**：反轉子句順序與換一個顏色都沒有把 state 推離自己的名冊
  （+0.0078／−0.0017，皆 ≥ −0.01 的地板，p 0.29／0.57）。

**不證明**：

* 不證明讀出拿得到（§70 的 B3 仍在：值臂 in-sample 0.4975、非線性容量 0.5650）；
* 不證明 k=5 一樣（34 列 < 50，J4 就是「這一輪不裁決」）；
* 不證明「名字」是**以可分離的個體**存放的——只證明集合改變會改變 state，順序不會；
* 不證明 `reverse`／`colour` 的「不推離」等於「完全沒變」：它們的 movement 是 0.23／0.17，state 確實
  變了，只是變完之後仍然在自己名冊的鄰域裡。這一點很重要：**不變的是名冊，不是 state**。

### 71.15 下一步（J1 的機械輸出）

J1 指名的不是「再加讀出家族」，而是**逐槽**看 `end_turn` 到底寫了什麼，以及為什麼那個痕跡讀不出
來。§70.3 已量到機制的一半：每回合只寫一個 `value_proj(h)`、16 個槽共用同一個 share、位址是常數
slot 10。J1 補上另一半：那個 share **依賴名字集合**（而不依賴順序或顏色）。所以下一個階段（§72）
要登記的是：

> 在同一個名冊邊界上，逐槽讀出 16 個槽的值與 key，問兩件事：
> (a) 16 個槽寫入的內容是否**逐槽不同**（若是同一個 share，則「位址碰撞」不是唯一解釋）；
> (b) 用**同一個**載體、**同一個**邊界，把「讀出」換成「只讀被寫入的那一槽」與「讀全部槽」，
> 比較兩者的 in-sample／留出——若單槽讀得出、合併讀不出，就是**疊加干擾**；若兩者都讀不出，
> 就是**表徵本身不可分**。

這一項要**另外登記**（槽的定義、讀法、門檻、no-op 對照都寫在跑之前），不能順手接在這一節後面跑。
**不加步數、不加寬度、不加資料**——這是 J1 的條件。

## §72 `end_turn` 到底寫了什麼（逐槽，不擬合）

### 72.1 為什麼是這一支

§71 的機械輸出是 **J1-roster-line-sets-the-roster**：名冊那一行確實改變 state，而且改變它的是
**名字的集合**（反轉子句、換一個未用顏色都沒有把 state 推離自己的名冊）。也就是說名冊在 state 裡
**可尋址**；但 §70 的 **B3** 還在——沒有任何可裁決的讀出家族取得到它（值臂 in-sample 0.4975、非線性
容量 0.5650）。

§70.3 只量了機制的一半（在**訓練**分割上）：每回合只有一個 `value_proj(h)`、16 個槽共用同一個
share、位址是常數。§72 要把它接完，而且要**機械**地回答「讀出為什麼取不到」：

> 那個失敗是**槽碰撞**（16 個槽互相干擾）、**疊加**（一個槽裡疊了很多回合），還是兩者都不是？

**這一節不改寫入、不改讀出、不加步數、不加寬度、不加資料。** 它只量「現在寫了什麼」。改寫入是下一個
階段（§73）的事，而且只有在這一節判定「損失在寫入」之後才做。

### 72.2 量什麼（同一載體、同一邊界、五個無擬合讀數 ＋ 四個線性臂）

對 400 段訓練＋200 段留出的 session，在**名冊邊界**（§69／§70 的同一個回合、同一個抽取器），
從一次前向得到 16×64 的 value 矩陣與 64 維 read，然後算：

| 讀數 | 定義 | 讀法 |
| --- | --- | --- |
| `max_share` | `max_j softmax(exp(log_write_scale) · slot_gate(h))_j` | 1.0 ＝ 一回合只寫一個槽 |
| `effective_slots` | `1 / Σ_j w_j²` | 1.0 ＝ 有效槽數 1（均勻時是 16） |
| `active_slots` | `#{j : ‖v_j‖ ≥ 1e-3 · max_k ‖v_k‖}` | 那個回合之後還有幾個槽不是空的 |
| `rank1_residual` | 16×64 值矩陣的 `σ₂/σ₁` | ≈ 0 ＝ 整個 store 是一個向量 |
| `read_cos` | `cos(read, v_{argmax‖v‖})` | 1.0 ＝ 讀出**就是**那一槽的值（差一個尺度） |
| `address_rank1_residual` | 16 維位址矩陣**跨段**中心化後的 `σ₂/σ₁` | ≈ 0 ＝ 所有回合共用同一個位址輪廓 |

前五個是**逐段**的，第六個是**跨段**的（問「位址是不是常數」）。全部沒有擬合參數。

四個線性臂（與 §70 同一個訓練器、同一個標準化、同一個置換容量控制、2,000 步）：

| 臂 | 特徵 | 目的 |
| --- | --- | --- |
| `values` | 整個 store 攤平（16×64） | **§70 `linear_values` 的逐字重現** |
| `read` | 64 維 read | 讀出這一路本身 |
| `state` | `[h, read]` | **§70 `linear_state` 的逐字重現** |
| `address` | 16 個寫入權重 | 名冊是不是寫在**位址**裡 |

兩個重現臂是**儀器檢查**：登記時寫定「`values` 應該重現 §70 的 `linear_values`（k=2 0.1400、
k=5 0.0050）」。重現不出來，這一輪的臂就不能跟 §70 比。

**這四個臂是寫入的診斷，不是生產候選。** 如果 store 只有一個槽，「換一個讀出家族」這個問題就已經被
回答：store 裡沒有別的東西可讀，修法必須是**換一個寫入**。

### 72.3 跑之前已經看過的數字（**訓練分割**，所以預測不是盲的）

登記前，我在**訓練**分割（400 段）上量過一次機制，用來決定這一節要問什麼。留出分割的這些讀數
**一個都沒算過**。

| 讀數 | k=2 | k=5 |
| --- | --- | --- |
| `max_share` 平均／最小 | **1.0000** / 1.0000 | **0.9987** / 0.6975 |
| `effective_slots` 平均 | **1.000** | **1.003** |
| 每段值矩陣 `σ₂/σ₁` 最大 | **1.11e-05** | **0.59** |
| `read` 對最強槽 `\|cos\|` 平均／最小 | **1.0000** / 1.0000 | **0.9998** / 0.9325 |
| `‖read‖ / amplitude` 平均 | **1.0000** | **0.9992** |
| 位址跨段中心化：第一奇異值能量占比 | **1.0000** | **0.9993** |
| LOO-NN `h`（chance 0.0175／0.0056） | 0.4225 | 0.0150 |
| LOO-NN `read` | 0.4250 | 0.2875 |
| LOO-NN `direction` | 0.4100 | 0.2625 |
| LOO-NN `address` | 0.3450 | 0.0825 |
| LOO-NN `amplitude` | 0.0100 | 0.0100 |

（位址矩陣那一列：k=2 是 1.0000、k=5 是 0.9993，都是「跨段第一奇異值幾乎占全部能量」＝常數輪廓。
探針另存中心化的 `σ₂/σ₁`，只作描述、**不設門檻**——它不是本節的任何閘門。）

**這張表能讀什麼、不能讀什麼**：

1. 兩個 k 的 store 都是**一個槽**（`max_share` ≈ 1、有效槽數 ≈ 1、值矩陣 rank 1）。所以「16 個槽互相
   碰撞」不是解釋；k=2 的殘差 1.11e-05 是浮點雜訊，k=5 的 0.59 是**真的有第二個方向**（少數段寫了
   第二個槽）。
2. 讀出**就是**那一槽的值（`|cos|` 1.0000／0.9998、範數比 1.0000／0.9992）——讀出沒有加入任何 store
   裡沒有的維度，所以「讀出抹掉資訊」也不是解釋。
3. 位址**跨段**只有一個方向。名字集合的資訊不在位址裡。
4. **LOO-NN 是訓練分割的最近鄰，會被語料的 order twin 灌高，不能當能力**。它只說明一件事：k=5 的
   `h`（0.0150，chance 0.0056）幾乎不含名冊身分，而 `read`（0.2875）有——但**庫存只有一個向量時，
   那仍然只是那一個向量的鄰近性**，不是「名冊被存下來了」。

結論（寫在跑之前）：這個 store 是**一回合一個摘要向量**，每個回合把同一個槽覆寫成移動平均。所以
真正的字是**時間疊加**（turn over turn 在同一個槽裡），不是槽碰撞、也不是跨槽疊加。§72 的門檻與
分叉因此以「一回合一個位址」為主軸。

### 72.4 程式

* 探針：`scripts/probe_pantry_slots.py`（`--report` 讀已訓練報告、`--check` 機械重驗、`--out` 寫
  JSON）；
* 契約測試：`tests/test_pantry_slots.py` **28 條**——重算的寫入門就是 `end_turn` 那一條式子（逐位
  相同）、一槽 store 恰好 rank 1、`active_slots` 的 1e-3 地板、`read_cos` 在「read 就是那一槽」時
  為 1、位址列就是 softmax 權重、常數位址跨段 rank 1、四個臂就是登記的四個、`arm()` 把 fold 結構
  交給 `cross_validate`、S0–S5 的地板、分支優先序、`--check` 會拒絕被改過的閘門／分支／分數／
  載體。

探針重用 §70 的邊界抽取（`scripts/probe_pantry_families.py`）與 §66 的載體重建
（`scripts/probe_pantry_readout.py`），所以 §69–§72 的特徵視角是同一個。

### 72.5 登記的門檻

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `ONE_ADDRESS_FLOOR` | **0.95** | 「一回合一個位址」：`max_share ≥ 0.95` 才算 |
| `FRACTION_FLOOR` | **0.95** | 逐段判定要**幾乎每一段**成立才算這一類 store |
| `ACTIVE_SLOT_SHARE` | **1e-3** | 槽「不是空的」的地板（相對最大槽） |
| `RANK1_EPS` | **1e-3** | `σ₂/σ₁ ≤ 1e-3` 才算 rank 1 |
| `READ_COS_FLOOR` | **0.999** | 「讀出就是那一槽」 |
| `ADDRESS_TRANSFER_MAX` | **0.10** | 位址臂的留出正確率上限（chance 0.5／0.2 之上只留一點餘裕） |
| `TRANSFER_FLOOR` | **0.50** | 與 §70 同一個「有轉移」的門檻 |
| `CAPACITY_MAX` | **0.50** | 置換標籤的容量控制上限，超過就不宣稱轉移 |
| `READABLE_FLOOR` | **0.95** | 與 §70 同一個「擬合得到」的門檻（本節只用於描述） |

### 72.6 閘門（跑之前寫定）

| 閘門 | 條件 |
| --- | --- |
| **S0 儀器** | 同一批 session 兩次前向逐位相同（`determinism_min_cosine ≥ 1−1e-6`）、載體 `weights_hash` 與 checkpoint sha256 前後相同、所有特徵有限 |
| **S1 一回合一個位址** | 留出 `max_share ≥ 0.95` 的段數 ≥ **95%** |
| **S2 store 只有一個槽** | 留出 `active_slots ≤ 1` 的段數 ≥ 95% **且** `rank1_residual ≤ 1e-3` 的段數 ≥ 95% |
| **S3 讀出就是寫入** | 留出 `read_cos ≥ 0.999` 的段數 ≥ 95% |
| **S4 位址不帶名冊** | `address` 臂的**留出正確率 ≤ 0.10** |
| **S5 store 讀不出來** | `values` 與 `read` 兩個臂**都沒有轉移**（留出 < 0.50，或容量 ≥ 0.50） |

### 72.7 分叉（跑之前寫定，機械決定；固定優先序）

| 分支 | 條件 | 下一步 |
| --- | --- | --- |
| **S0-instrument** | S0 不過 | 修抽取管路（決定性／有限性／載體雜湊），這一輪不讀任何東西 |
| **S4-slots-are-distributed** | S0 過、S1 不過 | 寫入不是 one-hot，store 會把一個回合攤到多個槽——§70.3 的「常數位址」在留出上不成立，先重量位址輪廓 |
| **S4-two-addresses** | S1 過、S2 不過 | 門是 one-hot 但 store 不是 rank 1：少數段寫了第二個槽；把 single-slot 的比例照實報，並**只對 rank-1 的段**重問 |
| **S2-read-is-not-the-write** | S1、S2 過、S3 不過 | store 只有一個槽，但讀出不是那一槽的值——輸的是讀出（query/key）那條路，不是寫入 |
| **S3-address-codes-the-roster** | S1–S3 過、S4 不過 | 名冊寫在**位址**裡（值沒有）：改成「一個名冊項一個位址」，不是「一回合一個位址」 |
| **S1-single-address-temporal-superposition** | S1–S5 都過 | 每個回合都寫同一個槽、15 個槽永遠空著、讀出就是那一個值、位址不帶名冊 → 名冊跟**先前每一回合的文字**共用同一個 64 維移動平均；損失在**寫入**，不在讀出 |

### 72.8 預測與否證（寫在跑之前）

| 讀數 | 預測 | 否證條件 |
| --- | --- | --- |
| S0 | PASS | 決定性、有限性、載體三者任一不過 |
| S1 | **PASS**（訓練分割已量到 `max_share` 1.0000／0.9987） | 留出 `≥ 0.95` 的段數 < 95% |
| S2 | **k=2 PASS、k=5 FAIL**（k=5 的殘差在訓練分割已到 0.59） | k=2 的 rank-1 段數 < 95% 或 `active_slots ≤ 1` 的比例 < 95% |
| S3 | **PASS**（訓練分割 `\|cos\|` 1.0000／0.9998） | 留出 `≥ 0.999` 的段數 < 95% |
| S4 | **PASS**（訓練分割 LOO-NN 位址 0.3450／0.0825，且位址跨段 rank 1） | 留出正確率 > 0.10 |
| S5 | **PASS**（§70 的 B3 就是這個） | `values` 或 `read` 任一個留出 ≥ 0.50 且容量 < 0.50 |
| 分支（k=2） | **S1-single-address-temporal-superposition** | 任何一個門不過（見上表） |
| 分支（k=5） | **S4-two-addresses** | S2 在 k=5 也過（殘差 ≤ 1e-3 的段數 ≥ 95%） |

**這一輪的預測不是盲的**（照實寫）：§72.3 的訓練分割數字看過，§70.3 的機制也看過；留出分割的這
六個讀數與四個臂**一個都沒算過**。所以 S1／S3 的預測是「訓練上成立、留出應該一樣」，S2 的 k=5
FAIL 是「訓練上已經不成立」，S4／S5 是「§70 的結論應該重現」。

**什麼會讓這一節作廢**：

1. S0 不過（重跑不逐位相同、特徵有非有限值、載體被改動）——整份讀數無效；
2. `values` 臂重現不出 §70 的 `linear_values`（k=2 0.1400／k=5 0.0050）：臂的管路與 §70 不同，
   兩個階段不能比；
3. 載體 `weights_hash` 或 checkpoint sha256 前後不同（探針不得訓練載體，也不得寫回 checkpoint）；
4. 任何人為改動門檻、讀數定義、臂、分割或分支表——改動必須以 amendment 另記。

**這一節不是能力分數**；核心分不變 **0.00/10**。

### 72.9 管路修正（跑之前就撞到，沒有任何讀數存在）

登記 commit `15fade29f` 之後、任何計分之前，第一次 k=2 執行在**第一個 matmul** 就中止：
`slot_block` 內部用 double 算 rank，卻把 `address`／`weights` 以 double 回傳，而 §70 的線性探針是
float32 → `RuntimeError: mat1 and mat2 must have the same dtype`。**當時沒有任何讀數被產生**（log 在
寫出 16×64 矩陣之前就結束），所以這個錯誤沒有被用來調整任何門檻或預測；那份 log 照實留下
（`slots72/k2_void_dtype.log`）。

修正：`slot_block` 內部照樣用 double 算奇異值，但回傳的兩個讀出視角**保持 store 的 dtype**
（`weights.to(values.dtype)`／`address.to(values.dtype)`）。契約測試不變（28 條仍全過），因為它們
比的是數值而不是 dtype。

**執行順序**（登記 commit `15fade29f`）：

| 時間（+08:00） | 產物 | 狀態 |
| --- | --- | --- |
| 12:30:22 | `slots72/k2_void_dtype.log` | **作廢**：dtype 錯誤，中止於第一個 matmul，無讀數 |
| 12:30:54 | `slots72/k2.{json,log}` | 計分（k=2，12.93 s） |
| 12:31:22 | `slots72/k5.{json,log}` | 計分（k=5，13.09 s） |

兩份 `--check` 都是 `OK`；`instrument_ok=True`；載體前後相同（k=2 `de17ed7d…`／`cc173f9d…`，
k=5 `05c3b103…`／`e4d13e56…`）；`determinism_min_cosine` 兩份都是 **1.0**；語料 digest 與
§69–§71 逐位元組相同（k=2 `416a8a68…`／`69c730e1…`，k=5 `d6ca78a8…`／`948b08cc…`）。

### 72.10 結果（k=2）

400 段訓練＋200 段留出，名冊邊界，一次前向，**沒有擬合**的五個讀數：

| 讀數 | 訓練（400） | 留出（200） |
| --- | --- | --- |
| `max_share` 平均（最小） | 0.999997（0.999952） | **0.999998**（0.999949） |
| `effective_slots` 平均 | 1.000006 | **1.000004** |
| `active_slots` 分佈 | `{1: 400}` | **`{1: 200}`** |
| `rank1_residual` 最大 | 1.10e-05 | **9.00e-06** |
| `read_cos` 最小 | 1.000000 | **1.000000** |
| 位址跨段中心化 `σ₂/σ₁` | 7.63e-06 | **6.68e-06** |
| 一回合一個位址（≥0.95）的段數 | 1.0000 | **1.0000** |
| 只有一個槽（`≤1`）的段數 | 1.0000 | **1.0000** |
| rank 1（`σ₂/σ₁ ≤ 1e-3`）的段數 | 1.0000 | **1.0000** |
| 讀出就是那一槽（`≥0.999`）的段數 | 1.0000 | **1.0000** |

四個線性臂（同一預算：2,000 步、同一個標準化、同一個置換容量控制）：

| 臂 | in-sample | 容量（置換標籤） | 訓練內交叉驗證 | **留出** |
| --- | --- | --- | --- | --- |
| `values` | 0.4975（199/400） | 0.1650 | 0.2625 | **0.1400（28/200）** |
| `read` | 0.2925（117/400） | 0.0250 | 0.2375 | **0.1350（27/200）** |
| `state` | **0.7700（308/400）** | 0.2500 | 0.4725 | **0.2850（57/200）** |
| `address` | 0.1975（79/400） | 0.0450 | 0.1525 | **0.0500（10/200）** |

→ S0 PASS、S1 PASS、S2 PASS、S3 PASS、S4 PASS、S5 PASS
→ **S1-single-address-temporal-superposition**（登記的預測，命中）。

**儀器檢查（兩個重現臂逐位相同，不是「差不多」）**：

| 臂 | §70 | §72 | 相同？ |
| --- | --- | --- | --- |
| `linear_values` → `values` | in 0.4975／cap 0.1650／held 0.1400 | in 0.4975／cap 0.1650／held 0.1400 | **是** |
| `linear_state` → `state` | in 0.7700／cap 0.2500／held 0.2850 | in 0.7700／cap 0.2500／held 0.2850 | **是** |

### 72.11 結果（k=5）

| 讀數 | 訓練（400） | 留出（200） |
| --- | --- | --- |
| `max_share` 平均（最小） | 0.998672（0.697512） | **0.998810**（0.903735） |
| `effective_slots` 平均（最大） | 1.003044（1.731888） | **1.002523**（1.210792） |
| `active_slots` 分佈 | `{1: 382, 2: 12, 3: 2, 6: 2, 8: 2}` | **`{1: 187, 2: 10, 5: 1, 6: 2}`** |
| `rank1_residual` 最大 | 0.592295 | **0.523976** |
| `read_cos` 最小 | 1.000000 | **0.599773** |
| 位址跨段中心化 `σ₂/σ₁` | 0.225570 | **0.247732** |
| 一回合一個位址（≥0.95）的段數 | 0.9925 | **0.9900** |
| 只有一個槽（`≤1`）的段數 | 0.9550 | **0.9350** |
| rank 1（`σ₂/σ₁ ≤ 1e-3`）的段數 | 0.9600 | **0.9400** |
| 讀出就是那一槽（`≥0.999`）的段數 | 1.0000 | **0.9950** |

| 臂 | in-sample | 容量 | 訓練內 CV | **留出** |
| --- | --- | --- | --- | --- |
| `values` | 0.0850（34/400） | 0.0300 | 0.0025 | **0.0050（1/200）** |
| `read` | 0.0225（9/400） | 0.0100 | 0.0025 | **0.0100（2/200）** |
| `state` | 0.1525（61/400） | 0.0700 | 0.0025 | **0.0050（1/200）** |
| `address` | 0.0125（5/400） | 0.0125 | 0.0000 | **0.0000（0/200）** |

→ S0 PASS、S1 PASS、S2 **FAIL**（單槽 0.9350 < 0.95、rank 1 0.9400 < 0.95）、S3 PASS、S4 PASS、
S5 PASS → **S4-two-addresses**（登記的預測，命中）。

**儀器檢查**：`values` 與 `state` 同樣逐位重現 §70 的 `linear_values`（0.0850／0.0300／0.0050）與
`linear_state`（0.1525／0.0700／0.0050）。

### 72.12 預測對帳

| 讀數 | 登記的預測 | 實際 | 對帳 |
| --- | --- | --- | --- |
| S0 | PASS | PASS | 中 |
| S1 | PASS | 1.0000（k=2）／0.9900（k=5） | 中 |
| S2 | k=2 PASS、k=5 FAIL | k=2 1.0000／1.0000；k=5 0.9350／0.9400 | 中 |
| S3 | PASS | 1.0000（k=2）／0.9950（k=5） | 中 |
| S4 | PASS | 0.0500（k=2）／0.0000（k=5） | 中 |
| S5 | PASS | k=2 0.1400／0.1350；k=5 0.0050／0.0100 | 中 |
| 分支（k=2） | S1-single-address-temporal-superposition | S1 | 中 |
| 分支（k=5） | S4-two-addresses | S4-two-addresses | 中 |

**8/8 全中。** 照實說：這不是一次「預測很準」的成就。S1 與 S3 的預測是**直接從 §72.3 的訓練分割
數字抄過來的**，S2 在 k=5 的 FAIL 也一樣；留出只是確認那些機制在同一個載體上不是訓練分割的產物。
真正有資訊量的是兩件事：(1) S2 在 k=5 的**分數**（0.9350／0.9400）與訓練幾乎一樣（0.9550／0.9600），
所以「少數段寫第二個槽」是機制而不是分割差異；(2) 兩個重現臂**逐位**重現 §70，代表 §70 與 §72 的
讀出管路真的同一個（否則兩個階段的分數不能並排）。

### 72.13 照實記的限制（哪些讀數不能那樣讀）

1. **S1 在 k=5 不是 1.0，是 0.9900。** 200 段留出裡有 2 段的 `max_share < 0.95`（最小 0.9037），
   所以「每個回合只寫一個槽」在 k=5 是 **99%**，不是全部。門檻是 95%，它過了；但宣稱必須寫成 99%。
2. **S3 在 k=5 是 0.9950，`read_cos` 最小 0.5998。** 有一段的讀出**不是**那一槽的值。k=2 的最小值
   是**正好 1.0**。所以「讀出就是寫入」在 k=2 是逐段精確，在 k=5 是 99.5%。
3. **`rank1_residual` 是「那個邊界的值矩陣」，不是整個 store 的一生。** 量的是名冊邊界那一次前向
   之後的 16×64 矩陣；沒有證明其他回合的 store 也 rank 1。§72.1 的「時間疊加」因此是**在這個邊界上**
   成立的機制描述，不是對全部回合的普查。
4. **`values` 臂 0.1400 是「store 單獨、線性探針」的上限，不是「名冊取不到」。** `state` 臂
   （`[h, read]`）在 k=2 有 0.2850——比 `values` 高——但**差額來自 `h`，而 `h` 不是記憶**。所以
   記憶那條路在線性探針下的上限就是 `values` 的 0.1400（k=2）／0.0050（k=5）。
5. **本節沒有加非線性臂，而 §70 的非線性臂也不是跑在 store 上。** §70 的 `nonlinear_quad` 是
   `quad(state)`＝`[x, x*x]` 展開 `[h, read]`（k=2 留出 0.3000、容量 0.5650 → 不可裁決；k=5
   0.0150），**不是** 16×64 store 的二次展開。所以「store 取不到名冊」在這裡只支持到**線性**臂
   （0.1400／0.0050）；**store 的非線性讀出沒有量過**，這是一個照實記的缺口。
6. **「15 個槽空著」是名冊邊界上的計數。** k=5 的 `active_slots` 分佈裡有 `{5: 1, 6: 2}`——少數段同時
   有 5–6 個槽不是空的，所以 k=5 不是「一個槽」的乾淨故事，這正是 S2 FAIL 的來源。
7. **位址的 `σ₂/σ₁`（0.2256／0.2477）沒有門檻、也不讀成「位址帶名冊」。** 「位址不帶名冊」是由
   `address` 臂的留出（0.05／0.00，chance 0.5／0.2）判定的，不是由這個比值。
8. **兩個 k 都是診斷，不是能力分數。** 核心分不變 **0.00/10**。

### 72.14 這一節證明什麼、不證明什麼

**證明**（k=2 是 400／200 段全部，k=5 是 99%／93.5%）：

* `end_turn` 的寫入門在名冊邊界是 **one-hot**：k=2 每一段的 `max_share` ≥ 0.999949（有效槽數
  1.000004）；k=5 是 0.998810（99%）。
* store 在名冊邊界是**一個向量**：k=2 每一段的 `σ₂/σ₁` ≤ 9.00e-06、`active_slots` 全部 `{1}`；
  k=5 是 94%（`σ₂/σ₁` 最大 0.524，10 段有第二個槽）。
* 讀出**就是**那一槽的值：k=2 每一段的 `|cos|` 都是 **1.000000**；k=5 是 99.5%。
* 位址是**常數輪廓**：跨段只有一個方向，而用位址去認名冊的留出正確率是 0.0500（k=2，chance 0.5）
  與 0.0000（k=5，chance 0.2）——**位址不帶名冊**。
* store 單獨的留出正確率是 0.1400（k=2）／0.0050（k=5），而兩個重現臂逐位重現 §70。

**不證明**：

* **不證明**「換一個讀出家族也沒有用」——只證明**在這個邊界、這個載體上，store 裡只有一個向量，而
  讀出就是它**；store 的非線性讀出沒有量過（§72.13 第 5 點）。
* 不證明「改成一個回合一個位址就會修好」——那是 §73，必須另外登記。
* 不證明 store 在**其他回合**也是一個槽（只量名冊邊界）。
* 不證明名冊**不在**那個向量裡：k=2 的 0.1400 大於 chance 0.0152，所以它是**有資訊、但遠低於可用**。

### 72.15 下一步（S1 的機械輸出）

分支 `S1-single-address-temporal-superposition` 指名的不是讀出，而是**寫入**：

> 同一個語料、同一組步數、同一組參數，只把寫入改成**一個回合一個位址**（回合序號當位址，不用
> softmax 門），然後重跑 §70 的四個臂。若 `values` 的留出從 0.1400 顯著上升，損失就確認在寫入；
> 若不動，問題在別處（例如 `value_proj` 把整個回合壓成一個向量本身）。

這一項要**另外登記**（新的寫入規則、同一個邊界、同一組門檻與 no-op 對照都寫在跑之前），不能順手
接在這一節後面跑。**不加步數、不加寬度、不加資料**——這是 §71／§72 共同定下的條件。

## §73 把寫入改成一個回合一個位址（S1 的機械輸出）

### 73.1 為什麼是這一支

§72 的機械輸出是 **S1-single-address-temporal-superposition**（k=2；k=5 是 S4-two-addresses，
但機制相同：99% 的段只有一個槽）。逐槽讀數是沒有擬合的：

* 寫入門在名冊邊界是 **one-hot**（k=2 留出 200/200 段，`max_share` 平均 0.999998、最小 0.999949）；
* 16 個槽裡 **15 個空著**（k=2 `active_slots` 全部 `{1}`），值矩陣 **rank 1**（每段 `σ₂/σ₁` ≤
  9.00e-06）；
* 讀出**就是**那一槽的值（每段 `|cos|` = 1.000000）；
* 位址跨段是常數輪廓，用位址認名冊的留出正確率只有 0.0500（chance 0.5）。

所以名冊不是被讀出抹掉的，也不是被槽碰撞弄掉的：它跟**先前每一回合的文字**共用同一個 64 維移動平均。
S1 指名的下一步是**換一個寫入**，不是換一個讀出。

### 73.2 改什麼（只改位址，其餘逐項固定）

`TurnStoreCore` 多一個**預設關閉**的旗標 `address`（`"gate"` 預設／`"turn"`）：

| 模式 | 寫入位址 `a` |
| --- | --- |
| `"gate"`（每一節到目前為止） | `softmax(exp(log_write_scale) · slot_gate(h))` |
| `"turn"`（§73） | `one_hot(turn_index % slots)` |

**其餘全部不動**：強度仍是 `g = sigmoid(write_gate(h))`、鍵與值仍是 `key_proj(h)`／`value_proj(h)`、
更新仍是 `slot ← slot (1 − a g) + a g · new`、讀出仍是 `softmax(scale · q·kᵀ) v`、`h` 的遞歸、
`al_step`、`head([h, r])`、`chunk_seconds`、參數個數（`slot_gate` 保留在模組清單裡，turn 模式下不進梯度，
所以兩個臂的參數量逐位相同）全部一樣。

**不加步數、不加寬度、不加資料、不加 epoch、不改語料、不改目標函數、不改讀出。** 這也是 §71／§72
共同定下的條件。語料、seed、10,000 步、lr 5e-4、batch 8、hidden 128、emb 64 與 §70 的兩個載體逐項相同。

`turn_index` 是**零基底**的回合序號（`run_session` 的迴圈索引）。這個語料最短的 session 是 4 回合
（罪行 0／名冊 1／證據 2／問句 3），所以 `% 16` 在這個語料上從不繞回；寫成 `% slots` 只是為了讓規則
在更長的 session 上也定義良好。

### 73.3 量什麼（同一個邊界、同一個探針、同一組臂）

**不新開探針**：直接跑 `scripts/probe_pantry_families.py`（§70 的探針），所以三個臂、標準化、
置換容量控制、結構檢定、seed、2,000 步全部與 §70／§72 逐項相同，`linear_values` 的留出可以直接跟
§72 的 **0.1400** 比。

探針新增一個**描述性**區塊 `store`（不是閘門、不進任何臂）：在名冊邊界從實際的 `v` 算
`active_slots`（地板 `1e-3 × 該段最強槽`）與每段值矩陣的 `σ₂/σ₁`，用的常數就是 §72 的
`ACTIVE_SLOT_SHARE`／`RANK1_EPS`。這是「寫入真的換了」的機械讀數，也是與 §72 同一句話的比較。

跑之前已在**預設（gate）載體**上驗過這個新增區塊不改變任何既有數字（73.4）。

### 73.4 程式與跑之前的回歸檢查

* `apps/backend/src/ai/core/stateful_decoder.py`：`TurnStoreCore(..., address="gate")`、
  `write_weights(hidden, address=None)`、`end_turn(tensors, *, address=None)`、`config()` 帶
  `address`；`load_weights(strict_config=True)` 新增一條「位址必須相符」的檢查（舊 checkpoint 沒有
  `address` 鍵，視為 `"gate"`，所以**§43–§72 的每一個 checkpoint 仍可載入**）。
* `scripts/train_pantry_deduction.py`：`build_core(..., address=...)`、`--address {gate,turn}`
  （預設 `gate`，且只有在 `--core turnstore` 時可用）、報告 `config.address`、`run_session` 把回合
  索引傳給 `end_turn`、兩個重建載體的路徑（配對重評與 `--check`）都讀 `config.address`。
* `scripts/probe_pantry_readout.py`、`scripts/probe_pantry_state.py`：重建載體時傳 `address`。
* `scripts/probe_pantry_families.py`：`store_shape()` 與報告的 `store` 區塊（描述性）；`--check`
  會驗證它與自己的 `active_slots` 計數一致（舊報告沒有這個鍵 → 跳過）。
* `tests/ai/test_turn_store_core.py`：**+10 條**（20 條綠）——預設規則就是那條 softmax 且忽略索引、
  turn 規則給出 one-hot 且不受 `slot_gate` 影響、缺索引會拒絕、未知模式會拒絕、四回合落在四個槽
  （gate 的均勻門會碰 16 個槽）、參數量與模組清單不變、checkpoint 記錄模式且 gate↔turn 互載會拒絕、
  **沒有 `address` 鍵的舊 checkpoint 仍是 gate 且可載入**、`build_core` 傳遞位址、CLI 拒絕
  `--address turn` 搭配非 turnstore。

**跑之前的回歸檢查（預設路徑逐位不變）**：

1. 用 §72 的兩個 checkpoint 重建：`address` 都是 `gate`，`weights_hash` 與報告相同
   （k=2 `de17ed7d…`、k=5 `05c3b103…`）；舊 checkpoint 沒有 `address` 鍵仍載入。
2. `probe_pantry_slots.py` 在 k=2 載體上重跑一次（輸出到暫存），與 §72 的 `slots72/k2.json`
   **除 `seconds` 外整份相同**。
3. `probe_pantry_families.py` 在 k=2 載體上重跑：`arms`／`structure`／`positive_controls` 與 §70 的
   `readout70/k2.json` **逐位元組相同**；新的 `store` 區塊給出 `{1: 400}`／`{1: 200}`、
   `σ₂/σ₁` 最大 1.10e-05／9.00e-06——與 §72 的機制讀數相同。

### 73.5 登記的門檻

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `READABLE_FLOOR` | **0.95** | 與 §70 同一個「擬合得到」的門檻（in-sample） |
| `CAPACITY_MAX` | **0.50** | 置換標籤容量控制上限，超過就不宣稱轉移 |
| `TRANSFER_FLOOR` | **0.50** | 與 §70 同一個「可用轉移」的門檻（**不是**本節的決策線） |
| 決策線 | **§72 的 0.1400** | 這一節問的是「同一個臂有沒有比 §72 高」，不是「有沒有過 0.50」 |
| `ACTIVE_SLOT_SHARE` | **1e-3** | §72 的「槽不是空的」地板 |
| `RANK1_EPS` | **1e-3** | §72 的 rank-1 門檻 |
| 逐段比例地板 | **0.95** | 與 §72 的 `FRACTION_FLOOR` 相同 |

### 73.6 閘門（跑之前寫定）

| 閘門 | 條件 |
| --- | --- |
| **W0 儀器** | 三個家族的 `H0_instrument` 全過（in-sample ≥ 0.95、容量 ≤ 0.50）、載體 `weights_hash` 與 checkpoint sha256 前後相同、同一份探針**跑兩次**除 `seconds` 外逐位相同 |
| **W1 寫入真的換了** | 留出名冊邊界 `active_slots ≥ 2` 的段數 ≥ 95% **且** `rank1_residual > 1e-3` 的段數 ≥ 95% |
| **W2 store 擬合得到** | `linear_values` in-sample ≥ 0.95 且容量 < 0.50 |
| **W3 比 §72 高** | `linear_values` 留出 **> 0.1400** 且容量 < 0.50 |
| **W4 可用轉移** | `linear_values` 留出 ≥ 0.50 且容量 < 0.50 |

**W0 的兩點照實寫**：

1. `H1_linear_state_reproduces_§69` 在這一節**不適用**：它比的是「同一個 §69 格重跑」，而 §73 是一個
   新訓練的載體，`linear_state` 本來就不會相同。`branch()` 的優先序**不看 H1**，所以它不阻擋任何分支；
   報告的 `instrument_ok` 會因為它顯示 `False`，這一節讀 **W0 本身**，不讀那個旗標。
2. `H0` 的正控制是「同一個讀出擬合載體自己的標籤（問句邊界的兇手）」，與名冊無關。

### 73.7 分叉（跑之前寫定，機械決定；固定優先序）

| 分支 | 條件 | 下一步 |
| --- | --- | --- |
| **W0-instrument** | W0 不過 | 修探針管路（決定性／有限性／載體雜湊），這一輪不讀任何東西 |
| **W1-write-not-turn-addressed** | W0 過、W1 不過 | 載體沒有在逐回合分槽寫入（`active_slots` 仍是 1）：先查明為什麼，這一輪不回答 §73 的問題 |
| **W2-not-readable-in-sample** | W0、W1 過、W2 不過 | 線性讀出在 turn 載體上擬合不到自己的訓練標籤 → **校準失敗**，不是「沒有轉移」的證據 |
| **W4-address-is-not-the-loss** | W0–W2 過、W3 不過 | 分槽了、讀得出來、但留出沒有比 §72 高 → 損失**不在位址**；下一個嫌疑是 `value_proj(h)` 把整個回合壓成一個向量本身 |
| **W3-write-was-part-of-the-loss** | W3 過、W4 不過 | 留出上升但仍在 0.50 以下：位址是損失的**一部分**；照實報 Δ，**不得**說「修好了」 |
| **W5-write-was-the-loss** | W3、W4 都過 | 分槽寫入讓 store 的留出達到 §70 的可用地板 → 寫入就是損失所在，下一個問題是讀出（或問句邊界） |

### 73.8 預測與否證（寫在跑之前）

| 讀數 | 預測 | 否證條件 |
| --- | --- | --- |
| W0 | PASS | 任一家族 H0 不過、載體或 checkpoint 變動、兩次跑不相同 |
| W1 | **PASS**（依構造：4 回合寫 4 個槽） | 留出 `active_slots ≥ 2` 或 `rank1_residual > 1e-3` 的段數 < 95% |
| W2 | **PASS**（§70 的 gate 載體在同一批資料上 in-sample 0.4975，turn 只是不再混合回合） | `linear_values` in-sample < 0.95 或容量 ≥ 0.50 |
| W3 | **PASS**：k=2 `values` 留出 **> 0.1400** | 留出 ≤ 0.1400 |
| W4 | **FAIL**（預期 0.1400–0.50 之間，不到可用地板） | 若 ≥ 0.50 則 W4 也過（那是比預期好的結果，照實報） |
| 分支（k=2） | **W3-write-was-part-of-the-loss** | 見上（任何一項不過就走它的分支） |
| 分支（k=5） | 同方向，**不預設**會過 0.50（§72 的 k=5 gate 載體是 0.0050，chance 0.0056） | 同 W3 |

**為什麼 W3 的預測是「會上升」**：§72 說名冊那一回合的 `value_proj(h)` 被灌進同一個移動平均，而那個
平均裡有先前的罪行回合。分槽之後，名冊回合的值單獨存在一個槽裡，線性探針只要看那一槽就夠——所以
**如果**那一個向量本身帶著名冊，留出就應該上升。**這一節的否證就是反面**：若留出不動，表示連
「名冊回合自己的 `value_proj(h)`」都不足以線性命名名冊，損失在**把一個回合壓成一個 64 維向量**這件事，
不在位址。

**這一輪的預測不是盲的**（照實寫）：§72 的 gate 讀數與兩個臂的數字都看過，W1 是構造保證，W2 是 §70
的 in-sample。真正有資訊量的是 **W3 與 W4 的留出值**，而 turn 模式的**任何**訓練或探針讀數在登記時
都**沒有**跑過。

**什麼會讓這一節作廢**：

1. W0 不過（兩次跑不相同、特徵有非有限值、載體被改動）——整份讀數無效；
2. 載體 `weights_hash` 或 checkpoint sha256 前後不同（探針不得訓練載體，也不得寫回 checkpoint）；
3. 語料 digest 與 §70 的同一個 k 不同（那就不是同一個語料，兩個階段不能比）；
4. 任何人為改動門檻、讀數定義、臂、分割或分支表——改動必須以 amendment 另記。

**這一節不是能力分數**；核心分不變 **0.00/10**。它只回答「S1 指名的寫入是不是損失所在」。

### 73.9 指令（登記；一次跑兩格）

```
for k in 2 5; do
  PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
      --train-sessions 400 --epochs 200 --core turnstore --address turn \
      --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
      --roster-size $k --gate-prefix M --device cpu --out data/pantry_stage/turn73/k${k}_arm
  ./.venv/bin/python scripts/train_pantry_deduction.py --check \
      $(ls -t data/pantry_stage/turn73/k${k}_arm/*.json | head -1)
done
```

量測（每一格跑兩次，第二次只為了 W0 的決定性）：

```
for k in 2 5; do
  for tag in "" "_rerun"; do
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_families.py \
        --report $(ls -t data/pantry_stage/turn73/k${k}_arm/*.json | head -1) \
        --out data/pantry_stage/write73/k${k}${tag}.json --device cpu
    ./.venv/bin/python scripts/probe_pantry_families.py --check \
        data/pantry_stage/write73/k${k}${tag}.json
  done
done
```

k=2 與 k=5 各自沿用 §70 同一個 k 的載體設定（`--roster-size`），語料 digest 必須等於
`416a8a68…`／`69c730e1…`（k=2）與 `d6ca78a8…`／`948b08cc…`（k=5）。

### 73.10 管路與執行

兩個載體都是**離線、detached** 訓練（`setsid nohup`，log 在 `data/pantry_stage/turn73/train.log`），
指令逐字是 §73.9（`--core turnstore --address turn`，其餘與 §70 逐項相同）：

| k | 訓練（wall） | epoch 200 的訓練 loss | 參數 | `weights_hash` | 語料 digest（train／heldout） |
| --- | --- | --- | --- | --- | --- |
| 2 | 12:52:47→13:25:35（1,968 s） | 0.0001 | 168,150 | `b03f2f6a…` | `416a8a68…`／`69c730e1…` |
| 5 | 13:25:36→13:58:00（1,944 s） | 0.0715 | 168,150 | `1e90d9fa…` | `d6ca78a8…`／`948b08cc…` |

* **參數量與 §70 的兩個載體逐位相同**（168,150）。`slot_gate` 在 turn 模式下不進梯度，但仍在模組清單裡，
  所以**沒有**「多一個參數才變好」這條替代解釋。
* 兩個 k 的語料 digest 與 §70 同一個 k 逐位相同，所以兩個階段的留出可以直接並排。
* 兩個載體 `--check` 都 exit 0（M1／M3／M4 PASS，M2／M5 FAIL——與 §70 同一個失敗形狀）。
* 報告的 `config` 是 `core="turnstore"`、`address="turn"`、`memory=true`、`hidden 128`、`emb 64`、
  `lr 5e-4`、`batch 8`、`epochs 200`（10,000 步）、`seed 20261118`、`--train-sessions 400`、
  `--aux-loss 1.0 --aux-mode resolvable`。

量測（§73.9 的第二段）對每個 k 跑**兩次**，四份 JSON 在 `data/pantry_stage/write73/`：

| 檔案 | 內容 | sha256 |
| --- | --- | --- |
| `k2.json` | k=2，第一次 | `51927417…` |
| `k2_rerun.json` | k=2，第二次（獨立行程） | `74603706…` |
| `k5.json` | k=5，第一次 | `a2bf0042…` |
| `k5_rerun.json` | k=5，第二次（獨立行程） | `65c01282…` |

* 同一個 k 的兩次執行**除 `seconds` 外逐鍵相同**（`k2` 與 `k5` 都逐鍵比對，不是只比 branch）。
* W0 的載體不變性：四份報告的 `weights_hash` 前後相同（k=2 `b03f2f6a…`、k=5 `1e90d9fa…`），
  `checkpoint_sha256` 前後相同（k=2 `a345fa8a…`、k=5 `06b81a4b…`）——探針沒有訓練載體，也沒有寫回 checkpoint。
* `H0_instrument` 在兩個 k 都 PASS：三個家族的置換容量控制是 0.2475／0.2575／0.3975（k=2）與
  0.2600／0.3025／0.4150（k=5），全部 < 0.50，且各自的 in-sample 都是 1.0。

### 73.11 登錄後的修正（amendment）：`--check` 的 H1 適用性

**什麼改了**：`scripts/probe_pantry_families.py` 的 `check()` 原本最後一行是「`instrument_ok` 不是 true
就 FAIL」。`instrument_ok` 是 `H0 and H1 and hash` 的合取，而 §73.6 已登記 **H1 在本節不適用**
（新訓練的載體不可能重現 §69 的 cell），所以四份 §73 報告的 `instrument_ok` 必然是 `False`，
`--check` 因此對四份檔案都回 `FAILED`，而且**只**因為這一行。

改成：`check()` 與探針的 exit code 讀 `instrument_problems()`，也就是 W0 的 components——
`H0_instrument.pass`、`carrier_unchanged`、`checkpoint_unchanged`——加上**只有記了 `--reference` 時**
才要求的 `H1_linear_state_reproduces_§69`。沒有 reference 卻宣稱 `instrument_ok: true` 會被拒絕
（反向也守住，所以這不是「放行任何報告」）。

**為什麼是修正而不是放寬**：W0 在登記時寫的是「三個家族的 `H0` 全過＋載體與 checkpoint 不變＋
兩次跑相同」。H1 只是 §70／§72 用來確認「兩個階段共用同一個儀器」的重現檢查；§73 是新載體，
**依構造**不會重現 §69。讓一個依構造必假的檢查否決一整節，是把「儀器壞了」和「這個儀器不適用」
混為一談。

**沒有變的東西（逐項）**：

1. 四份已存的 JSON **一個位元組都沒改**：修正前後 sha256 相同（見 73.10 的表），`--check` 只讀不寫。
2. 四份的 `instrument_ok` 欄位**仍然是 `False`**。它由報告產生時的路徑寫入，而這一輪**不改**那個路徑
   ——改了的話，同一份 checkpoint 重跑會寫出不同的 JSON，反而破壞可重現性。修正只影響 verdict 與
   exit code；`main()` 在這種情況下多印一行
   `instrument : H0 and both hashes hold; H1 is not applicable (no --reference)`。
3. 沒有任何門檻、讀數定義、臂、分割或分支表改變。`H1` 自己的 `pass` 仍是 `False`（不靜默通過），
   `gates()` 也沒有新增鍵（否則 §70／§72 的舊報告會全部變成 stale）。
4. **§70／§72 的既有報告仍然 `--check OK`**（有 `--reference` 時 H1 照樣是必要條件）。所以這不是
   「把 H1 關掉」，是「只在 H1 有答案時才問它」。
5. 修正後把 k=2 的探針再跑**兩次**（輸出到 `/tmp`，不動已存證據）：exit code 0，兩份結果除 `seconds`
   外與 `write73/k2.json` **逐鍵相同**——所以修正沒有動到任何讀數，三次獨立執行給同一組數字。

### 73.12 結果（k=2）

`store` 區塊是**描述性**的（不進任何臂、不進任何閘門），在名冊邊界從實際的 `v` 算：

| 讀數 | 訓練（400） | 留出（200） | §72 的 gate 載體（留出） |
| --- | --- | --- | --- |
| `active_slots` 分佈 | **`{2: 400}`** | **`{2: 200}`** | `{1: 200}` |
| `multi_slot_fraction` | 1.0000 | **1.0000** | 0.0000 |
| rank 1（`σ₂/σ₁ ≤ 1e-3`）的段數 | 0.0000 | **0.0000** | 1.0000 |
| `σ₂/σ₁` 平均 | 0.5732 | **0.5924** | ≈ 0（最大 9.00e-06） |
| `σ₂/σ₁` 最小／最大 | 0.1676／0.9479 | **0.1497／0.9055** | ≤ 9.00e-06 |

→ **W1 PASS**：留出 200 段**全部** `active_slots ≥ 2`、**全部** `rank1_residual > 1e-3`（門檻是 95%）。

三個臂（同一預算：2,000 步、同一個標準化、同一個置換容量控制；§70 的數字並排）：

| 臂 | §70 in-sample／容量／留出 | §73 in-sample／容量／留出 | 訓練內交叉驗證（§73） | Δ 留出 |
| --- | --- | --- | --- | --- |
| `linear_state` | 0.7700／0.2500／0.2850 | 0.8075／0.2550／**0.4650**（93/200） | 0.5425 | **+0.1800** |
| `linear_values` | 0.4975／0.1650／**0.1400** | 0.5325／0.0675／**0.3350**（67/200） | 0.3675 | **+0.1950** |
| `nonlinear_quad` | 0.9375／0.5650／0.3000 | 0.9625／0.5550／**0.4900**（98/200） | 0.5200 | **+0.1900** |

chance（名冊，12 取 2）= 0.0152。

結構檢定（無擬合參數）：留出 AUC **0.8645**、p 0.001（same 270／diff 19,630、66 個不同名冊）；
§70 是 0.7699、p 0.001。

### 73.13 結果（k=5）

| 讀數 | 訓練（400） | 留出（200） | §72 的 gate 載體（留出） |
| --- | --- | --- | --- |
| `active_slots` 分佈 | **`{2: 400}`** | **`{2: 200}`** | `{1: 187, 2: 10, 5: 1, 6: 2}` |
| `multi_slot_fraction` | 1.0000 | **1.0000** | 0.0650 |
| rank 1 的段數 | 0.0000 | **0.0000** | 0.9400 |
| `σ₂/σ₁` 平均 | 0.4306 | **0.4827** | — |
| `σ₂/σ₁` 最小／最大（§72 只記最大） | 0.0783／0.9409 | **0.0694／0.9850** | 0.5240 |

→ **W1 PASS**（200/200 段 `active_slots = 2`、`rank1_residual > 1e-3`）。

| 臂 | §70 in-sample／容量／留出 | §73 in-sample／容量／留出 | 訓練內 CV（§73） | Δ 留出 |
| --- | --- | --- | --- | --- |
| `linear_state` | 0.1525／0.0700／0.0050 | 0.1700／0.0775／**0.0050**（1/200） | 0.0075 | **0** |
| `linear_values` | 0.0850／0.0300／0.0050 | 0.0225／0.0125／**0.0050**（1/200） | 0.0025 | **0** |
| `nonlinear_quad` | 0.4575／0.2550／0.0150 | 0.5200／0.2900／**0.0050**（1/200） | 0.0050 | **−0.0100** |

chance（名冊，12 取 5）= 0.0013；留出的 1/200 = 0.0050 有 4 倍 chance，但 Wilson 下界是 0.0009，
所以那是**一格**，不是訊號。

結構檢定：留出 AUC **0.6804**、p 0.002；§70 是 0.5498、p 0.1918。**p 0.002 > 登記的 α 0.001**，
所以登記的 H4 判「沒有分開」（`transfers: false`），而且留出只有 24 個同冊配對。

### 73.14 預測對帳

| 讀數 | 登記的預測 | 實際 | 對帳 |
| --- | --- | --- | --- |
| W0 | PASS | H0 PASS（兩個 k）、載體與 checkpoint hash 前後相同、兩次跑相同 | 中 |
| W1 | PASS | k=2 與 k=5 都是 100%／100% | 中 |
| W2 | PASS（預期 ≈ §70 的 0.4975） | k=2 **0.5325 < 0.95**、k=5 **0.0225 < 0.95** → **FAIL** | **不中（登記本身有缺陷）** |
| W3 | PASS（k=2 **> 0.1400**） | k=2 **0.3350 > 0.1400**；k=5 0.0050（與 §72 的 0.0050 **相等**，沒有上升） | k=2 中、k=5 不中；但兩者都被 W2 的優先序擋住 |
| W4 | FAIL（預期 0.1400–0.50） | k=2 **0.3350 < 0.50** → FAIL；k=5 0.0050 → FAIL | 中 |
| 分支（k=2） | `W3-write-was-part-of-the-loss` | **`W2-not-readable-in-sample`** | **不中（條件不成立）** |
| 分支（k=5） | 同方向，不預設過 0.50 | **`W2-not-readable-in-sample`**；留出沒有移動 | 不中（條件不成立） |

**W2 的缺陷要照實寫清楚**：W2 的條件是 `linear_values` in-sample ≥ **0.95** 且容量 < 0.50，而它在
§73.8 登記的**預期**是「§70 的 gate 載體在同一批資料上是 0.4975，turn 只是不再混合回合」。
0.4975 < 0.95——也就是說，**照登記的預期，W2 本來就不可能通過**，除非換位址讓 in-sample 多跳 +0.45，
而 §73.8 沒有預測這件事。W2 把 §70 的 `READABLE_FLOOR`（0.95，§70 用在**正控制／非線性家族**上）
套到一個 §70 in-sample 只有 0.4975 的家族上，所以它是一個**依登記必然失敗**的門檻。

因此：

* **本節的裁決是 W2**（優先序固定，寫在跑之前），所以 §73 **不能**宣稱「位址是損失的一部分」。
* 數字確實落在登記預測的形狀上（0.1400 < 0.3350 < 0.50，W3 過、W4 不過）。這只能記成
  **事後觀察**，由下一個登記去檢定，不能在這裡改門檻再回頭宣稱分支命中——那正是「看到結果才調線」。
* k=5 的 W3 在登記時只寫了「同方向」而**沒有寫號碼**（§73.6 的 W3 只有 k=2 的 0.1400），這也是
  一個小的登記鬆散處：照實讀是「留出 0.0050 與 §72 的 0.0050 相等，**沒有移動**」。

### 73.15 照實記的限制

1. **W2 的門檻與它自己的預期互相矛盾**（上表）。這件事不是模型的問題，是登記的問題；在它被重新登記
   之前，這一節對「位址是不是損失」**沒有裁決**。
2. **0.3350 仍是不可用**：它 < 0.50，而且 in-distribution 0.3675 **高於**留出 0.3350——線性家族在自己的
   同分佈分割上都沒有比留出好。in-sample 0.5325 也意味著它只認得一半的訓練名冊。
3. **三個臂一起上升（+0.18～+0.195），不能全部歸給「名冊現在單獨佔一個槽」**。turn 規則同時改變了
   名冊邊界上**讀出看到什麼**（content-addressed 讀取在 2 個非空槽上做 softmax，而不是 1 個），
   `h` 沒有變。這一節只證明「位址換了、數字跟著動」，沒有把 Δ 拆成「寫入」與「讀出」兩塊。
4. **k=5 沒有移動**：`linear_values` 留出 0.0050（1/200，chance 0.0013），in-sample 反而從 0.0850 降到
   0.0225。所以 S1 指名的修法在 k=5 **不是**答案；k=5 的失敗在別處（或這個任務在 5 人名冊下就是更難）。
   這一節沒有分辨這兩者。
5. **非線性臂在兩個 k 都不可裁決**：k=2 in-sample 0.9625 但容量 0.5550 > 0.50（capacity-limited），
   k=5 in-sample 0.5200 < 0.95（讀不出來）。所以「store 的非線性讀出取不到名冊」**仍然沒有量到**。
6. **結構檢定的 k=2 結果（AUC 0.8645、p 0.001）不是「名冊可線性取出」**：它只說同名冊的 state 彼此
   比較近，沒有擬合參數，也沒有說名冊落在哪個方向。k=5 的 p 0.002 > 登記的 α 0.001，判「沒有分開」，
   而且同冊配對只有 24 個，虛無分佈很粗。
7. **`store` 區塊只在名冊邊界量**（那一次前向之後的 16×64 矩陣），沒有普查其他回合；`active_slots`
   的地板是「該段最強槽的 1e-3」，`σ₂/σ₁` 的門檻是 §72 的 1e-3。它是「寫入真的換了」的機械讀數，
   不是「state 裡有名冊」的證據。
8. **單一 seed、單一任務、CPU、每個 k 只有 200 段留出**；chance 是 0.0152（k=2）／0.0013（k=5）。
9. **這一節不是能力分數**；核心分不變 **0.00/10**。

### 73.16 這一節證明什麼、不證明什麼

**證明**：

* 位址真的換了：k=2 與 k=5 的留出**每一段**都是兩個非空槽（`active_slots = 2`）、`σ₂/σ₁` 最小
  0.1497（k=2）／0.0694（k=5）——對照 §72 的「一個槽、`σ₂/σ₁` ≤ 9.00e-06」。
* 同一組語料、步數、參數下，k=2 的三個臂留出全部上升（`state` +0.1800、`values` +0.1950、
  `nonlinear_quad` +0.1900），store 單獨的留出從 0.1400 到 **0.3350**，結構 AUC 從 0.7699 到 0.8645。
* k=5 的位址同樣換了，但**留出沒有移動**（`values` 0.0050 → 0.0050）。

**不證明**：

* **不證明**「位址是損失的一部分」——W2 擋住（而且 W2 的門檻與它自己的預期矛盾）；
  也**不證明**「位址不是損失」。
* 不證明 store 的非線性讀出取不到名冊（k=2 capacity-limited、k=5 unreadable）。
* 不證明 k=5 的失敗在別處（只證明換位址對它沒有幫助）。
* 不證明 0.3350 可用（< 0.50），也不證明它會推廣到別的語料、別的名冊長度或別的 seed。

### 73.17 下一步（W2 的機械輸出）

W2 指名的是**校準**，不是模型：`H2` 的 0.95 地板是 §70 給「載體被訓練去產生的那個標籤」的正控制用的；
套到「載體從未被訓練去產生的名冊標籤」上，它就變成一個依登記必然失敗的門檻（它自己的預期 0.4975
就低於它）。下一個登記要先把「可裁決的擬合」定義成**相對的**——例如同一家族在同一分割上必須顯著
高於自己的置換容量，且 in-distribution 與 held-out 的差距要被記錄——然後才准問 0.3350 是不是轉移。

在這一點被重新登記之前：

* **不得**以「W3 過了」宣稱位址是損失的一部分；
* **不得**用加 epoch／加寬度／加資料去追那個缺口（W2 是擬合判準的問題，不是訓練預算的問題）；
* 也不**得**把 k=5 的 null 讀成「k=5 沒有這個問題」——只讀成「換位址沒有幫到 k=5」。

## §74 「可裁決的擬合」改成相對的：0.3350 是讀到名冊，還是與名冊無關的先驗？

### 74.1 為什麼是這一支

§73 的裁決是 `W2-not-readable-in-sample`，而 W2 的缺陷是**登記**的缺陷：它的 0.95 地板是 §70 給
「載體被訓練去產生的那個標籤」（正控制）用的，卻套到「載體從未被訓練去產生的名冊標籤」上，而 W2 自己
登記的預期是 **0.4975**——照登記的預期它本來就不可能通過。§73.17 因此把下一步定死：**先把「可裁決的
擬合」定義成相對的**（同一家族在同一分割上必須顯著高於自己的置換分佈），然後才准問 0.3350 是不是轉移。

§74 就是那一支。它**不重訓任何東西**：載體、語料、特徵、標準化全部沿用 §73，並且用 `N0` 要求
in-sample／held-out 兩格**逐位**重現 §73 的報告。新增的只有兩件事：

1. 每個讀數都有一個 **400 次的置換分佈**（§70／§72／§73 只有**單次**置換的 `capacity`，所以「顯著高於
   自己的置換容量」在那些節裡無法檢定，只能比較一個點）；
2. 第三個分割 **leave-roster-out（LRO）**：擬合時拿走整個名冊 `R` 的所有段，再讀 `R` 的段。那對名字
   **從來沒有一起當過訓練標籤**，所以 LRO 過關不可能只是「標籤集合的查表」。

### 74.2 量什麼（三個讀數 × 三個分割；只有擬合方式不同，null 都是標籤置換）

| 讀數 | 擬合 | 打分 | null（400 次） |
| --- | --- | --- | --- |
| `in_sample`（Q1 相對擬合） | 真標籤 | 同一批段 | **每次重抽標籤、重擬合**，再對抽過的標籤打分 |
| `heldout`（Q2 轉移） | 真訓練標籤 | 留出 200 段 | 擬合固定，**置換留出標籤** |
| `leave_roster_out`（Q3 組合） | 拿走名冊 `R` 的全部段 | `R` 的段（訓練分割內） | 擬合固定，**置換被評分的標籤** |

每個讀數都記 `exact`（登記的門檻量）與 `overlap`（top-k 取回幾個真名字，**描述性、不進門檻**），
以及 `overlap_histogram`（0..k 各幾段）。三個家族與 §70 逐項相同（`linear_state`＝`[h, read]`、
`linear_values`＝store 的 `v` 攤平、`nonlinear_quad`＝`[x, x*x]`）。

`overlap` 是這一節唯一新增的**量尺**，它讓「讀到兩個名字」與「只讀到其中一個」分得開——`exact` 在
0.2–0.3 的時候兩者都可能是 0。

### 74.3 登記之前已經看過什麼（照實寫）

寫這支程式時跑了一次 **3-draw 的管路測試**（只是要確認兩支以上的 `k` 跑得完、欄位接得起來；輸出到
`/tmp`，不進版控、不進 `data/`）。因為 `observed` 是凍結載體的確定性函數、與 null 無關，那次測試已經
印出：

| k=2 的 observed 格 | `linear_state` | `linear_values` | `nonlinear_quad` |
| --- | --- | --- | --- |
| in-sample exact | 0.8075 | 0.5325 | 0.9625 |
| held-out exact | 0.4650 | 0.3350 | 0.4900 |
| LRO exact（57 個訓練名冊） | 0.2800 | **0.2350** | 0.1075 |
| LRO overlap（滿分 2） | 1.2700 | **1.2050** | 1.0525 |

所以：

* 本節**不宣稱盲預測**。上表的 observed 格在登記前就印出來了；`N0` 的重現也在那次測試裡就 `true`。
* 登記時**還沒有**的是每一個 **400 次 null 分佈**，因此 **Q1／Q2 的 p 值與裁決在登記時仍是未知的**。
  （3 次抽樣的最小 p 是 0.25，碰不到 α，所以那次測試無法預告 Q1／Q2。）
* Q3 的門檻（`0.75k`）與 α 在管路測試**之前**就寫在檔案常數裡，之後**沒有改**。因此 Q3 的裁決
  （1.2050 < 1.5 → FAIL）在登記時已經是算術結果，**不是預測**；這一節的 Q3 價值在於「把判準寫死並
  留下可機械重驗的 null」，不在於預測。
* 兩支程式的常數與門檻在跑之前就 commit（見 74.9）；`k=5` 的 observed 格**沒有**在登記前看過（管路
  測試只跑 `k=2`）。

### 74.4 程式

`scripts/probe_pantry_composition.py`（新檔；不改 §70／§72／§73 的探針，避免舊報告變成 stale）：

* `score_set()`：top-k 取回數與 `overlap`；`chance_block()`：`1/C(12,k)` 與盲取 `k²/12`。
* `in_sample_reading()`／`transfer_reading()`／`leave_roster_out()`：三個讀數，null 都是
  `permute_rows()`（種子 `NULL_SEED + d`，並檢查是雙射）。
* `null_block()`：`p = (1 + #{null ≥ observed}) / (draws + 1)`（平手算沒贏）。
* `gates()`／`branch()`／`check()`：門檻、固定優先序、機械重驗（p 值算術、`exact == correct/n`、
  `overlap == overlap_sum/n`、直方圖總和、門檻與分支可從存檔重算、`N0` 三個條件）。

`tests/test_pantry_composition.py` **17 條**（評分、置換雙射、p 值約定、平手、**α 在 400 次抽樣下
可達**、組合門檻＝`0.75k`、閘門、五條分支優先序、`check()` 的五種拒絕）。沒有載入任何載體。

### 74.5 登記的常數（跑之前寫定）

| 常數 | 值 | 理由（寫在跑之前） |
| --- | --- | --- |
| `NULL_DRAWS` | **400** | 最小可達 p = 1/401 = 0.002494；必須 < α，否則門檻永遠不可能觸發（正是 §73 W2 的缺陷形狀）。有一條測試釘住這件事。 |
| `ALPHA` | **0.005** | 與可達最小 p 相容（0.002494 < 0.005），且對 3 個家族是保守的（6 個檢定 ⇒ 族系誤差 0.03）。 |
| `NULL_SEED` | 20261125 | 第 `d` 次置換用 `NULL_SEED + d`；擬合仍用 §70 的 `PROBE_SEED`，所以只有標籤不同。 |
| 擬合預算 | 2,000 步、batch 64、lr 1e-3、wd 1e-4 | 與 §70 逐項相同，不因這一節改變。 |
| `COMPOSED_OVERLAP_FRACTION` | **0.75** | 「一對」的讀法：平均要取回 `0.75k` 個名字（k=2 → 1.5、k=5 → 3.75）。低於它就是「一個名字＋補位」，不是 binding。 |
| chance | exact `1/C(12,k)`（0.015152／0.001263）、overlap `k²/12`（0.3333／5） | 與 §70 同一個 chance 定義；overlap 的 chance 是盲取 top-k 的期望。 |

### 74.6 閘門（跑之前寫定）

| 閘門 | 條件 |
| --- | --- |
| `N0_instrument` | `carrier_unchanged` ∧ `checkpoint_unchanged` ∧ `reproduction.equal`（三臂的 in-sample／held-out 與 `--source` 指名的 §73 報告**逐位**相同） |
| `Q1_relative_fit`（每臂） | in-sample 的置換分佈 **p < 0.005**（＝觀測值高於幾乎所有「重抽標籤重擬合」的結果） |
| `Q2_transfer`（每臂） | held-out 的置換分佈 **p < 0.005** ∧ held-out exact **>** chance |
| `Q3_composed_from_names`（每臂） | LRO 的 `overlap ≥ 0.75k` ∧ LRO 的置換分佈 **p < 0.005** |

每個閘門另外記 `any`（至少一個家族過），分支只看 `any`。

### 74.7 分叉（跑之前寫定，機械決定；固定優先序）

| # | 條件 | id | 讀法 | 下一步 |
| --- | --- | --- | --- | --- |
| 1 | `N0` 不過 | `N0-instrument` | 載體／checkpoint／重現有一個動了；這一節什麼都不能讀 | 先修儀器 |
| 2 | 沒有家族過 `Q1` | `Q1-no-relative-fit` | 沒有任何家族顯著高於自己的置換分佈 ⇒ 0.3350 在這個預算下是讀出的產物 | 主題是讀出，不是寫入 |
| 3 | 有 `Q1`、沒有 `Q2` | `Q2-fit-but-no-transfer` | 擬合了訓練名冊，但沒有贏過留出的置換分佈 | 缺口在「同分佈 vs 留出」，不在組合 |
| 4 | 有 `Q2`、有 `Q3` | `Q3-composed-from-names` | 沒一起當過標籤的一對，仍被取回到 `0.75k` 以上 ⇒ store 的 `v` 帶的是名字的組合 | **換語料種子重做**才准宣稱 binding |
| 5 | 其餘 | `Q2-transfer-below-the-composition-floor` | 留出贏過 null，但 LRO 沒到登記的 `0.75k` ⇒ 這一節**不**稱它 binding，LRO 的 exact／overlap 連同自己的 null 並列，差多少看得見 | 用 LRO 的 null 格決定是「組合存在但弱」還是「逐段身分記憶」，並先登記留出的「看過／沒看過名冊」分割 |

### 74.8 預測與否證（寫在跑之前；observed 已見，見 74.3）

**預測（只針對還沒量的 null 分佈）：**

* **Q1**：三個家族都 PASS，p 都是最小可達值 0.002494。依據是 §70 的**單次**置換容量
  （0.2550／0.0675／0.5550）遠低於觀測（0.8075／0.5325／0.9625）；但單次抽樣不是分佈，所以這是先驗，
  不是保證。
* **Q2**：三個家族都 PASS（held-out 0.4650／0.3350／0.4900 對 chance 0.0152）。
* **Q3**：三個家族都 FAIL（LRO overlap 1.27／1.205／1.0525 < 1.5），分支 5。**這一條是算術，不是預測**
  （74.3）。
* **分支**：k=2 → 分支 5；k=5 預測 `Q1` 對 `linear_values` 不成立（in-sample 0.0225 vs 單次容量
  0.0125），但 `nonlinear_quad` 0.5200 vs 0.2900 可能過 `Q1`，而其 held-out 0.0050（1/200，chance
  0.0013）預期過不了 `Q2` → 分支 3。

**否證（若成立，本節的結論要照那樣寫）：**

1. 若 `linear_values` 的 in-sample p ≥ 0.005 → `Q1` 不成立，那 §73 的 0.3350 與 §70 的 0.1400 都只
   是讀出噪音，Q2／Q3 免談。
2. 若 `nonlinear_quad` 的 in-sample null 平均 ≥ 0.9625（置換標籤也到得了）→ §70 的
   `capacity_limited: true` 讀法**仍然**是對的，這一節不得說它被推翻了。
3. 若任一臂 LRO `overlap ≥ 0.75k` 且 p < 0.005 → 該臂把**沒一起當過標籤的一對**組合出來；§74 只能記
   成「在這一支語料上」，宣稱 binding 之前必須先換語料種子重做（§75）。
4. 若任一臂 held-out p ≥ 0.005 → 「跨段」不成立，0.3350 只在訓練段內部有效。

**這一節會改變什麼（也已登記）**：若 `nonlinear_quad` 過 `Q1`，則 §70 的 `capacity_limited`（由
**絕對** `CAPACITY_MAX = 0.50` 判的）不是最好的讀法；§74 記錄相對讀法，但**不改寫 §70 的文字**、也不
重算它的門檻——兩節的判準不同，這件事本身要留下來。

### 74.9 指令（登記；一次跑兩格）

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_composition.py \
  --report data/pantry_stage/turn73/k2_arm/pantry_deduction_20261115-125247.json \
  --source data/pantry_stage/write73/k2.json --device cpu \
  --out data/pantry_stage/compose74/k2.json

PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_composition.py \
  --report data/pantry_stage/turn73/k5_arm/pantry_deduction_20261115-132536.json \
  --source data/pantry_stage/write73/k5.json --device cpu \
  --out data/pantry_stage/compose74/k5.json
```

兩個 `k` 都跑，理由與 §73 相同（k=2 是這一節的主格，k=5 是同一讀法在更難的名冊上的複現）。跑完兩份
都要 `--check` 通過才寫結果。

### 74.10 管路與執行

一次 detached 執行（`setsid nohup`，log 在 `data/pantry_stage/compose74/run.log`），兩格依序、`--device cpu`：

| k | 起訖（wall） | 成本 | `--check` | `N0` | 訓練名冊數 | 每名冊段數（min／median／max） |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 14:24:52→14:34:58 | 604 s | OK | PASS | 57 | 2／6／14 |
| 5 | 14:34:58→14:47:27 | 747 s | OK | PASS | 177 | 2／2／6 |

* 兩份報告的 `reproduction.equal` 都是 `true`：三臂的 in-sample／held-out **逐位**等於 `write73/k2.json`
  與 `write73/k5.json`（0.8075／0.4650、0.5325／0.3350、0.9625／0.4900；k=5 的 0.1700／0.0050、
  0.0225／0.0050、0.5200／0.0050）——所以 §74 用的是同一個載體、同一組特徵、同一個標準化，
  差別只在新增的 null 與 LRO 分割。
* `weights_hash` 與 checkpoint sha256 前後相同（`carrier_unchanged`／`checkpoint_unchanged` 都 `true`），
  `instrument_ok` 兩份都是 `true`。
* 每份報告的每個讀數都是 **400 次**置換（`draws: 400`），總共 6 個讀數格 × 400 次重抽標籤
  （`in_sample` 每次都重擬合）＋ LRO 的 fold 擬合。

### 74.11 結果（k=2）

chance：exact **0.015152**（1/66）、overlap **0.3333**（盲取 top-2）。null 一律 400 次，`ge` 是
「null ≥ observed」的次數，`p = (1 + ge) / 401`。

| 臂 | 分割 | exact（正確／n） | overlap（滿分 2） | null exact 平均±sd（最大） | `ge` | p |
| --- | --- | --- | --- | --- | --- | --- |
| `linear_state` | in-sample | 0.8075（323/400） | 1.8075 | 0.2669 ± 0.0176（0.3200） | 0 | 0.002494 |
| | held-out | 0.4650（93/200） | 1.4500 | 0.0181 ± 0.0093（0.0500） | 0 | 0.002494 |
| | leave-roster-out | **0.2800（112/400）** | **1.2700** | 0.0188 ± 0.0065（0.0375） | 0 | 0.002494 |
| `linear_values` | in-sample | 0.5325（213/400） | 1.5300 | 0.0609 ± 0.0111（0.0925） | 0 | 0.002494 |
| | held-out | 0.3350（67/200） | 1.2900 | 0.0182 ± 0.0095（0.0500） | 0 | 0.002494 |
| | leave-roster-out | **0.2350（94/400）** | **1.2050** | 0.0207 ± 0.0068（0.0475） | 0 | 0.002494 |
| `nonlinear_quad` | in-sample | 0.9625（385/400） | 1.9625 | 0.5581 ± 0.0208（0.6200） | 0 | 0.002494 |
| | held-out | 0.4900（98/200） | 1.4850 | 0.0185 ± 0.0097（0.0500） | 0 | 0.002494 |
| | leave-roster-out | **0.1075（43/400）** | **1.0525** | 0.0191 ± 0.0066（0.0450） | 0 | 0.002494 |

overlap 直方圖（0／1／2 各幾段）——它才是「讀到幾個名字」的讀數：

| 臂 | in-sample | held-out | leave-roster-out |
| --- | --- | --- | --- |
| `linear_state` | 0／77／**323** | 3／104／**93** | 4／284／**112** |
| `linear_values` | 1／186／**213** | 9／124／**67** | 12／294／**94** |
| `nonlinear_quad` | 0／15／**385** | 1／101／**98** | 22／335／**43** |

閘門：`N0` PASS；**Q1 三臂全 PASS**（p 都是最小可達值 0.002494）；**Q2 三臂全 PASS**；
**Q3 三臂全 FAIL**——LRO 的 overlap 1.2700／1.2050／1.0525 都低於登記的 **1.5**（`0.75k`），
雖然 LRO 的 p 也都是 0.002494。→ 分支 **`Q2-transfer-below-the-composition-floor`**。

三個要照實讀的重點：

1. **相對判準把 §70 的「capacity-limited」判讀推翻了**：`nonlinear_quad` 的 in-sample 是 **0.9625**，
   而它自己的置換分佈平均 **0.5581**、最大 0.6200、p99 0.6075——觀測值比 400 次置換**任何一次**都高。
   §70 的 `capacity_limited: true` 是**絕對** `CAPACITY_MAX = 0.50` 判出來的，那個 0.50 不是這個家族
   的分佈。§70 的文字不改（它的判準是它登記的），但相對讀法是：**它擬合的是真標籤，不是任意標籤**。
2. **擬合最好的一臂，組合最差**：`nonlinear_quad` in-sample 0.9625 → LRO **0.1075**（43/400）；
   `linear_values` in-sample 最低（0.5325）→ LRO **0.2350**（94/400）。前者的 in-sample 幾乎全滿、
   留出 0.4900，但把那一對名字從擬合標籤拿掉之後只剩 0.1075；後者相反。這個排序不可能由「擬合能力」
   解釋，只能由「它記的是哪一種東西」解釋。
3. **LRO 的跌幅很小**：held-out 0.3350 → LRO 0.2350（少了 **0.100**），而 null 平均是 0.0207。
   一個「記住每一對」的讀出在 LRO 會塌到 null 附近；它沒有。這是**事後觀察**：登記的 Q3 判準（1.5）
   說「不是 binding」，而數字說「組合訊號存在但弱」。

### 74.12 結果（k=5）

chance：exact **0.001263**（1/792）、overlap **2.0833**；組合門檻 `0.75 × 5 = 3.75`。

| 臂 | 分割 | exact（正確／n） | overlap（滿分 5） | null exact 平均±sd（最大） | `ge` | p |
| --- | --- | --- | --- | --- | --- | --- |
| `linear_state` | in-sample | 0.1700（68/400） | 3.8000 | 0.1028 ± 0.0130（0.1400） | 0 | 0.002494 |
| | held-out | 0.0050（1/200） | 2.5700 | 0.0018 ± 0.0028（0.0100） | 125 | 0.314214 |
| | leave-roster-out | 0.0025（1/400） | 2.6950 | 0.0020 ± 0.0022（0.0100） | 224 | 0.561097 |
| `linear_values` | in-sample | 0.0225（9/400） | 3.1275 | 0.0099 ± 0.0049（0.0225） | 10 | **0.027431** |
| | held-out | 0.0050（1/200） | 2.4950 | 0.0012 ± 0.0024（0.0100） | 89 | 0.224439 |
| | leave-roster-out | 0.0050（2/400） | 2.6475 | 0.0017 ± 0.0021（0.0100） | 58 | 0.147132 |
| `nonlinear_quad` | in-sample | 0.5200（208/400） | 4.4175 | 0.3237 ± 0.0200（0.3900） | 0 | 0.002494 |
| | held-out | 0.0050（1/200） | 2.4600 | 0.0014 ± 0.0025（0.0100） | 102 | 0.256858 |
| | leave-roster-out | 0.0025（1/400） | 2.6825 | 0.0020 ± 0.0022（0.0100） | 227 | 0.568579 |

閘門：`N0` PASS；**Q1** `linear_state` PASS、`linear_values` **FAIL**（p 0.027431 > 0.005）、
`nonlinear_quad` PASS；**Q2 三臂全 FAIL**（留出全部 1/200，p 0.224–0.314）；**Q3 全 FAIL**
（LRO overlap 2.65–2.70 < 3.75，且 exact 1–2/400）。→ 分支 **`Q2-fit-but-no-transfer`**。

k=5 的 overlap 額外告訴我們一件事：留出的 overlap 2.46–2.57 **高於** chance 2.0833（null 平均
2.09–2.10），所以它比盲取多抓到 **0.4 個名字**；但 exact 是 1/200——多抓到的那一點沒有變成「整對」。
「比 chance 好一點」與「答得出來」在 5 人名冊上是兩件事。

### 74.13 預測對帳

| 登記的預測 | 實際 | 對帳 |
| --- | --- | --- |
| Q1：三臂都 PASS（p＝最小可達值） | k=2 三臂 p 都 0.002494；k=5 `linear_state` 0.002494、`nonlinear_quad` 0.002494、**`linear_values` 0.027431** | k=2 中；k=5 一臂不中（登記時已寫「k=5 對 `linear_values` 不成立」，方向中） |
| Q2：三臂都 PASS | k=2 三臂 p 都 0.002494；k=5 三臂 p 0.224–0.314 | k=2 中；k=5 全不中（登記時已寫「k=5 held-out 0.0050 預期過不了」，中） |
| Q3：三臂都 FAIL（1.05–1.27 < 1.5） | 三臂 overlap 1.2700／1.2050／1.0525 | 中（但 74.3 已記：這是算術，不是預測） |
| 分支 k=2＝5 | `Q2-transfer-below-the-composition-floor` | 中 |
| 分支 k=5＝3 | `Q2-fit-but-no-transfer` | 中 |
| 否證 2：若 `nonlinear_quad` 的 null 平均 ≥ 0.9625 則 capacity-limited 仍對 | null 平均 **0.5581**（最大 0.6200） | **否證未觸發** → §70 的絕對上限讀法被相對讀法取代（見 74.16） |
| 否證 3：若任一臂 LRO overlap ≥ 0.75k 且 p < 0.005 | 最高 1.2700 < 1.5（k=2）；2.70 < 3.75（k=5） | 否證未觸發 → 不宣稱 binding |
| 否證 4：若任一臂 held-out p ≥ 0.005 | k=2 全部 0.002494；k=5 全部 ≥ 0.224 | k=2 未觸發、k=5 **觸發**（跨段在 k=5 不成立） |

### 74.14 照實記的限制

1. **observed 不是盲的**（74.3）：`k=2` 的 observed 格在登記前就由 3-draw 管路測試印出。本節的
   新資訊是 **400 次 null 分佈**（因此是 p 值與 Q1／Q2 的裁決），不是 observed 格。
2. **Q3 的裁決是門檻的裁決，不是機制的裁決**。LRO 的 p 是 0.002494（三臂）、exact 是 chance 的
   11–18 倍，但 overlap 沒到 0.75k。所以「不稱 binding」是**登記的線**說的；線以下的訊號存在，
   這點在 74.11 第 3 點寫明。
3. **LRO 的 null 是「整批標籤置換」**（pooled），它檢定「預測與該段真正的名冊無關」，不是
   「同名冊 vs 不同名冊」的幾何檢定（那是 §70 的結構檢定在做的事，本節沒有重跑）。
4. **LRO 的分組很不平均**：k=2 的 57 個名冊、段數 2–14（中位 6）；k=5 的 177 個名冊、段數 2–6
   （中位 2）。pooled n 是 400，但每個 fold 的 probe 只看到 ~394 段，**單一名冊的估計變異很大**；
   本節只讀 pooled 值。
5. **留出仍然大部分是「看過的名冊、新的段」**：k=2 的訓練只涵蓋 57 個名冊（12 取 2 共 66 個），
   所以留出裡有一部分名冊從未在訓練出現——但本節**沒有**把留出拆成「看過／沒看過」，
   那個分割是 §75 登記的下一步（74.17）。
6. **overlap 只數「幾個」，不數「哪幾個」**：它不區分「抓到正確的兩個」與「抓到一個對的＋一個系統性
   混淆」。要讀混淆結構需要另一支探針。
7. **單一語料、單一 seed、單一任務、CPU**；k=5 的 5 人名冊只有一個載體。
8. **0.2350／0.2800 仍然不是可用答案**：最好的 LRO 也只有 23.5–28%，留出 33.5–46.5%，都 < 0.50。
   核心分不變 **0.00/10**。
9. 這一節沒有重跑 §73 的 `store` 區塊，也沒有改任何 §70／§72／§73 的門檻或報告。

### 74.15 這一節證明什麼、不證明什麼

**證明：**

* **§73 的 `W2-not-readable-in-sample` 與 §70 的 `capacity_limited` 都是絕對門檻的產物**：
  在同一個 400 段、同一個預算下，三個家族對**真標籤**的擬合都高於自己 400 次置換分佈的**每一次**
  （`linear_values` 0.5325 vs 最大 0.0925；`nonlinear_quad` 0.9625 vs 最大 0.6200）。判準改成相對的
  之後，「讀不出來」這個讀法不成立。
* **留出的答案依賴真正的名冊**（不是與名冊無關的先驗）：k=2 三臂的 held-out p 都是 0.002494，
  null 平均 0.018（＝獨立基線），觀測 0.335–0.490。
* **沒一起當過標籤的一對，仍然讀得到**：`linear_values` 94/400＝**0.2350**、`linear_state` 112/400＝
  **0.2800**，而同一格的 null 平均是 0.0207／0.0188（p 0.002494）。所以「pair 記憶」不是唯一機制：
  把那一對從擬合標籤整個拿掉，只掉 0.10（`linear_values` 0.3350→0.2350）。
* **擬合能力與組合能力反向**：`nonlinear_quad` in-sample 最高（0.9625）而 LRO 最低（0.1075）；
  `linear_values` in-sample 最低（0.5325）而 LRO 最高（0.2350）。
* **k=5 什麼都沒有轉移**：Q1 只有兩臂過（`linear_values` p 0.027 不過），Q2 三臂全不過
  （留出 1/200），LRO 1–2/400。5 人名冊在這個語料上沒有讀出來。

**不證明：**

* **不證明 binding**：登記的組合門檻是 `0.75k`（k=2 = 1.5），最高只有 1.2700。訊號存在、強度不足；
  這一節不把它升格成「store 會組合」。
* 不證明機制是「先解碼兩個名字再配對」還是「在名字層內插」；overlap 1.2050 與 exact 0.2350 對這兩種
  解釋都相容。
* 不證明它會推廣到**別的語料 seed、別的 roster 長度（k=5 就沒有）、別的載體、別的任務**。
* **不重開 §73 的 W3**：§74 量的是「讀數是什麼」，不是「§73 的上升是誰造成的」。
* 不改核心分（**0.00/10**），也不改任何既有節的門檻。

### 74.16 一個被取代的讀法：§70 的 `capacity_limited` 是絕對上限造成的

§70 的 `H3_nonlinear_is_admissible` 判 `capacity_limited: true`，因為 `capacity.exact = 0.5650`
（k=2）與 0.2550 之類的單次置換值超過了登記的 `CAPACITY_MAX = 0.50`。§74 把同一個家族放到
**400 次**置換分佈上：平均 **0.5581**、sd 0.0208、最大 0.6200、p99 0.6075；觀測 in-sample **0.9625**
高於**每一次**抽樣。也就是說 0.50 這個上限不是「這個家族的分佈」的一部分，而是一個外來的絕對值；
用它判「capacity-limited」等於說「任何在隨機標籤上高於 0.50 的家族都不可裁決」，而那與「它有沒有讀到
真標籤」是兩個問題。

**照實記**：§70 的文字不改（它登記的就是那個判準），§74 只記錄相對判準下的讀法。兩節並存，讀者要看
的是「那一節用哪一個判準」。這也**不是**說非線性家族因此可裁決——它的 LRO 是最低的 0.1075，正是
「in-sample 高、組合差」的那一臂。

### 74.17 下一步（Q2 與 Q3 的機械輸出）

分支 `Q2-transfer-below-the-composition-floor` 指名的下一步是 74.7 的第 5 列：**用 LRO 的 null 格
決定「組合存在但弱」還是「逐段身分記憶」**，並且**先登記留出的「看過／沒看過名冊」分割**。下一個登記
（§75）因此是：

1. **把 k=2 的留出拆成兩塊**（名冊在訓練出現過／從未出現過），只讀 `linear_values` 與 `linear_state`；
   這是**同一個已凍結載體、同一個 probe 的一次前向**，不需要重擬合，所以它檢定的是「組合」而不是
   「再擬合」。
2. 若「沒看過的名冊」那塊的 exact 與 overlap 都高於自己的置換分佈，則 0.2350/0.2800 是**組合**，
   不是身分記憶；否則 74.11 第 3 點那個「只掉 0.10」就要改讀成「它靠的是別的東西」。
3. **換語料 seed 重做 LRO**（同一支探針、同一個 `0.75k` 門檻、同一個預算），才准把「store 會組合」
   寫成這一支語料的結論。這一步**不能**用加 epoch／加寬度／加資料代替，也**不能**在這一節直接宣稱。

在 §75 登記之前：**不得**把 Q3 的 FAIL 讀成「store 不會組合」（null 是 0.0207，LRO 是 0.2350），
也**不得**把 0.2350 讀成「會組合」（門檻是 1.5，實際 1.2050）。

## §75 那 0.3350 是「看過的名冊」撐起來的嗎？換語料種子，弱訊號還在嗎？

### 75.1 為什麼是這兩支（§74.17 指名的下一步）

§74 的機械分支 `Q2-transfer-below-the-composition-floor` 指名兩件事，這一節就是那兩件：

1. **把留出拆成「載體看過的名冊」與「沒看過的名冊」。** §74 的留出 200 段混了兩群人：名冊那一對
   名字在 400 段訓練裡出現過，與從未出現過。只有後者能顯示**新的**組合。§74 只讀了 pooled 值，
   所以 0.3350 有可能是「已看過的那一對」在撐。
2. **換語料種子重做 leave-roster-out。** §74 的 `linear_values` LRO 是 0.2350（null 平均 0.0207），
   登記的門檻是 1.5 overlap：**訊號對 null 是真的、對門檻是不夠的**。第二支語料決定這個形狀是語料的
   還是載體的。

### 75.2 量什麼

**A（`--part seen`；§73 的 k=2 載體，凍結，不重訓）**

每個家族（`linear_state`、`linear_values`，就是 §74.17 指名的那兩個）用**與 §74 留出讀數完全相同**
的方式擬合：400 段訓練段、真標籤、2,000 步、`PROBE_SEED`，然後**一次前向**掃過 200 段留出。接著把留出
的列按「名冊 key 是否出現在 57 個訓練名冊裡」切成兩格，**每一格用自己那批列做 400 次標籤置換**（擬合
不動，只換被評分的標籤）。

因為擬合與 §74 的留出讀數逐位相同，**pooled 的 exact 必須重現 §74 存檔的那一格**（`N0a`）——否則這
就不是「同一個量測的切分」，而是另一個量測。`linear_state` 對 0.4650、`linear_values` 對 0.3350
（`data/pantry_stage/compose74/k2.json`）。

**B（`--part fresh`；新語料種子 20261126，重訓）**

§73 的訓練指令**只改 `--pantry-seed` 與輸出路徑**：400 段、200 epochs、10,000 步、168,150 參數、
`--core turnstore --address turn --aux-loss 1.0 --aux-mode resolvable --minimal-binding
--order-augmented --roster-size 2 --gate-prefix M`，**沒有**加 epoch／寬度／資料。然後跑 §74 的三個
讀數（`in_sample`、`heldout`、`leave_roster_out`），**同一個 400 次抽樣、同一個 α、同一個 `0.75k`
門檻**（§74 的程式直接 import，不複製一份）。

§73 的 reproduction 閘門對新語料**依構造不成立**（那個 corpus 在 §73 評分時不存在），所以 B 的儀器閘門
是 `N0b`：載體 `weights_hash` 與 checkpoint sha256 前後不變 ∧ 兩份 corpus digest 有記錄，而
`reproduction_applicable` 明確記成 `false`、`equal` 記成 `false`——不假裝重現。

### 75.3 登記之前已經看過什麼（照實寫）

* **看過語料組成（不是分數）**：k=2 的留出 200 段裡，**176 段**的名冊出現在訓練（57 個），**24 段**
  的名冊從未出現（9 個名冊，每組 1–4 段）。這是決定 A 的分格能不能裁決的必要資訊——若沒看過就登記，
  可能登記一個**永遠無法觸發**的門檻（正是 §73 W2 的缺陷形狀）。看的是 roster key 的分布，**沒有**
  擬合任何 probe、**沒有**讀任何分數。
* **沒看過 A 的分格分數**：兩格都需要擬合 probe；登記時一格都沒跑。
* **沒看過 B 的任何東西**：語料種子 20261126 尚未生成、載體尚未訓練。
* **管路測試**（登記前，只為確認程式接得起來）：見 75.9——跑在**未登記的那一格**（k=5 的 A 分格），
  輸出到 `/tmp`、不進 `data/`。它**不會**出現在本節的分數裡；若它洩漏了 k=5 的形狀，本節照實記，
  但 k=5 不是本節登記的格。

### 75.4 登記的常數（跑之前寫定；程式在 import 時斷言與 §74 相同）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `NULL_DRAWS` | **400** | 與 §74 相同；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | 20261125 | 同 §74：`NULL_SEED + d`，擬合仍用 `PROBE_SEED`。 |
| `ALPHA` | **0.005** | 同 §74。 |
| `COMPOSED_OVERLAP_FRACTION` | **0.75** | 同 §74；k=2 的門檻是 overlap 1.5。 |
| A 的家族 | `linear_state`、`linear_values` | §74.17 指名；**不**加第三個家族（那會把兩格的問題變成家族搜索）。 |
| B 的家族 | §74 的三個 | 複現要用同一組讀數。 |
| B 的語料種子 | **20261126** | 尚未使用過的種子；其餘訓練引數與 §73 逐項相同。 |

### 75.5 閘門（跑之前寫定）

**A**

| 閘門 | 條件 |
| --- | --- |
| `N0a_instrument` | `carrier_unchanged` ∧ `checkpoint_unchanged` ∧ pooled 的 exact **等於** §74 存檔的兩格 |
| `S1_seen`（每家族） | seen 格 p < 0.005 ∧ seen exact > chance（0.015152） |
| `S2_unseen`（每家族） | unseen 格 p < 0.005 ∧ unseen exact > chance |

**B**：`N0b_instrument`（見 75.2）＋ §74 的 `Q1_relative_fit`／`Q2_transfer`／`Q3_composed_from_names`
（同一組算術、同一個 `any`）。

### 75.6 分叉（跑之前寫定，機械決定；固定優先序）

**A：`N0a` > `S2` > `S1`**

| # | 條件 | id | 讀法 | 下一步 |
| --- | --- | --- | --- | --- |
| 1 | `N0a` 不過 | `N0-instrument` | 載體／checkpoint／重現有一個動了；這一節什麼都不能讀 | 先修儀器 |
| 2 | 任一家族 `S2` 過 | `U1-unseen-rosters-answer` | 載體**從未看過**的那一對名字，留出仍然顯著高於自己的 null | 先做 B（第二支語料）才准讀成組合 |
| 3 | 只有 `S1` 過 | `U2-seen-rosters-only` | 只有「看過的名冊」那格高於 null ⇒ pooled 的 0.3350 是「已看過的那一對」在撐 | 下一個要量的是「必須回答沒看過的一對」的載體，不是更大的留出池 |
| 4 | 兩格都不過 | `U3-neither-cell-above-null` | pooled 撐不過切分 | 主題是讀出，不是切分 |

**B：`N0b` > `Q1` > `Q2` > `Q3`**

| # | 條件 | id | 讀法 | 下一步 |
| --- | --- | --- | --- | --- |
| 1 | `N0b` 不過 | `N0-instrument` | 新載體／checkpoint／語料記錄動了 | 先修儀器 |
| 2 | 沒有家族過 `Q1` | `Q1-no-relative-fit` | 新語料上沒有任何家族高於自己的置換分佈 | **停止**：不得加 epoch／寬度／資料 |
| 3 | 有 `Q1`、沒有 `Q2` | `Q2-fit-but-no-transfer` | §74 的轉移沒有複現 | 轉移在第三支種子之前只算那一支語料的 |
| 4 | 有 `Q2`、有家族過 `Q3` | `Q3-composed-from-names-on-second-seed` | LRO 在**新語料**上到達 `0.75k` | 仍不宣稱 binding；要第三支種子＋第二個任務 |
| 5 | 有 `Q2`、沒有 `Q3`、但至少一個 LRO 的 **p < 0.005** | `Q3-below-floor-again` | 與 §74 同形：對 null 有訊號、對門檻不夠 | 問「寫入要裝什麼才會提高它」，不是加預算 |
| 6 | 其餘 | `Q3-flat-on-second-seed` | LRO 在新語料上**與置換不可分** ⇒ §74 的弱訊號是那一支語料的 | 撤回 §74 的「弱而存在」讀法 |

### 75.7 預測與否證（寫在跑之前）

**A（k=2）**

* pooled 必須逐位重現（`N0a`）；這是儀器，不是預測。
* **seen 的 exact 高於 unseen**（若 pooled 0.4650 且 unseen ≈ 0.25，則 seen ≈ 0.49）。
* **`S2` 至少一臂過**（unseen 24 段；若真率 ≈ 0.25，6/24 就遠超 400 次抽樣的最大值）。**這條不確定**：
  24 段的解析度是 1/24 = 0.0417，真率若低到 0.10（2–3 段）就可能不過。因此登記：**S2 過了只算
  「在這個大小上的證據」；S2 不過不算「組合不存在」**（這是 75.2 就寫定的讀法規則，不是事後補的）。

**B（新種子 20261126）**

* `N0b` 過；`Q1` 至少 `linear_state` 與 `nonlinear_quad` 過（§74 的 k=2 分別是 0.8075／0.9625 對
  null 0.2669／0.5581，`linear_values` 0.5325 對 0.0609 也預期過）。
* `Q2` 三臂都過（§74 的 k=2 三臂 p 都是最小可達值）。
* **`Q3` 三臂都不過門檻，但 `linear_values` 的 LRO p < 0.005** → 分支 **`Q3-below-floor-again`**。

**否證（若成立，結論照那樣寫）**

1. 若 B 的 `Q1` 全不過 → `Q1-no-relative-fit`，且**登記的停損**：不得以加 epoch／寬度／資料去追
   （§73 W2 的教訓是判準問題不是預算問題；這裡也一樣，換語料不是換預算）。
2. 若 B 的 `Q2` 全不過 → `Q2-fit-but-no-transfer`，§74 的轉移被記成該語料所有。
3. 若 B 的 LRO 對 null **不可分**（p ≥ 0.005）→ `Q3-flat-on-second-seed`，**§74 的「組合訊號弱而存在」
   要撤回**，只留「門檻沒到」。
4. 若 A 的 `S2` 不過而 `S1` 過 → `U2-seen-rosters-only`，且**不得**把 pooled 的 0.3350 當成新組合的證據。
5. 若 B 的 LRO 到達 `0.75k` → `Q3-composed-from-names-on-second-seed`；**仍然不宣稱 binding**（要第三支
   種子＋第二個任務），只記「不是單一語料的運氣」。

### 75.8 程式（新檔；不改 §74 的探針，避免 §74 的存檔變成 stale）

`scripts/probe_pantry_split75.py`：

* `load_composition()`：import §74 的模組（null 機制、三個讀數、`score_set`、`chance_block` 只有一份），
  並在 import 時斷言四個常數與本節登記值相同——任何一邊改了就是 `SystemExit`，不會靜默分岔。
* A：`split_rows()`（切分並驗證是分割）、`subset_reading()`（**只用該格的列**做 400 次置換）、
  `wilson()`（區間；24 段的寬度要看得見）、`seen_gates()`／`seen_branch()`／`check()`。
* B：`fresh_gates()`（§74 的 `gates()` ＋ 換成 `N0b`）、`fresh_branch()`／`check()`。
* `--check` 重驗：p 值算術、`exact == correct/n`、`overlap == overlap_sum/n`、Wilson 區間、直方圖總和、
  抽樣數、α、門檻、閘門可從存檔重算、分支 id、儀器欄位。

`tests/test_pantry_split75.py`（契約，不載入任何載體）：切分是分割且不漏列、`subset_reading` 只用該格的
列做置換、α 在 400 次抽樣下可達、門檻＝`0.75k`、兩張分叉表的優先序、`--check` 的各種拒絕。

### 75.9 指令（登記）

訓練（**只改種子與輸出路徑**；§73 的命令其餘逐項相同）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address turn \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261126 --device cpu \
    --out data/pantry_stage/seed75/k2_arm
./.venv/bin/python scripts/train_pantry_deduction.py --check \
    $(ls -t data/pantry_stage/seed75/k2_arm/*.json | head -1)
```

A 與 B 的量測：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_split75.py --part seen \
    --report data/pantry_stage/turn73/k2_arm/pantry_deduction_20261115-125247.json \
    --reference data/pantry_stage/compose74/k2.json --device cpu \
    --out data/pantry_stage/split75/seen_k2.json
./.venv/bin/python scripts/probe_pantry_split75.py --check data/pantry_stage/split75/seen_k2.json

PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_split75.py --part fresh \
    --report $(ls -t data/pantry_stage/seed75/k2_arm/*.json | head -1) --device cpu \
    --out data/pantry_stage/split75/fresh_k2.json
./.venv/bin/python scripts/probe_pantry_split75.py --check data/pantry_stage/split75/fresh_k2.json
```

**管路測試（登記前，未登記的格；已執行，結果照實記）**：`--part seen` 跑在 **k=5** 的報告上
（`--reference data/pantry_stage/compose74/k5.json`），只為確認切分／置換／重現／`--check` 接得起來，
輸出到 `/tmp`（`/tmp/opencode/split75_k5_plumbing.json`，`--check OK`，2.67 s）。它**完成了**：
pooled 的 exact 逐位重現 §74 的 k=5 格（0.0050／0.0050），切分是 60 seen／140 unseen（177 個訓練名冊、
125 個沒看過的名冊，因為 `C(12,5)=792`），兩臂的兩格都沒有高於自己的 null → `U3-neither-cell-above-null`。

這件事要照實記：**k=5 的分格形狀我已經看過**（與 §74 的 k=5「什麼都沒轉移」一致，不意外）。**k=2 的格
在登記時仍然一格都沒跑**，而本節登記的是 k=2 的 A 與新種子 20261126 的 B。k=5 的數字**不進**本節任何
表格、也不當預測的依據；它唯一的用途是證明儀器接得起來。

### 75.10 這一節不是能力分數

核心分不變 **0.00/10**；A 與 B 都是診斷。B 若過了門檻也**不**宣稱 binding。

### 75.11 執行（分離式；三份 `--check` 都 OK，沒有 amendment）

```
data/pantry_stage/seed75/run.sh   （setsid nohup；log data/pantry_stage/seed75/run.log）
A  seen    15:09:36 → 15:09:41    3.4 s   data/pantry_stage/split75/seen_k2.json    --check OK
B  train   15:09:41 → 15:41:27  1,904.6 s data/pantry_stage/seed75/k2_arm/pantry_deduction_20261115-150941.json
                                          --check OK
B  fresh   15:41:28 → 15:51:44    614.9 s data/pantry_stage/split75/fresh_k2.json   --check OK
```

三份存檔的 `instrument_ok` 都是 `true`。**探針與測試檔在登記 commit `9847c390b` 之後一個位元組都沒改**
（`scripts/probe_pantry_split75.py` sha256 `6768a7ef…`、`tests/test_pantry_split75.py` `6927ccb1…`，
執行前後相同），所以本節**沒有 amendment**，也**沒有作廢的執行**。登記前跑過的 k=5 管路測試
（§75.3／§75.9）仍只留在 `/tmp`，不進版控，也不進本節任何表格。

### 75.12 A：pooled 的 0.3350 是「看過的名冊」撐的（`U2-seen-rosters-only`）

切分（登記前看過組成、沒看過分數）：200 段留出 → **176 seen／24 unseen**，訓練名冊 57 個，沒看過的名冊 9 個
（`Alex+Elena` 3、`Alex+Grace` 3、`Alex+Hana` 4、`David+Lena` 4、`Elena+Frank` 2、`Frank+Ivan` 2、
`Grace+Judy` 1、`Ivan+Lena` 3、`Judy+Kevin` 2）。

`N0a_instrument` **PASS**：`carrier_unchanged`、`checkpoint_unchanged`、`reproduction.equal` 都 `true`，
pooled 的 exact **逐位**重現 §74（`linear_state` 0.4650＝93/200、`linear_values` 0.3350＝67/200），
所以這兩格確實是**同一個量測的切分**，不是另一個量測。

| 家族 | 格 | n | exact | Wilson | null 平均 | null 最大 | p | overlap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `linear_state` | seen | 176 | **0.5170**（91） | 0.4436–0.5897 | 0.019796 | 0.0568 | **0.002494** | 1.5114 |
| `linear_state` | unseen | 24 | 0.0833（2） | 0.0232–0.2585 | 0.013446 | 0.0833 | 0.027431 | 1.0000 |
| `linear_values` | seen | 176 | **0.3693**（65） | 0.3015–0.4427 | 0.019869 | 0.0625 | **0.002494** | 1.3466 |
| `linear_values` | unseen | 24 | 0.0833（2） | 0.0232–0.2585 | 0.013446 | 0.0833 | 0.027431 | 0.8750 |

`S1_seen` 兩臂都 **PASS**；`S2_unseen` 兩臂都 **FAIL**（p 0.027431 > α 0.005）→ 分支
**`U2-seen-rosters-only`**。overlap 直方圖（0/1/2）：state seen 1/84/91、unseen 2/20/2；
values seen 4/107/65、unseen 5/17/2。

**照實記一個事後觀察**（不是登記的閘門）：unseen 的 **overlap** 是 1.0000／0.8750，高於 chance 0.3333，
也高於那一格 null 的平均 0.3922 與最大值 0.6667——但 exact 只有 2/24。也就是說，24 段裡答對的那兩段
**各只抓到一個名字**（state：20 段抓到一個、2 段抓到兩個；values：17 段抓到一個、2 段抓到兩個），
沒有抓到「那一對」。登記的閘門是 exact，所以這**不算** `S2` 過；它只說明「單一名字」的訊號比「整對」先出現。

### 75.13 B：形狀複現、幅度沒有（`Q3-below-floor-again`）

`N0b_instrument` **PASS**：新載體與 checkpoint 前後不變、兩份 corpus digest 有記錄
（train `527d434cc706…`、held-out `69c730e116e1…`），而 `reproduction_applicable` 記成 **`false`**
（§73 的 cell 不屬於這支語料，依構造不能重現；不假裝重現）。

| 家族 | in-sample | null | p | held-out | null | p | LRO | overlap | p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `linear_state` | 0.5475 | 0.2448 | 0.002494 | 0.2200 | 0.017663 | 0.002494 | 0.0625（25/400） | 1.0475 | 0.002494 |
| `linear_values` | 0.3275 | 0.0995 | 0.002494 | 0.1600 | 0.0166 | 0.002494 | 0.0525（21/400） | 0.9375 | 0.002494 |
| `nonlinear_quad` | 0.8350 | 0.4991 | 0.002494 | 0.2250 | 0.01765 | 0.002494 | 0.0350（14/400） | 0.9625 | 0.027431 |

`Q1_relative_fit` **PASS**（三臂）、`Q2_transfer` **PASS**（三臂）、`Q3_composed_from_names` **FAIL**
（三臂的 overlap 都 < `0.75k`＝1.5）→ 分支 **`Q3-below-floor-again`**。LRO 直方圖（0/1/2）：
state 6/369/25、values 46/333/21、quad 29/357/14；57 個名冊、folds 2–14、中位數 6。

**幅度**（§74 k=2 → §75 B）：exact **0.2800 → 0.0625**、**0.2350 → 0.0525**、**0.1075 → 0.0350**；
overlap **1.2700 → 1.0475**、**1.2050 → 0.9375**、**1.0525 → 0.9625**。三臂的 p 仍然 ≤ 0.027431
（高於自己的 null），但「比 chance 多抓幾個名字」從 **+0.27～+0.21** 掉到 **+0.05～−0.06**
（`linear_values` 的 0.9375 甚至低於 1，也就是平均抓不到一個完整名字）。

**一個必須並列的共變數（不是藉口）**：這支語料的載體**沒有擬合到同樣的程度**。同一個指令
（400 段、200 epochs、10,000 步、168,150 參數），§73 的 k=2 訓練 loss 到 **0.0001**，§75 B 只到
**0.6345**；生產路徑自己的讀數（`results.full`）是 **0.1650／in-roster 0.2850／ranking 0.5900**，
對 §73 的 **0.3700／0.7350／0.4800**，所以它自己的閘門是 `M1_fits_the_declared_items` FAIL、
`M2_heldout_beats_chance` FAIL（`all_pass: false`；`--check` 仍 OK，因為 `--check` 驗的是算術與欄位，
不是門檻）。因此「幅度沒複現」**不能全歸給語料**：載體在這支種子上本來就比較弱，而 §75.7 的停損
**禁止用加 epoch／寬度／資料去追**。本節只記「形狀複現（高於 null、遠低於門檻）、幅度沒有」，
並把擬合差異登記為下一節必須控制的變數。

讀法上的對照：B 的 `Q1`／`Q2` 過、生產路徑的 `M1`／`M2` 不過，兩者不矛盾——前者是**相對置換分佈**
上的超額，後者是**絕對地板**（§74.16 已經量過絕對地板與分佈無關）。

### 75.14 預測對帳

| # | 登記的預測 | 實際 | 判 |
| --- | --- | --- | --- |
| A0 | pooled 逐位重現 §74（儀器） | `reproduction.equal: true`，0.4650／0.3350 | **命中** |
| A1 | seen 的 exact 高於 unseen | 0.5170／0.3693 對 0.0833／0.0833 | **命中** |
| A2 | `S2` 至少一臂過（真率 ≈0.25 時 6/24 就夠） | 兩臂都 **2/24**，p 0.027431 | **落空（miss）** |
| B0 | `N0b` 過 | PASS（`reproduction_applicable: false`） | **命中** |
| B1 | `Q1` 至少 `linear_state` 與 `nonlinear_quad` 過 | 三臂都過（p 都是 0.002494） | **命中** |
| B2 | `Q2` 三臂都過 | 三臂都過（p 都是 0.002494） | **命中** |
| B3 | `Q3` 三臂不過門檻、`linear_values` 的 LRO p < 0.005 → `Q3-below-floor-again` | 三臂不過門檻；LRO p 0.002494／0.002494／0.027431 | **命中（含分支）** |

**A2 落空要照實讀**：登記時就把讀法寫死了——「`S2` 過了只算在這個大小上的證據；`S2` 不過**不算**組合不存在」
（§75.2、§75.7）。所以這一條落空的結論是「**24 列的格在這個大小上量不出來**」，不是「沒有組合」。
具體差多少：那一格 null 的最大值是 **0.0833（2/24）**、有 10 次抽樣達到它，觀察值正好坐在 null 的頂端；
存檔的 null **一次都沒到 3/24**，所以 3/24＝0.1250 會是 `ge = 0`、p＝0.002494、**過關**。
換句話說，這一格「過」與「不過」的差是**一段**。

### 75.15 照實記的限制

1. **A 的 unseen 格只有 24 列**：解析度 1/24＝0.0417，Wilson 0.0232–0.2585；null 最大 0.0833，
   觀察值就等於它（ge 10 → p 0.027431）。差一段就翻面，所以它能排除「很強的組合」，不能排除「弱組合」。
2. **未見名冊的列數不均**：9 個名冊分佈 1–4 列（`Alex+Hana`、`David+Lena` 各 4；`Grace+Judy` 只有 1），
   所以那一格不是等權重的，兩對就佔掉 8/24。
3. **幅度沒複現，而且擬合也沒複現**（loss 0.0001 → 0.6345；生產讀數 0.3700 → 0.1650）。兩件事同時變，
   「語料 vs 載體」因此分不開；而 §75.7 的停損讓「加預算」不能當下一步。
4. **§73 的 k=2 可能是擬合特別深的那個種子**（loss 0.0001 ≈ 記住 400 段）。目前只有兩個種子的資料，
   不能說它是常態或例外。
5. **A 的 unseen overlap 不是登記的閘門**（1.0000／0.8750 對 null 最大 0.6667）：它顯示「一個名字」的訊號，
   但 exact 沒到，所以不算 `S2` 過。
6. **k=5 的分格形狀在登記前已看過**（§75.3／§75.9：`/tmp`、`--check OK`、
   `U3-neither-cell-above-null`）。k=2 的兩格在登記時沒跑過，但本節因此**不宣稱**「分格機制是盲的」，
   只宣稱 k=2 的**分數**是登記之後才算的。
7. **B 只換了語料種子**，其餘引數逐項相同；它回答的是「同一條指令換一支語料會怎樣」，
   不是「語料是唯一變因」。

### 75.16 這一節證明什麼、不證明什麼

**證明**

* §74 的 200 列留出 pooled 0.4650／0.3350，**切開之後只剩 seen 那 176 列在撐**（0.5170／0.3693，
  p 都是最小可達值 0.002494），而 24 列未見名冊與自己的置換分佈不可分（0.0833，p 0.027431）。
  這是「pooled 不是新組合的證據」的直接量測，不是從 §74 的門檻推出來的。
* §74 的**相對判準**（`Q1`／`Q2`）在**第二支語料種子**上複現（三臂、p 都是 0.002494），所以那不是
  單一語料的運氣；LRO 的**形狀**（高於 null、遠低於 `0.75k` 門檻）也在兩個種子上重複。

**不證明**

* **不證明組合不可能**：24 列、差一段就翻面、且新載體擬合較弱（§75.15 第 1、3 條）。
* **不證明幅度**：0.2800／0.2350 的 LRO 沒有複現（0.0625／0.0525），所以 §74「弱而存在」的**大小**
  不能外推，只能留住「方向」。
* **不宣稱 binding**、不是能力分數；核心分不變 **0.00/10**。

### 75.17 下一步（下一節要登記什麼；不是加預算）

§75.6 的兩張分叉表把下一步指到**寫入**，不是讀出、不是 epoch／寬度／資料（§75.7 的停損）：

1. **先讓 unseen 格有解析度**。24 列（9 個名冊、1–4 列）連「差一段」都分不出來。下一個量測要**先登記
   一個可觸發的功率地板**（像 §75.3 那樣在跑之前算：真率多少、幾列、α 多少時會過），並在**新種子**上做，
   不能在 §75 的格上調。做法至少兩種，都要預先寫明：(a) 語料讓留出裡有更多「訓練沒出現過的名冊」，
   且每組 ≥ N 列；(b) 把 LRO 的 folds 換成「整組名冊 × 更多列」的切法，並同時報每折的列數。
2. **把擬合當共變數控制住**。B 的 loss 0.6345 對 §73 的 0.0001 說明「同一條指令」不等於「同一個載體」。
   下一節要嘛**固定擬合**再換語料，要嘛**每個讀數旁邊都印擬合**，並在登記時寫明「擬合差異多大時讀數不可比」。
   仍然**不得**用加 epoch 去追。
3. **主體是寫入**。§75.6 分支 5 的 `next` 是「問寫入要裝什麼才會提高它」。候選（**尚未登記、尚無結果**）：
   讓 store 以**無序對**為位址寫入（`address=pair`），使「從未一起出現的一對」在寫入端就有位置，而不是
   只能靠讀出端把兩個名字併起來；以及讓 aux loss 要求「同一對的兩個名字在同一個槽可讀」。這些都必須是
   **下一節的預登記**，不是本節的結論。

**這一節不是能力分數**；核心分不變 **0.00/10**。

---

## §76 每回合寫入的解析度（等預算 A/B）

### 76.1 這一節問什麼

§75.17 的第 3 點指名「主體是寫入」。這一節把「寫入」變成一個**只有一個治療**的 A/B：

> 在**參數、語料、初始化、預算完全相同**的條件下，把「一個回合寫進**一個**槽」換成
> 「一個回合切成 4 塊寫進 **4 個**槽」，能否提高 leave-roster-out 的組合讀數？

它**不**加 epoch、寬度或資料；它**不**換讀出家族；它**不**改門檻。

### 76.2 登記前實測到的兩件事（決定了治療是什麼）

這兩件事都在**登記之前**量到，且都足以讓原本的治療作廢：

1. **`write_strength="force"` 是死的。** 在 §73 已訓練的 k=2 載體上，
   `sigmoid(write_gate(h))` 在**每一個回合**（train 與 held-out 都是）落在 **0.9964–0.9987**。
   把它強制成 1.0，寫入量只改變 **< 0.4%**。所以「強制寫入」不是一個治療，是**同一個治療的數值噪音**。
   這個候選在登記前被**丟棄**；`write_strength="force"` 留在核心裡作為**已記錄的死路**，不是本節的臂，
   並有契約測試守住它仍然存在且語意不變。
2. **`active_slots = 2` 是結構性的，不是學到的「11 回合裡留 2 個」。** 每個 session 是**4 個回合**，
   名冊邊界落在**第 2 個回合之後**；因此 §73 的 k=2 在邊界上「有 2 個槽非空」是**寫了 2 次**的必然結果。
   真正的非結構性事實是：**16 個槽裡有 14 個是空的**——整個回合（名冊、證據、值）被壓成**一個**
   64 維向量放進**一個**槽。

還有一件**必須照實記**的事：在確認上面第 1 點之前，曾為了確認管路而啟動過一次**以 `force` 為臂**的
探針（輸出到 `/tmp`、未進 `data/`）。確認該治療已死後**立即終止**，沒有產生任何 §76 讀數，也沒有寫入
任何 `data/` 檔案。那次啟動**不計入**本節，只作為「先量前提、再登記」的紀錄。

### 76.3 治療：每回合寫入的解析度

| 臂 | 寫入規則 | 參數 | 語料 |
| --- | --- | --- | --- |
| **control** | `address="turn"`, `write_slots=1`（§73 的寫入）：回合 `k` 把整個 `key_proj(h)` / `value_proj(h)` 寫進槽 `k`。 | 168,150 | 種子 20261127 |
| **treatment** | `address="turn"`, `write_slots=4`：同一組投影的**第 j 塊**寫進槽 `k*4+j`，其餘位置為 0。 | 168,150 | 種子 20261127 |

`key_proj` / `value_proj` 是**同一個線性映射**，只有**散佈方式**不同；因此參數數量、初始化與梯度预算
逐項相同。每個塊在自己的槽裡**只佔自己那一段、其餘為 0**，所以 `read_vector` **不用改**：查詢與某個
塊槽的內積只看到那一塊。也就是說，讀出從「內容定址**整個回合**」變成「內容定址回合的**片段**」，
讀出端可以在同一個回合裡給「名字那段」與「兇手那段」不同的權重。

一個**單元測試釘住**讓這是「只改寫入」的不變量：4 個塊**加起來等於** control 會寫的那個單槽值
（key 與 value 都測）。另一點照實記：兩個臂是**分開訓練**的，所以 `linear_values` 的位移讀的是**擬合**，
不是內容；內容不變量由測試釘住，不由跨臂的 `values` 讀數釘住。

### 76.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `NULL_DRAWS` | **400** | 同 §74／§75；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | 20261125 | 同 §74；擬合仍用 `PROBE_SEED`。 |
| `ALPHA` | **0.005** | 同 §74。 |
| `COMPOSED_OVERLAP_FRACTION` | **0.75** | 同 §74；k=2 的門檻是 overlap **1.5**。 |
| `CONTRAST_MARGIN` | **0.05** | 400 列上的 20 列。**跑之前**寫定：小於此的差不算「有效應」。 |
| `FIT_COMPARABILITY` | **0.15** | 兩臂的 in-sample 讀數差超過此值時，LRO 的差**不可比**（擬合是共變數，不是證據）。 |
| `UNSEEN_FLOOR` | **0.125** | 24 列上的 **3/24**；§75.15 顯示 3 列就足以清掉它儲存的 null（p=0.002494）。 |
| `SLOTS_PER_TURN` | control **1**、treatment **4** | 治療的定義本身。 |
| `MECHANISM_MAX` | control **3**、treatment **8** | 邊界只看到 **2 個回合**：1×2=2（允許 3 的雜訊），4×2=8（必須達到）。 |
| 家族 | `linear_state`、`linear_values`、`nonlinear_quad` | §74 的三個；**不**加第四個（那會把 A/B 變成家族搜索）。 |
| 語料種子 | **20261127** | 兩臂共用、且 §73／§75 都沒用過；其餘訓練引數與 §73 逐項相同。 |

### 76.5 閘門與機制檢查（跑之前寫定）

| 閘門 | 條件 |
| --- | --- |
| `N0_instrument` | `carrier_unchanged` ∧ `checkpoint_unchanged` ∧ 語料 train/heldout digest 都有记录。§73 的複現閘門**不適用**（這是它沒量過的語料），照實記為 `reproduction_applicable=False`。 |
| `W_mechanism` | **control**：留出名冊邊界的 `active_slots` 中位數 **≤ 3**。**treatment**：**≥ 8**。兩者都不過＝A/B 根本沒發生（`N0-instrument`）。 |
| `Q1_relative_fit` | 每家族 in-sample p < 0.005（§74 的算術）。 |
| `Q2_transfer` | 每家族 held-out p < 0.005 **且** exact > chance。 |
| `Q3_composed_from_names` | 每家族 LRO overlap ≥ **1.5** **且** p < 0.005。 |
| `S1_seen`／`S2_unseen` | §75 的兩格，各自用自己的列做 400 次置換。 |
| `U_unseen_floor` | **任一**家族的 unseen exact ≥ **0.125** **且** p < 0.005。 |

機制檢查**不用任何擬合參數**，只數「邊界上還有幾個槽不是空的」（地板 `1e-3 × 該段最強槽`，同 §72）。
若 treatment 的 store 沒有真的出現 8 個槽，這一節讀到的就不是「解析度」的效應。

### 76.6 對比與描述量

* **主對比**：`LRO exact`（treatment − control）。只有當**所有**家族的 in-sample 差都 ≤ `FIT_COMPARABILITY`
  時，這個對比才 `readable`；否則擬合差是共變數，分支改用 treatment **自己的**閘門，不能把「treatment
  擬合得更好」讀成「寫入更好」。
* **描述量**（**報告，不設閘門**）：三個家族 × 三個格（in-sample／held-out／LRO）的全部差值。登記的預期是
  `linear_values` 的位移**遠小於** `linear_state`（前者是同一批 128 個數字在 1024 維裡換排列）。因為兩臂
  分開訓練，這個描述量讀的是擬合；它不當證據用。

### 76.7 分支表（跑之前寫定；固定優先序 N0 > Q1 > Q3+U > Q2 > 對比）

| 優先 | id | 觸發條件 | `next` |
| --- | --- | --- | --- |
| 1 | `N0-instrument` | 任一臂 N0 或機制不過 | 先修儀器，兩個臂都不讀 |
| 2 | `W3-treatment-no-fit` | treatment 的 `Q1` 全部不過 | **停**：擬合失敗禁止「更多 epoch／寬度／資料」（§75.7）；主體仍是寫入規則 |
| 3 | `W1-the-write-resolution-was-the-limit` | 某家族 `Q2`∧`Q3` **且** `U` 過 | 仍不宣稱 binding；下一步是第三個種子＋內容定址寫入，兩者都不能從本節推論 |
| 4 | `W6-treatment-no-transfer` | treatment 的 `Q2` 全部不過 | 花掉空槽反而破壞轉移；主體是寫入規則，只再試一個寫入規則 |
| 5 | `W4-partial-gain-from-resolution` | readable ∧ 有 `gain_arms` | 解析度有效但不足；問「塊還缺什麼」（每個名字一次寫入），**不**加預算 |
| 6 | `W5-resolution-hurt` | readable ∧ 有 `loss_arms` | 解析度不是損失所在；下一節讀「整個回合的值裝了什麼是塊沒有的」 |
| 7 | `W2-the-write-was-not-the-limit` | 以上皆非 | 限制在 store 內容的下游；下一步是內容定址（per-name）寫入，不是更多預算 |

### 76.8 預測與反證（跑之前寫定）

* **預測（會被打臉的那種）**：因為 §73／§75 的 store 在邊界是**整回合 rank-1**，而讀出本來就能把
  兩個名字併起來，我預期 **`W2` 或 `W4`**：4 槽要嘛不動 LRO（< 0.05），要嘛動一點但到不了 1.5 的地板。
  **若 `W1`（同時過地板與 unseen 地板）**，則「一次寫入能裝多少」是損失的一部分——這會直接推翻我的預期。
* **反證 1（機制）**：若 treatment 的 `active_slots` 中位數 < 8，則治療沒發生（`N0-instrument`），
  任何讀數都不成立。
* **反證 2（擬合）**：若兩臂 in-sample 差 > 0.15，則對比 `readable=False`，不能用對比裁決，
  只能讀 treatment 自己的 `Q1/Q2/Q3`。
* **反證 3（內容）**：若 4 塊加起來**不等於**單槽值，則這不是「同內容、不同散佈」，而是換了內容；
  單元測試會直接失敗（已釘住）。
* **反證 4（方向）**：若 treatment 明顯**更差**（`W5`），則「整回合的值」是比較好的可定址單位，
  下一節不能假設「切細一定更好」。

### 76.9 停損（登記；與 §75.7 同一條）

1. `W3`（treatment 連自己的訓練名冊都擬合不到 null 之上）→ **不得**用更多 epoch、更寬或更多資料補救；
   主體回到寫入規則。這一條是**約束**，不是建議。
2. 對比不可比（`readable=False`）→ **不得**把擬合差讀成寫入效應；分支只能用 treatment 自己的閘門。
3. **不得**在看到結果後改 `CONTRAST_MARGIN`、`UNSEEN_FLOOR`、`FIT_COMPARABILITY`、α、抽樣數、家族、
   語料種子、臂或分支表。任何改動必須以 amendment 另記，並照實保留被作廢的數字。
4. **不得**在 held-out 上調參；`20261127` 只用於這一節。
5. 若機制不過，**不得**改門檻讓它過；先修儀器。

### 76.10 契約測試

`tests/test_pantry_write76.py`（**不載入任何已訓練載體**，37 條）：

* 核心：`write_slots` 不改參數數、`config()` 記錄、需要 `address="turn"`、`slots`/`slot_dim`/`value_dim`
  必須整除、寬度 0 被拒、嚴格載入拒絕寬度不符的 checkpoint、回合索引選對塊、塊內/塊外、四塊相加等於
  單槽值、`write_slots=1` 與 §73 逐位相同、`write_weights` 在 `>1` 時拒絕（單槽契約）、`force` 仍是
  已記錄的死路。
* 探針：登記常數、§74 的 `Q1/Q2/Q3` 算術、機制閘門（control ≤ 3、treatment ≥ 8）、對比邊界與
  `fit_comparability`、描述量涵蓋每一格、七個分支的固定優先序、`--check` 對「分支過期／p 值不跟隨／
  閘門不可重算／不是 §76／抽樣不足／`write_slots` 與登記不符」的拒絕。

### 76.11 指令（登記）

訓練（兩臂**只差 `--write-slots`**；其餘逐項相同，含種子）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address turn \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261127 --device cpu \
    --write-slots 1 --out data/pantry_stage/write76/control
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address turn \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261127 --device cpu \
    --write-slots 4 --out data/pantry_stage/write76/slots4
```

量測（一次；兩臂分開載入，載體不訓練、不寫回）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_write76.py \
    --control $(ls -t data/pantry_stage/write76/control/*.json | head -1) \
    --treatment $(ls -t data/pantry_stage/write76/slots4/*.json | head -1) \
    --device cpu --out data/pantry_stage/write76/k2.json
./.venv/bin/python scripts/probe_pantry_write76.py --check data/pantry_stage/write76/k2.json
```

**這一節不是能力分數**；核心分不變 **0.00/10**。它只回答「一次寫入能裝多少，是不是組合的損失所在」。

### 76.12 執行條件的修訂（**跑之前**寫定；沒有動任何常數、閘門或分支）

首次啟動（16:30）後，主機的使用者要求算力不得佔滿：**CPU ≤ 50%、RAM ≤ 60%、swap／VRAM ≤ 60%**，
且在整個階段都必須成立。原本的訓練指令讓 torch 用滿 12 個邏輯 CPU（約 8 秒／epoch），
這違反上述上限。因此**在產生任何 §76 讀數之前**修改執行條件，其餘逐項不變：

* **裝置仍是 `cpu`**（登記值），語料種子仍是 `20261127`，`--write-slots` 仍是唯一的自變數。
* 兩臂改在**同一個 transient user service** 下重訓，cgroup 硬上限：
  `CPUQuota=500%`（12 個邏輯 CPU 中的 5 個＝**41.7%**，留給桌面）、
  `MemoryMax=9216M`（15.40 GiB 的 **58.4%**）、`MemorySwapMax=0`（swap **0%**）。
  另設 `OMP_NUM_THREADS=5` 等，避免執行緒數與配額不一致。
* **對照臂一併重訓**（原 16:30–16:58 的 control 載體**作廢、不計分**）。理由：若只重訓治療臂，
  兩臂的浮點縮約順序（執行緒數）就不同，`FIT_COMPARABILITY` 會把執行緒差讀成寫入差；
  兩臂必須只差 `--write-slots`。作廢的載體留在 `data/pantry_stage/write76/control/` 供查，
  **沒有**任何讀數由它產生。
* 首次啟動在 epoch 196/200 因工作階段重啟而被終止，**沒有寫出報告**；`slots4/` 為空。
  該次不算一次跑，也不採用任何中間數字。
* **GPU 不使用**（0% ≤ 50%）：Intel Arc + torch 沒有可用的**逐行程利用率上限**；
  唯一能「一直保證 ≤ 50%」的做法就是讓它閒置。若日後要用 GPU，必須另立 amendment 並改兩臂裝置。
* 若 cgroup 的 `MemoryMax` 觸發 OOM，該次記為**失敗的跑**，不是結果；不得為此放寬上限。

命令（`systemd-run` 的資源上限即上表；輸出在 `data/pantry_stage/write76/capped.log`）：

```bash
systemd-run --user --unit=pantry76-capped --collect \
    -p CPUQuota=500% -p MemoryMax=9216M -p MemorySwapMax=0 \
    /home/cxuo/文件/GitHub/Unified-AI-Project/data/pantry_stage/write76/run_capped.sh
```

**這一節不是能力分數**；核心分不變 **0.00/10**。

### 76.13 執行（兩臂＋探針跑完；三份 `--check` 都 OK，沒有 amendment）

`data/pantry_stage/write76/capped.log`；兩個載體在 `capped/` 下，作廢的 16:30 對照留在 `control/` 不計分。

| 階段 | 起 | 迄 | 秒 | 產物 |
| --- | --- | --- | --- | --- |
| control（`--write-slots 1`） | 17:33:03 | 18:02:42 | 1,776.0 | `capped/control/pantry_deduction_20261115-173303.json`（`--check OK`） |
| treatment（`--write-slots 4`） | 18:02:42 | 18:32:21 | 1,776.5 | `capped/slots4/pantry_deduction_20261115-180242.json`（`--check OK`） |
| 探針（兩臂分開載入） | 18:32:21 | 18:54:05 | 675.98＋626.21 | `data/pantry_stage/write76/k2.json`（`--check OK`） |

兩臂**秒數差 0.5 秒**（1,776.0 對 1,776.5），步數同為 10,000，參數同為 168,150——4 槽沒有讓治療臂變貴，
所以「等預算」在實際執行上也成立，不只是登記上的宣稱。`instrument_ok` 兩臂都是 `true`：
`carrier_unchanged`、`checkpoint_unchanged` 逐位相同（權重 sha256 `f177be5f…`／`482a4a68…` 前後不變），
語料 digest 都記錄了（train `416a8a68…`／heldout `69c730e1…`），`reproduction_applicable=false`（§76.5 已寫定）。

**作廢的跑照實記**：(1) 16:30 的 control（12 執行緒，作廢）與 (2) epoch 196/200 被工作階段重啟終止、
沒有寫出報告的首次啟動。兩者都**沒有**產生本節任何讀數；`capped/` 下的兩臂是唯一被計分的載體。

### 76.14 機制檢查：寫入寬度真的變了（2.0 → 8.0）

| 臂 | `SLOTS_PER_TURN` | 邊界 `active_slots` | 200 段的計數 | 閘門 |
| --- | --- | --- | --- | --- |
| control | 1 | 中位數 **2.0**（min 2、max 2） | `{2: 200}` | **PASS**（≤ 3） |
| treatment | 4 | 中位數 **8.0**（min 8、max 8） | `{8: 200}` | **PASS**（≥ 8） |

兩臂都**剛剛好**落在登記的邊界上：控制臂是「2 個回合 × 1 槽」＝2，治療臂是「2 個回合 × 4 槽」＝8。
這正是 `MECHANISM_MAX` 寫的算術（2 個回合），也意味著**兩臂都沒有第三個回合的槽**——治療臂剛好觸到 8 的
下界，沒有任何一個段超過它。所以這一節的 A/B 量到的**只是「一次寫入的寬度」**，沒有混進「多裝了一個回合」。

`rank1_residual` 中位數 0.3508（control）→ 0.7721（treatment）：治療臂的每回合值**離 rank-1 更遠**，
也就是 4 塊**不是**原值換個排列（若只是重排，殘差會與控制臂同級）。`rank1_fraction` 兩臂都是 0.0。
這是描述量，不是閘門；它只確認「切開」真的發生了。

### 76.15 讀數（`k2.json`）

**主對比：leave-roster-out exact（400 段）**

| 家族 | control | treatment | Δ | in-sample 差 | 可比 |
| --- | --- | --- | --- | --- | --- |
| `linear_state` | **0.1175**（47/400） | **0.0925**（37/400） | **−0.0250** | 0.0275 | ✔ |
| `linear_values` | **0.0950**（38/400） | **0.0925**（37/400） | **−0.0025** | 0.1075 | ✔ |
| `nonlinear_quad` | **0.0575**（23/400） | **0.0375**（15/400） | **−0.0200** | 0.0075 | ✔ |

`CONTRAST_MARGIN` 是 0.05，三個 |Δ| 都不到它的一半 → `gain_arms=[]`、`loss_arms=[]`。
`FIT_COMPARABILITY` 是 0.15，三個 in-sample 差都 ≤ 0.1075 → `readable=true`，所以這個「都沒有動」
**可以用對比來說**，不必退到「只讀治療臂自己的閘門」。

**另外兩格（描述量，不裁決）**

| 家族 | in-sample c→t | held-out c→t | LRO overlap c→t |
| --- | --- | --- | --- |
| `linear_state` | 0.7050 → 0.6775 | 0.3400 → 0.3850 | 1.0750 → 1.0525 |
| `linear_values` | 0.2950 → 0.4025 | 0.2250 → 0.1950 | 0.9550 → 0.9850 |
| `nonlinear_quad` | 0.9200 → 0.9275 | 0.3600 → 0.3850 | 0.9600 → 0.9400 |

**閘門（兩臂各自）**

| 閘門 | control | treatment |
| --- | --- | --- |
| `N0_instrument` | PASS | PASS |
| `W_mechanism` | PASS（2.0 ≤ 3） | PASS（8.0 ≥ 8） |
| `Q1_relative_fit` | PASS 三家族（p=0.002494） | PASS 三家族（p=0.002494） |
| `Q2_transfer` | PASS 三家族（p=0.002494） | PASS 三家族（p=0.002494） |
| `Q3_composed_from_names` | **FAIL**（overlap 1.075／0.955／0.960 < 1.5；p 都 0.002494） | **FAIL**（1.0525／0.985／0.940；p 0.002494／0.002494／**0.017456**） |
| `S1_seen` | PASS 三家族 | PASS 三家族 |
| `S2_unseen` | FAIL（最好 2/24，p=0.107232） | FAIL（最好 2/24，p=0.054863） |
| `U_unseen_floor` | FAIL（最好 0.0833 < 0.125） | FAIL（最好 0.0833 < 0.125） |

### 76.16 分支：`W2-the-write-was-not-the-limit`

固定優先序跑完：N0 兩臂都過 → `W3` 不觸發（`Q1` 兩臂都過）→ `W1` 不觸發（沒有家族同時過 `Q3` 與 `U`）
→ `W6` 不觸發（`Q2` 兩臂都過）→ `W4`／`W5` 不觸發（`readable` 但兩個清單都空）→ **`W2`**。

> 把一次寫入切成 4 塊，在 leave-roster-out 上沒有比控制臂更接近、也沒有更遠（|Δ| ≤ 0.025 < 0.05），
> 所以**「一次寫入能裝多少」不是組合的限制所在**；限制在 store 內容的下游。下一步是**內容定址
> （per-name）寫入**，不是更多 epoch、寬度或資料。

這與 §74／§75 的形狀一致，但**不是**同一句話的重複：§74 量的是「store 會不會把沒一起當過標籤的一對取回」，
這一節量的是「把同一個回合的值散到 4 個槽會不會改變它」。後者的答案是**不會**——4 槽與 1 槽在 LRO 上
在統計上分不開（三個家族都低於 20 列），而兩臂的 `Q3` 都卡在同一個地方（overlap < 1.5）。
所以「解析度」這條變數被**排除**了，不是「還沒試夠」。

### 76.17 預測與描述量（照實記）

* **預測**：登記時寫「預期 `W2` 或 `W4`」。結果是 `W2`，**預測沒有被否證**。但這一條的資訊量很低——
  七個分支裡我寫了兩個，而且 `W4` 需要 `readable` 加至少一個 `gain_arm`，本來就比 `W2` 窄；
  照實說：這不是一次有效的預測，只是一次沒有落空的猜測。
* **描述量違反登記的預期**：§76.6 寫「`linear_values` 的位移**遠小於** `linear_state`」。實測相反——
  in-sample 位移 `linear_values` **+0.1075** 而 `linear_state` **−0.0275**；held-out 是 −0.030 對 +0.045，
  LRO 是 −0.0025 對 −0.0250。**一個方向一致、兩個方向相反**，所以登記的那句話**沒有成立**。
  它不影響分支（描述量本來就不裁決），但必須寫下來：我對「同一批數字換排列，位移應該更小」的直覺，
  在 in-sample 這一格是錯的（治療臂的 `linear_values` 反而**擬合得更好**，0.2950 → 0.4025）。
* **不要事後解釋它**：這個 in-sample 差（+0.1075）仍在 `FIT_COMPARABILITY` 內，所以它不是「治療臂贏了」；
  它只說明兩臂的擬合本來就會漂，而 `linear_values` 漂得比 `linear_state` 多。任何更強的解讀都要另一節。

### 76.18 這一節不是能力分數；且 §76.12 的 GPU 句已被同日的工具取代

核心分不變 **0.00/10**；這一節從頭到尾是**診斷**。它排除了一條假設（寫入解析度），沒有產生任何能力。

§76.12 寫過「Intel Arc + torch 沒有可用的逐行程利用率上限，所以唯一能保證 ≤ 50% 的做法是讓它閒置」。
那句話在**同一天**被 `scripts/gpu_limit.py` 取代：上限可以**算**出來，不必用閒置來保證。實測（Arc B570，
`--target 0.5`）自由運轉的 duty 是 0.8735（25,411 次 matmul），加上上限後 duty 0.4773、13,609 次；
`--target 0.25` 是 0.2428、7,057 次。**限制是有效的**，而且誤差在保守側（實際吞吐 0.5356／0.2777 對
預測 0.5464／0.2779）。細節與「為什麼不能做成回饋迴路」在 `docs/06-project-management/GPU_LIMIT.md`。

但 **§76 的裝置仍是 `cpu`**（登記值），這一節的讀數也全部在 `cpu` 上；上面那段是「同一天另一件事」的
更正，不是本節的條件變更。若之後要用 GPU 重跑，必須另立 amendment 並同時改兩臂裝置。

### 76.19 這一節增加了什麼、沒增加什麼

**增加**：一條被**排除**的變數。現在知道 §74–§75 的弱訊號不是「一次寫入裝不下」造成的——
把同一個回合的值切到 4 個槽，LRO exact 在三個家族上都沒動（−0.0250／−0.0025／−0.0200，邊界 0.05），
而機制檢查確認治療真的發生（2.0 → 8.0 個槽，`rank1_residual` 0.3508 → 0.7721）。
**沒增加**：任何能力、任何過線的家族、任何 `U` 的訊號（unseen 最好 2/24，兩臂相同）。
下一節的登記方向因此是**內容定址寫入**（每個名字一次寫入），而不是更多預算；這一節也再次證明
「加大預算」不會是答案（兩臂同預算、同步數、同參數數）。

## §77 每個清單項一次寫入（內容定址；等預算 A/B）

### 77.1 這一節問什麼

§76.19 指名「內容定址寫入（每個名字一次寫入）」。這一節把它做成**只有一個治療**的 A/B：

> 在**參數、語料、初始化、預算完全相同**的條件下，把「一個回合在回合結尾寫**一次**（來源是回合最後
> 一個 token 的 `h`）」換成「回合裡的每個清單項各自寫**一次**（來源是該項最後一個字元的 `h`），
> 每項一個槽」，能否提高 leave-roster-out 的組合讀數？

它**不**加 epoch、寬度或資料；它**不**換讀出家族；它**不**改門檻。

### 77.2 登記前實測到的兩件事（決定了治療是什麼）

兩件都在**登記之前**量到，且都足以改變治療的寫法：

1. **字面的「把內容 hash 到槽」在這個語料會壞掉。** 把每個清單項的 bytes 用 FNV-1a 對 16 個槽取模，
   訓練集 400 段裡有 **209** 段、留出 200 段裡有 **101** 段至少兩個項撞同一個槽（分別丟掉
   **245／121** 個槽）——撞到就是後寫的覆蓋前面的，等於半數 session 的治療被無關的項吃掉。而且 store
   的**讀**本來就是內容定址（`softmax(exp(scale)·W_q h·kᵀ)`），槽號只是**避免覆寫**的裝置。因此治療
   保留「每個名字一次寫入」的**內容**部分，槽號用**每 session 的項序號**（本語料 **5 項/session**、
   16 槽不會碰撞）。這個偏離字面「hash 定址」的決定寫在這裡、**跑之前**，不是看到結果才改。

2. **治療在已訓練的 §76 控制載體上真的改變 store，不是 `force` 那種死路。** 量測用
   `data/pantry_stage/write76/capped/control/pantry_deduction_20261115-173303.json`（`address=turn`、
   `write_slots=1`、168,150 參數、`weights_hash` `f177be5f…`），200 段留出（digest `71eab688…`），
   只讀不訓練、不寫 `data/`：
   - roster 邊界的 `active_slots` **2.00 → 3.00**（200/200 段都剛好是 2／3），`rank1_residual`
     平均 **0.3278 → 0.4552**。
   - 兩個 roster 項的 value 向量 cosine 平均 **0.2251**（min −0.6959、max 0.9436）——不是同一個東西。
   - 控制臂的 roster 槽是混合：與兩個項的 cosine 平均 **0.5682**（max 0.9850）。
   - 問題時讀出的 cosine 平均 **0.4931**（min −0.6731）——同一個 `h` 從兩個 store 讀到不同的內容。
   - 寫入門：roster 第一項平均 **0.6094**（min 0.1185）、第二項平均 **0.6932**（min 0.1819），
     沒有任何一項 < 0.1，所以每一項的寫入真的落地。

**登記前另外發現一個 §76 的儀器缺陷（這一節修在探針上，不改 §76 的腳本）**：
`scripts/probe_pantry_write76.py` 的 `run_arm` 呼叫 `load_corpus(...)` 時**沒有傳 `seed`**，
於是它讀的是預設種子 **20261113**（`PANTRY_SEED`）的語料，而兩個載體是用 `--pantry-seed 20261127`
訓練的。實測兩份語料的 digest 不同（`416a8a68…`/`69c730e1…` 對 `b12cb2fb…`/`71eab688…`），
所以 §76 的讀數是「在**同一個產生器、不同種子**的語料上」量到的，`N0` 只檢查了 digest *有記錄*、沒有檢查
*相符*。§76 的腳本不得覆寫（它已在版控裡），因此這一節的探針**逐字讀回報告記錄的種子**並把
`corpus_digests_match` 放進 `N0`；§76 的結論（`W2`：4 槽與 1 槽在 LRO 上分不開）仍照原文引用，
但任何跨節的數字比較都必須先記得這個種子差。

### 77.3 治療：每個清單項一次寫入

| 臂 | 寫入規則 | 參數 | 語料 |
| --- | --- | --- | --- |
| **control** | `address="turn"`（§73 的寫入）：回合 `k` 在回合最後一個 token 的 `h` 上寫 `key_proj(h)`／`value_proj(h)` 進槽 `k`。 | 168,150 | 種子 20261127 |
| **treatment** | `address="item"`：把回合的 bytes 以 U+3001（`、`）切成區塊（分隔符留在前一塊的尾端；最後一塊結束在回合最後一個非換行字元），**每塊各寫一次**，來源是該塊最後一個字元的 `h`，槽號是**每 session 的項序號** `counter++ % 16`。 | 168,150 | 種子 20261127 |

不變量（由單元測試釘住，不由跨臂讀數釘住）：

* **token 流與 `h` 軌跡完全不變**。切塊只是**寫入計畫**（哪些位置、哪些槽），不是另一個 forward：
  `_run_turn` 仍一次餵完整回合，`al_step` 仍只在回合之間。
* **參數完全不變**。`key_proj`、`value_proj`、`write_gate` 都是同一組映射，只有「用哪個 `h`、寫進哪個槽」
  不同；`state_dict` 的鍵與形狀逐項相同，參數量 168,150。
* **寫入強度不變**：每一塊仍是 `sigmoid(write_gate(h_chunk))`，沒有 `force`、沒有新的門。
* 單一項的回合（本語料 4 個回合裡有 3 個）只有一個區塊，寫入位置是該回合最後一個非換行字元；這與
  control 的「回合最後一個 token（含換行）」只差一個 token，屬於同一條規則，不是第二個治療。

照實記一個**共變數**：治療每段寫 **5** 次、控制寫 **4** 次。§76 已經量過「一次寫入的寬度」不是原因
（4 槽與 1 槽在 LRO 上分不開），所以多出來的那一次寫入**不是**本節的證據；它登記在這裡，避免把
「多寫一次」讀成「內容定址有效」。

### 77.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `NULL_DRAWS` | **400** | 同 §74／§75／§76；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | 20261125 | 同 §74；擬合仍用 `PROBE_SEED`。 |
| `ALPHA` | **0.005** | 同 §74。 |
| `COMPOSED_OVERLAP_FRACTION` | **0.75** | 同 §74；k=2 的門檻是 overlap **1.5**。 |
| `CONTRAST_MARGIN` | **0.05** | 400 列上的 20 列；小於此的差不算「有效應」。 |
| `FIT_COMPARABILITY` | **0.15** | 兩臂的 in-sample 讀數差超過此值時，LRO 的差**不可比**。 |
| `UNSEEN_FLOOR` | **0.125** | 24 列上的 **3/24**；同 §75／§76。 |
| `ITEM_SEPARATOR` | **U+3001（`、`）** | 本語料清單項的分隔符；治療的切塊規則本身。 |
| `EXPECTED_ITEMS_PER_SESSION` | **5** | 登記前量到：4 個回合、其中 roster 回合 2 塊，其餘各 1 塊。 |
| `MECHANISM_MAX` | control **3**、treatment **3** | 邊界前有 2 個回合；control 寫 2 次、treatment 寫 3 次（turn 0＋兩個項）。 |
| `MECHANISM_COVERAGE` | **0.99** | 機制檢查要求 99% 的留出段符合，不是中位數。 |
| `MECHANISM_COSINE` | **0.999** | 「這一項真的寫進那個槽」的判準（與期望 `value_proj(h_chunk)` 的 cosine）。 |
| 家族 | `linear_state`、`linear_values`、`nonlinear_quad` | §74 的三個；**不**加第四個。 |
| 語料種子 | **20261127** | 與 §76 相同：這一節問的是同一個語料下的另一個寫入變數，不新增種子以免把語料差讀成寫入差。 |

### 77.5 閘門與機制檢查（跑之前寫定）

| 閘門 | 條件 |
| --- | --- |
| `N0_instrument` | `carrier_unchanged` ∧ `checkpoint_unchanged` ∧ `mode_matches`（報告記錄的 `address`／`write_strength`／`write_slots` 就是該臂登記的那組）∧ 語料 train/heldout digest 都有記錄**且與探針重算的相符**（§77.2 的種子缺陷）。 |
| `M_slots` | **control**：留出名冊邊界 `active_slots` 中位數 **≤ 3**。**treatment**：中位數 **≥ 3**，且 **≥ 99%** 的留出段剛好是 **3**。 |
| `M_landed` | **≥ 99%** 的留出段：**treatment** 的兩個 roster 項各在**不同**且**非空**的槽，槽內容與 `sigmoid(write_gate(h_item))·value_proj(h_item)` 的 cosine **≥ 0.999**；**control** 的同一個判準套在它的一次性回合尾寫入上（roster 回合的槽內容 vs `sigmoid(write_gate(h_turn_last))·value_proj(h_turn_last)`）。只讀重算，不用擬合參數。 |
| `Q1_relative_fit` | 每家族 in-sample p < 0.005（§74 的算術）。 |
| `Q2_transfer` | 每家族 held-out p < 0.005 **且** exact > chance。 |
| `Q3_composed_from_names` | 每家族 LRO overlap ≥ **1.5** **且** p < 0.005。 |
| `S1_seen`／`S2_unseen` | §75 的兩格，各自用自己的列做 400 次置換。 |
| `U_unseen_floor` | **任一**家族 unseen exact ≥ **0.125** **且** p < 0.005。 |

**復現條款**：控制臂是**重訓**的（不是重用 §76 的載體），理由見 §77.12。若重訓出的控制臂在三個家族的
LRO 格上**逐位**重現 §76 控制臂的 **0.1175／0.0950／0.0575**，記為 `reproduction_equal=true`；若沒有，
照實記下差多少，且**不得**用 §76 的數字做跨節比較。`reproduction` **不是**閘門（兩臂都在本節重訓，
A/B 不依賴它）。

### 77.6 對比與描述量

* **主對比**：`LRO exact`（treatment − control）。只有當**所有**家族的 in-sample 差都 ≤ `FIT_COMPARABILITY`
  時才 `readable`；否則擬合差是共變數，分支改用 treatment **自己的**閘門。
* **描述量**（**報告，不設閘門**）：三個家族 × 三個格的全部差值，加上機制量（`active_slots`、
  `rank1_residual`、兩個 roster 項的 cosine、控制槽與兩項的 cosine、問題時讀出的 cosine）。
* **登記的預期**：`linear_values` 的位移應該**大於** `linear_state`（這一節動的就是 store 的內容；§76.6
  的相反預期在 §76.17 已被否證）。這條寫下來讓它可以被打臉；它不裁決任何分支。

### 77.7 分支表（跑之前寫定；固定優先序 N0 > Q1 > Q3+U > Q2 > 對比）

| 優先 | id | 觸發條件 | `next` |
| --- | --- | --- | --- |
| 1 | `N0-instrument` | 任一臂 N0、`M_slots` 或 `M_landed` 不過 | 先修儀器，兩個臂都不讀 |
| 2 | `P3-treatment-no-fit` | treatment 的 `Q1` 全部不過 | **停**：擬合失敗禁止「更多 epoch／寬度／資料」（§75.7）；主體仍是寫入規則 |
| 3 | `P1-item-content-was-the-limit` | 某家族 `Q2`∧`Q3` **且** `U` 過 | 仍不宣稱 binding；下一步是第三個種子＋名字索引檢索，兩者都不能從本節推論 |
| 4 | `P6-treatment-no-transfer` | treatment 的 `Q2` 全部不過 | 逐項寫入破壞轉移；主體是寫入規則，只再試一個內容規則 |
| 5 | `P4-partial-gain-from-item-content` | readable ∧ 有 `gain_arms` | 內容有效但不足；問「一項還缺什麼」（把值→名字配對寫成**同一個** entry），**不**加預算 |
| 6 | `P5-item-content-hurt` | readable ∧ 有 `loss_arms` | 回合尾的 `h` 是比較好的來源；下一節讀「回合尾裝了什麼是項尾沒有的」 |
| 7 | `P2-both-width-and-content-were-not-the-limit` | 以上皆非 | 限制在 store 內容的下游（讀出頭）；下一節換讀出端，不是更多預算 |

### 77.8 預測與反證（跑之前寫定）

* **預測（會被打臉的那種）**：登記前量到治療把兩個項分開（項間 cosine 0.2251、問題時讀出 cosine
  0.4931），而 §74／§75 的幅度都很小（LRO exact 0.1175／0.0950／0.0575），所以我預期
  **`P4` 或 `P1`**：至少一個家族的 LRO 上升 ≥ 0.05，但 `P1` 還要同時過 overlap 1.5 與 unseen 地板，
  兩者在 §76 都沒有出現過。**若 `P2`**，則「一次寫入的內容」與「一次寫入的寬度」都不是限制——這會
  直接把主體推到讀出端。
* **反證 1（機制）**：`M_slots` 或 `M_landed` 不過，則治療沒發生（`N0-instrument`），任何讀數都不成立。
* **反證 2（擬合）**：兩臂 in-sample 差 > 0.15，則對比 `readable=false`，不能把擬合差讀成寫入效應。
* **反證 3（內容）**：若訓練後的治療載體上兩個項的 value 向量幾乎共線（cos > 0.99），則治療是
  no-op；探針會重算並照實記，不能因為「登記前不是這樣」就跳過。
* **反證 4（方向）**：若 treatment 明顯**更差**（`P5`），則「回合尾的 `h`」是比較好的可定址單位，
  下一節不能假設「切細一定更好」。

### 77.9 停損（登記；與 §75.7、§76.9 同一條）

1. `P3`（treatment 連自己的訓練名冊都擬合不到 null 之上）→ **不得**用更多 epoch、更寬或更多資料補救；
   主體回到寫入規則。這是**約束**，不是建議。
2. 對比不可比（`readable=false`）→ **不得**把擬合差讀成寫入效應；分支只能用 treatment 自己的閘門。
3. **不得**在看到結果後改 `CONTRAST_MARGIN`、`UNSEEN_FLOOR`、`FIT_COMPARABILITY`、α、抽樣數、家族、
   語料種子、臂或分支表。任何改動必須以 amendment 另記，並照實保留被作廢的數字。
4. **不得**在 held-out 上調參；`20261127` 只用於這一節（與 §76 共用語料，但治療是新的）。
5. **不得**放寬 `M_slots` 或 `M_landed` 讓治療「看起來發生了」；機制不過先修儀器。

### 77.10 契約測試

`tests/test_pantry_item77.py`（**不載入任何已訓練載體**）：

* 切塊：`item_end_positions` 在「無分隔符」「一個分隔符」「兩個分隔符」「空回合」上的位置；分隔符留在
  前一塊尾端；最後一塊結束在最後一個非換行字元。
* 核心：`address="item"` 需要 `write_slots=1`、需要寫入計畫、拒絕 `force`；同一批不同樣本各自的槽號
  被尊重；`valid=0` 的樣本不寫；fresh 槽的內容等於 `strength·value_proj(h)`（cosine 1.0）；兩個項寫進
  兩個不同的槽；`state_dict` 的鍵／形狀與 `address="turn"` 逐項相同、參數量相同。
* 回合層：一個 roster 回合切成兩塊後，邊界上的非空槽數是 **3**（`address="turn"` 是 **2**）；單一項的
  回合只寫一次。
* 探針：登記常數、`M_slots`／`M_landed` 的判準、七個分支的固定優先序、`--check` 對「分支過期／
  p 值不跟隨／閘門不可重算／不是 §77／抽樣不足／`address` 與登記不符」的拒絕。

### 77.11 指令（登記）

訓練（兩臂**只差 `--address`**；其餘逐項相同，含種子與 `--write-slots 1`）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address turn \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261127 --device cpu \
    --write-slots 1 --out data/pantry_stage/item77/control
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address item \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261127 --device cpu \
    --write-slots 1 --out data/pantry_stage/item77/item
```

量測（一次；兩臂分開載入，載體不訓練、不寫回）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_item77.py \
    --control $(ls -t data/pantry_stage/item77/control/*.json | head -1) \
    --treatment $(ls -t data/pantry_stage/item77/item/*.json | head -1) \
    --device cpu --out data/pantry_stage/item77/k2.json
./.venv/bin/python scripts/probe_pantry_item77.py --check data/pantry_stage/item77/k2.json
```

### 77.12 執行條件（登記）

* **裝置仍是 `cpu`**（登記值），語料種子仍是 `20261127`，`--address` 是唯一的自變數。
* 兩臂在**同一個 transient user service** 下重訓，cgroup 硬上限：`CPUQuota=500%`
  （12 個邏輯 CPU 中的 5 個＝**41.7%**）、`MemoryMax=9216M`（15.40 GiB 的 **58.4%**）、
  `MemorySwapMax=0`（swap **0%**）；另設 `OMP_NUM_THREADS=5` 等，避免執行緒數與配額不一致。
* **GPU 不使用**（0% ≤ 50%）。
* **控制臂重訓，不重用 §76 的載體**：跨 session 重用會讓「這次的浮點縮約不同」與「治療有效」分不開。
  兩臂在同一個 service 裡跑完，才只差 `--address`。
* 若 cgroup 的 `MemoryMax` 觸發 OOM，該次記為**失敗的跑**，不是結果；不得為此放寬上限。

**這一節不是能力分數**；核心分不變 **0.00/10**。它只回答「一次寫入的**內容**（哪一個 `h`）是不是組合的損失所在」。

### 77.13 執行（兩臂＋探針；`--check` OK）

`data/pantry_stage/item77/capped.log`；兩臂在**同一個** `pantry77-capped` transient user service
（`CPUQuota=500%`、`MemoryMax=9216M`、`MemorySwapMax=0`、`OMP_NUM_THREADS=5`）下依登記的順序跑完，
探針在 `pantry77-probe`（同一組上限）下跑。

| 階段 | 起 | 迄 | 秒 | 產物 |
| --- | --- | --- | --- | --- |
| control（`--address turn`） | 18:34:46 | 19:03:47 | 1,741 | `control/pantry_deduction_20261116-183446.json`（`--check OK`） |
| treatment（`--address item`） | 19:03:57 | 19:32:37 | 1,720 | `item/pantry_deduction_20261116-190357.json`（`--check OK`） |
| 探針（第一次，**作廢**） | 19:32:46 | 19:43:04 | 618 | 無（見 §77.18） |
| 探針（登記的讀數） | 19:58:21 | 20:18:13 | 1,192 | `data/pantry_stage/item77/k2.json`（`--check OK`） |

兩臂：**10,000 步**、**168,150 參數**、`device=cpu`、語料種子 **20261127**、digest 與報告相符
（`N0_instrument` 的 `corpus_digests_match` 兩臂都是 `true`——§76 的探針沒有做這個檢查，見 §77.2）。
訓練 loss 0.0001（control）／0.0078（treatment）：**兩臂的寫入目標不同，所以這個數字不可跨臂比較**，
它只說明兩臂都收斂，不是「哪一臂擬合得比較好」的證據。

### 77.14 機制：兩個檢查都過，治療真的發生了

| 量 | control | treatment |
| --- | --- | --- |
| 寫入模式（報告記錄） | `address=turn`、`write_slots=1` | `address=item`、`write_slots=1` |
| `M_slots`：名冊邊界 `active_slots` | **2.0**（`{2: 200}`） | **3.0**（`{3: 200}`，剛好 3 的比例 **1.0000**） |
| `rank1_residual` 平均（min／max） | 0.327758（0.069606／0.924297） | 0.514831（0.123669／0.875882） |
| `M_landed`：落地段數 | **200/200**，min cosine **1.0** | **200/200**，min cosine **1.0** |
| `weights_hash`／checkpoint sha256 | 前後相同 | 前後相同 |

治療的算術與登記一致：1 個前段項（turn 0）＋名冊回合的 2 項＝**3** 次寫入、3 個非空槽，
200 段**全部**如此；控制是 2 個回合各寫一次＝**2**。落地檢查把每個寫入的槽內容與
`sigmoid(write_gate(h_item))·value_proj(h_item)` 逐段比對，cosine 最小值 **1.0**——每一項真的寫進它自己的槽，
不是「計畫寫了、實際沒寫」。**機制面：`N0`／`M_slots`／`M_landed` 兩臂都是 `PASS`，所以 A/B 真的發生了。**

### 77.15 讀數（三個家族 × 三個分割；每格 400 次置換，p 的最小可達值是 0.002494）

留出 **200** 段切開：**seen 193／unseen 7**（種子 20261127 的留出名冊只有 7 段是訓練段沒見過的組合）。

| 家族 | 臂 | in-sample | held-out | **LRO exact** | LRO overlap | LRO p | seen | unseen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `linear_state` | control | 0.7350 | 0.2650 | **0.2325** | 1.222 | 0.002494 | 0.2746 | 0.0000 |
| `linear_state` | treatment | 0.7725 | 0.2800 | **0.2900** | 1.282 | 0.002494 | 0.2902 | 0.0000 |
| `linear_values` | control | 0.4175 | 0.2100 | **0.1500** | 1.147 | 0.002494 | 0.2176 | 0.0000 |
| `linear_values` | treatment | 0.7200 | 0.5500 | **0.4300** | 1.423 | 0.002494 | 0.5699 | 0.0000 |
| `nonlinear_quad` | control | 0.9525 | 0.3100 | **0.0900** | 1.058 | 0.002494 | 0.3212 | 0.0000 |
| `nonlinear_quad` | treatment | 0.9600 | 0.3100 | **0.1225** | 1.085 | 0.002494 | 0.3212 | 0.0000 |

兩臂的 `Q1`（對自己的 400 次置換）與 `Q2`（留出高於 chance 且 p < 0.005）**三個家族全過**；
**`Q3`（LRO overlap ≥ 1.5）三個家族全不過**（最好的是 treatment 的 `linear_values` **1.423**）；
`S1_seen` 兩臂全過、`S2_unseen` 與 `U_unseen_floor` 兩臂全不過（unseen 都是 **0/7**）。

### 77.16 對比與裁決

| 家族 | control LRO | treatment LRO | Δ | in-sample 差 | 可比？ |
| --- | --- | --- | --- | --- | --- |
| `linear_state` | 0.2325 | 0.2900 | **+0.0575** | 0.0375 | 是 |
| `linear_values` | 0.1500 | 0.4300 | **+0.2800** | **0.3025** | **否** |
| `nonlinear_quad` | 0.0900 | 0.1225 | **+0.0325** | 0.0075 | 是 |

`readable=false`（`linear_values` 的 in-sample 差 **0.3025 > 0.15**）。依 §77.6 的登記規則，
擬合差是**共變數**，不能把 LRO 差讀成寫入效應；`gain_arms` 雖然名義上列出
`linear_state` 與 `linear_values`，**它不構成證據**。分支固定優先序：`N0`／`M_slots`／`M_landed` 過 →
treatment `Q1` 過 → `Q2`∧`Q3`∧`U` 不成立（`Q3` 三個家族全不過、`U` 0/7）→ treatment `Q2` 過 →
`readable=false` 且無 loss → **`P2-both-width-and-content-were-not-the-limit`**。

**裁決**：在參數、語料、初始化、預算完全相同、且機制檢查證明兩臂的寫入真的不同的條件下，
「每個清單項各自寫一次」**沒有**把 leave-roster-out 推過登記的組合地板（overlap 1.5），
也沒有把 unseen 推過 0.125；對比在登記的判準下不可讀。**一次寫入的寬度（§76）與內容（本節）都不是組合的損失所在**，
下一步（依登記的 `next`）是**讀出端**，不是更多 epoch／寬度／資料。

### 77.17 預測與反證：登記的預測**落空**，描述量的預期命中

* **登記的預測**是「`P4` 或 `P1`」（至少一個家族 LRO 上升 ≥ 0.05）。實際是 **`P2`**：兩臂的 LRO 確實都有上升
  （+0.0575／+0.2800／+0.0325），但**不符合登記的證據條件**——`linear_values` 的擬合差不合格，
  `linear_state` 的 +0.0575 只比 margin 0.05 多 0.0075 且 `Q3` 不過（overlap 1.282 < 1.5）、
  `U` 也不過。**照實記為 miss**，不事後把 margin 或可比性門檻改掉去救它。
* **描述量的預期命中**：§77.6 登記「`linear_values` 的位移應該大於 `linear_state`」（與 §76.6 的相反預期對立）。
  LRO 上是 **+0.2800 對 +0.0575**（held-out +0.34 對 +0.015、in-sample +0.3025 對 +0.0375），**成立**。
  §76.17 已經記過 §76.6 那一句不成立，這一節是同一件事的反面、而且是**跑之前**寫下的，所以可以算一次真的命中。
* **反證 3（內容）不成立**：訓練後的 treatment 載體上兩個 roster 項沒有塌成同一個向量——`rank1_residual`
  從控制的 0.3278 升到 **0.5148**，`M_landed` 的 200/200 顯示兩項各在**不同**的槽。所以「切細在訓練後變成
  no-op」這條反證**沒有發生**，`P2` 不是「治療沒做」。
* **§76 控制格沒有複現**（`reproduction.applicable=false`）：本節的 control LRO 是 0.2325／0.1500／0.0900，
  §76 存檔的 control 是 0.1175／0.0950／0.0575。兩者不可比的原因是語料：§76 的探針讀**預設種子
  20261113**、載體訓練在 **20261127**（§77.2 的缺陷），本節的探針讀 20261127、載體也訓練在 20261127。
  登記時已寫明「不是閘門」，照實記為**未複現、且不該期待它複現**。

### 77.18 照實記：作廢的探針、共變數、量測限制

1. **第一次探針（19:32:46–19:43:04）作廢，沒有寫出任何讀數。** 它在兩臂讀數都算完之後、
   寫 `corpus.items_per_session` 時把 session 的**回合字典**直接傳給 `item_end_positions`，
   死於 `ValueError: invalid literal for int() with base 10: 'turn_id'`。修正方式是抽出
   `items_per_session(trainer, probe, session)`（走 `probe.turn_payload` 拿 token 串）並加一條
   回歸測試；**沒有改任何閘門、常數、分割或讀數定義**。第二次執行才是登記的讀數。作廢那一次的
   10 分鐘算力照實記，不記入任何成本比較。
2. **共變數（寫在登記裡）**：治療每段寫 **5** 次、控制 **4** 次。§76 已量過寬度不是原因，
   所以多出來的那一次**不是**本節的證據；但它與「內容」在本節裡仍然綁在一起，無法分開。
3. **`U_unseen_floor` 在這一支語料上接近空轉**：unseen 只有 **7** 列（§75 的種子 20261126 是 24 列），
   登記的 0.125 地板在 7 列上等於「至少 1 題」。兩臂都是 0/7，所以 `U` 不過的**資訊量很低**；
   這一節**不得**用 `U` 不過去宣稱「沒有轉移」。
4. **`Q3` 的差距要照實寫**：treatment 的 `linear_values` LRO **0.4300**（overlap 1.423）是這一系列
   （§74–§77）最大的 LRO 格，離 1.5 只差 **0.077**；但它仍然**不過**，而且它的 in-sample 是 0.7200
   （控制 0.4175）——**擬合得更多、組合得更多，兩者在本節的判準下分不開**。這是 `P2` 的判準，
   不是「治療有效」的許可；若下一個登記要問這一格，必須先設計**等擬合**的對照，而不是放寬 0.15。
5. **核心分不變 0.00/10**：本節所有正確答案都來自「狀態 + 線性／二次讀出」的探針，不是模型自己生成；
   §77 是診斷，不是能力分數。

### 77.19 這一節改變了什麼

* **可裁決的結論**：`P2`——寫入的**寬度**（§76）與**內容**（§77）都不是 leave-roster-out 的瓶頸；
  兩者都在機制上真的改變了 store（槽數 2→8、2→3，rank-1 殘差上升），但組合讀數沒有過地板。
* **被排除的下一步**：更多 epoch／更寬／更多資料（§75.7 的停損，本節沒有觸發 `P3`，所以那條停損的
  適用性不變）、再一次「換寫入規則」（兩個內容變體都已做過）。
* **下一個登記要面對的**：讀出端——而且必須先解決本節暴露的**擬合不可比**問題（treatment 的
  `linear_values` in-sample 高 0.3025）。若下一節仍用同一條 `FIT_COMPARABILITY`，
  「治療把 store 裝得更好」就會一直被讀成共變數；等擬合對照或**固定載體換讀出**（像 §67 那樣）
  是不需要動門檻的做法。

## §78 等擬合讀出：§77 的 store 在同樣的擬合下還讀得比較好嗎？

### 78.1 這一節問什麼

§77 的機械輸出是 `P2-both-width-and-content-were-not-the-limit`，但它同時留下一個**讀不出來的對比**：
treatment 的 `linear_values` in-sample **0.7200** 對 control **0.4175**（差 **0.3025**），遠超
`FIT_COMPARABILITY` 0.15，所以那條 LRO 的 **+0.2800** 不能算在寫入頭上。§77.19 因此指名下一個登記
要**先讓擬合可比**，而且不能用「放寬 0.15」或「加 epoch」達成。

這一節問：

> 把兩個**凍結**的 §77 載體固定住、只讓讀出的**步數預算**變動，在**同一個 in-sample 擬合**上，
> per-item（內容定址）的 store 在 leave-roster-out 的 overlap 上還比 per-turn 的 store 讀得多嗎？

它**不**重訓任何載體（權重與 checkpoint hash 必須前後相同）、**不**換讀出家族（只用 §77 讓對比
不可讀的那一個）、**不**放寬任何門檻（新的匹配容差 0.05 比 0.15 更緊）、**不**換語料、**不**換種子。

### 78.2 登記前已經量到的（照實寫）

**（a）§77 存檔的三個家族**（`data/pantry_stage/item77/k2.json`，同一個 2,000 步預算、同一個讀出）：

| 家族 | control in-sample | treatment in-sample | 擬合差 | control LRO exact／overlap | treatment LRO exact／overlap | Δ exact |
| --- | --- | --- | --- | --- | --- | --- |
| `linear_state` | 0.7350 | 0.7725 | **0.0375** | 0.2325／1.2225 | 0.2900／1.2825 | +0.0575 |
| `linear_values` | 0.4175 | 0.7200 | **0.3025** | 0.1500／1.1475 | 0.4300／1.4225 | **+0.2800** |
| `nonlinear_quad` | 0.9525 | 0.9600 | **0.0075** | 0.0900／1.0575 | 0.1225／1.0850 | +0.0325 |

兩個**本來就可比**的家族，可讀的格都沒有超過 0.05 的效果量（`linear_state` +0.0575 剛好過線但仍
遠低於地板 1.5；`nonlinear_quad` +0.0325 連線都沒過）。所以這一節只擬合**唯一讓對比不可讀的那一個
家族**：`linear_values`（1024 維＝16 槽 × 64 維的 store 值展平）。這不是挑一個對自己有利的家族，
而是挑**唯一還有未讀完的問題**的那一個。

**（b）為什麼是「步數階梯」而不是「加 epoch」**：兩個載體都凍結，唯一能動的是**讀出**的擬合量。
`linear_values` 在 2,000 步只有 0.4175（control），代表這個讀出**還沒擬合完**，所以它還有可移動的
空間；把步數往上拉是「同一個讀出、同一個特徵、同一個分割」的**容量**變動，不是重訓、不是換模型、
不是加資料。階梯是 250–8000 的 2 的冪（§78.4），2,000 是 §77 的登記點（錨）。

**（c）登記前的儀器檢查（唯讀；不寫 `data/`）**：用凍結的 §77 control 載體、同一個語料種子
（20261127）、同一個 2,000 步讀出，重算 §77 存檔的 control 格。這一步是 `N0` 的前提：如果 2,000 步
的錨不能**逐位**重現 §77 的數字，這一節的階梯就不是同一支儀器量出來的，任何差都不能比。實測結果寫在
§78.2d（下面是執行前的協定，不是結果）。

**（d）實測**（本節登記前的唯讀檢查；載體未變、checkpoint 未變、語料 digest 相符；null 只抽 1 次
——這一步只比 observed 格，不重做 §77 的 400 次置換）：

| 臂 | §77 存檔（in-sample／held-out／LRO exact／LRO overlap） | 本節重算 | 逐位相同 |
| --- | --- | --- | --- |
| control | 0.4175／0.2100／0.1500／1.1475 | 0.4175／0.2100／0.1500／1.1475 | **是** |
| treatment | 0.7200／0.5500／0.4300／1.4225 | 0.7200／0.5500／0.4300／1.4225 | **是** |

同一次檢查印出的 6 個階梯（in-sample exact／同一個步數上的置換容量）：

| 步數 | control in-sample | control capacity | treatment in-sample | treatment capacity |
| --- | --- | --- | --- | --- |
| 250 | 0.3050 | 0.0475 | 0.5250 | 0.0700 |
| 500 | 0.3500 | 0.0550 | 0.5500 | 0.0750 |
| 1,000 | 0.3650 | 0.0525 | 0.6150 | 0.0875 |
| **2,000** | **0.4175** | 0.0550 | **0.7200** | 0.1050 |
| 4,000 | 0.4775 | 0.0625 | 0.8000 | 0.0900 |
| 8,000 | 0.5150 | 0.0700 | 0.8750 | 0.1125 |

兩件登記前就知道的事，寫在這裡以免事後看起來像挑選：

1. 兩個階梯都單調、跨度 0.21／0.35（`L` 的門檻是 0.10），6 個階梯的置換容量全部 **< 0.50**
   （全部可用）。所以 `L` 與「可用性濾網」在這一節不會擋掉任何階梯。
2. 依 78.5 的規則（共同擬合最高、平手取 gap 小、再平手取預算小），把上面的**階段 A** 數字代進去，
   匹配**必然**落在 **control@8000（0.5150）對 treatment@250（0.5250）**：control 的最高可用擬合
   就是 0.5150，而 treatment 的**最低**階（250 步）已經 0.5250，差 **0.01** ≤ 0.05。也就是說，
   per-item store 用 **250 步**就達到 per-turn store **8,000 步**的線性可讀度。

第 2 點是**規則作用在階段 A 數字上的結果**，不是階段的讀數：這一節要比較的 held-out 與
leave-roster-out 在那兩個階梯上**還沒有算過**（78.2d 只算了錨的 observed 格），所以對比本身仍是盲的。
它也讓 78.8 的 D1（匹配 level 低於 0.7200）在跑之前就成立——照實記為**低資訊量的預測**。

### 78.3 裝置：凍結載體 + 讀出步數階梯

| 項目 | control | treatment |
| --- | --- | --- |
| 報告 | `data/pantry_stage/item77/control/pantry_deduction_20261116-183446.json` | `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json` |
| checkpoint | `…-183446.pt` | `…-190357.pt` |
| 寫入 | `address="turn"`、`write_slots=1`、`write_strength="learned"` | `address="item"`、`write_slots=1`、`write_strength="learned"` |
| 參數 | 168,150 | 168,150 |
| 語料 | 種子 20261127、minimal binding、k=2、400 訓練／200 留出 | 同左（digest 必須相符） |

兩個載體**不重訓、不微調**：`rebuild_core` 之後記 `weights_hash` 與 checkpoint sha256，跑完再記一次，
兩者都必須相同（`N0`）。

階梯（**同一個** `linear_values` 讀出、同一個 `PROBE_SEED`、同一個 batch／lr／weight decay）：

| 步數 | 角色 |
| --- | --- |
| 250 | 最低階（擬合明顯不足） |
| 500 | |
| 1,000 | |
| **2,000** | **§77 的登記點（錨；必須逐位重現）** |
| 4,000 | |
| 8,000 | 最高階（擬合最多，容量也最大） |

每一個階梯都同時記**兩件事**：在真標籤上的 in-sample exact，以及在**列置換標籤**上的容量
（`capacity_ceiling`、`CAPACITY_SEED`）。兩者共用同一個步數，所以「這個階梯的擬合」與「這個階梯
能背多少任意標籤」是同一支儀器的兩個讀數。

### 78.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `STEPS_LADDER` | **(250, 500, 1000, 2000, 4000, 8000)** | 2 的冪；2,000 是 §77 的登記點。 |
| `ANCHOR_STEPS` | **2000** | §77 的點；`N0` 要求逐位重現。 |
| `FAMILY` | **`linear_values`** | §77 唯一讓對比不可讀的家族（78.2a）。 |
| `FIT_MATCH_TOLERANCE` | **0.05** | 400 列上的 **20 列**；比 §77 的 0.15 **緊三倍**。 |
| `CONTRAST_MARGIN` | **0.05** | 同 §76／§77；小於此的差不叫效果。 |
| `LADDER_SPAN_MIN` | **0.10** | 階梯的 in-sample 至少要掃過 40 列，否則「匹配」是雜訊。 |
| `MONOTONE_TOLERANCE` | **1e-6** | 步數增加時 in-sample 不得下降（容許浮點誤差）。 |
| `CAPACITY_MAX` | **0.50** | §70 的儀器上限；只當**可用性**濾網，不是結果的閘門。 |
| `COMPOSED_OVERLAP_FRACTION` | **0.75** | 同 §74；k=2 的地板是 overlap **1.5**。 |
| `NULL_DRAWS` | **400** | 同 §74–§77；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | 20261125 | 同 §74；擬合仍用 `PROBE_SEED` 20261121。 |
| `ALPHA` | **0.005** | 同 §74–§77。 |
| `PROBE_BATCH`／`PROBE_LR`／`PROBE_WEIGHT_DECAY` | 64／1e-3／1e-4 | §69 起的同一支讀出，不動。 |

### 78.5 兩階段協定（為什麼先擬合、後讀）

匹配的**唯一**輸入是 in-sample 擬合。若先看 held-out 或 LRO 再挑階梯，挑選本身就用了要控制的東西，
「等擬合」會變成「等一個剛好有差的擬合」。所以：

1. **階段 A（只看訓練端）**：對每個臂的 6 個階梯各擬合一次，記 in-sample exact 與置換容量。
   這一步**不計算**任何 held-out 或 leave-roster-out 數字。
2. **匹配**：在兩個臂**都可使用**（`capacity_exact < 0.50`）的階梯裡，找
   `|control_fit − treatment_fit| ≤ 0.05` 的配對；取**共同擬合最高**的那一對（`level` 最高），
   平手時取 gap 較小者，再平手時取總步數較小者（總次序，不含隨機）。
3. **階段 B（才讀結果）**：只在**錨（2,000）**與**匹配到的兩個階梯**上算完整格（in-sample、
   held-out、LRO、seen／unseen），每個格各 400 次置換。

若階段 A 找不到配對，階段 B 仍然只算錨（為了 `N0` 的重現），分叉是 `F1`；**不得**為了湊出配對
而加階梯、放寬 0.05 或改用別的家族。

### 78.6 閘門（跑之前寫定）

* **`N0`（儀器）**：兩個載體的 `weights_hash`／checkpoint sha256 前後相同、`mode_matches`、
  語料 digest 與報告相符、**且**錨（2,000）在兩個臂上都**逐位**重現 §77 的三個 observed 格
  （in-sample／held-out／LRO 的 exact 與 overlap，容差 1e-9）。任一不成立 → `F0`。
* **`L`（階梯有效）**：兩個臂的 in-sample 對步數**單調不降**（容差 1e-6）且**跨度 ≥ 0.10**。
  不成立 → `F0`（階梯沒掃到，匹配沒有意義）。
* **`W1`（找得到配對）**：依 78.5 的規則找到至少一對可用且落在容差內的階梯。
* **`W2`（匹配的格自己站得住）**：兩個匹配格的 in-sample null、held-out null、LRO null 的 p 都
  < 0.005，且 held-out exact 高於 chance（0.0152）。這是「這一格不是空的」的最低要求，不是效果量。
* **對比**：主讀數是 **leave-roster-out 的 overlap 差**（`treatment − control`，與 1.5 地板同一種
  貨幣）；`exact` 差是描述量。`gain`＝overlap 差 ≥ 0.05；`above_floor`＝treatment 的 overlap ≥ 1.5。

### 78.7 分叉（跑之前寫定，機械決定；固定優先序）

| # | 分支 | 條件（依序判斷，第一個成立者為準） | 讀法／下一步 |
| --- | --- | --- | --- |
| 1 | `F0-instrument` | `N0` 不過或 `L` 不過 | 儀器錯（hash／digest／錨／單調），**不讀** `W1` 與任何差；修好重跑。 |
| 2 | `F1-fit-not-matchable` | `N0`、`L` 過但 `W1` 不過 | 0.3025 的擬合差**不是步數能補的**：它是兩組特徵的性質，不是讀出容量；這一支家族在等擬合下**無法比較**。下一步是**由構造固定擬合**（對值矩陣取固定的 rank-1／SVD 投影），不是加步數。 |
| 3 | `F5-ungated-at-matched-fit` | `W1` 過但 `W2` 不過 | 配對存在但至少一臂的格過不了自己的置換 null；**不得**讀差。 |
| 4 | `F2-gain-above-floor-at-matched-fit` | `W2` 過、`gain` 且 `above_floor` | 等擬合下 per-item store 的 overlap 仍高 ≥ 0.05 **且**過 1.5 → §77 的差在等擬合後**還在**。仍**不是**綁定宣稱：要第二個語料種子＋以名字為位址的讀出複現，且不加預算。 |
| 5 | `F3-gain-below-floor-at-matched-fit` | `W2` 過、`gain` 但未過地板 | 等擬合下寫入有幫助、幅度不夠；問「一個項還缺什麼（同一筆裡的 value→name 配對）」，不加預算。 |
| 6 | `F4-fit-explains-the-delta` | `W2` 過、`gain` 不成立 | 等擬合下 per-item store **沒有**讀得更多 → §77 的 +0.2800 是與「治療比較好擬合」共變，不是組合增益。下一步換**讀出端**：以槽為位址的讀出（每個槽對候選名字打分，而不是把展平的 store 池化），不是再改寫入規則、不是加預算。 |

### 78.8 預測與否證（寫在跑之前）

1. **主預測：`F1` 或 `F4`；明確**不是** `F2`。** 理由寫在這裡、不是結果之後：§77 三個家族裡兩個
   本來就可比，而它們的差是 +0.0575（剛過線、遠低於地板）與 +0.0325（沒過線）；唯一大的
   +0.2800 正好是唯一擬合不可比的那一格。若那 0.2800 是寫入的功勞，等擬合後它應該還在；但同一個
   載體上另外兩個家族的讀數都說「沒有超過 0.05 的效果」，所以我預期 `linear_values` 的優勢會隨
   控制臂的擬合被追平而消失（`F4`），或者控制臂**根本追不到**那個擬合（`F1`）。
2. **`F2` 是這一節的否證對象**：若 `F2` 成立，代表寫入內容的增益在等擬合下仍 ≥ 0.05 且過 1.5；
   那會是 §74–§77 以來第一個過地板的格子，必須用第二個語料種子複現才准寫成結論。
3. **描述量預期（可核對、不裁決分支）**：
   * 匹配的 `level` **低於** treatment 在 2,000 步的 0.7200。**登記前就知道會成立**（78.2d 第 2 點
     把它算出來了），所以照實記為低資訊量，不由它宣稱任何東西。
   * 匹配格的 exact 差 **小於** §77 的 +0.2800。這一個**不是**先算出來的：control@8000 與
     treatment@250 的 LRO 都沒有量過。
4. **否證條件**：若 `L` 不過（階梯沒有掃過 0.10 或非單調），這一節**不能**說「擬合不是極限」，
   只能說儀器壞了；若 `N0` 的錨不能逐位重現，整節作廢（不是 amendment，是重跑）。

### 78.9 照實記的限制（哪些讀數不能那樣讀）

* **「等擬合」只等一個數字**。兩組特徵在同樣的 in-sample exact 上可以有不同維度、不同條件數、
  不同有效容量；匹配掉的是「擬合量」，不是「資訊量」。因此 `F4` 的讀法是「在這個讀出、這個擬合
  水平上，差消失了」，不是「寫入沒有改變 store」（§77 已量到 store 真的變了）。
* **`CAPACITY_MAX` 0.50 不是這個家族自己的分佈**（§74.16 已記）：它只當**可用性**濾網——一個
  連任意標籤都能背到 0.5 以上的階梯，拿來比較沒有意義——不是結果的閘門，也不調整。
* **步數不是正則化排程**。多步數同時改變擬合與隱含的參數範數；這一節量的是「讀出容量」，不是
  「訓練預算」。
* **單一語料種子、k=2、單一家族**。§75 已量到幅度不跨語料種子複現，所以任何 `F2`／`F3` 都只是
  **這一支語料**的結果。
* **錨的重現只比三個 observed 格**（4 位小數），不重新檢定 §77 的 null 分佈；它證明的是同一支
  儀器，不是 §77 的結論。
* **`seen`／`unseen` 只在匹配格與錨上算**，而這支種子切成 193/7（§77.18 第 3 點），所以 unseen
  仍然接近空轉，**不得**用 `U` 不過宣稱「沒有轉移」。

### 78.10 指令（登記；一次跑兩個臂）

```bash
data/pantry_stage/fit78/run_probe.sh
```

等價的單行（`run_probe.sh` 只是加上執行緒與 log）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_fit78.py \
    --control data/pantry_stage/item77/control/pantry_deduction_20261116-183446.json \
    --treatment data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --reference data/pantry_stage/item77/k2.json \
    --device cpu --out data/pantry_stage/fit78/k2.json

./.venv/bin/python scripts/probe_pantry_fit78.py --check data/pantry_stage/fit78/k2.json
```

`--check` 從存檔的數字重算：階梯的 exact／capacity 是否等於 correct/n、可用性是否重算、
`effective` 是否重導、**匹配是否由兩個階梯重導**、每個格的 exact／overlap 與 p 值是否自洽、
錨的重現是否重導、四個閘門是否重導、分叉是否為登記的六個之一且與閘門一致。任一不符即 FAIL。

### 78.11 執行條件（跟 §77 同一個上限，不是同一台機器）

* 走 transient user scope：`CPUQuota` 依**執行當下**機器已有的負載選，讓**整台**機器 ≤ 50%；
  `MemoryMax` ≤ 9 GiB（≤ 60%）、`MemorySwapMax=0`。
* `--device cpu`、`OMP_NUM_THREADS` 與其餘 BLAS 執行緒上限對齊 quota；**不使用 GPU**（本節沒有任何
  tensor 需要加速器，且 GPU／VRAM ≤ 60% 的規則是硬規則）。
* 只跑**一個**實例（同一個輸出檔）。輸出只寫 gitignored 的 `data/`。
* 登記（本節＋探針＋測試）**先 commit**，計分執行在其後；執行中的任何改動記為 amendment，
  作廢的跑照實記、不刪。
* 執行期間不跑全套測試（避免兩個重負載同時占滿 CPU）。

### 78.12 這一節不是能力分數

所有讀數都是「凍結載體 + 線性讀出」的診斷：沒有生成、沒有新的正確答案、沒有動到核心。核心分不變
**0.00/10**；`F2` 也不會讓它上升——讀出探針的正確答案不是模型產生的答案（§X #275 的判準）。

### 78.13 執行（一個 capped scope；`--check` OK）

| 項目 | 值 |
| --- | --- |
| 起 | 2026-11-16T20:58:54+08:00 |
| 迄 | 2026-11-16T21:44:10+08:00 |
| 秒 | **2,715.1** |
| scope | `fit78-probe`（transient user scope）：`CPUQuota=200%`、`MemoryMax=4096M`、`MemorySwapMax=0` |
| 執行緒 | `OMP_NUM_THREADS=2`（其餘 BLAS 同步） |
| 裝置 | `--device cpu`（沒有用到 GPU） |
| 報告 | `data/pantry_stage/fit78/k2.json` |
| `--check` | **OK** |
| `instrument_ok` | **true** |

**兩個載體都沒有重訓**：`weights_hash` 與 checkpoint sha256 前後相同（control `sha256:f177be5f…`／
`4949f2cf…`，treatment `sha256:0ca9e593…`／`ba1edf16…`），`mode_matches` 兩臂都是 `true`，
語料 digest 與 §77 報告相符（train `b12cb2fb…`、held-out `71eab688…`）。階梯本身的擬合只花
**10.8 s**（control）／**9.6 s**（treatment）。

2,715 s 幾乎全部在**六個格的置換 null**：`in_sample_reading` 的 400 次置換**每次都重新擬合**
（§74 起的同一支慣例），所以單是 in-sample null 就是 `400 × (250+2,000+8,000)` 步 × 2 臂 ≈ **8.2M 步**
的讀出，加上 leave-roster-out 的 62 折。這是登記的讀數成本，不是階梯的成本；這一點寫在這裡，
是因為它與「讀出只要幾秒」的直覺相反。

### 78.14 匹配（階段 A：只有 in-sample 擬合與容量）

| 步數 | control in-sample | control capacity | treatment in-sample | treatment capacity | 可用 |
| --- | --- | --- | --- | --- | --- |
| 250 | 0.3050 | 0.0475 | **0.5250** | **0.0700** | 兩臂 |
| 500 | 0.3500 | 0.0550 | 0.5500 | 0.0750 | 兩臂 |
| 1,000 | 0.3650 | 0.0525 | 0.6150 | 0.0875 | 兩臂 |
| **2,000**（錨） | **0.4175** | 0.0550 | **0.7200** | 0.1050 | 兩臂 |
| 4,000 | 0.4775 | 0.0625 | 0.8000 | 0.0900 | 兩臂 |
| 8,000 | **0.5150** | **0.0700** | 0.8750 | 0.1125 | 兩臂 |

`L`：兩臂都單調、跨度 **0.2100／0.3500**（地板 0.10）→ PASS。六個階梯的置換容量全部 ≤ **0.1125**
（`CAPACITY_MAX` 0.50）→ 全部可用，所以可用性濾網沒有擋掉任何階梯。

依 78.5 的次序（共同擬合最高 → gap 小 → 總步數小），`W1` 落在 **control@8000（0.5150）對
treatment@250（0.5250）**，gap **0.0100** ≤ 0.05，level **0.5150**——與 78.2d 在登記前由階段 A 算出的
那一對**完全相同**（那一對是規則作用在已量到的 in-sample 數字上的結果，不是看到對手讀數才挑的）。

三件必須照實記的性質：

1. **這一對是兩個階梯的邊緣，不是內部交會。** 兩條擬合範圍只在 **[0.5150, 0.5250]** 重疊：
   control 的**最高**階仍低於 treatment 的**最低**階（差 0.01）。也就是說 per-item store 用
   **250 步**就達到 per-turn store **8,000 步**的線性可讀度；「等擬合」在這支語料上只有這一個窄帶，
   而它同時是 control 讀出容量最大、treatment 讀出容量最小的點。
2. **匹配對的置換容量也剛好相同**（兩邊都是 **0.0700**）。這一項**沒有**列入匹配規則（規則只用
   in-sample 擬合與可用性），所以它是事後可見的描述量；但它讓「兩邊的讀出都能背一樣多的任意標籤」
   變成可直接核對的事實，減少了「一邊比較容量大」這個替代解釋。
3. **擬合差沒有消失，只是被推到極值。** control 的 in-sample 從來沒有達到 treatment 的水準
   （0.5150 < 0.5250），這與 §77 的 0.3025 差一致：treatment 在任何預算下都比較好擬合。這一節能問的
   只有「在兩者最接近的那一點，store 還讀得比較好嗎」，不能問「在所有擬合水平上」。

### 78.15 讀數（匹配對、錨、以及整條階梯的描述量；每格 400 次置換，p 的最小可達值 0.002494）

**（a）匹配對**（`level` 0.5150，gap 0.0100）：

| 臂 | 步數 | in-sample | held-out | **LRO exact**（Wilson 95%） | **LRO overlap** | LRO null 平均／最大 | LRO p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control | 8,000 | 0.5150 | 0.2100（42/200） | **0.1025**（41/400）［0.0765, 0.1361］ | **1.0875** | 0.0227／0.0500 | 0.002494 |
| treatment | 250 | 0.5250 | 0.3400（68/200） | **0.2925**（117/400）［0.2501, 0.3389］ | **1.2650** | 0.0222／0.0425 | 0.002494 |

**（b）錨（2,000 步；`N0` 的逐位重現）**：

| 臂 | in-sample | held-out | LRO exact | LRO overlap | 與 §77 存檔 |
| --- | --- | --- | --- | --- | --- |
| control | 0.4175 | 0.2100 | 0.1500 | 1.1475 | **逐位相同** |
| treatment | 0.7200 | 0.5500 | 0.4300 | 1.4225 | **逐位相同** |

**（c）整條階梯的傳遞格**（control@250 與 treatment@8000 是 78.17 第 4 點說的描述格，沒有閘門讀它們）：

| 臂 | 步數 | in-sample | held-out | LRO exact［Wilson 95%］ | LRO overlap | seen | unseen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control | 250 | 0.3050 | 0.1950 | 0.1000［0.0743, 0.1333］ | 1.0825 | 0.2021 | 0/7 |
| control | 2,000 | 0.4175 | 0.2100 | 0.1500［0.1183, 0.1883］ | 1.1475 | 0.2176 | 0/7 |
| control | 8,000 | 0.5150 | 0.2100 | 0.1025［0.0765, 0.1361］ | 1.0875 | 0.2176 | 0/7 |
| treatment | 250 | 0.5250 | 0.3400 | 0.2925［0.2501, 0.3389］ | 1.2650 | 0.3523 | 0/7 |
| treatment | 2,000 | 0.7200 | 0.5500 | 0.4300［0.3824, 0.4790］ | 1.4225 | 0.5699 | 0/7 |
| treatment | 8,000 | 0.8750 | 0.6300 | 0.4350［0.3873, 0.4840］ | 1.4325 | 0.6477 | **1/7** |

**（d）逐階梯的差**（同一個步數上 treatment − control，描述量）：

| 步數 | Δ LRO exact | Δ LRO overlap |
| --- | --- | --- |
| 250 | **+0.1925** | **+0.1825** |
| 2,000 | **+0.2800** | **+0.2750** |
| 8,000 | **+0.3325** | **+0.3450** |

三個步數上 treatment 都比較高，而且差值隨讀出預算**上升**（不是「只有在某一格贏」）。但六個格裡
**沒有任何一格**的 overlap 達到 1.5；全系列最高是 treatment@8000 的 **1.4325**，仍差 **0.0675**。

### 78.16 閘門與裁決

| 閘門 | 結果 | 依據 |
| --- | --- | --- |
| `N0_instrument` | **PASS** | 兩個載體的 `weights_hash`／checkpoint sha256 前後相同、`mode_matches`、digest 相符，錨的兩臂四個 observed 格**逐位**等於 §77 存檔 |
| `L_ladder_effective` | **PASS** | 兩臂 in-sample 單調不降（容差 1e-6），跨度 0.2100／0.3500 ≥ 0.10 |
| `W1_match_found` | **PASS** | control@8000 對 treatment@250，gap 0.0100 ≤ 0.05，兩者都可用 |
| `W2_matched_cells_gated` | **PASS** | 兩臂的 in-sample、held-out、LRO null p **都是 0.002494**；held-out exact（0.2100／0.3400）都高於 chance 0.0152 |

**對比**（主讀數是同一個貨幣：leave-roster-out overlap）：

| 量 | 值 |
| --- | --- |
| control overlap | 1.0875 |
| treatment overlap | 1.2650 |
| **Δ overlap** | **+0.1775** |
| `CONTRAST_MARGIN` | 0.05 → **gain = true** |
| 地板（k=2，overlap fraction 0.75） | **1.5** → treatment 1.2650 **未達** |
| Δ exact（描述量） | +0.1900 |

依 78.7 的固定優先序：`N0` 過、`L` 過、`W1` 過、`W2` 過 → `gain`（+0.1775 ≥ 0.05）但
`above_floor` 不成立（1.2650 < 1.5）→ **`F3-gain-below-floor-at-matched-fit`**。

**裁決**：在**同一個 in-sample 擬合**（gap 0.0100）與**同一個置換容量**（0.0700／0.0700）上，
per-item（內容定址）的 store 在 leave-roster-out 的 overlap 上比 per-turn 的 store 高 **+0.1775**
（exact 高 **+0.1900**），兩個格都過自己的置換 null。所以 §77 的差**不是**全部由「治療比較好擬合」
解釋：等擬合之後差值**縮小**（§77 的 overlap 差 0.2750 → 0.1775；exact 差 0.2800 → 0.1900）**但沒有消失**。
可是它仍然**沒有過登記的組合地板**（1.2650 < 1.5）——**寫入有幫助、幅度不夠**。

### 78.17 預測與反證：主預測**落空**，描述量的預期命中

1. **登記的主預測是「`F1` 或 `F4`」，而且明確不是 `F2`。實際是 `F3`。**
   * `F1`（擬合不可匹配）**不成立**：`W1` 找到配對，0.3025 的差在這支語料上**可以**被步數壓到 0.01。
   * `F4`（等擬合下差消失）**不成立**：Δ overlap **+0.1775**，遠高於 margin 0.05。
   * 「不是 `F2`」**成立**，但**理由是錯的**：`F2` 要求 `gain` ∧ `above_floor`；它沒有發生是因為
     **地板**（1.2650 < 1.5），不是因為 `gain` 不成立。所以照實記為**主預測 miss**，不把
     「不是 `F2`」算成命中。
   登記時寫下的理由是「另外兩個本來就可比的家族，讀數都說沒有超過 0.05 的效果」；那個理由對
   `linear_state`（+0.0575，只比 margin 多 0.0075、遠低於地板 1.5）與 `nonlinear_quad`
   （+0.0325，連 margin 都沒過）**仍然成立**，但**不能推廣到 `linear_values`**——等擬合之後它反而
   是唯一還有可讀增益的家族。這是這一節最重要的預測錯誤，寫在這裡而不是事後淡化。
2. **描述量 D2 命中**：登記「匹配格的 exact 差小於 §77 的 +0.2800」。實際 **+0.1900 < +0.2800**。
3. **D1（匹配 level 低於 0.7200）是低資訊量**：78.2d 在登記前就用階段 A 的數字把它算出來了，
   所以它**不算**預測命中，也不構成任何證據。
4. **描述格（照實記、不裁決）**：78.10 的 CLI 對兩個臂都算 **{250, 2,000, 8,000} 的聯集**，所以
   control@250 與 treatment@8000 也被算了。沒有任何閘門或分支配到它們；它們只在 78.15（c）與下面
   兩點出現，且標為描述量：
   * **兩臂在匹配對上都不在各自最好的傳遞點**：control 最好的是 @2000（overlap 1.1475，匹配的 @8000
     是 1.0875）；treatment 最好是 @8000（1.4325，匹配的 @250 是 1.2650）。
   * **事後描述量**：treatment 的**最差**格（@250，1.2650）仍然高於 control 的**最好**格（@2000，
     1.1475）與匹配格（@8000，1.0875）。這不是登記的對比（登記的對比是等擬合的那一對），也沒有
     第二個種子複現，所以它**不能**升級成結論；它只說明「per-item store 的優勢不是靠挑到好格子」。
5. **`unseen` 仍然接近空轉**：control 三個步數都是 0/7；treatment 在 250 與 2,000 是 0/7，@8000 是
   **1/7**（0.1429，置換 null 的 p **0.1397**，未達 0.005）。7 列上的 1 題不構成轉移證據，
   這一節**不得**用它宣稱「學到沒見過的組合」。

### 78.18 照實記：這一節對 §77 的 `P2` 說了什麼、以及不能說什麼

1. **§77.19 的 `P2` 措辭必須收窄，但原文不改。** §77.19 寫「寫入的**寬度**與**內容**都不是
   leave-roster-out 的瓶頸」。本節量到的是：內容（per-item 寫入）在**等擬合**下**確實**可讀得更多
   （Δ overlap +0.1775、Δ exact +0.1900，兩格都過 null），只是幅度**不夠**過地板。所以正確的讀法是
   **「內容不是惰性的，但仍不是充分條件」**，不是「內容無關」。依 §74.16 的先例，**不回頭改寫
   §77.19**；差額由這一節承接。
2. **等擬合吃掉的那一部分，照實給數字**：overlap 差 0.2750（錨）→ **0.1775**（等擬合），少了
   **0.0975**；exact 差 0.2800 → **0.1900**，少了 **0.0900**。所以 §77 的 +0.2800 裡大約 **0.10**
   與「治療比較好擬合」共變。但這個 0.0975 **不能**被拆成純「擬合」與純「換了格子」：匹配把兩臂
   移到**不同**的步數（control 8,000、treatment 250），兩個原因在這一節裡綁在一起；能分開的只有
   錨那一格（同步數、差 0.3025 的擬合）與匹配那一對（不同步數、差 0.01 的擬合）。
3. **「等擬合」只等了一個數字**（78.9 已登記）：兩組特徵在同樣的 in-sample exact 上可以有不同維度、
   條件數與有效容量。這一節能說的是「在這個讀出、這個擬合水平上，差還在、但不過地板」，**不能**說
   「寫入沒有改變 store」——§77 已量到 store 真的變了（槽 2→3、rank-1 殘差 0.3278→0.5148）。
4. **匹配對落在兩條階梯的邊緣**（78.14 第 1 點）：control 的最高階對 treatment 的最低階。這是規則的
   結果，不是挑選；但它同時意味著這一對是 control 讀出容量最大、treatment 讀出容量最小的點。
   照實記，不當成「平均而言」的估計。
5. **單一語料種子、k=2、單一家族**：所有讀數只屬於種子 20261127 的 400／200 分割。§75 已量到幅度
   不跨語料種子複現，所以 `F3` 的幅度也**不得**假設會複現；`F2` 的否證條件（第二個種子＋以名字為
   位址的讀出）在這一節**沒有觸發**，因為 `F2` 沒有發生。
6. **核心分不變 0.00/10**：所有正確答案都來自「凍結載體 + 線性讀出」的探針，不是模型自己生成；
   §78 是診斷，不是能力分數。

### 78.19 這一節改變了什麼

* **可裁決的結論**：`F3`——在等擬合（0.0100）與等容量（0.0700）下，per-item 的 store 在
  leave-roster-out 的 overlap 上高 **+0.1775**（exact **+0.1900**），兩格都過自己的置換 null，
  但 **1.2650 < 1.5**：寫入**有幫助、幅度不夠**。
* **被排除的下一步**：再加讀出預算。整條階梯（250–8,000）最好的一格是 treatment@8000 的
  **1.4325**，仍差 0.0675；而 matching 已經證明 control 要花 32× 的步數才追到 treatment 的最低階。
  所以「把讀出擬合得更多」不是缺的那一塊，也不需要再掃更大的步數。
* **仍然有效的停損**：更多 epoch／更寬／更多資料（§75.7）、再一次「換寫入規則」（§76／§77 已各做過
  一次）。
* **下一個登記要問的**（分支 `F3` 登記的 `next`）：「一個項還缺什麼（同一筆裡的 value→name 配對）」，
  **不加預算**。

### 78.20 下一步（登記的 `next`，不是本節的結論）

`F3` 登記的下一步是問「一個項還缺什麼」。本節量到、但**沒有**用對照隔離的東西是：寫入的內容是
`sigmoid(write_gate(h_item))·value_proj(h_item)`——**值**進了槽，但「這個值屬於哪個名字」只以
**讀出端的標籤**身分存在。leave-roster-out 把整個名冊對從訓練標籤裡拿掉，所以配對沒有任何支持；
等擬合下 LRO exact **0.2925**（117/400，chance 0.0152）遠高於 chance，說「名冊對有一部分被讀出來」；
overlap **1.2650 < 1.5** 說「沒有齊」。但這是**推論**，不是這一節量到的東西。

把「寫入時把項自己的名字一起綁進同一筆」當成下一個登記的**假設**是合理的，但這一節**沒有**量到
配對本身（沒有 name-in-entry 的對照、沒有以槽為位址的讀出），所以它是下一個登記要否證的東西，
不是本節的結果。任何這樣的登記仍受同一組停損約束：不加 epoch／寬度／資料，不改 1.5，不在
held-out 上調參。

## §79 一個項的同一筆寫入裡，值與名字有沒有配在一起？

### 79.1 這一節問什麼

§78 的機械輸出是 `F3-gain-below-floor-at-matched-fit`，它登記的 `next` 是「一個項還缺什麼（同一筆
裡的 value→name 配對），不加預算」。§78.20 明說那是**推論**：寫入的內容是
`sigmoid(write_gate(h_item))·value_proj(h_item)`，但「這筆寫入屬於哪個名字」只以**讀出端標籤**的
身分存在，從來沒有在**單一筆**上量過。

這一節問：

> 在**凍結的 §77 治療載體**上，一個 roster 項**自己那一筆** store 寫入裡，是否帶著「這個值屬於哪個
> 名字」——也就是拿**同一筆**的向量去認該項自己的名字，能不能在**同一 session 另一項**的名字之上
> 勝出？

它**不**重訓載體、**不**加預算、**不**掃讀出步數階梯、**不**換讀出家族、**不**改任何門檻、**不**在
held-out 上調參。它**不是** §78 的重新裁決：§78 的讀數是「整個 store 經 2,000 步讀出、pooled 後
解一組名冊」，本節的讀數是「單筆進入、單筆輸出一個二選一」。

### 79.2 登記前已經量到的（照實寫）

**（a）語料與標籤對齊**（唯讀，不改任何檔案）：train **400** sessions／**200** structures、held-out
**200**／**200**；全部 `apron`；`roster_turn=1`（每一段都一樣）；每個 session **5** 個 item；
roster 恰好 **2** 個 item → **800** 筆訓練 entry、**400** 筆留出 entry。item 文字與 roster 映射的
**順序對齊 0 bad**（兩邊都 0）：`…灰色是 Elena、橘色是 Ivan。` 的兩個區塊分別對到 mapping 的第 1、2
個鍵值，顏色顯示詞與名字都在同一區塊內。

**（b）訓練端 5 折（依 structure 分折）per-entry 線性讀出**（2000 步、batch 64、lr 1e-3、wd 1e-4、
`PROBE_SEED=20261121`；**只用 train**，held-out 完全沒進來）：

| 特徵 | 自己名字 top1 | 自己名字 forced | 自己顏色 top1 | 自己顏色 forced | 夥伴名字 forced |
| --- | --- | --- | --- | --- | --- |
| `h`（寫入前的狀態） | 0.9762 | 0.9862 | 0.5713 | 0.7963 | 0.8100 |
| `k`（存下來的鍵） | 0.9300 | 0.9587 | 0.3688 | 0.6850 | 0.6400 |
| `v`（存下來的值） | **0.7837** | **0.8450** | 0.2375 | **0.6138** | **0.3937** |

「夥伴名字 forced」是**另一顆頭**（訓練在夥伴標籤上）：問它「這一筆偏向夥伴還是自己」，`v` 是
**0.3937 < 0.5**（偏向自己），`h`／`k` 是 0.81／0.64（把夥伴也一起編進去）。位置診斷在這個乾跑是
**in-sample 1.0**（`、` 與 `。` 的終止符不同，本來就會分開），所以只當描述量、不當閘門。

**（c）儀器**（同一支乾跑，51.1 s，只讀不訓練）：§77 治療臂的三格**逐位重現**
（in_sample 0.72／1.72、heldout 0.55／1.52、LRO 0.43／1.4225）；`weights_hash`
`sha256:0ca9e593…`、checkpoint `ba1edf16…` 前後不變；**800／400 筆的 `cos_v`／`cos_k` 全部等於
1.0**（每一筆都真的是該項的 `sigmoid(gate)·proj` 寫入，不是旁邊的槽）；相異槽 **800/800**、
**400/400**；寫入門 min **0.2064／0.2095**、median **0.9907／0.9907**、max **0.9999／0.9999**；
`norm_v` min **3.7768／3.7868**（沒有空槽）。

**（d）登記前追加的分支 `D4`**：由（b）可看出「名字讀得出來、顏色讀不太出來」是合理的部分結果
（`v` 名字 0.8450 對顏色 0.6138）。名字是該項**最後一個字元**的 token（最近的輸入），而顏色在名字
**之前**——若只登記 D1/D2/D3，「owner 留下、value 掉了」會被誤記成「兩者都沒有」（D3）。因此
**跑之前**加入 `D4-owner-only`，順序 `D1 > D4 > D2 > D3`。

（b）與（c）都是**跑之前的證據與預測**，不是分數；計分的格子是 **held-out** 的 400 筆。

### 79.3 凍結的載體與語料（跑之前寫定）

| 項目 | 值 |
| --- | --- |
| 載體報告 | `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json` |
| checkpoint | `…-190357.pt`，`sha256:ba1edf16…` |
| `weights_hash` | `sha256:0ca9e593…` |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 參數 | 168,150（`hidden=128`、`emb=64`、`core="turnstore"`） |
| 語料 | 種子 **20261127**；`train_digest` `b12cb2fb…`、`heldout_digest` `71eab688…` |
| 分割 | 400 train／200 held-out sessions；**200**／**200** structures |
| entry | 2 個 roster 項／session → 800／400 筆 |

載體**不重訓**：跑完後 `weights_hash` 與 checkpoint sha256 都必須與上面相同。**只讀治療臂**，理由見
79.5。

### 79.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `FEATURES` | **(`v`, `k`, `h`)** | `v` 是 store 的內容（primary）；`k`／`h` 是診斷（鍵與寫入前狀態）。 |
| `PRIMARY_FEATURE` | **`v`** | §78.20 指的是「同一筆裡的配對」，那就是存下來的 value。 |
| `PROBE_STEPS` | **2000** | §69／§74／§77 的同一支讀出預算；不掃階梯（§78 已掃過並排除）。 |
| `PROBE_BATCH`／`PROBE_LR`／`PROBE_WEIGHT_DECAY` | 64／1e-3／1e-4 | 同一支讀出，不動。 |
| `PROBE_SEED` | **20261121** | 同上。 |
| `NULL_DRAWS` | **400** | 同 §74–§78；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | **20261125** | 同 §74。 |
| `ALPHA` | **0.005** | 同 §74–§78。 |
| `FORCED_FLOOR` | **0.5** | 二選一的 chance；不是可調的地板。 |
| `ENTRY_COVERAGE` | **0.99** | 每一筆都要是登記的那一筆，否則不讀。 |
| `ENTRY_COSINE` | **0.999** | 同上，逐筆檢查（乾跑是 1.0）。 |
| `BRIDGE_TOLERANCE` | **1e-9** | §77 三格必須逐位重現（浮點相等，不留餘裕）。 |
| `ROSTER_ITEMS` | **2** | 語料固定；不是 2 就中止。 |

### 79.5 為什麼只有治療臂

強迫選擇需要「同一 session 的**另一項**」當對照。control（`address="turn"`）一個回合只寫**一次**，
兩個名字共寫進同一筆／同一個混合槽，所以「某一項**自己那一筆**」在 control 上**不存在**，per-entry
的強迫選擇**未定義**。硬要定義就變成「拿同一個混合向量去比兩個標籤」，量到的是混合體的偏向，不是
per-entry 的內容——那正是 §77／§78 已經量過的東西。所以本節只讀 treatment；control 的對照角色由
§77／§78 承擔，不在本節重跑，也不在本節重新解釋。

### 79.6 per-entry 協定：一筆一個標籤

1. **entry 的定義**：該項在 store 裡**自己的槽**上的 `v`（primary 特徵）、同一槽的 `k`、以及該項
   **最後一個字元**的 `h`（診斷特徵，寫入前的狀態）。
2. **抽取方式**：`run_session(..., boundaries=snapshots)` 取得第 1 回合之後的 store；再用第 0 回合的
   邊界 + `al_step(gap)` 重建第 1 回合的 `h` 軌跡，索引 `item_end_positions` 的兩個位置（本語料是
   bytes 44 與 61），槽號 `counter + i`（第 0 回合 1 個 item → `counter=1` → 槽 **1、2**，兩個都是
   全新槽，沒有移動平均覆寫）。
3. **標籤**只從 roster assert 取（`grey`→Elena、`orange`→Ivan），不從問句文字或排序猜；`assert` 在
   語料裡本來就有，這不是新標註。
4. **擬合/評分分離**：只用 train 的 800 筆擬合；標準化的 mean/std 也只從 train 算；held-out 的 400
   筆**只**在前向時進來，標籤只用在計分。

### 79.7 主要指標與門檻

* **主要指標**：within-session **two-way forced choice**——`logit[own] > logit[partner]`，其中
  `partner` 是**同一 session 另一項**的名字（顏色題同理，換成另一項的顏色）。chance **0.5**。
* **通過條件**（兩個都要）：Wilson 95% 下界 **> 0.5**，且置換檢定 **p < 0.005**。
* **虛無**：400 次抽樣，**打亂 train 的標籤**（列置換）、用同一個頭重擬合、在**同一批 held-out
  真對**上重算強迫選擇；`p = (1 + #{null ≥ observed}) / 401`。打亂 train 而不是 held-out，是因為
  held-out 標籤從未進入擬合：打亂它只會檢驗計分，不會檢驗「擬合把配對帶過來了沒有」。
* **描述量（不裁決）**：12 路（名字）／8 路（顏色）的 top1，各自的 chance 是 1/12、1/8；position
  的 in-sample top1。top1 與 forced choice 的 chance 不同，只有 forced choice 在兩個標籤集之間可比。

### 79.8 儀器門檻 `I0`（跑完後檢查）

全部成立才讀任何一格：

1. `weights_hash` 與 checkpoint sha256 **前後相同**（載體沒被動到）。
2. 報告的寫入模式是 `address="item"`、`write_strength="learned"`、`write_slots=1`。
3. 語料 digest **等於**報告記錄的 `b12cb2fb…`／`71eab688…`（種子 20261127）。
4. item 文字與 roster 映射的對齊在**兩個分割都 pass**。
5. entry 稽核：兩個分割的 coverage **≥ 0.99**，且每筆 `cos_v`／`cos_k` **≥ 0.999**、相異槽、
   `norm_v > 0`。
6. §77 治療臂三格**逐位重現**（1e-9 內）。

任何一項失敗 → `E0-instrument`，不讀讀數。

### 79.9 分支配表（跑之前寫定，優先序由左到右）

| 分支 | 條件 | 讀法 | `next` |
| --- | --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 載體／語料／標籤／entry 稽核／§77 重現有一項動了，什麼都不讀 | 先修儀器 |
| `D1-entry-carries-owner` | 名字 pass **且** 顏色 pass | 一筆裡同時有 owner 與 value：寫入**有**綁配對，§78 的不足在讀出／聚合，不在 entry 的內容 | 登記「以槽為位址、把每筆的 key 與自己的 value 配起來」的讀出（不加預算），並在第二個語料種子複現後才談綁定 |
| `D4-owner-only` | 名字 pass、顏色 fail | owner 活下來、value 那一半沒有 | 問寫入門或 value 投影是不是把較早的 token 丟掉了；不加預算 |
| `D2-key-only` | 名字 fail、顏色 pass | value 活下來、owner 沒有 | 缺的是 owner 不是 value：登記針對該項最後一個 token 的寫入側探針；不加預算 |
| `D3-entry-lacks-owner` | 兩者都 fail | 一筆裡兩個都沒有，寫入沒有綁配對 | 先量這一筆到底帶了什麼（position／終止符）再改寫入規則 |

### 79.10 預測與反證（跑之前寫定）

1. **主預測是 `D1`，但顏色會弱得多。** 理由是 79.2（b）：`v` 的名字 forced **0.8450**（訓練端 5 折，
   高於 0.5 很多），顏色只有 **0.6138**（貼近 0.5）。所以預期名字過線、顏色在邊緣；若兩者都過就是
   `D1`，若只有名字過就是 `D4`——`D4` 已經是登記的部分結果，不是事後補的。
2. **反證條件**：held-out 名字 forced **≤ 0.5**（Wilson 下界 ≤ 0.5 或 p ≥ 0.005）→ 這一筆**不**帶
   owner，落到 `D2`（只有顏色）或 `D3`（兩者都沒有）。此時 §78.20 的推論被否證，下一個登記要往
   **寫入側**走，不是往讀出側。
3. **`D1` 不是「會組合」。** 就算 `D1` 成立，本節只說「一筆裡有 owner 與 value」；組合的讀數仍是
   §77／§78 的 leave-roster-out（**1.2650 < 1.5**）。不得把 `D1` 寫成「已解決組合」。
4. **不把 79.2（b）的訓練端數字算成命中**：那是同一批訓練資料上的 5 折，是登記前的證據，不是
   留出集結果。

### 79.11 照實記的限制

1. **單一載體、單一語料種子、k=2、單一讀出（線性）**：所有讀數只屬於種子 20261127 的 400／200 分割。
   §75 已量到幅度不跨語料種子複現，所以任何「綁定」宣稱都要等第二個種子。
2. **這是探針，不是模型生成**：核心分不變 **0.00/10**；本節是診斷，不是能力分數，也不是新的分數來源。
3. **強迫選擇的對照是同一 session 的另一項**（兩個名字都在同一份 roster 裡），所以它量的是「這一筆
   偏向自己的標籤」，**不是**「模型能從 store 檢索出名字」。後者需要以問題為 query 的讀出，不在本節。
4. **`h` 是寫入前的狀態，不是 store 的內容**：它高分只說「寫入點已經知道」，不證明「寫進去的東西
   帶著」。所以 `h` 只當診斷，裁決只用 `v`。
5. **`v` 只有 64 維，且兩個 item 的終止符不同**（`、` vs `。`）：顏色只有 8 個方向，容易被位置混淆。
   因此 position 只當描述量、不當閘門，也不拿它解釋顏色分數。
6. **兩個標籤集的先驗不同**（12 名字／8 顏色）：top1 不可互比，只有 forced choice（chance 都是 0.5）
   可比。
7. **control 不被讀**（79.5）：本節**不能**說「治療比 control 好」，只能說「治療的單筆裡有什麼」。
8. **§78 的 matched cell 不重跑**：§78 用 treatment@250（0.5250）配 control@8000（0.5150）；本節固定
   在 2,000 步的讀出慣例上，不掃階梯，所以不可拿來改寫 §78 的任何一格。

### 79.12 命令與執行上限

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=2 \
  systemd-run --scope --user -p CPUQuota=200% -p MemoryMax=4096M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/probe_pantry_pair79.py \
    --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --out data/pantry_stage/pair79/k2.json --device cpu

./.venv/bin/python scripts/probe_pantry_pair79.py --check data/pantry_stage/pair79/k2.json
```

上限沿用本專案的硬規則：**CPU 200%（兩核）／RAM 4 GiB／swap 0／GPU 不使用（`--device cpu`）**，低於
50%／60%／60% 的門檻；乾跑在 2 threads 下是 51.1 s，計分跑同一條路徑。輸出只寫
`data/pantry_stage/pair79/`（gitignored），不寫任何被量測的環境。

這一節在**計分跑之前**寫定。任何跑之前的改動都會以 amendment 記在 79.13 之前；被丟棄的跑法照實記。

### 79.13 結果：`D1-entry-carries-owner`（計分跑 1,144.72 s）

一次跑完，**沒有作廢的計分跑**。上限：`CPUQuota=200%`、`MemoryMax=4096M`、`MemorySwapMax=0`、
`OMP_NUM_THREADS=2`、`--device cpu`（實測 195% CPU、4.4% RAM）。`--check` **OK**。

**（a）主要讀數（held-out 400 筆，within-session 二選一，chance 0.5）**

| 特徵 | 標籤 | forced | Wilson 95% | top1（chance） | p | null 最大 |
| --- | --- | --- | --- | --- | --- | --- |
| **`v`（primary）** | **名字** | **0.9350**（374/400） | **0.9065–0.9553** | 0.8350（0.0833） | 0.002494 | 0.6325 |
| **`v`（primary）** | **顏色** | **0.6200**（248/400） | **0.5715–0.6662** | 0.2025（0.1250） | 0.002494 | 0.5875 |
| `k` | 名字 | 0.9900（396/400） | 0.9746–0.9961 | 0.9600 | 0.002494 | 0.6500 |
| `k` | 顏色 | 0.7375（295/400） | 0.6923–0.7782 | 0.4175 | 0.002494 | 0.6000 |
| `h` | 名字 | 1.0000（400/400） | 0.9905–1.0000 | 0.9950 | 0.002494 | 0.6775 |
| `h` | 顏色 | 0.8375（335/400） | 0.7982–0.8704 | 0.6650 | 0.002494 | 0.6025 |

六個讀數的 400 次置換都是 **0 次** ≥ 觀察值（p 都是最小可達的 0.002494），虛無的 forced 平均
**0.4906–0.5023**、p99 **0.5525–0.6150**。position 描述量三個特徵都是 **in-sample 1.0**
（`、`／`。` 不同，如 79.2 所述，不裁決）。

**（b）儀器 `I0` 全過**：`weights_hash` 與 checkpoint sha256 前後相同（`sha256:0ca9e593…`／
`ba1edf16…`）；寫入模式 `item`／`learned`／1；語料 digest 相符；item↔映射對齊 **400+200 段、0 bad**；
entry 稽核 coverage **1.0／1.0**、`cos_v`／`cos_k` 最小 **1.0**、相異槽 800/800 與 400/400、
`norm_v` 中位數 17.33（min 3.79）；§77 三格**逐位重現**（0.72／1.72、0.55／1.52、0.43／1.4225）。
寫入門 min 0.2064／0.2095、median 0.9907、max 0.9999——每一筆都真的落地。

**（c）分支**：`D1-entry-carries-owner`。

### 79.14 預測檢查

1. **主預測 `D1` 命中**（§79.10 第 1 點）。
2. **「顏色會弱得多」命中**：0.6200 對名字 0.9350（差 **0.3150**），與登記前乾跑的排序
   （0.6138 對 0.8450）一致。
3. **反證條件沒有觸發**：名字 forced 0.9350 遠高於 0.5，Wilson 下界 0.9065。
4. **但幅度不是預測命中，照實記**：登記前乾跑（訓練端 5 折）是 **0.8450／0.6138**，留出是
   **0.9350／0.6200**——名字被**低估 0.09**，顏色幾乎一樣（+0.0062）。所以命中的是**排序與方向**，
   不是數字；不得把乾跑當成預測精度。
5. **單調 `v < k < h` 成立**（名字 0.9350／0.9900／1.0000；顏色 0.6200／0.7375／0.8375），與「`v` 是
   128→64 投影後、`k` 是同一組投影的鍵、`h` 是寫入前狀態」一致。

### 79.15 `D1` 的準確讀法（它說什麼、不說什麼）

1. **一筆 entry 帶 owner，而且很強**：名字 0.9350、Wilson 0.9065–0.9553、400 次置換的最大值
   0.6325。這不是邊緣訊號。
2. **顏色過線但弱**：0.6200 ＝ chance **+0.12**。它通過的是**登記的門檻**（Wilson 下界 > 0.5、
   p < 0.005），不是「效果好」的證明。準確的說法是**owner 強、value 弱但可讀**，不是「兩個一樣牢」。
3. **§78 的 shortfall 不在 entry 的內容**：這是本節支持的方向——pooled 讀出把兩筆混在一起解一組名冊，
   而單筆裡本來就有自己的標籤。
4. **不是「store 會組合」**：LRO 仍是 **1.2650 < 1.5**（§78）。一筆帶自己的 key 與 value ≠ 能把跨槽的
   key 與 value 配起來回答「誰穿橘色」。組合的缺口沒有被本節補上。
5. **核心分仍 0.00/10**：這是凍結載體＋線性探針的診斷，不是模型生成，也不是能力分數。

### 79.16 結果後追加的描述量（不是新閘門，不改變分支）

登記的 Wilson 把 **400 筆 entry** 當獨立單位，但它們是 **200 個 session × 2 筆**。用**同一支已登記的
擬合**（同種子、同步數，entry 勝場數逐位重現 374/400 與 248/400）改按 session 計數：

| 標籤 | 兩項都對 | Wilson 95% | 至少一項對 | 兩項都錯 |
| --- | --- | --- | --- | --- |
| 名字 | **174/200 = 0.8700** | 0.8163–0.9097 | 200/200 = 1.0000 | **0** |
| 顏色 | **74/200 = 0.3700** | 0.3061–0.4388 | 174/200 = 0.8700 | **26（13%）** |

這**不**改寫 79.13 的任何一格，也**不**改分支（登記的閘門是 per-entry）。但它把「value 在 entry 裡」
的讀法收窄：**owner 在整個 session 上幾乎總是被讀到（至少一項 200/200），顏色則只有 37% 的 session
兩項都對、13% 兩項都錯**。所以正確的句子是「顏色在單筆上線性可讀、但不可靠」，不是「顏色也在」。

### 79.17 照實記的結果限制

1. **寫入門幾乎全開**（median 0.9907、max 0.9999），所以 `v ≈ value_proj(h)`：本節量到的是
   **配對在寫入點可用、且穿過 `value_proj` 之後仍可讀**，**不能**分離「store 的寫入規則保存了它」與
   「寫入點的狀態本來就有它」。§79.11 第 4 點在登記時就寫下這個限制，結果讓它變成實測事實（`h` 的
   1.0000／0.8375 是上界）。要分離需要把門壓低或換寫入規則，那是另一個登記。
2. **線性讀出**：0.6200 是「線性可讀」的**下界**，不是顏色的上界；非線性讀出可能更高，本節沒有量。
3. **單一載體、單一語料種子、k=2**：第二個種子未做，任何「綁定」宣稱仍要等它（§75 的教訓）。
4. **control 未讀**（79.5）：不能說「治療比 control 好」，只能說「治療的單筆裡有什麼」。
5. **`D1` 的 `next` 沒有做**：以槽為位址、把每筆的 key 與自己的 value 配起來的讀出，仍是未量的事。

### 79.18 這一節改變了什麼

* **可裁決的結論**：`D1`——在凍結的 §77 治療載體上，一筆 entry 帶自己的名字
  （0.9350，Wilson 0.9065–0.9553）與自己的顏色（0.6200，0.5715–0.6662），兩者都過 400 次置換
  （p 0.002494）。**owner 強、value 弱但可讀**。
* **被排除的下一步**：往寫入側找「配對根本沒進去」。它在（至少 owner 在），所以 §78.20 的推論
  被支持，而「寫入沒有綁任何東西」被否證。
* **仍然有效的停損**：不加 epoch／寬度／資料（§75.7）、不改 1.5、不在 held-out 上調參、不在
  benchmark 題目上調參。
* **下一個登記（分支 `next`）**：以槽為位址、把每筆的 `key` 與**自己的**`value` 配起來的讀出
  （不加預算），並在第二個語料種子複現後才談綁定。

## §80 store 自己的讀，在提問那一回合有沒有指到問題需要的那一筆？

### 80.1 這一節問什麼

§79 量的是**一筆 entry 裡有什麼**：用逐筆擬合的探針，強迫它在同一 session 的兩筆之間選一筆。那個探針
**被告知要看哪一筆**，所以它量的是**寫入**的內容，不是模型在回答時**實際做的那次讀**。

§79 登記的 `next` 是「以槽為位址、把每筆的 `key` 與自己的 `value` 配起來的讀出」。本節**不是**那個
新讀出——在加新讀出之前，先量**現有的那次讀**：

> 在凍結的 §77 治療載體上，模型在**提問回合的最後一個 token**、用**自己的** softmax
> （`softmax(exp(log_read_scale) · k·q)`）讀 store 時，有沒有把注意力放在「證據顏色所對應的那一筆
> 名冊 entry」上，而不是放在另一筆？

這一節**不**重訓、**不**微調、**不**改門檻、**不**掃讀出階梯、**不**在 held-out 上調參、**不**把探針
擬合到答案上。`A` 是模型自己 softmax 的輸出，**沒有任何擬合參數**。

### 80.2 登記前已經量到的（照實寫）

**（a）語料、標籤與讀點**（唯讀）：train **400** sessions／**200** structures（其中 **200** 個
order-augmented 雙生、200 對）、held-out **200**／**200** structures（**0** 個雙生）；全部 `apron`；
`roster_turn=1`、`evidence_turn=2`、提問回合是第 3 回合（最後一回合）。每個 session 的 item 數依回合是
**1／2／1／1**，所以 roster 之前已寫 **1** 筆 → roster 佔槽 **1、2**；證據回合寫槽 **3**；提問回合的
寫入在讀**之後**才發生，**不在**這次讀的 store 裡。標籤取語料自己的 `assert`：名冊是
`{"kind":"roster","value":{…}}`、證據是 `{"kind":"seen","value":"grey"}`——不是從問句文字或排序猜的。
item 文字與映射順序對齊 **0 bad**；正確那一筆在 train 是 **200／200**、held-out 是 **100／100**。

**（b）訓練端 400 次讀（**只用 train**，held-out 完全沒進來；跑之前的證據，不是分數）**：

| 讀數 | 值 |
| --- | --- |
| roster 兩槽的注意力質量 | mean **1.0**、min **1.0**、max **1.0** |
| argmax 落在哪個槽 | 槽 **2**，**400/400** |
| 二選一（正確槽 vs 夥伴槽） | **200/400 = 0.5000**，Wilson **0.4512–0.5488**，虛無平均 200、p **1.0** |
| 槽 1 的 key 範數 | min **1.0278**／median **2.6123**／max **4.5379** |
| 槽 2 的 key 範數 | min **6.6764**／median **9.8711**／max **14.7399** |
| query 範數 | min **16.7570**／median **17.8321**／max **17.9380** |
| `cos(r, v_槽2)` | **1.0**（400/400，min 1.0） |
| `cos(r, v_槽1)` | mean **0.3392**、max **0.9821** |

也就是說：**每一次讀的質量都完整落在槽 2**，而正確那一筆剛好一半在槽 2（100／200 的平衡），所以
二選一正好是 0.5。槽 2 的 key 範數是槽 1 的 **3–4 倍**（中位數 9.87 對 2.61），softmax 在
`exp(log_read_scale)=4` 下已經飽和——這是「**範數競賽**」的形狀，不是「問句指到哪一筆」的形狀。

**（c）雙生對的注意力移動（train 的 200 對）**：同一句問句、名冊順序對調（所以需要的那一筆從槽 1 換到
槽 2），兩次讀的注意力分布總變差（TV）mean **0.0**、sd **0.0**、max **0.0**；只算 roster 兩槽的 TV 也是
**0.0**。**一次都沒有移動。**

**（d）提問回合的狀態裡有沒有證據顏色**（描述量，不裁決）：`h_final → 證據顏色`（8 路，train 5 折、
2,000 步、同一個 `PROBE_SEED`）top1 **0.1050**（42/400），chance **0.125**。**低於 chance**：這個線性
讀看不到證據顏色。

**（e）讀點稽核**：在提問回合之前的邊界（`snapshots[q-1]`）上，槽 1、2 的 `v` 與 §79 抽出的同一筆
entry 的 `cos` **全部 = 1.0**（train 400/400），兩槽相異、非空。

**（f）為什麼本節**沒有**登記「解出犯人名」的格子**：這份語料的名冊映射高度重複——600 個 session 只有
**378** 個相異的完整映射，其中 **367/378（97.1 %）** 只有**一個**犯人。也就是說：只要讀得到名冊，
犯人的名字在 97 % 的 session 裡就被決定了，證據回合是多餘的。實測（train 5 折）：用槽 2 的 value 解
犯人名字是 **0.9550**（382/400），解證據顏色只有 **0.1675**（67/400，chance 0.125）；槽 1 是
**0.4650**／**0.2325**。名字那個數字是**映射記憶**，不是組合，所以本節**不**把它登記成格子；唯一計分
的格子是「注意力的二選一」。（150 筆的較早乾跑給 0.9533／0.1133，被這次 400 筆的完整量測取代；兩者都
不用作格子。）

（b）–（e）都是**跑之前的證據與預測**，不是 held-out 的分數。計分的格子是 held-out 的 **200** 次讀。

### 80.3 凍結的載體與語料（跑之前寫定）

| 項目 | 值 |
| --- | --- |
| 載體報告 | `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json` |
| checkpoint | `…-190357.pt`，`sha256:ba1edf16…` |
| `weights_hash` | `sha256:0ca9e593…` |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 參數 | 168,150（`hidden=128`、`emb=64`、`core="turnstore"`） |
| 語料 | 種子 **20261127**；`train_digest` `b12cb2fb…`、`heldout_digest` `71eab688…` |
| 分割 | 400 train／200 held-out sessions；**200**／**200** structures |
| 讀 | 1 次／session → **400**／**200** 次 |
| 雙生 | train **200** 對；held-out **0**（見 80.7） |

載體**不重訓**：跑完後 `weights_hash` 與 checkpoint sha256 都必須與上面相同。只讀治療臂；control 的
對照角色由 §77／§78 承擔（理由同 §79.5：control 一回合只寫一次，per-item 的注意力問題在它上面未定義）。

### 80.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `PROBE_STEPS` | **2000** | 只有 80.2（d）的描述量用到；與 §69／§74／§77／§79 同一支讀出。 |
| `PROBE_BATCH`／`PROBE_LR`／`PROBE_WEIGHT_DECAY` | 64／1e-3／1e-4 | 同上，不動。 |
| `PROBE_SEED` | **20261121** | 同上。 |
| `NULL_DRAWS` | **400** | 同 §74–§79；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | **20261125** | 同 §74。 |
| `ALPHA` | **0.005** | 同 §74–§79。 |
| `FORCED_FLOOR` | **0.5** | 二選一的 chance；不是可調的地板。 |
| `SW_SLOT_FLOOR` | **0.01** | 「固定槽」與「跟著內容走」的分界：平均 TV ≤ 1 % 視為沒移動。 |
| `ENTRY_COVERAGE` | **0.99** | 讀點上的兩筆都必須還是登記的那兩筆。 |
| `ENTRY_COSINE` | **0.999** | 同上，逐筆檢查（乾跑是 1.0）。 |
| `BRIDGE_TOLERANCE` | **1e-9** | §77 三格必須逐位重現。 |
| `ROSTER_ITEMS` | **2** | 語料固定；不是 2 就中止。 |
| `READ_BATCH` | **32** | 只影響速度，不影響任何讀數（分批不跨 session）。 |

### 80.5 讀點（跑之前寫定）

1. **store**：`run_session(..., boundaries=snapshots)` 之後，`snapshots[q-1]` ＝**證據回合之後、提問回合
   之前**的狀態（`q` 是最後一回合）。提問回合自己的寫入在讀之後，**不在**這次讀的 store 裡。
2. **`h`**：從該邊界出發，先 `al_step(提問回合的 gap)`，再逐 token 重放提問回合，取**最後一個 token**
   的 `h`（與 `_run_turn` 的計算方式相同）。
3. **讀**：`query = W_q h`、`scores = k · query`、`weights = softmax(exp(log_read_scale) · scores)`、
   `r = weights @ v`。**沒有任何擬合參數**；`log_read_scale` 是載體自己的。
4. **槽**：`counter + i`，`counter` ＝ roster 之前已寫的 item 數（本語料是 1）→ 槽 **1、2**；若
   `counter + 2 > slots` 就中止（不讓環繞把兩筆混在一起）。
5. **標籤**：證據回合的 `seen` assert 給顏色鍵；名冊 assert 給 `(顏色鍵, 名字)` 的**文字順序**；
   正確那一筆 ＝ 顏色鍵在名冊順序中的位置。**不**從問句文字、**不**從犯人名字反推。

### 80.6 主要指標與門檻

* **主要指標**：held-out 的 **two-way forced choice of attention mass**——`weights[correct] >
  weights[partner]`，`partner` 是同一 session 的**另一筆** roster entry。chance **0.5**。
* **通過條件**（兩個都要）：Wilson 95% 下界 **> 0.5**，且置換檢定 **p < 0.005**。
* **虛無**：**打亂 held-out 的 `item` 標籤**（列置換）、**不重擬合**（讀沒有參數）、在同一批讀的
  質量上重算二選一；400 次抽樣，`p = (1 + #{null ≥ observed}) / 401`。打亂標籤而不是重跑模型，是因為
  模型與 store 都是凍結的：要檢驗的是「注意力的高低與『哪一筆才是需要的那一筆』有沒有關係」。
* **描述量（不裁決）**：roster 質量、argmax 直方圖、兩槽的 key 範數、`cos(r, v)`；以及 80.2（d）的
  `h → 證據顏色`。

### 80.7 機制控制 `SW`（用 train 的雙生對，不是 held-out）

held-out **沒有**雙生（200 sessions／200 structures），所以「名冊順序對調、需要的那一筆換槽」這個
介入只能在 train 上做：train 有 **200** 對語料自己產生的 order-augmented 雙生（同一句問句、名冊
`灰色是 Elena、橘色是 Ivan` ↔ `橘色是 Ivan、灰色是 Elena`）。

* 對每一對，取兩次讀的注意力分布（16 槽）的**總變差** `TV = ½·Σ|w_a − w_b|`；`SW` ＝ 200 對的平均。
* **固定槽**的讀：TV = 0（兩次都停在同一個槽）。**跟著需要的那一筆**的讀：需要的那一筆換了槽，TV
  必須接近 1（或至少遠大於 0.01）。
* `SW` **沒有標籤**，所以它不能被調參；它**不進入**計分格子，只把「`A` 失敗」拆成
  `H1`（固定槽）與 `H2`（有跟著某種內容、但不是需要的那一筆）。
* 限制照實寫：雙生同時改了名冊的**文字順序**（token 序列）與槽位，所以 `SW > 0.01` 只證明「不是固定
  槽」，不證明「跟的是證據顏色」。要分離「跟顏色」與「跟位置／範數」，是另一個登記。

### 80.8 儀器門檻 `I0`（跑完後檢查）

全部成立才讀任何一格：

1. `weights_hash` 與 checkpoint sha256 **前後相同**。
2. 報告的寫入模式是 `address="item"`、`write_strength="learned"`、`write_slots=1`。
3. 語料 digest **等於**報告記錄的 `b12cb2fb…`／`71eab688…`（種子 20261127）。
4. item 文字與 roster 映射的對齊在**兩個分割都 pass**。
5. **讀點稽核**：兩個分割的 coverage **≥ 0.99**，且槽 1、2 的 `v` 與 §79 的同一筆 entry 的
   `cos ≥ 0.999`、兩槽相異、非空（讀點上的 store 還是名冊那兩筆，不是被後面的回合蓋掉）。
6. §77 治療臂三格**逐位重現**（1e-9 內）。

任何一項失敗 → `E0-instrument`，不讀讀數。

### 80.9 分支配表（跑之前寫定，優先序由左到右）

| 分支 | 條件 | 讀法 | `next` |
| --- | --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 載體／語料／標籤／讀點稽核／§77 重現有一項動了，什麼都不讀 | 先修儀器 |
| `H3-read-addresses` | `A` pass（Wilson 下界 > 0.5 且 p < 0.005） | 模型自己的讀**有**指到問題需要的那一筆：store 的讀是問題定址的，§78 的不足在讀之後 | 登記「讀向量經 head 的作答」格子（不加預算），並在第二個語料種子複現 |
| `H1-read-ignores-query` | `A` fail 且 `SW ≤ 0.01` | 讀沒過二選一，且名冊對調時**完全沒移動**：它是**固定槽**，不是在定址問題需要的那一筆 | 登記寫入側的改動（讓 key 在寫入點帶著名冊顏色），或登記「問句直接說出證據顏色」的 query；不加預算、門檻不動 |
| `H2-read-uses-query-but-wrong` | `A` fail 且 `SW > 0.01` | 讀有跟著某種 store 內容移動，但不是需要的那一筆 | 先量它跟的是什麼（key 範數／最近寫入／證據那一筆）再改讀的規則；不加預算 |

### 80.10 預測與否證（跑之前寫定）

1. **主預測是 `H1`。** 理由是 80.2（b）–（c）：train 的 400 次讀**全部**落在槽 2（質量 1.0），而
   正確那一筆是平衡的 200／200，所以二選一正好 0.5；名冊對調的 200 對 TV **全部是 0.0**。
2. **反證條件**：held-out 的 `A` **pass**（Wilson 下界 > 0.5、p < 0.005）→ `H3`。那會否證「讀是固定
   槽」，並把 §78 的缺口移到讀之後（聚合／head），不是讀之前。
3. **`H2` 是第三種結果**：`A` fail 但 `SW > 0.01`。事前證據讓它不太可能（train 的 SW 是 0），但它是
   機械分支，不是事後補的。
4. **`A` pass 不是「模型會回答」**：它只說注意力放對了那一筆。答案還要經過 `head`；本節**沒有**登記
   讀向量→答案的格子。
5. **不把 80.2 的訓練端數字算成命中**：那是 train 的 400 次讀與 200 對雙生，是登記前的證據。

### 80.11 照實記的限制

1. **單一載體、單一語料種子、k=2**：所有讀數只屬於種子 20261127 的 400／200 分割；§75 已量到幅度
   不跨語料種子複現，任何「定址」宣稱都要等第二個種子。
2. **`SW` 是 train 的機制控制，不是 held-out 讀數**：held-out 沒有雙生。它沒有標籤、不能調參，也不
   進入計分格子；但它不能單獨支持「模型會定址」——那只能由 held-out 的 `A` 支持。
3. **`A` 只有兩筆可選**：它量的是「在名冊的兩筆之間偏好哪一筆」。若模型偏好某個槽、而該槽剛好與
   正確那一筆相關，`A` 會被動到；`SW` 就是為了排除這個（固定槽在雙生上不動）。但 `A` pass 仍不等於
   「模型知道顏色的意義」。
4. **`r` 是 value 的加權平均**：`A` pass 只說質量放對；`r` 是否帶著可用的 name/colour 是 §79 的
   per-entry 讀數（0.9350／0.6200），不是本節。
5. **提問回合的寫入不在 store 裡**（80.5 第 1 點）：這是「提問時讀到的東西」的正確定義，但也意味著
   本節不能說「寫入之後的 store」如何。
6. **沒有解犯人的格子**（80.2（f））：名冊映射的重複讓那個格子會在 0.95 左右，與證據無關；本節不登記
   它，也不拿它當支持。
7. **這是探針，不是模型生成**：核心分不變 **0.00/10**；本節是診斷，不是能力分數，也不是新的分數來源。
8. **輸出只寫 `data/pantry_stage/address80/`**（gitignored），不寫任何被量測的環境。

### 80.12 命令與執行上限

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=2 \
  systemd-run --scope --user -p CPUQuota=200% -p MemoryMax=4096M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/probe_pantry_address80.py \
    --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --out data/pantry_stage/address80/k2.json --device cpu

./.venv/bin/python scripts/probe_pantry_address80.py --check data/pantry_stage/address80/k2.json
```

上限沿用本專案的硬規則：**CPU 200%（兩核）／RAM 4 GiB／swap 0／GPU 不使用（`--device cpu`）**，低於
50%／60%／60% 的門檻。登記前的 train-only 乾跑在同一條路徑上完成（400 次讀、200 對雙生、一次 5 折
描述量），計分跑多的是 held-out 的 200 次讀與 400 次標籤置換（置換**不重擬合**，只重算二選一）。

這一節在**計分跑之前**寫定。任何跑之前的改動都會以 amendment 記在 80.13 之前；被丟棄的跑法照實記。

### 80.13 執行（照實記）

* 登記的指令是 `CPUQuota=200%`；實際起跑時整機已經被別的程式佔到 **44 %**（用 `/proc/stat` 量的，不是本專案
  的負載），若照登記的 200 % 跑會頂到硬規則的 50 % 上限，所以改用 `CPUQuota=50%`、`OMP_NUM_THREADS=1`
  的 transient user service（`systemd-run --user --unit=address80-scored --collect`，
  `MemoryMax=4096M`、`MemorySwapMax=0`、`--device cpu`）。這是**執行方式**的改動：讀沒有擬合參數，也沒有
  隨機性，所以不影響任何讀數，只影響 wall time；照實記在這裡。
* 執行 **211.83 s**，峰值記憶體 **247.8 MB**、swap **0**；跑的時候量到整機 CPU **37 %**（< 50 %）。
* **沒有被丟棄的跑法**：第一次執行就是登記的讀數。輸出只寫 `data/pantry_stage/address80/k2.json`
  （gitignored，不進版控）。`--check` **OK**。

### 80.14 儀器 `I0`（全過）

| 條款 | 值 |
| --- | --- |
| `weights_hash` 前後 | 相同（`sha256:0ca9e593…`） |
| checkpoint sha256 前後 | 相同（`sha256:ba1edf16…`） |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 語料 digest | `b12cb2fb…`／`71eab688…`（種子 20261127） |
| item↔映射對齊 | train／held-out 都 **0 bad** |
| 讀點稽核 | coverage **1.0**（train 400/400、held-out 200/200）；槽 1、2 的 `cos` min／median／max 都 **1.0** |
| §77 三格 | in-sample 0.72／1.72、held-out 0.55／1.52、leave-roster-out 0.43／1.4225，**逐位重現**（1e-9） |

### 80.15 主要讀數 `A`（held-out 200 次讀）：**不過**

| 讀數 | 值 |
| --- | --- |
| 二選一勝出 | **100 / 200 = 0.5000** |
| Wilson 95% | **0.4314–0.5686**（下界 **< 0.5**） |
| 置換虛無 | 400 次抽樣，`#{null ≥ 觀察}` = **400 / 400**（平均 **100.0**、sd **0.0**） |
| p | **1.0**（> 0.005） |
| roster 兩槽的注意力質量 | mean／min／max 都 **1.0** |
| argmax | 槽 **2**，**200/200** |
| 兩槽 key 範數 | 槽 1 median **2.8158**（1.0264–4.3641）、槽 2 median **9.8219**（6.6717–14.3181） |

存下來的 `m0`（槽 1 的質量）**每一個都是 0.0**，`m1`（槽 2）**每一個都是 1.0**：不是「多數讀偏向槽 2」，
是**每一次讀都完整落在槽 2**。所以二選一在**任何** `item` 標籤排列下都剛好 100 勝——400 次置換沒有一次低於
觀察值，p 是 **1.0**。這不是「剛好沒過門檻」，是**沒有訊號**。

### 80.16 機制控制 `SW`（train 的 200 對雙生）：**一格都沒動**

`SW`（注意力分布的總變差平均）＝ **0.0**（sd 0.0、min 0.0、max 0.0）；只算兩槽的 roster TV 也是 **0.0**；
`slot_fixed = True`（門檻 0.01）。名冊順序對調、需要的那一筆從槽 1 換到槽 2，讀**完全沒有跟著換**。

### 80.17 描述量（不裁決）

* `h_final → 證據顏色`（train 5 折、2,000 步）：**0.1050**（42/400），chance **0.125**——與登記前同一支
  探針量到的 0.1050 逐位相同，五折是 8／8／14／6／6（每折 80 列）。
* 質量 1.0 落在槽 2 的算術結果是 `r` **就是槽 2 的 value**（`weights[2]=1` → `r = v_槽2`）；登記前量到的
  `cos(r, v_槽2)=1.0`／`cos(r, v_槽1)` mean 0.3392 仍然成立。
* 每次讀的兩個 roster 槽都非空、且與 §79 抽出的同一筆 entry `cos=1.0`（80.14 的讀點稽核）。

### 80.18 分支與預測檢查

* 機械分支：**`H1-read-ignores-query`**（`A` 不過，且 `SW` ≤ 0.01）。
* 登記的預測（80.10 第 1 點）**命中**：預測就是 `H1`。反證條件（held-out 的 `A` pass → `H3`）**沒有**發生
  （Wilson 下界 0.4314、p 1.0）。`H2` 也沒有發生（`SW` 是 0，不是 > 0.01）。
* **這一節改變了什麼**：§78 的 shortfall 在**讀之前**，而且不是「entry 沒帶配對」（§79：owner 0.9350），
  也不是「讀有看但看錯」（`SW` 是 0）——是**這次讀根本沒有用問句去選任何一筆**。在提問回合，模型自己的
  softmax 把 100 % 的質量放在槽 2，不管證據顏色要的是哪一筆；`r` 因此是固定那一槽的 value。這也解釋了
  §79 的 pooled 讀出為什麼只到 1.2650：餵進讀出的向量不隨問題移動，組合只能在讀之後無中生有。
* 照實記一個算術上的巧合：`A` 在「槽 2 剛好是正確那一筆」的一半 session 上才會是 0.5。本語料的 `item`
  是平衡的（train 200/200、held-out 100/100），所以固定槽的二選一**正好**是 0.5；這不是事後修正，是登記
  前就算過的事（80.2（b））。

### 80.19 照實記的限制

1. 單一載體、單一語料種子（20261127）、k=2（同 80.11）。「讀是固定槽」的宣稱只屬於這組凍結條件。
2. `SW` 是 train 的機制控制，held-out 沒有雙生；它把「`A` 失敗」拆成 `H1`／`H2`，本身不是 held-out 讀數。
3. `A` 只有兩筆可選：它說「不是需要的那一筆」，**不是**「讀不到任何東西」——固定槽的結論要靠 `SW` 補。
4. 提問回合自己的寫入不在這次讀的 store 裡（80.5 第 1 點）；本節不能說「寫入之後的 store」如何。
5. 沒有解犯人的格子（80.2（f））：名冊映射的重複讓那個數字會在 0.95 左右，與證據無關。
6. 這是探針，不是生成；**核心分仍 0.00/10**，本節不新增也不改變任何分數來源。
7. 執行時的 CPU quota 從登記的 200 % 降到 50 %（80.13），只影響 wall time，不影響任何讀數的定義。

### 80.20 下一個登記（分支 `next`，不在本節選）

依 `H1` 的 `next`，兩條路都**不加預算、不改門檻**：

1. **寫入側**：讓 `k` 在寫入點就帶著名冊顏色（現在槽 2 的 key 範數是槽 1 的 3–4 倍，softmax 在
   `exp(log_read_scale)=4` 下已經飽和——這是範數競賽的形狀，不是內容定址的形狀）。
2. **query 側**：登記一個**說出證據顏色**的 query，把「問句→顏色」這一跳從 `h` 的線性讀（0.105，
   低於 chance 0.125）移到 query 的輸入上。

先做哪一個由下一個登記寫定；本節不選，也不在前一節的結果上調參。

## §81 把鍵的範數拿掉，讀就能指到問題需要的那一筆嗎？

### 81.1 這一節問什麼

§80 量到的是「**這次讀沒有在選**」：held-out 200 次讀的注意力質量**每一次都完整落在槽 2**（`m0` 全
`0.0`、`m1` 全 `1.0`），二選一 **100/200 = 0.5000**，train 的 200 對雙生 TV **全部 0.0**。§80.20 因此
留下兩條互斥的修法（寫入側讓 key 帶顏色，或 query 側直接說出顏色）。

在那之前，§80 的診斷還留著**一個沒被否證的機械原因**：槽 2 的 key 範數中位數 **9.8219** 對槽 1 的
**2.8158**，而讀是 `softmax(exp(log_read_scale) · k·q)`、`exp(log_read_scale) = 4`、
`||q|| ≈ 17.8`。§80 的讀數與這個原因一致，但**沒有分離它**——「質量 1.0 在槽 2」既可能是「鍵的範數決定
了一切」，也可能是「兩鍵的方向根本沒有分辨這兩筆的資訊」。這兩件事的修法完全不同（改讀的算術 vs 改寫的
內容），而 §80.20 的兩條路**都假設了後者**。

本節只問前者，用**同一批凍結的讀**、**不重訓**、**零擬合參數**：

> 把 key 的範數（以及必要時的 query 範數與學到的溫度）拿掉之後，同一次讀會不會指到問題需要的那一筆？

三條讀的規則只差在「拿掉什麼」：

* `model`：`softmax(exp(scale) · k·q)`——模型自己的讀（＝§80）。
* `cosine`：`softmax(exp(scale) · (k/‖k‖)·q)`——拿掉 key 的範數，學到的溫度留著。
* `cosine_unit`：`softmax((k/‖k‖)·(q/‖q‖))`——連 query 範數與溫度都拿掉，logit 就是純餘弦。

**這條讀的規則是本節的，不是模型的。** pass 只說「store 裡的內容是可定址的」，**不**說「這個載體會用
這種方式定址」。fail 則說「這個形狀的讀規則都定址不了」，於是下一刀該落在寫入側。

`model` 欄是**錨**：它必須把 §80 存下來的質量重現到 **2e-9**、勝場數也必須是 **100**，否則什麼都不讀。

### 81.2 登記前已經量到的（照實寫）

**（a）全部來自 §80 的凍結報告**（`data/pantry_stage/address80/k2.json`，不改寫、不重跑）：

| 量 | 值 |
| --- | --- |
| held-out 讀數 | **200**（200 sessions／200 structures，**0** 雙生） |
| 二選一 | **100/200 = 0.5000**，Wilson **0.4314–0.5686**，p **1.0** |
| 槽 1 key 範數 | median **2.8158**（1.0264–4.3641） |
| 槽 2 key 範數 | median **9.8219**（6.6717–14.3181） |
| query 範數 | median **17.8321**（16.7570–17.9380） |
| `exp(log_read_scale)` | **4.0** |
| 質量 | `m0` 全 **0.0**、`m1` 全 **1.0**；argmax 槽 2 **200/200** |
| train 雙生 200 對 | TV mean／max 都 **0.0** |

**（b）算術形式（跑之前算的，不是事後解釋）**：把上面的數字代進去，兩個槽的 logit 差在「兩鍵與 query
夾角相同」時約 `4 × 17.83 × (9.82 − 2.82) ≈ 500`；float32 的 `softmax` 在這個差距下就是 `1.0` 與
`0.0`。這與 §80 存下來的 `m0`／`m1` 完全一致——**讀的輸出已經飽和**，方向差異最多只能在數百的尺度裡挪
動一點，改不了誰贏。所以「質量 1.0 在槽 2」在算術上是**可以先於內容**發生的；本節就是把這個先驗拿掉再
看一次。

**（c）`cosine` 與 `cosine_unit` 的**上界**（也是跑之前算的）**：`cosine` 的 logit 是
`4 · 17.83 · cos ≈ ±71`，差距還是可以很大；`cosine_unit` 的 logit 是 `cos ∈ [−1, 1]`，兩槽的質量比最多
`e² : 1`，也就是單次讀的質量最多 **0.881 / 0.119**。**二選一是嚴格比較（`correct > partner`），不是差距
門檻**，所以只要方向一致，邊界小也照樣算贏——這是本節能裁決的原因，也是它的限制（81.11 第 3 點）。

**（d）跑之前**沒有**量過任何一條 cosine 讀在這批 session 上的結果**。契約測試只在小張量上釘住算術
（三條規則的單調性、cosine 對 key 縮放不變、unit 對溫度不變），**不含任何載體資料**，也不產生讀數。
本節的分數只來自 81.12 的那一次計分跑。

**（e）已修的儀器缺陷（跑之前，照實記）**：argmax 直方圖原本以 `hist.get(int(slot))` 讀、以
`hist[str(slot)]` 寫，於是每一格都只會是 `1`（測試先抓到：`{'2': 1}` 對 `{'2': 4}`）。已改成先
`key = str(slot)` 再讀寫，與 §80 的寫法一致。這個欄位**不進**任何格子與門檻，只作描述量；修正後契約測試
30/30 綠。

### 81.3 凍結的載體與語料（跑之前寫定）

與 §80 完全同一份，**不重訓**：

| 項目 | 值 |
| --- | --- |
| 載體報告 | `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json` |
| checkpoint | `…-190357.pt`，`sha256:ba1edf16…` |
| `weights_hash` | `sha256:0ca9e593…` |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 參數 | 168,150（`hidden=128`、`emb=64`、`core="turnstore"`） |
| 語料 | 種子 **20261127**；`train_digest` `b12cb2fb…`、`heldout_digest` `71eab688…` |
| 分割 | 400 train／200 held-out sessions；**200**／**200** structures |
| 讀 | 1 次／session → **400**／**200** 次，**同一批讀套三條規則** |
| 雙生 | train **200** 對；held-out **0** |

### 81.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `ALPHA` | **0.005** | 同 §74–§80。 |
| `NULL_DRAWS` | **400** | 同 §74–§80；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | **20261125** | 同 §74–§80。 |
| `FORCED_FLOOR` | **0.5** | 二選一的 chance；不是可調的地板。 |
| `SW_MOVE_FLOOR` | **0.01** | 同 §80 的 `SW_SLOT_FLOOR`：平均 TV ≤ 1 % 視為沒移動。 |
| `ENTRY_COVERAGE` | **0.99** | 讀點上的兩筆都必須還是登記的那兩筆。 |
| `ENTRY_COSINE` | **0.999** | 同上，逐筆檢查（§80 是 1.0）。 |
| `REF_TOLERANCE` | **2e-9** | `model` 欄逐位重現 §80 質量的容差（存檔只到 9 位小數）。 |
| `ROSTER_ITEMS` | **2** | 語料固定；不是 2 就中止。 |
| `READ_BATCH` | **32** | 只影響速度；分批不跨 session。 |
| 擬合參數 | **0** | 三條規則都沒有參數；本節沒有探針訓練、沒有步數、沒有 seed。 |

與 §80 共用的常數（`ALPHA`／`NULL_DRAWS`／`NULL_SEED`／`FORCED_FLOOR`／`ENTRY_COVERAGE`／
`ENTRY_COSINE`／`ROSTER_ITEMS`）在載入 §80 模組時**逐項比對**；任何一項被改動就中止，不讓兩節偷偷用
不同的判準。

### 81.5 讀點與三條規則（跑之前寫定）

1. **store**：`run_session(..., boundaries=snapshots)` 之後的 `snapshots[q-1]`＝**證據回合之後、提問回合
   之前**的狀態（與 §80.5 同一點）。提問回合自己的寫入在讀之後，不在這次讀的 store 裡。
2. **`h`**：從該邊界出發，先 `al_step(提問回合的 gap)`，再逐 token 重放提問回合，取**最後一個 token**
   的 `h`；`query = W_q h`（`W_q` 是載體自己的，不重訓）。
3. **三條規則**（同一份 `keys`、同一個 `query`、同一個 `exp(log_read_scale)`）：

   | 規則 | logit | 拿掉什麼 |
   | --- | --- | --- |
   | `model` | `exp(scale) · k·q` | 沒有（§80） |
   | `cosine` | `exp(scale) · (k/‖k‖)·q` | key 的範數 |
   | `cosine_unit` | `(k/‖k‖)·(q/‖q‖)` | key 的範數＋query 的範數＋學到的溫度 |

   三者都是對 **16 個槽**的 softmax；計分只看 roster 那兩個槽。
4. **槽與標籤**：同 §80.5 第 4、5 點（`counter + i` → 槽 1、2；標籤取語料的 `assert`，不從問句或犯人名字
   反推）。`item` 兩槽相異、且 `seen` 必須剛好是一個 roster 顏色，否則中止。

### 81.6 主要指標與門檻

* **主要指標**：held-out 的 **two-way forced choice of attention mass**，**逐條規則各算一次**：
  `weights[correct] > weights[partner]`。chance **0.5**。
* **通過條件**（每一格都要）：Wilson 95% 下界 **> 0.5**，且置換檢定 **p < 0.005**。
* **虛無**：**打亂 held-out 的 `item` 標籤**（列置換）、**不重擬合**（讀沒有參數），在同一批質量上重算
  二選一；400 次抽樣，`p = (1 + #{null ≥ observed}) / 401`。三條規則用**同一個** `NULL_SEED`。
* **錨**：`model` 欄的 200 個 `m0`／`m1` 必須與 §80 存下來的逐位相同（2e-9），勝場數必須是 **100**。
* **描述量（不裁決）**：roster 兩槽的質量、argmax 直方圖、每條規則的 roster 質量總和；以及 81.7 的 query
  重配對。

### 81.7 機制控制 `SW` 與描述性的 query 重配對

**（a）`SW`（train 的 200 對雙生，逐條規則各算一次）**：同一對的兩次讀（16 槽）的總變差
`TV = ½·Σ|w_a − w_b|`，`SW` ＝ 200 對的平均；`moves = mean > 0.01`。`model` 的 `SW` 必須是 **0.0**
（§80 的值）——這是第二個錨：如果 `model` 欄在這裡不是 0，抽取的讀點就動了。
`SW` **沒有標籤**，不進計分格子；它只把「某條規則在 held-out 上贏」拆成「跟著名冊內容移動」與「靠標籤
平衡」兩種讀法。

**（b）query 重配對（描述量，不裁決）**：把 held-out 的 `query` 跨 session 重新配對（store 的 key 留在自
己的 session、不重擬合），同一條規則再算一次二選一。若一格的勝場**在重配對後掉到 chance**，那個贏是
「這個 session 的 query」帶來的；若**照樣贏**，那個贏不是 query 選的（例如只靠兩槽的固定差）。這一塊
**沒有門檻**，不影響分支。

### 81.8 儀器門檻 `I0`（跑完後檢查）

全部成立才讀任何一格：

1. `weights_hash` 與 checkpoint sha256 **前後相同**。
2. 報告的寫入模式是 `address="item"`、`write_strength="learned"`、`write_slots=1`。
3. 語料 digest **等於** `b12cb2fb…`／`71eab688…`（種子 20261127）。
4. **讀點稽核**：兩個分割的 coverage **≥ 0.99**，且槽 1、2 的 `v` 與 §79 同一筆 entry 的 `cos ≥ 0.999`、
   兩槽相異、非空。
5. **錨**：`model` 欄重現 §80 的 200 對質量（2e-9、0 mismatch）與勝場 **100**。

任何一項失敗 → `E0-instrument`，不讀讀數。

### 81.9 分支配表（跑之前寫定，優先序由左到右）

| 分支 | 條件 | 讀法 | `next` |
| --- | --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 載體／語料／讀點稽核／§80 錨有一項動了，什麼都不讀 | 先修儀器 |
| `N1-norm-race-is-the-limit` | `cosine` pass | 拿掉 key 範數後同一批讀就過了二選一：**鍵的方向有分開那兩筆**，是模型自己的讀輸給了一槽的範數 | 以「正規化 key 的讀」在**同預算**重訓（10,000 步、168,150 參數、同一語料），再讀 §80 的格子與 §77 的三格；不加 epoch、不加寬度、不加資料 |
| `N2-saturation-is-the-limit` | `cosine` 不過、`cosine_unit` pass | 只拿掉 key 範數不夠，連 query 範數與溫度一起拿掉才過：**比較是被飽和壓掉的**，不是沒有 | 以 cosine 讀（unit scale）同預算重訓並重讀 §80 的格子；不加預算 |
| `N3-keys-do-not-address` | 兩條都不過 | 在這個讀點上，**store 的鍵沒有分開問題需要的那一筆**：這個形狀的讀規則都不可能定址 | 登記**寫入側**的改動（key 在寫入點帶著名冊顏色），同預算；讀的規則不是缺口所在 |

`N1` 先於 `N2`：兩格都過時，較小的改動（只拿掉 key 範數）就是那個下界。

### 81.10 預測與否證（跑之前寫定）

1. **主預測是 `N1`（弱預測）**。理由：§79 量到同一筆 entry 的 `value` 帶著配對（owner **0.9350**），而
   key 與 value 是同一次 per-item 寫入寫下去的；§80 量到的唯一障礙是算術（81.2（b）），而二選一只需要
   **方向一致**，不需要大差距（81.2（c））。
2. **這個預測很弱，照實寫**：key 的**方向**從來沒被量過。§79 量的是 value，§80 只量到質量。所以
   `N3` 是實實在在的可能，不是形式上的分支。
3. **否證條件**：兩條 cosine 都不過 → `N3`。那會把 §80.20 的兩條路**收成一條**：先改寫入側，query 側
   的改動留到 key 帶了顏色之後再談。
4. **反方向的否證**：`cosine` 過 → `N1`，同時否證「鍵裡沒有可用的方向」。**不是**否證「載體會定址」——
   那是重訓之後才能問的。
5. **`model` 欄 pass 也不改變什麼**：它若 pass，就與 §80 的 100/200 矛盾，`I0`（錨）會先失敗，落在
   `E0`。
6. **pass 不是「模型會回答」**：本節完全沒有登記「讀向量 → 答案」的格子；`head` 之後的事仍是 §78 的
   缺口。

### 81.11 照實記的限制

1. **單一載體、單一語料種子（20261127）、k=2**（同 §80.11）。任何「可定址」的宣稱都只屬於這組凍結條件；
   §75 已量到幅度不跨種子複現。
2. **讀的規則是本節的，不是模型的**：pass 只說「這一組 keys 的方向分得開那兩筆」，不是「這個載體有這個
   能力」。要變成能力，得在**同預算**重訓後重讀（81.9 的 `next`）。
3. **`cosine_unit` 的質量差距天生很小**（最多 0.881 / 0.119，81.2（c））：它的 pass 門檻雖然只是嚴格
   比較，但「贏得少」意味著它**很容易被少量翻轉抹掉**；本節不把它的勝場大小當成效果量。
4. **`SW` 是 train 的機制控制**，held-out 沒有雙生；它不進計分格子，也不能單獨支持「模型會定址」。
5. **query 重配對沒有門檻**（81.7（b））：它是描述量，用來讀「贏是不是 query 帶來的」，不裁決。
6. **三條規則共用同一批讀**：這讓它們的比較乾淨（同樣的 store、同樣的 `h`），但也意味著它們**不是**三個
   獨立實驗；`N1` 與 `N2` 的差別只在「還要拿掉多少」。
7. **這是探針，不是生成**：核心分不變 **0.00/10**；本節是診斷，不是能力分數，也不是新的分數來源。
8. **輸出只寫 `data/pantry_stage/readrule81/`**（gitignored），不寫任何被量測的環境。

### 81.12 命令與執行上限

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=2 \
  systemd-run --scope --user -p CPUQuota=200% -p MemoryMax=4096M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/probe_pantry_readrule81.py \
    --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --anchor data/pantry_stage/address80/k2.json \
    --out data/pantry_stage/readrule81/k2.json --device cpu

./.venv/bin/python scripts/probe_pantry_readrule81.py --check data/pantry_stage/readrule81/k2.json
```

上限沿用本專案的硬規則：**CPU 200%（兩核）／RAM 4 GiB／swap 0／GPU 不使用（`--device cpu`）**，低於
50%／60%／60% 的門檻；起跑前用 `/proc/stat` 量整機負載，超過就照 §80.13 的先例降到 `CPUQuota=<剩餘>`、
`OMP_NUM_THREADS=1`，並照實記在 81.13。本節的計分跑比 §80 多的是 **三倍讀數的整流與 400 次置換**（置換
**不重擬合**，只重算二選一；`cosine_unit` 的置換是純 float 比較），以及一次 train 的 400 次讀。

這一節在**計分跑之前**寫定。任何跑之前的改動都會以 amendment 記在 81.13 之前；被丟棄的跑法照實記。

### 81.13 執行（照實記）

* 登記的指令**原樣**執行：`CPUQuota=200%`、`MemoryMax=4096M`、`MemorySwapMax=0`、`OMP_NUM_THREADS=2`、
  `--device cpu`。**沒有 amendment**：起跑前整機（`/proc/stat`，8 秒窗）是 **25 %**，登記的 200 %（兩核，
  12 核機器的 **16.7 %**）加上去仍在 50 % 的硬上限內。
* 跑的時候整機 **25 %**（同一個 8 秒窗；含本工作自己的 180 %≈1.8 核），峰值 RSS **532,316 kB ≈ 520 MiB**
  （上限 4 GiB）、**swap 0**（`MemorySwapMax=0`）；wall **25.50 s**、user 45.75 s、sys 0.31 s。儀器欄位來自
  同一條命令的一次**重跑**（輸出到 `/tmp`，不進版控）：計分跑本身只花 **25.39 s**，在第一個 8 秒整機取樣窗
  結束前就結束了，所以「跑的時候整機多少」是用重跑量的。重跑的三條規則的 `m0`／`m1`／`items`／勝場與
  `SW` 平均**逐位相同**（9 位小數），分支相同 → 這次讀**沒有隨機性**，重跑不是第二次量測。
* **沒有被丟棄的跑法**：第一次執行就是登記的讀數。輸出只寫 `data/pantry_stage/readrule81/k2.json`
  （gitignored）。`--check` **OK**。
* 一個警告照實記：`float(weights[slot])` 在 `no_grad` 之外的張量上會印 `requires_grad=True` 的
  `UserWarning`；它只影響是否留 autograd 圖，不影響取到的數值（重跑逐位相同）。

### 81.14 儀器 `I0`（全過）

| 條款 | 值 |
| --- | --- |
| `weights_hash` 前後 | 相同（`sha256:0ca9e593…`） |
| checkpoint sha256 前後 | 相同（`sha256:ba1edf16…`） |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 語料 digest | `b12cb2fb…`／`71eab688…`（種子 20261127） |
| 讀點稽核 | coverage **1.0**（train 400/400、held-out 200/200） |
| 錨（`model`） | 200 對質量最大絕對差 **0.0**、mismatch **0**、勝場 **100**（＝§80 的 100） |

`model` 欄與 §80 逐位相同，而且它的雙生 `SW` 也是 **0.0**（§80 的 0.0）：抽取的讀點沒有動。

### 81.15 主要讀數（held-out 200 次讀，逐條規則）：**三條都不過**

| 規則 | 勝出 | forced | Wilson 95% | 置換虛無 | p | roster 兩槽質量 mean（min–max） | argmax |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `model` | **100/200** | 0.5000 | 0.4314–0.5686 | 400/400 ≥ 觀察（100.0 ± 0.0） | **1.0** | **1.0000**（1.0–1.0） | 槽 2，**200/200** |
| `cosine` | **100/200** | 0.5000 | 0.4314–0.5686 | 400/400（100.0 ± 0.0） | **1.0** | **0.9992**（0.9064–1.0） | 槽 2，**200/200** |
| `cosine_unit` | **100/200** | 0.5000 | 0.4314–0.5686 | 400/400（100.0 ± 0.0） | **1.0** | **0.1785**（0.1288–0.2215） | 槽 2，**200/200** |

三條規則的勝場**都是 100**、虛無分佈**都是 100 恆定**（sd 0.0）、p **都是 1.0**——和 §80 一模一樣。差別只在
質量：

* `cosine` 拿掉 key 範數之後**還是飽和**：roster 兩槽的質量 mean **0.9992**（單次最低 0.9064）。算術上
  合理：`exp(scale)·‖q‖ ≈ 4 × 17.8 = 71`，只要兩槽的餘弦差超過 ~0.1 就會回到 1.0／0.0 的邊界。
* `cosine_unit`（純餘弦，沒有範數、沒有溫度）**終於把質量分開**：roster 兩槽合計 mean **0.1785**，也就
  是單次讀名冊兩槽各拿 **0.16／0.02** 左右，**不是**飽和——但 **argmax 還是槽 2，200/200**，槽 1 一次都
  沒贏過。

所以：**把範數與溫度全部拿掉之後，讀在每一 session 都還是偏好槽 2**，不管槽 2 放的是哪一個顏色、而
「需要的那一筆」在槽 1 還是槽 2。二選一因此剛好等於標籤的平衡（100/200），虛無一次都沒被超過。

### 81.16 機制控制 `SW`（train 的 200 對雙生，逐條規則）

| 規則 | 平均 TV | sd | min | median | p95 | max | TV = 0 的對 | TV > 0.01 的對 | `moves` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `model` | **0.0** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 200/200 | 0/200 | `False` |
| `cosine` | **0.0112** | 0.0809 | 0.0 | 0.0 | 0.0068 | 0.8368 | 122/200 | **8/200** | `True`（名目） |
| `cosine_unit` | **0.0209** | 0.0126 | 0.0012 | 0.0196 | 0.0454 | 0.0585 | 0/200 | **154/200** | `True` |

三個讀法分得很清楚：`model` 一格都不動；`cosine` 幾乎不動（122 對**剛好 0**，只有 8 對超過 0.01，其中 3 對
是 0.23／0.73／0.84 的大值，把平均從 0 拉到 0.0112）；`cosine_unit` **每一對都動一點**（中位數 0.0196）。

但**動不等於指對**：`cosine_unit` 在雙生上每一對都動，二選一卻仍然是 **100/200**（上面 81.15）。所以那點
移動是「store 換了、讀的分布也跟著換了一點」，不是「跟著需要的那一筆換」。這也是 81.7（a）把 `moves`
寫成**必要不充分**的原因——它在 `cosine_unit` 上 `True`，而那個格子仍然不過。

### 81.17 描述量（不裁決）

* **query 重配對**（`query` 跨 session 換掉、store 不動）：三條規則都是 **100/200**、`#{null ≥ 觀察}`
  **400/400**、p **1.0**。贏場數與「這個 session 的 query」無關——因為**根本沒有贏場數**。
* `argmax` 在 16 槽上的直方圖：三條規則都是 `{"2": 200}`。
* 讀點上的 roster 兩槽都在（coverage 1.0，81.14），所以「槽 2 贏」不是因為槽 1 空著。

### 81.18 分支與預測檢查

* 機械分支：**`N3-keys-do-not-address`**（`I0` 過、`cosine` 不過、`cosine_unit` 也不過；81.9 的優先序）。
* **登記的主預測（81.10 第 1 點：`N1`）落空**，照實記。登記時就標成「弱預測」，理由也寫了：key 的
  **方向**從來沒被量過，§79 量的是 value。實際量到的是反方向：方向**有**，但它不隨顏色走。
* **登記的否證條件（81.10 第 3 點）命中**：兩條 cosine 都不過 → `N3`。
* `N2` 也沒有發生（`cosine_unit` 不過），所以「只差一個溫度」也不是這個缺口的形狀。
* **這一節改變了什麼**：§80.20 的兩條路原本是並列的可能；本節把「改讀的算術」這條**關掉**——在凍結的
  store 與凍結的 query 上，換讀的規則是徒勞的。剩下的缺口在**寫進去的內容**（key 的方向）與**問句帶出來
  的內容**（query 的方向）之間；本節的設計**不能**把這兩邊分開（81.19 第 1 點），所以下一節先量這件事，
  不直接改寫入。

### 81.19 照實記的限制

1. **這一節不能分離「鍵沒有顏色」與「query 沒有顏色」**。雙生只對調名冊順序：需要的那一筆換了槽，但
   **問句逐字相同**、store 的 key 內容也對調。若 query 幾乎不隨顏色變、而 key 有顏色，讀照樣會固定偏好
   槽 2（因為槽 2 的 key 就是比較對得上同一個 query），二選一照樣是 100/200。`cosine_unit` 的雙生 TV
   0.0209 證明 query 不是常數，但**沒有**證明它跟著顏色。所以 `N3` 的正式讀法只能到「**這個形狀的讀規則
   在這批凍結的 keys 上定址不了**」，不能讀成「寫入側就是唯一的缺口」。§80.2（d）的 `h → 證據顏色`
   （**0.105**，低於 chance 0.125）是這個模糊的來源，不是它的解答。
2. 單一載體、單一語料種子（20261127）、k=2（同 §80.11）；§75 已量到幅度不跨語料種子複現。
3. **讀的規則是本節的**：`N3` 是對三條**登記過的**規則說的，不是「所有可能的讀都失敗」。沒有測過
   「換一個 key 投影」或「學一個新的讀」——那需要重訓，屬於下一節。
4. `cosine` 這一格**不能**當成「方向」的乾淨檢定：它還是飽和（0.9992），所以它與 `model` 幾乎是同一格；
   真正把方向顯露出來的是 `cosine_unit`。
5. `cosine_unit` 的質量差距天生小（最多 0.881／0.119，81.2（c）），本節只把它當**嚴格比較**用，不把勝場
   大小當效果量。
6. `SW` 是 train 的機制控制，held-out 沒有雙生；`moves=True` 在 `cosine_unit` 上成立而格子不過，正是
   81.7（a）寫的「必要不充分」。
7. **這是探針，不是生成**：核心分不變 **0.00/10**；本節是診斷，不新增也不改變任何分數來源。
8. 執行用登記的 200 % quota；整機全程 25 %（< 50 %），峰值 RSS 520 MiB（< 4 GiB），swap 0。

### 81.20 下一個登記（本節只寫問題，不選修法）

`N3` 的 `next`（81.9）是寫入側，但 81.19 第 1 點說本節**不能**把缺口定位在寫入側。所以在改寫入之前，
先量**兩邊各自的內容**——同一個凍結載體、同一個讀點、不重訓、不換讀規則：

1. **key → 顏色**（同一 session 內二選一）：rank 到 2、只用 train 的 800 筆 entry 擬合、留出 400 筆計分
   （與 §79 同一個探針與同一個分割慣例，只是把輸入從 `v` 換成 `k`）。若這一格是 chance，key 的方向真的
   不帶顏色，寫入側就是缺口；若它過，缺口在 query 側。
2. **query → 需要的顏色**（8 路與名冊二選一）：同一支 5 折線性探針（2,000 步、`PROBE_SEED` 20261121），
   輸入換成 `query = W_q h`。§80.2（d）在 `h` 上是 **0.105**（低於 chance），這一格量的是「經過 `W_q` 之後
   還在不在」。
3. 只有 1 過而 2 不過，才是「加一個說出顏色的 query」的證據；只有 2 過而 1 不過，才是「讓 key 帶顏色」的
   證據；兩個都不過 → 顏色在提問回合**兩邊都沒有**，那要回頭改的是證據回合的寫入，不是讀也不是 query。

門檻、分割與常數由下一節自己登記（本節不先寫死，也不在這一節的結果上調任何參數）。

## §82 缺的顏色在鍵那側、query 那側，還是兩邊都沒有？

### 82.1 這一節問什麼

§81 把兩條可能的算術原因（鍵的範數、學到的溫度）都拿掉，讀**仍然是 100/200**：held-out 200 次的二選一
剛好等於標籤的平衡，400 次標籤置換一次都沒被超過，`cosine_unit` 的 argmax 還是槽 2、**200/200**。所以
「這個形狀的讀規則定址不了這批凍結的鍵」是量到的，不是推論的。

但 §81.19 第 1 點寫得很清楚：**那個設計不能分離「鍵沒有顏色」與「query 沒有顏色」**。雙生只對調名冊的
順序——需要的那一筆換到另一個槽，但問句**逐字相同**、store 的鍵內容也對調——所以兩種缺法都會產生同一個
100/200。§80.20 的兩條修法（寫入側讓 key 帶顏色；query 側直接說出顏色）因此**仍是並列的可能**。

本節只做一件事：**用同一批凍結的載體、同一個讀點、不重訓、不換讀規則**，把兩邊的內容各自量一次，並
順帶量一個**零擬合參數**的修法候選（用邊界狀態的 query 去讀）：

| 格子 | 輸入 | 標籤 | 擬合參數 |
| --- | --- | --- | --- |
| `entry_key` | 讀點上那筆 entry 的**鍵** `k` | 它自己的名冊顏色（對照同 session 另一筆的顏色） | 一個線性探針 |
| `entry_value` | 同一筆 entry 的**值** `v` | 同上（**錨**：§79 的 0.6200／248） | 一個線性探針 |
| `query` | 提問回合最後一個 token 的 `W_q h` | 這次讀**需要**的顏色（＝證據回合的顏色；對照同 session 另一筆的顏色） | 一個線性探針 |
| `boundary_query` | 邊界狀態的 `W_q h_b`（提問回合**之前**那一刻） | 同上（用 §81 的 forced choice 計分） | **0** |

判讀是窄的：若 `entry_key` 過而 `query` 不過，顏色在鍵裡、不在提問回合的 query 裡——**換讀的規則不會
有幫助**，該改的是 query 從哪裡來。若兩邊都過而 `boundary_query` 不過，資訊都在、是讀自己的投影限制。
若 `entry_key` 不過，寫入側就真的是缺口。若 `boundary_query` 過，那麼缺口只在**提問回合的讀點**，而不在
store 或 query 投影——那是一個不需要新參數的修法方向。

**本節不是能力分數**：核心分不變 **0.00/10**（§275）；這裡全部是診斷。

### 82.2 登記前已經量到的（照實寫）

**（a）§79 的凍結格子**（`data/pantry_stage/pair79/k2.json`，不改寫、不重跑）。同一支 8 路線性探針
（2,000 步、batch 64、lr 1e-3、wd 1e-4、seed 20261121），**只用 train 的 800 筆 entry 擬合、留出 400 筆
計分**，指標是同 session 兩筆之間的二選一（自己的標籤 vs 另一筆的標籤）：

| 特徵 | 目標 | 二選一 | Wilson 95% | 8 路 top-1 | p |
| --- | --- | --- | --- | --- | --- |
| `k` | 顏色 | **0.7375**（295/400） | 0.6923–0.7782 | 0.4175 | 0.002494 |
| `v` | 顏色 | **0.6200**（248/400） | 0.5715–0.6662 | 0.2025 | 0.002494 |
| `h` | 顏色 | 0.8375 | 0.7982–0.8704 | 0.6650 | 0.002494 |
| `k`／`v`／`h` | 位置 | 1.0／1.0／1.0 | — | — | — |

虛無（400 次打亂標籤、**每次重擬合**）的平均都在 0.49–0.50。也就是說：**鍵裡有顏色，而且線性可讀**，
只是比 value 弱一點。這是本節把 `entry_key` 當成「寫入側有沒有顏色」的檢定的理由，也是它與 §81 的
「讀定址不了」不矛盾的地方——**可分離 ≠ 被讀出來**。

**（b）§80.2（d）的 query 缺口**：在提問回合的 `h` 上，`h → 證據顏色` 的 8 路 top-1 是 **0.105**，
**低於** chance 0.125。這是 §82 主預測的方向，但它量的是 `h`，不是 `W_q h`；本節的 `query` 格子量的是
「經過載體自己的投影之後還在不在」。

**（c）§69 的邊界讀數**：顏色在**證據邊界**可讀 **0.8900／0.9950**（兩個指標），到**答案邊界**掉到
**0.1400／0.1100**。這是 `boundary_query` 這格存在的理由：如果顏色在邊界還在，而讀點在提問回合之後，那麼
「把 query 換成邊界那一刻的」就是一個**不用新參數**的候選修法。

**（d）§81 的 N3**：三條讀規則都是 100/200、p 1.0、虛無 400/400；`cosine_unit` 終於把質量分開
（名冊兩槽合計 mean 0.1785、min 0.1288），**argmax 仍是槽 2、200/200**。

**（e）跑之前沒有量過**：`entry_key`、`query`、`boundary_query` 三格在這批 session 上的結果。契約測試
（`tests/test_pantry_readrule82.py`，30 條）只用合成張量與合成報告釘住算術、門檻形狀、分支優先序與
`--check` 的拒絕條件，**不含任何載體資料、不產生讀數**。

> **amendment（跑後補記，82.13 之前）**：這段寫定之後、計分跑之前，做了一次 `--null-draws 2` 的**儀器
> 預跑**（輸出到 `/tmp`、不進版控），它會印出三格的**觀察值**（不含任何可裁決的虛無與 p）。照實補記在這裡，
> 免得讀者以為計分跑是對這三格全盲的：預跑看到 `entry_key` 0.7375、`query` 0.5450、`boundary` 0.5000／
> 0.5050。**在預跑之後沒有改動任何常數、格子、門檻、分割或虛無慣例**；可裁決的部分（400 次重擬合虛無、
> p、Wilson 門檻、分支）都只來自 82.13 的那一次計分跑。

### 82.3 凍結的載體與語料（跑之前寫定）

與 §79／§80／§81 完全同一份，**不重訓**：

| 項目 | 值 |
| --- | --- |
| 載體報告 | `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json` |
| checkpoint | `…-190357.pt`，`sha256:ba1edf16…` |
| `weights_hash` | `sha256:0ca9e593…` |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 參數 | 168,150（`hidden=128`、`emb=64`、`core="turnstore"`） |
| 語料 | 種子 **20261127**；`train_digest` `b12cb2fb…`、`heldout_digest` `71eab688…` |
| 分割 | 400 train／200 held-out sessions；entry 800／400 筆；讀 400／200 次 |
| 雙生 | train **200** 對；held-out **0** |
| 名冊 | k=2、8 個顏色、12 個名字 |

`k` 不是 2、種子缺失、digest 不符、或報告不是 minimal-binding 語料 → 直接中止，不讀。

### 82.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `ALPHA` | **0.005** | 同 §74–§81。 |
| `NULL_DRAWS` | **400** | 同 §74–§81；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | **20261125** | 同 §74–§81。 |
| `FORCED_FLOOR` | **0.5** | 二選一的 chance；不是可調的地板。 |
| `ENTRY_COVERAGE` | **0.99** | 讀點上的兩筆都必須還是登記的那兩筆。 |
| `ENTRY_COSINE` | **0.999** | 同上，逐筆檢查。 |
| `REF_TOLERANCE` | **2e-9** | §81 質量錨的逐位容差。 |
| `ROSTER_ITEMS` | **2** | 語料固定。 |
| `READ_BATCH` | **32** | 只影響速度；分批不跨 session。 |
| 探針 | 2,000 步／batch 64／lr 1e-3／wd 1e-4／seed **20261121** | **與 §79 逐項相同**（載入 §79 模組時逐項比對，任一項不同就中止）。 |
| 錨 | §79 `v`→顏色 **0.6200／248**（n=400）；§81 `model` 勝場 **100** | 兩個都必須重現，否則 `E0-instrument`。 |

### 82.5 讀點與四個格子（跑之前寫定）

1. **store**：`run_session(..., boundaries=snapshots)` 之後的 `snapshots[q-1]`＝證據回合之後、提問回合
   之前的狀態（與 §80.5／§81.5 同一點）。
2. **`h`／`query`**：從該邊界 `al_step(提問回合的 gap)`，逐 token 重放提問回合，取最後一個 token 的
   `h`；`query = W_q h`。
3. **`query_boundary`**：`W_q · (snapshots[q-1].h)`——**同一個投影**，只是作用在提問回合之前那一刻的狀態。
4. **entry 兩格**：§79 的 `entry_records` 原樣沿用（寫入點的 `k`／`v` 由 store 取出，不是重算的），
   標籤取語料的 `assert`；`item` 兩槽相異、且 `seen` 必須剛好是一個名冊顏色，否則中止。
5. **分割慣例**（與 §79 相同，跑之前寫定）：三支探針都**只在 train 上擬合**（entry 800 筆、讀 400 次），
   **在 held-out 上計分**（entry 400 筆、讀 200 次）；chance 0.5（同 session 兩筆的顏色必不相同）。
6. **`boundary_query`**：輸入換成 `query_boundary`，其餘（store、槽、標籤、`exp(log_read_scale)`）不變，
   套 §81 的 `address_block`，只跑登記的兩條規則（`model`、`cosine_unit`）。

### 82.6 主要指標與門檻

* **擬合格子**（`entry_key`、`query`）：held-out 的 **two-way forced choice**；通過條件＝Wilson 95% 下界
  **> 0.5** 且置換檢定 **p < 0.005**。虛無＝**打亂標籤並重新擬合**（每次抽樣重擬合，400 次，§79 慣例）。
  `query` 另外報 **8 路 top-1** 作描述量（chance 0.125），**不裁決**。
* **未擬合格子**（`boundary_query` 的兩條規則）：同樣的二選一、同樣的 Wilson 與 p 門檻；虛無＝**只打亂
  `item` 標籤、不重擬合**（讀沒有參數，§80／§81 慣例）。
* **錨**：`entry_value` 必須重現 §79 的 **0.6200（248/400）**（forced、勝場、n 三項都對）；§81 的
  `model` 質量必須逐位重現（2e-9、mismatch 0、勝場 **100**）。
* **描述量（不裁決）**：`argmax` 直方圖、名冊兩槽質量、`entry_key`／`query` 的 8 路 top-1。

### 82.7 為什麼兩類格子用不同的虛無

擬合格子有參數：若虛無只打亂標籤而不重擬合，探針會把「這次打亂的標籤」記進權重，虛無會偏樂觀。§79
因此每次抽樣都重擬合（400 次）。`boundary_query` 沒有參數可記，打亂標籤就是唯一的不變量，重擬合不存在
（§80／§81 同）。兩種慣例都寫在 `probe`／`reads` 欄裡，`--check` 會逐格重算 p 的公式。

### 82.8 儀器門檻 `I0`（跑完後檢查）

全部成立才讀任何一格：

1. `weights_hash` 與 checkpoint sha256 **前後相同**。
2. 報告的寫入模式是 `address="item"`、`write_strength="learned"`、`write_slots=1`。
3. 語料 digest **等於** `b12cb2fb…`／`71eab688…`（種子 20261127）。
4. **entry 稽核**：兩個分割的 coverage **≥ 0.99**，逐筆 `cos_v`／`cos_k` ≥ 0.999、兩槽相異、非空。
5. **讀點稽核**：兩個分割的 coverage **≥ 0.99**，槽 1、2 的 `v` 與 §79 同一筆 entry 的 `cos ≥ 0.999`。
6. **對齊**：名冊文字逐項含著對應的顏色字與人名（§79 的 `alignment`）。
7. **兩個錨**：§79 的 `v`→顏色 0.6200／248、§81 的 `model` 質量與 **100** 勝場。

任何一項失敗 → `E0-instrument`，不讀任何一格。

### 82.9 分支配表（跑之前寫定，優先序由上到下）

| 分支 | 條件 | 讀法 | `next` |
| --- | --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 載體／語料／讀點稽核／任一錨動了，什麼都不讀 | 先修儀器 |
| `C1-state-addresses` | `boundary_query` 在**任一條**登記規則上 pass | 顏色**在邊界狀態裡**，而且那時的 query 就能用存下來的鍵**定址**到需要的那一筆：缺的不是內容，是**提問回合的讀點** | 以「邊界 query 的讀」在**同預算**重訓（10,000 步、168,150 參數、同一語料；不加 epoch、不加寬度、不加資料），再讀 §80 的格子與 §81 的三欄 |
| `C4-write-side-keys-lack-colour` | `entry_key` 不過 | 存下來的鍵**沒有**帶名冊顏色（同 session 二選一），所以任何 query 都定址不了它：資訊在**寫入側**就缺了 | 登記寫入側的改動（鍵在寫入點帶名冊顏色），同預算，再讀 §80 的格子 |
| `C2-both-sides-carry-colour` | `entry_key` 過且 `query` 過 | 兩邊都帶顏色，而邊界 query 反而定址不了：剩下的是**讀自己的投影／幾何**，不是資訊 | 登記一個用得到可讀方向的讀（同樣的鍵與 query 上學一個度量），同預算，再讀 §80 的格子 |
| `C3-query-missing` | `entry_key` 過、`query` 不過、邊界也不過 | 鍵有顏色、**提問回合的 query 沒有**、邊界 query 也定址不了：顏色從未進到讀的 query，換任何讀的規則都不會被它引導 | 改**query 從哪裡來**，讓它看得到證據顏色（攜帶它的是邊界狀態，§69 的 0.8900），同預算；鍵與讀的算術已被排除 |

`C1` 先於其他三支：它是唯一一個「不新增參數就能修」的結果。

### 82.10 預測與否證（跑之前寫定）

1. **主預測是 `C3`，信心低，照實寫。** 理由：§79 把顏色放進鍵（`k` 0.7375，Wilson 下界 0.6923）；
   §80.2（d）把顏色放在提問回合的 `h` 之外（0.105，低於 chance）。這兩件事合起來就是 C3 的形狀。
2. **登記的替代是 `C1`**：§69 在證據邊界讀到 0.8900／0.9950，而邊界 query 只要方向和鍵一致就能贏
   （§81.2（c）：二選一是嚴格比較，不需要大差距）。若 C1 成立，主預測落空，而且它會比 C3 更有用（零參數）。
3. **否證條件**：`entry_key` 不過 → `C4`，主預測與替代都落空，缺口在寫入側。兩邊都過而邊界不過 → `C2`。
4. **`query` 的 8 路 top-1 不是門檻**：它可能高於 0.125 而二選一仍不過（探針學到的是顏色本身，不是
   「哪一筆需要它」），照實報，不改門檻。
5. **pass 不是「模型會回答」**：本節沒有「讀向量 → 答案」的格子；`head` 之後仍是 §78 的缺口。
6. **不會因為結果改門檻**：`ALPHA`、虛無次數、Wilson 地板、分割慣例都在 §82.4／82.6 寫定；任何改動都會
   以 amendment 記在 82.13 之前。

### 82.11 照實記的限制

1. **線性探針可讀 ≠ 只有這些資訊**：`entry_key` 不過只說「rank-2 的線性讀不到顏色」，不是「鍵裡沒有
   任何顏色編碼」。這裡的探針與 §79 同一支，是為了讓 `entry_value` 能當錨。
2. **單一載體、單一語料種子（20261127）、k=2**（同 §79–§81）；§75 已量到幅度不跨種子複現。
3. **`boundary_query` 繼承 §81 的規則形狀**：`C1` 是「在這兩條登記規則下可定址」，不是「所有讀都可定址」。
4. **`query` 格子只有一個 token 的狀態**：`W_q` 是載體自己的投影，本節不換投影、不重訓；「換一個 query
   投影就會帶顏色」是重訓之後才能問的。
5. **`entry_key` 與 `entry_value` 的分數不是效果量**：兩者都是同一支探針的 forced choice，只拿來定位缺口。
6. **探針格子每次虛無都重擬合**（400 次），所以單格約 150–190 s；本節兩個擬合格子加上兩次語料重放，
   預期 400–600 s，**比 §81 貴**。
7. **這是探針，不是生成**：核心分不變 **0.00/10**；本節不新增也不改變任何分數來源。
8. **輸出只寫 `data/pantry_stage/readrule82/`**（gitignored）。

### 82.12 命令與執行上限

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=2 \
  systemd-run --scope --user -p CPUQuota=200% -p MemoryMax=4096M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/probe_pantry_readrule82.py \
    --report data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --anchor79 data/pantry_stage/pair79/k2.json \
    --anchor81 data/pantry_stage/readrule81/k2.json \
    --out data/pantry_stage/readrule82/k2.json --device cpu

./.venv/bin/python scripts/probe_pantry_readrule82.py --check data/pantry_stage/readrule82/k2.json
```

上限沿用硬規則：**CPU 200%（兩核＝整機 16.7%）／RAM 4 GiB／swap 0／GPU 不使用（`--device cpu`）**，
低於 50%／60%／60%；起跑前用 `/proc/stat` 量整機負載，超過就照 §80.13 的先例降到 `CPUQuota=<剩餘>`、
`OMP_NUM_THREADS=1`，並照實記在 82.13。

**儀器預跑（不是計分跑，照實記）**：`--null-draws 2` 的一次性 harness 檢查（輸出到 `/tmp`，不進版控、
26.0 s）確認四件事：兩個錨**逐位重現**（§79 `v`→顏色 0.6200／248/400、§81 `model` 質量 max abs diff
**0.0**、勝場 **100**）、entry／讀點稽核 coverage 都是 1.0、`entry_key` 的 forced 是 **0.7375**（＝§79 的
`k` 格子）、`entry_value` 的 forced 是 **0.6200**。它印出的分支**不能**當讀數：2 次抽樣下 p 的下限是
1/3，任何格子都不可能低於 0.005，所以那次一定落在 `C4`（`entry_key` 因 p 不過）。**這個預跑之後沒有
改動任何常數、格子、門檻或分割**；本節的登記（四格、兩個虛無慣例、五分支優先序、主預測 `C3`、替代
`C1`）在預跑之前就已經寫在 `scripts/probe_pantry_readrule82.py` 的常數裡。

這一節在**計分跑之前**寫定。任何跑之前的改動都會以 amendment 記在 82.13 之前；被丟棄的跑法照實記。

### 82.13 執行（照實記）

* 登記的指令**原樣**執行：`CPUQuota=200%`、`MemoryMax=4096M`、`MemorySwapMax=0`、`OMP_NUM_THREADS=2`、
  `--device cpu`。**沒有 amendment**：起跑前整機（`/proc/stat`，8 秒窗）是 **18.0 %**，加上登記的兩核
  （12 核機器的 **16.7 %**）仍在 50 % 的硬上限內。
* 量到的成本：**wall 5:40.43**（腳本自己的計時 **339.933 s**，差額是直譯器啟動）、CPU **199 %**、
  峰值 RSS **728,920 kB ≈ 712 MiB**（上限 4 GiB）、**swap 0**（`MemorySwapMax=0`）、user 675.69 s／sys 2.15 s。
* **沒有被丟棄的計分跑**：第一次就是登記的讀數。輸出只寫 `data/pantry_stage/readrule82/k2.json`
  （gitignored）。`--check` **OK**（p 的公式、勝場可重算、五個分支可重導、兩個錨）。
* 一個警告照實記（與 §81 同一個）：`float(weights[slot])` 在 `no_grad` 之外的張量上會印
  `requires_grad=True` 的 `UserWarning`；取到的數值不受影響（錨逐位相符就是證據）。
* 82.12 的 **2-draw 儀器預跑**照實記在登記裡：它**不是**計分跑（2 次抽樣下 p 的下限 1/3，任何格子都
  不可能低於 0.005），只證明管路與兩個錨可重現；預跑之後沒有改任何常數。

### 82.14 儀器 `I0`（全過）

| 條款 | 值 |
| --- | --- |
| `weights_hash` 前後 | 相同（`sha256:0ca9e593…`） |
| checkpoint sha256 前後 | 相同（`sha256:ba1edf16…`） |
| 寫入模式 | `address="item"`、`write_strength="learned"`、`write_slots=1` |
| 語料 digest | `b12cb2fb…`／`71eab688…`（種子 20261127） |
| entry 稽核 | coverage **1.0**／**1.0**（train 800 筆、held-out 400 筆） |
| 讀點稽核 | coverage **1.0**／**1.0**（train 400 次、held-out 200 次） |
| 對齊 | train／held-out 都過（名冊文字含對應顏色字與人名） |
| 錨 §79 | `v`→顏色 **0.6200／248／400**，逐項重現（forced、勝場、n） |
| 錨 §81 | `model` 質量 max abs diff **0.0**、mismatch **0**、勝場 **100** |

兩個錨都逐位重現，所以抽取的讀點與 §79／§81 是同一個；`entry_key` 的分數因此可以直接與 §79 的 `k` 格
比較。

### 82.15 四個格子（held-out 計分）

| 格子 | 勝出 | forced | Wilson 95% | p | top-1（chance） | 裁決 |
| --- | --- | --- | --- | --- | --- | --- |
| `entry_key` | **295/400** | **0.7375** | 0.6923–0.7782 | **0.002494** | 0.4175（0.1250） | **PASS** |
| `entry_value`（錨） | **248/400** | **0.6200** | 0.5715–0.6662 | —（§79 的格子） | 0.2025（0.1250） | 錨，不裁決 |
| `query` | **109/200** | **0.5450** | 0.4758–0.6125 | **0.069825** | 0.1550（0.1250） | **FAIL** |
| `boundary_query` `model` | **100/200** | **0.5000** | 0.4314–0.5686 | **1.0** | — | **FAIL** |
| `boundary_query` `cosine_unit` | **101/200** | **0.5050** | 0.4363–0.5735 | **0.551122** | — | **FAIL** |

`entry_key` 與 §79 的 `k`→顏色**逐項相同**（0.7375、295/400、Wilson 0.6923–0.7782、top1 0.4175、
p 0.002494、虛無平均 0.497106、`ge` 0）——同一個探針、同一個分割、同一個種子，換的只有輸入（`k` 而不是
`v`）。`entry_value` 也重現 §79 的 0.6200／248/400。這兩個「相同」是儀器的第三個錨。

### 82.16 `query` 那一格：有痕跡，但不是可用的量

登記的門檻是「Wilson 下界 > 0.5 且 p < 0.005」，`query` **兩項都不過**：Wilson 下界 **0.4758**，
p **0.069825**（400 次重擬合的虛無裡有 27 次 ≥ 觀察值，虛無平均 0.497275）。

照實記它**不是零**：點估計 **0.5450**（109/200）比 chance 高 4.5 個百分點，8 路 top-1 **0.1550** 也高於
chance 0.1250——比 §80.2（d）在 `h` 上量到的 0.1050 好，但**遠低於** §79 在鍵上量到的 0.7375。所以正式讀法
是「提問回合的 `W_q h` 帶著一點顏色方向，但**不足以**通過任何登記的門檻」，不是「query 完全沒有顏色」。
這一格**不能**因為點估計 > 0.5 就改判 pass：Wilson 下界與 p 在跑之前就寫定（82.6）。

### 82.17 `boundary_query`：把 query 移到邊界，讀還是不選

| 規則 | 勝出 | forced | p | 名冊兩槽質量 mean（min–max） | argmax |
| --- | --- | --- | --- | --- | --- |
| `model` | **100/200** | 0.5000 | **1.0**（虛無 400 次全部 100） | **1.0000**（1.0–1.0） | 槽 2，**200/200** |
| `cosine_unit` | **101/200** | 0.5050 | **0.551122** | **0.180198**（0.1350–0.2280） | 槽 2，**199/200**（槽 1 一次） |

兩條規則的讀數幾乎與 §81 的提問回合版本**一模一樣**：§81 的 `cosine_unit` 質量 mean **0.1785**、argmax
槽 2 **200/200**，這裡是 **0.180198**／**199/200**。也就是說：**把 query 換成「提問回合之前那一刻」的
`W_q h`，讀看到的名冊內容沒有變**——顏色在邊界狀態裡（§69 的 0.8900），但載體自己的 `W_q` 沒有把它投影成
一個能定址這些鍵的方向。

這一格是**零擬合參數**的候選修法，它失敗了，所以 `C1` 的「免費版本」被否證：**光把讀點往前移不夠**，
必須讓那個投影**被訓練**去帶顏色。

### 82.18 分支與預測檢查

* 機械分支：**`C3-query-missing`**（`I0` 過；`boundary_query` 兩條規則都不過；`entry_key` 過；
  `query` 不過；82.9 的優先序）。
* **登記的主預測 `C3` 命中**（登記時標成**低信心**，替代寫的是 `C1`）。替代 `C1` 沒有發生：零參數的邊界
  query 是 0.5050。
* `C4` 沒有發生：鍵真的帶著顏色（0.7375，與 §79 逐項相同），所以「寫入側缺資訊」被否證。
* `C2` 沒有發生：query 的點估計雖高於 chance，但登記的兩道門都沒過，所以不能稱「兩邊都帶顏色」。
* **這一節把 §81 的模糊拆開了**：§81 只能說「這個形狀的讀規則定址不了」，本節說**鍵有顏色、提問回合的
  query 幾乎沒有**——缺口在 query 側，不在寫入側。§80.20 的兩條修法因此**收成一條**：改 query 的來源，
  不是改寫入的內容。

### 82.19 照實記的限制

1. **`query` 的失敗是「不夠」，不是「沒有」**（82.16）：點估計 0.5450、8 路 0.1550 都在 chance 之上。
   任何「query 完全沒有顏色」的措辭都超過這一節量到的東西。
2. **線性探針可讀 ≠ 只有這些資訊**：`entry_key` 的 PASS 只說「存在一個線性方向讀得到顏色」；
   它沒有量「鍵裡還有什麼」，也沒有量非線性可讀性。
3. **`boundary_query` 繼承 §81 的兩條規則**：`C1` 的否證是「在這兩條登記規則下不可定址」，不是「所有讀都
   不行」。但註冊的 `cosine_unit` 已經把範數與溫度都拿掉，能拿掉的只剩投影本身——那需要重訓。
4. **單一載體、單一語料種子（20261127）、k=2**（同 §79–§81）；§75 已量到幅度不跨種子複現。
5. **`query` 只有一個 token 的狀態**，而且 `W_q` 是凍結的：這一節沒有量「換一個訓練過的 `W_q`」。
6. **`entry_key`／`entry_value` 不是效果量**：兩者是同一支探針的 forced choice，只用來定位缺口；8 路
   top-1 是描述量。
7. **沒有答案格**：本節沒有「讀向量 → 答案」的格子，`head` 之後仍是 §78 的缺口。
8. **這是探針，不是生成**：核心分不變 **0.00/10**；本節不新增也不改變任何分數來源。輸出只寫
   `data/pantry_stage/readrule82/`（gitignored）。

### 82.20 下一個登記（`C3` 的 `next`，本節只寫問題）

`C3` 的 `next`（82.9）是「改 query 從哪裡來，讓它看得到證據顏色，同預算」。本節已經把**免費版本**否證掉
（82.17：把同一個 `W_q` 作用在邊界狀態只有 0.5050），所以下一個登記必須是**訓練**那個投影，而不是搬動它：

1. **讀點**：讀發生在**證據邊界**（顏色在那裡可讀，§69 的 0.8900／0.9950），不是提問回合之後；讀的結果
   被帶到提問回合使用（序列上的搬移，不是新增參數）。
2. **預算**：**完全相同**——10,000 步、168,150 參數、同一份語料（種子 20261127、digest 不變）、同一個
   `address="item"`／`write_strength="learned"`／`write_slots=1`。**不加 epoch、不加寬度、不加資料**
   （§75.7 的停損）。
3. **先寫死判準**：重讀 §80 的同一格（held-out 200 次讀的二選一）與 §81 的三欄；若讀點的搬移讓二選一
   從 0.5000 上升，還要看它**有沒有到達**登記的 Wilson／p 門檻，以及 §79 的 entry 兩格是否**不迴歸**
   （0.7375／0.6200）。
4. **不是這一節的結論**：本節沒有量「訓練過的投影會不會帶顏色」；`C3` 只說「現在這個投影不帶」。

門檻、分割與常數由下一節自己登記（本節不先寫死，也不在這一節的結果上調任何參數）。

## §83 把讀點搬到證據邊界、同預算重訓：讀就會定址了嗎？

### 83.1 這一節問什麼

§82 的裁決是 **`C3-query-missing`**：存下來的鍵帶著名冊顏色（`entry_key` **0.7375**、295/400、p
0.002494），提問回合的 query 不帶（**0.5450**、109/200、p 0.069825），而把**同一個凍結的** `W_q`
搬到邊界狀態也只有 **100/200**（`model`）、**101/200**（`cosine_unit`）。免費的搬動被否證了，所以
§82.20 登記的下一步是：**訓練那個投影，不要再搬它**。

本節把那句話寫成一個可裁決的實驗。治療臂＝**同一架構、同一 stage-L 起點、同一語料、同一個 10,000
步／168,150 參數**，只把**讀點**換掉：

> 回答解碼的每一個 token，都用**前一個邊界**取一次的那個讀向量；`W_q`、`head`、store 全部不換，
> **新增參數 0**。

主問題：**在同預算重訓之後，這個讀在 held-out 200 次二選一上，會不會把注意力放在「證據顏色所對應
的那一筆名冊 entry」上？**

有一點讓本節與 §80／§82 不同，而且是本節成立的理由：§80／§82 量的是**診斷讀**——用探針或搬動去問
模型「你那裡有沒有顏色」。本節量的是**模型自己實際做的那次讀**：訓練時答案解碼用的就是它，計分時
問的也是它。所以「訓練的計算」與「計分的格子」是同一個，不是兩個。§82 的 `boundary_query` 是這個
讀在凍結載體上的**未訓練版本**（100/200），本節的對照臂就是它、治療臂是訓練過的它。

**本節不是能力分數**：核心分不變 **0.00/10**（§275）；這裡全部是診斷。

### 83.2 登記前已經量到的（照實寫）

**（a）§82 的四格**（`data/pantry_stage/readrule82/k2.json`，不改寫、不重跑）。held-out 200 次讀、
同 session 兩筆的二選一：

| 格子 | 特徵 | 二選一 | Wilson 95% | p | 讀數 |
| --- | --- | --- | --- | --- | --- |
| `entry_key` | 寫入點的鍵 | **0.7375**（295/400） | 0.6923–0.7782 | 0.002494 | 有顏色 |
| `entry_value` | 寫入點的值 | **0.6200**（248/400） | — | — | 錨 |
| `query` | 提問回合的 `W_q h` | 0.5450（109/200） | 0.4758–0.6125 | 0.069825 | 不過 |
| `boundary_query`／`model` | 邊界的 `W_q h_b` | **0.5000**（100/200） | 0.4314–0.5686 | **1.0** | 不過 |
| `boundary_query`／`cosine_unit` | 同上，無溫度 | **0.5050**（101/200） | 0.4363–0.5735 | **0.551122** | 不過 |

兩個邊界格子的名冊質量：`model` **1.0**（注意力全在兩槽、兩槽各半）、`cosine_unit` **0.180198**
（min 0.1288、max 0.2280）；兩者的 argmax 都在名冊槽，**200/200**。也就是說：讀**知道**要看名冊
那兩筆，只是**分不出是哪一筆**。

**（b）§79 的凍結格子**：鍵→顏色 **0.7375**（295/400）、值→顏色 **0.6200**（248/400），兩者的虛無
（400 次重擬合）都在 0.49–0.50。**可分離**是寫入側的事實。

**（c）§69 的邊界可讀性**：顏色在**證據邊界**可讀 **0.8900／0.9950**，到答案邊界掉到
**0.1400／0.1100**；§80.2（d）把提問回合的 `h → 證據顏色` 量成 8 路 top-1 **0.105**（低於 chance
0.125）。這三件事合起來是本節的動機：**資訊還在邊界，缺的是把它帶到解碼的那一次讀**。

**（d）跑之前沒有量過**：治療臂本身。上面全部是凍結載體上的讀數；「同一個 `W_q` 在 10,000 步之後
會不會學會定址」在跑之前沒有答案。§82.20 只登記了問題的形狀，沒有登記任何治療臂的數字。

**（e）這一節的契約測試**（`tests/test_pantry_readrule83.py`，**38 條**）只用合成張量與合成報告：
常數、五個分支的優先序、控制錨拒絕漂移、`model` 才是閘門（`cosine_unit` 只描述）、`I0` 的每一個
條款（同起點、同預算、同語料、讀點、對齊、錨）、以及 `--check` 對「勝場不可重算／p 不是置換慣例／
錨漂移／分支過期／預測命中造假／決定常數被改／外來報告」的拒絕。**不含任何載體資料、不產生讀數。**

### 83.3 凍結的控制臂與治療臂（跑之前寫定）

兩個臂都是 **§77 的 item 寫入臂**（`address="item"`、`write_strength="learned"`、`write_slots=1`、
`aux_lambda=1.0`、`aux_mode="resolvable"`、`--gate-prefix M`、語料種子 **20261127**、訓練種子
**20261118**、`--train-sessions 400 --epochs 200`＝**10,000 步**、`hidden=128`、`emb=64`）。

| 項目 | 控制臂（凍結，不重訓） | 治療臂（新跑） |
| --- | --- | --- |
| 報告 | `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json` | `data/pantry_stage/readrule83/treatment/…json` |
| checkpoint | `…-190357.pt`，`sha256:ba1edf16…` | 新檔（報告自己記） |
| `weights_hash` | `sha256:0ca9e593…` | 新值（報告自己記） |
| 讀點 (`read_at`) | `token`（= 未設定；每個 token 用自己的 `h`） | **`boundary`**（每個解碼用前一個邊界的讀） |
| 參數 | **168,150** | **168,150** |
| 語料 | `train_digest b12cb2fb…`、`heldout_digest 71eab688…` | 同一份（逐位比對） |
| 起點 | stage-L `sha256:77cb6af3…`（`L_WEIGHTS_HASH`） | 同一份（逐位比對） |
| 寫入 | `address="item"`、`learned`、`1` 槽 | 相同（唯一的自變數是 `--read-at`） |

**控制臂刻意重跑讀（不是重訓）**：把凍結載體在同一個行程裡重新抽取一次 `boundary_query`，逐筆比對
§82 的質量與勝場。任何抽取或算術漂移都會讓質量動，所以這是比 §82 的 entry／read 稽核更強的儀器
檢查（§82 的稽核量的是「槽裡是不是那兩筆」，這裡量的是「讀出來是不是同一個向量」）。

**治療臂從 stage-L 重新開始，不從 §77 的載體續訓**：續訓會把「這次的浮點縮約／最佳化路徑不同」與
「讀點有效」混在一起。兩個臂的 `start.checkpoint`／`start.weights_hash`／`start.init_weights_hash`
必須逐項相同，這是 `I0` 的一條。

### 83.4 登記的常數（跑之前寫定）

| 常數 | 值 | 理由 |
| --- | --- | --- |
| `ALPHA` | **0.005** | 同 §74–§82。 |
| `NULL_DRAWS` | **400** | 同 §74–§82；最小可達 p = 1/401 = 0.002494。 |
| `NULL_SEED` | **20261125** | 同 §74–§82。 |
| `FORCED_FLOOR` | **0.5** | 二選一的 chance；不是可調的地板。 |
| `REF_TOLERANCE` | **2e-9** | 控制錨的逐筆質量容差（§81 慣例）。 |
| `ROSTER_ITEMS` | **2** | 語料固定（k=2）。 |
| `READ_BATCH` | **32** | 只影響速度；分批不跨 session。 |
| `FIT_FLOOR` | **0.90** | §55 的 `GENERAL_FIT_FLOOR`／`STORE_FLOOR`；治療臂的**前置條件**。 |
| `CONTROL_STEPS` | **10,000** | §77 的 `400 sessions ÷ batch 8 × 200 epochs`。 |
| `CONTROL_PARAMS` | **168,150** | §77 的載體大小。 |
| 探針 | 2,000 步／batch 64／lr 1e-3／wd 1e-4／seed **20261121** | **與 §79 逐項相同**（載入 §79 模組時逐項比對）。 |
| 控制錨 | `model` 勝場 **100**、`cosine_unit` 勝場 **101**、逐筆質量 2e-9 | 三個都必須重現，否則 `E0-instrument`。 |
| 閘門規則 | **`model`** 是主規則；`cosine_unit` 只描述 | §82 的 `model` 是模型自己的 softmax；`cosine_unit` 拿掉溫度後也可能只是幾何巧合。 |

`read_at` **不在** `BUDGET_KEYS` 裡——它是本節唯一的自變數。

### 83.5 讀點與計分格子（跑之前寫定）

1. **store 與邊界**：`run_session(..., boundaries=snapshots)` 之後，`snapshots[q-1]` 是證據回合
   之後、提問回合之前的狀態（與 §80.5／§81.5／§82.5 同一點）；`q` 是提問回合（最後一回合）。
2. **治療臂的讀**：在 `--read-at boundary` 下，解碼從 `snapshots[index]` 開始，讀取自
   `snapshots[index-1]`：`r_b = Σ softmax(exp(log_read_scale) · k_bᵀ W_q h_b) v_b`，其中
   `k_b`／`v_b` 是 `snapshots[index-1]` 的 store，`h_b` 是它的 `h`。答案解碼（`index = q`）因此用
   `snapshots[q-1]` 的讀——**就是本節計分的那個格子**。
3. **索引 0**：第一個邊界之前 store 是空的，讀是 `0`（`memory=False` 回的那個向量）。這只影響
   輔助解碼，不影響答案解碼。
4. **輔助項**：`aux_mode="resolvable"` 的每個 prefix 解碼也各自帶**它前一個邊界**的讀；這與
   §77 的目標差別只在讀點，不在被問的邊界、不在權重。
5. **計分格子**：held-out 200 個 session、同 session 兩筆名冊 entry 的二選一——「證據顏色所對應
   的那一筆」對「另一筆」。輸入是 `snapshots[q-1]` 的 `W_q h_b`、`k_b`、`v_b`、名冊兩槽與
   `exp(log_read_scale)`；標籤取語料的 `assert`（證據是 `seen`、值是一個名冊顏色）。**沒有擬合
   參數**（`reads.fitted_parameters = 0`）。
6. **虛無**：只打亂 `item` 標籤、**不重擬合**（讀沒有參數，§80／§81／§82 慣例）。
7. **不迴歸**：在**治療載體**上重跑 §79 的 `entry_key`（鍵→顏色）與 `entry_value`（值→顏色）：
   train 擬合、held-out 計分、400 次重擬合虛無、§82 的閘門（Wilson 下界 > 0.5 且 p < 0.005）。
   逐點數字照實報，不要求逐位重現 §79（那是不同載體）。

### 83.6 主要指標、門檻與不迴歸

* **治療臂的主閘門**（跑一次）：held-out 200 的二選一，`model` 規則；通過條件＝Wilson 95% 下界
  **> 0.5** 且置換檢定 **p < 0.005**。
* **描述量（不裁決）**：`cosine_unit` 的同一格、兩條規則的名冊質量、argmax 直方圖、
  `argmax_on_roster`、治療報告自己的 held-out `full`（exact／ranking，**不當閘門**——那是答案格，
  不是本節的讀格）。
* **不迴歸**：`entry_key` 與 `entry_value` 在治療載體上都必須過 §82 的閘門；兩者**都**要過，缺一即
  `T2`。
* **前置條件**：治療報告的 `results.train_fit_subset.exact` **≥ 0.90**（§55 的
  `GENERAL_FIT_FLOOR`）。報告自己的 `G1_fits_the_subset` 與這個門檻不一致時，直接中止（不得用
  報告的布林值繞過算術）。
* **不會因為結果改門檻**：`ALPHA`、虛無次數、Wilson 地板、`FIT_FLOOR`、主規則、控制錨都在
  §83.4 寫定；任何跑之前的改動都以 amendment 記在 83.13 之前。

### 83.7 為什麼先要求治療臂擬合

一個沒擬合訓練子集的治療臂，它的 held-out 讀不通過時**不能**說是「讀點沒用」：可能只是這個預算
下沒學會任何東西。§77 的 item 臂在同樣的 10,000 步上 `train_fit_subset` 是 **0.9925**；治療臂若
顯著低於 0.90，本節的第一個結論會是 `T0`，而不是 `T3`。這條前置條件寫在跑之前，避免事後把「沒學會」
讀成「機制被否證」。

### 83.8 儀器門檻 `I0`（跑完後檢查）

全部成立才讀治療臂的任何一格：

1. 控制載體的 `weights_hash` 與 checkpoint sha256 **前後相同**（探針不寫回）。
2. 控制報告的 `read_at` 是 `token`（或沒有這個鍵），治療報告的是 **`boundary`**。
3. **同語料**：兩個報告的 `train_digest`／`heldout_digest` 相等，且等於重新載入的語料。
4. **同預算**：`BUDGET_KEYS` 逐項相等（`hidden`、`emb`、`core`、`memory`、`address`、
   `write_strength`、`write_slots`、`aux_lambda`、`aux_mode`、`gate_prefix`、`train_subset`、
   `minimal_binding`、`order_augmented`、`roster_size`、`seed`、`epochs`、`batch`、`lr`），且
   兩個報告的 `params` 都是 **168,150**、`training.steps` 都是 **10,000**。
5. **同起點**：兩個報告的 `start.checkpoint`／`start.weights_hash`／`start.init_weights_hash`／
   `start.params` 逐項相等。
6. **對齊**：名冊文字逐項含著對應的顏色字與人名（§79 的 `alignment`，兩個分割都要過）。
7. **控制錨**：§82 的 `boundary_query` 逐筆重現——`model` **100**、`cosine_unit` **101**、兩條
   規則的 `m0`／`m1` 與 `items` 逐筆相符、最大絕對差 **≤ 2e-9**、mismatch **0**。

任何一項失敗 → `E0-instrument`，不讀治療臂。

### 83.9 分支配表（跑之前寫定，優先序由上到下）

| 分支 | 條件 | 讀法 | `next` |
| --- | --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 控制臂、起點、預算或語料動了，或 §82 的格子沒有逐筆重現 | 先修儀器 |
| `T0-fit-fails` | 治療臂 `train_fit_subset < 0.90` | 這個預算下治療臂沒學會訓練子集；它的 held-out 讀不是讀點的檢定 | 同一支登記的臂重跑（不改讀點、不改預算），先查為什麼沒擬合 |
| `T2-pass-but-regression` | `model` 過閘門，但 `entry_key` 或 `entry_value` 不過 | 邊界讀**開始定址**，但重訓把寫入側推走了：增益不是免費的 | 在同一載體上分離兩側（keys 與 values 各自），同預算 |
| `T1-read-at-boundary-works` | `model` 過閘門且不迴歸通過 | 同預算、同參數、同 store 下，**把讀點搬到證據邊界是可以學會的**：凍結載體缺的不是資訊，是提問回合的那個讀點 | 讀這個載體的端到端答案格；若它跟著動，在下一個語料種子上登記同一個讀點再確認一次 |
| `T3-no-gain` | `model` 不過閘門 | 搬到邊界、同預算重訓之後讀**仍然定址不了**：限制不只是 query 取在哪裡，這個 store／head 在 10,000 步內也學不會用它 | 登記一個讓讀**有理由**在寫入點就分開兩筆的改動（鍵已經帶顏色，§79），不要再搬 query |

`T2` 先於 `T1`：它在「主格過、但不迴歸失敗」時觸發，兩者互斥。`T3` 是最後一支，只在主格不過時
觸發（`cosine_unit` 過而 `model` 不過仍是 `T3`——主規則寫在跑之前）。

### 83.10 預測與否證（跑之前寫定）

1. **主預測是 `T1`，信心低，照實寫。** 理由：§82 已經把鍵（0.7375）與邊界狀態（§69 的 0.8900）
   放在一起，而治療臂的**主損失直接依賴這個讀選對名冊 entry**——凍結載體從來沒有這個梯度。
   在 `--read-at boundary` 下，`r_b` 是答案解碼唯一的 store 入口，寫錯就答錯，梯度會穿過
   `W_q`／`key_proj`／`value_proj`。
2. **登記的替代是 `T3`**：同一個 10,000 步、同樣的載體大小，§78 的**擬合**讀出在答案格上也只有
   0.37；鍵雖然線性可讀，softmax 讀的幾何未必能在這個預算內被推到位。若 `T3` 成立，主預測落空。
3. **否證條件**：`model` 不過 → `T3`；`model` 過而不迴歸失敗 → `T2`；治療臂沒擬合 → `T0`。
4. **`cosine_unit` 不是門檻**：它可能過而 `model` 不過（或相反），照實報，不改主規則。
5. **pass 不是「模型會回答」**：本節的主格是**讀**，不是答案；端到端的 `full` 只描述。真正的
   「讀向量 → 答案」缺口仍是 §78 的那一個。
6. **不會因為結果改門檻**：見 §83.6。

### 83.11 照實記的限制

1. **單一語料種子（20261127）、k=2、單一 stage-L 起點**（同 §77–§82）；§75 已量到幅度不跨種子
   複現，所以 `T1` 是「在這個語料上學得會」，不是「這條規則普遍有效」。
2. **一個新的治療臂＝一次新的最佳化**：10,000 步的隨機性（shuffle 由 `seed:epoch` 決定）會讓
   治療臂與控制臂不只在讀點上不同；本節用「同起點、同語料、同預算」把它壓到最小，但不能說
   「只差讀點」是逐位的。
3. **`model` 與 `cosine_unit` 不是同一件事**：`model` 有自己的 `exp(log_read_scale)`，重訓會改它；
   若溫度塌掉，`model` 可能因為質量變均勻而輸，即使幾何方向是對的。本節把 `cosine_unit` 當描述量
   就是為此。
4. **不迴歸的兩格是新擬合的**：它們在治療載體上重擬合、在 held-out 計分，逐點數字與 §79 不同是
   正常的；「過」只說這個載體還讀得到顏色，不是說寫入沒變。
5. **治療臂的 `full` 不是本節的分數**：它只描述端到端答案有沒有跟著動，不進任何閘門。
6. **探針格子每次虛無不重擬合**（讀沒有參數），但**不迴歸的兩格要重擬合**（400 次），所以本節
   比 §82 貴：兩支重擬合探針＋三次讀取抽取＋兩次 entry 抽取。
7. **這是探針，不是生成**：核心分不變 **0.00/10**；本節不新增也不改變任何分數來源。
8. **輸出只寫 `data/pantry_stage/readrule83/`**（gitignored）。

### 83.12 命令與執行上限

訓練（治療臂；與 §77 的 item 臂逐項相同，唯一的差別是 `--read-at boundary`）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address item \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261127 --device cpu \
    --write-slots 1 --read-at boundary --out data/pantry_stage/readrule83/treatment
```

量測（一次；兩臂分開載入，載體不訓練、不寫回）：

```bash
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_readrule83.py \
    --control data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --treatment $(ls -t data/pantry_stage/readrule83/treatment/*.json | head -1) \
    --anchor82 data/pantry_stage/readrule82/k2.json \
    --device cpu --out data/pantry_stage/readrule83/k2.json
./.venv/bin/python scripts/probe_pantry_readrule83.py --check data/pantry_stage/readrule83/k2.json
```

上限沿用硬規則：**CPU ≤ 50% 整機、RAM ≤ 60%、swap 0、GPU 不使用（`--device cpu`）**。起跑前用
`/proc/stat` 量整機負載，配額取 `min(500%, floor((50% − 背景) × 12 核))`（以 25% 為一階往下取），
並照實記在 83.13。

**儀器預跑（不是計分跑，照實記）**：`--null-draws 2` 的一次性 harness 檢查（輸出到 `/tmp`，
不進版控、20.67 s）確認四件事：控制錨**逐筆重現**（`model` 100、`cosine_unit` 101、質量最大差
**0.0**、mismatch **0**）、對齊通過、兩個 `entry` 格子在**凍結載體**上回到 §79／§82 的點估計
（`entry_key` **295/400**、`entry_value` **248/400**）、`--check` **拒絕**這份 2-draw 報告
（`decision.null_draws` 不是登記的 400）。**這個預跑之後沒有改動任何常數、格子、門檻或分割**；
它印出的分支是 `E0-instrument`（治療報告＝控制報告，`read_at` 不是 `boundary`），那不是讀數。

這一節在**計分跑之前**寫定。任何跑之前的改動都會以 amendment 記在 83.13 之前；被丟棄的跑法照實記。

### 83.13 執行：治療臂（照實記）

登記的訓練指令原樣執行（唯一的自變數仍是 `--read-at boundary`）：

* **環境**：`CPUQuota=400%`、`MemoryMax=4096M`、`MemorySwapMax=0`、`OMP_NUM_THREADS=4`、
  `--device cpu`。起跑前整機（`/proc/stat`，12 秒窗）是 **7.8 %**；§83.12 的配額規則算出
  `min(500%, floor((50 − 7.8) × 12 / 25) × 25) = 500%`，本跑**只取 400 %**（整機 33.3 %），
  刻意留下 16.7 個百分點的餘裕給背景波動。**這是比登記上限更保守的選擇，不是 amendment。**
* **成本**：wall **28:00.15**（腳本自己的 `cost.train_seconds` 是 **1,678.8 s**）、user 6,678.24 s／
  sys 12.70 s、CPU **398 %**、峰值 RSS **782,596 kB ≈ 764 MiB**（上限 4 GiB）、**swap 0**、exit 0。
* **產物**：`data/pantry_stage/readrule83/treatment/pantry_deduction_20261117-020810.json`
  （checkpoint 同名 `.pt`，gitignored）。
* **登記的預算逐項相符**：`params` **168,150**、`training.steps` **10,000**、`read_at` **`boundary`**、
  語料種子 **20261127**、訓練種子 **20261118**、`train_digest b12cb2fb…`／`heldout_digest 71eab688…`；
  起點 `data/text_stage/text_stage_20261113-212446.pt`、`weights_hash sha256:36b78b6f…`、
  `init_weights_hash sha256:a7843b34…`、`params 168,150`。
* **擬合**：`train_fit_subset.exact` **0.8325**（333/400）、`train_fit`（前 200 段）**0.8700**、
  held-out `full` **0.3150**、`ranking_exact` **0.5050**。報告自己的 `M1_fits_the_declared_items`
  是 **false**（它以同一個 0.90 地板算，所以與這裡的算術一致）。
* **權重**：`weights_hash` **`sha256:6336734458335d13f0f84e7df5b369c8fc66d9fc13799f8eb325a5bcb8eccf10`**。

**登記的 `T0` 重跑（83.9 的 `next`）**：同一條指令、同一個環境、只換 `--out`，再跑一次：

* wall **26:42.03**、CPU **398 %**、峰值 RSS **783,968 kB**、**swap 0**、exit 0；
  腳本計時 **1,600.7 s**（與第一次的 1,678.8 s 差 4.7 %，是背景負載不是結果）。
* **逐項相同**：`train_fit_subset` **0.8325**、`train_fit` **0.8700**、`full` **0.3150**、
  `ranking_exact` **0.5050**、最後一個 epoch 的 `mean_loss` **0.1790**（main **0.0908**、
  aux **0.0882**）、`weights_hash` **完全相同**（`sha256:63367344…`）。
* checkpoint 檔案的 sha256 不同（`91e913a8…` vs `2d0a6dee…`）：那是序列化中繼資料，**權重相同**。
* 讀法：**這個擬合落差在登記的環境裡是確定性的、不是一次性的壞運**。兩份報告都留在
  `data/pantry_stage/readrule83/`（gitignored）。

### 83.14 執行：探針（一次作廢、一次登記讀數；照實記）

**（a）第一次探針——作廢，`E0-instrument`。** 它跑在 `CPUQuota=400%`、`OMP_NUM_THREADS=4` 下
（腳本計時 **292.137 s**），控制錨的 `model` 欄**逐位重現**（最大差 **0.0**、mismatch **0**、
勝場 **100**），但 `cosine_unit` 欄有 **41/200** 筆讀數超出容差，最大差 **3.0e-8**（勝場仍是 **101**）。

原因寫清楚：§82 的逐筆質量是在 **`OMP_NUM_THREADS=2`** 下產生的；`cosine_unit` 的歸一化與
`softmax` 的縮約順序隨執行緒數改變，float32 在這個尺度上就會差幾十個 ulp。**這不是讀數，也不是
「治療無效」**：`model` 逐位相符、勝場相同，差的是 2e-9 這個**儀器容差**在另一個算術環境下不成立。

處理：**沒有改任何常數、容差、格子、門檻或分割**（改容差就是事後放寬儀器）。作廢的報告留在
`data/pantry_stage/readrule83/discarded/k2.threads4.json`，它的分支是 `E0-instrument`，
`--check` 也正確地拒絕它（三條：錨未重現、`cosine_unit` 質量不符、超過容差）。它的內容**不進**
83.15–83.18 的任何一格。

**（b）登記的探針——在 §82.12 的算術環境下重跑。** `CPUQuota=200%`、`OMP_NUM_THREADS=2`、
`MemoryMax=4096M`、`MemorySwapMax=0`、`--device cpu`，其餘引數與 §83.12 相同：

* wall **4:31.30**（腳本計時 **270.84 s**）、user 538.45 s／sys 1.53 s、CPU **199 %**、
  峰值 RSS **726,564 kB ≈ 710 MiB**、**swap 0**、exit 0。
* 輸出 `data/pantry_stage/readrule83/k2.json`（gitignored）；**`--check` OK**（p 的公式、勝場
  可重算、五個分支可重導、控制錨）。
* 一個警告照實記（與 §81／§82 同一個）：`float(weights[slot])` 在 `no_grad` 之外取純量會印
  `requires_grad=True` 的 `UserWarning`；數值不受影響（錨最大差 **0.0** 就是證據）。

### 83.15 儀器 `I0`（全過）

| 條款 | 值 |
| --- | --- |
| 控制載體 `weights_hash` 前後 | 相同（`sha256:0ca9e593…`） |
| 控制 checkpoint sha256 前後 | 相同（`ba1edf16…`） |
| 控制報告 `read_at`／治療報告 `read_at` | `token`（缺鍵視為 `token`）／**`boundary`** |
| 同語料 | `b12cb2fb…`／`71eab688…`，且等於重新載入的語料 |
| 同預算 | `BUDGET_KEYS` 無差異；兩臂 `params` **168,150**、`training.steps` **10,000** |
| 同起點 | `start.checkpoint`／`weights_hash`／`init_weights_hash`／`params` 四項相同 |
| 對齊（train／held-out） | 都過 |
| 控制錨 `model` | 勝場 **100/200**、逐筆質量最大差 **0.0**、mismatch **0** |
| 控制錨 `cosine_unit` | 勝場 **101/200**、質量最大差 **0.0**、mismatch **0**、平均質量 **0.180198**（＝§82） |

`I0` 的讀法：控制臂是**同一個凍結載體、同一個行程、同一個算術環境**重新抽取的，逐筆重現 §82 的
`boundary_query` 欄；治療臂與它在語料、起點、步數、參數、寫入模式上逐項相同，只差讀點。

### 83.16 前置條件：治療臂有沒有擬合？（沒有）

| 量 | 治療臂（`--read-at boundary`） | 控制臂（§77 item，`token`） |
| --- | --- | --- |
| `train_fit_subset.exact`（400 段） | **0.8325**（333/400） | 0.9925（397/400） |
| `train_fit.exact`（前 200 段） | 0.8700（174/200） | — |
| 第 1 個 epoch `mean_loss` | 2.5805（main 1.3470／aux 1.2335） | 2.5833（main 1.3483／aux 1.2350） |
| 第 200 個 epoch `mean_loss` | **0.1790**（main 0.0908／aux 0.0882） | **0.0078**（main 0.0052／aux 0.0026） |

兩臂**從同一個損失開始**（2.58），治療臂到最後仍高 **23 倍**（0.179 vs 0.0078）。登記的地板是
**0.90**：**0.8325 < 0.90，前置條件不成立 → `T0-fit-fails`。** 依 83.7 的理由，這個臂的 held-out
讀**不是**讀點的檢定。

### 83.17 分支與預測檢查

| 分支 | 條件 | 這次 |
| --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 否（83.15 全過；第一次探針的 `E0` 已作廢，見 83.14(a)） |
| **`T0-fit-fails`** | 治療臂 `train_fit_subset < 0.90` | **是（0.8325）** |
| `T2-pass-but-regression` | 主格過、不迴歸失敗 | 未達（被 `T0` 先攔下） |
| `T1-read-at-boundary-works` | 主格過且不迴歸通過 | 未達 |
| `T3-no-gain` | 主格不過 | 未達（不是「讀還是不定址」，是「這個臂沒擬合」） |

**登記的預測 `T1` 落空**，登記的替代 `T3` 也**沒有**成立：實際分支是 `T0`，而 `T0` 的意義是
「這一格沒被測到」，不是「讀點被否證」。

### 83.18 描述量（在 `T0` 之下，不是本節的證據）

把治療載體上同一批 held-out 200 次讀照登記的格子算出來（**只描述，不裁決**；`T0` 說這些數字不能
當讀點的檢定）：

| 臂／規則 | 勝場 | 二選一 | Wilson 95% | p | 虛無 ge | 名冊質量 | argmax 在名冊 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 控制／`model` | 100/200 | 0.5000 | 0.4314–0.5686 | 1.0 | 400 | 1.0 | 1.0 |
| 控制／`cosine_unit` | 101/200 | 0.5050 | 0.4363–0.5735 | 0.551122 | 220 | 0.180198 | 1.0 |
| 治療／`model` | 100/200 | 0.5000 | 0.4314–0.5686 | 1.0 | 400 | 1.0 | 1.0 |
| 治療／`cosine_unit` | 100/200 | 0.5000 | 0.4314–0.5686 | 1.0 | 400 | **0.17784** | 1.0 |

**不迴歸**（在**治療載體**上重新擬合 §79 的兩格，held-out 400 筆，400 次重擬合虛無）：

| 格子 | 勝場 | 二選一 | Wilson 下界 | p | 8 路 top-1 | §82 閘門 |
| --- | --- | --- | --- | --- | --- | --- |
| `entry_key`（鍵→顏色） | 308/400 | **0.7700** | 0.7263 | 0.002494 | 0.4600 | **過** |
| `entry_value`（值→顏色） | 289/400 | **0.7225** | 0.6767 | 0.002494 | 0.3225 | **過** |

兩格都比凍結載體上的 0.7375／0.6200 **高**：重訓把**寫入側**推得更可分。但這只在「這個臂沒擬合」
的前提下成立，**不能**讀成「邊界讀有效」或「寫入變好是讀點的功勞」——兩臂差的不只是讀點，還有一條
新的最佳化軌跡（83.11 第 2 點）。

其他描述量：治療報告的 held-out `full` **0.3150**（控制 0.3700）、`ranking_exact` **0.5050**
（控制 0.5250）；`readout` 診斷在 turn 2／3 都是 **0.3150**（n=200）；名冊順序雙生在
`same_prediction` 上是 **0.7000**（140/200）、`both_correct` **0.7000**；順序置換的保留率是
**0.9524**（60/63）。這些都不進任何閘門。

### 83.19 為什麼沒擬合（診斷，不是另一個量測）

事實先列清楚，然後才是假設：

1. **兩臂從同一個損失出發**（2.5805 vs 2.5833），到第 200 個 epoch 治療臂停在 **0.1790**、控制臂
   到 **0.0078**。所以不是初始化或資料不同，是**訓練能到達的損失地板不同**。
2. **讀點改變的是什麼**：`--read-at boundary` 之下，回答解碼的每一個 token 都看到
   `snapshots[q-1]` 取出的**同一個**向量；`snapshots[q]`（提問回合自己的寫入，名冊幾何下的第 4 槽）
   在那次解碼裡**不可定址**。`token` 之下，解碼自己的 `h` 每個 token 都重新定址 store，**包括**
   提問回合的寫入。
3. **那個被凍結的讀本來就在 chance**（§82：100/200、p 1.0）。治療臂因此要**同時**學會「用一個固定
   向量選對 entry」與「透過它回答」，而控制臂可以把「選」與「答」分給每個 token 的 query。

**假設**（與上面三點一致，但沒有被單獨量測）：擬合落差來自「讀被固定成一個向量」與「這個向量取在
提問回合的寫入之前」這兩件事的**合取**；在這個預算下，10,000 步不足以把兩件事一起學好。

**不是**的結論：不是「邊界讀永遠學不會」（§83 沒有測到那一格），也不是「寫入側退步」（83.18 的兩格
反而更高）。要分離這兩個原因需要另一條臂（見 83.21），那條臂會是一個**新的登記**，不是這一節的補救。

### 83.20 照實記的限制（追加在 83.11 之後）

1. **`T0` 只說「沒測到」**：`train_fit_subset 0.8325 < 0.90`，所以 83.18 的四格、不迴歸的兩格與
   held-out `full` 都是描述量，不是讀點的證據。任何把「治療／`model` 100/200」讀成「讀點無效」的
   說法都越過了登記的分支。
2. **登記的預測落空**：主預測 `T1`、替代 `T3` 都沒有成立；實際是 `T0`。照實記，不改寫預測。
3. **控制錨對執行緒數敏感**：2e-9 的容差是在 §82 的 `OMP_NUM_THREADS=2` 下成立的；同一個載體在
   `OMP_NUM_THREADS=4` 下 `cosine_unit` 的逐筆質量會差到 **3.0e-8**（41/200 筆超差，勝場不變）。
   因此**這個探針必須在 §82 的執行緒數下跑**；第一次探針作廢並保留（83.14(a)），這不是結果。
4. **治療臂跑在 4 個執行緒、控制臂是 §77 的 5 個執行緒**：登記只固定步數、參數、語料與起點，
   沒有固定執行緒數（§83.11 第 2 點已說「只差讀點」不是逐位的）。用 4 執行緒重跑的**第二次**
   與第一次**權重逐位相同**，所以在同一個環境裡這個結果是確定性的；但**沒有**在 5 執行緒下重跑
   （那會是另一條最佳化軌跡，且在看到擬合之後才挑環境就是調參）。
5. **擬合守門的交叉檢查在 `M` 前綴下是空的**：§83.6 寫「報告自己的 `G1_fits_the_subset` 不一致就
   中止」，但治療報告用 `--gate-prefix M`，它的閘門叫 `M1_fits_the_declared_items`（值 **false**，
   以同一個 0.90 地板算）。程式只在 `G1` 存在時比對，所以這次是**直接套算術**、沒有繞過；但
   「名稱交叉檢查」這一條實際上沒執行。照實記，不改程式（改它就是事後動探針）。
6. **單一語料種子（20261127）、k=2、單一 stage-L 起點、一條治療臂**；§75 已量到幅度不跨種子複現。
7. **這是探針，不是生成**：核心分不變 **0.00/10**（§275）；本節沒有新增或改變任何分數來源。
   輸出只寫 `data/pantry_stage/readrule83/`（gitignored）。

### 83.21 下一個登記（`T0` 的 `next` 之後；本節只寫問題）

83.9 對 `T0` 的 `next` 是「同一條臂重跑、先報為什麼沒擬合」。兩件都做了（83.13 的重跑逐位相同、
83.19 的診斷）。下一個問題因此是**分離 83.19 的兩個原因**：

> 把讀取在**提問回合自己的邊界**（`snapshots[q]`，它的 store 已含提問回合的寫入）並在整個解碼中
> 固定住——**零新增參數、同一個 10,000 步／168,150 參數／同一份語料**——這個臂會不會擬合？
> 若會，那麼 §83 的失敗是「讀取在提問寫入之前」；若仍然不會，失敗就是「一個固定讀向量」。

這是一條**新的 `read_at` 值**（暫稱 `question`），不是 amendment：它與 `boundary` 只差「讀哪一個
邊界」，其餘逐項相同，所以兩臂可以乾淨地分離上面那兩件事。**它必須在自己的小節裡先登記再跑**，
包括：擬合地板、主格、不迴歸、分支與預測；本節不先寫它的門檻，也不先猜它的結果。

在那之前，**§83 的裁決就是 `T0-fit-fails`**：這個預算下治療臂沒有擬合，所以邊界讀的定址能力
**沒有被測到**，也沒有被否證。

## §84 讀點移到提問回合自己的邊界（登記）

### 84.1 這一節問什麼

§83 把讀點移到**證據邊界**（提問回合之前一個回合）並在整個回答解碼中固定住，結果在登記的預算下
**沒有擬合**（`train_fit_subset` **0.8325** < 0.90，分支 `T0-fit-fails`）。§83.19 把那個落差拆成
兩件同時被改動的事：

1. 讀是**一個固定向量**，整個解碼都用它；
2. 那個向量取在**提問回合的寫入之前**，所以提問回合自己的那一筆（名冊幾何下的下一個槽）在解碼中
   **不可定址**。

§84 **只改第 2 件**：`--read-at question` 讓讀取在**解碼自己的邊界**（`snapshots[q]`，store 已含
提問回合的寫入）取一次並固定住。同一個 `W_q`、同一個 `head`、同一個 store、同一個預算，
**零新增參數**。

這一節要回答的是**擬合**，不是分數：

> 把提問回合自己的寫入放進 store 之後，一個固定的讀向量在這個預算下擬合得了嗎？
> 若擬合，§83 的失敗就是「讀取在提問寫入之前」；若仍不擬合，兩條臂共同的因素就只剩「一個固定讀向量」。

### 84.2 登記前已經量到的（照實寫）

| 量 | 值 | 出處 |
| --- | --- | --- |
| §83 治療臂擬合 | **0.8325**（333/400） | §83.16 |
| §83 對照臂（§77 item）擬合 | **0.9925**（397/400） | §83.16 |
| §83 最後 `mean_loss`（治療／對照） | **0.1790**／**0.0078** | §83.16 |
| 鍵→顏色（凍結載體） | **0.7375**（295/400） | §82 |
| 提問回合 query→顏色（凍結載體，線性探針） | **0.5450**（109/200），8 路 top-1 0.1550 | §82 |
| 邊界 query（提問前邊界，零參數） | **0.5000／0.5050** | §82 |
| 證據邊界的顏色讀出 | **0.8900** | §69 |
| 提問回合的模型自己那次讀（store 在寫入**之前**） | **100/200**，質量 1.0，argmax 槽 2 200/200 | §80／§81 |
| 同一批讀的 `cosine_unit` | **100/200**，質量 **0.1785**，argmax 槽 2 200/200 | §81 |

**這一節的對照格是新格子**：§80／§81／§82 讀的都是**提問回合寫入之前**的 store；§84 的讀點是
**寫入之後**（`snapshots[q]`），所以沒有既有的逐筆質量可以錨。對照臂因此在這一節**只作描述**，不作錨；
儀器錨改用 §82 的 `boundary_query` 欄（逐筆 2e-9）＋ query 向量逐位相同（84.8）。

### 84.3 凍結的控制臂與治療臂（跑之前寫定）

* **控制臂**：凍結的 §77 item 載體
  `data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json`（`address=item`、
  `write_slots=1`、168,150 參數、`weights_hash sha256:0ca9e593…`）。它的讀取在**提問邊界**
  （store 含提問回合的寫入、query 是提問回合最後一個 token 的 `W_q h`），保持不訓練。
* **治療臂**：同一架構、同一個 stage-L 起點
  （`data/text_stage/text_stage_20261113-212446.pt`、`sha256:77cb6af3…`）、同一份語料
  （種子 **20261127**、`train_digest b12cb2fb…`／`heldout_digest 71eab688…`）、同一個預算
  （**10,000 步**、**168,150 參數**、`--device cpu`），**唯一自變數是 `--read-at question`**。
* 兩臂都走同一個 `run_session`、同一份 `--minimal-binding --order-augmented --roster-size 2`
  語料、同一個 `--aux-loss 1.0 --aux-mode resolvable --gate-prefix M` 目標；治療臂的每一個解碼
  （主答案與每一個輔助邊界）都攜帶**它自己那個邊界**取出的讀，並在整個解碼中固定。
* **執行環境刻意與 §83 的治療臂相同**（`CPUQuota=400%`、`OMP_NUM_THREADS=4`、
  `MemoryMax=4096M`、`MemorySwapMax=0`）：§84 要與 §83 比的是「讀點」，不是執行緒數。
  §77 的對照臂當年是 5 個執行緒，這件事在 §83.20 已照實記為限制，本節不重複挑環境。

### 84.4 登記的常數（跑之前寫定）

```text
FIT_FLOOR = 0.90          # §55/§77 的同一個擬合地板
ALPHA = 0.005             # §79/§80/§81/§82 的同一個顯著水準
FORCED_FLOOR = 0.5        # 二選一
NULL_DRAWS = 400          # 標籤置換次數，與 §80/§81/§82 相同
NULL_SEED = 20261125
REF_TOLERANCE = 2e-9      # §82 逐筆質量的儀器容差
PRIMARY_RULE = "model"    # 載體自己的 softmax 是閘門
RULES = ("model", "cosine_unit")   # 後者只作描述
ROSTER_ITEMS = 2
CONTROL_STEPS = 10000
CONTROL_PARAMS = 168150
CONTROL_WINS = {"model": 100, "cosine_unit": 101}   # §82 boundary_query 錨
```

### 84.5 讀點與計分格子（跑之前寫定）

* **讀點**：`snapshots[q]`（`q = len(turns) - 1`）的 store 與該邊界的 `h`；query 是
  `W_q h`，投影本身**完全沒換**。主解碼使用這個讀；輔助解碼使用它自己那個邊界
  （`snapshots[k]`）的讀。全部固定、全部零新增參數。
* **計分格**：§81 的**同一 session 二選一**——名冊兩筆中，證據顏色需要的那一筆是否拿到更多
  注意力質量。held-out **200** 次讀；`model` 規則（載體自己的 softmax，自己的溫度）是**閘門**，
  `cosine_unit`（去範數、去溫度）**只作描述**。
* **虛無**：400 次名冊標籤置換、**不重擬合**（§80/§81 的慣例）。
* **不迴歸**：§79 的兩格（`k`→顏色、`v`→顏色）在**治療載體**上重擬合（train 800 筆 entry），
  held-out 400 筆計分，套 §82 的同一道閘門（Wilson 下界 > 0.5、p < 0.005）。

### 84.6 主要指標、門檻與不迴歸

* **主要指標**：治療臂在 `model` 規則上的二選一勝場／200。**通過**＝Wilson 95% 下界 **> 0.5**
  且置換 p **< 0.005**。`cosine_unit` 只印出來對照，不裁決。
* **擬合前置條件**：治療臂 `train_fit_subset`（400 段）**≥ 0.90**。
* **不迴歸**：`entry_key` 與 `entry_value` 兩格都必須通過同一道閘門。
* **分支**（84.9）依 `E0 > Q0 > Q2 > Q1 > Q3` 的固定優先序。

### 84.7 為什麼先要求治療臂擬合

同 §83.7：若臂連自己訓練的 400 段都背不起來，它的留出讀量到的是「這個預算下沒學會」，不是
「提問邊界的固定讀能不能定址」。§83 就是這樣被攔下的；§84 沿用同一個地板，**不因 §83 失敗而放寬**。

### 84.8 儀器門檻 `I0`（跑完後檢查）

1. 控制載體 `weights_hash`／checkpoint sha256 前後相同。
2. 控制報告 `read_at` 缺鍵（`token`）／治療報告 `read_at` **`question`**。
3. 同語料（兩份 digest 相符且等於重新載入的語料）、同預算（`BUDGET_KEYS` 無差異、
   `params` 168,150、`steps` 10,000）、同起點（checkpoint／`weights_hash`／`init_weights_hash`／
   `params` 四項相同）。
4. 對齊（train／held-out）都過。
5. **§82 `boundary_query` 錨逐筆重現**：控制載體在同一個行程、同一個算術環境下重新抽取，
   `model` 與 `cosine_unit` 的質量最大差 ≤ **2e-9**、mismatch 0、勝場 100／101。
   （本探針必須在 **`OMP_NUM_THREADS=2`** 下跑：§83.14(a) 已量到 4 執行緒會讓這個錨漂到 3e-8。）
6. **query 恆等**：提問邊界讀的 query 向量，逐筆等於 §82 `query` 欄的 query 向量
   （`max_abs_diff` **0.0**、mismatch 0）。這一條把「只有 store 換了」變成機械可檢，
   而不是靠文字宣告。

`I0` 任一條失敗＝`E0-instrument`，這一節**不讀任何一格**。

### 84.9 分支配表（跑之前寫定，優先序由上到下）

| 分支 | 條件 |
| --- | --- |
| `E0-instrument` | `I0` 任何一條失敗（含錨未重現、query 不恆等） |
| **`Q0-fit-fails`** | 治療臂 `train_fit_subset < 0.90` |
| `Q2-pass-but-regression` | 主格過、不迴歸不過 |
| `Q1-read-at-question-works` | 主格過、不迴歸過 |
| `Q3-fits-but-no-gain` | 擬合過、主格不過 |

每一條的 `next` 都寫在探針的 `branch()` 裡，跑之前就固定。

### 84.10 預測與否證（跑之前寫定）

* **主預測：`Q3-fits-but-no-gain`**（低信心）。理由：§83.19 的假設是「固定讀」與「讀在提問寫入
  之前」的**合取**造成擬合地板；§84 只移除第二項，所以**擬合**是主預測。但 §82 量到這個 query 的
  痕跡只有 **0.5450**，而固定向量仍可能不足以定址，所以主格**不過**是保守的一半。
* **替代：`Q0-fit-fails`**。若擬合仍失敗，兩條臂共同的因素只剩「一個固定讀向量」；那會把 §83 的
  失敗從「讀點」移到「固定」，下一個登記就必須改「每個 token 重新定址」而不是再搬讀點。
* **否證條件（寫在這裡，跑完照它判）**：主格通過且不迴歸通過＝`Q1`，主預測落空，照實記；
  不得事後改寫預測或改門檻。

### 84.11 照實記的限制

1. **單一語料種子（20261127）、k=2、單一 stage-L 起點、一條治療臂**；§75 已量到幅度不跨種子複現。
2. **控制格是新格子**（store 在提問寫入之後），沒有既有的逐筆質量可錨，所以它**只作描述**；
   這一節的儀器錨是 §82 的 `boundary_query` 加 query 恆等，不是這個新格。
3. **執行緒數**：治療臂用 4 個執行緒（與 §83 的治療臂相同），控制臂是 §77 的 5 個執行緒；
   §83.20 已記為限制。不在看到結果之後換環境。
4. **`Q2` 不是「寫入變好」的證據**：兩臂差的不只是讀點，還有一條新的最佳化軌跡。
5. **這是探針，不是生成**：核心分不變 **0.00/10**（§275）；輸出只寫 `data/pantry_stage/readrule84/`
   （gitignored）。
6. **`T0` 的解讀不沿用**：§84 的 `Q0` 只說「這個臂在這個預算下沒擬合」，不單獨證明「固定讀永遠
   學不會」；要分離「固定」與「取一次」需要另一條臂（84.9 的 `next`）。

### 84.12 命令與執行上限

```bash
PYTHONPATH=apps/backend/src OMP_NUM_THREADS=4 \
  systemd-run --scope --user -p CPUQuota=400% -p MemoryMax=4096M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/train_pantry_deduction.py \
    --train-sessions 400 --epochs 200 --core turnstore --address item \
    --aux-loss 1.0 --aux-mode resolvable --minimal-binding --order-augmented \
    --roster-size 2 --gate-prefix M --pantry-seed 20261127 --device cpu --write-slots 1 \
    --read-at question --out data/pantry_stage/readrule84/treatment

PYTHONPATH=apps/backend/src OMP_NUM_THREADS=2 \
  systemd-run --scope --user -p CPUQuota=200% -p MemoryMax=4096M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/probe_pantry_readrule84.py \
    --control data/pantry_stage/item77/item/pantry_deduction_20261116-190357.json \
    --treatment data/pantry_stage/readrule84/treatment/<report>.json \
    --anchor82 data/pantry_stage/readrule82/k2.json \
    --out data/pantry_stage/readrule84/k2.json --device cpu

./.venv/bin/python scripts/probe_pantry_readrule84.py --check data/pantry_stage/readrule84/k2.json
```

* 訓練：`CPUQuota=400%`（整機 33.3%）、`MemoryMax=4096M`、`MemorySwapMax=0`、`--device cpu`、
  `OMP_NUM_THREADS=4`；起跑前用 `/proc/stat` 量整機負載（12 秒窗），若超過硬規則的 50%，照
  §80.13 的先例降到 `CPUQuota=<剩餘>` 並照實記。
* 探針：`CPUQuota=200%`（整機 16.7%）、`OMP_NUM_THREADS=2`（**§82 的算術環境**，見 84.8 第 5 條）、
  `MemoryMax=4096M`、`MemorySwapMax=0`、`--device cpu`。
* GPU 不使用（0% ≤ 50%）；swap 0。
* 若 cgroup 觸發 OOM，該次記為**失敗的跑**，不是結果，不得放寬上限。

**這一節不是能力分數**；核心分不變 **0.00/10**。它只回答「把讀取在提問回合自己的邊界並固定，
這個臂擬合得了嗎、那個讀定址得了嗎」。

### 84.13 執行：治療臂（照實記）

登記的訓練指令原樣執行（唯一的自變數是 `--read-at question`）：

* **環境**：`CPUQuota=400%`、`MemoryMax=4096M`、`MemorySwapMax=0`、`OMP_NUM_THREADS=4`、
  `--device cpu`。起跑前整機（`/proc/stat`，12 秒窗）是 **14.9 %**；§84.12 的配額規則算出
  `min(500%, floor((50 − 14.9) × 12 / 25) × 25) = 400%`，本跑**正是 400 %**（整機 33.3 %）。
* **成本**：wall **29:20.22**（腳本自己的 `cost.train_seconds` 是 **1,758.8 s**）、user 6,998.40 s／
  sys 11.97 s、CPU **398 %**、峰值 RSS **782,940 kB ≈ 765 MiB**（上限 4 GiB）、**swap 0**、
  Major page faults 9、exit 0。
* **產物**：`data/pantry_stage/readrule84/treatment/pantry_deduction_20261117-081253.json`
  （checkpoint 同名 `.pt`，gitignored）。
* **登記的預算逐項相符**：`params` **168,150**、`training.steps` **10,000**、`read_at` **`question`**、
  語料種子 **20261127**、訓練種子 **20261118**、`train_digest b12cb2fb…`／`heldout_digest 71eab688…`
  （與 §83 的治療臂**逐字相同**）；起點 `data/text_stage/text_stage_20261113-212446.pt`、
  `weights_hash sha256:36b78b6f…`、`init_weights_hash sha256:a7843b34…`、`params 168,150`。
* **擬合**：`train_fit_subset.exact` **0.6525**（261/400）、`train_fit`（前 200 段）**0.6650**
  （133/200）、held-out `full` **0.3850**、`ranking_exact` **0.5050**。報告自己的
  `M1_fits_the_declared_items` 是 **false**（同一個 0.90 地板），`M2_heldout_beats_chance` **false**。
* **損失**：第 1 個 epoch `mean_loss` **2.5809**（main 1.3472／aux 1.2337）；
  第 200 個 epoch **0.3300**（main 0.1665／aux 0.1636）；整段最低 **0.2805**（第 195 個 epoch）。
* **權重**：`weights_hash` **`sha256:b8d98a7994b3889d03d6d3239d8fa0c530b1bb43fbc3248ebcbeb6d3a4a760b3`**。

### 84.14 執行：探針（登記讀數；`--check` OK）

`CPUQuota=200%`、`OMP_NUM_THREADS=2`（**§82 的算術環境**，84.8 第 5 條）、`MemoryMax=4096M`、
`MemorySwapMax=0`、`--device cpu`，其餘引數與 §84.12 相同。起跑前整機負載 **5.7 %**。

* wall **5:01.43**（腳本計時 **300.955 s**）、user 598.06 s／sys 1.93 s、CPU **199 %**、
  峰值 RSS **729,664 kB ≈ 713 MiB**、**swap 0**、exit 0。
* 輸出 `data/pantry_stage/readrule84/k2.json`（gitignored）；**`--check` OK**。
* 分支：**`Q0-fit-fails`**（84.15–84.17）。
* 一個警告照實記（與 §81／§82／§83 同一個）：`float(weights[slot])` 在 `no_grad` 之外取純量會印
  `requires_grad=True` 的 `UserWarning`；數值不受影響（錨最大差 **0.0** 就是證據）。
* §83.14(a) 的執行緒教訓這次直接套用：探針跑在 2 個執行緒，所以錨**不需作廢、一次就過**。

### 84.15 儀器 `I0`（全過）

| 條款 | 值 |
| --- | --- |
| 控制載體 `weights_hash` 前後 | 相同（`sha256:0ca9e593…`） |
| 控制 checkpoint sha256 前後 | 相同 |
| 控制報告 `read_at`／治療報告 `read_at` | `token`（缺鍵視為 `token`）／**`question`** |
| 同語料 | `b12cb2fb…`／`71eab688…`，且等於重新載入的語料 |
| 同預算 | `BUDGET_KEYS` 無差異；兩臂 `params` **168,150**、`training.steps` **10,000** |
| 同起點 | `start.checkpoint`／`weights_hash`／`init_weights_hash`／`params` 四項相同 |
| 對齊（train／held-out） | 都過 |
| 控制錨 `model`（§82 `boundary_query`） | 勝場 **100/200**、逐筆質量最大差 **0.0**、mismatch **0** |
| 控制錨 `cosine_unit` | 勝場 **101/200**、質量最大差 **0.0**、mismatch **0** |
| **query 恆等** | **200/200 筆**、mismatch **0**、`max_abs_diff` **0.0**（容差 2e-9） |

`query_identity` 這一條是 §84 新加的：它把「只有 store 換了、query 沒換」變成機械可檢——
提問邊界讀用的 `W_q h` 與 §82 `query` 欄的向量**逐位相同**。所以 `I0` 通過的意思是：
控制臂在同一個行程、同一個算術環境下重現 §82 的 `boundary_query` 欄（比容差更嚴：差 0.0），
治療臂與它在語料、起點、步數、參數、寫入模式上逐項相同，**只差讀點與那條最佳化軌跡**。

### 84.16 前置條件：治療臂有沒有擬合？（沒有，而且更低）

| 量 | 治療臂（`--read-at question`） | §83 治療臂（`boundary`） | 控制臂（§77 item，`token`） |
| --- | --- | --- | --- |
| `train_fit_subset.exact`（400 段） | **0.6525**（261/400） | 0.8325（333/400） | 0.9925（397/400） |
| `train_fit.exact`（前 200 段） | 0.6650（133/200） | 0.8700（174/200） | — |
| `ranking_exact`（訓練 400 段） | 0.7850 | 0.8525 | — |
| 第 200 個 epoch `mean_loss` | **0.3300**（main 0.1665／aux 0.1636） | 0.1790（0.0908／0.0882） | **0.0078**（0.0052／0.0026） |

**0.6525 < 0.90，前置條件不成立 → `Q0-fit-fails`。** 依 84.7 的理由，這個臂的 held-out 讀
**不是**讀點的檢定。

照實記一件登記時沒預期到的事：把提問回合的寫入放進讀所定址的 store 之後，擬合**不是持平，而是
更低**（0.8325 → 0.6525，最後 `mean_loss` 0.1790 → 0.3300）。§84 的登記只說「這個預算下擬合不擬合」，
沒有預測方向；方向本身在 84.20 只作假設，不作結論。

### 84.17 分支與預測檢查

| 分支 | 條件 | 這次 |
| --- | --- | --- |
| `E0-instrument` | `I0` 失敗 | 否（84.15 全過） |
| **`Q0-fit-fails`** | 治療臂 `train_fit_subset < 0.90` | **是（0.6525）** |
| `Q2-pass-but-regression` | 主格過、不迴歸不過 | 未達（被 `Q0` 先攔下） |
| `Q1-read-at-question-works` | 主格過且不迴歸過 | 未達 |
| `Q3-fits-but-no-gain` | 擬合過、主格不過 | 未達 |

**登記的主預測 `Q3-fits-but-no-gain` 落空**，登記的替代 **`Q0-fit-fails` 成立**。
`Q0` 的意義是「這一格沒被測到」：既不是「提問邊界的固定讀定址失敗」的證據，也不是它的否證。
這是連續第二節主預測落空（§83 的 `T1`、§84 的 `Q3`），兩次都落在「沒擬合」那一側；照實記，
不改寫預測、不改門檻。

### 84.18 登記的 `next`：同臂重跑，地板**逐位**複現

`Q0` 的 `next` 是「重跑同一條已登記的臂（不改讀法、不改預算），在任何格子被讀之前先報損失地板
是否複現」。原樣重跑（只換 `--out`），環境與 §84.13 相同：

* wall **27:06.32**（腳本計時 **1,625.0 s**）、user 6,466.49 s／sys 11.01 s、CPU **398 %**、
  峰值 RSS **782,832 kB**、**swap 0**、exit 0；產物在 `data/pantry_stage/readrule84/repeat/`。
* **逐項相同**：`train_fit_subset` **0.6525**（261/400）、`train_fit` **0.6650**、`ranking_exact`
  **0.7850**／**0.5050**、`full` **0.3850**、最後一個 epoch `mean_loss` **0.3300**
  （main 0.1665／aux 0.1636）、最低 **0.2805 @195**、`weights_hash` **完全相同**
  （`sha256:b8d98a79…`）。

讀法：**這個損失地板在登記的環境裡是確定性的，不是一次性的壞運**（與 §83 的重跑同一個結論）。
重跑只證明可複現，**不**證明它跨語料種子或跨架構成立（84.21 第 6 條）。

### 84.19 描述量（在 `Q0` 之下，不是本節的證據）

同一批 held-out 200 次讀，照登記的格子算出來（`Q0` 說這些數字不能當讀點的檢定）：

| 臂／規則 | 勝場 | 二選一 | Wilson 95% | p | 虛無 ge | 名冊質量 | argmax 在名冊 | argmax 落點（200 筆） |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 控制／`model` | 100/200 | 0.5000 | 0.4314–0.5686 | 1.0 | 400 | 1.0 | 1.0 | 槽 2：**200** |
| 控制／`cosine_unit` | 100/200 | 0.5000 | 0.4314–0.5686 | 1.0 | 400 | 0.175673 | 1.0 | 槽 2：**200** |
| 治療／`model` | 101/200 | 0.5050 | 0.4363–0.5735 | 0.493766 | 197 | 0.990000 | 0.99 | 槽 1：**197**、槽 0：2、槽 2：1 |
| 治療／`cosine_unit` | 102/200 | 0.5100 | 0.4412–0.5784 | 0.254364 | 101 | 0.179333 | 0.99 | 槽 1：**197**、槽 0：2、槽 2：1 |

**不迴歸**（在**治療載體**上重新擬合 §79 的兩格，held-out 400 筆，400 次重擬合虛無）：

| 格子 | 勝場 | 二選一 | Wilson 95% | p | 8 路 top-1 | §82 閘門 |
| --- | --- | --- | --- | --- | --- | --- |
| `entry_key`（鍵→顏色） | 337/400 | **0.8425** | 0.8036–0.8749 | 0.002494 | 0.5475 | **過** |
| `entry_value`（值→顏色） | 312/400 | **0.7800** | 0.7368–0.8178 | 0.002494 | 0.4325 | **過** |

其他描述量：治療報告 held-out `full` **0.3850**（控制 §77 是 0.3700）、`ranking_exact` **0.5050**
（控制 0.5250）；`in_roster` 132/200（0.6600，chance 1/6），`distinct_predictions` 12。
這些都不進任何閘門。

**描述性診斷（不是格子，不裁決；`data/pantry_stage/readrule84/slots_diagnostic.json`，gitignored）**：
名冊兩筆的槽是 **`[1, 2]`**，提問回合自己的寫入落在**槽 4**（前 4 段 held-out 逐一相同）。所以
control／model 的 argmax 落在槽 2 **200/200**、治療／model 落在槽 1 **197/200**——兩者都在**名冊內**，
但都是**同一個槽**。名冊順序是平衡的（每槽一半），所以「永遠偏好同一個名冊槽」這個讀法**在二選一
上就只能得 ~0.5**：控制 100/200、治療 101/200 正是這個結構的算術結果，而不是「接近 chance 的巧合」。
這也意味著：這兩個固定讀在這一格上**沒有區分兩筆名冊**，只是各自固定選了一邊。

### 84.20 為什麼沒擬合（診斷，不是另一個量測）

事實先列清楚：

1. **兩臂從同一個損失出發**（2.5809 vs §83 的 2.5805），到第 200 個 epoch 治療臂停在 **0.3300**、
   §83 的臂停在 **0.1790**、控制臂到 **0.0078**。不是初始化或資料不同，是**能到達的損失地板不同**。
2. **§83.19 的兩個原因已被這一節切開一半**：把提問回合的寫入放進 store（也就是移除「讀在提問寫入
   之前」）**沒有**讓臂擬合，所以「讀取在提問寫入之前」**不是**擬合地板的原因。兩條臂共同剩下的
   因素是**一個固定讀向量**。
3. **但方向反了**：擬合從 0.8325 **降到** 0.6525。登記沒有預測方向，所以這是登記之外的觀察，只能
   當假設的來源。
4. **寫入側仍然可分**：同一個治療載體上，§79 的兩格是 **0.8425／0.7800**（84.19），比凍結載體上的
   0.7375／0.6200 更高。所以「store 裡沒有顏色」不是解釋；缺的是**讀**。
5. **讀在這一格沒有區分兩筆**：固定讀的 argmax 幾乎恆定居 1 或槽 2（84.19 的診斷）。

**假設（沒有被單獨量測）**：`--read-at question` 讓每一個解碼都帶著「自己那一回合剛寫入」之後取出的
向量；這個向量要同時（a）忽略剛寫入的槽 4、（b）在兩個名冊槽之間選對，而它是一個**與解碼位置無關的
常數**。相比之下 `--read-at boundary` 的常數至少不包含「剛寫入」這個最近的干擾項。若如此，擬合更低
是「固定讀要多忽略一項」的結果，而不是「位置更對」的結果。

**不是**的結論：不是「提問邊界的讀定址失敗」（那一格沒被測到，84.17）、不是「固定讀永遠學不會」
（單一預算、單一語料種子、單一臂），也不是「寫入退步」（84.19 的兩格反而更高）。

### 84.21 照實記的限制（追加在 84.11 之後）

1. **`Q0` 只說「沒測到」**：84.19 的四格、不迴歸的兩格、held-out `full` 與 `slots_diagnostic`
   都是描述量，不是讀點的證據。任何把「治療／`model` 101/200」讀成「提問讀無效」的說法都越過了
   登記的分支。
2. **登記的主預測落空、替代成立**：`Q3` → `Q0`。照實記，不改寫預測、不改門檻。
3. **擬合方向不在登記之內**：§84 只登記「擬合或不擬合」，沒有登記「會不會更低」。0.8325 → 0.6525
   是觀察，84.20 的解釋是假設；要判斷它需要另一條臂，不是這一節的補救。
4. **`slots_diagnostic` 的範圍**：槽身分（名冊 `[1,2]`、提問寫入槽 4）用前 4 段 held-out 逐一確認；
   argmax 落點用探針的 200 筆統計。它沒有進入任何閘門，也沒有改動任何常數。
5. **執行緒數不同**：治療臂 4 個執行緒（與 §83 的治療臂相同，這是刻意的），控制臂是 §77 的
   5 個執行緒（§83.20 已記）。探針在 §82 的 2 個執行緒下跑，錨差 **0.0**。
6. **單一語料種子（20261127）、k=2、單一 stage-L 起點、一條治療臂**；§75 已量到幅度不跨種子複現。
   逐位重跑只說明**同一個環境**下確定性，不說明跨種子。
7. **`M` 前綴的交叉檢查仍然是空的**（同 §83.20 第 5 條）：治療報告的閘門叫
   `M1_fits_the_declared_items`（**false**），探針的 `fit.report_gate` 是 **null**；擬合是直接
   套算術 0.6525 < 0.90，沒有繞過，但「名稱交叉檢查」這一條沒有執行。
8. **成本照實記**：治療 29:20 + 重跑 27:06 + 探針 5:01，共 **約 61 分鐘** 機時；全部在
   `CPUQuota=400%/400%/200%`、swap 0、GPU 0% 之下。
9. **這是探針，不是生成**：核心分不變 **0.00/10**（§275）；輸出只寫
   `data/pantry_stage/readrule84/`（gitignored）。

### 84.22 下一個登記（`Q0` 的 `next` 之後；本節只寫問題）

84.9 對 `Q0` 的 `next` 是「同臂重跑、先報地板是否複現」。做了（84.18，逐位相同）。`Q0` 的
`reading` 也把共同因素講清楚了：**一個固定讀向量**。下一個問題因此是分離「**在整個解碼中固定**」
與「**只在解碼邊界取一次**」：

> 在**提問邊界**的 store 上，讓回答解碼的**每一個 token 都重新定址**（`token` 臂的讀法），
> 但 store 是 `snapshots[q]`——**零新增參數、同一個 10,000 步／168,150 參數／同一份語料**——
> 這個臂會不會擬合？若會，§83／§84 的擬合地板就是「固定」，不是「位置」；若仍然不會，
> 共同因素就不只是「固定」。

這是一條**新的 `read_at` 值**（暫稱 `question-token`），與 `question` 只差「固定或每 token 重取」，
其餘逐項相同。**它必須在自己的小節裡先登記再跑**，包括擬合地板、主格、不迴歸、分支與預測。

這一節另外留下一個必須寫進下一個登記的約束（84.19 的診斷）：**「讀的 argmax 落在名冊內」不等於
「讀區分了兩筆名冊」**。控制與治療的固定讀都是**固定一個槽**（200/200、197/200），而名冊順序平衡，
所以二選一自然 ~0.5。下一個登記在讀格子時，必須先說清楚「什麼算區分」——例如同一段 session 內
兩筆名冊的質量**隨正解換邊**，而不是「有質量在名冊上」。

**§84 的裁決是 `Q0-fit-fails`**：把讀移到提問回合自己的邊界並固定，這個臂在這個預算下**沒有擬合**，
而且比 §83 更低；因此那個讀的定址能力**沒有被測到**，§83.19 的「位置」假設**被否證**（不是被支持），
剩下的共同因素是「固定」。核心分仍 **0.00/10**。

## §85 階梯：把 2.5M 直接長成 12M 再繼續訓，還是重來（登記）

### 85.1 這一節問什麼

§34 把「規模」這個槓桿拉到 10⁸（108.6M、1 epoch、XPU）並量到 0/40 數學、0/15 知識、0/10 代碼，
所以「再放大」不是下一個槓桿。但 §34 是一次**從隨機初始**開始的 10⁸ 訓練；它沒有回答另一個問題：

> 已經付過的訓練，能不能不要重付？也就是把 2.5M 的權重**直接長成 12M**，接著訓，
> 而不是每一個更大的模型都從隨機初始開始。

這個問題有兩半，必須分開量：

1. **機械上可不可以**：加寬後的孩子還在不在原地（同一組輸入、同一組輸出）？——已量，見 85.2。
2. **科學上有沒有效**：在同一個 token 預算下，加寬後繼續訓會不會比**留在原寬度繼續訓**得到更好的
   泛化？——這一節要登記的就是這一半。

第 2 半是可裁決的比較，不是哲學問題：**A（加寬後繼續）對 C（原寬度繼續）**，同一份列、同一個順序、
同一個 lr、同一個步數。B（同寬度從隨機初始）只是參照，不是裁決臂。

### 85.2 登記前已經量到的（照實寫）

| 項目 | 值 | 怎麼量的 |
| --- | --- | --- |
| 母模型 | `apps/backend/data/models/token_snn_distill.pt`，sha256 `445d4824…`，2,491,227 參數，`d_emb 96 / d_hidden 512 / 1 layer / vocab 3,577 / readout membrane` | `TokenSNN.load` |
| 加寬 ×4 | **12,069,723** 參數（4.84×），建立 **1.14 s**（1 執行緒） | `scripts/expand_token_snn.py` |
| 加寬的同一性 | 同一探針批次 `max|Δlogit| = 3.8e-06`，相對 **5.9e-08**（logit 尺度 65.0） | `data/ladder85/expand_x4.json` 的 `preservation` |
| 打破對稱的噪聲 | 新副本的輸入列加 `1e-3`（相對標準差）→ 相對漂移 **1.4e-04** | 同上 |
| 母模型在 `distill_val`（281 列）的 CE | **5.6964** | teacher-forced，batch 8 |
| 加寬孩子在 step 0 的 CE | **5.6963** | 同上；這是本節的 `I0-1` |
| 同寬度隨機初始 12M 的 CE | **8.3575** | `torch.manual_seed(0)` |
| 母模型在 `distill_val_holdout`（248 列）的 exact | **28/248 = 11.3%** | `exact_match(sample=0, seed=3)`，`_response_only` |
| 母模型的擬合程度 | 100 epochs 後 train loss **0.52**；前 200 列 CE **0.8799**（同時間 val 5.6964） | `data/intelligence_reports/token_snn_distill.json`＋本節量測 |
| 訓練／驗證重疊 | train∩val **0**、train∩holdout **0**（holdout ⊂ val，248/281） | 集合比對 |
| 每列成本（batch 1、2 執行緒） | 2.5M **14 ms/列**；12M **118 ms/列**（8.4×） | 同一批 `distill_train` 列 |

兩件要說清楚的事：

1. **母模型是過擬合的**（train 0.88／val 5.70，且 train loss 還有 0.52 的下探空間）。所以這一節量的是
   「在一個已經記住語料的母模型上，加寬是否還有效」，不是「在一個健康的母模型上」。寫進 85.8。
2. **參數不是算力**：×4 的參數只長 4.84 倍，每列成本長 **8.4 倍**（`w_rec` 隨隱藏層平方長、輸出頭隨
   隱藏層線性長）。階梯省下的是「已付過的訓練」，不是「之後每一步的價格」。

### 85.3 凍結的三條臂（跑之前寫定）

| 臂 | 起點 | 寬度 | 用途 |
| --- | --- | --- | --- |
| **A `warm`** | 上面的母模型，`expand_model(factor=4, noise=1e-3)`，噪聲種子 = 該 seed | 12,069,723 | **裁決臂**：長大後繼續訓 |
| **B `cold`** | 全新 12M，`torch.manual_seed(seed)` | 12,069,723 | 參照：同樣寬度從隨機初始在同預算下到哪 |
| **C `width_control`** | 母模型的同一份權重（重新載入） | 2,491,227 | **裁決臂**：留在原寬度繼續訓 |

三條臂逐項相同：`distill_train.jsonl` 全部 5,144 列、`epochs=2`、`batch=8`、`lr=1e-3` **常數**
（不用 cosine）、`tail_weight=1.0`、`ss_final=0`、`guard` 開、`seed ∈ {0,1,2}`（三條臂各三個 seed）。
`train_on` 內部以 `seed+epoch` 重排，所以同一 seed 的三條臂看到**同一個順序**（`I0-3` 驗）。

### 85.4 讀點與計分格子（跑之前寫定）

| 格子 | 定義 | 角色 |
| --- | --- | --- |
| **主格 `val_ce`** | `distill_val`（281 列）teacher-forced CE，batch 8，每條臂在 **step 0** 與**每個 epoch 後**各量一次 | **裁決**（A 對 C，三個 seed 的平均） |
| **共同主格 `holdout_exact`** | `distill_val_holdout`（248 列）`exact_match(sample=0, seed=3)`，`_response_only`，只在最後量一次 | **裁決**（A 對 C） |
| 描述量 `train_ce200` | `distill_train` 前 200 列的 CE | **`N0` 的判準**（85.5），其餘不裁決 |
| 描述量 `seconds` / `ms_per_row` | 每條臂的訓練牆鐘與每列成本 | 算力，不裁決 |
| 描述量 `b_vs_a` | B 的終點與 A 的終點 | 只看「暖起點是否至少勝過隨機初始」 |

### 85.5 分支與門檻（跑之前寫定，優先序由上到下）

| 分支 | 條件（三 seed 平均） | 意思 |
| --- | --- | --- |
| `N0-unusable` | `A_train_ce200` 在預算內下降 **< 0.15** | 加寬後的孩子**沒學到**（訓練損失沒動），其他比較都不成立 |
| `N1-ladder-pays` | `A_final ≤ C_final − 0.15` **且** `A_exact ≥ C_exact + 5 列` | 多出來的寬度在同 token 預算下換到泛化 |
| `N3-ladder-hurts` | `A_final ≥ C_final + 0.15` **且** `A_exact ≤ C_exact − 5 列` | 加寬後繼續訓比留在原寬度更差 |
| `N2-no-resolvable-gain` | `|A_final − C_final| < 0.15` **且** `|A_exact − C_exact| < 5 列` | 這個預算下兩把尺都分不出差別 |
| `N4-inconsistent` | 兩把尺各自越過自己的門檻，但**方向相反** | 兩個儀器不一致，這一節不作裁決 |

門檻的理由（先寫，不能事後改）：`0.15 nats` 是 `TRAINING_INTERNALS §11.1` 量到的初始化／順序散佈
（0.012–0.062 nats）的約 2.5 倍；`5 列` 是 248 列上約 2.0pp，比二項抽樣在 11% 附近的 ±2 列抖動寬。
`N2` 的讀法是「**這個預算下分不出來**」，不是「證明相等」。

**登記後的修正（跑之前，尚未產生任何結果）**：`N0` 原本寫的是「`A_final ≥ A_start − 0.15`」，
也就是看**驗證** CE 有沒有改善。這個寫法會讓 `N3` **永遠不可能成立**——加寬若真的有害，驗證 CE 通常
就是往上升，於是每一條「有害」的臂都會先被判成「什麼都沒學到」。修正為看**訓練** CE（前 200 列）：
`N0` 現在問的是「加寬後的孩子到底有沒有在學」，而「學了但泛化更差」交給 `N3`。兩個閘門用同一個
0.15 nats 邊界，沒有新增門檻。

### 85.6 儀器 `I0`（跑完後檢查，任何一項不過則整節作廢）

1. **同一性**：A 在 step 0 的 `val_ce` 與母模型相差 ≤ 1e-4（85.2 已量到 5.6963 對 5.6964）。
2. **無洩漏**：train∩val、train∩holdout 都是 0（85.2）。
3. **同一個順序**：三個 seed 各自在 epoch 0 的重排 digest 在 A／B／C 三臂相同（`random.Random(seed)` 重算）。
4. **同一個預算**：三臂的優化步數相同（`ceil(5144/8) × 2 = 1,286`）、batch 相同、lr 相同。
5. **不覆寫母模型**：所有產物只寫 `data/ladder85/`；母模型 sha256 跑完不變。

### 85.7 預測與否證（跑之前寫定）

**主預測：`N3-ladder-hurts`（中等信心）**。理由：母模型的 train loss 還有 0.52 的下探空間，而 val
CE 已經 5.70；12M 的容量會先被用來把那 0.52 壓下去（記得更牢），val CE 因此**上升**，而 2.5M 的 C 臂
升得較少。若如此，A 的 `val_ce` 會高於 C，且 `holdout_exact` 不會上升。

**替代（登記在案，不算事後解釋）**：若加寬真的解開了容量瓶頸，會走 `N1`；若兩把尺都分不出，走 `N2`。

**否證**：任何與 `N3` 方向相反且越過門檻的結果（`N1`），或落在 `N2`／`N4`，都算主預測落空，照實記。

### 85.8 照實記的限制（跑之前寫定）

1. **單一母模型、單一語料、一級階梯**（2.5M→12M，×4）：`N2`／`N3` 只說明**這一級、這個母模型**，
   不說明階梯在別處一定無效。
2. **母模型過擬合**：這一節測的是「從一個記住語料的母模型往上長」，不是「從一個泛化好的母模型往上長」。
3. **只有 teacher-forced CE 與 in-distribution exact**：不是能力分，也不進核心分（§275）。
4. **三個 seed 只夠估散佈**，不足以做區間估計；`N2` 不等於「相等」。
5. **每列成本在 batch 8 下量**（85.2 的 8.4× 是 batch 1）：階梯的價格要用同一 batch 下的
   `ms_per_row` 重算，這一節會照實記兩者，不混用。
6. **不是生成**：核心分仍 **0.00/10**；本節的任何 CE 下降都不改變那條線。

### 85.9 命令與執行上限（跑之前寫定）

```bash
OMP_NUM_THREADS=2 systemd-run --scope --user \
  -p CPUQuota=200% -p MemoryMax=1800M -p MemorySwapMax=0 \
  ./.venv/bin/python scripts/probe_ladder85.py --seeds 0,1,2 --epochs 2 --batch 8 --lr 1e-3
```

預算：約 **35–45 分鐘**（6 條 12M 臂 × 約 5 分鐘＋3 條 2.5M 臂＋9 次 held-out exact），
CPU 上限 200%（12 核機器上 16.7%）、RAM 上限 1.8 GB、swap 0、GPU 0%。

### 85.10 結果（跑完，照實寫）

**執行**：2600.9 秒（43.4 分鐘），`CPUQuota=200%`、`MemoryMax=1800M`、`MemorySwapMax=0`，GPU 未使用。
報告：`data/ladder85/report.json`（gitignored）。`--check` 重算 9 條臂的兩個量測並重算分支：**通過**
（`probe_ladder85 check OK (N0-unusable, 9 arms recomputed)`）。

#### I0 儀器檢查（§85.6）

| 項 | 量測 | 判定 |
| --- | --- | --- |
| 同一性：A 在 step 0 的 `val_ce` vs 母模型 5.696410 | seed0 5.696347（Δ 6.3e-5）、seed1 5.696427（Δ 1.7e-5）、seed2 5.696377（Δ 3.3e-5） | 通過（≤ 1e-4） |
| 無洩漏 | `train∩val = 0`、`train∩holdout = 0`、`val∩holdout = 248`（holdout 是 val 的子集，登記時就是） | 通過 |
| 同一順序 | 每個 seed 的 epoch 0 重排 digest 在三臂相同（`random.Random(seed)` 重算） | 通過 |
| 同預算 | 三臂 `ceil(5144/8) × 2 = 1,286` 步、batch 8、lr 1e-3 常數 | 通過 |
| 不覆寫母模型 | `parent_unchanged: true`；母模型 sha256 與跑前相同 | 通過 |
| 沒有 rollback | 9 條臂的 18 個 epoch 全是 `rolled_back: false` | 通過 |

#### 三臂（3 seeds 平均；括號是 min–max）

| 臂 | 參數 | 起點 val CE | 終點 val CE | 終點 sd | holdout exact | ms/row | 每臂秒數 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A `warm` | 12,069,723 | 5.6964 | **3.6641** (3.5444–3.7345) | 0.1042 | **18/248（7.3%）** | 39.4 | 405.8 |
| B `cold` | 12,069,723 | 8.3675 | **2.5824** (2.5511–2.6054) | 0.0280 | **1.7/248（0.7%）** | 37.9 | 389.5 |
| C `width_control` | 2,491,227 | 5.6964 | **4.6317** (4.5240–4.7156) | 0.0980 | **24.7/248（9.9%）** | 3.9 | 39.7 |

逐 seed 的 `C − A`：CE `+0.9211 / +1.0022 / +0.9795`（平均 **+0.9676**，sd 0.0418）；
holdout `−7 / −2 / −11` 列（平均 **−6.7**）。母模型自己的 holdout 是 **28/248（11.3%）**，
是全場最高的一個數字。

#### 登記的裁決：`N0-unusable`——而這個裁決**不能當成結論**

照 85.5 的表，`N0` 先觸發：`A` 的 `train_ce200` 由 0.8799 **升到** 1.3039（沒有下降 0.15），
所以其餘三條分支都不看。**但 `N0` 這把尺在這裡是壞的，必須照實寫出來**：

1. `train_ce200` 取的是 `distill_train` 的**前 200 列**，而母模型在那一小段上的 CE 已經是 **0.8799**
   ——那是**背下來的**，不是還沒學會的。一個已經接近 0 的量，本來就沒有 0.15 nats 的下探空間，
   它只會因為後續訓練被推開而上升。
2. 同一條臂的**全語料**訓練損失其實是**下降**的：1.3282 → 1.1221（seed0）、1.3302 → 1.1164（seed1）、
   1.3470 → 1.1115（seed2）；驗證 CE 也從 5.70 掉到 3.66（−2.03 nats）。
3. 所以「加寬後的孩子沒學到」在**描述上就是錯的**。`N0` 量到的是「母模型背過的那 200 列被遺忘了」，
   不是「沒有學習」。

這是**登記錯誤**（85.5 的修正把 `N0` 從驗證 CE 改成訓練 CE，動機是不要讓 `N3` 不可能成立；
結果換成一個**沒有餘裕**的訓練切片，讓 `N1`／`N3` 都不可能成立）。依規則**不修改門檻、不改判準**，
`report.json` 裡的 `branch` 就是 `N0-unusable`；但這一節**不作裁決**，理由寫在上面。

#### 把壞掉的 `N0` 拿掉之後，**登記表自己**會說什麼

不是新規則，是 85.5 表格剩下的部分套上去：`|ΔCE| = 0.97 ≥ 0.15` **且** `Δitems = −6.7 ≤ −5`，
兩把尺方向相反 → **`N4-inconsistent`**。也就是說：在這個預算、這個母模型上，
**CE 說加寬＋續訓比較好，exact 說比較差**。這一節因此**既不成立 `N1`，也不成立 `N3`**。

#### 預測檢查（85.7 登記的是 `N3`，中等信心）

| 登記的預測 | 結果 |
| --- | --- |
| `N3`：A 的 val CE 高於 C，且 holdout 不上升 | **一半對**：holdout 確實下降（18 vs 24.7，−6.7 列 ≥ 5 的門檻）；但 val CE **低於** C 0.97 nats（門檻 0.15），方向相反 |
| 替代 `N1` | 不成立（holdout 反向） |
| 替代 `N2` | 不成立（兩把尺都越過門檻） |

主預測**落空**（CE 那一半），照實記。

#### 兩個沒有登記、但比裁決更重要的觀察

1. **續訓本身讓 exact 變差**：母模型 28/248 → A 18/248、C 24.7/248。兩條臂都付了 CE（5.70 → 3.66／4.63）
   卻都掉了 exact。這一小段語料、這組超參數下，**CE 與 greedy exact 不是同一個方向**——這正是
   85.4 把兩個量測都登記成共同主要讀點的原因。
2. **A 比 C 好的部分，是母模型背下來的答案，不是新的學習**：B（同寬度、同預算、隨機初始）拿到**最好**的
   CE（2.58）卻只有 **1.7/248** 的 exact；A 的 CE 差 1.08 nats，exact 卻高 16.3 列。把權重加寬再續訓，
   保住的是**記憶**（教過的答案還在），不是**泛化**。這與 §272／§275 的「記憶 ≠ 學習」一致：
   §85 沒有推翻它，反而在 12M 尺度上重現了一次。

#### 計算成本（同一 batch 8，照 85.8-5 的要求重算，不混用 batch 1 的 8.4×）

| 比較 | ms/row | 倍數 |
| --- | --- | --- |
| A（12M）對 C（2.5M） | 39.4 vs 3.9 | **10.1×** |
| B（12M）對 C | 37.9 vs 3.9 | 9.8× |

母模型 val CE 5.70、train loss 0.52 的起點是**先前那 100 個 epoch**（batch 64、lr 3e-3）付掉的；
本次三臂各 2 個 epoch、1,286 步。所以「階梯」在這一節**沒有省下任何計算**：A 與 B 的秒數幾乎相同
（405.8 vs 389.5），A 只是多繼承了一份更早的權重。它省下的是「重跑那 100 個 epoch」，
但那 100 個 epoch 已經花掉了——**沉沒成本不是折扣**。

### 85.11 增量計算：改了什麼才重算（這一節不是分數）

§85 的 43 分鐘裡，絕大多數是**已經算過的東西**。新增的 `scripts/incremental.py` 把每一個臂的結果
存成一個 **unit**：`plan` 是「所有能改變這個結果的輸入」，key 是 `plan` 的 sha256；cache **只在
plan 相同、而且每個 artifact 的 sha256 仍然對得上**時才回傳結果（檔案不見、被改、JSON 寫一半 → 一律 miss）。

`plan` 的內容與**失效規則**（`probe_ladder85.arm_plan()` 是唯一來源，計算與查表共用同一個函式）：

| 改變 | 會失效嗎 | 為什麼 |
| --- | --- | --- |
| 母模型檔案（sha256） | 會 | 不同的起點 |
| 語料三份（`rows` 的內容 digest，不是列數） | 會 | 不同的輸入 |
| 協定（epochs／batch／lr／factor／noise／guard／…） | 會 | 不同的實驗 |
| **計算它的程式**（`token_snn.py`、`expand_token_snn.py`、`train_token_snn.py`、`probe_ladder85.py` 的 digest） | 會 | 結果是那些程式產生的 |
| 只**增加一個 seed** | 不會（只算新的那個） | 其他 seed 的 plan 沒變 |
| 改 `--report` 路徑、換 cache 目錄名稱 | 不會 | 不是 plan 的一部分 |

實測（同一台機器、同一個 2-core 配額）：

| 動作 | 結果 | 時間 |
| --- | --- | --- |
| `--adopt-report`（把跑完的報告登記成 units，**先逐臂重算** val CE 與 holdout 才接受） | 9 條全收、0 條拒絕 | — |
| 原命令重跑一次 | **0 computed / 9 reused**，數字完全相同 | **6.1 s**（原本 2,600.9 s，≈426×） |
| `--arms width_control --seeds 0,1,2,3`（多一個 seed） | **3 reused / 1 computed**（只有 seed3） | 54.7 s（其中 47 s 是 seed3 的 2 個 epoch） |
| 只算 `width_control/seed0` 1 個 epoch，再延伸成 2 個 | 第 2 個 epoch 只花 **23.0 s** | 兩次共約 47 s |
| 延伸後的 checkpoint vs 一次跑完 2 epoch 的 checkpoint | **10/10 個 tensor 位元相同，max\|diff\| = 0.0**；CE 4.6556、holdout 28/248 也相同 | — |

延伸之所以**等於**一次跑完，而不是「差不多」：`TokenSNN.train_on` 新增 `start_epoch`（batch 順序與
torch seed 都由 `seed + epoch` 決定，所以是**接續**而不是重排）與 `opt_state`（Adam 的一、二階動量），
以及 `guard_state`（rollback 會還原最佳權重並把 lr 減半；少了它，續跑就會用不同的權重與不同的 lr
進入下一個 epoch）。測試用**強制 rollback**（`diverge_factor=1e-9`）比對整份 `state_dict`，也通過。

**這條規則在這一輪真的觸發過**：寫完報告後修了 `check()` 的一個儀器 bug（把「holdout ⊂ val」誤判成洩漏），
`probe_ladder85.py` 的 digest 因此改變，先前登記的 **10 個 unit 全部失效**——所以 cache 是重建後重新
adopt 的，上表的 6.1 s 是重建之後量到的。這不是缺點，是設計：那 10 個結果是由**不同的程式**算的。

照實記的限制：

1. **第一次不會變快**。增量只省「已經付過的」，43 分鐘的第一跑一毛都省不掉。
2. **pre-cache 的產物可以重用、不能延伸**：舊報告沒有存優化器狀態，`prefix_unit` 因此不把它當成可續跑
   的前綴（勉強續跑會讓 Adam 從零開始，結果不再是同一條臂）。
3. **它不會讓失效的結果變有效**：改了程式就是重算，cache 不會替舊數字背書。
4. **單一機器、單一 cache 目錄**：沒有鎖；兩個進程同時寫同一個 cache 不在這一輪的保證內（本輪所有
   指令都是序列執行的）。

### 85.12 這一節回答了什麼、沒回答什麼

- **「增量訓練是不是一條路」**：作為**節省重算**，是——但只對已付過的 epoch 有效（85.11）。
  作為**能力捷徑**，不是：A 繼承了母模型的記憶（18 vs 1.7 的 exact），CE 卻比同寬度、同成本的隨機
  初始差 **1.08 nats**，而對照「不加寬」則貴 **10.1×** 且 exact 更差（−6.7 列）。加寬續訓買到的是
  **母模型已經背下來的東西**，不是它沒學會的東西。
- **沒回答**：`N1` 還是 `N3`。`N0` 的儀器壞了（85.10），而兩個主要讀點方向相反（`N4`）。
  要裁決需要**重新登記**一次：`N0` 必須用**有餘裕**的量（例如全語料訓練損失，或一個母模型沒背過的
  切片），而且要在跑之前寫定。這一輪**不做**這件事——在看到結果之後改判準，就是事後解釋。
- **核心分不變**：A／B／C 的 exact 是 7.3%／0.7%／9.9%，都不是生成，也不進核心分；核心仍 **0.00/10**（§275）。

### 85.13 量測本身的弱點（跑完才看得出，照實記，不改裁決）

上面 `N4` 的結論不變，但這一輪暴露出**兩個儀器問題**，下一個註冊必須先修，否則再跑一次也只會得到
另一組「分不出來」：

1. **`N0` 的切片沒有餘裕**（85.10 已寫）：母模型在 `train_ce200` 上已經 0.8799。要當「有沒有在學」的
   閘門，量必須**跑之前就知道有下探空間**，例如全語料訓練損失（這一輪實測 1.33 → 1.12），或一個
   母模型**沒有背過**的切片。
2. **5 列的門檻比 seed 雜訊小**：登記時用二項抽樣（248 列、11% 附近）算出 ±2 列，所以取 5 列；
   但三 seed 的**逐 seed 差**是 `−7 / −2 / −11`，樣本 sd = **4.5 列** → 門檻只有 **1.11 個 sd**。
   對照之下 CE 的逐 seed 差 sd 是 0.042，門檻 0.15 = **3.6 個 sd**。也就是說：
   **CE 這把尺在 n=3 下解析度夠，exact 這把尺不夠。** 因此「warm 的 exact 比 control 少 6.7 列」
   只能讀成方向一致（三個 seed 全為負），不能讀成「少了 6.7 列的確定估計」。
   下一輪若要用 exact 裁決，門檻必須 ≥ 2 個觀測 sd（≈ 9 列），或把 seed 數加到能讓 sd 收斂。

另外一個不是缺陷、但必須寫進下一輪讀法的東西：**exact 會獎勵背下來的答案**。母模型 28/248 是全場最高，
而兩條續訓臂都掉到 18／24.7，cold 只有 1.7；所以「exact 高」在這份語料上同時可能是「記得比較多」。
只報 exact 會把記憶誤讀成能力，必須同時報母模型的 exact 當基線。

**下一輪的登記清單（本輪不登記、不跑，只是把必要條件寫下來）**：

- `N0` 用量之前先記錄**餘裕**（母模型在該量上的值與可下探空間），不能用量完才知道會動的量。
- 每個裁決量都要有**逐 seed 散佈**，門檻以 sd 為單位寫（CE ≥ 3 sd、exact ≥ 2 sd），不用二項抽樣代替。
- 共同主要讀點若方向相反，照 85.5 報 `N4`，**不得事後加權**把其中一把尺壓下去。
- 報表同時列出**記憶基線**（母模型的 exact），否則無法區分「泛化」與「還記得」。

## §86 重新登記：換掉壞掉的閘門，用**沒跑過的 seed** 裁決同一個問題（登記）

### 86.1 為什麼要重新登記，以及為什麼不能就地改 §85

§85 的 `N0` 是在**跑之前**修正的（驗證 CE → 訓練 CE，動機是不要讓 `N3` 不可能成立），但換成了
`distill_train` 前 200 列——母模型在那一小段上已經是 **0.8799**（背下來的），沒有下探空間。結果
`N0` 先觸發，其餘分支不看，§85 因此**不作裁決**（85.10／85.13 已照實記）。

看到結果之後才換判準就是事後解釋，所以：

1. §85 的欄位**不動**：`report.json` 的 `branch` 仍是 `N0-unusable`，§85 仍然不作裁決。
2. §85 的 seed 0/1/2 **已經看過**，所以不能拿同一批資料重新裁決。**§86 用 seed 3/4/5**，這三個 seed
   在任何一輪裡都沒有跑過（`data/ladder85/` 只有 0、1、2 與一次 seed 3 的 `width_control` 單臂
   增量測試，後者只驗證快取，見 85.11；為了不讓它混進裁決，`data/ladder86/` 用**自己的快取目錄**，
   不重用 §85 的 unit）。
3. 這不是「換一個對自己有利的門檻」：移除 `N0` 之後 §85 的資料是 **`N4`**（CE 說 A 好 0.97 nats、
   exact 說 A 差 6.7 列），**既不是 `N1` 也不是 `N3`**。拿掉 `N0` 沒有讓任何一條分支更容易成立，
   它只是讓「訓練損失的拉鋸」不再冒充「有沒有學」。

### 86.2 登記前已經量到的（都不是裁決結果）

| 項目 | 值 | 怎麼量的 |
| --- | --- | --- |
| 母模型的**全語料訓練 CE**（本節的新尺） | **0.7039** | `mean_ce(parent, distill_train 5,144 列, batch 8)`，3.9 s |
| 母模型**逐列** CE 的分佈 | 中位數 0.4128、平均 0.6279、CE>1 的列佔 **23.5%**、最差 5 列 20.15/15.75/15.56/11.87/11.69（長度 31/10/38/62/7） | 逐列前向，同一份 5,144 列 |
| 母模型的 **hold-out exact**（記憶基線） | **28/248** | §85.10 已量；§86 報表會重算並並列 |
| §85 的**逐 seed 配對差**散佈 | CE sd **0.042**、exact sd **4.5 列** | §85.13，逐 seed 差 −7/−2/−11 |

三件事照實寫：

- **0.7039 不是 §85 曲線上的 1.3282**。曲線的 `train_loss` 是訓練時每個 epoch 的損失（逐 token
  加權、含 tail 權重），本節的 `train_ce_full` 是 `mean_ce`（每批平均再平均，batch 8）。**兩者不可互比**，
  報表會分開列。
- 0.7039 的「下探空間」是 0.7039，但那一格同時被兩股力量拉扯：母模型背過的列會被**忘掉**（§85 的
  `train_ce200` 0.88 → 1.30 就是忘記），中段的列會被**學會**。**這種拉鋸不能回答「有沒有在學」**——
  見 86.3。
- exact 這把尺在 n=3 的解析度是 4.5 列（1 sd）；§85 的 5 列門檻只有 1.1 sd，所以 85.13 的處方是
  **≥2 sd**。

### 86.3 這一節改什麼、不改什麼（跑之前寫定）

| 項目 | §85 | §86 | 為什麼 |
| --- | --- | --- | --- |
| 臂（warm／cold／width_control）、資料、順序、lr、步數、factor、noise、guard | 見 85.3 | **完全不變** | 換的是儀器，不是實驗 |
| 訓練程式 | `run_arm`（`probe_ladder85.py`） | **直接 import，不複製** | 複製會漂移；`data/ladder86/` 的 unit 金鑰含 `probe_ladder86.py` 的 digest |
| seed | 0,1,2 | **3,4,5** | 0-2 已經看過 |
| `N0` 學習閘門 | `train_ce200` 下降 ≥0.15 | **退役**（不是調鬆） | 見下 |
| 決策 CE 門檻 | 0.15 nats | **0.15 nats（不變）** | 3.6 sd，本來就 ≥ 3 sd |
| 決策 exact 門檻 | 5 列 | **9 列（收緊）** | 2 sd（4.5）＝85.13 的處方；5 列只有 1.1 sd |
| 新增描述量 | — | `holdout_ce`、`train_ce_full`（start/end） | 連續的尺，不裁決 |
| 記憶基線 | 未列 | 報表列母模型的 holdout exact | 85.13 的處方 |

**為什麼 `N0` 退役而不是改一個有餘裕的切片。** §85 的 `N0` 有兩個互不相干的失效模式，卻共用同一個
標籤：①「這條臂沒有真的訓練」（儀器／機械問題）；②「這條臂訓練了，但它的訓練損失往上升」。85.10
量到的是 ②——`train_ce200` 0.88 → 1.30 是**把背過的東西忘掉**，同時曲線上的全語料訓練損失是**下降**的
（1.3282 → 1.1221）。任何「訓練損失下降 ≥ x」的閘門都會在這兩股力量之間擺盪，換切片只是把擺盪換位置。
「有沒有真的在訓練」是機械事實，用 I0 回答就夠：1,286 個優化步、逐 epoch 損失有限、三臂步數相同、
checkpoint 可載回。`train_ce_full` 仍然**照實列**（start/end、逐 seed），但它是**結果的一部分**，
不該被當成「本節作廢」的理由。

### 86.4 讀點與計分格子（跑之前寫定）

| 格子 | 定義 | 角色 |
| --- | --- | --- |
| **主格 `val_ce`** | `distill_val`（281 列）teacher-forced CE，batch 8 | **裁決**（A 對 C，三個 seed 平均） |
| **共同主格 `holdout_exact`** | `distill_val_holdout`（248 列）`exact_match(sample=0, seed=3)`，`_response_only`，只量一次 | **裁決**（A 對 C） |
| 描述 `holdout_ce` | 同一份 248 列的 teacher-forced CE | 連續版的共同主格；**不裁決** |
| 描述 `train_ce_full` | `distill_train` 全部 5,144 列的 CE（`mean_ce`），step 0 與結束各一次 | 85.13 要求的餘裕記錄；**不裁決** |
| 描述 `delta_ce`／`delta_items` 的逐 seed 值與 sd | A−C | 85.13 的處方（門檻以 sd 為單位） |
| 描述 `seconds`／`ms_per_row` | 牆鐘與每列成本 | 算力 |
| 記憶基線 | 母模型在 `holdout_exact` 上的值 | 區分「泛化」與「還記得」 |

### 86.5 分支與門檻（跑之前寫定，優先序由上到下）

| 分支 | 條件（三 seed 平均） | 意思 |
| --- | --- | --- |
| `N1-ladder-pays` | `A_final ≤ C_final − 0.15` **且** `A_exact ≥ C_exact + 9 列` | 多出來的寬度在同 token 預算下換到泛化 |
| `N3-ladder-hurts` | `A_final ≥ C_final + 0.15` **且** `A_exact ≤ C_exact − 9 列` | 加寬後繼續訓比留在原寬度更差 |
| `N2-no-resolvable-gain` | `|A_final − C_final| < 0.15` **且** `|A_exact − C_exact| < 9 列` | 這個預算下兩把尺都分不出差別（≠ 相等） |
| `N4-inconsistent` | 其餘（一把尺越過門檻、另一把沒越過或方向相反） | 兩個儀器不一致，這一節不作裁決 |

`N4` 的讀法**先寫定**：報表要指出**哪一把尺**越過了門檻、哪一把沒有，並照 85.13 說明另一把尺的解析度
上限（n=3、4.5 列／1 sd、門檻 9 列）。`N4` **不得**被寫成「CE 說的那一邊成立」——CE 只是主格，共同主格
沒過就是沒過。

### 86.6 儀器 `I0`（跑完後檢查，任何一項不過則整節作廢）

1. **同一性**：A 在 step 0 的 `val_ce` 與母模型相差 ≤ 1e-4（母 5.6964）。
2. **無洩漏**：train∩val、train∩holdout 都是 0；holdout 是 val 的子集（248/248）。
3. **同一個順序**：三個 seed 各自在 epoch 0 的重排 digest 在 A／B／C 三臂相同。
4. **同一個預算**：三臂優化步數相同（`ceil(5144/8) × 2 = 1,286`）、batch 相同、lr 相同。
5. **不覆寫母模型**：所有產物只寫 `data/ladder86/`；母模型 sha256 跑完不變。
6. **量測不擾動訓練**：`probe_ladder86` 不修改 `run_arm`；用 §85 的 seed 0 checkpoint 重測
   `val_ce`／`holdout_exact`／`holdout_ce`／`train_ce_full`，前兩者必須等於 §85 的記錄值
   （≤1e-4／0 列）。這一項證明「新加的尺」與「舊的尺」是同一套量測。
7. **step 0 的兩條路徑一致**：`warm_init_{seed}.pt` 與母模型在 `train_ce_full` 上差 ≤ 1e-6。

### 86.7 預測與否證（跑之前寫定）

**主預測：`N4-inconsistent`（中等信心），且方向與 §85 相同**——CE 這把尺會**大幅**偏向 warm
（§85 是 +0.97 nats，門檻 0.15），exact 這把尺會落在 ±9 列的解析度內（§85 是 −6.7 列，sd 4.5）。
理由：CE 效應量（0.97）遠大於 seed 散佈（0.042）；exact 的效應在噪聲裡。

**第二預測**：CE 差**同號且量級 ≥0.5 nats**（複現，不是新現象）。

**替代（登記在案）**：exact 差若 ≤ −9 列 → 仍是 `N4`（CE 反向）；若 ≥ +9 列 → `N1`。

**否證**：CE 差落回 ±0.15 之內（→ `N2`，第一預測落空），或 CE 差 ≤ −0.15
（→ `N4`／`N3`，方向與第二預測相反）。任一種都照實記。

### 86.8 照實記的限制（跑之前寫定）

1. **單一母模型、單一語料、一級階梯**（2.5M→12M，×4）：`N1`／`N3`／`N2` 只說明這一級。
2. **n=3**：exact 的解析度上限是 9 列；`N2` 是「分不出來」，不是「相等」。
3. **`train_ce_full` 是描述量**：它上升不代表本節作廢（86.3 已寫），下降也不代表能力。
4. **不是生成、不進核心分**（§275／§277）：本節任何 CE 或 exact 的變化都不改變核心 **0.00/10**。
5. **§85 的 seed 0-2 不參與裁決**；§86 只用 3、4、5。
6. **符號一致性照實報**（3/3、2/3、1/3），但**不是**門檻（§85 的門檻表沒有這一條，§86 不新增）。
7. 這一節**只**回答 `N1`／`N3`／`N2`／`N4`；不改 §85 的欄位、不改任何既有門檻、不改評測題。

### 86.9 命令與執行上限（跑之前寫定）

```bash
OMP_NUM_THREADS=2 ./.venv/bin/python scripts/probe_ladder86.py \
    --seeds 3,4,5 --epochs 2 --batch 8 --lr 1e-3 \
    --out-dir data/ladder86 --cache data/ladder86/cache \
    --report data/ladder86/report.json
```

- 上限：**≤90 分鐘**牆鐘、**≤50% CPU**（12 核取 2 threads）、母模型不動、只寫 `data/ladder86/`。
  §85 九臂實測 2,600.9 s，三臂 × 三 seed 同預算約 42 分鐘，加上新的量測與快取寫入留到 90 分鐘。
- 跑完必做：`--check data/ladder86/report.json`（重算每一把尺與分支）、`python3 scripts/check_fact_gates.py`。
- **中止條件**：任何 `I0` 項不過 → 整節作廢並照實記，不得改門檻重跑。

### 86.10 結果（跑完，照實寫）

命令即 86.9（`--seeds 3,4,5`，2 threads）。**9 條臂全部現算，沒有任何 unit 被重用**（`data/ladder86/`
用自己的快取，不碰 §85 的），牆鐘 **3,034.9 s（50.6 分鐘）**。報表：`data/ladder86/report.json`。
`--check` 重算 9 條臂的四把尺與分支：**通過**（`probe_ladder86 check OK (N4-inconsistent, 9 arms
recomputed)`）。

| 臂 | params | `val_ce`（sd） | `holdout_exact` | `holdout_ce` | `train_ce_full` start→end | ms/row |
| --- | --- | --- | --- | --- | --- | --- |
| **A `warm`** | 12,069,723 | **3.6160**（0.1003） | **17/248** | **2.9415** | 0.7039 → **1.0761** | 38.9 |
| B `cold`（參照） | 12,069,723 | 2.5632（0.0474） | 4/248 | 2.2578 | 8.1703 → 2.1696 | 37.8 |
| **C `width_control`** | 2,491,227 | **4.6398**（0.0691） | **26/248** | **3.6886** | 0.7039 → 0.7066 | 3.7 |
| 母模型（記憶基線） | 2,491,227 | 5.6964 | **28/248** | 4.5373 | 0.7039 | — |

逐 seed 配對差（正 = warm 較好）：

| seed | `delta_ce` | `delta_items` | `delta_holdout_ce` |
| --- | --- | --- | --- |
| 3 | +1.0502 | −10 | +0.7759 |
| 4 | +0.9609 | −9 | +0.7043 |
| 5 | +1.0601 | −9 | +0.7610 |
| **平均（sd）** | **+1.0237**（0.0546） | **−9.33**（0.58） | **+0.7471** |

三個 seed **全部同號**（CE 3/3 正、exact 3/3 負）。照 86.5 的表：

> **`branch`：`N4-inconsistent`** —「the rulers disagree: CE +1.0237 nats (warm-better, margin 0.15)
> vs hold-out -9 items (warm-worse, margin 9)」。

### 86.11 儀器 `I0`（§86.6）

| 項 | 結果 |
| --- | --- |
| `I0-1` 同一性（step 0 val CE ≤1e-4） | **過**：9.1e-05／7.6e-05／1.7e-05 |
| `I0-2` 無洩漏 | **過**：train∩val 0、train∩holdout 0、val∩holdout 248（holdout 是 val 的子集） |
| `I0-3` 同一個順序 | **過**：三個 seed 的 epoch-0 重排 digest 由同一條 `random.Random(seed)` 規則重算，三臂共用同一個 seed 與列數 |
| `I0-4` 同一個預算 | **過**：`1,286` 步、batch 8、lr 1e-3（三臂共用同一個 protocol） |
| `I0-5` 不覆寫母模型 | **過**：`parent_unchanged: true`，母模型 sha256 與報表一致 |
| `I0-6` 量測不擾動訓練 | **過**：用 §86 的尺重測 §85 的 9 個 checkpoint，`val_ce` 到小數第四位**全同**、`holdout_exact` **全同**（例如 warm s0 3.7345/21、control s0 4.6556/28） |
| `I0-7` step 0 的兩條路徑（`train_ce_full` ≤1e-6） | **不過**：7.84e-06／5.30e-06／4.52e-06 |

### 86.12 所以 §86 **不作裁決**（照 §86.6）

86.6 寫的是「任何一項不過則整節作廢」。`I0-7` 不過，所以：報表裡的 `branch` 就是
`N4-inconsistent`，但**這一節不採用它**，`N1`／`N3` 仍然沒有被裁決。

**這是登記錯誤，不是量測失敗。** 加寬的對稱破壞噪聲是 `1e-3`，step 0 的 CE 差本來就在 `1e-5`
量級——§85.2 對同一個量登記的同一性是 **1e-4**（5.6963 對 5.6964）。`1e-6` 在這條路徑上**寫下的時候
就不可能成立**：它不是被結果推翻，是被算術推翻。

**為什麼不就地把它改成 1e-4**：那正是「看到結果才改判準」。§85 的 `N0` 與 §86 的 `I0-7` 是同一種錯的
兩次——**門檻不是從被量的量推導出來的**：`N0` 用一個母模型已背下（0.8799）的切片去問「有沒有在學」，
`I0-7` 用一個比噪聲小四個數量級的容差去問「兩條路徑一不一致」。兩次都不是科學問題，是**閘門設計**。

### 86.13 這一節照實量到什麼（描述，不裁決）

1. **CE 的效應複現，而且更大**：+1.02 nats（§85 是 +0.97），3/3 同號，逐 seed sd 0.055 → 平均是
   **19 個 sd**  away from 0。
2. **exact 這次越過門檻**：−9.33 列（−3.8pp），3/3 同號，逐 seed sd **0.58**。§85 的 sd 4.5 本身是
   n=3 的估計（sd 的 sd 很大），所以「5 列 ≈ 1.1 sd」「9 列 ≈ 2 sd」兩個門檻都建立在一個不穩的 sd
   上——這一輪的 sd 只有 0.58，同樣的 9 列門檻等於 16 個 sd。**門檻用 sd 表達是對的方向，但 sd 需要
   比 3 個點更穩的估計。**
3. **三把尺的分裂是「貪心解碼」造成的，不是分佈變差**：warm 在 `val_ce`（−1.02）與 `holdout_ce`
   （−0.75，3/3 同號）都**較好**，只有 `greedy exact` 較差。§85.10 只看到兩把尺相反；這一節多了一把
   連續的 holdout CE，指向前者。**同一個模型、同一個分佈，換一個解碼器就換一個結論。**
4. **續訓讓 exact 變差對母模型也成立**：母 28/248 ＞ C 26/248 ＞ A 17/248，B 只有 4/248。這一小段
   語料、這組超參數下，「再多訓兩個 epoch」本身就掉 exact。
5. **加寬的代價與收穫**：38.9 vs 3.7 ms/row（**10.5×**）；CE 換到 1.02 nats，exact 掉 9.3 列。
6. **核心分不變**：這些臂都不進生成路徑，核心仍 **0.00/10**（§275）。

### 86.14 下一輪（`§87`）的登記要修什麼

- **每個 `I0` 容差從它量的量推導**：加寬噪聲 1e-3 → step-0 的 CE 同一性 ≤1e-4（與 §85.2 一致），
  不是憑感覺寫 1e-6。
- **決策門檻不動**（0.15 nats／9 列）：這一輪沒有任何理由改它，看到結果之後改就是事後調參。
- **裁決要用沒跑過的 seed**（6/7/8）：3/4/5 已經看過，不能拿同一批資料重新裁決。
- **sd 的估計要更穩**：門檻寫成 sd 的倍數時，sd 本身必須來自足夠多的 seed（或跨一輪以上的配對），
  否則門檻會隨 sd 的估計亂跳（§85 的 4.5 vs §86 的 0.58）。

## §87 第二次重新登記：同一個問題，容差由量的尺度推導（登記）

### 87.1 為什麼又是重新登記

§86 的 `I0-7`（`warm_init` 對母模型在 `train_ce_full` 上差 ≤1e-6）沒過（7.8e-06），依 §86.6 整節作廢。
那條容差**寫下時就不可能成立**：加寬用 `1e-3` 的對稱破壞噪聲，step 0 的 CE 差必然在 `1e-5` 量級，
而 §85.2 對同一個量登記的同一性本來就是 **1e-4**（5.6963 對 5.6964）。

依規矩**不就地改容差**（那是看到結果才改判準），所以重新登記：

1. §86 的欄位不動（`branch: N4-inconsistent`，且 §86 不作裁決）。
2. seed 3/4/5 **已經看過**，不能拿來重新裁決。**§87 用 seed 6/7/8**。
3. §87 的預算、臂、語料、順序、lr、步數、門檻**全部照 §86**，只有 `I0-7` 的容差換成由噪聲尺度推導的
   值。

### 87.2 登記前已經量到的（不是裁決結果）

| 項目 | 值 | 用在哪裡 |
| --- | --- | --- |
| 加寬的對稱破壞噪聲 | `1e-3`（§85.3 已登記） | 推導 step-0 同一性的容差量級 |
| 同一性在 §85.2 的登記值 | **1e-4**（val CE 5.6963 對 5.6964） | 同一個量、同一種擾動，`1e-4` 是它的尺度 |
| 母模型 `train_ce_full` | 0.7039（§86.2，5,144 列、batch 8） | 描述量的起點 |
| 母模型 hold-out exact | 28/248 | 記憶基線 |
| §86 的逐 seed 散佈（描述） | CE 0.0546、exact 0.58 | **只作記錄，不用來改門檻**（見 87.3） |

**`I0-7` 的新容差是推導的**：噪聲 `1e-3` 擾動權重 → step-0 的 CE 差落在 `1e-5`；§85.2 對同一個量登記
`1e-4`。因此 §87 用 **`1e-4`（`val_ce` 與 `train_ce_full` 都是）**，並把三個 seed 的**實際**差額照實列出來
（它是描述量，不是門檻）。`1e-6` 之所以錯，不是因為它嚴格，是因為它比噪聲小四個數量級。

### 87.3 改什麼、不改什麼（跑之前寫定）

| 項目 | §86 | §87 | 為什麼 |
| --- | --- | --- | --- |
| 臂、資料、順序、lr、1,286 步、factor、noise、guard | 見 86.3 | **完全不變** | 換的是儀器，不是實驗 |
| seed | 3,4,5 | **6,7,8** | 3-5 已經看過 |
| 決策門檻 | 0.15 nats／9 列 | **0.15 nats／9 列（不變）** | 看到結果之後改門檻就是事後調參 |
| `I0-7` 容差 | `train_ce_full` ≤1e-6 | **`val_ce` 與 `train_ce_full` ≤1e-4（推導）** | 87.2 |
| 其餘 `I0` | 1-6 | **不變** | — |
| 描述量 | `holdout_ce`、`train_ce_full`、母模型基線 | **不變** | — |

**為什麼門檻不動，即使 §86 的散佈顯示 `0.15` 只有 2.7 個 sd。** 三個理由：(a) `0.15`／`9` 是在 §86 跑
之前定的，動它就是事後調參；(b) §86 的 sd 本身是三個點估出來的，不是穩定的散佈（§85 是 4.5、§86 是
0.58）；(c) 觀測到的 CE 效應是 `+1.02`，等於 19 個 sd，`0.15` 與 `0.165` 會給同一個分支。門檻在這個
量級上不影響答案，只影響「算不算越過」，所以**不動**。

### 87.4 讀點與計分格子（跑之前寫定）

與 86.4 完全相同：**主格 `val_ce`**、**共同主格 `holdout_exact`** 裁決；`holdout_ce`、`train_ce_full`、
逐 seed 散佈、`seconds`／`ms_per_row`、母模型 hold-out exact 是描述量。

### 87.5 分支與門檻（跑之前寫定，優先序由上到下）

與 86.5 完全相同：`N1-ladder-pays`（CE ≥ +0.15 且 exact ≥ +9）、`N3-ladder-hurts`（CE ≤ −0.15 且
exact ≤ −9）、`N2-no-resolvable-gain`（兩把尺都在門檻內）、`N4-inconsistent`（其餘）。`N4` 的讀法照
86.5：指出哪一把尺越過門檻、哪一把沒有；**不得**把 `N4` 寫成「CE 說的那一邊成立」。

### 87.6 儀器 `I0`（跑完後檢查，任何一項不過則整節作廢）

1. **同一性**：`warm` 在 step 0 的 `val_ce` 與母模型相差 ≤1e-4（母 5.6964）。
2. **無洩漏**：train∩val、train∩holdout 都是 0；holdout 是 val 的子集（248/248）。
3. **同一個順序**：三個 seed 的 epoch-0 重排 digest 由同一條規則重算。
4. **同一個預算**：三臂都是 `1,286` 步、batch 8、lr 1e-3。
5. **不覆寫母模型**：只寫 `data/ladder87/`；母模型 sha256 跑完不變。
6. **量測不擾動訓練**：用 §86 的尺重測 §85 的 9 個 checkpoint，`val_ce` 與 `holdout_exact` 必須等於
   §85 的記錄值（≤1e-4／0 列）。
7. **step 0 的兩條路徑**（推導容差）：`warm_init_{seed}.pt` 與母模型在 `val_ce` 與 `train_ce_full` 上
   都差 **≤1e-4**；三個 seed 的實際差額照實列（描述量）。

### 87.7 預測與否證（跑之前寫定）

**主預測：`N4-inconsistent`（高信心），兩把尺都越過門檻、方向相反。** 依據（§86 的描述量，非本節
裁決）：CE 差 `+1.02`（19 sd）、exact 差 `−9.3` 列（3/3 同號）。**數值預測**：CE 差 `+1.0 ± 0.2`、
exact 差 `−9 ± 3` 列。

**否證**：CE 差落回 ±0.15 之內（→ `N2`）、或 CE 差 ≤ −0.15（→ `N4`／`N3`，方向翻轉）、或 exact 差
≥ +9（→ `N1`）。任何一種都照實記，且**不改門檻重跑**。

### 87.8 照實記的限制（跑之前寫定）

1. 單一母模型、單一語料、一級階梯（2.5M→12M，×4）。
2. n=3；sd 本身的估計不穩（§85 4.5 vs §86 0.58），所以任何「N 個 sd」的說法都要同時列出 sd 值。
3. `train_ce_full` 上升是結果的一部分，不是作廢理由（86.3）。
4. 不進核心分（**0.00/10** 不變）。
5. §86 的數字仍然只是描述量；§87 的裁決只用 seed 6/7/8。

### 87.9 命令與執行上限（跑之前寫定）

```bash
OMP_NUM_THREADS=2 ./.venv/bin/python scripts/probe_ladder87.py \
    --seeds 6,7,8 --epochs 2 --batch 8 --lr 1e-3 \
    --out-dir data/ladder87 --cache data/ladder87/cache \
    --report data/ladder87/report.json
```

- 上限：**≤90 分鐘**牆鐘、**≤50% CPU**（12 核取 2 threads）、母模型不動、只寫 `data/ladder87/`。
  §86 九臂實測 3,034.9 s，同預算留到 90 分鐘。
- 跑完必做：`--check data/ladder87/report.json`、`python3 scripts/check_fact_gates.py`。
- **中止條件**：任何 `I0` 項不過 → 整節作廢並照實記，不得改門檻或容差重跑（要再來就是 §88 + 新 seed）。

### 87.10 結果（跑完，照實寫）

命令即 87.9。**9 條臂全部現算**，牆鐘 **3,068.8 s（51.1 分鐘）**。報表：`data/ladder87/report.json`。
`--check` 重算 9 條臂的四把尺、逐 seed 的 identity 差額與分支：**通過**
（`probe_ladder87 check OK (N4-inconsistent, 9 arms recomputed, I0 all pass)`）。

| 臂 | params | `val_ce`（sd） | `holdout_exact` | `holdout_ce` | `train_ce_full` start→end | ms/row |
| --- | --- | --- | --- | --- | --- | --- |
| **A `warm`** | 12,069,723 | **3.6134**（0.0618） | **19/248** | **2.9189** | 0.7039 → **1.0442** | 39.4 |
| B `cold`（參照） | 12,069,723 | 2.5894（0.0446） | 4/248 | 2.2944 | 8.4957 → 2.2002 | 38.2 |
| **C `width_control`** | 2,491,227 | **4.7159**（0.0702） | **27/248** | **3.7213** | 0.7039 → 0.6798 | 3.6 |
| 母模型（記憶基線） | 2,491,227 | 5.6964 | **28/248** | 4.5373 | 0.7039 | — |

逐 seed 配對差（正 = warm 較好）：

| seed | `delta_ce` | `delta_items` | `delta_holdout_ce` |
| --- | --- | --- | --- |
| 6 | +1.1298 | **−1** | +0.8392 |
| 7 | +0.9847 | **−12** | +0.6688 |
| 8 | +1.1931 | **−12** | +0.8993 |
| **平均（sd）** | **+1.1025**（0.1069） | **−8.33**（6.35） | **+0.8024**（0.1196） |

CE 三個 seed **全為正**；exact 三個 seed **全為負**（但大小從 −1 到 −12）。照 87.5 的表：

> **`branch`：`N4-inconsistent`** —「CE +1.1025 nats (warm-better, margin 0.15) vs hold-out −8 items
> (unresolved, margin 9)」。

**與前兩輪並列（描述，不新增裁決）**：

| 輪 | seeds | `delta_ce` | `delta_items` | 分支 | 這一輪算不算裁決 |
| --- | --- | --- | --- | --- | --- |
| §85 | 0/1/2 | +0.9676 | −6.67 | `N0-unusable`（`N0` 沒有餘裕） | 不算（85.10） |
| §86 | 3/4/5 | +1.0237 | −9.33 | `N4-inconsistent` | 不算（`I0-7`） |
| **§87** | **6/7/8** | **+1.1025** | **−8.33** | **`N4-inconsistent`** | **算（I0 全過）** |

九個 seed 的方向**完全一致**：CE **9/9 為正**（平均 **+1.031**、sd 0.087），exact **9/9 為負**
（平均 **−8.11**、sd 4.08）。方向是穩定的；**大小**不是——見 87.13。

### 87.11 儀器 `I0`（§87.6，全過）

| 項 | 結果 |
| --- | --- |
| `I0-1` step 0 的 `val_ce` ≤1e-4 | **過**：5.89e-05／2.73e-05／1.09e-06 |
| `I0-2` 無洩漏 | **過**：train∩val 0、train∩holdout 0、val∩holdout 248 |
| `I0-3` 同一個順序 | **過**：三個 seed 各自的 epoch-0 digest（`bc7e0d9e…`／`3ff7c733…`／`532aa001…`），三臂共用 |
| `I0-4` 同一個預算 | **過**：1,286 步、batch 8、lr 1e-3 |
| `I0-5` 不覆寫母模型 | **過**：`parent_unchanged: true`，sha256 與報表一致 |
| `I0-6` 量測不擾動訓練 | **過**：`--check` 用同一套尺重測 §85 的 9 個 checkpoint，`val_ce` 與 `holdout_exact` 與 §85 的記錄值相同 |
| `I0-7` step 0 的兩條路徑 ≤**1e-4**（`val_ce` 與 `train_ce_full`） | **過**：val 5.89e-05／2.73e-05／1.09e-06；train 6.92e-06／7.67e-06／7.58e-06 |

`I0-7` 的實際差額（描述量）比容差小 1–2 個數量級，這正是 87.2 推導的預期：噪聲 1e-3 在 step 0 留下
1e-5 量級的 CE 差，`1e-4` 是它的上界；§86 的 `1e-6` 比這個尺度小四個數量級，所以寫下時就不可能成立。

### 87.12 預測檢查（87.7 登記）

| 登記的預測 | 結果 |
| --- | --- |
| 主預測：`N4-inconsistent`（高信心） | **對**：CE 越過門檻（warm 較好），exact 沒有越過 |
| 「**兩把尺都越過門檻**、方向相反」 | **不對**：exact 差 −8.33，在 9 的門檻**之內** → `unresolved` |
| 數值：CE `+1.0 ± 0.2` | **對**：+1.1025 |
| 數值：exact `−9 ± 3` 列 | **對**：−8.33（但正因為門檻是 9，這一輪它不算「越過」） |
| 否證條件（CE 回到 ±0.15、方向翻轉、exact ≥ +9） | **都沒有觸發** |

主預測的分支對了，但「兩把尺都越過」這一半**落空**：同一組註冊門檻，§86 量到 −9.33（越過）、§87 量到
−8.33（沒越過）。這不是模型變了，是**這把尺在 n=3 的解像度不足**（87.13）。

### 87.13 這一節裁決了什麼、沒裁決什麼

- **裁決有效**：I0 全過，所以 §87 的 `N4-inconsistent` 是這一節的結果。`N1`（加寬續訓有回報）與
  `N3`（加寬續訓更差）**都沒有成立**：CE 這把尺說 warm 明顯較好（+1.10 nats），exact 這把尺既沒有
  確認、也沒有否定（−8.33，門檻 9）。
- **方向是穩定的**：九個 seed、三輪獨立配對，CE **9/9 為正**、exact **9/9 為負**。所以「加寬＋續訓
  在同 token 預算下把分佈擬合拉好、把貪心解碼的答對數拉差」這個**方向**有九個 seed 的支持，不是一輪
  的雜訊。
- **大小不穩定，而且這本身就是結果**：exact 的逐 seed sd 三輪是 **4.51 → 0.58 → 6.35**。用 sd 表達
  門檻（85.13 的處方）在 n=3 下**沒有穩定的意義**：9 列在 §86 是 15.5 個 sd，在 §87 只有 1.4 個 sd，
  在九個 seed 的合併 sd（4.08）下是 2.2 個 sd。同一條門檻、同一個效應，會因為 sd 的估計而落在線的
  兩邊——§86 與 §87 正是這樣。
- **逐 seed 的 exact 差是雙峰的**：seed 6 只掉 1 列，seed 7/8 各掉 12 列。所以「平均掉 8.3 列」不是
  一個「每個 seed 都會掉 8 列」的穩定估計，而是「一個 seed 幾乎沒差、兩個 seed 掉一成」的平均。
- **核心分不變**：19/248 的 exact 仍然是貪心解碼的字串比對，不是生成，也不進核心分；核心仍
  **0.00/10**（§275）。

### 87.14 照實記的限制

1. 單一母模型、單一語料、一級階梯（2.5M→12M，×4）。九個 seed 跨三輪，但只有 §87 這一輪的儀器全過，
   所以**裁決只來自 6/7/8**；§85／§86 的數字在 87.10 只作方向描述。
2. exact 的單位是 248 題裡的一列（0.40pp）；9 列的門檻等於 3.6pp。這個解析度在 n=3 下已經到頂。
3. `train_ce_full` 上升是結果（warm 0.7039→1.0442、control 0.7039→0.6798），不是作廢理由（86.3）。
4. 這一節沒有回答「更大的 n 會不會讓 exact 越過門檻」——那是新登記，不是這一節的推論。

### 87.15 這一輪之後：階梯問題的狀態

三次登記（§85、§86、§87）之後，可以說的話與不能說的話：

- **可以說**：在這個母模型、這份語料、這個預算下，把 2.5M 加寬成 12M 再續訓，**CE 明顯較好**
  （+1.03 ± 0.09 nats，九個 seed 全同號）、**貪心解碼的答對數明顯不是較好**（九個 seed 全為負，
  平均 −8.1 ± 4.1 列）。加寬的代價是 **10.9×** 每列成本（39.4 vs 3.6 ms/row）。
- **不能說**：`N1` 或 `N3`。exact 的門檻（9 列）在 n=3 的 sd 估計下不穩定，兩輪分別落在門檻的兩邊；
  登記的規則只有 `N4`，而 `N4` 的意思就是「這一節不作裁決」。
- **要把它變成 `N1`／`N3`**，只有兩條合法路徑，而且都是**新登記**：(a) 增加 seed 數讓 exact 的 sd
  收斂，門檻才有穩定的 sd 意義；(b) 登記**單一**裁決尺（例如只用 exact），承擔丢掉 CE 資訊的代價。
  兩者都不得在這一輪的結果上就地調整。
- **不建議**再跑一次同構的階梯（§88 只換 seed）。三輪已經把方向固定，第四輪只會得到同一個 `N4` 或
  一次剛好越線的 `N1`／`N3`，而那個「剛好」正是門檻不穩定的產物。下一個值得花算力的問題不是
  「哪條臂」，而是 `§276`／`§275` 留下的 **teacher-forced 38.5% 對 exact 0/40 的落差**：先分清那是
  解碼漂移還是分佈退化（~30–60 分鐘，不動訓練），再決定要不要為核心再付一次訓練。

## §88 teacher-forced 與 exact 的落差：解碼漂移，還是分佈退化（登記）

### 88.1 這一節問什麼

`§276` 留下的問題是：一個 token-SNN 可以在 teacher-forced 下拿到遠高於 0 的逐 token 正確率，
free-running 的 exact 卻接近 0。這個落差有兩種完全不同的成因，而它們的修法相反：

- **解碼（drift／exposure bias）**：餵 gold 前綴時模型選對，餵自己的前綴時走偏——錯一個 token 之後整段被帶走。
  修法是解碼（teacher forcing、scheduled sampling、beam／top-k 搜尋），不必換資料或加容量。
- **分佈（degradation）**：即使餵 gold 前綴，gold token 也不在模型的前幾名——對應關係根本沒學到。
  修法是容量／資料／目標函數；解碼再好也救不回來。

這一節登記兩個問題，**主問題在 held-out，第二個問題在記住的列上**：

> **Q1（主）**：在 `distill_val_holdout`（248 列，模型沒訓過、但與訓練語料同源）上，
> `distill` checkpoint 的失敗**逐列**分解之後，多數是「gold 前綴就能修」還是「gold 前綴也修不了」？
>
> **Q2（次）**：在模型**記住**的列上（`distill_train`／`core_train` 前 248 列），逐 token 正確率較高，
> 剩下的落差仍然是同一個分解——那裡多數是解碼還是分佈？
>
> **Q3（對照，不解釋成能力）**：`core149k` 在 `distill_val_holdout` 上的 **0/248** 與它在自己語料上的
> exact 差多少？這個差是不是「跨語料量測」造成的，而不是解碼造成的？

Q1 與 Q2 必須分開，因為它們的答案可以不同，而且**只有 Q2 是真正的 exposure-bias 測試**：Q1 的
逐 token 正確率太低（登記前已知 33.4%），低到「gold 前綴能修的行數」在算術上就有上界（88.7）。
把 Q1 當成「解碼 vs 分佈」的公平試驗會高估解碼的重要性。

### 88.2 登記前已經量到的（描述，不是裁決結果）

| 項目 | 值 | 怎麼量的 |
| --- | --- | --- |
| `token_snn_distill.pt` | 2,491,227 參數、vocab 3,577（`numeric_atoms=False`）、`d_hidden 512 / 1 layer / max_len 192 / membrane` | `TokenSNN.load` |
| `token_snn_core149k.pt` | 7,623,879 參數、vocab 12,005、`d_hidden 512 / 1 layer / max_len 192 / membrane` | 同上 |
| distill 的記錄值 | `eval` = `distill_val` 抽 150 列，exact **8%**；`split_tf_accuracy` = `distill_val` 281 列、1,834 token，**response_tf 0.3337** | `data/intelligence_reports/token_snn_distill.json` |
| core149k 的記錄值 | `eval` = `distill_val_holdout` 248 列，exact **0.0**；`eval_tf_accuracy` 1,186 token，**0.1391**；訓練語料是 `core_train.jsonl` | `data/intelligence_reports/token_snn_core149k.json` |
| `distill_val_holdout` | 248 列；答案 token 平均 **3.79**、中位 3、p90 6、最大 23 | 本節量測（`vocab.encode`） |
| `distill_train` | 5,144 列；前 248 列答案 token 平均 **3.07**，**0 個 UNK** | 同上 |
| `core_train` | 149,489 列；用 core 詞表過 `fits(max_len=192)` 後 138,671 列；前 248 列（可完整拼回）答案 token 平均 **39.9** | 同上 |
| holdout 的 UNK | 940 個答案 token 中 distill 詞表 **57 個 UNK（6.06%）**、core 詞表 51 個（5.43%）；**33/248 列的答案無法被詞表原樣拼回** | `decode(encode(answer)) != answer` |
| 語料重疊 | `distill_val_holdout ∩ distill_train = 0`；holdout 的 prompt **0/248** 出現在 `core_train` | 集合比對 |
| 機器 | CPU 13.4%、RAM 49.9%（可用 7.7 GB）、swap 16.2%，皆在硬上限內 | `/proc/stat`、`/proc/meminfo` |

三件必須先說清楚的事：

1. **歷史的 38.5% 不能重跑**：那個數字來自一個已被取代的小 char 模型（`d_hidden=128`、char 詞表 170、
   3,000 列），checkpoint 不在磁碟上。這一節量的是**同一個現象**在現有 checkpoint 上的版本，
   不是重播那個歷史 run。
2. **`core149k` 的 0/248 是跨語料量測**：它訓在 `core_train`，卻在 `distill_val_holdout` 上評。
   那 248 列與它的訓練分佈不同（短數值答案 vs 長篇 alpaca／association 答案），所以 0/248 同時混了
   「不會解碼」與「不是在回答這種題」。Q3 用它在自己語料上的列把兩者分開。
3. **33/248 列的答案無法被詞表原樣拼回**（UNK 會被 `decode` 丟掉）。所以原始字串比較會把這些列
   判成錯，**即使模型輸出完全正確的 token**。逐列分解因此用「模型可拼出的答案」（token 完全相等），
   同時並列原始字串比較（與 `exact_match` 相容）——兩個數都報，理由寫在 88.4。

### 88.3 凍結的四條臂（跑之前寫定；全部只做前向，不訓練、不更新權重）

| 臂 | checkpoint | 列 | 角色 |
| --- | --- | --- | --- |
| **`distill_holdout`** | `token_snn_distill.pt` | `distill_val_holdout` 全 248 列 | **Q1 主臂**（同語料、沒訓過） |
| `core_holdout` | `token_snn_core149k.pt` | 同上 248 列 | Q3 對照（跨語料；0/248 的來源） |
| **`distill_train`** | `token_snn_distill.pt` | `distill_train` **前 248 列** | **Q2 主臂**（記住的列） |
| `core_train` | `token_snn_core149k.pt` | `core_train` **前 248 列**（需 `fits(max_len=192)` 且 prompt／answer 都能原樣拼回） | Q2 複現（記住、但答案長） |

「前 248 列」是**固定順序**的檔頭切片，不是隨機抽樣，也不是看模型表現挑的。`core_train` 的
「能原樣拼回」條件只依詞表，不依模型輸出；若符合條件的列少於 248，這一臂作廢（`I0`）並照實記。
所有 checkpoint 以 sha256 記錄，載入後跑完再比一次。

### 88.4 逐列量什麼（跑之前寫定）

對每一列，令 `gold = vocab.encode(answer)`、`EOS = vocab.eos_id`、
`prefix = [BOS] + encode(prompt) + [NL]`。

| 量 | 定義 |
| --- | --- |
| `gold_len` | `len(gold)`；`gold_unk` = 其中 UNK 的個數 |
| `gold_text` | `decode(gold)`（模型可拼出的答案） |
| `argmax_exact`（`O`） | 餵 `prefix + gold + [EOS]`，**每一個**答案位置（含最後的 EOS）的 argmax 都等於 gold 的下一個 token |
| `topk_all[k]` | 同上，但要求 gold token 在每個位置的 **rank ≤ k**（k ∈ {3, 5, 10}）；`topk_all[1] ≡ O` |
| `token_tf` | 所有答案位置（含 EOS）的 argmax 命中率＝`tf_accuracy` 的同一個量 |
| `rank_median` | 答案位置 gold token rank 的中位數 |
| `greedy_ids` | 從 `prefix` 起、`argmax` 貪心解碼，遇 EOS／PAD／BOS 停（與 `generate` 同一規則） |
| `exact_model`（`G`） | `greedy_ids == gold`（模型可拼出的答案完全相等） |
| `exact_raw` | `decode(greedy_ids).strip() == answer.strip()`（與 `train_token_snn.exact_match` 同一個判定） |
| `first_div` | 貪心輸出與 `gold` 第一個不同的位置（0-based；全對為 −1） |
| `prefix_curve[f]` | 對 f ∈ {0.25, 0.5, 0.75, 1.0}：強制餵 `floor(f × gold_len)` 個 gold token，再貪心解出剩下的；**剩餘 token 完全相等**才算命中。f=1.0 等於 `O`，f=0 等於 `G`（兩端點互相檢查） |
| `greedy_len` | 貪心輸出的 token 數（提早 EOS／暴走都會改它） |
| `gold_logprob` | 每個答案位置 gold token 的 log-probability 平均（nats） |

**為什麼分解用 `exact_model` 而不是 `exact_raw`**：`exact_raw` 會把 33 列「詞表拼不回」的列判成錯，
而那些列的 gold 在模型自己的拼法裡是完整的。用 `exact_raw` 會把詞表的限制算進「分佈退化」。
所以裁決用 `exact_model`，`exact_raw` 並列報告，並在結果裡寫明兩者差幾列。

**登記後的修正（跑之前，尚未產生任何結果）**：`prefix_curve` 的每一個點都定義成
「強制 `k` 個 gold token 後，貪心輸出必須等於 `gold[k:] + [EOS]`」。若不把 EOS 放進續接目標，
f=1.0（`k = gold_len`）的剩餘目標是空字串，會對每一列**必然成立**，端點檢查就失去意義。
加上 EOS 之後：f=0 是「整段答案＋正確終止」（= `G`），f=1.0 是「餵完整 gold 後預測 EOS」（= `O`），
兩個端點分別由貪心與 gold 前向兩條獨立路徑算出，才構成真正的交叉檢查。`G` 因此是**終止含入**的
token 完全相等；`exact_model`／`exact_raw` 仍是字串比較，並列報告。

### 88.5 分支與門檻（跑之前寫定；唯一的分界是多數，沒有其他數字）

把每一列分成四格（`G` = `exact_model`、`T5` = `topk_all[5]`，且 `O ⊆ T5`）：

| 格 | 條件 | 意思 |
| --- | --- | --- |
| 成功 `G` | `G` | 貪心就對，沒有落差 |
| **`D`** | `O` 且 **非** `G` | **gold 前綴就能修**：餵對前綴就全對，錯在解碼 |
| **`S`** | 非 `O` 且 `T5` 且非 `G` | **前 5 名搜尋可能修**：gold 在每個位置的前 5 名內，但 argmax 路徑不是 gold；beam／top-k 搜尋**有機會**找到 |
| **`M`** | 非 `T5` | **分佈修不了**：至少一個位置 gold 掉出前 5 名，任何只看前 5 名的解碼都到不了 |
| `X` | 非 `O` 且 `G` | 貪心走別的路卻拼出同一個答案（預期接近 0，照實報） |

失敗總數 `F = D + S + M`（`X` 不算失敗）。主臂的讀法：

- `F = 0` → **`no-gap`**。
- `(D + S) / F ≥ 0.5` 且 `M / F < 0.5` → **`gap=decoding`**。
- `M / F > 0.5` → **`gap=distribution`**。
- 其餘（只有 0.5／0.5 的平手）→ **`gap=mixed`**。

門檻的理由：**0.5 是多數，不是調出來的數字**。不設「幾個 token 算近」之類的額外常數；
`D`、`S`、`M` 各給 Wilson 95% 區間，讀者看得到不確定性。`topk_all[3]`／`[10]` 只作描述，
不改裁決（改 k 會改答案，所以 k=5 先寫定）。

Q2 用同一條規則套在 `distill_train`（主）與 `core_train`（複現）。Q3 只比較兩個 `G` 的 Wilson 區間。

### 88.6 儀器 `I0`（跑完後檢查，任何一項不過則該臂作廢／整節照實記）

1. **checkpoint 不變**：載入前後 sha256 相同；參數量、vocab 大小、config 與 88.2 相同。
2. **沒有訓練**：全程 `net.eval()`、`torch.no_grad()`；不呼叫 `train_on`、不建 optimizer；跑完 `net.training is False`。
3. **列就是登記的列**：每臂 248 列、每臂 (prompt, answer) 的順序 digest；主臂
   `distill_val_holdout ∩ distill_train` 重算為 **0**。
4. **決定性**：主臂前 32 列**連跑兩次**，逐列記錄必須完全相同（貪心是 argmax，沒有隨機）。
5. **與生產解碼一致**：主臂的 `exact_raw` 命中數必須等於
   `train_token_snn.exact_match(primary_pairs, sample=0, seed=3)` 的命中數（同一個 `_response_only` 判定）。
6. **與生產 teacher-forced 一致**：主臂的 `token_tf`（我們的 gold 前綴前向）必須等於
   `model.tf_accuracy(primary_pairs)["tf_acc"]`，差 ≤ 1e-6。
7. **沒有截斷**：`len(ids) < max_len` 對每一列都成立（`gold` 完整）。若有截斷列，該臂的裁決只用在
   非截斷列上並報列數；截斷列超過 5% 則該臂作廢。
8. **端點自洽**：`prefix_curve[0]` 等於 `G`、`prefix_curve[1.0]` 等於 `O`，逐列相同。

### 88.7 預測與否證（跑之前寫定）

**Q1（主）主預測：`gap=distribution`（中高信心）**。理由先寫明，因為它讓這個預測不是丟硬幣：
`D ≤ O`，而 `O` 是「整條 gold argmax 路徑都對」的列數，其比例上限就是逐 token 正確率
（≈0.334）除以「至少不是貪心就對的列」；主臂的答案長度是 3.79（+EOS ≈ 4.79）。要讓解碼佔多數，
`S` 必須也很大，也就是 gold 在**每個**位置都留在前 5 名：若失敗列要有一半落在 `S`，每 token 的
前 5 名命中率得高到 `0.5^(1/4.79) ≈ 0.87`。主預測是 top-5 命中率**沒有**那麼高，所以分佈佔多數。
**否證**：Q1 出現 `gap=decoding` 或 `gap=mixed`。

**Q2（記住的列）主預測：`gap=decoding`（中等信心）**。理由：記住的列逐 token 正確率高，
gold 前綴應該能讓多數列全對（`O` 大），而貪心仍會走偏（記錄值 train exact 0.38、val 0.45），
所以 `D + S` 應該佔多數。**否證**：`distill_train` 出現 `gap=distribution`——那表示即使在記住的列上，
殘餘落差也不是解碼問題，Q2 的假設錯了，照實記。

**Q3 預測**：`core_train` 的 `G` 與 `core_holdout` 的 `G` 的 Wilson 95% 區間**不重疊**
（前者應遠高於 0）。**否證**：兩區間重疊——那表示 0/248 不能歸因於跨語料，Q3 的解釋錯了。

### 88.8 照實記的限制（跑之前寫定）

1. **這是前向診斷，不是能力分**：核心分不變 **0.00/10**（§275）。這一節不訓練、不改 checkpoint、
   不改任何門檻，也不把任何結果算進核心分。
2. **`S` 是「可能」不是「保證」**：gold 在每個位置前 5 名內，只代表 beam-5 **有機會**找到它；
   beam 以累積機率剪枝，不一定留得住 gold。結果會這樣寫，不把 `S` 說成「beam 就會對」。
3. **`O` 是 argmax 路徑，不是最大序列機率**：gold 可能不是 argmax 路徑、卻是最高機率的序列；
   這一節量的是「餵 gold 前綴時每個位置會不會選對」，不是全域搜尋。
4. **只有四個 checkpoint × 四組 248 列**，而且 `core_train` 的 248 列是檔頭切片（長答案為主），
   不代表整個 `core_train` 分佈。Q2 的結論只說明「這 248 列」。
5. **詞表可拼性**：33/248 的 held-out 列原始字串不可達，所以 `exact_raw` 是下界；`exact_model`
   是這一節的判準，兩者差幾列會照實寫。
6. **歷史的 38.5%／0-of-40 不可重跑**（88.2 第 1 條）：這一節量的是同一個現象，不是那個 run。
7. **`temperature=0`**：只量貪心。取樣解碼不在這一節；它會改變 `G`，但不會改變「gold 在不在前 5 名」。

### 88.9 命令與執行上限（跑之前寫定）

```bash
OMP_NUM_THREADS=2 ./.venv/bin/python scripts/probe_tf_exact_gap.py \
  --out-dir data/tf_gap88 --report data/tf_gap88/report.json
OMP_NUM_THREADS=2 ./.venv/bin/python scripts/probe_tf_exact_gap.py \
  --check data/tf_gap88/report.json
```

預算：**≤ 30 分鐘**、2 個執行緒、只寫 `data/tf_gap88/`（gitignored）、GPU 不使用。
若牆鐘超過 1,800 秒，停止並記為 **aborted**（不作裁決、不採用部分結果）。
