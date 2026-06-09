# Panoramic Mixed Training Plan

## 全景混合增量訓練計畫

> **Version**: 1.0  
> **Status**: Draft  
> **Scope**: All project-internal model/data sources × all training systems  
> **Excluded**: External LLM backends (Ollama/OpenAI/Anthropic/Google), FOREST/BIOME/ECOSYSTEM tiers (not implemented)

---

## 1. System Inventory — 完整資產清單

### 1.1 Training Systems (Trainers)

| # | System | Class | File | Train Type | Status | Connected |
|---|--------|-------|------|-----------|--------|-----------|
| T1 | ED3NTrainer | `ED3NTrainer` | `ai/ed3n/ed3n_trainer.py:25` | Supervised+Hebbian (dict+network) | ✅ | ✅ to ED3NEngine |
| T2 | SequenceTrainer | `SequenceTrainer` | `ai/ed3n/ed3n_trainer.py:291` | Sequential prediction + scheduled sampling | ✅ | ❌ never called in pipeline |
| T3 | JointTrainer | `JointTrainer` | `ai/ed3n/ed3n_trainer.py:396` | Combined dict+seq+anchor loss | ✅ | ❌ never called in pipeline |
| T4 | GARDEN Engine | `GARDENEngine.learn_from_interaction()` | `ai/garden/garden_engine.py:298` | Online Hebbian (dictionary + SNN) | ✅ | ✅ via GARDEN |  
| T5 | TensorSNNCore | `TensorSNNCore.hebbian_update()` | `ai/garden/snn_core.py:269` | Hebbian Oja's rule | ✅ | ✅ via GARDENEngine |
| T6 | ContinuousLearning | `ContinuousLearningPipeline` | `ai/ed3n/continuous_learning.py:39` | Online auto-growth + periodic train | ✅ | ✅ wired to ChatService |
| T7 | CrossModalTrainer | `CrossModalTrainer` | `ai/ed3n/multimodal/cross_modal_trainer.py:44` | Co-occurrence mapping (text/img/audio) | ✅ | ❌ not wired to chat |
| T8 | ED3N CoreNetwork | `CoreNetwork.train_step()` | `ai/ed3n/core_network.py:222` | Hebbian weight adjustment | ✅ | ✅ via ED3NTrainer |
| T9 | Neuroplasticity | `NeuroplasticitySystem` | `core/bio/neuroplasticity_core.py:217` | LTP/LTD/Hebbian/Ebbinghaus | ✅ | ❌ isolated — not wired to ED3N/GARDEN |
| T10 | LearningOrchestrator | `LearningOrchestrator` | `ai/meta/learning_orchestrator.py:16` | Meta-learning cycle (execute-evaluate-adapt) | ✅ | ❌ isolated |
| T11 | AdaptiveLearningCtrl | `AdaptiveLearningController` | `ai/meta/adaptive_learning_controller.py:43` | Dynamic LR/strategy adaptation | ✅ | ❌ isolated |
| T12 | MemoryLearningEngine | `MemoryLearningEngine` | `ai/memory/memory_learning.py:19` | Feedback-based template optimization | ✅ | ✅ via ED3NLearningIntegration |
| T13 | TrainingCoordinator | `TrainingCoordinator` | `ai/core/training_coordinator.py:37` | Cross-model dedup + domain routing | ✅ | ❌ not called before training |

### 1.2 Data Sources

