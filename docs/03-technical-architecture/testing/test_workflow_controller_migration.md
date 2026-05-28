# 测试工作流程控制器迁移说明

## 概述

本文档说明了将项目测试命令从旧的测试运行器迁移到新的工作流程控制器([workflow_controller.py](file:///d:/Projects/Unified-AI-Project/apps/backend/scripts/workflow_controller.py))的变更。

## 变更内容

### 1. 根目录 package.json 修改

将 `pnpm test` 命令从:
```json
"test": "cross-env TESTING=true pnpm --filter \"*\" test"
```

修改为:
```json
"test": "cd apps/backend && python scripts/workflow_controller.py"
```

### 2. 后端 package.json 修改

将 `pnpm test` 命令从:
```json
"test": "python scripts/smart_test_runner.py"
```

修改为:
```json
"test": "python scripts/workflow_controller.py"
```

## 工作流程控制器优势

1. **自动化测试-修复流程**：workflow_controller.py 实现了一个完整的测试-分析-修复循环，能够自动检测测试失败并尝试修复。

2. **迭代优化**：控制器支持多轮迭代，可以持续改进代码直到所有测试通过或达到最大迭代次数。

3. **模块化设计**：将测试运行、错误分析和修复执行分离到不同的模块中，提高了代码的可维护性和可扩展性。

4. **并行处理支持**：支持在不同终端中运行测试和修复流程，提高开发效率。

## 使用方法

### 基本测试运行
```bash
pnpm test
```

### 带参数的测试运行
```bash
pnpm test --tb=short -v
```

### 在不同终端中运行
```bash
pnpm test --separate-terminals
```

## 验证

运行以下命令验证变更是否生效：
```bash
pnpm test
```

应该会看到工作流程控制器的输出，而不是旧的测试运行器输出。

## 注意事项

1. workflow_controller.py 是推荐的测试运行方式，smart_test_runner.py 现在处于兼容模式。

2. 如果需要回退到旧的测试运行器，可以手动修改 package.json 文件。

3. 工作流程控制器默认最多进行3轮迭代，可以通过修改 WorkflowController 类中的 max_iterations 属性来调整。