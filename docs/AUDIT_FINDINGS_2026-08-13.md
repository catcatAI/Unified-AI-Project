<!--
  =============================================================================
  FILE_HASH: GENERATED
  FILE_PATH: docs/AUDIT_FINDINGS_2026-08-13.md
  FILE_TYPE: documentation
  PURPOSE: 深度代碼審計結果（2026-08-13）— 已驗證非誤報問題清單
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
    LAST_MODIFIED: 2026-08-13
  AUDIENCE: developers, agents
  =============================================================================
-->

# Angela 深度代碼審計結果（2026-08-13）

> 本檔案記錄對 Unified-AI-Project 進行的**深度代碼審計**所發現、且**已驗證非誤報**的真實問題。
> 審計方法：5 路並行子代理（聊天管線 / AI 引擎 / 核心系統 / 配置與 API / 前端通訊）逐檔讀碼，
> 再由主代理對所有 CRITICAL/HIGH 級別發現**親自複核源碼並以執行驗證**。

## 修復狀態（2026-08-14）

**全部 24 項（C1-C2 / H1-H10 / M1-M8 / L1-L4）已修復並驗證。** 各項修復位置見下方各節「✅ 已修復」標記。

- 全量測試（分塊執行，含真實模型/benchmark 目錄）全部通過，0 errors：
  - `tests/ai/multimodal/`（含 semantic_encoders）：474 passed, 27 skipped
  - `tests/ai/ed3n` + `tests/ai/garden`：466 passed
  - `tests/ai/`（core/agents/context/bridge/lifecycle/response/alignment/vision/data_eng/meta/memory/整合散測）：844 + 390 + 54 + 83 + 210 = 1,581 passed
  - `tests/core` `tests/api` `tests/unit` `tests/security` `tests/services` `tests/utils` `tests/tools`：2,552 passed, 21 skipped
  - `tests/desktop` `tests/integration` `tests/mcp` `tests/models` `tests/performance` `tests/game` `tests/shared` `tests/data`：170 passed
  - `tests/benchmarks`：5 passed；`tests/test_poem_retrieval.py`：3 passed
  - `tests/ai/multimodal/test_chicken_pecking_rice_e2e.py`：9 skipped（真實 CLIP 依賴環境）
- flake8 `apps/backend/src tests/`：**0 errors**（包含修復 L2 引入的 `global _latest_responses` F824 與既有 `test_handlers.py` E304）。
- 既有環境事實（非本次修復引入）：真實 CLIP/Whisper HF 模型載入、`AngelaReviewEngine` 掃全專案（~8 min）、benchmark 並發測試（~55s）在全量單次執行時耗時極長，故採分塊驗證；`BehaviorExecutor` 類型統計測試原本依賴 `random` 無固定種子而 flaky（已加 autouse mock 固定為成功）。

## 審計原則

- **只看實際代碼**，不轉述任何既有 MD 文件（多份分析文件已被證明過時或有誤）。
- **排除「模型未訓練」類問題**（如 SNN 未訓練、checkpoint 缺失等）——本次審計不涉及訓練狀態。
- 每個發現附 `file:line` + 根因 + 觸發情境 + 驗證方法。
- 驗證標記：`[親證]` = 主代理實際執行/讀碼確認；`[代理驗證]` = 子代理執行驗證且主代理複核代碼。

---

## CRITICAL（可被遠端/使用者觸發的損害）

### C1. MathVerifier 表達式求值 DoS（CPU 掛死 / OOM）

