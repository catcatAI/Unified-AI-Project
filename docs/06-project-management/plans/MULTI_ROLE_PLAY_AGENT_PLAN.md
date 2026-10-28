<!--
  =============================================================================
  ANGELA-MATRIX: L3 [βγ] [B] [L4]
  FILE_PATH: docs/06-project-management/plans/MULTI_ROLE_PLAY_AGENT_PLAN.md
  FILE_TYPE: planning
  PURPOSE: Multi-role-play with shared vs isolated contexts, per-role model
           binding, implemented via RolePlayAgent + MultiRoleOrchestrator.
  VERSION: 1.0.0-draft
  STATUS: draft
  LANGUAGE: zh-TW (technical terms in English)
  LAST_MODIFIED: 2026-10-28
  AUDIENCE: developers, product
  =============================================================================
-->

# 多角色扮演 + 共享/隔離上下文 + 模型綁定 計畫書

> **目標**：讓 Angela AI 支援「主 AI（共享上下文，角色 A）+ 角色 B（隔離上下文，Gemma 4 2B）+ 角色 C（隔離上下文，Qwen 3 1.5B）」的多角色扮演場景，並可擴展到 N 個角色，每個角色可綁定不同模型、不同 persona、不同記憶命名空間。

> **使用者原始需求**：Gemma 4 2B + Qwen 3 1.5B，然後做共享上下文（主 AI，角色扮演 A）+ 角色扮演 B（分隔上下文（Gemma 4 2B））+ 角色扮演 C（分隔上下文（Qwen 3 1.5B））。

> **狀態**：draft（規劃階段，尚未實作；需切換到 Build agent 才能動檔）。

---

## 0. 已確認的現狀（不再重查）

### 0.1 模型層（已具備多後端能力）

- 多後端註冊：`apps/backend/configs/system/llm.default.yaml` 的 `backends:` 區，支援 `unified / llama_cpp / ollama / openai / anthropic / google`。
- 雙模型分流已實作：`services/llm/router.py::_select_light_backend()` — 簡單問句自動走 executor (qwen)，複雜走 thinker (gemma)；健康快取 60s。
- 雙模型預設已存在：`apps/backend/configs/presets/dual_model.preset.yaml` — thinker=gemma-4-E2B-it (:8080), executor=qwen2.5-0.5b-instruct (:8081)，adapters 插槽狀態 `research`。
- 模型選擇入口：`AngelaLLMService.generate_response(user_message, context)`，`context` 可帶 `_used_backend_type`、`force_llm`、`use_ensemble` 等旗標；`_call_llm_backend()` 內部呼叫 `_select_light_backend()` 決定 light backend。
- **結論**：Gemma 4 2B / Qwen 3 1.5B 只要透過 Ollama/llama.cpp 跑起來就能接入，無需改模型層；缺的是「角色 → 模型」的綁定。

### 0.2 上下文層（session 隔離已具備，但無共享/私有分層）

- `ai/context/dialogue_context.py`：`DialogueContextManager`，`_MAX_CONVERSATIONS=100`，每 conversation 獨立 `messages`，LRU 淘汰。
- `api/routes/chat_routes.py::_handle_chat_request()`：以 `session_id` 為 key，`messages` 獨立持久化，多輪記憶；`_run_chat_pipeline(..., mode="1:1")`。
- `services/llm/context_scheduler.py`：`ContextLedger` 長程一致性帳本、`digest_overflow_sync`、`digest_with_llm`；保護 system 與最終 user，中段訊息消化。
- **結論**：session 級隔離已存在；缺「shared base context + per-role overlay + 可見性規則」。

### 0.3 角色/Persona 層（全域單例，無多實例）

