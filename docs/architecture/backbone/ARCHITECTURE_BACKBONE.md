<!--
  =============================================================================
  FILE_HASH: TBD
  FILE_PATH: docs/architecture/backbone/ARCHITECTURE_BACKBONE.md
  FILE_TYPE: architecture-design
  PURPOSE: 主幹線 (Backbone) 架構設計 — 核心矩陣 ↔ 自由矩陣 ↔ 多模態字典 ↔ CLI/前端
          之統一接線層設計，含現有元件完整盤點與增量演進策略。
  VERSION: 7.5.0-dev
  STATUS: draft (design — before implementation)
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-08-09
  AUDIENCE: architects, developers, agents
  =============================================================================
-->

# 主幹線 (Backbone) 架構設計文件

> **狀態**: 設計稿（實作前）。本文件先完整定義目標架構與現有盤點，**確認後才動手**。

---

## 1. 背景與動機

專案目前的核心矩陣 (`StateMatrix4D`)、自由矩陣 (`SharedLatentSpace`)、多模態字典
(`DictionaryLayer` / `VectorDictionary`)、核心模組、CLI/前端都已存在，但**彼此之間
的接線是散落、ad-hoc 的**：

- `api/routes/chat_routes.py` 內有 **9 個手動 fallback 工廠**（`_get_ed3n_engine`、
  `_get_bio_integrator`、`_get_lifecycle`、`_get_state_matrix` …），各自 `try/except`
  回退建單例，狀態不一致風險高。
- 全專案共有 **~130 個 `_get_*` / `get_*` 單例工廠**分散在 40+ 檔案，無統一註冊點。
- 轉譯層分裂為兩套：`ai/bridge/neural_bridge.py`（StateMatrix↔SNN key 對映）與
  `ai/multimodal/semantic_key_mapper.py`（latent↔key 對映），API 不一致。
- 座標軸分裂在 4 個檔案（`core/state/axis.py`、`axis_field.py`、`eta_axis.py`、
  `axis_port_registry.py`），與核心矩陣無統一介面。
- **沒有「主幹線」這個概念** — 缺少一個統一接線層，同時負責：元件註冊、輸入輸出傳遞、
  狀態傳遞、轉譯、配置設定傳遞。

本設計引入一個**薄主幹線層**（不加厚、不重寫），將既有元件的接線收斂，並支援
自由矩陣的**按需掛載/釋放（memory ↔ disk）**。

---

## 2. 目標架構總覽

```
┌──────────────────────────────────────────────────────────────────────┐
│                     外部世界 (External World)                         │
│  LLM providers (openai/anthropic/google/ollama/llamacpp) ·           │
│  weather · google-drive · web-search · atlassian · OS bridge · MCP   │
│  (一律經主幹線「外部閘道」進出，元件不得直接呼叫)                       │
└───────────────▲───────────────────────────────▲──────────────────────┘
                │ outbound (轉譯+重試+熔斷)       │ response/學習來源
┌───────────────┴───────────────────────────────┴──────────────────────┐
│                     CLI / 前端 / 外部呼叫者                            │
│   packages/cli · apps/backend/src/cli/repl.py · desktop-app ·        │
│   web-dashboard · web-live2d-viewer · gemini-os-bridge · MCP         │
└───────────────▲───────────────────────────────▲──────────────────────┘
                │ HTTP / WS / IPC                │ config/settings
┌───────────────┴───────────────────────────────┴──────────────────────┐
│  主幹線 · 下層  (Lower Backbone)                                     │
│  「入口/出口層」: 接收外部輸入 → 轉給中層；回傳輸出                     │
│  · 輸入輸出契約 (I/O Contract)                                       │
│  · 配置設定傳遞 (Config & Settings passing)                           │
└───────────────▲───────────────────────────────▲──────────────────────┘
                │ state updates                  │ config
┌───────────────┴───────────────────────────────┴──────────────────────┐
│  主幹線 · 中層  (Middle Backbone)                                     │
│  「字典/模組層」: 多模態字典、核心模組、轉譯器                          │
│  · 多模態字典註冊 (MultimodalDictionary registry)                    │
│  · 轉譯器註冊 (Translator registry)                                  │
│  · 核心模組註冊 (Module registry)                                    │
└───────────────▲───────────────────────────────▲──────────────────────┘
                │ translated I/O                  │ state/config
┌───────────────┴───────────────────────────────┴──────────────────────┐
│  主幹線 · 上層  (Upper Backbone)                                     │
│  「矩陣/座標軸層」: 核心矩陣 ↔ 自由矩陣 之統一接線與轉譯                │
│  · 核心矩陣 (Core Matrix): StateMatrix4D                            │
│  · 自由矩陣 (Free Matrix): SharedLatentSpace + 掛載/釋放              │
│  · 座標軸 (Axes): 統一座標軸介面                                      │
└───────────────▲───────────────────────────────▲──────────────────────┘
                │ axis reads/writes              │
┌───────────────┴───────────────────────────────┴──────────────────────┐
│  核心狀態 (GlobalStateStore / CNS EventBus)                          │
│  領域狀態、事件廣播、持久化後端                                        │
└──────────────────────────────────────────────────────────────────────┘
```

**核心概念**：所有跨元件溝通（輸入輸出、狀態、轉譯、配置）**都必須**經過主幹線，
元件之間不得直接互相依賴。主幹線是唯一註冊/解析中心，但不是厚服務層 — 它只做
**路由 + 轉譯 + 契約檢查**，實際計算仍由各元件自己完成。

---

## 3. 元件定義與現有對應盤點

> 標記：✅ 已存在（直接採用）｜🔧 已存在但需調整｜🆕 需新建｜❌ 已存在但建議廢棄

### 3.1 核心矩陣 (Core Matrix)

| 項目 | 現有實作 | 狀態 |
|---|---|---|
| 8 維狀態矩陣 | `core/engine/state_matrix.py` → `StateMatrix4D`（1,664 行） | 🔧 god-module，需收斂對外 API |
| 矩陣型別 | `core/engine/state_matrix_types.py`（`DimensionState`/`AllocateDecision`） | ✅ |
| 矩陣 adapter | `core/engine/state_matrix_adapter.py`（`StateMatrixAdapter` 帶 proxy 子物件） | 🔧 與主矩陣重疊，建議併入主幹線 |
| 後向相容 shim | `core/autonomous/state_matrix.py`（12 行 re-export） | ❌ 建議刪除 |
| 硬體精度/計算矩陣 | `core/hardware/precision_matrix.py` / `compute_matrix.py` | ✅ 概念不同（硬體調度），不混入 |

**主幹線角色**：`Backbone.register_matrix("core", state_matrix)` — 提供 `read_axis` /
`write_axis` / `get_state` / `get_position` 等統一讀寫。

### 3.2 座標軸 (Coordinate Axes)

| 項目 | 現有實作 | 狀態 |
|---|---|---|
| 座標軸類別 | `core/state/axis.py` → `Axis` | 🔧 需統一介面 |
| 軸欄位定義 | `core/state/axis_field.py` + `axis_fields.json` | 🔧 需對齊主矩陣 8 維 |
| η 軸 | `core/engine/eta_axis.py` | 🔧 |
| 軸埠註冊 | `core/engine/axis_port_registry.py` → `AxisPortRegistry` | 🔧 |
| 梯度場 | `core/engine/influence_applicator.py`、`core/influence/space.py` | 🔧 |

**主幹線角色**：`Backbone.register_axis("alpha", adapter)` — 所有對座標軸的讀寫統一經由
主幹線，矩陣內部與外部元件不直接改軸。

### 3.3 自由矩陣 (Free Matrix)

