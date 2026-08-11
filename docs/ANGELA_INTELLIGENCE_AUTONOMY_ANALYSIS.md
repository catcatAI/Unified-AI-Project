# Angela Intelligence, Autonomy & Conversation Pipeline — Deep Analysis

> Version: 1.0 — 2026-08-11
> Status: ACTIVE — Findings + Implementation Plan
> Author: Angela Review Engine §X #265

---

## 1. Intelligence Assessment

### 1.1 Actual Intelligence Components

| System | Rating | What It Actually Does | Contribution |
|--------|--------|----------------------|--------------|
| **MathVerifier** | ✅ REAL | Python AST arithmetic, trig, number theory, Chinese numerals | Genuine computation — strongest native intelligence |
| **Symbolic Reasoner** | ✅ REAL | Transitive/syllogism/calendar/qty inference | Real logical deduction |
| **Knowledge Base** | ✅ REAL (tiny) | ~100 hardcoded facts with keyword retrieval | Real but extremely limited scope |
| **Relational Chain** | ✅ REAL | Directed graph from comparisons, transitive closure | Real inference over stated facts |
| **QueryClassifier** | 🔶 PATTERN | 16 types via regex + keyword matching | Routing signal, no understanding |
| **ModelBus** | 🔶 PATTERN | Static routing table per query type | Dispatch, no learning |
| **ED3N SNN** | 🔶 PATTERN | LIF neurons, weight matrix × activation | Real computation but noisy without training |
| **GARDEN** | 🔶 PATTERN | Pseudo-embeddings + cosine similarity | Lookup, not semantic understanding |
| **CausalReasoning** | 🔶 PATTERN | Pearson/F-test but simplified do-calculus | Real stats, fabricated warm-start |
| **LLM Integration** | 🔶 PASS | Routes to cloud LLM for creative/knowledge | Actual intelligence when LLM available |
| **Training Pipeline** | 🔶 PATTERN | Converges on training set, doesn't generalize | Deterministic routers provide accuracy |

### 1.2 Intelligence Without LLM

When no LLM is available, Angela is a **sophisticated FAQ bot**:
- ✅ Math: `3 + 5 * 2` → `13` (via MathVerifier)
- ✅ Logic: `A>B, B>C → A>C?` → `true` (via Symbolic Reasoner)
- ✅ Facts: `法國首都是什麼` → `巴黎` (via Knowledge Base)
- ✅ Reflex: `你好` → `你好！我是 Angela` (via pattern match)
- ❌ Open-domain: `談談量子力學` → `抱歉，我沒理解你的意思`

### 1.3 Intelligence Upper Limit

| Factor | Current | Achievable | Ceiling |
|--------|---------|------------|---------|
| **Deterministic engines** | Math + Logic + ~100 facts | Expand to algebra, calculus, physics engine | Bounded by implementation effort |
| **Neural (ED3N/GARDEN)** | Random without training | Meaningful with real training data | Bounded by SNN architecture (associative, not generative) |
| **LLM delegation** | Claude/GPT/Gemini/Ollama | Better prompts, chain-of-thought | Bounded by external LLM capability |
| **Knowledge** | 100 facts | Expand KB, add RAG over documents | Bounded by retrieval quality |
| **Reasoning** | Structured patterns | Add planner, theorem prover | Bounded by symbolic engine scope |

**Verdict**: Angela's intelligence is **primarily LLM-dependent**. Native intelligence covers math/logic/facts but not open-domain reasoning. The SNN engines add associative memory but not generative capability.

### 1.4 Improvement Roadmap

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| P0 | Expand knowledge base to 1000+ facts | Medium | High — more questions answerable natively |
| P0 | Add proper embedding model (sentence-transformers) | Low | High — real semantic search |
| P0 | Improve symbolic reasoner (algebra, sets) | Medium | Medium — more logic types |
| P1 | Train ED3N/GARDEN on real data | High | Medium — meaningful associative memory |
| P1 | Add chain-of-thought prompting for LLM | Low | High — better reasoning via LLM |
| P2 | Implement planner (HTN or STRIPS) | High | Medium — multi-step problem solving |
| P2 | Add external tool use (Wikipedia, calculators) | Medium | High — expanded capability |

