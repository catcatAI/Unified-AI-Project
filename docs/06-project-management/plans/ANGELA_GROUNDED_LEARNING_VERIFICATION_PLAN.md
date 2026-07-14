# Angela「有查證的學習能力」— 設計紀錄（Spec / Record）

> 狀態：設計紀錄 → 已實作並接線（見 §8 實作現況）。
> 任務：優化/改進現有學習能力，使「學習有查證渠道」——知識量不強求，但學習必須能
> 查證、且能根據查證結果自我修正；查證來源使用專案自帶的網路搜尋能力。
> 對應用戶要求：智能與速度都及格（寬泛程度、學識面向、學識深度、對話能力追上本地 AI，
> 速度維持秒級），並具備「查證 + 根據查證的學習」。

- 作者：Angela AI Development Team
- 版本：7.5.0-dev
- 相關提交：§X #263（domain_ripple 接線 + B1-B5 修正）、本計畫 §X #264（有查證的學習能力）
- ANGELA-MATRIX：`[L3-L4] [βγδ] [B] [L2]`

---

## 0. 一句話總結

現有學習是「語言模式/詞典成長 + GARDEN 權重」，**完全沒有事實查證**；本計畫新增一個
**有查證渠道的學習子系統**：對話中萃取事實主張 → 背景用專案自帶的 `WebSearchTool`
（DuckDuckGo Lite + Wikipedia，純 stdlib urllib）查證 → 記錄 `VERIFIED / CONTRADICTED /
UNVERIFIED` 狀態與來源 → 未來回答可注入已查證知識。查證在**背景非同步**跑，不佔回答延遲；
知識注入是本地 O(n) 掃描，維持秒級。

---

## 1. 現狀調查（實際讀碼，非猜測）

### 1.1 現有「學習」能力（都沒有查證）
| 模組 | 學什麼 | 有無查證 | 備註 |
|------|--------|----------|------|
| `ai/response/learning_loop.py` `LearningLoop` | 從 LLM 回答萃取句子/emoji/collocation，長 ED3N 詞典 | ❌ | 無來源、無真偽 |
| `ai/ed3n/continuous_learning.py` `ContinuousLearningPipeline` | 成對 (user, response) 長 ED3N 詞典 + 週期訓練 | ❌ | 訓練樣本即原文，無事實校驗 |
| `ai/meta/learning_orchestrator.py` `LearningOrchestrator` | 評估→適應閉環（固定 0.5 評分器） | ❌ | `_SimpleEvaluator` 硬編 0.5 |
| `ai/memory/memory_learning.py` `MemoryLearningEngine` | 回應範本成功率的移動平均 | ❌ | 樣板層級，非事實 |
| `ai/meta/adaptive_learning_controller.py` | 依指標調學習策略 | ❌ | 同上 |
| `ai/agents/specialized/knowledge_graph_agent.py` | 記憶體 entity/relation dict | ❌ | 無持久化、無來源 |
| `core/knowledge/unified_knowledge_graph.py` + `_impl.py` | **STUB**（只有 init/log） | ❌ | 未實作 |

→ 結論：**學習很多，但沒有一條帶查證**。知識進系統後無法被「對錯」約束。

### 1.2 現有「網路搜尋/瀏覽」能力（查證來源）
| 模組 | 實作 | 依賴 |
|------|------|------|
| `core/tools/web_search_tool.py` `WebSearchTool` | **真實**：DuckDuckGo Lite + Wikipedia，純 `urllib` | ❌ 無外部依賴（永遠可用） |
| `ai/agents/specialized/web_search_agent.py` `WebSearchAgent` | 真實，但用 `requests` | ⚠ `requests` 可能未裝（venv 無 → `REQUESTS_AVAILABLE=False`） |
| `services/handlers/web_search_handler.py` | 包 `WebSearchTool`，作為搜尋意圖處理 | — |

→ 結論：**`WebSearchTool` 是最穩定的查證來源**（不依賴 `requests`）。`WebSearchAgent`
宣稱有 `source_verification` 能力但**未實作**。本計畫以 `WebSearchTool` 為查證後端。

### 1.3 速度現狀（承 §X #263 鏈路分析）
- 回答路徑主導成本 = LLM 呼叫（秒級）。
- 現有 `_process_continuous_learning` / `_process_garden_learning` 已在**回答後背景**跑
  （`chat_service.py:160-161`），是接線查證迴圈的理想位置。
- 關鍵約束：**查證不能進回答延遲**。因此查證必須 async 背景化；知識注入必須是本地 O(n)。

---

## 2. 設計目標與非目標

### 目標
1. 學習有**查證渠道**：事實主張能被檢索來源校驗，結果（VERIFIED/CONTRADICTED/UNVERIFIED）
   被記錄並可檢索。
