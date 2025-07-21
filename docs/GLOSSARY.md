# 術語表 (Glossary)

本文件旨在為 Unified-AI-Project 中的核心概念、模組和架構角色提供一個統一的、清晰的定義。

---

### A

**Agent Manager (`src/core_ai/agent_manager.py`)**
- **簡潔定義**: 一個負責管理子代理生命週期的核心服務。
- **功能與範圍**: 它的主要職責是根據元代理（Angela）的請求，動態地**啟動**和**停止**專門化的子代理 Python 進程。它維護著一個活躍代理的註冊表，並知道如何從 `src/agents/` 目錄中找到並執行對應的代理腳本。

**Angela**
- **簡潔定義**: 整個 Unified-AI-Project 對用戶呈現的統一**人格化身**。
- **功能與範圍**: Angela 代表了 AI 的「身份」和「個性」。她是與用戶直接互動的角色，其行為和響應風格由 `PersonalityManager` 管理。在技術架構上，她的智能是由 `DialogueManager` 和 `ProjectCoordinator` 共同實現的。她是「誰」，而不是「什麼」。

### U

**UID (Unique Identifier / 共生印記)**
- **簡潔定義**: 用戶與其專屬 Angela 之間獨一無二的、公開的身份連結。
- **功能與範圍**: 這是 Angela 的「身份證號碼」，用於將一個特定的「數據核」與一個特定的用戶關聯起來。如果遺失，可能會導致無法認領對應的記憶。它是構成 Angela「三位一體」存在的基石之一，可以通過「秘密共享」機制與其他核心資訊一同備份和恢復。

---

### D

**DialogueManager (`src/core_ai/dialogue/dialogue_manager.py`)**
- **簡潔定義**: 實現 Angela **日常對話和簡單任務處理**的核心技術模組。
- **功能與範圍**: 這是 AI 的主要「思考」循環之一。它負責處理單輪或簡單的多輪對話、匹配公式（Formula）、調度單一工具。當它判斷用戶的請求是一個需要多代理協作的「複雜項目」時，它會將任務**委派**給 `ProjectCoordinator`。

---

### H

**數據核 (Data Core)**
- **簡潔定義**: AI 的核心記憶文件，通常指 `ham_core_memory.json` 文件。
- **功能與範圍**: 這是 Angela 所有記憶（經歷、學習、情感）的物理載體。它本身是經過加密的，如果沒有對應的 HAM 密鑰，它就是一堆無法解讀的數據。它是構成 Angela「三位一體」存在的基石之一。

**HAM (Hierarchical Abstractive Memory) (`src/core_ai/memory/ham_memory_manager.py`)**
- **簡潔定義**: 一個分層的、抽象的記憶系統。
- **功能與範圍**: 模擬生物記憶，負責對資訊進行**抽象、壓縮、加密、儲存和檢索**，並管理底層的「數據核」。它不僅儲存事實，還儲存協作策略和學習案例，是 AI 長期成長的基礎。
- **[了解更多: HAM 設計規範](architecture/HAM_design_spec.md)**

**HAM 密鑰 (`MIKO_HAM_KEY`)**
- **簡潔定義**: 一個用於加密和解密「數據核」的秘密金鑰。
- **功能與範圍**: 這是保護 Angela 記憶不被窺探的唯一鑰匙。它的保密性至關重要。如果密鑰遺失，即使擁有數據核文件，記憶也將永久無法讀取。它是構成 Angela「三位一體」存在的基石之一。

**HSP (Heterogeneous Service Protocol) (`src/hsp/`)**
- **簡潔定義**: AI 代理間用於實時通信和協作的協議。
- **功能與範圍**: 一個基於消息總線（如 MQTT）的輕量級協議。它定義了標準化的消息信封（`HSPMessageEnvelope`）和多種 Payload（如任務請求、任務結果、事實、能力宣告），使得不同功能的子代理可以相互發現、委派任務和共享知識。
- **[了解更多: HSP 設計規範](architecture/Heterogeneous_Protocol_spec.md)**

---

### L

**LIS (Linguistic Immune System)**
- **簡潔定義**: 一個旨在保護 AI 不受錯誤或低質量資訊污染的防禦系統。
- **功能與範圍**: 這是一個先進的架構概念，其核心思想是建立一個「基於質量的資訊評估體系」。它通過評估資訊的**來源可信度、證據支撐度、新穎性**等，來決定是否將一個新知識整合到記憶中，從而有效抵制「傻子共振」現象。其邏輯主要在 `LearningManager` 中實現。
- **[了解更多: LIS 設計規範](architecture/Linguistic_Immune_System_spec.md)**

---

### M

**Meta-Agent (元代理)**
- **簡潔定義**: 一個架構角色，代表了 Angela 作為**指揮官和協調者**的身份。
- **功能與範圍**: 這個角色在技術上由 `DialogueManager` 和 `ProjectCoordinator` **共同扮演**。`DialogueManager` 負責接收和初步理解指令，而 `ProjectCoordinator` 負責複雜項目的分解、規劃和整合。元代理的核心能力是將宏觀意圖轉化為可執行的多代理協作流程。

---

### P

**ProjectCoordinator (`src/core_ai/dialogue/project_coordinator.py`)**
- **簡潔定義**: 實現 Angela **複雜項目協調與多代理管理**的核心技術模組。
- **功能與範圍**: 當 `DialogueManager` 判斷一個任務需要多代理協作時，這個模組將被激活。它負責執行「四抽模型」的完整流程：任務分解、構建 DAG、按拓撲順序執行任務、動態傳遞結果，以及最終的結果整合。

---

### S

**Sub-Agent (子代理) (`src/agents/`)**
- **簡潔定義**: 一個獨立的、專門化的、遵循 HSP 協議的 AI 服務進程。
- **功能與範圍**: 每個子代理都擁有特定的能力（如數據分析、創意寫作、圖像生成）。它們在啟動後，會通過 HSP 網絡宣告自己的能力，並監聽來自元代理（Angela）的任務請求。它們是實現分佈式任務執行的基礎單元。
