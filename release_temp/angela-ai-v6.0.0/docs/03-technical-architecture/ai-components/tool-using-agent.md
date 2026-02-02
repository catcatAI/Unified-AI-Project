# 工具使用代理 (Tool Using Agent)

## 概述
工具使用代理 (`tool_using_agent.py`) 是一個專門的 AI 代理，能夠利用各種外部工具/服務來完成複雜任務。它充當一個協調器，將子任務分派給其他專業的服務管理器。

## 當前狀態 (模擬)
目前，工具使用代理處於**模擬狀態**。它通過呼叫已整合的模擬服務管理器來展示其工具使用能力。這使得 Agent 可以在不依賴真實外部服務的情況下進行開發和測試。

## 核心組件
- **`ToolUsingAgent`**: 繼承自 `BaseAgent`，實現了感知、決策、行動和回饋循環。其 `act` 方法包含根據任務調度不同服務管理器的邏輯。

## 整合點
- **`tool_using_agent.py`**: 包含 `ToolUsingAgent` 的核心邏輯。
- **服務管理器**: 該代理直接與 `llm_manager`, `search_manager`, `image_manager`, `code_analysis_manager`, `data_analysis_manager`, `nlp_manager`, `vision_manager`, `audio_manager`, `planning_manager` 等服務管理器互動。

## 未來發展
- **真實工具整合**: 當底層服務管理器整合真實 API 後，`ToolUsingAgent` 將能夠利用這些真實工具執行任務。
- **工具選擇優化**: 實現更智能的工具選擇策略，例如基於上下文、任務類型和工具能力的動態選擇。
- **工具鏈接與組合**: 探索將多個工具鏈接或組合起來以解決更複雜問題的能力。