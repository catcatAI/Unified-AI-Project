#!/usr/bin/env python3
"""
验证项目修复进度的真实性
对比MD文档声明与实际状态
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

def search_in_files(pattern, file_extensions=('.py', '.md')):
    """在文件中搜索指定模式"""
    matches = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith(file_extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if pattern in content:
                            matches.append(filepath)
                except:
                    pass
    return matches

def check_syntax_errors():
    """检查实际的语法错误数量"""
    syntax_errors = 0
    total_files = 0
    
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in root or '.git' in root or 'node_modules' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_files += 1
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    compile(content, filepath, 'exec')
                except SyntaxError as e:
                    syntax_errors += 1
                    if syntax_errors <= 5:  # 只显示前5个
                        print(f"  语法错误: {filepath} - {e}")
                except Exception:
                    pass  # 其他错误不算语法错误
    
    return syntax_errors, total_files

def check_tests_conftest():
    """检查tests/conftest.py的实际状态"""
    conftest_path = Path('tests/conftest.py')
    if not conftest_path.exists():
        return "文件不存在"
    
    try:
        with open(conftest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        compile(content, str(conftest_path), 'exec')
        return "语法正确"
    except SyntaxError as e:
        return f"语法错误: {e}"
    except Exception as e:
        return f"其他错误: {e}"

def check_unified_fix_system():
    """检查统一自动修复系统的实际状态"""
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.modules.base_fixer import EnhancedSyntaxFixer
        return "系统正常加载"
    except Exception as e:
        return f"系统加载失败: {e}"

def main():
    print("🔍 项目修复进度真实性验证报告")
    print("=" * 60)
    print(f"验证时间: {datetime.now()}")
    print()
    
    # 1. 检查MD文档中声明的数字
    print("1️⃣ 检查MD文档中的数字声明:")
    
    # 搜索22046的出现
    files_with_22046 = search_in_files("22046")
    if files_with_22046:
        print(f"   ✅ 找到22046出现在: {files_with_22046}")
    else:
        print("   ❌ 未找到22046的具体出现位置")
    
    # 搜索其他相关数字
    for num in ["1154", "22,046", "22,038"]:
        files = search_in_files(num)
        if files:
            print(f"   ✅ {num}出现在: {files}")
    
    print()
    
    # 2. 检查实际的语法错误数量
    print("2️⃣ 实际语法错误检查:")
    actual_syntax_errors, total_python_files = check_syntax_errors()
    print(f"   📊 Python文件总数: {total_python_files}")
    print(f"   ❌ 实际语法错误数: {actual_syntax_errors}")
    print(f"   📈 MD声明语法错误: 22,046个")
    print(f"   📊 差异: {abs(actual_syntax_errors - 22046)}个")
    
    if actual_syntax_errors > 0:
        print("   ⚠️  发现实际语法错误，MD中的声明可能不准确")
    else:
        print("   ✅ 未发现语法错误，MD中的声明基本正确")
    
    print()
    
    # 3. 检查tests/conftest.py状态
    print("3️⃣ tests/conftest.py状态检查:")
    conftest_status = check_tests_conftest()
    print(f"   📋 实际状态: {conftest_status}")
    
    if "语法正确" in conftest_status:
        print("   ✅ 与MD声明一致")
    else:
        print("   ❌ 与MD声明不一致")
    
    print()
    
    # 4. 检查统一自动修复系统
    print("4️⃣ 统一自动修复系统状态:")
    fix_system_status = check_unified_fix_system()
    print(f"   📋 系统状态: {fix_system_status}")
    
    if "系统正常" in fix_system_status:
        print("   ✅ 系统可正常加载")
    else:
        print("   ❌ 系统存在问题")
    
    print()
    
    # 5. 检查pytest框架
    print("5️⃣ pytest框架检查:")
    try:
        import pytest
        print("   ✅ pytest可正常导入")
        
        # 尝试运行简单测试
        result = os.system('python -m pytest --version > nul 2>&1')
        if result == 0:
            print("   ✅ pytest命令可正常执行")
        else:
            print("   ⚠️  pytest命令执行有问题")
            
    except ImportError:
        print("   ❌ pytest无法导入")
    
    print()
    
    # 6. 总体评估
    print("6️⃣ 真实性评估总结:")
    print("=" * 40)
    
    discrepancies = []
    
    if actual_syntax_errors != 22046:
        discrepancies.append(f"语法错误数量差异: 声明22,046 vs 实际{actual_syntax_errors}")
    
    if "语法正确" not in conftest_status:
        discrepancies.append("tests/conftest.py状态与声明不符")
    
    if "系统正常" not in fix_system_status:
        discrepancies.append("统一自动修复系统加载失败")
    
    if discrepancies:
        print("   ❌ 发现以下差异:")
        for disc in discrepancies:
            print(f"      - {disc}")
        print("\n   📊 结论: MD文档中的进度声明存在夸大或不准确之处")
    else:
        print("   ✅ 基本无差异")
        print("\n   📊 结论: MD文档中的进度声明基本准确")
    
    print()
    print("🎯 建议:")
    print("- 重新运行实际的修复过程来验证数字准确性")
    print("- 建立真实的修复进度追踪机制")
    print("- 避免在文档中声明未经验证的修复数量")
    print("- 建立可验证的修复报告生成机制")

if __name__ == "__main__":
    main()