| 項目 | 現有實作 | 狀態 |
|---|---|---|
| 共享潛空間 | `ai/multimodal/shared_latent_space.py` → `SharedLatentSpace`（5 模態 + 2 語義，單例 `get_shared_latent_space`） | 🔧 需加掛載/釋放 |
| latent↔key 對映 | `ai/multimodal/semantic_key_mapper.py` → `SemanticKeyMapper` | 🔧 |
| 語義一致性 | `ai/multimodal/similarity_service.py` | ✅ |
| 生成/重建循環 | `ai/multimodal/reconstruction_cycle.py` | ✅ |
| 潛推理網路 | `ai/multimodal/latent_reasoning_network.py` | ✅ |
| 權重持久化 | `ai/multimodal/multimodal_bridge.py` 的 `load_weights/save_weights` | 🔧 擴充為完整掛載 |

**主幹線角色**：`Backbone.register_matrix("free", latent_space, mountable=True)` —
見 §4 掛載/釋放機制。

### 3.4 核心模組 (Core Modules)

| 項目 | 現有實作 | 狀態 |
|---|---|---|
| 數位生命整合器 | `core/life/digital_life_integrator.py`（含 `state_matrix`） | 🔧 需改由主幹線提供矩陣 |
| 自主生命週期 | `core/life/autonomous_life_cycle.py` | 🔧（16 測試失敗源，API drift） |
| 生物整合器 | `core/bio/biological_integrator.py` | 🔧 |
| 情感系統 | `ai/alignment/emotion_system.py`（訂閱 CNS） | 🔧 改由主幹線接事件 |
| 意圖模型 | `core/life/intent_model.py` | 🔧 |
| 行為執行器 | `core/autonomous/behavior_executor.py`（在 `core/engine/`？見註） | 🔧 |
| 執行閘 | `ai/core/execution_gate.py` | ✅ |
| 危機系統 | `ai/crisis/crisis_system.py` | ✅ |
| 心跳 | `core/life/heartbeat.py`（訂閱 CNS） | 🔧 |
| 因果推理 | `ai/reasoning/causal_reasoning_engine.py` | ✅ |
| 回應合成 | `ai/response/composer.py`（1,362 行） | ✅ |
| LLM 路由 | `services/llm/router.py`（2,072 行） | 🔧 讀取矩陣改經主幹線 |

**主幹線角色**：`Backbone.register_module("emotion", EmotionSystem)` — 模組生命週期
（init/start/stop）與對矩陣/字典的存取統一管理。

> 註：`core/autonomous/` 多數為 re-export shim（見 §8），實際實作在 `core/life/`、
> `core/bio/`、`core/engine/`。

### 3.5 多模態字典 (Multimodal Dictionaries)

| 模態 | 現有實作 | 狀態 |
|---|---|---|
| **文本** | `ai/ed3n/dictionary_layer.py` → `DictionaryLayer`（460K+ 條目） | 🔧 需實作統一介面 |
| **對話** | 部分由 `DictionaryLayer` 承載 + `ai/context/dialogue_context.py` | 🔧 |
| **概念/知識** | `ai/garden/dictionary.py` → `VectorDictionary` | 🔧 需實作統一介面 |
| **音頻** | `ai/ed3n/multimodal/audio_encoder.py`、`ai/multimodal/audio_encoder_spectral.py`、`audio_decoder.py` | 🆕 無字典層 |
| **圖像** | `ai/ed3n/multimodal/image_encoder.py`、`ai/multimodal/visual_encoder.py`、`visual_decoder.py` | 🆕 無字典層 |
| **物件** | `ai/multimodal/primitives/concept_space.py` → `ConceptSpaceMapper` | 🆕 無統一字典介面 |
| **空間** | `ai/multimodal/primitives/`（primitive_library/renderer/encoder） | 🆕 無字典層 |
| 分類器 | `ai/core/dictionary_classifier.py` | 🔧 |

**主幹線角色**：`Backbone.register_dictionary("text", dict_layer)` — 統一協定
`MultimodalDictionary`（見 §5.3），字典皆走主幹線接矩陣，不直接存取。

### 3.6 主幹線本身 (Backbone)

| 層級 | 職責 | 現有對應 | 狀態 |
|---|---|---|---|
| **上層** | 矩陣/座標軸統一接線 + 自由矩陣掛載 | `neural_bridge.py` + `state_matrix_adapter.py` | 🆕 需新建 `core/backbone/` |
| **中層** | 字典/模組/轉譯器註冊 | `PriorityNegotiator`（路由投票） | 🆕 需新建 registry |
| **下層** | 入口/出口 + 配置傳遞 | `api/router.py` + `magic_numbers.compute_*` | 🆕 需新建接線層 |
| 事件匯流排 | CNS 事件 | `core/event_loop_system.py` + `core/system/state_store/global_store.py` | ✅ 直接採用 |

### 3.7 CLI / 前端 (Clients)

| 項目 | 現有實作 | 狀態 |
|---|---|---|
| 後端 REPL | `apps/backend/src/cli/repl.py`（直接 in-process import） | 🔧 改經主幹線下層 |
| CLI 套件 | `packages/cli/cli/`（HTTP client） | ✅ 走 HTTP，不需改 |
| 桌機 | `apps/desktop-app/`（WS） | ✅ 走 WS |
| Web 儀表板 | `apps/web-dashboard/`（假資料 API，見 §X #204 後殘留） | 🔧 接真實後端 |
| Live2D | `apps/web-live2d-viewer/` | ✅ |
| MCP | `src/mcp/connector.py` | ✅ |

---

## 4. 自由矩陣掛載/釋放機制（新增）

### 4.1 目標

`SharedLatentSpace`（及各字典）支援**按需掛載**：不常使用的模態不常駐記憶體，
使用時才從磁碟載入（`mount`），用完可釋放（`unmount`）。

### 4.2 介面設計

```python
# core/backbone/mountable.py
class Mountable(Protocol):
    """可掛載/釋放資源的統一介面。"""
    def mount(self) -> bool: ...          # 從磁碟載入 → 記憶體
    def unmount(self) -> bool: ...        # 記憶體 → 磁碟 (flush)，釋放 RAM
    def is_mounted(self) -> bool: ...
    def persistence_path(self) -> str: ...

# Backbone 上的統一入口
backbone.mount("free", "vision")     # 掛載 vision 模態
backbone.unmount("free", "vision")   # 釋放 vision 模態
backbone.mounted("free")             # -> {"vision": True, "audio": False, ...}
```

### 4.3 掛載狀態機

```
         mount()                  unmount()/idle
DISK ───────────────▶ MEMORY ───────────────────▶ DISK
  ▲                    │   │                        │
  │    (load weights)  │   └── 使用中 (active)       │ (flush + free)
  └────────────────────┴────────────────────────────┘
        重新 mount()            idle timeout 自動釋放
```

- `mount()`：`load_weights`/反序列化 → `is_mounted=True`
- `unmount()`：`save_weights`/flush → 釋放 numpy/torch buffer → `is_mounted=False`
- 支援 **idle timeout 自動釋放**（讀取計數歸零後釋放）
- 存取時若未掛載 → 自動 lazy mount（`_ensure_mounted`）

### 4.4 現有資源的掛載點

| 資源 | 現有持久化 | 掛載器 |
|---|---|---|
| `SharedLatentSpace` | `multimodal_bridge.load_weights/save_weights`（無 save 目前） | 🆕 補 `save_weights` + 模態級 `_projections` 序列化 |
| GARDEN 矩陣 | `ai/garden/binary_store.py`（`np.memmap` 已近乎按需載入） | 🔧 包裝為 `Mountable` |
| ED3N 字典 | `ed3n_engine.save/load` | 🔧 包裝為 `Mountable` |
| 上下文儲存 | `ai/context/storage/memory.py` + `disk.py` | ✅ 已有 memory/disk 雙後端，直接做為參照 |

> 設計原則：**小資源常駐（核心矩陣、文本字典），大資源按需（GARDEN ~1GB、潛空間、影像字典）**。

---

## 5. 接線四大關切（輸入輸出 / 狀態 / 轉譯 / 配置）

所有主幹線連接都必須明確處理這四件事。以下為每項的契約設計。

### 5.0 成對排程 / 配對狀態（Stability Core，主幹線穩定性基石）

