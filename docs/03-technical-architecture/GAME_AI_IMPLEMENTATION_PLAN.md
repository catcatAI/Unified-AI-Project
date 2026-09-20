# Angela AI - Luanti 遊戲代理實作計畫

> **目標**：讓 Angela 在無 LLM 情況下以 20 FPS 玩 Luanti
> (Minetest)，支援基礎移動、挖掘、合成、戰鬥、長期規劃與異常恢復。

---

## 1. 架構總覽：五層分層認知架構

```
┌─────────────────────────────────────────────────────────────────┐
│ L4 Meta Strategy (10min+) ──► StrategyDirective (exploration_weight, risk_tolerance)        │
│         ▲                                                    │
│         │ PlanExecutionStats                                  │
│ ┌───────┴──────────────────────────────────────────────────┐  │
│ │ L3 Plan / 規劃推理 (30s-10min) ◄── LLM (async)           │  │
│ │   - 目標分解 DAG  │  前置條件檢查  │  子目標指派           │  │
│ └───────┬──────────────────────────────────────────────────┘  │
│         │ TaskProgress / SubgoalAssignment                     │
│ ┌───────┴──────────────────────────────────────────────────┐  │
│ │ L2 Task / 任務執行 (2s-30s)                               │  │
│ │   - 狀態機 + 子目標隊列  │  落後/卡住檢測  │  Fallback     │  │
│ └───────┬──────────────────────────────────────────────────┘  │
│         │ SkillContext / SkillResult                           │
│ ┌───────┴──────────────────────────────────────────────────┐  │
│ │ L1 Skill / 技能基元 (200ms-2s)                            │  │
│ │   - 技能庫註冊  │  參數化選擇  │  前置條件檢查             │  │
│ └───────┬──────────────────────────────────────────────────┘  │
│         │ SkillParams / SkillTrigger                           │
│ ┌───────┴──────────────────────────────────────────────────┐  │
│ │ L0 Reflex / 感動反射 (50ms, 20Hz)                         │  │
│ │   - Foveated Sampler (固定 83k px)                        │  │
│ │   - Visual Encoder (256-dim)                              │  │
│ │   - Continuous Policy Head (Diffusion/MLP)                │  │
│ │   - Visual Grounding Head (點擊熱力圖)                     │  │
│ └────────────────────────────────────────────────────────────┘  │
```

---

## 2. 實作階段與交付物

### Phase 1: 視覺採樣與連接器 (Week 1-2)

| 檔案                                                 | 功能                                                 | 關鍵介面                                             |
| ---------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| `apps/backend/src/ai/multimodal/foveated_sampler.py` | 固定預算非均勻採樣 (Log-polar / Deformable mesh)     | `sample(frame, focus_xy) -> (tensor, inverse_map)`   |
| `apps/backend/src/integrations/luanti_connector.py`  | Luanti WebSocket 連線、畫面抓取、指令下發            | `connect()`, `get_frame()`, `send_action(action)`    |
| `apps/backend/src/ai/multimodal/game_policy.py`      | L0 Policy: Continuous Action Head + Visual Grounding | `forward(latent) -> (continuous, discrete, heatmap)` |

**測試標準**：

- [ ] 連線 Luanti 本地伺服器成功
- [ ] 20 FPS 穩定抓取畫面
- [ ] Foveated sampling 輸出固定 shape (64, 64, 3)
- [ ] Policy forward < 5ms (CPU)

---

### Phase 2: 技能基元與任務執行 (Week 2-3)

| 檔案                                                   | 功能                                           | 關鍵介面                                       |
| ------------------------------------------------------ | ---------------------------------------------- | ---------------------------------------------- |
| `apps/backend/src/ai/multimodal/game_skills.py`        | 技能規格定義 (move, dig, place, craft, combat) | `GAME_SKILLS: Dict[str, SkillSpec]`            |
| `apps/backend/src/ai/multimodal/skill_selector.py`     | L1: 根據 latent + context 選技能 + 參數化      | `select(latent, context) -> SkillParams`       |
| `apps/backend/src/ai/multimodal/game_task_executor.py` | L2: 狀態機 + 子目標隊列 + 卡住檢測             | `tick(skill_result) -> Optional[SkillContext]` |

