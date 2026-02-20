# Angela AI v6.2.0 - Technical Specification

**Document Version**: 1.0.0  
**Created**: 2026-02-20  
**Project Version**: 6.2.0  
**Status**: Implementation Ready  
**Based On**: [requirements.md](./requirements.md)

---

## 1. Technical Context

### 1.1 Technology Stack

#### Backend (Python 3.8+)
- **Framework**: FastAPI 0.109+, Uvicorn 0.27+ (ASGI server)
- **AI/ML**: OpenAI 1.14+, Anthropic Claude SDK, Google Generative AI SDK
- **Vector Database**: ChromaDB 0.5+ (for semantic search and memory)
- **Embedding Models**: sentence-transformers 3.0+, transformers 4.37+
- **NLP**: jieba (Chinese word segmentation), tiktoken (token counting)
- **Database**: SQLAlchemy 2.0+, SQLite (default), PostgreSQL (production)
- **Encryption**: cryptography.fernet (AES-128-CBC), HMAC-SHA256
- **Audio**: pyaudio, sounddevice, faster-whisper, librosa
- **Testing**: pytest 8.0+, pytest-asyncio, pytest-cov
- **Code Quality**: black 24.1+, isort 5.13+, flake8, mypy

#### Frontend (JavaScript/TypeScript)
- **Desktop App**: Electron 40+, Node.js 22+
- **Live2D**: Live2D Cubism Web SDK
- **Mobile**: React Native (bridge to backend)
- **Communication**: WebSocket, REST API, HSP Protocol

#### Build & Development Tools
- **Package Manager**: pnpm 8.0+
- **Linting**: ESLint 8.56+, Prettier 3.2+
- **Pre-commit**: pre-commit hooks (black, flake8, mypy)
- **Monorepo**: pnpm workspaces

### 1.2 Existing Codebase Patterns

#### Service Architecture Pattern
```python
# Pattern: apps/backend/src/services/angela_llm_service.py
class AngelaLLMService:
    """Centralized service with dependency injection"""
    def __init__(self, config, dependencies):
        self.config = config
        self.dependencies = dependencies
        
    async def process(self, input): 
        # Async-first API design
        pass
```

#### Memory Management Pattern
```python
# Pattern: apps/backend/src/ai/memory/ham_memory/ham_manager.py
class HAMMemoryManager:
    """Manager pattern with composition"""
    def __init__(self):
        self.core_storage = HAMCoreStorage()
        self.vector_store = HAMVectorStoreManager()
        self.query_engine = HAMQueryEngine()
        self.background_tasks = HAMBackgroundTasks()
```

#### Configuration Pattern
```python
# Pattern: Config-driven, environment-based
from pydantic import BaseSettings

class AppConfig(BaseSettings):
    llm_backend: str = "openai"
    openai_api_key: str = ""
    
    class Config:
        env_file = ".env"
```

#### Error Handling Pattern
```python
# Pattern: Custom exception hierarchy
from apps.backend.src.core.angela_error import AngelaError

class LLMError(AngelaError):
    """LLM-specific errors"""
    pass

try:
    result = await llm_service.generate()
except LLMError as e:
    logger.error(f"LLM failed: {e}")
    raise
```

---

## 2. Implementation Approach

### 2.1 Phase 1: Fix Technical Debt (1-2 weeks)

**Objective**: Eliminate all 106 syntax errors and ensure codebase is runnable.

**Approach**:
1. **Automated Error Detection**
   - Use existing `unified_auto_fixer.py` framework
   - Parse `remaining_errors.json` for error locations
   - Run `flake8 apps/backend/src tests/` to identify all issues
   
2. **Systematic Fixes**
   - Priority 1: SyntaxError and IndentationError (blocks execution)
   - Priority 2: Import errors (breaks module loading)
   - Priority 3: Type errors and warnings (improves reliability)
   
3. **Verification**
   - Run `pytest tests/` after each batch fix
   - Ensure test pass rate > 90%
   - Run `black apps/backend/src tests/` and `isort apps/backend/src tests/`
   - Run `mypy apps/backend/src` (allow existing issues, prevent new ones)

**Testing Strategy**:
```bash
# Run full test suite
pytest tests/ -v --tb=short

# Run specific test file
pytest tests/test_angela_llm_service.py -v

# Run with coverage
pytest --cov=apps/backend/src --cov-report=html
```

---

### 2.2 Phase 2: Real AI Engine Integration (2-3 weeks)

**Objective**: Replace keyword-matching with real LLM inference.

#### 2.2.1 LLM Service Refactoring

**Current State** (angela_llm_service.py):
```python
class LLMBackend(Enum):
    LLAMA_CPP = "llamacpp"
    OLLAMA = "ollama"
    OPENAI = "openai"
```

