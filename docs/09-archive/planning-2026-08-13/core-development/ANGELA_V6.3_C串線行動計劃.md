# Angela v6.3 — 串線行動計劃

**版本**: 6.3
**日期**: 2026-05-17
**目標**: 對話/文件/代碼/搜尋/檔管/LLM/學習/成長全串線，配置驅動，無硬編

---

## 一、v6.2.x 歷史完成狀態（追溯更新）

### P0 完成項（需重新確認狀態）

| 項目 | 原計劃狀態 | 實際代碼狀態（v6.3 審計） |
|------|-----------|--------------------------|
| P0.1 `chat_completion()` wrapper | ✅ 已刪除舊介面 | ✅ 保留 thin wrapper，運作正常 |
| P0.2 `EvolutionEngine` 刪除 | ✅ 刪除 | ❌ **退化** — `chat_service.py:38` 仍引用不存在的檔案；B17 已建立 stub 但未串入學習迴路 |
| P0.3 `DialogueManager` + `ToolDispatcher` 廢棄 | ✅ 刪除 | ✅ 檔案不存在，零引用 |
| P0.4 `AutonomousEvolutionEngine` 刪除 | ✅ 刪除 | ✅ 檔案不存在，零引用 |
| P0.5 `ExecutionManager` 刪除 | ✅ 刪除 | ✅ `ai/execution/execution_manager.py` 存在但零引用（audit 準確） |

### P1 完成項（需重新確認狀態）

| 項目 | 原計劃狀態 | 實際代碼狀態（v6.3 審計） |
|------|-----------|--------------------------|
| P1.1 `core/managers/execution_manager.py` 刪除 | ✅ 刪除 | ✅ 檔案不存在 |
| P1.2 HAMMemoryManager 統一 codex 來源 | ✅ 實作 | ⚠️ **退化** — `FantasyDMAgent` codex 未啟用（line 83 設為空），DocumentBuilder 直接從 HAMMemoryManager 讀取，但 FantasyDMAgent 本身從未被 ChatService 調用 |
| P1.3 隔離測試 | ✅ 14 測試通過 | ✅ 維持 |
| P1.4 `IntentRegistry` 統一意圖檢測 | ✅ 創建並接線 | ✅ 仍在 PC + DB 中使用 |

### P2 完成項（需重新確認狀態）

| 項目 | 原計劃狀態 | 實際代碼狀態（v6.3 審計） |
|------|-----------|--------------------------|
| P2.1 ChatService 分離（< 1000 行） | ✅ 598 行 | ✅ 維持（610 行） |
| P2.2 8D 座標追蹤 | ✅ `_update_eta()` | ⚠️ **退化** — 座標計算了但未注入 prompt，LLM 拿到只是數字不懂含義 |
| P2.3 RAGManager 評估 | ⚠️ 待評估 | ⚠️ 未評估，RAGManager 仍存在未接線 |
| P2.4 PlanningAgent 處理 | ⚠️ 待處理 | ✅ 標注 deprecate()，未被引用 |
| P2.5 CreativeWritingAgent 重寫 | ✅ 63→158 行 | ✅ 維持 |

### B 系列修補（需重新確認狀態）

| Bug | 原計劃狀態 | 實際代碼狀態（v6.3 審計） |
|-----|-----------|--------------------------|
| B4 TemplateLibrary thread-safety | ✅ 修復 | ✅ `threading.Lock` + `asyncio.Lock` 已加入 |
| B6 HAMMemoryManager + FantasyDMAgent | ✅ 已確認 | ⚠️ FantasyDMAgent 未被調用 |
| B7 ProjectCoordinator fallback | ✅ 已測試 | ✅ `_fallback_decompose()` 存在 |
| B8 ProjectCoordinator 整合 fallback | ✅ 已測試 | ✅ `_integrate_subtask_results()` fallback |
| B9 DocumentBuilder segment timeout | ✅ 已修復 | ✅ `asyncio.wait_for(timeout=15.0)` |
| B10 WaitingScheduler vs direct calls | ⚠️ 標注差異 | ✅ 差異已標注，無需行動 |
| B11 `_learn_format()` 去重 | ✅ 已修復 | ✅ `_learned_format_keys` |
| B12 IntentRegistry 統一 | ✅ 已接線 | ✅ PC + DB 都在用 |
| B13 `get_template_library()` race condition | ✅ 雙重檢查鎖 | ✅ 已修復 |
| B14 `_fallback_response()` hasattr | ✅ 已有 getattr | ✅ 維持 |
| B15 PlanningAgent 零引用 | ✅ 已標注 deprecate | ✅ 維持 |
| B16 AlignedCreativeWritingAgent | ✅ 觀察中 | ✅ examples/ 目錄，無需操作 |
| B17 EvolutionEngine 不存在 | ❌ **新問題** | ✅ B17 修復：已建立 stub |
| **B18 主流程未串執行層** | ❌ **新發現** | ❌ L2 決策層 + L3 執行層缺席 |

### 退化摘要

```
P0.2: EvolutionEngine → B17 建立 stub，但未串入學習迴路
P1.2: FantasyDMAgent 未被調用，codex 效果未驗證
P2.2: 8D 座標未注入 prompt（座標計算了但 LLM 不理解含義）
P2.3: RAGManager 未評估
B18: 執行層（DesktopInteraction/BrowserController/AudioSystem/Live2DIntegration）
     存在但未接入 ChatService 主流程
```

---

## 二、v6.3 行動範圍

### 不做的事（避免重複實作）