| # | Source | Format | Entries | Domain | Loader Exists? | Used in Pipeline? |
|---|--------|--------|---------|--------|----------------|-------------------|
| D1 | `presets.json` (ED3N) | JSON | 33 reflex + 37 dict | greeting, general | ✅ `ED3NEngine.load_presets()` | ✅ |
| D2 | `math_presets.json` (ED3N) | JSON | 15 arith + 5 logic | math, logic | ✅ `ED3NEngine.load_presets()` | ✅ |
| D3 | `conversation.json` (GARDEN) | JSON | 39 reflex + 0 dict | conversation | ✅ `GARDENEngine.load_presets()` | ✅ |
| D4 | `science_knowledge.json` (GARDEN) | JSON | ~40 dict entries | science | ✅ `GARDENEngine.load_presets()` | ✅ |
| D5 | `emotion_knowledge.json` (GARDEN) | JSON | 7 dict entries | emotion | ✅ `GARDENEngine.load_presets()` | ✅ |
| D6 | `arithmetic_train_dataset.json` | JSON | 60,000 | math | ✅ `train_pipeline.py:load_all_data()` | ✅ |
| D7 | `arithmetic_test_dataset.csv` | CSV | 2,000 | math (eval) | ✅ `train_pipeline.py:load_all_data()` | ✅ |
| D8 | `logic_train.json` | JSON | 40,000 | logic | ✅ `train_pipeline.py:load_all_data()` | ✅ |
| D9 | `logic_test.json` | JSON | 800 | logic (eval) | ✅ `train_pipeline.py:load_all_data()` | ✅ |
| D10 | `alpaca_data.json` | JSON | 52,002 | general | ❌ `load_all_data()` skips it | ❌ |
| D11 | `knowledge_extra.json` | JSON | 467 | CS knowledge | ✅ `train_pipeline.py:load_all_data()` | ✅ |
| D12 | `templates_data.json` | JSON | 79 | conversation | ❌ | ❌ |
| D13 | `ai-trpg-codex.json` | JSON | ~200 items | game/world | ❌ | ❌ |
| D14 | `qwen3.5_vocab.txt` | Text | 248,320 tokens | tokenizer | ❌ | ❌ |
| D15 | `ollama_cat_formulas_log.json` | JSON | 24 | chat (low quality) | ❌ | ❌ |
| D16 | Lightweight model jsons | JSON | 2 files | logic/math ops | ❌ | ❌ |
| D17 | Knowledge bases (LingCat, MikoAI, etc.) | JSON/YAML | 5 files | persona/emotion | ❌ | ❌ |

### 1.3 Isolated Engines — Need Wiring

