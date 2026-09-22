
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

## R82 — 三域再清零 497→476＋跨檔測試 TypeError 噪聲根治＋棘輪門分布報告

### 一、mypy 棘輪：biological_integrator / backbone.training / demo_context_system 各 7→0
| 檔案 | 修復 |
|---|---|
| `bio/biological_integrator.py`（7→0） | `get_art_workflow` 死型別源頭修（`-> None` → `Optional[ArtLearningWorkflow]`，實際有回傳值）；PAD 窄化 `getattr` 防禦；`get_config` None 防禦（`or {}`）×2；單例 `_initialized` getattr 模式 |
| `backbone/training.py`（7→0） | **method/attr 撞名**：`persistence_path` 屬性與同名方法共存——方法體 `return self.persistence_path` 回傳的是可呼叫物件而非字串（型別揭發的真 bug）。方法改 `get_persistence_path()`；`mountable.persistence_path(key)` 同步相容 |
| `ai/context/demo_context_system.py`（7→0） | **真死碼**：demo 呼叫 `Context(id=, data=)` 與 `storage.save/load`——全是不存在的 API（真實是 `Context(context_id=, context_type=)`、`save_context/load_context`）。此 demo 一跑即炸。對齊真實 API＋閉環實測通過 |

### 二、跨檔 TypeError 噪聲根治（既有、stash 驗證非本輪引入）
`test_biological_integrator.py` 的 `_mock_heavy_modules` fixture 過寬——把輕量配置模組 `magic_numbers`/`tiered_loader` 整個塞進 `sys.modules` 為 MagicMock。之後任何檔案觸發 bio 背景循環，`from ... import loop_sleep` 拿到 MagicMock，`asyncio.sleep()` 即炸（三檔組合 14 次 TypeError）。修 fixture 只 mock 真正重的模組 → 組合噪聲 **14→0**。另 `hardware_profile.apply_multiplier`／`magic_numbers.loop_sleep` 加非數值防禦（深度防禦）。

### 三、mypy_budget_gate 新功能：`--top N` 按檔案分布報告
`python scripts/mypy_budget_gate.py --top 10` 在門檻輸出附「按檔案錯誤分布 Top-N（棘輪下一輪清零候選）」——「型別債集中區＝死路徑集中區」的經驗固化為工具能力。

### 四、驗證
- 全倉 **5,804 passed, 0 failed**；backbone 298、context 159、bio+core 32 passed
- mypy **476 鎖定**；black/isort/flake8/prettier/核對門全綠

## R83 — 長尾收割 476→432＋基準回歸確認無退化

### 一、基準回歸（棘輪修復後無退化確認）
angela_bench 全量重跑：native **80/26.7/97.5/0/100**、native-max mc **100%**——與 R79 官方數據逐位一致，R80–R82 的 6 個真 bug 修復零副作用。

### 二、長尾收割：11 檔 44 錯清零（--top 報告驅動）
| 檔案 | 要點 |
|---|---|
| `services/math_verifier.py`（5→0） | SAFE_OPS 型別收口、一元/二元 op 窄化 float()、`result` 變數重用清理 |
| `core/interfaces/protocols.py`（2→0） | ModelProvider 別名 fallback → `Any`（非 None，避免 type 賦值錯誤） |
| `engine/art_learning_workflow.py`（3→0） | milestones 標註、min key lambda 化、overall_progress float() |
| `multimodal/game_behaviors.py`（5→0） | lambda 簽名統一雙參（型別推斷失敗根因） |
| `hsp/performance_optimizer.py`（5→0） | **真 bug**：`message_metrics = self.message_metrics[-N:]` 把 deque 切片賦回 deque 欄位（切片回 list）——改重建 deque 保留 maxlen |
| `backbone/pairs.py`（2→0） | WaitingScheduler 別名 type: ignore |
| `module_manager/__init__.py`（3→0） | 可選 import 別名收口、`_build_deps_map` 回傳型別 str→Dict（原宣告與實作不符） |
| `primitives/decomposer.py`（2→0） | sort key object 窄化 |
| `backbone/structure.py`（5→0） | 三處 no-any-return list() 收口、kind None 防禦 str 化 |
| `life_intensity_formula.py`（3→0） | l_s float 標註、callback 變數遮蔽清理（`callback` 在同函式兩種簽名重用——mypy 揭發） |
| `ai/alignment/__init__.py`（4→0） | 可選 import 與 fallback stub 的 no-redef 收口 |

### 三、驗證
- 全倉 **5,804 passed, 0 failed**；multimodal game_behaviors 40 passed
- mypy **432 鎖定**；black/flake8/prettier/核對門全綠

## R84 — Dashboard E2E：Preview 實測七面板＋WS chat 死路徑修復（planned→partial）

### 一、Preview 實測（backend:8000＋dashboard:3100 實跑）
七面板逐一走訪：Chat（WS 🟢 Connected）、Models（後端表格＋統計）、Context（State Matrix＋12 intents）、Memory（誠實提示未初始化）、System（CPU/RAM/Disk 即時值）、Pet（互動閉環：Feed 後 Happiness 50→55、Hunger 50→30）、Config（Deployment/LLM/Backends/System 摘要）——全部渲染正常、資料來自真實後端 API。

### 二、E2E 抓到的真死路徑（修復）
**Dashboard Chat 面板從未成功發送過訊息**：
1. ChatPanel 不送 handshake——後端 websocket_handler 強制 10s 內 handshake，否則 4001 斷線
2. 發送格式 `{"type": "chat", "content"}` 不在後端分發清單——第一條被當 handshake 消費、之後被 echo，永遠拿不到 chat_response

修復：onopen 送 handshake、發送改 `{"type": "chat_message", "data": {"content"}}`（與 desktop electron 客戶端契約一致）。實測閉環：`You: 1+1等於幾？` → `Angela: 1+1 = 2.0`（確定性數學引擎，route=llm, emotion=happy）。

### 三、契約鎖定
`tests/services/test_dashboard_ws_chat_e2e.py`（3 tests）：handshake 必要性、chat_message 契約回 chat_response、**舊格式只會 echo** 的回歸鎖定（防止再走回死路徑）。

### 四、驗證
- web-dashboard `tsc --noEmit` 0 errors
- 全倉 **5,807 passed, 0 failed**（+3 E2E 契約測試）
- 真相源 dashboard-e2e planned→partial（附 Preview 實測證據）
