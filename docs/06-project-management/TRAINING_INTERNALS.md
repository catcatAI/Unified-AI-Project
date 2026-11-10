# 訓練內部：token-SNN 到底在學什麼、梯度從哪裡來、什麼時候會壞

> 2026-11-09。這份文件回答「訓練、學習的內部是怎麼運作的」，並且把每個數字標上**量測來源**。
>
> 目的不是解釋架構，而是回答一個操作問題：**現在可以開始訓練了嗎？** 答案由
> [`scripts/probe_training_readiness.py`](../../scripts/probe_training_readiness.py)
> 量出來，不由這份文件宣稱。
>
> 三個月來核心分一直是 0.00/10，而 108M
> checkpoint 的 loss 看起來「有在降」。這份文件記錄為什麼那兩件事可以同時成立：**loss 下降不代表在學**，它也可以代表模型找到了一條把非線性關掉的捷徑。

## 一、被訓練的東西（精確方程）

一個 token 一個時間步（`timesteps=1`），層數
`layers=1`，readout 讀膜電位（SLAYER，量測過的贏家）：

```
x_t      = Embed(token_t)                                     # d_emb
mem_t    = leak * mem_{t-1} + W_in x_t + W_rec s_{t-1}        # d_hidden
s_t      = H(mem_t - |theta|)                                 # 前向是階躍
out_t    = LayerNorm(mem_t)                                   # readout="membrane"
logits_t = W_head out_t                                       # vocab
```

其中
`leak = sigmoid(beta_param)`、`theta = |theta_param|`，兩者都是**可學參數**。`mem_{-1} = s_{-1} = 0`。

梯度只從一個地方穿過階躍函數——surrogate：

```
s_t = H(z) 前向,   d s / d z = alpha * sigmoid'(alpha * z) * ... （fast-sigmoid）
z = mem_t - |theta|
```

`alpha=5` 時 `ds/dz` 在 `z=0` 是 1.25、`|z|=1` 是 0.33、`|z|=2` 約 0.09，`|z|>4`
幾乎是 0。**這就是「梯度帶」**：前活動離閾值越遠，梯度越接近零，那一層就在**放電但沒在學**。`dynamics()`
量三個數：
`near_threshold`（|z|<0.1 的比例）、`sensitive`（|z|<2 的比例）、`spike_rate`。

損失只算答案位置（`TokenSNN.loss`）：

```
hidden = encode(ids)[:, :-1, :]
loss   = mean( cross_entropy(head(hidden), ids[:, 1:]) 只在 mask=1 的位置 )
```

`mask` 由 `_encode`
決定：`[BOS] + prompt + ['\n'] + answer + [EOS]`，只有 answer 到 EOS 之間是 1。prompt 的位置不產生梯度。`tail_weight`
對 `<al_out>`
之後的狀態區塊加權（核心語料沒有這個標記，所以整段都是 response）。

## 二、梯度分佈（實測，reduced config `d_emb=64 d_hidden=128`）

`mech.gradient_reaches_every_group`
對 8 筆真實資料做一次 forward/backward，量每組參數的梯度 L2：

```
beta=1.943e-02  embed=3.012e-02  head=1.497e+00  out_norm=1.276e-01
threshold=5.232e-02  w_in=4.780e-01  w_rec=1.714e+00
```

**每一組都收到非零且有限的梯度**——這件事不是理所當然：`w_skip` 在 `layers=1`
時是 `nn.Identity()`，沒有參數；`beta`/`threshold`
是純量，若被 clamp 成常數梯度就會變 0。這條檢查就是為了擋「某個模組悄悄不學」的迴歸。

`head` 與 `w_rec` 的梯度最大是預期行為：head 直接接在 loss 上，`w_rec`
是唯一讓第 t 步看到第 t−1 步的項。

## 三、參數分配（實測，108M checkpoint）

```
total 108,583,431
  head        83,931,653   77.3%
  embed       16,779,776   15.5%
  w_rec        6,553,600    6.0%
  w_in         1,313,280    1.2%
  out_norm         5,120    0.0%
```

**77% 的參數在輸出層、15.5% 在 embedding，真正承載上下文的 `w_rec` 只有 6%。**
這個比例決定了兩件事：

1. 模型很容易把 loss 降下來（head 大、詞表固定），所以「loss 有降」不能當作「在學」的證據。
2. 要提升的是**上下文的使用**，而那一部分只有 6.5M 參數；擴張 head 不會讓它變聰明。

reduced config 的比例更極端（head 66.6%、embed 33.0%、w_rec 0.3%），但方向相同。

## 四、三條穩定不變量（guards）：它們各擋掉一種「便宜的 loss」

這三個量都可以**不學任務**就讓 loss 下降。舊版預設全開（`theta_max=2.0`、`leak_floor=0`、`gain_cap=0`），於是 108M 那一輪找到了這條路：

