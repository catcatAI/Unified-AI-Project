# AL/AI 階梯：工作狀態與續航錨點

> **這份文件的用途**：上下文被壓縮、換 session、或換人接手時，**先讀這一頁**。它記的是「已量到的數字 + 決策 + 檔案地圖 + 下一步」，不是願景。詳細推導在
> `AL_LADDER_ROADMAP.md`；偽智能標準在 §7；路線差異在 §8。

- 版本：7.5.0-dev　｜　最後更新：2026-11-12
- ANGELA-MATRIX：`[L3-L4] [αβγ] [B] [L3]`
- 量測工具（都可重跑，不需 GPU）：`scripts/al_ladder.py`、`scripts/al_forgery.py`、`scripts/al_channel_audit.py`
- **核心契約**（改 state／生成路徑前先讀）：`AI_AL_SINGLE_CORE_CONTRACT.md`

---

## 0. 三句結論（先看這三句）

1. **生命證據可引用到 r6，r7 已可評分（機制，非能力）。** r3–r6 判定
   `admissible`；r1／r2 控制組也通過 →
   `control-passes`，不算證據；r7 的存疑機制已實作（`ClockGuard`，`time.monotonic`
   當不可偽造參考）。
2. **行為測試有天花板：`clone`（獨立重寫同一條規則）通過全部階。**
   所以「偽與真」的分野只能是**機制 + provenance**，不能是觀感或行為。
3. **「AI+AL 在同一個模型」目前是 0。**
   現有通道是 B（提示詞，10,001 值）＋ C-param（溫度，2,001 級）＋ routing（2 模式）；
   C-logit 已實作但未接生產，C-state／C-learn 只在自有 GARDEN 上成立（參數級）。
   **C-state 的現有實作（`al_snn_modulation.py` 改 GARDEN 發火閾值）是 C-state-lite**：
   它調的是**參數**，跨回合不保存、重啟即消失，所以**不是**持久核心狀態。真正的核心狀態
   是「同一份權重＋同一個 state 物件＋`ai_step`／`al_step` 兩個入口」，定義與門檻見
   `AI_AL_SINGLE_CORE_CONTRACT.md`。狀態**不得**以文字／數字寫進 prompt 充當連續性。
4. **單一核心契約的機制已在合成任務上通過（2026-11-12，P1 第一臂）**：同一個 `GRUCell`
   兩個入口（`ai_step`／`al_step`）、同一個 state 物件；T1 歸零 `h` 後時間題掉回 chance
   （0.9998 → 0.5092）、不跑 `al_step` 與歸零逐位同分、hand-state 對照組在同一 T1 下
   不受影響（1.0000）。**這是機制證據，不是能力**：核心分仍 0.00/10，生產聊天路徑仍走
   prompt／`state_for_llm`；只有 GRU、合成任務、同進程 restart，半群未成立。預登記與
   限制見 `CORE_GAP_ANALYSIS.md` §37。

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

> 這張表是 **2026-11-06 的快照**：`logit_bias`／`model_state` 當時是 0。之後
> 2026-11-07 續四／續五 實作了 C-state（GARDEN 發火閾值）與 C-learn（可塑性增益），
> 但那兩者調的是**參數**、不跨回合保存，屬 **C-state-lite**，不是持久核心狀態；
> 核心狀態的定義見 `AI_AL_SINGLE_CORE_CONTRACT.md`。

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
- **仍未量**：下游品質（真正的 held-out 任務——v11 量到現有任務的 held-out 對所有臂都是亂猜，見續二十四）、長期線上效果。

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

### 2026-11-07 續十五 — 修評分 bug，many_to_one 結論翻轉

- 找到並修掉評分 bug（`al_c_learn_downstream._evaluate`）：對手集合由 pair 索引拼 label，多對一任務下半數 pair 直接判 miss、命中率截在 0.5。改由目標 label 集決定；`al_c_learn_trace._margins`
  改共用 `_score`。
- 對照驗證：`hard` 族 v4 數字與 v3 完全相同（一對一不受影響）；`many_to_one`
  中性臂 0.486 → 0.972。
- 協定 v4 重跑：hard ep1 有害、ep3 **+0.2172/1.000**、ep5
  **+0.3455/1.000**；many_to_one ep1 校準不到（`uninformative`），ep3
  −0.0865/0.194、ep5 −0.1177/0.266（phase **最差**）。
- 整體仍
  `regime-dependent-no-claim`，但結論改寫：**方向取決於干擾結構，不是訓練量**。
- 新增回歸測試 3 個（同 label 不當對手、缺失 label 不當對手、多對一可得分 1.0）。
- 已知未修：校準種子與評估種子重疊 3 個（v5 處理）。

### 2026-11-07 續十六 — 修學習相位預覽的「舊體質」bug，並劃清生產／實驗的界線

- 修 `RhythmTracker.activation_preview()`：原本直接回傳
  `_osc.activation`，那是**上次推進那一刻**的相位。背景學習若隔很久才跑（沒有對話推振盪器），學到的是舊體質而不是「這一刻」。現在在振盪器副本上前進到
  `now` 再丟掉，仍然不推進、不落盤；時鐘倒退不倒退振盪器，長缺席以
  `MAX_CATCHUP_S` 封頂。
- 新增 `tests/core/test_al_rhythm_preview.py`（5 個）：與時鐘同步、與
  `activation()` 結果一致、不動狀態且不落盤、長缺席封頂、時鐘倒退不動狀態。
