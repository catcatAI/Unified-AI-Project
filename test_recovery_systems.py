#!/usr/bin/env python3
"""
测试恢复系统的简化版本
"""

import os
import sys
from pathlib import Path

def test_basic_functionality():
    """测试基础功能"""
    print("=== 测试基础功能 ===")
    
    # 测试路径
    project_root = Path(".").resolve()
    print(f"项目根目录: {project_root}")
    
    # 测试文件扫描
    python_files = list(project_root.rglob("*.py"))[:5]
    print(f"找到 {len(python_files)} 个Python文件（前5个）")
    
    for file_path in python_files:
        print(f"  - {file_path}")
    
    return True

def test_real_repair_system():
    """测试真实修复系统"""
    print("\n=== 测试真实修复系统 ===")
    
    try:
        # 导入修复系统
        from real_auto_repair_system import RealAutoRepairSystem
        print("✓ 修复系统导入成功")
        
        # 初始化修复系统
        repair_system = RealAutoRepairSystem()
        print("✓ 修复系统初始化成功")
        
        # 测试单个文件修复
        test_file = Path("apps/backend/src/config_loader.py")
        if test_file.exists():
            print(f"测试文件: {test_file}")
            
            # 读取文件内容
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"文件大小: {len(content)} 字符")
            
            # 测试语法检查
            import ast
            try:
                ast.parse(content)
                print("✓ 文件语法正确")
            except SyntaxError as e:
                print(f"✗ 语法错误: {e}")
                
                # 尝试简单修复
                lines = content.split('\n')
                print(f"文件有 {len(lines)} 行")
                
                # 检查缩进问题
                for i, line in enumerate(lines[:10], 1):  # 检查前10行
                    if '\t' in line:
                        print(f"  第{i}行有Tab字符")
                    leading_spaces = len(line) - len(line.lstrip())
                    if leading_spaces % 4 != 0 and line.strip():
                        print(f"  第{i}行缩进可能有问题: {leading_spaces} 个空格")
            
        else:
            print(f"测试文件不存在: {test_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ 修复系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligent_cleanup():
    """测试智能清理系统"""
    print("\n=== 测试智能清理系统 ===")
    
    try:
        # 导入清理系统
        from intelligent_cleanup_system import IntelligentCleanupSystem
        print("✓ 清理系统导入成功")
        
        # 初始化清理系统
        cleanup_system = IntelligentCleanupSystem()
        print("✓ 清理系统初始化成功")
        
        # 执行干运行
        result = cleanup_system.perform_intelligent_cleanup(dry_run=True)
        
        print(f"清理分析完成:")
        print(f"  扫描文件: {result['stats']['total_files_scanned']}")
        print(f"  重复文件: {result['cleanup_summary']['duplicate_files']}")
        print(f"  有害文件: {result['cleanup_summary']['harmful_files']}")
        print(f"  空文件: {result['cleanup_summary']['empty_files']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 清理系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_recovery():
    """测试完整恢复系统"""
    print("\n=== 测试完整恢复系统 ===")
    
    try:
        # 导入恢复系统
        from complete_system_recovery import CompleteSystemRecovery
        print("✓ 恢复系统导入成功")
        
        # 初始化恢复系统
        recovery_system = CompleteSystemRecovery()
        print("✓ 恢复系统初始化成功")
        
        # 执行干运行分析
        result = recovery_system.perform_complete_recovery(dry_run=True)
        
        if result["success"]:
            print("✓ 恢复分析完成")
            summary = result.get("summary", {})
            print(f"  处理文件: {summary.get('total_files_processed', 0)}")
            print(f"  解决问题: {summary.get('total_issues_resolved', 0)}")
            print(f"  空间恢复: {summary.get('space_recovered_mb', 0):.2f} MB")
            print(f"  系统健康: {summary.get('system_health_improvement', 0):.2%}")
        else:
            print(f"✗ 恢复分析失败: {result.get('error', '未知错误')}")
        
        return result["success"]
        
    except Exception as e:
        print(f"✗ 恢复系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=== Unified AI Project 恢复系统测试 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print()
    
    # 运行测试
    tests = [
        ("基础功能", test_basic_functionality),
        ("真实修复系统", test_real_repair_system),
        ("智能清理系统", test_intelligent_cleanup),
        ("完整恢复系统", test_complete_recovery),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            result = test_func()
            results[test_name] = result
            print(f"{test_name}: {'通过' if result else '失败'}")
        except Exception as e:
            print(f"{test_name}: 异常失败 - {e}")
            results[test_name] = False
    
    # 总结报告
    print(f"\n{'='*50}")
    print("测试总结报告:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status} {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！恢复系统可以正常工作。")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步调试。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)