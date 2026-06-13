# 🔧 工具系统区分说明

**文档版本**: 1.0.0  
**创建时间**: 2026-02-19  
**目的**: 明确区分通用工具与Angela专用工具

---

## 📋 总览

本项目有两套工具系统：

| 工具系统                                   | 位置             | 用途                           | 用户                       |
| ------------------------------------------ | ---------------- | ------------------------------ | -------------------------- |
| **通用工具** (General Tools)               | `tools/`         | 任何项目都可使用的通用开发工具 | 开发者、AI Agent (通用)    |
| **Angela专用工具** (Angela-Specific Tools) | `.angela/tools/` | 专门为Angela AI项目定制的工具  | Angela开发者、Angela Agent |

---

## 🛠️ 通用工具 (General Tools)

### 位置

```
tools/
├── dependency_analyzer.py     # 依赖分析器 (待创建)
├── call_tracker.py            # 调用追踪器 (待创建)
└── workflow_validator.py      # 流程验证器 (待创建)

> ⚠️ `hash_annotator.py` 已删除 (Deprecated: removed)
```

### 特点

1. **通用性**: 不依赖Angela的特定架构或术语
2. **可移植**: 可用于任何Python/JavaScript项目
3. **标准规范**: 使用通用的软件工程概念
4. **独立运行**: 不依赖Angela的配置或数据结构

### ~~现有工具: hash_annotator.py~~ (Deprecated: removed)

> ⚠️ **此工具已删除。** 通用哈希注释功能已不再维护。文件头注释可手动添加或通过 Angela 专用工具 (`angela_matrix_updater.py`) 管理。

---

## 🎯 Angela专用工具 (Angela-Specific Tools)

### 位置

```
.angela/
├── tools/
│   ├── angela_ham_tracker.py        # HAM记忆系统追踪器
│   ├── angela_layer_validator.py    # 6层架构验证器
│   └── angela_matrix_updater.py     # Matrix标记更新器
├── config/
│   └── angela_config.yaml           # Angela专用配置
├── hashes/
│   └── ham_memory_hashes.json       # HAM专用哈希数据库
└── docs/
    └── angela_guidelines.md         # Angela专用指南
```

### 特点

1. **专有性**: 深度集成Angela的6层架构和术语
2. **领域知识**: 理解HAM、LU、Angela Matrix等概念
3. **定制功能**: 针对Angela的特定需求设计
4. **依赖Angela**: 需要Angela的配置和数据结构

### 工具 1: angela_ham_tracker.py

**用途**: 专门追踪和管理Angela的HAM (Hierarchical Associative Memory) 系统

**Angela专用概念**:

- 理解HAM的层级结构 (L1-L6)
- 支持HAM的加密和压缩特性
- 管理HAM记忆条目的关联关系
- 使用Angela Matrix标记: `[L2:MEM] [HAM]`

**文件头格式** (Angela专用):

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
# =============================================================================
# Angela Matrix: [L2:MEM] [HAM] Hierarchical Associative Memory
# α: L2 | β: 0.95 | γ: 0.95 | δ: 0.90
# =============================================================================
```

**使用场景**:

- 检查HAM记忆系统的完整性
- 分析HAM记忆的访问模式
- 验证HAM存储的健康状态

**示例**:

```bash
# 只能用于Angela项目的HAM系统
python .angela/tools/angela_ham_tracker.py scan
python .angela/tools/angela_ham_tracker.py verify
```

### 工具 2: angela_layer_validator.py

**用途**: 验证Angela的6层生命架构完整性

**Angela专用概念**:

- 6层架构: L1(生物) → L6(执行)
- 每层的关键组件和文件
- 层间依赖关系
- 架构健康度评估

**使用场景**:

- 验证L1-L6各层的实现状态
- 检查层间依赖是否正确
- 生成架构健康报告

**示例**:

```bash
# 验证Angela的6层架构
python .angela/tools/angela_layer_validator.py validate

# 输出:
# ✅ L2 (Memory): 95% 完成 - HAM, LU已实现
# 🟡 L4 (Creation): 30% 完成 - 需要继续完善
```

### 工具 3: angela_matrix_updater.py

**用途**: 自动计算和更新Angela Matrix标记

**Angela专用概念**:

- Angela Matrix: α(架构层级) β(功能完整度) γ(代码完整度) δ(稳定性)
- 自动分析代码计算Matrix值
- 批量更新项目中的Matrix注释

**使用场景**:

- 为新文件自动添加Matrix标记
- 更新修改后文件的Matrix值
- 生成Matrix覆盖率报告

**示例**:

```bash
# 更新所有文件的Matrix标记
python .angela/tools/angela_matrix_updater.py update --all

