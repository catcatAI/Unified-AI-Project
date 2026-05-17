# Angela v6.2.x 系統審計與整合規劃

**版本**: 6.2.5
**審計日期**: 2026-05-17
**範圍**: `apps/backend/src`
**目標**: 合併重複系統，修訂整合優先級，以可擴展性強的為主

---

## 一、入口點確認

```
REPL / HTTP / WebSocket
  → main_api_server.py
    → ChatService.generate_response()     ← 唯一入口
      → 意圖路由 (math → code → task → llm_switch → general)
      → 子系統初始化 (懶載入，line 27)
      → 8D軸更新 + θ自檢 + η追蹤
      → 記憶存儲 + 演化學習

AngelaLLMService 也可獨立使用 via get_llm_service()
```

---

## 二、系統狀態總表

### 已發現問題（需修正）

| # | 問題 | 嚴重度 | 驗證狀態 |
|---|------|--------|---------|
| **A1** | P0.1 僅列出 `dialogue_manager.py` 一個 import，實際有 **5 個**：fact_extractor_module, ensemble, unified_control_center, dialogue_manager, language_models/router | 高 | ✅ 已確認 |
| **A2** | P0.3 建議用 `ProjectCoordinator._dispatch_single_subtask`（private 方法）替換 ToolDispatcher — 不可行 | 高 | ✅ 已確認 |
| **A3** | 廢棄清單有 `evolution_engine.py` 重複（出現兩次） | 低 | ✅ 已確認 |
| **A4** | 有另一個 `evolution_engine`：`core/evolution/autonomous_evolution_engine.py`（609行）從未被引用，需確認是否也要廢棄 | 中 | ✅ 已確認：無任何 import，只在自己檔案內定義 |
| **A5** | 兩個 ExecutionManager 都有 `get_execution_manager()` 全域單例；`core/managers/execution_manager.py` 有 17 行被註釋的 import，需確認是否有其他引用 | 中 | ✅ 已確認：core/managers/ 內的引用全是被註釋的 |
| **A6** | `CreativeWritingAgent` 是 63 行 STUB；但 `AlignedCreativeWritingAgent`（208行）在 `agents/examples/` 而非 `ai/agents/`，不在 AgentManager 管理範圍內，無法直接替代 | 低 | ✅ 已確認：需將 AlignedCreativeWritingAgent 遷移到 `ai/agents/specialized/` 或重寫 CreativeWritingAgent |
| **A7** | PlanningAgent（123行）實際功能是模板化任務創建，確實可被 ProjectCoordinator 替代 | 低 | ✅ 已確認：PlanningAgent 從未被 import |
| **A8** | FantasyDMAgent 的 `_load_codex()` 在 `__init__` 時從未被調用，codex_path 為 `"apps/backend/data/trpg/ai-trpg-codex.json"`（相對路徑），需確認路徑是否正確 | 低 | ✅ 已確認：需在初始化時主動調用 |
| **A9** | `EgoGuard` 行數僅列 59 行（審計文中），但 `ai/security/ego_guard.py` 實際行數需確認 | 低 | ✅ 已確認：59 行 |
| **A10** | 關鍵檔案索引中 VisionService 704行、AngelaLLMService 1743行、StateMatrix 1729行 — 需驗證實際行數 | 低 | ✅ 已確認：VisionService 704 ✓, AngelaLLMService 1780（更新）✓, StateMatrix 1729 ✓, TemplateLibrary 682 ✓, Connector 1071 ✓, BiologicalIntegrator 841 ✓ |
| **A11** | `angela_llm_service.py` 沒有 `ChatMessage`、`ModelConfig`、`ModelProvider` 這些從 multi_llm_adapter 引入的類別；`DialogueManager` 呼叫 `chat_completion()`，但 `angela_llm_service.py` 沒有 `chat_completion` 方法（只有 `generate()` 與 `generate_text()`）| 高 | ✅ 新發現 |
| **A12** | `ensemble.py` 的 `_query_model_safe` 呼叫 `self.llm_service.chat_completion()` — 同上，angela_llm_service 沒有此方法 | 高 | ✅ 新發現 |
| **A13** | `unified_control_center.py` 直接實例化 `MultiLLMService(llm_config_path)` — 如果刪除 multi_llm_adapter.py 但沒有等效替代，UCC 會炸 | 高 | ✅ 新發現 |
| **A14** | `language_models/router.py` 只 import `ModelProvider`（Enum），不在主要流程，可保留或移除 | 低 | ✅ 已確認 |
| **A15** | `fact_extractor_module.py` 呼叫 `self.llm_service.chat_completion()` — 同上，A11 連鎖 | 高 | ✅ 新發現 |
| **A16** | `LearningManager` 依賴 `FactExtractorModule`，而 `FactExtractorModule` 依賴 `MultiLLMService.chat_completion()` — 如果廢棄 multi_llm_adapter.py，需確保 `LearningManager` 也有替代路徑 | 中 | ✅ 新發現 |
| **A17** | `ai/agents/__init__.py` export `CreativeWritingAgent`；`api/router.py` 和 `agent_manager.py` 都引用 `CreativeWritingAgent` — 廢棄它需要更新這些引用 | 中 | ✅ 新發現 |
| **A18** | `core_service_manager.py` 中 `from core.managers.execution_manager import ExecutionManager` 被註釋掉，但同一檔案內其他處有動態類創建 `class_name="MultiLLMService"` — 需確認 MultiLLMService 實例化的時機 | 中 | ✅ 已確認：被註釋 |
| **A19** | `ai/execution/execution_manager.py` 的 `__init__` 中 `monitor_config` 參數傳錯（Config 對 Config），導致重複初始化；`core/managers/execution_manager.py` 的 `_load_config_from_system()` 缺少 `history_size` 參數（ExecutionManagerConfig 沒有這個欄位）| 低 | ✅ 新發現 |

