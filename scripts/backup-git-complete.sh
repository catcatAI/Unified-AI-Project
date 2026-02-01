#!/bin/bash
# 完整Git仓库备份脚本 - Unified-AI-Project
# 创建时间: $(date)

BACKUP_DIR=".git-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔄 开始完整备份..."
echo "备份目录: $BACKUP_DIR"

# 1. 创建完整bundle（包含所有分支和标签）
echo "📦 创建完整bundle..."
git bundle create "$BACKUP_DIR/unified-ai-COMPLETE.bundle" --all

# 2. 备份所有分支引用
echo "📝 备份分支列表..."
git branch -a > "$BACKUP_DIR/all-branches.txt"

# 3. 备份所有标签
echo "🏷️ 备份标签列表..."
git tag -l > "$BACKUP_DIR/all-tags.txt"

# 4. 备份reflog
echo "📜 备份reflog..."
git reflog show --all > "$BACKUP_DIR/all-reflog.txt"

# 5. 备份所有引用
echo "🔗 备份所有引用..."
git for-each-ref --format='%(refname:short) %(objectname:short)' > "$BACKUP_DIR/all-refs.txt"

# 6. 备份仓库配置
echo "⚙️ 备份配置..."
cp .git/config "$BACKUP_DIR/git-config.txt"

# 7. 创建提交日志
echo "📊 创建提交历史..."
git log --all --oneline > "$BACKUP_DIR/all-commits.txt"

# 8. 计算校验和
echo "🔐 计算校验和..."
find "$BACKUP_DIR" -type f -exec md5sum {} \; > "$BACKUP_DIR/CHECKSUMS.md5"

echo ""
echo "✅ 备份完成！"
echo "备份位置: $BACKUP_DIR"
echo ""
echo "📊 备份统计:"
echo "  - 分支数: $(git branch -a | wc -l)"
echo "  - 标签数: $(git tag -l | wc -l)"
echo "  - 总提交数: $(git log --all --oneline | wc -l)"
echo "  - Bundle大小: $(du -h $BACKUP_DIR/unified-ai-COMPLETE.bundle | cut -f1)"
echo ""
echo "💾 恢复方法:"
echo "  git clone unified-ai-COMPLETE.bundle new-repo"
echo "  cd new-repo"
echo "  git remote add origin <your-repo-url>"
