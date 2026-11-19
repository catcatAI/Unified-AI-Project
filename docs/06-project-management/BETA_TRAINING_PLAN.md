<!--
  FILE_HASH: BETA-TRAIN-PLAN-20261119
  FILE_PATH: docs/06-project-management/BETA_TRAINING_PLAN.md
  FILE_TYPE: planning
  PURPOSE: 從研究走向測試版：容量、模態、預檢、階段與出關條件的唯一整併計畫
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-11-19
-->

# 完整訓練與測試版計畫（容量 → 乾淨基底 → 放大 → beta）

> 2026-11-19。這份文件把「核心什麼時候可以脫離研究、進入測試版」整理成一份可執行的計畫。
> 它**不是**結果報告：每個數字都標了量測來源；還沒量到的寫「未量測」，不用預測填空。
>
> 讀法：§0 是這份文件的地位；§1 是實測現狀；§3 是「能裝多少內容」的協定（**§A 是跑前登記**）；
> §4 是模態矩陣；§5 是逐項預檢；§6 是執行階段；§7 是 beta 出關條件（與研究殘留分開）。

## 0. 這份文件的地位

- **它回答什麼**：現在能不能開始完整訓練；模型本身能裝多少內容；哪些模態真的可訓練；
  正式開跑前還有哪些細節沒確認；核心要達到什麼狀態才叫「測試版」。
- **它不回答什麼**：核心現在有多聰明（那是 `intelligence_report.json` 的唯一分數，目前核心
  **0.00/10**、系統 6.41/10）；也不宣稱訓練會讓核心變聰明——容量是必要條件，不是能力證明。
- **數字紀律**：所有「現況」數字都可用 §9 的指令重跑；所有「計畫」數字都寫成上限（時間、RAM、VRAM），
  不是承諾。容量量測的判準寫在 §A，**跑之前**定稿；跑完的結果另開 §B，不回寫 §A。
- **與其他文件的關係**：訓練內部機制看 `TRAINING_INTERNALS.md`；核心為何是 0 看
  `CORE_GAP_ANALYSIS.md`；每層在哪裡量看 `MEASUREMENT_MAP.md`；外部及格線看
  `INTELLIGENCE_PASS_CRITERIA.md`；產品驗收看 `RELEASE_CRITERIA.md`。這份文件只做整併與排程，
  不重複定義。

## 1. 實測現狀（2026-11-19）

### 1.1 分數與階梯（未變）

| 量                    | 值                      | 來源                                    |
| --------------------- | ----------------------- | --------------------------------------- |
| 核心分                | **0.00 / 10**           | `scripts/report_intelligence.py`        |
| 系統分（含表層）      | **6.41 / 10**           | 同上（表層不計入核心）                  |
| 核心階梯 / 系統階梯   | **L0 / L2**             | `AI_CAPABILITY_LADDER.md`               |
| 外部及格線（六維度）  | 45 / 61 / 70 / 44 / 53 / 54（%） | `INTELLIGENCE_PASS_CRITERIA.md` |

核心分不因這份計畫改變；任何訓練若沒有讓**模型產生且正確**的答案增加，核心分就不動。

### 1.2 checkpoint（實測參數，不是檔名推測）

| 檔案                          | 參數      | 形狀（d_emb / d_hidden） | 詞表 | 可續訓？                                             |
| ----------------------------- | --------- | ------------------------ | ---- | ---------------------------------------------------- |
| `token_snn_108m.pt`           | 108,583,431 | 512 / 2560             | 32,773 | **否**：beta 0.5407（記憶 ~2 token）、near 0.0014、sensitive 0.0283；`probe_training_readiness` 2 FAIL |
| `token_snn_core149k.pt`       | 7,623,879   | 96 / 512               | 12,005 | 未以 readiness 探針判定                              |
| `token_snn_distill.pt`        | 2,491,227   | 96 / 512（詞表較小）   | 未記 | 蒸餾實驗產物，非預設路徑                             |
| `token_snn.pt`                | 3,525,319   | 96 / 192               | 12,005 | 預設訓練輸出                                         |
| `token_snn_curriculum.pt`     | 60,403      | 96 / 192（max_len 24） | 小   | 課程實驗產物                                         |