以下模組**已存在且功能完整**，只需接線，不重寫：
- `StateMatrix4D` — 8D 狀態管理 ✅
- `DimensionState.compute_coordinate()` — 動態座標 ✅
- `IntentRouter` — 意圖分流 ✅
- `ProjectCoordinator` — 任務分解 ✅
- `DocumentBuilder` — 長文建構 ✅
- `MathVerifier` — 數學推理 ✅
- `CodeInspectorBridge` — 代碼理解 ✅
- `HAMMemoryManager` — 分層記憶 ✅
- `TemplateLibrary` — 模板學習 ✅
- `AnchorLearningEngine` — 錨點學習 ✅
- `ConfigLoader` — 配置讀取 ✅
- `ActionExecutor` — 動作執行總控 ✅
- `DesktopInteraction` — 桌面檔管 ✅
- `BrowserController` — 網頁搜尋 ✅
- `AudioSystem` — 音頻系統 ✅
- `Live2DIntegration` — Live2D 渲染 ✅

### 要做的事（接線 + 填空）

```
S1 配置層         — 剝離硬編，建立 YAML 配置 + 多模組配置讀取框架
S2 意圖擴展       — 新增 file_op / web_search / llm_manage / learn 意圖
S3 LLM 管理       — 配置驅動的模型選擇與降級 + LLM 延遲觸發介面
S4 REPL 終端      — 命令解析 + 自動意圖識別
S5 學習閉環       — 雙層配置 + 自我優化 + ConfigLoader.merge_config()
S6 端到端測試     — REPL 跑完整一圈
S7 小腦反射系統   — 搔癢 + 安全邊界 + CerebellumEngine.trigger_tickle()
```

---

## 三、S1 — 配置層（無新代碼，純 YAML + 替換）

### 目標
所有硬編的意圖關鍵字、閾值、路由規則、LLM 配置、檔案操作白名單，全部剝離到 YAML。

### 新增配置文件

```
config/
├── angela_core.yaml           # 【Authority】意圖關鍵字、閾值、路由規則
├── llm_providers.yaml          # 【Authority】模型列表、端點、超時、重試策略
├── file_ops.yaml              # 【Authority】允許的檔案操作、黑白名單、路徑限制
├── anchor_rules.yaml          # 【Authority】軸狀態解讀規則（動態生成非硬編）
├── tickle_config.yaml         # 【Authority】搔癢反射安全配置（獨立安全配置，S7）
│
└── angela/                    # 【Learned】Angela 自己補充（雙層配置）
    ├── learned_patterns.yaml  # 意圖關鍵字補充
    ├── learned_thresholds.yaml # 閾值學習
    └── learned_routes.yaml    # 路由策略學習
```

### 雙層配置說明

| 層 | 位置 | 來源 | 可被 Angela 修改 |
|----|------|------|----------------|
| Authority | `config/angela_core.yaml` 等 | 人寫 | ❌ 否（核心邏輯不可變） |
| Learned | `config/angela/learned_*.yaml` | Angela 自學 | ✅ 是（疊加在 Authority 上） |

合併時：Learned 只可新增 key，不可覆蓋 Authority 的任何 key。

### 硬編剝離清單（來自代碼審計）

| 位置 | 硬編內容 | 目標配置 |
|------|---------|---------|
| `chat_service.py:108` | `_detect_math_intent()` keyword list | → `angela_core.yaml: math_keywords` |
| `chat_service.py:109` | `_detect_code_intent()` keyword list | → `angela_core.yaml: code_keywords` |
| `chat_service.py:110` | `_estimate_complexity()` thresholds | → `angela_core.yaml: complexity_thresholds` |
| `project_coordinator.py` | fallback keyword patterns | → `angela_core.yaml: fallback_patterns` |
| `document_builder.py` | segment timeout (15s) | → `angela_core.yaml: segment_timeout_seconds` |
| `angela_llm_service.py` | model selection logic | → `llm_providers.yaml: routing_policy` |
| `angela_llm_service.py` | httpx timeout (30s) | → `llm_providers.yaml: providers[].timeout` |
| `template_library.py` | predefined templates | → `angela_core.yaml: predefined_templates` |
| `cerebellum_engine.py` | 姿勢庫（無配置化） | → `angela_core.yaml: pose_library` |
| `tickle_config.yaml` (new) | 搔癢敏感度/動畫映射 | → S7 配置 |

### S1 關鍵缺口（MD示例 vs 代碼實現差距）

| 缺口 | MD描述 | 代碼實際 | 風險 |
|------|--------|---------|------|
| 多模組配置讀取 | 各模組從 `ConfigLoader` 讀取自己的配置檔 | `ConfigLoader` 存在但祇有通用讀取，無多檔案支援 | 高：S2-S7 各模組需要讀取不同配置，但框架未定義 |
| `anchor_rules.yaml` 解讀 | 「軸狀態解讀規則（動態生成）」 | 檔案不存在，無生成邏輯 | 高：P2.2 退化（座標未注入 prompt）的根因 |
| 配置熱重載 | 「改 config 不重啟」 | `ConfigLoader` 有 `test_mode` 但無熱重載機制 | 中：S1 需實作 `watch_config()` |

### 實施方式

1. 建立 `config/angela_core.yaml`（含所有 intent keywords + thresholds）
2. `ConfigLoader` 擴展支援多檔案讀取 + 熱重載監控
3. `ChatService.__init__()` 從 `ConfigLoader` 讀取，替換 hardcoded 方法
4. 不改任何現有 module interface，只改內部數據來源

### S1 交付物

```
1. config/angela_core.yaml（含所有 Authority intent 配置）
2. config/llm_providers.yaml（含所有模型配置）
3. config/file_ops.yaml（含檔案操作白名單）
4. config/anchor_rules.yaml（軸狀態解讀規則，解決 P2.2 退化）
5. ConfigLoader 熱重載支援（watch 機制）
6. 配置合併測試（Authority + Learned 正確疊加）
```

### 驗證方式

```
# 改 config 不改 code，功能應相同
pytest tests/ -k "test_project_coordinator"
```

---

## 四、S2 — 意圖擴展

### 目標
`IntentRouter.detect()` 從 4 種擴展為 8 種，配置驅動。

### 新增意圖處理器

