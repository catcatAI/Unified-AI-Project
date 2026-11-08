# 全專案稽核報告 — 2026-11-05

> 主題：**宣告的裝置要真的被使用**。這一輪不是加功能，是把「設定說用了 GPU、實際在 CPU 上跑」這種**沒有錯誤訊息的謊**找出來，修成可驗證的行為；順手抓到一個只有在實跑表徵器時才會現形的獨立 bug（TextEncoder 回全零向量）。
>
> 上一輪（表層不得代替核心）的報告在
> `docs/AUDIT_REPORT_2026-11-04.md`；量測口徑見
> `docs/06-project-management/MEASUREMENT_MAP.md`；唯一的分數定義在
> `apps/backend/src/ai/meta/intelligence.py`。

## 一、判準（先寫清楚，否則修完會漂走）

1. **一個字串不是裝置。** `self.device = "cuda"`
   只有在 tensor 真的建在那裡時才算；屬性存在但沒有任何 tensor 跟著它，就是宣告了一張不存在的卡。
2. **「有沒有加速器」只有一份答案。** `torch.cuda.is_available()`
   不是這個問題：Intel Arc 透過 `torch.xpu`
   回答。解析器只能有一個（`core/system/config/compute_device.py`）。
3. **修復要有對照。** 任何「改 device／改後端」都要有 CPU
   vs 裝置的數值對照與回歸測試；預設值只放**實測較快**的那邊，不因為「有 GPU 就該用 GPU」。
4. **不動分數。**
   門檻、評測題、held-out、量測定義都沒改；核心分與系統分分開陳述。

## 二、已修（附證據）

### 1. `TensorSNNCore.device` 只被儲存、從沒被使用

`GardenEngine`／`VectorDictionary` 在 `compute_bool("garden_snn")` 開啟時把
`"cpu"` 改寫成字面值
`"cuda"`，但核心的所有 tensor（`_W`、activation、potential）都在 CPU 建立。也就是說：**配置宣稱 GPU、執行完全在 CPU、沒有任何 warning**。本機
`torch.cuda.is_available()` 是 `False`（GPU 走 `torch.xpu`），那段 `"cuda"`
連在別台机器上都不見得成立。

**同一個函式裡還有一顆地雷**：`_compute_timestep()` 用
`np.argpartition(potential, -k)` 取 top-k。CPU torch tensor 會透過 `__array__`
默默轉成 numpy 所以「以前能用」；一旦 tensor 真的在 XPU/CUDA 上，這行直接拋
`TypeError: can't convert xpu:0 device type tensor to numpy`。
**所以「把 device 接上」若沒先修這裡，就是一個會爆的錯誤修復。**

修法：

| 位置                   | 修正                                                                  |
| ---------------------- | --------------------------------------------------------------------- |
| `snn_core.resolve`     | `self.device` 由 `resolve_torch_device()` 決定（不可用→cpu＋warning） |
| `_zeros` / `_as_array` | 加 `device=`；`TensorSNNCore._new_zeros()` 一律建在 `self.device`     |
| `_compute_timestep`    | `np.argpartition` → 後端原生 `topk`（`_topk_indices`）                |
| `hebbian_update`       | index tensor 用 `as_tensor(..., device=self.device)`                  |
| `reset_for_retrain`    | `rand(..., device=self.device)`                                       |
| `load`                 | checkpoint（CPU/numpy）載入後 `.to(self.device)`                      |
| `get_stats`            | 多回 `"device"`，執行期可觀測（不再只能猜）                           |

### 2. `GardenEngine` / `VectorDictionary` 偽造 `"cuda"`

兩處 `if device == "cpu": device = "cuda"`
已移除。GARDEN 現在**預設 CPU**，理由是本輪實測（見第五節）：forward 在 XPU 上快 ~10x，但**每樣本一次的稀疏 Hebbian 更新慢 ~7x**，而訓練迴圈是後者主導。顯式
`device="xpu"`
仍被尊重（真的一路建在 XPU，parity 測試守住）。`compute_bool("garden_snn")`
仍決定sizing（`max_vocab`／`connection_budget`），不再假裝是裝置開關。

