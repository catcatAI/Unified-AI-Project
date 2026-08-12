# Neuro-Generative Response (NGR) System

> **Version**: v6.3 (2026-05-18)
> **Status**: Production
> **Core Files**: `apps/backend/src/ai/response/composer.py`, `learning_loop.py`

---

## 1. Overview

The NGR system replaces static response templates with dynamic, **8D-state-driven fragment composition**. Rather than selecting from predefined templates, Angela assembles responses on-the-fly from weighted semantic fragments, where each fragment has an 8D state vector determining when it should be used.

### Design Philosophy

- **No hardcoded templates**: All response content is decomposed into reusable fragments
- **State-driven selection**: Fragment choice depends entirely on current 8D state coordinates
- **Emergent variety**: The same query can produce different responses depending on Angela's current state
- **Offline capability**: NeuroBlender works without LLM, producing natural responses from local fragments

---

## 2. Core Components

### 2.1 NeuroFragment (`composer.py:379-426`)

A weighted semantic fragment with 8D state affinity vector:

```python
@dataclass
class NeuroFragment:
    id: str
    content: str
    category: str  # greeting, transition, confirmation, emotion, closing, etc.
    state_vector: List[float]  # 8D: [alpha, beta, gamma, delta, epsilon, theta, zeta, eta]
    energy_cost: float = 0.1
    tags: List[str] = field(default_factory=list)
```

Each fragment encodes *when* it should be selected via its `state_vector`:
- High `alpha` → high energy fragments (excited greetings)
- High `gamma` → positive/emotionally warm fragments
- High `beta` → curious/exploratory tone
- High `delta` → intimate/close social register

### 2.2 NeuroVocabulary (`composer.py:429-570`)

Fragment registry that manages lifecycle:

| Method | Description |
|--------|-------------|
| `load_from_config(config_data)` | Load fragments from `angela_core.yaml` `neuro_fragments` section |
| `decompose_from_templates(library)` | Decompose TemplateLibrary templates into fragments via sentence splitting |
| `get_fragments_by_energy(threshold)` | Filter fragments by energy cost |
| `get_stats()` | Registry statistics |

Config fragments (prefixed with `ng_`) receive a +0.15 similarity bonus during scoring, preferring hand-crafted natural language over decomposed template fragments.

### 2.3 NeuroBlender (`composer.py:573-889`)

The core synthesis engine with three sub-systems:

#### Target Vector Construction
```
target_vector = blend of:
  - state_matrix averages (αβγδεθζη)
  - intent vector (keyword-driven attention)
  - empathy valence (emotional alignment)
  - personality modifiers (curiosity/focus weighting)
```

#### Cosine Similarity Scoring
```python
score = cosine_similarity(target_vector, fragment.state_vector)
if fragment.id.startswith("ng_"):
    score += 0.15  # config fragment bonus
```

#### Structural Exploration
When `beta.curiosity > 0.6`, the blender explores non-standard fragment orderings (e.g., placing emotional interjection mid-sentence).

#### Natural Assembly (`_natural_assemble`)
Post-processing that adds:
- Logical connectors between fragments
- Proper punctuation flow (no double punctuation, trailing question mark detection)
- Ellipsis preservation (does NOT split on `.` to protect Chinese `...`)
- Final punctuation normalization

#### Energy-Aware Fragment Count
| Energy Level | Behavior |
|--------------|----------|
| `energy < 0.3` | No greeting, max 2 fragments |
| `energy 0.3-0.6` | Normal composition, 2-4 fragments |
| `energy > 0.6` | Up to 6 fragments, includes greeting |

### 2.4 ResponseComposer (`composer.py:891-954`)

High-level facade that integrates all subsystems:

```python
ResponseComposer
  ├── FragmentComposer (legacy template system, UNMODIFIED)
  ├── NeuroVocabulary (NGR fragment registry)
  └── NeuroBlender (NGR synthesis engine)
```

Key methods:
- `compose_response()` → delegates to FragmentComposer (legacy path)
- `neuro_synthesize()` → NeuroBlender path with 8D state + intent + empathy
- `load_neuro_fragments_from_config()` → populate vocabulary from YAML
- `decompose_templates_to_neuro()` → auto-decompose templates

---

## 3. Pipeline Architecture

```
User Message
    │
    ▼
chat_service.generate_response()
    │
    ├── Complexity < 0.4? ──→ NeuroBlender direct (fast path)
    │
    └── Complexity >= 0.4? ──→ LLM with neuro_blend_meta context
                                    │
                                    ▼
                         angela_llm_service._fallback_response()
                                    │
                                    └── (LLM unavailable) ──→ NeuroBlender
```