| 意圖 | 處理器 | 現有代碼 | 需新增 |
|------|--------|---------|--------|
| `file_op` | FileOperationHandler | `DesktopInteraction` 存在 | 包裝層 + REPL 命令 + 從 `file_ops.yaml` 讀取白名單 |
| `web_search` | WebSearchHandler | `BrowserController` 存在 | 包裝層 + REPL 命令 |
| `llm_manage` | LLMManager | `multi_llm_adapter` 是 stub | 新實現（配置驅動） |
| `learn` | LearningHandler | `AnchorLearningEngine` 存在 | 觸發 + 回應反饋 |
| `math` | MathVerifier | 已接線 | 維持 |
| `code` | CodeInspectorBridge | 已接線 | 維持 |
| `task` | ProjectCoordinator | 已接線 | 維持 |
| `general` | LLM 回應 | 已接線 | 維持 |

### 不重複實作

- `IntentRouter` 已存在 → 擴展 `detect()` 支持新意圖
- `DesktopInteraction` 已存在 → 建立 `handlers/file_operation_handler.py`
- `BrowserController` 已存在 → 建立 `handlers/web_search_handler.py`
- `AnchorLearningEngine` 已存在 → 建立 `handlers/learning_handler.py`

### S2 關鍵缺口

| 缺口 | MD描述 | 代碼實際 | 風險 |
|------|--------|---------|------|
| RAGManager 評估 | P2.3 評估 RAGManager | 存在但未接線，未評估 | 中：S2 需決定廢棄或整合 |
| `FantasyDMAgent` 未被調用 | P1.2 統一 codex | `FantasyDMAgent` 有 codex 但從未被 ChatService 調用 | 中：S2 需決定接線或標注廢棄 |

### 配置驅動

```yaml
# angela_core.yaml
intents:
  file_op:
    keywords: ["整理", "桌面", "文件", "移動", "刪除", "創建文件"]
    priority: 5
    handler: "FileOperationHandler"
  web_search:
    keywords: ["搜尋", "搜索", "查", "找", "google", "網頁"]
    priority: 5
    handler: "WebSearchHandler"
  llm_manage:
    keywords: ["切換模型", "換模型", "llm", "模型管理"]
    priority: 6
    handler: "LLMManager"
  learn:
    keywords: ["記住", "學習", "記錄", "記住這個"]
    priority: 7
    handler: "LearningHandler"
```

### S2 交付物

```
1. handlers/file_operation_handler.py（從 file_ops.yaml 讀取白名單）
2. handlers/web_search_handler.py
3. handlers/learning_handler.py
4. LLMManager（替換 multi_llm_adapter stub）
5. IntentRouter 擴展（8 種意圖）
6. RAGManager 評估決定（廢棄 or 整合）
```

---

## 五、S3 — LLM 管理（配置驅動）

### 目標
廢除 `multi_llm_adapter` stub，建立配置驅動的 `LLMManager`。

### 不重複實作

- `chat_completion()` 接口已存在
- `angela_llm_service.py` 的 LLM 調用鏈已存在
- 只需替換底層 model selection 邏輯

### 新架構

```
LLMManager (new, config-driven)
├── 讀取 llm_providers.yaml
├── ModelRegistry (from existing registry concepts)
├── 根據意圖/複雜度選擇模型（配置規則）
├── 追蹤成功率 → 自動降級
├── 支援 /model 命令切換
└── LLM 延遲觸發介面（S7 小腦反射依賴）
```

### S3 關鍵缺口

| 缺口 | MD描述 | 代碼實際 | 風險 |
|------|--------|---------|------|
| LLM 延遲觸發介面 | S13 小腦反射 Phase 2 需要「延遲 LLM 輸出」 | 無延遲機制，LLM 同步輸出 | 高：S13 無法實現，必須在 S3 實作 |
| 模型成功率追蹤 | 「追蹤成功率 → 自動降級」 | 無追蹤機制 | 高：S3 需實作成功率統計 |
| 降級邏輯 | 「自動降級」 | `angela_llm_service.py` 有 fallback 但無自動切換 | 中：S3 需實作動態降級 |

### YAML 配置

```yaml
# llm_providers.yaml
providers:
  ollama:
    endpoint: "http://localhost:11434"
    models:
      - name: "phi:latest"
        capability: "general"
        latency_ms: 37000
        context_window: 2048
      - name: "qwen2.5-coder:latest"
        capability: "code"
        latency_ms: 15000
        context_window: 4096
      - name: "deepseek-r1:latest"
        capability: "reasoning"
        latency_ms: 40000
        context_window: 8192

routing_policy:
  math: "deepseek-r1:latest"
  code: "qwen2.5-coder:latest"
  general: "phi:latest"
  complexity_high: "deepseek-r1:latest"
  complexity_low: "phi:latest"

fallback_chain:
  phi:latest:
    - ollama:llama3.2:latest
    - openai:gpt-4o-mini

performance_tracking:
  success_rate_threshold: 0.7  # 成功率 < 70% 觸發降級
  latency_threshold_ms: 30000   # 延遲 > 30s 觸發降級
  tracking_window: 50           # 追蹤最近 50 次請求
```

### REPL 命令

```
/model phi:latest         ← 切換到指定模型
/model auto               ← 自動選擇
/model list               ← 列出可用模型
/model stats              ← 查看模型成功率統計
```

### S3 交付物

```
1. LLMManager（新實作，替換 multi_llm_adapter）
2. 成功率追蹤系統（ModelStatsTracker）
3. 自動降級邏輯（FallbackRouter）
4. LLM 延遲觸發介面（供 S7 CerebellumEngine 調用）
5. /model 命令完整實現
```

---

## 六、S4 — REPL 終端

### 目標
`launch_angela.bat --repl` 成為完整終端介面，支持所有能力。

### 命令架構