**結論**：108M 是「loss 看起來有降、非線性已被關掉」的檢查點，不能拿來續訓；完整訓練必須從
新初始化 + guards 開始（`theta_max=1.0`、`leak_floor=0.85`、`gain_cap=1.0`）。這一點是
`TRAINING_INTERNALS.md` §4/§8 已量測的，不是本計畫的假設。

### 1.3 資料（實測）

| 項目                         | 值                                             |
| ---------------------------- | ---------------------------------------------- |
| `core_train.jsonl`           | 149,489 列（manifest sha256 已記錄）           |
| `core_val.jsonl`             | 7,822 列                                       |
| 基準洩漏                     | **0**（593 題凍結題；整題 + 8-gram shingle）   |
| 同一輸入多個答案             | 1,084 個 prompt（0.73%，本次 `--inventory` 重測；舊文件記 1,362） |
| 一個輸入多個答案的處理       | 取第一條；這是 supervised 噪聲，不是洩漏       |

**max_len=192、詞表 12,005（`max_vocab=12000` + 5 個特殊符號）時的容量包絡**（本次 `--inventory` 實測）：

| 量                           | 值                                  |
| ---------------------------- | ----------------------------------- |
| 可放進 192 atoms 的訓練列    | **138,671 / 149,489**（92.8%）      |
| 放不進（會被丟掉）           | **10,818**（7.2%）                  |
| 驗證集可放進                 | 7,197 / 7,822（92.0%）              |
| 驗證答案 atom 的 `<unk>` 比  | **1.78%**（12k 詞表）               |
| 唯一 prompt                  | 148,405（重複率 0.7%）              |
| 每列 atom 中位數             | 24                                  |

兩個必須說清楚的取捨：

1. **12k 詞表把 `<unk>` 從 0.65%（32,773 詞表）抬到 1.78%**。稀有詞變成 `<unk>` 後序列變短，
   所以「放得進」的列變多（舊文件在 32k 詞表下記 10,789 列被截斷，與這裡的 10,818 不可直接比）。
   完整訓練要選哪一個，必須用同一批驗證列量 val CE，不能只看 `<unk>` 或只看截斷率。
2. **7.2% 的列沒有目標**：題目+答案超過 192 atoms 時整列被 `fits()` 丟掉，它們仍佔語料但不參與訓練。
   這是 `max_len` 的硬上限，不是訓練不足。

### 1.4 硬體與磁碟

| 項目        | 值                                                            |
| ----------- | ------------------------------------------------------------- |
| CPU / RAM   | 12 cores / 15.7 GB                                            |
| 加速器      | Intel Arc B570（`torch.xpu`，torch 2.14.1+xpu）               |
| 磁碟        | 916 GB 總、748 GB 已用、**121 GB 可用**（87%）                |
| 既有模型    | `data/models` 14 GB（Qwen2.5 1.5B/7B/14B GGUF）               |
| checkpoint  | `data/checkpoints` 1.6 GB                                     |

**硬性上限（每次跑都適用）**：CPU ≤ 50%、RAM ≤ 60%（約 9.4 GB）、GPU/VRAM ≤ 60%、
swap ≤ 60%。同時只能有一個受上限約束的重跑；別人在跑時不啟動第二個。容量探針本身很輕
（見 §B），但完整訓練必須用 `scripts/gpu_limit.py --run --target 0.5` 之類的方式把 GPU 職責壓住。

## 2. 「完整訓練」的範圍與非目標

### 2.1 範圍（這次真的要做的）

