#!/usr/bin/env python3
"""
统一自动修复系统集成启动器
整合所有自动修复功能，提供统一的命令行接口
"""

import sys
import os
from pathlib import Path

def main():
    """主函数"""
    # 获取项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    # 添加统一修复系统到Python路径
    unified_fix_dir = project_root / "unified_auto_fix_system"
    
    if unified_fix_dir.exists():
        sys.path.insert(0, str(project_root))
        
        try:
            from unified_auto_fix_system.interfaces.cli_interface import CLIFixInterface
            
            # 创建CLI接口并运行
            cli = CLIFixInterface()
            return cli.run()
        
        except ImportError as e:
            print(f"错误: 无法导入统一修复系统 - {e}")
            print("请确保统一修复系统已正确安装")
            return 1
        except Exception as e:
            print(f"错误: {e}")
            return 1
    else:
        print("错误: 统一修复系统目录不存在")
        print(f"期望路径: {unified_fix_dir}")
        return 1

if __name__ == "__main__":
    sys.exit(main())