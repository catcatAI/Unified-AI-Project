# 备份与恢复标准化操作流程

> **备份说明**: 此文档已备份至 `backup_20250903/recovery_docs/BACKUP_RECOVERY_STANDARD_PROCEDURE.md.backup`，作为历史记录保存。
>
> **状态**: 问题已解决，此文档仅供历史参考。

## 1. 概述

本文档定义了 Unified AI Project 项目中备份与恢复操作的标准化流程，确保在执行任何修改前都进行适当的备份，并在需要时能够可靠地恢复文件。

## 2. 备份操作标准化流程

### 2.1 文件修改前备份流程

在对任何项目文件进行修改前，必须遵循以下备份流程：

#### 步骤 1: 确定要修改的文件
```
# 示例：确定要修改的文件
要修改的文件: apps/desktop-app/electron_app/main.js
```

#### 步骤 2: 创建备份文件
```bash
# 使用日期时间戳创建备份文件
cp apps/desktop-app/electron_app/main.js backup/desktop-app-main.js.backup_$(date +%Y%m%d_%H%M%S)
```

#### 步骤 3: 记录备份信息
在 [BACKUP_LOG.md](../../../../..) 中记录以下信息：
- 备份时间
- 原始文件路径
- 备份文件路径
- 备份原因
- 操作人员

#### 步骤 4: 验证备份完整性
```bash
# 检查备份文件是否存在且非空
if [ -s backup/desktop-app-main.js.backup_$(date +%Y%m%d_%H%M%S) ]; then
    echo "备份成功"
else
    echo "备份失败"
fi
```

### 2.2 批量文件备份流程

当需要备份多个文件时，使用以下流程：

#### 步骤 1: 创建备份清单
创建一个包含所有要备份文件的清单文件：
```bash
# backup_list.txt
apps/desktop-app/electron_app/main.js
packages/cli/cli/main.py
tools/train-manager.bat
scripts/setup_env.bat
```

#### 步骤 2: 执行批量备份
```bash
#!/bin/bash
# batch_backup.sh

# 创建带时间戳的备份目录
BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 读取备份清单并执行备份
while read file; do
    if [ -f "$file" ]; then
        # 创建目录结构
        FILE_DIR=$(dirname "$file")
        mkdir -p "$BACKUP_DIR/$FILE_DIR"
        
        # 执行备份
        cp "$file" "$BACKUP_DIR/$file"
        echo "已备份: $file"
    else
        echo "文件不存在: $file"
    fi
done < backup_list.txt

echo "批量备份完成，备份目录: $BACKUP_DIR"
```

#### 步骤 3: 验证批量备份
```bash
# 验证备份完整性
find backup/$(date +%Y%m%d_%H%M%S) -type f | wc -l
```

### 2.3 Git状态备份流程

在进行重大修改前，备份当前Git状态：

#### 步骤 1: 创建Git状态快照
```bash
# 创建包含当前Git状态的快照
git status > backup/git_status_$(date +%Y%m%d_%H%M%S).txt
git diff > backup/git_diff_$(date +%Y%m%d_%H%M%S).patch
```

#### 步骤 2: 创建提交备份
```bash
# 创建临时提交以保存当前状态
git add .
git commit -m "临时备份提交 $(date +%Y-%m-%d_%H:%M:%S)"
git tag -a backup_$(date +%Y%m%d_%H%M%S) -m "自动备份标签"
```

#### 步骤 3: 记录备份信息
在 [BACKUP_LOG.md](../../../../..) 中记录Git备份信息。

## 3. 恢复操作标准化流程

### 3.1 单文件恢复流程

#### 步骤 1: 确定要恢复的文件和备份版本
```bash
# 查找可用备份
ls -la backup/desktop-app-main.js.backup_*
```

#### 步骤 2: 执行恢复操作
```bash
# 从指定备份恢复文件
cp backup/desktop-app-main.js.backup_20250901_143022 apps/desktop-app/electron_app/main.js
```

#### 步骤 3: 验证恢复结果
```bash
# 检查文件完整性
ls -la apps/desktop-app/electron_app/main.js
# 运行相关测试验证功能
```

#### 步骤 4: 记录恢复操作
在 [BACKUP_LOG.md](../../../../..) 中记录恢复操作信息。

### 3.2 批量文件恢复流程

#### 步骤 1: 确定恢复点
```bash
# 查找备份目录
ls -la backup/
```

