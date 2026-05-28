# 测试失败修复计划

## 🎯 问题概述

在运行后端测试时，发现了几个失败的测试用例，主要集中在两个方面：

1. **数据分析师代理测试失败**：期望的错误消息与实际返回的不匹配
2. **项目协调器测试失败**：Mock对象不能在`await`表达式中使用

## 🔍 问题分析

### 1. 数据分析师代理测试失败

**错误信息**：
```
AssertionError: 'Dummy analysis failed: Unsupported query or invalid CSV.' != 'Dummy analysis failed: Invalid CSV format (inconsistent columns).'
```

**问题原因**：
在测试文件 [test_data_analysis_agent.py](../apps/backend/tests/agents/test_data_analysis_agent.py) 中，期望的错误消息是 "Invalid CSV format (inconsistent columns)"，但实际实现中返回的是 "Unsupported query or invalid CSV."。

**相关代码**：
- 测试文件：[apps/backend/tests/agents/test_data_analysis_agent.py](../apps/backend/tests/agents/test_data_analysis_agent.py) (第104行)
- 实现文件：[apps/backend/src/agents/data_analysis_agent.py](../apps/backend/src/agents/data_analysis_agent.py)

### 2. 项目协调器测试失败

**错误信息**：
```
TypeError: object MagicMock can't be used in 'await' expression
```

**问题原因**：
在测试文件 [test_project_coordinator.py](../apps/backend/tests/core_ai/dialogue/test_project_coordinator.py) 中，使用了 `MagicMock` 对象来模拟异步方法，但 `MagicMock` 不能在 `await` 表达式中使用。应该使用 `AsyncMock`。

**相关代码**：
- 测试文件：[apps/backend/tests/core_ai/dialogue/test_project_coordinator.py](../apps/backend/tests/core_ai/dialogue/test_project_coordinator.py)
- 实现文件：[apps/backend/src/core_ai/dialogue/project_coordinator.py](../apps/backend/src/ai/dialogue/project_coordinator.py)

## 🛠️ 解决方案

### 1. 修复数据分析师代理测试

**步骤**：
1. 修改 [apps/backend/src/agents/data_analysis_agent.py](../apps/backend/src/agents/data_analysis_agent.py) 中的错误消息，使其与测试期望一致
2. 或者修改 [apps/backend/tests/agents/test_data_analysis_agent.py](../apps/backend/tests/agents/test_data_analysis_agent.py) 中的期望值，使其与实现一致

**推荐方案**：
修改实现文件中的错误消息，使其更加准确地描述错误情况。

### 2. 修复项目协调器测试

**步骤**：
1. 在 [apps/backend/tests/core_ai/dialogue/test_project_coordinator.py](../apps/backend/tests/core_ai/dialogue/test_project_coordinator.py) 中，将所有应该返回异步对象的 `MagicMock` 替换为 `AsyncMock`
2. 确保所有异步方法都使用 `AsyncMock` 进行模拟

## 📝 具体修改

### 1. 数据分析师代理错误消息修复

修改 [apps/backend/src/agents/data_analysis_agent.py](../apps/backend/src/agents/data_analysis_agent.py) 文件：

```python
# 原代码
elif not is_csv_valid:
    error_message = "Dummy analysis failed: Unsupported query or invalid CSV."
else:
    error_message = "Dummy analysis failed: Unsupported query or invalid CSV."

# 修改后
elif not is_csv_valid:
    error_message = "Dummy analysis failed: Invalid CSV format (inconsistent columns)."
else:
    error_message = "Dummy analysis failed: Unsupported query or invalid CSV."
```

### 2. 项目协调器测试修复

修改 [apps/backend/tests/core_ai/dialogue/test_project_coordinator.py](../apps/backend/tests/core_ai/dialogue/test_project_coordinator.py) 文件：

```python
# 原代码
mock_service_discovery = MagicMock()

# 修改后
mock_service_discovery = AsyncMock()
```

还需要修改其他相关的地方，确保所有异步方法都使用 `AsyncMock`。

## ✅ 验证计划

1. 修改数据分析师代理的错误消息
2. 修改项目协调器测试中的 `MagicMock` 为 `AsyncMock`
3. 运行相关测试，确认问题已解决
4. 运行完整的测试套件，确保没有引入新的问题

## 📅 时间安排

1. **第1天**：修复数据分析师代理错误消息
2. **第2天**：修复项目协调器测试中的 Mock 对象问题
3. **第3天**：验证所有修复并运行完整测试套件

## 🎉 预期结果

通过这些修复，我们期望：

1. 所有测试都能通过
2. 项目代码更加健壮和准确
3. 测试代码更加符合异步编程的最佳实践