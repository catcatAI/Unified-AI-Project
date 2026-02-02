#!/bin/bash
# Unified Auto-Fix System

echo "=========================================="
echo "  Unified Auto-Fix System"
echo "=========================================="
echo

# 设置Python命令
PYTHON_CMD="python3"

# 检查Python是否可用
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    PYTHON_CMD="python"
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        echo "错误: Python未安装或不在PATH中"
        echo "请安装Python 3.8+并确保其在PATH中"
        exit 1
    fi
fi

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 运行统一修复系统
"$PYTHON_CMD" "$SCRIPT_DIR/unified-fix.py" "$@"

# 检查返回码
if [ $? -ne 0 ]; then
    echo
    echo "统一修复系统执行失败"
    exit 1
fi

exit 0