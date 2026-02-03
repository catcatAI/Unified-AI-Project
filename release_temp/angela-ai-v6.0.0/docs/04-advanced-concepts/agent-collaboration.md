# Agent Collaboration Manager (代理協作管理器)

## 總覽 (Overview)

`AgentCollaborationManager` 是 Unified AI 系統中的一個高階協調模組，其主要職責是管理和協調多個專門的 AI 代理 (Agent) 共同完成一個複雜的任務。它將一個大型任務分解為一系列子任務，並將這些子任務分派給具有相應能力的代理，最後將各個代理的結果整合成最終的解決方案。

此管理器嚴重依賴以下兩個核心元件：
- `AgentManager`: 用於追踪可用的代理。
- `HSPConnector`: 用於透過「異構服務協定 (HSP)」與代理進行非同步的任務分派和結果回收。

## 架構角色 (Architectural Role)

在系統架構中，`AgentCollaborationManager` 扮演著「元代理 (Meta-Agent)」或專案經理的角色。它位於單一代理之上，負責處理需要多種能力組合才能解決的複雜請求。例如，一個「分析報告生成」任務可能需要：
1.  一個 `WebSearchAgent` 來收集資料。
2.  一個 `DataAnalysisAgent` 來分析資料。
3.  一個 `CreativeWritingAgent` 來撰寫報告。

此管理器負責編排整個工作流程。

## 核心工作流程 (Core Workflow)

1.  **任務啟動**: 外部模組（如 `ProjectCoordinator`）呼叫 `coordinate_collaborative_task()` 方法，並傳入一個包含多個子任務定義的列表。
2.  **任務追蹤**: 管理器為整個協作任務和每個子任務建立唯一的 ID，並在 `self.collaboration_tasks` 中初始化追蹤狀態。
3.  **非同步分派**: 管理器使用 `asyncio.create_task()` 為每個子任務啟動一個 `_execute_subtask()` 的非同步執行個體。
4.  **子任務執行**:
    - `_execute_subtask()` 方法根據子任務所需的 `capability_needed` 建立一個 `HSPTaskRequestPayload`。
    - **(未來實現)** 在完整實現中，它將透過服務發現模組找到擁有該能力的最佳代理。
    - **(目前實現)** 目前程式碼中，此步驟為模擬，會直接返回一個模擬的成功結果。
5.  **結果回收**:
    - 當代理完成任務後，會透過 HSP 將結果傳回。
    - `HSPConnector` 觸發已註冊的 `_handle_agent_result()` 回呼函式。
6.  **結果整合**:
    - `_handle_agent_result()` 儲存收到的子任務結果，並更新協作任務的完成進度。
    - 當所有子任務都完成後，`coordinate_collaborative_task()` 會從 `asyncio.gather()` 收到所有結果，並將它們整合成一個字典後返回。

## 關鍵方法 (Key Methods)

- `async def coordinate_collaborative_task(task_id: str, subtasks: List[Dict[str, Any]])`:
  啟動並管理一個完整的協作任務。這是該模組的主要進入點。

- `async def _execute_subtask(subtask_id: str, subtask: Dict[str, Any]])`:
  執行單一子任務，將其打包成 HSP 請求。

- `def _handle_agent_result(result_payload: HSPTaskResultPayload, sender_ai_id: str)`:
  處理從代理返回的結果的回呼函式。

- `async def get_agent_capabilities()`:
  獲取所有可用代理的能力列表 (目前為靜態模擬資料)。

- `def get_collaboration_status(task_id: str)`:
  查詢特定協作任務的當前狀態。

- `def cancel_collaboration_task(task_id: str)`:
  取消一個正在進行中的協作任務。

## 使用範例 (Example Usage)

```python
# 建立一個協作任務，包含兩個子任務
task_id = "report_generation_task_001"
subtasks = [
    {
        "capability_needed": "search_web_v1.0",
        "task_parameters": {"query": "market trends for AI in 2025"},
        "task_description": "Search for market trends of AI in 2025."
    },
    {
        "capability_needed": "data_summary_v1.0",
        "task_parameters": {"input_data": "[dependency:previous_task_result]"},
        "task_description": "Summarize the findings from the web search."
    }
]

# 啟動協作
final_result = await collaboration_manager.coordinate_collaborative_task(task_id, subtasks)
```