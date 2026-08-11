# Module Map — Complete Implementation Inventory

> Version: 7.5.0-dev
> Last Updated: 2026-08-11
> Total Python files: ~659 in apps/backend/src/
> Total test files: ~4,488 collected

## Legend

- ✅ **COMPLETE** — Full implementation, real logic
- 🟡 **PARTIAL** — Some stubs or missing features
- 🔴 **STUB** — Mostly pass/docstring, needs implementation
- 📝 **Missing annotation** — No ANGELA-MATRIX header

---

## AI Core (`apps/backend/src/ai/`)

### `ai/core/` — Core AI Infrastructure

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `query_classifier.py` | ~700 | ✅ | ✅ | Query type + confidence routing |
| `execution_gate.py` | ~398 | ✅ | ✅ | Safety gating (reversibility × impact × clarity) |
| `model_bus.py` | ~600 | ✅ | ✅ | LLM/ED3N/GARDEN routing |
| `dictionary_classifier.py` | ~450 | ✅ | ✅ | Dictionary-enhanced classification |
| `trust_manager.py` | ~850 | ✅ | ✅ | Trust scoring system |
| `dynamic_threshold_manager.py` | ~1350 | ✅ | ✅ | Dynamic emotion thresholds |
| `training_coordinator.py` | ~230 | ✅ | ✅ | Domain training orchestration |
| `unicode_utils.py` | ~350 | ✅ | ✅ | CJK normalization, romaji |

### `ai/meta/` — Meta-Learning & Control

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `meta_controller.py` | ~367 | ✅ | ✅ | Confidence calibration, EWMA |
| `priority_negotiator.py` | ~315 | ✅ | ✅ | Weighted fusion routing |
| `adaptive_learning_controller.py` | ~150 | ✅ | ✅ | Adaptive learning rate |
| `knowledge_verifier.py` | ~190 | ✅ | ✅ | Knowledge verification |
| `learning_orchestrator.py` | ~80 | ✅ | ✅ | Learning orchestration |
| `learning_log_db.py` | ~100 | ✅ | ✅ | Learning event logging |
| `angela_review_engine.py` | ~950 | ✅ | ✅ | **NEW** Multi-dimensional audit |

### `ai/alignment/` — Emotion & Alignment

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `emotion_system.py` | ~550 | ✅ | ✅ | PAD model, feedback loop, sustained negative |
| `ontology_system.py` | ~300 | ✅ | ✅ | Ontology management |
| `alignment_manager.py` | ~250 | ✅ | ✅ | Alignment coordination |
| `asi_autonomous_alignment.py` | ~200 | ✅ | ✅ | ASI alignment checks |

### `ai/ed3n/` — ED3N Neural Engine

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `ed3n_engine.py` | ~1200 | ✅ | ✅ | Reflex → SNN → decode → cycle |
| `ed3n_trainer.py` | ~650 | ✅ | ✅ | Hebbian learning, contrastive |
| `snn/snn_core.py` | ~400 | ✅ | ✅ | LIF neurons, hormonal modulation |
| `dictionary_layer.py` | ~500 | ✅ | ✅ | Continuous vocabulary growth |
| `step_decoder.py` | ~300 | ✅ | ✅ | Step-by-step decoding |

### `ai/garden/` — GARDEN Inference Engine

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `garden_engine.py` | ~600 | ✅ | ✅ | Dual backend (torch/numpy) |
| `dictionary.py` | ~1247 | ✅ | ✅ | Vector dictionary, continuous growth |
| `binary_store.py` | ~289 | ✅ | ✅ | Persistent embedding storage |
| `snn_core.py` (garden) | ~350 | ✅ | ✅ | PyTorch-accelerated LIF |
| `vector_decoder.py` | ~200 | ✅ | ✅ | Vector decoding |
| `kg_import.py` | ~180 | ✅ | ✅ | Knowledge graph import |

### `ai/lifecycle/` — Lifecycle & Behavior

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `llm_decision_loop.py` | ~665 | ✅ | ✅ | LLM decision-making loop |
| `proactive_interaction_system.py` | ~576 | ✅ | ✅ | Proactive interaction triggers |
| `behavior_feedback_loop.py` | ~432 | ✅ | ✅ | Behavior→Response→Feedback |
| `memory_integration_loop.py` | ~492 | ✅ | ✅ | Memory integration cycle |
| `user_monitor.py` | ~408 | ✅ | ✅ | User activity monitoring |

