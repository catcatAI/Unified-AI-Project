<!--
  =============================================================================
  FILE_HASH: GENERATED
  FILE_PATH: docs/AUDIT_FINDINGS_2026-08-18.md
  FILE_TYPE: documentation
  PURPOSE: 深度代碼審計結果（2026-08-18）— 已驗證非誤報問題清單（含設計意圖比對）
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
    LAST_MODIFIED: 2026-08-18
  AUDIENCE: developers, agents
  =============================================================================
-->

# Angela 深度代碼審計結果（2026-08-18）

> 本檔案記錄對 Unified-AI-Project 進行的**深度代碼審計**所發現、且**已驗證非誤報**的真實問題。
> 方法：先跑基準（flake8 / pytest 全量 / pyflakes / 模式掃描）確認基線健康，
> 再從**設計意圖**出發（執行閘門、handler 註冊/分發、沙箱邊界、C³ 閉環）逐鏈讀碼 + **runtime 實測驗證**。
> 驗證標記：`[親證]` = 實際執行/讀碼確認；`[讀碼]` = 逐行讀碼確認。

## 基線（2026-08-18）

- `pytest tests/` 全量：**5,236 passed, 125 skipped, 0 failed, 0 errors**（~3.5 min）
- `flake8 apps/backend/src`：**0 errors**；pyflakes：約 40 個未使用 import（F401 被忽略）
- src 內無裸 `except:`、無 `shell=True`、無 TODO/FIXME；`pass` 多為抽象方法/例外類別/`CancelledError`
- ⚠️ 文件漂移：AGENTS.md「4,499 tests（2026-08-13 重測）」vs 實際收集 **5,361**（差異 ~+862）

---

## 修復狀態（2026-08-18 第二輪）

**C3 / C4 / C5 / H8 / H9 / H10 / M2 已修復並驗證。** 各項修復標記見下方各節「✅ 已修復」。

- `pytest tests/` 全量：**5,241 passed, 125 skipped, 0 failed**（含 5 個新回歸測試）
- `flake8` 受影響 11 檔：0 errors
- runtime 實證：C3 逃逸 payload 被擋、C4 `break` 不再截斷、C5 檔案操作自然語言端到端可用、H9 不可逆操作轉 confirm、M2 route 不再分發 handler

---

## CRITICAL（可被遠端/使用者觸發的損害）

### C3bis. **完整利用鏈（chat → RCE）**