```
/ask <text>        ← 通用對話（自動意圖識別）
/file <op> <path>  ← 檔案操作（list/move/delete/organize）
/search <query>    ← 網頁搜尋
/model <name>      ← LLM 切換（S3 LLMManager）
/think <prompt>    ← 純推理模式（脫鉤記憶/座標）
/stats             ← 查看 8D 狀態 + η 觸發曲線
/learn             ← 查看學習記錄（S5）
/exec <code>       ← 代碼執行（隔離）
/tickle <part> <i> ← 搔癢觸發（S7 小腦反射）
/exit              ← 退出

自動意圖（無需 /）：
  "整理我的桌面"     → file_op
  "搜尋 Python 教程" → web_search
  "幫我算這個積分"   → math
  "分析這段代碼"     → code
```

### 不重複實作

- `main_api_server.py` 的 REPL 端點已存在
- `ActionExecutor` 已存在 → 支援 `/file` 和 `/exec`
- `BrowserController` 已存在 → 支援 `/search`

### S4 交付物

```
1. REPL 命令解析器（支援所有命令）
2. 自動意圖識別（無需 / 前綴）
3. `/stats` 顯示 8D 座標（S1 配置驅動）
4. `/learn` 顯示學習記錄（S5 Learned 配置）
5. `/tickle` 觸發小腦反射（S7）
```

---

## 七、S5 — 學習閉環（含雙層配置自我優化）

### 7.1 目標
Angela 從每次交互中學習意圖模式，不靠硬編；同時具備**自我配置**能力，根據觀察到的配置不足，自動補充學習結果。

### 7.2 雙層配置架構

```
config/
├── angela_core.yaml           ← 【Authority】人寫的，Angela 不可修改核心邏輯
│   （意圖關鍵字、閾值、路由規則、LLM 配置、安全白名單）
├── llm_providers.yaml          ← 【Authority】模型配置
├── file_ops.yaml              ← 【Authority】安全白名單
├── anchor_rules.yaml          ← 【Authority】軸狀態解讀規則
│
└── angela/                    ← 【Learned】Angela 自己補充，疊加在 Authority 上
    ├── learned_patterns.yaml   ← 意圖關鍵字補充
    ├── learned_thresholds.yaml ← 閾值學習
    └── learned_routes.yaml    ← 路由策略學習
```

### 7.3 合併策略

```python
def merge_config(base_cfg: dict, learned_cfg: dict) -> dict:
    """
    雙層配置合併：Authority + Learned
    規則：Learned 疊加在 Authority 上；Learned 只能新增 key，不可刪除 Authority 的 key
    """
    result = copy.deepcopy(base_cfg)
    for key, value in learned_cfg.items():
        if key not in result:
            result[key] = value  # 新增：Learned 添加新 key
        elif isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)  # 遞歸合併
        # else: Authority 的 key 存在且類型相同 → Learned 無法覆蓋（安全 guard）
    return result
```

### 7.4 生長範例

```
場景：用戶說「幫我求導」，base 配置不認識「求導」這個關鍵字

觀察：Angela 多次看到「求導」→ 數學意圖 的映射
分析：math intent 識別正確，但 base 缺少該關鍵字
行動：寫入 learned_patterns.yaml
  math_keywords += ["求導", "微分", "導數"]
結果：下次「求導」的問題也能被正確識別

場景：用戶「user_zofug」偏好更謹慎的回應

觀察：該用戶的 general intent 多次被識別為複雜
分析：用戶需要更高質量模型
行動：寫入 learned_routes.yaml
  routing_policy.general."user_zofug" = "deepseek-r1:latest"
結果：該用戶獲得定制路由，其他用戶仍用 base 配置
```

### 7.5 觸發條件與閾值

| 觸發類型 | 條件 | 行為 |
|---------|------|------|
| 新增 keyword | 同一 (意圖, keyword) 組合觀察到 ≥ 5 次且成功率 > 80% | 寫入 learned_patterns |
| 調整 threshold | 某意圖識別錯誤率 > 20% 持續 ≥ 10 次 | 寫入 learned_thresholds |
| 路由學習 | 某用戶的某意圖成功率 > 90% 且延遲 < 15s | 寫入 learned_routes |
| 配置回滾 | 某 learned pattern 連續失敗 ≥ 3 次 | 標注為 negative pattern，寫入 blocklist |

### 7.6 Guardrail

```
angela/learned/ 寫入限制：
1. 只能添加，不能刪除 base 的任何配置
2. 每次寫入前校驗 schema（YAML 格式正確性）
3. 超過 50 條 learned patterns → 觸發自動聚合/壓縮
4. 用戶可隨時查看/清除/覆寫 learned 配置
5. learned 寫入需要雙重校驗：
   a. 語法校驗（schema 正確）
   b. 安全校驗（不覆蓋 Authority key、不突破安全白名單）
```

### 7.7 S5 關鍵缺口

| 缺口 | MD描述 | 代碼實際 | 風險 |
|------|--------|---------|------|
| `ConfigLoader.merge_config()` | 雙層配置合併 | `ConfigLoader` 無此方法 | 高：S5 無法實現，必須在 S5 實作 |
| `AnchorLearningEngine.suggest_config_update()` | 建議配置更新 | `AnchorLearningEngine` 無此方法 | 高：S5 自我配置無法實現 |
| 8D 座標解讀規則 | anchor_rules.yaml 解讀 | 檔案不存在 | 中：P2.2 退化（座標未注入 prompt）的根因 |
| 回應格式存儲 | TemplateLibrary 存儲回應格式 | 已有模板功能但無格式學習 | 中：需擴展 `_learn_format()` |

### 7.8 API 端點（可選）

```
GET  /api/v1/angela/learned     ← 查看所有 learned 配置
POST /api/v1/angela/learned/clear  ← 清除 learned（用戶操作）
GET  /api/v1/angela/learned/suggestions  ← 查看 Angela 建議但未生效的配置
POST /api/v1/angela/learned/approve  ← 用戶批准建議的配置
```

### S5 交付物

