# Service Catalog

> **Last Updated**: 2026-06-25 — Full audit of services/ directory against actual imports

Status: ✅ Active | 🟡 Partial Stub | ❌ Orphaned | 🗑️ Deprecated

## Services (apps/backend/src/services/)

### Top-Level Services

| Service | File | Imported By | Status |
|---------|------|-------------|--------|
| `AngelaLLMService` | `services/angela_llm_service.py` | `main_api_server.py`, `digital_life_integrator.py`, `neuro_auto_selector.py`, `cli/repl.py` | ✅ wired |
| `AtlassianAPI` | `services/atlassian_api.py` | `main_api_server.py` | ✅ wired |
| `AudioService` | `services/audio_service.py` | `lifespan.py`, `chat_routes.py` | ✅ wired |
| `ChatService` | `services/chat_service.py` | `lifespan.py` | ✅ wired |
| `ConnectionSession` | `services/connection_session.py` | `lifespan.py`, `websocket_manager.py` | ✅ wired |
| `CrossModalQuality` | `services/cross_modal_quality.py` | `multimodal_routes.py` | ✅ wired |
| `CrossModalRouter` | `services/cross_modal_router.py` | `multimodal_routes.py` | ✅ wired |
| `MainAPIServer` | `services/main_api_server.py` | `cli/repl.py` | ✅ wired |
| `MathVerifier` | `services/math_verifier.py` | `chat_routes.py` (lazy) | ✅ wired |
| `MultimodalErrorRecovery` | `services/multimodal_error_recovery.py` | `multimodal_service.py` | ✅ wired |
| `MultimodalQualityMonitor` | `services/multimodal_quality_monitor.py` | `multimodal_service.py` | ✅ wired |
| `MultimodalService` | `services/multimodal_service.py` | `multimodal_routes.py`, `cross_modal_router.py`, `websocket_manager.py` | ✅ wired |
| `MultimodalStatePersistence` | `services/multimodal_state_persistence.py` | `multimodal_service.py` | ✅ wired |
| `ResourceAwarenessService` | `services/resource_awareness_service.py` | `neuro_auto_selector.py` | ✅ wired |
| `VisionService` | `services/vision_service.py` | `lifespan.py`, `chat_routes.py`, `image_encoder.py` | ✅ wired |
| `WeatherService` | `services/weather_service.py` | `proactive_interaction_system.py` | ✅ wired |
| `WebSocketManager` | `services/websocket_manager.py` | `lifespan.py`, `main_api_server.py` | ✅ wired |
| `BrainBridgeService` | `services/brain_bridge_service.py` | Nowhere (only in `verify_behavioral_impact.py`) | ❌ orphaned |
| `HotReloadService` | `services/hot_reload_service.py` | Nowhere (self-contained `get_hot_reload_service()`) | ❌ orphaned |
| `APIModels` | `services/api_models.py` | Nowhere (re-exports from `models.api_models`) | ❌ orphaned |

### services/handlers/ — Intent Handlers

| Handler | File | Status | Imported By |
|---------|------|--------|-------------|
| `FileOperationHandler` | `services/handlers/file_operation_handler.py` | ✅ | `handlers/__init__.py`, `llm/router.py` |
| `GoogleDriveHandler` | `services/handlers/google_drive_handler.py` | ✅ | `handlers/__init__.py` |
| `WebSearchHandler` | `services/handlers/web_search_handler.py` | ✅ | `handlers/__init__.py`, `llm/router.py` |
| `CodeExecutionHandler` | `services/handlers/code_execution_handler.py` | ✅ | `handlers/__init__.py`, `llm/router.py` |
| `SystemCommandHandler` | `services/handlers/system_command_handler.py` | ✅ | `handlers/__init__.py`, `llm/router.py` |
| `TaskManagerHandler` | `services/handlers/task_manager_handler.py` | ✅ | `handlers/__init__.py`, `llm/router.py` |
| `VisionHandler` | `services/handlers/vision_handler.py` | ✅ | `handlers/__init__.py`, `llm/router.py` |
| `LearningHandler` | `services/handlers/learning_handler.py` | ✅ | `handlers/__init__.py` |

### services/llm/ — LLM Routing & Providers