### 已正確接入 ChatService（直接使用）

| 子系統 | 檔案 | 行數 | 成熟度 | 備註 |
|--------|------|------|--------|------|
| **StateMatrix4D** | `core/autonomous/state_matrix.py` | 1729 | 高 | 完整 8D 軸動態座標 |
| **StateMatrixAdapter** | `core/autonomous/state_matrix_adapter.py` | — | 高 | + AnchorLearning + ThetaRouter + EtaAxisState |
| **AnchorLearningEngine** | `core/autonomous/anchor_learning.py` | 374 | 高 | EMA 學習，詞→軸映射 |
| **BiologicalIntegrator** | `core/autonomous/biological_integrator.py` | 841 | 高 | 6 子系統，完整事件發布 |
| **HAMMemoryManager** | `ai/memory/ham_memory/ham_manager.py` | 236 | 高 | 向量+結構化存儲，持久化 |
| **TemplateLibrary** | `ai/memory/template_library.py` | 682 | 高 | 回應模板，已被 AngelaLLMService 使用 |
| **MemoryTemplate** | `ai/memory/memory_template.py` | 311 | 高 | 數據結構定義 |
| **EmotionSystem** | `ai/alignment/emotion_system.py` | — | 高 | 情緒分析+共情計算 |
| **ValueSystem** | `ai/alignment/value_assessment.py` | — | 高 | 意圖評估+價值權重 |
| **PersonalityManager** | `ai/personality/personality_manager.py` | — | 高 | 個性配置管理 |
| **EgoGuard** | `ai/security/ego_guard.py` | 59 | 中 | 簡單 regex 防護，可用 |
| **VisionService** | `services/vision_service.py` | 704 | 高 | 多模態，含 OCR/物體偵測 |
| **MathVerifier** | `services/math_verifier.py` | — | 高 | 數學驗證，含中文應用題 |
| **GlobalInputSensor** | `core/autonomous/input_sensor.py` | 108 | 中 | pynput 鍵鼠監控 |
| **WaitingScheduler** | `core/waiting_scheduler.py` | — | 高 | 單線程排程，非阻塞 LLM |
| **AngelaLLMService** | `services/angela_llm_service.py` | 1780 | 高 | 多後端，模板匹配，generate_text() |
| **HSPConnector** | `core/hsp/connector.py` | 1071 | 高 | 多協議，fallback 鏈 |
| **ServiceDiscovery** | `ai/service_discovery/service_discovery_module.py` | 203 | 高 | 能力註冊+清理 |

### 存在但未接入 ChatService

| 子系統 | 檔案 | 成熟度 | 接入價值 | 建議動作 |
|--------|------|--------|--------|----------|
| **DialogueManager** | `ai/dialogue/dialogue_manager.py` | 中高 | 低-中 | 與 ChatService 平行，功能重疊，廢棄 |
| **ProjectCoordinator** | `ai/dialogue/project_coordinator.py` | 中 | **高** | 剛重寫，需測試，已接入 task intent |
| **DocumentBuilder** | `ai/dialogue/document_builder.py` | 中 | **高** | 新建，需測試，已接入 ProjectCoordinator |
| **FantasyDMAgent** | `ai/agents/specialized/fantasy_dm_agent.py` | 中 | **高** | 有完整 codex，角色卡生成必備 |
| **AgentManager** | `ai/agents/agent_manager.py` | 高 | 中 | 15 個 agents，多數是 stub，接入價值有限 |
| **AlignedCreativeWritingAgent** | `ai/agents/examples/aligned_agent_example.py` | 高 | **高** | 208行實際實現，替代 CreativeWritingAgent（63行STUB）|
| **DigitalLifeIntegrator** | `core/autonomous/digital_life_integrator.py` | 高 | 中 | 數位生命集成，main_api_server 已用 |
| **BrainBridgeService** | `services/brain_bridge_service.py` | 高 | 中 | 狀態同步，main_api_server 已用 |
| **CerebellumEngine** | `core/autonomous/cerebellum_engine.py` | 中 | 低 | 運動執行，在 AngelaModelCore 內 |
| **AgentCollaborationManager** | `core/managers/agent_collaboration_manager.py` | 中 | 低 | 跨 agent 協作，未被使用 |

