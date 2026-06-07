# Service Catalog

Status: ✅ Active | 🟡 Partial Stub | ❌ Orphaned | 🗑️ Deprecated

## Core Services (initialized in lifespan.py)

| Service | File | Status | Init Method |
|---------|------|--------|-------------|
| `ChatService` | `services/chat_service.py` | ✅ | `get_angela_chat_service()` |
| `AngelaLLMService` | `services/llm/router.py` | ✅ | `get_llm_service()` |
| `BiologicalIntegrator` | `core/bio/biological_integrator.py` | ✅ | `bio.initialize()` |
| `WebSocketManager` | `services/websocket_manager.py` | ✅ | `broadcast_state_updates()` |
| `HotReloadService` | `services/hot_reload_service.py` | ✅ | `wiring.py:47` |

## ModuleManager Modules (discovered via modules/*/)

| Module | Directory | Status | Lifecycle |
|--------|-----------|--------|-----------|
| `vision_service` | `modules/vision_service/` | ✅ | init/start/stop |
| `audio_service` | `modules/audio_service/` | ✅ | init |
| `tactile_service` | `modules/tactile_service/` | ✅ | init |
| `google_drive_service` | `modules/google_drive_service/` | ✅ | init |
| `card_pipeline` | `modules/card_pipeline/` | ✅ | init/start/stop |
| `intent_registry` | `modules/intent_registry/` | ✅ | init |
| `chat_service` | `modules/chat_service/` | ✅ NEW | init/start/stop |
| `llm_service` | `modules/llm_service/` | ✅ NEW | init/start/stop |
| `hot_reload_service` | `modules/hot_reload_service/` | ✅ NEW | init/start/stop |
| `math_verifier` | `modules/math_verifier/` | ✅ NEW | init/start/stop |
| `resource_awareness_service` | `modules/resource_awareness_service/` | ✅ NEW | init/start/stop (also fixed `_load_profile`) |

## Intent Handlers

| Handler | File | Status | Intents |
|---------|------|--------|---------|
| `FileOperationHandler` | `services/handlers/file_operation_handler.py` | ✅ | file_op |
| `GoogleDriveHandler` | `services/handlers/google_drive_handler.py` | ✅ | google_drive |
| `WebSearchHandler` | `services/handlers/web_search_handler.py` | ✅ | web_search |
| `LearningHandler` | `services/handlers/learning_handler.py` | ✅ | learning |

## Plugin Handlers

| Handler | File | Status | Hooks |
|---------|------|--------|-------|
| `MessageLoggerHandler` | `core/plugin/handlers/message_logger.py` | ✅ | on_message, on_tick |

## Orphaned Services (no production import)

| Service | File | Status | Action |
|---------|------|--------|--------|
| `AIEditorService` | `services/ai_editor.py` | ❌ | Schedule removal |
| `AIEditorConfig` | `services/ai_editor_config.py` | ❌ | Schedule removal |
| `AIVirtualInputService` | `services/ai_virtual_input_service.py` | ❌ | Schedule removal |
| `BrainBridgeService` | `services/brain_bridge_service.py` | ❌ | Schedule removal |
| `OSContextService` | `services/os_context_service.py` | ❌ | Schedule removal |
| `angela_types` (TypeDefs) | `services/angela_types.py` | ❌ | Schedule removal |
| `api_models` (re-export) | `services/api_models.py` | ❌ | Schedule removal |

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

## AI Core Systems (NEW)

| System | File | Status |
|--------|------|--------|
| `ModelBus` | `ai/core/model_bus.py` | ✅ central registry + capability routing |
| `QueryClassifier` | `ai/core/query_classifier.py` | ✅ 8-domain rule-based classification |
| `TrainingCoordinator` | `ai/core/training_coordinator.py` | ✅ domain ownership + deconfliction |
| `ED3NEngine` | `ai/ed3n/ed3n_engine.py` | ✅ reflex + deep + SNN pipeline |
| `ED3NTrainer` | `ai/ed3n/ed3n_trainer.py` | ✅ Hebbian + topographic training |
| `GARDENEngine` | `ai/garden/garden_engine.py` | ✅ vector dictionary + TensorSNN |
| `ContinuousLearningPipeline` | `ai/ed3n/continuous_learning.py` | ✅ auto-growth + training loop |

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