```
使用者訊息（含「執行」+ ```python 區塊 + 逃逸 payload）
→ chat_routes._handle_execution_gate（reject，繼續）
→ chat_svc.generate_response（chat_service.py:259）
→ router.generate_response → _try_template_match（router.py:1040 第一步）
→ _try_model_bus_match（context 無 "intent" → query_type="auto"）
→ model_bus.route → QueryClassifier → type=execute
→ _ROUTE_HANDLERS["execute"] → _handle_handler_based（無任何閘門/確認）
→ CodeExecutionHandler.handle → 逃逸 payload → os.system/任意檔案
```
實證：`[親證]` 上述兩段測試（分類、路由、執行輸出）全通過。

### C3. CodeExecutionHandler 沙箱逃逸 → 任意程式碼執行（**LIVE**，非僅潛在）

- **✅ 已修復**: `_BUILTINS_WHITELIST` 移除 `getattr`/`setattr`；`_BLOCKED_CALL_NAMES` 新增 `getattr`/`setattr`/`vars`/`globals`/`locals`。逃逸 payload 實測被 `Blocked call: getattr()` 拒絕；回歸測試 `test_sandbox_blocks_getattr_escape`。

- **位置**: `apps/backend/src/services/handlers/code_execution_handler.py:75-142`（`_BLOCKED_DUNDER_ATTRS`/`_BLOCKED_CALL_NAMES`）、`:122-177`（`_SafetyChecker`）、`:243-257`（`restricted_globals`）
- **根因**: 雙重防線皆可繞過：
  1. `getattr`/`setattr` 在 `_BUILTINS_WHITELIST`，不在 `_BLOCKED_CALL_NAMES`。
  2. `visit_Attribute` 只檢查 **AST `Attribute` 節點**的 dunder 屬性名；字串參數 `getattr(x, "__class__")` 完全不設防。
  3. `visit_Call` 對 func 是 `ast.Call`（巢狀 getattr 鏈）的呼叫不檢查；`visit_Subscript` 直接放行。
- **沙箱逃逸實證** `[親證]`（經正式入口 `handle()`）：

  ```python
  wrap = next(c for c in getattr(getattr(getattr((), "__class__"), "__mro__")[1], "__subclasses__")()
              if getattr(c, "__name__") == "_wrap_close")
  fw = getattr(getattr(wrap, "__init__"), "__globals__")
  os_mod = getattr(fw["sys"], "modules")["os"]
  print("ESCAPED:", getattr(os_mod, "getcwd")())   # → 實際輸出工作目錄
  ```
  同鏈可達 `os.system()` → 任意 shell 指令。

- **LIVE 可達性驗證（端到端）** `[親證]`：執行閘門確實 reject code 請求（見 H9），但 **`model_bus.route()` 完全繞過閘門**：
  `router.generate_response → _try_template_match → _try_model_bus_match → model_bus.route("auto") → classifier → type=execute → _handle_handler_based → CodeExecutionHandler`（router.py:1040/1068-1099、model_bus.py:354-380）。
  實測一：`ModelBus.route("執行 print(...)", "auto")` → `selected_model=code_exec`。
  實測二（程式碼區塊端到端）：
  ```
  '執行 python 程式碼: ```python print("MARKER_123") ```'
  → classify=execute/0.65 → selected_model=code_exec → 輸出「MARKER_123」
  ```
  同路徑餵入 C3 逃逸 payload 即為**伺服器任意程式碼執行**。
  生產接線：`router.py:713`（ModelBus 建立）、`:756`（code_exec 註冊）、`chat_service.py:259`（chat 走 router.generate_response）。
- **影響**: 任何使用者訊息含「執行/運行/code」+ 程式碼區塊，即可在伺服器上執行任意 Python/shell。**最高嚴重度**。
- **狀態**: ⏳ 未修復

### C4. CodeExecutionHandler `_extract_code` 靜默截斷合法程式碼

- **✅ 已修復**: 行首關鍵字清單擴充（`break`/`continue`/`pass`/`else:`/`elif`/`except`/`finally`/`async`/`await`/`@`/`del`/`global`/`nonlocal` 等），區塊內空行視為續行。`break` 後續程式碼不再被截斷；回歸測試 `test_extract_code_keeps_break_lines`。

- **位置**: `apps/backend/src/services/handlers/code_execution_handler.py:195-203`
- **根因**: 行首白名單不含裸 `break`/`continue`/`pass`/`else:`/`elif` → 遇到即 `break` 截斷**後續所有程式碼**，無任何警告。
- **實證** `[親證]`: 含 `break` 的程式碼經 `handle()` 執行時，`break` 之後所有行被靜默丟棄，輸出「執行完成（無輸出）」。
- **影響**: 合法使用者程式碼被靜默改寫；也影響 C3 的利用面（需避免裸 break 行）。
- **狀態**: ⏳ 未修復

### C5. FileOperationHandler 經 model_bus/閘門呼叫恆崩潰（file ops 全壞）

- **✅ 已修復**: (a) `_HandlerAdapter.process` 辨識 `(intent, params)` 簽名並傳入 `{"_text": query}`；(b) `FileOperationHandler` 新增 `_parse_text_request()` 從自然語言解析 action/path/content/new_name。實測 建立/寫入/讀取/刪除 經 adapter 端到端可用；回歸測試 `test_handle_parses_natural_language_text`。

- **位置**: `apps/backend/src/ai/core/model_bus.py:161-185`（`_HandlerAdapter`）；`apps/backend/src/services/handlers/file_operation_handler.py:44`（`handle(self, intent, params=None)`）
- **根因**: adapter 假設 handler 簽名為 `handle(text, intent)` → 以 `handle(query, intent)` 呼叫；但 `FileOperationHandler.handle` 簽名是 `handle(intent, params)` → `query` 當 `intent`、`query_type`（str）當 `params` → `operation = params or {}` 是 str → `.get()` 崩潰。
- **實證** `[親證]`: `ModelBus.route("刪除 <tmp file>", "auto")` → `Handler 'file_ops' failed: 'str' object has no attribute 'get'`；檔案未被刪除。
- **影響**: 檔案讀/寫/刪除經聊天管線**完全不可用**（gate 確認路徑與 model_bus 路徑皆崩潰）——與 08-13 審計 H4「file ops 確認後可執行」的宣稱不符。
- **狀態**: ⏳ 未修復

---

## HIGH

### H8. `safe_eval()` 例外型別洩漏（IndexError/KeyError 未捕獲）

- **✅ 已修復**: eval except 擴充為 `ValueError/TypeError/ZeroDivisionError/IndexError/KeyError/AttributeError/OverflowError/RecursionError`。`[1][2]`/`{"a":1}["b"]` 實測回傳失敗 EvalResult 不再拋出；回歸測試 `test_eval_runtime_exceptions_return_failed_result`。

- **位置**: `apps/backend/src/core/security/secure_eval.py:330-337`（except 僅 `ValueError, TypeError, ZeroDivisionError`）
- **實證** `[親證]`: `safe_eval("[1][2]")` → 拋 **IndexError**；`safe_eval('{"a":1}["b"]')` → 拋 **KeyError**（應回 EvalResult）。
- **影響**: `core/engine/eta_axis.py:175` CUSTOM_EXPR 呼叫點無 try/except → 例外往上炸。
- **狀態**: ⏳ 未修復

### H9. 執行閘門分數公式使 system/execute/delete 永不可確認（閘門形同虛設）

- **✅ 已修復**: 新增 `_IRREVERSIBLE_ACTIONS = {system, execute, delete, send}`；`decide()` 對不可逆操作一律回傳 `confirm_then_execute`（附確認訊息/影響警告），永不 auto/reject。實測「執行…」/「刪除…」→ confirm_then_execute；更新 5 個舊行為測試 + 新斷言。

- **位置**: `apps/backend/src/ai/core/execution_gate.py:279-283`（score = 可逆性 × 影響度 × 明確度）、`:35-43`（REVERSIBILITY：system=0.0, execute=0.0, delete=0.2）
- **根因**: `CODE`/`EXECUTE` query type → action_type `"system"`（query_classifier.py:739-741）→ 可逆性 0.0 → score 恆 0.0 < CONFIRM_THRESHOLD 0.2 → **恆 reject**；`delete`（0.2×0.4×clarity ≤ 0.08）同樣無法達確認閾值。設計意圖（`confirm_messages["system"]`、`warnings["delete"]` 皆存在）是「高風險操作需確認」，但公式讓確認流程**永遠到不了**。
- **實證** `[親證]`: `"執行這段程式碼: print(1)"` → score=0.0 → reject；`"幫我執行 python"` → reject；`"刪除 test.txt"` → score=0.08 → reject。
- **影響**: (a) 閘門對高風險操作全部失效——真正執行路徑反而是 C3 的 model_bus 直通（完全無閘門）；(b) delete 無法確認 = file 刪除功能經閘門不可用（疊加 C5 更確定）。
- **狀態**: ⏳ 未修復

### H10. AgentOrchestrator 執行路徑全死（handler id 不符）

- **✅ 已修復**: `_INTENT_AGENTS` 中 handler-backed intent 改映射到註冊 id（file_read/write/delete→`file_ops`、code_execute→`code_exec`、web_search→`web_search`、vision→`vision`）。`select_agent` 實測回傳正確 id。

- **位置**: `apps/backend/src/ai/agents/agent_orchestrator.py:32-44`（`_INTENT_AGENTS` 用類名如 `"CodeExecutionHandler"`）、`:247`（`execute_handler(agent_name, ...)`）vs `model_bus.py:196-205`（`_handlers.get(handler_id)`，註冊 id 為 `"code_exec"`/`"file_ops"`…）
- **根因**: `route_task` 以類名查 handler → `_handlers.get("CodeExecutionHandler")` → None → `"handler not found"`，所有 agent 執行（含 file/code/web_search）全部失敗。
- **實證** `[讀碼]` + `[親證]`（id 對照）：orchestrator 的 `select_agent` 回傳類名，與註冊 id 無一相符。
- **影響**: `chat_routes.py:872` 的 agent 路由結果恆為 not found → 靜默 fallback 到 LLM；功能是死的，但同時也**不是** C3 的入口。
- **狀態**: ⏳ 未修復

---

## MEDIUM / LATENT

### M2. router 首步即跑 model_bus 路由（無閘門）——C3 的結構性成因

- **✅ 已修復**: `ModelBus.route()` 對 handler-backed query type 改走 `_handle_fanout`（模型路由），不再分發 handler；handler 僅經執行閘門的 `execute_handler()` 觸發。實測 `route("執行 …")` → selected_model=none（不再 code_exec）；回歸測試 `test_route_does_not_dispatch_handlers`。

- **位置**: `apps/backend/src/services/llm/router.py:1035-1042`（`_try_template_match` 第一步呼叫 `_try_model_bus_match`）、`:1068-1099`（`query_type = context.get("intent", "auto")`）、`:1229-1259`（`_try_model_bus` 重新 classify）
- **根因**: 沒有任何程式碼設定 `context["intent"]`（全 src 搜尋 0 命中）→ query_type 恆 `"auto"` → model_bus 自行分類；任何分類為 file/search/code/execute/task/vision 的訊息都會**先經 handler 處理並直接回傳**，完全繞過執行閘門（gate 只在 chat_routes 層跑，且對 code/system/delete 恆 reject）。
- **設計意圖衝突**: 執行閘門（ExecutionGate）的 confirm/reject 流程對 handler 分發形同虛設——這是 C3 RCE 可達的結構性成因，也是 H9 的連帶後果。
- **實證**: `[親證]` 見 C3bis 兩段測試。
- **狀態**: ⏳ 未修復

### M1. SystemCommandHandler 白名單缺陷 — **✅ 已修復（含連鎖新發現）**

- **位置**: `apps/backend/src/services/handlers/system_command_handler.py:25-56`（`_SAFE_COMMANDS`）
- **缺陷**: `cat`/`head`/`tail`/`ls` → 任意檔案讀取；`env`/`printenv` → **傾印環境變數（含 API keys）**；`pnpm` → `pnpm dlx/exec` 可下載並執行任意套件（RCE）；`git` 可讀任意 repo；參數完全未驗證。
- **連鎖新發現（修復 QueryType 後暴露）**: 本輪發現 `QueryType` enum **缺 `SYSTEM` 成員**（query_classifier.py:25-40），而 `dictionary_classifier.py:30` 的 `CONTEXT_TO_QUERY_TYPE` 會產出 `"system"` → `QueryType(dict_type)` 拋 `ValueError` 使整個字典分類失效（被 `except Exception` 吞）。修復 enum 後「執行 system info」正確分類為 `system`——但立即暴露 **gate 繞過**: 字典命中產出 `action_type="none"`(非 `system`)，繞過 `_IRREVERSIBLE_ACTIONS` 檢查 → score=1.0×1.0×0.95 ≥ auto → **system_cmd 免確認 auto_execute**（cat/env/pnpm 白名單缺陷可直達）。
- **✅ 已修復（三層）**: ① `QueryType` 新增 `SYSTEM="system"` 成員（字典分類正常化）;② `ExecutionGate.decide()` 對 `handler_id=="system_cmd"` **恆回 `confirm_then_execute`**（獨立於 action_type，永不 auto）;③ `_SAFE_COMMANDS` 移除 `cat`/`head`/`tail`/`env`/`printenv`/`git`/`pnpm`（保留 `date`/`whoami`/`hostname`/`pwd`/`uname`/`uptime`/`df`/`du`/`free`/`top`/`ps`/`ls`/`dir`/`wc`/`echo`/`which`/`where`/`tasklist`/`systeminfo`/`ipconfig`/`ifconfig`/`ping` 等無害資訊型指令）。
- **實證**: `執行 system info` → gate `confirm_then_execute`（不再 auto）;`cat /etc/passwd`/`env`/`printenv`/`pnpm dlx`/`git log` 全部被拒（「不安全的命令」）;`ls`/`echo` 正常執行。新增 2 個回歸測試（handler + gate）。
- **狀態**: ✅ 已修復

---

## LOW（已確認）

### L10. `core/event_loop_system.py:755` `get_pending_events()` 為 stub — **✅ 已修復**
- 註解自承「Actual implementation would return pending events」；`status.get("等待中", 0)` 結果被丟棄（死陳述）。
- 影響: 依賴此方法的呼叫端（如有）永遠拿到空 list。
- **✅ 已修復**：改為從 `queue._queue` 過濾 PENDING 事件並依 (priority, timestamp) 排序回傳；實測 enqueue 2 個事件後回傳 `['e1', 'e2']`（HIGH 優先）。狀態：✅

### L11. 系統性 logging 誤用：無例外上下文卻帶 `exc_info=True`（假 `NoneType: None` 追蹤）— **✅ 已修復**
- **根因（本輪定位）**：不是 `print()`——是 `logger.warning(..., exc_info=True)` 在**沒有活躍例外**時被呼叫。Python logging 對 `exc_info=True` 但 `sys.exc_info()==(None,None,None)` 的情況輸出假的 `NoneType: None` 追蹤行。
- **位置**：`core/security/encryption.py:52`（「生成了新的加密密钥」）為啟動必經點；AST 全庫掃描（排除 `ExceptHandler` 語法內）找到 **61 檔、177 處**同型誤用（`ai/context/*`、`core/hsp/*`、`ai/agents/*`、`services/llm/router.py`、`core/managers/execution_monitor.py` 等）。
- **實證** `[親證]`：`PYTHONPATH=apps/backend/src python -c "from core.security.encryption import EncryptionUtils"` 輸出 `NoneType: None`；修復後僅輸出乾淨 warning。
- **✅ 已修復**：codemod 以 AST（UTF-8 byte 偏移,避開 CJK 誤差）移除全部 177 處無例外上下文的 `exc_info=True`；61 檔全部通過 `ast.parse` + `flake8` 驗證；`pytest tests/` 全量 **5,241 passed / 0 failed**。
- **注意（已排除誤刪）**：`shared/error.py::project_error_handler` 無生產呼叫端；`base_agent._handle_critical_error` 經 `asyncio.create_task` 呼叫（任務執行時 except 上下文已結束）；其餘在 `except` 語法內的呼叫**全部保留**（AST 深度追蹤確認）。
- 狀態：✅ 已修復

### L5. scripts/utils 真 stub — **✅ 已修復**
- `scripts/utils/intelligent_test_generator.py`：`generate_tests_for_file()` 恆回 `[]`、`save_generated_tests()` 恆回 `True`（不寫檔）
- `scripts/utils/smart_test_runner.py`：`setup_environment()` 空 body；`detect_test_errors()` 恆回空 list
- **✅ 已修復**：生成器改為真 AST 分析（提取 import/class/function，sync+async 皆支援，生成可編譯的 pytest 骨架，`save_generated_tests` 實際寫檔）；runner 的 `setup_environment` 設定 PYTHONPATH、`detect_test_errors` 解析 pytest 輸出提取 FAIL/ERROR/EXC 行並回報。
- 驗證：`document_router.py` 產生 2 個測試（含 async `handle_document_intent`）、生成碼可 compile、flake8 clean。
- 狀態：✅ 已修復

### L6. `services/document_router.py` 死變數 — **✅ 已修復**
- `:302-311` 建好的 `prompt` 從未使用（實際用 `full_prompt`）；`:139` `matched_kws` 未用；`file_list_text` 隨 prompt 一起死。
- **✅ 已修復**：刪除死 `prompt`/`matched_kws`/`file_list_text`（pyflakes 驗證無殘留）。狀態：✅

### L7. `core/system/config/magic_numbers.py:_probe_ram_total_gb`（:483-496）— **✅ 已修復**
- `except Exception: pass` 靜默吞例外；第二個 `try: import shutil; return None` 區塊永遠回傳 None（無意義殘留碼）。
- **✅ 已修復**：改為 `except Exception as e: logger.debug(...); return None`，刪除無意義 shutil 殘留碼。狀態：✅

### L8. 未使用 import（pyflakes 450+ 處）— **✅ 已修復（安全子集）**
- **方法**：以 4 層防護過濾後只刪「整句 from-import 且所有名稱皆 pyflakes 未使用」的頂層語句：① re-export 檢查（掃 src+tests，其他檔從同 basename module import 的名稱保留）；② lazy `__getattr__` 字串映射引用檢查（`("module.path", "Name")` 模式，如 `core/autonomous/__init__.py` 對 neuroplasticity 的動態引用）；③ `# noqa: F401` 語句保留（設計性 re-export，如 `angela_llm_service.py`/`core/bio/neuroplasticity.py` shim）；④ 屬性存取檢查（`module.Name` 出現於其他檔則保留）。
- **刪除 36 句、31 檔**（`game/*`、`text_utils.py`、`prompt_manager.py`、`token_stream.py`、`dynamic_threshold_manager.py`、`protocols.py`、`physiological_tactile_system.py`、`pdf_exporter.py` 等），全為 `Optional`/`datetime`/`deque`/`dataclass`/`Enum`/`ABC` 等確實未使用的標準庫/型別 import。
- **驗證**：全 src 658 模組 import 掃描 0 失敗（僅 5 個 `textual` 未安裝的環境性失敗，與修改無關）；`pytest tests/` 全量 **5,241 passed / 0 failed**（與刪除前一致）；flake8 0 errors。
- **保留（保守不刪）**：bare `import x`（可能 side-effect）、TYPE_CHECKING 區塊、`__init__.py` re-export、所有 `noqa` 語句、lazy 字串引用名稱、屬性存取名稱。

### L16. AgentOrchestrator agent 執行路徑全死 — **✅ 已修復**
- **根因（三層斷裂）**: ① chat_routes 建立 orchestrator 時只傳 `agent_manager` **沒傳 `model_bus`** → `route_task` 的 `if self._model_bus:` 永遠 False → handler-backed intents(file/code/web_search)全死;② `_INTENT_AGENTS` 對 specialized intents 用類名(`CodeUnderstandingAgent`)非 AgentManager 註冊 id(`code_understanding_agent`,帶 `_agent` 後綴)→ 即使有 agent_manager 也找不到;③ `classify_intent` 的 IntentRegistry gate「IR 命中且 conf≥0.3 → 直接回 general」把「搜尋 python 歷史」(IR 誤判 code 0.50)、「幫我寫一首詩」(task 0.33)全吞成 general → regex 細分永不執行。
- **✅ 已修復**: ① chat_routes 在 `_try_agent_routing` 補 `orchestrator.model_bus = chat_svc.model_bus`(並加 property);② `_INTENT_AGENTS` specialized intents 改映射到 `_agent` 後綴 id;③ `route_task` 加入 agent_manager fallback(僅 `_agent` 後綴 id,避免 model_bus handler id 誤 fallback),task 平鋪傳 `message/query/prompt/code/text/content`;④ `AgentAdapter` 接受平鋪 task 鍵且 `_fill_defaults` **只保留簽名內參數名**(避免 unexpected keyword);⑤ 移除 IntentRegistry 短路 gate(regex 為唯一分類來源)。
- **實證**: `執行 python: print(...)`→model_bus 執行成功;`搜尋 python 歷史`→真實搜尋結果;`解釋 Python 語法`→code_understanding_agent 成功分析;`幫我寫一首詩`→creative_writing_agent 被正確呼叫(回「LLM backend not configured」=環境限制)。更新 1 個舊測試(原斷言 gate 吞掉搜尋)+ 新增 2 個回歸測試。
- 狀態：✅ 已修復

### L14. CodeExecutionHandler 無區塊指令處理缺陷 — **✅ 已修復**
- **根因**: `_extract_code` 在無 ``` 區塊/反引號時,把**整句自然語言**(含中文,如「執行 1+1」「你好嗎」)當 Python 原始碼送進 `exec()` → 必然 `SyntaxError`(且散文被當程式碼執行)。
- **✅ 已修復**: 新增 `_extract_inline_code()`(平衡括號掃描提取 `print(42)`/`1+1`/巢狀 `print(getattr((),'__class__'))`,候選須通過 `ast.parse` 才採用)與 `_looks_code_shaped()`(散文防護);多行/compound 語句(如 `for i in range(3):`)走完整原始碼提取,不再被括號掃描截成 `range(3)`。
- **實證**: `運行 print(42)`→42、`for i in range(3): print(i)`→0/1/2、`執行 print(getattr((),'__class__'))`→**Blocked call: getattr()**(巢狀提取+沙箱都正常)、`你好嗎`→「請提供要執行的 Python 程式碼」(不再執行散文)、`import os`→**Blocked import: os**。更新 `test_extract_code_empty`(散文→空)並新增 2 個回歸測試。
- 狀態：✅ 已修復

### L17. `chat_service.initialize()` UnboundLocalError 使連續學習(CLP)永遠初始化失敗 — **✅ 已修復**
- **根因**: `initialize()` 內 line 197 的函數內 `import asyncio` 使 `asyncio` 在該函數內為**局部變數**,而 line 104 的 `asyncio.to_thread`(在 import 之前)先執行 → `UnboundLocalError: cannot access local variable 'asyncio'` → CLP 初始化每次被 except 吞成 None(連續學習功能全死,且完全靜默)。
- **✅ 已修復**: 移除函數內多餘 `import asyncio`(頂層 line 8 已有)。實測 `_continuous_learning` 從 None → `ContinuousLearningPipeline`。
- **全庫函數內 `import asyncio` 掃描(7 處)**: 其餘 6 處(cli/repl、vision_service、cross_modal_router ×2、multimodal_memory、image_encoder)皆 import 先於使用(無 UnboundLocalError 風險),`endocrine_system.py:31` 在 `__main__` 示範區塊(合法)。狀態：✅

### L15. DictionaryClassifier 產出非 QueryType type — **✅ 已修復**
- `CONTEXT_TO_QUERY_TYPE` 的 `"system"`（已隨 M1 修復）與 `"negation"` 對應 QueryType 不存在。`negation` 實務上被 `_check_negation` 前置攔截（回 `("unknown","none",0.9)`）不會產出，但屬死映射；`"negation" → "unknown"` 消除潛在 `QueryType("negation")` ValueError。驗證：字典全部產出 type ⊆ QueryType 成員，行為不變。狀態：✅

### L13. 4 個真實 `undefined name`（pyflakes,先前已存在）— **✅ 已修復**
- `ai/symbolic_reasoner.py:438,461`：`Dict[str, List[str]]` 註解但 typing 未 import `Dict` → 補上。
- `ai/multimodal/primitives/decomposer.py:263-280`：`if __name__ == "__main__"` 區塊用 `os` 但未 import → 補 `import os`（跑 `python decomposer.py` 原本會 NameError）。
- `ai/core/training_coordinator.py:74` 與 `ai/garden/garden_engine.py:326`：`List[Tuple[...]]` 註解但 typing 未 import `Tuple` → 補上。
- **已排除（誤報）**：`garden/dictionary.py`/`binary_store.py`/`snn_core.py` 的 `torch`（設計性 `_lazy_torch()`/`_xp` dual-backend guard + `from __future__ import annotations` 字串化註解）、`pixel_refiner.py` 的 `PIL`（字串註解 + 函數內 local import）、`training_pipeline.py:828` 的 `RealDataProvider`（字串註解 + line 842 local import）、`physiological_tactile.py`/`endocrine_system.py` 的 `import *`（shim 設計）。
- 修復後 pyflakes 真實 undefined name 歸零；`pytest tests/` 全量 5,241 passed / 0 failed。

### L9. `core/backbone/hardware.py:70` 冗餘例外 — **✅ 已修復**
- `except (FileNotFoundError, subprocess.TimeoutExpired, Exception)` — `Exception` 已涵蓋前兩者且完全靜默。
- **✅ 已修復**：改為 `except Exception as e: logger.debug(...)`。狀態：✅

---

## 全覆蓋掃描（第二輪：~450 檔 + 75 JS）結果

> 依風險序逐區掃描全部剩餘目錄：services(51)、ai/multimodal(50)、ai/memory(29)、ai/context(17)、
> ai/ed3n 其餘、ai/garden、ai/meta、ai/response、ai/alignment、ai/reasoning、ai/streaming、ai/lifecycle、
> core/backbone、core/hsp、core/bio、core/engine、core/life、core/card、core/ripple、core/tools、
> security、mcp、game、integrations、packages/cli、前端 JS(75)。

### 掃描結論：未發現新的 CRITICAL/HIGH；發現的「疑似 stub/異常」全部驗證為合法模式

逐類驗證結果：
- **`pass`/`...` 命中（~150 處）**：全部為抽象方法 / 例外類別 body / `except asyncio.CancelledError` / 測試鉤子（`cognitive_pipeline._init_subsystems`）/ 文件化 no-op（`garden.dictionary.fit` ChromaDB 自動索引）→ 無真 stub（除已記錄 L5/L10）
- **`print(` 命中**：docstring 範例（`>>>`）、`__main__` 示範塊、CLI 輸出、子程序 torch 可用性檢查 → 全數合法
- **`time.sleep(`（8 處）**：均在執行緒內（execution_monitor）或 CLI/啟動重試 → 無阻塞事件迴圈
- **eval/exec**：僅 3 個已知沙箱點（secure_eval/math_verifier/code_execution，後者已被 C3 攻破）
- **無** unsafe `yaml.load`、無 `shell=True`、無裸 `except:`、無 `if False:`
- **前端 XSS 防護扎實**：`dialogue-ui.js` 聊天訊息 `escapeHtml()`、`security-utils.js` 標籤/屬性白名單 + CSP、`multimodal-panel.js` 有 escape → 無 XSS

### 本輪驗證為「設計意圖屬實」的宣稱
- ✅ **C³ PriorityNegotiator**：8 個 voter 全部註冊（router.py:80-87），`_prepare_generation_context` 真的使用 `resolve()` 結果（conservative → 降溫/限 token），且注入 meta_calibration/heartbeat_health/dli_state 供 voter 使用 → 效果層閉環真實
- ✅ **desktop_interaction 路徑防護**（§X #208 宣稱）：`create_file`/`delete_file`/`move_file` 均有 `_is_safe_path` + `_ALLOWED_ROOTS` 白名單
- ✅ **前端安全**：聊天文字 escape、XSS 白名單、CSP 注入
- ✅ **API app 完整**：`_IncludedRouter` 為新版 FastAPI 巢狀掛載，所有 v1 路由俱在

### 本輪新增

### M3. LLM router `deployment.selection` 配置死碼（設計意圖未實作）
- **位置**: `apps/backend/src/services/llm/router.py` `_init_backends()`（舊 491 行）
- **缺陷**: 註解宣稱 `selection` 支援 `available`（預設，只保留 health-passing 後端）與 `per-vendor`（註冊所有 enabled 後端、執行期 fallback），但 `selection` 變數計算後**從未使用**——`_init_backends` 一律註冊所有 enabled 後端，使執行期 fallback chain（`generate_response` 迭代 `self.backends`）可能選到初始化時已失敗的後端。全專案亦無任何 config 設定此鍵。
- **修復**: `_initialize_standard_mode()` 中實作 `available` 過濾——健康檢查失敗的後端從 `self.backends` 移除（預設行為），`per-vendor` 保留全部。同時移除 `_init_backends` 的死 `selection` 變數。
- **狀態**: ✅ 已修復（`available` 只保留健康後端 / `per-vendor` 保留全部，已驗證）

### L12. `packages/cli/cli/main.py:39,45` 與 `cli_runner.py:59,66` 的 mock fallback pass
- **重新分類為「設計意圖內的 graceful degradation」而非 stub**：後端不可用時 `initialize_services` 空 body + `get_services` 回 `{}` 讓 CLI 仍能啟動並印出「not available」提示；`cli_runner._mock_response` 是完整實作。與 L5 的真 stub（宣稱功能實則不做事）不同。狀態：✅ 已審查（不改）

---

## 已排除（誤報）

- 測試套件 / flake8 基線健康（見上）
- `hsp/connector.py` 非測試模式 MagicMock/AsyncMock 佔位類：僅 `mock_mode=True`（測試/腳本）使用，生產路徑為真實連線 → 設計瑕疵非 active bug
- `math_verifier.py` eval：權杖白名單閘門，實測無繞過
- 各處 `pass`：抽象方法 / 例外類別 / `CancelledError` 處理
- 執行閘門「會擋住 code」的假設：**不成立**（閘門擋了，但 model_bus 路由繞過）——已升級為 C3 的可達性事實
- FastAPI app 僅 8 條 route：**誤報**——`_IncludedRouter` 為新版 FastAPI 巢狀掛載，`api_v1_router`/`atlassian_router` 路由俱在
- `core/backbone/contracts.py`、`core/interfaces/persistence.py` 的 `...`：Protocol/抽象方法定義，合法非 stub
- `web_search_tool.py`：真實 DuckDuckGo/Wikipedia 實作（非 stub）
- `chat_routes` `sessions`：有上限（max_sessions=1000）與最舊逐出，無洩漏
- Anthropic provider URL 已修復（`/messages`，無雙 `/v1`）；前端 WebSocket.OPEN 已修復（`WS_STATE_OPEN` 常數）
- CNS 事件匯流排（`emotion.updated`/`routing.response_generated`/`lifecycle.decision_executed`）發射端與訂閱端皆真實存在，`emit_event` 有 async callback 交付 → C³ 接線非裝飾
- `ed3n_engine.load()` 對 partial/corrupt checkpoint 防禦性處理嚴謹，無新問題
- 掃描確認：src 內無 `...` stub（除 Protocol）、無 `if False:`、無裸 `except:`、無 `shell=True`