1. **文字核心**：token-SNN（`ai/ed3n/token_snn.py`）從乾淨初始化訓練，guards 全開。
2. **容量**：先量「能裝多少列」，再決定寬度與資料量（§3、§A）。
3. **乾淨基底**：用全語料跑一個短排程，讓 val CE 贏過 interpolated bigram floor，且梯度帶沒有塌。
4. **放大**：只有在容量曲線顯示「還沒飽和」且硬體包絡允許時才加寬/加深；不是先加再說。
5. **測試版接線**：checkpoint 進生產路徑時必須標 `source=snn`，且不得讓表層代答（§7）。

### 2.2 非目標（這次不做，避免把別的問題混進來）

- **不做 LLM 預訓練/微調**：Qwen GGUF 是教師與對照組，不是本次學生。
- **不做 CLIP/Whisper 端到端微調**：它們保持凍結（§4）；可訓練的是投影層。
- **不改 GARDEN 的稀疏 Hebbian 預設**：GPU 對稀疏更新反而慢（§X #281 實測），維持 CPU。
- **不改任何及格線、評測題、held-out 切分**：容量是描述量，不是拿來調門檻的。
- **不把模板/記憶/檢索的正确答案算進核心分**：`is_core_backend()` 是唯一邊界。

## 3. 容量：三種不同的「能裝多少」

「能裝多少內容」在三個層次上答案不同，混在一起就會得到一個聽起來很大、但沒有意義的數字。

| 層次             | 問的問題                                   | 怎麼量                                   | 本次會不會量 |
| ---------------- | ------------------------------------------ | ---------------------------------------- | ------------ |
| 硬體包絡         | 這台機器能跑多大的模型                     | `scripts/probe_scale_envelope.py`（RSS/VRAM） | 已有儀器，必要時重跑 |
| 表徵包絡         | 語料有多少列/詞進得去                      | `probe_content_capacity.py --inventory`  | **已量**（§1.3） |
| 參數容量（儲存） | 這個寬度能記住多少列，還能原樣產出         | `probe_content_capacity.py`（訓練）      | **本次要量**（§A） |
| 泛化             | 記住的東西能不能轉移到沒教過的列           | 同一份報告的 val 欄 + 後續 benchmark     | 同步量，僅描述 |

### 3.1 為什麼用「teacher-forced 整題正確率」當儲存判準

- 它把「答案在權重裡」和「解碼會漂移」分開：prompt 在眼前、gold 前綴餵進去，只要答案區每個
  token 都是 argmax，就表示這列被存住了。
- 它便宜：一次 forward，不需要逐 token 生成，所以可以在多個 N、多個寬度上重跑。
- 它**不是**能力分數：同一份報告另外印 greedy exact（能不能解碼出來）與 val 欄（能不能轉移）。
  三個數字必須一起讀，任何一個單獨拿去對外都會誤導。

### 3.2 判準（跑前寫死，見 §A）

- 一列算「存住」若整題 teacher-forced 正確率 ≥ **0.90**。
- 容量＝**連續通過的前綴**的最大 N；第一個失敗的 N 就是邊界。
- 若曲線非單調（小的失敗、大的反而通過），照實標 `non_monotonic`，不修圓、不挑對自己有利的點。
- 若 128 就失敗 → 回答「這個設定連 128 列都存不住」；若 2048 全過 → 回答「≥2048，網格沒碰到膝點」。
  兩者都是結果，都不四捨五入成「很大」。

### 3.3 這個儀器不能回答的問題

- 存住 ≠ 會算：記住乘積表與實作乘法在「存住」上同分（§95 的結論仍然成立）。
- 存住 ≠ 會轉移：val 欄只是描述；要裁決泛化，得用凍結 benchmark 與外部及格線。
- 它不量「事實知識」：`core_train` 是 instruction/算術/邏輯/關聯的混合，不是百科。
- 它不量多模態：視覺/音訊的容量要各自的線性探針，見 §4。

## 4. 模態矩陣（哪些真的可訓練）

