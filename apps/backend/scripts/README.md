# 自动修复工具使用说明

这个目录包含了几个自动修复工具，用于解决项目中的导入路径问题。

## 工具介绍

### 1. simple_auto_fix.py
简化版自动修复工具，专门修复 `core_ai` 模块的导入路径问题。

### 2. auto_fix_complete.py
完整版自动修复工具，修复所有已知模块的导入路径问题。

### 3. advanced_auto_fix.py
增强版自动修复工具，具有以下特性：
- 智能AST解析，准确识别导入语句
- 自动备份机制，确保安全修复
- 详细的修复报告
- 模块导入验证
- 错误处理和日志记录

### 4. final_validation.py
最终验证脚本，用于验证所有已知问题是否已解决：
- 验证原始问题中的导入是否修复
- 测试核心服务导入
- 测试主API服务器导入
- 验证DialogueManager中的HSPConnector
- 运行综合导入测试

### 5. auto_fix.bat
Windows批处理脚本，提供图形化菜单界面。

### 6. auto_fix.sh
Linux/Mac Shell脚本，提供交互式菜单界面。

### 7. test_fix_demo.py
自动修复工具演示脚本，展示如何使用自动修复工具解决原始问题。

## 使用方法

### 使用pnpm命令（推荐）

```bash
# 运行简化版自动修复
pnpm fix

# 运行完整版自动修复
pnpm fix:complete

# 运行增强版自动修复
pnpm fix:advanced

# 修复后运行测试
pnpm fix:test

# 增强版修复后运行测试
pnpm fix:advanced:test

# 运行最终验证
pnpm validate

# 自动修复并验证
pnpm validate:fix

# 运行演示脚本
pnpm demo:fix
```

### 直接运行脚本

```bash
# 激活虚拟环境后运行
cd apps/backend

# 简化版
python scripts/simple_auto_fix.py

# 完整版
python scripts/auto_fix_complete.py

# 增强版
python scripts/advanced_auto_fix.py

# 增强版带测试
python scripts/advanced_auto_fix.py --test

# 最终验证
python scripts/final_validation.py

# 演示脚本
python scripts/test_fix_demo.py
```

### 使用批处理脚本（Windows）

```cmd
# 在Windows环境下双击运行或在命令行中执行
apps\backend\scripts\auto_fix.bat
```

### 使用Shell脚本（Linux/Mac）

```bash
# 在Linux/Mac环境下运行
chmod +x apps/backend/scripts/auto_fix.sh
./apps/backend/scripts/auto_fix.sh
```

## 功能说明

### 自动扫描
工具会自动扫描项目中的所有Python文件，查找需要修复的导入语句。

### 自动修复
工具会自动将以下类型的导入语句进行修复：

```python
# 修复前
from core_ai.agent_manager import AgentManager
import core_ai.dialogue.dialogue_manager
from ..core_ai.dialogue import dialogue_manager

# 修复后
from apps.backend.src.core_ai.agent_manager import AgentManager
import apps.backend.src.core_ai.dialogue.dialogue_manager
from apps.backend.src.core_ai.dialogue import dialogue_manager
```

### 自动备份
增强版工具会在每次修复前自动备份文件，确保安全。

### 自动验证
修复完成后，工具会自动验证关键模块是否能够正确导入。

### 自动测试
可以选择在修复完成后自动运行测试，确保修复没有引入新的问题。

## 支持的模块

工具支持修复以下模块的导入路径：
- core_ai.*
- core.*
- services.*
- hsp.*
- mcp.*
- system.*
- tools.*
- shared.*
- agents.*
- game.*

## 增强版工具特性

### 智能AST解析
使用Python AST模块准确解析导入语句，避免误修复。

### 自动备份机制
每次运行都会创建时间戳备份目录，自动备份被修改的文件。

### 详细修复报告
生成JSON格式的修复报告，包含：
- 修复时间戳
- 扫描文件数
- 修复文件数
- 应用修复数
- 错误和警告信息
- 修复文件列表

### 模块导入验证
修复完成后自动验证关键模块是否能正确导入。

## 命令行选项

### advanced_auto_fix.py 选项

```bash
--test          # 修复后运行测试
--no-backup     # 不创建备份
--verbose       # 详细输出
```

## 最终验证脚本功能

### 原始问题导入测试
验证用户最初报告的两个问题是否已解决：
1. `NameError: name 'HSPConnector' is not defined`
2. `ModuleNotFoundError: No module named 'core_ai'`

### 核心服务导入测试
验证核心服务模块是否能正确导入：
- `core_services.py`
- 相关的类和函数

### 主API服务器导入测试
验证主API服务器是否能正确导入。

### DialogueManager HSPConnector测试
验证DialogueManager中的HSPConnector参数是否正确定义。

### 综合导入测试
测试项目中所有关键模块的导入。

## 演示脚本功能

### test_fix_demo.py
演示脚本展示自动修复工具如何解决原始问题：
1. 创建一个有问题的测试文件
2. 演示原始导入问题
3. 运行自动修复
4. 验证修复结果
5. 清理测试文件

## 图形化界面工具

### Windows批处理脚本
`auto_fix.bat` 提供了简单的菜单界面：
1. 简化版自动修复
2. 完整版自动修复
3. 增强版自动修复
4. 增强版自动修复 + 测试
5. 最终验证
6. 自动修复 + 验证
7. 退出

### Linux/Mac Shell脚本
`auto_fix.sh` 提供了类似的交互式菜单界面。

## 注意事项

1. 工具会跳过备份目录、node_modules目录和虚拟环境目录
2. 工具会自动检测是否已经修复过某个文件，避免重复修复
3. 如果遇到多个同名文件或找不到目标文件的情况，工具会跳过该文件并给出提示
4. 建议在运行工具前先备份项目代码
5. 增强版工具会自动创建备份，但建议仍保留项目备份

## 故障排除

如果自动修复工具无法解决问题，请手动检查以下几点：

1. 确保虚拟环境已正确激活
2. 检查文件路径是否正确
3. 确认模块是否确实存在于项目中
4. 检查是否有循环导入问题
5. 查看修复报告中的错误和警告信息

## 备份管理

增强版工具会自动创建备份：
- 备份目录：`backup/auto_fix_{timestamp}`
- 包含被修改的文件和修复报告
- 可用于回滚操作

## 推荐工作流程

1. **首次使用**：
   ```bash
   pnpm validate  # 首先验证当前状态
   ```

2. **自动修复**：
   ```bash
   pnpm validate:fix  # 自动修复并验证
   ```

3. **日常开发**：
   ```bash
   pnpm dev  # 正常启动开发环境
   ```

4. **问题排查**：
   ```bash
   pnpm validate  # 验证导入问题
   pnpm fix:advanced  # 运行增强版修复
   ```

5. **图形化界面**：
   - Windows用户可以双击运行 `apps\backend\scripts\auto_fix.bat`
   - Linux/Mac用户可以运行 `./apps/backend/scripts/auto_fix.sh`

6. **演示和学习**：
   ```bash
   pnpm demo:fix  # 运行演示脚本了解修复过程
   ```