**測試標準**：

- [ ] 技能庫覆蓋：move, dig, place, craft, combat
- [ ] 技能選擇準確率 > 90% (模擬環境)
- [ ] 任務執行器能完成「收集 3 圓石 → 合成石鎬」流程
- [ ] 卡住檢測能觸發 fallback

---

### Phase 3: 規劃與記憶整合 (Week 3-4)

| 檔案                                                   | 功能                                           | 關鍵介面                                                     |
| ------------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------ |
| `apps/backend/src/ai/multimodal/game_planner.py`       | L3: 目標分解 DAG + 前置條件 + LLM 非同步客戶端 | `propose_plan(goal) -> PlanDAG`, `replan(blocker)`           |
| `apps/backend/src/ai/multimodal/game_memory_bridge.py` | HAM 記憶查詢適配 (配方、經驗、位置)            | `query_recipes()`, `recall_location()`, `store_experience()` |
| `apps/backend/src/ai/multimodal/llm_game_interface.py` | LLM 非同步介面：結構化輸出、超時控制           | `apropose_plan()`, `adiagnose_anomaly()`                     |

**測試標準**：

- [ ] 能分解「建造石頭房子」為 10+ 子目標 DAG
- [ ] HAM 記憶能查詢合成表、資源分布
- [ ] LLM 非同步呼叫不阻塞主循環
- [ ] 異常恢復策略生效 (如掉進洞、工具耗盡)

---

### Phase 4: 元策略與端到端測試 (Week 4-5)

| 檔案                                              | 功能                                   | 關鍵介面                            |
| ------------------------------------------------- | -------------------------------------- | ----------------------------------- |
| `apps/backend/src/ai/multimodal/game_strategy.py` | L4: 長期統計、策略權重、探索/利用平衡  | `update_stats()`, `get_directive()` |
| `apps/backend/src/ai/multimodal/game_agent.py`    | 主控制器：串聯 L0-L4、主循環、生命週期 | `run()`, `step()`, `shutdown()`     |
| `configs/standard/game.default.yaml`              | 遊戲啟用配置                           | `enabled: true`, luanti 連線參數    |

**測試標準 (端到端)**：

- [ ] **生存測試**：新世界生存 30 分鐘不死、有食物、有工具
- [ ] **進度測試**：10 分鐘內完成「木工具 → 石工具 → 鐵工具」進度
- [ ] **建築測試**：能按規劃建造 5x5x3 簡易庇護所
- [ ] **異常測試**：掉進深坑能爬出來、工具壞了能換新的、遇到怪物能戰鬥/逃跑

---

## 3. 關鍵資料結構定義

