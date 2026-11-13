# AI+AL 單一核心狀態契約

> **先讀這一頁，再改 `core/state`、`ai/core`、`generation_gate`、`chat_routes` 的狀態或生成路徑。**
> 這份是**契約**，不是願景。違反 §2 的設計，不管分數多好都不算完成；文件結尾有審查清單。

- 版本：7.5.0-dev　｜　建立：2026-11-12　｜　狀態：active（contract）
- ANGELA-MATRIX：`[L3-L4] [αβγδ] [B] [L0-L11]`
- 相關文件：`AL_LADDER_ROADMAP.md` §8（通道 A/B/C）、`AL_AI_LADDER_STATE.md`（現況）、
  `CORE_GAP_ANALYSIS.md` §35–§36（能力量測）、`LAYER_SEPARATION.md`（分層）

---

## 0. 這份文件要防的三個歷史問題

1. **狀態走上下文**：把情緒／喚醒／生命階段寫成文字塞進 system prompt，模型只是
   「讀到一段描述自己的話」，不是「處於那個狀態」。它會增長、會被忽略、重啟只剩最後
   寫進去的那個數字，而且模型可以把數字覆述出來，看起來像有狀態。
2. **AI 與 AL 分成兩個實體再加一座橋**：AI 一個模型、AL 一個模型（或一堆 JSON／
   事件／提示詞），兩邊各自保存一份狀態，靠 prompt／參數／logit／routing 傳遞。
   外觀相同，性質不同：橋是可被忽略、可被注入者重現的，而且**狀態重複**。
3. **單回合 pairs 訓練 + 每次 reset**：`TokenSNN.generate()` 每次 `init_state(1)`，
   `train_on()` 的 `pairs` 彼此獨立。遞歸只用在一句答案之內，從未跨回合；量到的分數
   只回答「單回合 mapping」，不能拿來宣稱「persistent core」。

**結論先寫**：核心必須是**同一個模型、同一份權重、同一個狀態物件**，AI 週期與 AL
週期只是同一個底層的兩個入口；狀態**不進 context**。這就是本契約的主軸。

---

## 1. 名詞（避免同一個字指兩種東西）

| 名詞 | 定義 | 不是什麼 |
| --- | --- | --- |
| **AI** | 能力面：感知、語言、推理、生成 | 不是另一個模型 |
| **AL** | 生命面：時間、節律、情緒、穩態、生命週期、可塑性 | 不是另一份 JSON／提示詞 |
| **core** | 實際產生答案的模型；`core` provenance 只在「模型產生且正確」時成立 | 不是模板、檢索、路由 |
| **state** | 固定大小、可持久化、模型自己擁有的張量＋慢變量 | 不是 context、不是 KV cache、不是摘要 |
| **context** | 這一次請求要看的內容（檢索結果、指令、當前對話） | 不是「我是誰／我現在怎樣」 |
| **memory** | 事實與情節的內容庫（教過的事、對話回憶） | 不是 working state |
| **observable** | 由 state 投影出來、給表層／審計／可視化的讀數 | 不是狀態本體 |

三句話區分：

- **memory 記「發生過什麼」**（可以檢索、可以很長）。
- **state 記「我現在是什麼」**（固定大小、會衰減、跨回合）。
- **context 記「這一次要看什麼」**（用完就丟，不承擔人格連續性）。

---

## 2. 五條硬規則（違反即退回）

- **R1 單一底層**：同一份權重（一個 `weights_hash`）、同一個 state 物件、兩個 step
  函式（`ai_step`／`al_step`）。**不得**用第二個模型充當 AL。
- **R2 狀態不進 context**：core 路徑的 prompt 不得包含 state 的文字／數字摘要；
  KV cache 不得冒充 state。LLM fallback 可以用 `state_for_llm`，但必須標
  `route=prompt` 且不計核心。
- **R3 單一寫入者**：state 的突變必須序列化（per-session 鎖＋版本號）；持久化用原子
  寫入；載入失敗寧可拒絕，不得靜默重置。
- **R4 沒有 ablation 就沒有宣稱**：只憑「輸出有變」不算狀態證據；必須有
  state ablation、restart、cycle-switch 三項（§6）。
- **R5 重置是顯式操作**：只有新使用者／新 session／測試可以 `reset_state()`；
  進程啟動、每回合、每次生成都不得自動重置。

---

## 3. 狀態模型

### 3.1 四類欄位（沿用 `core/life/al_state.py` 的分類）

| 類別 | 內容 | 是否落盤 | 誰更新 |
| --- | --- | --- | --- |
| `invariant` | `schema_version`、`model_kind`、`weights_hash`、`user_id`、`session_id`、`born_at` | 是 | 建立時一次 |
| `slow` | 時鐘 `last_update`／`ticks`、振盪器相位、生命週期、arousal 目標 | 是 | `al_step` |
| `fast` | 模型張量：GRU `h`、SNN `mem/spk`、SSM `s` | 是 | `ai_step`／`al_step` |
| `derived` | observable：顯示用的情緒／強度／漂移 | **否**（只快取） | 讀取時投影 |

`derived` 不落盤，與 `al_state.py` 的 I3 一致；`slow` 與 `fast` 一起構成
「同一個 core 的狀態」，不是兩份。

### 3.2 schema（最小欄位）

```json
{
  "schema_version": 1,
  "model_kind": "gru|snn|ssm",
  "weights_hash": "sha256:...",
  "user_id": "...",
  "session_id": "...",
  "born_at": "2026-11-12T...Z",
  "last_update": "2026-11-12T...Z",
  "ticks": 1234,
  "last_dt_s": 12.5,
  "state_version": 42,
  "tensors": {"h": "<path or inline>"}
}
```

- **大小上限**：單一 session ≤ 10 MB；超過就量化或縮維，不得默默長大。
- **格式**：`meta.json` ＋ `tensors.npz`（或 `torch.save(weights_only=True)`）；
  不用 pickle 載入任意物件。
- **完整性**：`sha256` 涵蓋 meta＋tensors；不符即拒絕載入。
- **版本**：`schema_version` 或 `weights_hash` 不符 → 拒絕（或走顯式 migration），
  **不得**當成新狀態重來。
- **並發**：`state_version` 單調遞增；寫入採樂觀鎖（讀到的版本已被改過就重讀／重算）。

### 3.3 與 observable 的關係

`core/life/al_state.py` 的 `get_al_state()` 繼續存在，但角色改成**投影＋審計**：
它的值來自 core state 的 readout（或 core 推過去的事件），不是另一份獨立的真相。
`core/life` 不得 import `ai.*`（I8 不變）；由 AI 側把投影／事件推進去。

---

## 4. 兩個週期與切換

### 4.1 介面

```python
# 同一個 model、同一份 state
def ai_step(tokens, state) -> (logits, state):   # 有外部輸入
def al_step(dt, state, events) -> state:          # 沒有外部 token，只有時間／內感受
```

- `ai_step`：prefill 與逐 token 解碼都用它；`state` 是可選輸入（第一次可為
  `None` → 由 `init_state()` 建立，但**只在 session 建立時**）。
- `al_step`：把 `dt`、振盪器相位、事件摘要（有界）餵進**同一個 recurrence**；
  可以用一個學到的 tick embedding，或零輸入＋時間特徵；輸出更新後的 state。
- 兩者共用同一組權重與同一個 state；`al_step` **不得**呼叫另一個模型。

### 4.2 時間線（v1：回合邊界）