- 劃清界線（重要）：生產只在 `_batch_train_associations`
  **每批讀一次**增益，同批樣本共用；實驗操弄的是**逐樣本相位進展**。這兩個不是同一個變數——`hard`
  族的 +0.34 margin 不能算成生產環境的行為。`garden_engine._plasticity_gain`
  的 docstring 已改成這樣寫（原本寫「每個樣本都要問一次」，與呼叫點不符）。
- AL 相關 6 檔測試 65 passed；flake8 = 0。

### 2026-11-07 續十七 — 判詞補上「明顯更差」，負結果不再被記成空白

- 問題：`_verdict` 只有「贏／沒差」，`many_to_one` ep3/ep5 的 phase（margin
  −0.0865、−0.1177；top-1 0.194、0.266）被寫成
  `no-downstream-difference`，等於把可信的負結果抹掉。
- 修法：新增
  `phase-loses-to-matched-mean`（與「贏」對稱：兩項都差、贏 shuffled 的差距為負且超過種子散佈、多數種子同時輸兩臂）；整體多一個
  `mechanism-harm-consistent`；`NO_BENEFIT` 納入新判詞。
- 重跑（資料同 v4，只有標記改變）：hard ep1 沒差、ep3/ep5 贏；many_to_one
  ep3/ep5 **`phase-loses-to-matched-mean`**；整體仍
  `regime-dependent-no-claim`——但現在是「一邊受益、另一邊受害」的雙向結論。
- 新增測試 4 個（明顯虧損要叫虧損、小虧損仍算沒結果、一致的負結果是結論、混合時歸 no-benefit）。

### 2026-11-07 續十八 — 協定 v5：校準種子互斥

- 修掉 v4 留下的已知缺陷：校準種子 (11,23,37) 原本也在 12 個評估種子裡。改成 (211,223,241)，模組層加斷言（重疊即匯入失敗），測試釘住不變量。
- 重跑 v5：**判詞一格都沒變**，`hard` 三格的評估數字逐位相同（同一個 lr
  0.03）。變的是校準點（hard ep5
  0.465→0.497，洩漏版把中性臂估得偏難）與一格的可判讀性——`many_to_one` ep1 從
  `uninformative` 變成 lr 0.015／校準 0.306 的可判讀格。
- 六格五格可判讀：hard ep1 沒差、ep3/ep5 贏；many_to_one
  ep1 沒差、ep3/ep5 受害。整體 `regime-dependent-no-claim`。
- 這輪的教訓：`uninformative`
  未必是任務沒有中段，也可能是校準取樣太少或取樣被污染。先修儀器，再解釋任務。

### 2026-11-07 續十九 — 協定 v6：固定調制頻率，v5 的「受益」消失

- 缺陷：`_schedule` 讓整段訓練走完一個週期，`epochs`
  同時放大訓練量並拉長週期（ep5 的相位速度是 ep1 的 1/5）。「訓練夠了」與「振盪慢到像學習率排程」兩種解釋分不開。
- 修法：`_schedule(period, n, step_per_period=pairs)`，每個 epoch 一個週期；`al_c_learn_downstream.run`
  與協定 `evaluate_cell` 同步。
- 重跑 v6：hard ep3 由 `+0.2172/1.000` 變成 `−0.0125/0.516`（沒差）；ep5 由
  `+0.3455/1.000` 變成 `+0.0637/0.699`，**shuffled 反而更高（+0.0700/0.714）**→
  `timing-does-not-matter-only-gain`。many_to_one 三格全部
  `no-downstream-difference`。
- 整體判詞由 `regime-dependent-no-claim` 變成
  **`no-mechanism-benefit-consistent`**；v5 的「hard 後期受益」正式撤回，原因寫進協定文件（那個效果是慢週期＝前重後輕的學習率排程，不是時序）。
- 仍站得住的部分：ep5 的 phase 與 shuffled 都贏 neutral（0.699/0.714 vs
  0.443）——**增益有起伏有用，順序沒用**。

### 2026-11-07 續二十 — 修掉診斷腳本裡一條永遠走不到的判詞

- 缺陷：`al_c_learn_trace.LOW_GAIN = 0.2`，但增益的實際範圍是 0.4–1.6（中性 1.0）。也就是
  `low-gain-samples-are-the-losers`
  這個判詞**在任何資料下都判不出來**，即使 22 個翻轉全部落在 0.40–0.97。
- 修法：門檻改成 0.8（語義：明顯低於中性，落在擺幅下半段），並在報告裡加
  **基準率** `below_low_base_rate` 與
  `low_gain_threshold`，避免把「翻轉的多半低增益」跟「大部分樣本都低增益」混為一談。
- 修好後 hard/seed 11（ep1）：低增益基準率 0.479，翻轉列低增益比例
  **1.00**（22/22），`corr(gain, margin delta) = 0.9721`。判詞
  `low-gain-samples-are-the-losers`。
- 機制上說得通：一次性學習時，谷底寫入的樣本幾乎沒留下痕跡，卻仍要跟同一批共享噪聲位累積出來的對手競爭，所以 margin 由正翻負——這解釋了協定裡 ep1 的 phase 為何有害。
- 新增 2 個測試（門檻必須切開實際排程、報告必須暴露基準率）。

### 2026-11-07 續二十一 — 逐輪追蹤：谷底損失**沒有**被吸收（推翻自己的假設）

- 觸發：續二十說「一次性學習下谷底是淨損失」，自然假設多輪之後會被後面的峰值補回來。
- 先前障礙：`_train_logged` 把 epoch 數寫死成 `_downstream.EPOCHS`，且用 `zip`
  吃掉前 n 個增益——多輪時既不會換增益，長度不符還會靜默截斷。已改成 `epochs`
  參數＋逐 epoch 切片＋長度不符直接 `ValueError`。