### `ai/streaming/` — Streaming Pipeline

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `token_stream.py` | ~293 | ✅ | 📝 | Token streaming |
| `pipeline.py` | ~136 | ✅ | 📝 | Stream pipeline |
| `producers.py` | ~130 | ✅ | 📝 | Stream producers |
| `synthesizer_core.py` | ~195 | ✅ | ✅ | Token synthesis |

### `ai/memory/` — Memory Systems

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `ham_memory/ham_manager.py` | ~800 | ✅ | ✅ | HAM 3-type memory (Episodic/Semantic/Procedural) |
| `ham_memory/ham_query_engine.py` | ~400 | ✅ | ✅ | HAM query engine |
| `vector_store.py` | ~500 | ✅ | ✅ | Dual-backend vector store (chroma/numpy) |
| `cognitive_pipeline.py` | ~241 | 🟡 | 📝 | _init_subsystems() is hook for testing |
| `lu_logic/logic_unit.py` | ~350 | ✅ | ✅ | Logic unit for reasoning |
| `math_ripple_engine.py` | ~200 | ✅ | ✅ | Mathematical ripple processing |

### `ai/agents/` — Agent System

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `base/base_agent.py` | ~567 | ✅ | ✅ | Base agent ABC with lifecycle |
| `dynamic_agent_registry.py` | ~253 | ✅ | ✅ | Dynamic agent registration |
| `orchestrator.py` | ~300 | ✅ | ✅ | Agent orchestration |
| `adapter.py` | ~150 | ✅ | ✅ | Agent adapter |
| `collaboration_manager.py` | ~200 | ✅ | ✅ | Multi-agent collaboration |
| `specialized/` | various | ✅ | ✅ | 10 specialized agents |

### `ai/multimodal/` — Multimodal Processing

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `training_pipeline.py` | ~1361 | ✅ | ✅ | 8-phase contrastive training |
| `shared_latent_space.py` | ~400 | ✅ | ✅ | Singleton, 5 modalities |
| `visual_encoder.py` | ~150 | ✅ | ✅ | Image encoding |
| `visual_decoder.py` | ~180 | ✅ | ✅ | Image reconstruction |
| `audio_encoder_spectral.py` | ~120 | ✅ | ✅ | Spectral audio encoding |
| `audio_decoder.py` | ~150 | ✅ | ✅ | Waveform audio decoding |
| `quality_metrics.py` | ~100 | ✅ | ✅ | SSIM, PSNR, SNR metrics |
| `reconstruction_cycle.py` | ~200 | ✅ | ✅ | Reconstruction quality cycle |
| `semantic_visual.py` | ~180 | ✅ | ✅ | Semantic visual encoding |
| `semantic_audio.py` | ~160 | ✅ | ✅ | Semantic audio encoding |
| `three_layer_visual.py` | ~250 | ✅ | ✅ | 3-layer visual processing |
| `latent_reasoning.py` | ~200 | ✅ | ✅ | Latent reasoning network |
| `generator/training_data.py` | ~150 | ✅ | ✅ | Training data generation |

### `ai/reasoning/` — Reasoning Engine

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `causal_reasoning_engine.py` | ~500 | ✅ | ✅ | Retrospective warm start, predict |
| `planning_engine.py` | ~300 | ✅ | ✅ | Goal decomposition, planning |
| `reasoning_engines.py` | ~250 | ✅ | ✅ | Multi-strategy reasoning |
| `relational_chain.py` | ~200 | ✅ | ✅ | Relational chain reasoning |

---

## Core Infrastructure (`apps/backend/src/core/`)

### `core/life/` — Life Systems (Canonical Location)

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `autonomous_life_cycle.py` | ~1400 | ✅ | ✅ | Behavioral adjustment, interaction feedback |
| `digital_life_integrator.py` | ~1350 | ✅ | ✅ | CNS events, ModalityGateway |
| `heartbeat.py` | ~421 | ✅ | ✅ | System health scoring |
| `intent_model.py` | ~260 | ✅ | ✅ | 3D intent mapping |
| `life_essence.py` | ~753 | ✅ | ✅ | Life force, needs, growth |
| `cyber_identity.py` | ~450 | ✅ | ✅ | Self-model, identity growth |
| `dynamic_parameters.py` | ~348 | ✅ | 📝 | Dynamic life parameters |
| `evolution_engine.py` | ~300 | ✅ | ✅ | Personality evolution |
| `self_generation.py` | ~200 | ✅ | ✅ | Self-generation capabilities |