```
使用者訊息到達
  dt = now - state.last_update
  state = al_step(dt, state, events)        # AL 週期：時間先作用在狀態上
  logits, state = ai_step(prompt_tokens, state)
  ... 逐 token 生成 ...
  state.last_update = now; state_version += 1
  persist(state)                            # 原子寫入
```

- v2 才做背景 `al_step`（低頻心跳）；此時必須用同一把鎖，或版本檢查＋重算。
- `al_step(0)` 必須是 no-op（或誤差 ≤ 預設容差）；`al_step(dt1)` 後 `al_step(dt2)`
  應接近 `al_step(dt1+dt2)`（半群性質，對應 AL ladder r1）。
- 單次 `dt` 過大要分段（例：每段 ≤ 60 s），避免數值不穩。

### 4.3 「內在傳遞」是什麼意思

切換 AI／AL 週期時，**不需要搬運狀態**：`state` 是同一個物件／同一組張量，兩個 step
都直接讀寫它。任何需要「序列化 → 傳給另一邊 → 反序列化」的設計，都不符合本契約
（那就是 R1 的兩個實體）。

---

## 5. 訓練：同一個 trunk，兩個 loss

### 5.1 資料單位是 session，不是 pair

- 一筆訓練樣本是**多回合序列**：`(turn_1, gap_1, turn_2, gap_2, …)`，帶時間戳。
- 切分按 **session／user**，不按 row；同一 session 的回合不得跨 train/held-out
  （否則 state 會把答案從訓練帶到測試）。
- 沒有真實 gap 的資料，用合成 gap 做對照；gap 長度要覆蓋短／中／長。

### 5.2 兩個 loss

| loss | 作用 | 訊號 |
| --- | --- | --- |
| `L_ai` | 下一個 token 的 CE（只算助理回覆） | 有標註對話 |
| `L_al` | 狀態隨時間的自我預測／一致性 | 無需標註：`al_step(dt)` 後的 state 要能預測實際演化；`dt=0` 不變；`dt1+dt2` 近似半群 |

- 同一個 optimizer、同一個 trunk；`L_al` 可以由一個小 head 讀 state，
  但**不得**是第二個 trunk。
- `L_al` 的權重在實驗前固定；不得看 held-out 調。
- 跨回合用 truncated BPTT（窗口例如 2–4 回合），避免記憶體無限增長。

### 5.3 不要做的事

- 不要在獨立 pairs 上訓練，卻宣稱學到跨回合狀態。
- 不要把 `StateMatrix` 的數字當 label 硬背；那會把狀態變成另一個模板。
- 不要讓 AL loss 只學「複製上一個 state」；要有 dt 條件與 `dt=0` 的 no-op 約束。

---

## 6. 量測：六個測試，先預登記

任何「AI+AL 在同一個模型」的宣稱，至少要通過這六項；缺一項就只能說「AL 影響了
輸入／參數」。

| # | 測試 | 做法 | 通過條件（預先登記） |
| --- | --- | --- | --- |
| T1 | **state ablation** | 在回合 k 把 state 歸零／打亂，其餘不變 | 正確率或 AL 預測有**顯著下降**（幅度先寫定） |
| T2 | **prompt leak** | core 路徑的 prompt 不含任何 state 文字；另跑「state 只放 prompt」的 baseline | 兩者可區分；core 不依賴 prompt 裡的 state |
| T3 | **gap / retention** | 第 1 回合給事實／情緒事件，第 k 回合提問；前面回合從 context 移除 | 分數隨 gap 的衰減符合預測；優於 stateless |
| T4 | **restart** | 存檔 → 重啟 → 載入 → 同一輸入 | 行為在容差內一致；版本／hash 不符時**拒絕** |
| T5 | **cycle switch** | 回合間跑 `al_step(dt)`；對照：不跑、打亂 dt、假時鐘 | 行為按預測方向改變；對照組不變 |
| T6 | **provenance** | 記錄 `weights_hash`、`state_version`、`ticks`、`route` | 一次生成只對應一個 model、一份 state |

**baseline 三組**（缺一不可）：

1. stateless（每次 reset）；
2. state-in-prompt（把狀態寫成文字，這是現在的做法）；
3. hand-state（`StateMatrix` 當輸入，但不給模型自己的 state）。

**反偽造**：一個 stateless 模型 + 完整 state 文字，必須在 T1／T4／T5 失敗；
如果它也通過，代表測試沒有鑑別力，先修測試。

**停損**：T1 沒有下降 → 模型沒在用 state，不准宣稱；T4 不一致 → 不准宣稱重啟延續；
T5 對照組也變 → 先把實驗做乾淨。

---

## 7. 架構選擇（在這條契約下）

| 架構 | 原生 state | 變動 dt | 可訓練性 | 成本 | 適配 | 建議 |
| --- | --- | --- | --- | --- | --- | --- |
| **GRU** | `h` | 需把 dt 當輸入 | 已量到（0.68／0.81） | 低 | 好 | **第一個實作** |
| **SNN（LIF）** | `mem/spk` | 天生 leak | 較難（梯度帶） | 中 | 主題／效率線 | 同契約的第二個臂 |
| **SSM（Mamba 類）** | `s` | **原生**（dt 進遞歸） | 中 | 中 | 最貼合「時間作用在狀態上」 | 值得原型 |
| **Transformer** | 無 | 無 | 好 | 中高 | 能力強，但 state 要靠 adapter | 只當 teacher／fallback，或加固定大小 recurrent state 並通過 T1–T5 |
| **檢索／工具** | 不適用 | — | — | 低 | 事實與精確計算 | 不是核心 |

- **KV cache 不是 state**：它隨 session 增長、重啟消失、且只記 token。要用
  Transformer 當 core，必須另外設計固定大小的 recurrent state（state tokens／
  segment recurrence），並在 T1／T4／T5 上證明它真的被使用。
- 選擇規則：先過 T1–T6，再比「能力／秒」與「能力／瓦」；不要用架構偏好決定。

---

## 8. 與現有模組的關係（不要重造，也不要混淆）

| 現有模組 | 現在的角色 | 在本契約下的角色 |
| --- | --- | --- |
| `core/life/al_state.py` | AL 單一狀態面、快照、事件入口 | **observable 投影＋審計**；不是 core state 本體 |
| `core/life/al_snn_modulation.py` | C-state-lite：改 GARDEN 發火閾值 | 可作為 `al_step` 的 prior／控制輸入；**不是**持久 state |
| `core/life/al_oscillator.py` | 節律源 | `al_step` 的時間／相位輸入 |
| `core/life/al_generation_params.py`／`al_logit_bias.py` | C-param／C-logit | 只給 LLM fallback；不計核心 |
| `core/life/digital_life_integrator.py` | 生命週期協調 | 提供 `slow` 變量與事件，不是第二個模型 |
| `StateMatrix4D` | 手定義的狀態摘要 | core state 的投影／prior；**不得**在 core 路徑當文字注入 |
| `services/llm/prompt_builder.py`／`chat_routes.state_for_llm` | 把狀態寫進 prompt | 只保留給 LLM fallback，標 `route=prompt` |
| `services/llm/generation_gate.py` | 定義誰是生成後端 | 新增 `stateful` 能力旗標；只有 stateful 後端能宣稱 core state |
| `ai/garden/snn_core.py` | 聯想網路 | 可消費 AL 狀態；不是語言 core |
| `ai/ed3n/token_snn.py` | token-SNN 語言模型 | 加 `state` 進出；**不得**每次 `init_state` |