- `core/card/capabilities/roleplay_engine.py`：`RoleplayEngine.activate(card)` 把一張 Card 載入全域 `PersonalityAdapter`；`active_card` 單一。
- `ai/persona/persona_engine.py`：`PersonaEngine` 是 singleton (`get_persona_engine()`)，`current_state` 單一；`adapt_tone_from_al_state()` 調整語氣。
- `core/card/integration/personality_adapter.py`：`PersonalityAdapter.load_card()`。
- **結論**：角色卡系統存在，但 persona 是全域的，同時跑 B/C 會互相覆寫 tone/state。

### 0.4 代理層（基建最完整，但任務導向）

- `ai/agents/agent_manager.py`：AgentManager，支援 IN_PROCESS / SUBPROCESS / REMOTE，生命週期、監控、HSP 路由。
- `ai/agents/dynamic_agent_registry.py`：動態註冊。
- `ai/agents/agent_orchestrator.py`：意圖→代理路由，含 `"roleplay": "fantasy_dm_agent"`；`dispatchable_agent_ids()`。
- `ai/agents/agent_collaboration_manager.py`：HSP 非同步任務分派/結果回收。
- `ai/agents/agent_adapter.py`：把 specialized agent 包成 `execute(task)` 介面。
- `ai/agents/base/base_agent.py`：HSP 連線、佇列、重試。
- `ai/agents/specialized/fantasy_dm_agent.py`：RPG 場景生成，`handle_request()` 解析自然語言。
- **結論**：代理基建成熟，但 agent 是「任務處理器」，不是「對話角色」；沒有 per-agent 對話歷史、persona state、模型綁定。

### 0.5 記憶層（全域，無命名空間）

- HAM memory (`ai/memory/ham_memory/ham_manager.py`)、vector store (`ai/memory/vector_store.py` / `vector_memory_store.py`) 全域儲存。
- `_inject_memory_context()` / `_inject_ham_context()` 在 chat pipeline 中注入。
- **結論**：角色 B 的對話會汙染角色 C 的檢索；需加 namespace 過濾。

### 0.6 前端（單一 Live2D 角色）

- `apps/desktop-app/electron_app/libs/shared-js/live2d-manager.js`、`angela-character-config.js`：單模型。
- Archived analysis (`docs/09-archive/MULTI_PERSPECTIVE_ANALYSIS.md`) 明確標註：`[MEDIUM] Single model limit per session — Cannot create character switching or ensemble scenarios`。
- **結論**：前端多角色放後期；API/文字層先行。

### 0.7 既有相關計畫（無直接對應）

- `docs/06-project-management/plans/STREAMING_WINDOW_DUALMODEL_PLAN.md`：雙模型分流（thinker/executor），但按任務難度，非角色。
- `docs/09-archive/auto-archived-2026-08-11/ANGELA_CARD_INTEGRATION_PLAN.md`：Card 整合，RoleplayEngine 已用但 pipeline 未接。
- `docs/04-advanced-concepts/agent-collaboration.md`：多代理協作，任務導向。
- **結論**：roadmap 上沒有「多角色扮演 + 上下文隔離 + 模型綁定」的明確項目；本計畫填補此缺口。

---

## 1. 設計哲學

1. **角色是一等公民，不是 persona 的切換**：不要在全域 `PersonaEngine` 上切換 card；每個角色是獨立實體，持有自己的 persona state、對話歷史、模型綁定、記憶命名空間。
2. **Agent 是載體，不是任務**：復用 AgentManager/Registry/Monitoring 的生命週期基建，但角色代理的 `respond()` 是對話回合，不是 HSP task；對話路徑走 in-process 直接呼叫，避免 HSP envelope 的延遲與複雜度。
3. **上下文分層，不複製**：共享基底 (main AI view) 是 single source of truth；角色私有上下文是 overlay/delta，不是完整副本；避免 N 倍記憶體與一致性問題。
4. **模型綁定是強制的，不是偏好**：角色宣告 `backend_slot`，路由器在該角色的請求路徑上強制使用該 slot，繞過 `_select_light_backend` 的問句分流；`preferred_backend` (使用者偏好) 仍可覆寫，但預設按角色。
5. **記憶命名空間是隔離的，共享是顯式的**：預設 `namespace=role_id`；只有標記 `shared=true` 的記憶才進入共享基底；角色 B 的私人對話不會汙染主 AI 或角色 C。
6. **前端最後**：先做 API/文字層 + 測試；Live2D 多角色放 Phase 4 之後。

