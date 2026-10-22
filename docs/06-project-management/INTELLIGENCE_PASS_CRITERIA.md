# 智能的及格標準（外部基準推導，非自訂）

> 為什麼要有這份文件：如果及格線是本專案自己訂的（「我們覺得 25% 就算過」），
> 那就變成**自問自答**——先把門檻調到剛好能過，再宣稱「達標」。所以每一條
> 及格線都必須由**公開基準的量測規則**推導出來，並附上引用。
>
> 機器可讀的定義在 `apps/backend/src/ai/meta/intelligence.py`
> （`Anchor` / `pass_line()`）；門禁
> `scripts/check_intelligence_definition.py` 會重算，任何人手改門檻都會被擋。

## 一、推導規則（三條，統一適用）

| 規則 | 內容 | 依據 |
| --- | --- | --- |
| **R1 隨機地板** | 及格 ≥ **隨機基線 + 20 個百分點** | MMLU 論文用「比隨機高近 20 個百分點（almost 20 percentage points）」來描述 GPT-3 的**顯著進步**（Hendrycks et al., 2020, §1） |
| **R2 人類相對** | 及格 ≥ **0.5 × 人類上限** | 以人為尺：做到人類一半才算「開始會」。人類上限取自該基準公布的專家／標註者表現 |
| **R3 無人類基線** | 及格 = **0.7 × 已發表強基線／SOTA** | 該基準沒有公布人類表現時（例如工具呼叫只有排行榜），以已發表的強系統為尺 |

**及格線 = 對該題型適用的規則取大者**（例如 MMLU：R1 = 45%、R2 = 44.9% → 取 45%）。

三條規則的共同點：**尺都在外部**。本專案只決定「用哪條規則」，不決定「數字是多少」。

## 二、逐維度及格線

| 維度 | 外部基準（引用） | 公布錨點 | 規則 → 及格線 | 本專案實測 | 判定 |
| --- | --- | --- | --- | --- | --- |
| **facts** 事實與知識 | MMLU（Hendrycks et al., 2020, [arXiv:2009.03300](https://arxiv.org/abs/2009.03300)） | 4 選項隨機 25%；非專家 34.5%；**專家 89.8%** | R1：25% + 20pp = **45%**（R2 = 44.9%，取大） | 20.0% | ❌ FAIL |
| **math** 数理與邏輯 | GSM8K（Cobbe et al., 2021, [arXiv:2110.14168](https://arxiv.org/abs/2110.14168)；GPT-4 TR 2023 Table 2） | 已發表強基線 **87.3%**（Chinchilla+SFT+ORM-RL）；GPT-4 92.0% ※含污染註記 | R3：0.7 × 87.3% = **61.1%** | 80.0% | ✅ PASS |
| **paraphrase** 改述泛化（L1 關鍵） | PAWS（Zhang et al., 2019, [N19-1131](https://aclanthology.org/N19-1131/)） | 二元隨機 50%；**人類一致度 92.0%**（QQP）／94.7%（Wiki）；訓練後模型 85% | R1：50% + 20pp = **70%**（R2 = 46%，取大） | 0.0% | ❌ FAIL |
| **dialogue** 對話與記憶（L2 關鍵） | LoCoMo（Maharana et al., ACL 2024, [2024.acl-long.747](https://aclanthology.org/2024.acl-long.747/)） | **人類 87.9**（長對話 QA F1）；最佳 LLM 51.6 | R2：0.5 × 87.9% = **44.0%**（高於隨機地板 20%） | 75.7% | ✅ PASS |
| **boundary** 推理與例外 | FOLIO（Han et al., EMNLP 2024, [2024.emnlp-main.1229](https://aclanthology.org/2024.emnlp-main.1229/)） | 三值隨機 33.3%；非專家 61.8%；**專家 96.0%**；GPT-4 64.2%（CoT 68.9%） | R1：33.3% + 20pp = **53.3%**（R2 = 48.0%，取大） | 88.9% | ✅ PASS |
| **tools** 工具與行動 | BFCL V4（Patil et al., ICML 2025, [leaderboard](https://gorilla.cs.berkeley.edu/leaderboard)，2026-10-22） | Overall **SOTA 77.5%**（Claude Opus 4.5）；中位數約 45% | R3：0.7 × 77.5% = **54.2%** | 0.0% | ❌ FAIL |

實測值來源：`scripts/report_intelligence.py`（快照
`intelligence_report.json`）。**4.41/10 平均落在 L2 帶，但達成的階梯是 L0**
——L1 的關鍵度量（改述泛化）是 0%，距離 70% 的及格線很遠。

## 三、協定等價性（必須說清楚，否則就是另一種自欺）

內部量測**不是**在 MMLU／GSM8K／PAWS／LoCoMo／FOLIO／BFCL 上跑的。它們是
「**同題型、自己出題**」：

| 維度 | 等價等級 | 差異 |
| --- | --- | --- |
| facts | `analogous` | 同為 4 選項知識題；內部 40 題、主題不同 |
| math | `analogous` | 同為小學～競賽級套用題；內部 40 題 |
| paraphrase | `analogous` | PAWS 是「成對改述判定」；內部是「改述問答正確率」——同為看穿改述，計分不同 |
| dialogue | `analogous` | LoCoMo 是長對話 QA F1；內部是多輪人話標準通過率 |
| boundary | `analogous` | FOLIO 是三值一階邏輯；內部是「事實＋條件＋例外」斷言題 |
| tools | `analogous` | BFCL 是 API 工具呼叫；內部是沙箱執行＋路由選擇 |

因此這些及格線是**可比性下限（compatibility floor）**，不是「在這六個基準上
得分」。要升級為 `same`，唯一辦法是**真的去跑那六個公開基準**（或它們的官方
子集），那時才算同一把尺。

> 這份文件刻意**不**提供「良好／優秀」級距：多一級就多一個可以自己調的旋鈕。
> 及格線只有一條，且由外部規則算出。

## 四、變更程序

1. 改規則（R1／R2／R3）→ 需要一條新的外部依據，並在此文件寫明引用。
2. 改錨點（例如 BFCL SOTA 更新）→ 更新 `Anchor` 的公布值與日期。
3. 改我們的量測協定 → 同步更新 `protocol` 與「協定等價性」表。
4. 以上任一項都會被 `python scripts/check_intelligence_definition.py` 與
   事實門 `intelligence.definition_wellformed` 檢查（文件與程式必須一致）。