**I8 不變**：`core/life` 不 import `ai.*`；core state 在 AI 側，observable 由 AI 側
推事件／投影給 AL。

---

## 9. 遷移路徑（每階都有 gate）

| 階段 | 做什麼 | Gate（沒過就不進下一階） |
| --- | --- | --- |
| **P0** | 凍結本契約＋schema＋測試骨架（不改行為） | 文件與 schema 審查通過；T1–T6 的定義寫定 |
| — | **P0 狀態（2026-11-12）**：完成。`ai/core/core_state.py` ＋ 15 條 schema／拒絕載入測試；**行為未改**。 | `pytest tests/ai/test_core_state_contract.py` 綠；`mypy` 0 error |
| **P1** | 用 GRU 實作 `CoreState`＋`ai_step`／`al_step`；合成多回合資料；跑 T1–T6 | T1 有顯著下降、T4 一致、T5 對照組不變 |
| — | **P1 第一臂狀態（2026-11-12）**：完成，**17/17 預登記檢查通過**。主臂時間題／內容題 0.9998；歸零 `h` → 0.5092／0.0785（可回答半）；不跑 `al_step` 與歸零**逐位同分**；hand-state 臂歸零 `h` **完全不受影響**（1.0000）。預登記 §37.4–§37.5、結果 §37.6–§37.7。**這不是能力分**：核心分仍 0.00/10，生產路徑未接。§38 的等段數重跑（每 session
固定 8 個 chunk，排除「數更新次數」的捷徑）**18/18 通過**，主臂 1.0000、歸零 0.4986。 | `probe_state_cycles.py` 的 `all_pass=True`；`tests/ai/test_state_cycles.py` 17 條綠 |
| **P2** | 把同一契約接到 SNN（先修梯度帶）；與 GRU 同預算比較 | 同參數同步數下可訓練；T1–T6 過 |
| **P3** | SSM 原型（dt 原生） | 在 T3／T5 上優於或等於 GRU；成本可接受 |
| — | **P3 狀態（2026-11-12）**：SSM 臂**21/21 預登記檢查通過**（主臂 1.0000、歸零 0.0000＝常數錯答而非 chance、不跑 `al_step` 0.4970、打亂 0.4948、假時鐘 0.0000、restart 0）。半群 **1.9–3.8e-6**（登記 ≤1e-2）——但這是**架構保證**（指數相乘），不是學到的連續性。T3 1.0000（與 GRU 相同）；不跑 `al_step` 0.4970 vs GRU 0.4988（差 0.0018，在 ±0.0123 半寬內，不下降）。**成本已乾淨量測**（`--cost`，三次獨立 run、交替順序、每次 30 reps 取中位數）：參數 4,634 vs 21,402（0.217×）、checkpoint 20.8 vs 86.9 KiB（0.239×）、forward 1.14–1.15 vs 2.02–2.07 ms（**0.55×**）、訓練步 2.82–3.01 vs 6.31–6.42 ms（**0.45×**）。這是**合成任務尺寸**的計算量，不是生產延遲；P4 未接線前不宣稱「成本可接受」（見 `CORE_GAP_ANALYSIS.md` §40.7）。 | `probe_state_cycles.py --round 4` 的 `all_pass=True`；`tests/ai/test_ssm_core.py` 9 條綠 |
| **P4** | 接生產：`generation_gate` 加 `stateful`；`chat_routes` 傳 state 物件；`state_for_llm` 只給 fallback | 生產路徑不再把 state 寫進 core prompt；provenance 正確 |
| — | **P4 狀態（2026-11-12）**：接線完成，**opt-in、預設關**（`ANGELA_STATEFUL_CORE=1`）。`ai/core/stateful_runtime.py` 每回合推進一次 state 物件並存檔（每 session 一個目錄，共用同一份權重）；開啟時 `chat_routes._ctx_state_matrix` **不再發布** `state_for_llm`，回覆的 provenance 記 `state_source="core"` ＋ `core_state`（`ticks`／`state_version`／`dt_s`／`arch`／`tokenizer`／`weights_hash`）。**核心不寫回覆**：目前沒有任何核心能生成開放域文字，所以它只承載狀態，回覆仍由既有路由產生；`state_source` 就是為了不讓這件事被誤讀。預設關閉時回覆形狀完全不變。**核心分仍 0.00/10**（見 `CORE_GAP_ANALYSIS.md` §41）。 | 開啟後 `/api` 回覆帶 `state_source="core"`；`tests/ai/test_stateful_runtime.py` 16 條綠；關閉時 `_ctx_state_matrix` 行為與 §40 前相同 |
| **P5** | 量產級：per-user 持久化、重啟、版本遷移、成本 | 文件與分數同步；核心分只在模型產生時變動 |
| — | **P5 狀態（2026-11-13）**：量產級的三件事完成——**單一寫入者**（R3）、**狀態能說出它是誰的**、**真實回合的量測**。① R3 現在有三道鎖，各補別人的盲點：per-session 執行緒鎖（固定條帶，不會因為淘汰而讓同一 session 出現兩個鎖）、session 目錄裡的 advisory 檔案鎖（POSIX `flock`／Windows `msvcrt`）、以及存檔前的版本比對。第三道不是多餘的——它是唯一會發現「完全沒拿鎖的寫入者」的一道（測試用一次**合法**存檔、有效 checksum 的干擾寫入證明：只靠 checksum 會漏）。等待上限 2 秒，逾時就拒絕該回合而不是讓回覆卡住；`availability()` 回報 `lock`／`multi_writer_safe`，沒有檔案鎖的主機自己說出來。② `advance(user_id=...)`：新狀態記下主人，續接時主人不符就拒絕（session id 可猜，主人不行），空主人的舊狀態（§41 跑出來的那些）接受而不回溯作廢。③ `scripts/probe_core_turns.py` 走真正的 `_handle_chat_request`，把凍結標準集跑 **2,208 回合**（五個 stratum 各一個 session），逐回合寫 JSONL；gate 要求回合數、零拒絕、版本嚴格遞增（一次更新都沒掉）、五個 stratum 都在。**仍然沒變的**：核心不生成回覆，沒有任何東西把 state 讀回生成，核心分仍 **0.00/10**；`schema_version` 只有 v1，不符就拒絕（**沒有** migration 實作，照實記）；§40.7 的成本是合成任務的計算量，不是生產回合延遲。 | `tests/ai/test_stateful_runtime.py` 27 條綠；`scripts/probe_core_turns.py` 的 `all_pass=True`；`multi_writer_safe=True` 時可開多 worker |
| **內容** | state 裡裝的東西有沒有語言內容、生成會不會讀它（§43–§44） | `heldout_names` exact 過線、零狀態與冷啟掉回 0 |
| — | **內容狀態（2026-11-13）**：**有內容，但只在合成任務上，而且用法有邊界**。同一個 `GRUCore`（81,765 參數，`hidden=128`／`emb=64`，契約 R1 的那個臂）在 「教一次 `remember <name> = <value> .`（不算損失）→ `al_step(120 s)` → 問 `<name> ?` → 生成 `<value> .`」上，對**沒見過的名字＋沒見過的值** exact **0.995**（`dev` 0.994，3,000 題）；把 `h` 歸零（**同一個 state 物件、同一份權重、同一個 prompt**）**0.000**、跳過教學回合（`cold`，同題）**0.000**。teacher-forced 0.999、只讀 `h` 的線性 probe 0.851 → 失敗與成功都不是量測接錯。**三條邊界照實記**：① `wrong_name` **0.994**——教 A、問沒教過的 B 照樣吐 A 的值，所以是**單槽攜帶**、不是鍵值查詢（名字沒有被使用）；② 拿掉 `al_step` 掉到 **0.003**——不是間隙不變，學到的是「經過**一次** 120 秒」可讀；③ 詞彙是封閉 CV 音節（19 字母）、句型只有一種，這是**機制**不是語言。**核心分仍 0.00/10**：這條路沒有接進生產，`stateful_runtime` 仍是 `hash-bucket` tokenizer，回覆仍由表層產生——把只會講 `remember X = Y` 的 checkpoint 接上去會比不接更糟。 | `scripts/train_state_content.py` 的 `all_pass=True`；`tests/test_state_content_task.py` 13 條綠；checkpoint 重載後 `heldout` 0.995／零狀態 0.000 |
| **兩組** | state 能不能同時持**兩組**配對，並由查詢選一組（§45） | `heldout_names` exact 過線，且兩個問法各自都選對 |
| — | **兩組狀態（2026-11-13）**：**不能，而且不是預算問題**。同一個 81,765 參數的 `GRUCore`、同一個 seed（20261115）：**一組**配對 held-out exact **1.000**（probe 0.874），**兩組**配對 **0.0033**（`single` 目標）／**0.0100**（`both` 目標，兩組查詢都進損失），門檻 0.30，B1／B2／B3／B5 全 FAIL，零狀態與冷啟 0.000。`h` 的線性 probe 對「第一組教的值／第二組教的值／被問的值」只有 0.319／0.413／0.303（`single`）與 0.351／0.383／0.280（`both`）字元（chance 0.027）——**兩個槽都不可讀**，所以是「根本沒寫進去」，不是「寫進去選不出來」。**兩個已排除的解釋**：目標（兩臂排序在兩個 seed 上翻轉，差別在雜訊內；`both` 只是一致地比較好擬合，dev 損失 0.741 vs 1.007）與寬度（256 寬：訓練損失 0.196、held-out 0.057）。**照實記的一個陷阱**：兩臂的 `other_value_rate` 只有 0.002–0.004，但那是因為它們**兩組的值都沒答出來**，不是「避免賭」——所以 B5 必須同時要求兩個 `by_ask ≥ 0.50`，這一輪剛好是它的反例。結論是一條**設計要求**：可定址性（key 位址化的槽、或對教學回合做注意力）不會從「同一個向量連續覆寫」長出來。**核心分仍 0.00/10**，未接生產。 | `scripts/train_state_binding.py` 的兩份報告 `all_pass=False`（如實）；`tests/test_state_binding_task.py` 24 條綠；同 seed 單組對照 `state_content_20261113-033723` `all_pass=True` |

