# 项目修复计划

## 概述

本计划旨在修复Unified AI项目中的问题，同时确保修复范围限制在项目本体（源代码）内，不包括下载的内容（依赖、模型、数据集等）。

## 修复原则

1. **范围限制**：仅修复项目本体文件，包括：
   - apps/backend/src/
   - apps/frontend-dashboard/src/
   - apps/desktop-app/src/
   - packages/cli/src/
   - packages/ui/src/
   - tools/
   - scripts/

2. **排除内容**：不修复以下内容：
   - 下载的依赖（node_modules、venv等）
   - 下载的模型（model_cache、checkpoints等）
   - 下载的数据集（data、chroma_db等）
   - 缓存文件（__pycache__、.pytest_cache等）
   - 二进制文件（.pyc、.pyo、.dll、.exe等）

## 已完成的工作

### 1. 依赖检查和安装 ✅
- 前端依赖：通过pnpm安装完成
- 后端依赖：创建了requirements.txt和requirements-dev.txt，安装完成

### 2. 损坏文件修复 ✅
- 修复了缺失的API模块：apps/backend/src/api/__init__.py
- 修复了缺失的路由文件：apps/backend/src/api/routes.py
- 修复了缺失的系统管理器：apps/backend/src/core/managers/system_manager.py
- 修复了缺失的配置文件：apps/backend/src/core/config/system_config.py
- 简化了level5_config.py以修复导入错误

### 3. 自动修复系统范围限制 ✅
- 更新了tools/unified-fix.py，添加了项目范围限制
- 实现了ProjectScopeFixer类，确保只修复项目本体文件
- 添加了排除目录和文件类型的检查

### 4. 禁用未限制范围的修复脚本 ✅
- 识别了71个fix*.py脚本
- 禁用了主要的未限制修复脚本，包括：
  - tools/scripts/fix_all_syntax_errors.py
  - tools/scripts/fix_import_paths.py
  - tools/fix_import_paths.py
- 创建了归档目录：archived_fix_scripts/unrestricted_scripts_20251013

## 下一步工作

### 5. 检查并加强自动修复系统可用性 (进行中)
- 需要测试unified-fix.py的功能
- 验证范围限制是否正确工作
- 增强修复能力（如导入错误修复）

### 6. 恢复已归档的修复功能 (待处理)
- 分析已归档脚本的有用功能
- 重新实现具有范围限制的版本
- 整合到unified-fix.py中

### 7. 执行项目修复并检查成果 (待处理)
- 使用限制范围的修复系统扫描项目
- 修复发现的问题
- 验证修复效果

## 技术细节

### 修复范围配置
```python
self.project_scope_dirs = [
    "apps/backend/src",
    "apps/frontend-dashboard/src",
    "apps/desktop-app/src",
    "packages/cli/src",
    "packages/ui/src",
    "tools",
    "scripts"
]

self.exclude_dirs = [
    "node_modules",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "data",
    "model_cache",
    "checkpoints",
    "logs",
    "chroma_db",
    "chromadb_local"
]
```

### 使用方法
```bash
# 运行完整修复
python tools/unified-fix.py

# 只修复语法错误
python tools/unified-fix.py --type syntax

# 只修复导入错误
python tools/unified-fix.py --type import

# 详细输出
python tools/unified-fix.py --verbose
```

## 注意事项

1. **安全第一**：所有修复操作都限制在项目源代码范围内
2. **备份重要**：在执行修复前建议创建项目备份
3. **渐进修复**：优先修复语法错误，再处理导入错误
4. **验证结果**：修复后运行测试确保功能正常

## 预期成果

1. 项目所有源代码文件的语法正确
2. 导入路径问题得到解决
3. 项目可以正常启动和运行
4. 自动修复系统具备范围限制能力
5. 旧的未限制修复脚本被安全归档

## 完成标准

- [ ] 所有Python文件语法检查通过
- [ ] 所有导入错误修复完成
- [ ] 后端服务可以正常启动
- [ ] 前端服务可以正常启动
- [ ] 测试套件可以正常运行
- [ ] 自动修复系统功能验证通过

---

创建日期：2025-10-13
最后更新：2025-10-13