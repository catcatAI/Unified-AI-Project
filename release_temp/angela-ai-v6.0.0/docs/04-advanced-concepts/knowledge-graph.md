# Knowledge Graph (知識圖譜)

## 總覽 (Overview)

知識圖譜 (Knowledge Graph, KG) 是 Unified AI 系統中一個核心的 AI 元件，其目標是將非結構化的資訊（如純文字）轉化為一個由「實體 (Entities)」和「關係 (Relationships)」組成的結構化網路。這使得 AI 不僅能理解文字的表面含義，更能推理實體之間的深層連結，從而做出更智慧的決策。

此系統主要由兩部分構成：

1.  **資料結構 (Data Structures)**: 在 `apps/backend/src/ai/knowledge_graph/types.py` 中定義，為知識圖譜提供了標準化的綱要 (schema)。
2.  **互動代理 (Agent)**: 在 `apps/backend/src/ai/agents/specialized/knowledge_graph_agent.py` 中實現，作為系統其他部分與知識圖譜功能互動的統一介面。

## 1. 資料結構 (`types.py`)

為了確保資料的一致性和可預測性，知識圖譜的結構使用了 Python 的 `TypedDict` 進行了嚴格定義。

- **`KGEntity` (實體)**: 代表圖譜中的一個節點，例如「巴黎」、「愛因斯坦」或一個抽象概念。其關鍵欄位包括：
    - `id`: 實體的唯一識別碼。
    - `label`: 實體的顯示名稱。
    - `type`: 實體的類型（例如 `PERSON`, `LOCATION`, `CONCEPT`）。

- **`KGRelationship` (關係)**: 代表圖譜中連接兩個實體的邊。例如，它能描述「愛因斯坦」- `born_in` -> 「德國」這樣的關係。其關鍵欄位包括：
    - `source_id`: 起點實體的 ID。
    - `target_id`: 終點實體的 ID。
    - `type`: 關係的類型（例如 `is_a`, `works_for`, `located_in`）。

- **`KnowledgeGraph` (知識圖譜)**: 頂層的容器物件，它將一個特定的知識圖譜所需的所有實體、關係和元數據（`metadata`）捆綁在一起。

## 2. 知識圖譜代理 (`knowledge_graph_agent.py`)

`KnowledgeGraphAgent` 是一個專門的 AI 代理，負責提供所有與知識圖譜相關的服務。

### 能力 (Capabilities)

此代理向系統宣告並提供以下三種核心能力：

1.  **`entity_linking` (實體連結)**: 從一段文字中識別出命名實體，並將它們連結到知識庫中的對應項目。
2.  **`relationship_extraction` (關係抽取)**: 從文字中分析並抽取出不同實體之間的語義關係。
3.  **`graph_query` (圖譜查詢)**: 根據一個查詢語句，在現有的知識圖譜中尋找答案。

### **重要：目前的實現狀態**

當前版本的 `KnowledgeGraphAgent` 內部實現是**簡化的佔位符和原型**。它使用非常基礎的啟發式規則（例如，假定所有大寫單詞都是實體，或匹配「X is Y」這樣的簡單句式）來模擬上述能力。程式碼註解中明確指出，在未來的完整實現中，這些功能將會被真正的自然語言處理（NLP）模型和圖譜資料庫所取代。因此，目前的代理主要用於搭建架構和流程，而非提供生產級的精確度。

## 工作流程範例 (Workflow Example)

1.  一個模組（例如 `ContentAnalyzer`）取得一段需要分析的文字。
2.  它呼叫 `KnowledgeGraphAgent` 的 `entity_linking` 和 `relationship_extraction` 能力。
3.  代理處理文字後，回傳一個 `KnowledgeGraph` 物件，其中包含了從文字中識別出的所有實體和關係。
4.  這個 `KnowledgeGraph` 物件可以被儲存起來，與一個更大的主圖譜進行合併，或在之後透過代理的 `graph_query` 能力進行查詢。