| **可定址** | 同一個 state 裡開**可寫的槽**，查詢用位址去讀（§46，唯一變數＝結構） | 兩個問法各自選對（`by_ask` 皆 ≥ 0.50），且消融「拿掉 store」真的更差（B7 gap ≥ 0.20） |
| — | **可定址（2026-11-13）**：**結構改對了，但選取與接線壞了**。`SlotMemoryCore`（同一個 GRU ＋ 四個 gate 寫入、attention 讀取的槽，134,124 參數）在**同一份切分**（digest 相同）上：dev exact **0.0007**、held-out **0.0000**，B1／B2／B3／B5／B7 FAIL，B4／B6／B8 PASS。**這一輪的重點不是分數，是三個讀數**：① store **真的存了兩組值**——`read` 的線性探針對兩組各 **0.589／0.593** 字元（chance 0.1333）、full exact 0.008／0.010（chance 2.4e-6），所以「沒寫進去」已經排除；② **選不出來**——`distinct_read_slot_rate` **0.0000／0.0003**、`read_cosine_between_asks` **0.9998**、`attention_max_prob_mean` **0.97**，兩個問題讀同一格而且很果斷；③ **store 反而更差**——同參數、只把讀寫拿掉的消融臂 held-out **0.1233**，B7 的差是 **−0.1233**（不是 +0.20），`other_value_rate` 0.0 表示吐出來的字串**兩組都不是**（解碼壞了，不是 hedging）。B8 PASS（matched GRU 0.1557 < 0.30）→ 不是參數問題。**下一輪登記的變數是「定址訊號」**（對教學回合做 per-turn keys）**與讀取→控制器的接法**；在登記寫下來之前不開計分 run。**核心分仍 0.00/10**，未接生產。 | `scripts/train_state_binding.py` 的三份報告（A／C2／C3）`all_pass=False`（如實）；`tests/test_state_binding_task.py` 40 條綠；`scripts/check_layer_separation.py` 的 `stateful_core_two_bindings` 仍 `fail` |

| **語言** | 同一個 core 能不能讀進一段 byte 文字、再產生文字（§47 登記、§48 結果） | L1–L7 全過，且**英文與證詞各自**贏過自己的 trigram floor（合併數字不算） |
| — | **語言（2026-11-13）**：**設備有了，能力沒有跟著宣稱**。同一個 `GRUCore`／`CoreState` v1（**124,611** 參數、259 個 byte token）在 4.01 MB 上訓練 5 epochs（**402.65 s**、xpu），**L1–L7 全 PASS**：留出 BPC **1.3164** vs 插值 bigram 3.4317／trigram 2.1547；L3 100 個 prefix 有 **98** 個不同續寫、平均 LCP **8.14** vs trigram 1.71；L4 帶 state 1.3164 vs 每窗重置 1.4219（**7.4%**）；L5 在 `--check` 裡真的把 checkpoint 載回同一個類別；L6 文字流無 oracle／camera tag；L7 成本已記錄。**分解（§47.9 要求，也是這一輪最重要的讀數）**：英文 general **2.2201**（贏自己的 trigram 2.9739 約 **25%**）、證詞 **0.2480**（贏 1.1892 約 79%）；L3 拆開後英文只比 trigram 多對 **1.1 byte**（1.64 vs 0.55）且是固定填充詞，證詞的 16.09 才是拉高合併數字的原因。**照實記**：證詞低 BPC 是模板格式規律，不是中文能力；英文續寫不是理解。**核心分仍 0.00/10**、系統分 6.41 不動；這一階是 P 的載體，不是結果。 | `scripts/train_text_stage.py` 的報告 `all_pass=True`；`--check` 在 2026-11-13 之後**會回報 `weights_hash` 不符**——那是 §48.7 的欄位標錯（報告記的是初始化，不是 checkpoint），L1–L7 的判定不讀那個欄位，所以分數不動；`tests/test_text_stage.py` 22 條綠 |