| 量        | 108M 起點 | 108M 終點             | 意義                                   |
| --------- | --------- | --------------------- | -------------------------------------- |
| theta     | 0.5       | **1.9995**（cap 2.0） | 把閾值推到頂 → 幾乎不放電 → 遞歸失效   |
| beta      | 0.9       | **0.5407**            | 記憶視窗 1/(1−beta) 從 10 步掉到 ~2 步 |
| sr(w_rec) | 0.55      | 上升                  | 用「直通」取代「整合」                 |

結果：`spike_rate=0.0816`、`near_threshold=0.0018`、`sensitive=0.0338`——**非線性幾乎沒有梯度通過**，而 loss 停在 2.3623 看起來正常。這不是「訓練不夠」，是**訓練把非線性關掉了**。

三個投影（`_project_structure`，forward 不動、只夾參數）：

- `theta_max`：`theta.clamp_(0, theta_max)`。閾值跑到 cap 是**正常現象**（目標永遠偏好更稀疏的堆疊），所以它不是合格判準；判準是梯度帶。
- `leak_floor`：`beta.clamp_(min=logit(floor))`，保住 `1/(1-beta)` 的記憶視窗。
- `gain_cap`：對 `w_rec` 做譜半徑重標（power
  iteration），避免「>1 就成長」造成只靠閾值 clip 撐住。

**量測（同一份 4,000 筆子集、同一個 batch/lr，只改 guards）**：

| 設定                              | 2 epochs loss | 6 epochs loss | beta   | near   | sensitive | val CE |
| --------------------------------- | ------------- | ------------- | ------ | ------ | --------- | ------ |
| 舊：theta2.0 / leak0 / gain0      | 3.5564        | **2.2879**    | 0.7595 | 0.0242 | 0.542     | 3.874  |
| 新：theta1.0 / leak0.85 / gain1.0 | 3.6886        | 2.3302        | 0.85   | 0.0407 | 0.692     | 4.064  |

誠實讀法：**guard 在小規模短跑上貴 0.19 nats val CE**，換來 2.2 倍的梯度帶（near
0.0407 vs
0.0242）與被下界鎖住的記憶。短期它不會贏；它贏的是「跑很久之後還活著」。108M 那一輪就是沒有這條界線的證據（beta
0.54、near 0.0018）。

另外一個必須說清楚的量測細節：**theta 在 6
epochs 時已經到 0.9737/1.0（97%）**。把 cap 從 2.0 降到 1.0 只是把「釘住的位置」往下移，並沒有移除「想往外跑」的誘因。所以探針不把「theta 在 cap」當失敗，而是量
**梯度帶與 val CE**。

## 五、資料（實測）

`core_train.jsonl` / `core_val.jsonl`，`prepare_core_training_data.py`
產生（manifest 的 sha256 仍然吻合）：

| 項目                      | 值                                                                           |
| ------------------------- | ---------------------------------------------------------------------------- |
| 筆數                      | 149,489 train / 7,822 val（157,311 總，95/5）                                |
| 基準洩漏                  | **0**（593 題凍結題；整題比對 + 8-gram shingle）                             |
| 一個輸入多個答案          | 1,362（0.92%）                                                               |
| 答案被 `max_len=192` 切掉 | 0 筆「完全沒有目標」；10,789 筆（7.22%）被切在中途                           |
| val 答案的 `<unk>` 比例   | 0.65%                                                                        |
| 詞表                      | 32,773 atoms（`min_count=1`、`max_vocab=32768`；與 checkpoint **逐位相同**） |

詞表那一行是這一輪抓到的真缺陷之一：探針原本照 checkpoint 的 config 記錄用
`min_count=2`，重建出 31,081 個 atom——**id 的意義整個偏移**。`train_token_snn.py`
是硬寫 `min_count=1`（「罕見詞要能組合」），所以探針改成跟著它，並用
`kd.vocab_matches_checkpoint` 把「重建的詞表必須等於 checkpoint」變成檢查項。

## 六、學生 vs 教師（實測，同一批 val 答案位置）

| 模型 / 來源                      | 答案 atom 的 CE | 說明                                    |
| -------------------------------- | --------------- | --------------------------------------- |
| unigram                          | 5.78 nats       | 不看上下文                              |
| add-1 bigram                     | 4.98 nats       | 只有前一個 atom                         |
| **interpolated bigram（floor）** | **4.584 nats**  | λ=0.9，最強的「只看一個 token」         |
| 108M checkpoint（val）           | **3.088 nats**  | 13,925 atoms／400 筆；比 floor 好 1.497 |
| 教師 Qwen2.5-1.5B（atom 粒度）   | **1.755 nats**  | 1,526 atoms／40 筆                      |

