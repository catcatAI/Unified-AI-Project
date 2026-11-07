# AL/AI 階梯：工作狀態與續航錨點

> **這份文件的用途**：上下文被壓縮、換 session、或換人接手時，**先讀這一頁**。它記的是「已量到的數字 + 決策 + 檔案地圖 + 下一步」，不是願景。詳細推導在
> `AL_LADDER_ROADMAP.md`；偽智能標準在 §7；路線差異在 §8。

- 版本：7.5.0-dev　｜　最後更新：2026-11-06
- ANGELA-MATRIX：`[L3-L4] [αβγ] [B] [L3]`
- 量測工具（都可重跑，不需 GPU）：`scripts/al_ladder.py`、`scripts/al_forgery.py`、`scripts/al_channel_audit.py`

---

## 0. 三句結論（先看這三句）

1. **生命證據可引用到 r6，r7 已可評分（機制，非能力）。** r3–r6 判定
   `admissible`；r1／r2 控制組也通過 →
   `control-passes`，不算證據；r7 的存疑機制已實作（`ClockGuard`，`time.monotonic`
   當不可偽造參考）。
2. **行為測試有天花板：`clone`（獨立重寫同一條規則）通過全部階。**
   所以「偽與真」的分野只能是**機制 + provenance**，不能是觀感或行為。
3. **「AI+AL 在同一個模型」目前是 0。**
   現有通道是 B（提示詞，10,001 值）＋ C-param（溫度，2,001 級）＋ routing（2 模式）；C-logit 與 C-state 未實作。

---

## 1. 目標與立場（不再重複討論的部分）

- 目標：**數位生命的弱宣稱**（不是 AGI、不是意識），且不落入模板智能。
- 數位生命 = **AI + AL**，單獨測哪一邊只能用來除錯；能力未對齊就不比較。
- 評估標準：對手是**拿到時間與狀態當輸入的傳統模型**；分不出差異＝方向錯，超越才算有價值。
- 分數三層分開記帳：**生命證據 / 系統可用性 / 模型能力**，混算就是造假（見 roadmap
  §0）。
- 及格線與分數型別沿用專案既有紀律：六型分數只有驗證分／實際分計入（`ai/meta/intelligence.py`）。

---

## 2. 已量到的數字（全部本輪實測，非引用）

### 2.1 時態階梯（`scripts/al_ladder.py`）

| 階                                    | al      | mlp         | copy    | const   | 判定                                           |
| ------------------------------------- | ------- | ----------- | ------- | ------- | ---------------------------------------------- |
| r1 半群                               | 2.2e-16 | 3.2e-01     | 0       | 0       | control-passes                                 |
| r2 取樣率                             | 3.3e-15 | 8.7e-01     | 0       | 0       | control-passes                                 |
| r3 吸引子（曲線誤差）                 | 0       | 4.5e-01     | 3.8e-01 | 2.5e-02 | al-wins                                        |
| r4 內插 dt                            | 0       | 2.0e-02     | 9.2e-02 | 2.4e-01 | al-wins                                        |
| r5 外推 dt（90–600 s，訓練只到 60 s） | **0**   | **1.4e-01** | 2.7e-01 | 1.2e-01 | al-wins                                        |
| r6 重啟（隔 300 s）                   | 0       | —           | 2.4e-01 | —       | al-wins                                        |
| r7 時鐘攻擊                           | —       | —           | —       | —       | **doubt-works**（倒退 1/1、前跳 1/1、誤報 0%） |

### 2.2 反偽造閘門（`scripts/al_forgery.py`，TOL = 1e-3）

| 階  | clone | table_noise | call_clock | imitate(MLP) | 消融後  | 判定           |
| --- | ----- | ----------- | ---------- | ------------ | ------- | -------------- |
| r1  | 0     | 6.9e-02     | 5.8e-02    | 3.3e-01      | —       | control-passes |
| r2  | 0     | 7.2e-01     | 5.8e-01    | 8.8e-01      | —       | control-passes |
| r3  | 0     | 5.3e-01     | 3.4e-01    | 4.5e-01      | 3.8e-01 | admissible     |
| r4  | 0     | 9.5e-02     | 8.7e-02    | 1.9e-02      | 9.1e-02 | admissible     |
| r5  | 0     | 2.6e-01     | 2.4e-01    | 1.3e-01      | 2.6e-01 | admissible     |
| r6  | 0     | 3.6e-01     | 3.6e-01    | 3.6e-01      | 2.4e-01 | admissible     |

