# Angela AI v6.0 代码质量修复计划
## Comprehensive Code Quality Fix Plan

### 📊 质量检查总结
- **总代码行数**: 14,148 行
- **自主系统文件**: 20 个
- **错误**: 0 个（语法正确）
- **警告**: 107 个
- **测试覆盖率**: 0%

### 🎯 优先级修复任务

#### 🔴 P0: 关键运行时错误（必须修复）

1. **__init__.py 导入错误** ⚠️
   - MusicPlayer, CollisionDetector, Live2DGenerator 未定义
   - 位置: `apps/backend/src/core/autonomous/__init__.py`
   - 影响: 包导入失败
   - 修复: 移除未定义类的导出或创建对应类

2. **类型注解错误** ⚠️
   - 文件: `neuroplasticity.py`
   - 问题: `list[int]` 不能赋值给 `List[float]`
   - 行号: 201
   - 修复: 统一类型注解

3. **Tuple 类型不匹配** ⚠️
   - 文件: `neuroplasticity.py`
   - 问题: 使用可变长度 tuple 作为 Dict 的 key
   - 行号: 474, 481, 532, 538
   - 修复: 使用固定长度的 Tuple 或转换数据结构

4. **None 属性访问** ⚠️
   - 文件: `neuroplasticity.py` (1455行), `desktop_presence.py` (546行), `browser_controller.py` (542行)
   - 问题: 可能访问 None 的属性
   - 修复: 添加空值检查

5. **StimulusTemplates 方法签名** ⚠️
   - 文件: `autonomic_nervous_system.py`
   - 问题: 方法缺少 self 参数（stress, exercise, meditation, deep_breathing, surprise, comfort）
   - 修复: 添加 @staticmethod 或 @classmethod 装饰器

6. **ctypes.windll 错误** ⚠️
   - 文件: `desktop_interaction.py` (453行)
   - 问题: windll 不是已知属性（仅限 Windows）
   - 修复: 添加平台检查

#### 🟡 P1: 代码结构优化（建议修复）

7. **Dataclass __init__ 误报**
   - 实际上所有 dataclass 都自动生成了 __init__
   - 检查工具误报，不是真正的问题

8. **跨平台兼容性**
   - 桌面交互代码需要处理 Windows/macOS/Linux 差异
   - 添加平台检测和适配

9. **异常处理完善**
   - 添加更多 try-except 块
   - 提供有意义的错误消息

10. **日志系统**
    - 添加结构化日志
    - 便于调试和监控

#### 🟢 P2: 测试和文档（重要但不紧急）

11. **测试覆盖率 0%** ⚠️
    - 需要为所有20个自主系统文件创建测试
    - 优先测试核心功能：
      - physiological_tactile.py
      - endocrine_system.py
      - neuroplasticity.py
      - action_executor.py
      - desktop_interaction.py

12. **Live2D 依赖缺失**
    - 需要添加 Live2D SDK 说明
    - 提供下载和安装指南

13. **API 文档**
    - 为所有公共方法添加 docstring
    - 创建 API 参考文档

### 🔧 具体修复步骤

#### 阶段 1: 修复关键错误（立即执行）

1. 修复 __init__.py 导入
2. 修复类型注解错误
3. 修复 None 检查
4. 修复 StimulusTemplates 方法
5. 修复 ctypes 平台问题

#### 阶段 2: 代码审查和优化

6. 审查所有类型注解
7. 添加异常处理
8. 优化性能瓶颈

#### 阶段 3: 测试和文档

9. 创建核心系统测试
10. 完善文档
11. 创建示例代码

### 📋 验收标准

- [ ] 所有 P0 问题修复
- [ ] 代码可以通过类型检查（mypy）
- [ ] 所有导入正常工作
- [ ] 核心功能有基本测试（至少3个）
- [ ] 文档完整

### ⏱️ 预计时间

- 阶段 1: 2-3 小时
- 阶段 2: 3-4 小时
- 阶段 3: 4-5 小时
- **总计**: 9-12 小时

### 🎯 当前状态

代码**可以运行**，但有潜在问题和改进空间。建议先修复 P0 问题，然后进行优化。