---

## 2. Autonomy Assessment

### 2.1 What Angela CAN Do Autonomously

| Capability | Mechanism | Status |
|------------|-----------|--------|
| Monitor user activity | UserMonitor | ✅ Working |
| Track system health | Heartbeat | ✅ Working |
| Make internal decisions | AutonomousLifeCycle | ✅ Working (internal state) |
| Adjust routing parameters | PriorityNegotiator voters | ✅ Working |
| Evolve personality traits | EvolutionEngine | ✅ Working (internal state) |
| Enter rest/sleep states | DigitalLifeIntegrator | ✅ Working (passive) |
| Broadcast messages (if triggered) | BehaviorExecutor | ✅ Working |
| Detect interaction opportunities | ProactiveInteractionSystem | ✅ Working (detection) |

### 2.2 What Angela CANNOT Do (But Should)

| Capability | Why Missing | Impact |
|------------|-------------|--------|
| **Initiate conversation from internal state** | ProactiveInteractionSystem not wired to lifespan | HIGH — Angela is reactive only |
| **Stream tokens to frontend in real-time** | StreamingPipeline only used for document stream | MEDIUM — UX delay |
| **Self-directed learning** | All learning requires user input | MEDIUM — no growth without interaction |
| **Respect user boundaries** | No "do not disturb" or opt-out | HIGH — potential annoyance |
| **Wake from DORMANT autonomously** | Only external activity triggers wake | LOW — by design |
| **Express emotional needs** | No "I'm tired" or "I want to chat" messages | MEDIUM — one-sided relationship |
| **Perform real-world actions** | Gemini Bridge exists but not autonomous | LOW — safety boundary |

### 2.3 Critical Design Flaws

1. **BehaviorExecutor always returns success** (`success = True` hardcoded) — the feedback loop is non-functional
2. **ProactiveInteractionSystem never instantiated** — exists in code but never runs
3. **No user consent mechanism** — no way to disable proactive behavior
4. **No pub/sub in WebSocket manager** — subsystems can't push to frontend
5. **No general push API** — only state broadcasts, not arbitrary messages

---

## 3. Conversation Pipeline

### 3.1 Input Channels

| Channel | Protocol | Endpoint | Frontend Support |
|---------|----------|----------|-----------------|
| **Text chat** | HTTP POST | `/api/v1/chat/unified` | ✅ Desktop + Web |
| **Text chat** | WebSocket | `WS /ws` (chat_message) | ✅ Desktop only |
| **Image chat** | HTTP POST | `/api/v1/chat/with-image` | ✅ Desktop + Web |
| **Audio chat** | HTTP POST | `/api/v1/chat/with-audio` | ✅ Desktop + Web |
| **Session start** | HTTP POST | `/api/v1/session/start` | ✅ Desktop + Web |
| **Document stream** | HTTP POST (SSE) | `/api/v1/document/stream` | ⚠️ Backend only |
| **Touch/click** | Live2D events | Internal | ✅ Desktop + Web |
| **System events** | Internal | Heartbeat monitor | ✅ All |

### 3.2 Processing Pipeline (Backend)

```
User Input
  ↓
[1] Input validation + truncation (chat_routes.py:368)
  ↓
[2] Math verification dual-rail (chat_routes.py:388)
  ↓
[3] Emotion + crisis analysis (chat_routes.py:437)
  ↓
[4] Context injection (emotion, lifecycle, intent, DLI, causal) (chat_routes.py:506)
  ↓
[5] Execution gate (chat_routes.py:610)
  ↓
[6] Agent routing (chat_routes.py:771)
  ↓
[7] LLM generation (chat_service.py:191)
  ↓
[8] Causal learning + feedback (chat_routes.py:1026)
  ↓
[9] Continuous learning (ED3N + GARDEN) (chat_service.py:423)
  ↓
Response Formatting + Return
```

