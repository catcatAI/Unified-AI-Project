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