---

## 2. 核心資料模型

### 2.1 Role 資料類

新增 `apps/backend/src/ai/roleplay/role.py`（或擴充 `ai/agents/specialized/`）：

```python
@dataclass
class Role:
    role_id: str                          # "main" / "role_b" / "role_c"
    display_name: str                     # "Angela" / "Gemma 角色" / "Qwen 角色"
    persona_card_id: Optional[str]         # Card.qualified_id
    persona_state: PersonaState            # per-role，不共用 singleton
    backend_slot: Optional[str]           # "llamacpp-gemma" / "llamacpp-qwen" / None (用 active)
    context_scope: ContextScope            # SHARED / PRIVATE / HYBRID
    memory_namespace: str                  # 預設 = role_id
    shared_memory_read: bool = True        # 能讀共享基底記憶？
    shared_memory_write: bool = False      # 能寫共享基底記憶？(主 AI 才 true)
    conversation_id: Optional[str] = None  # 對應 dialogue_context 的 conversation
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None
```

### 2.2 ContextScope 列舉

```python
class ContextScope(Enum):
    SHARED = "shared"      # 完全共享主 AI 上下文 (角色 A = main)
    PRIVATE = "private"    # 完全隔離 (角色 B/C 預設)
    HYBRID = "hybrid"      # 讀共享基底 + 自己的 private overlay
```

### 2.3 RoleContext (上下文分層)

```python
@dataclass
class RoleContext:
    role_id: str
    shared_base: List[Dict[str, Any]]      # 主 AI 共享底層 (reference, not copy)
    private_overlay: List[Dict[str, Any]]  # 角色私有訊息 (delta)
    visible_to: Set[str]                   # 哪些角色可讀此 overlay (預設 {self})
    token_budget: int                     # 該角色的 token 預算
```

合併邏輯：`merged = shared_base (filtered by visibility) + private_overlay`，再經 ContextScheduler 消化。

### 2.4 ModelSlot 映射

在 `llm.default.yaml` 或 preset 中定義 slot → backend id：

```yaml
role_slots:
  main: null            # 用 active backend (thinker)
  role_b: llamacpp-gemma
  role_c: llamacpp-qwen
```

或在 Role 註冊時直接指定 `backend_slot`。

---

## 3. 架構：RolePlayAgent + MultiRoleOrchestrator

### 3.1 RolePlayAgent (新類，繼承 BaseAgent)

位置：`apps/backend/src/ai/agents/specialized/role_play_agent.py`（或 `ai/roleplay/role_play_agent.py`）。

```python
class RolePlayAgent(BaseAgent):
    def __init__(self, role: Role, llm_service, dialogue_ctx, memory_manager):
        super().__init__(agent_id=f"role_{role.role_id}", agent_name=role.display_name)
        self.role = role
        self._llm = llm_service
        self._dialogue = dialogue_ctx
        self._memory = memory_manager
        # per-role persona engine instance (not singleton)
        self._persona = PersonaEngine()  # 可載入 role.persona_card_id

    async def respond(self, user_message: str, shared_context: List[Dict]) -> LLMResponse:
        # 1. 建立 merged context
        merged = self._build_merged_context(user_message, shared_context)
        # 2. 模型綁定：強制 backend_slot
        ctx = dict(merged)
        ctx["_force_backend_slot"] = self.role.backend_slot  # 新旗標
        ctx["_role_id"] = self.role.role_id
        ctx["_memory_namespace"] = self.role.memory_namespace
        # 3. persona 注入
        ctx["persona_injection"] = self._persona.get_persona_prompt_injection(...)
        # 4. 呼叫 LLM (in-process，不走 HSP)
        resp = await self._llm.generate_response(user_message, ctx)
        # 5. 持久化到 private overlay
        self._record_turn(user_message, resp)
        # 6. 記憶寫入 (namespace)
        if self.role.shared_memory_write:
            await self._memory.store(..., namespace="shared")
        await self._memory.store(..., namespace=self.role.memory_namespace)
        return resp

    def _build_merged_context(self, user_message, shared_context):
        if self.role.context_scope == ContextScope.SHARED:
            return list(shared_context)
        if self.role.context_scope == ContextScope.PRIVATE:
            return list(self._private_history())
        # HYBRID
        visible_shared = [m for m in shared_context if self._visible(m)]
        return visible_shared + self._private_history()
```