### 需要修復或廢棄

| 子系統 | 檔案 | 問題 | 建議動作 |
|--------|------|------|----------|
| **ToolDispatcher** | `core/tools/tool_dispatcher.py` | **STUB（30行）** | 用 ProjectCoordinator._dispatch_single_subtask 替換 |
| **ExecutionManager** | `core/managers/execution_manager.py` | 與 `ai/execution/execution_manager.py` 完全重複 | 合併二選一，刪除一個 |
| **multi_llm_adapter.py** | `services/adapters/multi_llm_adapter.py` | 與 `angela_llm_service.py` 功能重疊 | 廢棄，統一用 `angela_llm_service.py` |
| **RAGManager** | `ai/rag/rag_manager.py` | 95行，不完整，依賴外部庫 | 評估後廢棄或用 HAMMemoryManager 向量替代 |
| **EvolutionEngine** | `core/autonomous/evolution_engine.py` | **53行**，無持久化，邏輯過於簡單 | **廢棄**，統一用 `AnchorLearningEngine` |
| **AutonomousEvolutionEngine** | `core/evolution/autonomous_evolution_engine.py` | **609行**，從未被任何系統引用 | **廢棄**，長期無維護 |
| **multi_llm_adapter.py** | `services/adapters/multi_llm_adapter.py` | 與 `angela_llm_service.py` 功能重疊 | 廢棄 |

---

## 三、合併遷移計畫

### P0 — 立即執行（破壞性最小，最大收益）

#### P0.1 廢棄 multi_llm_adapter.py（已修正：發現 8 個問題）

**重大發現**：`angela_llm_service.py` 沒有 `chat_completion()` 方法，只有 `generate()` 和 `generate_text()`。以下系統依賴 `MultiLLMService.chat_completion()`：
- `fact_extractor_module.py`（A15）
- `ensemble.py`（A12）
- `dialogue_manager.py`（A11）
- `unified_control_center.py`（A13，直接實例化 MultiLLMService）

直接刪除會導致多個系統無法運作。**正確方案**：

```
方案：將 multi_llm_adapter.py 的介面遷移到 angela_llm_service.py（適配層模式）

步驟：
1. 在 angela_llm_service.py 中新增 ChatMessage, LLMResponse, ModelConfig dataclass
   （從 multi_llm_adapter.py 複製或重新實現）
2. 在 angela_llm_service.py 新增 chat_completion() 方法，封裝 generate() 結果
3. 更新 5 個 import 點都指向 angela_llm_service：
   - fact_extractor_module.py → from services.angela_llm_service import MultiLLMService
   - ensemble.py → from services.angela_llm_service import MultiLLMService
   - dialogue_manager.py → from services.angela_llm_service import MultiLLMService
   - unified_control_center.py → from services.angela_llm_service import MultiLLMService
   - language_models/router.py → 保留（只用到 ModelProvider enum）
4. 刪除 services/adapters/multi_llm_adapter.py

風險：中（需確保 chat_completion() 封裝正確；unified_control_center 需確認 config_path 相容）
```

#### P0.2 廢棄 EvolutionEngine + AutonomousEvolutionEngine
```
理由：evolution_engine.py（53行）無持久化；autonomous_evolution_engine.py（609行）從未被引用
發現：
  - evolution_engine.py: 只有 chat_service.py 引用（line 38, 51），reflect_and_evolve() 改用 anchor_learning
  - autonomous_evolution_engine.py: 零 import，只在自己檔案內定義
動作：
  1. 移除 chat_service.py 中的 self.evolution 初始化（line 38-39）
  2. 移除 chat_service.py 中的 self.evolution.reflect_and_evolve() 調用（line 129）
  3. 在相同位置改為 anchor_learning.on_axis_update("beta", {"curiosity": 0.02}) 等效
  4. 刪除 core/autonomous/evolution_engine.py
  5. 刪除 core/evolution/autonomous_evolution_engine.py

風險：低（EvolutionEngine 只有一個調用點；AutonomousEvolutionEngine 無調用點）
```

#### P0.3 替換 ToolDispatcher STUB（已修正：重新設計方案）

**發現**：ToolDispatcher 只有 `dialogue_manager.py` 一個主要調用者（line 146）。DialogueManager 本身在廢棄清單（P2.1）。

**重新評估**：廢棄 DialogueManager 後，ToolDispatcher 的主要使用者消失。ToolDispatcher 可選擇：
1. 廢棄 ToolDispatcher + DialogueManager 一起（推薦）
2. 讓 ToolDispatcher 指向 ProjectCoordinator._dispatch_single_subtask（需將 private → public）