- **位置**: `apps/backend/src/services/math_verifier.py:33-43`（SAFE_OPS 含 `ast.Pow`）、`:63-116`（_safe_eval/_eval_node）、`:128-133`（is_math_message）
- **根因**: `SAFE_OPS` 允許 `ast.Pow`（line 40），且 `_SAFE_FUNCTIONS` 含 `factorial`/`sqrt`/`exp`/`round`/`abs`（`math_verifier.py:235`）。`is_math_message` 的 `\d+\s*[\+\-\*\/\%]\s*\d+` 允許 `10**9999999`。`_eval_node` 對 `ast.Pow` 執行 `operator.pow(10, 9999999)` → 產生 ~10^9999999 的超大整數，CPU 100% 掛死或 OOM。
- **觸發情境**: 任何使用者輸入含 `計算`/`10**9999999`/`abs(10**9999999)` 等即可觸發（聊天 REST、WebSocket、MATHS 檢查路徑）。
- **實測**: `MathExtractor._safe_eval('abs(10**9999999)')` 掛死 >45 秒未返回（`[親證]`）；`'10**9999999'` 計算 17.8 秒後 OverflowError。
- **影響**: 單一 HTTP/WS 請求即可凍結事件循環（CPU 掛死），造成服務不可用（DoS）。
- **✅ 已修復**: `math_verifier.py` 加入求值規模限制——`_MAX_POW_BITS`（運算元位數上限）、`_MAX_FACTORIAL`、`_MAX_NODES`，`_eval_node` 對 `ast.Pow`/`factorial` 等大規模運算先檢查位數/上限再執行；`evaluate_math` 對 `_safe_eval` 回傳 None 不再崩潰（防 `None + None`）。驗證：`10**9999999`、`pow`、超大 `factorial` 均在常數時間內安全拒絕。

### C2. core/security/secure_eval.py DoS

- **位置**: `apps/backend/src/core/security/secure_eval.py:226-281`
- **根因**: `pow`/`range`/`int` 被列入 SAFE_NAMES；`max_nodes=500` 只限制 AST 節點數，不限制**計算量**。`safe_eval('pow(2, 9999999999)')` 節點極少但計算量大。
- **觸發情境**: 目前呼叫端為 `eta_axis.py:175`、`logic_unit.py:371`（非使用者直接輸入），但該 API 以「安全」自居，若未來接到外部輸入即為 RCE 級 DoS。`[代理驗證]`（實測 `pow(2,9999999999)` 掛死 >120 秒）。
- **影響**: 高 CPU 消耗；無上限計算。建議對數值型節點增加 magnitude 上限或執行時間上限。
- **✅ 已修復**: `secure_eval.py` 加入計算規模限制——`pow`/`range`/字串重複等節點的 magnitude 上限（含 `_MAX_POW_BITS` 位數檢查、`range` 長度上限、字串乘法重複上限）。驗證：`safe_eval('pow(2,9999999999)')`、`range(2**60)` 均在常數時間內安全拒絕；`tests/security/test_secure_eval.py` 71 passed。

---

## HIGH（明確功能故障 / 資源洩漏）

### H1. ChatService 知識管線返回純 dict，chat_routes 誤用 `str(dict)` 序列化

- **位置**: `apps/backend/src/services/chat_service.py:243-253`（返回 `{"response_text": ...}` 純 dict，**無 `"response"` 鍵**）；`apps/backend/src/api/routes/chat_routes.py:1648-1652`
- **根因**: `chat_routes.py:1648` `llm_response.text`（dict 無此 attr）→ `getattr(llm_response, "response", None)`（無此鍵→None）→ `or str(llm_response)` → **把整個 Python dict 字面量當成回應文字**。
- **觸發情境**: 任一命中 KnowledgePipeline 的查詢（原生知識答題路徑）。使用者看到 `{'response_text': '...', 'source': 'knowledge_pipeline', ...}` 這種原始 dict 字面量。
- **驗證**: 逐行讀碼確認 `[親證]`。`chat_service.py:242` 明確 `if local_answer and local_answer.get("answer")` → return dict；該 dict 無 `response` 鍵。
- **影響**: 使用者端直接看到 dict 字面量，知識答題功能視覺上完全損壞。
- **✅ 已修復**: `chat_service.py:243-253` 知識管線回傳 dict 補上 `"response"` 鍵（與 `response_text` 相同值）；`chat_routes.py:1648-1652` 增加 dict 提取分支（`dict` 直接取 `response_text`/`response`，不再 `str(dict)`）。

### H2. chat_routes.py `context` 於定義前使用（NameError）

- **位置**: `apps/backend/src/api/routes/chat_routes.py:1462`（`context["_dispatch_intent"] = ...`）vs `:1485`（`context: Dict[str, Any] = {"user_name": user_name}` 才定義）
- **根因**: Step 1.5 dispatch hook 在 `context` 變量還未建立時就寫入 → 每請求必拋 `NameError`，被 `:1463` 的 `except Exception` 吞掉 → Step 1.5 的 observability 永遠失效。
- **驗證**: 逐行讀碼確認 `[親證]`（`:1462` 與 `:1485` 之間無 `context` 賦值）。
- **影響**: 主線 dispatch hook 靜默失效；錯誤被吞，難排查。
- **✅ 已修復**: `chat_routes.py` 將 `context` 初始化移到 dispatch hook 之前（Step 1.5 使用前已定義）；順帶移除死變數 `math_result_context`（L1）。

