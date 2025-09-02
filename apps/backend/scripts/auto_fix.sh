#!/bin/bash

# Unified AI Project 自动修复脚本
# 用于Linux/Mac环境下的快速修复

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在项目根目录
check_project_root() {
    if [ ! -f "package.json" ]; then
        print_error "请在项目根目录运行此脚本"
        print_info "当前目录: $(pwd)"
        exit 1
    fi
}

# 检查并创建虚拟环境
setup_virtualenv() {
    if [ ! -d "apps/backend/venv" ]; then
        print_warning "未找到虚拟环境，正在创建..."
        cd apps/backend
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            print_error "创建虚拟环境失败"
            exit 1
        fi
        print_success "虚拟环境创建完成"
        cd ../..
    fi
}

# 激活虚拟环境
activate_virtualenv() {
    print_info "激活虚拟环境..."
    cd apps/backend
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        print_error "激活虚拟环境失败"
        exit 1
    fi
    print_success "虚拟环境已激活"
}

# 显示菜单
show_menu() {
    echo
    echo "========================================"
    echo "Unified AI Project 自动修复工具"
    echo "========================================"
    echo
    echo "请选择操作:"
    echo "1. 简化版自动修复"
    echo "2. 完整版自动修复"
    echo "3. 增强版自动修复"
    echo "4. 增强版自动修复 + 测试"
    echo "5. 最终验证"
    echo "6. 自动修复 + 验证"
    echo "7. 退出"
    echo
}

# 执行选择的操作
run_operation() {
    case $1 in
        1)
            print_info "运行简化版自动修复..."
            python scripts/simple_auto_fix.py
            ;;
        2)
            print_info "运行完整版自动修复..."
            python scripts/auto_fix_complete.py
            ;;
        3)
            print_info "运行增强版自动修复..."
            python scripts/advanced_auto_fix.py
            ;;
        4)
            print_info "运行增强版自动修复 + 测试..."
            python scripts/advanced_auto_fix.py --test
            ;;
        5)
            print_info "运行最终验证..."
            python scripts/final_validation.py
            ;;
        6)
            print_info "运行自动修复 + 验证..."
            python scripts/advanced_auto_fix.py --test
            if [ $? -eq 0 ]; then
                print_info "运行最终验证..."
                python scripts/final_validation.py
            fi
            ;;
        7)
            print_success "感谢使用Unified AI Project自动修复工具！"
            cd ../..
            exit 0
            ;;
        *)
            print_warning "无效选择: $1"
            ;;
    esac
}

# 主函数
main() {
    check_project_root
    setup_virtualenv
    activate_virtualenv
    
    while true; do
        show_menu
        read -p "请选择操作 (1-7): " choice
        run_operation $choice
        echo
        read -p "按回车键继续..."
    done
}

# 运行主函数
main