| 模態             | 可用資料（實測）                        | 編碼器 / 維度                                   | 專案會更新的參數                    | 這次能不能訓 | 限制 |
| ---------------- | --------------------------------------- | ----------------------------------------------- | ----------------------------------- | ------------ | ---- |
| 文字（核心）     | 149,489 列 instruction/算術/邏輯/關聯   | token-SNN，3.5M（96/192）或 16.7M（256/1024）    | 全部（embed/w_in/w_rec/head/β/θ）   | **是**       | max_len 192；12k 詞表 unk 1.78% |
| 文字（語意）     | 同上                                    | CLIP text，512-d                                | **0（凍結）**                       | 否           | 只當表徵/檢索 |
| 視覺（手做特徵） | CIFAR-10：50,000 訓練 + 10,000 測試     | `VisualEncoder` 256-d（CNN 統計+顏色+邊緣+紋理）| 投影矩陣 256×~119（numpy，`train_step`） | 是（線性頭） | 只訓投影，不訓特徵抽取 |
| 視覺（語意）     | 同上                                    | CLIP image，512-d                               | **0（凍結）**                       | 否           | 無梯度 |
| 音訊（頻譜）     | ESC-50：2,000 clips、50 類（每類 40）   | `AudioSpectralEncoder` 128-d（MFCC+mel+統計）   | 投影矩陣 128×n_raw（`train_step`）   | 是（線性頭） | 2,000 筆，類別平衡但量小 |
| 音訊（語意）     | 同上                                    | Whisper encoder，384-d                          | **0（凍結）**                       | 否           | 無梯度 |
| 共享潛空間       | 以上特徵                                | `SharedLatentSpace` 64-d                        | 每個模態的 W、b（numpy）            | 是           | 只線性對齊 |
| ED3N 影像/音訊鍵 | 影像/音訊 bytes                         | `ai/ed3n/multimodal/{image,audio}_encoder.py`   | 無（規則→字典鍵）                   | 否           | 不是梯度訓練 |

**判讀**：

1. **只有文字核心是「模型本身」的完整訓練**；視覺/音訊目前只有線性投影與對齊層可訓，
   骨幹（CLIP/Whisper）凍結。把它們說成「多模態訓練完成」會是誇大。
2. **資料量 vs 容量**：CIFAR 50k、ESC-50 2k 都足以訓線性頭，但不足以訓骨幹；
   要端到端，得先有可觀的 GPU 預算與標註，這是 beta 之後的事。
3. **授權**：ESC-50 是 CC BY-NC 3.0（非商業）；CIFAR-10 供研究使用。 beta 若要對外散布，
   必須先換成可商用資料或只保留程式碼、不散布權重/資料。這件事寫進 §5 預檢（17）。

## 5. 逐項預檢（開跑前必須全部有答案）