> **核心原則**：主幹線的所有輸入輸出**必須成對**——每個輸入都必須（或在分析後能）對應
> 一個輸出。成對性讓「衝突」與「靜默報錯」在結構上不可能發生：
> 沒有孤兒輸入、沒有憑空輸出、沒有並發寫衝突。

#### 5.0.1 IO Pair（輸入輸出對）

每個輸入輸出共享一個 `IOPair` 追蹤結構：

```python
@dataclass
class IOPair:
    pair_id: str                     # 全域唯一 (uuid)
    correlation_id: str              # 沿用 HSP/HTTP 既有追蹤 id
    kind: str                        # "chat" | "tool_call" | "external" | "learning" | "event" | ...
    pattern: str                     # REQUEST_RESPONSE | REQUEST_ACK | EVENT_HANDLER |
                                     # BROADCAST_ACK | FIRE_AND_FORGET | PROACTIVE ...
    input_ref: Envelope              # 輸入信封
    output_ref: Optional[Envelope]   # 輸出信封；None = 待配對 (pending)
    status: str                      # QUEUED | RUNNING | PAIRED | TIMEOUT |
                                     # ORPHAN | CONFLICT | ERROR | CANCELLED
    schedule: Dict[str, Any]         # submitted_at / deadline / retries / slot / timeout
    analysis: Dict[str, Any]         # 配對分析證據（見 §5.0.4 潛在配對）
```

#### 5.0.2 排程器（PairScheduler）— 成對排程

- 在 `WaitingScheduler` 的 slot 分配之上，加**成對追蹤**：任務不再「submit 完即忘」，
  而是 `submit(輸入) → resolve(輸出)`，中間狀態全程可查。
- 排程保證：
  - **先入先配**：輸出永不早於其輸入被處理（避免時序反轉）。
  - **同對單執行**：同一 `pair_id` 不會被並發處理兩次（消除寫衝突）。
  - **逾時診斷**：超過 `deadline` 未配對 → 標記 `TIMEOUT`/`ORPHAN`，可重試或診斷，
    絕不靜默丟棄。

```python
# core/backbone/pairs.py (PairScheduler)
backbone.io.submit(input_envelope, timeout=8.0) -> pair_id
backbone.io.resolve(pair_id, output_envelope)    # 配對完成 → PAIRED
backbone.io.cancel(pair_id)                      # 取消 → CANCELLED
backbone.io.retry(pair_id)                       # 重排 → QUEUED
# 對所有外部/學習/訓練/LLM 呼叫統一生效（包住 §5.5.1-5.5.3 資料流）
```

#### 5.0.3 配對狀態（PairState）— 能查排程與處理狀態並管理

- **查詢**：`backbone.io.status(pair_id)`、`backbone.io.pending()`（全部未配對）、
  `backbone.io.orphans()`（逾時未配對）、`backbone.io.by_kind("external")`。
- **管理**：retry / cancel / 調整 deadline。
- **儲存**：配對日誌以 `correlation_id` 為索引，複用 `GlobalStateStore`（新 domain
  `io_pairs`）或獨立 domain，可持久化。
- **可觀測**：狀態滿足 §3.8.2「能查排程與處理狀態並進行管理」——排程階段
  （QUEUED→RUNNING）、處理階段（RUNNING→PAIRED/ERROR）全程可見。

#### 5.0.4 成對性不變式（Pairing Invariant）

> **∀ 輸入 ∃ 輸出 ∨ 可計算的潛在輸出**。未配對的輸入不得靜默消失。

| 表面型態 | 範例 | 成對方式 |
|---|---|---|
| request → response | chat / tool_call / external | 直接成對 |
| request → ack | HSP `correlation_id` + `_pending_acks` | ACK 或 timeout→ORPHAN |
| event → handler | CNS `emit_event` | **每個 subscriber 的處理回傳 = 隱式輸出**（count=0 → ORPHAN）|
| broadcast → 收件人 | WS broadcast / HSP publish | 每個收件人處理結果/ack = 配對輸出 |
| fire-and-forget | 學習寫回 | 學習寫回矩陣/字典的 diff = 輸出（可驗證）|
| proactive 主動行為 | DLI / AutonomousLifeCycle | 行為執行結果與狀態影響 = 輸出 |

**潛在配對（表面不成對，計算後成對）**：單向事件 / 廣播 / 主動行為，經
「分析」（subscriber 計數、因果鏈 `CausalTracer`、`correlation_id` 關聯）後可找出
其對應輸出。`IOPair.analysis` 存放此配對證據。

#### 5.0.5 衝突 / 錯誤消除機制

| 想消除的問題 | 成對機制提供的保證 |
|---|---|
| 輸入丟失（呼叫了沒人處理） | 逾時→ORPHAN，可診斷可重試，永不靜默 |
| 輸出來源不明（憑空回覆） | 每個輸出必屬某 `pair_id` |
| 並發寫衝突 | 同對單執行（slot 分配 + 每對鎖） |
| 時序反轉（輸出先於輸入） | 先入先配 |
| 靜默失敗（except: pass） | 未配對即異常狀態，配對日誌留痕 |
| LLM/外部服務掛起 | `WaitingScheduler` timeout 機制沿用（§5.0.2 覆蓋）|

現有對應與差距：
- ✅ `core/waiting_scheduler.py` `WaitingScheduler`：slot 分配與 timeout（可合併為排程核心）。
- ✅ HSP `connector.py`：`correlation_id` + `_pending_acks`（request→ack 成對雛形，直接沿用協定）。
- ✅ `GlobalStateStore`：可容納 `io_pairs` domain + 持久化。
- 🔧 目前 chat/tool/external 呼叫**無統一成對追蹤**（`ExecutionGate` 每次 new、CNS 事件不追蹤
  subscriber 處理結果）→ 主幹線 `backbone.io` 收斂。

### 5.1 輸入輸出傳遞 (I/O Contract)

主幹線定義統一的**輸入/輸出信封**（envelope），跨層傳遞不丟失語意：

```python
@dataclass
class Envelope:
    kind: str                    # "chat" | "image" | "audio" | "state_query" | ...
    payload: Dict[str, Any]      # 內容 (bytes/text/features/...)
    modality: Optional[str]      # "text"|"audio"|"vision"|"object"|"space"|"dialogue"
    meta: Dict[str, Any]         # 來源/時間戳/追蹤 id
    state: Dict[str, float]      # 隨附狀態 (如矩陣軸值快照)

# 主幹線方法
backbone.send_down(envelope)     # 下層→中層→上層 (使用者請求進入)
backbone.send_up(envelope)       # 上層→中層→下層 (處理結果回傳)
```

現有對應：`ExecutionResult.to_dict()`、`RouteDecision.to_dict()`、`Event.to_dict()`
都是信封雛形 — 主幹線收斂為單一 `Envelope`。

### 5.2 狀態傳遞 (State Passing)

- **即時狀態**：統一經 `Backbone.get_state("core")` / `write_axis(...)` 讀寫 `StateMatrix4D`。
- **事件/異步狀態**：統一經 CNS 事件匯流排（`GlobalStateStore.subscribe_event/emit_event`），
  現有訂閱者（emotion/heartbeat/DLI/biological_integrator）直接沿用。
- **隨請求狀態**：`Envelope.state` 快照隨輸入輸出傳遞，避免讀取時序問題。

現有對應與差距：
- ✅ `GlobalStateStore` 已支援 domain 狀態 + 事件 + 訂閱。
- 🔧 目前矩陣由 `chat_routes._get_state_matrix()` 與 `DLI.state_matrix` **兩個來源**提供
  （狀態不一致風險）→ 主幹線統一為單一註冊矩陣。

### 5.3 轉譯 (Translation)

統一**轉譯器註冊表**：從「StateMatrix ↔ SNN」「latent ↔ key」兩種擴充為通用模型。

```python
# core/backbone/translator.py
@dataclass
class TranslationRule:
    source: str        # 例如 "core_matrix.alpha"
    target: str        # 例如 "free_matrix.vision"
    convert: Callable[[Any], Any]

backbone.register_translator(TranslationRule(...))
backbone.translate(source, target, value)
```