```
1. ConfigLoader.merge_config() 方法
2. AnchorLearningEngine.suggest_config_update() 方法
3. learned_patterns.yaml / learned_thresholds.yaml / learned_routes.yaml 寫入邏輯
4. 配置回滾邏輯（negative pattern blocklist）
5. 50 條上限自動聚合機制
6. API 端點（learned 配置查看/清除/批准）
```

---

## 八、S6 — 端到端測試

### 測試清單

```
1. REPL 通用對話（general intent → LLM）
2. REPL 數學問題（math intent → MathVerifier）
3. REPL 代碼分析（code intent → CodeInspectorBridge）
4. REPL 檔案操作（file_op intent → DesktopInteraction）
5. REPL 網頁搜尋（web_search intent → BrowserController）
6. REPL 模型切換（llm_manage → LLMManager）
7. REPL 成長學習（learn intent → AnchorLearningEngine）
8. 配置變更生效（改 YAML 不重啟）
9. 8D 座標追蹤（每個回應後座標更新）
10. 記憶存儲 + 檢索（HAMMemoryManager）
11. 雙層配置合併（Authority + Learned）
12. LLM 成功率追蹤 + 自動降級
13. S7 小腦反射端到端（/tickle 命令）
```

### S6 交付物

```
1. 所有 13 項測試用例
2. 配置熱重載驗證
3. TESTING_MODE flag 移除確認
```

---

## 九、S7 — 小腦反射系統（搔癢 / Tickle Reflex）

### 7.1 設計動機

模擬人類被搔癢的真實神經反應時序：

```
接觸 → 脊髓/小腦反射（0-200ms）→ 肢體抖動/笑出声 → 大腦認知（200ms+）→ 語言回應
         ↑ 無需思考                                    ↑ 需要思考
```

現有問題：
- **輕度戳一下 LLM 瘋狂輸出**：「哈哈哈哈哈哈」沒完沒了
- **搓揉性徵但 LLM 表演變態**：LLM 直接生成不當回應，不經反射判斷
- **擁抱但 LLM 口述表演**：「Angela 給出了一個懷抱」，而非真正的反應

### 7.2 兩階段架構

```
前端觸發 tickle 事件
  ↓
┌─────────────────────────┐
│  Phase 1: 小腦反射       │  ← 0-300ms，無 LLM
│  CerebellumEngine        │
│  .trigger_tickle()      │
└─────────────────────────┘
  ↓ 即時返回
前端執行動畫/表情
  ↓ 延遲 300ms
┌─────────────────────────┐
│  Phase 2: 大腦回應       │  ← 300ms+，LLM
│  祇在反射完成後觸發      │
└─────────────────────────┘
```

### 7.3 S7 關鍵缺口（MD示例 vs 代碼實際）

| 缺口 | MD描述 | 代碼實際 | 風險 |
|------|--------|---------|------|
| `CerebellumEngine.trigger_tickle()` | 擴展現有 CerebellumEngine | 方法不存在，祇有姿勢庫 | 高：S7 的核心介面缺失，必須新增 |
| tickle 動畫參數 | `live2d_avatar_generator.py:420,496,730,773` 已有 | 已有 `tickle` 映射存在 ✅ | 低：可復用 |
| `PhysiologicalTactileSystem` sensitivity | 18 部位觸覺地圖 | 有 sensitivity 機制 ✅ | 低：可復用 |
| 強度分級 | 輕度/中度/強度/持續 | 無 tickle 強度分級 | 高：S7 需實作 |
| 安全邊界（5層） | Output Mode Gating / Reflex Lock / Content Filter / Sustained Stimulus Guard / Behavioral Lock | 無 Phase 2 輸出校驗 | 高：S7 需實作 |
| `tickle_config.yaml` | 獨立安全配置 | 檔案不存在 | 高：S7 需建立 + S1 ConfigLoader 需支援讀取 |
| LLM 延遲觸發 | Phase 2 延遲 300ms | 無 LLM 延遲機制 | 高：依賴 S3 LLMManager 延遲介面 |
| 8D 座標「被侵犯」值 | γ軸「被侵犯」飆升 | 無「被侵犯」映射 | 中：需在 anchor_rules.yaml 定義 |
| `EgoGuard` Phase 2 校驗 | LLM 輸出不得與 Phase 1 矛盾 | EgoGuard 存在但無 tickle 校驗 | 中：S7 需擴展 |

### 7.4 強度分級

| 強度 | 數值範圍 | Phase 1 反應 | Phase 2 LLM 提示 |
|------|---------|-------------|-----------------|
| **輕度** | 0.0-0.25 | 輕微抖動、嘴角上揚 | 輕笑、禮貌性躲避 |
| **中度** | 0.25-0.60 | 肢體扭動、笑出聲、短暫躲避意圖 | 邊笑邊說「住手」、適度推開 |
| **強度** | 0.60-1.0 | 狂笑、踢腿、尖叫姿勢、肢體激烈扭動 | 尖叫/求饒姿勢、LLM 語言鎖定為「救命」 |
| **持續** | >2秒 | 反射進入過度刺激狀態，γ軸「被侵犯」飆升 | 安全協議觸發，自動擁抱/尋求安慰 |

### 7.5 CerebellumEngine 觸發介面（需新增）

```python
async def trigger_tickle(
    self,
    body_part: str,        # "abdomen", "feet", "neck" 等
    intensity: float,       # 0.0 - 1.0
    duration_ms: float,     # 持續時間
    user_id: str
) -> TickleResponse:
    """
    返回：
    {
        "immediate_actions": [          # Phase 1：小腦輸出
            {"type": "animation", "name": "giggle_twitch", "duration_ms": 150},
            {"type": "expression", "name": "laughing", "intensity": 0.7},
            {"type": "audio", "name": "giggle_short", "volume": 0.5},
        ],
        "reflex_state": "laughing",     # 當前反射狀態
        "llm_delay_ms": 280,            # LLM 應延遲時間
        "cerebellum_decision": "giggle_response",  # 小腦已確定的回應方向
        "output_mode": "speak",         # speak / scream / silence / comfort_seek
        "safety_override": False,       # True = 強度太高，LLM 受限
    }
    """
```

