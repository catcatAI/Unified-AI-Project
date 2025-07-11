# ContextCore Module: Implementation Plan

**Version:** 0.1
**Date:** July 11, 2024
**Authors:** Jules (AI Agent)

## 1. Objective

This document outlines the implementation plan for the **ContextCore Module**. The primary objective is to develop a dedicated long-term memory and advanced context management system for the Unified-AI-Project. ContextCore will enhance the AI's coherence across extended interactions, enable deeper personalization, support more sophisticated learning, and provide a robust foundation for complex reasoning by maintaining and leveraging a rich, evolving model of users, topics, and the AI's own knowledge.

This plan expands upon the initial concepts detailed in `docs/architecture/blueprints/ContextCore_design_proposal.md`.

## 2. Core Functionalities

ContextCore will provide the following core functionalities:

1.  **Persistent Multi-Modal Knowledge Store:**
    *   Store diverse data types: structured facts, entities, relationships (knowledge graph triples), dialogue summaries, user profiles, experiential logs, and potentially embeddings or references to multimedia content.
    *   Ensure data persistence across sessions and system restarts.
2.  **Contextual Knowledge Graph (CKG):**
    *   Maintain a dynamic graph representing entities and their relationships, scoped by user, session, or global context.
    *   Support for evolving ontologies or schemas.
3.  **Vector Embeddings Store:**
    *   Store embeddings of textual and potentially other data for efficient semantic search and similarity-based retrieval.
4.  **Contextual Scoping & Namespacing:**
    *   Manage and retrieve context at various levels: global (shared knowledge), user-specific, session-specific, and task-specific.
    *   Prevent context leakage between different users or unrelated tasks.
5.  **Temporal Awareness & Knowledge Evolution:**
    *   Timestamp contextual items and track their evolution.
    *   Support for versioning or understanding the recency and relevance of information.
6.  **Context Compression, Summarization & Distillation:**
    *   Implement strategies to distill key information from verbose dialogues or large data chunks.
    *   Periodically summarize or compress older context to manage storage and retrieval efficiency while retaining salient information.
7.  **Knowledge Ingestion & Integration Pipeline:**
    *   Provide robust APIs and mechanisms for other modules (e.g., `LearningManager`, `DialogueManager`, `ContentAnalyzerModule`) to contribute new information, facts, and experiences to ContextCore.
    *   Handle potential conflicts or updates to existing knowledge.
8.  **Advanced Query & Retrieval Engine:**
    *   Support complex queries including semantic search (vector-based), graph pattern matching, faceted search, and queries that combine these methods.
    *   Enable retrieval of context relevant to specific queries, users, tasks, and temporal windows.
9.  **Personalization Support:**
    *   Store and manage user-specific preferences, history, and derived traits to enable personalized AI behavior.

## 3. Proposed New Modules/Classes (target: `src/core_ai/memory/context_core/`)

*   `manager.py`:
    *   `ContextCoreManager`: The main public interface for interacting with ContextCore. Orchestrates other internal components.
*   `graph_store.py`:
    *   `ContextualKnowledgeGraph`: Abstract base class (ABC) for graph operations.
    *   `Neo4jCKG(ABC)` / `NetworkXCKG(ABC)`: Concrete implementations (consider starting with NetworkX for simplicity, with an eye to Neo4j/other for scalability).
*   `vector_store.py`:
    *   `ContextVectorStore`: ABC for vector storage and search.
    *   `FAISSVectorStore(ABC)` / `PineconeVectorStore(ABC)`: Concrete implementations.
*   `document_store.py`: (For unstructured/semi-structured data like dialogue summaries, logs)
    *   `ContextDocumentStore`: ABC for document storage.
    *   `SQLiteDocumentStore(ABC)` / `ElasticsearchDocumentStore(ABC)`: Concrete implementations.
*   `data_models.py`:
    *   `ContextItem(TypedDict)`: Base model for all items stored in ContextCore (ID, type, content, metadata, timestamps, scopes, source).
    *   `ContextNode(TypedDict)`: For KG nodes.
    *   `ContextRelationship(TypedDict)`: For KG edges.
    *   `UserContextProfile(TypedDict)`: Structured user profile data.
    *   `RetrievedContext(TypedDict)`: Standard format for query results.