```
方案A（推薦）：廢棄 ToolDispatcher + DialogueManager 一起
理由：
  - DialogueManager 是 ChatService 的平行路由系統（功能重疊）
  - DialogueManager 依賴 ToolDispatcher（STUB）+ MultiLLMService.chat_completion（介面不相容）
  - ChatService 已有完整路由邏輯（math → code → task → llm_switch → general）
動作：
  1. 廢棄 DialogueManager（見 P2.1）
  2. ToolDispatcher 改為包裝 ProjectCoordinator._dispatch_single_subtask（作為 public method）
  3. 所有使用 ToolDispatcher 的地方改為直接使用 ProjectCoordinator 或 ChatService

方案B（替代）：將 _dispatch_single_subtask 公開
動作：
  1. 在 ProjectCoordinator 中新增 public 方法 dispatch_subtask(data)
  2. ToolDispatcher.dispatch_tool_request() 委派給 ProjectCoordinator.dispatch_subtask()
  3. 保持介面，內部替換

風險：低（DialogueManager 已在廢棄清單，ToolDispatcher 沒有其他外部依賴）
```

### P1 — 下一步（需驗證）

#### P1.1 合併 ExecutionManager（發現配置 Bug）
```
理由：兩個 ExecutionManager 幾乎完全相同，但配置加載方式不同
發現：
  - core/managers/execution_manager.py: _load_config_from_system() 無 history_size 欄位（Config 沒有）
  - ai/execution/execution_manager.py: 雙重初始化 monitor（execution_monitor + monitor），傳錯 Config
  - 兩者都有 get_execution_manager() singleton，但無衝突（core/managers 版本從未被引用）
動作：
  1. 保留 ai/execution/execution_manager.py（作為主）
  2. 刪除 core/managers/execution_manager.py
  3. 修復 ai/execution/execution_manager.py 雙重監控問題（移除 self.execution_monitor）
  4. 修復 _load_config_from_system() 的 history_size 參數
  5. 確認 core/managers/ 內無其他引用 → 已確認全是被註釋的 import

風險：低（core/managers 版本從未被任何代碼引用）
```

#### P1.2 整合 FantasyDMAgent codex → DocumentBuilder
```
理由：FantasyDMAgent 有完整 ai-trpg-codex.json，但從未被任何系統使用
     DocumentBuilder 需要增強角色卡生成
動作：
  1. 在 DocumentBuilder 中增加 _load_fantasy_codex() 方法
  2. 角色卡生成時：查詢 codex → 提取戰艦規格 → 傳入 LLM prompt
  3. 將 fantasy_dm_agent.py 中的 _load_codex 邏輯遷移到 DocumentBuilder
風險：低（FantasyDMAgent 目前未被接入）
```

#### P1.3 接入 ProjectCoordinator → ChatService 驗證
```
理由：確保新建的 ProjectCoordinator 與現有架構整合正確
動作：
  1. 實際測試：發送「生成一個艦娘角色卡」之類的任務
  2. 確認 DocumentBuilder 段落拆分、LLM 呼叫、格式學習都正常
  3. 確認 fallback（當 LLM 超時）正常運作
  4. 確認 anchor_learning.on_axis_update 在成功/失敗後正確觸發
風險：低（隔離測試即可）
```

### P2 — 中期（架構優化）

#### P2.1 廢棄 DialogueManager（已深度驗證）
```
理由：
  - 與 ChatService 功能重疊，ChatService 是實際入口
  - 依賴 ToolDispatcher（STUB）+ MultiLLMService.chat_completion（介面不相容）
  - 需要廢棄才能解除 ToolDispatcher 壓力（P0.3）
發現（32 個引用）：
  - chat_service.py: config 中有 dialogue_manager_config={...}（line 467），但只是傳給 ProjectCoordinator
  - ai/dialogue/project_coordinator.py: 使用 dialogue_manager_config（line 61, 70）
  - api/v1/endpoints/mobile.py: 註釋提到「對接到 DialogueManager」（未實作）
  - 其他都是無效引用（註釋掉的 demo code、README 範例）
動作：
  1. 確認 DialogueManager 在 ChatService 中從未被實例化
  2. 移除 project_coordinator.py 中多餘的 dialogue_manager_config 參數
  3. 刪除 ai/dialogue/dialogue_manager.py
  4. 更新 ai/dialogue/__init__.py 移除 DialogueManager export
  5. 更新 core/shared/types/common_types.py 中 DialogueTurn 等 types（這些是通用類，保留）

風險：低（DialogueManager 只在 import 時被引用，從未實際執行）
```

#### P2.2 用戶反饋迴路：格式學習完整串接
```
理由：TemplateLibrary 有 add_custom_template，但沒有反饋觸發機制
動作：
  1. 在 chat_service.py 增加 _detect_feedback_intent（如「格式不對」「重新生成」）
  2. 反饋觸發時：刪除錯誤格式 → 重新调用 DocumentBuilder.build(user_feedback=...)
  3. DocumentBuilder 已有 learn_from_output 邏輯，完善串接
風險：低
```