**Target State**:
```python
class LLMBackend(Enum):
    LLAMA_CPP = "llamacpp"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AUTO = "auto"  # Load balancer
```

**Implementation**:
1. **OpenAI Integration**
   ```python
   # File: apps/backend/src/services/llm_backends/openai_backend.py
   from openai import AsyncOpenAI
   
   class OpenAIBackend(BaseLLMBackend):
       def __init__(self, api_key: str, model: str = "gpt-4"):
           self.client = AsyncOpenAI(api_key=api_key)
           self.model = model
       
       async def generate(self, prompt: str, **kwargs) -> LLMResponse:
           response = await self.client.chat.completions.create(
               model=self.model,
               messages=[{"role": "user", "content": prompt}],
               **kwargs
           )
           return LLMResponse(
               text=response.choices[0].message.content,
               model=self.model,
               usage=response.usage
           )
   ```

2. **Anthropic Claude Integration**
   ```python
   # File: apps/backend/src/services/llm_backends/anthropic_backend.py
   from anthropic import AsyncAnthropic
   
   class AnthropicBackend(BaseLLMBackend):
       def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
           self.client = AsyncAnthropic(api_key=api_key)
           self.model = model
       
       async def generate(self, prompt: str, **kwargs) -> LLMResponse:
           response = await self.client.messages.create(
               model=self.model,
               messages=[{"role": "user", "content": prompt}],
               max_tokens=kwargs.get("max_tokens", 1024)
           )
           return LLMResponse(
               text=response.content[0].text,
               model=self.model,
               usage=response.usage
           )
   ```

3. **Google Gemini Integration**
   ```python
   # File: apps/backend/src/services/llm_backends/gemini_backend.py
   import google.generativeai as genai
   
   class GeminiBackend(BaseLLMBackend):
       def __init__(self, api_key: str, model: str = "gemini-pro"):
           genai.configure(api_key=api_key)
           self.model = genai.GenerativeModel(model)
       
       async def generate(self, prompt: str, **kwargs) -> LLMResponse:
           response = await self.model.generate_content_async(prompt)
           return LLMResponse(
               text=response.text,
               model=model,
               usage={"prompt_tokens": 0, "completion_tokens": 0}  # Gemini doesn't expose this
           )
   ```

4. **Load Balancer**
   ```python
   # File: apps/backend/src/services/llm_backends/load_balancer.py
   class LLMLoadBalancer:
       def __init__(self, backends: List[BaseLLMBackend]):
           self.backends = backends
           self.current_index = 0
       
       async def generate(self, prompt: str, **kwargs) -> LLMResponse:
           for i in range(len(self.backends)):
               backend = self.backends[self.current_index]
               self.current_index = (self.current_index + 1) % len(self.backends)
               
               try:
                   return await backend.generate(prompt, **kwargs)
               except Exception as e:
                   logger.warning(f"Backend {backend} failed: {e}, trying next...")
                   continue
           
           raise LLMError("All backends failed")
   ```

#### 2.2.2 Semantic Understanding System

**New Module**: `apps/backend/src/ai/semantics/`

1. **Chinese Tokenization**
   ```python
   # File: apps/backend/src/ai/semantics/tokenizer.py
   import jieba
   import jieba.posseg as pseg
   
   class SemanticTokenizer:
       def __init__(self):
           jieba.initialize()
       
       def tokenize(self, text: str) -> List[str]:
           return list(jieba.cut(text))
       
       def tokenize_with_pos(self, text: str) -> List[Tuple[str, str]]:
           return [(word, flag) for word, flag in pseg.cut(text)]
   ```

2. **Text Embedding**
   ```python
   # File: apps/backend/src/ai/semantics/embedder.py
   from sentence_transformers import SentenceTransformer
   
   class SemanticEmbedder:
       def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
           self.model = SentenceTransformer(model_name)
       
       def embed(self, texts: List[str]) -> np.ndarray:
           return self.model.encode(texts, convert_to_numpy=True)
       
       def similarity(self, text1: str, text2: str) -> float:
           emb1 = self.embed([text1])[0]
           emb2 = self.embed([text2])[0]
           return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
   ```