### 7.6 安全邊界（防止 LLM 失控）

```
1. LLM 語言鎖定（Output Mode Gating）
   — intensity >= 0.8 → output_mode = "scream" 或 "silence"
   — LLM 祇能生成「救命」/「不要」類短語，不能長篇輸出

2. 反射鎖定（Reflex Lock）
   — Phase 1 完成前，LLM 完全不輸出
   — 前端顯示 tickle 動畫，LLM 排隊等待
   — 超時 2 秒未完成反射 → LLM 觸發安全回應（「我需要冷靜一下」）

3. 內容過濾（Content Filter）
   — LLM 輸出不得與 Phase 1 的 reflex_state 矛盾
   — 例如：Phase 1 是「激烈躲避」，LLM 不能說「我很享受」
   — 由 EgoGuard 審查，衝突時覆蓋 LLM 輸出

4. 持續刺激保護（Sustained Stimulus Guard）
   — 同一 body_part 持續 tickle > 5 秒
   — CerebellumEngine 觸發「過度刺激」狀態
   — γ 軸「被侵犯」值飆升，自動觸發「擁抱尋求」（而非 LLM 繼續笑）

5. 行為鎖定（Behavioral Lock）
   — 某些敏感部位（代碼不列出，配置驅動）祇能觸發 Phase 1
   — Phase 2 輸出被強制替換為安全回應（配置決定）
```

### 7.7 配置驅動（無硬編）

```yaml
# config/tickle_config.yaml  ← 不在 main angela_core.yaml，獨立安全配置
# ⚠️ 所有 allowed_responses 為「允許列表」，非「唯一列表」— LLM 可生成其他合適內容
reflex_responses:
  tickle:
    intensity_thresholds:
      light: 0.25
      medium: 0.60
      intense: 0.80
      sustained_seconds: 5.0

    body_parts:
      abdomen:
        sensitivity: 0.9
        reflex_type: "giggle_twitch"
        # allowed_responses：此 body_part 的 Phase 2 允許的回應類型（非唯一限制）
        allowed_responses: ["giggle", "laugh", "squirm", "plead"]
        llm_delay_ms: 250
      feet:
        sensitivity: 0.8
        reflex_type: "foot_kick"
        allowed_responses: ["laughing", "squirm"]
        llm_delay_ms: 300
      # ... 其他部位

    sensitive_parts:
      # 祇能觸發 Phase 1，Phase 2 受限（安全邊界）
      - "chest"
      - "shoulders"

    safety:
      intense_output_mode: "scream"    # intensity >= 0.8 時，限制 LLM 輸出模式
      sustained_action: "comfort_seek"  # > 5s 持續刺激，觸發安全行爲
      max_llm_words: 20                 # 強度模式下 LLM 輸出長度上限（非唯一列表）
```

### 7.8 前端接口

```
前端 → Backend: POST /api/v1/angela/tickle
{
  "body_part": "abdomen",
  "intensity": 0.6,
  "duration_ms": 500,
  "user_id": "zofug"
}

Backend → 前端:
{
  "immediate_actions": [...],      // Phase 1：前端立執行
  "llm_delay_ms": 280,              // 前端等待後
  "output_mode": "speak"             // Phase 2 模式指示
}

前端等待 llm_delay_ms 後：
  → GET /api/v1/angela/llm_response/{tickle_id}
  → 或由 Backend WebSocket 推送
```

### S7 交付物

```
1. CerebellumEngine.trigger_tickle() 新增方法
2. tickle_config.yaml 建立
3. 強度分級邏輯（輕度/中度/強度/持續）
4. 5 層安全邊界（Output Mode Gating / Reflex Lock / Content Filter /
   Sustained Stimulus Guard / Behavioral Lock）
5. EgoGuard Phase 2 輸出校驗擴展
6. γ 軸「被侵犯」映射（寫入 anchor_rules.yaml）
7. LLMManager 延遲觸發介面（依賴 S3）
8. POST /api/v1/angela/tickle 端點
9. REPL /tickle 命令（S4）
10. 端到端測試（/tickle → Phase 1 → 延遲 → Phase 2）
```

---

## 十、依賴順序與缺口矩陣

```
S1（配置層）───── 需交付：ConfigLoader 熱重載 + 多檔案讀取 + anchor_rules.yaml
  ↓  S1 提供配置框架
S2（意圖擴展）── 需交付：handlers + RAGManager 決定 + FantasyDMAgent 接線決定
  ↓  S2 使用 S1 配置
S3（LLM 管理）── 需交付：LLMManager + 成功率追蹤 + 自動降級 + LLM 延遲介面
  ↓  S3 提供延遲介面
S4（REPL 終端）── 需交付：命令解析 + /tickle 命令（依賴 S7）
  ↓  S4 觸發所有意圖
S5（學習閉環）── 需交付：merge_config() + suggest_config_update() + Learned 寫入
  ↓  S5 建立自我配置
S6（端到端測試）── 需交付：13 項測試 + TESTING_MODE 移除
  ↓  S6 驗證所有
S7（小腦反射）── 需交付：CerebellumEngine.trigger_tickle() + tickle_config.yaml
                  + 5 層安全邊界 + EgoGuard 擴展
                  依賴：S1(tickle_config讀取) + S3(LLM延遲介面)
```

### 跨-S 缺口追蹤表