| # | Engine | Location | Current Status | Target Connection |
|---|--------|----------|---------------|-------------------|
| E1 | MathRippleEngine | `ai/memory/math_ripple_engine.py:445` | Standalone, only cognitive_pipeline references it | Wire to ED3N: math query → ripple compute → result → dictionary |
| E2 | FormulaEngine | `ai/formula_engine/__init__.py:20` | Standalone, dispatches to calculator tool | Wire to ED3N: formula pattern match → dispatch → store result |
| E3 | HSMFormulaSystem | `core/hsm_formula_system.py:28` | Standalone, only injected into prompt | Inject results into StateMatrix4D theta axis |
| E4 | ActiveCognitionFormula | `core/active_cognition_formula.py:116` | Standalone, only injected into prompt | Inject stress/order → StateMatrix4D |
| E5 | LifeIntensityFormula | `core/life_intensity_formula.py:119` | Standalone, only injected into prompt | Inject knowledge→constraint ratio → StateMatrix4D |
| E6 | CDMCognitiveDividendModel | `core/cdm_dividend_model.py:122` | Standalone | Wire to LearningOrchestrator for cognitive resource allocation |
| E7 | CausalReasoningEngine | `ai/reasoning/causal_reasoning_engine.py:7` | Standalone | Wire to ED3NLearningIntegration for causal insight |
| E8 | LogicUnit | `ai/memory/lu_logic/logic_unit.py:103` | Standalone rule engine | Wire to ED3N CoreNetwork for logic inference |
| E9 | Two UnifiedSymbolicSpace | `symbolic_space/` + `alignment/` | ⚠️ Same name, different impls, no relation | Merge: alignment version → use SQLite-backed one |
| E10 | HybridRouter | `ai/garden/hybrid_router.py:62` | Standalone, never called in chat flow | Wire as ModelBus tier-1 fallback |
| E11 | SequenceTrainer | `ed3n_trainer.py:291` | Has train_step but NO save() method | Add save/load |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FUSION LAYER                           │
│  Pipeline: DataSource → Normalizer → DomainTagger → ExampleFactory │
│                                                                     │
│  D1-D5  Config JSONs ──────► load_presets() ────► Dict entries      │
│  D6-D9  Arithmetic/Logic ──► load_all_data() ──► TrainingExample    │
│  D10    Alpaca ─────────────► AlpacaAdapter ───► TrainingExample    │
│  D11    knowledge_extra ────► load_all_data() ──► TrainingExample    │
│  D12    templates_data ─────► TemplateAdapter ──► SeqExample         │
│  D13    ai-trpg-codex ──────► CodexAdapter ────► TrainingExample    │
│  D14    qwen3.5_vocab ──────► (tokenizer-side, not in pipeline)     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                     DOMAIN ROUTING LAYER                           │
│  TrainingCoordinator.assign_domain()                                │
│                                                                     │
│  ┌──────────┬──────────────┬──────────┬───────────────────────┐    │
│  │ Domain   │ Owner        │ Trainer  │ Data Sources          │    │
│  ├──────────┼──────────────┼──────────┼───────────────────────┤    │
│  │ greeting │ ED3N         │ ED3NTnr  │ D1 presets            │    │
│  │ math     │ ED3N         │ SeqTrnr  │ D2, D6 (60K)          │    │
│  │ logic    │ ED3N         │ ED3NTnr  │ D2, D8 (40K)          │    │
│  │ reflex   │ ED3N         │ ED3NTnr  │ D1, D3                 │    │
│  │ general  │ ED3N+GARDEN  │ JointTnr │ D10 (52K)             │    │
│  │ knowledg │ GARDEN       │ GARDEN   │ D4, D5, D11 (467)     │    │
│  │ convers  │ ED3N+GARDEN  │ SeqTrnr  │ D3, D12               │    │
│  │ emotion  │ GARDEN       │ GARDEN   │ D5                    │    │
│  │ world    │ GARDEN       │ GARDEN   │ D13 (~200)            │    │
│  └──────────┴──────────────┴──────────┴───────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                      TRAINING EXECUTION LAYER                      │
│  Runs: Phase 1 → Phase 2 → Phase 3 → ...                           │
│                                                                     │
│  ┌────────────────────┐    ┌────────────────────┐                  │
│  │  ED3N Trainers     │    │  GARDEN Trainer    │                  │
│  │                    │    │                    │                  │
│  │  ED3NTrainer ──────┤    │  learn_from_       │                  │
│  │  (dict + network)  │    │  interaction()     │                  │
│  │                    │    │  → Hebbian SNN     │                  │
│  │  SequenceTrainer ──┤    │  → dictionary grow │                  │
│  │  (sequential pred) │    └────────────────────┘                  │
│  │                    │                                             │
│  │  JointTrainer ─────┤    ┌────────────────────┐                  │
│  │  (combined loss)   │    │  Neuroplasticity   │                  │
│  └────────────────────┘    │  System (LTP/LTD)  │                  │
│                            │  → SNN consolidation                 │
│  ┌────────────────────┐    └────────────────────┘                  │
│  │  CrossModalTrainer │                                            │
│  │  (co-occurrence)   │    ┌────────────────────┐                  │
│  │  → sync to network │    │  Meta-Learning     │                  │
│  └────────────────────┘    │  LearningOrch.     │                  │
│                            │  AdaptiveCtrl.     │                  │
│  ┌────────────────────┐    └────────────────────┘                  │
│  │  ContinuousLearn   │                                            │
│  │  Pipeline (online  │    ┌────────────────────┐                  │
│  │  auto-growth)      │    │  Engines (Ripple,  │                  │
│  └────────────────────┘    │  Formula, Causal)  │                  │
│                            │  → wire to ED3N    │                  │
│                            └────────────────────┘                  │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                     CROSS-SYSTEM SYNC LAYER                        │
│                                                                     │
│  TrainingCoordinator.sync_reflex_patterns(ED3N ⇄ GARDEN)          │
│  CrossModalTrainer.synchronize_to_network() → CoreNetwork          │
│  ED3NLearningIntegration → bridge to HAM/Replay/Memory            │
│  StateMatrix4D ← CognitiveOperations (math/spatial results)        │
│  NeuroplasticitySystem.consolidate_memories() → GARDEN SNN        │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                      VALIDATION LAYER                              │
│                                                                     │
│  84 ED3N tests + 50 GARDEN tests = 134 baseline (zero regression)  │
│  TrainingCoordinator accuracy tracking by domain                    │
│  logic_test.json (800) + arithmetic_test.csv (2000)                │
│  Generation quality tests (sad/physics/computer/bye)               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Migration Plan — 孤立系統遷移

### 3.1 Systems to move