#### 步骤 2: 执行批量恢复
```bash
#!/bin/bash
# batch_restore.sh

# 指定要恢复的备份目录
BACKUP_DIR="backup/20250901_143022"

# 从备份目录恢复文件
find $BACKUP_DIR -type f | while read backup_file; do
    # 计算原始文件路径
    original_file=${backup_file#$BACKUP_DIR/}
    
    # 创建目录（如果不存在）
    mkdir -p "$(dirname "$original_file")"
    
    # 执行恢复
    cp "$backup_file" "$original_file"
    echo "已恢复: $original_file"
done

echo "批量恢复完成"
```

#### 步骤 3: 验证批量恢复
```bash
# 验证恢复文件数量
find apps/ packages/ tools/ scripts/ -type f | wc -l
```

### 3.3 Git状态恢复流程

#### 步骤 1: 确定要恢复的Git状态
```bash
# 查看备份标签
git tag | grep backup_
```

#### 步骤 2: 执行Git恢复
```bash
# 恢复到指定标签状态
git reset --hard backup_20250901_143022
```

#### 步骤 3: 清理临时提交（如果需要）
```bash
# 删除备份标签
git tag -d backup_20250901_143022
```

## 4. 自动化备份脚本

### 4.1 日常备份脚本

```bash
#!/bin/bash
# daily_backup.sh

# 设置备份目录
BACKUP_ROOT="backups"
DAILY_BACKUP_DIR="$BACKUP_ROOT/$(date +%Y-%m-%d)"

# 创建备份目录
mkdir -p $DAILY_BACKUP_DIR

# 备份核心目录
echo "开始日常备份..."

# 备份应用代码
rsync -av --exclude='node_modules' --exclude='venv' --exclude='.git' apps/ $DAILY_BACKUP_DIR/apps/
rsync -av --exclude='node_modules' --exclude='.git' packages/ $DAILY_BACKUP_DIR/packages/
rsync -av --exclude='.git' tools/ $DAILY_BACKUP_DIR/tools/
rsync -av --exclude='.git' scripts/ $DAILY_BACKUP_DIR/scripts/

# 备份配置文件
cp package.json $DAILY_BACKUP_DIR/
cp pnpm-workspace.yaml $DAILY_BACKUP_DIR/
cp README.md $DAILY_BACKUP_DIR/

# 备份训练配置
rsync -av training/configs/ $DAILY_BACKUP_DIR/training/configs/

echo "日常备份完成: $DAILY_BACKUP_DIR"
```

### 4.2 完整项目快照脚本

```bash
#!/bin/bash
# full_snapshot.sh

# 设置快照目录
SNAPSHOT_ROOT="snapshots"
SNAPSHOT_DIR="$SNAPSHOT_ROOT/full_$(date +%Y%m%d_%H%M%S)"

# 创建快照目录
mkdir -p $SNAPSHOT_DIR

# 创建完整项目快照
echo "创建完整项目快照..."

# 使用rsync创建完整副本（排除临时文件）
rsync -av \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='*.tmp' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  ./ $SNAPSHOT_DIR/

# 记录快照信息
echo "快照创建时间: $(date)" > $SNAPSHOT_DIR/snapshot_info.txt
echo "快照目录: $SNAPSHOT_DIR" >> $SNAPSHOT_DIR/snapshot_info.txt
du -sh $SNAPSHOT_DIR >> $SNAPSHOT_DIR/snapshot_info.txt

echo "完整快照完成: $SNAPSHOT_DIR"
```

## 5. 备份验证和完整性检查

### 5.1 备份文件完整性检查

```bash
#!/bin/bash
# backup_integrity_check.sh

# 检查备份目录中的文件完整性
BACKUP_DIR="backup"

echo "检查备份完整性..."

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo "错误: 备份目录不存在"
    exit 1
fi

# 检查备份文件是否非空
find $BACKUP_DIR -type f -empty | while read empty_file; do
    echo "警告: 发现空备份文件: $empty_file"
done

# 统计备份文件数量和大小
echo "备份统计:"
find $BACKUP_DIR -type f | wc -l | xargs echo "文件数量:"
find $BACKUP_DIR -type f -exec du -ch {} + | grep total$ | xargs echo "总大小:"

echo "完整性检查完成"
```

### 5.2 备份可恢复性验证