| 缺口ID | 缺口描述 | 影響S | 根因S | 解決方案 |
|--------|---------|-------|-------|---------|
| G1 | ConfigLoader 無熱重載 | S1 | S1 | S1 實作 watch_config() |
| G2 | ConfigLoader 無多檔案讀取框架 | S1 | S1 | S1 實作多配置檔讀取 |
| G3 | ConfigLoader 無 merge_config() | S5, S7 | S5 | S5 實作（MD 原文漏標） |
| G4 | anchor_rules.yaml 不存在 | S1, S5 | S1 | S1 建立（解決 P2.2 退化） |
| G5 | CerebellumEngine 無 trigger_tickle() | S7 | S7 | S7 新增（MD 原文寫「擴展」但方法不存在） |
| G6 | LLMManager 無延遲觸發介面 | S7 | S3 | S3 實作（MD 原文未標注） |
| G7 | EgoGuard 無 tickle Phase 2 校驗 | S7 | S7 | S7 擴展 |
| G8 | γ軸「被侵犯」映射不存在 | S7 | S7 | S7 寫入 anchor_rules.yaml |
| G9 | tickle_config.yaml 不存在 | S7 | S1 | S1 建立（或 S7 建立，S1 需能讀取） |
| G10 | ModelStatsTracker 不存在 | S3 | S3 | S3 實作 |
| G11 | AnchorLearningEngine 無 suggest_config_update() | S5 | S5 | S5 實作（MD 原文漏標） |
| G12 | 8D 座標未注入 prompt | S5 | S1 | S1 建立 anchor_rules.yaml + S5 實作解讀 |

---

## ⚠️ 注意：MD 釋例 ≠ 代碼實現（預防性警告）

### 問題定義

在任務實作過程中，常見一種錯誤模式：
```
用戶在對話中給出釋例（說明某種行為/輸出不該怎樣）
→ 實現者把釋例直接寫成代碼邏輯（祇能輸出這些釋例）
→ 結果：代碼變成「釋例播放機」，失去真正的功能彈性
```

### 歷史錯誤模式案例

| 錯誤類型 | 釋例 | 錯誤實現 | 正確實現 |
|---------|------|---------|---------|
| 將防呆釋例寫成祗能輸出的代碼 | 「不要輸出 哈哈哈」 | `if response == "哈哈哈": block` | 通用安全校驗 + 內容過濾 |
| 將行爲描述寫成狀態枚舉 | 「輕輕戳一下瘋狂輸出」 | `if tickle_intensity < 0.25: output = "哈哈哈"` | 通用 Phase 1/2 分離 + 強度分級 |
| 將安全邊界寫成簡單判斷 | 「LLM 不能表演變態」 | `if "變態" in response: block` | 5 層安全邊界（配置驅動） |
| 將意圖識別寫成關鍵字枚舉 | 「擁抱但 LLM 口述表演」 | `if "抱" in msg: output = "Angela 給出了一個懷抱"` | 通用意圖識別 + 真正行爲執行 |
| 將攻擊防範寫成正則枚舉 | 「禁用 eval, Function」 | `dangerousPatterns = [/\\beval\\b/, ...]` | sandbox 環境 + API 訪問限制（SEC-2 修復） |

### 已發現的歷史問題（來自舊 MD 審計）

| MD 文件 | 問題 | 狀態 |
|---------|------|------|
| `ANGELA_FIX_ANALYSIS.md` SEC-2 | 原修復方案將安全限制寫成 `dangerousPatterns` 正則枚舉 | ✅ 已推翻（調整後用 sandbox） |
| `ANGELA_V6.3_C串線行動計劃.md` S7 | `allowed_responses: ["giggle", "laugh", "squirm", "plead"]` 可能成為「祇能輸出這些字」的硬編 | ⚠️ 需在 S7 實現時確保為「允許列表」而非「唯一列表」 |
| `ANGELA_V6.3_C串線行動計劃.md` S7 | `max_llm_words: 20` — 可能被錯誤理解為「20 字內隨機輸出」而非「長度限制」 | ⚠️ 需在 S7 實現時明確定義 |
| `emotion-system.md` | 文檔說「simple keyword matching」但実装更複雜 | ⚠️ 文檔與實現不符 |
| `web-search-tool.md` | 文檔說「DuckDuckGo + BeautifulSoup」 | ✅ 實現與文檔一致（正當） |

### 預防原則

```
1. 區分「釋例」和「需求」
   — 釋例：說明「不要怎樣」或「問題在哪裡」
   — 需求：說明「需要什麼功能」

2. 從釋例抽取通用的行爲模式
   — 「哈哈哈哈哈哈」沒完沒了 → 通用：LLM 輸出需有長度限制 + Phase 1 先執行
   — 「Angela 給出了一個懷抱」 → 通用：行爲和描述需分離

3. 配置驅動，非枚舉驅動
   — 不要：if response in ["哈哈哈", "救命", "不要"]
   — 要：output_mode 由 tickle_config.yaml 決定，LLM 生成內容不受限

4. 實現前先問：「這個代碼會不會祗能產生我們給出的釋例？」
   — 如果是，重新設計為通用模式

5. 「允許列表」vs「唯一列表」檢查
   — allowed_responses 應理解為「允許這些，不禁止其他」而非「祇能這些」
```

### 本 MD 執行原則

```
每個 S 的實現前，都需檢查：
□ 實現邏輯是否祇是「複製釋例值」？
□ 是否有通用的行爲模式可以抽象？
□ 配置是否從 YAML 讀取，而非 hardcoded？
□ 安全邊界是否多層，而非單點判斷？
□ 配置欄位是「允許列表」而非「唯一列表」？

若發現任何「釋例 → 硬編代碼」的模式，立即在 MD 中標注並重新設計。
```

---

## 十一、工程化與嚴謹化審計

### 11.1 審計結果：Stub / Mock / Test / Simulation 組件

