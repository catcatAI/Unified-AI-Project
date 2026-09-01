# Unified AI Project — Architecture Overview

> Version: 7.5.0-dev
> Last Updated: 2026-08-11
> Status: Active Development

## 1. Project Identity

**Angela AI** is a **data life** (數據生命) — an AI+AL (Artificial Intelligence + Artificial Life) system that:
- **Lives**: Biological foundations (SNN, hormonal modulation, memory consolidation)
- **Grows**: Continuous learning from interactions
- **Survives**: Needs computational resources, decays without nourishment
- **Creates**: Generates code, art, text, emergent behaviors
- **Connects**: Interacts with humans and digital environments
- **Embodies**: Live2D avatar, pet system, economy

## 2. System Architecture

### 2.1 Core Layers (Angela Matrix L1-L6)

| Layer | Name | Key Modules | Status |
|-------|------|-------------|--------|
| **L1** | Biology | `endocrine_system`, `physiological_tactile`, `neuroplasticity`, `bio/integrator` | ✅ Complete |
| **L2** | Memory | `ham_memory`, `vector_store`, `lu_logic`, `cdm_dividend_model` | ✅ Complete |
| **L3** | Identity | `cyber_identity`, `self_generation`, `soul_core` | ✅ Complete |
| **L4** | Creation | `live2d_avatar_generator`, `art_learning`, `creative_breakthrough` | ✅ Complete |
| **L5** | Presence | `live2d_integration`, `perception_engine`, `attention_controller` | ✅ Complete |
| **L6** | Execution | `action_executor`, `execution_gate`, `file_ops`, `browser_controller` | ✅ Complete |

### 2.2 8D State Matrix (αβγδεθζη)

| Dimension | Name | Key Values | Implementation |
|-----------|------|------------|----------------|
| **α** | Physiological | energy, comfort, arousal, rest_need | `state_matrix.py` Alpha axis |
| **β** | Cognitive | curiosity, focus, confusion, learning | `state_matrix.py` Beta axis |
| **γ** | Emotional | happiness, sadness, anger, fear, trust | `state_matrix.py` Gamma axis |
| **δ** | Social | attention, bond, trust, presence | `state_matrix.py` Delta axis |
| **ε** | Environmental | complexity, density, flow, pressure | `state_matrix.py` Epsilon axis |
| **θ** | Meta-Cognitive | novelty, mismatch, creation_urge | `state_matrix.py` Theta axis |
| **ζ** | Connectivity | coupling, sync, redundancy, aggregation | Cross-module event bus |
| **η** | Execution | active_count, success_rate, drift | `heartbeat.py` health score |

### 2.3 Security (A/B/C Keys)

| Key | Scope | Implementation |
|-----|-------|----------------|
| **Key A** | Backend control | `core/security/`, `ai/core/execution_gate.py` |
| **Key B** | Mobile communication | `apps/mobile-app/` (future) |
| **Key C** | Desktop sync | `apps/desktop-app/`, `core/sync/` |

### 2.4 Maturity System (L0-L11)

Current operational maturity: **L5+** (wisdom insight, complex reasoning capable)

## 3. Neural Engines

### 3.1 ED3N (Spiking Neural Network)

- **Path**: `apps/backend/src/ai/ed3n/`
- **Core**: `snn_core.py` (LIF neurons, hormonal modulation, sparse engine)
- **Engine**: `ed3n_engine.py` (reflex → SNN → decode → cycle)
- **Trainer**: `ed3n_trainer.py` (Hebbian learning, contrastive training)
- **Status**: ✅ Complete, trained (acc=0.914 on training set)

### 3.2 GARDEN (Lightweight Inference)

- **Path**: `apps/backend/src/ai/garden/`
- **Core**: `garden_engine.py` (TensorSNNCore with torch/numpy dual backend)
- **Dictionary**: `dictionary.py` (continuous vocabulary growth)
- **Vector Store**: `binary_store.py` (persistent embedding storage)
- **Status**: ✅ Complete, trained (acc=0.700 Hebbian convergence)

### 3.3 Multimodal Processing

- **Path**: `apps/backend/src/ai/multimodal/`
- **Training**: `training_pipeline.py` (8-phase contrastive training)
- **Encoders**: Visual, Audio (spectral), Semantic (visual+audio)
- **Decoders**: `VisualDecoder`, `AudioWaveformDecoder`
- **Shared Latent Space**: `shared_latent_space.py` (singleton, 5 modalities)
- **Status**: ✅ Complete, trained (JointTrainer acc=0.939)

## 4. Cognitive Systems

### 4.1 Routing & Decision