- 加上逐 epoch 快照（每輪結束就評一次 margin）與 `--epochs`，hard / seed 11：

| epoch | 翻轉數 | 翻轉中低增益比例 | 基準率 | 累積增益相關性 | 判詞       |
| ----- | ------ | ---------------- | ------ | -------------- | ---------- |
| 1     | 22     | 0.95             | 0.48   | 0.972          | 谷底是輸家 |
| 2     | 30     | 0.63             | 0.48   | 0.954          | 谷底是輸家 |
| 3     | 23     | 0.74             | 0.48   | 0.946          | 谷底是輸家 |
| 4     | 22     | 0.59             | 0.48   | 0.902          | 谷底是輸家 |
| 5     | 18     | 0.44             | 0.48   | 0.856          | 不再是谷底 |

- 結論一（推翻假設）：**沒有吸收**。第 5 輪仍有 18/48 個 cue 由命中翻成不命中。
- 結論二（原因會換）：累積增益跟 margin 變化的相關性一整路都高（0.97→0.86），但「翻轉的是不是被餵得少的那批」到第 5 輪已經跟基準率無異（0.44
  vs
  0.48）。也就是說**早期**是谷底直接造成，**後期**是別的原因在決定誰掉隊，只是整體上餵得少的仍然吃虧。
- 修掉的量綱錯誤：第一版的「逐輪相關性」拿累積 margin 去對「當輪增益」，所以 ep4/ep5 掉到 0.2 是自變數選錯，不是發現。改成對累積增益後才是真數字；累積門檻也必須跟著放大（分界線＝中性總量 epochs×1.0），否則「低增益」在累積量上永遠不存在——同一個坑第二次。
- 附註：seed 11 的 ep5 phase margin 均值 +0.054、neutral
  +0.128，單一 seed 上 phase 仍較差；協定的 ep5「phase 贏」是 12 個種子的平均，兩者不衝突，但足以說明單 seed 追蹤只能談機制、不能談效果。
- 新增 4 個測試（長度不符要拋錯、每輪吃自己那批增益、報告要帶累積量、門檻可傳入）。

### 2026-11-07 續二十二 — `epochs` 軸的混淆，與「7/12 不算贏」

- 缺陷：難度階梯是**逐格**校準的。`hard` 的 ep1 落在 48
  pair／3 噪聲位，ep3/ep5 落在 96 pair／2 噪聲位；`many_to_one` 的 ep1 用
  `target_group`
  12，ep3/ep5 用 24。所以 v6 裡所有跨 epoch 的句子（不只「後期受益」）都同時混了訓練量、題目大小與干擾強度。
- 修法（v7）：每族只校準一次，候選組合必須讓 `EPOCHS_MATRIX`
  每個 regime 的中性臂都在 [0.30, 0.70]；跑出範圍就標
  `neutral-out-of-range`，不換題。
- 第一次跑 v7 時 `hard`
  整族不可判讀：同一題目的中性命中率隨 epoch 單調上升，而階梯 48/3 →
  96/2 太粗（前者 ep5 飽和 1.0，後者 ep1 只有 0.24）。補一級 72/2 後窗口出現（0.333
  / 0.384 / 0.63）。
- v7 隔離後 `hard` ep5 看似正結果（phase 0.701 vs shuffled 0.653 vs neutral
  0.573），但逐種子 phase>neutral 11/12、phase>shuffled **7/12**。
- 修法（v8）：方向性判詞要求在兩個比較上至少 10/12 個種子同向（單尾二項 p≈0.019；9/12 是 0.073）。此規則**只會撤掉判詞**，且是看到 v7 數字後才加的，文件裡照實標記。
- v8 結果：`hard` ep1/ep3 `no-downstream-difference`、ep5
  `timing-does-not-matter-only-gain`（被降級）；`many_to_one` ep1
  `neutral-out-of-range`（0.299，差 0.001）、ep3/ep5
  `no-downstream-difference`；整體 `no-mechanism-benefit-consistent`。
- 讀法：`hard` ep1 的 phase
  top-1 是 12/12 個種子贏 neutral、卻只有 1/12 贏 shuffled
  → 起伏有用、順序沒用；`many_to_one`
  上 phase 在兩個 regime 都更差（1–2/12），但未達穩健性門檻，所以記成「沒差別」而不是「有害」。
- 一併修掉兩個自己引入的錯：階梯順序沒遞增（`test_each_family_ladder_starts_easy`
  抓到）、`_sign_test_minimum` 從上界往下找所以回傳 12 而非 10（新測試抓到）。
- 新增 7 個測試（種子門檻、強證據存活、擲硬幣降級、弱傷害不叫傷害、校準不吃 epochs、階梯至少三級）。

### 2026-11-07 續二十三 — 校準貼邊、確認種子，與量具解析度

- v8 的 0.001 缺口不是難度問題，是準則形狀：合格區是區間，「第一個合格就採用」必然貼下界。實測
  `many_to_one` 0.306（餘裕 0.006）、`hard` 0.333（餘裕 0.033）。
- v9：優先選每個 regime 都離邊界 ≥0.05 的候選（`HIT_MARGIN`），找不到才退回第一個合格者並標
  `centred: False`；`many_to_one` 階梯補 72 pair／group 12 一級。