| #   | 檢查項                     | 現況 | 證據 / 指令                                                                 | 備註 |
| --- | -------------------------- | ---- | --------------------------------------------------------------------------- | ---- |
| 1   | 資料雜湊仍吻合             | ✅   | `core_train_manifest.json` 的 sha256；`probe_training_readiness.py` A 域     | 檔案改過就重算 |
| 2   | 基準洩漏 = 0               | ✅   | manifest `benchmark_leak: 26`（已丟棄）；readiness A                       | 不可用 benchmark 題訓練 |
| 3   | 詞表與 checkpoint 綁定     | ✅   | `kd_cache.require_vocab`、`TokenSNN.load` 的 vocab 比對                     | 換詞表＝換 id，必須重訓 |
| 4   | 續訓基底是健康的           | ⚠️   | `probe_training_readiness.py --checkpoint ...`；108M 是 2 FAIL                | **不要續 108M**；從新初始化 |
| 5   | 同 seed 可重現             | ✅   | `--seed` 在建模前 `manual_seed`；`tests/test_train_token_snn.py` 有契約       | 跨裝置不保證 bitwise |
| 6   | 裝置解析正確               | ✅   | `core/system/config/compute_device.py`；`resolve_device` 回 `xpu`            | 配置 `off` 時不得偷用加速器 |
| 7   | 穩定 guards 開啟           | ✅   | `theta_max=1.0`、`leak_floor=0.85`、`gain_cap=1.0`（本次協定）               | 預設 CLI 仍是舊值，必須顯式傳 |
| 8   | 資源上限                   | ✅   | CPU ≤50%、RAM ≤60%、GPU ≤60%、swap ≤60%；`gpu_limit.py`                       | 同時只跑一個 |
| 9   | 續跑/斷點                  | ✅   | `train_on(start_epoch, opt_state, guard_state)`；`--resume`                  | 長跑每 epoch 存 |
| 10  | 評測集分離                 | ✅   | 訓練 `core_train`、驗證 `core_val`、凍結 benchmark 另存                       | 不得在 val 上調參後又報 val |
| 11  | 來源可追溯                 | ✅   | `census_reply_provenance.py --check`；`is_core_backend()`                    | 模型產生才算核心 |
| 12  | 表層不得代答               | ✅   | `services/llm/generation_gate.py`；§X #280 的 5 條修正                        | 有生成後端時交棒 |
| 13  | 報告 schema                | ✅   | `train_token_snn.py` 的 `report`（含 loss/val/dynamics/tf）                   | 缺欄位＝不可比 |
| 14  | 門禁                       | ✅   | `scripts/check_fact_gates.py`；`check_layer_separation.py`                   | 新儀器要加契約測試 |
| 15  | 版本/文件同步              | ✅   | `tests/test_version_consistency.py`；生成檔用 `check_generated_docs.py --fix` | 不手改生成檔 |
| 16  | `RELEASE_CRITERIA` 的舊敘述 | ⚠️   | 文件仍寫「hardware acceleration not supported, CPU only」                     | 與 §X #281 的 XPU 實測不一致，需另開文件修正（本次不動產品門檻） |
| 17  | 資料/權重授權              | ⚠️   | ESC-50 CC BY-NC 3.0；CIFAR-10 研究用途                                        | 對外散布前必須處理 |
| 18  | 回滾方案                   | ✅   | checkpoint 另存、`--out` 不覆蓋舊檔；報告進 `data/`（gitignored）             | 壞 run 不覆蓋好 run |

**判定**：1–15 與 18 已具備；4、16、17 是「已知且被記錄的限制」，不是阻擋開跑的理由——
4 的解法是「不要續 108M」，16/17 是 beta 對外散佈前的文件/授權工作。

## 6. 執行階段（含預算與門檻）

每個階段都先寫判準再跑；階段之間可以停，但不能把上一階段的失敗用下一階段的資源蓋掉。

### P0 — 預檢與包絡（✅ 本次已完成）

- `probe_training_readiness.py --skip-teacher`（108M 的 2 FAIL 已記錄）
- `probe_content_capacity.py --inventory`（§1.3）
- 產出：本文件 §1；無訓練、無 checkpoint。

### P1 — 容量曲線（本次要跑；§A 已登記）

- N ∈ {128, 512, 2048}；寬度 small（3.5M）與 medium（16.7M）；每列 8 epochs。
- 指標：train whole-answer TF、greedy exact、val whole；容量規則見 §3.2。
- 預算上限：每個 run ≤ 15 分鐘、總計 ≤ 90 分鐘；**用 CPU、`OMP_NUM_THREADS=4`**（XPU 實測
  整機 RAM 63.5% 超限，見 §A.2），不啟用 GPU。
- 產出：`data/capacity/report.json`（gitignored）+ §B（結果，跑後另寫）。

### P2 — 乾淨基底（容量結果出來後才排）

- 目的：證明「新初始化 + guards + 全語料」能讓 val CE 贏過同切片的 bigram floor，且
  `dynamics` 的 near/sensitive 沒有塌。
- 候選寬度由 P1 決定（若 medium 的容量明顯較高且硬體包絡允許，就用 medium；否則先用 small）。
- 排程：最多 2 epochs（先求健康，不求分數）；每個 epoch 存檔；`--eval-every` 量 exact。
- 門檻（跑前寫死）：val CE < 同切片 floor（`measure_bigram_floor.py`）；`near_threshold` 不低於
  0.01、`sensitive` 不低於 0.05；否則視為「非線性又被關掉」，不加 epoch，先修。