現有對應：
| 轉譯 | 現有實作 | 動作 |
|---|---|---|
| StateMatrix ↔ GARDEN/ED3N SNN | `ai/bridge/neural_bridge.py` | 🔧 改經主幹線註冊 |
| latent ↔ keys | `ai/multimodal/semantic_key_mapper.py` | 🔧 改經主幹線註冊 |
| 模態投影 | `shared_latent_space.project()` + `multimodal_bridge.encode_*_to_latent` | ✅ 直接採用 |
| 硬體調度轉譯 | `core/hardware/*` | ✅ 獨立，不混入 |

### 5.4 配置設定傳遞 (Config & Settings Passing)

- **讀取**：統一經 `magic_numbers.compute_*` / `_get(key, default)`（已有硬體感知層級鏈）。
- **傳遞**：主幹線啟動時載入設定並以 `Envelope.meta["config"]` 或注入方式傳給各元件，
  元件**不得自行讀檔**（目前多處直接 `load_config`，需收斂）。

現有對應：
- ✅ `magic_numbers.py`：`compute_mode/bool/int/float` + 硬體 profile 感知。
- ✅ `tiered_loader.py`：`get_config(path)` 分層合併。
- 🔧 `core/config_loader.py` / `core/system/config/` 多個入口 → 統一走主幹線注入。

### 5.5 學習 / 訓練 / 外部調用接線（補充定位）

學習、訓練、外部調用是**三種不同性質的資料流**，不屬於單一層，各按性質接線：

#### 5.5.1 外部調用 (External Calls) — 下層「外部閘道」

外部服務（LLM providers、天氣、Drive、搜尋、Atlassian、OS bridge、MCP）統一經
**下層的外部閘道**（`ExternalGateway`）進出。元件**不得**直接 `import` 這些服務。

```python
# core/backbone/external.py
backbone.register_external("llm.openai", OpenAIProvider)      # 包裝 providers/*.py
backbone.register_external("weather", WeatherService)
backbone.register_external("drive", GoogleDriveService)
backbone.register_external("search", WebSearchTool)

result = await backbone.call_external("llm.openai", "generate", prompt=..., ...)
# 內建: 重試 (RetryPolicy) + 熔斷 (CircuitBreaker) + rate-limit
```

現有對應與差距：
- ✅ LLM providers 已有統一介面：`services/llm/providers/base.py` → `BaseLLMBackend.generate()/check_health()`，`registry.py` 列舉 9 個 backend。
- ✅ `shared/network_resilience.py` 已有 `RetryPolicy`/`CircuitBreaker`（可直接用）。
- 🔧 其他外部服務（weather/drive/search/atlassian）**無統一介面** → 收斂為
  `ExternalBackend`（`call(method, **kwargs)`）並註冊到閘道。
- 🔧 目前 `llm_decision_loop.py`、`proactive_interaction_system.py` 等**直接 import**
  weather/LLM → 改經 `backbone.call_external()`。

#### 5.5.2 學習 (Learning) — 中層「學習協調器」

學習是**異步、增量、持續**的寫回流程（用完回應後長知識）。統一經中層的
`LearningCoordinator` 接線，訂閱 CNS 事件（如 `routing.response_generated`）而非
在 `chat_service` 內嵌呼叫：

```python
backbone.register_learning("continuous", ContinuousLearningPipeline)   # ai/ed3n/continuous_learning.py
backbone.register_learning("garden",    GARDENLearningPipeline)
backbone.register_learning("response",  LearningLoop)                   # ai/response/learning_loop.py
backbone.register_learning("orchestrator", LearningOrchestrator)        # ai/meta/learning_orchestrator.py

# 觸發: CNS 事件 response_generated → coordinator 依序執行 registered learners
```

現有對應與差距：
- ✅ `ai/core/training_coordinator.py`（領域訓練節流）、`ai/meta/learning_orchestrator.py`、
  `ai/response/learning_loop.py`（成長 ED3N 字典）、`ai/ed3n/continuous_learning.py`、
  `ai/multimodal/continuous_multimodal_learning.py` 皆已存在。
- 🔧 目前由 `chat_service._process_continuous_learning()` /
  `_process_garden_learning()`（第 201-202 行）**內嵌觸發** → 改為 CNS 事件驅動。
- 🔧 學習寫回**字典與矩陣**須經主幹線（`backbone.write_axis` / `dictionary.grow`），
  不得直接存取。

#### 5.5.3 訓練 (Training) — 上層「訓練工作流」+ 自由矩陣掛載

訓練是**批次、離線、重度**的寫入流程（更新權重）。與學習的差別：訓練需要
**掛載自由矩陣**，且耗時長、應可取消/續跑。統一經上層的 `TrainingCoordinator`：

```python
backbone.register_training("ed3n",  ED3NTrainer)                    # ai/ed3n/ed3n_trainer.py
backbone.register_training("multimodal", FullTrainingPipeline)      # ai/multimodal/training_pipeline.py
backbone.register_training("garden", GARDENEngine)                  # ai/garden/garden_engine.py

# 執行: 自動 mount 所需模態 → train → unmount/flush
async with backbone.training("multimodal") as t:
    await t.train(epochs=..., dataset=...)
```

現有對應與差距：
- ✅ `ai/ed3n/ed3n_trainer.py`、`ai/multimodal/training_pipeline.py`（6 種 trainer）、
  `ai/garden/garden_engine.py`、`ai/ed3n/multimodal/cross_modal_trainer.py` 皆已存在。
- 🔧 目前訓練僅由 CLI/scripts（`python -m ed3n train` 等）離線觸發 → 收斂為
  `TrainingCoordinator` 統一排程，並接上 `Mountable` 掛載/釋放。
- 🔧 `continuous_multimodal_learning.py` 已做掛載式載入的雛形，可作實作參照。

#### 5.5.4 三者的層級歸屬摘要

| 資料流 | 接線層 | 統一入口 | 觸發方式 | 對矩陣/字典 | 主要現有元件 |
|---|---|---|---|---|---|
| **外部調用** | 下層 外部閘道 | `backbone.call_external()` | 同步/請求時 | 只讀快照 | `providers/*`、`weather`、`drive`、`search` |
| **學習** | 中層 學習協調器 | `backbone.learn(trigger)` | CNS 事件/異步 | 寫回 (增量) | `continuous_learning`、`learning_loop`、`learning_orchestrator`、`training_coordinator` |
| **訓練** | 上層 訓練工作流 | `backbone.training()` | 批次/離線/掛載 | 寫回 (權重) | `ed3n_trainer`、`training_pipeline`、`garden_engine` |

> 設計原則：**外部調用是「入」**（把外部知識帶進來）、**學習是「內化」**（把經驗寫回
> 字典/矩陣）、**訓練是「重構」**（批次更新權重、可掛載/釋放大資源）。三者都必須
> 經主幹線，且都與 §4 掛載機制、§5.1-5.4 四大關切正交。

### 5.6 響應模式（Response Modes）— 層式 vs 流式 vs 傳統，1:1 / 1:N / 1:N×N 可切換

> **先釐清兩個易混淆的概念**（此前常在設計中分不清）：
> - **層式響應（Layered Response）**：輸出一層一層「補上/填上」。先有骨幹（大綱），
>   再填細節、再填片語，每層是**一個完整語意片段**，層間是「填補」關係
>   （section → paragraph → sentence → token）。
> - **流式響應（Streaming Response）**：輸出一個 token 一個 token「接連補上」。是
>   **同一個最終文本**的漸進片段，token 間是「串接」關係。
>
> 兩者**正交**：層式定義「內容結構如何分塊」，流式定義「單一文本如何分批送達」。
> 層式也可流式（每層到齊後再以 token 送出），也可一次性（層疊完後整段回傳）。

#### 5.6.1 三種響應模式與基數