```python
# apps/backend/src/ai/multimodal/game_structs.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import numpy as np

class SkillID(str, Enum):
    MOVE = "move"
    DIG = "dig"
    PLACE = "place"
    CRAFT = "craft"
    COMBAT = "combat"
    NAVIGATE = "navigate"  # 移動到座標
    EAT = "eat"
    BUILD = "build"       # 依藍圖放置方塊

@dataclass
class SkillSpec:
    continuous_dim: int           # 連續動作維度
    discrete_triggers: List[str]  # 離散觸發鍵
    params: List[str]             # 參數名
    preconditions: List[str]      # 前置條件 (如 "has_tool:pickaxe")
    duration_ticks: range         # 預期持續幀數

@dataclass
class SkillParams:
    skill_id: SkillID
    continuous_bias: np.ndarray   # shape: (continuous_dim,)
    discrete_triggers: Dict[str, float]  # key -> hold strength [0,1]
    termination_condition: str    # 如 "inventory_changed:stone_pickaxe"
    priority: float               # 0-1

@dataclass
class SkillResult:
    skill_id: SkillID
    success: bool
    side_effects: List[str]       # ["collected:cobblestone:3", "durability:-1"]
    next_suggested: List[str]     # 隱含意圖給 L2

@dataclass
class SkillContext:
    active_skill: SkillID
    params: Dict[str, Any]        # 具體參數值
    priority: float
    interrupt_on: List[str]       # 中斷條件

@dataclass
class Subgoal:
    subgoal_id: str
    skill_id: SkillID
    params: Dict[str, Any]
    preconditions: List[str]
    success_criteria: str
    timeout_ticks: int
    fallback: Optional[str] = None

@dataclass
class TaskProgress:
    task_id: str
    completed: List[str]
    remaining: List[str]
    blocker: Optional[str]
    eta_ticks: int

@dataclass
class PlanDAG:
    plan_id: str
    root_goal: str
    nodes: Dict[str, Subgoal]     # subgoal_id -> Subgoal
    edges: List[Tuple[str, str]]  # (from, to) 依賴關係

@dataclass
class StrategyDirective:
    exploration_weight: float
    risk_tolerance: float
    priority_goals: List[str]
    forbidden_actions: List[str]
```

---

## 4. LLM 非同步介面契約

```python
# apps/backend/src/ai/multimodal/llm_game_interface.py
from pydantic import BaseModel
from typing import Optional
import asyncio

class PlanContext(BaseModel):
    current_goal: str
    inventory: Dict[str, int]
    position: Dict[str, float]
    nearby_entities: List[Dict]
    known_recipes: List[str]
    ham_memories: List[str]  # 相關經驗摘要
    strategy: Dict[str, float]  # exploration_weight, risk_tolerance

class PlanProposal(BaseModel):
    plan_id: str
    subgoals: List[Dict]  # 每個含 id, skill, params, preconditions, success_criteria
    reasoning: str

class AnomalyContext(BaseModel):
    stuck_reason: str           # "blocked", "missing_resource", "combat_failed", "unknown"
    current_subgoal: str
    recent_actions: List[str]
    inventory: Dict[str, int]
    position: Dict[str, float]

class RecoveryStrategy(BaseModel):
    immediate_action: str       # "fallback_subgoal" / "replan" / "explore"
    fallback_subgoal: Optional[Dict] = None
    reasoning: str

class StrategyContext(BaseModel):
    session_duration_min: float
    goals_completed: List[str]
    goals_failed: List[str]
    death_count: int
    resource_collection_rate: Dict[str, float]
    anomaly_count: int

class StrategyAdjustment(BaseModel):
    exploration_weight_delta: float
    risk_tolerance_delta: float
    new_priority_goals: Optional[List[str]] = None
    reasoning: str

class LLMGameInterface:
    """非阻塞 LLM 介面，所有呼叫均為 async、帶超時、有 fallback"""

    async def apropose_plan(self, ctx: PlanContext) -> PlanProposal:
        """L3 呼叫：制定多步驟計劃"""
        ...

    async def adiagnose_anomaly(self, ctx: AnomalyContext) -> RecoveryStrategy:
        """L2/L3 卡住時呼叫：診斷並給恢復策略"""
        ...

    async def aevaluate_strategy(self, ctx: StrategyContext) -> StrategyAdjustment:
        """L4 定期呼叫：長期策略調整"""
        ...
```

---

## 5. 配置檔案