| System | From | To | Reason |
|--------|------|----|--------|
| MathRippleEngine | `ai/memory/math_ripple_engine.py` | `ai/ed3n/engines/` | Belongs with ED3N ecosystem — math is ED3N domain |
| FormulaEngine | `ai/formula_engine/` | `ai/ed3n/engines/` | Formula pattern match → ED3N dispatch |
| LogicUnit | `ai/memory/lu_logic/` | `ai/ed3n/engines/` | Logic is ED3N domain per TrainingCoordinator |
| HybridRouter | `ai/garden/hybrid_router.py` | `ai/core/` | Should serve both ED3N+GARDEN as shared router |
| CrossModalTrainer | `ai/ed3n/multimodal/` | `ai/ed3n/` (top-level) | Not truly "multimodal" in current form; text-only co-occurrence |
| SequenceTrainer save() | - | Add to `ed3n_trainer.py` | Missing persistence, blocking checkpoint |

### 3.2 Engines that stay (receive wiring only, not moved)

| Engine | Location | Wire to |
|--------|----------|---------|
| NeuroplasticitySystem | `core/bio/neuroplasticity_core.py` | GARDEN TensorSNNCore (as alternative Hebbian) |
| CausalReasoningEngine | `ai/reasoning/causal_reasoning_engine.py` | ED3NLearningIntegration |
| HSMFormulaSystem | `core/hsm_formula_system.py` | StateMatrix4D theta axis |
| ActiveCognitionFormula | `core/active_cognition_formula.py` | StateMatrix4D epsilon axis |
| LifeIntensityFormula | `core/life_intensity_formula.py` | StateMatrix4D delta axis |
| CDMCognitiveDividendModel | `core/cdm_dividend_model.py` | LearningOrchestrator |

### 3.3 Code changes needed

```
# File: ai/ed3n/ed3n_trainer.py — ADD save/load to SequenceTrainer
class SequenceTrainer:
    def save(self, path: str) -> None:
        ...  # serialize scheduled_sampling_prob + history

    @classmethod
    def load(cls, path: str, engine) -> "SequenceTrainer":
        ...

# File: ai/ed3n/ed3n_trainer.py — ADD JointTrainer save/load
class JointTrainer:
    def save(self, path: str) -> None:
        ...
    @classmethod
    def load(cls, path: str, engine) -> "JointTrainer":
        ...

# File: ai/core/training_coordinator.py — ensure assign_domain is called
# BEFORE training in all paths (currently not called by existing pipeline)

# File: scripts/train_pipeline.py — expand to call ALL trainers
```

### 3.4 New directories to create

```
apps/backend/src/ai/ed3n/engines/
  __init__.py
  math_ripple_adapter.py    # wraps MathRippleEngine for ED3N use
  formula_adapter.py         # wraps FormulaEngine for ED3N use
  logic_adapter.py           # wraps LogicUnit for ED3N use
```

---

## 4. Training Phases — 執行階段

### Phase 0: Pre-Migration (cleanup + wiring)

| Step | Action | Files Changed |
|------|--------|---------------|
| 0.1 | Add SequenceTrainer.save() | `ed3n_trainer.py` |
| 0.2 | Add JointTrainer.save() | `ed3n_trainer.py` |
| 0.3 | Create `ed3n/engines/` adapters | 3 new files |
| 0.4 | Wire MathRipple → ED3N (math query → ripple → result dict) | `engines/math_ripple_adapter.py` |
| 0.5 | Wire FormulaEngine → ED3N (formula pattern → dispatch) | `engines/formula_adapter.py` |
| 0.6 | Wire LogicUnit → ED3N (logic rules → CoreNetwork) | `engines/logic_adapter.py` |
| 0.7 | Wire HybridRouter into ModelBus fallback chain | `model_bus.py`, `hybrid_router.py` |
| 0.8 | Wire TrainingCoordinator into pipeline (ensure assign_domain is called) | `train_pipeline.py` |
| 0.9 | Merge two UnifiedSymbolicSpace → alignment uses SQLite version | `alignment/reasoning_system.py` |
| 0.10 | Re-run 134 tests to verify zero regression | — |

### Phase 1: Data Fusion (load ALL sources)

