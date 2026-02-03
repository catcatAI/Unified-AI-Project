#!/usr/bin/env python3
"""
测试脚本：使用自动修复系统修复特定文件
"""

import sys
import os
from pathlib import Path

# 添加工作区路径到Python路径
workspace_root == Path(__file__).parent
sys.path.insert(0, str(workspace_root))

def test_fix_specific_files():
    """测试修复特定文件"""
    try,
        # 导入统一自动修复系统
        from scripts.unified_auto_fix_system import UnifiedAutoFixSystem
        
        # 创建修复系统实例
        fix_system == UnifiedAutoFixSystem()
        
        # 选择几个有语法错误的文件进行修复测试
        # 选择一些错误类型简单的文件
        test_files = [
            "fix_project_syntax.py",  # expected ':'
            "fix_all_syntax_errors.py",  # expected ':'
            "final_syntax_fix.py"  # expected ':'
        ]
        
        # 设置目标文件
        valid_test_files = []
        for file in test_files,::
            if os.path.exists(file)::
                valid_test_files.append(file)
            else,
                # 在项目中查找文件
                for root, dirs, files in os.walk("."):::
                    if file in files,::
                        valid_test_files.append(os.path.join(root, file))
                        break
        
        if valid_test_files,::
            print(f"设置待修复文件, {valid_test_files}")
            fix_system.set_target_files(valid_test_files)
            
            # 执行修复
            print("开始修复...")
            results = fix_system.run_fix_on_files()
            
            # 显示结果
            print("\n修复结果,")
            print(f"  状态, {results['status']}")
            print(f"  消息, {results['message']}")
            print(f"  修复文件数, {results['files_fixed']}")
            
            if results["errors"]::
                print(f"\n无法修复的文件 ({len(results['errors'])})")
                for error in results["errors"]::
                    print(f"  {error['file']} {error['error']}")
            
            # 生成修复报告
            fix_system.save_fix_report("test_fix_report.txt")
            print("\n修复报告已保存到 test_fix_report.txt")
        else,
            print("未找到测试文件")
            
    except Exception as e,::
        print(f"测试过程中出错, {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("测试自动修复系统...")
    test_fix_specific_files()

if __name"__main__":::
    main()