| **推理** | 同一個 core 讀完多輪口供，指出違規的人（§49 登記、§49.13 結果） | 留出 free exact 與 ranking 的 Wilson 下界都高過最強 surface baseline 的上界 **0.2500**，且 `reset`／撤回／常數三條控制照登記方向 |
| — | **推理（2026-11-13）**：**儀器封頂，沒有任何推理宣稱**。同一個 `GRUCore`／`CoreState` v1 從 L 的 checkpoint 出發（G1 鎖檔案 sha256 與訓練後 hash）、800 段 11 輪口供、20 epochs、xpu **3,200.6 s**：留出 free exact **0.0850**（17/200）、ranking **0.1650**（chance 0.1591、surface 上界 0.2500），train exact **0.1150** → G3 不過。**三個讀數**：① 17/200 就是常數 `Kevin` 在留出的出現次數（訓練集邊際眾數；逐鏈 4/54、5/52、4/46、4/48 也剛好是它）；② 答案的 loss **2.526 nats** ≈ 12 個名字的熵（留出 2.4641、`ln 12` = 2.4849）→ 預測沒有條件於輸入；③ `full`、`reset`（問前歸零）、`skip_al`（不呼叫 `al_step`）的 200 題預測**逐位元組相同**，`changed_rate` 0.0。格式對照 0.0650／0.1550（G8 PASS）→ 不是格式。依 §49.7 這是「儀器封頂」分支：後面的數字都是上限，不是「推理失敗」。**下一個變數是過擬合校準**（32–64 段訓練集要接近 1.0），不是先加選取結構。**核心分仍 0.00/10**。**接著（2026-11-14，§50 Q1）**：過擬合校準**失敗**——32 段、100 epochs、輔助讀出 λ=1，train exact **0.1562**（5/32，正好是常數 `David` 的邊際），λ=0 的配對診斷也只有 **0.2188**；輔助讀出確實讓**每一輪**都拿到梯度（測試釘住：λ=0 時第 0–1 輪恰好 0），所以失敗點在**信用分配之後**——訊號到了，模型仍背不起 32 段。依登記停損，完整臂**沒有跑**，也沒有事後調 epochs／lr／寬度。這不證明路徑長度不重要，只證明它不是唯一的阻礙；**接著（§50.13 狀態探針）量到瓶頸在表徵**：對第 6–10 輪的 `h` 用 800 段擬合線性讀出、在 200 段留出上評分，三個載體（stage-L／λ=1／λ=0）**每一個邊界都在 chance**（0.055–0.140，chance 0.0833，null 0.040–0.105），但同一支探針讀「線索鏈」在同樣邊界是 **1.000**（第 5、7 輪）→ 探針有效，是**答案不在 state 裡**，而且第 9–10 輪連主題都讀不到。**接著（§51 階段 R）**：只把輔助項改成「只在 `derive()` 已有唯一答案的邊界監督」（32 段上第 0–5 輪 0 個、第 6 輪 16 個、第 7–9 輪各 32 個），R1 校準仍是 **FAIL**：train exact **0.2500**（8/32，`Ivan` 0.5625；門檻 0.90），依 §51.5 的否證條件（≤0.30）「空邊界監督」被排除為原因，完整臂不跑、四個超參數不調；但它沒有像 Q1 那樣在第 50 個 epoch 平掉（main 0.4170→0.3788→0.3609），main 2.026 nats/session 只比邊際低 0.343 → 失敗點仍在表徵。**接著（§52–§53 階段 S，容量階梯）**：固定 400 步、只變要背的段數，儀器在 1／4 段是 **1.00**（4 段有 4 個不同名字，不是常數），8 段 **7/8＝0.875**、16 段 **7/16＝0.4375** → 斷點 N\*=8；8 段的 4× 步（1,600）**PASS 8/8**，但 32 段的 1,600 步 **12/32＝0.375**、2× 寬（hidden 256，330,563 參數）**10/32＝0.3125**（`Kevin` 被預測 18 次、只有 4 個不同名字）→ 依 §52.4 判定**不是步數、不是寬度**，下一個變數是**接線**（per-turn 讀寫／同一 `CoreState` 的工作記憶槽），並由這個量測背書；核心分仍 0.00/10 | `scripts/train_pantry_deduction.py` 的三份報告 `all_pass=False`（如實）；`tests/test_pantry_deduction.py` **53 條綠**；`scripts/probe_credit_assignment.py --state-probe`（`tests/test_credit_assignment.py` **12 條綠**）；`LAYER_REGISTRY.json` 的 `stateful_core_pantry_deduction` 為 `fail`（Q1 校準／狀態探針／S 階梯亦記入） |

**停損**：

- P1 若 T1 沒有下降 → 先修模型／訓練，不是加大 state。
- P2 若 SNN 在 T1–T6 全過但能力仍落後 → 它可以是效率線，不是能力線。
- P4 若生產路徑仍需要 `state_for_llm` 才能運作 → 那還是 prompt 路線，不能宣稱
  「同一個模型」。

---

## 10. 反模式清單（看到就退）

1. 把 AL 狀態寫成文字放進 prompt，再說「AI+AL 在同一個模型」。
2. 用 KV cache 當 persistent state。
3. 每回合 `init_state()`／每次生成重建 state。
4. AI 一個模型、AL 一個模型，中間用 JSON／文字／事件橋接。
5. 讓 `StateMatrix` 成為唯一真相，模型只讀它的文字。
6. 在獨立 pairs 上訓練，卻宣稱跨回合狀態。
7. 只用「輸出有變」當證據，沒有 ablation／restart／cycle-switch。
8. 為了讓測試過而加大 state、調低門檻、或把 held-out 併回訓練。
9. AL 背景迴圈與 AI 同時寫 state，沒有鎖或版本檢查。
10. 把時鐘／振盪器（慢變量）誤當成模型學到的 state；它們是輸入，不是本體。
11. 把 GRU／Transformer 接上就宣稱核心，卻沒有 provenance 與正確認證。
12. 把「核心分」拿去平均 prompt／檢索／工具的分數。

---

## 11. 審查清單（PR／實驗前逐項打勾）

- [ ] 這次改動有沒有一個 `weights_hash`？有沒有一個 state 物件？
- [ ] core 路徑的 prompt 是否完全沒有 state 文字？
- [ ] `ai_step`／`al_step` 是否共用同一組權重？
- [ ] state 是否固定大小、可存檔、有 schema／hash／版本？
- [ ] 是否每回合都重置？（是 → 退回）
- [ ] 是否有 T1（ablation）、T4（restart）、T5（cycle switch）？
- [ ] baseline 是否有 stateless／state-in-prompt／hand-state 三組？
- [ ] provenance 是否記錄 model、state_version、ticks、route？
- [ ] 是否在 held-out 上調任何東西？（是 → 退回）
- [ ] 文件是否區分 memory／state／context／observable？

---

## 12. 檔案地圖與指令（提案，随實作更新）

**新增（P1）**

- `apps/backend/src/ai/core/core_state.py`：schema、save/load、hash、版本
  ——**P0 已建立**（見下方「P0 現況」）。
- `apps/backend/src/ai/core/core_step.py`：`ai_step`／`al_step` protocol、時間切段、registry
  ——**P1 已建立**（純 stdlib，不含模型）。
- `apps/backend/src/ai/core/stateful_decoder.py`：所有臂共用 `StatefulCore`（同一個 state
  物件／`weights_hash`／checkpoint）——`GRUCore`（**P1 第一臂**）、`SSMCore`（**P3 臂**，
  `h ← h·exp(-dt/τ)`、線性讀出）、`SlotMemoryCore`（**§46 的第七輪臂**：同一個 GRU ＋
  四個 gate 寫入、attention 讀取的槽；`model_kind="slots"`）；SNN 臂仍未接。

**修改**

- `apps/backend/src/ai/ed3n/token_snn.py`：`generate(prompt, state=None) -> (text, state)`。
- `apps/backend/src/services/llm/generation_gate.py`：`stateful` 能力旗標。
- `apps/backend/src/api/routes/chat_routes.py`：core 路徑傳 state 物件；`state_for_llm`
  只給 fallback。
- `apps/backend/src/services/llm/prompt_builder.py`：fallback 專用，標 `route=prompt`。

**測試／量測**