### 3.3 Output Channels

| Channel | Protocol | Format | Frontend Support |
|---------|----------|--------|-----------------|
| **Chat response** | HTTP JSON | `{response_text, emotion, source, ...}` | ✅ Desktop + Web |
| **Chat response** | WebSocket | `{type: "chat_response", data: {...}}` | ✅ Desktop only |
| **State update** | WebSocket broadcast | `{type: "state_update", ...}` | ✅ Desktop only |
| **Biological event** | WebSocket broadcast | `{type: "biological_event", ...}` | ✅ Desktop only |
| **Proactive action** | WebSocket broadcast | `{type: "proactive_action", ...}` | ❌ Not wired |
| **SSE stream** | HTTP SSE | `data: {token, confidence}\n\n` | ⚠️ Document only |

### 3.4 Frontend Display Capabilities

| Capability | Desktop App | Web Viewer | Status |
|------------|-------------|------------|--------|
| **Text chat bubbles** | ✅ | ✅ | Working |
| **Live2D avatar** | ✅ Full SDK | ✅ Full SDK | Working |
| **Expressions/Motions** | ✅ 7 expressions, 10 motions | ✅ Same | Working |
| **Source badges** | ✅ (neuro/llm/math) | ✅ Same | Working |
| **2D fallback** | ✅ Sprite sheets | ✅ Same | Working |
| **Audio playback** | ✅ | ✅ | Working |
| **System panel** | ❌ | ✅ CPU/mem/disk | Web only |
| **Game panel** | ❌ | ✅ Text adventure | Web only |
| **Terminal** | ❌ | ✅ Overlay | Web only |
| **Multimodal panel** | ✅ Separate window | ✅ Tab | Working |
| **WebSocket** | ✅ Via IPC bridge | ❌ HTTP only | Desktop only |
| **Proactive messages** | ✅ (if WS connected) | ❌ | Desktop only |
| **Real-time typing** | ❌ | ❌ | NOT IMPLEMENTED |

### 3.5 BROKEN/MISSING Links

| # | Issue | Impact | Fix Priority |
|---|-------|--------|-------------|
| 1 | ProactiveInteractionSystem not wired to lifespan | Angela cannot initiate conversation | **CRITICAL** |
| 2 | No chat token streaming to frontend | User waits for full response | **HIGH** |
| 3 | WebSocket manager lacks pub/sub | Subsystems can't push messages | **HIGH** |
| 4 | Web viewer has no WebSocket client | No real-time in browser | **HIGH** |
| 5 | BehaviorExecutor success hardcoded | Feedback loop non-functional | **MEDIUM** |
| 6 | No user consent for proactive | Potential annoyance | **MEDIUM** |
| 7 | SSE only for document stream | Chat not streamed | **MEDIUM** |
| 8 | `_actual_routing_mode` never set | Intent feedback broken | **LOW** |

---

## 4. Frontend Architecture

### 4.1 Desktop App (Electron)

```
electron_app/
├── main.js (1693 lines) — Main process: window, tray, WS client, IPC
├── preload.js — Secure contextBridge → renderer
├── js/
│   ├── websocket-wrapper.js — Native WS via Node.js net module
│   ├── backend-websocket.js (shared) — WS client with reconnect
│   ├── dialogue-ui.js (shared) — Chat UI with source badges
│   ├── live2d-manager.js (shared) — Cubism SDK wrapper
│   ├── tray-manager.js — System tray integration
│   └── state-persistence.js — Save/restore window state
└── libs/cubism/ — Live2D Cubism Web SDK 5.0
```

