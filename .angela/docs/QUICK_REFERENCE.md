# 🚀 Angela AI 工具系统快速参考

**版本**: 1.0.0  
**最后更新**: 2026-02-19

---

## 📂 工具系统结构

```
项目根目录/
├── tools/                           # 🔧 通用工具 (适用于任何项目)
│   ├── hash_annotator.py           # 文件哈希注释器
│   └── [其他通用工具]
│
├── .angela/                         # 🎯 Angela专用
│   ├── tools/                      # Angela专用工具
│   │   ├── angela_ham_tracker.py       # HAM系统追踪
│   │   ├── angela_layer_validator.py   # 6层架构验证
│   │   └── angela_matrix_updater.py    # Matrix标记更新
│   │
│   ├── hashes/                     # Angela专用哈希数据库
│   │   └── ham_memory_hashes.json
│   │
│   ├── config/                     # Angela配置
│   │   └── angela_config.yaml
│   │
│   └── docs/                       # Angela文档
│       └── TOOLS_DISTINCTION.md    # 工具区分说明
│
└── docs/workflow/                  # 流程文档
    ├── STANDARD_PROCESS.md         # 标准流程
    ├── FLOW_DEMONSTRATION.md       # 实战演示
    └── HASH_GUIDELINES.md          # 哈希规范
```

---

## 🎯 快速选择指南

### 我需要做什么？

#### 🔹 管理文件哈希和依赖

**使用**: `tools/hash_annotator.py` (通用)

```bash
# 为文件添加哈希注释
python tools/hash_annotator.py annotate --file path/to/file.py

# 扫描整个项目
python tools/hash_annotator.py scan

# 验证哈希唯一性
python tools/hash_annotator.py validate
```

#### 🔹 分析Angela的HAM记忆系统

**使用**: `.angela/tools/angela_ham_tracker.py` (Angela专用)

```bash
# 扫描HAM存储
python .angela/tools/angela_ham_tracker.py scan

# 验证HAM完整性
python .angela/tools/angela_ham_tracker.py verify

# 生成HAM报告
python .angela/tools/angela_ham_tracker.py report
```

#### 🔹 验证6层架构

**使用**: `.angela/tools/angela_layer_validator.py` (Angela专用)

```bash
# 验证所有层
python .angela/tools/angela_layer_validator.py validate

# 查看特定层
python .angela/tools/angela_layer_validator.py validate --layer L2

# 生成架构报告
python .angela/tools/angela_layer_validator.py report
```

#### 🔹 更新Angela Matrix标记

**使用**: `.angela/tools/angela_matrix_updater.py` (Angela专用)

```bash
# 更新所有文件的Matrix标记
python .angela/tools/angela_matrix_updater.py update --all

# 验证Matrix覆盖率
python .angela/tools/angela_matrix_updater.py validate

# 生成覆盖率报告
python .angela/tools/angela_matrix_updater.py report
```

---

## 📋 常用命令速查表

### 通用工具

| 命令                                                              | 说明           |
| ----------------------------------------------------------------- | -------------- |
| `python tools/hash_annotator.py annotate --file <file>`           | 为文件添加哈希 |
| `python tools/hash_annotator.py annotate --dir <dir> --recursive` | 为目录添加哈希 |
| `python tools/hash_annotator.py validate`                         | 验证哈希       |
| `python tools/hash_annotator.py scan --output <file>`             | 扫描项目       |

### Angela专用工具

| 命令                                                                 | 说明       |
| -------------------------------------------------------------------- | ---------- |
| `python .angela/tools/angela_ham_tracker.py scan`                    | 扫描HAM    |
| `python .angela/tools/angela_ham_tracker.py verify`                  | 验证HAM    |
| `python .angela/tools/angela_layer_validator.py validate`            | 验证架构   |
| `python .angela/tools/angela_layer_validator.py validate --layer L2` | 验证L2层   |
| `python .angela/tools/angela_matrix_updater.py update --all`         | 更新Matrix |
| `python .angela/tools/angela_matrix_updater.py validate`             | 验证Matrix |

---

## 🔍 何时使用哪个工具？

### 使用通用工具当...

✅ 处理通用文件管理  
✅ 建立基础文件追踪  
✅ 分析标准依赖关系  
✅ 工具需要可移植到其他项目

### 使用Angela专用工具当...

✅ 处理HAM记忆系统  
✅ 验证6层架构  
✅ 维护Angela Matrix标记  
✅ 分析Angela特定组件 (HAM, LU, CDM, HSM)

---

## 🎨 文件头注释对比

### 通用格式 (hash_annotator)

