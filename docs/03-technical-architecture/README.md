# Technical Architecture

This section provides in-depth documentation on the system's architecture, communication protocols, memory systems, and AI components.

## System Overview

The Unified AI Project follows a monorepo architecture organized into applications and packages. The core components include:

### Applications (`apps/`)
- **`apps/desktop-app`**: Electron + Live2D desktop companion (7 unique + 33 shared JS files).
- **`apps/backend`**: Core Python FastAPI backend (612 files, ~96K lines) — AI engines, LLM routing, memory, chat pipeline.
- **`apps/web-dashboard`**: Next.js web dashboard for developers to monitor and manage systems.
- **`apps/web-live2d-viewer`**: Web-based Live2D model viewer (10 unique JS files).
- **`apps/pixel-angela`**: PyQt6 pixel art rendering engine.
- **`apps/gemini-os-bridge`**: OS automation microservice (pyautogui).

### Packages (`packages/`)
- **`packages/cli`**: Command-line interface tools for interacting with backend services.
- **`packages/shared-js`**: Shared JavaScript utilities (33 files) used by desktop-app and web-live2d-viewer.
- **`packages/biology-core`**: AngelaDNA core library.

## Core Systems

### Heterogeneous Service Protocol (HSP)

The HSP is a high-speed synchronization protocol that enables collaboration between internal modules and external AI entities. Key features include:

- **Registration Mechanism**: New modules/AI entities joining the network
- **Reputation System**: Evaluating the trustworthiness of collaborating entities
- **Hot Updates**: Dynamic loading of new functional modules

### Hierarchical Abstract Memory (HAM) System

The HAM system manages memory in a hierarchical structure. Located at `src/ai/memory/ham_memory/` (10+ files, ~1,440 lines). Components include:

- **HAMManager**: Hierarchical semantic memory management (151 lines)
- **HAMQueryEngine**: Memory retrieval and query processing (302 lines)
- **VectorMemoryStore**: Dual-backend vector store (numpy + ChromaDB; auto-detects chromadb, falls back to pure numpy+JSON)

### AI Core Systems

The project implements several AI engines and routing components:

- **ED3N Engine**: SNN + reflex + deep learning pipeline (26 files, 5,521 lines, 114 tests) at `src/ai/ed3n/`
- **GARDEN Engine**: Lightweight associative inference (9 files, 2,586 lines, 205 tests) at `src/ai/garden/`
- **ModelBus**: Central registry + capability routing (34 tests) at `src/ai/core/model_bus.py`
- **QueryClassifier**: 16 QueryTypes for intent classification at `src/ai/core/query_classifier.py`
- **LLM Providers**: 7 providers (Anthropic, Google, OpenAI, Ollama, llama.cpp, ED3N, GARDEN) at `src/services/llm/providers/`
- **GVV Image Generation**: Compositional image generation (14 source files, ~62 tests) at `src/ai/multimodal/primitives/`

### State Matrix (6D)

The state matrix uses 6 dimensions (α β γ δ ε θ) implemented in `StateMatrix4D` at `src/core/engine/state_matrix.py` (1,244 lines). The 6D vector drives NGR fragment selection and autonomous cognition. An 8D target (adding ζ/η) exists as an architectural goal in `IDEAL_ARCHITECTURE.md`.

### Chat Pipeline

```
WebSocket → Emotion Analysis → Crisis Gate → Biological Stimulus → Alignment Gate → LLM → Causal Learning → Response
```

## Communication Layer

The communication layer facilitates interaction between different components of the system:

### Internal Communication
- Direct function calls within the same process
- Message queues for asynchronous communication
- Shared memory for high-performance data exchange

### External Communication
- RESTful APIs for web-based interactions
- WebSocket connections for real-time communication
- HSP protocol for AI-to-AI collaboration

## Data Flow Architecture

The system follows a layered data flow architecture:

1. **Input Layer**: Receives data from various sources (user input, sensors, network)
2. **Processing Layer**: Processes and analyzes the input data using AI models
3. **Memory Layer**: Stores processed information in the HAM system
4. **Decision Layer**: Makes decisions based on processed data and stored memories
5. **Action Layer**: Executes actions based on decisions
6. **Feedback Layer**: Collects feedback from actions to improve future decisions

## Security Architecture

The system implements multiple layers of security:

### Authentication
- UID/Key based authentication for all system components
- Role-based access control for different user types

### Data Protection
- Encryption for data at rest and in transit
- Semantic-level security to protect sensitive information

### Access Control
- Fine-grained permissions for different system resources
- Audit logging for all system activities

## Performance Optimization

The system incorporates several performance optimization strategies:

### Caching
- LRU-based caching for frequently accessed data
- TTL-based cache expiration to ensure data freshness

### Parallel Processing
- AsyncIO-based concurrent execution
- Thread pools for CPU-intensive tasks

### Resource Management
- Dynamic resource allocation based on system load
- Memory optimization techniques to reduce footprint

## Scalability Considerations

The architecture is designed to scale both vertically and horizontally:

### Vertical Scaling
- Efficient use of system resources
- Optimized algorithms to handle increased load on single nodes

### Horizontal Scaling
- Microservices architecture for independent scaling of components
- Load balancing for distributing workload across multiple instances

## Note on Analysis Documents

The `analysis/` subdirectory contains ~51 documents dating from 2026-02 to 2026-06. Files from 2026-02 (test reports, fix reports, completion reports) are **historical records** — the issues they describe have been resolved. Files from 2026-05 (WIRING_MAP, MODULARITY_ANALYSIS, CODE_STATISTICS, etc.) are **partially outdated** — many self-identify as ~30% stale. For current architecture state, see:
- `docs/COMPREHENSIVE_AUDIT_2026-06-25.md` (latest architecture audit)
- `docs/IDEAL_ARCHITECTURE.md` (target architecture)
- `AGENTS.md` (current code statistics and structure)

## Monitoring and Observability

The system includes comprehensive monitoring capabilities:

### Metrics Collection
- Real-time performance metrics
- Resource utilization tracking
- Error rate monitoring

### Logging
- Structured logging for easy analysis
- Log aggregation for centralized monitoring
- Debug logging for troubleshooting

### Alerting
- Threshold-based alerting for critical metrics
- Anomaly detection for unusual system behavior