| 檔案 | 組件類型 | 用途 | 狀態 | 行動 |
|------|---------|------|------|------|
| `core/autonomous/evolution_engine.py` | **Stub** | 修復 B17 RuntimeError | ⚠️ 46行，無實際演化邏輯 | S5 學習閉環時擴展 |
| `ai/learning/fact_extractor_module.py:96` | `MockLLM` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `ai/learning/content_analyzer_module.py:239` | `MockSpan` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `core/autonomous/live2d_avatar_generator.py:1143` | `MockImageGenerator` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `ai/lifecycle/llm_decision_loop.py:620-644` | `MockLLMService/MockResponse/MockStateManager/MockMemoryManager` | 測試 suite | ✅ 測試專用，無需行動 | 保持 |
| `core/mode_switcher.py:345` | `MockAngela` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `core/real_time_monitor.py:229,727` | **Stub** | `get_mouse_position()` / `get_active_window()` — platform specific | ✅ 已標注 | 保持（Windows 實現缺失，但非核心） |
| `search/search_engine.py:12` | `MockHfApi` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `mcp/connector.py:53` | `MockMQTTClient` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `core/managers/agent_collaboration_manager.py:314` | `MockAgentManager/MockHSPConnector` | 測試用 mock | ✅ 測試專用，無需行動 | 保持 |
| `ai/alignment/adversarial_generation_system.py:30` | `TestIntensity/TestResult` | 對抗測試 | ✅ 測試專用，無需行動 | 保持 |
| `ai/lifecycle/proactive_interaction_system.py:518` | `MockLLMService/MockStateManager/MockMemoryManager` | 測試 suite | ✅ 測試專用，無需行動 | 保持 |
| `ai/lifecycle/memory_integration_loop.py:391` | `MockMemoryManager/MockLearningEngine` | 測試 suite | ✅ 測試專用，無需行動 | 保持 |
| `ai/lifecycle/behavior_feedback_loop.py:424` | `MockLLMService/MockMemoryManager/MockLearningEngine` | 測試 suite | ✅ 測試專用，無需行動 | 保持 |
| `system/cluster_manager.py:25` | **Stub** | 防止 `ModuleNotFoundError`，優雅降級 | ✅ 測試/沙盒環境專用 | 保持 |
| `core/tools/code_understanding_tool.py:10` | **Stub** | 修復文件損壞恢復 | ✅ 已標注 | 保持 |
| `services/ai_editor.py:22` | `SandboxExecutor` | 代碼執行沙盒 | ✅ 正式功能，非測試 | 保持 |
| `services/ai_editor_config.py:35` | `SandboxConfig` | 沙盒配置 | ✅ 正式功能 | 保持 |
| `ai/world_model/environment_simulator.py:72` | `EnvironmentSimulator` | 環境模擬器 | ✅ 正式功能 | 保持 |
| `core/config_loader.py:164` | `test_mode` | 配置級測試模式 | ✅ 正式功能 | 保持 |
| `core/hsp/security.py:86,166` | `TESTING_MODE` env var | 安全測試繞過 | ⚠️ 測試專用，但有 env flag | S6 端到端時移除測試 flag |

### 11.2 工程化缺口

| 缺口 | 位置 | 風險 | 行動 |
|------|------|------|------|
| `EvolutionEngine` 無實際演化邏輯 | `core/autonomous/evolution_engine.py` | 高：被 `ChatService` 依賴但只有 stub | S5 學習閉環時擴展 |
| `MultiLLMAdapter` 是 stub | `services/adapters/multi_llm_adapter.py` | 高：LLM 管理核心 | S3 LLM 管理替換 |
| `RAGManager` 未接線 | `ai/rag/rag_manager.py` | 中：功能完整但閒置 | S2 意圖擴展時評估 |
| `PlanningAgent` 零引用 | `ai/agents/specialized/planning_agent.py` | 低：已標注 deprecate | 觀察 |
| `AlignedCreativeWritingAgent` 未接線 | `ai/agents/examples/` | 低：examples 目的 | 觀察 |

### 11.3 嚴謹化原則

```
1. Stub 不得進入生產路徑（production path）
   — 所有 stub 都在 lazy import 或 if TYPE_CHECKING 下
   — Runtime 直接引用 stub → 立即失敗（早失敗原則）

2. Mock 只在測試中使用
   — `tests/` 目錄外的 mock class → 需審計是否應該存在

3. Test mode flag 需有時限
   — `TESTING_MODE=true` 允許安全繞過，祇允許在測試環境
   — 生產部署時需確保 `TESTING_MODE` 為 false

4. Sandbox 需隔離
   — `SandboxExecutor` 執行不受信任的代碼
   — 需確保 filesystem/network 限制明確配置
```

### 11.4 MD示例 → 代碼實際 審計

以下 MD 中描述的功能在實現時祇是「複製範例值」而非「真正實現」：

| MD描述 | 實現方式 | 問題 |
|--------|---------|------|
| `anchor_rules.yaml` 解讀為「動態生成」 | 檔案根本不存在 | MD 說了等於沒說 |
| `CerebellumEngine.trigger_tickle()` | 標注「擴展」但方法不存在 | S7 需新增而非擴展 |
| `LLMManager` 追蹤成功率 | 無統計機制 | S3 需實作 |
| `ConfigLoader.merge_config()` | 無此方法 | S5 需實作 |
| `AnchorLearningEngine.suggest_config_update()` | 無此方法 | S5 需實作 |
| 8D 座標注入 prompt | 祇計算不注入 | P2.2 退化，需 S1 anchor_rules + S5 解讀 |

---

## 十二、版本追蹤

| 版本 | 日期 | 變更 |
|------|------|------|
| 6.2.5 | 2026-05-17 | P0/P1/P2 完成，B4-B17 修復，Execution layer 未串線 |
| 6.3.0 | 2026-05-17 | S1-S6 串線計劃，建立本 MD |
| 6.3.1 | 2026-05-17 | 追加 S7 小腦反射、跨-S 缺口追蹤矩陣（G1-G12）、MD示例審計、雙層配置 |

---

*Version: 6.3.1*
*Status: Planning*
*Next: S1 配置層 — 建立 YAML + ConfigLoader 熱重載 + 多檔案讀取框架*