### Dual Path Integration

| Path | Entry Point | When | Output |
|------|-------------|------|--------|
| Low-complexity direct | `chat_service.py:generate_response` | `complexity < 0.4` | Pure NeuroBlender response |
| LLM with context | `chat_service.py:generate_response` | `complexity >= 0.4` | LLM response + `neuro_blend_meta` |
| LLM fallback | `angela_llm_service.py:_fallback_response` | LLM unavailable | NeuroBlender with last-known state |

---

## 4. 8D State Target Vector

The NGR system uses the full 8D state matrix for fragment selection:

| Axis | Dimensions | Role in NGR |
|------|-----------|-------------|
| α (Physiological) | energy, comfort, arousal | Energy level → fragment count, greeting presence |
| β (Cognitive) | curiosity, focus, learning | Curiosity → structural exploration |
| γ (Emotional) | happiness, calm, trust, surprise | Valence → emotional tone of fragments |
| δ (Social) | attention, bond, engagement | Intimacy → social register (formal/casual/intimate) |
| ε (Logical) | logic, precision, certainty | Precision → fragment specificity |
| θ (Meta-cognitive) | self_reflection, meta_accuracy, doubt | Self-awareness → hedging/uncertainty fragments |
| ζ (Temporal-Narrative) | temporal_coherence, memory_depth, narrative_flow, identity_continuity | Narrative continuity → contextual referencing |
| η (Execution) | execution_count, success_rate, structural_drift | Execution history → response efficiency |

---

## 5. Config Fragment Format

Fragments are defined in `angela_core.yaml` under `neuro_fragments`:

```yaml
neuro_fragments:
  - id: ng_morning_bright
    content: "早安～今天也是閃閃發亮的一天呢！"
    category: greeting
    state_vector: [0.8, 0.3, 0.7, 0.4, 0.2, 0.1, 0.5, 0.5]
    energy_cost: 0.3
    tags: [morning, energetic, bright]

  - id: ng_trans_well
    content: "嗯～讓我想想..."
    category: transition
    state_vector: [0.3, 0.6, 0.4, 0.3, 0.5, 0.7, 0.3, 0.3]
    tags: [thinking, transition]
```

The `state_vector` must always be 8 elements matching [α, β, γ, δ, ε, θ, ζ, η] order.

---

## 6. LearningLoop — Autonomous Linguistic Evolution

**File**: `learning_loop.py` (new in v6.3)

The LearningLoop enables Angela to evolve her vocabulary autonomously:

| Component | Function |
|-----------|----------|
| `FragmentExtractor` | Extracts sentences, emoji/kaomoji, and collocations from LLM responses |
| `LearningLoop` | Orchestrates extraction → novelty check → integration → config save |

**Flow**:
1. LLM produces high-quality response
2. `FragmentExtractor` parses sentences, extracts new patterns
3. `LearningLoop.is_novel()` checks against existing vocabulary
4. Novel fragments are assigned default 8D weights and saved
5. User engagement feedback (conversation duration, re-engagement rate) adjusts weights over time

---

## 7. Performance

| Operation | Average Time | Target |
|-----------|-------------|--------|
| `NeuroBlender.synthesize()` | ~3.5ms | < 100ms ✓ |
| Fragment count (decomposed) | ~101 fragments | Scalable |
| Config fragments | 30+ hand-crafted | Growing |

---

## 8. File Reference

| File | Purpose | Key Classes |
|------|---------|-------------|
| `apps/backend/src/ai/response/composer.py` | Core NGR implementation | NeuroFragment, NeuroVocabulary, NeuroBlender, ResponseComposer |
| `apps/backend/src/ai/response/learning_loop.py` | Autonomous linguistic evolution | FragmentExtractor, LearningLoop |
| `apps/backend/src/ai/response/__init__.py` | Module exports | Exports all NGR classes |
| `apps/backend/src/services/chat_service.py` | Main integration point | NGR Phase D (empathy alignment) |
| `apps/backend/src/services/angela_llm_service.py` | Fallback LLM service | `_try_neuro_blender()` |
| `apps/backend/src/config/angela_core.yaml` | Fragment definitions | `neuro_fragments:` section |
| `apps/backend/src/core/config_loader.py` | Config loading | Double-layer merge (Authority + Learned) |