### 3.2 MultiRoleOrchestrator (新類)

位置：`apps/backend/src/ai/roleplay/multi_role_orchestrator.py`。

```python
class MultiRoleOrchestrator:
    def __init__(self, llm_service, dialogue_ctx, memory_manager, agent_manager):
        self._llm = llm_service
        self._dialogue = dialogue_ctx
        self._memory = memory_manager
        self._agent_manager = agent_manager
        self._roles: Dict[str, RolePlayAgent] = {}
        self._shared_context: List[Dict] = []   # 主 AI 共享底層

    def register_role(self, role: Role) -> RolePlayAgent:
        agent = RolePlayAgent(role, self._llm, self._dialogue, self._memory)
        # 註冊進 AgentManager (復用生命週期)
        self._agent_manager.register_agent(agent.agent_id, agent, capabilities=[...])
        self._roles[role.role_id] = agent
        return agent

    async def turn(self, user_message: str, target_role_id: Optional[str] = None) -> Dict[str, Any]:
        # 1. 主 AI (shared context) 先處理/路由
        main_resp = await self._main_respond(user_message)
        self._shared_context.append({"role": "user", "content": user_message})
        self._shared_context.append({"role": "assistant", "content": main_resp.text, "role_id": "main"})
        # 2. 若指定 target role，該角色回應
        results = {"main": main_resp}
        if target_role_id and target_role_id in self._roles:
            role_resp = await self._roles[target_role_id].respond(user_message, self._shared_context)
            results[target_role_id] = role_resp
        # 3. 或「ensemble」模式：所有角色都回應 (group chat)
        return results

    async def group_turn(self, user_message: str) -> Dict[str, LLMResponse]:
        results = {}
        for rid, agent in self._roles.items():
            results[rid] = await agent.respond(user_message, self._shared_context)
        # 主 AI 彙總
        results["main"] = await self._main_summarize(user_message, results)
        return results
```

### 3.3 路由器改動 (最小侵入)

在 `services/llm/router.py`：

1. `_call_llm_backend()` 內，在 `_select_light_backend()` 之前，檢查 `context.get("_force_backend_slot")`：
   ```python
   forced_slot = context.get("_force_backend_slot")
   if forced_slot:
       backend = self.backends.get(self._slot_to_backend_type(forced_slot))
       if backend is not None and await self._health_check(forced_slot):
           light_backend, light_type = backend, self._slot_to_backend_type(forced_slot)
   ```
2. `_inject_memory_context()` / `_inject_ham_context()` 傳入 `namespace=context.get("_memory_namespace", "default")`。
3. `context["_role_id"]` 寫入 response metadata，供前端/日誌追蹤。

### 3.4 記憶層改動 (最小侵入)

- `HAMMemoryManager.query_core_memory()` / `store()` 加 `namespace: Optional[str] = None` 參數；預設 None = 全域 (向後相容)。
- `VectorMemoryStore` 同樣加 namespace 過濾 (metadata filter)。
- `_inject_ham_context()` / `_inject_vector_context()` 讀 `context.get("_memory_namespace")`。

### 3.5 對話上下文改動

- `DialogueContextManager.start_conversation()` 已支援 `conversation_id`；為每個 role 建立獨立 conversation_id：`f"{base_session}:{role_id}"`。
- `RolePlayAgent._record_turn()` 寫入自己的 conversation_id。