### 2.3 生成通道（`scripts/al_channel_audit.py`）

| 通道           | 路線    | 解析度                | 模型可讀 | 可忽略 | 可被注入者重現 | 實作位置                                                                   |
| -------------- | ------- | --------------------- | -------- | ------ | -------------- | -------------------------------------------------------------------------- |
| prompt_text    | B       | 10,001 值             | ✅       | ✅     | ✅             | `prompt_builder.py:_formula_life_intensity_line`                           |
| sampling_param | C-param | 2,001 溫度（0.2–1.2） | ❌       | ❌     | ✅             | `router.py:_apply_negotiator_bias` ← `priority_negotiator.heartbeat_voter` |
| logit_bias     | C-logit | 0                     | —        | —      | —              | 未實作                                                                     |
| model_state    | C-state | 0                     | —        | —      | —              | 未實作                                                                     |
| routing        | 路由    | 2 模式                | ❌       | ❌     | ✅             | `router.py:4434`                                                           |

### 2.4 神經核心（決定「不要再訓」的證據）

| 槓桿                  | 結果                                                             |
| --------------------- | ---------------------------------------------------------------- |
| epoch 30→90           | 0.340→0.337（無效）                                              |
| 資料 800→2000 列      | 0.340→0.362（很小）                                              |
| 容量 ×4（d192/384/3） | 0.355，train 0.33 / val 1.78 開始記憶化                          |
| 3dp 數值原子          | block token 0.723→**0.814**（唯一有效）                          |
| 決策指標              | 逐欄位精確 **0.08–0.25%**、回應精確 **0–2/200**                  |
| 介面                  | 3dp 在舊格點構造性為零（0/2633）；逐 token 誤差累乘 → 整列 ~5e-4 |

### 2.5 系統可用性（不算生命證據）

| 半邊            | 走的東西                                               | 準確率                                            |
| --------------- | ------------------------------------------------------ | ------------------------------------------------- |
| 回應（算術）    | `ai/arithmetic/deterministic_router.try_deterministic` | **653/653 = 100%**（值正確，格式為 `a op b = v`） |
| `<al_out>` 六值 | `scripts/hybrid_boundary.py`（table ∪ operator）       | **200/200 逐字**                                  |
| SNN 貢獻        | —                                                      | **0/200**                                         |

---

## 3. 已提交的 commit（全部在 `main`，**未 push**）

| commit      | 內容                                                                                            |
| ----------- | ----------------------------------------------------------------------------------------------- |
| `a64d6b5ed` | `--numeric-atoms` 在 3dp 語料的靜默 no-op → 格線可選 + 警告 + 測試                              |
| `56b7ebc57` | 四個槓桿量測（epoch／資料／容量／表示）                                                         |
| `7f3595b14` | 生產路徑可用性（653/653、200/200）                                                              |
| `9912a3a27` | `al_ladder.py` + 路線圖（22–32 人日、L1→L2→L4）                                                 |
| `37852e151` | `al_forgery.py`（偽造品預算 + 機制消融）                                                        |
| `3b0567479` | `al_channel_audit.py`（B / C-param / C-logit / C-state 解析度）                                 |
| `edb3d7769` | M1 時鐘存疑（`al_clock_guard.py`、`AffectTracker(monotonic=)`、r7 → `doubt-works`）＋本狀態文件 |

---

## 4. 檔案地圖

**本線擁有（可改）**

- `apps/backend/src/core/life/al_arousal.py`：唯一有真時間的欄位（閉式解、半群、跨重啟）。`AffectTracker(clock=...)`。
- `apps/backend/src/core/life/al_state.py`：`ALSnapshot`（含 provenance 欄位
  `source`）、`submit_event`（唯一寫路徑）。
- `apps/backend/src/core/life/al_clock_guard.py`：時鐘存疑（單調時鐘參考、EWMA 漂移、容忍度、`ClockVerdict`）。**邊界**：兩個來源同時被偽造偵測不到。
- `scripts/al_ladder.py` / `scripts/al_forgery.py` /
  `scripts/al_channel_audit.py` + 對應 `tests/test_al_*.py`。