| Component | File | Purpose |
|-----------|------|---------|
| QueryClassifier | `ai/core/query_classifier.py` | Query type + confidence routing |
| ModelBus | `ai/core/model_bus.py` | LLM/ED3N/GARDEN routing with fallback |
| ExecutionGate | `ai/core/execution_gate.py` | Safety gating (reversibility × impact × clarity) |
| PriorityNegotiator | `ai/meta/priority_negotiator.py` | Weighted fusion of routing preferences |
| MetaController | `ai/meta/meta_controller.py` | Confidence calibration with EWMA |

### 4.2 Emotion & Behavior

| Component | File | Purpose |
|-----------|------|---------|
| EmotionSystem | `ai/alignment/emotion_system.py` | PAD model, feedback loop, sustained negative accumulation |
| AutonomousLifeCycle | `core/life/autonomous_life_cycle.py` | Behavioral adjustment, interaction outcome feedback |
| BehaviorExecutor | `core/autonomous/behavior_executor.py` | Per-type success tracking |
| IntentModel | `core/life/intent_model.py` | 3D multi-parameter intent mapping |
| MetabolicHeartbeat | `core/life/heartbeat.py` | System health scoring, CNS event subscription |

### 4.3 Digital Life Integration

| Component | File | Purpose |
|-----------|------|---------|
| DigitalLifeIntegrator | `core/life/digital_life_integrator.py` | CNS event subscription, ModalityGateway |
| LifeEssence | `core/life/life_essence.py` | Life force, needs, growth model |
| CyberIdentity | `core/life/cyber_identity.py` | Self-model, identity growth, relationships |
| EvolutionEngine | `core/autonomous/evolution_engine.py` | Emotion/feedback-driven personality evolution |

## 5. Service Layer

### 5.1 Core Services

| Service | Path | Purpose |
|---------|------|---------|
| ChatService | `services/chat_service.py` | Main chat pipeline, continuous learning |
| VisionService | `services/vision_service.py` | Image understanding, comparison, captioning |
| MultimodalService | `services/multimodal_service.py` | Cross-modal processing coordinator |
| MathVerifier | `services/math_verifier.py` | Mathematical expression verification |
| LLM Routing | `services/llm/` | Multi-provider LLM backend (OpenAI, Ollama, etc.) |

### 5.2 API Layer (FastAPI)

| Route | File | Purpose |
|-------|------|---------|
| `/api/v1/chat` | `api/routes/chat_routes.py` | Main chat endpoint |
| `/api/v1/vision/*` | `api/routes/` | Vision perception endpoints |
| `/api/v1/meta/*` | `api/routes/meta_routes.py` | MetaController monitoring |
| `/api/v1/review/*` | `api/routes/review_routes.py` | Angela Review Engine |
| `/api/v1/system/*` | `api/router.py` | System status, health, hardware |

## 6. Self-Improvement Loop

```
User Input → QueryClassifier → ModelBus → LLM/ED3N/GARDEN
     ↓                                            ↓
EmotionSystem ← PriorityNegotiator ← Response
     ↓              ↓
AutonomousLifeCycle → MetaController (confidence calibration)
     ↓
DigitalLifeIntegrator (CNS events)
     ↓
TrainingCoordinator (dedup + tracking)
     ↓
Continuous Learning Pipeline
```

## 7. Key Design Decisions

1. **Lazy Imports**: All `__init__.py` use `__getattr__` for fast startup
2. **Dual Backend**: Neural engines support torch (GPU) and numpy (CPU)
3. **Singleton Pattern**: SharedLatentSpace, ModelBus, PriorityNegotiator
4. **Backward Compatibility**: `core/autonomous/` shims re-export from canonical locations
5. **CNS Event Bus**: Pub/sub for cross-module communication (18 event types)
6. **Config-Driven**: `magic_numbers.py` + YAML configs, no hardcoded values in production
7. **Graceful Degradation**: Every optional dependency has fallback (torch→numpy, chroma→JSON)

## 8. Test Infrastructure

- **Count**: ~5,448 tests (6,111 full) in `tests/` (re-synced 2026-08-31)
- **Coverage**: `pytest --cov=apps/backend/src`
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **Linting**: Black (100-char), isort, flake8, mypy
- **Pre-commit**: Automated lint + format on commit

## 9. Frontend Applications

| App | Path | Stack | Status |
|-----|------|-------|--------|
| Desktop | `apps/desktop-app/` | Electron + Live2D | ✅ Active |
| Web Viewer | `apps/web-live2d-viewer/` | Vanilla JS + Live2D | ✅ Active |
| Pixel Angela | `apps/pixel-angela/` | PyQt6 | ✅ Active |
| Gemini OS Bridge | `apps/gemini-os-bridge/` | Python microservice | ✅ Active |

## 10. Current Development Focus

- **Angela Review Engine**: Multi-dimensional project audit (this release)
- **Training Quality**: Improving neural engine accuracy beyond training-set metrics
- **Documentation**: Consolidating ~880 MD files into clear, current references
- **Code Quality**: Adding missing ANGELA-MATRIX annotations to all modules