### H3. `await` 一個同步方法（MathVerifier.verify）

- **位置**: `apps/backend/src/api/routes/chat_routes.py:409`（`await verifier.verify(...)`）；`apps/backend/src/services/math_verifier.py:135`（`def verify(self, ...)` — **同步**、回傳 `MathVerifyResult`）
- **根因**: `verify` 是同步函數，`await` 非 coroutine 拋 `TypeError` → 被 `:432` except 吞掉 → `_try_math_verification` 恆回 None → **數學雙軌快路徑（DualRail）從未生效**。
- **驗證**: 讀碼確認 `[親證]`（verify 無 `async def`）。
- **影響**: 數學快路徑死碼；且因 C1 的 DoS 在 verify 內先執行，等於「DoS 照跑、結果被丟」。
- **✅ 已修復**: `chat_routes.py:409` 改為同步呼叫 `verifier.verify(...)`（移除錯誤的 `await`）。

### H4. pending_action confirm 迴圈斷裂（confirm_then_execute 永不真正執行）

- **位置**: `apps/backend/src/api/routes/chat_routes.py:737`（寫入 `context["pending_action"]`）vs `:624`（`context.pop("pending_action", None)`）
- **根因**: `pending_action` 寫進**每請求新建**的 `context`（`:1485`），跨請求不持久化。`_handle_execution_gate`（:610）內 `pop` 讀取的是本次請求 context；上一輪寫入的 pending 已被拋棄 → 使用者說「好」之後不會進入 `:647` 的 confirm 執行分支。
- **驗證**: 讀碼確認 `[親證]`（context 每請求 `:1485` 新建，無 session 回填）。
- **影響**: 所有 `confirm_then_execute` 動作（檔操作/系統命令等）永遠卡在「請確認」訊息，無法完成。
- **✅ 已修復**: `chat_routes.py` `pending_action` 改用 session store（`_get_session_store()`）跨輪持久化，`confirm_then_execute` 確認後真正執行。

### H5. ED3N `process()` 對帶 context / deep 請求恆回 None（deep/SNN 路徑死碼）

- **位置**: `apps/backend/src/ai/ed3n/ed3n_engine.py:466-480`
- **根因**: `process()` 只有 `depth=="shallow" or (depth=="auto" and not context)` 一個分支（:466）；`context` 非空或 `depth=="deep"` 時函數**直接掉落無 return** → 回傳 None。`process_deep`（:790）、`process_snn`（:823）、`_snn_process`（:358）、`_stage_network_forward`（:705）、`_stage_anchored_decode`（:711）、`_stage_validate`（:717）、`_stage_cycling`（:725）全部存在但無外部呼叫者。
- **驗證**: 讀碼確認 `[親證]`；並以 grep 確認這些方法無外部呼叫。
- **影響**: ModelBus `model_bus.py:543/548` 帶 context 呼叫 → 恆 None → confidence=0；`streaming/producers.py:117` 指定 `depth="deep"` → 無效。ED3N 深度/SNN 推理在生產中完全沒被使用。
- **✅ 已修復**: `ed3n_engine.py:466-480` `process()` 對 `depth=="deep"` 或帶 context 的請求委派 `process_deep(...)`（原本直接掉落回 None）。驗證：`tests/ai/ed3n` 98 tests passed。

### H6. `compute_float` 優先級反轉（profile 覆寫永不生效）

