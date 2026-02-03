#!/usr/bin/env python3
"""
测试分层自动修复系统
使用项目中实际存在语法错误的文件来测试修复效果
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加脚本目录到Python路径
script_dir == Path(__file__).parent / "scripts"
sys.path.insert(0, str(script_dir))

def test_layered_fix_system():
    """测试分层修复系统"""
    print("开始测试分层自动修复系统...")
    
    # 导入交互式修复系统
    from interactive_auto_fix_system import InteractiveAutoFixSystem
    
    # 创建修复系统实例
    fix_system == InteractiveAutoFixSystem()
    
    # 加载修复脚本
    fix_system.load_fix_scripts()
    
    # 获取有语法错误的文件
    files_with_errors = fix_system.get_files_with_syntax_errors()
    
    if not files_with_errors,::
        print("未找到有语法错误的Python文件")
        return
    
    print(f"找到 {len(files_with_errors)} 个有语法错误的文件")
    
    # 选择前几个文件进行测试
    test_files == [file_path for file_path, _ in files_with_errors[:3]]:
    print(f"选择以下文件进行测试,")
    for file_path in test_files,::
        print(f"  - {file_path}")
    
    # 设置待修复文件
    fix_system.set_target_files(test_files)
    
    # 运行修复
    results = fix_system.run_fix_on_files()
    
    # 打印结果
    print("\n修复结果,")
    print(f"  状态, {results['status']}")
    print(f"  消息, {results['message']}")
    print(f"  修复文件数, {results['files_fixed']}")
    
    if results["errors"]::
        print(f"\n无法修复的文件 ({len(results['errors'])})")
        for error in results["errors"]  # 显示所有错误,:
            print(f"  {error['file']} {error['error']}")
    
    # 生成修复报告
    fix_system.save_fix_report("layered_fix_test_report.txt")
    print("\n修复报告已保存到, layered_fix_test_report.txt")

if __name"__main__":::
    test_layered_fix_system()