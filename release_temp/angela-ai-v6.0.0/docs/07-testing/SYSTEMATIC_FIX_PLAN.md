# 系统化修复计划

## 问题分析

通过前面的检查，我们发现测试文件收集错误的主要原因有：

1. **导入路径问题**：测试文件中使用了错误的导入路径
2. **模块缺失问题**：缺少必要的依赖模块（如 semver）
3. **相对导入问题**：源代码文件中使用了错误的相对导入路径

## 修复策略

### 第一步：修复模块缺失问题
- 安装缺失的依赖模块（已完成：semver）

### 第二步：系统化修复导入路径问题
1. 逐个检查所有出错的测试文件
2. 修正测试文件中的导入路径
3. 修正源代码文件中的相对导入路径

### 第三步：验证修复结果
1. 运行 pytest 收集测试，确认错误数量减少
2. 运行受影响的测试文件，确保它们能正常执行

## 详细修复步骤

### 1. 修复测试文件导入路径
- [x] tests/agents/test_knowledge_graph_agent.py
- [x] tests/core_ai/dialogue/test_project_coordinator.py
- [x] tests/core_ai/dialogue/test_project_coordinator_fix.py
- [ ] tests/hsp/test_hsp_connector.py
- [ ] tests/hsp/test_hsp_security.py
- [ ] tests/integration/test_atlassian_integration.py
- [ ] tests/services/test_health_ready_endpoints.py
- [ ] tests/services/test_hot_endpoints.py
- [ ] tests/services/test_hsp_endpoints.py
- [ ] tests/services/test_main_api_server.py
- [ ] tests/services/test_main_api_server_hsp.py
- [ ] tests/services/test_models_endpoints.py

### 2. 修复源代码文件相对导入路径
- [x] src/ai/agents/specialized/knowledge_graph_agent.py
- [ ] 其他可能存在问题的源代码文件

### 3. 验证修复结果
- 运行完整的测试收集过程
- 确认所有错误都已解决