- v10：掃描只用 3 個種子會系統性偏樂觀（同題目 0.361
  vs 評估 0.306），加 8 個種子確認步驟。結果同一題目三組種子量到 0.306／0.406／0.299，差 0.107；確認步驟沒解決問題，反而讓校準提早接受貼邊那一級。
- 逐種子離散度寫進報告：中性臂 sd 0.08–0.12、se
  ≈0.03、個別種子 0.25–0.583。12 種子均值只能定位 ±0.03，而門檻要求 0.05 餘裕——0.299 與 0.30 本來就分不開。
- v10 結果：hard ep1 0.333（sd **0.000**）/0.500/0.499
  `no-downstream-difference`；ep3 0.330（sd 0.115）；ep5
  `timing-does-not-matter-only-gain`；m2o ep1
  `neutral-out-of-range`（0.299）、ep3/ep5 `no-downstream-difference`。整體
  `no-mechanism-benefit-consistent`。
- 唯一乾淨的格是 hard ep1：中性臂種子不變，phase 0.500、shuffled
  0.499。「起伏有用、順序沒用」靠的是它。
- 自我批評：一個 session 改三次儀器（餘裕、確認種子、離散度），每次都在看到數字後動；都只撤判詞、不造判詞，但節奏要停。下一步是事前決定的檢定力提升（種子 12→40、se→0.015），不是再調門檻。
- 另修：`nohup … &`
  在此環境會被工具清理殺掉，導致第一次 v10 根本沒跑（log 空檔）；改用受管背景進程並用
  `ps` 而非 `pgrep -f` 判斷存活（`pgrep -f` 會 match 到自己的 bash 命令列）。

### 2026-11-07 續二十四 — 根：訓練與評估是同一批 pair

- 往上追一層才看到地基：`_train` 用 `_pairs(task)`，`_evaluate` 也用
  `_pairs(task)`。報告裡的 `hit_rate` 一直是**訓練集**命中率。
- 實測（neutral，hard 48 pair）：訓練集 ep1 0.52 → ep3 0.96 → ep5
  1.00；同規則、沒訓練過的 cue（新增
  `_heldout_pairs`）在所有 epoch、所有種子都是 0.062 = 3/48 = 亂猜。
- 原因：這個 token 層模型沒有共用特徵，新 cue 的判別 token 從未出現過。它只會背，不會遷移。
- v11 把 held-out 寫進協定（`heldout_hit_rate_mean/sd`、`heldout_chance`、`heldout_at_chance`）：hard 三臂 held-out 全 0.028（亂猜 0.014）；m2o
  0.18–0.25（亂猜 0.083）高於亂猜，但那是共用噪聲 token `n0`–`n2`
  的偽遷移，且 phase 在該處是最差的臂（0.181–0.243）。
- 需要降級：§22–§33 與 `AL_SCORING_PROTOCOL`
  的所有「比較好／比較差」只成立於「記得比較快」。v3
  docstring 的「量的是 held-out 名次」是錯的，已改；§22「量 held-out 檢索」、§23「held-out
  margin」、§31「仍未量下游品質」三處一併更正。
- 根修方向：任務改成每個 target 有共用 feature
  token（訓練與 held-out 的 cue 都帶），才有真正的 held-out 與學習曲線；在那之前調門檻只是量背誦速度差。
- 檢查：協定單檔 30 passed、flake8=0。

### 2026-11-07 續二十五 — 真 held-out 與讀出壓平

- 新增任務族 `structured`：每個 target 一個 `feat{tXX}` token，訓練與 held-out
  cue 都帶；只差在未出現過的 `cueNN`。協定 `FAMILIES` 與 `TASKS` 都加了。
- 首次量到真遷移：neutral、48 pair、ep1 → 訓練集 top-1 1.000、held-out
  1.000（亂猜 0.083，12 個 target），margin +0.2389。
- 但 ep2 margin +0.4585、ep3 起 top-1 0.000 且 margin **恰 0.0000**（0.9545 vs
  0.9451、1.4354 vs 1.4354）——正確 label 與最強對手電位相等，各 target 被壓平。
- 因此 `structured` 在協定是
  `ladder-exhausted`：沒有 step／lr 能讓中性臂在 ep1/3/5 全在 [0.30,0.70]；最佳嘗試 192p/2b@0.02
  = `{ep1: 0.667, ep3: 0.056}`。
- 判讀：下游問題在任何訓練長度上都答不了——`hard`／`m2o` 是背誦速度，`structured`
  第一輪就遷移但第二輪就塌。卡的是讀出，不是判準、種子數或階梯。
- 下一個根問題：`TensorSNNCore.hebbian_update`
  重複訓練為何把各 target 膜電位壓成同值。修好之前 `epochs > 1`
  的格子都不能當學習曲線讀。
- v12 整體判詞仍
  `no-mechanism-benefit-consistent`（hard 與 m2o 的格未變）；協定單檔 33
  passed、flake8=0。

### 2026-11-07 續二十六 — 壓平在讀出端，換讀出後 phase 12/12 輸

- 追「ep3 起 margin 恰 0」：權重沒塌（ep5 `featt00→t00` 0.157 vs `shared→`
  各 target 0.13，結構還在）。塌的是 `potential`
  讀出——16 個時間步的膜電位累積 = 無向圖上的擴散，權重一強就填平整個連通分量。
- 同一批權重換成一步讀出 `direct`（`W·a`）：`structured`
  ep1/3/5 的 train 與 held-out 全部 1.000；`potential`
  在 ep3/5 是 0.000（ep3 正確 label 0.955
  vs 最強對手 0.945，排不進前三，`direct` 是 0.334 vs 0.201）。