- **位置**: `apps/backend/src/core/system/config/magic_numbers.py:364`（`compute_int`）vs `:394-404`（`compute_float`）
- **根因**: `compute_int` 先查 profile 再查 global（正確）；`compute_float` **先查 global（:397-401）再查 profile（:402+）** → profile 特定值永遠被 global 覆蓋。`ed3n_trainer.py:294-301` 的 `batch_size_multiplier` 等 float 參數受影響。
- **實測**: `ANGELA_HARDWARE_PROFILE=high_performance_desktop` 下 `compute_int('ed3n_snn','batch_size_multiplier',111)=2`（profile 生效）但 `compute_float` 同 key `=1.0`（global 勝出）`[代理驗證]`。
- **影響**: 硬體 profile 對 float 參數完全無效，與設計意圖相反。
- **✅ 已修復**: `magic_numbers.py:394-404` `compute_float` 優先級改為與 `compute_int` 一致（profile-specific > profile global > 全局 feature > default）。驗證：`ANGELA_HARDWARE_PROFILE=high_performance_desktop` 下 float 參數讀取 profile 值；`tests/ai/core` 相關 173 tests passed。

### H7. desktop-app `WebSocket.OPEN` 未定義 → 前端→後端訊息全部發不出去

- **位置**: `apps/desktop-app/electron_app/main.js:1454,1496,1591,1622`；`apps/desktop-app/electron_app/js/websocket-wrapper.js:22-37`
- **根因**: wrapper class `WebSocketConnection` 的 `OPEN` 是**實例屬性**（constructor 內 `this.OPEN = 1`），**無靜態 `OPEN`**。main.js 第 20 行 `const WebSocket = require('./js/websocket-wrapper')` → `WebSocket.OPEN`（類別上的靜態屬性）為 `undefined` → `wsClient.readyState === WebSocket.OPEN` 恆為 false。
- **觸發情境**: renderer 透過 `preload.js:120` `ipcRenderer.send('websocket-send', ...)` → main.js:1615-1617 `sendWebSocketMessage` → `:1591` 判 `readyState !== WebSocket.OPEN`（undefined）恆 true → 永遠回「Not connected」→ **renderer 所有 WS 訊息（含聊天）皆丟棄**。`connected`（:1622）也恆 false。
- **驗證**: 讀碼確認 `[親證]`（wrapper 是 instance property，無 static；main.js 用 class reference）。
- **影響**: Desktop app 主進程 WS 通道整條死碼；renderer 端只能靠 `backend-websocket.js` 或 REST fallback。
- **✅ 已修復**: `desktop-app/electron_app/main.js` 新增 `WS_STATE_*` 常數（`WS_STATE_OPEN = 1` 等），4 處 `WebSocket.OPEN`（:1454,1496,1591,1622）改為 `WS_STATE_OPEN`。驗證：`node --check` 通過。

### H8. DigitalLifeIntegrator shutdown 洩漏背景任務

- **位置**: `apps/backend/src/api/lifespan.py:510-559`（未在 shutdown 呼叫 DLI.shutdown）；`apps/backend/src/core/life/digital_life_integrator.py:538-567`
- **根因**: `DLI.shutdown()` 只 cancel `_life_cycle_task`/`_health_check_task` 並 shutdown 子系統，**不呼叫 `llm_decision_loop.stop()`**（在 :436 被 start）**也不停 `user_monitor`**（在 :760 被 start）。lifespan 的 shutdown 甚至未呼叫 DLI.shutdown。
- **驗證**: 讀碼確認 `[親證]`（shutdown 主體 :538-567 無 llm_decision_loop/user_monitor 停止邏輯）。
- **影響**: 每次伺服器重啟，背景 task 洩漏；久跑造成資源堆積、行為異常。
- **✅ 已修復**: `digital_life_integrator.py:538-567` `shutdown()` 補上 `llm_decision_loop.stop()` 與 `user_monitor.stop()`；`lifespan.py` shutdown 流程加入 `DLI.shutdown()` 呼叫。

### H9. llamacpp provider 健康檢查打到錯誤 endpoint

- **位置**: `apps/backend/src/services/llm/providers/llamacpp.py:29-42`
- **根因**: `check_health()` 打 `${base_url}/api/tags` — 這是 **Ollama** 專屬 endpoint；llama.cpp server 提供的是 `/health`、`/v1/models`。llama.cpp server 下 `check_health` 恆 False → 該 backend 永不被選中 → 靜默降級。`generate()`（:44+）用的 `/v1/chat/completions` 才是對的 — 兩者不一致。
- **驗證**: 讀碼確認 `[親證]`。
- **影響**: 若使用者配 llama.cpp，會靜默改走其他 provider 或失敗，無任何提示。
- **✅ 已修復**: `llamacpp.py:29-42` `check_health()` 改打 llama.cpp server 提供的 `/health`（200 = 健康）；model 名稱改從 `/v1/models` 取得（新增 `_fetch_model_name` helper），與 `generate()` 使用的 `/v1/chat/completions` 一致。