```bash
#!/bin/bash
# backup_recovery_test.sh

# 验证备份文件的可恢复性
TEST_RESTORE_DIR="test_restore"

echo "开始备份可恢复性测试..."

# 创建测试恢复目录
mkdir -p $TEST_RESTORE_DIR

# 选择几个关键文件进行恢复测试
cp backup/desktop-app-main.js.backup_* $TEST_RESTORE_DIR/ 2>/dev/null
cp backup/cli-main.py.backup_* $TEST_RESTORE_DIR/ 2>/dev/null

# 检查恢复文件
if [ -d "$TEST_RESTORE_DIR" ] && [ "$(ls -A $TEST_RESTORE_DIR)" ]; then
    echo "恢复测试成功"
    # 清理测试目录
    rm -rf $TEST_RESTORE_DIR
else
    echo "恢复测试失败"
fi

echo "可恢复性测试完成"
```

## 6. 备份日志管理

### 6.1 备份日志格式

所有备份操作都必须在 [BACKUP_LOG.md](../../../../..) 中记录以下信息：

```markdown
## 备份记录 - 2025-09-01 14:30:22

- **操作类型**: 文件修改前备份
- **原始文件**: apps/desktop-app/electron_app/main.js
- **备份文件**: backup/desktop-app-main.js.backup_20250901_143022
- **备份原因**: 添加新的IPC处理器
- **操作人员**: developer
- **状态**: 成功
```

### 6.2 备份日志轮转

```bash
#!/bin/bash
# rotate_backup_logs.sh

# 备份日志轮转脚本
LOG_FILE="BACKUP_LOG.md"
MAX_SIZE=10485760  # 10MB

# 检查日志文件大小
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE") -gt $MAX_SIZE ]; then
    # 创建新的日志文件
    mv $LOG_FILE ${LOG_FILE}.old
    echo "# 备份日志" > $LOG_FILE
    echo "" >> $LOG_FILE
    echo "旧日志已归档: ${LOG_FILE}.old"
fi
```

## 7. 紧急恢复流程

### 7.1 紧急情况识别

当出现以下情况时，需要执行紧急恢复：
- 核心功能严重故障
- 数据丢失或损坏
- 系统无法正常启动
- 批量文件误删除

### 7.2 紧急恢复步骤

#### 步骤 1: 停止所有写入操作
```bash
# 停止开发服务器
pkill -f "uvicorn"
pkill -f "next"
```

#### 步骤 2: 确定最近的稳定备份点
```bash
# 查看备份目录
ls -la backups/
```

#### 步骤 3: 执行紧急恢复
```bash
# 从最近的备份恢复
LATEST_BACKUP=$(ls -t backups/ | head -n1)
cp -r backups/$LATEST_BACKUP/* ./
```

#### 步骤 4: 验证恢复结果
```bash
# 运行健康检查
tools/health-check.bat
```

#### 步骤 5: 记录紧急恢复操作
在 [BACKUP_LOG.md](../../../../..) 中详细记录紧急恢复过程。

## 8. 最佳实践和注意事项

### 8.1 备份最佳实践

1. **定期备份**: 建立自动化的定期备份机制
2. **多地备份**: 在不同位置保存备份副本
3. **版本管理**: 保留多个备份版本
4. **完整性验证**: 定期验证备份文件的完整性
5. **访问控制**: 限制备份文件的访问权限

### 8.2 恢复最佳实践

1. **测试恢复**: 定期测试备份文件的可恢复性
2. **逐步恢复**: 优先恢复核心文件，再恢复其他文件
3. **验证功能**: 恢复后验证系统功能是否正常
4. **记录过程**: 详细记录恢复操作过程

### 8.3 安全注意事项

1. **备份加密**: 对敏感数据的备份进行加密
2. **权限控制**: 严格控制备份文件的访问权限
3. **传输安全**: 在传输备份文件时使用安全协议
4. **审计日志**: 记录所有备份和恢复操作

## 9. 相关工具和脚本

### 9.1 核心备份工具

- [restore_deleted_files_v4.ps1](../../../../..) - 文件恢复脚本
- [recover_all_deleted_files.ps1](../../../../..) - 全面文件恢复脚本
- [safe-git-cleanup.bat](../../../../..) - Git状态清理工具

### 9.2 辅助工具

- [health-check.bat](../../../../..) - 系统健康检查
- [run-tests.bat](../../../../..) - 测试运行工具