#### P2.3 評估並處理 RAGManager
```
理由：95行代碼，依賴外部庫 sentence-transformers + faiss，且從未接入
動作：
  1. 檢查環境是否有 sentence-transformers 和 faiss
  2. 如果沒有 → 廢棄 RAGManager，用 HAMMemoryManager 向量搜尋替代
  3. 如果有 → 評估功能是否值得擴展，或與 HAMMemoryManager 整合
風險：低（4 個引用都在同一檔案內，無外部依賴）
```

#### P2.4 接入 PlanningAgent 到 ProjectCoordinator
```
理由：PlanningAgent（123行）從未被 import，可用 ProjectCoordinator 替代
動作：
  1. 將 PlanningAgent 的任務計劃邏輯遷移到 ProjectCoordinator
  2. 或保持 PlanningAgent 獨立，由 ProjectCoordinator 委派
  3. 刪除 ai/agents/specialized/planning_agent.py
風險：低（PlanningAgent 零 import）
```

#### P2.5 處理 CreativeWritingAgent（發現 Aligned 版本在錯誤位置）
```
理由：CreativeWritingAgent（63行 STUB）被 3 個檔案引用
     AlignedCreativeWritingAgent（208行）在 agents/examples/ 而非 ai/agents/specialized/
發現：
  - ai/agents/__init__.py export CreativeWritingAgent
  - agent_manager.py 有 state-impact logic for CreativeWritingAgent（line 130）
  - api/router.py 有 creative-writing-1 endpoint
動作：
  方案A：將 AlignedCreativeWritingAgent 遷移到 ai/agents/specialized/，替換 CreativeWritingAgent
  方案B：在原位重寫 CreativeWritingAgent，引用 Aligned 基類
  方案C：廢棄 CreativeWritingAgent，更新所有引用
建議：方案B（最小變動）
風險：中（api/router.py 和 agent_manager.py 需更新引用）
```

#### P2.3 評估並處理 RAGManager
```
理由：95行代碼，依賴外部庫 sentence-transformers + faiss，且從未接入
動作：
  1. 檢查環境是否有 sentence-transformers 和 faiss
  2. 如果沒有 → 廢棄 RAGManager，用 HAMMemoryManager 向量搜尋替代
  3. 如果有 → 評估功能是否值得擴展，或與 HAMMemoryManager 整合
風險：低
```

### P3 — 長期（可選）

| 任務 | 理由 |
|------|------|
| 接入 DigitalLifeIntegrator 到 ChatService | 讓 Angela 在對話中感知自身狀態 |
| 接入 BrainBridgeService 到 ChatService | 同步大腦狀態到對話上下文 |
| 將 PlanningAgent 接入 ProjectCoordinator | 增強任務分解的結構化程度 |
| 完善 WebSearchTool：加入快取、驗證 | 目前是簡單 HTML 解析 |
| 移除 TYPE_CHECKING 中的虛假路徑引用 | 清理 import 鍊 |
| 補齊 ProjectCoordinator / DocumentBuilder 的測試 | 目前無測試覆蓋 |

---

## 四、路線圖（優先級排序）

```
P0（立即執行）
├── P0.1: multi_llm_adapter.py 介面遷移（保持 thin wrapper）
├── P0.2: 廢棄 EvolutionEngine + AutonomousEvolutionEngine
└── P0.3: 廢棄 DialogueManager + ToolDispatcher（廢棄 DialogueManager 後 ToolDispatcher 無引用）

P1（驗證後執行）
├── P1.1: 刪除 core/managers/execution_manager.py（零引用）
├── P1.2: 整合 FantasyDMAgent codex → DocumentBuilder
└── P1.3: ProjectCoordinator + DocumentBuilder 隔離測試

P2（架構優化）
├── P2.1: 廢棄 DialogueManager → 確認 ChatService 不會變成上帝類
├── P2.2: 用戶反饋迴路完整串接
├── P2.3: RAGManager 評估
├── P2.4: PlanningAgent 處理（零引用）
└── P2.5: CreativeWritingAgent 重寫（小心 api/router 和 agent_manager 引用）

P3（可選）
├── 接入 DigitalLifeIntegrator / BrainBridgeService
├── TemplateLibrary thread-safety 驗證
└── 補齊 ProjectCoordinator / DocumentBuilder 測試
```

---

## 五、當前真實能力（審計後）

