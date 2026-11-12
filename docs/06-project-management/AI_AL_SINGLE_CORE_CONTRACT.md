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
| — | **P0 狀態（2026-11-12）**：完成。`ai/core/core_state.py` ＋ 14 條 schema／拒絕載入測試；**行為未改**。 | `pytest tests/ai/test_core_state_contract.py` 綠；`mypy` 0 error |
| **P1** | 用 GRU 實作 `CoreState`＋`ai_step`／`al_step`；合成多回合資料；跑 T1–T6 | T1 有顯著下降、T4 一致、T5 對照組不變 |
| **P2** | 把同一契約接到 SNN（先修梯度帶）；與 GRU 同預算比較 | 同參數同步數下可訓練；T1–T6 過 |
| **P3** | SSM 原型（dt 原生） | 在 T3／T5 上優於或等於 GRU；成本可接受 |
| **P4** | 接生產：`generation_gate` 加 `stateful`；`chat_routes` 傳 state 物件；`state_for_llm` 只給 fallback | 生產路徑不再把 state 寫進 core prompt；provenance 正確 |
| **P5** | 量產級：per-user 持久化、重啟、版本遷移、成本 | 文件與分數同步；核心分只在模型產生時變動 |

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
- `apps/backend/src/ai/core/stateful_decoder.py`：GRU adapter（同一個 `GRUCell` 兩個入口）
  ——**P1 第一臂已建立**；SNN 臂仍未接。

**修改**

- `apps/backend/src/ai/ed3n/token_snn.py`：`generate(prompt, state=None) -> (text, state)`。
- `apps/backend/src/services/llm/generation_gate.py`：`stateful` 能力旗標。
- `apps/backend/src/api/routes/chat_routes.py`：core 路徑傳 state 物件；`state_for_llm`
  只給 fallback。
- `apps/backend/src/services/llm/prompt_builder.py`：fallback 專用，標 `route=prompt`。

**測試／量測**

- `tests/ai/test_core_state_contract.py`：schema、hash、版本、原子寫入、拒絕載入
  ——**P0 已建立，14 條通過**。
- `tests/ai/test_state_cycles.py`：`dt=0` 恆等、per-sample 更新、save/load 同 logits、
  weights hash、半群**只量不判**——**P1 已建立，17 條**。
- `scripts/probe_state_cycles.py`：T1–T6 的合成多回合 probe——**P1 已建立**；預登記在
  `CORE_GAP_ANALYSIS.md` §37，結果見 §37.6。
- `scripts/probe_state_restart.py`：跨進程 save/load（**尚未建立**；T4 目前用同進程的
  `CoreState.save`／`load`，跨進程版是後續）。

### P0 現況（2026-11-12，已實作，未改任何行為）

`ai/core/core_state.py` 只做「一個 state 怎麼被描述、存、驗、載」：

- `CoreState.create()` 是唯一重置點（契約 R5）；`bump()` 讓 `state_version` 單調遞增。
- `save()` 先張量、後 `meta.json`；checksum 同時涵蓋兩者，崩潰殘檔會在載入時被拒絕。
- `load()` 在檔案缺失、schema 不符、`weights_hash` 不符、checksum 不符時**一律拋錯**，
  不建立空狀態。張量用 `.npz`＋`allow_pickle=False`，meta 用 JSON。
- `derived` 不落盤（meta 的鍵集合被測試釘住）；單一 session ≤ 10 MB，超過拋錯不截斷。

**尚未做（P1 才做）**：per-session 鎖與樂觀鎖（R3 的並發部分）、`ai_step`／`al_step`、
跨回合訓練、T1–T6。所以 P0 綠燈**不代表**「模型在用 state」。

**指令**

```bash
# P0／P1 第一臂：已可執行
./.venv/bin/python -m pytest tests/ai/test_core_state_contract.py tests/ai/test_state_cycles.py -q
./.venv/bin/python scripts/probe_state_cycles.py --seeds 0 1 2 3 4

# 尚未建立（跨進程重啟版；T4 目前用同進程 CoreState.save／load）
# ./.venv/bin/python scripts/probe_state_restart.py
```

---

## 13. 變更紀錄

- 2026-11-12：建立。動機：§36 的 SNN/GRU 對照只量了單回合 mapping；使用者指出
  「狀態走上下文」與「AI/AL 分成兩個實體」會重複狀態問題。本契約把核心定義為
  **同一份權重＋同一個 state＋兩個 step**，並把 observable 降為投影。
- 2026-11-12（P0）：`ai/core/core_state.py` ＋ `tests/ai/test_core_state_contract.py`
  （14 條）。只定 schema 與拒絕規則，不接生產、不改行為；`ai_step`／`al_step` 仍是 P1。