```python
# =============================================================================
# FILE_HASH: A1B2C3D4
# FILE_PATH: apps/backend/src/ai/service.py
# FILE_TYPE: python
# PURPOSE: AI服务实现
# VERSION: 6.2.1
# STATUS: active
# DEPENDENCIES: []
# LAST_MODIFIED: 2026-02-19
# =============================================================================
```

### Angela专用格式 (包含Matrix)

```python
# =============================================================================
# FILE_HASH: HAM001
# FILE_PATH: apps/backend/src/ai/memory/ham_memory/ham_manager.py
# FILE_TYPE: memory
# PURPOSE: HAM记忆管理器
# VERSION: 6.2.1
# STATUS: production_ready
# LAYER: L2 (Memory Layer)
# DEPENDENCIES: [BASE001, ENC002]
# LAST_MODIFIED: 2026-02-19
# =============================================================================
# Angela Matrix: [L2:MEM] [HAM] Hierarchical Associative Memory
# α: L2 | β: 0.95 | γ: 0.95 | δ: 0.90
# =============================================================================
```

---

## ⚠️ 常见错误与解决

### 错误 1: 权限不足

```bash
chmod +x tools/hash_annotator.py
chmod +x .angela/tools/*.py
```

### 错误 2: 找不到模块

```bash
# 确保在正确的目录运行
cd D:\Projects\Unified-AI-Project
python tools/hash_annotator.py
```

### 错误 3: 误用工具

```bash
# ❌ 错误: 用通用工具分析HAM
python tools/hash_annotator.py scan --dir apps/backend/src/ai/memory/ham_memory/

# ✅ 正确: 用Angela专用工具
python .angela/tools/angela_ham_tracker.py scan
```

---

## 📊 工具状态总览

### 已完成 ✅

| 工具                                      | 类型       | 状态 | 用途           |
| ----------------------------------------- | ---------- | ---- | -------------- |
| `tools/hash_annotator.py`                 | 通用       | ✅   | 文件哈希管理   |
| `.angela/tools/angela_ham_tracker.py`     | Angela专用 | ✅   | HAM系统追踪    |
| `.angela/tools/angela_layer_validator.py` | Angela专用 | ✅   | 6层架构验证    |
| `.angela/tools/angela_matrix_updater.py`  | Angela专用 | ✅   | Matrix标记更新 |

### 待创建 ⏳

| 工具                           | 类型 | 计划 | 用途         |
| ------------------------------ | ---- | ---- | ------------ |
| `tools/dependency_analyzer.py` | 通用 | ⏳   | 通用依赖分析 |
| `tools/call_tracker.py`        | 通用 | ⏳   | 通用调用追踪 |
| `tools/workflow_validator.py`  | 通用 | ⏳   | 通用流程验证 |

---

## 📖 相关文档

### 通用文档

- `docs/workflow/STANDARD_PROCESS.md` - 标准流程
- `docs/workflow/FLOW_DEMONSTRATION.md` - 实战演示

### Angela专用文档

- `.angela/docs/TOOLS_DISTINCTION.md` - 工具区分说明
- `GIT_HISTORY_ANALYSIS.md` - Git历史分析

### 实施报告

- `IMPLEMENTATION_COMPLETE_REPORT.md` - 实施完成报告
- `PROJECT_SOLUTIONS.md` - 问题解决方案

---

## 🎯 5分钟入门

### 第1步: 验证工具可用

```bash
python tools/hash_annotator.py --help
python .angela/tools/angela_ham_tracker.py --help
```

### 第2步: 扫描项目状态

```bash
python tools/hash_annotator.py scan
```

### 第3步: 验证Angela架构

```bash
python .angela/tools/angela_layer_validator.py validate
```

### 第4步: 检查HAM系统

```bash
python .angela/tools/angela_ham_tracker.py report
```

---

## 💡 最佳实践

1. **先通用，后专用**
   - 先用通用工具建立基础
   - 再用Angela工具深度分析

2. **定期验证**
   - 每周运行一次架构验证
   - 每次修改后更新Matrix标记

3. **保持文档更新**
   - 修改后更新文件头注释
   - 记录变更日志

4. **不要混用**
   - HAM相关问题用 angela_ham_tracker
   - 通用文件问题用 hash_annotator

---

## 🔗 快速链接

- 查看区分说明: `.angela/docs/TOOLS_DISTINCTION.md`
- 查看标准流程: `docs/workflow/STANDARD_PROCESS.md`
- 查看实战演示: `docs/workflow/FLOW_DEMONSTRATION.md`

---

**记住口诀**:

- 通用问题 → `tools/`
- Angela问题 → `.angela/tools/`

**现在就开始使用吧！** 🚀

---

_本文档提供了快速上手指南，详细说明请参考各工具的文档字符串和相关文档。_
