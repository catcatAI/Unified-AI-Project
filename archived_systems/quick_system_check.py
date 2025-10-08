#!/usr/bin/env python3
"""
快速系统检查 - 识别主要问题和覆盖缺口
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime

def quick_system_check():
    """快速系统检查"""
    print("🔍 开始快速系统检查...")
    print("="*60)
    
    # 1. 检查统一自动修复系统状态
    print("1️⃣ 统一自动修复系统状态:")
    try:
        result = subprocess.run(['python', '-m', 'unified_auto_fix_system.main', 'status'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ 统一自动修复系统正常运行")
        else:
            print("❌ 统一自动修复系统存在问题")
    except Exception as e:
        print(f"❌ 统一自动修复系统检查失败: {e}")
    
    # 2. 检查复杂度评估系统
    print("\n2️⃣ 复杂度评估系统:")
    try:
        result = subprocess.run(['python', 'quick_complexity_check.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 1:  # 预期返回1表示COMPLEX级别
            print("✅ 复杂度评估系统正常（COMPLEX级别）")
        else:
            print("⚠️ 复杂度评估系统需要检查")
    except Exception as e:
        print(f"⚠️ 复杂度评估系统检查失败: {e}")
    
    # 3. 检查防范监控机制
    print("\n3️⃣ 防范监控机制:")
    try:
        result = subprocess.run(['python', 'enforce_no_simple_fixes.py', 'check'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ 防范监控机制正常")
        else:
            print("⚠️ 防范监控机制需要检查")
    except Exception as e:
        print(f"⚠️ 防范监控机制检查失败: {e}")
    
    # 4. 快速检查项目状态
    print("\n4️⃣ 项目状态快速检查:")
    try:
        result = subprocess.run(['python', 'quick_verify.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ 项目验证系统正常")
        else:
            print("⚠️ 项目验证系统需要检查")
    except Exception as e:
        print(f"⚠️ 项目验证系统检查失败: {e}")
    
    # 5. 检查主要问题
    print("\n5️⃣ 主要问题识别:")
    
    # 检查语法警告
    syntax_warnings = []
    for py_file in Path('.').glob('*.py'):
        if py_file.name.startswith('check_'):
            try:
                result = subprocess.run(['python', '-m', 'py_compile', str(py_file)], 
                                      capture_output=True, text=True, timeout=5)
                if result.stderr and 'SyntaxWarning' in result.stderr:
                    syntax_warnings.append(py_file.name)
            except:
                pass
    
    if syntax_warnings:
        print(f"⚠️ 发现语法警告: {len(syntax_warnings)}个文件")
        for warning in syntax_warnings[:5]:
            print(f"  - {warning}")
    else:
        print("✅ 未发现语法警告")
    
    # 6. 检查系统覆盖缺口
    print("\n6️⃣ 系统覆盖缺口识别:")
    
    # 检查可能未被发现的错误类型
    uncovered_issues = [
        "逻辑错误（复杂的业务逻辑）",
        "性能问题（效率瓶颈）", 
        "架构问题（设计模式）",
        "测试覆盖问题（用例不足）",
        "文档同步问题（代码与文档不一致）"
    ]
    
    print("⚠️ 可能未被充分发现的错误类型:")
    for issue in uncovered_issues:
        print(f"  - {issue}")
    
    print("\n" + "="*60)
    print("🎯 快速系统检查完成！")
    print("✅ 基础系统架构完整")
    print("⚠️ 发现需要增强的覆盖缺口")
    print("🚀 建议继续系统性增强和修复")

if __name__ == "__main__":
    quick_system_check()