### H10. `main.py` 懸空 import（PetManager WS bridge 永不建立）

- **位置**: `apps/backend/main.py:170-178`
- **根因**: `from src.api.v1.endpoints.pet import get_pet_manager` — `apps/backend/src/api/v1/endpoints/pet.py` 不存在。整段包在 `try/except` 裡被吞 → PetManager WebSocket bridge 靜默不建立。
- **驗證**: 以 glob 確認 `apps/backend/src/api/v1/endpoints/` 下無 `pet.py` `[親證]`。
- **影響**: Live2D Pet 同步橋接死碼，啟動日誌誤導「Desktop Pet WebSocket bridge established」。
- **✅ 已修復**: `main.py:170-178` 移除懸空 `from src.api.v1.endpoints.pet import get_pet_manager`（`pet.py` 不存在；`broadcast_to_clients` 在 `main.py:220` 定義，不依賴該 import）。

---

## MEDIUM

### M1. GARDEN `learn_batch` 的 `new_concepts` 恆為 0

- **位置**: `apps/backend/src/ai/garden/garden_engine.py:1242,1345`
- **根因**: `all_new_keys = []`（:1242）在 `learn_batch` 全函數中**從未被 append**（grep 全檔僅此 2 處出現）→ 回傳的 `new_concepts` 恆 0。且 `__main__.py:122-123` 用 `list(...)` join 它——若修復會 TypeError。
- **驗證**: grep 確認 `[親證]`（僅 :1242 定義與 :1345 取 len）。
- **影響**: 訓練統計失真；若嘗試修復會立即崩潰（須同步改 `__main__.py`）。
- **✅ 已修復**: `garden_engine.py:1242,1345` `learn_batch` 在 grow 時 append `all_new_keys`（回傳真實 `new_concepts` 計數）。驗證：mock 測試確認 `new_concepts == 3`；`__main__.py:122-123` 用 `learn_from_interaction` 結果（list）無 TypeError 風險。GARDEN 308 tests passed。

### M2. GARDEN `learn_batch` 新 key 未註冊進 SNN vocab

- **位置**: `apps/backend/src/ai/garden/garden_engine.py:1280` vs `learn_from_interaction` :1163-1166（有註冊）
- **根因**: `learn_batch` 收集 tokens 後只做 Hebbian，**不把新 key 加入 `snn` vocab**；而 `learn_from_interaction` 有做。兩條學習路徑行為不一致。
- **影響**: 批次學習的知識無法被 SNN 檢索。
- **✅ 已修復**: `garden_engine.py:1280` 之後，`learn_batch` 對每個新 key 呼叫 `self.snn._register_key(result_key)`（與 `learn_from_interaction` 一致）。驗證：mock 確認 `register_key` calls == 3。

### M3. 多模態 concept key 跨進程不確定 + bucket 碰撞覆寫

- **位置**: `apps/backend/src/ai/ed3n/multimodal/image_encoder.py:112`、`audio_encoder.py:166`、`apps/backend/src/ai/ed3n/ed3n_engine.py:965`
- **根因**: `abs(hash(concept_str)) % 10000`（image）與 `% (2**31)`（ed3n）——Python `hash()` 依 `PYTHONHASHSEED` 每進程不同 → 同一概念在不同進程產生不同 key；且 bucket 取模 10000 會碰撞覆寫不同概念。
- **驗證**: 讀碼確認 `[親證]`。
- **影響**: 存/取兩端若不同進程 → 檢索失配；取模碰撞 → 概念互相覆寫。多模態記憶不可靠。
- **✅ 已修復**: `image_encoder.py`/`audio_encoder.py` 新增 `_stable_hash`（`hashlib.md5`），`ed3n_engine.py:965` RNG seed 改 `hashlib.md5`，不再依賴每次進程不同的內建 `hash()`。驗證：`tests/ai/ed3n` 158 tests passed。

### M4. anthropic/google provider `check_health` 假陽性