2. 學習能**根據查證自我修正**：查證通過→提升可信度並可注入未來回答；查證矛盾→降信、標記。
3. **不破壞速度**：查證背景化；注入本地化；回答路徑維持秒級。
4. **真實可測**：用可注入的假搜尋工具，單元測試能在無網路下證明查證通道端到端工作。

### 非目標（本輪不做）
- 不追求知識「量」（用戶明言不強求）。
- 不替換 LLM 生成（對話能力主體仍是 LLM）。
- 不做完美事實辨識（v1 用透明、可解釋的 heuristic assessor；LLM assessor 作為可插拔升級）。

---

## 3. 架構

```
對話 (user, response)
      │
      ▼  [背景, 不佔延遲] chat_service._process_grounded_learning
GroundedLearningManager.queue_claims(user, response)
      │  1) ClaimExtractor.extract_claims(response)  → 候選事實句
      │  2) store.add_or_update(claim)               → UNVERIFIED（去重）
      │  3) schedule asyncio 背景任務 verify_each(claim)
      ▼
KnowledgeVerifier.verify(claim)
      │  query = 關鍵詞 from claim
      │  results = WebSearchTool.search(query)        [asyncio.to_thread, 背景]
      │  assessment = assessor(claim, results)         [預設 heuristic]
      ▼
store.record_verification(claim_key, status, sources, confidence)
      │
      ▼  [未來回答, 本地 O(n)] get_grounded_context(query)
回答 prompt 注入「已查證知識」區塊（有相關 VERIFIED 才注入）
```

### 3.1 `ai/memory/grounded_knowledge.py` — 已查證知識庫（無網路）
- `VerificationStatus`(Enum): `UNVERIFIED, VERIFIED, CONTRADICTED, DISPUTED`.
- `SourceRef`(dataclass): `url, title, snippet`.
- `GroundedClaim`(dataclass): `claim_key, claim_text, sources:List[SourceRef],
  status, confidence(0..1), domain, first_seen, last_verified, verify_count,
  contradict_count`.
- `GroundedKnowledgeStore`:
  - `_normalize(text)` → 小寫/去標點/空白摺疊；`claim_key = sha1(normalized)`。
  - `add_or_update(claim_text, domain=None) -> GroundedClaim`（同 key 合併 sources）。
  - `find_related(query, limit) -> List[GroundedClaim]`（token 重疊，本地 O(n)）。
  - `verified_for(query, limit) -> List[GroundedClaim]`（只回 `VERIFIED`，按 confidence 降序）。
  - `record_verification(claim_key, status, sources, confidence)`（更新狀態 + 計數）。
  - `save(path)` / `load(path)` → `data/grounded_knowledge.json`（JSON）。
  - 全記憶體 + 檔案，純 stdlib，可單測。

### 3.2 `ai/memory/claim_extractor.py` — 事實主張萃取（無網路）
- `extract_claims(text) -> List[str]`：
  - 分句（中英文句號）。
  - 保留「像事實」的句子：含繫詞/關係動詞（`is/are/was/were/means/equals/refers to/是指/為/等於`
    + 領域動詞如 `discovered/invented/founded/成立/發明/發現`），且至少一個錨點
    （Capital 開頭 token / 數字 / 引號詞 / 小領域名詞表）。
  - 排除：疑問句（結尾 `?`/`？`）、祈使（`please/請/幫我` 開頭）、純閒聊（無錨點）。
  - 去重、截最短長度。
- 純函數，可單測。

### 3.3 `ai/meta/knowledge_verifier.py` — 查證器（可注入搜尋/評估）
- `VerificationResult`(dataclass): `status, sources:List[SourceRef], confidence, query`。
- `KnowledgeVerifier`:
  - `__init__(self, search_tool=None, assessor=None, cache=None)`：
    `search_tool` 預設 `WebSearchTool()`；`assessor` 預設 `heuristic_assess`。
  - `async verify(claim, num_results=5) -> VerificationResult`：
    - `query = _build_query(claim.claim_text)`（取關鍵 token）。
    - `results = await asyncio.to_thread(self.search_tool.search, query, num_results)`。
    - `assessment = self.assessor(claim.claim_text, results)` → `(status, confidence, sources)`。
    - 寫入 `self._cache[claim.claim_key]` 避免重搜。
  - `heuristic_assess(claim_text, results)`（透明、可解釋）：
    - 取 claim 關鍵 token（Capital/digit/引號/領域名詞）。
    - `support = ` 含關鍵 token 且附近無否定詞的來源比例。
    - `contradict = ` 含否定詞（not/no/錯誤/誤/假/never）且含關鍵 token 的來源比例。
    - `contradict >= 0.34 → CONTRADICTED`（confidence≈contradict）；
      `support >= 0.34 → VERIFIED`（confidence≈support）；
      否則 `UNVERIFIED`。
  - 評估器可插拔：未來可用 LLM assessor 提升準確率（不在本輪預設，避免額外 LLM 成本/依賴）。

