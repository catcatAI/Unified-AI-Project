
## R80 — Luanti mod 配置化＋mypy 棘輪 540→518（遊戲規劃棧清零）

### 一、Luanti 部署面收斂（接 R79 全域掃尾發現）
- `agent_poller/mod.conf`：補 per-world 配置註解（`agent_poller_bridge_url`、`agent_poller_allow_give`），LAN 部署照表可查
- `GAME_AI_IMPLEMENTATION_PLAN.md` 狀態表新增「poller bridge URL ✅ 可配置」條目
- `INVOCATION_MATRIX.md` run_luanti_agent 條目補 bridge URL 配置說明

### 二、mypy 棘輪 540→518：遊戲規劃棧清零
| 檔案 | 修復 |
|---|---|
| `game_planner.py`（12→0） | **真運行時 bug**：`_parse_llm_proposal` 對 pydantic `PlanSubgoal` 呼叫 `.get()`——LLM 提案一解析就 AttributeError，被 except 吞掉靜默退回規則規劃，LLM 規劃路徑從未工作。改屬性存取＋回歸測試鎖定（解析/依賴邊/未知 skill 降級 MOVE）。另修 var-annotated ×4、no-any-return、`params: Dict = None` 簽名 |
| `game_task_executor.py`（10→0） | `_handle_blocked` 局部窄化＋None 防禦守衛（呼叫端保證非 None，註明契約）；`dependencies: Optional[List[str]]` 簽名 |

### 三、驗證
- 全倉 **5,804 passed, 0 failed**（+1 回歸測試）；multimodal 605 passed
- mypy **518 鎖定**（`mypy_budget.txt` 同步）；black/isort/flake8/prettier/核對門（25+10+11+33）全綠
- 地圖重生成零漂移（5246/10000）

## R81 — 三域 mypy 清零 518→497＋靜默降級全系統掃描

### 一、mypy 棘輪：key_manager / cross_modal_router / hsp.transport 各 7→0
| 檔案 | 修復 |
|---|---|
| `shared/key_manager.py`（7→0） | `abc_km` 宣告前移 Optional＋TYPE_CHECKING 匯入；`_load_keys` 窄化 non-dict JSON；`key_hashes` 型別收口；`get_security_key/get_api_key` isinstance 窄化回傳值 |
| `services/cross_modal_router.py`（7→0） | 四個 lazy getter 補回傳型別＋TYPE_CHECKING 前向宣告＋None 斷言 |
| `core/hsp/transport.py`（7→0） | **真死路徑修復**：`MQTTTransport.publish` 呼叫不存在的 `ExternalConnector.publish`——一發布就 AttributeError。生產路徑（HSPConnector._raw_publish_message）用的是 `send(message)` 契約，改為 topic 併入 message 走 `send()`。另修 `disconnect` 對齊 ExternalConnector 回 None 的語意、`_subscription_manager` Optional 宣告、mp.Queue 型別標註 |

### 二、靜默降級全系統掃描（59 個「except 無 log＋return 空值」候選逐一抽查）
結論：**全部為合法模式**——可選依賴偵測（playwright/torch/faster_whisper）、超時語意（waiting_scheduler / send_action_wait 的 None=逾時是 API 契約）、確定性引擎的 None=不可解約定（math_verifier/_solve_calendar）、驗證函式回 False 的職責。無 `_parse_llm_proposal` 式真 bug 吞噬。440 個無 log handler 中多數為 import 防護與窄化 except，屬可接受面。

### 三、驗證
- 全倉 **5,804 passed, 0 failed**；hsp 57 passed、cross_modal 25 passed、key_manager 4 passed
- mypy **497 鎖定**；black/flake8/prettier/核對門（25+10+11+33）全綠
