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

### [ ] Step: Planning

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

Rule of thumb for step size: each step should represent a coherent unit of work (e.g., implement a component, add an API endpoint). Avoid steps that are too granular (single function) or too broad (entire feature).

Important: unit tests must be part of each implementation task, not separate tasks. Each task should implement the code and its tests together, if relevant.

If the feature is trivial and doesn't warrant full specification, update this workflow to remove unnecessary steps and explain the reasoning to the user.

Save to `{@artifacts_path}/plan.md`.

### [ ] Step: Implementation

This step should be replaced with detailed implementation tasks from the Planning step.

If Planning didn't replace this step, execute the tasks in `{@artifacts_path}/plan.md`, updating checkboxes as you go. Run planned tests/lint and record results in plan.md.
