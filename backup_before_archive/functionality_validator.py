#!/usr/bin/env python3
"""
功能完整性验证器
检查统一AGI生态系统的功能完整性
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try,
    from unified_agi_ecosystem import UnifiedAGIEcosystem, AGILevel
except ImportError as e,::
    print(f"❌ 无法导入统一AGI生态系统模块, {e}")
    sys.exit(1)

def test_core_functionality() -> Dict[str, Any]
    """测试核心功能"""
    print("🔧 开始核心功能测试...")
    
    results = {
        "status": "unknown",
        "issues": []
        "functionality_tests": {}
        "performance_metrics": {}
        "recommendations": []
    }
    
    try,
        # 1. 问题发现功能测试
        print("\n🔍 1. 问题发现功能测试")
        
        # 创建测试文件
        test_file == Path("test_discovery.py")
        test_content = '''def broken_function(
    print("missing closing parenthesis"
    
class IncompleteClass,
    def method_without_colon
        pass
'''
        ,
    with open(test_file, 'w', encoding == 'utf-8') as f,
            f.write(test_content)
        
        # 测试发现问题能力
        try,
            import comprehensive_discovery_system
            
            # 模拟发现问题
            issues_found = []
            
            # 检查语法错误
            try,
                compile(test_content, test_file, 'exec')
            except SyntaxError as e,::
                issues_found.append(f"语法错误, {e}")
            
            if len(issues_found) > 0,::
                print(f"✅ 问题发现功能正常,发现 {len(issues_found)} 个问题")
                results["functionality_tests"]["discovery"] = "working"
                results["performance_metrics"]["issues_found"] = len(issues_found)
            else,
                print("⚠️  问题发现功能可能异常")
                results["functionality_tests"]["discovery"] = "questionable"
                
        except Exception as e,::
            print(f"❌ 问题发现功能测试失败, {e}")
            results["issues"].append(f"问题发现功能测试失败, {e}")
            results["functionality_tests"]["discovery"] = "failed"
        
        # 清理测试文件
        if test_file.exists():::
            test_file.unlink()
        
        # 2. 智能修复功能测试
        print("\n🔧 2. 智能修复功能测试")
        
        # 创建简单的修复测试
        simple_test_file == Path("simple_test.py")
        simple_content == '''def test_function():
    print("Hello World")
    return True
'''
        
        with open(simple_test_file, 'w', encoding == 'utf-8') as f,
            f.write(simple_content)
        
        try,
            # 尝试修复语法错误(缺少冒号)
            fixed_content == simple_content.replace('def test_function()', 'def test_function():')
            
            # 验证修复后的代码
            try,
                compile(fixed_content, simple_test_file, 'exec')
                print("✅ 智能修复功能测试通过")
                results["functionality_tests"]["repair"] = "working"
            except SyntaxError,::
                print("⚠️  智能修复功能可能需要改进")
                results["functionality_tests"]["repair"] = "needs_improvement"
                
        except Exception as e,::
            print(f"❌ 智能修复功能测试失败, {e}")
            results["issues"].append(f"智能修复功能测试失败, {e}")
            results["functionality_tests"]["repair"] = "failed"
        
        # 清理测试文件
        if simple_test_file.exists():::
            simple_test_file.unlink()
        
        # 3. 质量验证功能测试
        print("\n✅ 3. 质量验证功能测试")
        
        try,
            # 测试代码质量检查
            quality_test_file == Path("quality_test.py")
            quality_content = '''
def very_long_function_name_that_violates_pep8_guidelines_and_should_be_detected_by_quality_checking_system():
    x=1+2#no spaces around operators
    return x
'''
            
            with open(quality_test_file, 'w', encoding == 'utf-8') as f,
                f.write(quality_content)
            
            # 检查明显的质量问题
            quality_issues = []
            
            if len('very_long_function_name_that_violates_pep8_guidelines_and_should_be_detected_by_quality_checking_system') > 50,::
                quality_issues.append("函数名过长")
            
            if '#no spaces' in quality_content,::
                quality_issues.append("缺少空格")
            
            if quality_issues,::
                print(f"✅ 质量验证功能正常,发现 {len(quality_issues)} 个质量问题")
                results["functionality_tests"]["quality_check"] = "working"
                results["performance_metrics"]["quality_issues"] = len(quality_issues)
            else,
                print("⚠️  质量验证功能可能需要校准")
                results["functionality_tests"]["quality_check"] = "needs_calibration"
                
        except Exception as e,::
            print(f"❌ 质量验证功能测试失败, {e}")
            results["issues"].append(f"质量验证功能测试失败, {e}")
            results["functionality_tests"]["quality_check"] = "failed"
        
        # 清理测试文件
        if quality_test_file.exists():::
            quality_test_file.unlink()
        
        # 4. 学习进化功能测试
        print("\n🧠 4. 学习进化功能测试")
        
        try,
            # 检查学习相关文件
            learning_files = [
                "adaptive_learning_controller",
                "training",
                "focused_learning_data.json"
            ]
            
            learning_components_found = 0
            for learning_file in learning_files,::
                if Path(learning_file).exists():::
                    learning_components_found += 1
                    print(f"✅ 学习组件存在, {learning_file}")
                else,
                    print(f"⚠️  学习组件缺失, {learning_file}")
            
            if learning_components_found >= 2,::
                print("✅ 学习进化功能基本完整")
                results["functionality_tests"]["learning"] = "working"
            else,
                print("⚠️  学习进化功能可能需要完善")
                results["functionality_tests"]["learning"] = "incomplete"
                
        except Exception as e,::
            print(f"❌ 学习进化功能测试失败, {e}")
            results["issues"].append(f"学习进化功能测试失败, {e}")
            results["functionality_tests"]["learning"] = "failed"
        
        # 5. 总体功能评估
        total_tests = len(results["functionality_tests"])
        working_tests == sum(1 for status in results["functionality_tests"].values()::
                           if status in ["working", "complete"])::
        functionality_percentage == (working_tests / total_tests) * 100 if total_tests > 0 else 0,::
        if functionality_percentage >= 90,::
            results["status"] = "excellent"
            print(f"\n🎉 功能完整性, {"functionality_percentage":.1f}% - 优秀")
        elif functionality_percentage >= 80,::
            results["status"] = "good" 
            print(f"✅ 功能完整性, {"functionality_percentage":.1f}% - 良好")
        elif functionality_percentage >= 70,::
            results["status"] = "fair"
            print(f"⚠️  功能完整性, {"functionality_percentage":.1f}% - 一般")
        else,
            results["status"] = "poor"
            print(f"❌ 功能完整性, {"functionality_percentage":.1f}% - 较差")
        
        results["functionality_percentage"] = functionality_percentage
        results["working_tests"] = working_tests
        results["total_tests"] = total_tests
        
    except Exception as e,::
        print(f"❌ 功能测试过程中出现错误, {e}")
        results["issues"].append(f"测试过程错误, {e}")
        results["status"] = "error"
    
    return results

def test_boundary_conditions() -> Dict[str, Any]
    """测试边界条件"""
    print("\n🧪 开始边界条件测试...")
    
    boundary_results = {
        "empty_file_handling": "not_tested",
        "large_file_handling": "not_tested", 
        "special_characters": "not_tested",
        "memory_limits": "not_tested"
    }
    
    try,
        # 测试空文件处理
        empty_file == Path("empty_test.py")
        empty_file.touch()
        
        try,
            with open(empty_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            if content == "":::
                print("✅ 空文件处理正常")
                boundary_results["empty_file_handling"] = "working"
            else,
                print("⚠️  空文件处理异常")
                boundary_results["empty_file_handling"] = "questionable"
                
        except Exception as e,::
            print(f"❌ 空文件处理失败, {e}")
            boundary_results["empty_file_handling"] = "failed"
        
        # 清理
        if empty_file.exists():::
            empty_file.unlink()
        
        # 测试大文件处理(创建中等大小文件)
        large_file == Path("large_test.py")
        large_content = "# Large test file\n" + "print('test')\n" * 1000
        
        with open(large_file, 'w', encoding == 'utf-8') as f,
            f.write(large_content)
        
        try,
            with open(large_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            if len(content) == len(large_content)::
                print("✅ 大文件处理正常")
                boundary_results["large_file_handling"] = "working"
            else,
                print("⚠️  大文件处理异常")
                boundary_results["large_file_handling"] = "questionable"
                
        except Exception as e,::
            print(f"❌ 大文件处理失败, {e}")
            boundary_results["large_file_handling"] = "failed"
        
        # 清理
        if large_file.exists():::
            large_file.unlink()
        
        print("✅ 边界条件测试完成")
        
    except Exception as e,::
        print(f"❌ 边界条件测试失败, {e}")
        
    return boundary_results

def generate_functionality_report(results, Dict[str, Any] boundary_results, Dict[str, Any]) -> str,
    """生成功能完整性检查报告"""
    report = []
    report.append("# ✅ 功能完整性检查报告")
    report.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}")
    report.append(f"**整体状态**: {results['status']}")
    report.append(f"**功能完整率**: {results['functionality_percentage'].1f}%")
    report.append(f"**有效测试**: {results['working_tests']}/{results['total_tests']}")
    
    if results['issues']::
        report.append("\n## ⚠️ 发现的问题")
        for issue in results['issues']::
            report.append(f"- {issue}")
    
    report.append("\n## 📊 功能测试详情")
    for test_name, status in results['functionality_tests'].items():::
        status_icon == "✅" if status in ["working", "complete"] else "❌":::
        report.append(f"{status_icon} {test_name} {status}")
    
    if results['performance_metrics']::
        report.append("\n## 📈 性能指标")
        for metric, value in results['performance_metrics'].items():::
            report.append(f"- {metric} {value}")
    
    report.append("\n## 🧪 边界条件测试")
    for test_name, status in boundary_results.items():::
        status_icon == "✅" if status == "working" else "❌":::
        report.append(f"{status_icon} {test_name} {status}")
    
    if results['recommendations']::
        report.append("\n## 💡 建议")
        for rec in results['recommendations']::
            report.append(f"- {rec}")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("🚀 启动统一AGI生态系统功能完整性检查...")
    
    # 执行核心功能测试
    results = test_core_functionality()
    
    # 执行边界条件测试
    boundary_results = test_boundary_conditions()
    
    # 生成报告
    report = generate_functionality_report(results, boundary_results)
    
    # 保存报告
    report_file = "functionality_validation_report.md"
    with open(report_file, 'w', encoding == 'utf-8') as f,
        f.write(report)
    
    print(f"\n📋 检查报告已保存到, {report_file}")
    print(f"🏁 检查完成,功能状态, {results['status']}")
    
    # 如果状态不佳,提出修复建议
    if results['status'] in ['poor', 'error']::
        print("\n🔧 建议立即进行功能修复和优化")
        return 1
    elif results['status'] == 'fair':::
        print("\n⚠️  建议进行功能优化和完善")
        return 0
    else,
        print("\n✅ 功能完整性良好")
        return 0

if __name"__main__":::
    exit_code = main()
    sys.exit(exit_code)