*   `query_engine.py`:
    *   `ContextQueryEngine`: Processes queries, interacts with different stores (graph, vector, document), and aggregates results.
*   `ingestion.py`:
    *   `ContextIngestionPipeline`: Handles processing and storing new data into ContextCore. Includes steps like entity extraction, relationship identification, embedding generation.
*   `persistence.py`:
    *   Handles overall saving and loading of ContextCore state if not managed by individual store backends (e.g., for NetworkX graphs or local FAISS indexes).
*   `summarizer.py`:
    *   `ContextSummarizer`: Module responsible for context compression and summarization tasks (potentially using LLMs via `LLMInterface`).

## 4. Data Structures (`TypedDict` Examples)

```python
from typing import TypedDict, List, Dict, Any, Optional, Literal, Union, Tuple

class ContextItemMetadata(TypedDict):
    created_at: float # timestamp
    updated_at: float # timestamp
    source_module: str # e.g., "DialogueManager", "LearningManager"
    source_interaction_id: Optional[str]
    confidence: Optional[float]
    tags: Optional[List[str]]
    custom_properties: Optional[Dict[str, Any]]

class ContextItem(TypedDict):
    item_id: str # Unique ID for the context item
    item_type: str # e.g., "fact", "dialogue_summary", "user_preference", "entity_profile"
    content: Any # The actual data (text, structured dict, embedding vector, etc.)
    scopes: List[str] # e.g., ["global", "user:USER_ID", "session:SESSION_ID"]
    metadata: ContextItemMetadata

class KnowledgeGraphTriple(TypedDict):
    subject_id: str
    predicate: str
    object_id_or_literal: Union[str, Any]
    scope: str # e.g., "user:USER_ID"

class RetrievedContextChunk(TypedDict):
    item_id: str
    content: Any
    score: float # Relevance score
    source_store: Literal["graph", "vector", "document"]
    metadata: ContextItemMetadata
```

## 5. API Definitions (Conceptual Methods for `ContextCoreManager`)

*   `async def add_item(self, item_content: Any, item_type: str, scopes: List[str], source_module: str, metadata_override: Optional[Dict] = None) -> str: # Returns item_id`
*   `async def get_item(self, item_id: str) -> Optional[ContextItem]:`
*   `async def update_item_content(self, item_id: str, new_content: Any) -> bool:`
*   `async def add_graph_triples(self, triples: List[KnowledgeGraphTriple], scope: str):`
*   `async def query_knowledge_graph(self, pattern: str, scope: str) -> List[Dict]: # e.g., Cypher query or SPARQL`
*   `async def semantic_search(self, query_text: str, scopes: List[str], top_k: int = 5, vector_property: Optional[str]=None) -> List[RetrievedContextChunk]:`
*   `async def get_relevant_context(self, primary_query: str, user_id: str, session_id: Optional[str], task_description: Optional[str], num_chunks: int = 10) -> List[RetrievedContextChunk]:` (Composite method using query engine)
*   `async def store_user_interaction(self, user_id: str, session_id: str, interaction_summary: Dict, dialogue_transcript: Optional[str]):`
*   `async def get_user_profile_summary(self, user_id: str) -> Optional[UserContextProfile]:`
*   `async def run_context_maintenance(self): # For summarization, archiving, etc.`

## 6. Core Logic/Algorithms

*   **Knowledge Ingestion Pipeline (`ContextIngestionPipeline`):**
    1.  Receive data (e.g., text, structured facts).
    2.  Pre-processing (cleaning, normalization).
    3.  Entity/Relationship Extraction (e.g., using spaCy or an LLM-based extractor Tech Block if Bus system is available).
    4.  Embedding Generation (for text, using a SentenceTransformer or similar model).
    5.  Store structured data in KG (`ContextualKnowledgeGraph`).
    6.  Store embeddings in Vector Store (`ContextVectorStore`).
    7.  Store raw/summarized content in Document Store (`ContextDocumentStore`).
    8.  Create/Update `ContextItem` entries.