- 實作：`garden_readout_variants._direct`；`al_c_learn_downstream.READOUT` 與
  `_evaluate(readout=)`；協定 `--readout {potential,direct}`，讀出參數串進
  `_measure`／`calibrate_family`／`evaluate_cell`。預設仍 `potential`
  以保留舊報告可重現。
- `--readout direct` 重新基線：`hard`／`structured` 皆
  `ladder-exhausted`（線性讀出下 cue 自身 token 有非零邊就贏，任何 lr 都 1.000）；`many_to_one`
  校準到 48p/3b/group 24/lr 0.005（neutral 0.408／0.535／0.528）。
- `many_to_one` ep1／ep3：**`phase-loses-to-matched-mean`，P>N 0/12、P>S
  0/12**（top-1 0.184 vs 0.408/0.274；0.399 vs
  0.535/0.464）——AL 線第一個種子穩健的負結果。ep5 phase 0.689、P>N 12/12 但 P>S
  5/12，降級為 `no-downstream-difference`。整體
  `no-mechanism-benefit-consistent`。
- 下一個根問題：任務只有「唯一 token」一種證據，所以只有 1.0/0 兩種值；要有多個衝突證據才有中段。`many_to_one`
  的中段是共用噪聲 token 撐出來的。
- 檢查：協定單檔 36 passed、flake8=0。

### 2026-11-07 續二十七 — 衝突證據：中段＋遷移，答案仍是沒有差別

- 新增 `conflict` 族：cue 沒有專屬 token，只由跨 target 共用的 feature 組成（8
  target、12 feature、每 cue 5
  token＝2 支持＋3 抽樣，每個 feature 至少對 2 個 target 有邊）。
- 校準 lr 0.01：中性臂 ep1/3/5 = 0.375／0.483／0.497，held-out（新組合）=
  0.347／0.486／0.500，亂猜 0.125 → 中段與遷移同時成立（第一次）。
- 結果（`--readout direct`）：conflict ep1 phase 0.431 vs 0.375/0.375（P>N
  8/12、P>S 8/12）、ep3 0.486 vs 0.483/0.469（4/12、2/12）、ep5 0.500 vs
  0.497/0.490（1/12、2/12）→ 三格皆 `no-downstream-difference`。
- `many_to_one` 仍 ep1/ep3
  `phase-loses-to-matched-mean`（0/12、0/12），ep5 降級；`hard`／`structured` 仍
  `ladder-exhausted`（唯一 token → 任何 lr 都 1.000）。
- 判讀：相位調制在「有學習、有遷移」的任務上沒有好處；在背誦型任務上早期有害。兩者分開陳述，整體
  `no-mechanism-benefit-consistent`。
- 量具現況：`direct` 讀出＋`conflict`
  任務＋held-out 同步＋種子穩健性／符號檢定，已是能分辨差別的儀器。
- 檢查：協定單檔 40 passed、flake8=0。

### 2026-11-07 續二十八 — 檢定力與配對差

- 新增 `paired`（同種子 `phase − neutral`／`phase − shuffled`
  的均值、sd、se、95% 半寬、勝場）與 `detectable_hit_delta`（MDE）。
- MDE 定義：符號門檻需 ≥`SIGN_TEST_MIN`
  個種子同向，單種子同向機率 Φ(δ/σ)，反解 power
  0.8 的最小 δ。實測 σ=0.10 時 n=12 需 δ≥0.112、n=40 需 0.052；σ=0.05 時 n=12 需 0.056。
- **結論之一：12 個種子偵測不到 <0.11 的差**，之前對 0.05 餘裕的爭論都在檢定力以下。
- v15 結果（direct 讀出）：conflict ep1 +0.0556（95% 半寬 0.043，CI
  [0.013,0.099] 不含 0）、margin −0.00136、MDE 0.085 → 協定仍判
  `no-downstream-difference`（兩指標未同向）；ep3/ep5 +0.0035。m2o ep1
  −0.2240、ep3 −0.1354（12/12 同向、遠超 MDE）`phase-loses-to-matched-mean`；ep5
  +0.1615 但 margin −0.0002 → 降級。
- 讀法：命中率上升而 margin 不動 = 平手被打破，不是表徵變好。相位調制沒有時序優勢。
- 檢查：協定單檔 44 passed、flake8=0。

### 2026-11-07 續二十九 — 量具控制：打亂標籤

- 新增
  `_label_shuffle_baseline`：同批輸入、target 迴圈位移一位再訓練（權重統計同真訓練），用真 pair 評估；寫進每次執行的
  `controls` 並印出。
- 實測（`--readout direct`，3 校準種子）：hard 0.000 / conflict 0.000 /
  structured 0.000 / m2o 0.000，亂猜分別 0.021 / 0.125 / 0.083 / 0.042 →
  **掉到亂猜以下**（固定雙射使模型把錯標籤學得更牢），是「學到特定對應」的簽名。
- 結論：conflict 的中段是學來的，不是輸入結構給的；前面跨臂比較量的確實是學習。
- 協定升
  `al-downstream-v16`；判詞與 v15 相同（`no-mechanism-benefit-consistent`）。
- 檢查：協定單檔 46 passed、flake8=0。

### 2026-11-07 續三十 — 加種子必須同時加門檻

- 修 bug：`_seed_robust` 原本用常數
  `SIGN_TEST_MIN`（10/12），加種子會讓判詞變鬆。改為由 `_sign_test_minimum(n)`
  導出；`run()` 拒絕校準種子混入評估；`_measure`／`evaluate_cell`／`run` 接受
  `seeds`，CLI 加 `--seeds`／`--families`。