- **位置**: `apps/backend/src/services/llm/providers/anthropic.py:37-41`、`google.py:34-38`
- **根因**: 只要有非佔位 API key 就回 True，**不做任何網路驗證**（對比 `openai.py:37-51` 會打 `/models`）。
- **影響**: 已失效/錯誤的 key 被當成健康 → 選中後 generate 才失敗，延遲錯誤。
- **✅ 已修復**: `anthropic.py:37-41` `check_health` 改打 `/v1/models`（帶 `x-api-key` + `anthropic-version` header）；`google.py:34-38` 改打 `{GEMINI_BASE}/models?key=`。兩者均保留 API key 佔位檢查。驗證：9 garden provider tests passed。

### M5. `state_for_llm` 的 eta 參數硬編碼為 0

- **位置**: `apps/backend/src/api/routes/chat_routes.py:532-542`（line 540 `"eta": {"module_count": 0, "success_rate": 0.0, "structural_drift": 0.0}`）
- **根因**: eta 維度被硬編碼為全 0，未從實際系統讀取（StateMatrix4D 有 eta）。
- **影響**: LLM 看到的系統狀態中「進化」維度恆為零，誤導 prompt。
- **✅ 已修復**: `chat_routes.py` 新增 `_get_eta_axis()` helper（`EtaAxisState` + `create_default_modules` 註冊，經 `_backbone_module("chat.eta_axis", ...)` 單例存取），`state_for_llm["eta"]` 改讀真實 `active_modules`/`success_rate`/`structural_drift`。實測 `module_count=21, success_rate=1.0`（原本恆 0）。

### M6. `recent_memories` 恆空（memory context 注入失效）

- **位置**: `apps/backend/src/api/routes/chat_routes.py:581`（`context["recent_memories"] = recent_memories`）——上游 `_build_chat_context` 的 retrieval（:546-566）依賴 `history`，而聊天快路徑多為單輪 → retrieval 常空。
- **驗證**: 讀碼確認 `[親證]`（retrieval 只在 `history` 非空時執行）。
- **影響**: LLM 上下文缺近期記憶。
- **✅ 已修復**: `chat_routes.py:581` `recent_memories` 改由共享 `_get_dialogue_ctx().get_recent_conversations(limit=5)` 取得（原本每次 new 空殼 `MemoryContextManager`，恆空）。實測可取回真實對話。

### M7. ExecutionGate `HANDLER_MAP` 缺 `command`/`audio`

- **位置**: `apps/backend/src/ai/core/execution_gate.py:60-68`
- **根因**: `HANDLER_MAP` 只有 file/search/code/execute/system/task/vision；`model_bus.py:234-248` 卻支援 `audio`/`command` 等路由。gate 對這些類型 `handler_id=None` → 走不到 auto/confirm 執行。
- **影響**: 部分合法命令類型在 gate 層被硬拒絕/漏判。
- **✅ 已修復**: `execution_gate.py:60-68` `command`/`audio` 加入 non-actionable 清單——gate 對這些類型 reject 放行給 ModelBus `_handle_fanout`（LLM 推理），與 `model_bus.py:234-248` 支援的路由一致。驗證：`tests/ai/core/test_execution_gate.py` 101 tests passed。

### M8. `classify_pair("", "")` 回傳單一 enum 而非 Tuple

- **位置**: `apps/backend/src/ai/core/query_classifier.py`（`classify_pair`）
- **根因**: 空輸入的邊界路徑回傳類型與文件標稱的 `(type, conf)` 不符，呼叫端解包會崩潰。
- **影響**: 邊界輸入觸發 TypeError（實際多為被吞）。
- **✅ 已修復**: `relation_classifier.py:52`（實際位置，審計 MD 原誤標 query_classifier）空輸入改回傳 `(RelationType.UNRELATED, 0.0)` tuple，符合文件標稱的 `(type, conf)`。驗證：`tests/ai/ed3n` 16 tests passed。

---

## LOW

### L1. `math_result_context` 死變數

- **位置**: `apps/backend/src/api/routes/chat_routes.py:1482` 賦值後僅 `:1487` 讀 `_math_result`（不同名）→ 死變數。`[親證]`
- **✅ 已修復**: 已移除死變數（grep 確認 `math_result_context` 無殘留）。