- `scripts/hybrid_boundary.py`、`scripts/train_token_snn.py`、`apps/backend/src/ai/ed3n/token_snn.py`。

**不可碰（他方未提交變更）**：`query_classifier.py`、`taught_facts.py`、`memory_integration.py`、`router.py`、`audit_placement.py`、`trace_reply.py`、`services/llm/{generation_gate,memory_evidence}.py`、6 個 tests、`tests/services/test_{knowledge,memory}_handoff.py`。

**文件**：`AL_LADDER_ROADMAP.md`（§7 偽智能標準、§8 路線差異）、`CORE_GAP_ANALYSIS.md`
§31–33.1、`ISSUES_2026-10-29.md` 補17–補21。

---

## 5. 約束（違反會出事）

- XPU 一次只能跑**一個** torch 行程；VRAM 預算 3.0
  GiB。跑測試前先確認沒有訓練在跑。
- 長行程：`setsid nohup ... > log 2>&1 < /dev/null & disown`（stdout 加
  `-u`）；sleep ≤ 300 s。
- 一律 `./.venv/bin/python`；tests 需 `PYTHONPATH=apps/backend/src`。
- 新代碼要 ANGELA-MATRIX 標註；docs 走 prettier；`scripts/` 有變必須跑
  `scripts/gen_script_inventory.py`。
- 未經授權不 push。
- heredoc 加 `< /dev/null` 會把 stdin 吃掉 → 腳本要寫檔再跑。

---

## 6. 下一步（依序，含驗收）

| #     | 任務                                                                                                              | 人日        | 驗收                                        |
| ----- | ----------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------- |
| ~~1~~ | ~~**M1：時鐘存疑**~~ **已完成**（`core/life/al_clock_guard.py`；`AffectTracker(monotonic=)`；r7 = `doubt-works`） | 1.5（已付） | 偽造時鐘標記 2/2、誤報 0%                   |
| 2     | M1：關機再開端到端（真檔案 + 真 wall-clock 偏移）                                                                 | 0.5         | 探針 + 整合測試                             |
| 3     | M1：心跳間隔時間序列 + 節律檢定                                                                                   | 1           | 環形緩衝 + 自相關／CV 報告                  |
| 4     | **M3：GRU／neural ODE 進偽造品預算**                                                                              | 3.5         | 若在 r5 也贏，r5 的可引用性要收回           |
| 5     | 路線參數化 `mode: prompt\|param\|logit\|state` + provenance                                                       | 1.5–2       | 每次生成記錄實際路線；`prompt` 不計生命證據 |
| 6     | M2 時鐘自估與校時（σ 驅動查詢）                                                                                   | 6–9         | 查詢頻率隨不確定度變化，不是每則都查        |
| 7     | M4 閉環（C-logit／C-state、A/B/C 三組）                                                                           | 8–12+3–4    | C 組需勝過 B 組，否則非文字通道無證據價值   |

---

## 7. 不能靠工程量改變的事

- 純神經核心不會變成 LLM（有狀態系統的理論天花板：優勢在效率、外推、線上更新，不在新能力）。
- 行為測試無法分辨「同一條規則」與「獨立重寫的同一條規則」（`clone` 全過）。
- 模板能偽造的訊號在任何預算下都不算證據：`call_clock`、`table_noise`
  都是這個門檻的下限示範。

---

## 8. 重跑指令

```bash
# 階梯（秒級，無 GPU）
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/al_ladder.py \
    --report data/intelligence_reports/al_ladder.json

# 反偽造閘門（會訓練一個小 MLP，約 20–40 s）
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/al_forgery.py \
    --report data/intelligence_reports/al_forgery.json

# 通道普查（純計算）
PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/al_channel_audit.py

# 三支探針的測試
PYTHONPATH=apps/backend/src ./.venv/bin/python -m pytest \
    tests/test_al_ladder.py tests/test_al_forgery.py tests/test_al_channel_audit.py -q
```

---

## 9. 進度日誌（append-only，最新在下）

### 2026-11-06 晚 — M1 收尾