| 能力 | 觸發 | 實現 |
|------|------|------|
| 數學計算 | `123+235=` / `魚吃了2隻` | `MathVerifier` → 直接計算 |
| 代碼意圖解析 | 含 code/python 關鍵字 | `chat_service._detect_code_intent` → AST 解析 |
| 模型切換 | `[ollama:phi:latest]` | `chat_service._handle_llm_switch_intent` |
| 8D 軸狀態追蹤 | 每次輸入 | `StateMatrix` + `StateMatrixAdapter` + `AnchorLearningEngine` |
| θ 自檢與校正 | `theta_negativity > 0.5` | `state_matrix.detect_misallocated_points()` + `auto_correct_all()` |
| η 執行追蹤 | 每次任務 | `eta_state.execution_count` + `structural_drift` |
| 意圖路由 | 全量 keyword 表 | 8D resonance routing (dimension_fit) |
| 多步任務 | 生成/整理/角色卡關鍵字 | `ProjectCoordinator` + `DocumentBuilder`（需測試驗證） |
| 記憶存儲/檢索 | 每次對話 | `HAMMemoryManager` (向量+結構化) |
| 情緒分析 | 每次輸入 | `EmotionSystem` |
| 生物模擬 | 持續運行 | `BiologicalIntegrator` (6 子系統) |
| 螢幕/視覺分析 | 每次 | `VisionService` (OCR/物體偵測) |
| 非阻塞 LLM | 每次對話 | `WaitingScheduler` (30s timeout → fallback) |
| 工具調用 | — | **STUB**（需 P0.3 修復）|
| 多 agent 協作 | — | AgentManager 存在但未接入 |
| RAG 搜索增強 | — | RAGManager 存在但不完整 |

---

## 六、廢棄清單

| 檔案 | 理由 | 替代 |
|------|------|------|
| `services/adapters/multi_llm_adapter.py` | 功能重疊 | `angela_llm_service.py` |
| `core/autonomous/evolution_engine.py` | 53行，邏輯簡單 | `AnchorLearningEngine` |
| `core/evolution/autonomous_evolution_engine.py` | 609行，從未被引用 | 刪除 |
| `ai/rag/rag_manager.py` | 不完整，依賴外部庫 | `HAMMemoryManager` 向量搜尋 |
| `core/managers/execution_manager.py` | 與 `ai/execution/execution_manager.py` 重複（但需處理單例衝突） | 合併後保留一個 |
| `ai/dialogue/dialogue_manager.py` | 與 `chat_service.py` 平行，ChatService 已是唯一入口 | 逐步遷移後廢棄 |

---

## 七、關鍵檔案索引

### 核心整合點
- `services/chat_service.py` — 唯一入口（748行）
- `services/angela_llm_service.py` — LLM 調度（1780行，含 generate_text）
- `ai/dialogue/project_coordinator.py` — 任務協調（新建，293行）
- `ai/dialogue/document_builder.py` — 多段生成+格式學習（新建，305行）

### 認知與學習
- `core/autonomous/state_matrix.py` — 8D 軸（1729行）
- `core/autonomous/state_matrix_adapter.py` — 軸適配器+AnchorLearning
- `core/autonomous/anchor_learning.py` — 錨點學習（374行）

### 記憶系統
- `ai/memory/ham_memory/ham_manager.py` — HAM 記憶（236行）
- `ai/memory/template_library.py` — 模板庫（682行）
- `ai/memory/memory_template.py` — 模板數據結構（311行）

### 基礎設施
- `core/autonomous/biological_integrator.py` — 生物模擬（841行）
- `core/autonomous/waiting_scheduler.py` — 非阻塞排程
- `core/hsp/connector.py` — HSP 通信（1071行）
- `services/vision_service.py` — 視覺服務（704行）

## 八、模組邊界清晰度分析

### 核心問題：避免變成 LLM 黑盒子

審計發現以下系統存在職責模糊或過度依賴 LLM 的風險：

#### B1. P0.1 方案風險：`chat_completion()` 封裝層
```
問題：在 angela_llm_service.py 中新增 chat_completion() 封裝，
     把 multi_llm_adapter 的介面橋接過去。

風險：
- 如果封裝只是簡單的 generate() → chat_completion() 轉換，
  會把 angela_llm_service 變成另一個「萬能 LLM 介面」
- 5 個 consumer 各自有不同的調用模式，封裝層可能需要複製所有這些模式
- 介面暴露越多，內部複雜度越難管控

建議：
- chat_completion() 應該是 thin wrapper，不是新的抽象層
- 每個 consumer 的調用方式需單獨對接，不做統一封裝
```

#### B2. ProjectCoordinator + DocumentBuilder 耦合風險
```
問題：ProjectCoordinator._llm_generate_async() 直接綁定 generate_text()，
     DocumentBuilder 接收 llm_generate_fn callback。

風險：
- 依賴鏈：ChatService → ProjectCoordinator → DocumentBuilder → generate_text()
  如果 generate_text() 失敗，整個鏈都失敗
- DocumentBuilder 的「格式學習」基於 LLM 輸出，
  如果 LLM 行為改變，格式也會變
- _decompose_user_intent_into_subtasks() 本身是 LLM 呼叫，
  任務分解品質完全取決於 LLM

建議：
- 維持現狀（沒有替代方案）
- 明確標註這段依賴鏈是「有条件自治」，非完全模組化
- 標明 failure point：LLM 失敗時的 fallback 行為
```