| Step | Action | Data Added | Target Trainer |
|------|--------|-----------|---------------|
| 1.1 | Load ED3N presets → dict entries | 70 entries | ED3NTrainer dict phase |
| 1.2 | Load GARDEN configs → dict entries | ~86 entries | GARDEN dict phase |
| 1.3 | Load arithmetic_train (60K) → TrainingExamples | 60,000 math | SequenceTrainer |
| 1.4 | Load logic_train (40K) → TrainingExamples | 40,000 logic | ED3NTrainer |
| 1.5 | Load alpaca (52K) → TrainingExamples | 52,000 general | JointTrainer |
| 1.6 | Load knowledge_extra → GARDEN interaction | 467 knowledge | GARDENEngine |
| 1.7 | Load templates_data → SeqExamples | 79 dialog | SequenceTrainer |
| 1.8 | Load ai-trpg-codex → GARDEN interaction | ~200 world | GARDENEngine |
| 1.9 | Load LingCat/MikoAI knowledge → dict entries | 5 persona | ED3N dictionary |
| 1.10 | **Total fused** | **~152,872** | — |

### Phase 2: ED3N Basic Training

| Step | Action | Epochs | Target |
|------|--------|--------|--------|
| 2.1 | Dictionary growth from presets + configs | — | 156 dict entries |
| 2.2 | ED3NTrainer on logic (40K) | 5 | Loss < 0.3, Acc > 75% |
| 2.3 | ED3NTrainer on alpaca subset (10K) | 3 | General pattern coverage |
| 2.4 | ED3NTrainer on knowledge_extra (467) | 3 | Knowledge domain coverage |

### Phase 3: Sequence Training

| Step | Action | Epochs | Target |
|------|--------|--------|--------|
| 3.1 | SequenceTrainer on arithmetic (60K) | 8 | Loss < 0.05, Acc > 98% |
| 3.2 | SequenceTrainer on templates (79) | 8 | Conversation flow |
| 3.3 | SequenceTrainer on alpaca response chains (10K) | 5 | Response coherence |

### Phase 4: Mixed Training

| Step | Action | Epochs | Target |
|------|--------|--------|--------|
| 4.1 | JointTrainer on combined preset+alpaca (52K+152) | 10 | Loss < 0.01, Acc > 99% |
| 4.2 | GARDEN learn_from_interaction on knowledge (467+200) | — | SNN weight update |
| 4.3 | CrossModalTrainer sync (if image/audio keys exist) | — | Network mapping |

### Phase 5: Cross-System Sync

| Step | Action | Target |
|------|--------|--------|
| 5.1 | TrainingCoordinator.sync_reflex_patterns(ED3N → GARDEN) | Pattern mirroring |
| 5.2 | TrainingCoordinator.sync_reflex_patterns(GARDEN → ED3N) | Bidirectional sync |
| 5.3 | NeuroplasticitySystem.consolidate_memories() → GARDEN SNN | LTP/LTD consolidation |
| 5.4 | ED3NLearningIntegration → bridge to HAM memory | Knowledge persistence |
| 5.5 | Engine adapters (Ripple/Formula/Logic) → inject results into dictionary | Math capability |

### Phase 6: Validation

| Step | Action | Expected |
|------|--------|----------|
| 6.1 | Run 84 ED3N tests | Zero regression |
| 6.2 | Run 50 GARDEN tests | Zero regression |
| 6.3 | Arithmetic eval (arithmetic_test.csv 2K) | > 90% accuracy |
| 6.4 | Logic eval (logic_test.json 800) | > 85% accuracy |
| 6.5 | Generation quality test: "sad" → "I'm here for you..." | Pass |
| 6.6 | Generation quality test: "physics" → "力 重力 运动 能量" | Pass |
| 6.7 | Generation quality test: "computer" → "程序 网络 人工智能" | Pass |
| 6.8 | Math query → MathRippleEngine → correct computation | Pass |
| 6.9 | Formula pattern → FormulaEngine → correct dispatch | Pass |

---

## 5. Data Format Mappings

### 5.1 External Data → TrainingExample