- 產出：報告 + checkpoint 到 `data/checkpoints/`（不覆蓋既有檔）。

### P3 — 放大決策（不訓練）

- 只有當 P1 顯示「容量 ≥ 2048 且還沒飽和」或「medium 明顯優於 small」時，才把寬度往上加。
- 上限由 `probe_scale_envelope.py` 的實測包絡決定，不由「覺得可以」決定。
- 若 P1 在 512 就飽和，結論是「先改架構/表徵（vocab、max_len、readout），不是加寬」。
  這一條是止損：加寬一個已經飽和的模型只會燒電。

### P4 — 完整訓練（P2/P3 通過才做）

- 全語料（138,671 列可訓練）、guards、cosine、patience 以 val CE 為準；每 epoch 存
  `weights + opt_state + guard_state`，可中斷續跑。
- 蒸餾（`--kd-cache`）**預設不開**：§11.7 的結論是「管線通、未建立品質增益」。若要開，必須
  另寫受檢定力的登記（5 seeds、配對、CI 排除 0），不得先跑再挑。
- 預算：先以「1 epoch 的實測時間 × 期望 epoch 數」估，跑之前印出來；超過 6 小時就切成兩段續跑。
- 產出：`data/intelligence_reports/` 的報告 + checkpoint；核心分仍是量測後才知道。

### P5 — 接線與影子模式（beta 前置）

- 把 checkpoint 接進生產路径的**影子分支**：同一題同時跑核心與現有路徑，核心輸出不直接給使用者，
  只記錄 `source=snn`、延遲、是否正確（用凍結題）。
- 這一步不改使用者看到的行為，因此可以在不冒險的情況下量「核心上線會長什麼樣」。
- 通過條件：延遲在使用者可接受範圍（先量，不先訂）、錯誤不影響主路徑、provenance 正確。

### P6 — 測試版（§7）

## 7. 測試版出關條件（與研究殘留分開）

「測試版」是**工程與量測狀態**，不是「核心變聰明了」。以下 B0–B3 依序達成；任何一項沒過，
就還是研究版，不對外稱 beta。

### B0 — 可重現的訓練產物

- 一個 checkpoint 附：資料 sha256、詞表指紋、config、seed、guards、loss/val 曲線、`dynamics`。
- 同一條指令重跑能得到同 seed 的相同初始 loss（bitwise 不要求跨裝置）。
- 報告在 `data/intelligence_reports/`，不進版控；文件只引用可重跑的指令。

### B1 — 核心開始產生正確答案（不是表層）

- `census_reply_provenance.py --check`：**模型產生且正確的答案 > 0**（目前是 0）。
- 同一批凍結題上，`source=snn` 的覆蓋率（有回答的比例）與正確率分開報告；不得把棄權算成錯，
  也不得把表層答案算成核心。
- 這一條只要求「> 0 且可重跑」，不要求達到外部及格線；達到與否如實印出。

### B2 — 至少一個維度跨過外部及格線（能力，不是工程）

- 用 `INTELLIGENCE_PASS_CRITERIA.md` 的同一條線（facts 45 / math 61 / paraphrase 70 /
  dialogue 44 / boundary 53 / tools 54），且答案是**模型產生**。
- 未達就照實寫「beta 能力未達」，不把系統分（6.41）借來當核心分。

### B3 — 產品層面可交付

- 主流程 15/15（`verify_main_flow_e2e.py`）、全回歸 0 failed、門禁全綠。
- 延遲/記憶體在 §1.4 的上限內；當機/回滾路徑已測。
- 文件：README/評測/階梯同步；`RELEASE_CRITERIA` 的「CPU only」等過時敘述修正。
- 授權：散布的權重與資料可商用（或明確標非商業、不散布）。

**beta 不是**：不是 L2/L3 的宣稱、不是「會說人話」、不是把系統分當核心分。這三件事各自有
自己的量測與及格線，Beta 只保證「核心真的在線上、來源可追溯、數字可重跑」。

## 8. 風險與止損