*   **Context Retrieval (`ContextQueryEngine`):**
    1.  Parse input query/need (e.g., from `DialogueManager`).
    2.  Determine relevant scopes (user, session, global).
    3.  Perform parallel or sequential queries across stores:
        *   Semantic search in `ContextVectorStore`.
        *   Graph pattern matching in `ContextualKnowledgeGraph`.
        *   Keyword/metadata search in `ContextDocumentStore`.
    4.  Aggregate and rerank results based on relevance, recency, confidence.
    5.  Format results as `List[RetrievedContextChunk]`.
*   **Context Summarization/Distillation (`ContextSummarizer`):**
    *   Triggered periodically or by data volume thresholds.
    *   Identifies older/verbose context items.
    *   Uses LLMs (via `LLMInterface` or an LLM Tech Block) to generate concise summaries.
    *   Updates or replaces original items with summaries, possibly archiving full versions.
*   **Temporal Management:**
    *   All `ContextItem`s have `created_at` and `updated_at` timestamps.
    *   Retrieval logic can factor in recency.
    *   Future: Implement decay functions for relevance scores of older, less accessed items.

## 7. Integration Points & Refactoring Plan

*   **`HAMMemoryManager` (`src/core_ai/memory/ham_memory_manager.py`):**
    *   **Initial Phase (Complementary):** HAM continues to manage short-term/episodic memory (dialogue turns, raw experiences).
    *   A new process (possibly within `LearningManager` or `ContextCoreManager` itself) will periodically extract key information (facts, summaries, entities) from HAM and ingest it into ContextCore for long-term storage and structuring.
    *   `DialogueManager` might still use HAM for very recent turn history, but rely on ContextCore for broader context.
    *   **Long-Term Vision:** HAM's functionality could be largely absorbed by ContextCore, with ContextCore directly handling various memory types. This would be a significant refactor of `DialogueManager`'s memory interactions.
*   **`DialogueManager` (`src/core_ai/dialogue/dialogue_manager.py`):**
    *   Will instantiate and use `ContextCoreManager`.
    *   Before generating a response, it will call `ContextCoreManager.get_relevant_context()` with the current query, user ID, session ID, and task details.
    *   After processing a user turn, it will call `ContextCoreManager.store_user_interaction()` with summaries and key takeaways.
    *   Will use `ContextCoreManager.get_user_profile_summary()` for personalization.
*   **`LearningManager` & `ContentAnalyzerModule` (`src/core_ai/learning/`):**
    *   These modules will become primary producers of structured knowledge for ContextCore.
    *   `FactExtractorModule` outputs will be sent to `ContextCoreManager.add_item()` or `add_graph_triples()`.
    *   `ContentAnalyzerModule`'s knowledge graph generation will directly populate/update `ContextCore`'s CKG for the relevant scope.
*   **`FragmentaOrchestrator` / Future Bus System:**
    *   Individual modules/Tech Blocks orchestrated by Fragmenta/Bus will be able to query ContextCore for specific information needed for their tasks.
    *   ContextCore itself might be exposed as a service/module accessible via the Bus system.
*   **User Profile System (if any existing):**
    *   User preferences, history, and traits currently stored elsewhere should be migrated to or synchronized with `ContextCore`'s `UserContextProfile`.

## 8. Configuration (`configs/`)

*   `configs/memory/context_core_config.yaml`:
    *   `knowledge_graph_backend`: "networkx" (default, local) or "neo4j" (requires connection details).
    *   `vector_store_backend`: "faiss" (default, local) or "pinecone" (requires API key, environment).
    *   `document_store_backend`: "sqlite" (default, local) or "elasticsearch" (requires connection details).
    *   `persistence_path`: Base directory for storing local ContextCore data.
    *   `embedding_model_name`: Name of sentence transformer model to use (e.g., "all-MiniLM-L6-v2").
    *   `summarization_llm_model`: LLM model to use for summarization tasks.
    *   `ingestion_batch_size`: Batch size for processing new items.
    *   `maintenance_schedule`: Cron-like string for running context maintenance (summarization, archiving).

## 9. Basic Test Cases

*   **Storage & Retrieval:**
    *   Test `add_item` and `get_item` for various `ContextItem` types and scopes.
    *   Test atomicity of updates.