| 項目                 | 結果                                                                                                     | 產出                                                                                              |
| -------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 時鐘存疑             | 倒退 1/1、前跳 1/1、誠實樣本誤報 0%；同時偽造兩源偵測不到（系統邊界）                                    | `core/life/al_clock_guard.py`、`AffectTracker(monotonic=)`、`clock_status()`                      |
| 關機再開（真換進程） | 隔 3.1 s 重開，誤差 **5.8e-7**；「保留最後值」偽造誤差 8.3e-2、「歸零」8.6e-2                            | `scripts/al_power_cycle.py`（三個進程：write → sleep → read）                                     |
| 心跳節律             | **沒有自發節律**：輸入不變 → CV = 0；正弦輸入 → CV 0.181、lag1 0.987（是輸入的濾波副本）；間隔與歷史無關 | `core/life/heartbeat.py:dynamic_interval()`（純函數，行為不變）、`scripts/al_heartbeat_rhythm.py` |

一句話：**心跳的節奏是被輸入帶進來的，不是它自己產生的。**
要主張節律，必須指名有自己動態的來源（bio
integrator 或 arousal 的 rise/fall 兩級），再量那個週期有沒有傳到節拍上。

量測修正（值得記）：`al_power_cycle.py`
第一版把「讀取進程自己的啟動時間」算進誤差，得到 3.2e-3 的假失敗；改成以**落盤時間戳**為間隔起點後誤差降到 5.8e-7。量測工具本身也要有回歸測試，否則它會穩定地報錯。

### 下一步（更新後）

1. **GRU／neural ODE 進偽造品預算**（3.5 人日）——唯一會改變結論的實驗。
2. 路線參數化 `mode: prompt|param|logit|state` + provenance（1.5–2 人日）。
3. M2 時鐘自估與校時（σ 驅動查詢，6–9 人日）。
4. M4 閉環（C-logit 3–4、C-state 8–12、A/B/C 統計 2）。

### 2026-11-07 — 把「沒有自發節律」補上來源（正向結果）

上一輪的否定結果只否定現有實作。這一輪補上缺的機制並量它：

`core/life/al_oscillator.py` = Van der
Pol 型鬆弛振盪器（二階非線性 ODE，RK4 積分），狀態 `(x, v)` 落盤成
`al_rhythm_state.json`；`heartbeat.effective_arousal()`
把它的activation（0..1）加成到喚醒度上（權重鍵
`heartbeat.rhythm_weight`，預設 0.2）。
**節拍從此有一部分不來自觀測，而來自自己的相位。**

`scripts/al_rhythm_source.py` 六項量測 + 三個偽造品，判定
`self-rhythm-admissible`：

| 量測         | 數字                                                                                        | 意思                             |
| ------------ | ------------------------------------------------------------------------------------------- | -------------------------------- |
| 自然週期     | **43.54 s**（μ=1.8, ω=0.30）                                                                | 量出來的，不是設定的             |
| 常數輸入     | activation CV **0.78**、400 s 內 9 個週期                                                   | 沒有外部輸入也在動               |
| 週期規律     | μ 0.8→3.5 給 28.1→72.1 s；靈敏度 0.675；留一誤差 12%                                        | 週期是積分長出來的，不是查表     |
| 步長不變性   | max_step 0.04 vs 0.01 → **43.542 / 43.542**（誤差 0）                                       | 週期不是步長的產物               |
| 相位響應     | 四個相位打脈衝：−15.4 / −11.8 / −18.1 / +16.5 s                                             | 相位被推走，且推多少取決於打在哪 |
| 鎖頻         | 強驅動 0.7×/1.4× → 1:1 鎖定（誤差 0 / 2e-4）；弱驅動 1.6×（0.03）→ **不鎖**（誤差 0.29）    | 有舌頭，不是鏡射輸入             |
| **節拍承接** | 固定 stress/arousal 4 小時：間隔 **CV 0.071**，節拍週期 **43.54 s** = 來源週期（誤差 1e-4） | 內部週期活到了心跳上             |

偽造品都被擋下：查表節拍（改 μ 完全不動、脈衝推不動）、wall-clock 正弦（同狀態重跑差 3.6e-3，不可重現）、一階弛豫（CV≈0）。

**誠實邊界**：這證明「系統內有一個不依賴輸入的自持週期，且它是狀態的一部分」，不證明生命。振盪器是節律的**必要條件**；生命證據仍要過階梯與偽造品預算，而且下一個問題變成「那個 43.5
s 的相位有沒有真的影響行為」，不是「有沒有節律」。