### 3.6 API 層

新增端點 (或擴充 `/api/v1/chat`)：

- `POST /api/v1/roles` — 註冊角色 (role_id, display_name, persona_card_id, backend_slot, context_scope, memory_namespace)。
- `GET /api/v1/roles` — 列出角色。
- `DELETE /api/v1/roles/{role_id}` — 註銷。
- `POST /api/v1/chat/multi` — 多角色回合：body `{user_message, target_role_id?, mode: "single"|"group"}`。
- `GET /api/v1/roles/{role_id}/context` — 查看角色的 private overlay (debug)。

或更簡單：擴充既有 `/chat/unified`，加 `role_id` / `group` 參數，向後相容。

---

## 4. 實作階段 (Phased Plan)

### Phase 0 — 基礎資料模型 (1-2 天) ✅ 2026-10-28

- [x] P0-1 建立 `apps/backend/src/ai/roleplay/` 套件 (`__init__.py`, `role.py`, `context.py`)。
- [x] P0-2 實作 `Role` dataclass + `ContextScope` + `RoleContext`。
- [x] P0-3 單元測試 `tests/ai/roleplay/test_role_model.py` (25 tests)：資料類驗證、scope 列舉、預設值、可見性過濾、預算估算。
- [x] P0-4 確認 `PersonaEngine` 可實例化多份：`get_persona_engine(role_id=None)` 無參數仍是原本的 singleton（向後相容），給 `role_id` 則回傳 per-role 快取實例。

> 落地備註：`RoleContext` 目前只管「誰看得到哪些訊息」與 token 估算；真正餵給 LLM 前的截斷與排序，屬 Phase 1 的 ContextScheduler。

### Phase 1 — RolePlayAgent + 記憶命名空間 (2-3 天) — 進行中

- [x] P1-1 實作 `RolePlayAgent(BaseAgent)`，持有 per-role persona、conversation、backend_slot。
- [x] P1-2 `respond()` 方法：merged context → 強制 backend_slot → persona 注入 → LLM 呼叫 → private overlay（記憶體內）。**落盤/重啟倖存與 P1-3 的 HAM namespace 一起接**；LLM 與記憶都走注入 seam（`llm_service` / `memory_writer`），P1-3 不必改這個檔。
- [ ] P1-3 HAM/vector store 加 `namespace` 參數 (向後相容，預設 None)。
- [ ] P1-4 chat pipeline `_inject_*_context()` 讀 `context["_memory_namespace"]`。
- [x] P1-5 單元測試 `tests/ai/roleplay/test_role_play_agent.py` (28 tests)：fake LLM / fake memory，驗證 backend_slot 強制、namespace、private overlay、降級路徑。

### Phase 2 — MultiRoleOrchestrator + 路由器改動 (2-3 天)

- [x] P2-1 實作 `MultiRoleOrchestrator`：register/unregister role、turn()、group_turn()。**未接路由器**：group_turn 依註冊順序循序執行，主 AI 的回覆在同一輪就進共享基底，後面的角色讀得到；第二個 SHARED 角色會被擋。
- [x] P2-2 路由器 `_call_llm_backend()` 加 `_force_backend_slot` 檢查 (在 `_select_light_backend()` 之前)。實作落在 `_choose_backend()`：強制槽用 exact token 比對（`llamacpp-qwen` 不會掉到 `llamacpp`），未知槽只記 log 並回退正常選路，不會讓聊天壞掉。
- [x] P2-3 路由器 metadata 寫入 `_role_id`。落地為 `context["_role_id"]` → `response.metadata["role_id"]`（`setdefault`，不覆寫既有值；metadata 鍵沿用既有無底線慣例）。
- [ ] P2-4 整合進 chat_routes：`_run_chat_pipeline` 接 `role_id`/`group` 參數。
- [ ] P2-5 單元 + 整合測試 `tests/ai/roleplay/test_orchestrator.py` + `tests/api/test_multi_role_chat.py` (>=25 tests)。