3. **Intent Recognition**
   ```python
   # File: apps/backend/src/ai/semantics/intent_recognizer.py
   class IntentRecognizer:
       def __init__(self, embedder: SemanticEmbedder):
           self.embedder = embedder
           self.intent_templates = {
               "greeting": ["你好", "嗨", "早安", "晚安", "hello", "hi"],
               "question": ["什么", "为什么", "怎么", "如何", "哪里", "what", "why", "how"],
               "command": ["帮我", "请", "能不能", "可以吗", "please", "help"],
               "emotion": ["开心", "难过", "生气", "害怕", "happy", "sad", "angry"],
           }
           self._build_intent_embeddings()
       
       def _build_intent_embeddings(self):
           self.intent_embeddings = {}
           for intent, templates in self.intent_templates.items():
               self.intent_embeddings[intent] = self.embedder.embed(templates)
       
       def recognize(self, text: str) -> str:
           text_emb = self.embedder.embed([text])[0]
           best_intent = "unknown"
           best_score = 0.0
           
           for intent, embeddings in self.intent_embeddings.items():
               scores = [np.dot(text_emb, emb) / (np.linalg.norm(text_emb) * np.linalg.norm(emb)) 
                        for emb in embeddings]
               max_score = max(scores)
               if max_score > best_score:
                   best_score = max_score
                   best_intent = intent
           
           return best_intent if best_score > 0.5 else "unknown"
   ```

**Integration with angela_llm_service.py**:
```python
# Modify: apps/backend/src/services/angela_llm_service.py
from ..ai.semantics.tokenizer import SemanticTokenizer
from ..ai.semantics.embedder import SemanticEmbedder
from ..ai.semantics.intent_recognizer import IntentRecognizer

class AngelaLLMService:
    def __init__(self, ...):
        # ... existing code ...
        self.tokenizer = SemanticTokenizer()
        self.embedder = SemanticEmbedder()
        self.intent_recognizer = IntentRecognizer(self.embedder)
    
    async def process_message(self, user_input: str) -> str:
        # NEW: Real semantic processing
        tokens = self.tokenizer.tokenize(user_input)
        intent = self.intent_recognizer.recognize(user_input)
        
        # OLD: Hardcoded keyword matching (REMOVE THIS)
        # if "hello" in user_input.lower():
        #     return "Hello!"
        
        # NEW: LLM-based response generation
        context = await self._build_context(user_input, intent)
        response = await self.llm_backend.generate(context)
        return response.text
```

---

### 2.3 Phase 3: HAM Memory System Enhancement (1-2 weeks)

**Current State**: HAM system exists but not fully integrated with LLM.

**Enhancements**:

1. **Memory Retrieval for Context**
   ```python
   # File: apps/backend/src/services/angela_llm_service.py
   async def _build_context(self, user_input: str, intent: str) -> str:
       # Retrieve relevant memories
       memories = await self.ham_manager.query_engine.query_by_text(
           user_input, 
           top_k=5,
           importance_threshold=0.6
       )
       
       # Build context
       context_parts = [
           "You are Angela, a friendly AI companion.",
           f"User's intent: {intent}",
           f"User's message: {user_input}",
       ]
       
       if memories:
           context_parts.append("Relevant past experiences:")
           for mem in memories:
               context_parts.append(f"- {mem.abstracted_data}")
       
       return "\n".join(context_parts)
   ```

2. **Automatic Memory Storage**
   ```python
   # File: apps/backend/src/services/angela_llm_service.py
   async def process_message(self, user_input: str) -> str:
       # ... process message ...
       
       # Store interaction as memory
       await self.ham_manager.store_experience(
           raw_data=user_input,
           data_type="dialogue_text",
           metadata={
               "timestamp": datetime.now(timezone.utc).isoformat(),
               "user_id": self.current_user_id,
               "intent": intent,
               "importance_score": self._calculate_importance(user_input, intent),
           }
       )
       
       return response
   ```

3. **Memory Template Library**
   ```python
   # File: apps/backend/src/ai/memory/template_library.py
   def get_template_library() -> Dict[str, MemoryTemplate]:
       return {
           "user_preference": MemoryTemplate(
               template_id="user_pref",
               pattern=r"(?:我喜欢|I like|I love)\s+(.+)",
               importance_multiplier=1.5,
               retention_days=365
           ),
           "personal_fact": MemoryTemplate(
               template_id="personal",
               pattern=r"(?:我是|我叫|My name is)\s+(.+)",
               importance_multiplier=2.0,
               retention_days=730
           ),
       }
   ```

---

### 2.4 Phase 4: Desktop Application Optimization (1-2 weeks)

**Current State**: Live2D rendering works, but performance needs optimization.

**Optimizations**:

1. **FPS Optimization**
   ```javascript
   // File: apps/desktop-app/electron_app/js/live2d-manager.js
   class Live2DManager {
       constructor(performanceMode = 'auto') {
           this.targetFPS = this._getTargetFPS(performanceMode);
           this.frameInterval = 1000 / this.targetFPS;
           this.lastFrameTime = 0;
       }
       
       _getTargetFPS(mode) {
           const modes = {
               'very_low': 30,
               'low': 30,
               'medium': 45,
               'high': 60,
               'ultra': 120
           };
           return modes[mode] || 60;
       }
       
       update(currentTime) {
           if (currentTime - this.lastFrameTime < this.frameInterval) {
               requestAnimationFrame((t) => this.update(t));
               return;
           }
           
           this.lastFrameTime = currentTime;
           
           // Update Live2D model
           this.model.update();
           this.model.draw();
           
           requestAnimationFrame((t) => this.update(t));
       }
   }
   ```