| 模式 | 基數 | 語意 | 現有實作 | 狀態 |
|---|---|---|---|---|
| **傳統對話** | 1:1 | 一輸入 → 一完整回應 | `router.generate_response()` → `ChatResponse`（`services/llm/router.py:799`） | 🟢 主路徑 |
| **層式響應** | 1:N | 一輸入 → N 層語意片段（逐層填補） | `StreamingPipeline`（`ai/streaming/pipeline.py`：section→paragraph→sentence→token，fast+slow pass）；`ResponseComposer`/`FragmentComposer`/`NeuroBlender`（`ai/response/composer.py`） | 🟡 已存在但未進主聊天 |
| **流式響應** | 1:N | 一輸入 → 單一文本 N 個 token 分批送達 | `TokenStream` + `StreamSynthesizer` + `TokenProducer` 系列（`ai/streaming/*`） | 🟡 旁路可用，**未接 LLM 主聊天** |
| **層式 × 流式** | 1:N×N | 一輸入 → N 層，每層又以 N' token 送達 | `StreamingPipeline` 內已用 `TokenStream`（層間 emit 到同一個 stream） | 🟡 骨架存在，未正式化 |

現有對應與差距：
- ✅ **層式**：`StreamingPipeline`（四層 fast/slow pass + buffer `_merge` 填補）
  + `FragmentComposer`（6 種 `FragmentType`）+ `NeuroBlender`（神經合成）。
- ✅ **流式**：`TokenStream`（async queue、backpressure、seq_id）+
  `StreamSynthesizer`（predicted/retrieved/generated 三源合成）+
  4 個 `*Producer`（section/paragraph/sentence/token）。
- 🔧 **主聊天無 stream**：`router.generate_response()` 為同步單一回應；
  流式能力只掛在 `/document/stream`（`chat_routes.py:1936`）與
  `multimodal_ws_handler.py:115`（`chat_stream`），未進主 `chat` endpoint。
- 🔧 **層式與流式未整合為統一模式**：目前 `StreamingPipeline` 把層式輸出 emit 到
  `TokenStream`（層式⊂流式），但主 LLM 回應走 `_generate_with_llm` 不經 pipeline。

#### 5.6.2 衝突風險（用戶提問：1:N×N 是否可能衝突）

| 衝突場景 | 成因 | 主幹線處理 |
|---|---|---|
| 層式 vs 流式同時寫 buffer | `StreamingPipeline._merge`（填補）與 LLM token 串接（append）語意不同 | 響應模式**二選一**或「層式為父、流式為子」明確包裝；不得並行寫同一 buffer |
| 多源合成順序 | `StreamSynthesizer` 的 predicted/retrieved/generated 到達順序不保證 | `seq_id` 排序 + `SynthesizerConfig`（correction/verify 閾值）已存在，主幹線套 `IOPair`（§5.0）追蹤每 token 配對 |
| 1:N×N 回應多分支 | 一個輸入觸發多層多 token，最後需合併為單一回應 | `ComposedResponse`/`RouteDecision` 信封統一收斂（§5.1）|
| 流式 + 非流式 fallback 混用 | `_try_*` 鏈在 stream 中途 fallback 會切斷 stream | 模式切換只在**請求層級**決定（`mode` 參數），不中途切換 |

#### 5.6.3 模式切換機制

```python
# 請求層級決定，不中途切換
backbone.respond(mode="1:1" | "layered" | "stream" | "layered_stream")

# 1:1  — router.generate_response()（現有主路徑）
# layered     — StreamingPipeline 逐層 emit（每層一完整片段）
# stream      — LLM token 流（需先接 TokenStream 到 LLM provider，§11.5 可選項）
# layered_stream — StreamingPipeline 層內 token 送出（現有 pipeline 已具雛形）
```

- 切換維度獨立於內容：同一輸入可任選模式，**不改變矩陣/字典/狀態**。
- 與 §5.0 成對排程整合：每個輸出 token / 每層輸出都是一個 `IOPair` 的輸出側，
  可追蹤、可查、可重試（§5.0.3）。
- **驗收**：同一請求以四種模式各跑一次，最終組出的回應文本一致
  （1:1 == layered 疊合 == stream 拼接 == layered_stream 疊合拼接）。

#### 5.6.4 現有實作歸位（不新建重複系統）

| 概念 | 現有實作 | 主幹線動作 |
|---|---|---|
| 1:1 傳統 | `router.generate_response` + `ChatResponse` | ✅ 直接採用 |
| 層式組合 | `ResponseComposer` + `FragmentComposer` + `NeuroBlender`（`composer.py`） | 🔧 註冊為「層式組合器」 |
| 層式 pipeline | `StreamingPipeline`（`pipeline.py`） | 🔧 註冊為「層式執行器」 |
| 流式基礎 | `TokenStream` + `StreamSynthesizer` + `TokenProducer` 系列（`ai/streaming/*`） | ✅ 直接採用 |
| 流式接 LLM | 無 | 🆕 主聊天接 stream（§11.5 可選項） |

> 結論：專案**已有層式（StreamingPipeline / composer）與 1:1 傳統對話**；流式
> `TokenStream` 基礎已在但主聊天未接。主幹線只做「模式選取器 + 統一信封 + 成對追蹤」，
> 不重寫任何現有生成引擎。1:N×N 以「層式 ⊃ 流式」包裝支援，衝突點見 §5.6.2 表格。

---

## 6. 建議模組結構（新建部分）

```
apps/backend/src/core/backbone/
  __init__.py              # get_backbone() 單例 + 公開 API
  backbone.py              # Backbone 類（註冊表 + 路由 + 信封）
  contracts.py             # Envelope / Mountable / TranslationRule / IOPair 協定
  registry.py              # matrix/axis/module/dictionary/translator 五個註冊表
  mountable.py             # 掛載/釋放機制 (idle timeout, lazy mount)
  io.py                    # send_up / send_down 信封路由
  response.py              # ★ Response Mode 選取器（1:1/layered/stream/layered_stream, §5.6）
  pairs.py                 # ★ Stability Core: IOPair + PairScheduler + PairState
                           #   (成對排程/配對狀態/成對性不變式, §5.0)
  state.py                 # 統一狀態讀寫 (代理 GlobalStateStore + StateMatrix4D)
  translate.py             # 轉譯器註冊與執行
  config.py                # 配置注入 (包裝 magic_numbers + tiered_loader)
  external.py              # 下層外部閘道: call_external + RetryPolicy/CircuitBreaker
  learning.py              # 中層學習協調器: register_learning + CNS 事件驅動
  training.py              # 上層訓練工作流: register_training + 掛載/釋放
  lower_layer.py           # 下層入口：API/CLI/WS → 主幹線
  upper_layer.py           # 上層：矩陣/座標軸/自由矩陣接線
  middle_layer.py          # 中層：字典/模組/轉譯器註冊與協調
  tests/                   # 對應單元測試 (見 §7 步驟 A)
```

> `pairs.py` 合併現有 `core/waiting_scheduler.py`（slot 排程核心），並在 HSP
> `correlation_id`/`_pending_acks` 協定之上提供統一的成對追蹤；`backbone.io`
> 的 `submit/resolve/cancel/retry` 即其公開介面。

> **明確非目標**：不建立額外的服務容器 / DI 框架。主幹線只是**薄註冊表 + 路由**，
> 不持有計算邏輯。現有元件保留內部實作，只把「對外接線」改為主幹線。

---

## 7. 增量演進策略（三步走，每步可獨立合併）

### 步驟 A — 建立主幹線骨架（不影響現有行為）
1. 新建 `core/backbone/`（§6），實作註冊表 + 信封 + 掛載機制。
2. 註冊現有單例：`StateMatrix4D`、`SharedLatentSpace`、`DictionaryLayer`、
   `VectorDictionary`、CNS bus、`magic_numbers`。
3. **實作 `pairs.py`（§5.0 Stability Core）**：合併 `WaitingScheduler` slot 排程，
   新增 `IOPair`/`PairScheduler`/`PairState`（submit/resolve/cancel/retry +
   `status/pending/orphans` 查詢），先獨立可用、不改既有呼叫。