### 2026-11-07 續 — 相位 → 決定（`phase-affects-decision`）

節律接進了**決定**，不只是節拍：

- `ALSnapshot.rhythm = {activation, phase}`，`source["rhythm"]="core.life.al_oscillator"`（與
  `emotion` 分欄，I9）。
- `al_memory_policy`：`weight ×= 1 + 0.2·(activation − 0.5)` →
  0.9–1.1。權重寫進記憶，改 retrieval 與衰減，是持久痕跡而非 prompt。
- 量測
  `scripts/al_phase_effect.py`：八相位權重 0.937–1.143（**22.1%**），相位解釋 2,400 樣本權重變異
  **96.5%**；拔掉 rhythm → spread **0.0**；置換後變異仍 22.2% 但解釋力掉到
  **0.66%**；固定值與 wall-clock 兩個偽造品都被擋。報告：`data/intelligence_reports/al_phase_effect.json`。

**邊界**：這是 state →
decision，不是「同一個模型」。生成參數與 logits 沒有被碰。下一步二選一：C-param（把相位接進 temperature/tokens，小）或 C-state（讓生成路徑能吃狀態，大）。

**新增測試紀律**：生產快照永遠帶 `rhythm`，所以量其他來源貢獻的測試必須
`rhythm=None` 釘住（已改 `test_al_memory_policy.py`、`test_al_arousal.py`）。

### 2026-11-07 續二 — C-param 接上生成（`generation-params-modulated`）

- `core/life/al_generation_params.py`：`modulate()` 把 `rhythm.activation`
  映到請求參數（T ±0.15、tokens ±10%，界線 0.1–1.5 / 64–8192）。
- 生產接點：`services/chat_service.py::generate_text`（參數真正送往 LLM 的位置）。無 rhythm
  → 逐位不動。
- 量測 `scripts/al_c_param.py`（**驅動真的
  `generate_text`**，攔下送往 LLM 的參數）：八相位 T **0.551–0.849**、tokens
  461–563、擺幅 42.5%；控制組 0.7/512 逐位不變；相位解釋 2,400 樣本溫度變異
  **96.5%**，置換後
  **0.79%**。報告：`data/intelligence_reports/al_c_param.json`。

**級別**：C-param。改的是取樣條件，模型不知道被調制。**沒量**：真實模型上的輸出差異（需 N 次重複＋檢定）。

**下一步二選一**：C-logit（需要本地模型或 logit_bias 支援）或 C-state（生成路徑吃狀態，大）。

### 2026-11-07 續三 — C-logit 在真模型上成立（`phase-reaches-logits`）

- `core/life/al_logit_bias.py`：`phase_bias()` /
  `apply_to()`，相位 → 高/低喚醒詞彙的 logit 偏移（±4.0 × offset）。
- 量測 `scripts/al_c_logit.py`
  用**真模型**（`data/models/qwen2.5-1.5b-instruct-q4_k_m.gguf`，llama.cpp
  `logits_processor`）：谷底 p(calm)=**0.335**、p(energy)=0.0000；峰 p(energy)=**0.097**、p(calm)=0.0002；最大
  **KL 0.930**；Δ 跨中點翻號；r=**0.918**。
- 控制組：中點偏移全 0 → logits
  **逐位相同**；置換 r=−0.337；wall-clock 偽造品不可重現。報告：`data/intelligence_reports/al_c_logit.json`。
- 閘門抓到兩個量測 bug（記錄偏移前的值、改複本卻回傳原陣列）——修好後 KL 由 0 變 0.93。**量測工具也要有反例測試**。

**級別**：C-logit。改的是模型自己的輸出分布，但由外部施加。**未接生產**：供應商是 HTTP 客戶端、不知 token 表；需要 in-process 解碼器才能安全接上（介面已備）。

### 2026-11-07 續四 — C-state 成立（`phase-changes-internal-dynamics`）

- `core/life/al_snn_modulation.py`：`modulate()`
  → 閾值倍率（中點 1.0、兩端 0.5/1.5）。