### Phase 3 — API + 配置 + 文件 (1-2 天)

- [ ] P3-1 新增 `/api/v1/roles*` 端點 (或擴充 `/chat/unified`)。
- [ ] P3-2 `llm.default.yaml` 加 `role_slots:` 區 (或 preset)。
- [ ] P3-3 `docs/03-technical-architecture/` 新增 `MULTI_ROLE_PLAY.md` 架構說明。
- [ ] P3-4 更新 `MASTER_TASK_MAP.md`、`MEASUREMENT_MAP.md`。

### Phase 4 — 前端多角色 (3-5 天，可選)

- [ ] P4-1 desktop-app 支援多 Live2D 實例 (scene manager)。
- [ ] P4-2 角色切換 UI + group chat 顯示。
- [ ] P4-3 角色狀態面板 (per-role context/memory)。

### Phase 5 — 驗證與基準 (1-2 天)

- [ ] P5-1 整合測試：主 AI + 角色 B (gemma) + 角色 C (qwen) 同時運行，驗證 context 隔離。
- [ ] P5-2 記憶洩漏測試：角色 B 的私人對話不應出現在角色 C 的檢索結果。
- [ ] P5-3 模型綁定測試：角色 B 的請求必須走 gemma slot，角色 C 走 qwen slot。
- [ ] P5-4 效能測試：三角色同時回應的延遲與記憶體。
- [ ] P5-5 更新 `check_fact_gates.py` 加 `multi_role` 域 (可選)。

---

## 5. 檔案變更清單 (File Change List)

### 新增

| 檔案 | 用途 |
|---|---|
| `apps/backend/src/ai/roleplay/__init__.py` | 套件 |
| `apps/backend/src/ai/roleplay/role.py` | Role/ContextScope/RoleContext 資料類 |
| `apps/backend/src/ai/roleplay/role_play_agent.py` | RolePlayAgent |
| `apps/backend/src/ai/roleplay/multi_role_orchestrator.py` | MultiRoleOrchestrator |
| `apps/backend/src/ai/roleplay/context_builder.py` | merged context 建構 + visibility 過濾 |
| `tests/ai/roleplay/test_role_model.py` | 資料類測試 |
| `tests/ai/roleplay/test_role_play_agent.py` | Agent 測試 |
| `tests/ai/roleplay/test_orchestrator.py` | 編排器測試 |
| `tests/api/test_multi_role_chat.py` | API 整合測試 |
| `docs/03-technical-architecture/MULTI_ROLE_PLAY.md` | 架構說明 |

### 修改

| 檔案 | 改動 |
|---|---|
| `apps/backend/src/ai/persona/persona_engine.py` | `get_persona_engine()` 改 factory，支援 role_id；移除強制 singleton (向後相容) |
| `apps/backend/src/services/llm/router.py` | `_call_llm_backend()` 加 `_force_backend_slot`；metadata 加 `_role_id`；`_inject_*_context()` 讀 `_memory_namespace` |
| `apps/backend/src/api/routes/chat_routes.py` | `_run_chat_pipeline()` / `_handle_chat_request()` 加 `role_id`/`group` 參數 |
| `apps/backend/src/ai/memory/ham_memory/ham_manager.py` | `query_core_memory()`/store 加 `namespace` |
| `apps/backend/src/ai/memory/vector_store.py` (或 vector_memory_store) | 加 namespace 過濾 |
| `apps/backend/src/ai/context/dialogue_context.py` | per-role conversation_id 規則 (無程式碼改動，只文件) |
| `apps/backend/configs/system/llm.default.yaml` | 加 `role_slots:` 區 |
| `apps/backend/src/ai/agents/agent_adapter.py` | `_METHOD_MAP` 加 `"RolePlay": ("respond", None)` |

### 不動

- 模型 provider 層 (ollama/llamacpp) — 已支援任意模型。
- ContextScheduler / ContextLedger — 直接復用。
- AgentManager / DynamicAgentRegistry — 直接復用。
- Ensemble — 可選整合 (Phase 5)。

