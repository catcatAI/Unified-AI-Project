#!/usr/bin/env python3
"""
统一自动修复系统主入口
提供命令行接口和API接口
"""

import sys
import argparse
from pathlib import Path

def main():
    """主函数"""

    # 检查是否在项目根目录下
    project_root = Path.cwd()
    
    # 尝试导入统一修复系统
    try:
        from unified_auto_fix_system.interfaces.cli_interface import CLIFixInterface
        
        # 创建CLI接口并运行
        cli = CLIFixInterface()
        return cli.run()
    
    except ImportError as e:
        print(f"错误: 无法导入统一修复系统 - {e}")
        print("请确保在项目根目录下运行此脚本")
        return 1
    
    except Exception as e:
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())