兩個結論：

1. 學生**確實用了超過一個 token 的上下文**（floor
   4.584 打不贏它）。所以「SNN 什麼都沒學到」是錯的；它學到的是表徵，答題能力是另一回事。
2. 教師比學生好 **~1.3
   nats**，而且教師的優勢不是「更會猜下一個字」而已——在**字元邊界對齊**的位置上，教師把 53.2% 的質量放在與標準答案相容的 token 上（對齊率 58.7%，895/1,526）。**蒸餾有信息，不是儀式。**

## 七、蒸餾管線（實測）

學生切詞是
`["the", " c", "at"]`，教師是 BPE（151k）。兩邊邊界不一致，所以「軟標籤」必須**投影**，不能假設相等。`ai/ed3n/kd_targets.py`
的規則只有一條：

> 教師 token 的質量給**它是其前綴的最長 atom**；若沒有任何 atom 是它的前綴（BPE 片段比 atom 短），給**以它為前綴的最短 atom**；都沒有就丟掉並計數。

在真實位置上的量測（探針每次重跑都重算，不引用舊值）：

| 量                                  | 值                                   |
| ----------------------------------- | ------------------------------------ |
| 教師 top-64 質量成功投影的比例      | **0.989**（top-64 佔全部質量 0.989） |
| 答案 atom 有軟標籤的比例            | 314/565 = **55.6%**                  |
| 軟標籤中包含正解 atom 的比例        | **99.4%**                            |
| 正解 atom 在軟標籤上的平均質量      | 0.512                                |
| 學生在同一位置給正解 atom 的機率    | 0.123                                |
| KD loss（30 步 Adam，完整 softmax） | 10.492 → 2.814（×0.268）             |

「學生 0.123
vs 教師 0.512」是**相對**判準，不是自訂絕對門檻：蒸餾只有在教師比學生更知道答案時才會教對東西。若有 5% 以上的軟標籤不含正解 atom，restricted
KL 會把正解推向 0——那是**反向教學**，所以它是一條門檻（≥95%）。

`kd.loss_is_differentiable` 量到
`grad(embed)=3.68e-02`、`grad(w_rec)=2.97`——KD 目標會訓練遞歸堆疊，不是只訓練 head。

### 7.1 損失的形式（這一行曾經量錯）

KD 項是 **`-Σ_a q_a log p_a`，`p` 是模型對整個詞表的 softmax**，`q`
是教師分佈投影到學生 atom 後的質量、**不正規化**（`KdTargets.probs`
在保留的 atom 上重規一化到 1， `KdCache.build` 再乘回 `mapped_mass`，所以
`Σ q = mapped_mass`）。不是「對目標 atom 子集再 softmax」：子集 softmax 改掉了學生的正規化項，模型只要把目標 atom 一起放大、無視詞表其餘部分，loss 就會下降——**loss 下降但什麼都沒預測**。上面 10.492
→ 2.814 是完整 softmax 的重量；舊文件裡的「3.298 → 1.834」是子集版本，已作廢。

`q` 不正規化是刻意的：`mapped_mass < 1`
的位置（教師質量在投影中掉了）**貢獻得少**，而不是被悄悄重標成 1。快取統計裡的
`mapped_mass` 就是這個質量（不是重規一化後的 1.0），建置報告另存
`teacher_mapped_mass` 於 meta，訓練報告直接引用。

### 7.2 快取與訓練器接線

教師前向是每列一次 1.5B 推論，所以目標只算一次、存成
`KdCache`（`ai/ed3n/kd_cache.py`）：

- **綁定詞表**：快取存學生的 atom 指紋；載入時 `require_vocab()`
  不符就拒絕。同尺寸但順序不同的詞表也會被拒。
- **位置是學生 hidden 位置**：`start + k - 1`（`k`
  = 答案 atom 索引），不是教師 token 索引。
- **列索引就是樣本索引**：快取建在 `fits(read_pairs(...))`
  上，訓練器也吃同一份；`--kd-cache` 會先比對 `n_rows`，再抽樣 `verify_rows()`
  重新編碼比對 ids/start，不符就**拒絕訓練**而不是讓 loss 微微變差。
- **每 epoch 分開報告**：history 每列有 `kd_loss` 與
  `kd_batches`；總 loss 上升而 KD 下降＝軟標籤與硬標籤在互相拉扯。

詞表敏感度（實測兩個快取）：32,773 atoms → `mapped_mass` 0.989；12,005 atoms →
1.000。對齊率與覆蓋率**與詞表無關**，它們只取決於
`tokenize()`（純文字函數）與教師邊界；受詞表影響的是投影後保留多少質量。這是兩點量測，不是曲線。

## 八、準備度探針：五個域、三個結局

`scripts/probe_training_readiness.py`（read-only：不改資料、不寫 checkpoint、不碰評測題）：