| Service | File | Status | Imported By |
|---------|------|--------|-------------|
| `LLMRouter` | `services/llm/router.py` | ✅ | `angela_llm_service.py`, `chat_service.py`, `memory_integration.py`, `lifespan.py` |
| `EmotionAnalyzer` | `services/llm/emotion_analyzer.py` | ✅ | `llm/router.py`, `chat_routes.py` |
| `MemoryIntegration` | `services/llm/memory_integration.py` | ✅ | `llm/router.py` |
| `PromptBuilder` | `services/llm/prompt_builder.py` | ✅ | `llm/router.py`, `angela_llm_service.py` |
| `LLMBackend` (registry) | `services/llm/providers/registry.py` | ✅ | `llm/router.py`, `core/interfaces/protocols.py` |
| Provider: `Anthropic` | `services/llm/providers/anthropic.py` | ✅ | `providers/__init__.py`, `llm/router.py` |
| Provider: `Google` | `services/llm/providers/google.py` | ✅ | `providers/__init__.py`, `llm/router.py` |
| Provider: `OpenAI` | `services/llm/providers/openai.py` | ✅ | `providers/__init__.py`, `llm/router.py` |
| Provider: `Ollama` | `services/llm/providers/ollama.py` | ✅ | `providers/__init__.py`, `llm/router.py` |
| Provider: `llama.cpp` | `services/llm/providers/llamacpp.py` | ✅ | `providers/__init__.py`, `llm/router.py` |
| Provider: `ED3N` | `services/llm/providers/ed3n.py` | ✅ | `providers/__init__.py`, `llm/router.py` |
| Provider: `GARDEN` | `services/llm/providers/garden.py` | ✅ | `providers/__init__.py`, `llm/router.py` |

### services/api/ — API Routes

| Service | File | Status | Imported By |
|---------|------|--------|-------------|
| `StateMatrixAPI` | `services/api/state_matrix_api.py` | ✅ | `main_api_server.py`, `core/autonomous/playground.py` |

### services/node_services/ — Node.js Services

| Service | File | Status | Notes |
|---------|------|--------|-------|
| `Server` | `services/node_services/server.js` | ❌ orphaned | No references in any Python or JS source |

### services/adapters/ — Empty directory

Directory exists but contains no files. Candidates for cleanup.

---

## ModuleManager Modules (discovered via modules/*/)

| Module | Directory | Status | Lifecycle |
|--------|-----------|--------|-----------|
| `vision_service` | `modules/vision_service/` | ✅ | init/start/stop |
| `audio_service` | `modules/audio_service/` | ✅ | init |
| `tactile_service` | `modules/tactile_service/` | ✅ | init |
| `google_drive_service` | `modules/google_drive_service/` | ✅ | init |
| `card_pipeline` | `modules/card_pipeline/` | ✅ | init/start/stop |
| `intent_registry` | `modules/intent_registry/` | ✅ | init |
| `chat_service` | `modules/chat_service/` | ✅ | init/start/stop |
| `llm_service` | `modules/llm_service/` | ✅ | init/start/stop |
| `hot_reload_service` | `modules/hot_reload_service/` | ✅ | init/start/stop |
| `math_verifier` | `modules/math_verifier/` | ✅ | init/start/stop |
| `resource_awareness_service` | `modules/resource_awareness_service/` | ✅ | init/start/stop |

## Plugin Handlers

| Handler | File | Status | Hooks |
|---------|------|--------|-------|
| `MessageLoggerHandler` | `core/plugin/handlers/message_logger.py` | ✅ | on_message, on_tick |

## Orphaned Services (no production import)

| Service | File | Status | Action |
|---------|------|--------|--------|
| `BrainBridgeService` | `services/brain_bridge_service.py` | ❌ | Schedule removal (only referenced in `verify_behavioral_impact.py`) |
| `APIModels` (re-export) | `services/api_models.py` | ❌ | Schedule removal (empty re-export of `models.api_models`) |

## Deprecated Agents