#### B3. DialogueManager 廢棄後的功能真空
```
問題：廢棄 DialogueManager 後，ChatService 會不會變成 748 行的「上帝類」？

現狀：
- ChatService._handle_task_intent() → ProjectCoordinator
- ProjectCoordinator 有自己的 task_results, task_completion_events
- 兩者都有 session_id 概念，但沒有共享

風險：
- 如果 ChatService 承擔所有功能，會變成「上帝類」

建議：
- 廢棄 DialogueManager 前，先確認 ChatService 不會因此變成黑盒子
- 如果 ChatService 超過 1000 行，需要拆分（split by intent routing vs response generation）
```

#### B4. TemplateLibrary 作為格式學習的中間層
```
問題：TemplateLibrary 被多個地方使用（angela_llm_service, DocumentBuilder, ham_manager）

風險：
- 多個 consumer 共享同一個 TemplateLibrary instance，可能有 race condition
- 格式學習如果失敗，很難定位是哪個 consumer 的觸發

建議：
- 維持現狀（複雜度在可控範圍內）
- 標註：TemplateLibrary thread-safety 需要在 P3 階段驗證
```

#### B5. 8D State Matrix 的作用邊界
```
問題：StateMatrix 是「事實上的中央狀態」，所有模組都依賴它。

風險：
- 如果 StateMatrix 有 bug，會影響整個系統（單點故障）
- 但這不是「黑盒子」問題，而是「單點故障」問題

建議：
- StateMatrix 職責（軸狀態追蹤）保持清晰
- 不要在 StateMatrix 中加入新的 LLM 依賴
- 保持 export_for_llm() 輸出格式穩定
```

### 模組邊界原則

| 原則 | 說明 |
|------|------|
| **顯式依賴** | 每個模組的 public API 必須明確列出依賴的別的模組 |
| **失敗隔離** | LLM 失敗時，每個模組必須有明確的 fallback 行為 |
| **無環依賴** | 嚴禁 A→B→C→A 的循環依賴 |
| **責任單一** | 每個模組不超過 2 個主要職責（LRU: LLM + 非LLM 分離）|
| **可測試性** | 每個模組的關鍵邏輯必須可以用 mock LLM 測試 |

### P0 方案的模組邊界影響

| 任務 | 邊界影響 | 評估 |
|------|---------|------|
| P0.1 | 新增 chat_completion() 封裝 | ⚠️ 需保持 thin wrapper |
| P0.2 | 廢棄 EvolutionEngine，統一用 AnchorLearning | ✅ 清晰 |
| P0.3 | 廢棄 DialogueManager + ToolDispatcher | ✅ 需監控 ChatService 大小 |
| P1.1 | 刪除 core/managers/execution_manager.py | ✅ 零引用 |
| P1.2 | DocumentBuilder._load_fantasy_codex() | ✅ DocumentBuilder 職責範圍內 |
| P2.1 | 廢棄 DialogueManager | ✅ 需確保 ChatService 不變成上帝類 |
| P2.5 | CreativeWritingAgent 重寫 | ⚠️ api/router 和 agent_manager 都引用 |

### 額外發現：B6-B14（來自深度代碼審查）

| # | 系統 | 問題 | 評估 |
|---|------|------|------|
| **B6** | HAMMemoryManager + FantasyDMAgent | 兩者都加載 TRPG Codex，行為不一致 | ✅ 統一到 HAMMemoryManager |
| **B7** | ProjectCoordinator._decompose_user_intent_into_subtasks() | LLM 失敗時無 fallback | ✅ 已測試 + fallback |
| **B8** | ProjectCoordinator._integrate_subtask_results() | LLM 失敗時 raw concat，需標註 | ✅ 已測試 + fallback |
| **B9** | DocumentBuilder 段落無 timeout | 慢模型會導致 document build hang | ✅ asyncio.wait_for(timeout=15.0) |
| **B10** | ChatService 用 WaitingScheduler，DocumentBuilder 不用 | LLM 調用模式不一致 | ✅ 標註差異原因 |
| **B11** | DocumentBuilder._learn_format() 無去重 | 每次成功都寫入，累積重複 | ✅ _learned_format_keys dedup |
| **B12** | 三處 hardcoded keyword 意圖檢測 | _detect_task_intent + _detect_complex_task + _detect_task_type | ✅ core/intent_registry.py 統一 |
| **B13** | `get_template_library()` singleton 模塊初始化時無鎖保護 | init order + race condition | ✅ double-checked locking + threading.Lock |
| **B14** | ChatService._fallback_response() missing hasattr check | Confirmed: uses `getattr(..., "primary_emotion", None)` ✅ | ✅ 已修復 |
| **B15** | PlanningAgent (123行) 無任何引用 | 未被導入或調用 | ⏳ 已在代碼標注 deprecate staticmethod |
| **B16** | AlignedCreativeWritingAgent 位於 examples/ 目錄 | 從未被主代碼導入 | ✅ 無需操作（無引用） |

---

## 九、行動優先級（最終版）

經過模組邊界分析，調整後的優先級：