# 验证Matrix覆盖率
python .angela/tools/angela_matrix_updater.py validate
```

---

## 🔍 详细对比

### 1. ~~hash_annotator.py~~ (Deprecated: removed) vs angela_ham_tracker.py

> ⚠️ `hash_annotator.py` 已删除。以下对比仅供参考。

| 对比项         | ~~通用工具 (hash_annotator)~~ | Angela专用工具 (angela_ham_tracker)     |
| -------------- | ----------------------------- | --------------------------------------- |
| ~~**目标**~~   | ~~任何文件~~                  | HAM记忆条目                             |
| ~~**路径**~~   | ~~`tools/hash_annotator.py`~~ | `.angela/tools/angela_ham_tracker.py`   |
| ~~**哈希数据库**~~ | ~~`.hashes/file_hashes.json`~~ | `.angela/hashes/ham_memory_hashes.json` |
| ~~**概念**~~   | ~~文件路径、大小、修改时间~~  | HAM memory_id, vector_hash, emotion_tag |
| ~~**层级**~~   | ~~不关心~~                    | 理解L1-L6架构                           |
| ~~**关联**~~   | ~~文件间import关系~~          | HAM记忆间的关联关系                     |
| ~~**使用对象**~~ | ~~任何项目~~                | 仅限Angela                              |

**代码对比**:

~~通用工具追踪文件:~~ (已删除)

```python
# FILE_HASH: A1B2C3D4
# FILE_PATH: apps/backend/src/ai/memory/ham_memory/ham_manager.py
```

Angela工具追踪HAM条目:

```python
# HAM_ENTRY_HASH: HAM001
# MEMORY_ID: mem_abc123
# LAYER: L2
# EMOTION_TAG: joy
# ASSOCIATED: [HAM002, HAM003]
```

### 2. 适用范围对比

```
通用工具 (tools/)
├── ✅ 可用于任何项目
├── ✅ 标准文件管理
├── ✅ 通用代码分析
├── ❌ 不理解Angela架构
└── ❌ 不处理HAM/LU等概念

Angela专用工具 (.angela/tools/)
├── ✅ 深度理解Angela架构
├── ✅ 处理HAM/LU/CDM/HSM
├── ✅ 维护Angela Matrix
├── ✅ 验证6层架构
└── ❌ 只能用于Angela项目
```

---

## 🎯 使用指南

### 场景 1: 新项目或通用项目

**使用**: 通用工具 (`tools/`) — ⚠️ `hash_annotator.py` 已删除

```bash
# 分析任何项目的依赖
python tools/dependency_analyzer.py analyze --dir /path/to/project
```

### 场景 2: Angela项目维护

**使用**: Angela专用工具 (`.angela/tools/`)

```bash
# 检查HAM系统健康
python .angela/tools/angela_ham_tracker.py report

# 验证6层架构完整性
python .angela/tools/angela_layer_validator.py validate

