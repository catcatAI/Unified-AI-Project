# 多角色扮演架構（Multi-Role Play）

> **這份文件是什麼**：多角色系統的**對外契約與內部接線**——一個請求怎麼變成「某個角色的回答」，記憶怎麼分區，舞台怎麼同步，以及哪些地方刻意不做。
>
> **這份文件不是什麼**：不是計畫（那是
> `plans/MULTI_ROLE_PLAY_AGENT_PLAN.md`）、不是舞台規格（那是
> `plans/INTERACTIVE_SPACE_PLAN.md`）。
>
> - 作者：Angela AI Development Team
> - 版本：7.5.0-dev
> - ANGELA-MATRIX：`[L3-L4] [βγδ] [B] [L3]`
> - 日期：2026-10-28

---

## 1. 一層一層看

```
HTTP  POST /chat/unified { role_id }        POST /chat/group { role_ids[] }
        │                                    │
        ▼                                    ▼
   _apply_role_binding(context)          （每個 role 各跑一次左邊的路徑，session 分離）
        │  _role_id
        │  _force_backend_slot   ──→ router._choose_backend()（先於 dual-model 選路）
        │  _memory_namespace     ──→ ChatService 召回 / 寫入
        │  _role_persona         ──→ prompt_builder._append_role_persona()
        ▼
   LLM response  →  response.metadata["role_id"]

WebSocket  /ws/space  ⇄  SpaceService（舞台狀態）  ⇄  browser SpacePort
```

四條線各自可測、可關：

| 線       | 模組                                                           | 沒有它會怎樣                     |
| -------- | -------------------------------------------------------------- | -------------------------------- |
| 角色登錄 | `ai/roleplay/runtime.py` + `configs/system/roles.default.yaml` | `role_id` 一律 400               |
| 模型綁定 | `services/llm/router.py::_choose_backend`                      | 角色用預設模型（聲音對、腦子錯） |
| 記憶分區 | `ai/memory/vector_store.py` + `ham_manager.py`                 | 角色互相污染記憶                 |
| 人格文字 | `services/llm/prompt_builder.py::_append_role_persona`         | 換了模型仍講 Angela 的話         |

---

## 2. 角色從哪裡來

**伺服器端設定，不是請求內容。** 客戶端只能選 `role_id`，不能定義角色。

```yaml
# apps/backend/configs/system/roles.default.yaml
roles:
  - role_id: main
    display_name: Angela
    context_scope: shared # shared = 主 AI，擁有共享基底
    memory_namespace: main
    shared_memory_write: true
  - role_id: role_b
    display_name: Gemma 角色
    context_scope: private
    backend_slot: llamacpp-gemma # 必須對應已註冊的 backend id
    memory_namespace: role_b
  - role_id: role_d
    display_name: DeepSeek 角色
    context_scope: private
    backend_slot: deepseek # 需要 DEEPSEEK_API_KEY；沒 key 就回退 active
    memory_namespace: role_d
```

已註冊的槽（`llm.default.yaml`）：`llamacpp-local`、`llamacpp-qwen`、`llamacpp-gemma`（預設關）、
`ollama-llama3`、`openai-gpt4`、`deepseek-chat`（有 key 才註冊）、`anthropic-claude`、`google-gemini`、`unified-1g`。

三個本地模型同時跑（Arc B570 實測）見
[`LOCAL_THREE_MODELS.md`](LOCAL_THREE_MODELS.md)：`main`=Qwen2.5-3B、`role_b`=Gemma-2-2B、
`role_c`=Llama-3.2-1B，共 6.34 GB VRAM（9.44 GB 的 70%），啟動與還原由
`scripts/run_local_three_models.py` 負責。

- 未知 id → `400 unknown role: <id>`（不靜默回 Angela）。
- `backend_slot` 找不到對應 backend →
  router 記 log 並回退正常選路（刪模型不該讓聊天癱瘓）。
- 第二個 `context_scope: shared`
  的角色在註冊時就被拒（兩個主 AI 會讓「誰擁有基底」無定義）。

---

## 3. API 契約

### 3.1 `POST /api/v1/chat/unified`

```json
{ "message": "你好", "role_id": "role_b", "user_id": "u1", "session_id": "s1" }
```

- `role_id` 可選。沒有它 = 原本的單一人格行為（逐字不變）。
- 回應多一個 `context._role_id`；`response.metadata.role_id` 由 router 蓋章。

### 3.2 `POST /api/v1/chat/group`