- `tests/ai/test_core_state_contract.py`：schema、hash、版本、原子寫入、拒絕載入
  ——**P0 已建立，15 條通過**（P1 追加「存檔拒絕非 numpy 張量」1 條）。
- `tests/ai/test_state_cycles.py`：`dt=0` 恆等、per-sample 更新、save/load 同 logits、
  weights hash、半群**只量不判**、等段數產生器——**P1 已建立，21 條**。
- `scripts/probe_state_cycles.py`：T1–T6 的合成多回合 probe——**P1 已建立**；`--round 2`
  是等段數重跑。預登記在 `CORE_GAP_ANALYSIS.md` §37／§38，結果見 §37.6／§38.4。
- `scripts/probe_state_restart.py`：**跨進程** restart（P3 的 T4 第二半）——`--phase
  capture` 在新行程存權重＋查詢前的 state，`--phase resume` 在**另一個**新行程只靠檔案
  重跑；同時驗「另一臂的 state／被改寫的 state／接到錯的臂」三種拒絕。結果見
  `CORE_GAP_ANALYSIS.md` §40.8：兩臂 Δp = 0、歸零 state 差 0.91（GRU）／0.99（SSM）。
- `tests/ai/test_state_restart.py`：上面那條的機制測試（煙霧預算，驗 Δp、hash、ticks、
  三種拒絕；**不**驗「歸零 state 差異」，那需要訓練過的核心）。
- `apps/backend/src/ai/core/stateful_runtime.py`：**P4 的生產綁定**（opt-in、預設關），
  **P5 加上 R3 的三道鎖與所有權**。`ChatCoreRuntime` 每回合推進一次 state 物件並存檔；
  每 session 一個狀態目錄（id 的 digest），共用同一份權重；`availability()` 說明為何不可用
  （未開啟／沒有 checkpoint／上次載入失敗）並回報 `lock`／`multi_writer_safe`；
  `advance()` 在任何拒絕路徑都回 `None` 且**不改動**既有狀態檔，`last_refusal` 說明是哪一種
  拒絕（同一個 `None` 可能是「沒有 checkpoint」「檔案被改」「版本輸了」「主人不符」）。
- `apps/backend/src/services/llm/generation_gate.py` 的 `STATEFUL_BACKENDS`／
  `stateful_core_active()`：連續性是**另一種能力**，`stateful-core` **不在**
  `GENERATIVE_BACKENDS` 裡（它不能吃提示改寫，放進去就會讓模板答案被記在模型頭上）。
- `scripts/probe_core_turns.py`：**P5 的回合量測**。走真正的 `_handle_chat_request`，把凍結
  標準集整輪整輪地跑（不截斷最後一輪，否則尾端 stratum 會無故缺額），每個 stratum 一個
  session，逐回合寫 JSONL 到 `data/core_turns/`（gitignored）。gate：回合數、零拒絕、版本嚴格
  遞增、五個 stratum 都在。它量的是**載體**，不是能力——回覆仍由表層產生。
- `tests/test_probe_core_turns.py`（8 條）：上面那個 gate 自己的測試（掉一次更新／一次拒絕／
  少一個 stratum 都必須讓 `all_pass=False`），以及「整輪不截斷」與可重現性。
- `scripts/train_state_content.py`：**§43–§44 的內容量測**。教一個配對、跨 `al_step(120 s)`、
  再用問題生成答案；四種量測各有一個可以失敗的對照（零狀態 ablation 用**同一個** state
  物件只把 `h` 歸零、`cold` 是同一批題目跳過教學回合、`wrong_name` 分開「值被攜帶」與
  「配對被使用」），另加 teacher-forced 與只讀 `h` 的線性 probe 兩個診斷，用來說明資訊是
  「沒存進去」還是「存了但讀不出來」。報告與 checkpoint 寫到 `data/state_content/`
  （gitignored）。
- `tests/test_state_content_task.py`（13 條）：那個任務自己的契約——洩漏偵測器被**故意餵壞**
  一次（重用值／訓練過的名字）、`cold` 必須與 held-out 同一批題目、重跑可重現、答案不在
  問句裡、損失從答案的第一個字元開始、零狀態真的把 `h` 歸零而**不換物件也不換權重**。
- `scripts/train_state_binding.py`：**§45 的兩組配對量測**。兩個教學回合（各一次 `ai_step`／
  `al_step(120 s)`）、一個查詢、生成該鍵的值；唯一變數是目標（`single` 只訓練被抽中的
  那一組、`both` 兩組都訓練且各自從**全新的 state** 出發，所以兩臂的差別沒有序列佈局）。
  checkpoint 以**最低 dev 答案損失**選，不以 exact 選（exact 是階躍函數，`--patience 0`
  單獨修不好這件事）。診斷：`h` 對兩個槽與「被問的那組」的線性 probe、`by_ask`、
  `other_value_rate`、`wrong_name.taught_value_rate`、`both_sequential`。**§46 追加**
  `--core slots`（可定址 store）／`--no-memory`（同參數的消融）／`--control`（把對照報告
  讀回來，B7 的消融差與 B8 的參數匹配才可能算得出來；資料 digest 不符就拒絕），以及
  `addressing_diagnostics`（兩個問題讀到同不同格）——消融臂沒有 attention 權重，回
  `applicable: false` 而不崩潰。
- `scripts/train_text_stage.py`：**§47 的文字階段（L）**。byte 詞表（259：`<pad>`／
  `<bos>`／`<eos>` ＋ 256 bytes）、**同一個** `GRUCore` 與 `CoreState` v1、128-byte 窗、
  每 4096 bytes 重置 state；floor 是**算出來的**內插 bigram／trigram（權重在訓練尾巴選），
  L3 比的是同一個 trigram 的貪心續寫，L4 是「同一份權重、每個窗重置 state」，L5 在
  `--check` 裡也會真的把 checkpoint 載回同一個類別。語料是 core_train／core_val 的前
  N bytes ＋ pantry v2 證詞（登記的位元組數在執行時比對，不符就中止）。
- `tests/test_text_stage.py`（22 條）：詞表對 256 個 byte 可逆、loader 只切整行、floor 是
  機率分布且 λ 只在訓練尾巴選、gate 由記錄的數字重算、`--check` 對竄改／缺 checkpoint
  都會失敗、洩漏的 camera tag 在訓練前就中止。
- `scripts/train_pantry_deduction.py`：**§49 的 pantry 推理（P）**，從 L 的 checkpoint
  出發（G1 鎖檔案 sha256 與訓練後 hash）。11 個 turn 逐輪 `ai_step`、輪間
  `al_step(turn["dt_s"])`，目標只有兇手名字的 4–5 bytes ＋ `\n`；正解、前綴解、每個消融解
  都由產生器的 `derive()` 算出來，不由人手指定。G8 的格式對照（同文字、同步數、答案換成
  隨機的另一個人）是**另一支臂**，計分臂在它完成前拒絕啟動。
- `tests/test_pantry_deduction.py`（53 條）：語料兩份 digest 與 L 相同、逐輪 runner 與
  `ai_step`＋`al_step` 逐位相同（含 `state_version`／`ticks`）、批次不改變單筆 state、
  重置臂只看最後一輪、前綴在 **98** 題上是陷阱、格式對照永遠不是兇手、gate 由數字重算、
  `verdict` 只數布林、smoke 報告不會被當成對照；§52 之後再加上：`--gate-prefix` 只收單一
  大寫字母（報告與 `--check` 用同一個前綴）、`--widen-to` 的起點必須是「L 或 L 的行為等價
  加寬」（新單元零接線，`h[:128]` 與 logits 逐步相同），以及 CLI 拒絕 `--widen-to 128`、
  同時給 `--hidden` 或改 `--emb` 的組合。
