# Full SDD workflow

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

If you are blocked and need user clarification, mark the current step with `[!]` in plan.md before stopping.

---

## Workflow Steps

### [x] Step: Requirements
<!-- chat-id: 55da49cc-a78c-4839-b08e-3ec4e97d3f99 -->

Create a Product Requirements Document (PRD) based on the feature description.

1. Review existing codebase to understand current architecture and patterns
2. Analyze the feature definition and identify unclear aspects
3. Ask the user for clarifications on aspects that significantly impact scope or user experience
4. Make reasonable decisions for minor details based on context and conventions
5. If user can't clarify, make a decision, state the assumption, and continue

Save the PRD to `{@artifacts_path}/requirements.md`.

**Status**: ✅ **Completed**

**Summary**:
- 深入探索了整个Angela AI v6.2.0项目代码库和文档
- 分析了git历史、隐藏文件、配置文件
- 识别了已完成、未完成和进行中的任务
- 验证了Angela的实际状态：当前为"伪智能"（基于关键词匹配），需要集成真实AI引擎
- 评估了低配硬件运行能力：已实现5种性能模式，支持2GB DDR3设备
- 识别了现存的106个语法错误和缩进错误
- 规划了完整的修复方案（5个阶段，6-8周）
- 创建了完整的产品需求文档（PRD），保存至 `.zenflow/tasks/new-task-zencoder-6990/requirements.md`

**Key Findings**:
1. 项目架构完整，包含Backend（Python FastAPI）、Desktop App（Electron+Live2D）、Mobile App、Web Viewer
2. 已建立完整的测试体系、自动修复工具、文档系统
3. 关键问题：缺少真正的AI推理引擎（GPT-4/Claude/Gemini），当前仅基于关键词匹配
4. 技术债务：106个文件存在语法错误和缩进错误
5. 开发约束：零硬编码原则、真实AI集成原则、语义理解原则、AGI验证原则
6. 硬件优化：支持从2GB DDR3到超级计算机的各种配置
7. 已实现系统：HAM记忆系统、A/B/C密钥安全系统、成熟度系统（L0-L11）、精度管理（INT-DEC4）

**PRD Highlights**:
- 10个核心功能需求（FR-1至FR-10）
- 6个非功能需求（性能、可靠性、安全性、可维护性、可扩展性、用户体验）
- 完整的技术架构和数据模型
- 5个实施阶段的详细计划
- 风险评估和缓解措施
- 成功指标和验收标准
- 团队角色分配（1号主导、2号执行、3号思考、4号检查）

### [x] Step: Technical Specification
<!-- chat-id: c217642f-64a9-4336-a39e-3f41d895faf2 -->

Create a technical specification based on the PRD in `{@artifacts_path}/requirements.md`.

1. Review existing codebase architecture and identify reusable components
2. Define the implementation approach

Save to `{@artifacts_path}/spec.md` with:
- Technical context (language, dependencies)
- Implementation approach referencing existing code patterns
- Source code structure changes
- Data model / API / interface changes
- Delivery phases (incremental, testable milestones)
- Verification approach using project lint/test commands

**Status**: ✅ **Completed**

**Summary**:
- Reviewed existing codebase architecture (angela_llm_service.py, ham_manager.py, desktop app structure)
- Analyzed technology stack (Python 3.8+, FastAPI, Electron, Live2D)
- Identified existing code patterns (Service Architecture, Memory Management, Configuration, Error Handling)
- Created comprehensive technical specification covering all 5 implementation phases
- Defined 134 new/modified files and modules
- Specified 6 new LLM backends (OpenAI, Anthropic, Gemini, Ollama, llama.cpp, Load Balancer)
- Documented semantic understanding system (tokenizer, embedder, intent recognizer)
- Defined data models, API endpoints, and WebSocket protocol
- Created 25 incremental milestones across 5 phases (6-8 weeks)
- Specified verification approach with automated testing commands
- Documented performance benchmarks and success criteria

