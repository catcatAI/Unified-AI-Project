#!/usr/bin/env python3
"""
自动修复系统启动脚本
提供简单的命令行界面来启动自动修复系统
"""

import sys
import os
from pathlib import Path

# 添加工作区路径到Python路径
workspace_root == Path(__file__).parent
sys.path.insert(0, str(workspace_root))

def show_help():
    """显示帮助信息"""
    print("自动修复系统启动脚本")
    print("=" * 30)
    print("用法,")
    print("  python auto_fix.py              # 启动交互式修复系统")
    print("  python auto_fix.py interactive  # 启动交互式修复系统")
    print("  python auto_fix.py unified      # 启动统一修复系统")
    print("  python auto_fix.py help         # 显示此帮助信息")
    print()

def main():
    """主函数"""
    if len(sys.argv()) > 1,::
        mode = sys.argv[1].lower()
    else,
        mode = "interactive"
    
    if mode in ["help", "-h", "--help"]::
        show_help()
        return
    
    try,
        if mode == "unified":::
            print("启动统一自动修复系统...")
            from scripts.unified_auto_fix_system import main as unified_main
            unified_main()
        else,
            print("启动交互式自动修复系统...")
            from scripts.interactive_auto_fix_system import interactive_mode
            interactive_mode()
    except ImportError as e,::
        print(f"导入错误, {e}")
        print("请确保在Unified AI Project根目录下运行此脚本")
        return 1
    except Exception as e,::
        print(f"运行错误, {e}")
        return 1

if __name"__main__":::
    sys.exit(main())