4. 加入 `get_backbone()` 單例（仿 `get_shared_latent_space` 模式）。
5. **測試**：新增 `tests/core/backbone/`（註冊/路由/掛載/轉譯/外部/學習/訓練 7 類
   測試 + **成對排程測試**：先入先配、同對單執行、逾時→ORPHAN、重試、衝突防範）。

### 步驟 B — 遷移接線（一次遷移一個元件）
1. `chat_routes.py` 的 9 個 `_get_*` 工廠 → 改經 `get_backbone()`。
2. `neural_bridge.py` / `semantic_key_mapper.py` → 註冊為 translator。
3. **外部閘道**：包裝 LLM providers（先做 `openai`/`ed3n`/`garden`）→ `call_external()`。
4. **成對排程套用**：`call_external()` / CNS `emit_event`（追蹤 subscriber 處理
   結果）/ `ExecutionGate` 工具呼叫 → 全部包 `backbone.io.submit/resolve`，
   使既有呼叫獲得成對追蹤與 ORPHAN 診斷。
5. **學習協調器**：把 `chat_service._process_continuous_learning()` /
   `_process_garden_learning()` 改為 CNS 事件驅動。
6. 修 16 個失敗測試（`AutonomousLifeCycle` API drift 等）。
7. 每個遷移一個 commit，跑對應測試。

### 步驟 C — 自由矩陣掛載 + 字典統一介面
1. `SharedLatentSpace` 補 `save_weights` + `Mountable` 包裝。
2. 定義 `MultimodalDictionary` 協定，ED3N/GARDEN 實作之。
3. **訓練工作流**：`ED3NTrainer` / `FullTrainingPipeline` 接 `Mountable` 掛載/釋放。
4. 音頻/圖像/物件/空間字典以協定為基礎逐步加入。

### 里程碑判定
- 步驟 A 完成 ⟺ `pytest tests/` 全綠（現有 5,468 pass 不倒退）
- 步驟 B 完成 ⟺ 16 個失敗測試歸零 + `call_external`/`learn` 有測試覆蓋
- 步驟 C 完成 ⟺ `backbone.mount/unmount` 有測試覆蓋，字典統一協定有 2+ 實作

---

## 8. 需清理/調整的既有問題（隨重構一併處理）

| 類別 | 項目 | 動作 |
|---|---|---|
| 空 shim | `core/autonomous/state_matrix.py`（12L） | 刪除 |
| 空 shim | `core/autonomous/` 其餘 re-export（見 AGENTS 說明） | 收斂 |
| 幽靈模組 | `core/metacognition/metacognitive_capabilities_engine.py`（24L） | 實作或刪除 |
| 幽靈模組 | `core/ethics/ethics_manager.py`（17L） | 實作或刪除 |
| 幽靈模組 | `core/evolution/emergence_engine.py`（21L） | 實作或刪除 |
| 幽靈模組 | `core/feedback_loop_engine.py`（24L） | 實作或刪除 |
| god-module | `services/llm/router.py`（2,072L） | 只收斂接線，不拆分 |
| god-module | `api/routes/chat_routes.py`（1,985L） | 只收斂接線，不拆分 |
| API drift | `AutonomousLifeCycle.should_act/decide/evaluate_state` | 測試對齊或補實作 |
| Windows-only 測試 | `test_set_wallpaper_windows` | 加 skipif(platform) |
| 可移植性 | `test_three_layer_visual` 硬編碼 `/nonexistent` | 改用 tmp_path |
| 假資料 | `web-dashboard` 3 個 API route | 接真實後端 |
| CLI 缺陷 | `packages/cli/cli/__main__.py` import 錯路徑 | 修路徑 |
| Live2D | `.gitignore` 的 `*.model3.json` 遮蔽清單檔 | 修 .gitignore |
| 無成對追蹤 | `ExecutionGate` 每次 new、工具呼叫無 pair 追蹤 | 包 `backbone.io.submit/resolve`（§5.0）|
| 無成對追蹤 | CNS `emit_event` 不追蹤 subscriber 處理結果（count=0 靜默）| 事件→隱式配對，0 訂閱者→ORPHAN |
| 無成對追蹤 | LLM/外部呼叫失敗 `except: pass` 靜默 | 未配對即異常狀態（§5.0.5）|

---

## 9. 風險與非目標

### 風險
1. **遷移範圍過大** → 步驟 B 採「一次一元件 + 一個 commit + 對應測試」控管。
2. **新增抽象層過厚** → 主幹線明確為「薄註冊表 + 路由」，禁止持有業務邏輯；否則
   就是複製 `services/` 的錯誤。
3. **惰性載入被破壞** → 主幹線啟動只註冊**工廠**（lazy），不實例化重量元件。
4. **`neural_bridge` 預設 off** → 主幹線維持 `compute_bool("neural_bridge", False)`，
   不改變預設行為。
5. **外部閘道過度包裝** → `call_external` 只加「重試/熔斷/速率」薄殼，不複製各
   provider 的私有邏輯；`BaseLLMBackend.generate()` 已統一，直接轉接即可。
6. **學習改事件驅動後遺漏** → `chat_service` 改 CNS 事件前，先確認事件
   `routing.response_generated` 在所有成功路徑都有 emit，否則學習會漏觸發。

### 非目標
- ❌ 不重寫 `StateMatrix4D` / `router.py` / `chat_routes.py` 的內部實作。
- ❌ 不引入 DI 框架 / 服務容器。
- ❌ 不做全專案接線一次性遷移。
- ❌ 不改變 8 維矩陣的語意（αβγδεθζ）。
- ❌ 不新增外部服務提供者（不實作新 LLM/tool），只收斂現有的接線。

---

## 10. 驗證方式

```bash
# 步驟 A/B 每步完成後
.venv/bin/python -m pytest tests/core/backbone/ -q          # 新增測試
.venv/bin/python -m pytest tests/ -q --timeout=90           # 全量回歸
.venv/bin/flake8 apps/backend/src tests/                    # lint
```

---

## 11. 附錄：全專案接線盤點總表（2026-08-09 完整盤點）

> 本附錄為跨五次探索（記憶/執行/安全/core/services）的完整盤點，作為主幹線
> 設計與後續遷移的**對照基準**。標記：🟢 活躍（接進主幹線）｜🟡 半活/待接｜
> 🔴 死碼/孤兒（無 production 消費者）。

### 11.1 主幹線資料流現況（單次對話請求旅程）

```
POST /chat/unified (或 WS chat_message)
 └─ chat_routes._handle_chat_request (L1329) → _run_chat_pipeline
     ├─ Step 5a-h: context 注入 (bio / ALC / EmotionSystem / IntentModel /
     │              ModalityGateway / DLI awareness / alignment / crisis /
     │              IntentRegistry / DesktopInteraction)
     ├─ _try_math_verification (L385): MathVerifier(state_matrix) + domain_ripple
     ├─ _build_chat_context (L503): BioState + StateMatrix4D(α..ζ+θ) + ED3N 檢索 + 對話 + 記憶
     ├─ Step 7: ExecutionGate(model_bus=ChatService.model_bus)  [短接]
     ├─ Step 8: AgentManager + AgentOrchestrator [短接]
     ├─ Step 9: CausalReasoningEngine 因果注入
     └─ Step 10: chat_service.generate_response
         └─ router._route_response:
             模板(COMPOSED/HYBRID) → _generate_with_llm
             → 失敗降級 _try_fallback_chain(config routing.fallback_chain)
             → _fallback_response: ModelBus(Tier0) → ED3N/GARDEN(Tier1) → NeuroBlender → 純模板
             旁路: _try_template_match → _try_ensemble → _try_memory_retrieval
                   → _try_knowledge(短路) → _try_neural_bridge(StateMatrix↔SNN)
```

### 11.2 各子系統健康狀態

#### 🟢 活躍（已接進主幹線，遷移時優先註冊）