```
Source: arithmetic_train_dataset.json
{"problem": "178 + 101", "answer": "279"}
  → TrainingExample(
      input_text="178 + 101",
      expected_output="279",
      input_keys=["178", "plus", "101"],        # tokenized
      output_keys=["279"],
      relation_pairs=[("178", "operation", "101"), ("178", "result", "279")],
      confidence=0.9,
      metadata={"domain": "math"},
    )

Source: logic_train.json
{"proposition": "明天会下雨 或 温度高于零度 是否成立", "answer": false}
  → TrainingExample(
      input_text="明天会下雨 或 温度高于零度 是否成立",
      expected_output="false",
      input_keys=["proposition_1", "proposition_2", "or_op"],  # encoded
      output_keys=["false"],
      relation_pairs=[("or_op", "evaluates_to", "false")],
      confidence=0.9,
      metadata={"domain": "logic"},
    )

Source: alpaca_data.json
{"instruction": "Explain gravity", "input": "", "output": "Gravity is a force..."}
  → TrainingExample(
      input_text="Explain gravity",
      expected_output="Gravity is a force...",
      input_keys=["explain", "gravity"],    # dictionary encoded
      output_keys=["gravity", "force", ...], # dictionary encoded
      relation_pairs=[("gravity", "mapping", "force")],
      confidence=0.8,
      metadata={"domain": "general"},
    )
```

### 5.2 External Data → SequenceExample

```
Source: arithmetic_train_dataset.json
{"problem": "178 + 101", "answer": "279"}
  → SequenceExample(
      input_text="178 + 101",
      target_text="279",
      input_key_seq=["178", "plus", "101"],     # sequential, ordered
      target_key_seq=["279"],
      confidence=0.9,
    )

Source: templates_data.json
  → SequenceExample(
      input_text="hello",
      target_text="Hello! How can I help?",
      input_key_seq=["greeting", "hello"],
      target_key_seq=["response", "greeting", "offer_help"],
      confidence=0.8,
    )
```

---

## 6. Connectivity Audit — Full Wiring Matrix

### 6.1 Chat Flow (user → ... → response)

```
User Input
  → [API] chat_routes.py
  → [Service] AngelaLLMService.generate_response()
    → [Step 1] TemplateMatcher.match() → 0.8+ → COMPOSED (return)
    → [Step 2] MemoryIntegration → HAM hit → return
    → [Step 3] NeuroAutoSelector → backend selection
    → [Step 4] LLM Backend.generate()
    → [Fallback] ModelBus.route()
      → [T0] HybridRouter (NEW: wire in)
        → reflex → ED3N
        → knowledge → GARDEN
        → math → ED3N → MathRippleAdapter (NEW)
        → creative → template
      → [T1] ED3NBackend.generate()
        → ED3NEngine.process()
          → ReflexLayer (O(1) pattern match)
          → DictionaryLayer.encode()
          → CoreNetwork.forward()
          → StepDecoder.generate()
      → [T2] GARDENBackend.generate()
        → GARDENEngine.process()
          → ReflexLayer
          → VectorDictionary.encode()
          → TensorSNNCore.forward()
          → VectorDecoder.generate()
      → [T3] NeuroBlender.synthesize()
      → [T4] TemplateLibrary fallback
```

### 6.2 Training Flow

```
Pipeline entry: scripts/train_pipeline.py
  → [Phase 1] DataFusion.load_all()
  → [Phase 2] TrainingCoordinator.assign_domain() per sample
  → [Phase 3] ED3NTrainer.train_step(Batch) — for reflex/math/logic
  → [Phase 4] SequenceTrainer.train_step(SeqBatch) — for arith sequences
  → [Phase 5] JointTrainer.train_step(TrainBatch, SeqBatch) — for mixed
  → [Phase 6] GARDENEngine.learn_from_interaction() — for knowledge
  → [Phase 7] CrossModalTrainer.synchronize_to_network()
  → [Phase 8] NeuroplasticitySystem.consolidate_memories()
  → [Phase 9] TrainingCoordinator.sync_reflex_patterns()
  → [Phase 10] Engine adapters (Ripple/Formula/Logic) → inject to dict
  → [Save] All trainers save()
  → [Validate] Run test suite + eval benchmarks
```

### 6.3 Current Wiring Issues to Fix

| Issue | Severity | Fix |
|-------|----------|-----|
| HybridRouter not called in chat | HIGH | Wire into ModelBus fallback chain |
| SequenceTrainer has no save() | HIGH | Add save/load methods |
| JointTrainer has no save() | HIGH | Add save/load methods |
| TrainingCoordinator.assign_domain not called | MEDIUM | Call before each training batch |
| CrossModalTrainer not wired to chat | MEDIUM | Wire when image/audio input exists |
| NeuroplasticitySystem not connected | MEDIUM | Wire to GARDEN SNN consolidation cycle |
| Two UnifiedSymbolicSpace (same name) | MEDIUM | Merge into one |
| MathRippleEngine standalone | LOW | Create adapter → wire to ED3N |
| FormulaEngine standalone | LOW | Create adapter → wire to ED3N |
| LogicUnit standalone | LOW | Create adapter → wire to ED3N |