*   **Knowledge Graph:**
    *   Test `add_graph_triples` and verify graph structure.
    *   Test graph queries for specific patterns and relationships.
*   **Vector Store & Semantic Search:**
    *   Test embedding generation during ingestion.
    *   Test `semantic_search` for relevance and `top_k` results.
*   **Query Engine:**
    *   Test `get_relevant_context` combines results from different stores appropriately.
    *   Test scoping (user, session, global) correctly filters results.
*   **Integration:**
    *   Test `DialogueManager` receiving and utilizing context from `ContextCore`.
    *   Test `LearningManager` successfully ingesting facts into `ContextCore`.
*   **Persistence:**
    *   Test saving and loading ContextCore state across restarts (for local backends).
*   **Summarization:**
    *   Test the `ContextSummarizer` producing coherent summaries of long texts/dialogues.

## 10. Potential Challenges & Mitigation

*   **Data Scalability:** Managing potentially terabytes of contextual data.
    *   **Mitigation:**
        *   Choose scalable backend technologies (Neo4j, Elasticsearch, Pinecone).
        *   Implement effective indexing and sharding strategies if needed.
        *   Aggressive summarization and archiving of old/less relevant data.
*   **Knowledge Representation Complexity:** Designing a flexible yet efficient ontology/schema for the CKG.
    *   **Mitigation:** Start with a simple, core ontology and allow it to evolve. Use flexible graph structures.
*   **Query Performance:** Ensuring low-latency retrieval for real-time dialogue.
    *   **Mitigation:** Optimized query patterns, caching of frequent queries/results, pre-computation of some contextual views.
*   **Relevance Ranking:** The "art" of ensuring the `get_relevant_context` method returns truly useful information.
    *   **Mitigation:** Hybrid retrieval methods (keyword, semantic, graph), learnable re-ranking models (future), user feedback loops.
*   **Cold Start Problem:** ContextCore will be empty for new users or new system deployments.
    *   **Mitigation:** Allow for initial knowledge base seeding. Design system to learn rapidly from initial interactions.
*   **Privacy and Security:** Storing potentially sensitive long-term user data.
    *   **Mitigation:**
        *   Implement robust access control based on user scope.
        *   Encryption at rest and in transit for sensitive fields.
        *   Provide users with mechanisms to view, export, and delete their data.
        *   Consider differential privacy techniques for aggregated insights.
*   **Consistency:** Managing consistency across distributed stores if different backends are used.
    *   **Mitigation:** Prioritize strong consistency for critical data; eventual consistency might be acceptable for some auxiliary context. Use transactional updates where possible.

## 11. Phased Implementation (High-Level)

1.  **Phase 1: Core Infrastructure & Local Stores.**
    *   Implement `ContextCoreManager` with basic `add_item`, `get_item`.
    *   Develop `NetworkXCKG`, local `FAISSVectorStore`, and `SQLiteDocumentStore`.
    *   Implement basic `ContextIngestionPipeline` (manual embedding for now).
    *   Basic `ContextQueryEngine` focusing on individual store queries.
2.  **Phase 2: DialogueManager Integration (Read-Only).**
    *   `DialogueManager` starts querying ContextCore for relevant context.
    *   Focus on retrieval and relevance ranking.
    *   Begin manual ingestion of key existing knowledge/lore into ContextCore.
3.  **Phase 3: LearningManager & ContentAnalyzer Integration (Write).**
    *   `LearningManager` and `ContentAnalyzerModule` start ingesting facts and analyzed content into ContextCore.
    *   Refine ingestion pipeline, entity/relationship extraction.
4.  **Phase 4: Summarization, Maintenance & Advanced Querying.**
    *   Implement `ContextSummarizer`.
    *   Develop context maintenance routines (archiving, etc.).
    *   Enhance `ContextQueryEngine` with hybrid retrieval and reranking.
5.  **Phase 5: Scalable Backends & Advanced Features.**
    *   Explore and implement integrations for scalable backends (Neo4j, Pinecone, Elasticsearch) if needed.
    *   Develop more advanced features like temporal reasoning, proactive context suggestion, etc.

This ContextCore module will be a cornerstone of the Unified-AI-Project's intelligence, enabling it to achieve a new level of understanding and continuity.