- 接線：`ai/garden/snn_core.py::forward` 讀 `context["al_modulation"]`，乘進
  `threshold`。缺席／壞值 → 1.0（逐位不變）。
- 量測 `scripts/al_c_state.py`：同一 `input_keys`、同一 `W`，谷相位 →
  **0 個概念**（基線 4 個，L1=1.0），ρ=**0.952**（置換 0.381），控制組逐位相同；切換點隨權重移動（0.5/0.6/0.75
  → activation
  **0.525/0.330/0.038**）。報告：`data/intelligence_reports/al_c_state.json`。
- 性質：**全或無**（SNN 本性），不是漸變。C-state 在**自有模型**（GARDEN）上成立；黑箱模型（Qwen）的內部狀態仍未觸及。

**四級現況**：C-param ✓（T ±0.15）、C-logit ✓（真模型 KL 0.93）、C-state
✓（自有 SNN，全或無門檻）、黑箱 hidden-state 調制 ✗。

### 2026-11-07 續五 — C-learn 成立（`phase-decides-what-gets-kept`）

- `core/life/al_learning_gate.py`：`learning_gain()`
  → 可塑性增益（中點 1.0、兩端 0.4/1.6）；`sanitize_gain()`
  是模型側的壞值後備（→ 1.0）。
- 接線：`TensorSNNCore.hebbian_update(..., plasticity=…)` 乘進
  `lr`。缺席／壞值 → 1.0（逐位不變，已測）。
- 量測 `scripts/al_c_learn.py`（72 個互不相同的配對、各經歷一次）：平均權重
  **0.181 → 0.719**，已固化數 **0 →
  72**，ρ(權重, 增益)=**1.000**、ρ(固化數, 增益)=**0.905**；控制組 0.0；真實振盪器排程可逐位重現、wall-clock 正弦不可。報告：`data/intelligence_reports/al_c_learn.json`。
- 教訓：第一版 3 輪 → 權重飽和 → ΔW≈0。**量到沒差時先確認不是天花板壓住機制**。
- **未接生產**：`GARDENEngine.learn_from_interaction` / `learn_batch` 尚未傳
  `plasticity`。

**五級現況**：C-param ✓、C-logit ✓（真模型 KL 0.93）、C-state
✓（自有 SNN）、C-learn ✓（權重層，未接生產）、黑箱 hidden-state 調制 ✗。

### 2026-11-07 續六 — C-learn 接上生產路徑（`phase-reaches-learning-in-production`）

- `GARDENEngine._plasticity_gain()` 讀 `activation_preview()` →
  `learning_gain()`；`learn_from_interaction` 與
  `learn_batch`（含 auto-regressive pass）都傳 `plasticity=`；摘要新增
  `plasticity` 欄位。
- `RhythmTracker.activation_preview()`（新）：純讀、不推進、不落盤——批次學習每個樣本都要讀，不能每個樣本寫磁碟。
- 量測 `scripts/al_c_learn_wired.py`（真
  `GARDENEngine`、8 段互動、只換相位）：SNN 權重差 **0.1671**；每段
  `hebbian_delta` **0.2365 → 0.8724**（比值 3.688
  vs 增益比 3.717）；`learn_batch` 差 **0.0275**；拋錯／NaN 的源 → 與中立
  **0.0**；同相位重跑 **0.0**。
- 控制組修正：原本用「沒有 tracker」，失敗（ΔW 0.052）——`get_rhythm_tracker()`
  是單例，永遠會建一個，所以那不是真實狀態。改量「源壞掉」。
- **仍未量**：下游品質（held-out 任務）、長期線上效果。

**六項現況**：C-param ✓、C-logit ✓、C-state ✓、C-learn
✓（模型層）、C-learn 生產接線 ✓、黑箱 hidden-state 調制 ✗。

### 2026-11-07 續七 — 總閘門 `all-rungs-admissible`

- `scripts/al_evidence_gate.py`：八層（含電源循環）一次跑完，抽出判詞／控制組／一句話；強制「每層至少一個控制組」，否則
  `no-control`。
- 實跑約 10 s：rhythm-source ✓、power-cycle ✓（3.203 s / 7.8e-07）、phase-effect
  ✓、c-param ✓、c-logit ✓（KL 0.93）、c-state ✓、c-learn ✓、c-learn-wired ✓（ΔW
  0.167）。