### `core/engine/` — Engine Systems (Canonical Location)

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `state_matrix.py` | ~1664 | ✅ | ✅ | 6D state matrix (αβγδεθ) |
| `state_matrix_adapter.py` | ~280 | ✅ | ✅ | State matrix adapter |
| `action_executor.py` | ~1119 | ✅ | ✅ | Action queue, priority, safety |
| `angela_model_core.py` | ~164 | ✅ | ✅ | Angela model core |
| `eta_axis.py` | ~200 | ✅ | ✅ | Epsilon dimension axis |
| `theta_router.py` | ~180 | ✅ | ✅ | Theta dimension routing |
| `cognitive_operations.py` | ~750 | ✅ | ✅ | Cognitive operations |
| `live2d_avatar_generator.py` | ~1100 | ✅ | ✅ | Live2D avatar generation |
| `browser_controller.py` | ~600 | ✅ | ✅ | Browser automation |
| `desktop_interaction.py` | ~900 | ✅ | ✅ | Desktop file operations |

### `core/bio/` — Biological Systems (Canonical Location)

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `endocrine_system.py` | ~550 | ✅ | ✅ | Hormone types, feedback loops |
| `physiological_tactile.py` | ~450 | ✅ | ✅ | Touch receptors, Live2D mapping |
| `neuroplasticity.py` | ~400 | ✅ | ✅ | Hebbian learning, Ebbinghaus |
| `autonomic_nervous_system.py` | ~300 | ✅ | ✅ | Autonomic responses |
| `biological_integrator.py` | ~250 | ✅ | ✅ | Biological system integration |
| `emotional_blending.py` | ~200 | ✅ | ✅ | Emotion blending |
| `endocrine_system_core.py` | ~535 | ✅ | ✅ | Core endocrine implementation |
| `kinetic_validator.py` | ~150 | ✅ | ✅ | Kinetics validation |

### `core/backbone/` — Backbone Training System

| File | Lines | Status | Annotation | Notes |
|------|-------|--------|------------|-------|
| `backbone.py` | ~516 | ✅ | ✅ | Core backbone with 5 registries |
| `config.py` | ~102 | ✅ | ✅ | BackboneConfig facade |
| `structure.py` | ~150 | ✅ | ✅ | Structure inventory |
| `pairs.py` | ~413 | ✅ | ✅ | IOPair, PairScheduler |
| `learning.py` | ~193 | ✅ | ✅ | Backbone learning |
| `external.py` | ~209 | ✅ | ✅ | External data connectors |
| `response.py` | ~279 | ✅ | ✅ | Response handling |
| `mountable.py` | ~229 | ✅ | ✅ | Mountable interface |
| `training.py` | ~160 | ✅ | ✅ | Training orchestration |

### `core/autonomous/` — Backward-Compat Shims

All files in this directory are **intentional backward-compatibility shims** that re-export from canonical locations in `core/engine/`, `core/bio/`, or `core/life/`. They should NOT be modified independently.

| File | Re-exports From |
|------|-----------------|
| `action_executor.py` | `core/engine/action_executor.py` |
| `cyber_identity.py` | `core/life/cyber_identity.py` |
| `desktop_interaction.py` | `core/engine/desktop_interaction.py` |
| `endocrine_system.py` | `core/bio/endocrine_system.py` |
| `neuroplasticity.py` | `core/bio/neuroplasticity.py` |
| `physiological_tactile.py` | `core/bio/physiological_tactile.py` |
| `state_matrix.py` | `core/engine/state_matrix.py` |

### Other Core Directories

