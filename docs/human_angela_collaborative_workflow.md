# Human+Angela 協作工作流
## 2026-05-14 v1.0

---

## 願景

Angela 不是替代人類，而是**增強人類**。
人類做決策，Angela 執行、追蹤、反思、提供建議。

---

## 核心原則

1. **人類主動** — 目標、價值觀、重大決策由人類設定
2. **Angela 代理** — 執行、重複任務、監控、提供分析
3. **雙向反饋** — 人類糾正錯誤，Angela 學習進化
4. **透明可追蹤** — 所有操作有日誌，所有狀態可查看
5. **θ 自糾** — 當懷疑當前行動時，Angela 主動請求確認

---

## 工作流模式

### 模式 1: 目標導向（Goal-Oriented）

```
Human: "幫我分析這個代碼庫的架構問題"

  Angela:
    → CodeInspector.inspect() → 結構化結果
    → integrate_code_inspect() → 更新 ε 軸複雜度
    → navigate_to_attractor(["math_overload"]) → ε 軸趨向分析模式
    → 提取問題列表

  Angela → Human: "發現 3 個 Critical 問題、12 個 High 問題..."
            "最優先的是 X，建議先處理，原因如下："
            "建議我自動修復哪些？哪些需要你親自確認？"

  Human: "自動修復測試覆蓋率，架構問題我來看"

  Angela:
    → 自動修復測試文件
    → 觸發 θ 自糾 (creation_urge += 0.1)
    → 追蹤修復結果
    → 報告完成

  Human → Angela: "好，繼續監控這個代碼庫的質量趨勢"
```

### 模式 2: 探索學習（Exploration）

```
Human: "我想了解這個項目的測試框架"

  Angela:
    → CodeInspector 分析測試文件結構
    → TemporalState 查詢歷史趨勢
    → GradientField 計算當前認知狀態
    → 生成分析報告

  Angela → Human: "項目有 3 種測試框架混合使用..."
            "單元測試覆蓋率 67%，集成測試覆蓋率 43%..."
            "我標記了 5 個測試黑洞，需要關注"

  Human: "幫我提高單元測試覆蓋率"

  Angela:
    → 識別覆蓋率低的模組
    → 生成測試模板
    → 應用漣漪效應（每修復一處，影響臨近模組）
    → 追蹤覆蓋率趨勢
    → 定期報告進度

  Human → Angela: "每小時報告一次覆蓋率變化"
```

### 模式 3: 創意生成（Creative）

```
Human: "我們需要一個新的用戶反饋系統"

  Angela:
    → θ 軸 novelty 提升
    → ε 軸 complexity 提升
    → 檢索現有架構中相似的模式
    → 模擬可能的方案

  Angela → Human: "根據現有架構，有 3 種可能的方案：
    A: 事件驅動（低耦合，高複雜度）
    B: REST API（簡單，強耦合）
    C: 消息隊列（可擴展，額外依賴）
    推薦 A，因為你的架構已經支持事件驅動"

  Human: "用 A，但要保持簡單"

  Angela:
    → 生成實現計劃
    → 分配到 StateMatrixAdapter 的軸上
    → 端口路由：代碼端口 → ε 軸，分析結果
    → 觸發 creation_urge
```

### 模式 4: 複查審計（Review）

```
Human: "檢查上週的所有代碼變更"

  Angela:
    → CodeInspector 分析 git diff
    → TemporalState 查詢歷史快照
    → 觸發 θ_negativity (audit_intensity)
    → detect_misallocated_points()
    → 生成審計報告

  Angela → Human: "上週 47 個文件變更..."
            "發現 2 個潛在的錯配需要確認..."
            "單元測試覆蓋率下降了 3%，建議回滾或補測"

  Human: "標記那 2 個錯配，追踪問題"

  Angela:
    → correct_misallocation()
    → 設置監控 watchpoints
    → 下次對話時主動報告
```

---

## 端口配置示例

```python
# 人類輸入端口（命令）
sm.register_port(
    name="human_command",
    direction="in",
    semantic_vector=text_to_vector("human command instruction task", 32),
    tags=["human", "command"]
)

# Angela 輸出端口（建議）
sm.register_port(
    name="angela_suggestion",
    direction="out",
    semantic_vector=text_to_vector("analysis recommendation suggestion advice", 32),
    tags=["angela", "output"]
)

# 代碼檢查端口
sm.register_port(
    name="code_inspector",
    direction="io",
    semantic_vector=text_to_vector("code quality architecture test", 32),
    tags=["code", "analysis"]
)

# 數學驗證端口
sm.register_port(
    name="math_verifier",
    direction="io",
    semantic_vector=text_to_vector("calculation number equation math", 32),
    tags=["math", "epsilon"]
)
```

---

## θ 軸觸發條件

| 觸發 | 條件 | 動作 |
|------|------|------|
| 懷疑 | 分配結果與預期不符 | `trigger_theta_negativity()` |
| 審計 | 人類要求複查 | `audit_intensity` 提升 |
| 創建 | 新需求無匹配軸 | `creation_urge` 提升 |
| 校正 | 發現錯配點位 | `correct_misallocation()` |

---

## HTTP API 觸發

```bash
# 人類發送命令
POST /state/axis/{axis}/update  {"values": {"focus": 0.8}}

# 獲取 Angela 分析
GET  /state/summary

# 觸發代碼審計
GET  /state/theta/detect

# 導航到分析模式
POST /state/navigate  {"target_tags": ["math_excite"], "max_steps": 3}

# 端口狀態
GET  /state/port/list
```

---

## 狀態報告格式

```json
{
  "state_matrix": {
    "alpha": {"energy": 0.7, "comfort": 0.6},
    "beta": {"focus": 0.8, "curiosity": 0.5},
    "gamma": {"happiness": 0.6, "calm": 0.4},
    "delta": {"bond": 0.7},
    "epsilon": {"complexity": 0.5},
    "theta": {"novelty": 0.6, "creation_urge": 0.3}
  },
  "human_collaboration": {
    "pending_tasks": [...],
    "confirmed_tasks": [...],
    "correction_needed": [...],
    "attractor_state": "analytical"
  },
  "recommendations": [
    {"action": "add_tests", "reason": "coverage dropped", "confidence": 0.8}
  ]
}
```