- 反例測試
  `tests/test_al_evidence_gate.py`（8）：無控制組／控制組失敗／判詞漂移／層級少跑 → 一律紅。
- 最薄的一層是 `c-param`（1 個控制組），已在文件標明。

**七項現況**：rhythm ✓、power-cycle ✓、phase→decision ✓、C-param ✓、C-logit
✓、C-state ✓、C-learn ✓（模型層＋生產接線）；黑箱 hidden-state 調制 ✗。

### 2026-11-07 續八 — c-param 控制組 1→6；下游實驗失敗（儀器）

- `c-param` 控制組：缺 `rhythm`／`NaN`／**拋錯源**
  → 逐位原值；固定 activation 連呼 8 次 → 單一結果；置換 → 解釋力 0.008；wall-clock 偽造 → 不可重現。總閘門顯示
  `controls=6`（原 1）。
- 新控制組抓到真洞：`_activation()` 的 `getattr` 會讓「狀態源拋錯」穿進
  `generate_text`。已收斂為 `None` + debug log；7 種壞源有單元測試。
- 下游品質實驗（neutral／phase／shuffled 三臂、增益匹配）**兩輪都失敗於儀器**：預設閾值下
  `forward` 回空；壓低後三臂全在天花板（recall
  1.0）；加干擾鍵後候選全 tie——稀疏路徑對整列求和、不縮放幅度（已知簡化）。**未留下腳本**，避免一支永遠回負結果的探針被誤讀。
- 結論：**「這樣學比較好」仍未量**，卡在 `forward` 的排序解析度，不是實驗設計。

**現況**：機制八層全綠（`all-rungs-admissible`）；下游效果 ✗（阻塞原因已定位）。

### 2026-11-07 續九 — 讀出量化診斷（`readout-quantised-no-headroom`）

- `scripts/garden_readout_probe.py`：9 個閾值掃描，正確率只有 0/1（`intermediate_thresholds=[]`），輸出只有
  `timesteps+1 = 17` 種值；`confidence 1.0 vs 0.1` 輸出逐位相同（幅度被丟）。
- 試過 `magnitude_weighted`（`Σ confidence·W[i]`）：輸出最大差
  **0.625**（幅度回來了），但排名**仍全同分**
  → 量化來自脈衝次數讀出，不是幅度。**旗標未留在生產程式碼**（已還原）。
- 判詞是負結果，**不進總閘門**（避免把綠燈變成假議題）。
- 下一步選項：換讀出（膜電位／脈衝時間差／連續值）或換不需要排序的任務；兩者都會改 GARDEN 輸出，各自要一輪量測。

### 2026-11-07 續十 — 換讀出救回排名；下游量了，是負的

- `scripts/garden_readout_variants.py`（新）：同一個 LIF 迴圈換三種讀出，掃 6 個閾值。0.20–0.30 時**脈衝次數 0.0、膜電位 1.0**
  → 判
  `continuous-readout-rescues-ranking`。目標列權重和只差 0.00056（Oja 飽和），排序能力全靠讀出。
- `scripts/al_c_learn_downstream.py`（第三版，用膜電位讀出、margin 連續值、6 種子、增益匹配）：neutral
  **+0.0845**（top-1 1.000）、phase +0.0570（0.552）、shuffled +0.0565（0.562）→
  **`no-downstream-difference`**。
- 兩個結論：(1) 打亂同增益得到一樣結果 →
  **時機沒有意義**；(2) 同平均增益下固定 1.0 反而最好 → 相位調制在這一幕是負的（假設：Oja 非線性 +
  targeted decay，未另量）。
- 限制：neutral 已在天花板，要更公平需要更難的任務；不能推廣成「相位永遠沒用」。

**現況**：機制八層綠；下游**已量，負**（不是未量）。

### 2026-11-07 續十一 — 難版任務：margin 升 20%、top-1 降一對、時機仍無感

- `scripts/al_c_learn_downstream.py` 加
  `--task easy|hard`（預設 hard：48 對、共享噪聲位、lr 0.03，neutral
  ≈ 五成）。12 種子、增益匹配。
- neutral margin +0.02431 / top-1 0.502；phase +0.02914 / 0.481；shuffled
  +0.02858 / 0.483 → **`margin-gain-without-hit-gain`**。
