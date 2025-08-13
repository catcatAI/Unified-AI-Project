# Fact Extractor Module (fact_extractor_module.py)

## 模組概述 (Overview)
`fact_extractor_module.py` 模組實現了 `FactExtractorModule` 類，該類旨在利用大型語言模型 (LLM) 從自然語言文本中提取結構化的事實和用戶偏好。它能夠將非結構化的用戶輸入轉換為可供 AI 系統進一步處理和利用的結構化數據，對於構建個性化和上下文感知的 AI 系統至關重要。

## 目的 (Purpose)
本模組的主要目的是識別並提取用戶在其消息中明確陳述的偏好（例如：喜歡、不喜歡、最愛）和事實斷言（例如：姓名、職業、位置、財產等），並將這些信息轉換為統一的、機器可讀的 JSON 格式。

## 主要職責與功能 (Key Responsibilities and Features)

### `FactExtractorModule` 類
-   **初始化 (`__init__`)**:
    -   接收一個 `MultiLLMService` 實例，用於與 LLM 進行通信。
    -   設定 `model_id` (預設為 "fact_extraction_model_placeholder") 和可選的 `model_params` (預設為 `{"temperature": 0.3}`)，用於配置 LLM 的行為。
-   **構建事實提取提示 (`_construct_fact_extraction_prompt`)**:
    -   根據輸入文本和可選的 `user_id` (目前未直接使用，但為未來個性化預留) 構建一個詳細的 LLM 提示。
    -   提示明確指示 LLM 識別用戶偏好和事實斷言，並要求以特定 JSON 格式響應，其中包含 `fact_type`、`content` (鍵值對) 和 `confidence` 字段。
    -   提供了 `user_preference` 和 `user_statement` 兩種 `fact_type` 的具體 `content` 示例。
-   **提取事實 (`extract_facts`)**:
    -   一個異步方法，負責與 LLM 服務交互以執行事實提取。
    -   如果 `llm_service` 不可用，則記錄錯誤並返回空列表。
    -   將構建好的提示發送給 LLM，並等待響應。
    -   處理 LLM 的原始 JSON 響應，包括 JSON 解碼和對提取數據結構的驗證。
    -   對每個提取的事實項目進行結構和數據類型驗證，確保 `fact_type` 為字串，`content` 為字典，`confidence` 為浮點數或整數。
    -   將 `confidence` 值規範化到 0.0 到 1.0 之間。
    -   跳過無效或格式錯誤的事實項目，並記錄警告。
    -   返回一個包含成功解析的 `ExtractedFact` 對象的列表。
-   **錯誤處理**: 包含 `try-except` 區塊，用於捕獲 JSON 解碼錯誤和 LLM 響應處理期間可能發生的其他異常，確保模組的健壯性。

## 工作原理 (How it Works)
1.  **實例化**: 創建 `FactExtractorModule` 的實例，並提供一個能夠與 LLM 通信的 `MultiLLMService` 對象。
2.  **提示構建**: 當調用 `extract_facts` 方法並傳入用戶文本時，模組內部會調用 `_construct_fact_extraction_prompt` 方法，生成一個專門為事實提取優化的 LLM 提示。
3.  **LLM 交互**: 生成的提示被發送給配置的 LLM（通過 `MultiLLMService`），LLM 根據提示的指示處理用戶文本並返回一個 JSON 格式的響應。
4.  **響應解析與驗證**: 模組接收到 LLM 的原始 JSON 字串響應後，會嘗試解析它。它會遍歷解析後的數據，驗證每個提取的事實是否符合預期的 `ExtractedFact` 結構。
5.  **結果返回**: 成功驗證的事實將被收集到一個 `ExtractedFact` 對象列表中並返回。任何解析或驗證失敗都會被記錄，並返回空列表或部分有效的事實列表。

## 與其他模組的整合 (Integration with Other Modules)
-   **`services.multi_llm_service.MultiLLMService`**: 本模組的核心功能依賴於 `MultiLLMService` 來與 LLM 進行通信，執行實際的事實提取任務。
-   **`.types.ExtractedFact`**: 模組的輸出類型 `ExtractedFact` 預計來自 `apps/backend/src/core_ai/learning/types.py`，確保了數據結構的一致性。
-   **`logging`**: 模組廣泛使用 Python 的標準 `logging` 模組來記錄調試信息、警告和錯誤，便於監控和問題排查。

## 程式碼位置 (Code Location)
`apps/backend/src/core_ai/learning/fact_extractor_module.py`