- 40 種子重跑 `conflict`（門檻 26/40）：ep1 P−N +0.0396（sd 0.0864、CI ±0.0268 →
  [0.013, 0.066]）、**僅 22/40 同向**、MDE 0.045；ep3 +0.0052（8/40）；ep5
  +0.0042（**4/40**，CI 也不含 0）。三格皆 `no-downstream-difference`。
- 判讀：均值不含 0 但逐種子只有 55%（ep5 甚至 4/40）——多數種子略負、少數大幅正。12 種子時的 8/12（67%）低估散佈；「CI 不含 0」比「逐種子同向」容易被運氣滿足。
- **污染修正**：第一次擴充種子 `range(200,…)`
  撞上校準種子 211／223／241，舊守衛只查 `min(seeds)`
  未擋住；改集合交集＋擴充種子自 1000 起，重跑後數字取代第一次的 +0.0510／27-40。
- 檢查：協定單檔 49 passed、flake8=0、isort=0。

### 2026-11-07 續三十一 — 增益匹配閘門沒有力量

- 發現：`gain_matched` 用
  `abs(mean(phase)−1.0) <= 0.05`，但排程每 epoch 走完整週期，均值實測 1.0000369（差 3.7e-5）→ 該閘門**不可能失敗**。
- 改為
  `_gains_matched()`：驗同上同一組增益（multiset）、順序確實不同（否則 shuffled 是 phase 複本）、均值差 ≤
  `GAIN_MATCH_TOL`(0.01)；`gain_match` 寫入每格。
- 順帶暴露混淆：相位臂增益 0.4–1.6、sd 0.4762，`phase` vs `neutral`
  混了散佈與順序；只有 `phase` vs `shuffled` 隔離時序。
- 隔離後重讀（v17 `direct`）：conflict P>S 25/40、14/40、6/40（無時序效果）；m2o
  ep1 P>S **0/40**、ep3 0/12、ep5 5/12
  → 背誦型任務的傷害**不是散佈造成**，是順序。
- 判詞不變
  `no-mechanism-benefit-consistent`，理由更硬：與同散佈隨機順序相比，相位順序沒有好處、在背誦型任務上更差。
- 檢查：協定單檔 53 passed、flake8=0。

### 2026-11-07 續三十二 — 又兩個不會失敗的檢查

- **`_heldout_pairs` 洩漏斷言是空的**：比
  `id()`，兩邊永遠不同物件 → 不可能失敗；且 `conflict` 分支在斷言前就
  `return`。改比 cue 內容、兩支都接。實測五族 0 重疊（無洩漏，但現在有檢查）。
- **held-out 亂猜門檻 `2/len(targets)` 無來源**：改二項上界
  `p+2√(p(1−p)/m)`；conflict 0.250→0.193、m2o
  0.083→0.099。結論不變；新觀察：m2o 的 neutral 在亂猜（0.056），phase/shuffled 是 2.8×
  → 遷移來自變動增益。
- **margin 閘門擋掉 top-1 效果**：m2o ep5 margin 差 −0.0002、top-1
  +0.1615（12/12），舊判詞寫 `no-downstream-difference`。新增
  `hit-gain-without-margin-gain`（算機制沒好處）與
  `hit-gain-over-both-arms`（未定，不入 NO_BENEFIT）。
- 門檻改用 `_sign_test_minimum(n)`：8/12 是多數但 P=0.19；此舉讓 conflict
  ep1 維持 `no-downstream-difference`（否則整體會變
  `regime-dependent-no-claim`）。
- v18 重跑：`no-mechanism-benefit-consistent`；m2o ep1/ep3
  phase-loses（0/12 贏）、ep5 換標籤 → 相位調制在該族**有效果但不是時序**，符號隨訓練量翻轉。
- 檢查：協定+下游 80 passed、flake8=0。

### 2026-11-08 續三十三 — 門檻的尺度量出來，與兩個沒量到的族

- 動手前的假設：margin 閘門 `gain > pstdev(neutral)` 約等於十幾個配對 SE。
  **量完被推翻**：`yardstick/se` 只有 conflict 2.29/2.32/2.20、m2o
  2.00/3.34/2.08。線寬與 SE 同量級，雜訊越過線是現實可能，不是理論擔心。
- `evaluate_cell()` 新增
  `cell.margin_gate`（`yardstick`/`gain`/`paired_sd`/`paired_se`/
  `gain_over_se`/`yardstick_over_se`），判詞尺度可重算。
- 新增**只收緊**的證據下限
  `MIN_GAIN_OVER_SE = 2.0`（`_paired_se()`；無散佈/樣本不足不套用）。它只能把「有差」推向「沒差」，不可能生出新的正向判詞。
- v19 → v20 重跑：**六格判詞逐格相同**，整體仍
  `no-mechanism-benefit-consistent`。測試同時驗兩個方向：gain
  0.10 且配對差穩定 → 判贏；同樣 gain 但差值 ±0.20（SE≈0.09）→ 判
  `no-downstream-difference`（這格舊規則會判贏，下限唯一擋下的就是它）。
- 另一個負結果：15 格只有 6 格有 `cell`；`hard`（`DEFAULT_TASK`）與 `structured`
  三輪全是 `informative: False` / `ladder-exhausted` ——
  **沒量到**，不是「沒差」，不可計入多數。
- 檢查：下游 33 passed、協定 55 passed、flake8=0。

### 2026-11-08 續三十四 — `hard` 的中段是讀出的產物