- `scripts/train_pantry_deduction.py --widen-to 256`：**§52.4 的寬度 rung**。L 是 128 寬，
  `load_weights(strict_config=True)` 會拒絕把 128 載進 256，所以加寬不是換一個新的隨機
  載體，而是把 L 的 block 複製、新單元零接線（`cell.weight_hh` 的新欄、`head` 的新欄為 0），
  使起點的函數與 L 相同、只多出容量。`start_is_stage_l` 是 G1 與 `--check` 共用的唯一判定。
- `scripts/probe_credit_assignment.py`：**§49.16 的儀器診斷**（不是能力量測、沒有門檻）。
  沿用 driver 的 tokenisation 與 `_answer_loss`，逐輪保留 `h`、一次 backward，報每一輪的
  `|dL/dh|`、最早越過 `1e-6` 的一輪、往回的每輪縮小倍率；兩臂（L 的載體／P 的 checkpoint）
  同一次執行。
- `tests/test_credit_assignment.py`（6 條）：前置傳播與 `run_session` 逐位相同、reach 取
  最早越線的一輪、全在 floor 下時回 `None` 而不是 0、縮小倍率是往回量、floor 必須為正、
  玩具模型上梯度也到不了前面的輪。
- `tests/test_state_binding_task.py`（40 條）：洩漏偵測器被故意餵壞（重用值／訓練過的名字／
  `wrong_name` 竟然問到教過的 key／`ask` 越界）、`cold` 與 held-out 同題、兩個教學回合是
  **兩個**各自只帶一個值的序列、兩個 `ask` 位置都出現、`_teach` 真的是兩次 `ai_step` 加兩次
  `al_step`、checkpoint 選擇用的是連續訊號、消融臂的診斷回 `applicable: false` 而不是
  崩潰、判定只數布林門檻（數字不是門檻）。
- `tests/ai/test_stateful_runtime.py`（27 條）＋ `tests/services/test_memory_handoff.py`
  的兩條能力邊界測試：開關預設關、沒有 checkpoint 不建目錄、兩回合推進、session 互不
  汙染、restart 續接、三種拒絕（毀損／換權重）且檔案位元組不變、prompt 端不再發布
  `state_for_llm`、回覆 provenance 記 `core`／`none`、關閉時回覆形狀不變、「有 checkpoint 但還沒載入」不算承載連續性（載入失敗時不得把 prompt 載體關掉卻什麼都不補）。

### P0 現況（2026-11-12，已實作，未改任何行為）

`ai/core/core_state.py` 只做「一個 state 怎麼被描述、存、驗、載」：

- `CoreState.create()` 是唯一重置點（契約 R5）；`bump()` 讓 `state_version` 單調遞增。
- `save()` 先張量、後 `meta.json`；checksum 同時涵蓋兩者，崩潰殘檔會在載入時被拒絕。
- `load()` 在檔案缺失、schema 不符、`weights_hash` 不符、checksum 不符時**一律拋錯**，
  不建立空狀態。張量用 `.npz`＋`allow_pickle=False`，meta 用 JSON。
- `derived` 不落盤（meta 的鍵集合被測試釘住）；單一 session ≤ 10 MB，超過拋錯不截斷。

**當時尚未做（P1 才做）**：per-session 鎖與樂觀鎖（R3 的並發部分）、`ai_step`／`al_step`、
跨回合訓練、T1–T6。所以 P0 綠燈**不代表**「模型在用 state」。

（R3 的並發部分後來在 P5 補上：per-session 執行緒條帶 ＋ `flock`／`msvcrt` 檔案鎖 ＋
存檔前版本比對，見 §9 的 P5 列與 `CORE_GAP_ANALYSIS.md` §42。`core_state.py` 本身仍只提供
「原子寫入＋拒絕載入」，鎖在它的呼叫者身上。）

**指令**

```bash
# P0／P1 第一臂：已可執行
./.venv/bin/python -m pytest tests/ai/test_core_state_contract.py tests/ai/test_state_cycles.py -q
./.venv/bin/python scripts/probe_state_cycles.py --seeds 0 1 2 3 4

# 跨進程 restart（T4 的第二半；兩臂 Δp = 0，三個拒絕檢查全過）
./.venv/bin/python scripts/probe_state_restart.py
./.venv/bin/python -m pytest tests/ai/test_state_restart.py -q

# P4：opt-in 的生產接線（預設關；核心只承載狀態，不寫回覆）
./.venv/bin/python -m pytest tests/ai/test_stateful_runtime.py -q
ANGELA_STATEFUL_CORE=1 ANGELA_STATEFUL_CORE_DIR=data/core_state \
    ./.venv/bin/python -c "from ai.core.stateful_runtime import get_runtime; print(get_runtime().availability())"

# P5：2,208 回合的真實路徑量測（沙盒；約 26 分鐘；gate 不過就 exit 1）
./.venv/bin/python scripts/probe_core_turns.py --turns 2000
./.venv/bin/python -m pytest tests/test_probe_core_turns.py -q

# R3：跨進程鎖真的會擋（測試裡用一個持有 flock 的 subprocess）
./.venv/bin/python -m pytest tests/ai/test_stateful_runtime.py -q -k "lock or owner or version"
```

---

## 13. 變更紀錄

- 2026-11-12：建立。動機：§36 的 SNN/GRU 對照只量了單回合 mapping；使用者指出
  「狀態走上下文」與「AI/AL 分成兩個實體」會重複狀態問題。本契約把核心定義為
  **同一份權重＋同一個 state＋兩個 step**，並把 observable 降為投影。
- 2026-11-12（P0）：`ai/core/core_state.py` ＋ `tests/ai/test_core_state_contract.py`
  （14 條；P1 追加 1 條後為 15 條）。只定 schema 與拒絕規則，不接生產、不改行為；
  `ai_step`／`al_step` 仍是 P1。