| 子系統 | 元件 | 主幹線角色 | 目前接法 |
|---|---|---|---|
| 生命整合 | `core/life/digital_life_integrator.py` | 中央聚合器（lifespan 單例） | 組裝 Bio+ActionExecutor+StateMatrix+Intent，訂閱 3 CNS 事件 |
| 生物 | `core/bio/biological_integrator.py` | 情感/危機每輪分析 | chat_routes 呼叫 `_analyze_emotion_and_crisis()` |
| 狀態 | `core/engine/state_matrix.py` | **核心矩陣** | DLI 持有；chat_routes `_get_state_matrix()` fallback 第二實例 ⚠️ |
| 生命週期 | `core/life/autonomous_life_cycle.py` | 主動行為 + 路由調整 | lifespan `get_lifecycle()` 共用單例；CNS 訂閱 |
| 心跳 | `core/life/heartbeat.py` | 系統健康 | lifespan `get_metabolic_heartbeat()`；CNS 訂閱 3 事件 |
| 意圖 | `core/life/intent_model.py` | 路由調整 voter | CNS 事件發送者；router 讀取 |
| 路由 | `ai/meta/priority_negotiator.py` | **8 選民路由** | router.py L80-87 註冊全部 voter |
| 執行閘 | `ai/core/execution_gate.py` | 工具調用安全閘 | chat_routes L687 每次 new；ModelBus 對齊 7 handlers |
| 代理 | `ai/agents/agent_manager.py` + `dynamic_agent_registry.py` | 任務代理路由 | chat_routes Step 8；寫 StateMatrix(αβγδ) |
| 因果 | `ai/reasoning/causal_reasoning_engine.py` | 因果預測注入 | lifespan 初始化；chat_routes Step 9 |
| 記憶 | `ai/memory/ham_memory/ham_manager.py` | **記憶核心樞紐** | ⚠️ **4+ 實例**（router/chat_service/drive/DLI）各自 new |
| 向量記憶 | `ai/memory/vector_store.py` | 語義搜尋 | chat_service `semantic_search`（1s timeout 永久停用） |
| 落地學習 | `ai/memory/grounded_learning_manager.py` | 知識驗證（單例） | chat_service 三處使用 |
| 數理 | `ai/memory/domain_ripple.py` | 數理認知情 | chat_routes L415 對 DLI 的 live StateMatrix4D |
| 協調記憶 | `ai/memory/unified_memory_coordinator.py` | HAM+LU+CDM 整合 | router.py L389 建構，`store_experience` |
| 對話上下文 | `ai/context/dialogue_context.py` | 對話狀態 | chat_routes `_get_dialogue_ctx()` 單例 |
| 文化 | `ai/context/cultural_context.py` | 語言文化注入 | chat_service |
| CNS 事件 | `core/system/state_store/global_store.py` | **事件匯流排** | 訂閱 2 元件 6 筆 / 發送 41 筆 |
| LLM 樞紐 | `services/llm/router.py`（2,072L） | **LLM 路由** | get_llm_service() 註冊進 service_registry |
| 外部閘道候選 | `services/llm/providers/*.py` | 9 LLM backend | BaseLLMBackend.generate()/check_health() 統一 |
| WS 樞紐 | `services/websocket_manager.py` | 外部進/出 | /ws → chat_routes；DLI 主動 → manager.broadcast |
| 流式 | `ai/streaming/pipeline.py` | SSE/WS 旁路 | 僅 2 旁路，不接 LLM token 流 |
| 插件 | `core/plugin/plugin_manager.py` + `hook_registry.py` | 擴展點 | lifespan `_init_plugins`；api/v1/endpoints/plugins.py |
| 追蹤 | `core/tracing/causal_tracer.py` | 因果鏈 | api/v1/endpoints/trace.py 已掛載 |
| 安全評估 | `core/security/secure_eval.py` | safe_eval | math_ripple/logic_unit/eta_axis |

#### 🟡 半活/待接（有實作但缺對接點或單例重複）

| 子系統 | 元件 | 問題 |
|---|---|---|
| 座標軸 | `core/state/axis.py` + `axis_field.py` + `eta_axis.py` + `axis_port_registry.py` | **4 檔案分裂**，無統一介面 |
| θ 路由 | `core/engine/theta_router.py` | **空參數實例化**（prompt_builder L49 `ThetaRouter()`）→ theta_values 回傳 `{}` |
| θ 三件套 | `port_channel.py` / `axis_port_registry.py` / `state_matrix_adapter.py` | 僅 docstring/playground，**request path 全未接** |
| 學習整合 | `ai/ed3n/learning_integration.py` | chat_service 有接（synchronize_knowledge） |
| 字典 | `ai/ed3n/dictionary_layer.py` + `ai/garden/dictionary.py` | 各自獨立介面，需統一 |
| 深度字典 | `ai/ed3n/continuous_learning.py` | 有接（load/save） |
| 外部分支 | `core/life/cyber_identity.py`、`self_generation.py`、`evolution_engine.py`、`tickle_reflex_system.py` | 僅 autonomous facade / bio re-export |
| 感知 | `core/perception/*.py`（visual/auditory sampler, attention） | vision_service/audio_service 用，**與 StateMatrix4D 無接線** |
| 生物細節 | `core/bio/`（endocrine, tactile, emotional_blending, cerebellum, habit, trauma, hormone_kinetics） | 被 DLI/heartbeat 用，但無統一主幹線對接 |
| DLI 記憶橋 | `core/bio/memory_neuroplasticity_bridge.py` | **`DLI.memory_bridge = None` 從未賦值** → trigger_consolidation 全 no-op |
| 落地記憶 | `ai/memory/cognitive_pipeline.py`、`attractor_field.py` | 僅 lab/playground，**生產未用** |
| 決策記憶 | `ai/lifecycle/llm_decision_loop.py` | 需 `get_recent_memories` 但 HAM 無此法 → hasattr 靜默跳過 |
| 協調整合 | `ai/lifecycle/memory_integration_loop.py`、`proactive_interaction_system.py`、`behavior_feedback_loop.py` | **全庫無實例化**（設計有但沒接） |
| LLM 決策 import | `ai/core/dynamic_threshold_manager.py:455` | **import 路徑錯**（services.llm.llm_decision_loop 不存在）→ 被 except ImportError 吞 |
| 協調器記憶 | `ai/memory/unified_memory_coordinator.py` | 呼叫 `query_core_memory` 但 HAM 無此法 |
| 記憶整合 | `ai/context/integration_with_ham.py` | **HAM import 全註解**（dead） |

#### 🔴 死碼 / 孤兒（無 production 消費者，設計時不可假設存在）

| 子系統 | 元件 | 說明 |
|---|---|---|
| 頂層安全 | `security/`（audit_logger, content_filter, permission_control, safety_audit） | **4 檔全孤兒**，僅測試引用 |
| HTTP 安全 | `core/security/AuthMiddleware` | DORMANT（FastAPI 無 auth dependency）；`setup_middleware()` 只有 CORS |
| 簽章 | `shared/security_middleware.SignedCommunicationMiddleware` | 定義但從未註冊（no-op） |
| 密鑰 | `shared/key_manager.UnifiedKeyManager` | **從未實例化**；`set_key_manager()` 無人呼叫 |
| MCP | `mcp/connector.py` | **production 零使用**，僅測試 |
| 監控 | `monitoring/system_monitor.py` | ops_routes 用內聯 psutil，不經它 |
| 遊戲 | `game/`（12 檔） | **完全獨立死碼**，無 AI core 接線 |
| 片段 | `fragmenta/`（4 檔） | src 內無任何 import |
| 模型 | `models/api_models.py` + `services/api_models.py` shim | 無 production route 使用 |
| 熱載入 | `services/hot_reload_service.py` | 孤兒 |
| LLM shim | `services/angela_llm_service.py` | re-export shim |
| 幽靈 | `core/metacognition/`、`core/ethics/`、`core/evolution/`、`core/feedback_loop_engine.py` | docstring-only stub |
| 事件 | `core/event_loop_system.py` | 自稱 DEPRECATED，production 零引用 |
| 監控實時 | `core/real_time_monitor.py`（1,162L） | 無人用 |
| 變形 | `core/metamorphosis/`、`core/maturity/`、`core/clock/`、`core/hardware/`、`core/desktop/`、`core/card/`、`core/ripple/`、`core/influence/`、`core/knowledge/` | 僅 core/__init__ lazy export 或 tests |
| 上下文 lab | `ai/context/manager_fixed.py`、`model_context.py`、`tool_context.py`、`config.py`、`storage/*` | 僅 demo_context_system 使用 |
| 記憶重複 | `ai/memory/importance_scorer.py`（根目錄版） | 與 ham_memory 版重複，無消費者 |
| 執行橋 | `core/action_execution_bridge.py` | 半活（僅 action_executor 用） |
| router 死碼 | `router.py` L747-771 `_try_action_router`/`_try_router_chain`、L772 `_try_agent_routing` | 定義但 generate_response 鏈未呼叫 |
| MQTT | `core/hsp/fallback/fallback_protocols.py` HTTPProtocol、`MessageBridge`、`DataAligner`、`StreamSynthesizer` | stub 或未連通路徑 |

