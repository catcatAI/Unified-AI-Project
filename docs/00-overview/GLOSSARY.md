# Glossary

This document defines key terms and concepts used throughout the Angela AI project.

## A

### AGI (Artificial General Intelligence)
Intelligent agents that understand or learn any intellectual task that a human being can. In this project, we aim for Level 3-4 AGI capabilities.

### Alpha Deep Model
A concept model that represents advanced deep learning capabilities for complex pattern recognition and decision making.

## C

### Closed-Loop Architecture
A system design where outputs are fed back as inputs to influence future behavior, enabling continuous learning and adaptation.

### Concept Models
Abstract representations of complex ideas or systems that guide AI behavior and decision-making processes.

## D

### Data Life
The philosophy that data should be treated as a living entity that can grow, evolve, and interact with its environment.

## E

### ED3N (External Dictionary Decoupled Neural Network)
Angela's primary inference engine — a hybrid SNN (Spiking Neural Network) + dictionary-lookup system for low-latency local reasoning. Uses trie-based reflex tables, LRU-cached dictionary encoding, and continuous learning pipelines. ~5,500 lines across 26 files.

### Environment Simulator
A concept model that creates virtual environments for AI training and testing.

### Eta (η) Axis
The 8th axis of the state matrix, responsible for **execution/operation layer** — module invocation, parameter adjustment, and structural drift tracking. Works in a dual-loop with θ (cognitive layer).

### 8D State Matrix (理想目標) / StateMatrix4D (實際)
The expanded state matrix (αβγδεθζη) that drives Angela's autonomous behavior. **實際代碼**: `StateMatrix4D` class (`core/engine/state_matrix.py`, 1,244 行, 6 軸 αβγδεθ) + `DimensionState` 結構體。8 軸規格（含 ζ Connectivity + η Execution）為理想架構目標，尚未完全實作。

## G

### GARDEN (Giant Associative Relation Decoupled Evolutionary Network)
Lightweight local inference engine complementing ED3N. Provides vector semantic search via `VectorDictionary` (+ optional SentenceTransformer) and sparse SNN inference via `TensorSNNCore`. ~2,600 lines across 9 files. Dual-backend (torch or numpy) for cross-platform compatibility.

### GVV (Geometric Vocabulary Vector)
Compositional image generation pipeline: ConceptMapper → GeometricVocabulary → InstanceOptimizer → LearnableDecomposer → PixelRefiner. 14 source files, ~62 tests. Part of the primitives system under `ai/multimodal/primitives/`.

## H

### HAM (Hierarchical Abstract Memory)
A memory system that organizes information in a hierarchical structure for efficient storage and retrieval. Vector store supports dual-backend (ChromaDB or numpy+JSON).

### HSP (Heterogeneous Service Protocol)
A high-speed synchronization protocol that enables collaboration between different AI services and modules.

## L

### Layered Architecture
6-layer system design: Execution/Presentation → API → Session → Services → Core → AI Engine → Theoretical Foundation.

### LearningLoop
An autonomous linguistic evolution module that extracts fragments, emoji, and collocations from LLM responses. Uses novelty detection and user engagement feedback to continuously expand Angela's expressive vocabulary.

## M

### Multi-Modal AI
AI systems that can process and understand multiple types of data (text, audio, images) simultaneously.

## N

### NGR (Neuro-Generative Response)
Angela's next-generation response system that replaces static templates with dynamic 8D-state-driven fragment composition. Pipeline: state matrix → target vector → cosine similarity scoring → fragment selection → natural assembly → output. Components: NeuroFragment, NeuroVocabulary, NeuroBlender.

### NeuroFragment
A weighted semantic fragment in the NGR system. Each NeuroFragment carries an 8D state vector (alpha through eta) that determines when it should be selected during response synthesis.

### NeuroVocabulary
The fragment registry that stores, loads from config, and decomposes templates into NeuroFragments. Managed by the ResponseComposer.

### NeuroBlender
The core synthesis engine of the NGR system. Uses cosine similarity between the current 8D state target vector and fragment state vectors to select and assemble natural-language responses.

## R

### Rovo Dev Agents
Atlassian's AI agents that can be integrated with the Unified AI Project for enhanced functionality.

## S

### Semantic-Level Security
Security mechanisms that protect data based on its meaning and context rather than just its format or location.

### StateMatrix4D
The 4-dimensional state space object exported by `core.engine.state_matrix`. Companion struct `DimensionState` represents individual axis states. See also: 8D State Matrix.

## T

### ThreeLayerVisual
Three-layer visual representation pipeline: PCA encoder → nonlinear decoder → concept space mapping from CLIP embeddings. 128-dim latent space. decoder.pt ~6.9MB. Achieves MSE 0.0042.

## U

### Unified Representation
The approach of mapping different types of data to a common symbolic space to reduce processing complexity.

## V

### VectorStore
A database system that stores and retrieves information using vector embeddings for semantic search. Dual-backend: ChromaDB (auto-detected) or pure numpy+JSON fallback.

## Z

### Zeta (ζ) Axis
The 7th axis of the state matrix, tracking temporal-narrative dimensions: temporal_coherence, memory_depth, narrative_flow, and identity_continuity. Bridges short-term narrative context with long-term identity persistence.