| 風險                                   | 徵兆                                             | 止損 |
| -------------------------------------- | ------------------------------------------------ | ---- |
| 容量在幾百列就飽和                     | P1 的 512 就 `whole < 0.90`                      | 不加寬、不加 epoch；先改表徵（vocab/max_len/readout） |
| 非線性又被關掉                         | `near_threshold < 0.01` 或 `sensitive < 0.05`     | 停止該 run，檢查 guards 是否真的傳進去 |
| val CE 贏不了 bigram floor             | P2 門檻失敗                                       | 視為表徵/目標問題，不加訓練量 |
| 過擬合後 exact 反而下降                | train TF ↑、val exact ↓                          | 以 val 選 checkpoint；不要用 train loss 選 |
| VRAM/RAM 超限                          | RSS > 60%、GPU > 60%                             | 降 batch/寬度；`gpu_limit.py`；一次只跑一個 |
| 表層污染核心分                         | census 出現 template/lookup 被記成 snn           | 立即修 `is_core_backend`/provenance，分數作廢重跑 |
| 蒸餾被誤讀成有效                       | 只報 KD loss 下降                                | 回到 §11.7：未建立品質增益；要重啟先寫受檢定力登記 |
| 對外散布非商用資料/權重                | ESC-50 權重或資料進 release                      | 先換資料或只散布程式碼（§5 #17） |

## 9. 重跑指令（唯一入口）

```bash
# 包絡（不訓練）
./.venv/bin/python scripts/probe_content_capacity.py --inventory \
    --report data/capacity/inventory.json

# 容量曲線（本次 P1；先讀 §A 的判準；CPU 是為了守住 RAM 上限，見 §A.2）
OMP_NUM_THREADS=4 ./.venv/bin/python scripts/probe_content_capacity.py \
    --sizes 128,512,2048 --configs small,medium --epochs 8 --min-steps 800 \
    --device cpu --report data/capacity/report.json

# 報告算術檢查（不需要重訓）
./.venv/bin/python scripts/probe_content_capacity.py --check data/capacity/report.json

# 訓練準備度（108M 的 2 FAIL 是已知的；新 checkpoint 用 --checkpoint 指定）
./.venv/bin/python scripts/probe_training_readiness.py --skip-teacher

# 硬體包絡（RSS/VRAM；每個 config 一個子行程）
./.venv/bin/python scripts/probe_scale_envelope.py --report data/capacity/envelope.json

# 正式訓練（乾淨基底；guards 必須顯式傳）
./.venv/bin/python scripts/train_token_snn.py \
    --vocab token --max-len 192 --max-vocab 12000 \
    --epochs 2 --batch 32 --lr 3e-3 --seed 0 \
    --theta-max 1.0 --leak-floor 0.85 --gain-cap 1.0 \
    --out data/checkpoints/p2_base.pt --report data/intelligence_reports/p2_base.json
```

## A. 跑前登記（P1 容量曲線；寫在任何 P1 分數之前）

- **儀器**：`scripts/probe_content_capacity.py`（本次新增；契約測試
  `tests/test_probe_content_capacity.py`）。它只讀 `core_train.jsonl` / `core_val.jsonl`，
  不碰凍結 benchmark，不寫 `apps/backend/data/models`。
- **資料切片**：`fits(max_len=192)` 後的 138,671 列；以 prompt+answer 的 blake2b 內容雜湊排序，
  N=128/512/2048 **巢狀**（小的樣本是大的子集），避免「前三列都是同一模板」。
- **詞表**：全語料建一次，`min_count=1`、`max_vocab=12000` → 12,005 atoms；所有臂共用，
  不因 N 或寬度改變 id。
- **寬度**：`small = d_emb 96 / d_hidden 192`（3,525,319 params）、
  `medium = 256 / 1024`（16,692,199 params）。兩者都 1 層、`readout=membrane`、`timesteps=1`。
