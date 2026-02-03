# 剩余错误修复计划

## 问题分析

根据 pytest 收集测试的结果，目前存在以下错误文件需要修复：

1. `test_project_coordinator_fix.py` - 文件位置错误
2. `tests/agents/test_knowledge_graph_agent.py` - 导入路径问题
3. `tests/core_ai/dialogue/test_project_coordinator.py` - 导入路径问题
4. `tests/hsp/test_hsp_connector.py` - 导入路径问题
5. `tests/hsp/test_hsp_security.py` - 导入路径问题
6. `tests/hsp/test_message_bridge.py` - 文件可能不存在或位置错误
7. `tests/integration/test_atlassian_integration.py` - 导入路径问题
8. `tests/services/test_health_ready_endpoints.py` - 导入路径问题
9. `tests/services/test_hot_endpoints.py` - 导入路径问题
10. `tests/services/test_hsp_endpoints.py` - 导入路径问题
11. `tests/services/test_main_api_server.py` - 导入路径问题
12. `tests/services/test_main_api_server_hsp.py` - 导入路径问题
13. `tests/services/test_models_endpoints.py` - 导入路径问题

## 修复策略

### 1. 文件位置错误
- 将错误位置的测试文件移动到正确的目录

### 2. 导入路径问题
- 修正测试文件中的导入路径，确保使用正确的相对导入或绝对导入

### 3. 文件缺失问题
- 检查文件是否存在，如果不存在则创建或恢复

## 详细修复步骤

### 第一步：修复文件位置错误
1. 检查并移动 `test_project_coordinator_fix.py` 到正确位置
2. 检查并移动 `test_message_bridge.py` 到正确位置（如果存在）

### 第二步：修复导入路径问题
1. 逐个检查上述列出的测试文件
2. 修正导入路径，确保所有导入都正确指向项目中的模块

### 第三步：验证修复结果
1. 运行 pytest 收集测试，确认错误数量减少
2. 运行受影响的测试文件，确保它们能正常执行

## 预期结果

完成以上步骤后，应该能够解决所有 pytest 收集测试时的错误，使测试套件能够正常运行。