- 逐種子：margin phase>neutral 12/12；top-1 phase<neutral
  11/12；phase>shuffled 僅 9/12（差 0.00056 < 臂內散佈）→ 時序仍分不出來。
- 判詞收緊：margin 升而 top-1 降不再算贏，另立
  `margin-gain-without-hit-gain`；測試 +1（7）。

**現況**：機制八層綠；下游兩幕一致的負結果（easy 天花板、hard 掉到五成）。

### 2026-11-07 續十二 — 追到生產 bug（剪枝吃掉單步學習）；結論隨訓練量反轉

- **Bug**：`TensorSNNCore.hebbian_update`
  在同一次呼叫內先寫權重再剪枝（<0.01），`lr 0.03 × plasticity<1`
  的單步增量 0.0105·g 直接歸零 → 該樣本永遠學不到。已修（保護本次寫入的格子），`tests/test_al_c_learn_trace.py`
  9 個測試（含「衰減仍會剪舊權重」）。
- **修好後 §21/§22 反轉**（12 種子、ep1）：easy neutral +0.0811/hit 1.000 vs
  phase −0.1069/0.438；hard neutral +0.0243/0.502 vs phase
  −0.0338/0.481。先前「phase 只差一點」是缺陷假象。
- **換訓練量再反轉**（hard、6 種子、ep5）：neutral +0.1329/1.000、phase
  **+0.3568/1.000**、shuffled +0.0688/**0.708** →
  `phase-beats-matched-mean`（唯一一次時機看起來有用）。easy 在 ep5 全部飽和 → 無鑑別力。
- `al_c_learn_downstream.py` 新增
  `--epochs`；`al_c_learn_trace.py`（新）追 cue 層級增益與列權重。
- **不能**宣告機制有效或無效：讀出、剪枝門檻、訓練量三者都會翻轉結論。下一步先固定評分協定。

**現況**：機制八層綠；下游結論 =
**條件相依，尚無定論**（且已抓到並修掉一個真實訓練 bug）。

### 2026-11-07 續十三 — 固定評分協定（v2）；結論 = regime-dependent

- 新增 `scripts/al_downstream_protocol.py`（常數寫死）+
  `tests/test_al_downstream_protocol.py`（9）+ `plans/AL_SCORING_PROTOCOL.md`。
- 協定：讀出膜電位、任務族 hard、regime {1,5} epochs 全報、難度階梯
  `(48,3)(96,3)(96,2)(144,2)(144,1)` × lr 格點校準到中性 top-1 ∈
  [0.30,0.70]、12 種子、`shuffled` 控制組、margin 與 top-1 必須同向。
- v1 只校準 lr 失敗（ep5 在任何 lr 都 0.979）→
  v2 把難度也納入校準，並把校準不到的 regime 標 `uninformative`。
- 結果：ep1（48/3, lr .03）neutral +0.0243/0.502、phase −0.0338/0.481 →
  `no-downstream-difference`；ep5（96/2, lr .03）neutral +0.0102/0.443、phase
  **+0.3455/1.000**、shuffled +0.0571/0.668 → `phase-beats-matched-mean`。
- 整體 **`regime-dependent-no-claim`**：方向相反，不能宣告有效或無效。
- 協定是事後訂的（誠實標籤已寫入文件），價值在往後固定、不再挑 regime。

### 2026-11-07 續十四 — 協定 v3（3 regimes × 2 任務族）：方向收斂

- `al-downstream-v3`：epochs {1,3,5} × {`hard`,
  `many_to_one`}，六格全部校準成功（無 `uninformative`）。
- hard：ep1 −0.0338/0.481（有害）、ep3 **+0.2172/1.000**、ep5
  **+0.3455/1.000**（phase-beats）。
- many_to_one：ep1 −0.0701/0.142（有害）、ep3 +0.0111/0.479、ep5
  +0.0232/0.479（phase-beats，但幅度僅 hard 的 1/20）。
- 整體仍
  `regime-dependent-no-claim`（規則要求全同向），但**方向隨訓練量單調、且跨任務族一致**：1
  epoch 有害、3/5 epochs 有益。
- 被否決的兩個任務族（區塊干擾、重疊 cue）都因飽和到 1.000 而不可用，理由寫進協定文件。