2. **Resource Management**
   ```javascript
   // File: apps/desktop-app/electron_app/main.js
   const { systemPreferences } = require('electron');
   
   function detectHardwareProfile() {
       const totalMemory = os.totalmem() / (1024 ** 3); // GB
       const cpuCount = os.cpus().length;
       
       if (totalMemory < 4) return 'very_low';
       if (totalMemory < 8) return 'low';
       if (totalMemory < 16) return 'medium';
       if (totalMemory < 32) return 'high';
       return 'ultra';
   }
   
   const performanceMode = detectHardwareProfile();
   ```

3. **Emotion-Driven Behavior**
   ```javascript
   // File: apps/desktop-app/electron_app/js/emotion-system.js
   class EmotionSystem {
       constructor() {
           this.emotionalState = {
               valence: 0.5,   // α: -1 to 1
               arousal: 0.5,   // β: 0 to 1
               dominance: 0.5  // γ: 0 to 1
           };
       }
       
       updateEmotion(userInput, llmResponse) {
           // Use LLM to analyze emotional content
           const sentiment = this._analyzeSentiment(llmResponse);
           
           // Update emotional state with decay
           this.emotionalState.valence = 0.9 * this.emotionalState.valence + 0.1 * sentiment.valence;
           this.emotionalState.arousal = 0.9 * this.emotionalState.arousal + 0.1 * sentiment.arousal;
           this.emotionalState.dominance = 0.9 * this.emotionalState.dominance + 0.1 * sentiment.dominance;
       }
       
       getExpression() {
           const { valence, arousal } = this.emotionalState;
           
           if (valence > 0.6 && arousal > 0.6) return 'happy';
           if (valence < -0.6 && arousal > 0.6) return 'angry';
           if (valence < -0.6 && arousal < 0.4) return 'sad';
           if (valence > 0.3 && arousal < 0.4) return 'love';
           if (arousal > 0.7) return 'surprised';
           return 'neutral';
       }
   }
   ```

---

### 2.5 Phase 5: Security & Deployment (1 week)

**Security Enhancements**:

1. **Key Rotation**
   ```python
   # File: apps/backend/src/security/abc_key_manager_enhanced.py
   class ABCKeyManager:
       def __init__(self):
           self.rotation_interval_days = 30
       
       async def rotate_key(self, key_type: str):
           new_key = Fernet.generate_key()
           
           # Re-encrypt all data with new key
           await self._reencrypt_data(key_type, new_key)
           
           # Update key in secure storage
           await self._update_key_storage(key_type, new_key)
           
           logger.info(f"Rotated {key_type} key successfully")
   ```

2. **Multi-Device Sync**
   ```python
   # File: apps/backend/src/sync/device_sync_manager.py
   class DeviceSyncManager:
       async def sync_to_device(self, device_id: str, data: Dict):
           # Encrypt with device-specific key (Key C)
           encrypted = self.key_manager.encrypt_for_device(device_id, data)
           
           # Send via WebSocket
           await self.ws_manager.send_to_device(device_id, encrypted)
   ```

---

## 3. Source Code Structure Changes

### 3.1 New Modules

```
apps/backend/src/
├── ai/
│   ├── semantics/                          # NEW
│   │   ├── __init__.py
│   │   ├── tokenizer.py                    # Jieba tokenization
│   │   ├── embedder.py                     # Sentence embeddings
│   │   └── intent_recognizer.py            # Intent classification
│   └── memory/
│       ├── ham_memory/                     # EXISTING (enhance)
│       ├── memory_template.py              # EXISTING (enhance)
│       └── template_library.py             # ENHANCE
├── services/
│   ├── llm_backends/                       # NEW
│   │   ├── __init__.py
│   │   ├── base_backend.py                 # Abstract base class
│   │   ├── openai_backend.py               # OpenAI integration
│   │   ├── anthropic_backend.py            # Claude integration
│   │   ├── gemini_backend.py               # Gemini integration
│   │   ├── ollama_backend.py               # EXISTING (refactor)
│   │   ├── llamacpp_backend.py             # EXISTING (refactor)
│   │   └── load_balancer.py                # Multi-model orchestration
│   └── angela_llm_service.py               # REFACTOR (remove hardcoding)
├── security/
│   └── abc_key_manager_enhanced.py         # ENHANCE (key rotation)
└── sync/
    └── device_sync_manager.py              # ENHANCE (multi-device)

apps/desktop-app/electron_app/
├── js/
│   ├── emotion-system.js                   # NEW
│   ├── performance-monitor.js              # NEW
│   └── live2d-manager.js                   # ENHANCE
└── main.js                                 # ENHANCE

tests/
├── test_llm_backends/                      # NEW
│   ├── test_openai_backend.py
│   ├── test_anthropic_backend.py
│   ├── test_gemini_backend.py
│   └── test_load_balancer.py
├── test_semantics/                         # NEW
│   ├── test_tokenizer.py
│   ├── test_embedder.py
│   └── test_intent_recognizer.py
└── integration/
    └── test_end_to_end_conversation.py     # NEW
```