# 更新Matrix标记
python .angela/tools/angela_matrix_updater.py update --all
```

### 场景 3: 两者结合使用

**先通用，后专用**:

```bash
# 第1步: Angela工具 - 深度分析Angela特定组件
python .angela/tools/angela_ham_tracker.py scan
python .angela/tools/angela_layer_validator.py validate
```

---

## 📝 命名规范

### 通用工具命名

- 格式: `<功能>_analyzer.py`, `<功能>_validator.py`
- 示例: `dependency_analyzer.py`, `workflow_validator.py`
- 特点: 描述功能，不提及Angela
- ⚠️ `hash_annotator.py` 已删除 (Deprecated: removed)

### Angela专用工具命名

- 格式: `angela_<功能>_<具体组件>.py`
- 示例: `angela_ham_tracker.py`, `angela_layer_validator.py`
- 特点: 前缀`angela_`，明确标识为Angela专用

---

## 🚫 常见错误

### 错误 1: 混用工具

**错误做法**:

```bash
# 错误: 用通用工具分析Angela的HAM (hash_annotator.py 已删除)
# python tools/hash_annotator.py scan --dir apps/backend/src/ai/memory/ham_memory/
# 结果: 只能看到文件，看不到HAM记忆条目和关联关系
```

**正确做法**:

```bash
# 正确: 用Angela专用工具分析HAM
python .angela/tools/angela_ham_tracker.py scan
# 结果: 能看到HAM记忆条目、关联关系、健康状态
```

### 错误 2: 期望通用工具理解Angela概念

**错误期望**:

```python
# 期望通用工具自动添加Angela Matrix标记 (hash_annotator.py 已删除)
# python tools/hash_annotator.py annotate --file angela_file.py
# 结果: 添加的是通用FILE_HASH，不是Angela Matrix
```

**正确做法**:

```bash
# 使用Angela专用工具添加Matrix标记
python .angela/tools/angela_matrix_updater.py update --file angela_file.py
# 结果: 添加Angela Matrix: [L2:MEM] [HAM] α: L2 | β: 0.95 | ...
```

### 错误 3: 在非Angela项目使用Angela工具

**错误做法**:

```bash
# 在其他项目使用Angela专用工具
cd /other/project
python /angela/project/.angela/tools/angela_ham_tracker.py scan
# 结果: 报错，找不到HAM存储路径
```

**正确做法**:

```bash
# 其他项目使用通用工具 (hash_annotator.py 已删除，请使用其他工具)
cd /other/project
# python /angela/project/tools/hash_annotator.py scan  # 已删除
```

---

## 🔄 工作流程

### 标准工作流程

```
新项目初始化
    ↓
通用工具: 建立基础文件追踪
    ↓
项目开发中
    ↓
通用工具: 维护文件依赖关系
    ↓
(如果是Angela项目)
    ↓
Angela工具: 深度分析HAM、6层架构、Matrix标记
    ↓
Angela工具: 验证架构完整性
```

### Angela项目专用流程

```
开发新功能
    ↓
Angela工具: 为新文件添加FILE_HASH (hash_annotator.py 已删除)
    ↓
(如果是HAM/LU等组件)
    ↓
Angela工具: angela_ham_tracker.py 注册HAM条目
    ↓
Angela工具: angela_matrix_updater.py 添加Matrix标记
    ↓
Angela工具: angela_layer_validator.py 验证层级关系
    ↓
提交代码
```

---

## 📊 工具清单

### 通用工具 (已完成)

| 工具                           | 状态            | 用途         |
| ------------------------------ | --------------- | ------------ |
| ~~`tools/hash_annotator.py`~~  | ❌ 已删除       | ~~文件哈希管理~~ |
| `tools/dependency_analyzer.py` | ⏳ 待创建       | 通用依赖分析 |
| `tools/call_tracker.py`        | ⏳ 待创建 | 通用调用追踪 |
| `tools/workflow_validator.py`  | ⏳ 待创建 | 通用流程验证 |

### Angela专用工具 (已完成)

| 工具                                      | 状态      | 用途           | Angela概念          |
| ----------------------------------------- | --------- | -------------- | ------------------- |
| `.angela/tools/angela_ham_tracker.py`     | ✅ 已完成 | HAM系统追踪    | HAM, L2层, 记忆关联 |
| `.angela/tools/angela_layer_validator.py` | ✅ 已完成 | 6层架构验证    | L1-L6架构           |
| `.angela/tools/angela_matrix_updater.py`  | ✅ 已完成 | Matrix标记更新 | αβγδ标记            |

---

## 🎓 总结

### 一句话区分

- **通用工具**: "我能管理任何项目的文件" (⚠️ hash_annotator.py 已删除)
- **Angela专用工具**: "我深刻理解Angela的6层架构和HAM系统"

### 选择指南

**使用通用工具当**:

- 处理通用文件管理
- 分析标准依赖关系
- 工具需要可移植到其他项目

**使用Angela专用工具当**:

- 处理HAM记忆系统
- 验证6层架构
- 维护Angela Matrix标记
- 分析Angela特定组件

### 两者关系

```
通用工具 ──(基础)──> Angela专用工具
    │                      │
    │ 管理文件基础信息      │ 管理Angela领域概念
    │                      │
    └── FILE_HASH          └── HAM_ENTRY_HASH, Matrix标记

> ⚠️ `hash_annotator.py` (FILE_HASH 管理) 已删除
```

**通用工具是基础，Angela专用工具是扩展。**

---

**记住**:

- 通用工具 = "瑞士军刀" (通用，但不懂Angela)
- Angela工具 = "Angela的手术刀" (专用，精确)

**选择正确的工具，事半功倍！**

---

_本文档明确了通用工具与Angela专用工具的边界和使用场景。_