---

## 6. 風險與緩解

| 風險 | 緩解 |
|---|---|
| **記憶體**：3 個模型同時常駐 (main + gemma 2B + qwen 1.5B) 可能 OOM | 復用 hardware profile 偵測；`role_slots` 可設 `enabled: false` 關閉某角色；RolePlayAgent 支援 lazy load (首次 respond 才載入 backend) |
| **上下文洩漏**：共享基底可能把角色 B 的私人訊息洩漏給角色 C | `visible_to` 過濾 + 測試 P5-2；預設 `shared_memory_write=False` |
| **模型綁定被問句分流覆寫** | `_force_backend_slot` 在 `_select_light_backend()` 之前檢查，優先級最高；加測試 P5-3 |
| **per-role persona singleton 破壞** | `get_persona_engine(role_id=None)` factory：role_id=None 回全域 (向後相容)，role_id 有值回 per-role 實例；測試確認多實例不互相覆寫 |
| **HSP 複雜度** | 對話路徑走 in-process 直接呼叫，不走 HSP；HSP 只用於 agent 生命週期管理 |
| **前端單一角色** | Phase 4 之後；API 層先行，文字/CLI 可先驗證 |
| **測試汙染** | 每個 role 測試用 mock LLM service；autouse fixture 清理 `_CAUSAL_BUFFERS` 等全域狀態 (參考 R85 機制) |

---

## 7. 成功標準 (Success Criteria)

1. **功能**：可註冊 ≥3 個角色 (main + B + C)，每個綁定不同 backend_slot；`group_turn()` 回傳 3 份回應。
2. **隔離**：角色 B 的私人對話不出現在角色 C 的 `_inject_memory_context()` 結果中 (測試 P5-2)。
3. **綁定**：角色 B 的請求 `_used_backend_type` == gemma slot，角色 C == qwen slot (測試 P5-3)。
4. **向後相容**：不帶 `role_id` 的既有 `/chat/unified` 請求行為不變 (所有既有測試通過)。
5. **測試**：新增 ≥60 個測試 (P0 15 + P1 20 + P2 25)，全數通過；既有 8,700+ 測試無迴歸。
6. **效能**：三角色同時 group_turn 延遲 < 3× 單角色延遲 (可接受的平行開銷)。
7. **文件**：`docs/03-technical-architecture/MULTI_ROLE_PLAY.md` + `MASTER_TASK_MAP.md` 更新。

---

## 8. 與既有系統的整合點 (Integration Points)

| 既有系統 | 整合方式 | 風險 |
|---|---|---|
| AgentManager | RolePlayAgent 註冊為 in-process agent；復用生命週期/監控 | 低 |
| DynamicAgentRegistry | 動態註冊/註銷角色 | 低 |
| ContextScheduler | merged context 經 `plan_query` / `digest_overflow_sync` 處理 | 中 (token 預算需 per-role) |
| PriorityNegotiator | 主 AI 的路由決策仍走 negotiator；角色代理的 respond() 繞過 (強制 slot) | 低 |
| EmotionSystem | per-role persona state 可讀全域 emotion (共享) 或 per-role emotion (私有)；預設讀全域 | 中 |
| CausalReasoningEngine | per-role 可有獨立 causal buffer (session_id 已含 role_id) | 低 |
| HAM/Vector Memory | namespace 過濾 | 中 (需改 query signature) |
| Chat routes | 加 optional `role_id`/`group` 參數，向後相容 | 低 |

---

## 9. 替代方案與否決理由

| 方案 | 否決理由 |
|---|---|
| 全部走 HSP agent 協作 | HSP envelope 對話延遲太高；角色扮演需要輕量回合 |
| 每個角色獨立 LLM service 實例 | 記憶體爆炸；復用單一 AngelaLLMService + backend_slot 強制即可 |
| 共享上下文 = 完整複製 | N 倍記憶體 + 一致性問題；用 reference + overlay |
| 前端先做多角色 | 風險高、驗證慢；API/文字層先行 |
| 用 ensemble 替代多角色 | ensemble 是投票融合，不是分隔上下文；語意不同 |