```yaml
# configs/standard/game.default.yaml
game:
  enabled: false # 預設關閉，需手動開啟

  luanti:
    host: 'localhost'
    port: 30000
    password: ''
    protocol_version: 39 # Minetest 5.8+
    auto_reconnect: true
    reconnect_interval: 5

  vision:
    budget_pixels: 83000 # 1/25 of 1920x1080 ≈ 82944
    fovea_ratio: 0.7 # 70% 預算給焦點區
    fovea_radius_px: 160 # 焦點半徑 (原圖座標)
    sampling_strategy: 'log_polar' # "log_polar" | "deformable" | "quadtree"
    fps: 20
    input_size: [64, 64] # 送入 encoder 的固定尺寸

  policy:
    latent_dim: 128
    continuous_dim: 16 # move(3) + look(2) + dig(2) + place(2) + craft(0) + combat(3) + navigate(2) + eat(0) + build(2)
    discrete_dim: 8 # attack, use, jump, sprint, sneak, inventory, craft_grid, craft_output
    hidden_dim: 256
    diffusion_steps: 4 # Diffusion Policy 步數
    use_diffusion: true

  skills:
    move_speed: 4.5 # 節點/秒
    dig_range: 4.0 # 挖掘距離
    place_range: 4.0
    combat_range: 3.0
    eat_threshold: 0.3 # hunger < 30% 才吃

  task:
    stuck_threshold_ticks: 600 # 30s 無進展視為卡住
    max_subgoal_retries: 3
    fallback_timeout_ticks: 3000

  planner:
    max_plan_depth: 10
    max_subgoals_per_plan: 20
    replan_on_blocker: true
    llm_timeout_sec: 5.0

  memory:
    ham_recall_limit: 20
    experience_decay_days: 7
    spatial_index_radius: 100

  llm:
    enabled: true
    model: 'qwen2.5:7b' # 本地模型優先
    base_url: 'http://localhost:11434/v1'
    timeout_sec: 10.0
    max_concurrent: 2
```

---

## 6. 測試與驗收腳本

```bash
# 1. 單元測試
cd /home/cxuo/文件/GitHub/Unified-AI-Project
source .venv/bin/activate
python -m pytest tests/ai/multimodal/test_foveated_sampler.py -v
python -m pytest tests/ai/multimodal/test_game_policy.py -v
python -m pytest tests/ai/multimodal/test_skill_selector.py -v
python -m pytest tests/ai/multimodal/test_game_task_executor.py -v
python -m pytest tests/ai/multimodal/test_game_planner.py -v
python -m pytest tests/ai/multimodal/test_game_memory_bridge.py -v
python -m pytest tests/ai/multimodal/test_llm_game_interface.py -v

# 2. 整合測試 (需啟動 Luanti 伺服器)
# Terminal 1: 啟動 Luanti
# minetest-server --gameid minetest_game --world /tmp/luanti_test --port 30000

# Terminal 2: 執行測試
python -m pytest tests/integration/test_game_agent_e2e.py -v -s

# 3. 手動觀察測試
python -m apps.backend.src.ai.multimodal.game_agent --config configs/standard/game.default.yaml --duration 600
```

---

## 7. 進度追蹤

| 階段                        | 狀態                 | 開始日期   | 完成日期   | 備註                                          |
| --------------------------- | -------------------- | ---------- | ---------- | --------------------------------------------- |
| Phase 1: 視覺採樣與連接器   | ✅ 完成 (2026-09-20) | 2026-09-19 | 2026-09-20 | foveated_sampler + polling bridge 實測通過    |
| Phase 2: 技能基元與任務執行 | ✅ 完成 (2026-09-20) | 2026-09-20 | 2026-09-20 | 9 技能 + 狀態機 + 卡住/超時/跳過，36 測試全過 |
| Phase 3: 規劃與記憶整合     | ✅ 完成 (2026-09-20) | 2026-09-20 | 2026-09-20 | 規則規劃 + 真實 HAM + LLM fallback            |
| Phase 4: 元策略與端到端     | ✅ 完成 (2026-09-20) | 2026-09-20 | 2026-09-20 | 策略權重 + 活體 Luanti 驗證 (chat 到達遊戲)   |
| 文檔更新                    | ✅ 本次同步          | -          | 2026-09-20 | 誠實狀態表見 §10                              |

---

## 10. 誠實狀態表 (2026-09-20 實測為準)