### 3.2 Files to Modify

**Priority 1 - Critical**:
1. `apps/backend/src/services/angela_llm_service.py` - Remove hardcoding, add LLM integration
2. `apps/backend/src/ai/memory/ham_memory/ham_manager.py` - Enhance LLM integration
3. `apps/desktop-app/electron_app/js/live2d-manager.js` - Performance optimization

**Priority 2 - Important**:
4. `apps/backend/src/security/abc_key_manager_enhanced.py` - Add key rotation
5. `apps/backend/src/sync/device_sync_manager.py` - Enhance multi-device sync
6. `apps/desktop-app/electron_app/main.js` - Hardware detection

**Priority 3 - Enhancement**:
7. Configuration files (.env.example, config.yaml)
8. Documentation (README.md, API docs)

---

## 4. Data Model / API / Interface Changes

### 4.1 LLM Response Model

```python
# File: apps/backend/src/services/llm_backends/base_backend.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class LLMResponse:
    """Standardized LLM response"""
    text: str
    model: str
    backend: str
    usage: Dict[str, int]  # {"prompt_tokens": 100, "completion_tokens": 50}
    metadata: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
```

### 4.2 Semantic Analysis Result

```python
# File: apps/backend/src/ai/semantics/models.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class SemanticAnalysisResult:
    """Result of semantic analysis"""
    tokens: List[str]
    pos_tags: List[Tuple[str, str]]  # [(word, POS)]
    intent: str
    entities: List[Tuple[str, str]]  # [(entity, type)]
    embedding: Optional[np.ndarray] = None
```

### 4.3 REST API Endpoints (New/Modified)

**New Endpoint**: POST /api/v1/chat
```python
# File: apps/backend/src/api/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    emotion: str
    intent: str
    session_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint using real LLM"""
    result = await angela_service.process_message(
        user_input=request.message,
        user_id=request.user_id,
        session_id=request.session_id
    )
    return ChatResponse(**result)
```

**Modified Endpoint**: GET /api/v1/memory
```python
@router.get("/memory", response_model=List[MemoryResponse])
async def get_memories(
    user_id: str,
    query: Optional[str] = None,
    limit: int = 10,
    importance_threshold: float = 0.5
):
    """Retrieve memories with semantic search"""
    if query:
        memories = await ham_manager.query_engine.query_by_text(
            query, 
            top_k=limit,
            importance_threshold=importance_threshold
        )
    else:
        memories = await ham_manager.get_recent_memories(user_id, limit)
    
    return [MemoryResponse.from_ham_memory(m) for m in memories]
```

### 4.4 WebSocket Protocol (HSP Enhanced)

**Message Format**:
```json
{
    "protocol": "HSP",
    "version": "1.0",
    "message_type": "chat_request|chat_response|emotion_update|memory_sync",
    "payload": {
        "user_message": "...",
        "llm_response": "...",
        "emotion_state": {"valence": 0.7, "arousal": 0.6, "dominance": 0.5},
        "intent": "question",
        "timestamp": "2026-02-20T15:30:00Z"
    },
    "metadata": {
        "session_id": "...",
        "device_id": "...",
        "encryption": "AES-128-CBC"
    }
}
```

---

## 5. Delivery Phases (Incremental Milestones)

### Phase 1: Technical Debt Cleanup (Week 1-2)

**Milestones**:
- [ ] **M1.1**: Fix all 106 syntax/indentation errors
  - Verify: `flake8 apps/backend/src tests/` returns 0 errors
- [ ] **M1.2**: pytest pass rate > 90%
  - Verify: `pytest tests/ --tb=short` shows >90% pass
- [ ] **M1.3**: Code formatting standardized
  - Verify: `black --check apps/backend/src tests/` passes
  - Verify: `isort --check apps/backend/src tests/` passes

**Deliverables**:
- Clean codebase with zero syntax errors
- Updated `remaining_errors.json` (empty or minimal)
- Test report showing >90% pass rate

---

### Phase 2: Real AI Engine Integration (Week 3-5)