- **預算**：每列 **8 epochs 或至少 800 個 update steps（取較大者）**、batch 32、lr 3e-3 cosine、
  seed 0、guards `theta_max=1.0 / leak_floor=0.85 / gain_cap=1.0`。每個 N 拿到至少相同的
  「每列曝光」與相同的最低優化步數；不是相同的總步數。
- **指標**：train teacher-forced **整題**正確率（主要）、token TF、greedy exact（≤32 列）、
  val whole（≤128 列，描述用）。
- **判準**：整題 TF ≥ **0.90** 算存住；容量＝連續通過前綴的最大 N；非單調照實標記；
  128 失敗 → `not-even-128`；2048 全過 → `at-least-2048`。
- **預測（寫在跑之前；錯了照實記）**：
  - small：128 應該過；512 可能在 0.9 附近；2048 預期不過。
  - medium：128、512 應該過；2048 不確定（這是「容量是否隨寬度成長」的主要觀察點）。
  - val whole 會明顯低於 train whole（儲存 ≠ 轉移）。
- **不會做的事**：不調門檻、不在看過結果後改 N 或 epochs、不把 train 數字當能力、不把 val 數字
  當 benchmark 分數。

### A.1 跑前修正（第一次啟動之後、任何容量裁決之前）

第一次啟動照原文跑了 `small / N=128 / 8 epochs`。batch 32、128 列 = 每 epoch **4 步**，
所以「8 epochs」只有 **32 個 update steps**；該臂跑完是 `train whole=0.000`、`tf=0.090`、
`loss=4.9761`，第二臂啟動後手動停止。**判讀：32 步量的是優化器，不是儲存量。**
這個 0.000 不是「128 列存不住」的證據，也不能拿去和 800 步的臂比較。

因此：

- 第一次啟動**作廢（void）**：沒有產出 `data/capacity/report.json`、沒有容量裁決、本文件不引用
  那個 0.000；`data/capacity/report.json` 之後只會來自修正後的完整重跑。
- 修正只有一項：每個臂至少 **800 個 update steps**（`--min-steps 800`，
  `effective_epochs = max(8, ceil(800 / ceil(N/32)))`）。N、寬度、巢狀取樣、seed、guards、
  指標與 **0.90 判準全部不變**。
- 這是**儀器修正**，不是看結果調門檻：第一次啟動沒有留下任何容量結論，0.90 與「連續通過前綴」
  的規則仍與 §A 原文逐字相同。
- 作廢的執行記錄：`small N=128` 一次，10 秒，未寫 checkpoint、未寫報告以外的檔案。

### A.2 裝置修正（第二次啟動之後、同樣沒有任何容量裁決）

第二次啟動改用 XPU（`--device auto` → `xpu`）並以 `gpu_limit.py --target 0.5` 壓住 GPU 職責。
第一個臂還沒跑完，整機 `free -m` 的 used 已到 **10,014 / 15,774 MB（63.5%）**，超過硬性上限
RAM ≤ 60%；本行程 RSS 為 4.0 GB（其餘 6.0 GB 是使用者既有程式）。**依規則停止**，不採用任何
該次啟動的數字（同樣沒有 report、沒有裁決）。

修正：容量曲線改用 **CPU**（`--device cpu`），`OMP_NUM_THREADS=4`（≤ 33% 的 12 核），
不啟用 XPU。裝置不是容量定義的一部分；這個修正只影響速度與 RAM，**不改 N、寬度、步數、
指標或 0.90 判準**。XPU 的用途仍以正式訓練（P2/P4）為主，屆時同樣受 60% 上限約束。
- **登記時間**：2026-11-19，於任何 P1 計分之前。

## B. P1 結果（跑後追加；本節不回寫 §A）

> 狀態：**待跑**（§A.1 的第一次啟動已作廢，不採用其任何數字）。跑完後在此貼上
> `data/capacity/report.json` 的摘要（容量、每臂 train/val、秒數、RSS），並照 §A 的判準逐條套；
> 若與預測不符，照實寫「預測錯了，錯在哪」。在此之前，任何「模型能裝多少」的說法都只是推測，
> 不得引用。