| 域  | 問題                          | 檢查                                                                      |
| --- | ----------------------------- | ------------------------------------------------------------------------- |
| A   | 資料能不能學                  | manifest 雜湊、基準洩漏、被截斷/無目標的列、矛盾監督、`<unk>` 比例        |
| B   | 圖能不能學（reduced config）  | 每組梯度非零、動態在梯度帶內、24 筆可過擬合、seed 可重現、train/eval 一致 |
| C   | 目標函數有沒有信息            | interpolated bigram floor                                                 |
| D   | 蒸餾管線通不通                | 詞表一致、投影質量、覆蓋率、正解在標籤內、教師 > 學生、可微、可下降       |
| E   | checkpoint 是不是可續訓的基底 | 記憶有沒有塌、梯度帶、**同批 val CE vs floor**                            |

Exit code：`0` 全部通過、`1` 有 FAIL、`2`
沒有 FAIL 但有 BLOCKED（例如缺教師模型）。

**對 108M
checkpoint 的實測結果**（`{'PASS': 20, 'INFO': 8, 'FAIL': 2}`，172s）：

- FAIL `ckpt.leak_not_collapsed`：beta 0.5407（記憶 ~2 tokens）
- FAIL `ckpt.gradient_band`：near 0.0014、sensitive 0.0283
- PASS `ckpt.val_ce_vs_floor`：3.088 vs 4.584（+1.497）

**判讀**：108M
checkpoint 不是可續訓的基底。它的 loss 低是因為表徵有效，但遞歸與非線性已經被關掉；再跑下去只會沿著同一條捷徑走。這不是「epoch 不夠」，所以「多訓練幾輪」不是修法。

## 九、還沒被證明的事（照實寫）

1. **guard 的長期效果沒有量到**。上面只有 2/6 epochs 的小規模 A/B；「跑 1 epoch
   ×
   149k 之後 guard 仍守得住」是預測，不是量測。要證實它，需要用新 guards 跑一次真正的 run。
2. **教師的 1.755
   nats 是 atom 粒度、且含對齊損失**。它與學生 3.088 的比較是「同一批位置、不同切詞」，方向可信、絕對值不可當成嚴格的下界。
3. **55.6% 的覆蓋率**是「有軟標籤的 atom 比例」。其餘 44.4% 仍用硬標籤，所以蒸餾是**混合**目標，不是純 KD。這在
   `--kd-weight` 上是可調的，但沒有量過最佳值。
4. **answer coverage 受 `max_len`
   影響**：長答案被截斷後，尾端的 atom 沒有教師位置可對齊。
5. **參數分配 77% 在 head** 意味著「擴大模型」不會自動改善上下文使用；要動的是
   `w_rec` 與序列長度，這一輪沒有做。
6. **KD 的有效訊號受覆蓋率折扣**：只有 55.6% 的答案 atom 有目標，每個目標又只帶
   `mapped_mass`（0.989）的質量，所以 `--kd-weight 0.5`
   不等於「一半的損失來自教師」。權重與覆蓋率的交互作用沒有被分離量測。

## 十、怎麼重跑

```bash
# 完整準備度（含教師與 checkpoint；約 3 分鐘，需要 GGUF 與 llama_cpp）
./.venv/bin/python scripts/probe_training_readiness.py

# 離線（沒有教師模型時；D 會是 BLOCKED，exit 2）
./.venv/bin/python scripts/probe_training_readiness.py --skip-teacher

# 只量另一個 checkpoint
./.venv/bin/python scripts/probe_training_readiness.py --skip-teacher --checkpoint path/to/model.pt

# 寫成 JSON 給 CI 或報告用
./.venv/bin/python scripts/probe_training_readiness.py --json /tmp/readiness.json
```

蒸餾：

```bash
# 1) 建快取（每列一次教師前向；--limit/--max-len/--max-vocab 必須與之後的訓練完全相同）
./.venv/bin/python scripts/build_kd_cache.py \
    --limit 4000 --max-len 192 --max-vocab 12000 \
    --out data/kd/kd_4k_12k.npz --report data/kd/kd_4k_12k.json

# 2) 訓練（快取不符會直接拒絕，不會安靜地訓練錯位置）
./.venv/bin/python scripts/train_token_snn.py \
    --vocab token --limit 4000 --max-len 192 --max-vocab 12000 \
    --d-emb 512 --d-hidden 2560 --batch 8 --epochs 5 --patience 2 \
    --kd-cache data/kd/kd_4k_12k.npz --kd-weight 0.5 \
    --out /tmp/kd_ab/kd.pt --report /tmp/kd_ab/kd.json

# 3) 對照臂：同一條命令不加 --kd-cache，其他全部相同（同 seed、同資料、同詞表）
```
