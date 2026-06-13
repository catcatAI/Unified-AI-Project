# 🔧 Angela AI 标准化开发与维护流程

**版本**: 1.0.0  
**创建时间**: 2026-02-19  
**适用对象**: 所有开发者、AI Agent、代码审查者

---

## 📋 流程概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    标准化开发维护流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: 分析阶段                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ 初步扫描     │ -> │ 依赖分析     │ -> │ 问题识别     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  生成文件清单         生成依赖图          标记问题文件           │
│                                                                 │
│  Phase 2: 深入分析阶段                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ 代码审查     │ -> │ 调用链分析   │ -> │ 影响评估     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  添加哈希注释         建立调用地图        评估修改风险           │
│                                                                 │
│  Phase 3: 解决问题阶段                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ 制定方案     │ -> │ 实施修改     │ -> │ 验证测试     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  更新哈希映射         添加变更日志        回归测试               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 核心原则

### 1. 每个关键实体必须有唯一哈希标识

**需要哈希标识的实体**:

- ✅ 文件 (FILE_HASH)
- ✅ 函数/方法 (FUNC_HASH)
- ✅ 类 (CLASS_HASH)
- ✅ 模块 (MODULE_HASH)
- ✅ 配置文件 (CONFIG_HASH)
- ✅ API端点 (API_HASH)
- ✅ 数据库表 (TABLE_HASH)

### 2. 每个调用必须有明确的调用链记录

**调用关系必须记录**:

- 调用方 (CALLER_HASH)
- 被调用方 (CALLEE_HASH)
- 调用路径 (CALL_PATH)
- 调用类型 (CALL_TYPE: import | function | api | db)

### 3. 避免混淆的注释规范

**所有注释必须包含**:

```python
# =============================================================================
# FILE_HASH: <8位十六进制>
# FILE_PATH: <标准化路径>
# FILE_TYPE: <类型>
# PURPOSE: <一句话说明>
# VERSION: <版本号>
# STATUS: <active|deprecated|draft>
# DEPENDENCIES: <依赖文件HASH列表>
# CALLEES: <被调用文件HASH列表>
# =============================================================================
```

---

## 📁 标准化目录结构

```
D:\Projects\Unified-AI-Project/
├── .hashes/                          # 哈希数据库
│   ├── file_hashes.json              # 文件哈希映射
│   ├── func_hashes.json              # 函数哈希映射
│   ├── call_graph.json               # 调用关系图
│   └── api_hashes.json               # API端点哈希
├── .workflow/                        # 工作流配置
│   ├── analysis_config.yaml          # 分析配置
│   ├── hash_rules.json               # 哈希规则
│   └── validation_rules.json         # 验证规则
├── tools/                            # 开发工具
│   ├── call_tracker.py               # 调用追踪器
│   ├── dependency_analyzer.py        # 依赖分析器
│   └── workflow_validator.py         # 流程验证器
├── docs/workflow/                    # 流程文档
│   ├── STANDARD_PROCESS.md           # 标准流程
│   ├── HASH_GUIDELINES.md            # 哈希规范
│   └── TROUBLESHOOTING.md            # 问题排查
└── [项目代码...]
```

---

## 🔍 Phase 1: 分析阶段

### 步骤 1.1: 初步扫描

**目标**: 生成项目文件清单

**执行**:

```bash
# (Deprecated: hash_annotator.py removed — use manual file inventory or alternative tooling)
# python tools/hash_annotator.py scan --output .hashes/file_inventory.json
```

**输出**:

```json
{
  "scan_time": "2026-02-19T10:00:00Z",
  "total_files": 20503,
  "files_by_type": {
    "python": 17718,
    "javascript": 127,
    "markdown": 883,
    "json": 1635
  },
  "files": [
    {
      "path": "apps/backend/main.py",
      "size": 18784,
      "last_modified": "2026-02-19T09:00:00Z",
      "current_hash": "FE20AD61",
      "status": "active"
    }
  ]
}
```

### 步骤 1.2: 依赖分析

**目标**: 识别文件间的依赖关系

**执行**:

```bash
python tools/dependency_analyzer.py analyze --deep
```

**输出**:

```json
{
  "dependencies": {
    "FE20AD61": {
      "file": "apps/backend/main.py",
      "imports": [
        {
          "hash": "SEC001",
          "path": "src.system.security_monitor",
          "type": "internal"
        },
        {
          "hash": "MID001",
          "path": "src.shared.security_middleware",
          "type": "internal"
        },
        { "hash": "FASTAPI", "path": "fastapi", "type": "external" }
      ],
      "imported_by": [
        { "hash": "LAU001", "path": "run_angela.py", "type": "launcher" }
      ]
    }
  }
}
```

### 步骤 1.3: 问题识别

**目标**: 识别需要解决的问题

**检查清单**:

- [ ] 文件重复 (同名不同路径)
- [ ] 未完成的代码 (大量注释)
- [ ] 缺失的导入
- [ ] 版本不一致
- [ ] 没有哈希注释的文件
- [ ] 循环依赖

**执行**:

```bash
python tools/workflow_validator.py identify-issues
```

**输出**:

```json
{
  "issues": [
    {
      "type": "missing_hash",
      "severity": "high",
      "file": "apps/backend/src/ai/new_module.py",
      "recommendation": "Add FILE_HASH comment"
    },
    {
      "type": "duplicate",
      "severity": "medium",
      "files": [
        "trust_manager_module.py",
        "trust_manager/trust_manager_module.py"
      ],
      "recommendation": "Consolidate into one file"
    }
  ]
}
```

---

## 🔬 Phase 2: 深入分析阶段

### 步骤 2.1: 代码审查与哈希注释

**目标**: 为所有关键代码添加哈希注释

**执行**:

```bash
# (Deprecated: hash_annotator.py removed — hash annotations must be added manually or via alternative tooling)
# python tools/hash_annotator.py annotate --target apps/backend/src --recursive

# 验证哈希唯一性
# python tools/hash_annotator.py validate --check-collisions
```

**生成的注释示例**:

**Python文件**:

```python
# =============================================================================
# FILE_HASH: A1B2C3D4
# FILE_PATH: apps/backend/src/ai/service.py
# FILE_TYPE: service
# PURPOSE: AI服务核心实现
# VERSION: 6.2.1
# STATUS: active
# DEPENDENCIES: [FE20AD61, SEC001, MID001]
# CALLEES: [AI001, AI002]
# =============================================================================

# 函数级别注释
# FUNC_HASH: F1A2B3C4
# PURPOSE: 处理AI请求
# CALLS: [F5D6E7F8, F9A0B1C2]
def process_ai_request(request):
    """处理AI请求

    FUNC_HASH: F1A2B3C4
    CALLEE_HASHES: [F5D6E7F8, F9A0B1C2]
    """
    pass
```

**JavaScript文件**:

```javascript
/**
 * =============================================================================
 * @file service.js
 * @hash J1A2B3C4
 * @path apps/desktop-app/electron_app/js/service.js
 * @type service
 * @purpose 桌面端服务实现
 * @version 6.2.1
 * @status active
 * @dependencies [J5D6E7F8]
 * =============================================================================
 */

/**
 * 处理请求
 * @func_hash F1A2B3C4
 * @calls [F5D6E7F8]
 */
function processRequest() {
  // implementation
}
```

### 步骤 2.2: 调用链分析

**目标**: 建立完整的调用关系地图

**执行**:

```bash
python tools/call_tracker.py build-graph --include-api --include-db
```

**输出** (call_graph.json):

```json
{
  "nodes": [
    { "hash": "FE20AD61", "type": "file", "path": "apps/backend/main.py" },
    { "hash": "F1A2B3C4", "type": "function", "name": "process_ai_request" },
    { "hash": "API001", "type": "api", "endpoint": "/api/v1/ai/process" }
  ],
  "edges": [
    { "from": "FE20AD61", "to": "SEC001", "type": "import" },
    { "from": "API001", "to": "F1A2B3C4", "type": "api_call" },
    { "from": "F1A2B3C4", "to": "DB001", "type": "db_query" }
  ]
}
```

**调用链可视化**:

```
main.py [FE20AD61]
├── import -> security_monitor [SEC001]
├── import -> middleware [MID001]
└── route -> /api/v1/ai/process [API001]
    └── calls -> process_ai_request() [F1A2B3C4]
        ├── calls -> validate_input() [F5D6E7F8]
        └── calls -> query_db() [DB001]
```

### 步骤 2.3: 影响评估

**目标**: 评估修改的影响范围

**执行**:

```bash
python tools/dependency_analyzer.py impact --target A1B2C3D4 --depth 3
```

**输出**:

```json
{
  "target": "A1B2C3D4",
  "impact_analysis": {
    "direct_dependencies": 5,
    "indirect_dependencies": 23,
    "api_endpoints_affected": 3,
    "tests_affected": 12,
    "risk_level": "high",
    "recommendation": "Comprehensive testing required"
  }
}
```

---

## 🔧 Phase 3: 解决问题阶段

### 步骤 3.1: 制定方案

**要求**:

1. 基于哈希标识指定修改范围
2. 列出所有受影响的文件 (通过依赖分析)
3. 制定回滚策略
4. 定义验证步骤

**方案模板**:

```markdown
## 修改方案

**目标文件**: apps/backend/src/ai/service.py [A1B2C3D4]

**影响范围**:

- 直接依赖: [SEC001, MID001]
- 间接依赖: [API001, API002, API003]
- 测试文件: [TEST001, TEST002]

**修改内容**:

1. 更新函数 process_ai_request [F1A2B3C4]
2. 修改数据库查询逻辑

**回滚策略**:

- 备份文件: archive/A1B2C3D4_20260219.py
- 回滚命令: git checkout A1B2C3D4

**验证步骤**:

1. 语法检查: python -m py_compile
2. 单元测试: pytest tests/test_service.py
3. 集成测试: python health_check.py
```

### 步骤 3.2: 实施修改

**执行规范**:

1. **备份原文件**:

```bash
# (Deprecated: hash_annotator.py removed — use git or manual backup)
# python tools/hash_annotator.py backup --hash A1B2C3D4 --to archive/
```

2. **实施修改** (带变更日志):

```python
# =============================================================================
# CHANGE_LOG:
# 2026-02-19: Modified by AI Assistant
#   - Enabled storage layer imports
#   - Implemented create_context logic
#   - PREV_HASH: EA4C6CBB
#   - CURR_HASH: 8DADEC46
# =============================================================================
```

3. **更新哈希映射**:

```bash
# (Deprecated: hash_annotator.py removed — update hash comments manually)
# python tools/hash_annotator.py update-hash --file service.py
```

### 步骤 3.3: 验证测试

**验证清单**:

- [ ] 语法检查通过
- [ ] 所有导入正常
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 哈希验证通过 (无碰撞)
- [ ] 调用链完整

**执行**:

```bash
# 完整验证流程
python tools/workflow_validator.py full-check --hash A1B2C3D4
```

---

## 🛠️ 工具使用指南

### 1. hash_annotator.py - 哈希注释器 *(Deprecated: removed)*

> **Note**: `tools/hash_annotator.py` has been removed. Hash annotations must be added and maintained manually or via alternative tooling.

**功能**: 自动添加和验证哈希注释

**常用命令** *(all commands no longer available)*:

```bash
# (Deprecated: hash_annotator.py removed)
# python tools/hash_annotator.py scan
# python tools/hash_annotator.py annotate --dir apps/backend/src
# python tools/hash_annotator.py validate
# python tools/hash_annotator.py backup --hash A1B2C3D4
# python tools/hash_annotator.py update --file path/to/file.py
```

### 2. call_tracker.py - 调用追踪器

**功能**: 分析调用关系

**常用命令**:

```bash
# 构建调用图
python tools/call_tracker.py build

# 查找调用链
python tools/call_tracker.py trace --from FE20AD61 --to DB001

# 查找谁调用了指定函数
python tools/call_tracker.py callers --hash F1A2B3C4

# 可视化调用图
python tools/call_tracker.py visualize --output call_graph.html
```

### 3. dependency_analyzer.py - 依赖分析器

**功能**: 分析文件依赖和影响范围

**常用命令**:

```bash
# 分析依赖
python tools/dependency_analyzer.py analyze

# 影响分析
python tools/dependency_analyzer.py impact --hash A1B2C3D4

# 查找循环依赖
python tools/dependency_analyzer.py cycles

# 导出依赖图
python tools/dependency_analyzer.py export --format json
```

### 4. workflow_validator.py - 流程验证器

**功能**: 验证整个开发流程

**常用命令**:

```bash
# 识别问题
python tools/workflow_validator.py identify-issues

# 完整检查
python tools/workflow_validator.py full-check

# 验证特定文件
python tools/workflow_validator.py check --hash A1B2C3D4

# 生成报告
python tools/workflow_validator.py report --output validation_report.md
```

---

