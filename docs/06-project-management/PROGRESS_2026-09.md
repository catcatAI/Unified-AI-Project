
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