### 3. CLIP / Whisper 只在 CUDA 上「有 GPU」

`semantic_visual.py`／`semantic_audio.py`／`text_encoder.py` 寫死
`torch.cuda.is_available()`。在這台 Arc 機器上模型永遠留在 CPU，而程式碼看起來「支援 GPU」。改為共用解析器，模型與**輸入**一起搬（`move_batch_to_device`；只搬模型會 device
mismatch）。

### 4. 實跑才發現的獨立 bug：`TextEncoder` 在 transformers 5.x 回全零向量

`transformers 5.15.1` 的 `CLIPModel.get_text_features()` 回傳
`BaseModelOutputWithPooling`，不是 tensor。`encode_batch()` 直接呼叫
`text_features.cpu()` → `AttributeError` → 被 `except` 吞掉 → 回 `None` →
`encode()` 回**全零向量**。也就是 ED3N 文字路徑、`multimodal_bridge`、
`training_pipeline`
拿到的文字特徵全是 0（相似度永遠 0、訓練學不到東西），而且只有一行 warning。

修法：`pooler_output` → `text_embeds` → 裸 tensor 的順序取值（與
`semantic_visual` 一致），並補「pooled
output」與「舊版 tensor」兩種輸出的測試。**這是本輪唯一影響語意的修復**；其餘都是裝置（top-k 換成原生實作只在平手時可能改變勝者，見第 8 條）。

### 5. 裝置解析只有一份

`core/system/config/compute_device.py`：`device_available()`／
`resolve_torch_device()`（明確可用 > `xpu` > `cuda` >
`cpu`；不可用降級並warning）／`move_batch_to_device()`。`token_snn.resolve_device()`
改為委派（簽名不變，舊呼叫端不受影響）。

### 6. 診斷腳本不再把 Arc 說成「No CUDA GPU」

`scripts/test_gpu_direct.py`／`scripts/test_gpu_compat.py`
的子程序探針現在回報 CUDA 與 XPU，並在解析到的裝置上做 matmul；原本的建議文字（「去裝 wgpu/kompute 才能訓練 SNN」）也改成與專案實況一致（token-SNN 用 torch；GARDEN 預設 CPU 是量測結果）。

### 7. `compute.<feature>.mode` 曾被完全忽略

`configs/system/compute.default.yaml` 對每個特徵宣告 `auto`／`on`／`off`，並寫明
`off` = 「Force
CPU-only」。但 CLIP/Whisper/TextEncoder 只看「有沒有加速器」，從不讀這個設定；在本機（`laptop_power_saver`，三個旗標都是
`off`）它們照樣會選 XPU——**宣告與使用再次不一致**，只是方向相反。

修法：`resolve_feature_device(feature, ...)` 先問
`feature_compute_enabled(feature)`（讀 `compute_bool`），`off` 就回
`cpu`；讀不到設定時 fail open（仍可執行，只是不釘在 CPU）。三個表徵器改用
`semantic_visual`／`semantic_audio`（`TextEncoder` 是 CLIP 文字塔，跟
`semantic_visual` 同一開關）。**本機實測**：載入後
`_CLIP_DEVICE=_WHISPER_DEVICE=self._device="cpu"`；把 `compute_bool`
暫時改為 True 時，模型與輸入真的搬到 `xpu:0`
且輸出為單位向量（兩條路徑都驗過）。

### 8. top-k 換成原生實作後，一個測試其實在測 tie-break

全量測試只有一個失敗：`test_neural_state_merges_into_activations`。追下去發現它**不是**測注入，而是測平手時誰贏——兩條關聯權重都是 0.9，`potential`
在 r1／r2 上同為 0.9，舊的 `np.argpartition` 挑到 r2，`torch.topk`
挑到 r1。也就是說，那個測試原本靠的是 numpy 的任意的平手順序；換到後端原生 topk 後才顯露。修法是把測試資料改成**權重有明確高低**（0.95
vs
0.9），讓「注入讓 r2 勝出」變成真的因果，而不是 tie-break 的副作用；並補一條「注入信心為 0
→ 與沒有注入完全相同」的斷言。這是測試修正，不是改產品行為。