### 11.3 主幹線設計必須處理的「重複/斷點」清單

| # | 問題 | 影響 | 主幹線處理 |
|---|---|---|---|
| 1 | `StateMatrix4D` **兩個來源**（DLI 持有 + chat_routes fallback） | 狀態不一致 | 主幹線單一註冊矩陣 |
| 2 | `HAMMemoryManager` **4+ 實例**（router/chat_service/drive/DLI） | 記憶分片 | `backbone.memory("ham")` 統一單例 |
| 3 | `ThetaRouter()` **空參數實例化** | θ 狀態永不進 prompt | backbone 注入 state_adapter + port_registry |
| 4 | CNS **domain 無訂閱者**（StateMatrix4D 同步後無人讀） | 事件匯流排半空轉 | backbone state.py 統一訂閱 |
| 5 | `StateMatrix4D` **無 theta/zeta 寫入者** | 8 維只更新 6 維 | 主幹線補 theta 路由寫回 |
| 6 | `DLI.memory_bridge = None` 從未賦值 | consolidation no-op | backbone 接 memory_neuroplasticity_bridge |
| 7 | `dynamic_threshold_manager.py:455` import 路徑錯 | feedback_aggregator=None | 修路徑（ai/lifecycle/） |
| 8 | HAM 缺 `get_recent_memories`/`retrieve_emotional_memories`/`query_core_memory` | LLMDecisionLoop 記憶拿不到 | 補方法或改呼叫 |
| 9 | LLM 主聊天**無 stream**（TokenStream 未接 LLM） | 無法流式輸出 | 步驟 C 可選：StreamSynthesizer 啟用 |
| 10 | 安全層**不在 HTTP 層也不在核心層** | auth/filter 未生效 | backbone 下層掛載 security |

### 11.4 學習/訓練/外部調用完整接線圖（含本盤點補全）

```
外部世界 (LLM providers×9 / weather / drive / search / atlassian / OS bridge / MCP)
   ▲                                   │
   │ call_external (Retry+熔斷)        │ response / 學習來源
   ▼                                   ▼
┌─ 主幹線下層 外部閘道 (external.py) ─────────────────────────────────┐
│  LLM providers 有統一介面 ✅ | weather/drive/search 需收斂 🔧       │
│  RetryPolicy+CircuitBreaker 已有 ✅ (HSP 唯一消費)                  │
└───────────────┬──────────────────────────────────────────────────┘
                │ Envelope (kind/modality/payload/state/meta)
┌─ 主幹線中層 ──┼──────────────────────────────────────────────────┐
│  LearningCoordinator (learning.py)                               │
│  · continuous_learning ✅ / learning_loop ✅ / learning_orchestrator ✅ │
│  · 目前由 chat_service L201-202 內嵌觸發 🔧 → 改 CNS 事件驅動       │
│  · memory_integration_loop / proactive_interaction 未接 🔴         │
│  字典 registry: DictionaryLayer ✅ / VectorDictionary ✅            │
│  模組 registry: EmotionSystem / IntentModel / ExecutionGate /     │
│                AgentManager / Crisis / CausalReasoning             │
└───────────────┬──────────────────────────────────────────────────┘
                │ 轉譯 (neural_bridge + semantic_key_mapper)
┌─ 主幹線上層 ──┼──────────────────────────────────────────────────┐
│  TrainingCoordinator (training.py)                               │
│  · ed3n_trainer ✅ / training_pipeline(6 trainers) ✅ / garden ✅  │
│  · 目前僅 CLI/scripts 離線觸發 🔧 → mount/unmount 包裝             │
│  Core Matrix (StateMatrix4D) ↔ Free Matrix (SharedLatentSpace)    │
│  Axes (統一介面, 目前 4 檔案分裂 🔧)                                │
└───────────────┴──────────────────────────────────────────────────┘
```

### 11.5 盤點後新增的遷移項目（追加到 §7 步驟）

| 步驟 | 追加項目 |
|---|---|
| A | 建立 `Backbone` 時一併註冊：`GlobalStateStore`（CNS）、`service_registry`、`get_lifecycle()` |
| A | 記憶統一：`backbone.memory("ham")` 取代 4+ 個 `HAMMemoryManager()` 實例 |
| A | **成對排程核心（§5.0）**：`pairs.py` 合併 `WaitingScheduler` + `IOPair`/`PairScheduler`/`PairState` |
| B | 修 3 個已知 bug：`dynamic_threshold_manager:455` import、HAM 缺 3 方法、`DLI.memory_bridge=None` |
| B | `ThetaRouter` 注入 state_adapter + port_registry（解鎖 θ 狀態進 prompt） |
| B | CNS domain 訂閱：`backbone.state.subscribe("core")` 取代 composer/router 的 update_state |
| B | **成對追蹤套用**：`call_external`/CNS `emit_event`/`ExecutionGate` 工具呼叫包 `backbone.io`（§5.0.5）|
| B | **響應模式選取器（§5.6）**：`response.py` 包 `router.generate_response`（1:1）+ `StreamingPipeline`（layered）+ `TokenStream`（stream），請求層級選模式、不中途切換 |
| C | 安全層掛載：`setup_middleware()` 掛 AuthMiddleware + ContentFilter（下層入口） |
| C | `StreamSynthesizer` 啟用（LLM 流式）——**可選**，不阻塞主線 |
| C | **主聊天接 stream（§5.6.4）**：LLM provider 接 `TokenStream`，`mode="stream"` 才走——**可選** |
| 清理 | 死碼移除：`game/`、`fragmenta/`、`models/api_models.py`、`mcp/connector.py`、`security/`（或重新掛載）、`core/event_loop_system.py`、4 個幽靈 stub |

### 11.6 盤點涵蓋範圍聲明

本次盤點涵蓋：`ai/`（memory/context/lifecycle/meta/agents/multimodal/ed3n/garden/
streaming）、`core/`（life/bio/engine/state/security/perception/autonomous/tracing/
allocation/card/i18n/plugin/ripple/influence/maturity/knowledge/evolution/ethics/
metacognition/metamorphosis/desktop/hardware/clock/feedback）、`services/`
（頂層 + llm + handlers + api）、`api/`（routes + lifespan + v1/endpoints）、
`shared/`、`security/`、`mcp/`、`monitoring/`、`game/`、`fragmenta/`、`models/`、
`utils/`、`cli/`、`integrations/`。

**未涵蓋**（基礎設施，不影響主幹線接線設計）：`core/hsp` 內部細節（已在 §11.2 標記）、
`core/system/`（bootstrap/config/module_manager）、`core/config/`、`core/api/`、
`core/sync/`、`core/tools/`、`core/managers/`、`core/error/`、`core/logging/`、
`core/interfaces/`、`core/database/`、`core/services/`、`core/art/`。這些屬橫切
基礎設施，若後續需要對接再個別補盤點。

> **完整性結論**：核心主幹線所需元件（矩陣/軸/自由矩陣/字典/模組/學習/訓練/外部閘道/
> 記憶/上下文/CNS/WS）**全部已盤點**。設計可直接進入 §7 步驟 A 實作。
