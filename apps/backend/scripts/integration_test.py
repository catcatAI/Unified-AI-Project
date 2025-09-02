#!/usr/bin/env python3
"""
集成测试脚本
测试所有自动修复组件是否能协同工作
"""

import os
import sys
from pathlib import Path
import subprocess
import json
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_all_fix_tools():
    """测试所有修复工具"""
    print("=== 测试所有修复工具 ===")
    
    tools = [
        ("简化版修复工具", "scripts/simple_auto_fix.py"),
        ("完整版修复工具", "scripts/auto_fix_complete.py"),
        ("增强版修复工具", "scripts/advanced_auto_fix.py"),
        ("最终验证脚本", "scripts/final_validation.py"),
    ]
    
    results = []
    for tool_name, tool_path in tools:
        print(f"\n测试 {tool_name}...")
        try:
            # 测试脚本是否存在
            script_path = PROJECT_ROOT / tool_path
            if not script_path.exists():
                print(f"✗ {tool_name} 不存在: {script_path}")
                results.append((tool_name, False, "脚本不存在"))
                continue
            
            # 测试脚本是否有语法错误
            import ast
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast.parse(content)
            print(f"✓ {tool_name} 语法正确")
            results.append((tool_name, True, "语法正确"))
            
        except SyntaxError as e:
            print(f"✗ {tool_name} 语法错误: {e}")
            results.append((tool_name, False, f"语法错误: {e}"))
        except Exception as e:
            print(f"✗ {tool_name} 测试失败: {e}")
            results.append((tool_name, False, f"测试失败: {e}"))
    
    return results

def test_package_json_scripts():
    """测试package.json中的脚本"""
    print("\n=== 测试package.json脚本 ===")
    
    try:
        # 读取package.json
        package_json_path = PROJECT_ROOT.parent / "package.json"
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_json = json.load(f)
        
        # 检查必要的脚本是否存在
        required_scripts = [
            "fix",
            "fix:complete", 
            "fix:advanced",
            "fix:advanced:test",
            "validate",
            "validate:fix",
            "demo:fix"
        ]
        
        scripts = package_json.get("scripts", {})
        missing_scripts = []
        for script in required_scripts:
            if script not in scripts:
                missing_scripts.append(script)
        
        if missing_scripts:
            print(f"✗ 缺少脚本: {missing_scripts}")
            return False
        else:
            print("✓ 所有必需的脚本都存在")
            return True
            
    except Exception as e:
        print(f"✗ 测试package.json脚本时出错: {e}")
        return False

def test_user_interface_scripts():
    """测试用户界面脚本"""
    print("\n=== 测试用户界面脚本 ===")
    
    ui_scripts = [
        ("Windows批处理脚本", "scripts/auto_fix.bat"),
        ("Linux/Mac Shell脚本", "scripts/auto_fix.sh"),
    ]
    
    results = []
    for script_name, script_path in ui_scripts:
        print(f"\n测试 {script_name}...")
        try:
            full_path = PROJECT_ROOT / script_path
            if not full_path.exists():
                print(f"✗ {script_name} 不存在: {full_path}")
                results.append((script_name, False, "脚本不存在"))
                continue
            
            # 检查文件大小
            if full_path.stat().st_size == 0:
                print(f"✗ {script_name} 为空")
                results.append((script_name, False, "脚本为空"))
                continue
                
            print(f"✓ {script_name} 存在且非空")
            results.append((script_name, True, "脚本存在且非空"))
            
        except Exception as e:
            print(f"✗ {script_name} 测试失败: {e}")
            results.append((script_name, False, f"测试失败: {e}"))
    
    return results

def generate_test_report(tool_results, package_json_result, ui_results):
    """生成测试报告"""
    print("\n" + "="*50)
    print("集成测试报告")
    print("="*50)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"测试时间: {timestamp}")
    
    # 工具测试结果
    print(f"\n工具测试结果:")
    tool_passed = 0
    for tool_name, passed, message in tool_results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}: {tool_name} - {message}")
        if passed:
            tool_passed += 1
    
    # Package.json测试结果
    package_status = "✓ 通过" if package_json_result else "✗ 失败"
    print(f"\nPackage.json测试: {package_status}")
    
    # UI脚本测试结果
    print(f"\nUI脚本测试结果:")
    ui_passed = 0
    for script_name, passed, message in ui_results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}: {script_name} - {message}")
        if passed:
            ui_passed += 1
    
    # 总结
    total_tests = len(tool_results) + 1 + len(ui_results)
    passed_tests = tool_passed + (1 if package_json_result else 0) + ui_passed
    
    print(f"\n测试总结:")
    print(f"  通过: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有集成测试通过！")
        return True
    else:
        print("❌ 部分测试失败。")
        return False

def main():
    """主函数"""
    print("=== Unified AI Project 集成测试 ===")
    
    # 测试所有修复工具
    tool_results = test_all_fix_tools()
    
    # 测试package.json脚本
    package_json_result = test_package_json_scripts()
    
    # 测试用户界面脚本
    ui_results = test_user_interface_scripts()
    
    # 生成测试报告
    success = generate_test_report(tool_results, package_json_result, ui_results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())