## 三、需注意（未修，附理由）

1. **GARDEN 訓練沒有 GPU 加速，是刻意的。**
   稀疏 Hebbian 是「每樣本一次、每次幾十個元素」的散寫，XPU 的 kernel
   launch／同步成本遠大於計算本身（實測 1.45s vs
   0.22s／200 次）。要讓 GPU 真的有意義，得先把更新**批次化**
   （累積 N 個樣本再一次寫入），那是行為變更與新測試，不在本輪。
2. **`garden_snn` 旗標的語意變窄了。**
   它以前（名義上）是裝置開關，現在只決定 sizing。把 `off`
   進一步解讀成「強制 numpy 後端」會改變 checkpoint 格式與記憶體行為，未做。
3. **`VectorDictionary.device` 是資訊性屬性。** 它的 embedding matrix 來自 numpy
   encoder，沒有 tensor 需要搬；保留欄位是 API 相容，不是宣稱。
4. **加速器首次呼叫有暖機成本。**
   CLIP 文字第一批約 1s（XPU 編譯），穩態才快（0.013s vs CPU
   0.125s／64 條）。短批次可能比 CPU 慢。
5. **`semantic-qa` 仍被 `classify_source`
   算 neural**（前一輪遺留）：改標籤會改量測定義，需單獨一輪。
6. **`scripts/train_token_snn.py --device` 不受 `compute.ed3n_snn` 限制。**
   應用內的 SNN 推論（`ai/ed3n/snn/snn_core.py`）讀
   `compute_bool("ed3n_snn")`；訓練腳本是操作者顯式指定裝置（`--device auto|xpu|cuda|cpu`），把它再依設定降級會違背那個顯式指令並拖慢刻意發起的訓練。這是**有意的區分**，不是漏改。
7. **GARDEN 的 activation 信心值目前不影響傳播。** 稀疏化（commit
   `15d3f3d70`）把 dense `a @ W` 換成「只加總作用中的列」，因此 `conf=0.1` 與
   `conf=1.0` 的傳播完全相同（只有 0 與非 0 之別）。`forward()`
   的 docstring 原先寫「低信心貢獻較少」，與程式不符——本輪**只更正docstring**，沒有改數學：恢復信心加權會改變所有 GARDEN 輸出，需要自己的量測輪（現有 341 個 GARDEN 測試是釘住目前行為的）。

## 四、查過沒問題

- CPU torch 上 `np.argpartition` 為何以前沒炸：透過 `__array__`
  轉 numpy；改成原生 `topk` 後 341 個 GARDEN 測試全過、輸出相同。
- checkpoint 跨後端：XPU 上 `save()` 產生的 `.pt`＋`.npz`
  sidecar 可在 CPU 載回，值完全一致（`test_save_load_roundtrip_is_device_independent`）。
- eviction／compaction、`reset_for_retrain`、`apply_decay`、`get_stats`
  在 XPU 上與 CPU parity（`test_snn_device.py`，本機真的跑，不是 skip）。
- 記憶體：20k×20k float32 = 1.6GB，在 9.9GB VRAM 內；RAM clamp 仍照舊。
- 全專案再掃 `cuda.is_available`／`.cuda()`：只剩註解與兩支診斷腳本（已改）。
- `flake8`／`black`／`isort`：本輪觸及的檔案全乾淨。

## 五、本輪量測（實跑，Arc B570 vs CPU）

| 項目                                        | CPU       | XPU        | 說明                                           |
| ------------------------------------------- | --------- | ---------- | ---------------------------------------------- |
| GARDEN forward ×50（V=20k, 1% 稀疏）        | 8.79s     | **0.83s**  | 推論 GPU 快 ~10x                               |
| GARDEN Hebbian ×200（V=10k, 稀疏散寫）      | **0.22s** | 1.45s      | 訓練 GPU 慢 ~7x                                |
| CLIP 文字 64 條（穩態）                     | 0.125s    | **0.013s** | 首次 XPU 約 1s 暖機                            |
| CLIP 影像 1 張                              | 0.165s    | **0.028s** |                                                |
| CLIP/Whisper/TextEncoder 數值               | —         | —          | CPU vs XPU `max diff ≤ 4.8e-7`、`cos 1.000000` |
| `train_token_snn.py --limit 120 --epochs 1` | 1s        | 5s         | 小模型；確認 `device=xpu` 真的跑得完、能存檔   |