---

## 7. File Changes Summary

### Files to modify:

| File | Changes |
|------|---------|
| `scripts/train_pipeline.py` | Data fusion for ALL sources, call all 3 trainers, wire adapters |
| `ai/ed3n/ed3n_trainer.py` | Add SequenceTrainer.save/load, JointTrainer.save/load |
| `ai/core/training_coordinator.py` | Ensure assign_domain is called before each training step |
| `ai/garden/hybrid_router.py` | Expose callable interface for ModelBus |
| `ai/core/model_bus.py` | Wire HybridRouter as tier-0 fallback |
| `ai/alignment/reasoning_system.py` | Use SQLite-backed UnifiedSymbolicSpace |
| `docs/06-project-management/plans/PANORAMIC_MIXED_TRAINING_PLAN.md` | This file |

### Files to create:

| File | Purpose |
|------|---------|
| `ai/ed3n/engines/__init__.py` | Package init |
| `ai/ed3n/engines/math_ripple_adapter.py` | Wraps MathRippleEngine for ED3N math queries |
| `ai/ed3n/engines/formula_adapter.py` | Wraps FormulaEngine for ED3N formula dispatch |
| `ai/ed3n/engines/logic_adapter.py` | Wraps LogicUnit for ED3N logic inference |

### No new files needed for:

| System | Justification |
|--------|---------------|
| NeuroplasticitySystem | Stays in `core/bio/`, wire via import in training sync phase |
| CausalReasoningEngine | Stays in `ai/reasoning/`, wire via ED3NLearningIntegration |
| HSM/ActiveCognition/LifeIntensity | Stays in `core/`, wire via StateMatrix4D adapter |

---

## 8. Post-Training Verification

### Metrics to track

| Metric | Current Baseline | Target After Pipeline |
|--------|-----------------|----------------------|
| ED3N dict entries | 74 | 200+ (from all data sources) |
| GARDEN vocab | 87 | 300+ |
| SequenceTrainer loss | 0.009 | < 0.01 (hold) |
| SequenceTrainer acc | 99.93% | > 99.5% (hold) |
| ED3NTrainer acc | ~77.7% | > 85% (from logic training) |
| Arithmetic accuracy | untested | > 90% on test set |
| Logic accuracy | untested | > 85% on test set |
| 134 tests | pass | zero regression |
| Math queries | no coverage | MathRippleEngine responds |
| Domain report domains | 0 | 8+ tracked by coordinator |

### Validation commands

```bash
# Run all tests
pytest tests/

# Run evaluation benchmarks
python scripts/train_pipeline.py  # full pipeline

# Domain report
coordinator.get_domain_report()

# Generation quality
python -c "
from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine
e = ED3NEngine()
e.load_presets()
for q in ['sad', 'physics', 'computer', '178+101']:
    print(f'{q}: {e.process(q)}')
"
```

---

## 9. Existing Script vs. Expanded Pipeline

```
train_pipeline.py (CURRENT)                 train_pipeline.py (EXPANDED)
────────────────────────────                 ────────────────────────────
[1] Load math/logic/knowledge                [1] Load ALL 13+ data sources
[2] Init ModelBus + Coordinator              [2] Init ALL trainers
[3] Deconflict samples                       [3] Domain routing + deconflict
[4] ED3N train (2 epochs, basic)             [4] ED3NTrainer (5 epochs)
[5] GARDEN learn_from_interaction            [5] SequenceTrainer (8 epochs)
[6] Sync ED3N→GARDEN                         [6] JointTrainer (10 epochs)
[7] Save checkpoints                         [7] GARDEN learn_from_interaction
[8] Evaluate                                 [8] CrossModal sync
                                             [9] Neuroplasticity consolidate
                                             [10] Engine adapters inject
                                             [11] Sync bidirectional
                                             [12] Save ALL checkpoints
                                             [13] Full evaluation suite
                                             [14] Domain report
```

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| sentence-transformers blocked on Python 3.14 | Certain | MEDIUM | TF-IDF fallback already in place; plan uses it |
| Alpaca 52K examples overwhelm Hebbian learning | Medium | LOW | Subset sampling (10K batch, shuffle) |
| MathRippleEngine integration conflicts | Low | MEDIUM | Adapter pattern isolates changes |
| LogicUnit rule engine conflicts with DictionaryLayer encode | Low | LOW | Logic adapter normalizes before ED3N call |
| Test regression after wiring changes | Medium | HIGH | Run 134 tests after each change |
| SequenceTrainer/JointTrainer save format compatibility | Low | LOW | Version field in saved JSON |
| GARDEN dense tensor memory with 600+ vocab | Low | MEDIUM | 600×600×4 = 1.44 MB — still tiny |