- 追 9 格「沒有 cell」：不是階梯不夠長，是那幾族沒有中段。同一個 `hard`
  任務換讀出量 ep1： `direct` 在 48/144 對、lr 0.005/0.05
  **全部 1.000**；`potential` 是 0.042/1.000/0.000/1.000
  ——中段只存在於很窄的 lr 窗口。v7/v8 的 `hard` 中段（0.573/0.701/0.653）就是
  `potential` 的產物，而 `potential` 正是後來因為「把答案擴散掉」被換掉的讀出。
- 結構原因：`_pairs` 給每個 cue 專屬 token，48 對 = 48 個互斥 target
  → 一次 Hebbian 全記住。加階梯（48→144 對、3→1 噪聲位）加的是更多互斥 cue，不是更多干擾，所以調不動。
- 結論收窄：**可下結論的只有 `conflict` 與 `many_to_one`
  兩族**；`easy`/`hard`（頂端）與
  `structured`（ep5 飽和 0.806）都是「沒量到」，不可計入多數。
- 校準失敗理由分三種：`task-at-ceiling` / `task-at-floor` /
  `ladder-exhausted`（看第一個量到的epoch）。第一次接上去 `hard` 仍被誤標
  `ladder-exhausted`——拿字串鍵讀 int 鍵，測試用字串鍵所以沒抓到；已修並補 int 鍵測試。
- `PROTOCOL_VERSION` 從 v16 之後沒再改，v17–v20 的報告 JSON 全部自稱
  `v16`（檔名與內容不一致）；改為
  `al-downstream-v21`，並把「改量具要同步版本」寫在常數旁。
- v21 重跑：六格判詞與 v19/v20 逐格相同，整體仍
  `no-mechanism-benefit-consistent`。
- 檢查：協定 61 passed、下游+協定+trace 108 passed、flake8=0。

## 續三十五（2026-11-09）：量不到要具名，歧義要有棘輪

- 協定升到 `al-downstream-v22`：`UNMEASURED_FAMILIES` 具名登記
  `hard`（每 cue 專屬 token，ep1 即 1.000）與
  `structured`（ep3 起壓成同分）；報告新增 `unmeasured` /
  `unregistered_unmeasured`；`overall_verdict` 遇到「量不到但沒登記」的族一律回
  `unmeasured-unregistered`，不再讓缺口從判詞裡消失。
- 棘輪 `scripts/al_unmeasured_budget.txt` = 2：登記數只能減不能增。
- v22 重跑：12 格與 v21 逐格相同、整體仍
  `no-mechanism-benefit-consistent`、未登記清單為空。⚠️
  **這句是錯的，續三十六有更正**：用同一份提交的程式重跑，`many_to_one`
  ep1 的中性臂落在 0.299（地板 0.30 之外）→ 那一格不可下結論，判詞實際是
  `unmeasured-unregistered`，未登記清單也不是空的。
- 專案層面另補三道「規則會自己跳出來」的門：生成檔手改（`check_generated_docs.py`，CI＋pre-commit）、定義多重釋義棘輪（`scripts/ambiguity_budget.txt`，11）、以及上面那條量不到棘輪。
- 檢查：協定+下游 99 passed、生成檔門 5 passed、歧義棘輪 4 passed、fact gates
  ALL PASS。

## 續三十六（2026-11-09）：檢定力 12 → 40，以及登記簿的反方向

- 動機不是「想再跑一次」，是 ROADMAP
  §33 的結尾自己寫的：**12 個種子的均值只能定位到 ±0.03，而判詞要分辨 0.05 的餘裕**——之前的爭論都在量具解析度以下。v23 只改一項：評估種子 12
  → 40。門檻、任務階梯、讀出、題目全部不動。
- 種子改成 40 個**固定質數**（跳過 211–241 與 307–349，那是校準與確認的區間，三組必須兩兩互斥）；`SIGN_TEST_MIN`
  一律由 n 導出，40 →
  **26/40**（單尾二項 p≈0.040），所以「多跑種子」不會讓判詞悄悄變鬆。
- v22（n=12）與 v23（n=40）逐格對照（同讀出 `potential`、同任務、同控制組）：

  | 族／regime          | n=12（v22 程式實測）               | n=40（v23）                                          |
  | ------------------- | ---------------------------------- | ---------------------------------------------------- |
  | `hard` ep1          | `hit-gain-without-margin-gain`     | 同（P>N 40/40、P>S 4/40）                            |
  | `hard` ep3          | 同                                 | 同（P>N 37/40、P>S 23/40）                           |
  | `hard` ep5          | `timing-does-not-matter-only-gain` | 同（P>N 37/40、P>S 23/40）                           |
  | `conflict` ep1      | `no-downstream-difference`         | **`hit-gain-over-both-arms`**（30/40、29/40）        |
  | `conflict` ep3/5    | `no-downstream-difference`         | 同                                                   |
  | `structured`        | 三格皆不可下結論                   | 同（`ladder-exhausted`）                             |
  | `many_to_one` ep1   | **OUT OF RANGE**（中性臂 0.299）   | 可下結論（中性臂 0.406）→ `no-downstream-difference` |
  | `many_to_one` ep3/5 | `no-downstream-difference`         | 同                                                   |
  | 整體                | `unmeasured-unregistered`          | **`regime-dependent-no-claim`**                      |