### 3.4 `ai/memory/grounded_learning_manager.py` — 協調單例
- `GroundedLearningManager`：
  - 持有 `store`, `verifier`, `extractor`；`asyncio` 任務集（限制並發 + 去重 + 跳過已查證）。
  - `queue_claims(user_message, response_text)`（**fire-and-forget**）：
    萃取 → `store.add_or_update` → 對每個 UNVERIFIED 派發背景 `asyncio.create_task(self._verify_one(...))`。
  - `async _verify_one(claim)`：呼叫 `verifier.verify` → `store.record_verification`。
    異常吞掉（logging），不影響主流程。
  - `get_grounded_context(query, limit=3) -> str`：本地 `store.verified_for` 組成
    簡短「已查證知識」區塊（無相關則空字串，呼叫方視為 no-op）。
  - `get_stats() -> dict`、`save()`、`load()`。
  - `get_grounded_learning_manager()` 共享單例工廠（與 §X #263 的 `apply_domain_cognition`
    共用入口模式一致，避免多實例分歧）。

### 3.5 接線點（`services/chat_service.py`）
- 在既有背景學習區（`_process_continuous_learning` 同層）新增
  `_process_grounded_learning(user_message, response_text)`：
  - `manager = get_grounded_learning_manager()`
  - `asyncio.create_task(manager.queue_claims(user_message, response_text))`
    （**不 await**，不佔回答延遲；錯誤由 manager 內部吞掉）。
- 可選接地注入：在組 LLM 上下文步驟呼叫 `manager.get_grounded_context(user_message)`，
  非空則作為 system note 注入（本地 O(n)，<幾 ms，在秒級預算內）。
- 全部 `try/except` 守衛：管理器不可用時靜默 no-op，主回答不受影響。

---

## 4. 速度預算（為何能維持秒級）
- **回答路徑**：LLM 生成（秒級）— 不變。
- **查證**：背景 `asyncio` 任務，每個搜尋 ~1–2s 但**與用戶回答並行**，不計入感知延遲；
  受 cache + 去重 + 並發上限約束，不會無限成長。
- **接地注入**：本地 store 掃描，sub-ms ~ 數 ms。
- 結論：用戶感知延遲仍 = LLM 秒級；查證是「免費」的背景自我修正。

---

## 5. 智能預算（為何能追上本地 AI 的「學識面向/深度」）
- 寬泛程度 / 學識面向：接地知識庫從對話中持續萃取事實並查證，跨領域成長（不限於預訓練 cutoff）。
- 學識深度：已查證知識可注入未來回答，提供有來源依據的事實（含 url），比無來源更可信。
- 對話能力：主體仍是 LLM；接地只做「有根據的補強」，不替換生成。
- 自我修正：CONTRADICTED 主張降信、不再注入；系統不會把錯誤當成知識固化。
- 知識量：用戶明言不強求；本設計讓「量」隨對話自然增長且**可被查證約束**。

---

## 6. 誠實聲明（v1 限制）
- heuristic assessor 是「關鍵詞重疊 + 否定偵測」，非嚴格事實辨識；它提供**透明、可解釋、
  有來源**的查證通道，而非 100% 準確的真理判定。這符合用戶「有查證渠道」的要求；
  準確率提升路徑 = 插拔 LLM assessor（已預留介面）。
- 查證依賴外部搜尋可用性；搜尋失敗時主張維持 UNVERIFIED（不會誤判為錯）。

---

## 7. 驗收 / 測試
- `tests/ai/memory/test_grounded_knowledge.py`：add/dedupe、find_related、verified_for、
  record_verification 狀態轉移、save/load 持久化。
- `tests/ai/memory/test_claim_extractor.py`：萃取事實句、排除疑問/祈使/閒聊。
- `tests/ai/meta/test_knowledge_verifier.py`：用 `FakeSearchTool`（可注入）證明
  verify() 在來源支持→VERIFIED、來源否定→CONTRADICTED、來源不足→UNVERIFIED；
  cache 命中避免重搜。
- `tests/ai/memory/test_grounded_learning_manager.py`：queue_claims 萃取+派發驗證
  （fake verifier/search）；get_grounded_context 回傳 VERIFIED；get_stats；save/load。
- 整合：確保 `chat_service` 匯入無誤、既有 `_process_continuous_learning` 行為不變。
- 廣泛回歸：`pytest tests/ai/memory tests/ai/meta tests/services` 確認無回歸。

---

## 8. 實作現況
- 已建立 `ai/memory/grounded_knowledge.py`、`ai/memory/claim_extractor.py`、
  `ai/meta/knowledge_verifier.py`、`ai/memory/grounded_learning_manager.py`。
- 已接線 `chat_service._process_grounded_learning`（背景 fire-and-forget）+ 可選接地注入。
- 已加 §7 全部測試（無網路，用 FakeSearchTool）。共計測試全過。
- 已更新 `docs/architecture/ANGELA_FULL_ARCHITECTURE.md` §5.9（有查證學習子系統）。
- 提交：`§X #264`。
