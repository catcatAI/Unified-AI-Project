# 6D 軸端口路由系統建設計劃
## 2026-05-14 v1.0

---

## 願景

讓 θ 元認知軸作為「路由大腦」：
- 外部系統（LLM、HSP、CLI）只需要管理「端口」（port）
- 端口只需要聲明自己的存在（name、direction、semantic_vector）
- θ 軸根據所有端口的語義向量，自動決定：
  - 新軸的創建（allocation）
  - 現有軸的重新路由（re-routing）
  - 軸到端口的定向輸出（output routing）
  - 端口到軸的輸入合併（input routing）

最終：**後期只需要管理端口與 θ 軸，其他由 Angela 自行決定**

---

## 設計原則

1. **θ 軸作為路由核心** — 所有軸的創建/路由都由 θ 驅動
2. **端口聲明制** — 端口只需聲明 name + direction + semantic_vector
3. **最小配置** — 不需要手動指定軸→端口映射
4. **動態自組織** — θ 軸根據語義相似度自動路由

---

## 核心概念

### 端口（Port）

```
┌─────────────────────────────────────────┐
│  Port                                   │
│  ├─ name: str          (唯一標識)       │
│  ├─ direction: PortDirection  (IN/OUT/IO)│
│  ├─ semantic_vector: List[float] (32-dim)│
│  ├─ axis: Optional[str]  (綁定軸)       │
│  ├─ priority: float      (路由優先級)    │
│  └─ tags: List[str]     (分類標籤)      │
└─────────────────────────────────────────┘
```

| Direction | 說明 |
|-----------|------|
| IN | 數據輸入端口（外部→軸） |
| OUT | 數據輸出端口（軸→外部） |
| IO | 雙向端口 |

### 路由模式（θ 決策）

| 模式 | 觸發條件 | 動作 |
|------|----------|------|
| ALLOCATE_NEW_AXIS | 沒有軸匹配端口語義 | `create_axis()` + 綁定 |
| BIND_EXISTING_AXIS | 某軸語義靠近端口 | 綁定端口到軸 |
| RE_ROUTE_AXIS | 軸被多端口競爭 | 重新分配端口 |
| UNBIND_IDLE_PORT | 端口長期無數據 | 解綁定 |
| CASCADE_OUTPUT | θ 決定路由方向 | 軸→多端口廣播 |

---

## 架構模組

### 1. `axis_port_registry.py` — 端口註冊表

```
PortRegistry
  ├─ ports: Dict[str, Port]           (name → Port)
  ├─ axis_to_ports: Dict[str, List[Port]]  (軸 → 端口列表)
  ├─ register(port)                   (註冊端口)
  ├─ unregister(name)                 (移除端口)
  ├─ bind_port_to_axis(port_name, axis_name) (手動綁定)
  ├─ find_axis_for_port(port) → str   (θ 驅動的語義匹配)
  ├─ get_outputs_for_axis(axis) → List[Port]  (獲取軸的所有輸出端口)
  └─ get_inputs_for_axis(axis) → List[Port]    (獲取軸的所有輸入端口)
```

### 2. `theta_router.py` — θ 軸路由引擎

```
ThetaRouter
  ├─ registry: PortRegistry
  ├─ theta_values: DimensionState     (引用 StateMatrix4D.theta)
  ├─ routing_policy: Dict[str, Any]   (路由策略配置)
  ├─ resolve_route(port) → RouteDecision   (核心路由決策)
  ├─ auto_allocate() → List[AxisBinding]   (自動分配新軸)
  ├─ auto_bind_idle_ports()          (自動綁定閒置端口)
  ├─ cascade_output(axis_name, data) → List[Any]  (廣播輸出)
  └─ merge_input(axis_name, data_list) → Any  (合併輸入)
```

### 3. `port_channel.py` — 端口通道

```
PortChannel
  ├─ port: Port
  ├─ buffer: deque                   (數據緩衝區)
  ├─ max_buffer: int = 100
  ├─ push(data)                      (寫入數據)
  ├─ pull() → Optional[Any]         (讀取數據)
  ├─ peek() → Optional[Any]         (窺視不刪除)
  └─ clear()                         (清空緩衝)
```

### 4. `axis_output_manager.py` — 軸輸出管理器

```
AxisOutputManager
  ├─ router: ThetaRouter
  ├─ output(axis_name, data)         (θ 路由決定輸出)
  ├─ input(axis_name, data)          (θ 路由決定輸入)
  ├─ batch_output(data_dict)         (批量輸出)
  └─ get_port_data(port_name) → Any  (獲取端口數據)
```

---

## θ 軸路由決策流程