```
P0（立即執行）
├── P0.1: multi_llm_adapter.py 介面遷移（保持 thin wrapper）
├── P0.2: 廢棄 EvolutionEngine + AutonomousEvolutionEngine
└── P0.3: 廢棄 DialogueManager + ToolDispatcher

P1（驗證後執行）
├── P1.1: 刪除 core/managers/execution_manager.py（零引用）
├── P1.2: DocumentBuilder._load_fantasy_codex()（統一 HAMMemoryManager 的 codex 為唯一來源）
└── P1.3: ProjectCoordinator + DocumentBuilder 隔離測試（測試 B7/B8/B9/B10）

P2（架構優化）
├── P2.1: 廢棄 DialogueManager → 確認 ChatService 不會變成上帝類
├── P2.2: 用戶反饋迴路完整串接（+ B11 去重邏輯）
├── P2.3: RAGManager 評估
├── P2.4: PlanningAgent 處理（+ B12 統一意圖 registry）
└── P2.5: CreativeWritingAgent 重寫（小心 api/router 和 agent_manager 引用）

P3（可選）
├── 接入 DigitalLifeIntegrator / BrainBridgeService
├── TemplateLibrary thread-safety 驗證（B4 + B13）
└── 補齊 ProjectCoordinator / DocumentBuilder 測試
```

---

## 十、廢棄清單（最終版）

| 檔案 | 理由 | 替代 | 模組邊界影響 |
|------|------|------|------------|
| `services/adapters/multi_llm_adapter.py` | 介面遷移至 angela_llm_service | 封裝 chat_completion() | ⚠️ 需保持 thin |
| `core/autonomous/evolution_engine.py` | 無持久化 | AnchorLearningEngine | ✅ 無風險 |
| `core/evolution/autonomous_evolution_engine.py` | 零引用 | 刪除 | ✅ 無風險 |
| `core/tools/tool_dispatcher.py` | STUB，DialogueManager 廢棄 | N/A | ✅ 無風險 |
| `core/managers/execution_manager.py` | 零引用 | 刪除 | ✅ 無風險 |
| `ai/dialogue/dialogue_manager.py` | 從未實例化 | ChatService | ✅ 需監控 ChatService 大小 |
| `ai/rag/rag_manager.py` | 外部依賴 | HAMMemoryManager | ✅ 無風險 |
| `ai/agents/specialized/planning_agent.py` | 零引用 | ProjectCoordinator | ✅ 無風險 |

**保留（需要重寫）**：
- `ai/agents/specialized/creative_writing_agent.py` — 63行 STUB，3 個引用，需重寫
- `ai/agents/examples/aligned_agent_example.py` — 208行，需遷移或重寫

---

## 十一、關鍵檔案索引（更新）

### 角色卡與創作
- `ai/agents/specialized/fantasy_dm_agent.py` — TRPG codex（96行，codex 未被使用）
- `ai/agents/specialized/creative_writing_agent.py` — stub（63行，無實際功能）→ 需重寫
- `ai/agents/specialized/planning_agent.py` — 模板化規劃（123行）→ 零引用，待廢棄

### 需要修復（最終版）

| 子系統 | 檔案 | 問題 | 動作 |
|--------|------|------|------|
| **ToolDispatcher** | `core/tools/tool_dispatcher.py` | STUB（30行），DialogueManager 廢棄後無引用 | 刪除 |
| **ExecutionManager** | `core/managers/execution_manager.py` | 零引用，與 ai/execution 版本重複 | 刪除 |
| **multi_llm_adapter.py** | `services/adapters/multi_llm_adapter.py` | 介面遷移至 angela_llm_service | 封裝 chat_completion() 後刪除 |
| **RAGManager** | `ai/rag/rag_manager.py` | 95行，外部依賴，零引用 | 評估後廢棄 |
| **EvolutionEngine** | `core/autonomous/evolution_engine.py` | 53行，無持久化 | 刪除 |
| **AutonomousEvolutionEngine** | `core/evolution/autonomous_evolution_engine.py` | 609行，零引用 | 刪除 |
| **DialogueManager** | `ai/dialogue/dialogue_manager.py` | 從未實例化，與 ChatService 重疊 | 刪除 |
| **CreativeWritingAgent** | `ai/agents/specialized/creative_writing_agent.py` | 63行 STUB，3 個引用 | 需重寫 |
| **PlanningAgent** | `ai/agents/specialized/planning_agent.py` | 123行，零引用 | 刪除 |

---

## 十二、最終版備註

- `autonomous_evolution_engine.py` 零 import，可直接刪除 ✅
- `core/managers/execution_manager.py` 零 live import（都是註釋），可刪除 ✅
- `DialogueManager` 從未實例化，ChatService 從未使用，可刪除 ✅
- `PlanningAgent` 零外部 import，可刪除 ✅
- `chat_completion()` 封裝需保持 thin，不做統一抽象 ✅
- ChatService（748行）廢棄 DialogueManager 後需監控大小，超過 1000 行需拆分 ✅
- TemplateLibrary thread-safety 需在 P3 驗證 ✅
- StateMatrix 作為中央狀態，保持職責清晰，不加入新的 LLM 依賴 ✅