**Milestones**:
- [ ] **M2.1**: OpenAI GPT-4 integration complete
  - Verify: End-to-end test with GPT-4 passes
  - Test: `pytest tests/test_llm_backends/test_openai_backend.py -v`
- [ ] **M2.2**: Anthropic Claude integration complete
  - Verify: End-to-end test with Claude passes
  - Test: `pytest tests/test_llm_backends/test_anthropic_backend.py -v`
- [ ] **M2.3**: Semantic understanding system operational
  - Verify: Intent recognition accuracy > 80%
  - Test: `pytest tests/test_semantics/ -v`
- [ ] **M2.4**: All hardcoded responses removed
  - Verify: Code review finds zero instances of `.count()` or hardcoded templates
  - Verify: `grep -r "random.uniform" apps/backend/src/` returns empty

**Deliverables**:
- Working LLM backends (OpenAI, Anthropic, Gemini)
- Load balancer with fallback support
- Semantic analysis pipeline (tokenization, embedding, intent recognition)
- Zero hardcoded responses

---

### Phase 3: HAM Memory Enhancement (Week 6)

**Milestones**:
- [ ] **M3.1**: Memory retrieval integrated with LLM context
  - Verify: Conversations use past memories correctly
  - Test: `pytest tests/integration/test_memory_aware_conversation.py -v`
- [ ] **M3.2**: Automatic memory storage working
  - Verify: All conversations stored in HAM
  - Verify: Memory count increases after each interaction
- [ ] **M3.3**: Memory performance optimized
  - Verify: Retrieval latency < 100ms
  - Test: `pytest tests/test_ham_performance.py -v`

**Deliverables**:
- Memory-aware conversation system
- Performance benchmarks showing <100ms retrieval
- Memory template library

---

### Phase 4: Desktop App Optimization (Week 7)

**Milestones**:
- [ ] **M4.1**: 60 FPS rendering (high mode)
  - Verify: FPS counter shows stable 60 FPS
  - Verify: CPU usage < 20% idle, < 30% active
- [ ] **M4.2**: 30 FPS rendering (low mode)
  - Verify: Works smoothly on 2GB DDR3 test device
  - Verify: Memory usage < 500MB
- [ ] **M4.3**: Emotion system integrated
  - Verify: Expressions change based on conversation
  - Test: Manual testing with various inputs

**Deliverables**:
- Optimized Live2D rendering
- Hardware auto-detection
- Emotion-driven behavior system
- Cross-platform testing report (Windows/macOS/Linux)

---

### Phase 5: Security & Deployment (Week 8)

**Milestones**:
- [ ] **M5.1**: Security audit passed
  - Verify: Penetration testing report
  - Verify: No critical vulnerabilities
- [ ] **M5.2**: Key rotation implemented
  - Verify: Keys rotate every 30 days automatically
  - Test: `pytest tests/test_abc_key_rotation.py -v`
- [ ] **M5.3**: Multi-device sync working
  - Verify: Desktop <-> Mobile sync works
  - Test: Manual cross-device testing

**Deliverables**:
- Security audit report
- Key rotation implementation
- Multi-device sync documentation
- Deployment guide

---

## 6. Verification Approach

### 6.1 Automated Testing Commands

**Unit Tests**:
```bash
# Run all unit tests
pytest tests/ -v --tb=short -m unit

# Run specific module tests
pytest tests/test_llm_backends/ -v
pytest tests/test_semantics/ -v
pytest tests/test_ham_memory/ -v
```

**Integration Tests**:
```bash
# Run integration tests
pytest tests/ -v -m integration

# End-to-end conversation test
pytest tests/integration/test_end_to_end_conversation.py -v
```

**Performance Tests**:
```bash
# Memory retrieval performance
pytest tests/test_ham_performance.py -v

# LLM response time
pytest tests/test_llm_latency.py -v
```

### 6.2 Code Quality Commands

**Linting**:
```bash
# Python linting
flake8 apps/backend/src tests/
mypy apps/backend/src

# JavaScript linting
cd apps/desktop-app/electron_app && npm run lint
```

**Formatting**:
```bash
# Python formatting (check mode)
black --check apps/backend/src tests/
isort --check apps/backend/src tests/

# Python formatting (apply)
black apps/backend/src tests/
isort apps/backend/src tests/
```

**Pre-commit**:
```bash
# Run all pre-commit hooks
pre-commit run --all-files
```

### 6.3 Coverage Reports

```bash
# Generate coverage report
pytest --cov=apps/backend/src --cov-report=html --cov-report=term-missing

# Coverage threshold: >80%
pytest --cov=apps/backend/src --cov-fail-under=80
```

### 6.4 Performance Benchmarks