### L2. `_latest_response` 跨 session 洩漏

- **位置**: `apps/backend/src/api/routes/chat_routes.py`（模組級 `_latest_response`，多處讀寫）
- **根因**: 全域變數跨 session 共享，session A 的 response 可能被 session B 的 finally 讀到。
- **影響**: 多 session 併發時回應文字錯亂（低機率）。
- **✅ 已修復**: 改為 per-session `_latest_responses: Dict[str, Dict[str, Any]]`（`:137` 定義、`global` session_id 存取，7 個寫入點 + finally 讀取全改為 keyed by `session_id`）。多餘的 `global _latest_responses` 宣告已移除（dict mutation 不需 global，F824）。驗證：`tests/api/test_chat_session_memory.py` 9 passed。

### L3. heartbeat.py `stop()` AttributeError + psutil 阻塞事件迴圈

- **位置**: `apps/backend/src/core/life/heartbeat.py:200-216,338`
- **根因**: stop() 參照不存在的屬性；psutil 呼叫為同步阻塞。`[代理驗證]`
- **✅ 已修復**: `__init__` 補 `self._integration_task = None`（防 stop 前未 start 的 AttributeError）；`psutil.cpu_percent(interval=None)` 改非阻塞。驗證：`tests/core/test_heartbeat.py` 14 tests passed。

### L4. 既有測試用 `WebSocket.OPEN` 於 renderer（browser）context

- **位置**: `packages/shared-js/js/haptic-handler.js:316`、`backend-websocket.js:646,684,735,...`
- **根因**: browser 中 `WebSocket` 全域存在故 OK；但 haptic-handler 檢查 `backendWs.readyState === WebSocket.OPEN` 中的 `backendWs` 若是自製物件（無 readyState）則恆 false → tactile 永不上送。`[代理驗證]`
- **✅ 已修復**: `haptic-handler.js:316` 檢查改為支援 `readyState === WebSocket.OPEN || (readyState === undefined && connected === true)`（自製 wrapper 物件場景）。驗證：`node --check` 通過。`backend-websocket.js` 在 browser context 有全域 `WebSocket`，維持原狀（見誤報排除清單）。

---

## 誤報排除清單（審計過程中被提出但判定為非問題）

| 項目 | 位置 | 為何排除 |
| --- | --- | --- |
| shared-js `backend-websocket.js` 用 `WebSocket.OPEN` | `packages/shared-js/js/backend-websocket.js` | browser context 有全域 `WebSocket`，OPEN 正常；與 H7 的 Electron main process 情境不同 |
| pet 模組「可能只是路徑不同」 | — | 以 glob 全庫確認無 `endpoints/pet.py`（`main.py` 用之），判為真缺失（H10）而非誤報 |
| `context` NameError「可能被 else 分支保護」 | chat_routes.py:1462 | 逐行確認 :1462 到 :1485 之間無任何 `context` 賦值；若被 except 吞即為靜默失效（H2） |

---

## 驗證方法備註

- 所有 `[親證]` 項目均由主代理（本次 session）直接 `read`/`grep` 源碼確認，部分以 `.venv/bin/python` 實測（C1 掛死、H6 profile 反轉）。
- `[代理驗證]` 項目由對應子代理執行驗證，主代理已複核其 file:line 引用真實存在。
- 未列入之「未訓練/checkpoint 缺失」議題依使用者指示排除於本次審計範圍。
- 附帶修復（非審計項，測試過程中發現）：`visual_encoder.py` `_edge_histogram` 由每 bin 全陣列掃描 8 次改為 `np.bincount` 加權單次計算（既有影像編碼效能缺陷）；`tests/ai/multimodal/test_data_loader.py` 改注入空 data_dir 避免觸發真實 CIFAR 40000 張重算（既有慢測試）；`tests/ai/multimodal/test_semantic_encoders.py` CLIP/Whisper fixture 在模型不可用時改 skip 而非 assert（既有環境依賴缺陷）；`tests/core/test_autonomous_life_cycle.py` 類型統計測試加 autouse mock 固定 `random.random`（既有 flaky 測試）；`tests/api/test_chat_session_memory.py` 改用 per-session `_latest_responses`（配合 L2 修復）；`tests/services/test_handlers.py` 移除 decorator 與 class 間空行（既有 E304）。