**Communication:**
- Renderer → IPC → Main process → WebSocket → Backend
- Backend → WebSocket → Main process → IPC → Renderer
- HTTP fallback via direct `fetch()` from renderer

### 4.2 Web Live2D Viewer (Vanilla JS SPA)

```
js/
├── backend-websocket.js (shared) — NOT USED (HTTP only)
├── dialogue-ui.js (shared) — Chat UI
├── live2d-manager.js (shared) — Live2D control
├── unified-shell.js — Tabbed panel system
├── hardware-detection.js — GPU/CPU detection
└── storage-manager.js — localStorage
```

**Gap**: No WebSocket client — relies on HTTP polling for chat.

### 4.3 Shared JS (packages/shared-js/)

35 modules shared between desktop + web:
- `api-client.js` — HTTP client
- `backend-websocket.js` — WS client with auto-reconnect
- `dialogue-ui.js` — Chat UI rendering
- `live2d-manager.js` — Live2D control
- `state-matrix.js` — 8D state matrix
- `performance-manager.js` — FPS/quality tiers
- `i18n.js` — Internationalization

---

## 5. Implementation Plan

### Phase 1: Wire Proactive System (CRITICAL)

1. **Create WebSocket push API** in `ConnectionManager`
2. **Instantiate ProactiveInteractionSystem** in lifespan with broadcast callback
3. **Add proactive message handler** in frontend WebSocket client
4. **Add "proactive_action" message type** to frontend renderer
5. **Add user consent toggle** in settings

### Phase 2: Real-time Streaming (HIGH)

1. **Integrate StreamingPipeline** into chat response generation
2. **Add SSE streaming endpoint** for regular chat
3. **Add streaming WebSocket message type** (`chat_token`)
4. **Implement frontend streaming renderer** (token-by-token display)

### Phase 3: Web Viewer WebSocket (HIGH)

1. **Add BackendWebSocketClient** to web viewer
2. **Add WebSocket connection panel** in settings
3. **Implement reconnection + offline queue**
4. **Enable proactive messages in browser**

### Phase 4: Intelligence Improvements (MEDIUM)

1. **Expand knowledge base** to 1000+ facts
2. **Add proper embeddings** (sentence-transformers or fallback)
3. **Fix BehaviorExecutor feedback loop**
4. **Add chain-of-thought prompting**

### Phase 5: User Control (MEDIUM)

1. **Add "Do Not Disturb" mode**
2. **Add proactive frequency slider**
3. **Add per-type proactive toggles**
4. **Add Angela autonomy level setting**

---

## 6. Angela's Upper Bound

### Current Ceiling

| Dimension | Current | Ceiling |
|-----------|---------|---------|
| **Knowledge** | 100 facts | Unlimited (with RAG + external sources) |
| **Reasoning** | Pattern matching | Bounded by symbolic engine + LLM |
| **Creativity** | LLM-dependent | Bounded by LLM |
| **Memory** | HAM + VectorStore | Bounded by storage |
| **Learning** | Hebbian + dictionary | Bounded by SNN architecture |
| **Autonomy** | Internal state only | Bounded by safety design |
| **Embodiment** | Live2D | Bounded by rendering capability |

### Key Insight

**Angela is an LLM-orchestrator, not an LLM-replacement.** Her native intelligence handles structured domains (math, logic, facts) efficiently. Open-domain intelligence comes from cloud LLM delegation. The SNN engines provide associative memory but not generative reasoning.

**To increase intelligence:**
1. Better LLM prompts (chain-of-thought, few-shot)
2. More native knowledge (expanded KB)
3. Real semantic search (proper embeddings)
4. External tool use (Wikipedia, Wolfram, etc.)
5. Structured reasoning (planner, theorem prover)

**To increase autonomy:**
1. Wire existing systems (proactive → frontend)
2. Add self-directed learning loops
3. Add emotional expression triggers
4. Add user consent framework
5. Add goal-directed behavior