---

## 10. 參考 (References)

### 10.1 專案內部

- `apps/backend/configs/presets/dual_model.preset.yaml` — 雙模型分流先例
- `apps/backend/src/services/llm/router.py` (`_select_light_backend`, `_call_llm_backend`, `_inject_*_context`)
- `apps/backend/src/ai/agents/agent_orchestrator.py` (`_INTENT_AGENTS`, `dispatchable_agent_ids`)
- `apps/backend/src/ai/agents/agent_manager.py`, `dynamic_agent_registry.py`
- `apps/backend/src/ai/context/dialogue_context.py`
- `apps/backend/src/ai/persona/persona_engine.py`
- `apps/backend/src/core/card/capabilities/roleplay_engine.py`
- `docs/09-archive/MULTI_PERSPECTIVE_ANALYSIS.md` (single model limit note)
- `docs/06-project-management/plans/STREAMING_WINDOW_DUALMODEL_PLAN.md` (計畫書格式參考)

### 10.2 外部 (Web)

- Atlan: "How to Manage Context Across Multiple AI Agents in 2026" — shared substrate + coordination architecture + governance + freshness
- Google ADK blog: "Architecting efficient context-aware multi-agent framework for production" — tiered context
- Cognition: "Don't Build Multi-Agents" — 警示：決策過度分散、上下文不一致的風險；本計畫因此採「主 AI 彙總 + 角色代理 respond()」而非完全分散
- Character.AI multi-character group chat (2025-09) — 多角色群聊的產品參考
- WyrdTale — server-side world/character state (非依賴模型 context window) — 支持「記憶命名空間」設計
- arXiv DeLM "Decentralized Multi-Agent Systems with Shared Context" — 共享上下文的理論參考

### 10.3 跨檔 mock 汙染陷阱 (R85，實作時必讀)

參考 `AGENTS.md`「跨檔 mock 汙染陷阱」：`monkeypatch.setattr("module.X", mock)` 只還原源模組；測試 except handler 必須能執行。實作 `RolePlayAgent` 時，消費端對「會被測試 patch 的系統類」建構要用模組屬性動態解析 (如 `import services.llm.router as _m; _m.AngelaLLMService()`)，避免 from-import 綁定汙染。

---

## 11. 開放問題 (Open Questions)

1. **角色 B/C 的 persona 是否需要獨立的 AL 代謝狀態 (fatigue/stress/valence)**？預設：共用全域 emotion (簡單)；可選 per-role (複雜)。Phase 1 先共用。
2. **group_turn 的順序**：並行 (asyncio.gather) vs 串行 (B 看到 C 的回應)？預設並行 + 主 AI 彙總；串行放 Phase 5。
3. **角色可否「主動發言」(不等使用者)**？目前只支援被動回應；主動發言需 autonomous lifecycle 整合，放 Phase 5+。
4. **是否支援使用者自訂角色卡** (上傳 JSON)？Phase 3 API 預留端點，實作放 Phase 4。
5. **模型綁定是否允許執行期切換** (例如角色 B 從 gemma 切到 qwen)？預設允許 (更新 `backend_slot` + 重新健康檢查)。

---

## 12. 下一步 (Next Steps)

1. 使用者確認本計畫方向 (角色代理 vs 直接綁模型 vs 混合)。
2. 切換到 Build agent。
3. 從 Phase 0 開始實作，每 Phase 完成後跑 `pytest tests/ai/roleplay/` + 既有測試迴歸。
4. 每 Phase 完成更新本文件的 checkbox 與 `MASTER_TASK_MAP.md`。

---

> **本計畫為 draft**。所有檔案變更需在 Build agent 模式下執行；Plan 模式下僅討論與規劃。