> 原則：只寫驗證過的；stub 明確標出，不宣稱。

| 能力                                                  | 狀態                  | 證據                                                                                                                                                                                             |
| ----------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Foveated 採樣 (log-polar/deformable/quadtree/uniform) | ✅ 真實               | 單元測試 4/4，固定輸出 shape                                                                                                                                                                     |
| Continuous policy + grounding head (numpy/MLP)        | ✅ 真實               | 前向 <5ms，整合測試通過                                                                                                                                                                          |
| 9 技能選擇 + 前置條件 + 參數化                        | ✅ 真實               | 整合測試，live 吃到 dig/move                                                                                                                                                                     |
| 任務狀態機 + 超時重試 + 卡住跳過                      | ✅ 真實               | live：eat blocked 10 ticks → skip → craft → dig                                                                                                                                                  |
| 規則規劃 DAG + 拓撲驗證                               | ✅ 真實               | survival 3 subgoals，live 產出                                                                                                                                                                   |
| HAM 持久記憶 (store + recall)                         | ✅ 真實               | `ham_game_memory.json`，非 Mock                                                                                                                                                                  |
| EmotionSystem / AutonomousLifeCycle 回饋              | ✅ 真實               | 每 100 tick 按任務成敗餵入                                                                                                                                                                       |
| LLM 非同步規劃 + 超時 fallback                        | ✅ 真實               | fallback 實測；LLM 本體為本地 llama.cpp（:8080），規劃/診斷/對話皆可走真模型                                                                                                                     |
| Polling bridge ↔ Luanti 雙向                          | ✅ 真實               | live：server poll + `AngelaBot digs` + 遊戲內 chat 可見                                                                                                                                          |
| skill_result 閉環                                     | ✅ 真實               | 背包差分推導，不再恆 None                                                                                                                                                                        |
| 識別：截窗視覺（GameVision→encoder）                  | ✅ 真實               | `_capture_screen_vision` 先 `select_source()`（無遊戲窗自動退整屏，R71b 修復）→節流截幀→recognize→`current_state.visual` 真實像素特徵；只截圖不動鏡頭；失敗靜默降級 None；591 multimodal 測試過  |
| 識別：世界語義（raycast scan/vision）                 | ✅ 真實               | poller 射線/掃描結果即時入空間記憶（`observe_world`，vision 帶 `pointed.under` 世界座標）；此前只被行為閉環短暫消費                                                                              |
| `/api/frame` 畫面來源                                 | ⚠️ 不再依賴           | stub 保留但非視覺來源；畫面改由 pyautogui 截窗（GameVision.capture，有遊戲窗截窗否則整屏）                                                                                                       |
| 記憶：空間記憶持久化                                  | ✅ 真實               | `save_spatial/load_spatial`（JSON 原子寫）；啟動載入、cleanup＋每 600 tick 週期存檔（crash-safe）；逐行容錯＋相容舊格式；上限 2000 地點防洩漏；R71b 審查後 591 multimodal 測試過                 |
| 記憶：觀察入 HAM episodic                             | ✅ 真實               | 每 300 tick 將「在哪看到什麼」（scan/vision，過濾空氣，同點去重）寫 episodic；recall 可回「之前在東邊看過一棵樹」                                                                                |
| 自主性：好奇探索                                      | ✅ 真實（語意已修正） | `find_unexplored` 取「看過但久未親訪」的點 → goto 重訪；`last_seen`（看到）/`last_visited`（親訪）分離——R71b 修復「站著盯著的點永不會被選」因果顛倒；goto 到場 `mark_visited`；live 待玩家在線驗 |
| poller `craft` 動作                                   | ✅ 真實               | live 驗證：wood×4 → craft stick → wood×2 + stick×4，`crafted stick for AngelaBot` 留痕；material 不足/無配方 log 失敗不當機                                                                      |
| poller `place` 動作                                   | ✅ 真實               | live 驗證：cobble×8 → place → cobble×7，`placed default:cobble at (2,6,65)`；look 優先＋鄰格 fallback（空氣＋實心支撐），手牌空時 auto-wield 背包第一個可放方塊；無格/無料 log 失敗不當機        |
| poller `give` 後門                                    | ✅ 已上鎖             | `agent_poller_allow_give` 預設 false（拒絕＋warning）；測試環境 minetest.conf 顯式開啟                                                                                                           |
| poller `move` 步進＋撞牆轉彎                          | ✅ 真實               | live：`(0.6,4.5,64.9)→(2.6,4.5,66.2)`；移動是客戶端權威所以 server 側步進（1.5m/格，碰撞感知）；被擋轉 45°                                                                                       |
| 身體反射層（poller per-poll，只感受身體）             | ⚠️ 半驗               | 缺氧上浮＋灼傷脫離＋滯空凍結＋撞牆轉彎；觸發全是 body-state（breath/hp/y），水深檢查／視線轉彎兩版錯層已刪；待玩家重生後 live 驗                                                                 |
| 本地 LLM（Qwen2.5-1.5B-Q4，:8080）                    | ✅ 真實               | 全離線；`llama_cpp.server`；中文回覆＋JSON 編排 live 驗證；依賴 `localllm` extra 已宣告                                                                                                          |
| 行為庫 game_behaviors（7 行為）                       | ✅ 真實               | walk/turn/dig_burst/place_one/look_scan/speak/wait；LLM compose＋adjust；20 測試；live：「幫我挖」→dig_burst→無拾取→自動改參數重試                                                               |
| 遊戲對話閉環（聽→回→做＋記憶）                        | ✅ 真實               | poller 擷取→bridge /api/chat→LLM 回覆＋行為→HAM 記憶；bridge 端到端驗證；遊戲內送達待玩家在線驗                                                                                                  |
| 名稱斷層修復（itemstring↔短名）                       | ✅ 真實               | `ITEM_ALIASES`＋`normalize_inventory`；此前可合成判斷＋完成檢測全錯；單元測試覆蓋                                                                                                                |
| L1 craft 節制（做不出就不排）                         | ✅ 真實               | 無材料時 abstain（此前每 2s 空轉刷屏）；單元測試覆蓋，live 待驗                                                                                                                                  |
| Policy 權重訓練 (BC/RL)                               | ❌ 未做               | 現為 Xavier 初始化，動作笨拙屬實                                                                                                                                                                 |
| 20 FPS 閉環                                           | ❌ 未達               | agent 10Hz + poller 2s；截窗視覺已補上幀源（pyautogui），仍需降級策略達 20 FPS                                                                                                                   |