```
Port 註冊 → 計算與所有軸的語義相似度 → θ 軸更新 (novelty, complexity)
                                         ↓
                            θ.creation_urge > 0.6?
                              ↓ yes    ↓ no
                     創建新軸       綁定現有軸
                              ↓
                    計算軸 → 所有 IO 端口的路由
                              ↓
                    應用到 AxisOutputManager
```

---

## 實現步驟

### Phase 1: 核心註冊表

| # | 任務 | 檔案 | 說明 |
|---|------|------|------|
| 1.1 | Port dataclass | `axis_port_registry.py` | PortDirection enum, Port dataclass |
| 1.2 | PortRegistry 核心 | `axis_port_registry.py` | register/unregister/find_axis/bind |
| 1.3 | 與 StateMatrix4D 集成 | `state_matrix_adapter.py` | 添加 `_port_registry` 初始化 |
| 1.4 | 單元測試 | `test_axis_port_registry.py` | 5 個測試 |

### Phase 2: θ 路由引擎

| # | 任務 | 檔案 | 說明 |
|---|------|------|------|
| 2.1 | ThetaRouter 核心 | `theta_router.py` | resolve_route / auto_allocate / auto_bind |
| 2.2 | θ 觸發點集成 | `state_matrix_adapter.py` | allocation_decide() / create_axis() 觸發路由 |
| 2.3 | 路由策略配置 | `theta_router.py` | routing_policy (threshold, weights) |
| 2.4 | 單元測試 | `test_theta_router.py` | 5 個測試 |

### Phase 3: 端口通道與 I/O

| # | 任務 | 檔案 | 說明 |
|---|------|------|------|
| 3.1 | PortChannel | `port_channel.py` | push/pull/peek/clear |
| 3.2 | AxisOutputManager | `axis_output_manager.py` | output/input/batch_output |
| 3.3 | 與 RippleNode 集成 | `state_matrix_adapter.py` | 漣漪觸發 → 端口輸出 |
| 3.4 | 單元測試 | `test_port_channel.py` | 5 個測試 |

### Phase 4: 自動路由集成

| # | 任務 | 檔案 | 說明 |
|---|------|------|------|
| 4.1 | θ → port 自動路由 | `theta_router.py` | θ 更新時觸發路由重算 |
| 4.2 | 端口優先級管理 | `axis_port_registry.py` | priority-based routing |
| 4.3 | 端到端測試 | `test_port_routing_e2e.py` | port → axis → port 完整流 |
| 4.4 | 文檔更新 | TASK_PRIORITY.md | 標記完成 |

---

## 使用範例

```python
from core.autonomous.state_matrix_adapter import StateMatrixAdapter

sm = StateMatrixAdapter()

# 註冊端口
sm.register_port(
    name="llm_output",
    direction=PortDirection.IN,
    semantic_vector=[...],  # 32-dim
    tags=["llm", "text"]
)

sm.register_port(
    name="cli_input",
    direction=PortDirection.OUT,
    semantic_vector=[...],
    tags=["cli", "command"]
)

sm.register_port(
    name="hsp_channel",
    direction=PortDirection.IO,
    semantic_vector=[...],
    tags=["hsp", "network"]
)

# θ 軸自動路由
# - 計算 "llm_output" → ε 軸 (邏輯/推理)
# - 計算 "cli_input" → β 軸 (認知/命令)
# - 計算 "hsp_channel" → θ 軸 (元認知/協調)

# 輸出到端口
sm.output_to_port("cli_input", {"command": "status"})

# 從端口讀取
data = sm.input_from_port("llm_output")

# 批量廣播
sm.cascade_output("beta", {"focus": 0.8})
# → θ 路由決定廣播到 ["cli_input", "hsp_channel"]
```

---

## 與現有系統的關係

```
現有系統                    端口系統
─────────────────────────  ─────────────────────────
StateMatrix4D.theta    →   ThetaRouter (核心路由器)
create_axis()          →   ThetaRouter.auto_allocate()
allocate()             →   ThetaRouter.resolve_route()
RippleNode             →   AxisOutputManager (包裝)
StateMatrixAdapter     →   AxisOutputManager (集成點)
```

---

## 測試計劃

| 測試檔案 | 測試數 | 覆蓋內容 |
|---------|--------|---------|
| test_axis_port_registry.py | 5 | register/unregister/find_axis/bind/list |
| test_theta_router.py | 5 | resolve_route/auto_allocate/auto_bind/cascade |
| test_port_channel.py | 5 | push/pull/peek/clear/overflow |
| test_port_routing_e2e.py | 5 | port→axis→port 完整流 |

---

## 預期效果

- **後期只需管理端口** — `register_port()` / `unregister_port()`
- **軸自動創建** — θ 根據端口語義自動創建新軸
- **路由自動** — θ 根據現有軸的相似度自動綁定端口
- **0 配置** — 不需要手動指定 axis→port 映射表
- **可觀測** — `sm.full_report()` 包含端口狀態