**Backend Performance**:
```python
# File: tests/benchmarks/test_llm_performance.py
import pytest
import asyncio
import time

@pytest.mark.asyncio
async def test_llm_response_time():
    """Verify LLM response < 2 seconds"""
    service = AngelaLLMService()
    
    start = time.time()
    response = await service.process_message("Hello, Angela!")
    elapsed = time.time() - start
    
    assert elapsed < 2.0, f"Response took {elapsed}s, expected <2s"

@pytest.mark.asyncio
async def test_memory_retrieval_time():
    """Verify memory retrieval < 100ms"""
    manager = HAMMemoryManager()
    
    start = time.time()
    memories = await manager.query_engine.query_by_text("test query", top_k=5)
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    assert elapsed < 100, f"Retrieval took {elapsed}ms, expected <100ms"
```

**Desktop App Performance**:
```javascript
// File: apps/desktop-app/electron_app/tests/test_fps.js
const { performance } = require('perf_hooks');

describe('Live2D Performance', () => {
    it('should maintain 60 FPS in high mode', async () => {
        const manager = new Live2DManager('high');
        const frames = [];
        
        for (let i = 0; i < 300; i++) {  // 5 seconds at 60 FPS
            const start = performance.now();
            manager.update();
            const end = performance.now();
            frames.push(end - start);
        }
        
        const avgFrameTime = frames.reduce((a, b) => a + b) / frames.length;
        const fps = 1000 / avgFrameTime;
        
        expect(fps).toBeGreaterThanOrEqual(55);  // Allow 5 FPS tolerance
    });
});
```

### 6.5 Manual Testing Checklist

**Conversation Quality**:
- [ ] Angela responds naturally without hardcoded templates
- [ ] Angela remembers past conversations
- [ ] Intent recognition works for 5+ different intents
- [ ] Multi-turn conversations maintain context (>10 turns)

**Performance**:
- [ ] Desktop app runs at 60 FPS (high mode, 16GB+ RAM)
- [ ] Desktop app runs at 30 FPS (low mode, 2GB RAM)
- [ ] LLM response time < 2 seconds (average)
- [ ] Memory retrieval < 100ms

**Cross-Platform**:
- [ ] Works on Windows 10/11
- [ ] Works on macOS 12+
- [ ] Works on Ubuntu 20.04+

**Security**:
- [ ] API keys stored securely (not in code)
- [ ] Memory data encrypted at rest
- [ ] WebSocket communication encrypted
- [ ] No key leakage in logs

---

## 7. Risk Mitigation

### 7.1 Technical Risks

| Risk | Mitigation |
|------|-----------|
| **API Rate Limiting** | Implement load balancer with fallback to local models |
| **High API Costs** | Monitor usage, implement caching, prefer local models |
| **Performance Regression** | Benchmark each phase, rollback if metrics drop |
| **Memory Leaks** | Monitor memory usage, implement cleanup tasks |
| **Cross-Platform Issues** | Test on all platforms in each phase |

### 7.2 Development Constraints Compliance

**From DEVELOPMENT_CONSTRAINTS.md**:

1. **✅ Zero Hardcoding Principle**
   - Remove all `random.uniform()` calls
   - Remove all `.count()` keyword matching
   - Remove all hardcoded response templates

2. **✅ Real AI Integration Principle**
   - Integrate OpenAI GPT-4
   - Integrate Anthropic Claude
   - Integrate Google Gemini

3. **✅ Semantic Understanding Principle**
   - Use jieba for tokenization
   - Use sentence-transformers for embeddings
   - Use semantic similarity for intent recognition

4. **✅ AGI Verification Principle**
   - End-to-end tests verify real conversation
   - Performance tests verify <2s response time
   - Memory tests verify context retention

---

## 8. Success Criteria

### 8.1 Functional Criteria

- [ ] All 106 syntax errors fixed (Phase 1)
- [ ] Real LLM integration working (Phase 2)
- [ ] Zero hardcoded responses (Phase 2)
- [ ] Semantic understanding operational (Phase 2)
- [ ] Memory-aware conversations (Phase 3)
- [ ] 60 FPS desktop rendering (Phase 4)
- [ ] Security audit passed (Phase 5)

### 8.2 Performance Criteria

- [ ] LLM response time < 2s (average)
- [ ] Memory retrieval < 100ms
- [ ] Desktop app 60 FPS (high mode)
- [ ] Desktop app 30 FPS (low mode)
- [ ] CPU usage < 30% (active)
- [ ] Memory usage < 500MB (low mode)

### 8.3 Quality Criteria

- [ ] Test coverage > 80%
- [ ] pytest pass rate > 95%
- [ ] flake8 errors = 0
- [ ] mypy errors = 0 (new code)
- [ ] Zero critical security vulnerabilities

---

## 9. Dependencies & Requirements

### 9.1 New Python Packages