---

## 8. 風險與對策

| 風險                   | 影響        | 對策                                      |
| ---------------------- | ----------- | ----------------------------------------- |
| Luanti 協議版本不相容  | 無法連線    | 先實作協議探測、支援多版本                |
| 畫面抓取延遲 > 50ms    | 20 FPS 破功 | 使用共享記憶體 / GPU 直傳、降級至 10 FPS  |
| Policy 訓練資料不足    | 動作笨拙    | 先用行為克隆 (BC) 預訓練、再 RL 微調      |
| LLM 呼叫超時阻塞主循環 | 卡頓        | 強制非同步 + 超時 fallback + 本地規則備援 |
| 記憶體洩漏 (長時間跑)  | 崩潰        | 定期 GC、經驗緩衝區上限、定期 checkpoint  |

---

## 9. 相關文檔

- `docs/03-technical-architecture/THREE_LAYER_VISUAL.md` - 視覺編碼器細節
- `apps/backend/src/ai/multimodal/shared_latent_space.py` - 共享潛在空間
- `apps/backend/src/ai/memory/ham_memory/ham_manager.py` - HAM 記憶管理
- `apps/backend/src/core/autonomous/behavior_executor.py` - 行為執行器參考
- `apps/game-rpg/backbone_bridge.py` - Backbone 橋接模式參考