| Directory | Status | Notes |
|-----------|--------|-------|
| `core/security/` | ✅ | Auth, encryption, key management, secure eval |
| `core/hsp/` | ✅ | HSP protocol (connector, security, versioning) |
| `core/perception/` | ✅ | Attention, auditory, visual, tactile perception |
| `core/influence/` | ✅ | Influence system (2 ABC pass = normal) |
| `core/ripple/` | 🟡 | `node.py` apply() returns self unchanged |
| `core/allocation/` | ✅ | Resource allocation (4 ABC pass = normal) |
| `core/event_loop_system.py` | ✅ | 849 lines, event loop |
| `core/real_time_monitor.py` | ✅ | 1162 lines, monitoring |
| `core/config_loader.py` | ✅ | YAML config with Authority+Learned merge |
| `core/clock/` | ✅ | Global system clock |
| `core/managers/` | ✅ | Dependency, execution, system managers |
| `core/system/` | ✅ | Cluster, bootstrap, module manager |
| `core/tools/` | ✅ | Web search, JS dispatcher, param extractor |
| `core/tracing/` | ✅ | Chain tracing and validation |
| `core/plugin/` | ✅ | Plugin system with audit logger |
| `core/card/` | ✅ | Card system for RPG game |
| `core/ethics/` | ✅ | Ethics manager |
| `core/i18n/` | ✅ | Internationalization |
| `core/maturity/` | ✅ | Maturity system |
| `core/metacognition/` | ✅ | Metacognition engine |
| `core/metamorphosis/` | ✅ | Soul core, body adapter |

---

## Services (`apps/backend/src/services/`)

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `chat_service.py` | ~614 | ✅ | Main chat pipeline |
| `vision_service.py` | ~500 | ✅ | Image understanding |
| `multimodal_service.py` | ~300 | ✅ | Cross-modal coordinator |
| `math_verifier.py` | ~430 | ✅ | Math verification |
| `weather_service.py` | ~200 | ✅ | Weather data |
| `llm/__init__.py` | lazy | ✅ | Lazy LLM provider loading |
| `llm/router.py` | ~400 | ✅ | LLM routing with PriorityNegotiator |
| `llm/providers/` | various | ✅ | 9 LLM backends |

---

## API Layer (`apps/backend/src/api/`)

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `router.py` | ~193 | ✅ | Main API router aggregation |
| `lifespan.py` | ~699 | ✅ | Server lifecycle (startup/shutdown) |
| `routes/chat_routes.py` | ~600 | ✅ | Main chat endpoint |
| `routes/meta_routes.py` | ~81 | ✅ | MetaController monitoring |
| `routes/review_routes.py` | ~85 | ✅ | **NEW** Review Engine API |
| `routes/ops_routes.py` | ~200 | ✅ | Operations endpoints |
| `routes/multimodal_routes.py` | ~150 | ✅ | Multimodal endpoints |
| `routes/game_routes.py` | ~100 | ✅ | Game endpoints |
| `routes/desktop_routes.py` | ~100 | ✅ | Desktop app endpoints |

---

## Issues Found

### Partial Implementations (2 files)

| File | Issue | Severity |
|------|-------|----------|
| `ai/memory/cognitive_pipeline.py` | `_init_subsystems()` is pass hook | LOW (intentional test hook) |
| `core/ripple/node.py` | `RippleNode.apply()` returns self unchanged | MEDIUM (core logic missing) |

### Missing ANGELA-MATRIX Annotations (13 files)

| File | Layer | Dimensions |
|------|-------|------------|
| `ai/streaming/token_stream.py` | L6 | η |
| `ai/streaming/producers.py` | L6 | η |
| `ai/streaming/pipeline.py` | L6 | η |
| `ai/memory/cognitive_pipeline.py` | L2 | β |
| `core/influence/space.py` | L3 | ζ |
| `core/allocation/policy.py` | L6 | η |
| `core/security/secure_eval.py` | L6 | δ |
| `core/event_loop_system.py` | L6 | η |
| `core/life/dynamic_parameters.py` | L1 | α |
| `core/config_loader.py` | L6 | ε |
| `core/ripple/node.py` | L2 | β |
| `core/clock/global_system_clock.py` | L6 | η |
| `services/multimodal_quality_monitor.py` | L5 | ζ |

### Duplicate MD Files (resolved)

- 133 outdated MD files archived to `docs/09-archive/auto-archived-2026-08-11/`
- Remaining duplicates are either package-level docs (README.md) or intentionally separated by audience