> 讀法：CLIP/Whisper 那兩列是**把 `compute_bool` 暫時設為 True**
> 量到的上限，不是本機預設行為——本機 profile 是 `laptop_power_saver`，
> `semantic_visual`／`semantic_audio`／`garden_snn` 都是
> `off`，因此實際執行走 CPU（仍可推論，只是不加速）。這也是第 7 條修復的驗收：宣告
> `off` 就得是 `off`。

重現指令（本機）：

```bash
# 1. 裝置與後端
PYTHONPATH=apps/backend/src ./.venv/bin/python - <<'PY'
import torch
from ai.ed3n.token_snn import resolve_device
print(torch.__version__, torch.cuda.is_available(),
      hasattr(torch, "xpu") and torch.xpu.is_available(), resolve_device(torch))
PY

# 2. GARDEN 裝置 parity／存讀（會真的跑 XPU）
./.venv/bin/python -m pytest tests/ai/garden/test_snn_device.py -v

# 3. 表徵器（快取模型、離線）
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=apps/backend/src \
  ./.venv/bin/python - <<'PY'
from ai.multimodal.semantic_visual import SemanticVisualEncoder
print(SemanticVisualEncoder().encode_text(["a photo of a cat"]).shape)
PY

# 4. token-SNN 真的在 XPU 上跑
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/train_token_snn.py \
  --limit 120 --epochs 1 --batch 8 --max-len 48 --d-hidden 24 --d-emb 12 \
  --eval-sample 5 --out /tmp/tok_snn.pt --report /tmp/tok_snn.json
```

## 六、後續（依序）

1. **批次化 Hebbian 更新**，再決定 GARDEN 是否值得走 XPU 訓練（目前預設 CPU 是正確的，但「GPU 沒用」不是永久結論）。
2. `semantic-qa` 的來源標籤（前一輪遺留；會讓 `neural_share` 下降但更誠實）。
3. 邊界題 0/324（核心缺口）——與裝置無關，仍是最大的失分來源。
4. 全量測試與事實門的結果記在下方（本輪收尾時填）。

## 七、驗收（2026-11-05 實跑）

| 檢查                                               | 結果                                                |
| -------------------------------------------------- | --------------------------------------------------- |
| `pytest tests/ apps/backend/tests/`                | **9,248 passed / 107 skipped / 0 failed**（8:27）   |
| `tests/ai/garden`                                  | 341 passed（含 10 條真的在 XPU 上跑的 parity）      |
| `tests/core/config/test_compute_device.py`         | 19 passed                                           |
| `tests/ai/multimodal/test_text_encoder_outputs.py` | 4 passed                                            |
| `scripts/check_fact_gates.py`                      | **ALL PASS**（`definitions 定義差=11` 為既有 INFO） |
| `flake8` / `black --check` / `isort --check-only`  | 本輪觸及檔案全乾淨                                  |

## 八、追查「核心分為什麼是 0.00/10」（是不是量測把部分正確吃掉）

問題：核心 0.00 是否其實是「0～0.999 的部分正確被評分規則判成 0」？

三個層次要分開，逐一查：

### 1. 生產路徑：0 因為核心「不在回答路徑上」，不是答錯

`scripts/census_reply_provenance.py` 對同一條被計分的 `NativeBackend`
路徑逐題記錄正確答案的生產者：

| 正確答案  | 題數 | 生產者                             |
| --------- | ---- | ---------------------------------- |
| knowledge | 8    | 全部 `lookup`（精選庫／wiki 檢索） |
| math      | 32   | 全部 `computed`（確定性算術引擎）  |
| routing   | 10   | 全部 `classifier`（分類器標籤）    |
| code      | 0    | —                                  |