```json
{ "message": "今天怎麼樣？", "role_ids": ["main", "role_b", "role_c"] }
```

```json
{
  "session_id": "group::ab12cd34",
  "role_ids": ["main", "role_b", "role_c"],
  "replies": { "main": {...}, "role_b": {...}, "role_c": {...} }
}
```

- 上限 4 個角色；重複 id 會去重；空陣列或非陣列 → 400。
- 每個角色跑**完整**
  pipeline（驗證／數學／危機／執行閘門），不是繞過安全層的捷徑。
- session 以 `{base}::{role_id}` 隔離，一份 transcript 不會滲進另一份。
- **循序**執行：延遲隨角色數線性成長（並行要解共享基底的寫入順序，還沒做）。

### 3.3 `WS /ws/space`

```
server → client  {"type": "space.snapshot", "rev": 3, "data": {"room_id": ..., "actors": [...]}}
client → server  {"type": "space.action", "data": {"type": "say", "actor_id": "role_b", "text": "..."}}
client → server  {"type": "space.ping"}  →  {"type": "space.pong"}
server → client  {"type": "space.error", "message": "..."}
```

- 連上先送快照；每個 action 套用後把新快照廣播給同房間的所有連線。
- 壞訊息只回 `space.error`，**不斷線**。
- 啟動時用 `space/roles.json` 種舞台；`SPACE_SEED_ROLES=0` 可關。
- 已知限制：**整房廣播**，`visible_to` 目前只是前端渲染提示，不是安全邊界。

---

## 4. 記憶分區

`namespace` 是**硬分割**，不是排名偏好：

| 地方                                                  | 行為                                                             |
| ----------------------------------------------------- | ---------------------------------------------------------------- |
| `VectorMemoryStore.add_memory(..., namespace=)`       | 寫進 `metadata["namespace"]`；明示 metadata 優先                 |
| `VectorMemoryStore.semantic_search(..., namespace=)`  | numpy backend 先篩索引再排名；chroma 用 `where={"namespace": …}` |
| `HAMMemoryManager.store_experience(..., namespace=)`  | 同上，寫進 `metadata`                                            |
| `HAMMemoryManager.query_core_memory(..., namespace=)` | 只回該 namespace；未標的舊資料不混入                             |

沒有角色時**不傳**參數（不是傳 `None`），所以舊的自訂 store / 測試替身不受影響。

---

## 5. 失敗模式

| 情況                  | 行為                           | 為什麼                           |
| --------------------- | ------------------------------ | -------------------------------- |
| 未知 `role_id`        | 400，不回答                    | 錯的聲音比錯誤更糟               |
| `backend_slot` 不存在 | log + 回退預設選路             | 刪模型不該讓聊天癱瘓             |
| 記憶寫入失敗          | log，回覆照送                  | 記憶是 best-effort               |
| 舞台 WS 斷線          | 前端自動重連；連不上留本機模式 | 「沒有後端」是一種模式，不是壞掉 |
| 舞台快照缺演員        | 該演員從本機移除               | 避免別人關掉視窗後留下幽靈       |

---

## 6. 刻意不做

- 不做角色市場／使用者自建角色（角色是伺服器設定）。
- 不做角色之間的自主對話迴圈（`/chat/group` 是「同一題問所有人」）。
- 不做 per-viewer 快照（私密舞台要等 S2）。
- 不做跨進程角色註冊（registry 是 process-local singleton）。

---

## 7. 測試地圖

| 檔案                                                | 守什麼                                               |
| --------------------------------------------------- | ---------------------------------------------------- |
| `tests/ai/roleplay/test_role_model.py`              | Role/RoleContext 資料契約                            |
| `tests/ai/roleplay/test_role_play_agent.py`         | 強制 slot、persona 注入、降級路徑                    |
| `tests/ai/roleplay/test_multi_role_orchestrator.py` | 註冊、群組輪次、共享/私有                            |
| `tests/ai/roleplay/test_runtime.py`                 | 角色設定載入、未知 id                                |
| `tests/ai/memory/test_memory_namespace.py`          | 記憶硬分割（含重啟後仍在）                           |
| `tests/services/llm/test_role_backend_slot.py`      | router 選路與 metadata 蓋章                          |
| `tests/services/llm/test_role_persona_prompt.py`    | 人格文字真的進 system prompt                         |
| `tests/api/test_chat_role_binding.py`               | HTTP → context 綁定                                  |
| `tests/api/test_multi_role_chat.py`                 | /chat/unified 與 /chat/group 端到端（pipeline stub） |
