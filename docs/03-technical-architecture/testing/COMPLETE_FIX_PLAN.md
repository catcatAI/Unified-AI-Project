# 项目全面修复计划

## 概述
根据编译检查结果，项目中存在大量Python文件语法错误。这些错误主要分为以下几类：
1. 错误的字典语法：`_ = "key": value` 应该是 `"key": value`
2. 错误的异常抛出语法：`_ = raise Exception(...)` 应该是 `raise Exception(...)`
3. 错误的装饰器语法：`_ = @decorator` 应该是 `@decorator`
4. 错误的断言语法：`_ = assert ...` 应该是 `assert ...`
5. 缩进错误
6. 参数顺序错误

## 修复策略

### 1. 自动化修复脚本
创建脚本来自动修复常见的语法错误模式：

### 2. 分批处理
按目录分批处理文件，确保修复过程有序进行：

### 3. 验证机制
每修复一批文件后进行验证，确保修复有效且不引入新问题。

## 详细修复计划

### 第一阶段：核心服务文件修复
- apps/backend/src/services/multi_llm_service.py (已完成)
- apps/backend/src/shared/network_resilience.py
- apps/backend/src/system/deployment_manager.py
- apps/backend/src/system/hardware_probe.py
- apps/backend/src/system/integrated_graphics_optimizer.py
- apps/backend/src/system_integration.py

### 第二阶段：工具模块修复
- apps/backend/src/tools/calculator_tool.py
- apps/backend/src/tools/logic_model/ 目录下所有文件
- 其他工具模块

### 第三阶段：测试文件修复
- apps/backend/tests/ 目录下所有文件

### 第四阶段：其他模块修复
- apps/backend/src/ 目录下其他文件

## 自动化修复脚本

我们将创建以下脚本来自动化修复常见问题：

1. `fix_dictionary_syntax.py` - 修复字典语法错误
2. `fix_raise_syntax.py` - 修复异常抛出语法错误
3. `fix_decorator_syntax.py` - 修复装饰器语法错误
4. `fix_assert_syntax.py` - 修复断言语法错误

## 验证脚本

创建验证脚本来确保修复质量：

1. `validate_syntax.py` - 验证语法正确性
2. `validate_imports.py` - 验证模块可导入性
3. `validate_functionality.py` - 验证基本功能

## 时间安排

- 第1天：完成自动化修复脚本开发和测试
- 第2-3天：修复核心服务文件
- 第4-5天：修复工具模块
- 第6-7天：修复测试文件
- 第8天：修复其他模块并进行最终验证

## 风险控制

1. 在修复前备份所有文件
2. 每次修复后进行验证
3. 保持与用户的沟通，及时报告进度
4. 如遇到复杂问题，及时寻求用户指导