**49 個正確答案中，由模型（SNN／ED3N／GARDEN／LLM）產生的：0。**
這一類 0 的正確讀法是「缺席」——核心沒有被放上場，不是被評分判錯。把它和「量到但錯」混為一談，會誤以為核心有 49 題的近失。

### 2. 對照組：把核心直接放上同一批題目，結果仍是 0 正確

`scripts/probe_core_control.py`
用同一批凍結題、同一條評分，讓 GARDEN／ED3N／TOK-SNN／LLM 各自回答（`data/intelligence_reports/core_control.json`）：

| 套件            | ED3N answered / 正確 | TOK-SNN answered / 正確 | GARDEN      |
| --------------- | -------------------- | ----------------------- | ----------- |
| math（40）      | 40 / **0**           | 40 / **0**              | 0（無覆蓋） |
| knowledge（15） | 15 / **0**           | 15 / **0**              | 0（無覆蓋） |
| code（10）      | 10 / **0**           | 10 / **0**              | 0（無覆蓋） |

所以「有回答」和「答對」是分開量的：coverage 100% 的兩套核心，正確率是 0%。

### 3. 有沒有「近正確」被評分抹掉？用比門檻更寬的規則重測

評分規則（`run_benchmarks.score_item`）不是嚴格的：numeric 只看「最後一個數字」（`_final_numbers`，有 final-answer 標記時取標記後第一個），keyword 只要標定概念全在即可。也就是說若模型真的算出正解、只是後面又接了別的字，**多數情況會被判錯**
——這是真的假陰性風險，所以另外用更寬的規則重測：**答案體中任何位置出現正解數字都算**（先切掉 TOK-SNN 的
`<al_out>` 情緒狀態塊，避免 `health=0.86`
這類數字干擾，也避免它遮蔽前面真正的答案）。實測（同一份 rows）：

| 套件      | 生產者     | 正解字串出現在輸出任何位置 | 答案體中出現正解數字 |
| --------- | ---------- | -------------------------- | -------------------- |
| math      | ED3N       | 0 / 40                     | 0 / 40               |
| math      | TOK-SNN    | 2 / 40                     | 0 / 40               |
| knowledge | ED3N / TOK | 0 / 15、0 / 15             | —                    |
| code      | ED3N / TOK | 0 / 10、0 / 10             | —                    |

那 2 筆 TOK-SNN「沾到」是巧合，不是答對：`math-002`（gold 4）命中 `a=0.4`、
`math-008`（gold 3）命中 `0.37`／`0.33`——兩者都在情緒狀態塊裡，與題目無關。

抽樣輸出也一致：ED3N math 回「何为」「六 〦 亅 兆電子伏 六碳糖」，TOK-SNN 回
`The 1verage 5] … <al_out> v=0.21 …`，knowledge
ED3N 回情緒詞串、TOK 回無關英文句子——**沒有任何一題是「意思對、字面不同」**。

### 結論（照實）

- **0.00/10 不是量測下限造成的**：換成最寬鬆的規則重算，仍是 0。
- 核心的失敗是「規模／表徵」層面的失敗（見
  `CORE_GAP_ANALYSIS.md`），不是評分太嚴。
- 仍存在的量測限制（不影響上面的結論，但要寫清楚）：numeric 只看最後一個數字，若核心哪天算出正解卻在後面接情緒狀態塊，會被判錯（本輪用切掉狀態塊的寬鬆規則重測，0/40 不受影響）；只量四類題型；strict 的 keyword 判定仍是 surface 比對（語意等價但換詞會判錯，只是本次沒有任何一筆落在邊界）；ED3N 讀
  `step_decoder`，不是
  `generate()`；GARDEN 沒有 prompt-following 能力，等於不參賽。若要更嚴格，應另立一輪「部分正確／語意相近」評分，且不得拿來改動現有門檻。

## 九、108.6M 核心訓練：結果與同輪修掉的三個誤判來源

### 1. 訓練真的跑完了（XPU，1 epoch）