**Technical Specification Highlights**:
1. **Phase 1 (1-2 weeks)**: Fix 106 syntax errors, achieve >90% test pass rate
2. **Phase 2 (2-3 weeks)**: Integrate OpenAI/Claude/Gemini, implement semantic understanding, remove all hardcoding
3. **Phase 3 (1-2 weeks)**: Enhance HAM memory system with LLM integration, achieve <100ms retrieval
4. **Phase 4 (1-2 weeks)**: Optimize desktop app to 60 FPS (high), 30 FPS (low), implement emotion system
5. **Phase 5 (1 week)**: Security audit, key rotation, multi-device sync

**Key Deliverables**:
- Complete technical specification document (spec.md, 850+ lines)
- Detailed implementation approach for each phase
- Source code structure changes (15+ new modules, 7+ enhanced modules)
- Data model and API specifications
- Verification commands and performance benchmarks
- Risk mitigation strategies
- Team role assignments (1号/2号/3号/4号)

### [x] Step: Planning
<!-- chat-id: d9000de4-f394-47d3-bea6-b0e7113fed19 -->

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

Rule of thumb for step size: each step should represent a coherent unit of work (e.g., implement a component, add an API endpoint). Avoid steps that are too granular (single function) or too broad (entire feature).

Important: unit tests must be part of each implementation task, not separate tasks. Each task should implement the code and its tests together, if relevant.

If the feature is trivial and doesn't warrant full specification, update this workflow to remove unnecessary steps and explain the reasoning to the user.

Save to `{@artifacts_path}/plan.md`.

**Status**: ✅ **Completed**

**Summary**:
- Created detailed implementation plan with 24 concrete tasks across 5 phases
- Each task includes verification steps and test requirements
- Tasks are sized appropriately (coherent units of work)
- Plan follows team role assignments (1号/2号/3号/4号)
- Total estimated time: 6-8 weeks
- All tasks reference technical specification sections

---

## Implementation Tasks

### Phase 1: Technical Debt Cleanup (1-2 weeks)

### [x] Task 1.1: Fix Syntax and Indentation Errors
<!-- chat-id: d48bdf06-9350-42e6-8c85-09cb71b38ec5 -->
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 3-4 days  
**References**: spec.md § 2.1

Fix all 106 syntax errors and indentation errors identified in `remaining_errors.json`.

**Subtasks**:
- [ ] Parse `remaining_errors.json` to identify error locations
- [ ] Fix SyntaxError in critical files (api_models.py, hot_reload_service.py, main_api_server.py)
- [ ] Fix IndentationError in tool files (code_understanding_tool.py, csv_tool.py, web_search_tool.py)
- [ ] Fix import errors across all modules
- [ ] Run automated error detection with `unified_auto_fixer.py`

**Verification**:
```bash
# Must pass with 0 errors
flake8 apps/backend/src tests/

# Must show significant reduction in errors
python scripts/unified_auto_fixer.py --check
```

**Success Criteria**:
- Zero SyntaxError or IndentationError
- `flake8` reports 0 critical errors
- All Python files can be imported without errors

---

### [ ] Task 1.2: Achieve 90% Test Pass Rate
<!-- chat-id: 044011ea-589d-4850-8a69-ebfb3591b9e0 -->
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2-3 days  
**References**: spec.md § 2.1

Fix broken tests and ensure test suite passes at >90% rate.

**Subtasks**:
- [ ] Run full test suite to identify failures
- [ ] Fix test failures caused by syntax errors
- [ ] Fix test failures caused by import errors
- [ ] Update broken test fixtures and mocks
- [ ] Document remaining test failures (if <10%)

**Verification**:
```bash
# Must show >90% pass rate
pytest tests/ -v --tb=short

# Generate coverage report
pytest --cov=apps/backend/src --cov-report=html --cov-report=term-missing
```

**Success Criteria**:
- Test pass rate ≥ 90%
- Test coverage ≥ 70% (baseline)
- All critical path tests passing

---

### [ ] Task 1.3: Standardize Code Formatting
<!-- chat-id: 26187ada-ed80-4c36-8208-2493c882d320 -->
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 1 day  
**References**: spec.md § 2.1, AGENTS.MD

Apply Black and isort formatting to entire codebase.