Add to `requirements.txt`:
```
# LLM Providers
anthropic>=0.18.0
google-generativeai>=0.3.0

# NLP & Semantics
jieba>=0.42.1
```

### 9.2 API Keys Required

Create `.env.example`:
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
GOOGLE_API_KEY=...

# HAM Encryption
MIKO_HAM_KEY=...  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 9.3 Development Environment

**Minimum**:
- Python 3.8+
- Node.js 16+
- pnpm 8+
- 8GB RAM
- 10GB disk space

**Recommended**:
- Python 3.12
- Node.js 22
- pnpm 8+
- 16GB RAM
- 20GB disk space
- GPU (for local LLM models)

---

## 10. Documentation Updates

**Files to Update**:
1. `README.md` - Add LLM setup instructions
2. `docs/API.md` - Document new /chat endpoint
3. `docs/SETUP.md` - Add API key configuration
4. `docs/ARCHITECTURE.md` - Update with new semantic modules
5. `apps/backend/src/services/README.md` - Document LLM backends

**New Documentation**:
1. `docs/LLM_INTEGRATION.md` - How to add new LLM backends
2. `docs/SEMANTIC_SYSTEM.md` - Semantic understanding architecture
3. `docs/MEMORY_SYSTEM.md` - HAM memory usage guide
4. `docs/PERFORMANCE_TUNING.md` - Performance optimization guide

---

## 11. Team Roles (1号/2号/3号/4号)

**1号 - Project Lead / Architect**:
- Review and approve this spec
- Make technical decisions on LLM backend priorities
- Risk assessment and mitigation
- Phase gate reviews

**2号 - Implementation Developer**:
- Implement LLM backends (OpenAI, Anthropic, Gemini)
- Implement semantic understanding system
- Fix syntax errors (Phase 1)
- Write unit tests

**3号 - Research / Optimization**:
- Research best embedding models for Chinese
- Optimize memory retrieval performance
- Optimize Live2D rendering
- Performance benchmarking

**4号 - Quality Assurance / Release Manager**:
- Code review all PRs
- Run integration tests
- Cross-platform testing
- Git commit management
- Release verification

---

## 12. Appendix

### A. Code Style Examples

**Python (Black + isort)**:
```python
# Correct
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI

from apps.backend.src.core.angela_error import AngelaError


class AngelaService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def process(self, input_data: str) -> str:
        result = await self._internal_process(input_data)
        return result
```

**JavaScript (Prettier)**:
```javascript
// Correct
class Live2DManager {
  constructor(performanceMode = 'auto') {
    this.performanceMode = performanceMode;
    this.targetFPS = this._getTargetFPS(performanceMode);
  }

  async update(deltaTime) {
    this.model.update(deltaTime);
    await this.render();
  }
}
```

### B. Testing Examples

**Unit Test**:
```python
# tests/test_llm_backends/test_openai_backend.py
import pytest
from apps.backend.src.services.llm_backends.openai_backend import OpenAIBackend

@pytest.mark.asyncio
async def test_openai_generate():
    backend = OpenAIBackend(api_key="test-key", model="gpt-4")
    response = await backend.generate("Hello!")
    
    assert response.text is not None
    assert response.model == "gpt-4"
    assert response.backend == "openai"
    assert response.usage["total_tokens"] > 0
```

**Integration Test**:
```python
# tests/integration/test_end_to_end_conversation.py
import pytest
from apps.backend.src.services.angela_llm_service import AngelaLLMService

@pytest.mark.asyncio
async def test_conversation_with_memory():
    service = AngelaLLMService()
    
    # First interaction
    response1 = await service.process_message("My name is Alice")
    assert "Alice" in response1 or "alice" in response1.lower()
    
    # Second interaction - should remember
    response2 = await service.process_message("What's my name?")
    assert "Alice" in response2 or "alice" in response2.lower()
```

### C. Performance Benchmarks

| Metric | Target | Current | Phase |
|--------|--------|---------|-------|
| LLM Response Time | < 2s | N/A (hardcoded) | Phase 2 |
| Memory Retrieval | < 100ms | ~150ms | Phase 3 |
| Desktop FPS (High) | 60 | ~55 | Phase 4 |
| Desktop FPS (Low) | 30 | ~28 | Phase 4 |
| CPU Usage (Idle) | < 10% | ~12% | Phase 4 |
| Memory Usage (Low) | < 500MB | ~520MB | Phase 4 |

---

**Document Status**: Ready for Planning Phase  
**Next Step**: Create detailed implementation plan (plan.md)  
**Estimated Timeline**: 6-8 weeks  
**Team Size**: 2-4 developers

**Sign-off**:
- Created by: Zencoder AI Assistant (2号)
- Technical Review: [Pending 3号 review]
- Approved by: [Pending 1号 approval]
- QA Review: [Pending 4号 review]