| 項目     | 值                                                                     |
| -------- | ---------------------------------------------------------------------- |
| 參數     | 108,583,431                                                            |
| 語料     | 149,489 列（`max_len 192` 可容納 138,671）                             |
| 設定     | d_emb 512 / d_hidden 2560 / 1 layer / vocab 32,773、batch 4、lr 1e-3   |
| 時間     | 6,677 s 訓練（總 6,755 s），`device=xpu`                               |
| loss     | 2.3623（1 epoch）                                                      |
| dynamics | `alive`（spike rate 0.0816、threshold 1.9995）                         |
| TF       | 回應 0.4215、狀態塊 0（語料沒有 `<al_out>`，`--tail-weight` 是 no-op） |
| exact    | train 6/100、val 8/100                                                 |

**那 8% 不是能力**：逐一列印命中，5 句是比較句（`giraffe is shorter than turtle.`、
`train比高铁矮`…）、3 個是
`False`；同一份 val 的前 200 列是 0/200。它學到的是比較句的格式與實體次序，不是算術或知識。

### 2. 凍結題目仍是 0（不是沒回答）

| 套件      | 正確 | 有回答 | distinct | LLM 對照 |
| --------- | ---- | ------ | -------- | -------- |
| math      | 0/40 | 37/40  | 19       | 27/40    |
| knowledge | 0/15 | 15/15  | 9        | 11/15    |
| code      | 0/10 | 6/10   | 5        | 9/10     |

所以 0 不是 coverage、也不是單一模式崩潰：模型在生成不同句子，只是句子不對（`3+5×2`
→ `12`、`2**10` → `120`、不同物理題共用 `The sum of 10 is 10.`）。核心分維持
**0.00/10**；系統分 6.41 不變（這輪沒有動任何表現層分數）。

### 3. 同輪修掉的誤判來源

- **`--core-checkpoint` 不再覆蓋生產快取**：原本指定 checkpoint 時探針會寫回
  `core_control.json`，下一次 `--from-cache`
  就會把別顆模型的數字當成上線核心。現在寫到
  `core_control_<checkpoint>.json`，並在 payload 記 `core_probe_checkpoint`。
- **`hebbian_update` 同呼叫剪枝（另一邊的發現）**：`snn_core.py`
  先寫權重再對同一列剪枝（floor 0.01），單步增量
  `lr × plasticity × target_strength` 在 plasticity <
  1 時必被剪掉，樣本永遠學不到。修法只豁免本次寫入的格子，其他剪枝不變。實測（hard、seed
  11、1 epoch）：修前 23/48 目標列整列 0、phase margin **+0.02946**
  （0 分被算成「不差」），修後 0 列為 0、margin
  **−0.03326**——先前的正 margin 是缺陷造成的假象，不是相位調制有效。
- **`test_ham_al_policy.py` 的 6 個失敗是測試過期，不是生產 bug**：HEAD
  `ebcbe5d14` 把內生節律（`rhythm.activation`）加入記憶權重（文件寫在
  `al_memory_policy.py`），但測試 fixture 只清了
  `drift/intensity/life_phase`，於是生產快照裡一直在跑的振盪器讓「未觀測」永遠不成立、期望值 1.5 變成 1.4004。fixture 現在釘
  `rhythm=None` 與
  `emotion=None`，並新增一條「相位在場時要留下權重與歸因」的測試。73 條 AL/記憶測試全過。

### 4. 驗收（本輪實跑）

- 全量 `pytest tests/ apps/backend/tests/`：**9,455 passed / 107 skipped / 0
  failed**（8:28，HEAD 8a09ae156 前後一致）。
- `scripts/check_fact_gates.py`：**ALL PASS**。
- `black` / `isort` / `flake8`：乾淨。
- 一個過程中的插曲照實記：第一次全量跑出 3 個 `test_al_downstream_protocol`
  失敗，是另一邊在跑期間（12:14）提交 `8a09ae156`
  改了同一個測試檔——pytest 收集到舊版、斷言時讀到新版，行號與測試名對不上。HEAD 穩定後重跑全綠，單檔也 10/10，不是真缺陷。