- 2026-11-12（P1 第一臂）：`ai/core/core_step.py`（切段規則）、`ai/core/stateful_decoder.py`
  （同一個 `GRUCell` 兩個入口，per-sample `dt`，用完的樣本不再被零輸入推動）、
  `scripts/probe_state_cycles.py`（T1–T6）、`tests/ai/test_state_cycles.py`（25 條）。
  預登記（§37.4–§37.5）在跑之前寫定，登記 run **17/17 通過**：state 被 `al_step` 使用，
  且 T1 偵測得到；hand-state 對照組在同一 T1 下不受影響（測試有鑑別力）。
  2026-11-12（§38 等段數）：每 session 固定 8 個 chunk 後重跑，**18/18 通過**，主臂
  1.0000、歸零 0.4986——「數更新次數」的捷徑排除。半群在該輪 0.9180（仍未成立）。
  2026-11-12（§39 `L_al`）：λ=0.5、只教 (25,25)、量 (30,30)／(20,40)；半群差縮小
  12–24 倍（1.66–1.88 → 0.069–0.140），但未達登記的 1e-2，**3 項 FAIL**。最後 batch 的
  loss 1.4e-5 與 held-out 的 6.9e-2 並列，說明約束只作用在當前狀態分布。否定結果照實記，
  不調 λ；P3（SSM）是下一步。
  2026-11-12（P4 接線）：`stateful_runtime.py` 把「每回合推進同一個 state 物件」接進
  `chat_routes._handle_chat_request`，並在 `_ctx_state_matrix` 停止把 state 發布成 prompt
  文字；**opt-in、預設關**，預設回覆形狀不變。回覆 provenance 記 `state_source`
  （`core`／`none`）與 `core_state`。核心**不生成回覆**——目前沒有能生成開放域文字的核心，
  所以這是「載體正確」而不是「載體被讀回生成」。核心分仍 0.00/10。
  過程中修掉兩個真缺陷：`CoreState.load` 交回 numpy（必須 `attach_state` 才能步進）、
  以及 `last_update` 是 UTC 卻用 `time.mktime`（本地時區）解析，會把每個 gap 多算
  8 小時（改 `calendar.timegm`，測試釘住 epoch 0）。
  2026-11-12（§40.8 跨進程 restart）：新的 `probe_state_restart.py` 在**兩個新行程**之間
  傳遞權重檔＋狀態檔，兩臂 Δp = 0.000e+00、`ticks`／`state_version`／`last_dt_s`／hash
  全部保留、歸零 state 差 0.9063（GRU）／0.9904（SSM）。順手修掉真缺陷：
  `attach_state()` 原本**不檢查** `model_kind`／`weights_hash`，同尺寸（hidden=64）時會
  安靜接受另一臂的 state；現在兩項都驗並丟 `CoreStateInvalid`（+2 測試）。
  2026-11-12（§40.7 成本）：`train_arm` 的單步抽成 `_train_step()`（登記 run 重跑逐位
  相同），`--cost` 量同一份工作；SSM/GRU = 0.217 參數、0.239 checkpoint、0.55 forward、
  0.45 訓練步（三次獨立 run，差 ≤3%）。桌面機、負載 3.6–4.7，不是專用 benchmark 機。
  2026-11-12（§40 SSM 臂）：`StatefulCore` 收攏 state／hash／checkpoint；`SSMCore`
  （對角 decay、per-dim log-spaced `τ`、線性讀出）在**沒有** `L_al` 下 21/21 通過，
  半群 1.9–3.8e-6（架構保證）、T3／T5 與 GRU 同分。**這是 P3 候選，不是能力提升**；
  成本未乾淨量測，P4 未開始。
  **限制照實記**：合成任務、同進程 restart（§40.8 已補上跨進程）；§37／§38 的半群未成立（0.7588／0.9180），
  §39 把它縮小 12–24 倍但仍未達 1e-2，§40 靠架構讓它精確；核心分不變（0.00/10），
  生產路徑未接。

- 2026-11-13（P5）：量產級的三件事。① **R3 的三道鎖**：per-session 執行緒條帶
  （固定 64 條，不做淘汰——淘汰掉一個正在被持有的鎖會讓同一 session 出現兩個鎖）、
  session 目錄的 advisory 檔案鎖（POSIX `flock`／Windows `msvcrt`，`LOCK_NB` 輪詢、
  上限 2 秒）、以及**存檔前的版本比對**。第三道能抓到前兩道抓不到的寫入者（工具、手改、
  舊版建置），測試用一次**合法**存檔（有效 checksum）的干擾寫入證明不能只靠 checksum。
  `availability()` 回報 `lock`／`multi_writer_safe`；沒有檔案鎖的主機記一次 warning 並
  只允許單一 worker。② **所有權**：`advance(user_id=...)` 在新狀態記下主人，續接時主人
  不符就拒絕（session id 可猜）；空主人的舊狀態接受（§41 的 state 不能回溯作廢）。
  `last_refusal` 說明是哪一種拒絕。③ **回合量**：`scripts/probe_core_turns.py` 走真正的
  `_handle_chat_request`，2,208 回合（五個 stratum 各一個 session），逐回合記
  `state_source`／`ticks`／`state_version`／`dt_s`，gate 含「版本嚴格遞增」（掉一次更新就紅）。
  **沒變的**：核心不生成回覆，`schema_version` 只有 v1（不符拒絕，**沒有** migration），
  核心分仍 0.00/10。結果與限制見 `CORE_GAP_ANALYSIS.md` §42。

- 2026-11-13（內容，§43–§44）：前面每一輪量的都是**載體**。這一輪問的是「state 裡裝的
  東西有沒有語言內容、生成會不會讀它」——那是核心分 0.00 的**前置條件**，不是分數本身。
  任務：教 `remember <name> = <value> .`（不計損失）→ `al_step(120 s)` → 問 `<name> ?`
  → 生成 `<value> .`；答案是**兩次 `ai_step`**、不是兩句接成一個序列，第二回合的輸入裡
  沒有值，所以 state 是唯一通道。所有非 train 切分都由**訓練沒看過的字串**組成，洩漏
  檢查是機械的（值交集、名字交集、train 內重複、字母表外的字元）。
  **實測**（`--seed 20261114 --epochs 60 --patience 0`，81,765 參數，271.6 秒，XPU）：
  `heldout_names` exact **0.995**、`dev` 0.994、零狀態 ablation **0.000**、`cold`
  **0.000**、teacher-forced 0.999、只讀 `h` 的線性 probe 0.851。checkpoint 重載後
  數字相同。
  **照實記的邊界**：`wrong_name` **0.994**（名字沒有被使用 → 單槽攜帶，不是鍵值查詢）、
  拿掉 `al_step` 掉到 **0.003**（不是間隙不變）、封閉 CV 音節不是語言、**沒有接進生產**。
  §43 的登記 run 先 FAIL（dev 0.001）並被判定為**協定缺陷**（早停看階躍的 exact），
  §44 只改訓練長度與早停、門檻逐字不動、換一個沒用過的資料 seed 重跑——不是回頭改
  登記的次數。核心分**不變**（0.00/10）。結果見 `CORE_GAP_ANALYSIS.md` §43／§44。

- 2026-11-13（兩組，§45）：上一輪證明了「state 裡有內容」，但它自己量到的 `wrong_name` 0.994
  說明那只是**單槽緩衝區**（教 A、問沒教過的 B 還是回 A 的值），名字沒有被使用。這一輪問
  「能不能同時持**兩組**、由查詢選一組」。任務：兩個教學回合（各一次 `ai_step` ＋
  `al_step(120 s)`）→ 問 `<name A> ?` 或 `<name B> ?` → 生成 `<value> .`；單槽在這個任務上
  的上限是 0.5，所以高於 0.5 只能來自選對。唯一變數是**目標**（`single` 只算被抽中那組、
  `both` 兩組都算且各自從全新 state 出發）。
  **實測**（登記 `d9aacbc5e`、seed 20261115、100 epochs、81,765 參數）：`single`
  held-out exact **0.0033**、`both` **0.0100**（門檻 0.30）→ **FAIL**；零狀態與冷啟 0.000。
  **同一個臂、同一個 seed 的單組對照 C1 是 1.000**（probe 0.874），所以不是臂或 seed 壞了。
  `h` 的線性 probe 對兩個槽都只有 0.32–0.41 字元（chance 0.027）→ **沒寫進去**，不是選不出來。
  已排除：目標（兩臂排序在兩個 seed 上翻轉）、寬度（256 寬：訓練損失 0.196、held-out 0.057）。
  **陷阱照實記**：`other_value_rate` 低（0.002–0.004）不代表「不賭」，是因為兩組的值都沒
  答出來——所以 B5 同時要求兩個 `by_ask ≥ 0.50`。結論是設計要求（可定址的槽／注意力），
  不是預算。核心分**不變**（0.00/10）。結果見 `CORE_GAP_ANALYSIS.md` §45。
