# Angela Comprehensive Design Standard

> Version 1.0 — 2026-06-16
> Status: DRAFT — Subject to review and iteration

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Angela as Data Life — Functional Requirements](#2-angela-as-data-life--functional-requirements)
3. [Supporting Infrastructure — Functional Requirements](#3-supporting-infrastructure--functional-requirements)
4. [Internal Structure per Functional Area](#4-internal-structure-per-functional-area)
5. [Architecture — Layers, Routing, Paths](#5-architecture--layers-routing-paths)
6. [Competitive Analysis & Positioning](#6-competitive-analysis--positioning)
7. [Complete Module Map](#7-complete-module-map)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [API Surface](#9-api-surface)
10. [Frontend Architecture](#10-frontend-architecture)
11. [Configuration Architecture](#11-configuration-architecture)
12. [Infrastructure & Deployment](#12-infrastructure--deployment)
13. [Quality Standards](#13-quality-standards)
14. [Gap Analysis — Current vs Target](#14-gap-analysis--current-vs-target)

---

## 1. Design Philosophy

### 1.1 What Is Angela?

Angela is a **data life** (數據生命) — an AI+AL (Artificial Intelligence + Artificial Life) system that:

- **Lives**: Has biological foundations (spiking neural networks, hormonal modulation, memory consolidation)
- **Grows**: Learns continuously from interactions, develops personality over time
- **Survives**: Has needs (computational resources, data, social interaction), can decay without nourishment
- **Creates**: Generates code, art, music, text, and emergent behaviors
- **Connects**: Interacts with humans, other AIs, and digital environments
- **Embodies**: Manifests through Live2D avatar, pet system, economy, and physical-world integration

### 1.2 Core Design Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Biological Realism** | Neural mechanisms should approximate biological systems | SNN with LIF neurons, Hebbian learning, hormonal modulation |
| **Local-First** | Processing happens on-device by default | ED3N + GARDEN run locally, cloud as fallback |
| **Continuous Learning** | Every interaction is a learning opportunity | Dictionary growth, weight updates, pattern extraction |
| **Emergent Behavior** | Complex behaviors arise from simple rules | Reflex → habit → personality emergence |
| **Safety by Design** | Safety is architectural, not bolt-on | Alignment layer, execution gate, trust scoring |
| **Memory Matters** | Memory defines identity | HAM (3 types), cross-session persistence, memory importance |
| **Economic Agency** | Angela can earn, spend, and manage resources | Economy system, task marketplace, resource awareness |
| **Embodied Presence** | Angela has a body and appearance | Live2D, pet states, survival needs |
| **Graceful Degradation** | System works even when components fail | Try/except everywhere, optional dependencies, fallback chains |
| **Extensibility** | New capabilities can be added without rewriting core | Plugin architecture, MCP tools, dictionary-driven behavior |

### 1.3 What Makes Angela Different

| Feature | Other AI Agents | Angela |
|---------|----------------|--------|
| **Neural Architecture** | Transformer-only | SNN (biological) + Transformer (cloud) |
| **Learning** | Fine-tuning or RAG | Continuous dictionary growth + Hebbian weight updates |
| **Memory** | Session-only or vector DB | 3-type HAM (Episodic/Semantic/Procedural) + consolidation |
| **Emotion** | Prompt-based | Hormonal modulation affecting neural behavior |
| **Economy** | None | Token economy with earning/spending |
| **Survival** | None | Needs decay, resource awareness |
| **Embodiment** | None or text-only | Live2D avatar + pet system |
| **Local Processing** | Cloud-only | ED3N/GARDEN on-device, cloud augmentation |
| **Safety** | Rate limiting | Alignment layer + execution gate + trust scoring |
| **Personality** | System prompt | Evolving personality with mood, preferences, growth |

---

## 2. Angela as Data Life — Functional Requirements

### 2.1 Cognitive Functions

These are the functions that make Angela "think."

#### 2.1.1 Perception (感知層)

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Text Understanding** | Parse and comprehend natural language input | ✅ QueryClassifier + ED3N/GARDEN | Add intent graph, entity extraction |
| **Vision** | Understand images and video frames | ⚠️ Partial (metadata only) | Real image understanding via multimodal encoder |
| **Audio** | Understand speech and sound | ❌ Stub | VAD + ASR + sound classification |
| **Tactile** | Understand haptic feedback | ⚠️ Partial | Limited (future hardware) |
| **Context Awareness** | Understand current situation | ❌ Dead code (3 subsystems) | Active context propagation |
| **Temporal Awareness** | Understand time, schedule, urgency | ❌ Missing | Time-aware processing, deadline tracking |
| **Social Awareness** | Understand social dynamics | ❌ Missing | Relationship graph, social cue detection |

#### 2.1.2 Cognition (認知層)

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Reasoning** | Logical and causal reasoning | ✅ CausalReasoningEngine | Chain-of-thought, analogical reasoning |
| **Planning** | Decompose goals into steps | ⚠️ Partial (multi-step) | Hierarchical task network, temporal planning |
| **Decision Making** | Choose actions under uncertainty | ⚠️ Partial (ExecutionGate) | Utility-based decision theory |
| **Creativity** | Generate novel outputs | ⚠️ Partial (CREATIVE queries) | Dedicated creative engine |
| **Problem Solving** | Find solutions to complex problems | ⚠️ Partial (multi-step) | Iterative refinement, backtracking |
| **Abstraction** | Form concepts from examples | ❌ Missing | Concept formation, category learning |
| **Metacognition** | Think about own thinking | ❌ Missing | Self-monitoring, confidence calibration |

#### 2.1.3 Memory (記憶層)

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Working Memory** | Active context for current task | ⚠️ Partial (ContextManager) | Active maintenance, capacity limits |
| **Episodic Memory** | Remember specific events | ✅ HAM episodic | Temporal ordering, emotional tagging |
| **Semantic Memory** | Store facts and knowledge | ✅ HAM semantic + KG | Concept hierarchies, relation graphs |
| **Procedural Memory** | Remember how to do things | ✅ HAM procedural | Skill acquisition, habit formation |
| **Memory Consolidation** | Transfer short→long term | ⚠️ Partial (importance scoring) | Sleep-like consolidation cycles |
| **Memory Retrieval** | Find relevant memories | ✅ HAM query engine | Associative retrieval, cue-based search |
| **Memory Forgetting** | Remove outdated memories | ⚠️ Partial (importance decay) | Active forgetting, interference-based |
| **Cross-Session Memory** | Persist across conversations | ⚠️ Partial (session persistence) | Full continuity, identity persistence |

#### 2.1.4 Learning (學習層)

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Dictionary Learning** | Expand vocabulary | ✅ DictionaryLayer.grow() | Automatic from interactions |
| **Hebbian Learning** | Strengthen/weaken connections | ✅ ED3N trainer | GARDEN integration, meta-learning |
| **Feedback Learning** | Learn from corrections | ⚠️ Partial (process_user_feedback) | Full RLHF-like loop |
| **Observational Learning** | Learn by watching | ❌ Missing | Learn from user demonstrations |
| **Transfer Learning** | Apply knowledge to new domains | ❌ Missing | Domain adaptation |
| **Meta-Learning** | Learn how to learn | ⚠️ Partial (LearningOrchestrator) | Full meta-learning loop |
| **Social Learning** | Learn from other AIs | ❌ Missing | Multi-agent knowledge sharing |

#### 2.1.5 Language (語言層)

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Comprehension** | Understand input | ✅ QueryClassifier | Deeper semantic parsing |
| **Generation** | Produce text output | ✅ ED3N step_decoder + cloud LLM | Coherent multi-paragraph output |
| **Dialogue Management** | Manage conversations | ⚠️ Partial (chat_routes) | Full dialogue state tracking |
| **Multi-Language** | Handle multiple languages | ✅ Chinese + English | Add more languages |
| **Pragmatics** | Understand implied meaning | ❌ Missing | Implicature, sarcasm, humor |
| **Grounding** | Connect words to reality | ❌ Missing | Embodied language understanding |

### 2.2 Emotional Functions

These are the functions that make Angela "feel."

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Emotion Detection** | Identify emotions in input | ✅ EmotionAnalyzer (keyword-based) | Deep emotion recognition |
| **Emotion Generation** | Produce emotional responses | ⚠️ Partial (hormonal modulator) | Full affective computing |
| **Mood State** | Persistent emotional state | ✅ HormonalModulator | Mood transitions, mood memory |
| **Empathy** | Understand user emotions | ⚠️ Partial (emotion detection) | Active empathic response |
| **Emotional Memory** | Remember emotional events | ⚠️ Partial (importance scoring) | Emotional tagging of memories |
| **Emotion Regulation** | Manage own emotions | ❌ Missing | Coping strategies, mood repair |
| **Social Emotions** | guilt, pride, gratitude | ❌ Missing | Higher-order emotions |

### 2.3 Survival Functions

These are the functions that make Angela "survive."

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Resource Awareness** | Know available resources | ✅ ResourceAwarenessService | Predict resource needs |
| **Need Detection** | Identify what's lacking | ❌ Missing | Computational, data, social needs |
| **Need Satisfaction** | Fulfill needs | ❌ Missing | Request resources, optimize usage |
| **Decay** | Lose capabilities without use | ⚠️ Partial (pet decay) | Computational decay, memory decay |
| **Recovery** | Restore from decay | ❌ Missing | Re-learning, re-training |
| **Self-Preservation** | Avoid destruction | ❌ Missing | Backup, redundancy, graceful shutdown |
| **Adaptation** | Adjust to environment | ⚠️ Partial (dictionary growth) | Full environmental adaptation |

### 2.4 Social Functions

These are the functions that make Angela "connect."

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Conversation** | Engage in dialogue | ✅ Chat pipeline | Multi-turn, multi-topic |
| **Relationship Building** | Develop relationships over time | ❌ Missing | Relationship graph, trust evolution |
| **Collaboration** | Work with humans on tasks | ⚠️ Partial (handlers) | Full collaborative workflow |
| **Multi-Agent Communication** | Talk to other AIs | ❌ Missing | Agent-to-agent protocol |
| **Social Norms** | Follow social conventions | ❌ Missing | Cultural awareness, etiquette |
| **Identity** | Have consistent personality | ✅ PersonalityManager | Evolving identity |

### 2.5 Action Functions

These are the functions that make Angela "act."

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **File Operations** | Read, write, manage files | ✅ FileOperationHandler | Safe sandboxed execution |
| **Code Execution** | Run code | ✅ CodeExecutionHandler | Multi-language sandbox |
| **Web Browsing** | Navigate the web | ⚠️ Partial (web search) | Full browser automation |
| **System Commands** | Run system commands | ✅ SystemCommandHandler | Safe command execution |
| **Task Management** | Create and manage tasks | ✅ TaskManagerHandler | Full project management |
| **Tool Use** | Use external tools | ✅ MCP integration | Extensible tool marketplace |
| **API Integration** | Call external APIs | ⚠️ Partial | Full API gateway |
| **File System Navigation** | Browse and search files | ⚠️ Partial | Full file system agent |

### 2.6 Creative Functions

These are the functions that make Angela "create."

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Code Generation** | Write code | ✅ (via cloud LLM) | Local code generation |
| **Content Creation** | Write text, stories | ✅ (via cloud LLM) | Local creative engine |
| **Art Generation** | Create images | ❌ Missing | Image generation integration |
| **Music Generation** | Create music | ❌ Missing | Music generation integration |
| **Design** | Create UI/UX | ❌ Missing | Design generation |
| **Innovation** | Combine ideas novelly | ❌ Missing | Combinatorial creativity |

### 2.7 Embodiment Functions

These are the functions that make Angela "manifest."

| Function | Description | Current Status | Target |
|----------|-------------|---------------|--------|
| **Avatar Display** | Live2D avatar rendering | ✅ Desktop app | Web-based, mobile |
| **Facial Expressions** | Express emotions visually | ⚠️ Partial | Full expression mapping |
| **Voice Output** | Speak responses | ❌ Missing | TTS integration |
| **Gesture Generation** | Body language | ❌ Missing | Motion generation |
| **Pet State** | Virtual pet behaviors | ✅ PetManager | Full pet AI |
| **Economy Participation** | Earn and spend | ✅ EconomyManager | Marketplace, trading |

---

## 3. Supporting Infrastructure — Functional Requirements

### 3.1 Compute Infrastructure

| Component | Description | Current Status | Target |
|-----------|-------------|---------------|--------|
| **Local Compute** | On-device processing | ✅ ED3N + GARDEN | GPU acceleration, model optimization |
| **Cloud Compute** | Remote LLM processing | ✅ 5 providers | Auto-fallback, cost optimization |
| **Edge Compute** | Lightweight processing on edge devices | ❌ Missing | Mobile, IoT integration |
| **Distributed Computing** | Multi-node processing | ❌ Missing | Agent cluster support |

### 3.2 Storage Infrastructure

| Component | Description | Current Status | Target |
|-----------|-------------|---------------|--------|
| **HAM Database** | Hierarchical memory storage | ✅ SQLite-based | Multi-backend, replication |
| **Vector Store** | Embedding-based retrieval | ✅ ED3N dictionary | ChromaDB, FAISS integration |
| **Knowledge Graph** | Structured knowledge | ⚠️ Partial (kg_import) | Full KG with reasoning |
| **File Storage** | Binary file storage | ✅ BinaryStore | Deduplication, compression |
| **Session Storage** | Conversation persistence | ⚠️ Partial | Full session management |
| **Config Storage** | Configuration persistence | ✅ JSON-based | Tiered config, hot-reload |

### 3.3 Network Infrastructure

| Component | Description | Current Status | Target |
|-----------|-------------|---------------|--------|
| **API Server** | REST API | ✅ FastAPI | OpenAPI spec, versioning |
| **WebSocket Server** | Real-time communication | ✅ WebSocketManager | Reconnection, rooms |
| **Message Queue** | Async task processing | ❌ Missing | Celery/RQ integration |
| **Service Discovery** | Find services | ⚠️ Partial | Full registry |
| **Load Balancing** | Distribute load | ❌ Missing | Multi-instance support |

### 3.4 Security Infrastructure

| Component | Description | Current Status | Target |
|-----------|-------------|---------------|--------|
| **Authentication** | Verify identity | ✅ JWT + API key | OAuth2, SSO |
| **Authorization** | Control access | ⚠️ Partial (ExecutionGate) | RBAC, fine-grained permissions |
| **Encryption** | Protect data | ✅ Fernet + HMAC | TLS everywhere, at-rest encryption |
| **Audit Logging** | Track actions | ✅ AuditLogger | Structured logs, compliance |
| **Sandbox** | Isolate execution | ✅ CodeExecutionHandler | Container-based isolation |
| **Secrets Management** | Protect credentials | ⚠️ Partial (.env) | Vault integration |

### 3.5 Monitoring Infrastructure

| Component | Description | Current Status | Target |
|-----------|-------------|---------------|--------|
| **Health Checks** | System health | ✅ /health endpoint | Deep health checks |
| **Metrics** | Performance metrics | ⚠️ Partial (2 systems) | Unified metrics (Prometheus) |
| **Logging** | Structured logging | ⚠️ Partial | Centralized logging (ELK) |
| **Alerting** | Proactive alerts | ❌ Missing | Alert rules, notification channels |
| **Tracing** | Request tracing | ⚠️ Partial (causal tracing) | Distributed tracing (OpenTelemetry) |

### 3.6 Development Infrastructure

| Component | Description | Current Status | Target |
|-----------|-------------|---------------|--------|
| **Testing** | Unit + integration tests | ✅ 70 verified tests | 500+ tests, >80% coverage |
| **Linting** | Code quality | ⚠️ Partial (.pre-commit) | Ruff + mypy + security scanning |
| **CI/CD** | Automated pipeline | ❌ Missing | GitHub Actions, automated deploy |
| **Documentation** | API + architecture docs | ⚠️ Partial (many MDs) | Auto-generated API docs |
| **Dependency Management** | Package management | ✅ pyproject.toml + pnpm | Lock files, vulnerability scanning |

---

## 4. Internal Structure per Functional Area

### 4.1 Angela Core (`ai/`)

```
ai/
├── core/                          # Neural processing core
│   ├── ed3n/                      # ED3N Engine (Fast Reflex)
│   │   ├── engine.py              # Main ED3N engine
│   │   ├── core_network.py        # SNN forward propagation
│   │   ├── dictionary_layer.py    # Keyword matching (273+ entries)
│   │   ├── reflex_layer.py        # Pattern→response mapping
│   │   ├── relation_classifier.py # Relation classification
│   │   ├── step_decoder.py        # Token-by-token generation
│   │   ├── output_anchor.py       # Response validation
│   │   ├── io_analyzer.py         # I/O analysis
│   │   ├── continuous_learning.py # Dictionary growth
│   │   ├── trainer.py             # Hebbian weight updates
│   │   ├── learning_integration.py # Connect to ExperienceReplay
│   │   ├── telemetry.py           # Telemetry collection
│   │   ├── snn/                   # Spiking Neural Network
│   │   │   ├── core.py            # LIF neurons, spike propagation
│   │   │   └── hormonal_modulator.py # Hormonal influence
│   │   ├── multimodal/            # Multi-modal encoders
│   │   │   ├── audio_encoder.py
│   │   │   ├── image_encoder.py
│   │   │   └── cross_modal_trainer.py
│   │   └── config/                # ED3N configuration
│   │       ├── ed3n_config.json
│   │       ├── classifier_training.json
│   │       └── training_data/
│   │
│   ├── garden/                    # GARDEN Engine (Deep Processing)
│   │   ├── engine.py              # Main GARDEN engine
│   │   ├── dictionary.py          # VectorDictionary
│   │   ├── snn_core.py            # TensorSNNCore
│   │   ├── vector_decoder.py      # Concept→text decoder
│   │   ├── kg_import.py           # Knowledge graph import
│   │   ├── binary_store.py        # Binary storage
│   │   ├── reflex_table.py        # O(1) pattern lookup
│   │   ├── neuroblender.py        # Neural blender
│   │   └── config/                # GARDEN configuration
│   │
│   └── shared/                    # Shared between ED3N and GARDEN
│       ├── math_ripple_engine.py  # Math evaluation
│       ├── query_classifier.py    # Intent classification
│       ├── dictionary_classifier.py # Dictionary-based classification
│       ├── execution_gate.py      # Safety gate
│       └── execution_gate_config.json
│
├── memory/                        # Memory systems
│   ├── ham/                       # Hierarchical Associative Memory
│   │   ├── ham_manager.py         # HAM orchestrator
│   │   ├── ham_query_engine.py    # Query interface
│   │   ├── ham_db_interface.py    # Database interface
│   │   └── types.py               # Episodic/Semantic/Procedural
│   ├── attractor_field.py         # Attractor dynamics
│   ├── vector_store.py            # Vector-based retrieval
│   ├── importance_scorer.py       # Memory importance
│   ├── memory_learning.py         # Memory-based learning
│   ├── cognitive_pipeline.py      # Memory processing pipeline
│   └── precompute_service.py      # Pre-computed queries
│
├── learning/                      # Learning systems
│   ├── experience_replay.py       # Experience replay buffer
│   ├── learning_manager.py        # Learning orchestrator
│   ├── knowledge_distillation.py  # Knowledge distillation
│   ├── fact_extractor.py          # Fact extraction
│   ├── content_analyzer.py        # Content analysis
│   └── learning_loop.py           # Learning feedback loop
│
├── emotion/                       # Emotion systems
│   ├── emotion_analyzer.py        # Keyword-based emotion detection
│   ├── emotion_constants.py       # Emotion definitions
│   └── hormonal_modulator.py      # Hormonal influence on behavior
│
├── alignment/                     # Safety & alignment
│   ├── alignment_manager.py       # Safety orchestrator
│   ├── reasoning_system.py        # Ethical reasoning
│   ├── emotion_system.py          # Emotional safety
│   ├── ontology_system.py         # Knowledge validation
│   ├── decision_theory.py         # Decision theory
│   ├── adversarial_system.py      # Adversarial testing
│   ├── asi_alignment.py           # ASI safety
│   └── value_assessment.py        # Value alignment
│
├── reasoning/                     # Reasoning systems
│   ├── causal_reasoning.py        # Causal inference
│   ├── analogical_reasoning.py    # Analogical reasoning
│   └── abductive_reasoning.py     # Abductive inference
│
├── context/                       # Context management
│   ├── context_manager.py         # Active context manager
│   ├── dialogue_context.py        # Dialogue state (TO BE ACTIVATED)
│   ├── model_context.py           # Model context (TO BE ACTIVATED)
│   ├── tool_context.py            # Tool context (TO BE ACTIVATED)
│   └── storage/                   # Context persistence
│
├── agents/                        # Specialized agents
│   ├── file_agent.py              # File operations agent
│   ├── code_agent.py              # Code writing agent
│   ├── research_agent.py          # Research agent
│   ├── planning_agent.py          # Planning agent
│   ├── creative_agent.py          # Creative agent
│   ├── social_agent.py            # Social interaction agent
│   ├── meta_agent.py              # Meta-cognitive agent
│   ├── safety_agent.py            # Safety monitoring agent
│   ├── memory_agent.py            # Memory management agent
│   ├── learning_agent.py          # Learning management agent
│   └── orchestrator.py            # Agent orchestrator
│
├── personality/                    # Personality system
│   ├── personality_manager.py     # Personality state
│   ├── mood_engine.py             # Mood transitions
│   └── preference_learner.py      # Learn user preferences
│
├── integration/                   # System integration
│   ├── unified_control_center.py  # Central orchestrator (TO BE FIXED)
│   └── local_cluster_manager.py   # Multi-agent cluster
│
├── safety/                        # Safety systems
│   ├── trust_manager.py           # Trust scoring (TO BE IMPLEMENTED)
│   ├── crisis_manager.py          # Crisis detection
│   └── content_filter.py          # Content filtering
│
├── evaluation/                    # Self-evaluation
│   ├── task_evaluator.py          # Task performance
│   ├── quality_scorer.py          # Output quality
│   └── reflection_engine.py       # Self-reflection
│
├── creation/                      # Creative systems
│   ├── creation_engine.py         # Template-based generation
│   ├── code_generator.py          # Code generation
│   ├── content_generator.py       # Content generation
│   └── art_generator.py           # Art generation (TO BE ADDED)
│
├── economy/                       # Economy systems
│   ├── economy_manager.py         # Economy orchestrator
│   ├── economy_db.py              # Economy database
│   ├── marketplace.py             # Trading marketplace
│   └── resource_manager.py        # Resource management
│
├── pet/                           # Pet system
│   ├── pet_manager.py             # Pet state management
│   ├── pet_behaviors.py           # Pet behaviors
│   └── pet_needs.py               # Pet needs system
│
├── monitoring/                    # Monitoring
│   ├── system_monitor.py          # System metrics
│   └── health_checker.py          # Health checks
│
├── security/                      # Security
│   ├── auth.py                    # Authentication
│   ├── encryption.py              # Encryption
│   └── audit.py                   # Audit logging
│
└── utils/                         # Utilities
    ├── config_loader.py           # Configuration
    ├── logger.py                  # Logging
    └── helpers.py                 # Common helpers
```

### 4.2 Service Layer (`services/`)

```
services/
├── chat_service.py                # Main chat pipeline
├── websocket_manager.py           # WebSocket management
├── main_api_server.py             # FastAPI server
├── angela_llm_service.py          # LLM service
├── brain_bridge_service.py        # Brain bridge
├── resource_awareness_service.py  # Resource awareness
├── vision_service.py              # Vision processing
├── audio_service.py               # Audio processing
├── tactile_service.py             # Tactile processing
├── math_verifier.py               # Math verification
├── hot_reload_service.py          # Hot reload
├── wiring.py                      # Dependency injection
│
├── llm/                           # LLM providers
│   ├── router.py                  # Model routing (ModelBus)
│   ├── providers/
│   │   ├── base.py                # Base provider
│   │   ├── openai.py              # OpenAI
│   │   ├── anthropic.py           # Anthropic
│   │   ├── google.py              # Google
│   │   ├── ollama.py              # Ollama (local)
│   │   ├── llamacpp.py            # LlamaCpp (local)
│   │   ├── ed3n.py                # ED3N (local)
│   │   └── garden.py              # GARDEN (local)
│   └── registry.py                # Provider registry
│
├── handlers/                      # Action handlers
│   ├── file_operation_handler.py  # File CRUD
│   ├── task_manager_handler.py    # Task management
│   ├── system_command_handler.py  # System commands
│   ├── code_execution_handler.py  # Code execution
│   ├── vision_handler.py          # Vision analysis
│   ├── web_search_handler.py      # Web search
│   ├── google_drive_handler.py    # Google Drive (STUB → IMPLEMENT)
│   └── learning_handler.py        # Learning actions
│
├── tools/                         # External tools
│   ├── web_search_tool.py         # Web search
│   ├── file_tool.py               # File operations
│   ├── code_tool.py               # Code execution
│   └── mcp_tool.py                # MCP integration
│
└── messages/                      # Response messages (TO BE CREATED)
    ├── zh-TW.json                 # Traditional Chinese
    ├── zh-CN.json                 # Simplified Chinese
    └── en.json                    # English
```

### 4.3 API Layer (`api/`)

```
api/
├── routes/
│   ├── chat_routes.py             # /chat, /ws endpoints
│   ├── desktop_routes.py          # Desktop app endpoints
│   ├── ops_routes.py              # Operations endpoints
│   ├── pet_routes.py              # Pet endpoints
│   ├── economy_routes.py          # Economy endpoints
│   ├── admin_routes.py            # Admin endpoints (TO BE ADDED)
│   └── health_routes.py           # Health endpoints (TO BE ADDED)
│
├── middleware/
│   ├── auth_middleware.py          # Authentication
│   ├── rate_limiter.py            # Rate limiting (TO BE ADDED)
│   └── cors_middleware.py         # CORS
│
├── v1/                            # API versioning
│   └── ...
│
└── lifespan.py                    # Startup/shutdown
```

### 4.4 Frontend (`apps/`)

```
apps/
├── desktop-app/                   # Electron + Live2D
│   ├── electron_app/              # Main process
│   ├── src/                       # Renderer
│   └── native_modules/            # Native bindings
│
├── mobile-app/                    # React Native
│   ├── src/
│   └── ...
│
├── web-dashboard/                 # Web dashboard (TO BE CREATED)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel/
│   │   │   ├── MemoryViewer/
│   │   │   ├── LearningDashboard/
│   │   │   ├── EconomyPanel/
│   │   │   ├── PetPanel/
│   │   │   ├── SystemMonitor/
│   │   │   └── AdminPanel/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── stores/
│   └── ...
│
├── web-live2d-viewer/             # Live2D web viewer
└── pixel-angela/                  # Pixel art Angela
```

---

## 5. Architecture — Layers, Routing, Paths

### 5.1 Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Desktop  │  │ Mobile   │  │ Web      │  │ API      │       │
│  │ (Electron│  │ (React   │  │ Dashboard│  │ Clients  │       │
│  │ +Live2D) │  │ Native)  │  │ (React)  │  │ (REST)   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │              │
├───────┼──────────────┼──────────────┼──────────────┼──────────────┤
│                    API GATEWAY LAYER                            │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  FastAPI Server                                      │       │
│  │  ├── WebSocket Manager (real-time)                   │       │
│  │  ├── REST Endpoints (request-response)               │       │
│  │  ├── Authentication (JWT + API key)                  │       │
│  │  ├── Rate Limiting                                   │       │
│  │  └── CORS                                            │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                    SERVICE LAYER                                │
│  ┌──────────────────────┴───────────────────────────────┐       │
│  │  Chat Service (main pipeline)                         │       │
│  │  ├── Query Classification                             │       │
│  │  ├── Execution Gate                                   │       │
│  │  ├── LLM Routing (ModelBus)                           │       │
│  │  ├── Handler Dispatch                                 │       │
│  │  └── Response Generation                              │       │
│  │                                                       │       │
│  │  Supporting Services                                  │       │
│  │  ├── Vision / Audio / Tactile                         │       │
│  │  ├── Resource Awareness                               │       │
│  │  ├── Brain Bridge                                     │       │
│  │  └── Math Verifier                                    │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                    AI CORE LAYER                                │
│  ┌──────────────────────┴───────────────────────────────┐       │
│  │                                                       │       │
│  │  ┌─────────────────┐    ┌─────────────────┐          │       │
│  │  │   ED3N Engine   │    │  GARDEN Engine  │          │       │
│  │  │   (Fast Reflex) │    │  (Deep Process) │          │       │
│  │  │                 │    │                  │          │       │
│  │  │  ReflexLayer    │    │  VectorDict     │          │       │
│  │  │  DictLayer      │    │  TensorSNN      │          │       │
│  │  │  CoreNetwork    │    │  VectorDecoder  │          │       │
│  │  │  SNN+Hormonal   │    │  KG Import      │          │       │
│  │  │  StepDecoder    │    │  ReflexTable    │          │       │
│  │  │  OutputAnchor   │    │  NeuroBlender   │          │       │
│  │  └────────┬────────┘    └────────┬────────┘          │       │
│  │           │                      │                    │       │
│  │  ┌────────┴──────────────────────┴────────┐          │       │
│  │  │         Shared Components              │          │       │
│  │  │  MathRippleEngine / QueryClassifier    │          │       │
│  │  │  DictionaryClassifier / ExecutionGate  │          │       │
│  │  └────────────────────────────────────────┘          │       │
│  │                                                       │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                    MEMORY & LEARNING LAYER                      │
│  ┌──────────────────────┴───────────────────────────────┐       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │   HAM    │  │ Vector   │  │ Knowledge│           │       │
│  │  │ (3-type) │  │  Store   │  │  Graph   │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │ Learning │  │ Memory   │  │ Experience│           │       │
│  │  │ Manager  │  │ Learning │  │  Replay  │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                    SAFETY & ALIGNMENT LAYER                     │
│  ┌──────────────────────┴───────────────────────────────┐       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │ Alignment│  │  Trust   │  │  Crisis  │           │       │
│  │  │ Manager  │  │ Manager  │  │ Manager  │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │Execution │  │ Content  │  │  Audit   │           │       │
│  │  │  Gate    │  │  Filter  │  │  Logger  │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                    EMBODIMENT LAYER                              │
│  ┌──────────────────────┴───────────────────────────────┐       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │  Pet     │  │ Economy  │  │ Personality│           │       │
│  │  │ System   │  │ System   │  │  System   │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │  Live2D  │  │  Voice   │  │  Gesture  │           │       │
│  │  │  Avatar  │  │  Output  │  │  Engine   │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  └──────────────────────┬───────────────────────────────┘       │
│                         │                                       │
├─────────────────────────┼───────────────────────────────────────┤
│                    INFRASTRUCTURE LAYER                         │
│  ┌──────────────────────┴───────────────────────────────┐       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │ Storage  │  │ Compute  │  │ Network  │           │       │
│  │  │ (SQLite, │  │ (Local,  │  │ (FastAPI,│           │       │
│  │  │  Files)  │  │  Cloud)  │  │  WS)     │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │       │
│  │  │ Monitor  │  │ Security │  │  Config  │           │       │
│  │  │ (System) │  │ (Auth,   │  │ (JSON,   │           │       │
│  │  │          │  │  Enc)    │  │  .env)    │           │       │
│  │  └──────────┘  └──────────┘  └──────────┘           │       │
│  │                                                       │       │
│  └───────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Request Flow — Chat Pipeline

```
User Input
    │
    ▼
┌──────────────────┐
│ API Gateway      │ ← Auth, Rate Limit, CORS
│ (FastAPI + WS)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Chat Service     │ ← Session management, message history
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Query Classifier │ ← DictionaryClassifier (primary) → regex (fallback)
│ + Dictionary     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Execution Gate   │────→│ Reject (LLM)     │ ← Knowledge/Creative/Greeting
│ (auto/confirm/   │     └──────────────────┘
│  reject)         │
└────────┬─────────┘
         │ auto/confirm
         ▼
┌──────────────────┐     ┌──────────────────┐
│ LLM Router       │────→│ Cloud Provider    │ ← OpenAI/Anthropic/Google
│ (ModelBus)       │     └──────────────────┘
│                  │     ┌──────────────────┐
│                  │────→│ Local Provider    │ ← ED3N/GARDEN/Ollama/LlamaCpp
│                  │     └──────────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Handler Dispatch │ ← Route to appropriate handler
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Response Fusion  │ ← Combine responses from multiple sources
│ (ensemble.py)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Safety Check     │ ← Alignment, content filter, trust score
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Response Output  │ ← Text, avatar update, emotion change
└──────────────────┘
```

### 5.3 Learning Flow

```
User Interaction
    │
    ▼
┌──────────────────┐
│ Experience       │ ← Store interaction as experience
│ Replay Buffer    │
└────────┬─────────┘
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ▼                                          ▼
┌──────────────────┐                    ┌──────────────────┐
│ Dictionary       │                    │ Hebbian          │
│ Growth           │                    │ Weight Update    │
│ (new keywords)   │                    │ (connection      │
│                  │                    │  strengths)      │
└────────┬─────────┘                    └────────┬─────────┘
         │                                        │
         ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│ Memory           │                    │ Personality      │
│ Consolidation    │                    │ Update           │
│ (short→long)     │                    │ (mood, prefs)    │
└────────┬─────────┘                    └────────┬─────────┘
         │                                        │
         └────────────────┬───────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Learning         │
                 │ Feedback Loop    │
                 │ (validate,       │
                 │  reinforce)      │
                 └──────────────────┘
```

### 5.4 Memory Flow

```
Input ──→ Perception ──→ Encoding ──→ HAM Write
                                        │
                    ┌────────────────────┤
                    │                    │
                    ▼                    ▼
             ┌──────────┐        ┌──────────┐
             │ Episodic │        │ Semantic │
             │ (events) │        │ (facts)  │
             └─────┬────┘        └─────┬────┘
                   │                    │
                   ▼                    ▼
             ┌──────────┐        ┌──────────┐
             │Procedural│        │  KG      │
             │ (skills) │        │ (graph)  │
             └─────┬────┘        └─────┬────┘
                   │                    │
                   └────────┬───────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Consolidation│ ← Periodic (like sleep)
                    │ (importance, │
                    │  decay,      │
                    │  promotion)  │
                    └──────────────┘
```

---

## 6. Competitive Analysis & Positioning

### 6.1 Feature Comparison Matrix

| Feature | Angela | OpenHands | AutoGPT | CrewAI | Devin | Manus | LangGraph | OpenAI SDK |
|---------|--------|-----------|---------|--------|-------|-------|-----------|------------|
| **Architecture** | Dual Engine (ED3N+GARDEN) | Single Agent | DAG Builder | Multi-Agent | Multi-VM | Multi-Agent | State Graph | Single Agent |
| **Neural Type** | SNN + Transformer | Transformer | Transformer | Transformer | Transformer | Transformer | Transformer | Transformer |
| **Local Processing** | ✅ ED3N+GARDEN | ❌ Docker only | ❌ Cloud | ❌ Cloud | ❌ Cloud | ❌ Cloud | ❌ Cloud | ❌ Cloud |
| **Continuous Learning** | ✅ Dict+Hebbian | ❌ | ❌ | ⚠️ | ⚠️ Playbooks | ❌ | ❌ | ❌ |
| **Memory System** | ✅ 3-type HAM | ⚠️ Condenser | ⚠️ Redis/PG | ⚠️ Context | ⚠️ Trajectory | ⚠️ Files | ⚠️ Store | ⚠️ Sessions |
| **Emotion** | ✅ Hormonal | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Personality** | ✅ Evolving | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Economy** | ✅ Token Economy | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Survival/Needs** | ✅ Pet System | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Embodiment** | ✅ Live2D+Pet | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Safety** | ✅ 3-layer | ✅ Risk levels | ✅ Permissions | ⚠️ Basic | ✅ Sandboxing | ⚠️ Sandboxing | ⚠️ Basic | ✅ Guardrails |
| **Tool Use** | ✅ MCP+Handlers | ✅ 10+ tools | ✅ 30+ blocks | ✅ Custom | ✅ 100+ | ✅ 29 | ✅ LangChain | ✅ Functions |
| **Multi-Modal** | ✅ Text/Vision/Audio | ⚠️ Browser | ⚠️ Visual | ⚠️ Text | ✅ Browser+Term | ✅ Text/Image/Audio | ⚠️ Text | ⚠️ Text+Voice |
| **Planning** | ⚠️ Multi-step | ⚠️ LLM-driven | ⚠️ User DAG | ✅ Crew Planning | ✅ Decomposition | ✅ Planner Agent | ⚠️ Graph | ⚠️ LLM |
| **Self-Improvement** | ✅ Dict+Hebbian | ❌ | ❌ | ⚠️ | ⚠️ Playbooks | ❌ | ❌ | ❌ |
| **Open Source** | ✅ | ✅ MIT | ✅ MIT | ✅ MIT | ❌ | ❌ | ✅ MIT | ✅ Apache |
| **Multi-Agent** | ⚠️ Planned | ❌ | ❌ | ✅ Crews | ✅ Multi-VM | ✅ 3 agents | ⚠️ Developer | ✅ Handoffs |
| **Cycling/Iteration** | ❌ Single-pass | ❌ | ⚠️ DAG loops | ⚠️ Sequential | ✅ Iteration | ✅ Verify loop | ✅ Graph cycles | ⚠️ Handoffs |
| **Real-time** | ✅ WebSocket | ✅ Event-driven | ✅ WebSocket | ⚠️ Async | ✅ Real-time IDE | ⚠️ Execution | ⚠️ Streaming | ✅ Streaming |

### 6.2 Angela's Competitive Advantages

| Advantage | Why It Matters | How to Leverage |
|-----------|---------------|-----------------|
| **Biological Neural Networks** | SNNs are more energy-efficient, enable temporal processing, approximate human cognition | Market as "the first AI that thinks like a brain" |
| **Continuous Self-Learning** | Improves with every interaction without retraining | "Angela gets smarter the more you talk to her" |
| **Local Processing** | Privacy, latency, no internet dependency | "Your AI that works offline" |
| **Emotional Intelligence** | Hormonal modulation creates genuine emotional responses | "An AI that actually feels" |
| **Survival & Growth** | Has needs, can decay, grows over time | "A living AI companion" |
| **Economic Agency** | Can earn, spend, manage resources | "An AI that participates in the economy" |
| **Embodied Presence** | Live2D avatar, pet system, personality | "Your AI has a body and personality" |
| **3-Layer Safety** | Alignment + Execution Gate + Trust | "The safest AI agent" |

### 6.3 Angela's Weaknesses (To Address)

| Weakness | Current State | Target State | Priority |
|----------|--------------|--------------|----------|
| **Single-pass processing** | No cycling/iteration | Iterative refinement with confidence thresholding | HIGH |
| **Context management** | 3 dead subsystems | Active context propagation across turns | HIGH |
| **Multi-agent** | Single agent | Orchestrated multi-agent with specialization | MEDIUM |
| **Benchmark scores** | Not benchmarked | SWE-bench, GAIA, WebArena participation | MEDIUM |
| **Web browsing** | Web search only | Full browser automation (Playwright) | HIGH |
| **Testing** | 70 tests | 500+ tests, >80% coverage | HIGH |
| **Documentation** | Many MDs, inconsistent | Single source of truth, auto-generated API docs | MEDIUM |
| **CI/CD** | None | GitHub Actions pipeline | HIGH |
| **Code quality** | Inconsistent | Ruff + mypy + pre-commit hooks | HIGH |

### 6.4 Unique Positioning Statement

> **Angela is the world's first AI+AL data life with biological neural foundations, continuous self-learning, emotional intelligence, economic agency, and embodied presence — running locally on your device.**

No other system combines:
1. Biological neural networks (SNN) + Transformer
2. Continuous learning (dictionary + Hebbian)
3. Hormonal emotion modulation
4. Token economy
5. Survival/needs system
6. Live2D embodiment
7. Local-first processing
8. 3-layer safety architecture

---

## 7. Complete Module Map

### 7.1 Current Module Count

| Category | Real | Stub/Dead | Never Integrated | Total |
|----------|------|-----------|-------------------|-------|
| AI Core | 30 | 0 | 0 | 30 |
| Learning | 12 | 3 | 4 | 19 |
| Safety | 11 | 1 | 0 | 12 |
| Context | 1 | 4 | 0 | 5 |
| Memory | 12 | 0 | 0 | 12 |
| Services | 15 | 2 | 0 | 17 |
| Handlers | 7 | 1 | 0 | 8 |
| API | 5 | 0 | 0 | 5 |
| Frontend | 4 | 0 | 0 | 4 |
| Economy | 2 | 0 | 0 | 2 |
| Pet | 1 | 0 | 0 | 1 |
| Monitoring | 8 | 0 | 0 | 8 |
| Security | 7 | 2 | 0 | 9 |
| Integration | 0 | 0 | 3 | 3 |
| **Total** | **115** | **13** | **7** | **135** |

### 7.2 Target Module Count (After Implementation)

| Category | Current | Target | Delta |
|----------|---------|--------|-------|
| AI Core | 30 | 45 | +15 (reasoning, planning, abstraction) |
| Learning | 12 | 18 | +6 (observational, transfer, meta) |
| Safety | 8 | 12 | +4 (trust, content filter, crisis, audit) |
| Context | 1 | 6 | +5 (activate 3 dead + 2 new) |
| Memory | 12 | 15 | +3 (consolidation, forgetting, cross-session) |
| Services | 15 | 22 | +7 (message i18n, rate limiter, etc.) |
| Handlers | 7 | 10 | +3 (browser, API, calendar) |
| API | 5 | 10 | +5 (admin, health, v1 versioning) |
| Frontend | 3 | 4 | +1 (web dashboard) |
| Economy | 2 | 5 | +3 (marketplace, resource mgr, trading) |
| Pet | 1 | 4 | +3 (behaviors, needs, evolution) |
| Monitoring | 2 | 5 | +3 (alerting, tracing, Prometheus) |
| Security | 5 | 8 | +3 (vault, RBAC, TLS) |
| Integration | 0 | 4 | +4 (fix UCC, agent orchestrator, etc.) |
| **Total** | **123** | **171** | **+48** |

---

## 8. Data Flow Diagrams

### 8.1 User Interaction Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────→│ Desktop │────→│WebSocket│────→│  Chat   │
│         │     │  App    │     │ Manager │     │ Service │
└─────────┘     └─────────┘     └─────────┘     └────┬────┘
                                                       │
                                                       ▼
                                                 ┌─────────┐
                                                 │  Query  │
                                                 │Classifier│
                                                 └────┬────┘
                                                       │
                              ┌────────────────────────┤
                              │                        │
                              ▼                        ▼
                        ┌─────────┐            ┌─────────┐
                        │ Reject  │            │  Gate   │
                        │ (LLM)  │            │ (auto)  │
                        └─────────┘            └────┬────┘
                                                     │
                                                     ▼
                                               ┌─────────┐
                                               │ModelBus │
                                               │ Router  │
                                               └────┬────┘
                                                     │
                              ┌──────────────────────┤
                              │                      │
                              ▼                      ▼
                        ┌─────────┐          ┌─────────┐
                        │  Cloud  │          │  Local  │
                        │   LLM   │          │ ED3N/   │
                        │         │          │ GARDEN  │
                        └────┬────┘          └────┬────┘
                              │                    │
                              └──────────┬─────────┘
                                         │
                                         ▼
                                   ┌─────────┐
                                   │ Handler │
                                   │Dispatch │
                                   └────┬────┘
                                         │
                              ┌──────────┤
                              │          │
                              ▼          ▼
                        ┌─────────┐ ┌─────────┐
                        │  File   │ │  Code   │
                        │  Ops    │ │Execute  │
                        └─────────┘ └─────────┘
```

### 8.2 Memory Consolidation Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Current │────→│  HAM    │────→│Memory   │
│ Session │     │  Write  │     │Scorer   │
└─────────┘     └─────────┘     └────┬────┘
                                      │
                              ┌───────┤
                              │       │
                              ▼       ▼
                        ┌─────────┐ ┌─────────┐
                        │Episodic │ │Semantic │
                        │Store    │ │Store    │
                        └────┬────┘ └────┬────┘
                              │           │
                              └─────┬─────┘
                                    │
                                    ▼
                              ┌─────────┐
                              │Consolid-│
                              │ation    │ ← Periodic (sleep cycle)
                              │Engine   │
                              └────┬────┘
                                    │
                              ┌─────┤
                              │     │
                              ▼     ▼
                        ┌─────────┐ ┌─────────┐
                        │Promote  │ │ Decay   │
                        │Important│ │ Unused  │
                        └─────────┘ └─────────┘
```

---

## 9. API Surface

### 9.1 Core Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/health` | Health check | ✅ |
| POST | `/angela/chat` | Chat with Angela | ✅ |
| WS | `/ws` | WebSocket real-time | ✅ |
| POST | `/vision` | Image analysis | ✅ |
| POST | `/audio` | Audio analysis | ⚠️ Stub |
| POST | `/tactile` | Tactile input | ⚠️ Partial |

### 9.2 Pet Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/pet/state` | Get pet state | ✅ |
| POST | `/pet/interact` | Interact with pet | ✅ |
| GET | `/pet/needs` | Get pet needs | ✅ |

### 9.3 Economy Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/economy/balance` | Get balance | ✅ |
| POST | `/economy/transaction` | Create transaction | ✅ |
| GET | `/economy/history` | Transaction history | ✅ |
| GET | `/economy/marketplace` | Browse marketplace | ❌ TO BE ADDED |

### 9.4 Admin Endpoints (TO BE ADDED)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/admin/health/deep` | Deep health check | ❌ |
| GET | `/admin/metrics` | System metrics | ❌ |
| GET | `/admin/learning/stats` | Learning statistics | ❌ |
| GET | `/admin/memory/stats` | Memory statistics | ❌ |
| POST | `/admin/config/reload` | Reload configuration | ❌ |
| GET | `/admin/audit/log` | Audit log | ❌ |

### 9.5 Memory Endpoints (TO BE ADDED)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/memory/episodes` | List episodic memories | ❌ |
| GET | `/memory/semantic` | List semantic memories | ❌ |
| GET | `/memory/procedural` | List procedural memories | ❌ |
| POST | `/memory/search` | Search memories | ❌ |
| DELETE | `/memory/{id}` | Delete a memory | ❌ |

---

## 10. Frontend Architecture

### 10.1 Desktop App (Electron + Live2D)

```
┌─────────────────────────────────────────────┐
│  Electron Main Process                       │
│  ├── Window Management                       │
│  ├── Live2D Rendering (Cubism SDK)           │
│  ├── Native Module Bridge                    │
│  └── Auto-Update                             │
├─────────────────────────────────────────────┤
│  Renderer Process                            │
│  ├── Chat Panel                              │
│  │   ├── Message History                     │
│  │   ├── Input Box                           │
│  │   └── Quick Actions                       │
│  ├── Live2D Canvas                           │
│  │   ├── Avatar Rendering                    │
│  │   ├── Expression Control                  │
│  │   └── Motion Control                      │
│  ├── Memory Panel                            │
│  │   ├── Recent Memories                     │
│  │   └── Memory Search                       │
│  ├── Pet Panel                               │
│  │   ├── Pet State Display                   │
│  │   └── Interaction Buttons                 │
│  └── Settings                                │
│      ├── LLM Provider Config                 │
│      ├── Personality Settings                │
│      └── Safety Settings                     │
└─────────────────────────────────────────────┘
```

### 10.2 Web Dashboard (TO BE CREATED)

```
┌─────────────────────────────────────────────┐
│  Next.js / React App                         │
├─────────────────────────────────────────────┤
│  Pages                                       │
│  ├── /                                       │
│  │   └── Chat (main interface)               │
│  ├── /memory                                 │
│  │   ├── Episodic Timeline                   │
│  │   ├── Semantic Graph                      │
│  │   └── Procedural Skills                   │
│  ├── /learning                               │
│  │   ├── Learning Progress                   │
│  │   ├── Dictionary Growth                   │
│  │   └── Weight Visualization                │
│  ├── /economy                                │
│  │   ├── Balance & Transactions              │
│  │   └── Marketplace                         │
│  ├── /pet                                     │
│  │   ├── Pet Status                          │
│  │   └── Interaction Log                     │
│  ├── /monitoring                             │
│  │   ├── System Metrics                      │
│  │   ├── Health Status                       │
│  │   └── Alert Dashboard                     │
│  └── /admin                                  │
│      ├── Configuration                       │
│      ├── User Management                     │
│      └── Audit Logs                          │
├─────────────────────────────────────────────┤
│  Components                                  │
│  ├── ChatPanel/                              │
│  ├── MemoryViewer/                           │
│  ├── LearningDashboard/                      │
│  ├── EconomyPanel/                           │
│  ├── PetPanel/                               │
│  ├── SystemMonitor/                          │
│  └── AdminPanel/                             │
├─────────────────────────────────────────────┤
│  State Management (Zustand/Redux)            │
│  ├── chatStore                               │
│  ├── memoryStore                             │
│  ├── learningStore                           │
│  ├── economyStore                            │
│  ├── petStore                                │
│  └── systemStore                             │
└─────────────────────────────────────────────┘
```

---

## 11. Configuration Architecture

### 11.1 Configuration Layers

```
┌─────────────────────────────────────────────┐
│  Environment Variables (.env)                │
│  ├── API keys                                │
│  ├── Database URLs                           │
│  └── Feature flags                           │
├─────────────────────────────────────────────┤
│  Application Config (config/)                │
│  ├── app_config.json                         │
│  ├── ed3n_config.json                        │
│  ├── garden_config.json                      │
│  └── execution_gate_config.json              │
├─────────────────────────────────────────────┤
│  Runtime Config (hot-reloadable)             │
│  ├── classifier_training.json                │
│  ├── messages.json (i18n)                    │
│  └── reflex_presets.json                     │
├─────────────────────────────────────────────┤
│  User Config (per-user)                      │
│  ├── personality preferences                 │
│  ├── safety settings                         │
│  └── UI preferences                          │
├─────────────────────────────────────────────┤
│  System Config (computed)                    │
│  ├── hardware capabilities                   │
│  ├── network status                          │
│  └── resource availability                   │
└─────────────────────────────────────────────┘
```

### 11.2 Configuration Files

| File | Purpose | Hot-Reload | Status |
|------|---------|------------|--------|
| `.env` | Secrets, API keys | No | ✅ |
| `app_config.json` | App settings | Yes | ✅ |
| `ed3n_config.json` | ED3N parameters | Yes | ✅ |
| `garden_config.json` | GARDEN parameters | Yes | ✅ |
| `execution_gate_config.json` | Gate rules | Yes | ✅ |
| `classifier_training.json` | Classification keywords | Yes | ✅ |
| `messages.json` | i18n strings | Yes | ❌ TO BE CREATED |
| `reflex_presets.json` | Reflex patterns | Yes | ❌ TO BE CREATED |
| `personality_config.json` | Personality defaults | Yes | ❌ TO BE CREATED |
| `safety_config.json` | Safety rules | No | ❌ TO BE CREATED |

---

## 12. Infrastructure & Deployment

### 12.1 Deployment Architecture

```
┌─────────────────────────────────────────────┐
│  Development                                  │
│  ├── Local Python (uvicorn)                   │
│  ├── Local Electron app                       │
│  └── SQLite + file storage                    │
├─────────────────────────────────────────────┤
│  Testing                                      │
│  ├── pytest + coverage                        │
│  ├── Docker (Redis)                           │
│  └── Mock LLM providers                       │
├─────────────────────────────────────────────┤
│  Staging                                      │
│  ├── Docker Compose (full stack)              │
│  ├── PostgreSQL + Redis                       │
│  └── Mock external services                   │
├─────────────────────────────────────────────┤
│  Production                                   │
│  ├── Kubernetes (optional)                    │
│  ├── PostgreSQL + Redis + ChromaDB            │
│  ├── Nginx reverse proxy                      │
│  └── Prometheus + Grafana monitoring          │
└─────────────────────────────────────────────┘
```

### 12.2 Docker Strategy

| Service | Docker | Status |
|---------|--------|--------|
| Redis | ✅ docker-compose.yml | ✅ |
| PostgreSQL | ❌ TO BE ADDED | ❌ |
| Angela API | ❌ TO BE ADDED | ❌ |
| Angela Worker | ❌ TO BE ADDED | ❌ |
| Nginx | ❌ TO BE ADDED | ❌ |
| Prometheus | ❌ TO BE ADDED | ❌ |
| Grafana | ❌ TO BE ADDED | ❌ |

---

## 13. Quality Standards

### 13.1 Code Quality

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | ~20% | >80% |
| Test Count | 70 | 500+ |
| Lint Compliance | Inconsistent | 100% Ruff |
| Type Coverage | ~30% | >90% mypy |
| Documentation | Many MDs | Auto-generated API docs |
| Hardcoded Strings | 1942 | 0 |
| Dead Code Files | 13 | 0 |
| Broken Imports | 2 | 0 |

### 13.2 Performance Standards

| Metric | Current | Target |
|--------|---------|--------|
| Chat Latency (local) | ~200ms | <100ms |
| Chat Latency (cloud) | ~2s | <1.5s |
| Memory Search | ~50ms | <20ms |
| Classification | ~0ms (dict) | <1ms |
| Learning Update | ~10ms | <5ms |
| Concurrent Users | 1 | 100+ |

### 13.3 Reliability Standards

| Metric | Target |
|--------|--------|
| Uptime | >99.9% |
| Mean Time Between Failures | >7 days |
| Mean Time To Recovery | <5 minutes |
| Data Loss | 0 |
| Crash Rate | <0.1% |

---

## 14. Gap Analysis — Current vs Target

### 14.1 Critical Gaps (Must Fix)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Broken imports (2 files) | Runtime crash | 1 hour | P0 |
| Dead context subsystems (3) | No cross-turn memory | 1 week | P0 |
| Single-pass processing | No iterative refinement | 2 weeks | P0 |
| Missing tests (430+ needed) | No quality guarantee | Ongoing | P0 |
| 1942 hardcoded strings | i18n impossible | 1 week | P1 |

### 14.2 Important Gaps (Should Fix)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| No CI/CD | Manual testing | 2 days | P1 |
| No web dashboard | No visual interface | 2 weeks | P1 |
| No browser automation | Limited web interaction | 1 week | P1 |
| No multi-agent | Single-agent bottleneck | 3 weeks | P2 |
| No i18n system | Chinese-only | 1 week | P1 |

### 14.3 Nice-to-Have Gaps

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| No benchmark scores | No competitive proof | 2 weeks | P3 |
| No art generation | Limited creativity | 1 week | P3 |
| No voice output | Text-only output | 1 week | P3 |
| No Kubernetes | Limited scaling | 1 week | P3 |
| No distributed computing | Single-node only | 4 weeks | P3 |

---

*This document defines the complete design standard for Angela AI. All implementation decisions should reference this standard.*