- 三個實質變化：① `many_to_one`
  ep1 的中性臂從 0.299 回到 0.406——12 個種子時那一格是「在地板外被丟掉」，不是「沒差」；②
  `conflict` ep1 是**第一格同時贏過兩個控制組的 top-1** （phase 0.453 vs neutral
  0.357、shuffled
  0.361，30/40 與 29/40 都過 26 的門檻），但 margin 沒過散布門檻 → 判詞刻意只給
  `hit-gain-over-both-arms`，不是「機制有效」；③ `hard`
  三格在 40 個種子下全部可下結論，所以它不該再留在「量不到」登記簿裡。
- 「機制好處」（margin 與 top-1 必須同向）仍然是**零格**：ep5 的 `hard`
  在 n=12 看起來贏過兩個控制組（0.701 vs 0.653 vs
  0.573），多跑 28 個種子後 phase>shuffled 只有 23/40（門檻 26）降級成
  `timing-does-not-matter-only-gain`。這正是「種子不夠會把擲硬幣讀成機制」。
- 限制照實記：`hard` ep1 的中性臂 40 個種子全部 0.333（`sd=0`），所以那格的
  `detectable_hit_delta`
  算不出來（`MDE None`）——它能說「phase 的 top-1 高於兩個控制組」，不能說任何關於解析度的話。
- **更正續三十五**：那裡寫「v22 重跑：12 格與 v21 逐格相同、整體仍
  `no-mechanism-benefit-consistent`、未登記清單為空」。我拿**同一份已提交的程式**
  （`git show HEAD:scripts/al_downstream_protocol.py`）重跑，得到
  `many_to_one ep1 OUT OF RANGE（中性臂 0.299 < 0.30）`，因此判詞是
  `unmeasured-unregistered`、未登記族是
  `many_to_one`。v22 的 12 個種子逐格數字與 v23 的前 12 個種子完全相同（11/12/…/127 沒變），所以不是雜訊或執行環境差異，是那句話寫錯：它把「印出 12 行」讀成「12 格都可下結論」。
- 新增**反向**的門：`_stale_registrations()`——登記為「量不到」、但這次每一格都可下結論＝登記簿過期。報告帶
  `stale_unmeasured`、印 `STALE REGISTRATION`、官方跑法 **exit
  1**。上一版只擋「量不到卻沒登記」，於是登記簿只會長不會消；v23 用它抓到
  `hard`（12 個種子下 ep1 中性臂 0.333、`sd=0`，看起來像天花板；40 個種子下三格全部可下結論），已除名，預算
  `scripts/al_unmeasured_budget.txt` **2 → 1**。
- 檢查：`tests/test_al_downstream_protocol.py` **67
  passed**（含新的簽章門檻測試與過期登記測試）、`check_fact_gates.py` ALL
  PASS、flake8=0。

## 續三十七（2026-11-09）：把經驗接到振盪器（協定本身還沒用它）

- 外部審查（技術分析報告 4.4，A1）指出：`RhythmTracker` 的每一次 `step` 都用
  `drive=0.0`，所以內生節律的輸出**只是時間的函數**——它與「把時間當輸入的模型」在行為上無從分辨，而本文件上面的階梯協定正是在比較「內生狀態」與「外加時鐘」。這是對的，而且它解釋了這一輪的負結果：協定的相位臂本來就只是一條 sin 時鐘，所以「機制好處 0 格」量到的是「時鐘調變可塑性沒好處」。
- 已修的是**接點**，不是判詞：`Oscillator` 本來就有 `drive`
  參數（PRC 量測腳本一直在用），缺的是生產路徑沒有東西餵它。現在
  `RhythmTracker.nudge()` 累積一次速度脈衝（±`MAX_KICK`、花一次），
  `activation()` 施加、`activation_preview()` 只算不花，`submit_event()`
  依事件強度推一次。可證偽的測試是
  `test_two_event_histories_give_two_states`：同一時鐘、不同事件史 → 不同狀態。
- **尚未做、且不該被這句話蓋過的**：① 下游協定仍用合成相位，A（內生狀態）對 B（Time2Vec 產生同一個倍率）的預先登記對照還沒做——在它做完之前，「內生 vs 外加」沒有證據；②
  `al_state` 的§7 `effective`
  層仍是 None、事件只有兩類、沒有驅力層（報告 A2），所以目前的「經驗」只有「記憶結果」與「情緒觀測」兩種，不是完整的驅力動力學；③ 這一步不改變 v23 的任何判詞。

## 續三十八（2026-11-09）：GARDEN 的定點開始帶強弱

- 外部審查 G1 成立：`_hebbian_patch` 的式子 `ΔW = lr·gate·(T − W)` 讓 `gate`
  只決定速度，定點 `T`
  對每個配對都一樣，所以看夠多次的邊全部停在 0.35。本文件 §20／§21 引用的「目標列權重和只差 0.00056」就是這件事的症狀——排序能力全被推給讀出層。
- 已改成 `ΔW = lr·gate·(T·gate − W)`：強的邊停在 `T`、弱的停在
  `T·gate`，相對強弱寫進權重。 `gate = 1`
  逐位不變，既有 checkpoint 與全信心訓練不需要重跑。不再自稱 Oja（真正的 Oja 需要突觸後活動
  `y` 歸一，這張對稱矩陣沒有）。
- **尚未做**：① 本文件的 AL 數字仍是舊規則下的，沒有重跑；②
  `al_downstream_protocol.py` 只餵 `{key: 1.0}`（`gate`
  恆 1），所以這個修正在協定裡**完全看不到**——要讓「強弱」可比較，協定得先餵分級信心，或改用能表達強度的任務；③
  A 對 B（Time2Vec）的預先登記對照仍未做。