---

## Appendix A: Data Source Details

| Source | Path | Load Function | Output Type |
|--------|------|--------------|-------------|
| ED3N presets | `src/ai/ed3n/config/presets.json` | `load_presets()` | dict entries |
| ED3N math | `src/ai/ed3n/config/math_presets.json` | `load_presets()` | dict entries |
| GARDEN conversation | `src/ai/garden/config/conversation.json` | `load_presets()` | reflex + dict |
| GARDEN science | `src/ai/garden/config/science_knowledge.json` | `load_presets()` | dict entries |
| GARDEN emotion | `src/ai/garden/config/emotion_knowledge.json` | `load_presets()` | dict entries |
| Arithmetic train | `data/raw_datasets/arithmetic_train_dataset.json` | `load_all_data()` | TrainExample |
| Arithmetic test | `data/raw_datasets/arithmetic_test_dataset.csv` | `load_all_data()` | TrainExample |
| Logic train | `data/raw_datasets/logic_train.json` | `load_all_data()` (with parser) | TrainExample |
| Logic test | `data/raw_datasets/logic_test.json` | `load_all_data()` | TrainExample |
| Alpaca | `data/raw_datasets/alpaca_data.json` | `AlpacaAdapter.load()` | TrainExample |
| Knowledge extra | `data/raw_datasets/knowledge_extra.json` | `load_all_data()` | TrainExample |
| Templates | `src/ai/memory/templates_data.json` | `TemplateAdapter.load()` | SeqExample |
| TRPG codex | `data/trpg/ai-trpg-codex.json` | `CodexAdapter.load()` | TrainExample |
| Qwen vocab | `data/raw_datasets/qwen3.5_vocab.txt` | (tokenizer-side only) | vocabulary |
| LingCat/MikoAI | `data/knowledge_bases/*.json` | `PersonaAdapter.load()` | dict entries |
| Behaviors | `data/ai-trpg-codex.json` | `BehaviorAdapter.load()` | behavior patterns |

## Appendix B: Training System Interface Reference

| Class | Method | Input | Output |
|-------|--------|-------|--------|
| ED3NTrainer | `train_step(batch)` | `TrainingBatch` | `TrainMetrics` |
| ED3NTrainer | `train_dictionary_phase(examples)` | `List[TrainingExample]` | `TrainMetrics` |
| ED3NTrainer | `train_network_phase(examples)` | `List[TrainingExample]` | `TrainMetrics` |
| SequenceTrainer | `train_step(batch)` | `SeqBatch` | `TrainMetrics` |
| JointTrainer | `train_step(batch, seq_batch)` | `TrainingBatch`, `SeqBatch` | `TrainMetrics` |
| GARDENEngine | `learn_from_interaction(text, resp, conf)` | str, str, float | `Dict` |
| TensorSNNCore | `hebbian_update(in_keys, out_keys, lr, target)` | List, List, float, float | `float` |
| ContinuousLearningPipeline | `process_interaction(text, resp, ctx)` | str, str, Dict | `Dict` |
| CrossModalTrainer | `record_co_occurrence(text_key, img_key, aud_key)` | str, str, str | None |
| NeuroplasticitySystem | `apply_ltp/apply_ltd/consolidate_memories()` | various | various |
| TrainingCoordinator | `assign_domain(domain)` | str | `Optional[str]` |
| TrainingCoordinator | `record_training(domain, model, count, acc, examples)` | str, str, int, float, List | None |
