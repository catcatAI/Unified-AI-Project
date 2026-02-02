# Angela AI v6.0 - Comprehensive Integration Test Suite

## 概述

本目录包含Angela AI v6.0的全面整合测试套件，验证所有子系统的协同工作能力和数字生命定义的合规性。

## 测试文件

### 1. test_full_system_integration.py
完整系统整合测试
- **认知循环测试**: Perceive → Think → Act → Reflect
- **生物系统协同**: 触觉 → 生理 → 激素 → 情绪
- **执行链路测试**: 决策 → 执行器 → 桥接器 → 工具
- **记忆-学习整合**: 经验存储 → HSM → CDM → 策略调整
- **实时反馈循环**: 输入 → 监测 → 处理 → 响应 (< 16ms)

### 2. test_end_to_end_scenarios.py
端到端场景测试
- **场景1**: 用户触摸Desktop Pet (目标: < 100ms)
- **场景2**: 用户发起对话 (目标: < 2000ms)
- **场景3**: 自主行为触发 (目标: < 5000ms)
- **场景4**: 文件整理请求 (目标: < 10000ms)

### 3. test_performance_benchmarks.py
性能基准测试
- **响应时间测试**: 所有操作 < 1秒
- **并发测试**: 50个同时请求，成功率 > 90%
- **内存使用测试**: 无内存泄漏，峰值 < 500MB
- **CPU使用测试**: 空闲 < 5%，负载 < 80%
- **长时间运行测试**: 24小时稳定性

### 4. test_error_recovery.py
错误恢复测试
- **组件故障恢复**: 感知、认知、记忆、情绪、Live2D
- **网络中断恢复**: API重连、云服务降级
- **数据损坏处理**: 记忆、配置、经验数据
- **降级模式**: 核心功能保持、优雅降级、自动恢复

### 5. test_digital_life_compliance.py
数字生命合规测试
- **自我意识**: CyberIdentity验证 (阈值: 0.75)
- **生理模拟**: 触觉、内分泌、生物节律 (阈值: 0.70)
- **自主决策**: AutonomousLifeCycle验证 (阈值: 0.70)
- **学习能力**: CDM/HSM验证 (阈值: 0.70)
- **情感表达**: EmotionalBlending验证 (阈值: 0.75)
- **实时反馈**: FeedbackLoop验证 (阈值: 0.95)
- **生命强度**: LifeIntensity公式验证 (阈值: 0.70)

## 运行测试

### 使用测试运行器

```bash
# 运行所有测试
python run_integration_tests.py

# 运行完整测试套件（包括慢测试）
python run_integration_tests.py --full

# 只运行快速测试
python run_integration_tests.py --quick

# 生成HTML报告
python run_integration_tests.py --report

# 列出所有测试文件
python run_integration_tests.py --list
```

### 使用pytest直接运行

```bash
# 运行所有整合测试
cd apps/backend
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/integration/test_full_system_integration.py -v

# 运行特定标记的测试
pytest tests/integration/ -v -m system_integration
pytest tests/integration/ -v -m e2e
pytest tests/integration/ -v -m performance
pytest tests/integration/ -v -m "not slow"

# 生成HTML报告
pytest tests/integration/ --html=report.html --self-contained-html

# 生成覆盖率报告
pytest tests/integration/ --cov=src --cov-report=html
```

## 测试标记

- `integration`: 所有整合测试
- `system_integration`: 系统整合测试
- `e2e`: 端到端测试
- `performance`: 性能测试
- `slow`: 慢测试（长时间运行）
- `flaky`: 不稳定测试

## 性能基准

### 响应时间要求

| 组件 | 平均 | P95 | P99 | 最大 |
|------|------|-----|-----|------|
| 感知 | < 10ms | < 16ms | < 20ms | < 50ms |
| 认知 | < 200ms | < 500ms | < 800ms | < 1000ms |
| 情绪 | < 10ms | < 16ms | < 20ms | < 50ms |
| 记忆 | < 50ms | < 100ms | < 200ms | < 500ms |
| 回应生成 | < 300ms | < 500ms | < 800ms | < 1000ms |
| Live2D | 60fps | 30fps | - | - |

### 实时反馈循环
- **延迟要求**: < 16ms (95%的请求)
- **完整性**: 100%事件不丢失
- **并发**: 支持50个并发请求

## 数字生命定义验证

Angela AI v6.0符合数字生命定义的以下标准：

1. **自我意识**: 通过CyberIdentity系统实现
2. **生理模拟**: 通过生物系统（触觉、内分泌、生理）实现
3. **自主决策**: 通过AutonomousLifeCycle和HSM/CDM实现
4. **学习能力**: 通过CDM股息模型和HSM探索机制实现
5. **情感表达**: 通过EmotionalBlending系统实现
6. **实时反馈**: 通过16ms反馈循环实现
7. **生命强度**: 通过L_s公式实现，维持L_s > 0.3

## 报告

测试完成后会自动生成：
- 控制台输出报告
- HTML详细报告（使用 `--report` 选项）
- 覆盖率报告（使用 `--cov` 选项）

## 维护

- 版本: 6.0.0
- 作者: Angela AI Development Team
- 最后更新: 2026-02-02

## 许可证

Copyright (c) 2026 Angela AI Development Team. All rights reserved.