## 📝 哈希注释规范

### Python 文件标准头部

```python
# =============================================================================
# FILE_HASH: <8位大写十六进制>
# FILE_PATH: <相对项目根目录的路径，统一小写，正斜杠>
# FILE_TYPE: <backend|frontend|service|tool|test|config>
# PURPOSE: <一句话描述文件用途>
# VERSION: <语义化版本号，如 6.2.1>
# STATUS: <active|deprecated|draft|experimental>
# DEPENDENCIES: [<依赖1_HASH>, <依赖2_HASH>, ...]
# CALLEES: [<被调用1_HASH>, <被调用2_HASH>, ...]
# CREATED: <创建日期，格式 YYYY-MM-DD>
# LAST_MODIFIED: <最后修改日期>
# AUTHOR: <作者或团队>
# =============================================================================
```

### 函数/方法注释

```python
# FUNC_HASH: <8位大写十六进制>
# PURPOSE: <函数用途>
# PARAMS: <参数说明>
# RETURNS: <返回值说明>
# CALLS: [<被调用函数_HASH>, ...]
# CALLED_BY: [<调用者_HASH>, ...]
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """函数文档字符串

    FUNC_HASH: F1A2B3C4
    PURPOSE: 详细说明函数功能

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        返回值说明

    Raises:
        ExceptionType: 异常说明

    Example:
        >>> result = function_name(value1, value2)
        >>> print(result)
    """
    pass
```

### 类注释

```python
# CLASS_HASH: <8位大写十六进制>
# PURPOSE: <类用途>
# INHERITS: [<父类_HASH>, ...]
# USED_BY: [<使用者_HASH>, ...]
class ClassName:
    """类文档字符串

    CLASS_HASH: C1A2B3D4
    PURPOSE: 类的详细说明

    Attributes:
        attr1: 属性1说明
        attr2: 属性2说明

    Methods:
        method1: 方法1说明 [HASH: M1A2B3C4]
        method2: 方法2说明 [HASH: M5D6E7F8]
    """
    pass
```

---

## 🚨 常见错误与避免方法

### 错误 1: 哈希冲突

**症状**: 两个文件有相同的 FILE_HASH

**避免**:

```bash
# (Deprecated: hash_annotator.py removed — use manual inspection or alternative tooling)
# 验证前检查冲突
# python tools/hash_annotator.py validate --check-collisions

# 如果发现冲突，重新生成
# python tools/hash_annotator.py regenerate --file conflicting_file.py
```

### 错误 2: 调用链断裂

**症状**: CALLEES 指向不存在的哈希

**避免**:

```bash
# 验证调用链完整性
python tools/call_tracker.py validate --check-dangling
```

### 错误 3: 路径不一致

**症状**: Windows路径和Unix路径混用

**避免**:

```bash
# (Deprecated: hash_annotator.py removed — normalize paths manually)
# 标准化所有路径
# python tools/hash_annotator.py normalize-paths
```

### 错误 4: 版本号不一致

**症状**: 文件头写 6.2.0，但 VERSION 文件写 6.2.1

**避免**:

```bash
# (Deprecated: hash_annotator.py removed — sync version numbers manually)
# 同步版本号
# python tools/hash_annotator.py sync-version
```

---

## 📊 质量保证检查清单

### 提交前必须检查

- [ ] 所有修改的文件都有 FILE_HASH 注释
- [ ] 所有新函数都有 FUNC_HASH 注释
- [ ] 哈希唯一性验证通过
- [ ] 调用链验证通过
- [ ] 依赖关系已更新
- [ ] 影响分析已完成
- [ ] 备份已创建
- [ ] 测试全部通过
- [ ] 文档已更新

### 审查清单

- [ ] 代码逻辑正确
- [ ] 类型提示完整
- [ ] 错误处理适当
- [ ] 日志记录充分
- [ ] 性能考虑到位
- [ ] 安全性检查通过
- [ ] 向后兼容性保持

---

## 🔄 持续维护

### 每日任务

- 运行 `workflow_validator.py full-check`
- 检查是否有新文件缺失哈希

### 每周任务

- 更新依赖图
- 审查调用链变化
- 生成维护报告

### 发布前任务

- 完整验证所有哈希
- 生成最终调用图
- 更新版本号
- 生成发布说明

---

**最后更新**: 2026-02-19  
**维护者**: Angela AI Development Team  
**状态**: Active