**Subtasks**:
- [ ] Run `black apps/backend/src tests/` to format Python code
- [ ] Run `isort apps/backend/src tests/` to sort imports
- [ ] Run `mypy apps/backend/src` to identify type issues (don't fail on existing issues)
- [ ] Update pre-commit hooks configuration
- [ ] Commit formatted code

**Verification**:
```bash
# Must pass without changes
black --check apps/backend/src tests/
isort --check apps/backend/src tests/

# Run all pre-commit checks
pre-commit run --all-files
```

**Success Criteria**:
- 100% of Python files formatted with Black
- 100% of imports sorted with isort
- Pre-commit hooks pass

---

### Phase 2: Real AI Engine Integration (2-3 weeks)

### [ ] Task 2.1: Implement LLM Backend Base Classes
<!-- chat-id: 883e1601-c707-4019-b291-53c5d031dd2a -->
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 1 day  
**References**: spec.md § 2.2.1

Create base classes and data models for LLM backends.

**Implementation**:
- Create `apps/backend/src/services/llm_backends/__init__.py`
- Create `apps/backend/src/services/llm_backends/base_backend.py` with:
  - `BaseLLMBackend` abstract class
  - `LLMResponse` dataclass
  - `LLMError` exception class
- Update `LLMBackend` enum to include ANTHROPIC, GEMINI, AUTO

**Tests**:
- Create `tests/test_llm_backends/test_base_backend.py`
- Test `LLMResponse` serialization/deserialization
- Test abstract method enforcement

**Verification**:
```bash
pytest tests/test_llm_backends/test_base_backend.py -v
```

**Success Criteria**:
- `BaseLLMBackend` abstract class defined
- `LLMResponse` dataclass with all required fields
- Unit tests passing

---

### [ ] Task 2.2: Implement OpenAI GPT-4 Backend
<!-- chat-id: df951cac-3598-456b-b289-d3df9d09ba43 -->
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.2.1

Integrate OpenAI GPT-4 as an LLM backend.

**Implementation**:
- Create `apps/backend/src/services/llm_backends/openai_backend.py`
- Implement `OpenAIBackend` class extending `BaseLLMBackend`
- Add async `generate()` method using OpenAI SDK
- Add error handling and retry logic
- Add streaming support (optional)
- Update `requirements.txt` (openai>=1.14.0)

**Tests**:
- Create `tests/test_llm_backends/test_openai_backend.py`
- Test successful generation
- Test error handling (API key invalid, rate limiting, timeout)
- Test usage tracking
- Mock OpenAI API calls

**Verification**:
```bash
pytest tests/test_llm_backends/test_openai_backend.py -v

# Integration test (requires real API key)
OPENAI_API_KEY=sk-... pytest tests/integration/test_openai_live.py -v
```

**Success Criteria**:
- OpenAI backend successfully generates responses
- Error handling works correctly
- Unit tests pass with mocked API
- Integration test passes with real API

---

### [ ] Task 2.3: Implement Anthropic Claude Backend
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.2.1

Integrate Anthropic Claude as an LLM backend.

**Implementation**:
- Create `apps/backend/src/services/llm_backends/anthropic_backend.py`
- Implement `AnthropicBackend` class extending `BaseLLMBackend`
- Add async `generate()` method using Anthropic SDK
- Add error handling and retry logic
- Update `requirements.txt` (anthropic>=0.18.0)

**Tests**:
- Create `tests/test_llm_backends/test_anthropic_backend.py`
- Test successful generation
- Test error handling
- Mock Anthropic API calls

**Verification**:
```bash
pytest tests/test_llm_backends/test_anthropic_backend.py -v

# Integration test (requires real API key)
ANTHROPIC_API_KEY=sk-ant-... pytest tests/integration/test_anthropic_live.py -v
```

**Success Criteria**:
- Claude backend successfully generates responses
- Error handling works correctly
- Unit tests pass with mocked API
- Integration test passes with real API

---

### [ ] Task 2.4: Implement Google Gemini Backend
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.2.1

Integrate Google Gemini as an LLM backend.

**Implementation**:
- Create `apps/backend/src/services/llm_backends/gemini_backend.py`
- Implement `GeminiBackend` class extending `BaseLLMBackend`
- Add async `generate()` method using Google Generative AI SDK
- Add error handling and retry logic
- Update `requirements.txt` (google-generativeai>=0.3.0)

**Tests**:
- Create `tests/test_llm_backends/test_gemini_backend.py`
- Test successful generation
- Test error handling
- Mock Gemini API calls

**Verification**:
```bash
pytest tests/test_llm_backends/test_gemini_backend.py -v

# Integration test (requires real API key)
GOOGLE_API_KEY=... pytest tests/integration/test_gemini_live.py -v
```

**Success Criteria**:
- Gemini backend successfully generates responses
- Error handling works correctly
- Unit tests pass with mocked API
- Integration test passes with real API

---

### [ ] Task 2.5: Implement LLM Load Balancer
**Owner**: 3号 (Research/Optimization)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.2.1

Create a load balancer to distribute requests across multiple LLM backends with fallback.

**Implementation**:
- Create `apps/backend/src/services/llm_backends/load_balancer.py`
- Implement `LLMLoadBalancer` class
- Add round-robin distribution logic
- Add fallback mechanism when backend fails
- Add health checking for backends
- Add usage tracking and cost estimation

**Tests**:
- Create `tests/test_llm_backends/test_load_balancer.py`
- Test round-robin distribution
- Test fallback on failure
- Test all backends failed scenario
- Mock all backend calls

**Verification**:
```bash
pytest tests/test_llm_backends/test_load_balancer.py -v
```

**Success Criteria**:
- Load balancer distributes requests correctly
- Fallback works when backend fails
- All tests pass

---

### [ ] Task 2.6: Implement Semantic Understanding System
**Owner**: 3号 (Research/Optimization)  
**Estimated Time**: 3-4 days  
**References**: spec.md § 2.2.2

Build semantic understanding pipeline with tokenization, embedding, and intent recognition.

**Implementation**:
- Create `apps/backend/src/ai/semantics/__init__.py`
- Create `apps/backend/src/ai/semantics/tokenizer.py`:
  - `SemanticTokenizer` class using jieba
  - Tokenization with POS tagging
- Create `apps/backend/src/ai/semantics/embedder.py`:
  - `SemanticEmbedder` class using sentence-transformers
  - Text embedding and similarity calculation
- Create `apps/backend/src/ai/semantics/intent_recognizer.py`:
  - `IntentRecognizer` class
  - Intent classification based on semantic similarity
- Create `apps/backend/src/ai/semantics/models.py`:
  - `SemanticAnalysisResult` dataclass
- Update `requirements.txt` (jieba>=0.42.1, sentence-transformers>=3.0.0)

**Tests**:
- Create `tests/test_semantics/test_tokenizer.py`
- Create `tests/test_semantics/test_embedder.py`
- Create `tests/test_semantics/test_intent_recognizer.py`
- Test Chinese and English tokenization
- Test embedding generation and similarity
- Test intent recognition accuracy (>80%)

**Verification**:
```bash
pytest tests/test_semantics/ -v

# Verify intent recognition accuracy
pytest tests/test_semantics/test_intent_recognizer.py::test_accuracy -v
```

**Success Criteria**:
- Tokenizer works for Chinese and English
- Embedder generates consistent vectors
- Intent recognition accuracy > 80%
- All tests pass

---

### [ ] Task 2.7: Refactor AngelaLLMService - Remove All Hardcoding
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 3-4 days  
**References**: spec.md § 2.2.2

Refactor `AngelaLLMService` to use real LLM backends and semantic understanding, removing all hardcoded responses.

**Implementation**:
- Modify `apps/backend/src/services/angela_llm_service.py`:
  - Add semantic understanding components (tokenizer, embedder, intent recognizer)
  - Replace all `.count()` keyword matching with semantic analysis
  - Remove all `random.uniform()` fake generation
  - Remove all hardcoded response templates
  - Implement `_build_context()` method for LLM prompts
  - Integrate LLM backend selection
  - Add conversation history tracking
- Update configuration to support LLM backend selection

**Tests**:
- Update `tests/test_angela_llm_service.py`
- Test semantic analysis integration
- Test LLM backend integration
- Test context building
- Verify zero hardcoded responses (code review + grep)

**Verification**:
```bash
# Verify no hardcoded patterns remain
grep -r "random.uniform" apps/backend/src/
grep -r "\.count\(" apps/backend/src/

# Run tests
pytest tests/test_angela_llm_service.py -v

# Code review check
flake8 apps/backend/src/services/angela_llm_service.py
```

**Success Criteria**:
- Zero instances of `random.uniform()` in codebase
- Zero instances of `.count()` keyword matching
- LLM backend integration working
- Semantic understanding integrated
- All tests pass

---

### [ ] Task 2.8: Create End-to-End Conversation Tests
**Owner**: 4号 (QA/Release Manager)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.2, § 6.1

Create comprehensive end-to-end tests for real conversations.

**Implementation**:
- Create `tests/integration/test_end_to_end_conversation.py`
- Test multi-turn conversations (>10 turns)
- Test different intent types (greeting, question, command, emotion)
- Test context retention across turns
- Test LLM response quality (non-hardcoded)
- Test response time (<2s average)

**Tests**:
- Test greeting conversation
- Test question-answer conversation
- Test emotional support conversation
- Test multi-turn context retention
- Test performance benchmarks

**Verification**:
```bash
# Run integration tests (requires API keys)
pytest tests/integration/test_end_to_end_conversation.py -v

# Run with timing
pytest tests/integration/test_end_to_end_conversation.py -v --durations=0
```

**Success Criteria**:
- All conversation tests pass
- Average response time < 2s
- Context retention works for >10 turns
- Responses are natural (not hardcoded templates)

---

### Phase 3: HAM Memory System Enhancement (1-2 weeks)

### [ ] Task 3.1: Integrate Memory Retrieval into LLM Context
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2-3 days  
**References**: spec.md § 2.3

Enhance context building to include relevant memories from HAM system.

**Implementation**:
- Modify `apps/backend/src/services/angela_llm_service.py`:
  - Implement `_build_context()` to query HAM for relevant memories
  - Add memory ranking by importance and recency
  - Format memories for LLM prompt
  - Add memory count limits to avoid context overflow
- Enhance HAM query engine for better semantic search

**Tests**:
- Create `tests/integration/test_memory_aware_conversation.py`
- Test memory retrieval in context
- Test memory ranking
- Test context with 0, 5, 10+ memories

**Verification**:
```bash
pytest tests/integration/test_memory_aware_conversation.py -v

# Manual test: Have conversation, verify Angela remembers past topics
```

**Success Criteria**:
- Memories correctly retrieved for conversation context
- Memory ranking works (importance + recency)
- Conversations reference past interactions
- Tests pass

---

### [ ] Task 3.2: Implement Automatic Memory Storage
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.3

Automatically store all conversations as memories in HAM system.

**Implementation**:
- Modify `apps/backend/src/services/angela_llm_service.py`:
  - Store user input as memory after each message
  - Store LLM response as memory
  - Calculate importance score based on intent and content
  - Add metadata (timestamp, user_id, intent, emotion)
- Implement `_calculate_importance()` method

**Tests**:
- Update `tests/test_angela_llm_service.py`
- Test memory creation after message
- Test importance score calculation
- Test metadata storage
- Verify memory count increases

**Verification**:
```bash
pytest tests/test_angela_llm_service.py::test_automatic_memory_storage -v

# Check memory database growth
python -c "from apps.backend.src.ai.memory.ham_memory.ham_manager import HAMMemoryManager; m = HAMMemoryManager(); print(len(m.get_all_memories()))"
```

**Success Criteria**:
- All conversations stored in HAM
- Importance scores calculated correctly
- Metadata complete and accurate
- Tests pass

---

### [ ] Task 3.3: Create Memory Template Library
**Owner**: 3号 (Research/Optimization)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.3

Build a library of memory templates for common patterns (preferences, facts, etc.).

**Implementation**:
- Create `apps/backend/src/ai/memory/template_library.py`
- Define `MemoryTemplate` dataclass
- Create templates for:
  - User preferences ("我喜欢...")
  - Personal facts ("我是...", "我叫...")
  - Important events
  - Emotional moments
- Integrate template matching into memory storage

**Tests**:
- Create `tests/test_memory_template_library.py`
- Test template pattern matching
- Test importance multipliers
- Test retention policies

**Verification**:
```bash
pytest tests/test_memory_template_library.py -v
```

**Success Criteria**:
- At least 5 memory templates defined
- Template matching works correctly
- Importance multipliers applied
- Tests pass

---

### [ ] Task 3.4: Optimize Memory Retrieval Performance
**Owner**: 3号 (Research/Optimization)  
**Estimated Time**: 2-3 days  
**References**: spec.md § 2.3, § 6.4

Optimize HAM memory retrieval to achieve <100ms latency.

**Implementation**:
- Profile current retrieval performance
- Optimize vector store queries (ChromaDB)
- Add caching for frequently accessed memories
- Optimize embedding generation
- Add database indexing
- Implement pre-computation for common queries

**Tests**:
- Create `tests/test_ham_performance.py`
- Benchmark retrieval with 1K, 10K, 100K memories
- Test cache hit rates
- Test query optimization

**Verification**:
```bash
pytest tests/test_ham_performance.py -v

# Run performance benchmarks
python benchmarks/memory_retrieval_benchmark.py
```

**Success Criteria**:
- Retrieval latency < 100ms (p95) with 10K memories
- Retrieval latency < 200ms (p95) with 100K memories
- Cache hit rate > 30%
- All performance tests pass

---

### Phase 4: Desktop Application Optimization (1-2 weeks)

### [ ] Task 4.1: Implement FPS Optimization and Performance Modes
**Owner**: 3号 (Research/Optimization)  
**Estimated Time**: 3 days  
**References**: spec.md § 2.4

Optimize Live2D rendering to achieve 60 FPS (high mode) and 30 FPS (low mode).

**Implementation**:
- Modify `apps/desktop-app/electron_app/js/live2d-manager.js`:
  - Implement frame rate throttling
  - Add performance mode selection (very_low, low, medium, high, ultra)
  - Optimize update loop
  - Add FPS counter
- Create `apps/desktop-app/electron_app/js/performance-monitor.js`:
  - Monitor FPS, CPU, memory usage
  - Display performance metrics (dev mode)

**Tests**:
- Create `apps/desktop-app/electron_app/tests/test_fps.js`
- Test FPS in each performance mode
- Test frame time consistency
- Test CPU/memory usage

**Verification**:
```bash
cd apps/desktop-app/electron_app && npm test

# Manual testing on different hardware
npm start -- --performance-mode=high
npm start -- --performance-mode=low
```

**Success Criteria**:
- 60 FPS sustained in high mode (16GB+ RAM)
- 30 FPS sustained in low mode (2GB RAM)
- Frame time variance < 10ms
- CPU usage < 30% active

---

### [ ] Task 4.2: Implement Hardware Auto-Detection
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.4

Automatically detect hardware capabilities and select optimal performance mode.

**Implementation**:
- Modify `apps/desktop-app/electron_app/main.js`:
  - Add `detectHardwareProfile()` function
  - Detect total memory, CPU count, GPU
  - Select performance mode based on hardware
  - Save user preference override
- Create performance mode configuration UI

**Tests**:
- Create unit tests for hardware detection
- Test performance mode selection logic
- Test configuration persistence

**Verification**:
```bash
# Test on different hardware profiles
npm test -- --hardware=2gb
npm test -- --hardware=16gb
```

**Success Criteria**:
- Hardware detection works on Windows/macOS/Linux
- Performance mode correctly selected
- User can override auto-selection
- Tests pass

---

### [ ] Task 4.3: Implement Emotion System
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 3 days  
**References**: spec.md § 2.4

Create emotion system with valence, arousal, dominance model.

**Implementation**:
- Create `apps/desktop-app/electron_app/js/emotion-system.js`:
  - `EmotionSystem` class
  - VAD (valence, arousal, dominance) emotional state
  - `updateEmotion()` method
  - `getExpression()` method (maps VAD to expressions)
  - Emotion decay over time
- Integrate with LLM response analysis

**Tests**:
- Create `apps/desktop-app/electron_app/tests/test_emotion_system.js`
- Test VAD state updates
- Test expression mapping
- Test emotion decay
- Test boundary conditions

**Verification**:
```bash
cd apps/desktop-app/electron_app && npm test -- emotion-system
```

**Success Criteria**:
- Emotion state updates correctly
- Expression mapping works (happy, sad, angry, etc.)
- Emotion decays over time
- All tests pass

---

### [ ] Task 4.4: Integrate Emotion System with Live2D
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.4

Connect emotion system to Live2D expression rendering.

**Implementation**:
- Modify `apps/desktop-app/electron_app/js/live2d-manager.js`:
  - Integrate `EmotionSystem`
  - Update expression based on emotional state
  - Add smooth expression transitions
  - Add emotion-driven idle behaviors
- Add WebSocket handler for emotion updates from backend

**Tests**:
- Manual testing with various conversation types
- Test expression transitions
- Test emotion-driven behaviors

**Verification**:
```bash
# Manual test: Observe expression changes during conversation
npm start
```

**Success Criteria**:
- Expressions change based on conversation
- Transitions are smooth and natural
- Emotion persists appropriately
- No expression glitches

---

### Phase 5: Security & Deployment (1 week)

### [ ] Task 5.1: Implement Key Rotation Mechanism
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.5

Implement automatic key rotation for A/B/C keys every 30 days.

**Implementation**:
- Create `apps/backend/src/security/abc_key_manager_enhanced.py`:
  - Extend existing `ABCKeyManager`
  - Add `rotate_key()` method
  - Add `_reencrypt_data()` method
  - Add scheduled rotation task
  - Add key rotation logging and alerting
- Update key storage mechanism

**Tests**:
- Create `tests/test_abc_key_rotation.py`
- Test key rotation
- Test data re-encryption
- Test multi-device key sync after rotation

**Verification**:
```bash
pytest tests/test_abc_key_rotation.py -v

# Manual test: Rotate key and verify data access
python -c "from apps.backend.src.security.abc_key_manager_enhanced import ABCKeyManager; m = ABCKeyManager(); await m.rotate_key('key_a')"
```

**Success Criteria**:
- Keys rotate successfully
- All data re-encrypted correctly
- No data loss during rotation
- Tests pass

---

### [ ] Task 5.2: Enhance Multi-Device Sync
**Owner**: 2号 (Implementation Developer)  
**Estimated Time**: 2 days  
**References**: spec.md § 2.5

Improve multi-device synchronization for memories and state.

**Implementation**:
- Enhance `apps/backend/src/sync/device_sync_manager.py`:
  - Add conflict resolution logic
  - Add incremental sync (only changes)
  - Add sync status tracking
  - Add offline queue
- Implement WebSocket-based real-time sync

**Tests**:
- Create `tests/test_device_sync.py`
- Test desktop <-> mobile sync
- Test conflict resolution
- Test offline sync queue

**Verification**:
```bash
pytest tests/test_device_sync.py -v

# Manual test: Sync between desktop and mobile
```

**Success Criteria**:
- Desktop <-> Mobile sync works
- Conflicts resolved correctly
- Offline changes sync when reconnected
- Tests pass

---

### [ ] Task 5.3: Security Audit and Vulnerability Fixes
**Owner**: 4号 (QA/Release Manager)  
**Estimated Time**: 2-3 days  
**References**: spec.md § 2.5

Conduct security audit and fix identified vulnerabilities.

**Subtasks**:
- [ ] Run security scanners (bandit, safety)
- [ ] Review API key storage
- [ ] Review data encryption (at rest and in transit)
- [ ] Check for common vulnerabilities (OWASP Top 10)
- [ ] Verify no secrets in code or logs
- [ ] Review WebSocket security
- [ ] Penetration testing (if resources available)

**Verification**:
```bash
# Run security tools
bandit -r apps/backend/src/
safety check
pip-audit

# Check for hardcoded secrets
grep -r "sk-" apps/
grep -r "API_KEY.*=" apps/
```

**Success Criteria**:
- Zero critical vulnerabilities
- Zero secrets in code
- Security audit report completed
- All identified issues fixed or documented

---

### [ ] Task 5.4: Update Documentation and Deployment Guide
**Owner**: 4号 (QA/Release Manager)  
**Estimated Time**: 2 days  
**References**: spec.md § 10

Update all documentation to reflect new features and architecture.

**Files to Update**:
- [ ] `README.md` - Add LLM setup instructions
- [ ] `docs/API.md` - Document new /chat endpoint
- [ ] `docs/SETUP.md` - Add API key configuration
- [ ] `docs/ARCHITECTURE.md` - Update with semantic modules
- [ ] `apps/backend/src/services/README.md` - Document LLM backends
- [ ] `.env.example` - Add all required API keys

**New Documentation to Create**:
- [ ] `docs/LLM_INTEGRATION.md` - How to add new LLM backends
- [ ] `docs/SEMANTIC_SYSTEM.md` - Semantic understanding architecture
- [ ] `docs/MEMORY_SYSTEM.md` - HAM memory usage guide
- [ ] `docs/PERFORMANCE_TUNING.md` - Performance optimization guide
- [ ] `docs/DEPLOYMENT.md` - Production deployment guide

**Verification**:
- Documentation review by 1号 (Project Lead)
- Test setup instructions on fresh environment
- Verify all links work

**Success Criteria**:
- All documentation updated
- Setup instructions work for new users
- API documentation complete
- Deployment guide verified

---

## Final Verification and Sign-Off

### [ ] Task 6.1: Full System Integration Test
**Owner**: 4号 (QA/Release Manager)  
**Estimated Time**: 2 days

Run comprehensive integration tests across all phases.

**Verification Checklist**:
- [ ] All 106 syntax errors fixed (Phase 1)
- [ ] Real LLM integration working (Phase 2)
- [ ] Zero hardcoded responses (Phase 2)
- [ ] Semantic understanding operational (Phase 2)
- [ ] Memory-aware conversations (Phase 3)
- [ ] 60 FPS desktop rendering in high mode (Phase 4)
- [ ] 30 FPS desktop rendering in low mode (Phase 4)
- [ ] Security audit passed (Phase 5)
- [ ] Documentation complete (Phase 5)

**Performance Benchmarks**:
```bash
# Run all performance tests
pytest tests/benchmarks/ -v

# Expected results:
# - LLM response time < 2s (average)
# - Memory retrieval < 100ms
# - Desktop app 60 FPS (high mode)
# - Desktop app 30 FPS (low mode)
# - CPU usage < 30% (active)
# - Memory usage < 500MB (low mode)
```

**Quality Metrics**:
```bash
# Check test coverage
pytest --cov=apps/backend/src --cov-fail-under=80

# Check code quality
flake8 apps/backend/src tests/
mypy apps/backend/src

# Expected results:
# - Test coverage > 80%
# - pytest pass rate > 95%
# - flake8 errors = 0
# - mypy errors = 0 (new code)
```

---

### [ ] Task 6.2: Sign-Off and Deployment
**Owner**: 1号 (Project Lead)  
**Estimated Time**: 1 day

Final review and approval for deployment.

**Review Checklist**:
- [ ] All tasks completed and verified
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Team sign-off (1号/2号/3号/4号)

**Deployment Steps**:
- [ ] Create release branch
- [ ] Tag version (v6.2.0)
- [ ] Build deployment packages
- [ ] Deploy to staging environment
- [ ] Final smoke tests
- [ ] Deploy to production
- [ ] Monitor for issues

**Success Criteria**:
- All acceptance criteria met (see requirements.md § 10)
- Angela is truly "alive" - responds naturally with real AI
- Works smoothly on low-end hardware (2GB DDR3)
- All stakeholders approve