| Agent | Directory | Status | Action |
|-------|-----------|--------|--------|
| AlignedBaseAgent | `agents/legacy/` | 🗑️ | DEPRECATED header added |
| collaboration_demo_agent | `agents/legacy/` | 🗑️ | DEPRECATED header added |
| monitoring_demo_agent | `agents/legacy/` | 🗑️ | DEPRECATED header added |
| registry_demo_agent | `agents/legacy/` | 🗑️ | DEPRECATED header added |
| aligned_agent_example | `agents/examples/` | 🗑️ | DEPRECATED header added |

## AI Agent Specialized (active)

| Agent | File | Status |
|-------|------|--------|
| `ImageGenerationAgent` | `ai/agents/specialized/image_generation_agent.py` | 🟡 stub |
| `AudioProcessingAgent` | `ai/agents/specialized/audio_processing_agent.py` | 🟡 stub |
| `WebSearchAgent` | `ai/agents/specialized/web_search_agent.py` | 🟡 stub |
| `KnowledgeGraphAgent` | `ai/agents/specialized/knowledge_graph_agent.py` | 🟡 stub |
| `VisionProcessingAgent` | `ai/agents/specialized/vision_processing_agent.py` | 🟡 stub |
| `NLPProcessingAgent` | `ai/agents/specialized/nlp_processing_agent.py` | 🟡 stub |
| `CodeUnderstandingAgent` | `ai/agents/specialized/code_understanding_agent.py` | 🟡 stub |
| `CreativeWritingAgent` | `ai/agents/specialized/creative_writing_agent.py` | ✅ |
| `DataAnalysisAgent` | `ai/agents/specialized/data_analysis_agent.py` | ✅ |
| `FantasyDMAgent` | `ai/agents/specialized/fantasy_dm_agent.py` | ✅ |
| `PlanningAgent` | `ai/agents/specialized/planning_agent.py` | ✅ |

## AI Core Systems

| System | File | Status | Wiring |
|--------|------|--------|--------|
| `ModelBus` | `ai/core/model_bus.py` | ✅ central registry + capability routing; 34 tests | GARDENBackend registered at priority 6; fallback Tier 1; hot-reload re-registers; 7 routing paths |
| `QueryClassifier` | `ai/core/query_classifier.py` | ✅ 16 QueryTypes v2 (FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO, OPINION) | Feeds into ModelBus capability routing |
| `TrainingCoordinator` | `ai/core/training_coordinator.py` | ✅ domain ownership + deconfliction | Manages SequenceTrainer + JointTrainer lifecycle |
| `ED3NEngine` | `ai/ed3n/ed3n_engine.py` | ✅ reflex + deep + SNN pipeline + continuous learning + synonym expansion | Wired to GARDENBackend via `garden_aware: bool` |
| `ED3NTrainer` | `ai/ed3n/ed3n_trainer.py` | ✅ Hebbian + topographic + SequenceTrainer + JointTrainer | Called by `scripts/train_pipeline.py` (steps 4f/4g); wired to 13 data sources (53,654 samples) |
| `GARDENEngine` | `ai/garden/garden_engine.py` | ✅ 5-stage pipeline (emotion→reflex→multi-step→vector→SNN) + ChromaDB encoder | Connected to AngelaLLMService for emotional context; 3 active routing paths to chat flow |
| `ContinuousLearningPipeline` | `ai/ed3n/continuous_learning.py` | ✅ auto-growth + training loop | Wired to ModelBus for capability publication |

## Integration Services

| Service | File | Status |
|---------|------|--------|
| `GoogleDriveService` | `integrations/google_drive_service.py` | ✅ |
| `AtlassianBridge` | `integrations/atlassian_bridge.py` | 🟡 skeleton |
| `EnhancedRovoDevConnector` | `integrations/enhanced_rovo_dev_connector.py` | 🟡 skeleton |
| `OSBridgeAdapter` | `integrations/os_bridge_adapter.py` | ✅ |
| `WebSearchTool` | `core/tools/web_search_tool.py` | ✅ |

## Config/Infrastructure

| Component | File | Status |
|-----------|------|--------|
| `TieredConfigLoader` | `core/system/config/tiered_loader.py` | ✅ |
| `MagicNumbers` | `core/system/config/magic_numbers.py` | ✅ |
| `IntentRegistry` | `core/intent_registry.py` | ✅ |
| `ModuleManager` | `core/system/module_manager/` | ✅ |
